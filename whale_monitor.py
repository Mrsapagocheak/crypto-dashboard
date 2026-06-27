"""
whale_monitor.py — מעקב אחר ארנק whale ב-Ethereum
מקור: Etherscan API (חינמי, 5 req/sec)
שומר ל-Supabase: whale_txs
שולח התראות ל-Telegram על מהלכים גדולים
"""

import os
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- הגדרות ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")
WHALE_WALLET = os.getenv("WHALE_WALLET", "").lower()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")

# סף מינימלי לדיווח (בדולרים)
MIN_USD_ALERT = 50_000       # $50K+ → שולח התראה טלגרם
MIN_USD_SAVE = 10_000        # $10K+ → שומר ל-Supabase

# סף יתרת ארנק — רק ארנקים עם יתרה מעל סכום זה ייחשבו whales
MIN_WALLET_BALANCE_USD = 1_000_000   # $1M

# כמה שניות בין בדיקות
POLL_INTERVAL = 30

# ERC-20 tokens מעניינים (contract address → symbol)
KNOWN_TOKENS = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "WBTC",
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": "AAVE",
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": "UNI",
    "0x514910771af9ca656af840dff83e8264ecf986ca": "LINK",
}

db = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# cache: ארנקים שכבר בדקנו
_qualified_wallets: dict[str, float] = {}   # address → balance_usd (עבר $1M)
_rejected_wallets: set[str] = set()         # address (נכשל בבדיקה, <$1M)


# ---------------------------------------------------------------------------
# מחיר ETH מ-Binance (ללא key)
# ---------------------------------------------------------------------------

def get_eth_price() -> float:
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": "ETHUSDT"},
            timeout=5,
        )
        return float(r.json()["price"])
    except Exception:
        return 3_000.0  # fallback


def get_token_price_usd(symbol: str) -> float:
    """שולף מחיר token מ-Binance (אם קיים)"""
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": f"{symbol}USDT"},
            timeout=5,
        )
        data = r.json()
        if "price" in data:
            return float(data["price"])
    except Exception:
        pass
    return 1.0  # stablecoins default


# ---------------------------------------------------------------------------
# Etherscan API calls
# ---------------------------------------------------------------------------

ETHERSCAN_BASE = "https://api.etherscan.io/api"


def etherscan_get(params: dict) -> list:
    """קריאה ל-Etherscan, מחזירה list של תוצאות או []"""
    params["apikey"] = ETHERSCAN_KEY
    try:
        r = requests.get(ETHERSCAN_BASE, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "1" and isinstance(data.get("result"), list):
            return data["result"]
    except Exception as e:
        print(f"[whale] Etherscan error: {e}")
    return []


def get_wallet_balance_eth(address: str) -> float:
    """שולף יתרת ETH של ארנק מ-Etherscan. מחזיר 0.0 בשגיאה."""
    params = {
        "module": "account",
        "action": "balance",
        "address": address,
        "tag": "latest",
        "apikey": ETHERSCAN_KEY,
    }
    try:
        r = requests.get(ETHERSCAN_BASE, params=params, timeout=10)
        data = r.json()
        if data.get("status") == "1":
            return int(data["result"]) / 1e18
    except Exception as e:
        print(f"[whale] balance error ({address[:8]}...): {e}")
    return 0.0


def is_qualified_whale(address: str, eth_price: float) -> bool:
    """
    בודק האם ארנק הוא whale (יתרה > $1M).
    משתמש ב-cache — לא שולח קריאת API חוזרת לאותו ארנק.
    """
    if not address or address == WHALE_WALLET:
        return True  # את הארנק שלנו אנחנו תמיד סומכים

    if address in _qualified_wallets:
        return True
    if address in _rejected_wallets:
        return False

    # קריאת API חדשה לארנק לא מוכר
    time.sleep(0.2)  # rate limit
    balance_eth = get_wallet_balance_eth(address)
    balance_usd = balance_eth * eth_price

    if balance_usd >= MIN_WALLET_BALANCE_USD:
        _qualified_wallets[address] = balance_usd
        print(
            f"[whale] ✅ ארנק מאומת: {address[:8]}... "
            f"יתרה: {balance_eth:.2f} ETH (${balance_usd:,.0f})"
        )
        return True
    else:
        _rejected_wallets.add(address)
        print(
            f"[whale] ⛔ ארנק דחוי: {address[:8]}... "
            f"יתרה: {balance_eth:.4f} ETH (${balance_usd:,.0f}) — מתחת ל-$1M"
        )
        return False


def get_eth_txs(wallet: str, start_block: int) -> list:
    """ETH transfers (txlist)"""
    return etherscan_get({
        "module": "account",
        "action": "txlist",
        "address": wallet,
        "startblock": start_block,
        "endblock": 99999999,
        "sort": "desc",
        "offset": 50,
        "page": 1,
    })


def get_token_txs(wallet: str, start_block: int) -> list:
    """ERC-20 token transfers"""
    return etherscan_get({
        "module": "account",
        "action": "tokentx",
        "address": wallet,
        "startblock": start_block,
        "endblock": 99999999,
        "sort": "desc",
        "offset": 50,
        "page": 1,
    })


# ---------------------------------------------------------------------------
# Parse transactions
# ---------------------------------------------------------------------------

def parse_eth_tx(tx: dict, eth_price: float) -> dict | None:
    """ממיר ETH transaction לפורמט אחיד"""
    try:
        value_eth = int(tx.get("value", 0)) / 1e18
        if value_eth < 0.001:
            return None

        usd_value = value_eth * eth_price
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()
        direction = "OUT" if from_addr == WHALE_WALLET else "IN"

        return {
            "wallet": WHALE_WALLET,
            "tx_hash": tx.get("hash", ""),
            "symbol": "ETH",
            "direction": direction,
            "token_amount": round(value_eth, 6),
            "usd_value": round(usd_value, 2),
            "from_address": from_addr,
            "to_address": to_addr,
            "block_number": int(tx.get("blockNumber", 0)),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"[whale] parse_eth_tx error: {e}")
        return None


def parse_token_tx(tx: dict) -> dict | None:
    """ממיר ERC-20 token transfer לפורמט אחיד"""
    try:
        contract = tx.get("contractAddress", "").lower()
        symbol = KNOWN_TOKENS.get(contract, tx.get("tokenSymbol", "UNKNOWN"))
        decimals = int(tx.get("tokenDecimal", 18))
        amount = int(tx.get("value", 0)) / (10 ** decimals)

        if amount < 0.01:
            return None

        usd_value = amount * get_token_price_usd(symbol)
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()
        direction = "OUT" if from_addr == WHALE_WALLET else "IN"

        return {
            "wallet": WHALE_WALLET,
            "tx_hash": tx.get("hash", ""),
            "symbol": symbol,
            "direction": direction,
            "token_amount": round(amount, 4),
            "usd_value": round(usd_value, 2),
            "from_address": from_addr,
            "to_address": to_addr,
            "block_number": int(tx.get("blockNumber", 0)),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"[whale] parse_token_tx error: {e}")
        return None


# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------

_seen_hashes: set[str] = set()


def save_to_supabase(row: dict) -> bool:
    """שומר transaction ל-Supabase. מחזיר True אם נשמר (לא duplicate)"""
    if not db:
        return False
    if row["tx_hash"] in _seen_hashes:
        return False

    try:
        db.table("whale_txs").insert(row).execute()
        _seen_hashes.add(row["tx_hash"])
        return True
    except Exception as e:
        err = str(e).lower()
        if "duplicate" in err or "unique" in err:
            _seen_hashes.add(row["tx_hash"])
        else:
            print(f"[whale] Supabase error: {e}")
        return False


def load_recent_hashes():
    """טוען tx hashes אחרונים מ-Supabase כדי לא לשלוח כפולות אחרי restart"""
    if not db:
        return
    try:
        result = (
            db.table("whale_txs")
            .select("tx_hash")
            .order("created_at", desc=True)
            .limit(200)
            .execute()
        )
        for row in result.data:
            _seen_hashes.add(row["tx_hash"])
        print(f"[whale] טעון {len(_seen_hashes)} tx hashes קיימים")
    except Exception as e:
        print(f"[whale] load_recent_hashes error: {e}")


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print(f"[whale] Telegram not configured: {msg}")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        print(f"[whale] Telegram error: {e}")


def format_alert(row: dict) -> str:
    """מפרמט התראה לטלגרם"""
    direction_emoji = "📤" if row["direction"] == "OUT" else "📥"
    direction_label = "SENT" if row["direction"] == "OUT" else "RECEIVED"

    symbol = row["symbol"]
    amount = row["token_amount"]
    usd = row["usd_value"]
    tx = row["tx_hash"]
    short_from = row["from_address"][:6] + "..." + row["from_address"][-4:]
    short_to = row["to_address"][:6] + "..." + row["to_address"][-4:] if row["to_address"] else "?"

    size_label = "🐳 MEGA WHALE" if usd >= 1_000_000 else "🐋 Whale Move"

    return (
        f"{direction_emoji} <b>{size_label}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 {amount:,.4f} <b>{symbol}</b> (${usd:,.0f})\n"
        f"📌 {direction_label}\n"
        f"👤 From: <code>{short_from}</code>\n"
        f"➡️ To: <code>{short_to}</code>\n"
        f"🔗 <a href='https://etherscan.io/tx/{tx}'>Etherscan</a>"
    )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def monitor():
    if not WHALE_WALLET:
        print("[whale] ❌ WHALE_WALLET לא מוגדר ב-.env — הוסף כתובת ארנק ועצור/הפעל מחדש")
        return

    print(f"[whale] 🐋 מתחיל מעקב: {WHALE_WALLET[:8]}...{WHALE_WALLET[-4:]}")
    load_recent_hashes()

    last_block = 0
    eth_price = get_eth_price()
    price_refresh_counter = 0

    while True:
        try:
            # רענון מחיר ETH כל 10 איטרציות (~5 דקות)
            price_refresh_counter += 1
            if price_refresh_counter % 10 == 0:
                eth_price = get_eth_price()

            # שלב 1: ETH transactions
            eth_txs = get_eth_txs(WHALE_WALLET, last_block)
            time.sleep(0.3)  # rate limit: 5 req/sec

            for tx in eth_txs:
                row = parse_eth_tx(tx, eth_price)
                if not row:
                    continue
                if row["usd_value"] < MIN_USD_SAVE:
                    continue

                # ← בדיקת יתרה: הצד השני של העסקה חייב להיות whale ($1M+)
                counterparty = row["from_address"] if row["direction"] == "IN" else row["to_address"]
                if not is_qualified_whale(counterparty, eth_price):
                    continue  # מתחת ל-$1M — מתעלם בשקט

                saved = save_to_supabase(row)
                if saved:
                    bal_usd = _qualified_wallets.get(counterparty, 0)
                    print(
                        f"[whale] ETH {row['direction']} {row['token_amount']:.2f} ETH "
                        f"(${row['usd_value']:,.0f}) | counterparty bal: ${bal_usd:,.0f}"
                    )
                    if row["usd_value"] >= MIN_USD_ALERT:
                        send_telegram(format_alert(row))

                # עדכן last_block
                if row["block_number"] > last_block:
                    last_block = row["block_number"]

            # שלב 2: ERC-20 token transfers
            token_txs = get_token_txs(WHALE_WALLET, last_block)
            time.sleep(0.3)

            for tx in token_txs:
                row = parse_token_tx(tx)
                if not row:
                    continue
                if row["usd_value"] < MIN_USD_SAVE:
                    continue

                # ← בדיקת יתרה: הצד השני של העסקה חייב להיות whale ($1M+)
                counterparty = row["from_address"] if row["direction"] == "IN" else row["to_address"]
                if not is_qualified_whale(counterparty, eth_price):
                    continue  # מתחת ל-$1M — מתעלם בשקט

                saved = save_to_supabase(row)
                if saved:
                    bal_usd = _qualified_wallets.get(counterparty, 0)
                    print(
                        f"[whale] TOKEN {row['direction']} {row['token_amount']:,.2f} {row['symbol']} "
                        f"(${row['usd_value']:,.0f}) | counterparty bal: ${bal_usd:,.0f}"
                    )
                    if row["usd_value"] >= MIN_USD_ALERT:
                        send_telegram(format_alert(row))

                if row["block_number"] > last_block:
                    last_block = row["block_number"]

        except KeyboardInterrupt:
            print("[whale] ⏹ הופסק ידנית")
            break
        except Exception as e:
            print(f"[whale] שגיאה: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    monitor()
