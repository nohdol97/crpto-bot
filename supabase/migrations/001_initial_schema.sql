-- Supabase Database Schema for Crypto Trading Bot

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum types
CREATE TYPE trade_side AS ENUM ('BUY', 'SELL');
CREATE TYPE position_status AS ENUM ('OPEN', 'CLOSED', 'PARTIALLY_CLOSED');
CREATE TYPE order_status AS ENUM ('NEW', 'FILLED', 'PARTIALLY_FILLED', 'CANCELED', 'REJECTED');
CREATE TYPE strategy_status AS ENUM ('ACTIVE', 'PAUSED', 'DISABLED');
CREATE TYPE log_level AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL');

-- Trading strategies configuration
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- 'sma_crossover', 'rsi_reversion', 'bb_breakout'
    status strategy_status DEFAULT 'ACTIVE',
    config JSONB DEFAULT '{}', -- Strategy-specific parameters
    allocation_percent DECIMAL(5,2) DEFAULT 0, -- Portfolio allocation percentage
    max_positions INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Market data cache
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_time TIMESTAMPTZ NOT NULL,
    open DECIMAL(20,8) NOT NULL,
    high DECIMAL(20,8) NOT NULL,
    low DECIMAL(20,8) NOT NULL,
    close DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    quote_volume DECIMAL(20,8),
    trades_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timeframe, open_time)
);

-- Trading positions
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    strategy_id UUID REFERENCES strategies(id),
    side trade_side NOT NULL,
    status position_status DEFAULT 'OPEN',
    
    -- Entry details
    entry_price DECIMAL(20,8) NOT NULL,
    entry_quantity DECIMAL(20,8) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    entry_order_id VARCHAR(100),
    
    -- Exit details
    exit_price DECIMAL(20,8),
    exit_quantity DECIMAL(20,8),
    exit_time TIMESTAMPTZ,
    exit_order_id VARCHAR(100),
    
    -- Risk management
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    trailing_stop_percent DECIMAL(5,2),
    
    -- Performance metrics
    pnl DECIMAL(20,8) DEFAULT 0,
    pnl_percent DECIMAL(10,4) DEFAULT 0,
    fees DECIMAL(20,8) DEFAULT 0,
    
    -- Metadata
    notes TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trade history (individual trades/orders)
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id UUID REFERENCES positions(id),
    strategy_id UUID REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    side trade_side NOT NULL,
    order_id VARCHAR(100) UNIQUE,
    status order_status DEFAULT 'NEW',
    
    -- Order details
    price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    executed_quantity DECIMAL(20,8) DEFAULT 0,
    executed_price DECIMAL(20,8),
    
    -- Fees and costs
    commission DECIMAL(20,8) DEFAULT 0,
    commission_asset VARCHAR(10),
    
    -- Timestamps
    order_time TIMESTAMPTZ DEFAULT NOW(),
    executed_time TIMESTAMPTZ,
    
    -- Additional info
    order_type VARCHAR(20) DEFAULT 'MARKET', -- MARKET, LIMIT, STOP_LOSS, etc
    time_in_force VARCHAR(10) DEFAULT 'GTC',
    response JSONB, -- Raw API response
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance tracking
CREATE TABLE performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES strategies(id),
    date DATE NOT NULL,
    
    -- Daily metrics
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    
    -- P&L metrics
    gross_pnl DECIMAL(20,8) DEFAULT 0,
    fees DECIMAL(20,8) DEFAULT 0,
    net_pnl DECIMAL(20,8) DEFAULT 0,
    
    -- Statistical metrics
    win_rate DECIMAL(5,2) DEFAULT 0,
    avg_win DECIMAL(20,8) DEFAULT 0,
    avg_loss DECIMAL(20,8) DEFAULT 0,
    profit_factor DECIMAL(10,2) DEFAULT 0,
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    
    -- Portfolio metrics
    starting_balance DECIMAL(20,8),
    ending_balance DECIMAL(20,8),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(strategy_id, date)
);

-- System logs
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    level log_level NOT NULL,
    module VARCHAR(100),
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    error_trace TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Backtesting results
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id UUID REFERENCES strategies(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(20,8) NOT NULL,
    final_capital DECIMAL(20,8) NOT NULL,
    
    -- Performance metrics
    total_return DECIMAL(10,4),
    annual_return DECIMAL(10,4),
    total_trades INTEGER,
    win_rate DECIMAL(5,2),
    profit_factor DECIMAL(10,2),
    sharpe_ratio DECIMAL(10,4),
    sortino_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    
    -- Trade statistics
    avg_trade_return DECIMAL(10,4),
    best_trade DECIMAL(20,8),
    worst_trade DECIMAL(20,8),
    avg_holding_time INTERVAL,
    
    -- Configuration used
    config JSONB NOT NULL,
    trades JSONB, -- Detailed trade log
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Account balance snapshots
CREATE TABLE balance_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    total_balance_usdt DECIMAL(20,8) NOT NULL,
    free_balance_usdt DECIMAL(20,8) NOT NULL,
    locked_balance_usdt DECIMAL(20,8) NOT NULL,
    assets JSONB DEFAULT '{}', -- Detailed asset breakdown
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts and notifications
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL, -- 'trade_executed', 'stop_loss_hit', 'error', etc
    severity VARCHAR(20) DEFAULT 'INFO', -- INFO, WARNING, ERROR, CRITICAL
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_strategy ON positions(strategy_id);
CREATE INDEX idx_positions_created_at ON positions(created_at DESC);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_position ON trades(position_id);
CREATE INDEX idx_trades_strategy ON trades(strategy_id);
CREATE INDEX idx_trades_order_time ON trades(order_time DESC);

CREATE INDEX idx_market_data_symbol_timeframe ON market_data(symbol, timeframe);
CREATE INDEX idx_market_data_open_time ON market_data(open_time DESC);

CREATE INDEX idx_performance_strategy_date ON performance(strategy_id, date DESC);
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_logs_level ON logs(level);

CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX idx_alerts_is_read ON alerts(is_read);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS)
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE balance_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth strategy)
-- For now, we'll use service role for all operations
CREATE POLICY "Enable all access for service role" ON strategies
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON positions
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON trades
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON performance
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON logs
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON backtest_results
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON balance_snapshots
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON alerts
    FOR ALL USING (true);
CREATE POLICY "Enable all access for service role" ON market_data
    FOR ALL USING (true);

-- Insert default strategies
INSERT INTO strategies (name, type, status, config, allocation_percent) VALUES
    ('SMA Crossover', 'sma_crossover', 'ACTIVE', 
     '{"fast_period": 20, "slow_period": 50, "adx_threshold": 20}', 33.33),
    ('RSI Reversion', 'rsi_reversion', 'ACTIVE',
     '{"rsi_period": 14, "oversold": 30, "overbought": 70, "volume_multiplier": 1.5}', 33.33),
    ('Bollinger Breakout', 'bb_breakout', 'ACTIVE',
     '{"period": 20, "std_dev": 2.0, "squeeze_threshold": 0.01}', 33.34);

-- Create view for active positions summary
CREATE VIEW active_positions_summary AS
SELECT 
    p.symbol,
    p.side,
    p.entry_price,
    p.entry_quantity,
    p.stop_loss,
    p.take_profit,
    p.pnl,
    p.pnl_percent,
    s.name as strategy_name,
    p.entry_time,
    p.created_at
FROM positions p
LEFT JOIN strategies s ON p.strategy_id = s.id
WHERE p.status = 'OPEN'
ORDER BY p.created_at DESC;

-- Create view for daily performance summary
CREATE VIEW daily_performance_summary AS
SELECT 
    date,
    SUM(total_trades) as total_trades,
    SUM(winning_trades) as winning_trades,
    SUM(losing_trades) as losing_trades,
    SUM(net_pnl) as total_pnl,
    AVG(win_rate) as avg_win_rate,
    MAX(max_drawdown) as max_drawdown
FROM performance
GROUP BY date
ORDER BY date DESC;