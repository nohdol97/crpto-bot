-- Add is_testnet field to distinguish between testnet and mainnet trades

-- Add is_testnet to positions table
ALTER TABLE positions 
ADD COLUMN is_testnet BOOLEAN DEFAULT true;

-- Add is_testnet to trades table
ALTER TABLE trades 
ADD COLUMN is_testnet BOOLEAN DEFAULT true;

-- Add is_testnet to balance_snapshots table
ALTER TABLE balance_snapshots 
ADD COLUMN is_testnet BOOLEAN DEFAULT true;

-- Add is_testnet to performance table
ALTER TABLE performance 
ADD COLUMN is_testnet BOOLEAN DEFAULT true;

-- Add is_testnet to backtest_results table (backtests are always simulated, but we track which network config was used)
ALTER TABLE backtest_results 
ADD COLUMN is_testnet BOOLEAN DEFAULT true;

-- Create indexes for better query performance
CREATE INDEX idx_positions_is_testnet ON positions(is_testnet);
CREATE INDEX idx_trades_is_testnet ON trades(is_testnet);
CREATE INDEX idx_balance_snapshots_is_testnet ON balance_snapshots(is_testnet);
CREATE INDEX idx_performance_is_testnet ON performance(is_testnet);

-- Update the active_positions_summary view to include network info
DROP VIEW IF EXISTS active_positions_summary;
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
    p.is_testnet,
    s.name as strategy_name,
    p.entry_time,
    p.created_at
FROM positions p
LEFT JOIN strategies s ON p.strategy_id = s.id
WHERE p.status = 'OPEN'
ORDER BY p.created_at DESC;

-- Update the daily_performance_summary view to separate testnet and mainnet
DROP VIEW IF EXISTS daily_performance_summary;
CREATE VIEW daily_performance_summary AS
SELECT 
    date,
    is_testnet,
    SUM(total_trades) as total_trades,
    SUM(winning_trades) as winning_trades,
    SUM(losing_trades) as losing_trades,
    SUM(net_pnl) as total_pnl,
    AVG(win_rate) as avg_win_rate,
    MAX(max_drawdown) as max_drawdown
FROM performance
GROUP BY date, is_testnet
ORDER BY date DESC;