"""
Backtesting engine for strategy evaluation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
from dataclasses import dataclass, asdict
from utils.logger import logger
from core.supabase_client import supabase_manager

@dataclass
class BacktestConfig:
    """Configuration for backtesting"""
    initial_capital: float = 10000
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005  # 0.05%
    position_sizing: str = "fixed"  # fixed, percentage, kelly
    position_size: float = 0.1  # 10% of capital per trade
    max_positions: int = 1
    stop_loss_pct: float = 0.02  # 2%
    take_profit_pct: float = 0.04  # 4%
    use_atr_stops: bool = True
    atr_stop_multiplier: float = 2.0
    atr_profit_multiplier: float = 3.0

@dataclass
class Trade:
    """Represent a single trade"""
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    side: str  # BUY or SELL
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    commission: float
    pnl: Optional[float]
    pnl_percent: Optional[float]
    exit_reason: Optional[str]  # signal, stop_loss, take_profit
    
    def close(self, exit_price: float, exit_time: datetime, reason: str):
        """Close the trade"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = reason
        
        # Calculate PnL
        if self.side == "BUY":
            self.pnl = (exit_price - self.entry_price) * self.quantity - self.commission
        else:  # SELL/SHORT
            self.pnl = (self.entry_price - exit_price) * self.quantity - self.commission
        
        self.pnl_percent = (self.pnl / (self.entry_price * self.quantity)) * 100

class BacktestEngine:
    """Engine for backtesting trading strategies"""
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.current_capital: float = self.config.initial_capital
        self.open_positions: List[Trade] = []
        self.performance_metrics: Dict = {}
        
        logger.info("Backtest engine initialized", module="backtest", config=asdict(self.config))
    
    def run(self, data: pd.DataFrame, strategy_func: Callable, 
            start_date: str = None, end_date: str = None) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            data: DataFrame with OHLCV data
            strategy_func: Function that returns BUY/SELL/HOLD signal
            start_date: Start date for backtest
            end_date: End date for backtest
        
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest from {start_date} to {end_date}", module="backtest")
        
        # Filter data by date range
        if start_date:
            data = data[data.index >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data.index <= pd.to_datetime(end_date)]
        
        # Reset state
        self.trades = []
        self.equity_curve = [self.config.initial_capital]
        self.current_capital = self.config.initial_capital
        self.open_positions = []
        
        # Add technical indicators that might be needed
        data = self._prepare_data(data)
        
        # Iterate through each bar
        for i in range(50, len(data)):  # Start from 50 to ensure indicators are ready
            current_bar = data.iloc[i]
            current_time = data.index[i]
            historical_data = data.iloc[:i+1]
            
            # Check stop loss and take profit for open positions
            self._check_exits(current_bar, current_time)
            
            # Get signal from strategy
            try:
                signal = strategy_func(historical_data)
            except Exception as e:
                logger.error(f"Strategy error: {e}", module="backtest")
                signal = "HOLD"
            
            # Process signal
            if signal == "BUY" and len(self.open_positions) < self.config.max_positions:
                self._open_position("BUY", current_bar, current_time)
            elif signal == "SELL" and self.open_positions:
                self._close_all_positions(current_bar, current_time, "signal")
            
            # Update equity curve
            self._update_equity(current_bar)
        
        # Close any remaining positions
        if self.open_positions and len(data) > 0:
            last_bar = data.iloc[-1]
            self._close_all_positions(last_bar, data.index[-1], "end_of_data")
        
        # Calculate performance metrics
        self.performance_metrics = self._calculate_metrics(data)
        
        logger.info("Backtest completed", module="backtest", 
                   total_trades=len(self.trades),
                   final_capital=self.current_capital)
        
        return {
            "metrics": self.performance_metrics,
            "trades": [asdict(t) for t in self.trades],
            "equity_curve": self.equity_curve,
            "config": asdict(self.config)
        }
    
    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add necessary indicators to data"""
        from core.indicators import calculate_atr
        
        if self.config.use_atr_stops:
            data['atr'] = calculate_atr(data, 14)
        
        return data
    
    def _open_position(self, side: str, bar: pd.Series, timestamp: datetime):
        """Open a new position"""
        # Calculate position size
        position_size = self._calculate_position_size(bar['close'])
        
        if position_size <= 0:
            return
        
        # Apply slippage
        entry_price = bar['close'] * (1 + self.config.slippage_rate if side == "BUY" else 1 - self.config.slippage_rate)
        
        # Calculate commission
        commission = position_size * entry_price * self.config.commission_rate
        
        # Check if we have enough capital
        required_capital = position_size * entry_price + commission
        if required_capital > self.current_capital:
            return
        
        # Create trade
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            symbol="BTCUSDT",  # Placeholder
            side=side,
            entry_price=entry_price,
            exit_price=None,
            quantity=position_size,
            commission=commission,
            pnl=None,
            pnl_percent=None,
            exit_reason=None
        )
        
        self.open_positions.append(trade)
        self.current_capital -= required_capital
        
        logger.debug(f"Opened {side} position at {entry_price}", module="backtest")
    
    def _close_position(self, trade: Trade, bar: pd.Series, timestamp: datetime, reason: str):
        """Close a specific position"""
        # Apply slippage
        exit_price = bar['close'] * (1 - self.config.slippage_rate if trade.side == "BUY" else 1 + self.config.slippage_rate)
        
        # Add exit commission
        trade.commission += trade.quantity * exit_price * self.config.commission_rate
        
        # Close trade
        trade.close(exit_price, timestamp, reason)
        
        # Update capital
        self.current_capital += trade.quantity * exit_price - trade.commission
        if trade.pnl:
            self.current_capital += trade.pnl
        
        # Move to completed trades
        self.open_positions.remove(trade)
        self.trades.append(trade)
        
        logger.debug(f"Closed position at {exit_price}, PnL: {trade.pnl:.2f}", module="backtest")
    
    def _close_all_positions(self, bar: pd.Series, timestamp: datetime, reason: str):
        """Close all open positions"""
        for trade in self.open_positions[:]:
            self._close_position(trade, bar, timestamp, reason)
    
    def _check_exits(self, bar: pd.Series, timestamp: datetime):
        """Check stop loss and take profit conditions"""
        for trade in self.open_positions[:]:
            exit_triggered = False
            
            if self.config.use_atr_stops and 'atr' in bar and not pd.isna(bar['atr']):
                # ATR-based stops
                stop_distance = bar['atr'] * self.config.atr_stop_multiplier
                profit_distance = bar['atr'] * self.config.atr_profit_multiplier
                
                if trade.side == "BUY":
                    stop_price = trade.entry_price - stop_distance
                    profit_price = trade.entry_price + profit_distance
                    
                    if bar['low'] <= stop_price:
                        self._close_position(trade, bar, timestamp, "stop_loss")
                        exit_triggered = True
                    elif bar['high'] >= profit_price:
                        self._close_position(trade, bar, timestamp, "take_profit")
                        exit_triggered = True
            else:
                # Percentage-based stops
                if trade.side == "BUY":
                    stop_price = trade.entry_price * (1 - self.config.stop_loss_pct)
                    profit_price = trade.entry_price * (1 + self.config.take_profit_pct)
                    
                    if bar['low'] <= stop_price:
                        self._close_position(trade, bar, timestamp, "stop_loss")
                        exit_triggered = True
                    elif bar['high'] >= profit_price:
                        self._close_position(trade, bar, timestamp, "take_profit")
                        exit_triggered = True
    
    def _calculate_position_size(self, price: float) -> float:
        """Calculate position size based on strategy"""
        if self.config.position_sizing == "fixed":
            # Fixed dollar amount
            return self.config.position_size * self.config.initial_capital / price
        elif self.config.position_sizing == "percentage":
            # Percentage of current capital
            return self.config.position_size * self.current_capital / price
        else:
            # Default to fixed
            return self.config.position_size * self.config.initial_capital / price
    
    def _update_equity(self, bar: pd.Series):
        """Update equity curve with current value"""
        total_equity = self.current_capital
        
        # Add unrealized PnL from open positions
        for trade in self.open_positions:
            current_price = bar['close']
            if trade.side == "BUY":
                unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
            else:
                unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
            total_equity += trade.quantity * current_price + unrealized_pnl
        
        self.equity_curve.append(total_equity)
    
    def _calculate_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                "total_return": 0,
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0
            }
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl and t.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Returns
        total_return = ((self.equity_curve[-1] - self.config.initial_capital) / 
                       self.config.initial_capital * 100) if self.equity_curve else 0
        
        # Sharpe ratio (simplified)
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown
        equity_series = pd.Series(self.equity_curve)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = abs(drawdown.min()) * 100 if len(drawdown) > 0 else 0
        
        # Average trade metrics
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Trade duration
        trade_durations = []
        for t in self.trades:
            if t.exit_time and t.entry_time:
                duration = (t.exit_time - t.entry_time).total_seconds() / 3600  # Hours
                trade_durations.append(duration)
        
        avg_duration = np.mean(trade_durations) if trade_durations else 0
        
        return {
            "total_return": round(total_return, 2),
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown": round(max_drawdown, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "avg_trade_duration_hours": round(avg_duration, 2),
            "best_trade": round(max([t.pnl for t in self.trades if t.pnl], default=0), 2),
            "worst_trade": round(min([t.pnl for t in self.trades if t.pnl], default=0), 2),
            "final_capital": round(self.equity_curve[-1] if self.equity_curve else self.config.initial_capital, 2)
        }
    
    async def save_results(self, strategy_id: str, start_date: str, end_date: str):
        """Save backtest results to database"""
        try:
            result_data = {
                "strategy_id": strategy_id,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": self.config.initial_capital,
                "final_capital": self.performance_metrics.get("final_capital", self.config.initial_capital),
                "total_return": self.performance_metrics.get("total_return", 0),
                "annual_return": self._calculate_annual_return(start_date, end_date),
                "total_trades": self.performance_metrics.get("total_trades", 0),
                "win_rate": self.performance_metrics.get("win_rate", 0),
                "profit_factor": self.performance_metrics.get("profit_factor", 0),
                "sharpe_ratio": self.performance_metrics.get("sharpe_ratio", 0),
                "sortino_ratio": self._calculate_sortino_ratio(),
                "max_drawdown": self.performance_metrics.get("max_drawdown", 0),
                "avg_trade_return": self._calculate_avg_trade_return(),
                "best_trade": self.performance_metrics.get("best_trade", 0),
                "worst_trade": self.performance_metrics.get("worst_trade", 0),
                "avg_holding_time": f"{self.performance_metrics.get('avg_trade_duration_hours', 0)} hours",
                "config": asdict(self.config),
                "trades": [asdict(t) for t in self.trades]
            }
            
            await supabase_manager.client.table("backtest_results").insert(result_data).execute()
            logger.info("Backtest results saved to database", module="backtest")
            
        except Exception as e:
            logger.error(f"Failed to save backtest results: {e}", module="backtest")
    
    def _calculate_annual_return(self, start_date: str, end_date: str) -> float:
        """Calculate annualized return"""
        if not self.equity_curve or len(self.equity_curve) < 2:
            return 0
        
        days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
        if days <= 0:
            return 0
        
        total_return = (self.equity_curve[-1] - self.config.initial_capital) / self.config.initial_capital
        annual_return = ((1 + total_return) ** (365 / days) - 1) * 100
        
        return round(annual_return, 2)
    
    def _calculate_sortino_ratio(self) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if len(self.equity_curve) < 2:
            return 0
        
        returns = pd.Series(self.equity_curve).pct_change().dropna()
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return 0
        
        downside_std = downside_returns.std()
        if downside_std == 0:
            return 0
        
        sortino = returns.mean() / downside_std * np.sqrt(252)
        return round(sortino, 4)
    
    def _calculate_avg_trade_return(self) -> float:
        """Calculate average trade return percentage"""
        if not self.trades:
            return 0
        
        returns = [t.pnl_percent for t in self.trades if t.pnl_percent is not None]
        return round(np.mean(returns), 2) if returns else 0