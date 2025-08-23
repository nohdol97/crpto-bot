'use client';

import { useEffect, useState } from 'react';

export default function NetworkIndicator() {
  const [isTestnet, setIsTestnet] = useState<boolean | null>(null);

  useEffect(() => {
    // Check environment variable or fetch from API
    // For now, we'll check if any recent trades are testnet
    async function checkNetwork() {
      try {
        // In production, you might want to fetch this from an API endpoint
        // that reads the actual config from the backend
        const response = await fetch('/api/config');
        if (response.ok) {
          const data = await response.json();
          setIsTestnet(data.isTestnet);
        } else {
          // Fallback: assume testnet if no config available
          setIsTestnet(true);
        }
      } catch (error) {
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