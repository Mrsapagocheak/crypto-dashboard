---
name: crypto-data
description: >
  Knows all API endpoints, data sources, and Python code patterns for the crypto dashboard.
  Triggers on: "איך מחברים API", "קוד לבוט", "whale monitor code", "copy bot code", "CoinGlass API", "Etherscan".
---

# Crypto Data Sources & Bot Code

## API Sources Summary

| Data | Source | Free Tier | Key Name |
|------|--------|-----------|----------|
| Liquidations live | CoinGlass WebSocket | 1000 req/day | COINGLASS_API_KEY |
| Funding rates | CoinGlass REST | included | same |
| On-chain txs | Etherscan | 5 req/sec | ETHERSCAN_API_KEY |
| On-chain (multi-chain) | Moralis | 40k req/day | MORALIS_API_KEY |
| News + sentiment | CryptoPanic | free | CRYPTOPANIC_API_KEY |
| Fear & Greed | alternative.me | no key needed | — |
| Exchange trading | Binance | free | BINANCE_API_KEY + SECRET |
| Exchange trading | Bybit | free | BYBIT_API_KEY + SECRET |

---

## whale_monitor.py

```python
import os, time, requests
from supabase import create_client
from telegram import Bot

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALERT_THRESHOLD_USD = 50000

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def get_watched_wallets():
    result = supabase.table("whale_watchlist").select("*").execute()
    return result.data

def get_recent_txs(wallet_address):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&sort=desc&offset=10&apikey={ETHERSCAN_KEY}"
    r = requests.get(url, timeout=10)
    return r.json().get("result", [])

def is_new_tx(tx_hash):
    result = supabase.table("whale_transactions").select("tx_hash").eq("tx_hash", tx_hash).execute()
    return len(result.data) == 0

def save_tx(wallet, tx, usd_value):
    supabase.table("whale_transactions").insert({
        "wallet_address": wallet["address"],
        "wallet_label": wallet.get("label", "Unknown"),
        "tx_hash": tx["hash"],
        "action": "transfer",
        "token": "ETH",
        "usd_value": usd_value,
        "timestamp": int(tx["timeStamp"])
    }).execute()

def send_alert(wallet, usd_value, tx_hash):
    msg = f"🐋 WHALE ALERT\n{wallet.get('label', wallet['address'][:8]+'...')}\nMoved: ${usd_value:,.0f}\nhttps://etherscan.io/tx/{tx_hash}"
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

def monitor():
    print("Whale monitor started...")
    while True:
        wallets = get_watched_wallets()
        for wallet in wallets:
            try:
                txs = get_recent_txs(wallet["address"])
                for tx in txs:
                    if is_new_tx(tx["hash"]):
                        eth_amount = int(tx["value"]) / 1e18
                        usd_value = eth_amount * get_eth_price()
                        save_tx(wallet, tx, usd_value)
                        if usd_value > ALERT_THRESHOLD_USD:
                            send_alert(wallet, usd_value, tx["hash"])
            except Exception as e:
                print(f"Error monitoring {wallet['address']}: {e}")
        time.sleep(60)

def get_eth_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=5)
        return r.json()["ethereum"]["usd"]
    except:
        return 3000  # fallback

if __name__ == "__main__":
    monitor()
```

---

## copy_bot.py

```python
import os, time
from supabase import create_client
from binance.client import Client  # pip install python-binance
from telegram import Bot

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
binance = Client(BINANCE_KEY, BINANCE_SECRET)
telegram = Bot(token=TELEGRAM_TOKEN)

def get_bot_settings():
    result = supabase.table("bot_settings").select("*").eq("id", 1).execute()
    return result.data[0] if result.data else None

def get_last_whale_tx(wallet_address):
    result = supabase.table("whale_transactions") \
        .select("*") \
        .eq("wallet_address", wallet_address) \
        .order("timestamp", desc=True) \
        .limit(1) \
        .execute()
    return result.data[0] if result.data else None

def open_position(symbol, side, usd_size):
    # Paper trading mode check
    settings = get_bot_settings()
    if settings.get("paper_mode", True):
        log_trade(symbol, side, usd_size, paper=True)
        return

    price = float(binance.get_symbol_ticker(symbol=f"{symbol}USDT")["price"])
    qty = round(usd_size / price, 3)
    order = binance.order_market(symbol=f"{symbol}USDT", side=side, quantity=qty)
    log_trade(symbol, side, usd_size, order_id=order["orderId"])
    notify(f"🤖 Bot opened {side} {symbol} ${usd_size:,.0f}")

def log_trade(symbol, side, usd_size, paper=False, order_id=None):
    supabase.table("bot_trades").insert({
        "symbol": symbol,
        "action": side,
        "usd_size": usd_size,
        "paper_trade": paper,
        "exchange_order_id": order_id,
        "status": "open",
        "timestamp": int(time.time())
    }).execute()

def notify(msg):
    telegram.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

last_tx_seen = {}

def run():
    print("Copy bot started (paper mode by default)...")
    while True:
        settings = get_bot_settings()
        if not settings or not settings.get("is_active"):
            time.sleep(30)
            continue

        wallet = settings.get("copy_wallet_address")
        copy_pct = settings.get("copy_percentage", 10) / 100
        max_size = settings.get("max_position_usd", 500)

        if not wallet:
            time.sleep(30)
            continue

        tx = get_last_whale_tx(wallet)
        if tx and tx["tx_hash"] != last_tx_seen.get(wallet):
            last_tx_seen[wallet] = tx["tx_hash"]
            our_size = min(tx["usd_value"] * copy_pct, max_size)
            if our_size > 10:  # min $10 trade
                open_position("BTC", "BUY", our_size)

        time.sleep(30)

if __name__ == "__main__":
    run()
```

---

## Supabase Tables to Create

Run these in Supabase SQL editor:

```sql
-- Whale watchlist
create table whale_watchlist (
  id uuid primary key default gen_random_uuid(),
  address text not null unique,
  label text,
  added_at timestamp default now()
);

-- Whale transactions
create table whale_transactions (
  id uuid primary key default gen_random_uuid(),
  wallet_address text,
  wallet_label text,
  tx_hash text unique,
  action text,
  token text,
  usd_value float,
  timestamp bigint,
  created_at timestamp default now()
);

-- Bot settings (single row)
create table bot_settings (
  id int primary key default 1,
  is_active boolean default false,
  paper_mode boolean default true,
  copy_wallet_address text,
  copy_percentage float default 10,
  max_position_usd float default 500
);
insert into bot_settings (id) values (1);

-- Bot trades log
create table bot_trades (
  id uuid primary key default gen_random_uuid(),
  symbol text,
  action text,
  usd_size float,
  paper_trade boolean default true,
  exchange_order_id text,
  entry_price float,
  exit_price float,
  pnl float,
  status text default 'open',
  timestamp bigint,
  created_at timestamp default now()
);
```
