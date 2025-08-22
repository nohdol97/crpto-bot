import pandas as pd
from core.indicators import bbands

def signal(df: pd.DataFrame, window: int = 20, num_std: float = 2.0, squeeze: float = 0.06):
    df = df.copy()
    up, mid, low, width = bbands(df["close"], window, num_std)
    df["up"], df["mid"], df["low"], df["width"] = up, mid, low, width
    buy = (df["close"].iloc[-1] > df["up"].iloc[-1]) and (df["width"].iloc[-2] < squeeze)
    sell = (df["close"].iloc[-1] < df["low"].iloc[-1]) and (df["width"].iloc[-2] < squeeze)
    return {"buy": bool(buy), "sell": bool(sell), "width": float(df["width"].iloc[-1])}