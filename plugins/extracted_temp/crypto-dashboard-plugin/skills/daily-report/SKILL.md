---
name: daily-report
description: >
  Automated daily morning report sent to Telegram: bot performance, whale activity, market overview.
  Triggers on: "דוח יומי", "סיכום בוקר", "daily report", "כל בוקר", "סיכום יומי", "מה קרה אתמול", "report".
---

# Daily Report — סיכום בוקר אוטומטי

## מה נשלח כל בוקר ב-8:00

```
📊 Daily Report — [תאריך]

💰 הבוט אתמול:
  P&L: +$47.30 (+2.1%)
  עסקאות: 3 פתח | 2 סגר
  Win rate: 67% (2/3)
  
🐋 הוויל שלך (0x1a2b...):
  פעולות: 2
  • קנה ETH $82,000 ב-22:14
  • מכר SOL $15,000 ב-23:45

📈 שוק:
  BTC: $67,420 (+1.2%)
  ETH: $3,841 (-0.4%)
  Liquidations 24h: $312M
  Funding (BTC): +0.01%
  Fear & Greed: 72 (Greed)

⚡ לתשומת לבך:
  • הבוט הפסיד 2 עסקאות רצופות
  • הוויל פתח פוזיציה גדולה חדשה

/status | /pnl | /positions
```

---

## קוד — daily_report.py

```python
import os
from datetime import datetime, timedelta
from supabase import create_client
from telegram import Bot
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def get_yesterday():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def get_bot_summary():
    yesterday = get_yesterday()
    trades = supabase.table("bot_trades") \
        .select("*") \
        .gte("created_at", yesterday) \
        .lt("created_at", datetime.now().strftime("%Y-%m-%d")) \
        .execute().data
    
    if not trades:
        return {"pnl": 0, "opened": 0, "closed": 0, "wins": 0, "total_closed": 0}
    
    closed = [t for t in trades if t["status"] == "closed"]
    wins = [t for t in closed if (t.get("pnl") or 0) > 0]
    total_pnl = sum(t.get("pnl") or 0 for t in closed)
    opened = len([t for t in trades if t["status"] == "open"])
    
    return {
        "pnl": round(total_pnl, 2),
        "opened": len(trades),
        "closed": len(closed),
        "wins": len(wins),
        "total_closed": len(closed),
        "win_rate": round(len(wins) / len(closed) * 100) if closed else 0
    }

def get_whale_summary():
    yesterday = get_yesterday()
    txs = supabase.table("whale_transactions") \
        .select("*") \
        .gte("created_at", yesterday) \
        .order("timestamp", desc=True) \
        .execute().data
    
    return txs[:5]  # אחרונות 5 פעולות

def get_market_data():
    try:
        # BTC + ETH מחיר
        prices = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true",
            timeout=5
        ).json()
        
        btc = prices.get("bitcoin", {})
        eth = prices.get("ethereum", {})
        
        # Fear & Greed
        fg = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5).json()
        fg_value = fg["data"][0]["value"]
        fg_class = fg["data"][0]["value_classification"]
        
        return {
            "btc_price": btc.get("usd", 0),
            "btc_change": round(btc.get("usd_24h_change", 0), 1),
            "eth_price": eth.get("usd", 0),
            "eth_change": round(eth.get("usd_24h_change", 0), 1),
            "fg": f"{fg_value} ({fg_class})"
        }
    except:
        return {"btc_price": 0, "btc_change": 0, "eth_price": 0, "eth_change": 0, "fg": "N/A"}

def get_alerts(bot_summary, whale_txs):
    alerts = []
    
    # 2 הפסדים רצופים
    recent = supabase.table("bot_trades") \
        .select("pnl") \
        .eq("status", "closed") \
        .order("created_at", desc=True) \
        .limit(3) \
        .execute().data
    
    if len(recent) >= 2 and all((t.get("pnl") or 0) < 0 for t in recent[:2]):
        alerts.append("⚠️ הבוט הפסיד 2 עסקאות רצופות")
    
    # פוזיציה גדולה של הוויל
    big_txs = [t for t in whale_txs if (t.get("usd_value") or 0) > 100000]
    if big_txs:
        alerts.append(f"🐋 הוויל פתח פוזיציה גדולה: ${big_txs[0]['usd_value']:,.0f}")
    
    # win rate נמוך
    if bot_summary["total_closed"] >= 5 and bot_summary["win_rate"] < 40:
        alerts.append(f"📉 Win rate נמוך: {bot_summary['win_rate']}%")
    
    return alerts

async def send_daily_report():
    bot_data = get_bot_summary()
    whale_txs = get_whale_summary()
    market = get_market_data()
    alerts = get_alerts(bot_data, whale_txs)
    
    # בניית ההודעה
    date_str = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    
    pnl_sign = "+" if bot_data["pnl"] >= 0 else ""
    pnl_emoji = "💚" if bot_data["pnl"] >= 0 else "🔴"
    btc_emoji = "📈" if market["btc_change"] >= 0 else "📉"
    eth_emoji = "📈" if market["eth_change"] >= 0 else "📉"
    
    msg = f"📊 *Daily Report — {date_str}*\n\n"
    
    msg += f"💰 *הבוט אתמול:*\n"
    msg += f"  {pnl_emoji} P&L: {pnl_sign}${bot_data['pnl']}\n"
    msg += f"  עסקאות: {bot_data['opened']} פתח | {bot_data['closed']} סגר\n"
    if bot_data["total_closed"] > 0:
        msg += f"  Win rate: {bot_data['win_rate']}%\n"
    
    if whale_txs:
        msg += f"\n🐋 *הוויל אתמול ({len(whale_txs)} פעולות):*\n"
        for tx in whale_txs[:3]:
            time_str = datetime.fromtimestamp(tx.get("timestamp", 0)).strftime("%H:%M")
            msg += f"  • {tx.get('action','?')} {tx.get('token','?')} ${tx.get('usd_value',0):,.0f} ב-{time_str}\n"
    
    msg += f"\n{btc_emoji} *שוק:*\n"
    msg += f"  BTC: ${market['btc_price']:,.0f} ({'+' if market['btc_change']>=0 else ''}{market['btc_change']}%)\n"
    msg += f"  ETH: ${market['eth_price']:,.0f} ({'+' if market['eth_change']>=0 else ''}{market['eth_change']}%)\n"
    msg += f"  Fear & Greed: {market['fg']}\n"
    
    if alerts:
        msg += f"\n⚡ *לתשומת לבך:*\n"
        for alert in alerts:
            msg += f"  {alert}\n"
    
    msg += f"\n/status | /pnl | /positions"
    
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=msg,
        parse_mode="Markdown"
    )
    print(f"Daily report sent: {date_str}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(send_daily_report())
```

---

## הגדרת שליחה אוטומטית כל בוקר

### אפשרות א׳ — GitHub Actions (חינם, מומלץ)

```yaml
# .github/workflows/daily-report.yml
name: Daily Report
on:
  schedule:
    - cron: '0 6 * * *'  # 8:00 שעון ישראל (UTC+2) = 06:00 UTC
  workflow_dispatch:       # גם אפשר להריץ ידנית

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install supabase python-telegram-bot requests
      - run: python daily_report.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

**הוסף secrets ב-GitHub:**
`Settings → Secrets → Actions → New secret` — אותם ערכים מ-.env

### אפשרות ב׳ — Render Cron Job

```yaml
# ב-render.yaml הוסף:
  - type: cron
    name: daily-report
    env: python
    schedule: "0 6 * * *"
    buildCommand: pip install -r requirements.txt
    startCommand: python daily_report.py
```

---

## Cowork — מה לעשות

1. צור `~/crypto-dashboard/bots/daily_report.py` עם הקוד למעלה
2. צור `.github/workflows/daily-report.yml`
3. הוסף Secrets ב-GitHub repo
4. דחוף ל-GitHub
5. בדוק: Actions → Run workflow ידנית → ודא שמגיע בטלגרם
6. עדכן PROGRESS.md
