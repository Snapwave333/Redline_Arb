"""
Profit Reinvestment Strategy for Kalshi Trading Bot

This module implements an exponential growth strategy by reinvesting profits
from successful bets to place larger bets, growing the bankroll daily.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

from .config import config
from .kalshi_client import KalshiAPIClient, Position
from .strategy import TradingSignal
from .execution import ExecutionResult

logger = structlog.get_logger(__name__)


@dataclass
class ProfitReinvestmentConfig:
    """Configuration for profit reinvestment strategy"""
    enabled: bool = True
    daily_reinvestment_pct: float = 0.8  # Reinvest 80% of daily profits
    max_reinvestment_pct: float = 0.5  # Max 50% of total bankroll per day
    min_profit_threshold: float = 10.0  # Minimum $10 profit to reinvest
    compound_growth_target: float = 0.1  # Target 10% daily growth
    emergency_reserve_pct: float = 0.1  # Keep 10% as emergency reserve


@dataclass
class DailyPerformance:
    """Daily performance tracking"""
    date: datetime
    starting_balance: float
    ending_balance: float
    daily_pnl: float
    trades_made: int
    winning_trades: int
    losing_trades: int
    reinvestment_amount: float
    growth_rate: float


@dataclass
class ExponentialGrowthPlan:
    """Exponential growth plan"""
    current_balance: float
    target_daily_growth: float
    reinvestment_amount: float
    expected_new_balance: float
    days_to_double: float
    projected_30_day_balance: float


class ProfitReinvestmentEngine:
    """Engine for managing profit reinvestment and exponential growth"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.config = ProfitReinvestmentConfig()
        self.daily_performance: List[DailyPerformance] = []
        self.current_day_start_balance: float = 0.0
        self.daily_trades_count: int = 0
        self.daily_winning_trades: int = 0
        self.daily_losing_trades: int = 0
        self.last_reset_date: Optional[datetime] = None
    
    async def initialize_daily_tracking(self):
        """Initialize daily tracking for a new day"""
        try:
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            today = datetime.now().date()
            
            # Check if we need to reset for a new day
            if (self.last_reset_date is None or 
                self.last_reset_date.date() != today):
                
                # Save previous day's performance if exists
                if self.last_reset_date is not None:
                    await self._save_daily_performance()
                
                # Reset for new day
                self.current_day_start_balance = current_balance
                self.daily_trades_count = 0
                self.daily_winning_trades = 0
                self.daily_losing_trades = 0
                self.last_reset_date = datetime.now()
                
                logger.info("Daily tracking initialized",
                           date=today,
                           starting_balance=current_balance)
            
        except Exception as e:
            logger.error("Failed to initialize daily tracking", error=str(e))
    
    async def _save_daily_performance(self):
        """Save the previous day's performance"""
        try:
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            daily_pnl = current_balance - self.current_day_start_balance
            growth_rate = daily_pnl / self.current_day_start_balance if self.current_day_start_balance > 0 else 0
            
            performance = DailyPerformance(
                date=self.last_reset_date.date(),
                starting_balance=self.current_day_start_balance,
                ending_balance=current_balance,
                daily_pnl=daily_pnl,
                trades_made=self.daily_trades_count,
                winning_trades=self.daily_winning_trades,
                losing_trades=self.daily_losing_trades,
                reinvestment_amount=0.0,  # Will be calculated
                growth_rate=growth_rate
            )
            
            self.daily_performance.append(performance)
            
            logger.info("Daily performance saved",
                       date=performance.date,
                       daily_pnl=daily_pnl,
                       growth_rate=growth_rate,
                       trades=self.daily_trades_count)
            
        except Exception as e:
            logger.error("Failed to save daily performance", error=str(e))
    
    def calculate_reinvestment_amount(self, current_balance: float, 
                                    daily_pnl: float) -> float:
        """
        Calculate how much to reinvest from daily profits
        
        Args:
            current_balance: Current total balance
            daily_pnl: Today's profit/loss
        
        Returns:
            Amount to reinvest
        """
        if not self.config.enabled or daily_pnl <= 0:
            return 0.0
        
        # Only reinvest if we have minimum profit threshold
        if daily_pnl < self.config.min_profit_threshold:
            logger.info("Daily profit below threshold, no reinvestment",
                       daily_pnl=daily_pnl,
                       threshold=self.config.min_profit_threshold)
            return 0.0
        
        # Calculate reinvestment amount
        reinvestment_amount = daily_pnl * self.config.daily_reinvestment_pct
        
        # Apply maximum reinvestment limit
        max_reinvestment = current_balance * self.config.max_reinvestment_pct
        reinvestment_amount = min(reinvestment_amount, max_reinvestment)
        
        # Ensure we keep emergency reserve
        emergency_reserve = current_balance * self.config.emergency_reserve_pct
        available_for_reinvestment = current_balance - emergency_reserve
        reinvestment_amount = min(reinvestment_amount, available_for_reinvestment)
        
        logger.info("Reinvestment amount calculated",
                   daily_pnl=daily_pnl,
                   reinvestment_amount=reinvestment_amount,
                   reinvestment_pct=self.config.daily_reinvestment_pct)
        
        return reinvestment_amount
    
    def create_exponential_growth_plan(self, current_balance: float) -> ExponentialGrowthPlan:
        """
        Create an exponential growth plan
        
        Args:
            current_balance: Current total balance
        
        Returns:
            Exponential growth plan
        """
        target_daily_growth = self.config.compound_growth_target
        
        # Calculate reinvestment amount for next day
        # Assume we'll make the target daily growth
        expected_daily_profit = current_balance * target_daily_growth
        reinvestment_amount = expected_daily_profit * self.config.daily_reinvestment_pct
        
        # Calculate expected new balance
        expected_new_balance = current_balance + expected_daily_profit
        
        # Calculate days to double (rule of 72)
        days_to_double = 72 / (target_daily_growth * 100)
        
        # Project 30-day balance
        projected_30_day_balance = current_balance * ((1 + target_daily_growth) ** 30)
        
        plan = ExponentialGrowthPlan(
            current_balance=current_balance,
            target_daily_growth=target_daily_growth,
            reinvestment_amount=reinvestment_amount,
            expected_new_balance=expected_new_balance,
            days_to_double=days_to_double,
            projected_30_day_balance=projected_30_day_balance
        )
        
        logger.info("Exponential growth plan created",
                   current_balance=current_balance,
                   target_growth=target_daily_growth,
                   days_to_double=days_to_double,
                   projected_30_day=projected_30_day_balance)
        
        return plan
    
    def adjust_position_sizes_for_growth(self, signal: TradingSignal, 
                                       current_balance: float,
                                       daily_pnl: float) -> TradingSignal:
        """
        Adjust position sizes to accelerate growth using reinvested profits
        
        Args:
            signal: Original trading signal
            current_balance: Current total balance
            daily_pnl: Today's profit/loss
        
        Returns:
            Adjusted signal with larger position size
        """
        if not self.config.enabled:
            return signal
        
        # Calculate reinvestment amount
        reinvestment_amount = self.calculate_reinvestment_amount(current_balance, daily_pnl)
        
        if reinvestment_amount <= 0:
            return signal
        
        # Calculate growth multiplier
        # Use a portion of reinvestment to increase position sizes
        growth_multiplier = 1.0 + (reinvestment_amount / current_balance) * 0.5
        
        # Apply growth multiplier to position size
        new_quantity = int(signal.quantity * growth_multiplier)
        
        # Ensure we don't exceed safety limits
        max_safe_quantity = int(current_balance * 0.1 / signal.price)  # Max 10% per position
        new_quantity = min(new_quantity, max_safe_quantity)
        
        # Create enhanced signal
        enhanced_signal = TradingSignal(
            ticker=signal.ticker,
            side=signal.side,
            quantity=new_quantity,
            price=signal.price,
            model_probability=signal.model_probability,
            implied_probability=signal.implied_probability,
            probability_delta=signal.probability_delta,
            confidence=signal.confidence,
            kelly_fraction=signal.kelly_fraction,
            expected_value=signal.expected_value * growth_multiplier,
            timestamp=signal.timestamp,
            reason=f"{signal.reason} (Growth Enhanced: {new_quantity} shares)"
        )
        
        logger.info("Position size enhanced for growth",
                   ticker=signal.ticker,
                   original_quantity=signal.quantity,
                   enhanced_quantity=new_quantity,
                   growth_multiplier=growth_multiplier,
                   reinvestment_amount=reinvestment_amount)
        
        return enhanced_signal
    
    def track_trade_result(self, signal: TradingSignal, result: ExecutionResult, pnl: float):
        """Track trade result for daily performance"""
        self.daily_trades_count += 1
        
        if pnl > 0:
            self.daily_winning_trades += 1
        else:
            self.daily_losing_trades += 1
        
        logger.info("Trade result tracked",
                   ticker=signal.ticker,
                   pnl=pnl,
                   daily_trades=self.daily_trades_count,
                   winning_trades=self.daily_winning_trades)
    
    def get_growth_summary(self) -> Dict[str, any]:
        """Get comprehensive growth summary"""
        if not self.daily_performance:
            return {"message": "No performance data available"}
        
        # Calculate growth metrics
        total_growth = 0.0
        total_trades = 0
        total_winning_trades = 0
        
        for performance in self.daily_performance:
            total_growth += performance.growth_rate
            total_trades += performance.trades_made
            total_winning_trades += performance.winning_trades
        
        avg_daily_growth = total_growth / len(self.daily_performance) if self.daily_performance else 0
        win_rate = total_winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate compound growth
        if len(self.daily_performance) > 0:
            first_balance = self.daily_performance[0].starting_balance
            last_balance = self.daily_performance[-1].ending_balance
            total_compound_growth = (last_balance - first_balance) / first_balance if first_balance > 0 else 0
        else:
            total_compound_growth = 0
        
        return {
            "total_days_tracked": len(self.daily_performance),
            "average_daily_growth": avg_daily_growth,
            "total_compound_growth": total_compound_growth,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "reinvestment_config": {
                "enabled": self.config.enabled,
                "daily_reinvestment_pct": self.config.daily_reinvestment_pct,
                "max_reinvestment_pct": self.config.max_reinvestment_pct,
                "min_profit_threshold": self.config.min_profit_threshold,
                "compound_growth_target": self.config.compound_growth_target
            },
            "recent_performance": self.daily_performance[-5:] if len(self.daily_performance) >= 5 else self.daily_performance
        }
    
    def update_config(self, **kwargs):
        """Update reinvestment configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info("Reinvestment config updated", key=key, value=value)


class ExponentialGrowthManager:
    """Main manager for exponential growth strategy"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.reinvestment_engine = ProfitReinvestmentEngine(client)
        self.is_active = False
    
    async def initialize(self):
        """Initialize exponential growth manager"""
        await self.reinvestment_engine.initialize_daily_tracking()
        self.is_active = True
        logger.info("Exponential growth manager initialized")
    
    async def enhance_signal_for_growth(self, signal: TradingSignal) -> TradingSignal:
        """
        Enhance a trading signal for exponential growth
        
        Args:
            signal: Original trading signal
        
        Returns:
            Enhanced signal with growth-optimized position size
        """
        try:
            # Get current balance
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            # Calculate today's P&L
            daily_pnl = current_balance - self.reinvestment_engine.current_day_start_balance
            
            # Enhance signal for growth
            enhanced_signal = self.reinvestment_engine.adjust_position_sizes_for_growth(
                signal, current_balance, daily_pnl
            )
            
            return enhanced_signal
            
        except Exception as e:
            logger.error("Failed to enhance signal for growth", error=str(e))
            return signal
    
    async def track_trade_execution(self, signal: TradingSignal, result: ExecutionResult):
        """Track trade execution for growth analysis"""
        try:
            # Calculate P&L (simplified - would need actual trade outcome)
            # This would be updated when the trade closes
            pnl = 0.0  # Placeholder - would be calculated from actual trade result
            
            self.reinvestment_engine.track_trade_result(signal, result, pnl)
            
        except Exception as e:
            logger.error("Failed to track trade execution", error=str(e))
    
    def get_growth_plan(self) -> ExponentialGrowthPlan:
        """Get current exponential growth plan"""
        try:
            # This would need to be called with actual current balance
            current_balance = 1000.0  # Placeholder
            return self.reinvestment_engine.create_exponential_growth_plan(current_balance)
        except Exception as e:
            logger.error("Failed to get growth plan", error=str(e))
            return None
    
    def get_growth_summary(self) -> Dict[str, any]:
        """Get comprehensive growth summary"""
        return self.reinvestment_engine.get_growth_summary()
    
    def configure_growth_strategy(self, **kwargs):
        """Configure growth strategy parameters"""
        self.reinvestment_engine.update_config(**kwargs)
        logger.info("Growth strategy configured", config=kwargs)
