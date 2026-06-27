---
name: lovable-builder
description: >
  Knows exactly what prompts to send to Lovable.dev for each phase of the crypto dashboard.
  Triggers on: "תכתוב פרומפט ללובבל", "מה לכתוב ב-Lovable", "lovable prompt", "שלב X ב-Lovable".
---

# Lovable Builder — Exact Prompts Per Phase

When operating Lovable via Chrome, copy-paste these prompts exactly. After each prompt, wait for Lovable to finish generating before sending the next one.

---

## PHASE_1_PROMPT — Initial Dashboard Shell

```
Build a private crypto intelligence dashboard with the following structure:

AUTHENTICATION:
- Login page with email/password (Supabase Auth)
- Only one authorized user (my email)
- Redirect to dashboard after login

MAIN LAYOUT:
- Dark theme (#0f0f0f background, #1a1a1a cards)
- Left sidebar navigation with 5 tabs:
  1. 📊 Dashboard (home)
  2. 🐋 Whale Tracker
  3. ⚡ Liquidations
  4. 🤖 Copy Bot
  5. 📰 News & Trends
- Top bar: current time (UTC), connection status dot (green/red)

DASHBOARD TAB (home):
- 4 metric cards at top: BTC Price, ETH Price, Total Liquidations 24h, Market Sentiment
- Funding Rates table: columns = Exchange | Symbol | Rate | 1h Change
- Open Interest chart: line chart, last 24 hours, BTC and ETH
- All data shows placeholder/mock data for now — we'll connect APIs later

TECH STACK:
- React + TypeScript
- Supabase for database and auth
- Recharts for charts
- Tailwind CSS
- shadcn/ui components

Make it look professional, like a Bloomberg terminal but cleaner.
```

---

## PHASE_2_LIQUIDATIONS_PROMPT

```
Add real-time liquidations feed to the Liquidations tab.

Connect to CoinGlass WebSocket API for live liquidation data.
API endpoint: wss://open-api-ws.coinglass.com/public/v1 (requires API key from env)

LIQUIDATIONS TAB:
- Live feed table that auto-updates (WebSocket):
  Columns: Time | Exchange | Symbol | Side (Long/Short) | Size (USD) | Price
  - Red row = Long liquidated
  - Green row = Short liquidated
  - Show last 100 liquidations
  - Auto-scroll to newest
- Summary bar above table:
  - Total longs liquidated (1h): $X
  - Total shorts liquidated (1h): $X  
  - Biggest single liquidation: $X
- Filter buttons: All | BTC | ETH | SOL | >$100k only

Store API key in Supabase secrets as COINGLASS_API_KEY.
```

---

## PHASE_3_WHALE_TRACKER_PROMPT

```
Build the Whale Tracker tab.

WHALE TRACKER TAB:

Search section:
- Input field: "Enter wallet address (ETH/BSC)"
- "Add to Watchlist" button
- Shows wallet label if it's a known exchange/fund

Watchlist table:
- Columns: Label | Address (truncated) | Last Activity | Total Volume 30d | Actions
- "Remove" button per row
- Click row → opens detail view

Wallet Detail View (slide-in panel from right):
- Wallet address + copy button
- Timeline chart: position size over time (last 30 days)
- Transactions table:
  Columns: Date | Action | Token | Size | USD Value | TX Hash (link)
  - Green = Buy/Open Long
  - Red = Sell/Open Short
- PnL estimate if calculable

Alert settings (per wallet):
- Toggle: "Alert when opens position > $___"
- Send alert to: Telegram

Data comes from a Python backend that writes to Supabase table `whale_transactions`.
Frontend just reads from Supabase in real-time using Supabase realtime subscriptions.
```

---

## PHASE_4_COPY_BOT_PROMPT

```
Build the Copy Bot tab.

COPY BOT TAB:

Status card at top:
- Big ON/OFF toggle switch (saves to Supabase settings table)
- Current status: "Active — copying [wallet name]" or "Inactive"
- Today's P&L from bot trades

Settings panel:
- "Wallet to copy" dropdown (from watchlist)
- "Position size" slider: 1% to 100% of their size (default 10%)
- "Max position size" input: max $X per trade (default $500)
- "Allowed tokens" multi-select: BTC, ETH, SOL, BNB, or All
- "Save Settings" button → writes to Supabase

Trade log table:
- Columns: Time | Token | Action | Size | Entry Price | Exit Price | P&L | Status
- Status: Open (yellow) / Closed (green/red)
- Filter: Today / This Week / All Time
- Export CSV button

Risk warning banner (always visible when bot is ON):
"⚠️ Bot is active. Monitor your positions. Past performance does not guarantee future results."
```

---

## PHASE_5_NEWS_PROMPT

```
Build the News & Trends tab.

NEWS & TRENDS TAB:

Left column (60%): News Feed
- Cards with: headline, source, time ago, sentiment badge (Bullish/Bearish/Neutral)
- Data from CryptoPanic API (CRYPTOPANIC_API_KEY in Supabase secrets)
- Filter buttons: All | BTC | ETH | DeFi | NFT | Regulation
- Auto-refresh every 5 minutes

Right column (40%): Trending
- "Top Movers" table: Symbol | Price | 24h % | Volume 24h
  - Green = up, Red = down
  - Sort by: % change or volume
- "Hot Topics" word cloud or tag list (from news headlines)
- "Fear & Greed Index" widget (from alternative.me API, free)

Make news cards clickable — opens original article in new tab.
```
