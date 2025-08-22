'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase';
import type { BacktestResult, Strategy } from '@/lib/supabase';
import { Play, Download, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';

export default function BacktestPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
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
    
    // Simulate backtest run (in real implementation, this would call your Python backend)
    setTimeout(() => {
      const mockResult: BacktestResult = {
        id: 'mock-' + Date.now(),
        strategy_id: selectedStrategy,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        final_capital: initialCapital * 1.23,
        total_return: 23.45,
        annual_return: 45.2,
        total_trades: 156,
        win_rate: 58.3,
        profit_factor: 1.85,
        sharpe_ratio: 1.45,
        sortino_ratio: 2.1,
        max_drawdown: 12.5,
        config: {},
        created_at: new Date().toISOString()
      };
      
      setResults(mockResult);
      setRunning(false);
    }, 3000);
  }

  function downloadResults() {
    if (!results) return;
    
    const csv = `Strategy,Start Date,End Date,Initial Capital,Final Capital,Total Return,Win Rate,Sharpe Ratio,Max Drawdown
${selectedStrategy},${startDate},${endDate},${initialCapital},${results.final_capital},${results.total_return}%,${results.win_rate}%,${results.sharpe_ratio},${results.max_drawdown}%`;
    
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
                    value={`${results.total_return.toFixed(2)}%`}
                    icon={<TrendingUp className="h-5 w-5" />}
                    positive={results.total_return > 0}
                  />
                  <MetricCard
                    title="Win Rate"
                    value={`${results.win_rate.toFixed(1)}%`}
                    icon={<Activity className="h-5 w-5" />}
                    positive={results.win_rate > 50}
                  />
                  <MetricCard
                    title="Profit Factor"
                    value={results.profit_factor.toFixed(2)}
                    icon={<DollarSign className="h-5 w-5" />}
                    positive={results.profit_factor > 1}
                  />
                  <MetricCard
                    title="Max Drawdown"
                    value={`${results.max_drawdown?.toFixed(1) || '0.0'}%`}
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
                        <span className="font-medium">${results.initial_capital.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Final Capital</span>
                        <span className="font-medium">${results.final_capital.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Total Trades</span>
                        <span className="font-medium">{results.total_trades}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Annual Return</span>
                        <span className="font-medium">{results.annual_return?.toFixed(2) || '0.00'}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Sharpe Ratio</span>
                        <span className="font-medium">{results.sharpe_ratio?.toFixed(2) || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Sortino Ratio</span>
                        <span className="font-medium">{results.sortino_ratio?.toFixed(2) || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Avg Win/Loss Ratio</span>
                        <span className="font-medium">
                          {results.profit_factor > 0 ? (results.profit_factor * 0.8).toFixed(2) : 'N/A'}
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