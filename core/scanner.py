import pandas as pd
from typing import List, Dict
from core.indicators import ema, rsi, bbands, atr, adx

def evaluate_symbol(df: pd.DataFrame) -> Dict:
    df = df.copy()
    df = df.tail(250)
    df["ema20"] = ema(df["close"], 20)
    df["ema50"] = ema(df["close"], 50)
    df["rsi"] = rsi(df["close"], 14)
    up, mid, low, width = bbands(df["close"], 20, 2.0)
    df["bb_width"] = width
    df["atr"] = atr(df, 14)
    df["adx"] = adx(df, 14)

    slope = (df["ema20"].iloc[-1] - df["ema20"].iloc[-5]) / 5.0
    momentum = df["close"].pct_change(20).iloc[-1]
    vol = df["bb_width"].iloc[-1]
    strength = df["adx"].iloc[-1]

    score = 0.0
    # 가중치 예시
    score += 2.0 * (1 if slope > 0 else -1)
    score += 2.0 * (1 if momentum > 0 else -1)
    score += 1.0 * (1 if strength >= 25 else -1)
    # 변동성은 너무 작아도/너무 커도 감점
    if 0.03 <= vol <= 0.12:
        score += 1.0
    else:
        score -= 1.0

    recommend = []
    if slope > 0 and strength >= 20:
        recommend.append("추세추종(SMA/EMA 크로스)")
    if vol < 0.06:
        recommend.append("돌파전략(볼린저 밴드 스퀴즈)")
    if df["rsi"].iloc[-1] < 33 or df["rsi"].iloc[-1] > 67:
        recommend.append("역추세(RSI 기반)")

    return {
        "score": float(score),
        "rsi": float(df["rsi"].iloc[-1]),
        "bb_width": float(vol),
        "adx": float(strength) if strength == strength else 0.0,
        "ema_slope": float(slope),
        "momentum_20": float(momentum),
        "recommendations": recommend or ["관망"],
    }

def scan_symbols(fetch_klines_func, symbols: List[str], interval: str = "15m") -> pd.DataFrame:
    rows = []
    for sym in symbols:
        try:
            df = fetch_klines_func(sym, interval)
            m = evaluate_symbol(df)
            rows.append({"symbol": sym, **m})
        except Exception as e:
            rows.append({"symbol": sym, "error": str(e), "score": -999})
    res = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    return res