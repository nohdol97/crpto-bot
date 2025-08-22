import asyncio
import logging
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from config import cfg
from utils.state import get_state, set_state
from exchange.binance_client import BinanceSpot, BinanceFutures
from core.scanner import scan_symbols
from core.trader import run_auto_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Clients
spot = BinanceSpot(cfg.binance_api_key, cfg.binance_api_secret, cfg.binance_testnet)
fut = BinanceFutures(cfg.futures_api_key, cfg.futures_api_secret, cfg.futures_testnet) if cfg.enable_futures else None

# Universe
DEFAULT_UNIVERSE = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","LTCUSDT","LINKUSDT","AVAXUSDT","TRXUSDT","MATICUSDT","NEARUSDT","ATOMUSDT","APTUSDT"]

# Helper funcs to connect spot by default
def fetch_klines(sym, interval):
    return spot.klines(sym, interval, 300)

def buy_market_quote(sym, quote):
    return spot.market_buy_quote(sym, quote)

def sell_market_qty(sym, qty):
    return spot.market_sell_base(sym, qty)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📊 스캔", callback_data="scan"),
         InlineKeyboardButton("⚙️ 설정", callback_data="settings")],
        [InlineKeyboardButton("▶️ 자동매매 시작", callback_data="auto_on"),
         InlineKeyboardButton("⏹️ 자동매매 중지", callback_data="auto_off")],
        [InlineKeyboardButton("ℹ️ 상태", callback_data="status")]
    ]
    await update.message.reply_text("안녕하세요! 자동매매 봇입니다. 아래 버튼으로 조작하세요.", reply_markup=InlineKeyboardMarkup(kb))

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "scan":
        await q.edit_message_text("스캔 중... 상위 유동성 USDT 마켓을 분석합니다.")
        syms = spot.top_usdt_symbols()
        df = scan_symbols(fetch_klines, syms, cfg.timeframe)
        set_state(scan_result=df.to_dict(orient="records"))

        # 추천 상위 5 표시
        top5 = df.head(5)
        lines = ["📊 *스캔 결과 (Top 5)*"]
        for _, r in top5.iterrows():
            reco = ", ".join(r.get("recommendations", []))
            lines.append(f"- *{r['symbol']}* | 점수 {r['score']:.1f} | ADX {r['adx']:.1f} | RSI {r['rsi']:.1f} | 추천: {reco}")
        lines.append("\n원하는 심볼을 선택하려면 /set <심볼> 을 입력하세요. 예: `/set BTCUSDT`")
        await q.edit_message_text("\n".join(lines), parse_mode="Markdown")

    elif data == "settings":
        s = get_state()
        text = (f"현재 선택 심볼: {s['selected_symbol']}\n"
                f"현재 전략: {s['selected_strategy']}\n"
                f"타임프레임: {cfg.timeframe}\n"
                f"거래 금액: {cfg.trade_usdt} USDT\n"
                f"TP/SL(ATR): {cfg.tp_atr}/{cfg.sl_atr}\n\n"
                "전략 변경: /strategy <sma_crossover|rsi_reversion|bb_breakout>\n"
                "심볼 변경: /set <SYMBOL> (예: /set BTCUSDT)")
        await q.edit_message_text(text)

    elif data == "auto_on":
        s = get_state()
        if s["auto_enabled"]:
            await q.edit_message_text("이미 자동매매가 실행 중입니다.")
            return
        set_state(auto_enabled=True)
        await q.edit_message_text("자동매매를 시작합니다. /status 로 상태 확인 가능.")
        # fire-and-forget task
        async def send_log(msg: str):
            try:
                await context.bot.send_message(chat_id=cfg.tg_chat_id or q.message.chat_id, text=msg)
            except Exception:
                pass

        async def get_flag():
            return get_state()["auto_enabled"]

        asyncio.create_task(run_auto_loop(
            fetch_klines, buy_market_quote, sell_market_qty,
            s["selected_symbol"], cfg.timeframe, cfg.trade_usdt, cfg.tp_atr, cfg.sl_atr,
            lambda: get_state()["auto_enabled"], send_log
        ))

    elif data == "auto_off":
        set_state(auto_enabled=False)
        await q.edit_message_text("자동매매를 중지했습니다.")

    elif data == "status":
        s = get_state()
        await q.edit_message_text(f"자동매매: {s['auto_enabled']}\n심볼: {s['selected_symbol']}\n전략: {s['selected_strategy']}")

async def cmd_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /set <SYMBOL>  예: /set BTCUSDT")
        return
    sym = context.args[0].upper()
    set_state(selected_symbol=sym)
    await update.message.reply_text(f"선택 심볼을 {sym} 로 설정했습니다.")

async def cmd_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /strategy <sma_crossover|rsi_reversion|bb_breakout>")
        return
    st = context.args[0]
    if st not in ["sma_crossover","rsi_reversion","bb_breakout"]:
        await update.message.reply_text("알 수 없는 전략입니다.")
        return
    set_state(selected_strategy=st)
    await update.message.reply_text(f"전략을 {st} 로 설정했습니다.")

def main():
    app = Application.builder().token(cfg.tg_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(CommandHandler("set", cmd_set))
    app.add_handler(CommandHandler("strategy", cmd_strategy))
    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()