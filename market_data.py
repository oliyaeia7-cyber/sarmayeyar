"""
سرویس دریافت داده بازار.
منبع اصلی: yfinance (پوشش سهام آمریکایی/جهانی، ارز دیجیتال با پسوند -USD، فارکس، طلا).
برای نمادهایی که داده واقعی در دسترس نیست، از تولیدکننده داده نمایشی (Demo Data)
استفاده می‌شود تا کاربر همیشه خروجی ببیند و بعداً بتوانید آداپتور اختصاصی
(مثل TSETMC برای بورس ایران) اضافه کنید.
"""
from __future__ import annotations
import random
import time
from datetime import datetime, timedelta

import pandas as pd

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

_cache: dict[str, tuple[float, pd.DataFrame]] = {}
CACHE_TTL_SECONDS = 300


def _demo_dataframe(symbol: str, days: int = 180) -> pd.DataFrame:
    """داده نمایشی قطعی (seed بر اساس نماد) برای زمانی که داده واقعی در دسترس نیست."""
    seed = sum(ord(c) for c in symbol) or 1
    rng = random.Random(seed)
    price = 100 + (seed % 500)
    dates = [datetime.utcnow() - timedelta(days=days - i) for i in range(days)]
    rows = []
    drift = rng.uniform(-0.0015, 0.0025)
    for d in dates:
        shock = rng.gauss(0, 0.018)
        price *= max(0.5, 1 + drift + shock)
        high = price * (1 + abs(rng.gauss(0, 0.01)))
        low = price * (1 - abs(rng.gauss(0, 0.01)))
        vol = rng.uniform(1000, 50000)
        rows.append({"Date": d, "Open": price, "High": high, "Low": low,
                      "Close": price, "Volume": vol})
    df = pd.DataFrame(rows).set_index("Date")
    return df


def get_price_history(symbol: str, period: str = "6mo", interval: str = "1d") -> tuple[pd.DataFrame, bool]:
    """بازگرداندن (DataFrame قیمت، is_demo)"""
    key = f"{symbol}:{period}:{interval}"
    now = time.time()
    if key in _cache:
        ts, df = _cache[key]
        if now - ts < CACHE_TTL_SECONDS:
            return df, False

    if yf is not None:
        try:
            df = yf.Ticker(symbol).history(period=period, interval=interval)
            if df is not None and not df.empty and len(df) > 10:
                _cache[key] = (now, df)
                return df, False
        except Exception:
            pass

    return _demo_dataframe(symbol), True


def get_last_price(symbol: str) -> tuple[float, float, bool]:
    """قیمت آخر، درصد تغییر روزانه، آیا داده نمایشی است"""
    df, is_demo = get_price_history(symbol, period="5d", interval="1d")
    if len(df) < 2:
        return float(df["Close"].iloc[-1]), 0.0, is_demo
    last = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])
    change = ((last - prev) / prev) * 100 if prev else 0.0
    return round(last, 4), round(change, 2), is_demo
