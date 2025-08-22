import pandas as pd
from core.indicators import sma

def signal(df: pd.DataFrame, short: int = 20, long: int = 50):
    df = df.copy()
    df["sma_s"] = sma(df["close"], short)
    df["sma_l"] = sma(df["close"], long)
    df["diff"] = df["sma_s"] - df["sma_l"]
    df["cross"] = (df["diff"] > 0).astype(int).diff().fillna(0)
    # 1 = 골든크로스(매수), -1 = 데드크로스(매도)
    last_cross = int(df["cross"].iloc[-1]) if len(df) else 0
    trend_up = bool(df["diff"].iloc[-1] > 0)
    return {"buy": last_cross == 1, "sell": last_cross == -1, "trend_up": trend_up}