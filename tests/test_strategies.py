"""
Unit tests for trading strategies
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.sma_crossover import sma_crossover_signal
from strategies.rsi_reversion import rsi_reversion_signal
from strategies.bb_breakout import bb_breakout_signal

class TestStrategies:
    """Test suite for trading strategies"""
    
    @pytest.fixture
    def bullish_trend_data(self):
        """Generate data with clear bullish trend"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        
        # Create uptrending price data
        base_price = 45000
        trend = np.linspace(0, 5000, 100)  # Upward trend
        noise = np.random.randn(100) * 100
        close_prices = base_price + trend + noise
        
        df = pd.DataFrame({
            'open': close_prices - np.random.uniform(0, 100, 100),
            'high': close_prices + abs(np.random.randn(100) * 100),
            'low': close_prices - abs(np.random.randn(100) * 100),
            'close': close_prices,
            'volume': np.random.uniform(1000, 5000, 100)
        }, index=dates)
        
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
    @pytest.fixture
    def bearish_trend_data(self):
        """Generate data with clear bearish trend"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        
        # Create downtrending price data
        base_price = 50000
        trend = np.linspace(0, -5000, 100)  # Downward trend
        noise = np.random.randn(100) * 100
        close_prices = base_price + trend + noise
        
        df = pd.DataFrame({
            'open': close_prices + np.random.uniform(0, 100, 100),
            'high': close_prices + abs(np.random.randn(100) * 100),
            'low': close_prices - abs(np.random.randn(100) * 100),
            'close': close_prices,
            'volume': np.random.uniform(1000, 5000, 100)
        }, index=dates)
        
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
    @pytest.fixture
    def sideways_data(self):
        """Generate sideways/ranging market data"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        
        # Create oscillating price data
        base_price = 45000
        oscillation = np.sin(np.linspace(0, 4*np.pi, 100)) * 1000
        noise = np.random.randn(100) * 100
        close_prices = base_price + oscillation + noise
        
        df = pd.DataFrame({
            'open': close_prices + np.random.uniform(-50, 50, 100),
            'high': close_prices + abs(np.random.randn(100) * 100),
            'low': close_prices - abs(np.random.randn(100) * 100),
            'close': close_prices,
            'volume': np.random.uniform(1000, 5000, 100)
        }, index=dates)
        
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
    def test_sma_crossover_bullish(self, bullish_trend_data):
        """Test SMA crossover in bullish trend"""
        signal = sma_crossover_signal(bullish_trend_data)
        
        assert signal in ['BUY', 'SELL', 'HOLD']
        
        # In strong uptrend, should eventually generate BUY signal
        # Check if fast SMA is above slow SMA at the end
        from core.indicators import calculate_sma
        sma_fast = calculate_sma(bullish_trend_data['close'], 20)
        sma_slow = calculate_sma(bullish_trend_data['close'], 50)
        
        if not sma_fast.isna().iloc[-1] and not sma_slow.isna().iloc[-1]:
            if sma_fast.iloc[-1] > sma_slow.iloc[-1]:
                # Fast SMA above slow SMA indicates bullish
                assert signal in ['BUY', 'HOLD']
    
    def test_sma_crossover_bearish(self, bearish_trend_data):
        """Test SMA crossover in bearish trend"""
        signal = sma_crossover_signal(bearish_trend_data)
        
        assert signal in ['BUY', 'SELL', 'HOLD']
        
        # In strong downtrend, should eventually generate SELL signal
        from core.indicators import calculate_sma
        sma_fast = calculate_sma(bearish_trend_data['close'], 20)
        sma_slow = calculate_sma(bearish_trend_data['close'], 50)
        
        if not sma_fast.isna().iloc[-1] and not sma_slow.isna().iloc[-1]:
            if sma_fast.iloc[-1] < sma_slow.iloc[-1]:
                # Fast SMA below slow SMA indicates bearish
                assert signal in ['SELL', 'HOLD']
    
    def test_rsi_reversion_oversold(self):
        """Test RSI reversion with oversold conditions"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        
        # Create data that will result in low RSI (oversold)
        # Sharp decline followed by stabilization
        prices = np.concatenate([
            np.linspace(50000, 45000, 50),  # Decline
            np.ones(50) * 45000  # Stabilize
        ])
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': np.ones(100) * 2000
        }, index=dates)
        
        signal = rsi_reversion_signal(df)
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_rsi_reversion_overbought(self):
        """Test RSI reversion with overbought conditions"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        
        # Create data that will result in high RSI (overbought)
        # Sharp rise followed by stabilization
        prices = np.concatenate([
            np.linspace(45000, 50000, 50),  # Rise
            np.ones(50) * 50000  # Stabilize
        ])
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + 100,
            'low': prices - 100,
            'close': prices,
            'volume': np.ones(100) * 2000
        }, index=dates)
        
        signal = rsi_reversion_signal(df)
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_bb_breakout_squeeze(self, sideways_data):
        """Test Bollinger Band breakout with squeeze conditions"""
        signal = bb_breakout_signal(sideways_data)
        
        assert signal in ['BUY', 'SELL', 'HOLD']
        
        # Sideways market often creates squeeze conditions
        # Signal should be HOLD most of the time unless breakout occurs
    
    def test_bb_breakout_expansion(self):
        """Test Bollinger Band breakout with band expansion"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        
        # Create data with increasing volatility (band expansion)
        base_price = 45000
        volatility = np.linspace(100, 1000, 100)  # Increasing volatility
        prices = base_price + np.cumsum(np.random.randn(100)) * volatility / 100
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + volatility,
            'low': prices - volatility,
            'close': prices,
            'volume': np.ones(100) * 2000
        }, index=dates)
        
        signal = bb_breakout_signal(df)
        assert signal in ['BUY', 'SELL', 'HOLD']
    
    def test_strategies_with_insufficient_data(self):
        """Test strategies with insufficient data"""
        # Create minimal dataset
        dates = pd.date_range(start='2024-01-01', periods=10, freq='15min')
        df = pd.DataFrame({
            'open': np.ones(10) * 45000,
            'high': np.ones(10) * 45100,
            'low': np.ones(10) * 44900,
            'close': np.ones(10) * 45000,
            'volume': np.ones(10) * 1000
        }, index=dates)
        
        # All strategies should return HOLD with insufficient data
        assert sma_crossover_signal(df) == 'HOLD'
        assert rsi_reversion_signal(df) == 'HOLD'
        assert bb_breakout_signal(df) == 'HOLD'
    
    def test_strategies_with_nan_values(self, bullish_trend_data):
        """Test strategies handle NaN values properly"""
        # Insert NaN values
        data_with_nan = bullish_trend_data.copy()
        data_with_nan.loc[data_with_nan.index[10:15], 'close'] = np.nan
        
        # Strategies should handle NaN gracefully
        signal1 = sma_crossover_signal(data_with_nan)
        signal2 = rsi_reversion_signal(data_with_nan)
        signal3 = bb_breakout_signal(data_with_nan)
        
        assert signal1 in ['BUY', 'SELL', 'HOLD']
        assert signal2 in ['BUY', 'SELL', 'HOLD']
        assert signal3 in ['BUY', 'SELL', 'HOLD']
    
    @pytest.mark.parametrize("strategy_func", [
        sma_crossover_signal,
        rsi_reversion_signal,
        bb_breakout_signal
    ])
    def test_strategy_consistency(self, strategy_func, bullish_trend_data):
        """Test that strategies give consistent results with same data"""
        signal1 = strategy_func(bullish_trend_data)
        signal2 = strategy_func(bullish_trend_data)
        
        assert signal1 == signal2  # Should be deterministic