"""
bot.py — בוט טלגרם לדשבורד קריפטו
- עונה על שאלות קריפטו בעברית דרך OpenRouter (claude-sonnet-4-5)
- פקודות: /news /funding /whales /status /help
- משולב עם: news_fetcher, funding_rates, whale_monitor, Supabase
- Flask health endpoint על PORT (ל-Render free tier + UptimeRobot)
"""

import os
import asyncio
import logging
import threading
import requests
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# מודולים פנימיים
from news_fetcher import fetch_news, format_for_telegram as news_format
from funding_rates import get_all_funding_rates, format_for_telegram as funding_format

load_dotenv()

# --- הגדרות ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# Supabase client (optional — לפקודת /whales)
try:
    from supabase import create_client
    db = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
except Exception:
    db = None


# ---------------------------------------------------------------------------
# Flask health endpoint (מונע שינה ב-Render free tier)
# ---------------------------------------------------------------------------

_flask_app = Flask(__name__)

@_flask_app.route("/health")
def health():
    return "OK", 200

@_flask_app.route("/")
def index():
    return "🤖 Crypto Bot is running", 200

def _run_flask():
    port = int(os.environ.get("PORT", 5000))
    log.info(f"Health server on port {port}")
    _flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


# ---------------------------------------------------------------------------
# OpenRouter AI
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """אתה עוזר מומחה לשוק הקריפטו. אתה עונה בעברית תמיד.
אתה מנתח נתוני שוק, מסביר מושגים, ומספק תובנות על:
- Bitcoin, Ethereum ואלטקוינים
- DeFi, liquidations, funding rates
- ניתוח on-chain ותנועות whale
- מגמות שוק וסנטימנט

ענה בצורה קצרה וממוקדת. אם אין לך מידע עדכני — אמור זאת בכנות.
אל תיתן עצות השקעה ספציפיות."""


def ask_ai(question: str, context: str = "") -> str:
    """שולח שאלה ל-OpenRouter ומחזיר תשובה"""
    if not OPENROUTER_KEY:
        return "❌ OPENROUTER_API_KEY לא מוגדר ב-.env"

    messages = []
    if context:
        messages.append({
            "role": "user",
            "content": f"רקע נוכחי:\n{context}\n\nשאלה: {question}"
        })
    else:
        messages.append({"role": "user", "content": question})

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "HTTP-Referer": "https://github.com/Mrsapagocheak/crypto-dashboard",
                "X-Title": "Crypto Dashboard Bot",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *messages,
                ],
                "max_tokens": 800,
                "temperature": 0.7,
            },
            timeout=30,
        )
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        elif "error" in data:
            return f"❌ OpenRouter error: {data['error'].get('message', 'unknown')}"
    except requests.Timeout:
        return "⏱ תגובת AI ארכה יותר מדי — נסה שוב"
    except Exception as e:
        log.error(f"OpenRouter error: {e}")
        return f"❌ שגיאה: {e}"

    return "❌ תגובה לא צפויה מ-AI"


def get_market_context() -> str:
    """בונה קונטקסט שוק עדכני לשאלות AI"""
    lines = []
    try:
        for symbol in ["BTCUSDT", "ETHUSDT"]:
            r = requests.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": symbol},
                timeout=5,
            )
            price = float(r.json()["price"])
            lines.append(f"{symbol.replace('USDT','')}: ${price:,.0f}")
    except Exception:
        pass
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        fng = r.json()["data"][0]
        lines.append(f"Fear & Greed: {fng['value']} ({fng['value_classification']})")
    except Exception:
        pass
    return "\n".join(lines) if lines else ""


# ---------------------------------------------------------------------------
# עוזרי Supabase
# ---------------------------------------------------------------------------

def get_recent_whales(limit: int = 5) -> list[dict]:
    if not db:
        return []
    try:
        result = (
            db.table("whale_txs")
            .select("symbol,direction,token_amount,usd_value,from_address,to_address,created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        log.error(f"Supabase whales error: {e}")
        return []


def format_whale_row(row: dict) -> str:
    emoji = "📤" if row["direction"] == "OUT" else "📥"
    addr = row["from_address"][:6] + "..." + row["from_address"][-4:]
    return (
        f"{emoji} <b>{row['symbol']}</b> {row['token_amount']:,.2f} "
        f"(${row['usd_value']:,.0f})\n"
        f"   👤 {addr}"
    )


# ---------------------------------------------------------------------------
# פקודות טלגרם
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 <b>Crypto Dashboard Bot</b>\n\n"
        "שלח לי שאלה בעברית על הקריפטו ואענה!\n\n"
        "<b>פקודות:</b>\n"
        "/news — חדשות אחרונות\n"
        "/funding — Funding Rates (Bybit)\n"
        "/whales — תנועות whale אחרונות\n"
        "/status — סטטוס כל השירותים\n"
        "/help — עזרה\n\n"
        "💬 או פשוט שאל כל שאלה בחופשיות!"
    )
    await update.message.reply_html(text)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>מדריך שימוש</b>\n\n"
        "• <b>שאלות חופשיות:</b> \"מה קורה עם BTC?\" / \"מה זה funding rate?\"\n"
        "• <b>/news [מילת מפתח]</b> — חדשות (אפשר לסנן: /news bitcoin)\n"
        "• <b>/funding</b> — Funding rates ל-BTC/ETH/SOL/BNB\n"
        "• <b>/whales</b> — 5 תנועות whale אחרונות שנשמרו\n"
        "• <b>/status</b> — בדיקת חיבורים לכל ה-APIs\n"
    )
    await update.message.reply_html(text)


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(ctx.args) if ctx.args else None
    await update.message.reply_text("📰 מביא חדשות...")
    news = fetch_news(max_items=10, keyword_filter=keyword)
    if not news:
        await update.message.reply_text(
            f"📰 לא נמצאו חדשות{'  ל-' + keyword if keyword else ''}"
        )
        return
    msg = news_format(news, max_items=5)
    if keyword and news:
        titles = "\n".join(f"- {n['title']}" for n in news[:5])
        analysis = ask_ai(f"נתח בקצרה את החדשות הבאות על {keyword}:", context=titles)
        msg += f"\n\n🤖 <b>ניתוח AI:</b>\n{analysis}"
    await update.message.reply_html(msg, disable_web_page_preview=True)


async def cmd_funding(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 מביא funding rates...")
    rates = get_all_funding_rates()
    msg = funding_format(rates)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_whales(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = get_recent_whales(limit=5)
    if not rows:
        await update.message.reply_html(
            "🐋 אין תנועות whale שמורות עדיין.\n"
            "<i>whale_monitor.py צריך לרוץ ברקע</i>"
        )
        return
    lines = ["🐋 <b>תנועות Whale אחרונות</b>\n"]
    for row in rows:
        lines.append(format_whale_row(row))
        ts = row.get("created_at", "")[:16].replace("T", " ")
        lines.append(f"   🕐 {ts}\n")
    await update.message.reply_html("\n".join(lines))


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 בודק שירותים...")
    results = []
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
        btc = float(r.json()["price"])
        results.append(f"✅ Binance — BTC: ${btc:,.0f}")
    except Exception as e:
        results.append(f"❌ Binance — {e}")
    try:
        r = requests.get("https://api.bybit.com/v5/market/funding/history", params={"category": "linear", "symbol": "BTCUSDT", "limit": 1}, timeout=5)
        code = r.json().get("retCode", -1)
        results.append(f"✅ Bybit funding API" if code == 0 else f"❌ Bybit (code {code})")
    except Exception as e:
        results.append(f"❌ Bybit — {e}")
    etherscan_key = os.getenv("ETHERSCAN_API_KEY", "")
    if etherscan_key:
        try:
            r = requests.get("https://api.etherscan.io/api", params={"module": "stats", "action": "ethprice", "apikey": etherscan_key}, timeout=5)
            data = r.json()
            if data.get("status") == "1":
                results.append(f"✅ Etherscan — ETH: ${float(data['result']['ethusd']):,.0f}")
            else:
                results.append(f"⚠️ Etherscan — {data.get('result','?')}")
        except Exception as e:
            results.append(f"❌ Etherscan — {e}")
    else:
        results.append("⚠️ Etherscan — API key חסר")
    if OPENROUTER_KEY:
        try:
            r = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {OPENROUTER_KEY}"}, timeout=5)
            results.append("✅ OpenRouter" if r.status_code == 200 else f"❌ OpenRouter (HTTP {r.status_code})")
        except Exception as e:
            results.append(f"❌ OpenRouter — {e}")
    else:
        results.append("⚠️ OpenRouter — API key חסר")
    if db:
        try:
            db.table("whale_txs").select("id").limit(1).execute()
            results.append("✅ Supabase")
        except Exception as e:
            results.append(f"❌ Supabase — {e}")
    else:
        results.append("⚠️ Supabase — לא מחובר")
    try:
        news = fetch_news(max_items=1)
        results.append(f"✅ RSS News — {len(news)} פריטים")
    except Exception as e:
        results.append(f"❌ RSS — {e}")
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    msg = f"🔧 <b>סטטוס שירותים</b> ({now})\n\n" + "\n".join(results)
    await update.message.reply_html(msg)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if not question:
        return
    await update.message.reply_text("💭 חושב...")
    context = get_market_context()
    answer = ask_ai(question, context=context)
    if len(answer) > 4000:
        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i+4000])
    else:
        await update.message.reply_text(answer)


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.error(f"שגיאה: {ctx.error}", exc_info=ctx.error)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not TELEGRAM_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN לא מוגדר ב-.env")
        return

    # הפעל Flask health server בthread נפרד
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    log.info(f"מפעיל בוט עם מודל: {OPENROUTER_MODEL}")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("funding", cmd_funding))
    app.add_handler(CommandHandler("whales", cmd_whales))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    log.info("✅ בוט פעיל — מחכה להודעות...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
