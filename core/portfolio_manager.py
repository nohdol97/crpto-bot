"""
Portfolio manager for multi-strategy trading
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from decimal import Decimal
from dataclasses import dataclass, asdict
from utils.logger import logger
from core.supabase_client import supabase_manager
from core.websocket_manager import BinanceWebSocketManager
from strategies.sma_crossover import sma_crossover_signal
from strategies.rsi_reversion import rsi_reversion_signal
from strategies.bb_breakout import bb_breakout_signal

@dataclass
class StrategyAllocation:
    """Strategy allocation configuration"""
    strategy_id: str
    name: str
    type: str
    allocation_percent: float
    max_positions: int
    is_active: bool
    current_positions: int = 0
    current_allocation: float = 0.0
    performance_score: float = 1.0  # Performance-based weight

class PortfolioManager:
    """Manage multiple strategies and capital allocation"""
    
    def __init__(self, total_capital: float, binance_client):
        self.total_capital = total_capital
        self.available_capital = total_capital
        self.binance_client = binance_client
        self.strategies: Dict[str, StrategyAllocation] = {}
        self.positions: Dict[str, Dict] = {}  # position_id: position_data
        self.ws_manager = None
        self.running = False
        
        # Strategy function mapping
        self.strategy_functions = {
            'sma_crossover': sma_crossover_signal,
            'rsi_reversion': rsi_reversion_signal,
            'bb_breakout': bb_breakout_signal
        }
        
        logger.info(f"Portfolio manager initialized with ${total_capital}", module="portfolio")
    
    async def initialize(self):
        """Initialize portfolio manager with strategies from database"""
        try:
            # Load active strategies
            strategies = await supabase_manager.get_active_strategies()
            
            for strategy in strategies:
                allocation = StrategyAllocation(
                    strategy_id=strategy['id'],
                    name=strategy['name'],
                    type=strategy['type'],
                    allocation_percent=float(strategy.get('allocation_percent', 0)),
                    max_positions=strategy.get('config', {}).get('max_positions', 1),
                    is_active=strategy['status'] == 'ACTIVE'
                )
                self.strategies[strategy['id']] = allocation
                
                logger.info(f"Loaded strategy: {allocation.name} ({allocation.allocation_percent}%)", 
                          module="portfolio")
            
            # Load open positions
            open_positions = await supabase_manager.get_open_positions()
            for position in open_positions:
                self.positions[position['id']] = position
                
                # Update strategy position count
                if position.get('strategy_id') in self.strategies:
                    self.strategies[position['strategy_id']].current_positions += 1
            
            # Calculate current allocations
            await self._update_allocations()
            
            logger.info(f"Portfolio initialized with {len(self.strategies)} strategies and {len(self.positions)} open positions", 
                       module="portfolio")
            
        except Exception as e:
            logger.error(f"Failed to initialize portfolio: {e}", module="portfolio")
    
    async def start_monitoring(self, symbols: List[str], timeframe: str = "15m"):
        """Start monitoring markets for all strategies"""
        if self.running:
            logger.warning("Portfolio monitoring already running", module="portfolio")
            return
        
        self.running = True
        logger.info(f"Starting portfolio monitoring for {symbols}", module="portfolio")
        
        # Initialize WebSocket manager
        self.ws_manager = BinanceWebSocketManager(testnet=self.binance_client.testnet)
        
        # Subscribe to real-time data
        for symbol in symbols:
            await self.ws_manager.subscribe_kline(
                symbol, timeframe, 
                lambda data: asyncio.create_task(self._on_kline_update(data))
            )
        
        # Start main monitoring loop
        asyncio.create_task(self._monitoring_loop(symbols, timeframe))
    
    async def stop_monitoring(self):
        """Stop portfolio monitoring"""
        self.running = False
        
        if self.ws_manager:
            await self.ws_manager.close_all()
        
        logger.info("Portfolio monitoring stopped", module="portfolio")
    
    async def _monitoring_loop(self, symbols: List[str], timeframe: str):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check each symbol for each strategy
                for symbol in symbols:
                    await self._evaluate_symbol(symbol, timeframe)
                
                # Update allocations and rebalance if needed
                await self._update_allocations()
                await self._check_rebalancing()
                
                # Check position exits
                await self._check_position_exits()
                
                # Update performance metrics
                await self._update_performance_metrics()
                
                # Sleep for interval
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", module="portfolio")
                await asyncio.sleep(5)
    
    async def _evaluate_symbol(self, symbol: str, timeframe: str):
        """Evaluate a symbol for all active strategies"""
        try:
            # Get market data
            klines = self.binance_client.klines(symbol, timeframe, 300)
            if not klines:
                return
            
            df = pd.DataFrame(klines)
            
            # Evaluate each strategy
            for strategy_id, allocation in self.strategies.items():
                if not allocation.is_active:
                    continue
                
                # Check if strategy has room for more positions
                if allocation.current_positions >= allocation.max_positions:
                    continue
                
                # Check if strategy has available capital
                strategy_capital = self._get_strategy_available_capital(strategy_id)
                if strategy_capital < 100:  # Minimum position size
                    continue
                
                # Get signal from strategy
                strategy_func = self.strategy_functions.get(allocation.type)
                if not strategy_func:
                    continue
                
                try:
                    signal = strategy_func(df)
                    
                    if signal == "BUY":
                        await self._open_position(symbol, strategy_id, strategy_capital)
                    elif signal == "SELL" and self._has_position(symbol, strategy_id):
                        await self._close_positions(symbol, strategy_id)
                
                except Exception as e:
                    logger.error(f"Strategy evaluation error for {allocation.name}: {e}", 
                               module="portfolio")
        
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {e}", module="portfolio")
    
    async def _open_position(self, symbol: str, strategy_id: str, available_capital: float):
        """Open a new position for a strategy"""
        try:
            allocation = self.strategies[strategy_id]
            
            # Calculate position size
            position_size = min(
                available_capital * 0.95,  # Use 95% of available capital
                self.total_capital * (allocation.allocation_percent / 100) / allocation.max_positions
            )
            
            if position_size < 10:  # Minimum position size
                return
            
            # Get current price
            ticker = self.binance_client.ticker_price(symbol)
            if not ticker:
                return
            
            current_price = float(ticker['price'])
            quantity = position_size / current_price
            
            # Place order
            order = self.binance_client.market_buy_quote(symbol, position_size)
            
            if order and order.get('status') == 'FILLED':
                # Record position in database
                position_data = {
                    "symbol": symbol,
                    "strategy_id": strategy_id,
                    "side": "BUY",
                    "entry_price": float(order.get('fills', [{}])[0].get('price', current_price)),
                    "entry_quantity": float(order.get('executedQty', quantity)),
                    "entry_time": datetime.utcnow().isoformat(),
                    "entry_order_id": order.get('orderId'),
                    "status": "OPEN"
                }
                
                position_id = await supabase_manager.create_position(position_data)
                
                if position_id:
                    self.positions[position_id] = position_data
                    allocation.current_positions += 1
                    
                    logger.info(f"Opened position for {allocation.name}: {symbol} @ ${position_data['entry_price']}", 
                              module="portfolio")
                    
                    # Create alert
                    await supabase_manager.create_alert(
                        alert_type="position_opened",
                        title=f"Position Opened: {symbol}",
                        message=f"{allocation.name} opened {quantity:.4f} {symbol} @ ${current_price:.2f}",
                        severity="INFO",
                        metadata=position_data
                    )
        
        except Exception as e:
            logger.error(f"Failed to open position: {e}", module="portfolio")
    
    async def _close_positions(self, symbol: str, strategy_id: str = None):
        """Close positions for a symbol and optionally a specific strategy"""
        try:
            positions_to_close = []
            
            for position_id, position in self.positions.items():
                if position['symbol'] == symbol and position['status'] == 'OPEN':
                    if strategy_id is None or position.get('strategy_id') == strategy_id:
                        positions_to_close.append((position_id, position))
            
            for position_id, position in positions_to_close:
                # Place sell order
                quantity = position['entry_quantity']
                order = self.binance_client.market_sell_base(symbol, quantity)
                
                if order and order.get('status') == 'FILLED':
                    exit_price = float(order.get('fills', [{}])[0].get('price', 0))
                    pnl = (exit_price - position['entry_price']) * quantity
                    
                    # Update position in database
                    await supabase_manager.close_position(
                        position_id, exit_price, quantity, pnl
                    )
                    
                    # Update local state
                    del self.positions[position_id]
                    
                    if position.get('strategy_id') in self.strategies:
                        self.strategies[position['strategy_id']].current_positions -= 1
                    
                    logger.info(f"Closed position: {symbol} @ ${exit_price:.2f}, PnL: ${pnl:.2f}", 
                              module="portfolio")
                    
                    # Create alert
                    await supabase_manager.create_alert(
                        alert_type="position_closed",
                        title=f"Position Closed: {symbol}",
                        message=f"Closed {quantity:.4f} {symbol} @ ${exit_price:.2f}, PnL: ${pnl:.2f}",
                        severity="INFO" if pnl > 0 else "WARNING",
                        metadata={"position_id": position_id, "pnl": pnl}
                    )
        
        except Exception as e:
            logger.error(f"Failed to close positions: {e}", module="portfolio")
    
    async def _check_position_exits(self):
        """Check all positions for exit conditions"""
        for position_id, position in list(self.positions.items()):
            if position['status'] != 'OPEN':
                continue
            
            try:
                # Get current price
                ticker = self.binance_client.ticker_price(position['symbol'])
                if not ticker:
                    continue
                
                current_price = float(ticker['price'])
                entry_price = position['entry_price']
                
                # Check stop loss and take profit
                # These should be set based on strategy configuration
                stop_loss = position.get('stop_loss')
                take_profit = position.get('take_profit')
                
                should_close = False
                reason = ""
                
                if stop_loss and current_price <= stop_loss:
                    should_close = True
                    reason = "stop_loss"
                elif take_profit and current_price >= take_profit:
                    should_close = True
                    reason = "take_profit"
                
                if should_close:
                    await self._close_positions(position['symbol'], position.get('strategy_id'))
                    logger.info(f"Position closed due to {reason}: {position['symbol']}", 
                              module="portfolio")
            
            except Exception as e:
                logger.error(f"Error checking position exit: {e}", module="portfolio")
    
    def _get_strategy_available_capital(self, strategy_id: str) -> float:
        """Get available capital for a strategy"""
        allocation = self.strategies[strategy_id]
        
        # Calculate allocated capital
        allocated_capital = self.total_capital * (allocation.allocation_percent / 100)
        
        # Calculate used capital
        used_capital = 0
        for position in self.positions.values():
            if position.get('strategy_id') == strategy_id and position['status'] == 'OPEN':
                used_capital += position['entry_price'] * position['entry_quantity']
        
        return max(0, allocated_capital - used_capital)
    
    def _has_position(self, symbol: str, strategy_id: str) -> bool:
        """Check if strategy has position in symbol"""
        for position in self.positions.values():
            if (position['symbol'] == symbol and 
                position.get('strategy_id') == strategy_id and 
                position['status'] == 'OPEN'):
                return True
        return False
    
    async def _update_allocations(self):
        """Update current allocations based on positions"""
        try:
            # Calculate total value
            total_value = self.available_capital
            
            for position in self.positions.values():
                if position['status'] == 'OPEN':
                    # Get current price
                    ticker = self.binance_client.ticker_price(position['symbol'])
                    if ticker:
                        current_price = float(ticker['price'])
                        position_value = current_price * position['entry_quantity']
                        total_value += position_value
                        
                        # Update strategy allocation
                        strategy_id = position.get('strategy_id')
                        if strategy_id in self.strategies:
                            self.strategies[strategy_id].current_allocation += position_value
            
            self.total_capital = total_value
            
            # Calculate allocation percentages
            for strategy in self.strategies.values():
                if total_value > 0:
                    strategy.current_allocation = (strategy.current_allocation / total_value) * 100
        
        except Exception as e:
            logger.error(f"Failed to update allocations: {e}", module="portfolio")
    
    async def _check_rebalancing(self):
        """Check if portfolio needs rebalancing"""
        try:
            needs_rebalancing = False
            
            for strategy in self.strategies.values():
                if not strategy.is_active:
                    continue
                
                # Check if allocation is off by more than 5%
                allocation_diff = abs(strategy.current_allocation - strategy.allocation_percent)
                if allocation_diff > 5:
                    needs_rebalancing = True
                    logger.info(f"Strategy {strategy.name} needs rebalancing: {strategy.current_allocation:.1f}% vs target {strategy.allocation_percent:.1f}%", 
                              module="portfolio")
            
            if needs_rebalancing:
                await self._rebalance_portfolio()
        
        except Exception as e:
            logger.error(f"Failed to check rebalancing: {e}", module="portfolio")
    
    async def _rebalance_portfolio(self):
        """Rebalance portfolio allocations"""
        logger.info("Starting portfolio rebalancing", module="portfolio")
        
        # Implementation depends on rebalancing strategy
        # Could be immediate rebalancing or gradual over time
        # For now, just log the need for rebalancing
        
        await supabase_manager.create_alert(
            alert_type="rebalancing_needed",
            title="Portfolio Rebalancing Required",
            message="Portfolio allocations have drifted from targets",
            severity="WARNING",
            metadata={
                "allocations": {
                    s.name: {
                        "current": s.current_allocation,
                        "target": s.allocation_percent
                    }
                    for s in self.strategies.values()
                }
            }
        )
    
    async def _update_performance_metrics(self):
        """Update performance metrics for each strategy"""
        try:
            for strategy_id, allocation in self.strategies.items():
                # Get recent performance
                performance = await supabase_manager.get_performance_history(
                    strategy_id=strategy_id, days=7
                )
                
                if not performance.empty:
                    # Calculate performance score based on recent metrics
                    recent_performance = performance.iloc[0] if len(performance) > 0 else {}
                    
                    # Simple scoring: win rate * profit factor
                    win_rate = recent_performance.get('win_rate', 50) / 100
                    profit_factor = recent_performance.get('profit_factor', 1)
                    
                    allocation.performance_score = win_rate * profit_factor
                    
                    # Update daily performance
                    metrics = {
                        "total_trades": len([p for p in self.positions.values() 
                                           if p.get('strategy_id') == strategy_id]),
                        "net_pnl": recent_performance.get('net_pnl', 0)
                    }
                    
                    await supabase_manager.update_daily_performance(strategy_id, metrics)
        
        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}", module="portfolio")
    
    async def _on_kline_update(self, data):
        """Handle real-time kline updates"""
        if data.get("is_closed"):
            # Candle closed, evaluate strategies
            symbol = data.get("symbol")
            if symbol:
                await self._evaluate_symbol(symbol, data.get("interval", "15m"))
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        return {
            "total_capital": self.total_capital,
            "available_capital": self.available_capital,
            "strategies": {
                s.name: {
                    "allocation_percent": s.allocation_percent,
                    "current_allocation": s.current_allocation,
                    "positions": s.current_positions,
                    "max_positions": s.max_positions,
                    "performance_score": s.performance_score,
                    "is_active": s.is_active
                }
                for s in self.strategies.values()
            },
            "open_positions": len(self.positions),
            "positions": list(self.positions.values())
        }