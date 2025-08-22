from binance.spot import Spot
from binance.um_futures import UMFutures
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
import pandas as pd

class BinanceSpot:
    def __init__(self, key: str, secret: str, testnet: bool = True):
        base_url = "https://testnet.binance.vision" if testnet else None
        self.client = Spot(api_key=key, api_secret=secret, base_url=base_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(1, 3))
    def klines(self, symbol: str, interval: str = "15m", limit: int = 300) -> pd.DataFrame:
        raw = self.client.klines(symbol, interval, limit=limit)
        cols = ["open_time","open","high","low","close","volume",
                "close_time","qav","ntrades","tbbv","tbqav","ignore"]
        df = pd.DataFrame(raw, columns=cols)
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(1, 3))
    def top_usdt_symbols(self, min_volume_usdt: float = 5_000_000, limit: int = 30):
        tickers = self.client.ticker_24hr()
        # Filter USDT pairs, exclude stable/stable and leveraged tokens
        def ok(sym):
            return sym.endswith("USDT") and not any(x in sym for x in ["UPUSDT","DOWNUSDT","BULLUSDT","BEARUSDT"])
        filtered = [t for t in tickers if ok(t["symbol"])]
        # Sort by quoteVolume desc
        filtered.sort(key=lambda x: float(x.get("quoteVolume", 0.0)), reverse=True)
        result = []
        for t in filtered[:max(limit, 1)]:
            if float(t.get("quoteVolume", 0.0)) >= min_volume_usdt:
                result.append(t["symbol"])
        return result or ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT"]

    def market_buy_quote(self, symbol: str, quote_qty: float):
        return self.client.new_order(symbol=symbol, side="BUY", type="MARKET", quoteOrderQty=str(quote_qty))

    def market_sell_base(self, symbol: str, qty: float):
        return self.client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=str(qty))

    def balances(self):
        return self.client.account().get("balances", [])

class BinanceFutures:
    def __init__(self, key: str, secret: str, testnet: bool = True):
        base_url = "https://testnet.binancefuture.com" if testnet else None
        self.client = UMFutures(key=key, secret=secret, base_url=base_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(1, 3))
    def klines(self, symbol: str, interval: str = "15m", limit: int = 300) -> pd.DataFrame:
        raw = self.client.klines(symbol=symbol, interval=interval, limit=limit)
        cols = ["open_time","open","high","low","close","volume",
                "close_time","qav","ntrades","tbbv","tbqav","ignore"]
        df = pd.DataFrame(raw, columns=cols)
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df

    def market_long(self, symbol: str, qty: float):
        return self.client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=str(qty))

    def market_short(self, symbol: str, qty: float):
        return self.client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=str(qty))

    def set_leverage(self, symbol: str, leverage: int = 3):
        try:
            return self.client.change_leverage(symbol, leverage)
        except Exception as e:
            return {"error": str(e)}