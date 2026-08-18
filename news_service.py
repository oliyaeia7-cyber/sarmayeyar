"""
سرویس اخبار و تحلیل احساسات ساده (Lexicon-based Sentiment).
منبع: فیدهای RSS (قابل تنظیم در config.py).
اگر بخواهید از یک مدل زبانی واقعی برای تحلیل عمیق‌تر استفاده کنید،
کافیست تابع analyze_sentiment را با یک فراخوانی API جایگزین کنید
(کلید AI_API_KEY در تنظیمات پیش‌بینی شده است).
"""
from __future__ import annotations
import re
from app.config import settings

try:
    import feedparser
except Exception:  # pragma: no cover
    feedparser = None

POSITIVE_WORDS = {
    "rally", "surge", "gain", "bullish", "growth", "profit", "record", "boost",
    "rise", "soar", "upgrade", "strong", "recovery", "optimis",
    "رشد", "صعود", "سود", "افزایش", "مثبت", "جهش", "بهبود", "امیدوار",
}
NEGATIVE_WORDS = {
    "crash", "plunge", "loss", "bearish", "decline", "sell-off", "selloff",
    "drop", "fall", "downgrade", "weak", "recession", "risk", "warning", "fear",
    "افت", "سقوط", "ریزش", "کاهش", "منفی", "بحران", "نگرانی", "ریسک",
}


def _score_text(text: str) -> int:
    text_l = text.lower()
    score = 0
    for w in POSITIVE_WORDS:
        if w in text_l:
            score += 1
    for w in NEGATIVE_WORDS:
        if w in text_l:
            score -= 1
    return score


def fetch_related_news(symbol: str, limit: int = 6) -> list[dict]:
    """اخبار مرتبط با نماد را واکشی و امتیاز احساسی هرکدام را محاسبه می‌کند."""
    items: list[dict] = []
    if feedparser is None:
        return items
    for feed_url in settings.NEWS_RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:8]:
                title = getattr(entry, "title", "")
                summary = re.sub("<[^<]+?>", "", getattr(entry, "summary", ""))
                sentiment = _score_text(title + " " + summary)
                items.append({
                    "title": title,
                    "link": getattr(entry, "link", "#"),
                    "published": getattr(entry, "published", ""),
                    "sentiment": sentiment,
                })
        except Exception:
            continue
    return items[:limit]


def news_sentiment_score(news_items: list[dict]) -> float:
    """میانگین امتیاز احساسی اخبار را به بازه ۰ تا ۱۰۰ نگاشت می‌کند (۵۰ = خنثی)."""
    if not news_items:
        return 50.0
    total = sum(item["sentiment"] for item in news_items)
    avg = total / len(news_items)
    # نگاشت تقریبی: هر واحد امتیاز ~ ۸ نمره جابه‌جایی از خنثی
    mapped = 50 + (avg * 8)
    return max(0.0, min(100.0, mapped))
