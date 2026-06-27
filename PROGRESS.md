# PROGRESS — דשבורד קריפטו
**עודכן**: 2026-06-26

## מה הושלם

### שלב 1: תשתית ✅ (כמעט מלא)
- ✅ פתיחת חשבונות: Lovable, Supabase, GitHub, Telegram
- ✅ Supabase פרויקט חדש: `crypto-dashboard` (ref: `ohughnqhrwkejudtmwzx`, region: Tokyo)
- ✅ Telegram Bot Token: `8838739272:AAE2vjoudrTSUWA9df2TqXLkBVLFtFsV5GY`
- ✅ Telegram Chat ID: `7110726587`
- ✅ קובץ `.env` מלא עם Supabase URL + ANON_KEY + SERVICE_ROLE_KEY + Telegram
- ✅ קובץ `.gitignore` עם `.env`
- ✅ 4 טבלאות Supabase נוצרו + RLS מופעל:
  - `liquidations`
  - `whale_txs`
  - `positions`
  - `daily_reports`
- ✅ פלאגין `crypto-dashboard-manager` מותקן ב-Claude
- ✅ סקיל `lovable-optimizer` נוצר ומותקן

### חסר בשלב 1:
- ✅ GitHub repo: https://github.com/Mrsapagocheak/crypto-dashboard (קיים וריק)
- ⬜ API keys: Etherscan, CoinGlass, OpenRouter
- ✅ CryptoPanic — הוחלף ב-RSS חינמי (CoinDesk + CoinTelegraph), קובץ news_fetcher.py נוצר
- ✅ CoinGlass — הוחלף בחינמיים:
  - Liquidations: Binance WebSocket → liquidations_monitor.py
  - Funding Rates: Bybit REST API → funding_rates.py

## שלב נוכחי
**שלב 2: דשבורד ראשי (Lovable)**

הפרומפט הראשון מוכן ונכנס לשדה הטקסט של Lovable — אבל נגמרו credits.
Lovable מחלק credits חינמיים מדי יום — כשיהיו credits, אפשר לשלוח מיד.

## הצעד הבא

**כשה-credits יתחדשו ב-Lovable:**
1. פתח Lovable.dev
2. הפרומפט הראשון מוכן — שלח אותו (הוא ב-SKILL.md של lovable-builder)
3. המתן לבנייה (~2-3 דקות)
4. שלח פרומפט 2 (Liquidations component)
5. שלח פרומפט 3 (Whale Tracker)
6. שלח פרומפט 4 (Copy Bot UI)
7. שלח פרומפט 6 (חיבור Supabase)

**במקביל (לא דורש credits):**
- יצירת GitHub repo בשם `crypto-dashboard`
- השלמת API keys החסרים (Etherscan, CryptoPanic, OpenRouter)

## דברים שעולים כסף (כשיגיע הזמן)
- Lovable Pro: ~$25/חודש (נדרש אחרי מיצוי credits חינמיים)
- OpenRouter: ~$0.001/הודעה — הוסף $10 credit
- Render.com: חינמי (750 שעות/חודש)
- Supabase: חינמי (free tier)
