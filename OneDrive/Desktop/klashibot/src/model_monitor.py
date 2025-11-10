"""
Model Performance Monitoring and Drift Detection for Kalshi Trading Bot

This module provides comprehensive monitoring of model performance, drift detection,
and automated retraining triggers to ensure models remain accurate over time.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum
import json
import sqlite3
from scipy import stats
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss

logger = structlog.get_logger(__name__)


class DriftType(Enum):
    """Types of model drift"""
    PERFORMANCE = "performance"
    FEATURE = "feature"
    CONCEPT = "concept"
    DATA = "data"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    timestamp: datetime
    model_name: str
    ticker: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    brier_score: float
    log_loss: float
    prediction_count: int
    window_size: int


@dataclass
class DriftAlert:
    """Drift detection alert"""
    timestamp: datetime
    model_name: str
    ticker: str
    drift_type: DriftType
    alert_level: AlertLevel
    metric_name: str
    current_value: float
    baseline_value: float
    drift_magnitude: float
    description: str
    recommended_action: str
    acknowledged: bool = False


@dataclass
class ModelHealth:
    """Overall model health status"""
    model_name: str
    ticker: str
    is_healthy: bool
    health_score: float
    last_updated: datetime
    active_alerts: List[DriftAlert]
    performance_trend: str  # "improving", "stable", "declining"
    recommended_action: str


class ModelPerformanceMonitor:
    """
    Comprehensive model performance monitoring and drift detection system
    """
    
    def __init__(self, db_path: str = "data/model_monitoring.db"):
        self.db_path = db_path
        self.performance_history: Dict[str, deque] = {}
        self.drift_alerts: List[DriftAlert] = []
        self.model_health: Dict[str, ModelHealth] = {}
        
        # Monitoring configuration
        self.performance_window = 100  # Number of predictions to track
        self.drift_threshold = 0.05  # Performance drop threshold
        self.min_samples_for_drift = 20  # Minimum samples needed for drift detection
        
        # Alert thresholds
        self.alert_thresholds = {
            'accuracy_drop': 0.05,
            'precision_drop': 0.05,
            'recall_drop': 0.05,
            'f1_drop': 0.05,
            'roc_auc_drop': 0.05,
            'brier_score_increase': 0.05
        }
        
        # Initialize database
        self._init_database()
        
        logger.info("Model performance monitor initialized", db_path=db_path)
    
    def _init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                model_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                accuracy REAL NOT NULL,
                precision REAL NOT NULL,
                recall REAL NOT NULL,
                f1_score REAL NOT NULL,
                roc_auc REAL NOT NULL,
                brier_score REAL NOT NULL,
                log_loss REAL NOT NULL,
                prediction_count INTEGER NOT NULL,
                window_size INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Drift alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drift_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                model_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                drift_type TEXT NOT NULL,
                alert_level TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                current_value REAL NOT NULL,
                baseline_value REAL NOT NULL,
                drift_magnitude REAL NOT NULL,
                description TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Model health table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                is_healthy BOOLEAN NOT NULL,
                health_score REAL NOT NULL,
                last_updated DATETIME NOT NULL,
                performance_trend TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_model_ticker ON performance_metrics(model_name, ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_model_ticker ON drift_alerts(model_name, ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON drift_alerts(timestamp)")
        
        conn.commit()
        conn.close()
    
    def track_prediction(self, model_name: str, ticker: str, prediction: float, 
                        confidence: float, actual_outcome: Optional[int] = None):
        """
        Track a single prediction for performance monitoring
        
        Args:
            model_name: Name of the model
            ticker: Market ticker
            prediction: Model prediction probability
            confidence: Model confidence score
            actual_outcome: Actual market outcome (if available)
        """
        key = f"{model_name}_{ticker}"
        
        if key not in self.performance_history:
            self.performance_history[key] = deque(maxlen=self.performance_window)
        
        # Create prediction record
        prediction_record = {
            'timestamp': datetime.now(),
            'prediction': prediction,
            'confidence': confidence,
            'actual_outcome': actual_outcome,
            'predicted_outcome': 1 if prediction > 0.5 else 0
        }
        
        self.performance_history[key].append(prediction_record)
        
        # Calculate performance metrics if we have enough data
        if len(self.performance_history[key]) >= self.min_samples_for_drift:
            self._calculate_performance_metrics(model_name, ticker)
            self._detect_drift(model_name, ticker)
            self._update_model_health(model_name, ticker)
        
        logger.debug("Prediction tracked", 
                    model_name=model_name, 
                    ticker=ticker,
                    prediction=prediction,
                    confidence=confidence)
    
    def _calculate_performance_metrics(self, model_name: str, ticker: str):
        """Calculate comprehensive performance metrics"""
        key = f"{model_name}_{ticker}"
        history = self.performance_history[key]
        
        if len(history) < 2:
            return
        
        # Extract data
        predictions = [record['prediction'] for record in history]
        confidences = [record['confidence'] for record in history]
        predicted_outcomes = [record['predicted_outcome'] for record in history]
        actual_outcomes = [record['actual_outcome'] for record in history 
                          if record['actual_outcome'] is not None]
        
        if len(actual_outcomes) < 2:
            return
        
        # Calculate metrics
        accuracy = accuracy_score(actual_outcomes, predicted_outcomes[:len(actual_outcomes)])
        precision = precision_score(actual_outcomes, predicted_outcomes[:len(actual_outcomes)], 
                                  average='weighted', zero_division=0)
        recall = recall_score(actual_outcomes, predicted_outcomes[:len(actual_outcomes)], 
                             average='weighted', zero_division=0)
        f1 = f1_score(actual_outcomes, predicted_outcomes[:len(actual_outcomes)], 
                     average='weighted', zero_division=0)
        
        # ROC-AUC and Brier score
        if len(set(actual_outcomes)) > 1:
            roc_auc = roc_auc_score(actual_outcomes, predictions[:len(actual_outcomes)])
        else:
            roc_auc = 0.5
        
        brier_score = brier_score_loss(actual_outcomes, predictions[:len(actual_outcomes)])
        
        # Log loss
        log_loss = self._calculate_log_loss(actual_outcomes, predictions[:len(actual_outcomes)])
        
        # Create performance metrics record
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            model_name=model_name,
            ticker=ticker,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc,
            brier_score=brier_score,
            log_loss=log_loss,
            prediction_count=len(history),
            window_size=len(actual_outcomes)
        )
        
        # Save to database
        self._save_performance_metrics(metrics)
        
        logger.debug("Performance metrics calculated", 
                    model_name=model_name,
                    ticker=ticker,
                    accuracy=accuracy,
                    roc_auc=roc_auc,
                    brier_score=brier_score)
    
    def _calculate_log_loss(self, actual: List[int], predicted: List[float]) -> float:
        """Calculate log loss"""
        epsilon = 1e-15
        predicted = np.clip(predicted, epsilon, 1 - epsilon)
        return -np.mean(actual * np.log(predicted) + (1 - np.array(actual)) * np.log(1 - predicted))
    
    def _detect_drift(self, model_name: str, ticker: str):
        """Detect performance drift"""
        # Get recent performance metrics
        recent_metrics = self._get_recent_metrics(model_name, ticker, window=20)
        baseline_metrics = self._get_baseline_metrics(model_name, ticker, window=50)
        
        if not recent_metrics or not baseline_metrics:
            return
        
        # Compare recent vs baseline performance
        drift_detected = False
        
        for metric_name in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']:
            recent_value = recent_metrics[metric_name]
            baseline_value = baseline_metrics[metric_name]
            
            if metric_name == 'brier_score':
                # For Brier score, increase is bad
                drift_magnitude = recent_value - baseline_value
                threshold = self.alert_thresholds.get('brier_score_increase', 0.05)
            else:
                # For other metrics, decrease is bad
                drift_magnitude = baseline_value - recent_value
                threshold = self.alert_thresholds.get(f'{metric_name}_drop', 0.05)
            
            if drift_magnitude > threshold:
                drift_detected = True
                alert_level = AlertLevel.CRITICAL if drift_magnitude > threshold * 2 else AlertLevel.WARNING
                
                alert = DriftAlert(
                    timestamp=datetime.now(),
                    model_name=model_name,
                    ticker=ticker,
                    drift_type=DriftType.PERFORMANCE,
                    alert_level=alert_level,
                    metric_name=metric_name,
                    current_value=recent_value,
                    baseline_value=baseline_value,
                    drift_magnitude=drift_magnitude,
                    description=f"{metric_name} dropped by {drift_magnitude:.3f}",
                    recommended_action=self._get_recommended_action(metric_name, drift_magnitude)
                )
                
                self.drift_alerts.append(alert)
                self._save_drift_alert(alert)
                
                logger.warning("Performance drift detected", 
                             model_name=model_name,
                             ticker=ticker,
                             metric=metric_name,
                             drift_magnitude=drift_magnitude,
                             alert_level=alert_level.value)
        
        # Detect feature drift (simplified)
        self._detect_feature_drift(model_name, ticker)
    
    def _detect_feature_drift(self, model_name: str, ticker: str):
        """Detect feature distribution drift"""
        # This is a simplified implementation
        # In practice, you would compare feature distributions over time
        
        key = f"{model_name}_{ticker}"
        history = self.performance_history[key]
        
        if len(history) < 50:
            return
        
        # Check confidence distribution drift
        recent_confidences = [record['confidence'] for record in list(history)[-20:]]
        baseline_confidences = [record['confidence'] for record in list(history)[-50:-20]]
        
        if len(recent_confidences) >= 10 and len(baseline_confidences) >= 10:
            # Kolmogorov-Smirnov test for distribution drift
            statistic, p_value = stats.ks_2samp(baseline_confidences, recent_confidences)
            
            if p_value < 0.05:  # Significant drift detected
                alert = DriftAlert(
                    timestamp=datetime.now(),
                    model_name=model_name,
                    ticker=ticker,
                    drift_type=DriftType.FEATURE,
                    alert_level=AlertLevel.WARNING,
                    metric_name='confidence_distribution',
                    current_value=np.mean(recent_confidences),
                    baseline_value=np.mean(baseline_confidences),
                    drift_magnitude=statistic,
                    description=f"Confidence distribution drift detected (KS statistic: {statistic:.3f})",
                    recommended_action="Consider retraining model or investigating feature changes"
                )
                
                self.drift_alerts.append(alert)
                self._save_drift_alert(alert)
                
                logger.warning("Feature drift detected", 
                             model_name=model_name,
                             ticker=ticker,
                             ks_statistic=statistic,
                             p_value=p_value)
    
    def _get_recent_metrics(self, model_name: str, ticker: str, window: int = 20) -> Optional[Dict[str, float]]:
        """Get recent performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT accuracy, precision, recall, f1_score, roc_auc, brier_score
            FROM performance_metrics
            WHERE model_name = ? AND ticker = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        cursor.execute(query, (model_name, ticker, window))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return None
        
        # Calculate averages
        metrics = {}
        for i, metric_name in enumerate(['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'brier_score']):
            values = [row[i] for row in results]
            metrics[metric_name] = np.mean(values)
        
        return metrics
    
    def _get_baseline_metrics(self, model_name: str, ticker: str, window: int = 50) -> Optional[Dict[str, float]]:
        """Get baseline performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT accuracy, precision, recall, f1_score, roc_auc, brier_score
            FROM performance_metrics
            WHERE model_name = ? AND ticker = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, (model_name, ticker, window, window))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return None
        
        # Calculate averages
        metrics = {}
        for i, metric_name in enumerate(['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'brier_score']):
            values = [row[i] for row in results]
            metrics[metric_name] = np.mean(values)
        
        return metrics
    
    def _get_recommended_action(self, metric_name: str, drift_magnitude: float) -> str:
        """Get recommended action based on drift type and magnitude"""
        if drift_magnitude > 0.1:
            return "Immediate model retraining required"
        elif drift_magnitude > 0.05:
            return "Schedule model retraining within 24 hours"
        else:
            return "Monitor closely, consider retraining if trend continues"
    
    def _update_model_health(self, model_name: str, ticker: str):
        """Update overall model health status"""
        key = f"{model_name}_{ticker}"
        
        # Get recent performance
        recent_metrics = self._get_recent_metrics(model_name, ticker, window=20)
        if not recent_metrics:
            return
        
        # Calculate health score (0-1, higher is better)
        health_score = (
            recent_metrics['accuracy'] * 0.3 +
            recent_metrics['roc_auc'] * 0.3 +
            recent_metrics['f1_score'] * 0.2 +
            (1 - recent_metrics['brier_score']) * 0.2
        )
        
        # Determine performance trend
        baseline_metrics = self._get_baseline_metrics(model_name, ticker, window=50)
        if baseline_metrics:
            accuracy_change = recent_metrics['accuracy'] - baseline_metrics['accuracy']
            if accuracy_change > 0.02:
                performance_trend = "improving"
            elif accuracy_change < -0.02:
                performance_trend = "declining"
            else:
                performance_trend = "stable"
        else:
            performance_trend = "unknown"
        
        # Check for active alerts
        active_alerts = [alert for alert in self.drift_alerts 
                        if alert.model_name == model_name and alert.ticker == ticker 
                        and not alert.acknowledged]
        
        # Determine if model is healthy
        is_healthy = (health_score > 0.6 and 
                     len([a for a in active_alerts if a.alert_level == AlertLevel.CRITICAL]) == 0)
        
        # Get recommended action
        if not is_healthy:
            recommended_action = "Model requires attention - check alerts and consider retraining"
        elif performance_trend == "declining":
            recommended_action = "Monitor closely - performance declining"
        else:
            recommended_action = "Model performing well"
        
        # Update model health
        health = ModelHealth(
            model_name=model_name,
            ticker=ticker,
            is_healthy=is_healthy,
            health_score=health_score,
            last_updated=datetime.now(),
            active_alerts=active_alerts,
            performance_trend=performance_trend,
            recommended_action=recommended_action
        )
        
        self.model_health[key] = health
        self._save_model_health(health)
        
        logger.info("Model health updated", 
                   model_name=model_name,
                   ticker=ticker,
                   health_score=health_score,
                   is_healthy=is_healthy,
                   performance_trend=performance_trend)
    
    def _save_performance_metrics(self, metrics: PerformanceMetrics):
        """Save performance metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics 
            (timestamp, model_name, ticker, accuracy, precision, recall, f1_score, 
             roc_auc, brier_score, log_loss, prediction_count, window_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.timestamp, metrics.model_name, metrics.ticker,
            metrics.accuracy, metrics.precision, metrics.recall, metrics.f1_score,
            metrics.roc_auc, metrics.brier_score, metrics.log_loss,
            metrics.prediction_count, metrics.window_size
        ))
        
        conn.commit()
        conn.close()
    
    def _save_drift_alert(self, alert: DriftAlert):
        """Save drift alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO drift_alerts 
            (timestamp, model_name, ticker, drift_type, alert_level, metric_name,
             current_value, baseline_value, drift_magnitude, description, recommended_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.timestamp, alert.model_name, alert.ticker, alert.drift_type.value,
            alert.alert_level.value, alert.metric_name, alert.current_value,
            alert.baseline_value, alert.drift_magnitude, alert.description,
            alert.recommended_action
        ))
        
        conn.commit()
        conn.close()
    
    def _save_model_health(self, health: ModelHealth):
        """Save model health to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO model_health 
            (model_name, ticker, is_healthy, health_score, last_updated, 
             performance_trend, recommended_action)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            health.model_name, health.ticker, health.is_healthy, health.health_score,
            health.last_updated, health.performance_trend, health.recommended_action
        ))
        
        conn.commit()
        conn.close()
    
    def get_model_health(self, model_name: str, ticker: str) -> Optional[ModelHealth]:
        """Get current model health status"""
        key = f"{model_name}_{ticker}"
        return self.model_health.get(key)
    
    def get_active_alerts(self, model_name: Optional[str] = None, 
                         ticker: Optional[str] = None) -> List[DriftAlert]:
        """Get active (unacknowledged) alerts"""
        alerts = [alert for alert in self.drift_alerts if not alert.acknowledged]
        
        if model_name:
            alerts = [alert for alert in alerts if alert.model_name == model_name]
        if ticker:
            alerts = [alert for alert in alerts if alert.ticker == ticker]
        
        return alerts
    
    def acknowledge_alert(self, alert_id: int):
        """Acknowledge a drift alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE drift_alerts 
            SET acknowledged = TRUE 
            WHERE id = ?
        """, (alert_id,))
        
        conn.commit()
        conn.close()
        
        # Update in-memory alerts
        for alert in self.drift_alerts:
            if hasattr(alert, 'id') and alert.id == alert_id:
                alert.acknowledged = True
                break
    
    def should_retrain(self, model_name: str, ticker: str) -> Tuple[bool, str]:
        """
        Determine if a model should be retrained
        
        Returns:
            Tuple of (should_retrain, reason)
        """
        health = self.get_model_health(model_name, ticker)
        if not health:
            return False, "No health data available"
        
        # Check for critical alerts
        critical_alerts = [alert for alert in health.active_alerts 
                          if alert.alert_level == AlertLevel.CRITICAL]
        
        if critical_alerts:
            return True, f"Critical alerts: {len(critical_alerts)}"
        
        # Check health score
        if health.health_score < 0.5:
            return True, f"Low health score: {health.health_score:.3f}"
        
        # Check performance trend
        if health.performance_trend == "declining":
            return True, "Performance declining"
        
        return False, "Model performing adequately"
    
    def get_performance_summary(self, model_name: str, ticker: str, days: int = 7) -> Dict[str, Any]:
        """Get performance summary for a model"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT accuracy, precision, recall, f1_score, roc_auc, brier_score, timestamp
            FROM performance_metrics
            WHERE model_name = ? AND ticker = ? 
            AND timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp
        """.format(days)
        
        cursor.execute(query, (model_name, ticker))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {'error': 'No performance data available'}
        
        # Calculate summary statistics
        metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'brier_score']
        summary = {}
        
        for i, metric in enumerate(metrics):
            values = [row[i] for row in results]
            summary[metric] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'trend': self._calculate_trend(values)
            }
        
        # Get health status
        health = self.get_model_health(model_name, ticker)
        summary['health'] = health
        
        # Get active alerts
        alerts = self.get_active_alerts(model_name, ticker)
        summary['active_alerts'] = len(alerts)
        
        return summary
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend
        x = np.arange(len(values))
        slope, _, _, _, _ = stats.linregress(x, values)
        
        if slope > 0.001:
            return "improving"
        elif slope < -0.001:
            return "declining"
        else:
            return "stable"
