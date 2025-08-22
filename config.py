from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Config:
    # Spot
    binance_api_key: str = os.getenv("BINANCE_API_KEY", "")
    binance_api_secret: str = os.getenv("BINANCE_API_SECRET", "")
    binance_testnet: bool = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

    # Futures
    enable_futures: bool = os.getenv("ENABLE_FUTURES", "false").lower() == "true"
    futures_api_key: str = os.getenv("BINANCE_FUTURES_API_KEY", "")
    futures_api_secret: str = os.getenv("BINANCE_FUTURES_API_SECRET", "")
    futures_testnet: bool = os.getenv("BINANCE_FUTURES_TESTNET", "true").lower() == "true"

    # Trading defaults
    base_asset: str = os.getenv("BASE_ASSET", "BTC")
    quote_asset: str = os.getenv("QUOTE_ASSET", "USDT")
    symbol: str = os.getenv("SYMBOL", "BTCUSDT")
    timeframe: str = os.getenv("TIMEFRAME", "15m")
    trade_usdt: float = float(os.getenv("TRADE_USDT", "50"))
    max_open_positions: int = int(os.getenv("MAX_OPEN_POSITIONS", "1"))
    risk_per_trade_pct: float = float(os.getenv("RISK_PER_TRADE_PCT", "0.01"))
    tp_atr: float = float(os.getenv("TAKE_PROFIT_ATR", "2.0"))
    sl_atr: float = float(os.getenv("STOP_LOSS_ATR", "1.5"))

    # Telegram
    tg_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

cfg = Config()