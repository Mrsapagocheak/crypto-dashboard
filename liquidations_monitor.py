"""
liquidations_monitor.py — מעקב חיסולים בזמן אמת
מקור: Binance WebSocket (חינמי, ללא API key)
שומר לטבלת Supabase: liquidations
"""

import asyncio
import json
import os
from datetime import datetime, timezone

import websockets
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
WS_URL = os.getenv("BINANCE_WS_LIQUIDATIONS", "wss://fstream.binance.com/ws/!forceOrder@arr")

# סף מינימלי לשמירה (בדולרים) — מסנן רעש
MIN_USD_VALUE = 10_000


def parse_liquidation(raw: dict) -> dict | None:
    """ממיר הודעת WebSocket לפורמט הטבלה"""
    try:
        o = raw.get("o", {})
        usd_value = float(o.get("q", 0)) * float(o.get("p", 0))

        if usd_value < MIN_USD_VALUE:
            return None

        return {
            "symbol": o.get("s", ""),           # e.g. "BTCUSDT"
            "side": o.get("S", ""),              # "BUY" = short liquidated, "SELL" = long liquidated
            "quantity": float(o.get("q", 0)),
            "price": float(o.get("p", 0)),
            "usd_value": round(usd_value, 2),
            "exchange": "binance",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"[liquidations] שגיאת parse: {e}")
        return None


async def listen(supabase_client=None):
    """מאזין ל-WebSocket ושומר חיסולים ל-Supabase"""
    db = supabase_client or create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"[liquidations] מתחבר ל-{WS_URL}")

    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                print("[liquidations] מחובר ✅")
                async for message in ws:
                    data = json.loads(message)
                    row = parse_liquidation(data)
                    if row:
                        try:
                            db.table("liquidations").insert(row).execute()
                            side_label = "LONG" if row["side"] == "SELL" else "SHORT"
                            print(
                                f"[liquidations] {side_label} {row['symbol']} "
                                f"${row['usd_value']:,.0f}"
                            )
                        except Exception as e:
                            print(f"[liquidations] שגיאת Supabase: {e}")
        except Exception as e:
            print(f"[liquidations] ניתוק, מנסה שוב בעוד 5s: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(listen())
