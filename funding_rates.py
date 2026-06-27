"""
funding_rates.py — שולף funding rates מ-Bybit
מקור: Bybit REST API (חינמי, ללא API key לקריאה בלבד)
"""

import os
from datetime import datetime, timezone

import requests

BYBIT_URL = os.getenv("BYBIT_FUNDING_URL", "https://api.bybit.com/v5/market/funding/history")

# מטבעות מעניינים לניטור
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]


def get_funding_rate(symbol: str, limit: int = 1) -> dict | None:
    """
    שולף funding rate נוכחי עבור סימבול.

    Returns:
        {symbol, rate, rate_pct, annualized_pct, timestamp} או None
    """
    try:
        resp = requests.get(
            BYBIT_URL,
            params={"category": "linear", "symbol": symbol, "limit": limit},
            timeout=10,
        )
        data = resp.json()
        if data.get("retCode") != 0:
            return None

        items = data.get("result", {}).get("list", [])
        if not items:
            return None

        latest = items[0]
        rate = float(latest.get("fundingRate", 0))

        return {
            "symbol": symbol,
            "rate": rate,
            "rate_pct": round(rate * 100, 4),          # e.g. 0.0100 → 0.01%
            "annualized_pct": round(rate * 3 * 365 * 100, 2),  # 3 fundings/day
            "timestamp": latest.get("fundingRateTimestamp"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"[funding] שגיאה ב-{symbol}: {e}")
        return None


def get_all_funding_rates(symbols: list[str] = None) -> list[dict]:
    """שולף funding rates לכל הסימבולים"""
    symbols = symbols or DEFAULT_SYMBOLS
    results = []
    for symbol in symbols:
        rate = get_funding_rate(symbol)
        if rate:
            results.append(rate)
    return results


def format_for_telegram(rates: list[dict]) -> str:
    """מפרמט funding rates לשליחה בטלגרם"""
    if not rates:
        return "📊 אין נתוני funding rate"

    lines = ["📊 *Funding Rates (Bybit)*\n"]
    for r in rates:
        # חיובי = longs משלמים לshorts (bearish pressure)
        # שלילי = shorts משלמים ללongs (bullish pressure)
        if r["rate_pct"] > 0.03:
            emoji = "🔴"  # גבוה מדי — longs בלחץ
        elif r["rate_pct"] < -0.01:
            emoji = "🟢"  # שלילי — shorts בלחץ
        else:
            emoji = "⚪"

        lines.append(
            f"{emoji} `{r['symbol']}`: {r['rate_pct']:+.4f}% "
            f"({r['annualized_pct']:+.1f}% שנתי)"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print("מביא funding rates...")
    rates = get_all_funding_rates()
    for r in rates:
        print(
            f"{r['symbol']}: {r['rate_pct']:+.4f}% "
            f"({r['annualized_pct']:+.1f}% שנתי)"
        )
