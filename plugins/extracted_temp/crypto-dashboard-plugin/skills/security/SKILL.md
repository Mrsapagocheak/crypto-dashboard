---
name: security
description: >
  Security checklist and code patterns for protecting API keys, exchange permissions, and the dashboard.
  Triggers on: "אבטחה", "security", "API key בטוח", "הגנה", "מישהו יכול לגנוב", "הרשאות", "permissions", "לפני כסף אמיתי", "secure".
---

# Security — הגנה על הפרויקט

## הרץ את הצ'קליסט הזה לפני שמפעילים כסף אמיתי

---

## 1. API Keys — כללי זהב

**לעולם לא:**
- לשמור API key בתוך קוד Python (גם לא כ-comment)
- לעלות `.env` ל-GitHub
- לשתף `.env` בשום מקום
- לתת ל-Lovable גישה ל-Binance API key (הוא frontend בלבד)

**תמיד:**
```bash
# ודא ש-.env ב-.gitignore לפני כל push
echo ".env" >> ~/crypto-dashboard/bots/.gitignore
echo "*.env" >> ~/crypto-dashboard/bots/.gitignore

# בדוק שלא עלה בטעות
git log --all --full-history -- .env
# אם מחזיר תוצאות — המפתחות חשופים! בטל אותם מיד בבורסה
```

---

## 2. Binance / Bybit — הרשאות מינימליות

**הגדר את ה-API key בצורה הזו בלבד:**

| הרשאה | מצב | למה |
|-------|-----|-----|
| Enable Reading | ✅ כן | קריאת מחירים ויתרות |
| Enable Spot Trading | ✅ כן | פתיחת עסקאות |
| Enable Futures | ✅ רק אם סוחרים futures | |
| Enable Withdrawals | ❌ לעולם לא | אם גנבו את ה-key — לא יכולים להוציא כסף |
| IP Restriction | ✅ מומלץ | הגבל ל-IP של Render |

**איך לקבל IP של Render:**
```
render.com → Service → Logs → תראה את ה-outbound IP
הגדר ב-Binance: API → Edit → Restrict access to trusted IPs only
```

---

## 3. Supabase — הגבלת גישה

**Row Level Security (RLS) — הפעל על טבלאות רגישות:**
```sql
-- הפעל RLS על bot_settings (רק המשתמש שלך יכול לשנות)
alter table bot_settings enable row level security;

create policy "owner only" on bot_settings
  for all using (auth.uid() = 'YOUR_USER_ID');

-- bot_trades — קריאה בלבד מה-frontend
alter table bot_trades enable row level security;

create policy "read only frontend" on bot_trades
  for select using (true);

create policy "write only backend" on bot_trades
  for insert using (auth.role() = 'service_role');
```

**שני סוגי keys ב-Supabase:**
- `anon key` → ב-Lovable (frontend) — גישה מוגבלת לפי RLS
- `service_role key` → בבוטים Python (backend) — גישה מלאה, **לעולם לא ב-frontend**

---

## 4. Lovable Dashboard — הגנת Login

**ודא שיש:**
```
- Login page עם Supabase Auth ✅
- Redirect לדשבורד רק אחרי auth ✅
- Session timeout (Supabase ברירת מחדל: 1 שעה) ✅
```

**הוסף ל-Lovable prompt אם חסר:**
```
Add route protection to all dashboard pages.
If user is not authenticated, redirect to /login.
Use Supabase onAuthStateChange to detect session changes.
Add a logout button in the top bar.
```

---

## 5. Render — משתני סביבה בטוחים

**לעולם לא ב-render.yaml:**
```yaml
# ❌ לא ככה:
envVars:
  - key: BINANCE_API_KEY
    value: abc123secret  # חשוף ב-GitHub!

# ✅ ככה (sync: false = ידני דרך ממשק Render):
envVars:
  - key: BINANCE_API_KEY
    sync: false
```

---

## 6. בדיקת חשיפה — הרץ לפני deploy

```python
# security_check.py — הרץ לפני כל deploy
import os, re, sys

SENSITIVE_PATTERNS = [
    r'[A-Za-z0-9]{64}',           # Binance secret
    r'[0-9]{10}:[A-Za-z0-9_-]{35}', # Telegram token
    r'eyJ[A-Za-z0-9_-]{100,}',    # Supabase JWT
]

FILES_TO_CHECK = ['whale_monitor.py', 'copy_bot.py', 'render.yaml']

issues = []
for fname in FILES_TO_CHECK:
    if not os.path.exists(fname):
        continue
    content = open(fname).read()
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, content):
            issues.append(f"⚠️  {fname} אולי מכיל secret hardcoded!")

if issues:
    print("\n".join(issues))
    print("\nבדוק את הקבצים לפני push!")
    sys.exit(1)
else:
    print("✅ לא נמצאו secrets hardcoded")
```

**הוסף ל-.github/workflows (רץ אוטומטית לפני כל push):**
```yaml
name: Security Check
on: [push]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python security_check.py
```

---

## 7. אם חשדת שנגנב API key

**פעולות מיידיות לפי סדר:**
1. **Binance/Bybit** → בטל את ה-API key מיד (Account → API Management → Delete)
2. **Telegram** → שלח `/revoke` ל-@BotFather
3. **Supabase** → Settings → API → Reset anon key
4. **Etherscan** → My Profile → API Keys → Delete
5. צור כל המפתחות מחדש
6. עדכן ב-Render Environment Variables
7. בדוק bot_trades ו-whale_transactions — האם יש פעילות חשודה?
