"""
Unit tests for technical indicators
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.indicators import (
    calculate_sma, calculate_ema, calculate_rsi,
    calculate_bollinger_bands, calculate_atr, calculate_adx,
    calculate_macd, calculate_stochastic
)

class TestIndicators:
    """Test suite for technical indicators"""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample OHLCV data for testing"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='15min')
        np.random.seed(42)
        
        # Generate realistic price data
        close_prices = 45000 + np.cumsum(np.random.randn(100) * 100)
        
        df = pd.DataFrame({
            'open': close_prices + np.random.randn(100) * 50,
            'high': close_prices + abs(np.random.randn(100) * 100),
            'low': close_prices - abs(np.random.randn(100) * 100),
            'close': close_prices,
            'volume': np.random.uniform(100, 1000, 100)
        }, index=dates)
        
        # Ensure high is highest and low is lowest
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        return df
    
    def test_sma_calculation(self, sample_data):
        """Test Simple Moving Average calculation"""
        sma_20 = calculate_sma(sample_data['close'], 20)
        
        assert len(sma_20) == len(sample_data)
        assert sma_20.isna().sum() == 19  # First 19 values should be NaN
        assert not sma_20[20:].isna().any()  # No NaN after period
        
        # Manual calculation check for one point
        manual_sma = sample_data['close'][0:20].mean()
        assert abs(sma_20.iloc[19] - manual_sma) < 0.01
    
    def test_ema_calculation(self, sample_data):
        """Test Exponential Moving Average calculation"""
        ema_20 = calculate_ema(sample_data['close'], 20)
        
        assert len(ema_20) == len(sample_data)
        assert not ema_20[20:].isna().any()
        
        # EMA should react faster to recent prices than SMA
        sma_20 = calculate_sma(sample_data['close'], 20)
        assert ema_20.iloc[-1] != sma_20.iloc[-1]
    
    def test_rsi_calculation(self, sample_data):
        """Test RSI calculation"""
        rsi = calculate_rsi(sample_data['close'], 14)
        
        assert len(rsi) == len(sample_data)
        assert not rsi[14:].isna().any()
        
        # RSI should be between 0 and 100
        valid_rsi = rsi[~rsi.isna()]
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_bollinger_bands(self, sample_data):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = calculate_bollinger_bands(sample_data['close'], 20, 2)
        
        assert len(upper) == len(sample_data)
        assert len(middle) == len(sample_data)
        assert len(lower) == len(sample_data)
        
        # Upper band should be above middle, lower below
        valid_idx = ~upper.isna()
        assert (upper[valid_idx] > middle[valid_idx]).all()
        assert (lower[valid_idx] < middle[valid_idx]).all()
        
        # Middle band should be SMA
        sma_20 = calculate_sma(sample_data['close'], 20)
        pd.testing.assert_series_equal(middle, sma_20)
    
    def test_atr_calculation(self, sample_data):
        """Test Average True Range calculation"""
        atr = calculate_atr(sample_data, 14)
        
        assert len(atr) == len(sample_data)
        assert not atr[14:].isna().any()
        
        # ATR should be positive
        valid_atr = atr[~atr.isna()]
        assert (valid_atr > 0).all()
    
    def test_adx_calculation(self, sample_data):
        """Test ADX calculation"""
        adx = calculate_adx(sample_data, 14)
        
        assert len(adx) == len(sample_data)
        
        # ADX should be between 0 and 100
        valid_adx = adx[~adx.isna()]
        assert (valid_adx >= 0).all()
        assert (valid_adx <= 100).all()
    
    def test_macd_calculation(self, sample_data):
        """Test MACD calculation"""
        macd_line, signal_line, histogram = calculate_macd(
            sample_data['close'], 12, 26, 9
        )
        
        assert len(macd_line) == len(sample_data)
        assert len(signal_line) == len(sample_data)
        assert len(histogram) == len(sample_data)
        
        # Histogram should be MACD - Signal
        valid_idx = ~histogram.isna()
        calculated_hist = macd_line[valid_idx] - signal_line[valid_idx]
        pd.testing.assert_series_equal(
            histogram[valid_idx], 
            calculated_hist,
            check_names=False
        )
    
    def test_stochastic_calculation(self, sample_data):
        """Test Stochastic oscillator calculation"""
        k_percent, d_percent = calculate_stochastic(sample_data, 14, 3)
        
        assert len(k_percent) == len(sample_data)
        assert len(d_percent) == len(sample_data)
        
        # %K and %D should be between 0 and 100
        valid_k = k_percent[~k_percent.isna()]
        valid_d = d_percent[~d_percent.isna()]
        
        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
        assert (valid_d >= 0).all()
        assert (valid_d <= 100).all()
    
    def test_indicators_with_insufficient_data(self):
        """Test indicators with insufficient data"""
        # Create very small dataset
        small_data = pd.Series([100, 101, 102])
        
        # Should handle gracefully
        sma = calculate_sma(small_data, 5)
        assert sma.isna().all()  # All NaN because period > data length
        
        rsi = calculate_rsi(small_data, 14)
        assert rsi.isna().all()
    
    def test_indicators_with_nan_values(self, sample_data):
        """Test indicators handle NaN values properly"""
        # Insert some NaN values
        data_with_nan = sample_data['close'].copy()
        data_with_nan[10:15] = np.nan
        
        # Should still calculate where possible
        sma = calculate_sma(data_with_nan, 5)
        assert not sma[20:].isna().all()  # Should have some valid values