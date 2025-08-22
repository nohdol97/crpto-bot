"""
Enhanced logging system with Supabase integration and structured logging
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
import os
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class CryptoLogger:
    """Enhanced logger with Supabase integration and structured logging"""
    
    def __init__(self, name: str = "crypto_bot", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create separate loggers for different purposes
        self.system_logger = self._setup_logger(f"{name}_system", "system.log")
        self.trade_logger = self._setup_logger(f"{name}_trade", "trades.log")
        self.error_logger = self._setup_logger(f"{name}_error", "errors.log")
        
        # Supabase client will be initialized separately
        self.supabase = None
        
        # Sensitive fields to mask
        self.sensitive_fields = {
            'api_key', 'api_secret', 'password', 'token', 
            'secret', 'private_key', 'seed', 'mnemonic'
        }
    
    def set_supabase_client(self, supabase_client):
        """Set Supabase client for database logging"""
        self.supabase = supabase_client
    
    def _setup_logger(self, logger_name: str, filename: str) -> logging.Logger:
        """Setup individual logger with JSON formatting and rotation"""
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        logger.handlers = []
        
        # File handler with rotation
        file_path = self.log_dir / filename
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # JSON formatter
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Recursively mask sensitive information in logs"""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    masked[key] = "***MASKED***"
                else:
                    masked[key] = self._mask_sensitive_data(value)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            # Check if string looks like a key/token
            if len(data) > 20 and not ' ' in data:
                return f"{data[:4]}...{data[-4:]}"
            return data
        return data
    
    async def _log_to_supabase(self, level: str, module: str, message: str, 
                               context: Dict = None, error_trace: str = None):
        """Log to Supabase database"""
        if not self.supabase:
            return
        
        try:
            log_entry = {
                "level": level,
                "module": module,
                "message": message,
                "context": self._mask_sensitive_data(context) if context else {},
                "error_trace": error_trace,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.supabase.table("logs").insert(log_entry).execute()
        except Exception as e:
            # Fallback to file logging if Supabase fails
            self.system_logger.error(f"Failed to log to Supabase: {e}")
    
    def debug(self, message: str, module: str = None, **kwargs):
        """Log debug message"""
        context = self._mask_sensitive_data(kwargs) if kwargs else {}
        self.system_logger.debug(message, extra={"module": module, "context": context})
        
        if self.supabase:
            import asyncio
            asyncio.create_task(self._log_to_supabase("DEBUG", module, message, context))
    
    def info(self, message: str, module: str = None, **kwargs):
        """Log info message"""
        context = self._mask_sensitive_data(kwargs) if kwargs else {}
        self.system_logger.info(message, extra={"module": module, "context": context})
        
        if self.supabase:
            import asyncio
            asyncio.create_task(self._log_to_supabase("INFO", module, message, context))
    
    def warning(self, message: str, module: str = None, **kwargs):
        """Log warning message"""
        context = self._mask_sensitive_data(kwargs) if kwargs else {}
        self.system_logger.warning(message, extra={"module": module, "context": context})
        
        if self.supabase:
            import asyncio
            asyncio.create_task(self._log_to_supabase("WARNING", module, message, context))
    
    def error(self, message: str, module: str = None, exc_info: bool = True, **kwargs):
        """Log error message with traceback"""
        context = self._mask_sensitive_data(kwargs) if kwargs else {}
        error_trace = None
        
        if exc_info:
            error_trace = traceback.format_exc()
            
        self.error_logger.error(
            message, 
            exc_info=exc_info,
            extra={"module": module, "context": context}
        )
        
        if self.supabase:
            import asyncio
            asyncio.create_task(
                self._log_to_supabase("ERROR", module, message, context, error_trace)
            )
    
    def critical(self, message: str, module: str = None, exc_info: bool = True, **kwargs):
        """Log critical message"""
        context = self._mask_sensitive_data(kwargs) if kwargs else {}
        error_trace = None
        
        if exc_info:
            error_trace = traceback.format_exc()
            
        self.error_logger.critical(
            message,
            exc_info=exc_info,
            extra={"module": module, "context": context}
        )
        
        if self.supabase:
            import asyncio
            asyncio.create_task(
                self._log_to_supabase("CRITICAL", module, message, context, error_trace)
            )
    
    def log_trade(self, action: str, symbol: str, side: str, 
                  price: float, quantity: float, **kwargs):
        """Log trading activity"""
        trade_data = {
            "action": action,
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "timestamp": datetime.utcnow().isoformat(),
            **self._mask_sensitive_data(kwargs)
        }
        
        self.trade_logger.info(
            f"Trade: {action} {side} {quantity} {symbol} @ {price}",
            extra=trade_data
        )
        
        # Also log to main logger for visibility
        self.info(
            f"Trade executed: {action} {side} {quantity} {symbol} @ {price}",
            module="trader",
            **trade_data
        )
    
    def log_position(self, action: str, position: Dict):
        """Log position changes"""
        masked_position = self._mask_sensitive_data(position)
        
        self.trade_logger.info(
            f"Position {action}: {position.get('symbol', 'N/A')}",
            extra={"action": action, "position": masked_position}
        )
    
    def log_performance(self, metrics: Dict):
        """Log performance metrics"""
        self.info(
            "Performance update",
            module="performance",
            **metrics
        )
    
    def log_alert(self, alert_type: str, title: str, message: str, 
                  severity: str = "INFO", metadata: Dict = None):
        """Log alerts and notifications"""
        alert_data = {
            "type": alert_type,
            "title": title,
            "message": message,
            "severity": severity,
            "metadata": self._mask_sensitive_data(metadata) if metadata else {}
        }
        
        # Choose logger based on severity
        if severity in ["ERROR", "CRITICAL"]:
            self.error(f"Alert: {title} - {message}", module="alert", **alert_data)
        elif severity == "WARNING":
            self.warning(f"Alert: {title} - {message}", module="alert", **alert_data)
        else:
            self.info(f"Alert: {title} - {message}", module="alert", **alert_data)
        
        # Save to Supabase alerts table
        if self.supabase:
            import asyncio
            asyncio.create_task(self._save_alert_to_supabase(alert_data))
    
    async def _save_alert_to_supabase(self, alert_data: Dict):
        """Save alert to Supabase alerts table"""
        try:
            await self.supabase.table("alerts").insert(alert_data).execute()
        except Exception as e:
            self.error(f"Failed to save alert to Supabase: {e}", module="logger")
    
    def get_recent_logs(self, limit: int = 100, level: str = None) -> list:
        """Get recent logs from files"""
        logs = []
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_size > 0:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-limit:]
                    for line in lines:
                        try:
                            log_entry = json.loads(line)
                            if not level or log_entry.get('levelname') == level:
                                logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
        
        # Sort by timestamp
        logs.sort(key=lambda x: x.get('asctime', ''), reverse=True)
        return logs[:limit]

# Singleton instance
logger = CryptoLogger()

# Convenience functions
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
log_trade = logger.log_trade
log_position = logger.log_position
log_performance = logger.log_performance
log_alert = logger.log_alert