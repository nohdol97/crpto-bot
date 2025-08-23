import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Proxy to Python API server to get actual configuration
    const response = await fetch('http://localhost:5001/api/config');
    
    if (!response.ok) {
      throw new Error('Failed to fetch config from backend');
    }
    
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching config:', error);
    
    // Fallback to environment variable if backend is unavailable
    const isTestnet = process.env.BINANCE_TESTNET !== 'false';
    
    return NextResponse.json({
      is_testnet: isTestnet,
      network: isTestnet ? 'testnet' : 'mainnet',
      base_asset: 'BTC',
      quote_asset: 'USDT',
      symbol: 'BTCUSDT',
      timeframe: '15m'
    });
  }
}