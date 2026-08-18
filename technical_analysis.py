"""
محاسبه شاخص‌های تکنیکال با pandas/numpy (بدون وابستگی به کتابخانه‌های بیرونی سنگین).
خروجی هر تابع یک عدد یا سری قابل استفاده در موتور امتیازدهی است.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=max(2, window // 2)).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=max(2, window // 2)).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def volatility(series: pd.Series, window: int = 30) -> float:
    """انحراف معیار بازده روزانه (سالانه‌شده) به‌عنوان معیار نوسان"""
    returns = series.pct_change().dropna()
    if len(returns) < 2:
        return 0.0
    return float(returns.rolling(window=min(window, len(returns))).std().iloc[-1] * np.sqrt(252) * 100)


def max_drawdown(series: pd.Series) -> float:
    cumulative_max = series.cummax()
    drawdown = (series - cumulative_max) / cumulative_max
    return float(drawdown.min() * 100)


def build_indicator_snapshot(df: pd.DataFrame) -> dict:
    """خلاصه‌ای از تمام شاخص‌های تکنیکال برای آخرین روز"""
    close = df["Close"].astype(float)
    sma20 = sma(close, 20)
    sma50 = sma(close, 50)
    ema12 = ema(close, 12)
    ema26 = ema(close, 26)
    rsi14 = rsi(close, 14)
    macd_line, signal_line, hist = macd(close)
    upper, mid, lower = bollinger_bands(close)

    last_close = float(close.iloc[-1])
    return {
        "last_close": last_close,
        "sma20": float(sma20.iloc[-1]) if not np.isnan(sma20.iloc[-1]) else last_close,
        "sma50": float(sma50.iloc[-1]) if not np.isnan(sma50.iloc[-1]) else last_close,
        "ema12": float(ema12.iloc[-1]),
        "ema26": float(ema26.iloc[-1]),
        "rsi": float(rsi14.iloc[-1]),
        "macd": float(macd_line.iloc[-1]),
        "macd_signal": float(signal_line.iloc[-1]),
        "macd_hist": float(hist.iloc[-1]),
        "bb_upper": float(upper.iloc[-1]) if not np.isnan(upper.iloc[-1]) else last_close,
        "bb_lower": float(lower.iloc[-1]) if not np.isnan(lower.iloc[-1]) else last_close,
        "volatility": volatility(close),
        "max_drawdown": max_drawdown(close),
    }
