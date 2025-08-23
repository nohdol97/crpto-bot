import { NextResponse } from 'next/server';

export async function GET() {
  // Read the environment variable to determine if we're in testnet mode
  // This should match the Python backend configuration
  const isTestnet = process.env.BINANCE_TESTNET !== 'false';
  
  return NextResponse.json({
    isTestnet,
    network: isTestnet ? 'testnet' : 'mainnet',
  });
}