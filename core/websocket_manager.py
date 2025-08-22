"""
WebSocket manager for real-time Binance data streaming
"""

import json
import asyncio
import websockets
from typing import Dict, List, Callable, Optional
from datetime import datetime
import pandas as pd
from utils.logger import logger
from core.supabase_client import supabase_manager

class BinanceWebSocketManager:
    """Manage Binance WebSocket connections for real-time data"""
    
    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        self.base_url = "wss://testnet.binance.vision" if testnet else "wss://stream.binance.com:9443"
        self.connections = {}
        self.callbacks = {}
        self.running = False
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_attempts = 10
        
        logger.info(f"WebSocket manager initialized (testnet={testnet})", module="websocket")
    
    def _get_stream_url(self, streams: List[str]) -> str:
        """Build WebSocket URL for multiple streams"""
        streams_param = "/".join(streams)
        return f"{self.base_url}/stream?streams={streams_param}"
    
    async def subscribe_ticker(self, symbol: str, callback: Callable):
        """Subscribe to 24hr ticker statistics"""
        stream = f"{symbol.lower()}@ticker"
        await self._subscribe(stream, callback, "ticker")
    
    async def subscribe_kline(self, symbol: str, interval: str, callback: Callable):
        """Subscribe to candlestick/kline data"""
        stream = f"{symbol.lower()}@kline_{interval}"
        await self._subscribe(stream, callback, "kline")
    
    async def subscribe_depth(self, symbol: str, callback: Callable, levels: int = 20):
        """Subscribe to order book depth"""
        stream = f"{symbol.lower()}@depth{levels}"
        await self._subscribe(stream, callback, "depth")
    
    async def subscribe_trade(self, symbol: str, callback: Callable):
        """Subscribe to individual trade data"""
        stream = f"{symbol.lower()}@trade"
        await self._subscribe(stream, callback, "trade")
    
    async def subscribe_aggTrade(self, symbol: str, callback: Callable):
        """Subscribe to aggregated trade data"""
        stream = f"{symbol.lower()}@aggTrade"
        await self._subscribe(stream, callback, "aggTrade")
    
    async def subscribe_miniTicker(self, symbols: List[str], callback: Callable):
        """Subscribe to mini ticker for multiple symbols"""
        if symbols:
            streams = [f"{symbol.lower()}@miniTicker" for symbol in symbols]
            await self._subscribe_multiple(streams, callback, "miniTicker")
        else:
            # Subscribe to all symbols
            stream = "!miniTicker@arr"
            await self._subscribe(stream, callback, "miniTicker")
    
    async def _subscribe(self, stream: str, callback: Callable, stream_type: str):
        """Internal method to subscribe to a single stream"""
        url = f"{self.base_url}/ws/{stream}"
        
        if stream in self.callbacks:
            self.callbacks[stream].append(callback)
            logger.info(f"Added callback to existing stream: {stream}", module="websocket")
        else:
            self.callbacks[stream] = [callback]
            asyncio.create_task(self._connect_and_listen(url, stream, stream_type))
            logger.info(f"Subscribed to stream: {stream}", module="websocket")
    
    async def _subscribe_multiple(self, streams: List[str], callback: Callable, stream_type: str):
        """Subscribe to multiple streams in a single connection"""
        url = self._get_stream_url(streams)
        combined_key = "|".join(streams)
        
        if combined_key in self.callbacks:
            self.callbacks[combined_key].append(callback)
        else:
            self.callbacks[combined_key] = [callback]
            asyncio.create_task(self._connect_and_listen(url, combined_key, stream_type))
            logger.info(f"Subscribed to {len(streams)} streams", module="websocket")
    
    async def _connect_and_listen(self, url: str, stream_key: str, stream_type: str):
        """Connect to WebSocket and listen for messages"""
        reconnect_attempts = 0
        
        while reconnect_attempts < self.max_reconnect_attempts:
            try:
                async with websockets.connect(url) as websocket:
                    self.connections[stream_key] = websocket
                    reconnect_attempts = 0  # Reset on successful connection
                    
                    logger.info(f"WebSocket connected: {stream_key}", module="websocket")
                    
                    # Send ping every 30 seconds to keep connection alive
                    asyncio.create_task(self._keep_alive(websocket))
                    
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            
                            # Process data based on stream type
                            processed_data = await self._process_data(data, stream_type)
                            
                            # Call all registered callbacks
                            for callback in self.callbacks.get(stream_key, []):
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(processed_data)
                                    else:
                                        callback(processed_data)
                                except Exception as e:
                                    logger.error(f"Callback error: {e}", module="websocket")
                        
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse WebSocket message: {e}", module="websocket")
                        except Exception as e:
                            logger.error(f"Error processing WebSocket message: {e}", module="websocket")
            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {stream_key} - {e}", module="websocket")
                reconnect_attempts += 1
                
                if reconnect_attempts < self.max_reconnect_attempts:
                    await asyncio.sleep(self.reconnect_delay * reconnect_attempts)
                    logger.info(f"Reconnecting WebSocket: {stream_key} (attempt {reconnect_attempts})", 
                              module="websocket")
                else:
                    logger.error(f"Max reconnection attempts reached for: {stream_key}", module="websocket")
                    break
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}", module="websocket")
                reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay * reconnect_attempts)
        
        # Clean up
        if stream_key in self.connections:
            del self.connections[stream_key]
        if stream_key in self.callbacks:
            del self.callbacks[stream_key]
    
    async def _keep_alive(self, websocket):
        """Send ping to keep WebSocket connection alive"""
        try:
            while websocket.open:
                await asyncio.sleep(30)
                await websocket.ping()
        except Exception as e:
            logger.debug(f"Keep-alive ping failed: {e}", module="websocket")
    
    async def _process_data(self, data: Dict, stream_type: str) -> Dict:
        """Process raw WebSocket data based on stream type"""
        processed = {
            "stream_type": stream_type,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_data": data
        }
        
        try:
            if stream_type == "ticker":
                processed.update({
                    "symbol": data.get("s"),
                    "price": float(data.get("c", 0)),
                    "volume": float(data.get("v", 0)),
                    "quote_volume": float(data.get("q", 0)),
                    "change_24h": float(data.get("P", 0)),
                    "high_24h": float(data.get("h", 0)),
                    "low_24h": float(data.get("l", 0))
                })
            
            elif stream_type == "kline":
                k = data.get("k", {})
                processed.update({
                    "symbol": data.get("s"),
                    "interval": k.get("i"),
                    "open": float(k.get("o", 0)),
                    "high": float(k.get("h", 0)),
                    "low": float(k.get("l", 0)),
                    "close": float(k.get("c", 0)),
                    "volume": float(k.get("v", 0)),
                    "is_closed": k.get("x", False)
                })
                
                # Save closed candles to database
                if k.get("x", False):
                    await self._save_kline_to_db(data)
            
            elif stream_type == "depth":
                processed.update({
                    "symbol": data.get("s"),
                    "bids": data.get("b", []),
                    "asks": data.get("a", []),
                    "last_update_id": data.get("u")
                })
            
            elif stream_type == "trade":
                processed.update({
                    "symbol": data.get("s"),
                    "price": float(data.get("p", 0)),
                    "quantity": float(data.get("q", 0)),
                    "trade_id": data.get("t"),
                    "is_buyer_maker": data.get("m")
                })
            
            elif stream_type == "aggTrade":
                processed.update({
                    "symbol": data.get("s"),
                    "price": float(data.get("p", 0)),
                    "quantity": float(data.get("q", 0)),
                    "first_trade_id": data.get("f"),
                    "last_trade_id": data.get("l"),
                    "is_buyer_maker": data.get("m")
                })
            
            elif stream_type == "miniTicker":
                if isinstance(data, list):
                    # All symbols mini ticker
                    processed["tickers"] = [
                        {
                            "symbol": item.get("s"),
                            "price": float(item.get("c", 0)),
                            "volume": float(item.get("v", 0)),
                            "quote_volume": float(item.get("q", 0))
                        }
                        for item in data
                    ]
                else:
                    processed.update({
                        "symbol": data.get("s"),
                        "price": float(data.get("c", 0)),
                        "volume": float(data.get("v", 0)),
                        "quote_volume": float(data.get("q", 0))
                    })
        
        except Exception as e:
            logger.error(f"Error processing {stream_type} data: {e}", module="websocket")
        
        return processed
    
    async def _save_kline_to_db(self, data: Dict):
        """Save closed kline to database"""
        try:
            k = data.get("k", {})
            kline_data = pd.DataFrame([{
                "open": float(k.get("o", 0)),
                "high": float(k.get("h", 0)),
                "low": float(k.get("l", 0)),
                "close": float(k.get("c", 0)),
                "volume": float(k.get("v", 0))
            }], index=[pd.Timestamp(k.get("t"), unit='ms')])
            
            await supabase_manager.save_market_data(
                symbol=data.get("s"),
                timeframe=k.get("i"),
                data=kline_data
            )
        except Exception as e:
            logger.error(f"Failed to save kline to database: {e}", module="websocket")
    
    async def unsubscribe(self, stream: str):
        """Unsubscribe from a stream"""
        if stream in self.connections:
            try:
                await self.connections[stream].close()
                del self.connections[stream]
                del self.callbacks[stream]
                logger.info(f"Unsubscribed from stream: {stream}", module="websocket")
            except Exception as e:
                logger.error(f"Error unsubscribing from stream: {e}", module="websocket")
    
    async def close_all(self):
        """Close all WebSocket connections"""
        for stream, ws in list(self.connections.items()):
            try:
                await ws.close()
                logger.info(f"Closed WebSocket: {stream}", module="websocket")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}", module="websocket")
        
        self.connections.clear()
        self.callbacks.clear()
        logger.info("All WebSocket connections closed", module="websocket")

# Example usage with real-time price monitoring
class PriceMonitor:
    """Monitor real-time prices and trigger alerts"""
    
    def __init__(self, ws_manager: BinanceWebSocketManager):
        self.ws_manager = ws_manager
        self.price_alerts = {}
        self.price_cache = {}
    
    async def monitor_symbol(self, symbol: str, alert_threshold: float = 0.01):
        """Monitor a symbol for price changes"""
        self.price_alerts[symbol] = alert_threshold
        
        async def on_ticker_update(data):
            if data["stream_type"] == "ticker":
                symbol = data["symbol"]
                new_price = data["price"]
                
                if symbol in self.price_cache:
                    old_price = self.price_cache[symbol]
                    change = abs((new_price - old_price) / old_price)
                    
                    if change > self.price_alerts.get(symbol, 0.01):
                        await supabase_manager.create_alert(
                            alert_type="price_change",
                            title=f"Price Alert: {symbol}",
                            message=f"{symbol} price changed by {change:.2%}: ${old_price:.2f} → ${new_price:.2f}",
                            severity="INFO",
                            metadata={
                                "symbol": symbol,
                                "old_price": old_price,
                                "new_price": new_price,
                                "change_percent": change * 100
                            }
                        )
                
                self.price_cache[symbol] = new_price
        
        await self.ws_manager.subscribe_ticker(symbol, on_ticker_update)
    
    async def monitor_multiple_symbols(self, symbols: List[str]):
        """Monitor multiple symbols"""
        for symbol in symbols:
            await self.monitor_symbol(symbol)