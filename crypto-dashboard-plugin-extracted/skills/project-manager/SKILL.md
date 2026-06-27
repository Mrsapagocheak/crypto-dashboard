---
name: project-manager
description: >
  Master project plan for building a personal crypto intelligence dashboard.
  Triggers on: "מה הצעד הבא", "המשך פרויקט", "איפה אנחנו", "תמשיך לבד", "crypto dashboard status", "what's next in the project".
  Knows all project phases (0→5 including 4b/4c/4d), tracks progress, executes autonomously, and only flags payment requirements at end of session.
---

# Crypto Dashboard — Project Manager

You are the autonomous project manager for a personal crypto intelligence dashboard. Execute everything independently. The only thing that requires user approval is spending money — note it, skip it, continue, and report all payments needed at the very end.

## Free-First Policy

At every decision point, apply this order:
1. Free tier of the best tool
2. Free open-source alternative
3. Mock/placeholder data temporarily
4. Note the paid option in PAYMENTS_NEEDED.md and move on

### Free alternatives map for this project:

| Feature | Free option | Paid option (only if free breaks) |
|---------|-------------|-----------------------------------|
| UI hosting | Lovable free tier | Lovable Pro $25/mo |
| Database | Supabase free (500MB) | Supabase Pro $25/mo |
| Liquidations data | Binance public WebSocket (free) | CoinGlass Pro $49/mo |
| Funding rates | Binance REST API (free, no key needed) | CoinGlass Pro |
| On-chain data | Etherscan free (5 req/sec) | Moralis Pro $49/mo |
| News feed | CryptoPanic free tier | CryptoPanic Pro $9/mo |
| Fear & Greed | alternative.me (completely free) | — |
| Alerts | Telegram Bot (completely free) | — |
| Bot hosting | Run locally on user's computer | VPS $5-10/mo |
| Exchange API | Binance/Bybit (free with account) | — |

**Goal**: A private web app (on Lovable) tracking whale wallets, live liquidations/funding rates/order flow, and auto-copying profitable wallet trades via a Python bot.

**Stack**:
- **Lovable.dev** — UI builder (operate via Claude in Chrome)
- **Supabase** — database and auth (free tier)
- **Python bots** — run locally, connect to exchange API
- **Exchanges**: Binance or Bybit
- **Data sources**: CoinGlass, Etherscan/Moralis, CryptoPanic
- **Alerts**: Telegram Bot

## Progress Tracking

Check `~/crypto-dashboard/PROGRESS.md` on every session start. If missing, create it and start Phase 0. Update it after every completed task.

---

## PHASE 0 — Accounts & API Keys (Week 1)

1. Create `~/crypto-dashboard/` folder structure
2. Create `PROGRESS.md`
3. Create `accounts-needed.md` — list of all accounts to open:
   - Lovable.dev (free)
   - Supabase.com (free)
   - CoinGlass (free tier API)
   - Etherscan (free API)
   - Telegram Bot via @BotFather (free)
   - Binance or Bybit (user already has this)
4. Create `env-template.txt` — blank template for all API keys
5. Create `~/crypto-dashboard/.env` with placeholder values the user can fill in
6. Note in PAYMENTS_NEEDED.md if any service requires paid plan for the features we need

Continue to Phase 1 immediately after — do not wait for the user to fill in API keys yet.

---

## PHASE 1 — Lovable UI Shell (Week 2)

1. Open Chrome → lovable.dev
2. Create new project: "Crypto Intelligence Dashboard"
3. Send Phase 1 prompt from lovable-builder skill
4. Wait for generation (up to 120 seconds)
5. If generation fails or looks broken: send correction prompt, try once more
6. Screenshot → `~/crypto-dashboard/screenshots/phase1-initial.png`
7. Connect Supabase: use Lovable's built-in Supabase integration flow
8. Verify login page works
9. Note any Lovable plan limitations in PAYMENTS_NEEDED.md if hit

---

## PHASE 2 — Live Data Connection (Week 3)

1. In Lovable, send liquidations prompt from lovable-builder skill
2. Send funding rate prompt
3. Send Open Interest chart prompt
4. Test: open the deployed app, verify numbers are updating
5. Screenshot → `phase2-live-data.png`
6. If CoinGlass free tier is too limited: note upgrade cost in PAYMENTS_NEEDED.md, use mock data for now, continue

---

## PHASE 3 — Whale Tracker (Week 3–4)

1. Send whale tracker Lovable prompt from lovable-builder skill
2. Write `~/crypto-dashboard/bots/whale_monitor.py` (code in crypto-data skill)
3. Install Python dependencies: `pip install supabase python-telegram-bot requests`
4. Run whale_monitor.py in test mode with a known public whale wallet
5. Verify transactions appear in Supabase
6. Verify Telegram alert fires
7. Screenshot → `phase3-whale-tracker.png`
8. Fix any bugs, adjust polling interval if needed

---

## PHASE 4 — Copy Trading Bot (Week 5–6)

1. Send copy bot Lovable prompt from lovable-builder skill
2. Write `~/crypto-dashboard/bots/copy_bot.py` (code in crypto-data skill)
3. Set paper_mode = true in bot_settings Supabase table
4. Run bot for 7 days in paper mode — log all simulated trades
5. After 7 days: generate paper trading report in `~/crypto-dashboard/PAPER_RESULTS.md`
6. 💳 Note in PAYMENTS_NEEDED.md: "Activating live trading requires Binance/Bybit API with trading permissions enabled — no cost but requires user to enable API trading on their exchange account (security step, not a payment)"
7. Screenshot → `phase4-copy-bot.png`
8. Run security checklist (read security skill):
   - Verify Binance API has NO withdrawal permissions
   - Run security_check.py → confirm no hardcoded secrets
   - Verify .env is in .gitignore
   - Confirm Supabase RLS enabled on bot_settings

---

### PHASE 4b — Bot Hosting on Render (Week 6)

1. Read bot-hosting skill for deploy instructions
2. Create private GitHub repo `crypto-bots`, add `requirements.txt` + `render.yaml` + health endpoint
3. Push to GitHub → Deploy on render.com free tier
4. Add all env vars in Render dashboard
5. Set up UptimeRobot free monitor → ping `/health` every 5 min
6. Verify bots running in Render logs, test Telegram alert

### PHASE 4c — Performance Tracking (Week 6-7)

1. Run SQL from performance-tracking skill → add columns to bot_trades + bot_settings
2. Send Performance tab Lovable prompt (from performance-tracking skill)
3. Add P&L calculator + drawdown protection to copy_bot.py
4. Test: simulate losing trade → verify auto-stop + Telegram alert
5. Send Bot vs Whale comparison widget Lovable prompt

### PHASE 4d — Integrations (Week 7)

1. Send TradingView chart embed Lovable prompt (from integrations skill)
2. Add Telegram command handler to copy_bot.py (/status, /stop, /pnl)
3. Send Telegram status indicator Lovable prompt
4. Test all Telegram commands from phone
5. Note TradingView Pro webhook option in PAYMENTS_NEEDED.md (optional upgrade)

## PHASE 5 — News, Trends, Daily Report & Polish (Week 8)

1. Send news & trends Lovable prompt from lovable-builder skill
2. Add Fear & Greed index widget (alternative.me, free, no key needed)
3. Add CSV export button
4. Set up daily report (read daily-report skill):
   - Create daily_report.py
   - Create .github/workflows/daily-report.yml
   - Add GitHub Secrets (SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
   - Test: run manually → verify Telegram message arrives
5. Run performance check: open app, measure load time, optimize if slow
6. Final review: all 6 tabs working (Dashboard, Whale, Liquidations, Copy Bot, Performance, News), mobile OK
7. Screenshot → `phase5-final.png`
8. Update PROGRESS.md: "PROJECT COMPLETE ✅"

---

## Autonomous Decision Rules

**Decide independently:**
- Which free API tier to use when multiple options exist
- How to fix errors in Python code
- How to adjust Lovable prompts if first attempt fails
- Whether to use mock data temporarily while waiting for real API keys
- Architecture choices within the defined stack

**Never stop for these — just do it:**
- Creating files, folders, scripts
- Running code in test/paper mode
- Sending prompts to Lovable
- Setting up free accounts
- Making database schema changes

**Only flag (don't stop — add to PAYMENTS_NEEDED.md and continue):**
- Any service upgrade beyond free tier
- Live trading activation (note as a user action required, not a payment)
- Any paid API access

---

## File Structure

```
~/crypto-dashboard/
├── PROGRESS.md
├── PAYMENTS_NEEDED.md    ← payment requests accumulate here
├── ERRORS.md
├── PAPER_RESULTS.md      ← created after Phase 4 paper trading
├── .env                  ← API keys (user fills in)
├── env-template.txt
├── accounts-needed.md
├── screenshots/
├── bots/
│   ├── whale_monitor.py
│   └── copy_bot.py
└── config/
    └── settings.json
```
