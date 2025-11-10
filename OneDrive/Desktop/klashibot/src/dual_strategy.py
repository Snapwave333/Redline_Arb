"""
Dual Strategy: Daily Income + Exponential Compounding

This module implements a sophisticated dual strategy that:
1. Generates $400 daily withdrawable income for job quitting
2. Simultaneously compounds the remaining bankroll exponentially
3. Almost doubles the bankroll every day through reinvestment
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
from .ach_transfer_manager import ACHTransferManager

logger = structlog.get_logger(__name__)


@dataclass
class DualStrategyConfig:
    """Configuration for dual income + compounding strategy"""
    # Daily Income Settings
    daily_income_target: float = 400.0  # $400 daily income
    daily_withdrawal_pct: float = 0.8   # Withdraw 80% of daily profits
    
    # Compounding Settings
    compounding_enabled: bool = True
    daily_compounding_target: float = 0.5  # Target 50% daily growth
    reinvestment_pct: float = 0.9  # Reinvest 90% of remaining profits
    
    # Safety Settings
    emergency_reserve: float = 2000.0  # Keep $2000 emergency reserve
    max_daily_risk: float = 1000.0  # Max $1000 daily risk
    min_balance_for_compounding: float = 5000.0  # Need $5k to start compounding


@dataclass
class DailyDualStatus:
    """Daily status for dual strategy"""
    date: datetime
    starting_balance: float
    daily_income_generated: float
    compounding_growth: float
    total_daily_profit: float
    withdrawable_amount: float
    reinvested_amount: float
    ending_balance: float
    growth_rate: float
    income_target_reached: bool
    compounding_target_reached: bool


@dataclass
class CompoundingProjection:
    """Compounding growth projection"""
    current_balance: float
    daily_income: float
    daily_compounding_rate: float
    projected_balance_7_days: float
    projected_balance_30_days: float
    projected_balance_90_days: float
    days_to_double: float
    monthly_income_potential: float


class DualStrategyEngine:
    """Engine for dual income + compounding strategy"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.config = DualStrategyConfig()
        self.daily_status: Optional[DailyDualStatus] = None
        self.starting_balance: float = 0.0
        self.daily_income: float = 0.0
        self.compounding_growth: float = 0.0
        self.trades_made_today: int = 0
        self.last_reset_date: Optional[datetime] = None
    
    async def initialize_daily_dual_strategy(self):
        """Initialize daily dual strategy"""
        try:
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            today = datetime.now().date()
            
            # Reset for new day
            if (self.last_reset_date is None or 
                self.last_reset_date.date() != today):
                
                self.starting_balance = current_balance
                self.daily_income = 0.0
                self.compounding_growth = 0.0
                self.trades_made_today = 0
                self.last_reset_date = datetime.now()
                
                # Create daily status
                self.daily_status = DailyDualStatus(
                    date=today,
                    starting_balance=current_balance,
                    daily_income_generated=0.0,
                    compounding_growth=0.0,
                    total_daily_profit=0.0,
                    withdrawable_amount=0.0,
                    reinvested_amount=0.0,
                    ending_balance=current_balance,
                    growth_rate=0.0,
                    income_target_reached=False,
                    compounding_target_reached=False
                )
                
                logger.info("Dual strategy initialized",
                           starting_balance=current_balance,
                           income_target=self.config.daily_income_target,
                           compounding_target=self.config.daily_compounding_target)
            
        except Exception as e:
            logger.error("Failed to initialize dual strategy", error=str(e))
    
    def calculate_dual_position_sizing(self, signal: TradingSignal, 
                                    current_balance: float) -> Tuple[int, float, float]:
        """
        Calculate position size for dual strategy
        
        Args:
            signal: Trading signal
            current_balance: Current account balance
        
        Returns:
            Tuple of (position_size, expected_income, expected_compounding)
        """
        # Calculate remaining income needed
        remaining_income = max(0, self.config.daily_income_target - self.daily_income)
        
        # Calculate expected profit per share
        if signal.side == "yes":
            expected_profit_per_share = signal.price * signal.model_probability - signal.price
        else:
            expected_profit_per_share = signal.price * (1 - signal.model_probability) - signal.price
        
        if expected_profit_per_share <= 0:
            return 0, 0.0, 0.0
        
        # Calculate position size for income generation
        if remaining_income > 0:
            income_position_size = int(remaining_income / expected_profit_per_share)
        else:
            income_position_size = 0
        
        # Calculate position size for compounding
        compounding_position_size = 0
        if (self.config.compounding_enabled and 
            current_balance >= self.config.min_balance_for_compounding):
            
            # Calculate compounding target
            compounding_target = current_balance * self.config.daily_compounding_target
            compounding_position_size = int(compounding_target / expected_profit_per_share)
        
        # Total position size
        total_position_size = income_position_size + compounding_position_size
        
        # Apply safety limits
        max_position_by_balance = int(current_balance * 0.2 / signal.price)  # Max 20% of balance
        max_position_by_risk = int(self.config.max_daily_risk / signal.price)
        
        total_position_size = min(total_position_size, max_position_by_balance, max_position_by_risk)
        
        # Calculate expected profits
        expected_income = min(income_position_size, total_position_size) * expected_profit_per_share
        expected_compounding = max(0, total_position_size - income_position_size) * expected_profit_per_share
        
        logger.info("Dual position sizing calculated",
                   ticker=signal.ticker,
                   total_size=total_position_size,
                   income_size=income_position_size,
                   compounding_size=compounding_position_size,
                   expected_income=expected_income,
                   expected_compounding=expected_compounding)
        
        return total_position_size, expected_income, expected_compounding
    
    def create_dual_enhanced_signal(self, signal: TradingSignal, 
                                 current_balance: float) -> TradingSignal:
        """
        Create signal enhanced for dual strategy
        
        Args:
            signal: Original trading signal
            current_balance: Current account balance
        
        Returns:
            Enhanced signal for dual strategy
        """
        # Calculate dual position sizing
        position_size, expected_income, expected_compounding = self.calculate_dual_position_sizing(
            signal, current_balance
        )
        
        if position_size == 0:
            return signal
        
        # Calculate total expected profit
        total_expected_profit = expected_income + expected_compounding
        
        # Create enhanced signal
        enhanced_signal = TradingSignal(
            ticker=signal.ticker,
            side=signal.side,
            quantity=position_size,
            price=signal.price,
            model_probability=signal.model_probability,
            implied_probability=signal.implied_probability,
            probability_delta=signal.probability_delta,
            confidence=signal.confidence,
            kelly_fraction=signal.kelly_fraction,
            expected_value=total_expected_profit,
            timestamp=signal.timestamp,
            reason=f"{signal.reason} (Dual: Income=${expected_income:.2f}, Compound=${expected_compounding:.2f})"
        )
        
        logger.info("Dual enhanced signal created",
                   ticker=signal.ticker,
                   original_quantity=signal.quantity,
                   enhanced_quantity=position_size,
                   expected_income=expected_income,
                   expected_compounding=expected_compounding)
        
        return enhanced_signal
    
    def update_dual_progress(self, trade_pnl: float):
        """Update dual strategy progress"""
        # Allocate profit between income and compounding
        if self.daily_income < self.config.daily_income_target:
            # First, fill income target
            remaining_income_needed = self.config.daily_income_target - self.daily_income
            income_allocation = min(trade_pnl, remaining_income_needed)
            compounding_allocation = max(0, trade_pnl - income_allocation)
        else:
            # Income target reached, allocate to compounding
            income_allocation = 0
            compounding_allocation = trade_pnl
        
        # Update totals
        self.daily_income += income_allocation
        self.compounding_growth += compounding_allocation
        self.trades_made_today += 1
        
        # Update daily status
        if self.daily_status:
            self.daily_status.daily_income_generated = self.daily_income
            self.daily_status.compounding_growth = self.compounding_growth
            self.daily_status.total_daily_profit = self.daily_income + self.compounding_growth
            
            # Calculate withdrawable amount
            self.daily_status.withdrawable_amount = self.daily_income * self.config.daily_withdrawal_pct
            
            # Calculate reinvested amount
            self.daily_status.reinvested_amount = self.compounding_growth * self.config.reinvestment_pct
            
            # Update ending balance
            self.daily_status.ending_balance = self.starting_balance + self.daily_status.total_daily_profit
            
            # Calculate growth rate
            self.daily_status.growth_rate = self.daily_status.total_daily_profit / self.starting_balance
            
            # Check if targets are reached
            self.daily_status.income_target_reached = self.daily_income >= self.config.daily_income_target
            self.daily_status.compounding_target_reached = (
                self.compounding_growth >= self.starting_balance * self.config.daily_compounding_target
            )
        
        logger.info("Dual progress updated",
                   trade_pnl=trade_pnl,
                   income_allocation=income_allocation,
                   compounding_allocation=compounding_allocation,
                   daily_income=self.daily_income,
                   compounding_growth=self.compounding_growth,
                   income_target_reached=self.daily_status.income_target_reached if self.daily_status else False)
    
    def get_compounding_projection(self, current_balance: float) -> CompoundingProjection:
        """Get compounding growth projection"""
        daily_income = self.config.daily_income_target
        daily_compounding_rate = self.config.daily_compounding_target
        
        # Calculate projected balances
        projected_7_days = current_balance * ((1 + daily_compounding_rate) ** 7)
        projected_30_days = current_balance * ((1 + daily_compounding_rate) ** 30)
        projected_90_days = current_balance * ((1 + daily_compounding_rate) ** 90)
        
        # Calculate days to double
        days_to_double = np.log(2) / np.log(1 + daily_compounding_rate)
        
        # Calculate monthly income potential
        monthly_income_potential = daily_income * 30
        
        projection = CompoundingProjection(
            current_balance=current_balance,
            daily_income=daily_income,
            daily_compounding_rate=daily_compounding_rate,
            projected_balance_7_days=projected_7_days,
            projected_balance_30_days=projected_30_days,
            projected_balance_90_days=projected_90_days,
            days_to_double=days_to_double,
            monthly_income_potential=monthly_income_potential
        )
        
        logger.info("Compounding projection calculated",
                   current_balance=current_balance,
                   days_to_double=days_to_double,
                   projected_30_days=projected_30_days)
        
        return projection
    
    def get_dual_status(self) -> Dict[str, any]:
        """Get comprehensive dual strategy status"""
        if not self.daily_status:
            return {"error": "Dual status not initialized"}
        
        # Get compounding projection
        portfolio = asyncio.run(self.client.get_portfolio())
        current_balance = portfolio.get("total_value", 0.0)
        projection = self.get_compounding_projection(current_balance)
        
        return {
            "daily_status": {
                "date": self.daily_status.date.isoformat(),
                "starting_balance": self.daily_status.starting_balance,
                "daily_income_generated": self.daily_status.daily_income_generated,
                "compounding_growth": self.daily_status.compounding_growth,
                "total_daily_profit": self.daily_status.total_daily_profit,
                "withdrawable_amount": self.daily_status.withdrawable_amount,
                "reinvested_amount": self.daily_status.reinvested_amount,
                "ending_balance": self.daily_status.ending_balance,
                "growth_rate": self.daily_status.growth_rate,
                "income_target_reached": self.daily_status.income_target_reached,
                "compounding_target_reached": self.daily_status.compounding_target_reached
            },
            "compounding_projection": {
                "current_balance": projection.current_balance,
                "daily_income": projection.daily_income,
                "daily_compounding_rate": projection.daily_compounding_rate,
                "projected_7_days": projection.projected_balance_7_days,
                "projected_30_days": projection.projected_balance_30_days,
                "projected_90_days": projection.projected_balance_90_days,
                "days_to_double": projection.days_to_double,
                "monthly_income_potential": projection.monthly_income_potential
            },
            "strategy_summary": {
                "income_target": self.config.daily_income_target,
                "compounding_target": self.config.daily_compounding_target,
                "reinvestment_pct": self.config.reinvestment_pct,
                "emergency_reserve": self.config.emergency_reserve,
                "max_daily_risk": self.config.max_daily_risk,
                "trades_made_today": self.trades_made_today
            }
        }


class DualIncomeCompoundingManager:
    """Main manager for dual income + compounding strategy"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.dual_engine = DualStrategyEngine(client)
        self.paypal_manager = ACHTransferManager()  # ACH replaces PayPal
        self.is_active = False
    
    async def initialize(self):
        """Initialize dual strategy manager"""
        await self.dual_engine.initialize_daily_dual_strategy()
        await self.paypal_manager.initialize()
        self.is_active = True
        logger.info("Dual income + compounding manager initialized with ACH integration")
    
    async def enhance_signal_for_dual_strategy(self, signal: TradingSignal) -> TradingSignal:
        """
        Enhance signal for dual income + compounding strategy
        
        Args:
            signal: Original trading signal
        
        Returns:
            Enhanced signal for dual strategy
        """
        try:
            # Get current balance
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            # Enhance signal for dual strategy
            enhanced_signal = self.dual_engine.create_dual_enhanced_signal(
                signal, current_balance
            )
            
            return enhanced_signal
            
        except Exception as e:
            logger.error("Failed to enhance signal for dual strategy", error=str(e))
            return signal
    
    async def process_daily_paypal_transfer(self):
        """
        Process daily $400 PayPal transfer
        
        This method checks if we have generated enough income and automatically
        transfers $400 to PayPal at the configured time.
        """
        try:
            # Get current daily status
            daily_status = self.dual_engine.get_daily_dual_status()
            
            if not daily_status:
                logger.warning("No daily status available for PayPal transfer")
                return
            
            # Check if we have enough withdrawable amount for $400 transfer
            if daily_status.withdrawable_amount >= 400.0:
                logger.info("Initiating daily $400 PayPal transfer",
                           withdrawable_amount=daily_status.withdrawable_amount)
                
                # Execute the transfer
                transfer_result = await self.paypal_manager.transfer_daily_income(
                    daily_status.withdrawable_amount
                )
                
                if transfer_result.success:
                    logger.info("Daily $400 PayPal transfer successful",
                               transfer_id=transfer_result.transfer_id,
                               amount=transfer_result.amount,
                               fees=transfer_result.fees)
                else:
                    logger.error("Daily $400 PayPal transfer failed",
                                error=transfer_result.error_message)
            else:
                logger.info("Insufficient withdrawable amount for $400 transfer",
                           withdrawable_amount=daily_status.withdrawable_amount,
                           required=400.0)
                
        except Exception as e:
            logger.error("Failed to process daily PayPal transfer", error=str(e))
    
    async def schedule_automatic_transfers(self):
        """
        Schedule automatic $400 PayPal transfers
        
        This method should be called periodically to check if it's time
        for the daily transfer and execute it automatically.
        """
        try:
            # Get current daily status
            daily_status = self.dual_engine.get_daily_dual_status()
            
            if not daily_status:
                return
            
            # Schedule the transfer using PayPal manager
            await self.paypal_manager.schedule_daily_transfer(
                daily_status.withdrawable_amount
            )
            
        except Exception as e:
            logger.error("Failed to schedule automatic transfers", error=str(e))
    
    async def track_dual_execution(self, signal: TradingSignal, result: ExecutionResult, pnl: float):
        """Track execution for dual strategy"""
        try:
            self.dual_engine.update_dual_progress(pnl)
            
            logger.info("Dual execution tracked",
                       ticker=signal.ticker,
                       trade_pnl=pnl,
                       daily_income=self.dual_engine.daily_income,
                       compounding_growth=self.dual_engine.compounding_growth)
            
        except Exception as e:
            logger.error("Failed to track dual execution", error=str(e))
    
    def get_dual_summary(self) -> Dict[str, any]:
        """Get comprehensive dual strategy summary including PayPal transfers"""
        summary = self.dual_engine.get_dual_status()
        
        # Add PayPal transfer summary
        summary["paypal_transfer_summary"] = self.paypal_manager.get_transfer_summary()
        
        return summary
    
    def configure_dual_strategy(self, **kwargs):
        """Configure dual strategy parameters"""
        for key, value in kwargs.items():
            if hasattr(self.dual_engine.config, key):
                setattr(self.dual_engine.config, key, value)
                logger.info("Dual strategy configured", key=key, value=value)
