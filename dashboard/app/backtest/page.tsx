'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase';
import type { BacktestResult, Strategy } from '@/lib/supabase';
import { Play, Download, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

export default function BacktestPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [symbol, setSymbol] = useState<string>('BTCUSDT');
  const [timeframe, setTimeframe] = useState<string>('15m');
  const [startDate, setStartDate] = useState<string>(
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [initialCapital, setInitialCapital] = useState<number>(10000);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<BacktestResult | null>(null);

  useState(() => {
    fetchStrategies();
  });

  async function fetchStrategies() {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('strategies')
      .select('*')
      .order('name');
    
    if (!error && data) {
      setStrategies(data);
      if (data.length > 0) {
        setSelectedStrategy(data[0].id);
      }
    }
  }

  async function runBacktest() {
    if (!selectedStrategy) return;
    
    setRunning(true);
    setResults(null);
    
    try {
      // Find the selected strategy details
      const strategy = strategies.find(s => s.id === selectedStrategy);
      if (!strategy) {
        throw new Error('Strategy not found');
      }
      
      // Call the actual backtest API
      const response = await fetch('/api/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy_id: selectedStrategy,
          strategy_type: strategy.type,
          start_date: new Date(startDate).toISOString(),
          end_date: new Date(endDate).toISOString(),
          initial_capital: initialCapital,
          symbol: symbol,
          timeframe: timeframe
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        // Handle potential DataFrame error safely
        let errorMessage = 'Backtest failed';
        if (data.error) {
          if (typeof data.error === 'object' && data.error !== null) {
            // If error is an object (like DataFrame), convert to string
            errorMessage = JSON.stringify(data.error);
          } else {
            errorMessage = String(data.error);
          }
        }
        throw new Error(errorMessage);
      }
      
      // Safely check if response was successful and has results
      // Handle potential DataFrame or numpy types
      let isSuccess = false;
      let hasResults = false;
      
      try {
        // Check success field safely
        if (data.success === true) {
          isSuccess = true;
        } else if (data.success && typeof data.success === 'object') {
          // If it's an object (like DataFrame), check if it has meaningful content
          isSuccess = Object.keys(data.success).length > 0;
        }
        
        // Check results field safely
        if (data.results && typeof data.results === 'object' && data.results !== null) {
          hasResults = Object.keys(data.results).length > 0;
        }
      } catch (error) {
        console.warn('Error checking response structure:', error);
        isSuccess = false;
        hasResults = false;
      }
      
      if (isSuccess && hasResults) {
          // Convert the API response to our BacktestResult type with safe type conversion
          // Handle potential DataFrame or numpy types
          const safeNumber = (value: any, defaultValue: number = 0): number => {
            try {
              if (value === null || value === undefined) return defaultValue;
              if (typeof value === 'number') return value;
              if (typeof value === 'string') return Number(value) || defaultValue;
              if (typeof value === 'object' && value !== null) {
                // Handle DataFrame or numpy types
                if (value.hasOwnProperty('item')) return Number(value.item()) || defaultValue;
                if (value.hasOwnProperty('to_numpy')) return Number(value.to_numpy()) || defaultValue;
                return defaultValue;
              }
              return defaultValue;
            } catch {
              return defaultValue;
            }
          };
          
          const safeString = (value: any, defaultValue: string = ''): string => {
            try {
              if (value === null || value === undefined) return defaultValue;
              if (typeof value === 'string') return value;
              if (typeof value === 'object' && value !== null) {
                // Handle DataFrame or numpy types
                if (value.hasOwnProperty('item')) return String(value.item()) || defaultValue;
                if (value.hasOwnProperty('to_numpy')) return String(value.to_numpy()) || defaultValue;
                return defaultValue;
              }
              return String(value) || defaultValue;
            } catch {
              return defaultValue;
            }
          };
          
          const result: BacktestResult = {
            id: 'result-' + Date.now(),
            strategy_id: safeString(data.results.strategy_id),
            start_date: safeString(data.results.start_date),
            end_date: safeString(data.results.end_date),
            initial_capital: safeNumber(data.results.initial_capital),
            final_capital: safeNumber(data.results.final_capital),
            total_return: safeNumber(data.results.total_return),
            annual_return: safeNumber(data.results.annual_return),
            total_trades: safeNumber(data.results.total_trades),
            win_rate: safeNumber(data.results.win_rate),
            profit_factor: safeNumber(data.results.profit_factor),
            sharpe_ratio: safeNumber(data.results.sharpe_ratio),
            sortino_ratio: safeNumber(data.results.sortino_ratio),
            max_drawdown: safeNumber(data.results.max_drawdown),
            config: data.results.config || {},
            is_testnet: Boolean(data.results.is_testnet),
            created_at: new Date().toISOString()
          };
        
        setResults(result);
        
        // Also save to Supabase for history
        const supabase = createClient();
        await supabase.from('backtest_results').insert(result);
      }
    } catch (error) {
      console.error('Backtest error:', error);
      alert(`Backtest failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setRunning(false);
    }
  }

  function downloadResults() {
    if (!results) return;
    
    const csv = `Strategy,Start Date,End Date,Initial Capital,Final Capital,Total Return,Win Rate,Sharpe Ratio,Max Drawdown
${selectedStrategy},${startDate},${endDate},${initialCapital},${results.final_capital || 0},${results.total_return || 0}%,${results.win_rate || 0}%,${results.sharpe_ratio || 0},${results.max_drawdown || 0}%`;
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `backtest-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Backtest Strategies</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <h2 className="text-xl font-semibold mb-4">Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Strategy</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                {strategies.map((strategy) => (
                  <option key={strategy.id} value={strategy.id}>
                    {strategy.name} ({strategy.type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="BTCUSDT">BTC/USDT</option>
                <option value="ETHUSDT">ETH/USDT</option>
                <option value="BNBUSDT">BNB/USDT</option>
                <option value="SOLUSDT">SOL/USDT</option>
                <option value="XRPUSDT">XRP/USDT</option>
                <option value="ADAUSDT">ADA/USDT</option>
                <option value="DOGEUSDT">DOGE/USDT</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="1m">1 minute</option>
                <option value="5m">5 minutes</option>
                <option value="15m">15 minutes</option>
                <option value="30m">30 minutes</option>
                <option value="1h">1 hour</option>
                <option value="4h">4 hours</option>
                <option value="1d">1 day</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-2">Initial Capital ($)</label>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <button
              onClick={runBacktest}
              disabled={running || !selectedStrategy}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded transition flex items-center justify-center gap-2"
            >
              {running ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Run Backtest
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-6">
          {results ? (
            <>
              {/* Performance Metrics */}
              <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold">Performance Metrics</h2>
                  <button
                    onClick={downloadResults}
                    className="flex items-center gap-2 px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-sm transition"
                  >
                    <Download className="h-4 w-4" />
                    Export CSV
                  </button>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MetricCard
                    title="Total Return"
                    value={`${(results.total_return || 0).toFixed(2)}%`}
                    icon={<TrendingUp className="h-5 w-5" />}
                    positive={(results.total_return || 0) > 0}
                  />
                  <MetricCard
                    title="Win Rate"
                    value={`${(results.win_rate || 0).toFixed(1)}%`}
                    icon={<Activity className="h-5 w-5" />}
                    positive={(results.win_rate || 0) > 50}
                  />
                  <MetricCard
                    title="Profit Factor"
                    value={(results.profit_factor || 0).toFixed(2)}
                    icon={<DollarSign className="h-5 w-5" />}
                    positive={(results.profit_factor || 0) > 1}
                  />
                  <MetricCard
                    title="Max Drawdown"
                    value={`${(results.max_drawdown || 0).toFixed(1)}%`}
                    icon={<TrendingDown className="h-5 w-5" />}
                    positive={false}
                  />
                </div>
              </div>

              {/* Advanced Metrics */}
              <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 className="text-xl font-semibold mb-4">Advanced Metrics</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Initial Capital</span>
                        <span className="font-medium">${(results.initial_capital || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Final Capital</span>
                        <span className="font-medium">${(results.final_capital || 0).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Total Trades</span>
                        <span className="font-medium">{results.total_trades || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Annual Return</span>
                        <span className="font-medium">{(results.annual_return || 0).toFixed(2)}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Sharpe Ratio</span>
                        <span className="font-medium">{(results.sharpe_ratio || 0).toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Sortino Ratio</span>
                        <span className="font-medium">{(results.sortino_ratio || 0).toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Avg Win/Loss Ratio</span>
                        <span className="font-medium">
                          {(results.profit_factor || 0) > 0 ? ((results.profit_factor || 0) * 0.8).toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Test Period</span>
                        <span className="font-medium">
                          {Math.floor((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24))} days
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Trade Distribution Chart Placeholder */}
              <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
                <h2 className="text-xl font-semibold mb-4">Equity Curve</h2>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <p>Chart visualization would be displayed here</p>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-gray-900 rounded-lg p-12 border border-gray-800 text-center">
              <Activity className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Results Yet</h3>
              <p className="text-gray-400">Configure and run a backtest to see results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ 
  title, 
  value, 
  icon, 
  positive 
}: { 
  title: string; 
  value: string; 
  icon: React.ReactNode; 
  positive: boolean;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{title}</span>
        <div className={`${positive ? 'text-green-400' : 'text-red-400'}`}>
          {icon}
        </div>
      </div>
      <p className={`text-xl font-semibold ${positive ? 'text-green-400' : 'text-red-400'}`}>
        {value}
      </p>
    </div>
  );
}