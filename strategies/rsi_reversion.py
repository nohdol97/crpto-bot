import pandas as pd
from core.indicators import rsi

def signal(df: pd.DataFrame, low: int = 30, high: int = 70, period: int = 14):
    df = df.copy()
    df["rsi"] = rsi(df["close"], period)
    val = df["rsi"].iloc[-1]
    return {"buy": val <= low, "sell": val >= high, "rsi": float(val)}