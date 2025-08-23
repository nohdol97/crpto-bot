'use client';

import { useEffect, useState } from 'react';

export default function NetworkIndicator() {
  const [isTestnet, setIsTestnet] = useState<boolean | null>(null);

  useEffect(() => {
    // Fetch network configuration from Python API server
    async function checkNetwork() {
      try {
        // Fetch from Python API server directly
        const response = await fetch('http://localhost:5001/api/config');
        if (response.ok) {
          const data = await response.json();
          setIsTestnet(data.is_testnet);
        } else {
          // Fallback: assume testnet if no config available
          setIsTestnet(true);
        }
      } catch (error) {
        console.error('Failed to fetch network config:', error);
        // Default to testnet on error
        setIsTestnet(true);
      }
    }

    checkNetwork();
  }, []);

  if (isTestnet === null) {
    return (
      <div className="flex items-center space-x-2">
        <div className="h-2 w-2 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-sm text-gray-400">Detecting...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      <div className={`h-2 w-2 rounded-full animate-pulse ${
        isTestnet ? 'bg-yellow-400' : 'bg-green-400'
      }`}></div>
      <span className={`text-sm font-medium px-2 py-1 rounded ${
        isTestnet 
          ? 'bg-yellow-900/50 text-yellow-400 border border-yellow-800' 
          : 'bg-green-900/50 text-green-400 border border-green-800'
      }`}>
        {isTestnet ? 'TESTNET' : 'MAINNET'}
      </span>
    </div>
  );
}