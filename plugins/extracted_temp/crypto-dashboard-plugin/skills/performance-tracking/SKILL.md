---
name: performance-tracking
description: >
  Knows how to build full bot performance tracking: P&L realtime, bot vs whale comparison, drawdown alerts.
  Triggers on: "ביצועי הבוט", "P&L", "כמה הרוויח", "השוואה לוויל", "drawdown", "התראת הפסד", "performance", "bot results".
---

# Performance Tracking — מעקב ביצועים מלא

## 3 רבדים של מעקב

### 1. P&L בזמן אמת

**Lovable prompt — Performance Tab:**
```
Add a Performance tab to the dashboard.

PERFORMANCE TAB:

Summary cards (top row):
- Total P&L: $X (green if positive, red if negative)
- Today's P&L: $X
- Win Rate: X% (winning trades / total trades)
- Total Trades: X

Equity curve chart:
- Line chart showing cumulative P&L over time
- X axis: date, Y axis: USD profit/loss
- Baseline at $0 (dashed line)
- Fill green above zero, red below zero
- Time range selector: 1D / 1W / 1M / All

Open positions table:
- Columns: Symbol | Side | Entry | Current | P&L $ | P&L % | Duration
- Auto-refreshes every 30 seconds from Supabase

Closed trades table:
- Columns: Symbol | Side | Entry | Exit | P&L $ | P&L % | Date
- Filter: Today / This Week / All Time
- Sort by: Date / P&L / Symbol
- Export CSV button

Data source: Supabase bot_trades table (real-time subscription)
```

**Python — P&L calculator (הוסף ל-copy_bot.py):**
```python
def update_trade_pnl(trade_id, current_price):
    trade = supabase.table("bot_trades").select("*").eq("id", trade_id).execute().data[0]
    if trade["status"] != "open":
        return
    
    entry = trade["entry_price"]
    size = trade["usd_size"]
    side = trade["action"]
    
    if side == "BUY":
        pnl = (current_price - entry) / entry * size
    else:
        pnl = (entry - current_price) / entry * size
    
    pnl_pct = pnl / size * 100
    
    supabase.table("bot_trades").update({
        "current_price": current_price,
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2)
    }).eq("id", trade_id).execute()
```

---

### 2. השוואה: הבוט vs הוויל המקורי

**הרעיון:** לכל עסקה שהבוט פתח, נשמור גם את מה שהוויל עשה באותה עסקה. בסוף נשווה: האם העתקה השתלמה?

**הוסף לטבלת bot_trades:**
```sql
alter table bot_trades add column whale_entry_price float;
alter table bot_trades add column whale_exit_price float;
alter table bot_trades add column whale_pnl_pct float;
alter table bot_trades add column copy_pnl_pct float;
alter table bot_trades add column outperformed boolean;
```

**Lovable prompt — Comparison widget:**
```
Add a "Bot vs Whale" comparison widget to the Performance tab.

COMPARISON WIDGET:
- Table: Trade | Bot P&L% | Whale P&L% | Difference | Result
  - Green "✓ Better" if bot > whale
  - Red "✗ Worse" if bot < whale
- Summary: "Bot outperformed whale in X% of trades"
- Bar chart: side-by-side bars, Bot (blue) vs Whale (purple) per trade

Note: whale data comes from bot_trades.whale_pnl_pct column
```

---

### 3. התראות הפסד — Drawdown Protection

**ב-copy_bot.py — הוסף drawdown monitor:**
```python
MAX_DAILY_LOSS_USD = 200      # עצור אם הפסדנו יותר מ-$200 היום
MAX_SINGLE_LOSS_PCT = 5       # סגור פוזיציה אם הפסד > 5%
DRAWDOWN_ALERT_PCT = 3        # התראה ב-3% הפסד

def check_drawdown():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # סכום הפסדים של היום
    result = supabase.table("bot_trades") \
        .select("pnl") \
        .eq("status", "closed") \
        .gte("created_at", today) \
        .execute()
    
    daily_pnl = sum(t["pnl"] or 0 for t in result.data)
    
    if daily_pnl < -MAX_DAILY_LOSS_USD:
        # עצור הכל
        supabase.table("bot_settings").update({"is_active": False}).eq("id", 1).execute()
        telegram.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"🚨 BOT STOPPED\nDaily loss limit hit: ${abs(daily_pnl):.0f}\nBot deactivated automatically.\nCheck dashboard to reactivate."
        )
        return False
    
    if daily_pnl < -(MAX_DAILY_LOSS_USD * 0.7):
        # התראה מוקדמת
        telegram.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"⚠️ Drawdown Warning\nToday's loss: ${abs(daily_pnl):.0f} / ${MAX_DAILY_LOSS_USD}\nApproaching daily limit."
        )
    
    return True

def check_position_loss(trade_id, current_pnl_pct):
    if current_pnl_pct < -MAX_SINGLE_LOSS_PCT:
        close_position(trade_id, reason="stop_loss")
        telegram.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"🛑 Stop Loss Hit\nPosition closed at {current_pnl_pct:.1f}%"
        )

# הוסף ב-run() loop:
if not check_drawdown():
    time.sleep(60)
    continue
```

**Lovable prompt — Risk dashboard:**
```
Add risk metrics to the Performance tab.

RISK SECTION:
- Daily P&L progress bar: shows today's loss vs max allowed ($200)
  - Green: 0-50% of limit
  - Yellow: 50-80% of limit  
  - Red: 80-100% of limit
  - "BOT STOPPED" badge if limit hit
- Max drawdown (all time): X%
- Longest losing streak: X trades
- Sharpe ratio (if enough data): X
- Settings button: "Edit risk limits" → opens modal to change MAX_DAILY_LOSS and MAX_SINGLE_LOSS_PCT
  → saves to Supabase bot_settings table
```

---

## Supabase — עמודות נוספות לטבלאות

```sql
-- הוסף ל-bot_trades
alter table bot_trades add column current_price float;
alter table bot_trades add column pnl float default 0;
alter table bot_trades add column pnl_pct float default 0;
alter table bot_trades add column whale_entry_price float;
alter table bot_trades add column whale_pnl_pct float;
alter table bot_trades add column close_reason text; -- 'stop_loss' | 'whale_closed' | 'manual'

-- הוסף ל-bot_settings  
alter table bot_settings add column max_daily_loss_usd float default 200;
alter table bot_settings add column max_single_loss_pct float default 5;
alter table bot_settings add column total_pnl float default 0;
```
