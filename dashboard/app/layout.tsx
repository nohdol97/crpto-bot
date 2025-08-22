import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Crypto Trading Bot Dashboard",
  description: "Monitor and manage your crypto trading strategies",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} dark bg-gray-950 text-gray-100`}>
        <div className="min-h-screen">
          <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur">
            <div className="container mx-auto px-4">
              <div className="flex h-16 items-center justify-between">
                <div className="flex items-center space-x-8">
                  <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    Crypto Bot
                  </h1>
                  <div className="flex space-x-6">
                    <a href="/" className="text-sm hover:text-blue-400 transition">Dashboard</a>
                    <a href="/trades" className="text-sm hover:text-blue-400 transition">Trades</a>
                    <a href="/backtest" className="text-sm hover:text-blue-400 transition">Backtest</a>
                    <a href="/settings" className="text-sm hover:text-blue-400 transition">Settings</a>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-400">Connected</span>
                </div>
              </div>
            </div>
          </nav>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
