import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}

// Types for our database tables
export interface Strategy {
  id: string
  name: string
  type: string
  status: 'ACTIVE' | 'PAUSED' | 'DISABLED'
  config: Record<string, any>
  allocation_percent: number
  max_positions: number
  created_at: string
  updated_at: string
}

export interface Position {
  id: string
  symbol: string
  strategy_id: string
  side: 'BUY' | 'SELL'
  status: 'OPEN' | 'CLOSED' | 'PARTIALLY_CLOSED'
  entry_price: number
  entry_quantity: number
  entry_time: string
  exit_price?: number
  exit_quantity?: number
  exit_time?: string
  stop_loss?: number
  take_profit?: number
  pnl?: number
  pnl_percent?: number
  strategies?: {
    name: string
    type: string
  }
}

export interface Trade {
  id: string
  position_id?: string
  strategy_id?: string
  symbol: string
  side: 'BUY' | 'SELL'
  order_id?: string
  status: 'NEW' | 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELED' | 'REJECTED'
  price: number
  quantity: number
  executed_quantity: number
  executed_price?: number
  commission?: number
  order_time: string
  executed_time?: string
}

export interface Performance {
  id: string
  strategy_id: string
  date: string
  total_trades: number
  winning_trades: number
  losing_trades: number
  gross_pnl: number
  fees: number
  net_pnl: number
  win_rate: number
  avg_win: number
  avg_loss: number
  profit_factor: number
  sharpe_ratio?: number
  max_drawdown?: number
}

export interface Alert {
  id: string
  type: string
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  title: string
  message: string
  metadata?: Record<string, any>
  is_read: boolean
  created_at: string
}

export interface BacktestResult {
  id: string
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return: number
  annual_return?: number
  total_trades: number
  win_rate: number
  profit_factor: number
  sharpe_ratio?: number
  sortino_ratio?: number
  max_drawdown?: number
  config: Record<string, any>
  trades?: any[]
  created_at: string
}