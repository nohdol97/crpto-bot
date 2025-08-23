import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.PYTHON_API_URL || 'http://localhost:5001';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward the request to Python backend
    const response = await fetch(`${API_BASE_URL}/api/backtest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || 'Backtest failed' },
        { status: response.status }
      );
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Backtest API error:', error);
    return NextResponse.json(
      { error: 'Failed to run backtest' },
      { status: 500 }
    );
  }
}