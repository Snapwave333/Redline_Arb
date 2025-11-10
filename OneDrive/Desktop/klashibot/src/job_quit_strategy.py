"""
Daily Profit Withdrawal Strategy for Kalshi Trading Bot

This module implements a strategy to generate $400 in withdrawable profits daily,
enabling users to quit their jobs and live off trading profits.
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
class DailyProfitTarget:
    """Daily profit target configuration"""
    target_daily_profit: float = 400.0  # $400 daily target
    minimum_withdrawable: float = 350.0  # Minimum $350 to withdraw
    emergency_reserve: float = 1000.0  # Keep $1000 emergency reserve
    max_daily_risk: float = 200.0  # Max $200 daily risk
    profit_withdrawal_pct: float = 0.8  # Withdraw 80% of profits


@dataclass
class DailyProfitStatus:
    """Daily profit status tracking"""
    date: datetime
    target_profit: float
    current_profit: float
    remaining_target: float
    trades_made: int
    trades_needed: int
    estimated_completion_time: Optional[datetime]
    risk_taken: float
    max_risk_allowed: float


@dataclass
class WithdrawalPlan:
    """Withdrawal plan for daily profits"""
    daily_target: float
    weekly_target: float
    monthly_target: float
    required_starting_balance: float
    recommended_position_size: float
    risk_per_trade: float
    trades_per_day: int


class DailyProfitManager:
    """Manages daily profit generation and withdrawal strategy"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.config = DailyProfitTarget()
        self.daily_status: Optional[DailyProfitStatus] = None
        self.starting_balance: float = 0.0
        self.current_profit: float = 0.0
        self.trades_made_today: int = 0
        self.risk_taken_today: float = 0.0
        self.last_reset_date: Optional[datetime] = None
    
    async def initialize_daily_target(self):
        """Initialize daily profit target"""
        try:
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            today = datetime.now().date()
            
            # Reset for new day
            if (self.last_reset_date is None or 
                self.last_reset_date.date() != today):
                
                self.starting_balance = current_balance
                self.current_profit = 0.0
                self.trades_made_today = 0
                self.risk_taken_today = 0.0
                self.last_reset_date = datetime.now()
                
                # Create daily status
                self.daily_status = DailyProfitStatus(
                    date=today,
                    target_profit=self.config.target_daily_profit,
                    current_profit=0.0,
                    remaining_target=self.config.target_daily_profit,
                    trades_made=0,
                    trades_needed=self._estimate_trades_needed(),
                    estimated_completion_time=None,
                    risk_taken=0.0,
                    max_risk_allowed=self.config.max_daily_risk
                )
                
                logger.info("Daily profit target initialized",
                           target=self.config.target_daily_profit,
                           starting_balance=current_balance)
            
        except Exception as e:
            logger.error("Failed to initialize daily target", error=str(e))
    
    def _estimate_trades_needed(self) -> int:
        """Estimate number of trades needed to reach daily target"""
        # Assume average profit per trade of $50-100
        avg_profit_per_trade = 75.0
        trades_needed = int(self.config.target_daily_profit / avg_profit_per_trade)
        return max(1, trades_needed)
    
    def calculate_required_position_size(self, signal: TradingSignal, 
                                      current_balance: float) -> Tuple[int, float]:
        """
        Calculate position size needed to generate target daily profit
        
        Args:
            signal: Trading signal
            current_balance: Current account balance
        
        Returns:
            Tuple of (position_size, expected_profit)
        """
        # Calculate remaining profit needed
        remaining_profit = self.config.target_daily_profit - self.current_profit
        
        if remaining_profit <= 0:
            return 0, 0.0
        
        # Calculate expected profit per share
        if signal.side == "yes":
            expected_profit_per_share = signal.price * signal.model_probability - signal.price
        else:
            expected_profit_per_share = signal.price * (1 - signal.model_probability) - signal.price
        
        # Ensure positive expected profit
        if expected_profit_per_share <= 0:
            return 0, 0.0
        
        # Calculate position size needed
        position_size = int(remaining_profit / expected_profit_per_share)
        
        # Apply safety limits
        max_position_by_balance = int(current_balance * 0.1 / signal.price)  # Max 10% of balance
        max_position_by_risk = int(self.config.max_daily_risk / signal.price)
        
        position_size = min(position_size, max_position_by_balance, max_position_by_risk)
        
        # Calculate expected profit
        expected_profit = position_size * expected_profit_per_share
        
        logger.info("Position size calculated for daily target",
                   ticker=signal.ticker,
                   position_size=position_size,
                   expected_profit=expected_profit,
                   remaining_target=remaining_profit)
        
        return position_size, expected_profit
    
    def create_aggressive_signal(self, signal: TradingSignal, 
                              current_balance: float) -> TradingSignal:
        """
        Create an aggressive signal optimized for daily profit target
        
        Args:
            signal: Original trading signal
            current_balance: Current account balance
        
        Returns:
            Aggressive signal with larger position size
        """
        # Calculate required position size
        position_size, expected_profit = self.calculate_required_position_size(
            signal, current_balance
        )
        
        if position_size == 0:
            return signal
        
        # Create aggressive signal
        aggressive_signal = TradingSignal(
            ticker=signal.ticker,
            side=signal.side,
            quantity=position_size,
            price=signal.price,
            model_probability=signal.model_probability,
            implied_probability=signal.implied_probability,
            probability_delta=signal.probability_delta,
            confidence=signal.confidence,
            kelly_fraction=signal.kelly_fraction,
            expected_value=expected_profit,
            timestamp=signal.timestamp,
            reason=f"{signal.reason} (Daily Target: ${expected_profit:.2f})"
        )
        
        logger.info("Aggressive signal created for daily target",
                   ticker=signal.ticker,
                   original_quantity=signal.quantity,
                   aggressive_quantity=position_size,
                   expected_profit=expected_profit)
        
        return aggressive_signal
    
    def update_daily_progress(self, trade_pnl: float):
        """Update daily progress with trade result"""
        self.current_profit += trade_pnl
        self.trades_made_today += 1
        
        if self.daily_status:
            self.daily_status.current_profit = self.current_profit
            self.daily_status.remaining_target = max(0, self.config.target_daily_profit - self.current_profit)
            self.daily_status.trades_made = self.trades_made_today
            
            # Estimate completion time
            if self.current_profit > 0:
                avg_profit_per_trade = self.current_profit / self.trades_made_today
                remaining_trades = self.daily_status.remaining_target / avg_profit_per_trade
                estimated_minutes = remaining_trades * 30  # Assume 30 min per trade
                self.daily_status.estimated_completion_time = datetime.now() + timedelta(minutes=estimated_minutes)
        
        logger.info("Daily progress updated",
                   current_profit=self.current_profit,
                   remaining_target=self.daily_status.remaining_target if self.daily_status else 0,
                   trades_made=self.trades_made_today)
    
    def is_daily_target_reached(self) -> bool:
        """Check if daily profit target has been reached"""
        return self.current_profit >= self.config.target_daily_profit
    
    def can_withdraw_profits(self) -> Tuple[bool, float]:
        """
        Check if profits can be withdrawn
        
        Returns:
            Tuple of (can_withdraw, withdrawable_amount)
        """
        if self.current_profit < self.config.minimum_withdrawable:
            return False, self.current_profit
        
        # Calculate withdrawable amount (80% of profits)
        withdrawable_amount = self.current_profit * self.config.profit_withdrawal_pct
        
        # Ensure we keep emergency reserve
        current_balance = self.starting_balance + self.current_profit
        min_balance = self.config.emergency_reserve
        max_withdrawable = current_balance - min_balance
        
        withdrawable_amount = min(withdrawable_amount, max_withdrawable)
        
        return True, withdrawable_amount
    
    def get_withdrawal_plan(self, current_balance: float) -> WithdrawalPlan:
        """Get comprehensive withdrawal plan"""
        daily_target = self.config.target_daily_profit
        weekly_target = daily_target * 7
        monthly_target = daily_target * 30
        
        # Calculate required starting balance
        # Assume 20% daily return needed for $400 profit
        required_starting_balance = daily_target / 0.20  # $2,000 minimum
        
        # Calculate recommended position size
        avg_profit_per_trade = 75.0
        trades_per_day = int(daily_target / avg_profit_per_trade)
        recommended_position_size = current_balance * 0.05  # 5% per trade
        
        # Calculate risk per trade
        risk_per_trade = self.config.max_daily_risk / trades_per_day
        
        plan = WithdrawalPlan(
            daily_target=daily_target,
            weekly_target=weekly_target,
            monthly_target=monthly_target,
            required_starting_balance=required_starting_balance,
            recommended_position_size=recommended_position_size,
            risk_per_trade=risk_per_trade,
            trades_per_day=trades_per_day
        )
        
        logger.info("Withdrawal plan created",
                   daily_target=daily_target,
                   required_balance=required_starting_balance,
                   trades_per_day=trades_per_day)
        
        return plan
    
    def get_daily_status(self) -> Dict[str, any]:
        """Get current daily status"""
        if not self.daily_status:
            return {"error": "Daily status not initialized"}
        
        can_withdraw, withdrawable_amount = self.can_withdraw_profits()
        
        return {
            "date": self.daily_status.date.isoformat(),
            "target_profit": self.daily_status.target_profit,
            "current_profit": self.daily_status.current_profit,
            "remaining_target": self.daily_status.remaining_target,
            "progress_pct": (self.daily_status.current_profit / self.daily_status.target_profit) * 100,
            "trades_made": self.daily_status.trades_made,
            "trades_needed": self.daily_status.trades_needed,
            "estimated_completion": self.daily_status.estimated_completion_time.isoformat() if self.daily_status.estimated_completion_time else None,
            "can_withdraw": can_withdraw,
            "withdrawable_amount": withdrawable_amount,
            "risk_taken": self.daily_status.risk_taken,
            "max_risk_allowed": self.daily_status.max_risk_allowed,
            "target_reached": self.is_daily_target_reached()
        }


class JobQuitStrategy:
    """Main strategy for generating daily profits to quit jobs"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.profit_manager = DailyProfitManager(client)
        self.is_active = False
    
    async def initialize(self):
        """Initialize job quit strategy"""
        await self.profit_manager.initialize_daily_target()
        self.is_active = True
        logger.info("Job quit strategy initialized - Target: $400/day")
    
    async def enhance_signal_for_daily_profit(self, signal: TradingSignal) -> TradingSignal:
        """
        Enhance signal to maximize daily profit generation
        
        Args:
            signal: Original trading signal
        
        Returns:
            Enhanced signal optimized for daily profits
        """
        try:
            # Get current balance
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            # Check if we've already reached daily target
            if self.profit_manager.is_daily_target_reached():
                logger.info("Daily target already reached, using conservative sizing")
                return signal
            
            # Create aggressive signal for daily profit
            aggressive_signal = self.profit_manager.create_aggressive_signal(
                signal, current_balance
            )
            
            return aggressive_signal
            
        except Exception as e:
            logger.error("Failed to enhance signal for daily profit", error=str(e))
            return signal
    
    async def track_profit_generation(self, signal: TradingSignal, result: ExecutionResult, pnl: float):
        """Track profit generation for daily target"""
        try:
            self.profit_manager.update_daily_progress(pnl)
            
            logger.info("Profit generation tracked",
                       ticker=signal.ticker,
                       trade_pnl=pnl,
                       daily_progress=self.profit_manager.current_profit,
                       target_reached=self.profit_manager.is_daily_target_reached())
            
        except Exception as e:
            logger.error("Failed to track profit generation", error=str(e))
    
    def get_withdrawal_status(self) -> Dict[str, any]:
        """Get withdrawal status and recommendations"""
        daily_status = self.profit_manager.get_daily_status()
        
        # Get withdrawal plan
        portfolio = asyncio.run(self.client.get_portfolio())
        current_balance = portfolio.get("total_value", 0.0)
        withdrawal_plan = self.profit_manager.get_withdrawal_plan(current_balance)
        
        return {
            "daily_status": daily_status,
            "withdrawal_plan": {
                "daily_target": withdrawal_plan.daily_target,
                "weekly_target": withdrawal_plan.weekly_target,
                "monthly_target": withdrawal_plan.monthly_target,
                "required_starting_balance": withdrawal_plan.required_starting_balance,
                "recommended_position_size": withdrawal_plan.recommended_position_size,
                "risk_per_trade": withdrawal_plan.risk_per_trade,
                "trades_per_day": withdrawal_plan.trades_per_day
            },
            "job_quit_analysis": {
                "current_daily_income": 400.0,  # Target
                "days_to_quit": 1 if daily_status["target_reached"] else "In Progress",
                "monthly_projected_income": withdrawal_plan.monthly_target,
                "annual_projected_income": withdrawal_plan.monthly_target * 12,
                "recommendation": "Ready to quit!" if daily_status["target_reached"] else "Keep trading!"
            }
        }
    
    def configure_for_job_quit(self, daily_target: float = 400.0):
        """Configure strategy for job quitting"""
        self.profit_manager.config.target_daily_profit = daily_target
        self.profit_manager.config.minimum_withdrawable = daily_target * 0.875  # 87.5% of target
        self.profit_manager.config.max_daily_risk = daily_target * 0.5  # 50% of target as max risk
        
        logger.info("Strategy configured for job quitting",
                   daily_target=daily_target,
                   minimum_withdrawable=self.profit_manager.config.minimum_withdrawable,
                   max_daily_risk=self.profit_manager.config.max_daily_risk)
