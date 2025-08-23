'use client';

import { useEffect, useState } from 'react';

interface NetworkToggleProps {
  onNetworkChange?: (isTestnet: boolean) => void;
}

export default function NetworkToggle({ onNetworkChange }: NetworkToggleProps) {
  const [isTestnet, setIsTestnet] = useState<boolean | null>(null);
  const [isChanging, setIsChanging] = useState(false);

  useEffect(() => {
    fetchNetworkStatus();
  }, []);

  const fetchNetworkStatus = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/config');
      if (response.ok) {
        const data = await response.json();
        setIsTestnet(data.is_testnet);
      } else {
        setIsTestnet(true);
      }
    } catch (error) {
      console.error('Failed to fetch network config:', error);
      setIsTestnet(true);
    }
  };

  const toggleNetwork = async () => {
    if (isTestnet === null || isChanging) return;

    const newIsTestnet = !isTestnet;
    
    // Confirmation dialog for switching to mainnet
    if (!newIsTestnet) {
      const confirmed = window.confirm(
        '⚠️ WARNING: Switching to MAINNET\n\n' +
        'This will use REAL funds for trading.\n' +
        'Make sure you have:\n' +
        '1. Real Binance API keys configured\n' +
        '2. Sufficient funds in your account\n' +
        '3. Tested your strategies thoroughly\n\n' +
        'Are you sure you want to switch to MAINNET?'
      );
      
      if (!confirmed) return;
    }

    setIsChanging(true);

    try {
      // Note: This would require implementing a backend endpoint to update the config
      // For now, we'll show an instruction message
      alert(
        `To switch to ${newIsTestnet ? 'TESTNET' : 'MAINNET'}:\n\n` +
        `1. Edit the .env file\n` +
        `2. Set BINANCE_TESTNET=${newIsTestnet}\n` +
        `3. Restart the API server\n\n` +
        `Current network will remain: ${isTestnet ? 'TESTNET' : 'MAINNET'}`
      );
      
      // In a real implementation, you would call an API endpoint like:
      // const response = await fetch('http://localhost:5001/api/config/update', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ is_testnet: newIsTestnet })
      // });
      
    } catch (error) {
      console.error('Failed to toggle network:', error);
      alert('Failed to change network. Please check the API server.');
    } finally {
      setIsChanging(false);
      // Refresh the status
      await fetchNetworkStatus();
    }
  };

  if (isTestnet === null) {
    return (
      <div className="flex items-center space-x-2">
        <div className="h-2 w-2 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-sm text-gray-400">Detecting...</span>
      </div>
    );
  }

  return (
    <button
      onClick={toggleNetwork}
      disabled={isChanging}
      className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-all ${
        isChanging 
          ? 'opacity-50 cursor-not-allowed' 
          : 'hover:opacity-80 cursor-pointer'
      } ${
        isTestnet
          ? 'bg-yellow-900/50 border border-yellow-800 hover:bg-yellow-900/70'
          : 'bg-green-900/50 border border-green-800 hover:bg-green-900/70'
      }`}
      title={`Click to switch to ${isTestnet ? 'MAINNET' : 'TESTNET'}`}
    >
      <div className={`h-2 w-2 rounded-full ${
        isChanging ? 'animate-spin' : 'animate-pulse'
      } ${
        isTestnet ? 'bg-yellow-400' : 'bg-green-400'
      }`}></div>
      <span className={`text-sm font-medium ${
        isTestnet ? 'text-yellow-400' : 'text-green-400'
      }`}>
        {isTestnet ? 'TESTNET' : 'MAINNET'}
      </span>
      <svg 
        className={`w-3 h-3 ${isTestnet ? 'text-yellow-400' : 'text-green-400'}`}
        fill="none" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
        strokeWidth="2" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
      </svg>
    </button>
  );
}