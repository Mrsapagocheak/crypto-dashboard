"""
news_fetcher.py — שולף חדשות קריפטו מ-RSS חינמי
מקורות: CoinDesk + CoinTelegraph
אין צורך ב-API key
"""

import feedparser
import os
from datetime import datetime, timezone
from typing import Optional

RSS_FEEDS = {
    "coindesk": os.getenv("NEWS_RSS_COINDESK", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    "cointelegraph": os.getenv("NEWS_RSS_COINTELEGRAPH", "https://cointelegraph.com/rss"),
}

CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "defi", "nft",
    "binance", "coinbase", "altcoin", "blockchain", "web3", "solana",
    "liquidation", "whale", "bull", "bear", "market", "price",
]


def fetch_news(max_items: int = 10, keyword_filter: Optional[str] = None) -> list[dict]:
    """
    שולף חדשות מכל ה-RSS feeds.

    Args:
        max_items: מספר פריטים מקסימלי לכל מקור
        keyword_filter: סינון לפי מילת מפתח (אופציונלי)

    Returns:
        רשימת חדשות ממוינת לפי זמן (חדש → ישן)
    """
    all_news = []

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")

                # סינון לפי מילת מפתח אם נדרש
                if keyword_filter:
                    combined = (title + summary).lower()
                    if keyword_filter.lower() not in combined:
                        continue

                # המר זמן
                published = entry.get("published_parsed")
                if published:
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                else:
                    pub_dt = datetime.now(timezone.utc)

                all_news.append({
                    "source": source,
                    "title": title,
                    "summary": summary[:300] if summary else "",
                    "link": link,
                    "published": pub_dt.isoformat(),
                    "sentiment": detect_sentiment(title + " " + summary),
                })
        except Exception as e:
            print(f"[news_fetcher] שגיאה ב-{source}: {e}")

    # מיין לפי זמן — חדש קודם
    all_news.sort(key=lambda x: x["published"], reverse=True)
    return all_news


def detect_sentiment(text: str) -> str:
    """
    ניתוח sentiment פשוט לפי מילות מפתח.
    מחזיר: 'bullish', 'bearish', או 'neutral'
    """
    text_lower = text.lower()

    bullish_words = [
        "surge", "rally", "bull", "gain", "rise", "pump", "ath",
        "breakout", "adoption", "partnership", "approve", "approved",
        "soar", "jump", "high", "record", "growth",
    ]
    bearish_words = [
        "crash", "drop", "bear", "loss", "fall", "dump", "hack",
        "ban", "regulation", "sell", "fear", "low", "liquidation",
        "scam", "fraud", "collapse", "plunge", "decline",
    ]

    bullish_score = sum(1 for w in bullish_words if w in text_lower)
    bearish_score = sum(1 for w in bearish_words if w in text_lower)

    if bullish_score > bearish_score:
        return "bullish"
    elif bearish_score > bullish_score:
        return "bearish"
    return "neutral"


def format_for_telegram(news_items: list[dict], max_items: int = 5) -> str:
    """מפרמט חדשות לשליחה בטלגרם"""
    if not news_items:
        return "📰 אין חדשות כרגע"

    sentiment_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
    lines = ["📰 *חדשות קריפטו אחרונות*\n"]

    for item in news_items[:max_items]:
        emoji = sentiment_emoji.get(item["sentiment"], "⚪")
        source_tag = f"[{item['source'].upper()}]"
        lines.append(f"{emoji} {source_tag} {item['title']}")
        lines.append(f"🔗 {item['link']}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    print("מביא חדשות...")
    news = fetch_news(max_items=5)
    print(f"נמצאו {len(news)} פריטים\n")
    for item in news[:3]:
        print(f"[{item['source']}] {item['sentiment'].upper()} — {item['title']}")
        print(f"  {item['link']}\n")
