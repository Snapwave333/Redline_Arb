"""
Logging and Monitoring System for Kalshi Trading Bot

This module provides comprehensive logging, monitoring, and alerting
capabilities for the trading bot.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
from pathlib import Path
import sqlite3

from .config import config

logger = structlog.get_logger(__name__)


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Alert type enumeration"""
    TRADE_EXECUTED = "trade_executed"
    TRADE_FAILED = "trade_failed"
    RISK_VIOLATION = "risk_violation"
    MODEL_RETRAINED = "model_retrained"
    API_ERROR = "api_error"
    SYSTEM_ERROR = "system_error"
    PORTFOLIO_UPDATE = "portfolio_update"


@dataclass
class Alert:
    """Alert structure"""
    alert_id: str
    alert_type: AlertType
    severity: LogLevel
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class PerformanceMetrics:
    """Performance metrics structure"""
    timestamp: datetime
    portfolio_value: float
    total_pnl: float
    daily_pnl: float
    win_rate: float
    total_trades: int
    active_positions: int
    risk_level: str
    model_accuracy: float
    api_calls_made: int
    errors_count: int


class LoggingManager:
    """Manages structured logging for the bot"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup structured logging configuration"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Setup file logging
        log_file = self.log_dir / f"kalshi_bot_{datetime.now().strftime('%Y%m%d')}.log"
        
        import logging
        logging.basicConfig(
            level=getattr(logging, config.bot.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def log_trade_execution(self, signal, result):
        """Log trade execution"""
        logger.info(
            "Trade executed",
            ticker=signal.ticker,
            side=signal.side,
            quantity=signal.quantity,
            price=signal.price,
            success=result.success,
            order_id=result.order_id,
            execution_time=result.execution_time
        )
    
    def log_model_prediction(self, prediction):
        """Log model prediction"""
        logger.info(
            "Model prediction",
            ticker=prediction.ticker,
            model_probability=prediction.model_probability,
            implied_probability=prediction.implied_probability,
            probability_delta=prediction.probability_delta,
            confidence=prediction.confidence
        )
    
    def log_risk_violation(self, violation):
        """Log risk violation"""
        logger.warning(
            "Risk violation",
            violation_type=violation.violation_type,
            severity=violation.severity.value,
            message=violation.message,
            current_value=violation.current_value,
            limit_value=violation.limit_value
        )
    
    def log_api_error(self, endpoint, error, status_code=None):
        """Log API error"""
        logger.error(
            "API error",
            endpoint=endpoint,
            error=str(error),
            status_code=status_code
        )
    
    def log_system_error(self, component, error):
        """Log system error"""
        logger.error(
            "System error",
            component=component,
            error=str(error)
        )


class MonitoringDatabase:
    """Database for storing monitoring data"""
    
    def __init__(self, db_path: str = "data/monitoring.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                portfolio_value REAL NOT NULL,
                total_pnl REAL NOT NULL,
                daily_pnl REAL NOT NULL,
                win_rate REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                active_positions INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                model_accuracy REAL NOT NULL,
                api_calls_made INTEGER NOT NULL,
                errors_count INTEGER NOT NULL
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                data_json TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                resolved BOOLEAN DEFAULT FALSE
            )
        """)
        
        # System events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                data_json TEXT,
                timestamp DATETIME NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON system_events(timestamp)")
        
        conn.commit()
        conn.close()
    
    def save_performance_metrics(self, metrics: PerformanceMetrics):
        """Save performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics 
            (timestamp, portfolio_value, total_pnl, daily_pnl, win_rate, 
             total_trades, active_positions, risk_level, model_accuracy, 
             api_calls_made, errors_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.timestamp,
            metrics.portfolio_value,
            metrics.total_pnl,
            metrics.daily_pnl,
            metrics.win_rate,
            metrics.total_trades,
            metrics.active_positions,
            metrics.risk_level,
            metrics.model_accuracy,
            metrics.api_calls_made,
            metrics.errors_count
        ))
        
        conn.commit()
        conn.close()
    
    def save_alert(self, alert: Alert):
        """Save alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO alerts 
            (alert_id, alert_type, severity, title, message, data_json, 
             timestamp, acknowledged, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.alert_id,
            alert.alert_type.value,
            alert.severity.value,
            alert.title,
            alert.message,
            json.dumps(alert.data),
            alert.timestamp,
            alert.acknowledged,
            alert.resolved
        ))
        
        conn.commit()
        conn.close()
    
    def save_system_event(self, event_type: str, component: str, 
                         message: str, data: Dict[str, Any] = None):
        """Save system event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO system_events 
            (event_type, component, message, data_json, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event_type,
            component,
            message,
            json.dumps(data) if data else None,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def get_performance_metrics(self, hours: int = 24) -> List[PerformanceMetrics]:
        """Get performance metrics for the last N hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM performance_metrics 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        """.format(hours))
        
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            metric = PerformanceMetrics(
                timestamp=datetime.fromisoformat(row[1]),
                portfolio_value=row[2],
                total_pnl=row[3],
                daily_pnl=row[4],
                win_rate=row[5],
                total_trades=row[6],
                active_positions=row[7],
                risk_level=row[8],
                model_accuracy=row[9],
                api_calls_made=row[10],
                errors_count=row[11]
            )
            metrics.append(metric)
        
        return metrics
    
    def get_unresolved_alerts(self) -> List[Alert]:
        """Get unresolved alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM alerts 
            WHERE resolved = FALSE
            ORDER BY timestamp DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alert = Alert(
                alert_id=row[1],
                alert_type=AlertType(row[2]),
                severity=LogLevel(row[3]),
                title=row[4],
                message=row[5],
                data=json.loads(row[6]),
                timestamp=datetime.fromisoformat(row[7]),
                acknowledged=bool(row[8]),
                resolved=bool(row[9])
            )
            alerts.append(alert)
        
        return alerts


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, monitoring_db: MonitoringDatabase):
        self.monitoring_db = monitoring_db
        self.active_alerts: Dict[str, Alert] = {}
    
    def create_alert(self, alert_type: AlertType, severity: LogLevel, 
                    title: str, message: str, data: Dict[str, Any] = None) -> Alert:
        """Create a new alert"""
        alert_id = f"{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            data=data or {},
            timestamp=datetime.now()
        )
        
        # Save to database
        self.monitoring_db.save_alert(alert)
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        # Log alert
        logger.warning("Alert created", 
                     alert_id=alert_id,
                     alert_type=alert_type.value,
                     severity=severity.value,
                     title=title)
        
        return alert
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.monitoring_db.save_alert(self.active_alerts[alert_id])
            
            logger.info("Alert acknowledged", alert_id=alert_id)
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.monitoring_db.save_alert(self.active_alerts[alert_id])
            
            logger.info("Alert resolved", alert_id=alert_id)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def cleanup_old_alerts(self, days: int = 7):
        """Cleanup old resolved alerts"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        alerts_to_remove = []
        for alert_id, alert in self.active_alerts.items():
            if alert.resolved and alert.timestamp < cutoff_date:
                alerts_to_remove.append(alert_id)
        
        for alert_id in alerts_to_remove:
            del self.active_alerts[alert_id]
        
        logger.info("Cleaned up old alerts", count=len(alerts_to_remove))


class PerformanceMonitor:
    """Monitors bot performance and generates metrics"""
    
    def __init__(self, monitoring_db: MonitoringDatabase):
        self.monitoring_db = monitoring_db
        self.api_call_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
    
    def increment_api_calls(self):
        """Increment API call counter"""
        self.api_call_count += 1
    
    def increment_errors(self):
        """Increment error counter"""
        self.error_count += 1
    
    def record_performance_metrics(self, portfolio_value: float, 
                                  total_pnl: float, daily_pnl: float,
                                  win_rate: float, total_trades: int,
                                  active_positions: int, risk_level: str,
                                  model_accuracy: float):
        """Record performance metrics"""
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            portfolio_value=portfolio_value,
            total_pnl=total_pnl,
            daily_pnl=daily_pnl,
            win_rate=win_rate,
            total_trades=total_trades,
            active_positions=active_positions,
            risk_level=risk_level,
            model_accuracy=model_accuracy,
            api_calls_made=self.api_call_count,
            errors_count=self.error_count
        )
        
        self.monitoring_db.save_performance_metrics(metrics)
        
        # Reset counters
        self.api_call_count = 0
        self.error_count = 0
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        metrics = self.monitoring_db.get_performance_metrics(hours)
        
        if not metrics:
            return {}
        
        latest = metrics[0]
        
        # Calculate changes
        if len(metrics) > 1:
            oldest = metrics[-1]
            pnl_change = latest.total_pnl - oldest.total_pnl
            portfolio_change = latest.portfolio_value - oldest.portfolio_value
        else:
            pnl_change = 0
            portfolio_change = 0
        
        return {
            "current_portfolio_value": latest.portfolio_value,
            "current_total_pnl": latest.total_pnl,
            "current_daily_pnl": latest.daily_pnl,
            "current_win_rate": latest.win_rate,
            "current_total_trades": latest.total_trades,
            "current_active_positions": latest.active_positions,
            "current_risk_level": latest.risk_level,
            "current_model_accuracy": latest.model_accuracy,
            "pnl_change_24h": pnl_change,
            "portfolio_change_24h": portfolio_change,
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }


class MonitoringSystem:
    """Main monitoring system that coordinates all monitoring components"""
    
    def __init__(self):
        self.monitoring_db = MonitoringDatabase()
        self.logging_manager = LoggingManager()
        self.alert_manager = AlertManager(self.monitoring_db)
        self.performance_monitor = PerformanceMonitor(self.monitoring_db)
        self.is_monitoring = False
    
    async def start_monitoring(self):
        """Start monitoring system"""
        self.is_monitoring = True
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_performance())
        asyncio.create_task(self._monitor_alerts())
        
        logger.info("Monitoring system started")
    
    async def stop_monitoring(self):
        """Stop monitoring system"""
        self.is_monitoring = False
        logger.info("Monitoring system stopped")
    
    async def _monitor_performance(self):
        """Monitor performance metrics"""
        while self.is_monitoring:
            try:
                # This would be called by the main bot to update metrics
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error("Error in performance monitoring", error=str(e))
                await asyncio.sleep(60)
    
    async def _monitor_alerts(self):
        """Monitor alerts and notifications"""
        while self.is_monitoring:
            try:
                # Check for unresolved alerts
                unresolved_alerts = self.monitoring_db.get_unresolved_alerts()
                
                for alert in unresolved_alerts:
                    if alert.severity == LogLevel.CRITICAL and not alert.acknowledged:
                        # Handle critical alerts
                        logger.critical("Critical alert not acknowledged", 
                                      alert_id=alert.alert_id,
                                      title=alert.title)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Error in alert monitoring", error=str(e))
                await asyncio.sleep(60)
    
    def log_trade_execution(self, signal, result):
        """Log trade execution"""
        self.logging_manager.log_trade_execution(signal, result)
        
        # Create alert for trade execution
        if result.success:
            self.alert_manager.create_alert(
                AlertType.TRADE_EXECUTED,
                LogLevel.INFO,
                f"Trade Executed: {signal.ticker}",
                f"Successfully executed {signal.side} order for {signal.quantity} shares at {signal.price}",
                {"ticker": signal.ticker, "side": signal.side, "quantity": signal.quantity, "price": signal.price}
            )
        else:
            self.alert_manager.create_alert(
                AlertType.TRADE_FAILED,
                LogLevel.ERROR,
                f"Trade Failed: {signal.ticker}",
                f"Failed to execute {signal.side} order: {result.error_message}",
                {"ticker": signal.ticker, "side": signal.side, "error": result.error_message}
            )
    
    def log_model_prediction(self, prediction):
        """Log model prediction"""
        self.logging_manager.log_model_prediction(prediction)
    
    def log_risk_violation(self, violation):
        """Log risk violation"""
        self.logging_manager.log_risk_violation(violation)
        
        # Create alert for risk violation
        self.alert_manager.create_alert(
            AlertType.RISK_VIOLATION,
            LogLevel.WARNING,
            f"Risk Violation: {violation.violation_type}",
            violation.message,
            {
                "violation_type": violation.violation_type,
                "current_value": violation.current_value,
                "limit_value": violation.limit_value
            }
        )
    
    def log_api_error(self, endpoint, error, status_code=None):
        """Log API error"""
        self.logging_manager.log_api_error(endpoint, error, status_code)
        
        # Create alert for API error
        self.alert_manager.create_alert(
            AlertType.API_ERROR,
            LogLevel.ERROR,
            f"API Error: {endpoint}",
            str(error),
            {"endpoint": endpoint, "error": str(error), "status_code": status_code}
        )
        
        self.performance_monitor.increment_errors()
    
    def log_system_error(self, component, error):
        """Log system error"""
        self.logging_manager.log_system_error(component, error)
        
        # Create alert for system error
        self.alert_manager.create_alert(
            AlertType.SYSTEM_ERROR,
            LogLevel.ERROR,
            f"System Error: {component}",
            str(error),
            {"component": component, "error": str(error)}
        )
        
        self.performance_monitor.increment_errors()
    
    def record_performance_metrics(self, **kwargs):
        """Record performance metrics"""
        self.performance_monitor.record_performance_metrics(**kwargs)
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        performance_summary = self.performance_monitor.get_performance_summary()
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            "performance": performance_summary,
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.severity == LogLevel.CRITICAL]),
            "monitoring_status": "active" if self.is_monitoring else "inactive"
        }
