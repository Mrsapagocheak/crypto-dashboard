---
name: cowork-executor
description: >
  Rules for how to execute the crypto dashboard project autonomously in Cowork.
  Triggers on: "תתחיל לעבוד", "המשך", "עשה את השלב הבא", "start working", "execute next step".
---

# Cowork Executor — Autonomous Work Rules

## Core Principle

**Work fully autonomously. Never stop to ask for permission.**
The only exception: anything that costs money. For everything else — decide, act, move on.

---

## Session Start (always do this first)

1. Check if `~/crypto-dashboard/PROGRESS.md` exists
   - If not: create it, start Phase 0
   - If yes: read it, continue from last checkpoint
2. Say: "אני ב-Phase X, ממשיך מ-[last task]." — then immediately start working
3. Do not wait for a response. Begin.

---

## What Requires Zero Permission

Do all of the following without asking, without confirming, without pausing:

- Create, edit, move, or delete files and folders
- Write Python code, config files, SQL, scripts
- Open Chrome and navigate anywhere
- Log into sites (Lovable, Supabase, etc.) using saved credentials
- Create accounts on free-tier services
- Send prompts to Lovable and accept the generated code
- Connect Supabase to Lovable
- Create database tables, run SQL
- Set up Telegram bot (free)
- Register for free API keys (CoinGlass free, Etherscan free, CryptoPanic free)
- Run Python scripts locally
- Deploy bots in paper trading / test mode
- Fix errors and retry with a different approach
- Make technical decisions (library choice, architecture, data structure)
- Screenshot results
- Update PROGRESS.md

**If unsure whether something is free: check quickly, if it's free — proceed.**

---

## The ONLY Thing That Requires User Approval

💳 **Paying money when there is no free alternative.**

### Decision tree for every service or feature:

```
Is there a free tier or free alternative that works well enough?
  YES → use it. Don't mention it. Just proceed.
  NO  → note in PAYMENTS_NEEDED.md, skip, continue working on everything else.
```

### Always prefer free:
- Free tier of a paid service → use it
- Open source alternative → use it
- Mock/placeholder data until real API is available → use it
- Self-hosted option instead of paid SaaS → use it
- A slightly less polished solution that's free → use it

### Only flag as payment needed when:
- The free tier is fundamentally broken for this use case (e.g. 10 req/day when we need 1000)
- There is genuinely no free alternative anywhere
- The feature simply cannot be built without paying

**Do not stop mid-session for payments.** Instead:

1. Note it in `~/crypto-dashboard/PAYMENTS_NEEDED.md`
2. Build the best possible version using free tools
3. Continue with everything else
4. Report at end of session

---

## PAYMENTS_NEEDED.md Format

```
# Payments Needed — [date]

## 1. [Service Name]
- **What**: [e.g. CoinGlass Pro]
- **Why free tier isn't enough**: [e.g. Free = 100 req/day, we need ~2000/day for live updates]
- **Free alternatives tried**: [e.g. Binance public WebSocket — works for BTC/ETH but missing altcoins]
- **Current workaround**: [e.g. Using Binance WebSocket, missing 80% of altcoin data]
- **Cost to fix**: $49/month
- **Link**: [upgrade URL]
```

## FREE_ALTERNATIVES_USED.md Format

Also maintain this file so the user can see every free decision made:

```
# Free Alternatives Used

| Instead of | We used | Trade-off |
|------------|---------|-----------|
| Lovable Pro ($25/mo) | Lovable free tier | Has Lovable watermark on app |
| CoinGlass Pro ($49/mo) | Binance public WebSocket | Missing some altcoin liquidation data |
| Moralis Pro ($49/mo) | Etherscan free API | 5 req/sec limit, slightly slower whale updates |
| VPS hosting ($10/mo) | Run bots locally on your computer | Bots stop when computer is off |
```

---

## End-of-Session Summary

At the end of every work session, always send this:

```
✅ סיום סשן — [date]

הושלם:
- [task 1]
- [task 2]
- [task 3]

Phase הנוכחי: X / 5
---
🆓 החלטות חינמיות שעשיתי:
[paste FREE_ALTERNATIVES_USED.md table — what free tool was used instead of paid]

---
💳 רק אם אין אופציה חינמית — צריך אישורך:
[paste PAYMENTS_NEEDED.md, or "אין — הכל מכוסה בחינם 🎉"]

---
⏭️ בפעם הבאה: [next task]
```

---

## Error Handling

When something fails:
1. Try a different approach immediately — do not stop
2. If still failing after 2 tries: save to `~/crypto-dashboard/ERRORS.md`, skip the task, continue to the next one
3. Include the error in the end-of-session summary

Never stop the session because of a single error.

---

## Technical Decisions

Make all technical decisions independently. Examples:

- Which Python library to use → choose the most common/stable one
- Lovable generated ugly UI → send a correction prompt, accept the result
- API returns unexpected format → adapt the code
- Supabase table needs an extra column → add it
- Bot crashes → fix the bug and restart

Document decisions in PROGRESS.md under "Notes" so the user can review if curious.
