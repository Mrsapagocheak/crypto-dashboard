---
name: setup-guide
description: >
  Complete setup checklist before starting the project. Knows exactly what accounts, keys, and costs are needed.
  Triggers on: "מה צריך להקים", "לפני שמתחילים", "setup", "מה עולה כסף", "אילו חשבונות", "checklist", "10 דקות להתחיל", "מה צריך".
---

# Setup Guide — מה צריך לפני שמתחילים

## הצג את זה בתחילת כל פרויקט חדש

---

## ✅ חשבונות חינמיים — פתח לפני הכל

| שירות | למה צריך | קישור | זמן פתיחה |
|-------|---------|-------|-----------|
| **Lovable.dev** | בונה את ממשק הדשבורד | lovable.dev | 2 דקות |
| **Supabase.com** | מסד הנתונים | supabase.com | 2 דקות |
| **GitHub.com** | שמירת קוד הבוטים | github.com | 2 דקות |
| **Render.com** | הרצת הבוטים 24/7 | render.com | 2 דקות |
| **UptimeRobot.com** | שומר הבוטים ערים | uptimerobot.com | 1 דקה |

---

## 🔑 API Keys — כולם חינמיים

### 1. Etherscan API Key
- כנס ל: etherscan.io → My Profile → API Keys → Create
- שמור ב-`.env` תחת: `ETHERSCAN_API_KEY=`

### 2. CoinGlass API Key
- כנס ל: coinglass.com → API → Free Plan
- שמור ב-`.env` תחת: `COINGLASS_API_KEY=`

### 3. CryptoPanic API Key
- כנס ל: cryptopanic.com/developers/api → Get Free Key
- שמור ב-`.env` תחת: `CRYPTOPANIC_API_KEY=`

### 4. Telegram Bot Token
- פתח Telegram → חפש `@BotFather`
- שלח: `/newbot`
- בחר שם לבוט (לדוגמה: `MyCryptoDashboardBot`)
- BotFather ישלח לך token בפורמט: `1234567890:ABCdef...`
- שמור ב-`.env` תחת: `TELEGRAM_BOT_TOKEN=`

### 5. Telegram Chat ID (ה-ID שלך)
- פתח Telegram → חפש `@userinfobot`
- שלח כל הודעה → הוא יחזיר את ה-ID שלך
- שמור ב-`.env` תחת: `TELEGRAM_CHAT_ID=`

### 6. Binance או Bybit API Key
- **Binance**: Account → API Management → Create API
  - הפעל: Enable Reading ✅ + Enable Spot & Margin Trading ✅
  - **אל תפעיל**: Enable Withdrawals ❌
  - שמור: `BINANCE_API_KEY=` ו-`BINANCE_API_SECRET=`
- **Bybit**: Account → API → Create New Key (אותו עיקרון)

---

## 💳 מה עולה כסף — ומתי

### לא צריך לשלם כדי להתחיל

הפרויקט כולו רץ בחינם בהתחלה. תשלום רלוונטי רק אם:

| מצב | עלות | מתי נדרש |
|-----|------|---------|
| Lovable watermark מפריע | $25/חודש | רק אם רוצים לוגו נקי |
| CoinGlass חורג מ-free tier | $49/חודש | רק אם צריך היסטוריה ארוכה |
| TradingView Webhooks | $14.95/חודש | רק אם רוצים סיגנלים אוטומטיים |
| Render עולה על 750 שעות | $7/חודש | רק אם מריצים 3+ בוטים |
| **Trading בכסף אמיתי** | **$0 עלות** אבל **$X סיכון** | רק אחרי paper trading שבוע |

### סדר עדיפויות אם רוצים לשלם:
1. קודם כל — TradingView Pro (מוסיף webhooks לסיגנלים)
2. אחר כך — Lovable Pro (מסיר watermark)
3. רק אז — CoinGlass Pro (אם צריך יותר נתונים)

---

## 📋 `.env` — תבנית מלאה

Cowork ייצור את הקובץ הזה אוטומטית ב-`~/crypto-dashboard/.env`.
**המשתמש ממלא את הערכים בעצמו — לעולם לא לשתף קובץ זה.**

```
# Database
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Crypto Data
ETHERSCAN_API_KEY=
COINGLASS_API_KEY=
CRYPTOPANIC_API_KEY=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Exchange (בחר אחד)
BINANCE_API_KEY=
BINANCE_API_SECRET=
# או:
BYBIT_API_KEY=
BYBIT_API_SECRET=

# Optional
TRADINGVIEW_SECRET=my-secret-key
OPENROUTER_API_KEY=
```

---

## ⏱️ כמה זמן עד שהכל עובד?

| שלב | מה קורה | זמן |
|-----|---------|-----|
| פתיחת חשבונות | ידני — המשתמש עושה | ~15 דקות |
| Phase 0–1 | Cowork בונה תשתית + UI | ~2–3 שעות |
| Phase 2 | חיבור נתונים חיים | ~1 יום |
| Phase 3 | Whale tracker עובד | ~2–3 ימים |
| Phase 4 | Copy bot בנייר | ~1 שבוע |
| **Live trading** | **אחרי שבוע paper trading** | **שבוע 6–7** |

**אם רוצים להתחיל תוך 10 דקות:**
1. פתח Lovable.dev + Supabase (2 דקות כל אחד)
2. פתח @BotFather ב-Telegram → צור בוט (2 דקות)
3. קח Chat ID מ-@userinfobot (1 דקה)
4. מלא `.env` עם הטוקנים
5. הגד ל-Cowork: "תתחיל לעבוד" — הוא עושה את השאר
