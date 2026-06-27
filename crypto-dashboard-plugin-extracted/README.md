# Crypto Dashboard Manager Plugin

Plugin for managing the full build of a personal crypto intelligence dashboard.

## What This Plugin Does

Gives Cowork complete knowledge of the project so it can work autonomously:
- Knows all 5 phases and every task within them
- Has exact prompts ready to paste into Lovable
- Has Python bot code ready to deploy
- Knows when to work independently vs when to pause for approval

## How to Use

Open Cowork and say any of:
- **"המשך פרויקט"** — continues from last checkpoint
- **"איפה אנחנו?"** — shows current status
- **"תתחיל לעבוד"** — begins/resumes autonomous execution
- **"מה הצעד הבא?"** — shows next task without executing

## Skills Included

| Skill | Purpose |
|-------|---------|
| project-manager | Master plan, phase tracker, approval gates |
| lovable-builder | Exact prompts to paste into Lovable per phase |
| crypto-data | API docs, Python bot code, Supabase SQL |
| cowork-executor | Rules for autonomous operation |

## Approval Gates (🔴)

Cowork will stop and wait at:
1. After Phase 0 — verify accounts and API keys are ready
2. After Phase 1 — confirm UI looks good before connecting live data
3. After Phase 2 — confirm live data working
4. After Phase 3 — confirm whale tracker working
5. Before live trading — MUST confirm paper trading tested first
6. Final — confirm all features working

## Requirements

- Claude Cowork (desktop app, any paid plan)
- Claude in Chrome extension enabled
- Accounts: Lovable.dev, Supabase.com, CoinGlass, Etherscan, Telegram
- Exchange account: Binance or Bybit
