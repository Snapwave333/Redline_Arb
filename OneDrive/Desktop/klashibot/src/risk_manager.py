"""
Risk Management System for Kalshi Trading Bot

This module implements comprehensive risk management including position limits,
drawdown protection, and portfolio risk monitoring.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog

from .config import config
from .kalshi_client import Position
from .strategy import TradingSignal
from .execution import ExecutionOrder

logger = structlog.get_logger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Risk metrics structure"""
    portfolio_value: float
    cash_balance: float
    total_exposure: float
    max_position_size: float
    portfolio_var: float  # Value at Risk
    max_drawdown: float
    current_drawdown: float
    daily_pnl: float
    risk_level: RiskLevel
    timestamp: datetime


@dataclass
class RiskViolation:
    """Risk violation structure"""
    violation_type: str
    severity: RiskLevel
    message: str
    current_value: float
    limit_value: float
    timestamp: datetime
    action_required: str


class PositionRiskManager:
    """Manages position-level risk"""
    
    def __init__(self):
        self.max_position_size = config.trading.max_position_size
        self.max_position_value_pct = 0.1  # 10% of portfolio per position
        self.max_correlation_exposure = 0.2  # 20% max exposure to correlated positions
    
    def validate_position_size(self, signal: TradingSignal, 
                             portfolio_value: float) -> Tuple[bool, str]:
        """
        Validate position size against risk limits
        
        Args:
            signal: Trading signal
            portfolio_value: Total portfolio value
        
        Returns:
            Tuple of (is_valid, reason)
        """
        position_value = signal.quantity * signal.price
        
        # Check absolute position size limit
        if signal.quantity > self.max_position_size:
            return False, f"Position size {signal.quantity} exceeds limit {self.max_position_size}"
        
        # Check position value as percentage of portfolio
        position_pct = position_value / portfolio_value
        if position_pct > self.max_position_value_pct:
            return False, f"Position value {position_pct:.1%} exceeds limit {self.max_position_value_pct:.1%}"
        
        return True, "Position size valid"
    
    def calculate_position_risk(self, position: Position, 
                              current_price: float) -> Dict[str, float]:
        """Calculate risk metrics for a position"""
        position_value = position.quantity * current_price
        unrealized_pnl = position.unrealized_pnl
        
        # Calculate risk metrics
        risk_metrics = {
            "position_value": position_value,
            "unrealized_pnl": unrealized_pnl,
            "pnl_pct": unrealized_pnl / position_value if position_value > 0 else 0,
            "exposure_pct": position_value / config.risk.max_portfolio_risk if config.risk.max_portfolio_risk > 0 else 0
        }
        
        return risk_metrics


class PortfolioRiskManager:
    """Manages portfolio-level risk"""
    
    def __init__(self):
        self.max_daily_loss = config.risk.max_daily_loss
        self.max_portfolio_risk = config.risk.max_portfolio_risk
        self.max_drawdown_pct = 0.15  # 15% maximum drawdown
        self.daily_pnl_tracker = {}
        self.portfolio_high_water_mark = 0.0
    
    def validate_portfolio_risk(self, positions: Dict[str, Position], 
                               portfolio_value: float) -> List[RiskViolation]:
        """
        Validate portfolio risk against limits
        
        Args:
            positions: Current positions
            portfolio_value: Total portfolio value
        
        Returns:
            List of risk violations
        """
        violations = []
        
        # Calculate total exposure
        total_exposure = sum(pos.quantity * pos.average_price for pos in positions.values())
        
        # Check portfolio risk limit
        if total_exposure > self.max_portfolio_risk:
            violations.append(RiskViolation(
                violation_type="portfolio_exposure",
                severity=RiskLevel.HIGH,
                message=f"Total exposure {total_exposure:.2f} exceeds limit {self.max_portfolio_risk:.2f}",
                current_value=total_exposure,
                limit_value=self.max_portfolio_risk,
                timestamp=datetime.now(),
                action_required="Reduce positions"
            ))
        
        # Check daily loss limit
        daily_pnl = self.get_daily_pnl()
        if daily_pnl < -self.max_daily_loss:
            violations.append(RiskViolation(
                violation_type="daily_loss",
                severity=RiskLevel.CRITICAL,
                message=f"Daily loss {daily_pnl:.2f} exceeds limit {self.max_daily_loss:.2f}",
                current_value=daily_pnl,
                limit_value=-self.max_daily_loss,
                timestamp=datetime.now(),
                action_required="Stop trading"
            ))
        
        # Check drawdown
        current_drawdown = self.calculate_drawdown(portfolio_value)
        if current_drawdown > self.max_drawdown_pct:
            violations.append(RiskViolation(
                violation_type="drawdown",
                severity=RiskLevel.HIGH,
                message=f"Drawdown {current_drawdown:.1%} exceeds limit {self.max_drawdown_pct:.1%}",
                current_value=current_drawdown,
                limit_value=self.max_drawdown_pct,
                timestamp=datetime.now(),
                action_required="Reduce risk"
            ))
        
        return violations
    
    def get_daily_pnl(self) -> float:
        """Get today's P&L"""
        today = datetime.now().date()
        return self.daily_pnl_tracker.get(today, 0.0)
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L"""
        today = datetime.now().date()
        self.daily_pnl_tracker[today] = self.daily_pnl_tracker.get(today, 0.0) + pnl
    
    def calculate_drawdown(self, current_value: float) -> float:
        """Calculate current drawdown from high water mark"""
        if current_value > self.portfolio_high_water_mark:
            self.portfolio_high_water_mark = current_value
        
        if self.portfolio_high_water_mark == 0:
            return 0.0
        
        drawdown = (self.portfolio_high_water_mark - current_value) / self.portfolio_high_water_mark
        return drawdown
    
    def calculate_var(self, positions: Dict[str, Position], 
                     confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) for the portfolio
        
        Args:
            positions: Current positions
            confidence_level: Confidence level for VaR calculation
        
        Returns:
            VaR value
        """
        if not positions:
            return 0.0
        
        # Simple VaR calculation based on position sizes and volatility assumptions
        total_exposure = sum(pos.quantity * pos.average_price for pos in positions.values())
        
        # Assume 2% daily volatility for prediction markets
        daily_volatility = 0.02
        
        # Calculate VaR using normal distribution approximation
        z_score = np.percentile(np.random.normal(0, 1, 10000), (1 - confidence_level) * 100)
        var = total_exposure * daily_volatility * abs(z_score)
        
        return var


class CorrelationRiskManager:
    """Manages correlation risk between positions"""
    
    def __init__(self):
        self.max_correlation_exposure = 0.3  # 30% max exposure to correlated positions
        self.correlation_threshold = 0.7  # Positions with correlation > 0.7 are considered correlated
    
    def calculate_position_correlation(self, ticker1: str, ticker2: str) -> float:
        """
        Calculate correlation between two positions
        This is a simplified implementation - in practice, you'd use historical data
        """
        # Simple correlation based on market categories
        # This would be enhanced with actual historical correlation data
        
        categories = {
            "POLITICS": ["TRUMP", "BIDEN", "ELECTION"],
            "ECONOMICS": ["GDP", "INFLATION", "UNEMPLOYMENT"],
            "SPORTS": ["NFL", "NBA", "MLB"],
            "WEATHER": ["HURRICANE", "SNOW", "RAIN"]
        }
        
        category1 = self._get_category(ticker1, categories)
        category2 = self._get_category(ticker2, categories)
        
        if category1 == category2:
            return 0.8  # High correlation within same category
        else:
            return 0.2  # Low correlation across categories
    
    def _get_category(self, ticker: str, categories: Dict[str, List[str]]) -> str:
        """Get category for a ticker"""
        ticker_upper = ticker.upper()
        for category, keywords in categories.items():
            if any(keyword in ticker_upper for keyword in keywords):
                return category
        return "OTHER"
    
    def validate_correlation_risk(self, new_signal: TradingSignal, 
                                 existing_positions: Dict[str, Position]) -> Tuple[bool, str]:
        """
        Validate correlation risk for a new position
        
        Args:
            new_signal: New trading signal
            existing_positions: Existing positions
        
        Returns:
            Tuple of (is_valid, reason)
        """
        if not existing_positions:
            return True, "No existing positions"
        
        correlated_exposure = 0.0
        
        for ticker, position in existing_positions.items():
            correlation = self.calculate_position_correlation(new_signal.ticker, ticker)
            
            if correlation > self.correlation_threshold:
                position_value = position.quantity * position.average_price
                correlated_exposure += position_value
        
        if correlated_exposure > self.max_correlation_exposure:
            return False, f"Correlated exposure {correlated_exposure:.2f} exceeds limit"
        
        return True, "Correlation risk acceptable"


class RiskManager:
    """Main risk management system"""
    
    def __init__(self):
        self.position_risk_manager = PositionRiskManager()
        self.portfolio_risk_manager = PortfolioRiskManager()
        self.correlation_risk_manager = CorrelationRiskManager()
        self.risk_violations: List[RiskViolation] = []
        self.risk_metrics_history: List[RiskMetrics] = []
    
    def validate_cash_safety(self, required_cash: float, 
                           available_cash: float) -> Tuple[bool, str]:
        """
        Validate cash safety for a trade
        
        Args:
            required_cash: Cash needed for the trade
            available_cash: Currently available cash
        
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check basic availability
        if required_cash > available_cash:
            return False, f"Insufficient cash: need ${required_cash:.2f}, have ${available_cash:.2f}"
        
        # Check minimum reserve
        min_reserve = 10.0
        usable_cash = max(0.0, available_cash - min_reserve)
        if required_cash > usable_cash:
            return False, f"Would exceed safe cash limit: need ${required_cash:.2f}, usable ${usable_cash:.2f}"
        
        # Check maximum usage percentage
        max_usage_pct = 0.95
        max_safe_amount = available_cash * max_usage_pct
        if required_cash > max_safe_amount:
            return False, f"Exceeds maximum safe usage: need ${required_cash:.2f}, max safe ${max_safe_amount:.2f}"
        
        return True, "Cash safety check passed"
    
    def validate_signal(self, signal: TradingSignal, 
                      portfolio_value: float,
                      existing_positions: Dict[str, Position]) -> Tuple[bool, List[str]]:
        """
        Validate a trading signal against all risk limits
        
        Args:
            signal: Trading signal to validate
            portfolio_value: Total portfolio value
            existing_positions: Existing positions
        
        Returns:
            Tuple of (is_valid, list_of_reasons)
        """
        reasons = []
        
        # Validate position size
        is_valid_size, size_reason = self.position_risk_manager.validate_position_size(
            signal, portfolio_value
        )
        if not is_valid_size:
            reasons.append(size_reason)
        
        # Validate correlation risk
        is_valid_correlation, correlation_reason = self.correlation_risk_manager.validate_correlation_risk(
            signal, existing_positions
        )
        if not is_valid_correlation:
            reasons.append(correlation_reason)
        
        # Validate portfolio risk
        portfolio_violations = self.portfolio_risk_manager.validate_portfolio_risk(
            existing_positions, portfolio_value
        )
        
        if portfolio_violations:
            for violation in portfolio_violations:
                reasons.append(violation.message)
        
        # Validate cash safety
        required_cash = signal.quantity * signal.price
        # This would need to be passed from the execution manager
        # For now, we'll add a placeholder check
        cash_safety_check = True  # Will be implemented with actual cash balance
        
        is_valid = len(reasons) == 0
        
        if not is_valid:
            logger.warning("Signal validation failed", 
                          ticker=signal.ticker,
                          reasons=reasons)
        
        return is_valid, reasons
    
    def update_risk_metrics(self, positions: Dict[str, Position], 
                           portfolio_value: float,
                           cash_balance: float) -> RiskMetrics:
        """
        Update risk metrics for the portfolio
        
        Args:
            positions: Current positions
            portfolio_value: Total portfolio value
            cash_balance: Cash balance
        
        Returns:
            Current risk metrics
        """
        # Calculate metrics
        total_exposure = sum(pos.quantity * pos.average_price for pos in positions.values())
        max_position_size = max((pos.quantity for pos in positions.values()), default=0)
        portfolio_var = self.portfolio_risk_manager.calculate_var(positions)
        current_drawdown = self.portfolio_risk_manager.calculate_drawdown(portfolio_value)
        daily_pnl = self.portfolio_risk_manager.get_daily_pnl()
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            current_drawdown, daily_pnl, total_exposure, portfolio_value
        )
        
        metrics = RiskMetrics(
            portfolio_value=portfolio_value,
            cash_balance=cash_balance,
            total_exposure=total_exposure,
            max_position_size=max_position_size,
            portfolio_var=portfolio_var,
            max_drawdown=self.portfolio_risk_manager.max_drawdown_pct,
            current_drawdown=current_drawdown,
            daily_pnl=daily_pnl,
            risk_level=risk_level,
            timestamp=datetime.now()
        )
        
        # Store metrics
        self.risk_metrics_history.append(metrics)
        
        # Keep only last 1000 metrics
        if len(self.risk_metrics_history) > 1000:
            self.risk_metrics_history = self.risk_metrics_history[-1000:]
        
        logger.info("Risk metrics updated", 
                   risk_level=risk_level.value,
                   total_exposure=total_exposure,
                   current_drawdown=current_drawdown)
        
        return metrics
    
    def _determine_risk_level(self, drawdown: float, daily_pnl: float, 
                            total_exposure: float, portfolio_value: float) -> RiskLevel:
        """Determine current risk level"""
        # Critical risk conditions
        if daily_pnl < -self.portfolio_risk_manager.max_daily_loss:
            return RiskLevel.CRITICAL
        
        if drawdown > self.portfolio_risk_manager.max_drawdown_pct:
            return RiskLevel.CRITICAL
        
        # High risk conditions
        if drawdown > self.portfolio_risk_manager.max_drawdown_pct * 0.8:
            return RiskLevel.HIGH
        
        if total_exposure > self.portfolio_risk_manager.max_portfolio_risk * 0.9:
            return RiskLevel.HIGH
        
        # Medium risk conditions
        if drawdown > self.portfolio_risk_manager.max_drawdown_pct * 0.5:
            return RiskLevel.MEDIUM
        
        if total_exposure > self.portfolio_risk_manager.max_portfolio_risk * 0.7:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def get_risk_summary(self) -> Dict[str, any]:
        """Get current risk summary"""
        if not self.risk_metrics_history:
            return {}
        
        current_metrics = self.risk_metrics_history[-1]
        
        return {
            "risk_level": current_metrics.risk_level.value,
            "portfolio_value": current_metrics.portfolio_value,
            "total_exposure": current_metrics.total_exposure,
            "current_drawdown": current_metrics.current_drawdown,
            "daily_pnl": current_metrics.daily_pnl,
            "portfolio_var": current_metrics.portfolio_var,
            "max_position_size": current_metrics.max_position_size,
            "n_violations": len(self.risk_violations)
        }
    
    def should_stop_trading(self) -> bool:
        """Determine if trading should be stopped due to risk"""
        if not self.risk_metrics_history:
            return False
        
        current_metrics = self.risk_metrics_history[-1]
        
        # Stop trading conditions
        stop_conditions = [
            current_metrics.risk_level == RiskLevel.CRITICAL,
            current_metrics.daily_pnl < -self.portfolio_risk_manager.max_daily_loss,
            current_metrics.current_drawdown > self.portfolio_risk_manager.max_drawdown_pct
        ]
        
        return any(stop_conditions)
    
    def get_position_risk_summary(self, positions: Dict[str, Position]) -> Dict[str, Dict[str, float]]:
        """Get risk summary for all positions"""
        position_risks = {}
        
        for ticker, position in positions.items():
            # Calculate current price (this would come from market data)
            current_price = position.average_price  # Simplified
            
            risk_metrics = self.position_risk_manager.calculate_position_risk(
                position, current_price
            )
            
            position_risks[ticker] = risk_metrics
        
        return position_risks
    
    def add_risk_violation(self, violation: RiskViolation):
        """Add a risk violation"""
        self.risk_violations.append(violation)
        
        logger.warning("Risk violation detected", 
                      violation_type=violation.violation_type,
                      severity=violation.severity.value,
                      message=violation.message)
    
    def clear_risk_violations(self):
        """Clear all risk violations"""
        self.risk_violations.clear()
        logger.info("Risk violations cleared")
