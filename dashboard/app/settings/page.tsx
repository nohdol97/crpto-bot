'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase';
import type { Strategy } from '@/lib/supabase';
import { Save, Plus, Trash2, Pause, Play, Settings } from 'lucide-react';

export default function SettingsPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchStrategies();
  }, []);

  async function fetchStrategies() {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('strategies')
      .select('*')
      .order('name');
    
    if (!error && data) {
      setStrategies(data);
      if (data.length > 0) {
        setSelectedStrategy(data[0]);
      }
    }
    setLoading(false);
  }

  async function saveStrategy() {
    if (!selectedStrategy) return;
    
    setSaving(true);
    const supabase = createClient();
    
    const { error } = await supabase
      .from('strategies')
      .update({
        name: selectedStrategy.name,
        type: selectedStrategy.type,
        status: selectedStrategy.status,
        config: selectedStrategy.config,
        allocation_percent: selectedStrategy.allocation_percent,
        max_positions: selectedStrategy.max_positions,
        updated_at: new Date().toISOString()
      })
      .eq('id', selectedStrategy.id);
    
    if (!error) {
      await fetchStrategies();
    }
    setSaving(false);
  }

  async function toggleStrategyStatus(strategy: Strategy) {
    const newStatus = strategy.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    const supabase = createClient();
    
    const { error } = await supabase
      .from('strategies')
      .update({ status: newStatus })
      .eq('id', strategy.id);
    
    if (!error) {
      await fetchStrategies();
    }
  }

  async function deleteStrategy(id: string) {
    if (!confirm('Are you sure you want to delete this strategy?')) return;
    
    const supabase = createClient();
    const { error } = await supabase
      .from('strategies')
      .delete()
      .eq('id', id);
    
    if (!error) {
      await fetchStrategies();
      if (strategies.length > 1) {
        setSelectedStrategy(strategies.find(s => s.id !== id) || null);
      } else {
        setSelectedStrategy(null);
      }
    }
  }

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
        <h1 className="text-2xl font-bold">Strategy Settings</h1>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition">
          <Plus className="h-4 w-4" />
          New Strategy
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Strategy List */}
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <h2 className="text-xl font-semibold mb-4">Strategies</h2>
          
          <div className="space-y-2">
            {strategies.map((strategy) => (
              <div
                key={strategy.id}
                onClick={() => setSelectedStrategy(strategy)}
                className={`p-3 rounded cursor-pointer transition ${
                  selectedStrategy?.id === strategy.id
                    ? 'bg-blue-600 bg-opacity-20 border border-blue-600'
                    : 'bg-gray-800 hover:bg-gray-700 border border-gray-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{strategy.name}</p>
                    <p className="text-sm text-gray-400">{strategy.type}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleStrategyStatus(strategy);
                      }}
                      className="p-1 hover:bg-gray-600 rounded transition"
                    >
                      {strategy.status === 'ACTIVE' ? (
                        <Pause className="h-4 w-4 text-yellow-400" />
                      ) : (
                        <Play className="h-4 w-4 text-green-400" />
                      )}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteStrategy(strategy.id);
                      }}
                      className="p-1 hover:bg-gray-600 rounded transition"
                    >
                      <Trash2 className="h-4 w-4 text-red-400" />
                    </button>
                  </div>
                </div>
                <div className="mt-2 text-xs">
                  <span className={`px-2 py-1 rounded ${
                    strategy.status === 'ACTIVE' 
                      ? 'bg-green-900 text-green-300' 
                      : strategy.status === 'PAUSED'
                      ? 'bg-yellow-900 text-yellow-300'
                      : 'bg-gray-700 text-gray-300'
                  }`}>
                    {strategy.status}
                  </span>
                  <span className="ml-2 text-gray-400">
                    {strategy.allocation_percent}% allocation
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Strategy Configuration */}
        {selectedStrategy && (
          <div className="lg:col-span-2 bg-gray-900 rounded-lg p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">Configuration</h2>
              <button
                onClick={saveStrategy}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded transition"
              >
                {saving ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Save Changes
              </button>
            </div>

            <div className="space-y-6">
              {/* Basic Settings */}
              <div>
                <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Basic Settings
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Strategy Name</label>
                    <input
                      type="text"
                      value={selectedStrategy.name}
                      onChange={(e) => setSelectedStrategy({
                        ...selectedStrategy,
                        name: e.target.value
                      })}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Type</label>
                    <select
                      value={selectedStrategy.type}
                      onChange={(e) => setSelectedStrategy({
                        ...selectedStrategy,
                        type: e.target.value
                      })}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="RSI_MEAN_REVERSION">RSI Mean Reversion</option>
                      <option value="SMA_CROSSOVER">SMA Crossover</option>
                      <option value="BOLLINGER_BANDS">Bollinger Bands</option>
                      <option value="TREND_FOLLOWING">Trend Following</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Allocation (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={selectedStrategy.allocation_percent}
                      onChange={(e) => setSelectedStrategy({
                        ...selectedStrategy,
                        allocation_percent: Number(e.target.value)
                      })}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Max Positions</label>
                    <input
                      type="number"
                      min="1"
                      value={selectedStrategy.max_positions}
                      onChange={(e) => setSelectedStrategy({
                        ...selectedStrategy,
                        max_positions: Number(e.target.value)
                      })}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Strategy Parameters */}
              <div>
                <h3 className="text-lg font-medium mb-4">Strategy Parameters</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedStrategy.type === 'RSI_MEAN_REVERSION' && (
                    <>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">RSI Period</label>
                        <input
                          type="number"
                          defaultValue="14"
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">RSI Oversold</label>
                        <input
                          type="number"
                          defaultValue="30"
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">RSI Overbought</label>
                        <input
                          type="number"
                          defaultValue="70"
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </>
                  )}
                  
                  {selectedStrategy.type === 'SMA_CROSSOVER' && (
                    <>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Fast SMA Period</label>
                        <input
                          type="number"
                          defaultValue="20"
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">Slow SMA Period</label>
                        <input
                          type="number"
                          defaultValue="50"
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </>
                  )}
                  
                  {selectedStrategy.type === 'BOLLINGER_BANDS' && (
                    <>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">BB Period</label>
                        <input
                          type="number"
                          defaultValue="20"
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">BB Std Dev</label>
                        <input
                          type="number"
                          step="0.1"
                          defaultValue="2.0"
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Risk Management */}
              <div>
                <h3 className="text-lg font-medium mb-4">Risk Management</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Stop Loss (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      defaultValue="2.0"
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Take Profit (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      defaultValue="5.0"
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Position Size (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      defaultValue="10.0"
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">ATR Multiplier</label>
                    <input
                      type="number"
                      step="0.1"
                      defaultValue="2.0"
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}