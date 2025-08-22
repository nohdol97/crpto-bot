'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase';
import type { Trade } from '@/lib/supabase';
import { ArrowUp, ArrowDown, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'FILLED' | 'CANCELED' | 'REJECTED'>('ALL');
  const [dateRange, setDateRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d');

  useEffect(() => {
    fetchTrades();
    
    // Set up real-time subscription
    const supabase = createClient();
    
    const subscription = supabase
      .channel('trades-channel')
      .on('postgres_changes', { 
        event: 'INSERT', 
        schema: 'public', 
        table: 'trades' 
      }, () => {
        fetchTrades();
      })
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [filter, dateRange]);

  async function fetchTrades() {
    const supabase = createClient();
    
    let query = supabase
      .from('trades')
      .select('*')
      .order('order_time', { ascending: false });
    
    // Apply status filter
    if (filter !== 'ALL') {
      query = query.eq('status', filter);
    }
    
    // Apply date range filter
    if (dateRange !== 'all') {
      const now = new Date();
      let startDate = new Date();
      
      switch (dateRange) {
        case '24h':
          startDate.setDate(now.getDate() - 1);
          break;
        case '7d':
          startDate.setDate(now.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(now.getDate() - 30);
          break;
      }
      
      query = query.gte('order_time', startDate.toISOString());
    }
    
    const { data, error } = await query.limit(100);
    
    if (!error && data) {
      setTrades(data);
    }
    setLoading(false);
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'FILLED':
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'CANCELED':
        return <XCircle className="h-4 w-4 text-gray-400" />;
      case 'REJECTED':
        return <XCircle className="h-4 w-4 text-red-400" />;
      case 'NEW':
        return <Clock className="h-4 w-4 text-blue-400" />;
      case 'PARTIALLY_FILLED':
        return <AlertCircle className="h-4 w-4 text-yellow-400" />;
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateFee = (trade: Trade) => {
    if (trade.commission) {
      return trade.commission.toFixed(4);
    }
    return '0.0000';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Trade History</h1>
        
        <div className="flex gap-4">
          {/* Date Range Filter */}
          <div className="flex gap-2">
            {(['24h', '7d', '30d', 'all'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setDateRange(range)}
                className={`px-3 py-1 rounded text-sm transition ${
                  dateRange === range 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {range === 'all' ? 'All Time' : range}
              </button>
            ))}
          </div>
          
          {/* Status Filter */}
          <div className="flex gap-2">
            {(['ALL', 'FILLED', 'CANCELED', 'REJECTED'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-3 py-1 rounded text-sm transition ${
                  filter === status 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Trades Table */}
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-gray-800">
                <th className="pb-3">Time</th>
                <th className="pb-3">Symbol</th>
                <th className="pb-3">Side</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Price</th>
                <th className="pb-3">Quantity</th>
                <th className="pb-3">Filled</th>
                <th className="pb-3">Total</th>
                <th className="pb-3">Fee</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {trades.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-gray-500">
                    No trades found
                  </td>
                </tr>
              ) : (
                trades.map((trade) => {
                  const total = (trade.executed_price || trade.price) * trade.executed_quantity;
                  return (
                    <tr key={trade.id} className="border-t border-gray-800">
                      <td className="py-3 text-gray-400">
                        {formatDate(trade.order_time)}
                      </td>
                      <td className="py-3 font-medium">{trade.symbol}</td>
                      <td className="py-3">
                        <div className="flex items-center gap-1">
                          {trade.side === 'BUY' ? (
                            <ArrowUp className="h-4 w-4 text-green-400" />
                          ) : (
                            <ArrowDown className="h-4 w-4 text-red-400" />
                          )}
                          <span className={trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                            {trade.side}
                          </span>
                        </div>
                      </td>
                      <td className="py-3">
                        <div className="flex items-center gap-1">
                          {getStatusIcon(trade.status)}
                          <span className="text-gray-300">{trade.status}</span>
                        </div>
                      </td>
                      <td className="py-3">${trade.price.toFixed(2)}</td>
                      <td className="py-3">{trade.quantity.toFixed(4)}</td>
                      <td className="py-3">
                        <span className={trade.executed_quantity > 0 ? 'text-green-400' : 'text-gray-500'}>
                          {trade.executed_quantity.toFixed(4)}
                        </span>
                      </td>
                      <td className="py-3 font-medium">
                        ${total > 0 ? total.toFixed(2) : '0.00'}
                      </td>
                      <td className="py-3 text-gray-400">
                        ${calculateFee(trade)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        
        {/* Summary Stats */}
        {trades.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-800">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-gray-400 text-sm">Total Trades</p>
                <p className="text-xl font-semibold mt-1">{trades.length}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Buy Orders</p>
                <p className="text-xl font-semibold mt-1 text-green-400">
                  {trades.filter(t => t.side === 'BUY').length}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Sell Orders</p>
                <p className="text-xl font-semibold mt-1 text-red-400">
                  {trades.filter(t => t.side === 'SELL').length}
                </p>
              </div>
              <div>
                <p className="text-gray-400 text-sm">Fill Rate</p>
                <p className="text-xl font-semibold mt-1">
                  {((trades.filter(t => t.status === 'FILLED').length / trades.length) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}