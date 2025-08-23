"""
API server for the crypto trading bot dashboard
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

from config import cfg
from exchange.binance_client import BinanceSpot
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies import sma_crossover, rsi_reversion, bb_breakout
from core.supabase_client import supabase_manager
from utils.logger import logger

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:3001"])

# Initialize Binance client
spot = BinanceSpot(cfg.binance_api_key, cfg.binance_api_secret, cfg.binance_testnet)

# Strategy map
STRATEGY_MAP = {
    'sma_crossover': sma_crossover,
    'rsi_reversion': rsi_reversion,
    'bb_breakout': bb_breakout
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'is_testnet': cfg.binance_testnet
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'is_testnet': cfg.binance_testnet,
        'network': 'testnet' if cfg.binance_testnet else 'mainnet',
        'base_asset': cfg.base_asset,
        'quote_asset': cfg.quote_asset,
        'symbol': cfg.symbol,
        'timeframe': cfg.timeframe
    })

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtest for a strategy"""
    try:
        data = request.json
        
        # Validate input
        required_fields = ['strategy_id', 'strategy_type', 'start_date', 'end_date', 'initial_capital']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parse dates
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        # Get symbol and timeframe
        symbol = data.get('symbol', cfg.symbol)
        timeframe = data.get('timeframe', cfg.timeframe)
        
        # Fetch historical data
        logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}", module="api")
        
        # Calculate the number of days
        days = (end_date - start_date).days
        if days <= 0:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        # Fetch klines from Binance (returns DataFrame)
        df = spot.klines(symbol, timeframe, limit=min(days * 24, 1000))  # Adjust based on timeframe
        
        if df is None or df.empty:
            return jsonify({'error': 'Failed to fetch historical data'}), 500
        
        # Convert open_time to datetime and set as index
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
        df.set_index('open_time', inplace=True)
        
        # Filter by date range
        df = df.loc[start_date:end_date]
        
        if df.empty:
            return jsonify({'error': 'No data available for the specified date range'}), 400
        
        # Get strategy module
        strategy_type = data['strategy_type']
        if strategy_type not in STRATEGY_MAP:
            return jsonify({'error': f'Unknown strategy type: {strategy_type}'}), 400
        
        strategy_module = STRATEGY_MAP[strategy_type]
        
        # Create backtest config
        config = BacktestConfig(
            initial_capital=float(data['initial_capital']),
            commission_rate=float(data.get('commission', 0.001)),
            slippage_rate=float(data.get('slippage', 0.001)),
            position_size=float(data.get('position_size', 0.1)),
            max_positions=int(data.get('max_positions', 1)),
            stop_loss_pct=float(data.get('stop_loss', 0.02)) if data.get('stop_loss') else 0.02,
            take_profit_pct=float(data.get('take_profit', 0.05)) if data.get('take_profit') else 0.04
        )
        
        # Run backtest
        logger.info(f"Running backtest for {strategy_type} strategy", module="api")
        engine = BacktestEngine(config)
        
        # Define strategy function wrapper
        def strategy_func(data, index):
            # Call the strategy's signal function
            if index < 50:  # Need enough data for indicators
                return 'HOLD'
            
            df_slice = data.iloc[:index+1]
            signal_result = strategy_module.signal(df_slice)
            
            if signal_result.get('buy'):
                return 'BUY'
            elif signal_result.get('sell'):
                return 'SELL'
            else:
                return 'HOLD'
        
        # Run the backtest
        results = engine.run(
            data=df,
            strategy_func=strategy_func,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Extract metrics from results
        metrics = results.get('metrics', {})
        
        # Calculate additional metrics
        days = (end_date - start_date).days
        total_return = metrics.get('total_return', 0)
        annual_return = 0
        if days > 0:
            annual_return = ((1 + total_return/100) ** (365/days) - 1) * 100
        
        # Calculate Sortino ratio manually if not available
        sortino_ratio = metrics.get('sortino_ratio', 0)
        if sortino_ratio == 0 and len(results.get('equity_curve', [])) > 1:
            equity_series = pd.Series(results['equity_curve'])
            returns = equity_series.pct_change().dropna()
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0 and downside_returns.std() > 0:
                sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252)
        
        # Save results to database
        result_data = {
            'strategy_id': data['strategy_id'],
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat(),
            'initial_capital': config.initial_capital,
            'final_capital': metrics.get('final_capital', config.initial_capital),
            'total_return': metrics.get('total_return', 0),
            'annual_return': round(annual_return, 2),
            'total_trades': metrics.get('total_trades', 0),
            'win_rate': metrics.get('win_rate', 0),
            'profit_factor': metrics.get('profit_factor', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'sortino_ratio': round(sortino_ratio, 4),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'config': {
                'strategy_type': strategy_type,
                'symbol': symbol,
                'timeframe': timeframe,
                'commission': config.commission_rate,
                'position_size': config.position_size
            },
            'is_testnet': cfg.binance_testnet
        }
        
        # Save to database (optional - can be commented out if Supabase is not configured)
        try:
            supabase_manager.client.table("backtest_results").insert(result_data).execute()
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}", module="api")
        
        logger.info(f"Backtest completed: {metrics.get('total_return', 0):.2f}% return", module="api")
        
        # Ensure response is always a proper JSON structure
        response_data = {
            'success': True,
            'results': result_data
        }
        
        # Convert any potential DataFrame or numpy types to native Python types
        import json
        try:
            # Test if the response can be serialized
            json.dumps(response_data)
            return jsonify(response_data)
        except (TypeError, ValueError) as e:
            logger.error(f"Response serialization error: {e}", module="api")
            # Fallback to safe response
            safe_response = {
                'success': True,
                'results': {
                    'strategy_id': data['strategy_id'],
                    'start_date': start_date.date().isoformat(),
                    'end_date': end_date.date().isoformat(),
                    'initial_capital': config.initial_capital,
                    'final_capital': config.initial_capital,
                    'total_return': 0,
                    'annual_return': 0,
                    'total_trades': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'sharpe_ratio': 0,
                    'sortino_ratio': 0,
                    'max_drawdown': 0,
                    'config': {
                        'strategy_type': strategy_type,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'commission': config.commission_rate,
                        'position_size': config.position_size
                    },
                    'is_testnet': cfg.binance_testnet
                }
            }
            return jsonify(safe_response)
        
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}", module="api")
        # Ensure error is always a string, not a DataFrame or other object
        error_message = str(e)
        if hasattr(e, '__dict__'):
            # If it's a complex object, try to extract meaningful error info
            error_message = getattr(e, 'message', str(e))
        
        return jsonify({'error': error_message}), 500

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Get available strategies"""
    try:
        # Use sync version for Flask
        response = supabase_manager.client.table("strategies").select("*").eq("status", "ACTIVE").execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Get current account balance"""
    try:
        account = spot.account()
        if not account:
            return jsonify({'error': 'Failed to fetch account info'}), 500
        
        # Extract USDT balance
        usdt_balance = 0
        for balance in account.get('balances', []):
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free']) + float(balance['locked'])
                break
        
        return jsonify({
            'total_balance_usdt': usdt_balance,
            'is_testnet': cfg.binance_testnet
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)