"""
موتور امتیازدهی سرمایه‌یار.

فلسفه طراحی: این سیستم هرگز فرمان قطعی «بخر» یا «بفروش» صادر نمی‌کند.
خروجی نهایی یک «امتیاز سرمایه‌یار» بین ۰ تا ۱۰۰ و سه سناریوی احتمالاتی
(صعودی / خنثی / نزولی) است که مجموع احتمالات آن‌ها همیشه ۱۰۰٪ می‌شود.

وزن‌دهی:
  - تحلیل تکنیکال (روند و مومنتوم)   -> ۴۵٪
  - اخبار و احساسات بازار            -> ۲۵٪
  - ارزیابی ریسک و نوسان             -> ۳۰٪  (ریسک بالا امتیاز را کم می‌کند)
"""
from __future__ import annotations
from dataclasses import dataclass, field

from app.services import market_data, technical_analysis as ta, news_service


@dataclass
class AnalysisResult:
    symbol: str
    is_demo: bool
    last_price: float
    daily_change: float
    indicators: dict
    news: list
    technical_score: float
    sentiment_score: float
    risk_score: float          # ۰=کم‌ریسک ... ۱۰۰=پرریسک
    final_score: float         # امتیاز نهایی سرمایه‌یار
    scenario_bullish: float
    scenario_neutral: float
    scenario_bearish: float
    risk_label: str
    verdict_label: str
    disclaimer: str = field(default=(
        "این خروجی صرفاً یک تحلیل آماری و احتمالاتی است و توصیه مالی قطعی "
        "محسوب نمی‌شود. تصمیم نهایی خرید یا فروش بر عهده شماست."
    ))


def _technical_score(ind: dict) -> float:
    """امتیاز روند/مومنتوم بین ۰ تا ۱۰۰ بر اساس موقعیت قیمت نسبت به میانگین‌ها،
    RSI و هیستوگرام MACD."""
    score = 50.0

    # روند: قیمت نسبت به SMA20 و SMA50
    if ind["last_close"] > ind["sma20"] > ind["sma50"]:
        score += 15
    elif ind["last_close"] > ind["sma20"]:
        score += 7
    elif ind["last_close"] < ind["sma20"] < ind["sma50"]:
        score -= 15
    elif ind["last_close"] < ind["sma20"]:
        score -= 7

    # RSI: خیلی اشباع خرید یا اشباع فروش را جریمه/تعدیل می‌کنیم
    rsi_v = ind["rsi"]
    if rsi_v >= 70:
        score -= 8   # اشباع خرید -> احتمال اصلاح
    elif rsi_v <= 30:
        score += 6   # اشباع فروش -> احتمال برگشت
    elif 45 <= rsi_v <= 60:
        score += 4   # ناحیه متعادل رو به رشد

    # MACD histogram
    if ind["macd_hist"] > 0 and ind["macd"] > ind["macd_signal"]:
        score += 10
    elif ind["macd_hist"] < 0 and ind["macd"] < ind["macd_signal"]:
        score -= 10

    return max(0.0, min(100.0, score))


def _risk_score(ind: dict) -> float:
    """امتیاز ریسک: نوسان سالانه‌شده و حداکثر افت از قله."""
    vol = ind["volatility"]  # درصد سالانه
    dd = abs(ind["max_drawdown"])  # درصد

    vol_component = min(100, vol / 0.9)     # نوسان ۹۰٪ سالانه یعنی حداکثر ریسک
    dd_component = min(100, dd * 2.2)

    risk = (vol_component * 0.6) + (dd_component * 0.4)
    return max(0.0, min(100.0, risk))


def _risk_label(risk_score: float) -> str:
    if risk_score < 30:
        return "ریسک پایین"
    if risk_score < 60:
        return "ریسک متوسط"
    return "ریسک بالا"


def _verdict_label(final_score: float) -> str:
    if final_score >= 70:
        return "دیدگاه مثبت با احتیاط"
    if final_score >= 55:
        return "کمی مثبت / نیازمند پایش"
    if final_score > 45:
        return "خنثی / بلاتکلیف"
    if final_score > 30:
        return "کمی منفی / نیازمند احتیاط"
    return "دیدگاه منفی با احتیاط"


def analyze(symbol: str) -> AnalysisResult:
    df, is_demo = market_data.get_price_history(symbol, period="6mo", interval="1d")
    indicators = ta.build_indicator_snapshot(df)
    last_price, daily_change, _ = market_data.get_last_price(symbol)

    news_items = news_service.fetch_related_news(symbol)
    sentiment = news_service.news_sentiment_score(news_items)
    technical = _technical_score(indicators)
    risk = _risk_score(indicators)

    # امتیاز نهایی: ریسک بالا از امتیاز مثبت می‌کاهد
    raw = (technical * 0.45) + (sentiment * 0.25) + ((100 - risk) * 0.30)
    final_score = max(0.0, min(100.0, raw))

    # ساخت سناریوهای احتمالاتی از روی امتیاز نهایی و ریسک (عدم قطعیت بیشتر => پخش شدن بیشتر احتمالات)
    # نگاشت ساده و پایدار به سه سناریو با جمع دقیق ۱۰۰
    bull_raw = max(1.0, final_score + (10 - risk / 10))
    bear_raw = max(1.0, (100 - final_score) + (10 - risk / 10))
    neutral_raw = max(1.0, 60 - abs(final_score - 50) * 0.6)
    total_raw = bull_raw + bear_raw + neutral_raw
    scenario_bullish = round(bull_raw / total_raw * 100, 1)
    scenario_bearish = round(bear_raw / total_raw * 100, 1)
    scenario_neutral = round(100 - scenario_bullish - scenario_bearish, 1)

    return AnalysisResult(
        symbol=symbol.upper(),
        is_demo=is_demo,
        last_price=last_price,
        daily_change=daily_change,
        indicators=indicators,
        news=news_items,
        technical_score=round(technical, 1),
        sentiment_score=round(sentiment, 1),
        risk_score=round(risk, 1),
        final_score=round(final_score, 1),
        scenario_bullish=scenario_bullish,
        scenario_neutral=scenario_neutral,
        scenario_bearish=scenario_bearish,
        risk_label=_risk_label(risk),
        verdict_label=_verdict_label(final_score),
    )
