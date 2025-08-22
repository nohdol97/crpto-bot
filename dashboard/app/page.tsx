'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase';
import type { Position, Performance, Alert, Strategy } from '@/lib/supabase';
import { TrendingUp, AlertCircle, Activity, DollarSign } from 'lucide-react';

export default function Dashboard() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [performance, setPerformance] = useState<Performance[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function init() {
      await Promise.all([
        fetchPositions(),
        fetchPerformance(),
        fetchAlerts(),
        fetchStrategies()
      ]);
      setLoading(false);
    }
    
    init();
    
    // Set up real-time subscriptions
    const supabase = createClient();
    
    const positionsSubscription = supabase
      .channel('positions-channel')
      .on('postgres_changes', { 
        event: '*', 
        schema: 'public', 
        table: 'positions' 
      }, () => {
        fetchPositions();
      })
      .subscribe();

    const alertsSubscription = supabase
      .channel('alerts-channel')
      .on('postgres_changes', { 
        event: 'INSERT', 
        schema: 'public', 
        table: 'alerts' 
      }, () => {
        fetchAlerts();
      })
      .subscribe();

    return () => {
      positionsSubscription.unsubscribe();
      alertsSubscription.unsubscribe();
    };
  }, []);

  async function fetchPositions() {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('positions')
      .select('*, strategies(name, type)')
      .eq('status', 'OPEN')
      .order('created_at', { ascending: false });
    
    if (!error && data) {
      setPositions(data);
    }
  }

  async function fetchPerformance() {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('performance')
      .select('*')
      .order('date', { ascending: false })
      .limit(7);
    
    if (!error && data) {
      setPerformance(data);
    }
  }

  async function fetchAlerts() {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('alerts')
      .select('*')
      .eq('is_read', false)
      .order('created_at', { ascending: false })
      .limit(5);
    
    if (!error && data) {
      setAlerts(data);
    }
  }

  async function fetchStrategies() {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('strategies')
      .select('*')
      .eq('status', 'ACTIVE');
    
    if (!error && data) {
      setStrategies(data);
    }
  }

  const totalPnL = positions.reduce((sum, pos) => sum + (pos.pnl || 0), 0);
  const winRate = performance[0]?.win_rate || 0;
  const totalTrades = performance.reduce((sum, p) => sum + p.total_trades, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total P&L"
          value={`$${totalPnL.toFixed(2)}`}
          change={totalPnL > 0 ? '+' : ''}
          changeType={totalPnL > 0 ? 'positive' : 'negative'}
          icon={<DollarSign className="h-5 w-5" />}
        />
        <StatCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          change=""
          changeType={winRate > 50 ? 'positive' : 'negative'}
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <StatCard
          title="Open Positions"
          value={positions.length.toString()}
          change=""
          changeType="neutral"
          icon={<Activity className="h-5 w-5" />}
        />
        <StatCard
          title="Total Trades"
          value={totalTrades.toString()}
          change=""
          changeType="neutral"
          icon={<Activity className="h-5 w-5" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Positions Table */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <h2 className="text-xl font-semibold mb-4">Open Positions</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-gray-400 text-sm">
                    <th className="pb-3">Symbol</th>
                    <th className="pb-3">Side</th>
                    <th className="pb-3">Entry Price</th>
                    <th className="pb-3">Quantity</th>
                    <th className="pb-3">P&L</th>
                    <th className="pb-3">Strategy</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {positions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-gray-500">
                        No open positions
                      </td>
                    </tr>
                  ) : (
                    positions.map((position) => (
                      <tr key={position.id} className="border-t border-gray-800">
                        <td className="py-3">{position.symbol}</td>
                        <td className="py-3">
                          <span className={`px-2 py-1 rounded text-xs ${
                            position.side === 'BUY' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                          }`}>
                            {position.side}
                          </span>
                        </td>
                        <td className="py-3">${position.entry_price.toFixed(2)}</td>
                        <td className="py-3">{position.entry_quantity.toFixed(4)}</td>
                        <td className="py-3">
                          <span className={position.pnl && position.pnl > 0 ? 'text-green-400' : 'text-red-400'}>
                            ${position.pnl?.toFixed(2) || '0.00'}
                          </span>
                        </td>
                        <td className="py-3 text-gray-400">
                          {position.strategies?.name || 'N/A'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Alerts & Strategies */}
        <div className="space-y-6">
          {/* Alerts */}
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <h2 className="text-xl font-semibold mb-4">Recent Alerts</h2>
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <p className="text-gray-500 text-sm">No new alerts</p>
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="flex items-start space-x-3">
                    <AlertCircle className={`h-5 w-5 mt-0.5 ${
                      alert.severity === 'ERROR' ? 'text-red-400' :
                      alert.severity === 'WARNING' ? 'text-yellow-400' :
                      'text-blue-400'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{alert.title}</p>
                      <p className="text-xs text-gray-400">{alert.message}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Active Strategies */}
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <h2 className="text-xl font-semibold mb-4">Active Strategies</h2>
            <div className="space-y-3">
              {strategies.map((strategy) => (
                <div key={strategy.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{strategy.name}</p>
                    <p className="text-xs text-gray-400">{strategy.type}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm">{strategy.allocation_percent}%</p>
                    <p className="text-xs text-gray-400">allocation</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ 
  title, 
  value, 
  change, 
  changeType, 
  icon 
}: { 
  title: string; 
  value: string; 
  change: string; 
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-semibold mt-1">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${
              changeType === 'positive' ? 'text-green-400' : 
              changeType === 'negative' ? 'text-red-400' : 
              'text-gray-400'
            }`}>
              {change}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${
          changeType === 'positive' ? 'bg-green-900/20 text-green-400' :
          changeType === 'negative' ? 'bg-red-900/20 text-red-400' :
          'bg-gray-800 text-gray-400'
        }`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
