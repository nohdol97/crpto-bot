import asyncio, time
from typing import Callable, Dict
import pandas as pd
from core.indicators import atr
from strategies import sma_crossover, rsi_reversion, bb_breakout

STRATEGIES = {
    "sma_crossover": sma_crossover.signal,
    "rsi_reversion": rsi_reversion.signal,
    "bb_breakout": bb_breakout.signal,
}

async def run_auto_loop(
    fetch_klines: Callable,
    buy_market_quote: Callable,
    sell_market_qty: Callable,
    symbol: str,
    interval: str,
    trade_usdt: float,
    tp_atr: float,
    sl_atr: float,
    get_auto_flag: Callable,
    send_log: Callable,
):
    await send_log(f"자동매매 루프 시작: {symbol} ({interval}), {trade_usdt} USDT/트레이드")
    position_qty = 0.0
    entry_price = None

    while get_auto_flag():
        try:
            df = fetch_klines(symbol, interval)
            df = df.tail(200)
            # 기본 전략: SMA 크로스 + RSI 보조
            sig1 = STRATEGIES["sma_crossover"](df, 20, 50)
            sig2 = STRATEGIES["rsi_reversion"](df, 30, 70, 14)

            price = float(df["close"].iloc[-1])
            _atr = float(atr(df, 14).iloc[-1])

            if position_qty == 0.0:
                if sig1["buy"] or (sig2["buy"] and sig1["trend_up"]):
                    await send_log(f"매수 시그널 발생 @ {price:.2f}  (ATR={_atr:.2f})")
                    resp = buy_market_quote(symbol, trade_usdt)
                    entry_price = price
                    # 대략 수량 추정
                    position_qty = trade_usdt / price
                    await send_log(f"시장가 매수 실행: ~{position_qty:.6f} {symbol[:-4]}")
            else:
                tp = entry_price + tp_atr * _atr
                sl = entry_price - sl_atr * _atr
                if price >= tp:
                    await send_log(f"TP 도달({tp:.2f}) → 전량 매도")
                    sell_market_qty(symbol, position_qty)
                    position_qty = 0.0
                    entry_price = None
                elif price <= sl or sig1["sell"]:
                    await send_log(f"손절/크로스 다운 ({sl:.2f}) → 전량 매도")
                    sell_market_qty(symbol, position_qty)
                    position_qty = 0.0
                    entry_price = None

        except Exception as e:
            await send_log(f"에러: {e}")

        await asyncio.sleep(5)
    await send_log("자동매매 루프 종료")