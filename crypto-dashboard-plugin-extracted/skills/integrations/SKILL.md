---
name: integrations
description: >
  TradingView and Telegram integration for the crypto dashboard.
  Triggers on: "TradingView", "טלגרם", "חיבור ל", "webhook", "alerts from TradingView", "Telegram bot commands", "pine script".
---

# Integrations — TradingView + Telegram

## TradingView Integration

### אפשרות א׳ — Charts embed בדשבורד (הכי פשוט, חינם)

מטמיע את גרפי TradingView ישירות בדשבורד — בלי API, בלי הרשמה.

**Lovable prompt:**
```
Add TradingView charts to the Dashboard tab.

Use TradingView's free embeddable widget (no API key needed).
Add two chart widgets:

1. Full-width chart at the bottom of Dashboard tab:
<div class="tradingview-widget-container">
  <div id="tradingview_chart"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
    new TradingView.widget({
      container_id: "tradingview_chart",
      symbol: "BINANCE:BTCUSDT",
      interval: "15",
      theme: "dark",
      style: "1",
      locale: "en",
      toolbar_bg: "#1a1a1a",
      enable_publishing: false,
      hide_side_toolbar: false,
      allow_symbol_change: true,
      height: 500,
      width: "100%"
    });
  </script>
</div>

2. Add a symbol selector above the chart: BTC | ETH | SOL | BNB | custom input
   When user clicks a symbol, update the chart (change TradingView widget symbol).
```

### אפשרות ב׳ — TradingView Webhooks → הבוט סוחר (Pro feature)

TradingView יכול לשלוח webhook כשאינדיקטור מוצא סיגנל. הבוט מקבל את ה-webhook וסוחר.

**דורש TradingView Pro ($14.95/מ׳) — סמן ב-PAYMENTS_NEEDED.md ומשתמשים בחלופה חינמית לעכשיו.**

**Pine Script alert → Render webhook:**
```javascript
// Pine Script (TradingView) — הוסף alert condition:
//@version=5
strategy("Whale Signal", overlay=true)

// דוגמה: RSI oversold
rsi = ta.rsi(close, 14)
longCondition = ta.crossover(rsi, 30)

if longCondition
    strategy.entry("Long", strategy.long)
    alert('{"action":"BUY","symbol":"' + syminfo.ticker + '","price":"' + str.tostring(close) + '"}', alert.freq_once_per_bar)
```

**Render endpoint לקבלת TradingView alerts (הוסף ל-copy_bot.py):**
```python
from flask import Flask, request, jsonify
import hmac, hashlib

app = Flask(__name__)
TV_SECRET = os.getenv("TRADINGVIEW_SECRET", "my-secret-key")

@app.route("/webhook/tradingview", methods=["POST"])
def tradingview_webhook():
    # אמת שהבקשה מ-TradingView
    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400
    
    action = data.get("action")  # BUY or SELL
    symbol = data.get("symbol", "BTCUSDT")
    price = float(data.get("price", 0))
    
    settings = get_bot_settings()
    if not settings or not settings.get("is_active"):
        return jsonify({"status": "bot inactive"}), 200
    
    if action == "BUY":
        open_position(symbol, "BUY", settings["max_position_usd"])
        notify(f"📡 TradingView Signal: BUY {symbol} @ ${price:,.2f}")
    elif action == "SELL":
        open_position(symbol, "SELL", settings["max_position_usd"])
        notify(f"📡 TradingView Signal: SELL {symbol} @ ${price:,.2f}")
    
    return jsonify({"status": "executed"}), 200

# הרץ Flask בthread נפרד
def start_webhook_server():
    app.run(host="0.0.0.0", port=5000)

threading.Thread(target=start_webhook_server, daemon=True).start()
```

---

## Telegram Integration מלא

### התראות שכבר יש (מה-whale_monitor + copy_bot):
- 🐋 ארנק פתח פוזיציה גדולה
- 🤖 הבוט פתח/סגר עסקה
- 🚨 הבוט נעצר (daily loss limit)
- ⚠️ התראת drawdown

### להוסיף: פקודות Telegram לשליטה על הבוט

**הוסף ל-copy_bot.py — Telegram Command Handler:**
```python
from telegram.ext import Application, CommandHandler, ContextTypes

async def cmd_status(update, context):
    settings = get_bot_settings()
    open_trades = supabase.table("bot_trades").select("*").eq("status","open").execute().data
    
    status = "🟢 Active" if settings["is_active"] else "🔴 Inactive"
    mode = "📄 Paper" if settings["paper_mode"] else "💰 Live"
    
    msg = f"""
*Bot Status*
{status} | {mode}
Copying: {settings.get('copy_wallet_address','None')[:8]}...
Open positions: {len(open_trades)}
Max position: ${settings['max_position_usd']}
Daily loss limit: ${settings['max_daily_loss_usd']}
    """
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_stop(update, context):
    supabase.table("bot_settings").update({"is_active": False}).eq("id", 1).execute()
    await update.message.reply_text("🔴 Bot stopped.")

async def cmd_start_bot(update, context):
    supabase.table("bot_settings").update({"is_active": True}).eq("id", 1).execute()
    await update.message.reply_text("🟢 Bot started.")

async def cmd_pnl(update, context):
    trades = supabase.table("bot_trades").select("pnl").execute().data
    total = sum(t["pnl"] or 0 for t in trades)
    today_trades = [t for t in trades if t.get("created_at","").startswith(datetime.now().strftime("%Y-%m-%d"))]
    today = sum(t["pnl"] or 0 for t in today_trades)
    
    emoji = "📈" if total > 0 else "📉"
    await update.message.reply_text(
        f"{emoji} *P&L Report*\nToday: ${today:+.2f}\nTotal: ${total:+.2f}",
        parse_mode="Markdown"
    )

async def cmd_help(update, context):
    await update.message.reply_text("""
*Available Commands:*
/status — bot status & settings
/start\\_bot — activate bot  
/stop — deactivate bot
/pnl — profit & loss report
/positions — open positions
/help — this message
    """, parse_mode="Markdown")

# הוסף לפני run():
def start_telegram_bot():
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(CommandHandler("status", cmd_status))
    app_bot.add_handler(CommandHandler("stop", cmd_stop))
    app_bot.add_handler(CommandHandler("start_bot", cmd_start_bot))
    app_bot.add_handler(CommandHandler("pnl", cmd_pnl))
    app_bot.add_handler(CommandHandler("help", cmd_help))
    app_bot.run_polling()

threading.Thread(target=start_telegram_bot, daemon=True).start()
```

### פקודות Telegram שיהיו זמינות:

| פקודה | מה עושה |
|-------|---------|
| `/status` | סטטוס הבוט, מצב, פוזיציות פתוחות |
| `/start_bot` | מפעיל את הבוט |
| `/stop` | עוצר את הבוט מיידית |
| `/pnl` | דוח רווח/הפסד |
| `/positions` | פוזיציות פתוחות כרגע |
| `/help` | רשימת פקודות |

---

## Lovable prompt — Telegram status in dashboard

```
Add a Telegram connection status indicator to the top bar.

- Small icon: 🤖 Telegram
- Green dot if bot is connected and responding
- Shows last message sent time
- Click → opens modal with "Recent Telegram Activity" (last 5 alerts sent)

Data: add telegram_last_ping timestamp to bot_settings table,
updated every time the bot sends a message.
```
