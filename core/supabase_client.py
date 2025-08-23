"""
Supabase client integration for database operations
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import json
from supabase import create_client, Client
from supabase.client import ClientOptions
import pandas as pd
from utils.logger import logger

class SupabaseManager:
    """Manage all Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for server-side operations
        
        if not url or not key:
            raise ValueError("Supabase URL and service key must be set in environment variables")
        
        # Create client with service role for full access
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized", module="supabase")
        
        # Set logger's Supabase client
        logger.set_supabase_client(self)
        
        # Track if we're in testnet mode
        from config import cfg
        self.is_testnet = cfg.binance_testnet
    
    # ============== Strategy Management ==============
    
    async def get_active_strategies(self) -> List[Dict]:
        """Get all active trading strategies"""
        try:
            response = self.client.table("strategies")\
                .select("*")\
                .eq("status", "ACTIVE")\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get active strategies: {e}", module="supabase")
            return []
    
    async def update_strategy(self, strategy_id: str, updates: Dict) -> bool:
        """Update strategy configuration"""
        try:
            response = self.client.table("strategies")\
                .update(updates)\
                .eq("id", strategy_id)\
                .execute()
            logger.info(f"Strategy {strategy_id} updated", module="supabase", updates=updates)
            return True
        except Exception as e:
            logger.error(f"Failed to update strategy: {e}", module="supabase")
            return False
    
    # ============== Position Management ==============
    
    async def create_position(self, position_data: Dict) -> Optional[str]:
        """Create a new position record"""
        try:
            # Convert Decimal to float for JSON serialization
            position_data = self._convert_decimals(position_data)
            
            # Add testnet flag
            position_data["is_testnet"] = self.is_testnet
            
            response = self.client.table("positions")\
                .insert(position_data)\
                .execute()
            
            position_id = response.data[0]["id"]
            logger.log_position("OPENED", position_data)
            logger.info(f"Position created: {position_id}", module="supabase", position=position_data)
            return position_id
        except Exception as e:
            logger.error(f"Failed to create position: {e}", module="supabase")
            return None
    
    async def get_open_positions(self, symbol: str = None) -> List[Dict]:
        """Get all open positions, optionally filtered by symbol"""
        try:
            query = self.client.table("positions")\
                .select("*, strategies(name, type)")\
                .eq("status", "OPEN")
            
            if symbol:
                query = query.eq("symbol", symbol)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get open positions: {e}", module="supabase")
            return []
    
    async def update_position(self, position_id: str, updates: Dict) -> bool:
        """Update position data"""
        try:
            updates = self._convert_decimals(updates)
            
            response = self.client.table("positions")\
                .update(updates)\
                .eq("id", position_id)\
                .execute()
            
            logger.log_position("UPDATED", updates)
            return True
        except Exception as e:
            logger.error(f"Failed to update position: {e}", module="supabase")
            return False
    
    async def close_position(self, position_id: str, exit_price: float, 
                           exit_quantity: float, pnl: float) -> bool:
        """Close a position with exit details"""
        try:
            updates = {
                "status": "CLOSED",
                "exit_price": exit_price,
                "exit_quantity": exit_quantity,
                "exit_time": datetime.utcnow().isoformat(),
                "pnl": pnl,
                "pnl_percent": 0  # Calculate based on entry/exit prices
            }
            
            # Get position to calculate PnL percentage
            position = await self.get_position(position_id)
            if position:
                entry_value = float(position["entry_price"]) * float(position["entry_quantity"])
                if entry_value > 0:
                    updates["pnl_percent"] = (pnl / entry_value) * 100
            
            success = await self.update_position(position_id, updates)
            
            if success:
                logger.log_position("CLOSED", updates)
                logger.info(f"Position {position_id} closed with PnL: {pnl}", module="supabase")
            
            return success
        except Exception as e:
            logger.error(f"Failed to close position: {e}", module="supabase")
            return False
    
    async def get_position(self, position_id: str) -> Optional[Dict]:
        """Get a specific position by ID"""
        try:
            response = self.client.table("positions")\
                .select("*, strategies(name, type)")\
                .eq("id", position_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get position: {e}", module="supabase")
            return None
    
    # ============== Trade Management ==============
    
    async def record_trade(self, trade_data: Dict) -> Optional[str]:
        """Record a trade execution"""
        try:
            trade_data = self._convert_decimals(trade_data)
            
            # Add testnet flag
            trade_data["is_testnet"] = self.is_testnet
            
            response = self.client.table("trades")\
                .insert(trade_data)\
                .execute()
            
            trade_id = response.data[0]["id"]
            
            logger.log_trade(
                action="EXECUTED",
                symbol=trade_data.get("symbol"),
                side=trade_data.get("side"),
                price=trade_data.get("price"),
                quantity=trade_data.get("quantity"),
                order_id=trade_data.get("order_id")
            )
            
            return trade_id
        except Exception as e:
            logger.error(f"Failed to record trade: {e}", module="supabase")
            return None
    
    async def get_recent_trades(self, limit: int = 50, symbol: str = None) -> List[Dict]:
        """Get recent trades"""
        try:
            query = self.client.table("trades")\
                .select("*, positions(symbol, pnl), strategies(name)")\
                .order("order_time", desc=True)\
                .limit(limit)
            
            if symbol:
                query = query.eq("symbol", symbol)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}", module="supabase")
            return []
    
    # ============== Performance Tracking ==============
    
    async def update_daily_performance(self, strategy_id: str, metrics: Dict):
        """Update or insert daily performance metrics"""
        try:
            today = datetime.utcnow().date().isoformat()
            metrics = self._convert_decimals(metrics)
            metrics["strategy_id"] = strategy_id
            metrics["date"] = today
            metrics["is_testnet"] = self.is_testnet
            
            # Try to update existing record, or insert new one
            response = self.client.table("performance")\
                .upsert(metrics, on_conflict="strategy_id,date")\
                .execute()
            
            logger.log_performance(metrics)
            return True
        except Exception as e:
            logger.error(f"Failed to update performance: {e}", module="supabase")
            return False
    
    async def get_performance_history(self, strategy_id: str = None, 
                                     days: int = 30) -> pd.DataFrame:
        """Get performance history as DataFrame"""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
            
            query = self.client.table("performance")\
                .select("*, strategies(name)")\
                .gte("date", start_date)\
                .order("date", desc=True)
            
            if strategy_id:
                query = query.eq("strategy_id", strategy_id)
            
            response = query.execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to get performance history: {e}", module="supabase")
            return pd.DataFrame()
    
    # ============== Market Data ==============
    
    async def save_market_data(self, symbol: str, timeframe: str, data: pd.DataFrame):
        """Save market data to database"""
        try:
            records = []
            for idx, row in data.iterrows():
                record = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "open_time": idx.isoformat() if isinstance(idx, pd.Timestamp) else idx,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"])
                }
                records.append(record)
            
            # Batch insert with upsert to handle duplicates
            response = self.client.table("market_data")\
                .upsert(records, on_conflict="symbol,timeframe,open_time")\
                .execute()
            
            logger.debug(f"Saved {len(records)} market data records for {symbol}", module="supabase")
            return True
        except Exception as e:
            logger.error(f"Failed to save market data: {e}", module="supabase")
            return False
    
    async def get_market_data(self, symbol: str, timeframe: str, 
                             limit: int = 100) -> pd.DataFrame:
        """Get market data from database"""
        try:
            response = self.client.table("market_data")\
                .select("*")\
                .eq("symbol", symbol)\
                .eq("timeframe", timeframe)\
                .order("open_time", desc=True)\
                .limit(limit)\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['open_time'] = pd.to_datetime(df['open_time'])
                df.set_index('open_time', inplace=True)
                df.sort_index(inplace=True)
                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to get market data: {e}", module="supabase")
            return pd.DataFrame()
    
    # ============== Balance Tracking ==============
    
    async def save_balance_snapshot(self, balance_data: Dict):
        """Save account balance snapshot"""
        try:
            balance_data = self._convert_decimals(balance_data)
            
            # Add testnet flag
            balance_data["is_testnet"] = self.is_testnet
            
            response = self.client.table("balance_snapshots")\
                .insert(balance_data)\
                .execute()
            
            logger.info("Balance snapshot saved", module="supabase", balance=balance_data)
            return True
        except Exception as e:
            logger.error(f"Failed to save balance snapshot: {e}", module="supabase")
            return False
    
    async def get_balance_history(self, days: int = 7) -> pd.DataFrame:
        """Get balance history"""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            response = self.client.table("balance_snapshots")\
                .select("*")\
                .gte("timestamp", start_date)\
                .order("timestamp", desc=True)\
                .execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df
            
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to get balance history: {e}", module="supabase")
            return pd.DataFrame()
    
    # ============== Alerts ==============
    
    async def create_alert(self, alert_type: str, title: str, 
                          message: str, severity: str = "INFO", metadata: Dict = None):
        """Create an alert record"""
        try:
            alert_data = {
                "type": alert_type,
                "title": title,
                "message": message,
                "severity": severity,
                "metadata": metadata or {}
            }
            
            response = self.client.table("alerts")\
                .insert(alert_data)\
                .execute()
            
            logger.log_alert(alert_type, title, message, severity, metadata)
            return True
        except Exception as e:
            logger.error(f"Failed to create alert: {e}", module="supabase")
            return False
    
    async def get_unread_alerts(self) -> List[Dict]:
        """Get unread alerts"""
        try:
            response = self.client.table("alerts")\
                .select("*")\
                .eq("is_read", False)\
                .order("created_at", desc=True)\
                .execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Failed to get unread alerts: {e}", module="supabase")
            return []
    
    async def mark_alerts_read(self, alert_ids: List[str]):
        """Mark alerts as read"""
        try:
            response = self.client.table("alerts")\
                .update({"is_read": True})\
                .in_("id", alert_ids)\
                .execute()
            
            return True
        except Exception as e:
            logger.error(f"Failed to mark alerts as read: {e}", module="supabase")
            return False
    
    # ============== Realtime Subscriptions ==============
    
    def subscribe_to_positions(self, callback):
        """Subscribe to position changes in realtime"""
        try:
            # Supabase realtime subscription
            subscription = self.client.table("positions")\
                .on("*", callback)\
                .subscribe()
            
            logger.info("Subscribed to position changes", module="supabase")
            return subscription
        except Exception as e:
            logger.error(f"Failed to subscribe to positions: {e}", module="supabase")
            return None
    
    def subscribe_to_alerts(self, callback):
        """Subscribe to new alerts in realtime"""
        try:
            subscription = self.client.table("alerts")\
                .on("INSERT", callback)\
                .subscribe()
            
            logger.info("Subscribed to alerts", module="supabase")
            return subscription
        except Exception as e:
            logger.error(f"Failed to subscribe to alerts: {e}", module="supabase")
            return None
    
    # ============== Utility Methods ==============
    
    def _convert_decimals(self, data: Any) -> Any:
        """Recursively convert Decimal objects to float for JSON serialization"""
        if isinstance(data, dict):
            return {k: self._convert_decimals(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        return data
    
    async def health_check(self) -> bool:
        """Check if Supabase connection is healthy"""
        try:
            response = self.client.table("strategies").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}", module="supabase")
            return False

# Singleton instance
supabase_manager = SupabaseManager()