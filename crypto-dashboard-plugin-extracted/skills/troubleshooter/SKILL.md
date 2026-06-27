---
name: troubleshooter
description: >
  Diagnoses and fixes common problems in the crypto dashboard project. Knows every error pattern and its solution.
  Triggers on: "יש שגיאה", "לא עובד", "error", "נתקעתי", "בעיה", "failed", "crash", "לא מתחבר", "לא מקבל", "למה", "fix", "debug".
---

# Troubleshooter — אבחון ופתרון בעיות

## פרוטוקול אבחון

כשיש בעיה:
1. קרא את `~/crypto-dashboard/ERRORS.md`
2. בדוק לוגים ב-Render dashboard
3. הצלב עם הטבלה למטה
4. נסה את הפתרון
5. אם עדיין לא עובד — נסה את הפתרון החלופי
6. אם שניהם נכשלו — תעד ב-ERRORS.md ושלח למשתמש

---

## שגיאות נפוצות ופתרונות

### 🔴 Supabase

**שגיאה:** `Invalid API key` / `JWT expired`
```
פתרון: בדוק שה-SUPABASE_KEY ב-.env הוא ה-anon key (לא service role key)
מיקום: supabase.com → Project Settings → API → anon/public
```

**שגיאה:** `relation "whale_transactions" does not exist`
```
פתרון: הטבלאות לא נוצרו עדיין
פעולה: הרץ את ה-SQL מתוך crypto-data skill → Supabase SQL Editor
```

**שגיאה:** `row-level security policy`
```
פתרון: RLS חוסם כתיבה
פעולה: supabase.com → Table Editor → [table] → RLS → Disable RLS (לפרויקט פרטי זה בסדר)
```

---

### 🔴 Telegram

**בעיה:** הבוט לא שולח הודעות
```
בדוק:
1. שלחת /start לבוט שלך לפחות פעם אחת? (חובה לפני שהוא יכול לשלוח)
2. TELEGRAM_CHAT_ID נכון? בדוק מ-@userinfobot
3. TELEGRAM_BOT_TOKEN נכון? העתק שוב מ-BotFather

בדיקה מהירה:
curl "https://api.telegram.org/bot[TOKEN]/sendMessage?chat_id=[CHAT_ID]&text=test"
אם מחזיר {"ok":true} — הטוקנים נכונים
```

**בעיה:** פקודות Telegram לא עובדות (`/status` לא מגיב)
```
פתרון: הבוט רץ ב-polling mode — בדוק שה-thread של Telegram רץ
בדוק ב-Render logs: אם רואה "Application.run_polling()" — זה עובד
אם לא — הוסף print("Starting Telegram polling...") לפני run_polling()
```

---

### 🔴 Render / Bot Hosting

**בעיה:** הבוט "נרדם" ומפסיק לעבוד
```
פתרון א: UptimeRobot לא מוגדר — הגדר monitor ל-/health endpoint
פתרון ב: הוסף health endpoint לבוט (ראה bot-hosting skill)
```

**בעיה:** `ModuleNotFoundError: No module named 'xyz'`
```
פתרון: הוסף את החבילה ל-requirements.txt ו-push מחדש
pip freeze > requirements.txt
git add requirements.txt && git commit -m "add deps" && git push
```

**בעיה:** `Environment variable not found`
```
פתרון: המשתנה לא הוזן ב-Render
מיקום: render.com → Service → Environment → Add Environment Variable
הוסף את כל המשתנים מ-.env
```

**בעיה:** בוט מתרסק כל כמה דקות
```
בדוק Render logs → מצא שורת השגיאה האחרונה לפני ה-crash
הוסף try/except רחב סביב הלולאה הראשית:
while True:
    try:
        [קוד הבוט]
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)  # המתן ונסה שוב
```

---

### 🔴 Lovable / Frontend

**בעיה:** Lovable מייצר UI שנראה שגוי / לא מה שביקשנו
```
פתרון: שלח prompt תיקון ספציפי:
"The [element] looks wrong. Fix it so that: [תיאור מדויק של מה שרוצים]
Keep everything else unchanged."
נסה עד 2 פעמים — אם עדיין לא עובד, עבור לפרומפט הבא בתור
```

**בעיה:** Lovable לא מצליח לחבר Supabase
```
פתרון:
1. ב-Lovable: Settings → Supabase → Disconnect → Connect again
2. ודא שה-Supabase project פעיל (לא paused — supabase מפסיק פרויקטים חינמיים אחרי 7 ימים ללא שימוש)
3. אם paused: supabase.com → Resume project
```

**בעיה:** הדשבורד לא מציג נתונים חיים
```
בדוק לפי סדר:
1. API key נכון ב-Supabase Secrets? (Lovable → Settings → Secrets)
2. הטבלה קיימת ב-Supabase ויש בה נתונים? (בדוק ב-Table Editor)
3. ה-Supabase Realtime מופעל? (Database → Replication → Tables → הפעל עבור הטבלה)
4. Console errors בדפדפן? (F12 → Console)
```

---

### 🔴 Binance / Exchange API

**שגיאה:** `APIError(code=-2015): Invalid API-key`
```
פתרון: 
1. בדוק שהעתקת את המפתח נכון (ללא רווחים)
2. ודא שה-IP שלך מורשה — ב-Binance API settings: "Unrestricted" לפיתוח
3. ודא שה-API key לא נמחק — Binance מוחק keys לא פעילים
```

**שגיאה:** `APIError(code=-1021): Timestamp out of sync`
```
פתרון: שעון המחשב/שרת לא מסונכרן
על Render: זה נדיר — אם קורה, restart את ה-service
מקומית: sudo ntpdate pool.ntp.org
```

**שגיאה:** `APIError(code=-2010): Insufficient balance`
```
פתרון: אין מספיק USDT בחשבון
בדוק: הסכום ב-max_position_usd קטן מהיתרה הזמינה?
```

---

### 🔴 Etherscan / On-chain

**שגיאה:** `Max rate limit reached`
```
פתרון: חרגת מ-5 req/sec של free tier
הוסף time.sleep(0.2) בין קריאות לארנקים שונים
אם יש הרבה ארנקים במעקב — עבור לסריקה כל 2 דקות במקום 1
```

**בעיה:** ארנק לא מציג עסקאות
```
בדוק:
1. הכתובת נכונה? (42 תווים, מתחיל ב-0x)
2. זה ארנק ETH? (Etherscan = ETH בלבד)
3. יש עסקאות בכלל? בדוק ב-etherscan.io/address/[address]
4. אם הארנק על Binance Smart Chain — צריך bscscan.com API (שונה)
```

---

### 🔴 Python כללי

**שגיאה:** `Import error` בכל חבילה
```
# ודא requirements.txt מעודכן:
pip freeze > requirements.txt
# חבילות חובה:
supabase>=2.0.0
python-telegram-bot>=20.0
requests>=2.28.0
python-binance>=1.0.17
flask>=3.0.0
```

**בעיה:** `.env` לא נטען
```
הוסף לתחילת כל סקריפט:
from dotenv import load_dotenv
load_dotenv()
# וב-requirements.txt: python-dotenv>=1.0.0
```

---

## בעיות שדורשות התערבות משתמש

אם אחד מאלה קורה — עצור ושלח הודעה למשתמש:

| בעיה | מה לכתוב למשתמש |
|------|----------------|
| Supabase project paused | "Supabase הפסיק את הפרויקט (חינמי → pause אחרי 7 ימים). כנס ל-supabase.com → Resume Project." |
| Render free tier נגמר | "הגענו ל-750 שעות חינמי ב-Render החודש. אפשרויות: 1) חכה לחודש הבא. 2) שדרג ל-$7/מ׳. 3) עבור ל-Railway." |
| Exchange API נוצר מחדש | "נראה שה-Binance API key השתנה. צור key חדש ועדכן ב-Render Environment Variables." |
| Telegram bot נחסם | "הבוט נחסם. צור בוט חדש ב-@BotFather ועדכן TELEGRAM_BOT_TOKEN." |

---

## לוג שגיאות — פורמט סטנדרטי

כשנתקלים בשגיאה שלא נפתרת, שמור כך ב-`~/crypto-dashboard/ERRORS.md`:

```markdown
## [תאריך] — [שם הקובץ/שירות]

**שגיאה:**
[העתק את ה-error message המלא]

**הקשר:**
[מה עשינו כשזה קרה]

**ניסיון 1:**
[מה ניסינו] → [תוצאה]

**ניסיון 2:**
[מה ניסינו] → [תוצאה]

**סטטוס:** OPEN / RESOLVED
```
