---
name: bot-hosting
description: >
  Knows how to host Python bots 24/7 for free without a local machine or VPS.
  Triggers on: "איך הבוט ירוץ כשהמחשב כבוי", "bot hosting", "24/7", "שרת לבוט", "deploy bot", "render", "railway", "lovable hosting".
---

# Bot Hosting — 24/7 בחינם

## חשוב להבין: Lovable לא מריץ Python

Lovable מארח רק את ה-**frontend** (React). הוא לא יכול להריץ בוטים Python ברקע.
הבוטים צריכים שרת נפרד שרץ כל הזמן.

## אפשרויות חינמיות מדורגות

### 🥇 Render.com — הכי טוב לפרויקט זה (חינם)

**למה זה הבחירה:**
- Free tier: שירות רץ 24/7 (750 שעות/חודש = מספיק לבוט אחד)
- Deploy ישירות מ-GitHub — push קוד → הבוט עולה אוטומטית
- משתני סביבה (API keys) מוגנים בממשק
- לוגים בזמן אמת בדפדפן
- סיפורט WebSocket לחיבורים ארוכים

**מגבלה:** שירות free "נרדם" אחרי 15 דקות ללא בקשות — פתרון: הוסף `/health` endpoint שה-whale_monitor מחזיר 200, ו-UptimeRobot (חינם) יפנג אותו כל 10 דקות.

**Deploy process (Cowork יעשה את זה):**
```bash
# 1. צור GitHub repo
git init ~/crypto-dashboard/bots
git remote add origin https://github.com/YOUR_USERNAME/crypto-bots.git

# 2. צור requirements.txt
pip freeze > requirements.txt

# 3. צור render.yaml
cat > render.yaml << 'EOF'
services:
  - type: worker
    name: whale-monitor
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python whale_monitor.py
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: ETHERSCAN_API_KEY
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false

  - type: worker
    name: copy-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python copy_bot.py
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: BINANCE_API_KEY
        sync: false
      - key: BINANCE_API_SECRET
        sync: false
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID
        sync: false
EOF

# 4. push ל-GitHub
git add . && git commit -m "initial bot deploy" && git push

# 5. ב-render.com: New → Blueprint → חבר GitHub repo → הוסף env vars → Deploy
```

**Health check להוסיף ל-whale_monitor.py:**
```python
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): pass  # שקט בלוגים

def start_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    server.serve_forever()

# הוסף בתחילת main():
threading.Thread(target=start_health_server, daemon=True).start()
```

**UptimeRobot (חינם, שומר הבוט ער):**
1. הרשם ב-uptimerobot.com
2. New Monitor → HTTP(s)
3. URL: `https://whale-monitor.onrender.com/health`
4. Interval: 5 minutes

---

### 🥈 Railway.app — חלופה (free tier מוגבל יותר)

- $5 credit חינמי בחודש → מספיק לבוט קטן
- Deploy זהה ל-Render
- ממשק נוח יותר למתחילים

---

### 🥉 GitHub Actions — לסקריפטים לא-רציפים

לא מתאים לבוטים שרצים כל הזמן, אבל מתאים למשימות מתוזמנות:
```yaml
# .github/workflows/daily-report.yml
on:
  schedule:
    - cron: '0 8 * * *'  # כל יום ב-8:00
jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python generate_daily_report.py
```

---

## ארכיטקטורה מלאה אחרי Hosting

```
┌─────────────────────────────────────────┐
│         Lovable (Frontend)              │
│   Dashboard • Whale Tracker • Bot UI    │
└──────────────┬──────────────────────────┘
               │ קורא/כותב
               ▼
┌─────────────────────────────────────────┐
│         Supabase (Database)             │
│  whale_transactions • bot_trades        │
│  bot_settings • whale_watchlist         │
└──────┬──────────────────────┬───────────┘
       │ כותב                 │ קורא הגדרות
       ▼                      ▼
┌──────────────┐    ┌──────────────────────┐
│ whale_monitor│    │     copy_bot.py      │
│  (Render)    │    │     (Render)         │
│  רץ 24/7    │    │     רץ 24/7         │
└──────────────┘    └──────────────────────┘
       │                      │
       └──────────┬───────────┘
                  ▼
         Telegram Alerts
```

## Cowork — מה לעשות בשלב ה-Hosting

1. צור GitHub repo פרטי: `crypto-bots`
2. Push `whale_monitor.py` + `copy_bot.py` + `requirements.txt` + `render.yaml`
3. פתח render.com → Deploy from GitHub
4. הזן env vars (מה-`.env` הלוקלי)
5. הוסף UptimeRobot monitor
6. בדוק לוגים ב-Render אחרי 5 דקות — ודא הבוט רץ
7. עדכן PROGRESS.md: "בוטים על Render ✅"
