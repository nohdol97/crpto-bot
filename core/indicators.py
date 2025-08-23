import numpy as np
import pandas as pd

def sma(series: pd.Series, window: int):
    return series.rolling(window).mean()

def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=period - 1, adjust=False).mean()
    ma_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-12)
    return 100 - (100 / (1 + rs))

def bbands(series: pd.Series, window: int = 20, num_std: float = 2.0):
    ma = sma(series, window)
    sd = series.rolling(window).std()
    upper = ma + num_std * sd
    lower = ma - num_std * sd
    width = (upper - lower) / ma
    return upper, ma, lower, width

def atr(df: pd.DataFrame, period: int = 14):
    # expects columns: high, low, close
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def adx(df: pd.DataFrame, period: int = 14):
    high, low, close = df["high"], df["low"], df["close"]
    plus_dm = (high.diff().where(lambda x: x > 0, 0.0)).fillna(0.0)
    minus_dm = (-low.diff().where(lambda x: x < 0, 0.0)).fillna(0.0)
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    tr_smooth = tr.rolling(period).sum()
    plus_di = 100 * (plus_dm.rolling(period).sum() / tr_smooth.replace(0, np.nan))
    minus_di = 100 * (minus_dm.rolling(period).sum() / tr_smooth.replace(0, np.nan))
    dx = ( (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) ) * 100
    return dx.rolling(period).mean()

# Alias for compatibility
def calculate_atr(df: pd.DataFrame, period: int = 14):
    """Calculate Average True Range (ATR)"""
    return atr(df, period)