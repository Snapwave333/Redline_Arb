"""
Realistic Growth Strategy for $20 Starting Balance

This module implements a phased growth strategy that starts with $20 and gradually
builds up to the $400 daily income goal through conservative, sustainable trading.

Also includes DailyCapitalManager for enforcing daily $400 transfer rules.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, time
from dataclasses import dataclass
from enum import Enum
import structlog

from .config import config
from .kalshi_client import KalshiAPIClient, Position
from .strategy import TradingSignal
from .execution import ExecutionResult
from .firebase_manager import FirebaseManager
from .paypal_manager import PayPalTransferManager

logger = structlog.get_logger(__name__)


class GrowthPhase(Enum):
    """Growth phases for realistic progression"""
    MICRO_START = "micro_start"          # $20-$50: Ultra-conservative
    SMALL_SCALE = "small_scale"          # $50-$200: Small positions
    MEDIUM_SCALE = "medium_scale"        # $200-$1000: Medium positions
    LARGE_SCALE = "large_scale"         # $1000-$5000: Large positions
    TARGET_SCALE = "target_scale"        # $5000+: Full $400 daily income


@dataclass
class PhaseConfig:
    """Configuration for each growth phase"""
    min_balance: float
    max_balance: float
    max_position_size: int
    kelly_fraction: float
    daily_income_target: float
    compounding_rate: float
    max_daily_risk: float
    description: str


@dataclass
class GrowthStatus:
    """Current growth status"""
    current_phase: GrowthPhase
    current_balance: float
    phase_progress: float  # 0.0 to 1.0
    days_in_phase: int
    total_days: int
    projected_days_to_target: int
    daily_income_generated: float
    compounding_growth: float
    next_phase_threshold: float


class RealisticGrowthManager:
    """
    Manages realistic growth from $20 to $400 daily income
    """
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.current_phase = GrowthPhase.MICRO_START
        self.start_date = datetime.now()
        self.daily_income = 0.0
        self.compounding_growth = 0.0
        self.trades_made_today = 0
        
        # Define growth phases
        self.phases = {
            GrowthPhase.MICRO_START: PhaseConfig(
                min_balance=20.0,
                max_balance=50.0,
                max_position_size=2,
                kelly_fraction=0.02,
                daily_income_target=1.0,
                compounding_rate=0.05,
                max_daily_risk=0.5,
                description="Ultra-conservative micro-trading"
            ),
            GrowthPhase.SMALL_SCALE: PhaseConfig(
                min_balance=50.0,
                max_balance=200.0,
                max_position_size=5,
                kelly_fraction=0.03,
                daily_income_target=5.0,
                compounding_rate=0.08,
                max_daily_risk=1.0,
                description="Small-scale conservative trading"
            ),
            GrowthPhase.MEDIUM_SCALE: PhaseConfig(
                min_balance=200.0,
                max_balance=1000.0,
                max_position_size=20,
                kelly_fraction=0.05,
                daily_income_target=25.0,
                compounding_rate=0.10,
                max_daily_risk=5.0,
                description="Medium-scale strategic trading"
            ),
            GrowthPhase.LARGE_SCALE: PhaseConfig(
                min_balance=1000.0,
                max_balance=5000.0,
                max_position_size=100,
                kelly_fraction=0.08,
                daily_income_target=100.0,
                compounding_rate=0.15,
                max_daily_risk=20.0,
                description="Large-scale aggressive trading"
            ),
            GrowthPhase.TARGET_SCALE: PhaseConfig(
                min_balance=5000.0,
                max_balance=float('inf'),
                max_position_size=500,
                kelly_fraction=0.10,
                daily_income_target=400.0,
                compounding_rate=0.20,
                max_daily_risk=100.0,
                description="Full-scale $400 daily income"
            )
        }
    
    async def initialize(self):
        """Initialize the growth manager"""
        try:
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 20.0)
            
            # Determine current phase based on balance
            self.current_phase = self._determine_phase(current_balance)
            
            logger.info("Realistic growth manager initialized",
                       starting_balance=current_balance,
                       current_phase=self.current_phase.value)
            
        except Exception as e:
            logger.error("Failed to initialize growth manager", error=str(e))
            raise
    
    def _determine_phase(self, balance: float) -> GrowthPhase:
        """Determine current growth phase based on balance"""
        for phase in GrowthPhase:
            phase_config = self.phases[phase]
            if phase_config.min_balance <= balance < phase_config.max_balance:
                return phase
        
        # If balance exceeds all phases, we're in target scale
        return GrowthPhase.TARGET_SCALE
    
    def get_current_phase_config(self) -> PhaseConfig:
        """Get configuration for current phase"""
        return self.phases[self.current_phase]
    
    def enhance_signal_for_growth_phase(self, signal: TradingSignal) -> TradingSignal:
        """
        Enhance signal based on current growth phase
        
        Args:
            signal: Original trading signal
            
        Returns:
            Enhanced signal optimized for current phase
        """
        try:
            phase_config = self.get_current_phase_config()
            
            # Adjust position size based on phase
            max_position = min(signal.quantity, phase_config.max_position_size)
            
            # Adjust Kelly fraction for phase
            adjusted_kelly = phase_config.kelly_fraction
            
            # Create enhanced signal
            enhanced_signal = TradingSignal(
                ticker=signal.ticker,
                action=signal.action,
                quantity=max_position,
                price=signal.price,
                confidence=signal.confidence,
                probability_delta=signal.probability_delta,
                kelly_fraction=adjusted_kelly,
                expected_return=signal.expected_return,
                risk_score=signal.risk_score,
                metadata={
                    **signal.metadata,
                    "growth_phase": self.current_phase.value,
                    "phase_max_position": phase_config.max_position_size,
                    "phase_kelly_fraction": phase_config.kelly_fraction,
                    "phase_description": phase_config.description
                }
            )
            
            logger.info("Signal enhanced for growth phase",
                       ticker=signal.ticker,
                       phase=self.current_phase.value,
                       original_quantity=signal.quantity,
                       enhanced_quantity=max_position,
                       kelly_fraction=adjusted_kelly)
            
            return enhanced_signal
            
        except Exception as e:
            logger.error("Failed to enhance signal for growth phase", error=str(e))
            return signal
    
    async def track_growth_progress(self, signal: TradingSignal, result: ExecutionResult, pnl: float):
        """Track progress through growth phases"""
        try:
            # Update daily metrics
            self.trades_made_today += 1
            
            if pnl > 0:
                self.daily_income += pnl * 0.8  # 80% to income
                self.compounding_growth += pnl * 0.2  # 20% to compounding
            
            # Check if we should advance to next phase
            await self._check_phase_advancement()
            
            logger.info("Growth progress tracked",
                       ticker=signal.ticker,
                       pnl=pnl,
                       daily_income=self.daily_income,
                       compounding_growth=self.compounding_growth,
                       current_phase=self.current_phase.value)
            
        except Exception as e:
            logger.error("Failed to track growth progress", error=str(e))
    
    async def _check_phase_advancement(self):
        """Check if we should advance to the next growth phase"""
        try:
            portfolio = await self.client.get_portfolio()
            current_balance = portfolio.get("total_value", 0.0)
            
            # Determine if we should advance phase
            new_phase = self._determine_phase(current_balance)
            
            if new_phase != self.current_phase:
                old_phase = self.current_phase
                self.current_phase = new_phase
                
                logger.info("Growth phase advanced",
                           old_phase=old_phase.value,
                           new_phase=new_phase.value,
                           current_balance=current_balance)
                
                # Reset daily metrics for new phase
                self.daily_income = 0.0
                self.compounding_growth = 0.0
                self.trades_made_today = 0
                
        except Exception as e:
            logger.error("Failed to check phase advancement", error=str(e))
    
    def get_growth_status(self) -> GrowthStatus:
        """Get current growth status"""
        try:
            # Calculate phase progress
            phase_config = self.get_current_phase_config()
            phase_range = phase_config.max_balance - phase_config.min_balance
            current_progress = (self.current_balance - phase_config.min_balance) / phase_range
            current_progress = max(0.0, min(1.0, current_progress))
            
            # Calculate days in current phase
            days_in_phase = (datetime.now() - self.start_date).days
            
            # Calculate projected days to target
            if self.current_phase == GrowthPhase.TARGET_SCALE:
                projected_days = 0
            else:
                # Estimate based on current compounding rate
                target_balance = 5000.0  # Balance needed for $400 daily income
                current_balance = self.current_balance
                daily_growth_rate = phase_config.compounding_rate
                
                if daily_growth_rate > 0:
                    projected_days = int(np.log(target_balance / current_balance) / np.log(1 + daily_growth_rate))
                else:
                    projected_days = 365  # Conservative estimate
            
            return GrowthStatus(
                current_phase=self.current_phase,
                current_balance=self.current_balance,
                phase_progress=current_progress,
                days_in_phase=days_in_phase,
                total_days=(datetime.now() - self.start_date).days,
                projected_days_to_target=projected_days,
                daily_income_generated=self.daily_income,
                compounding_growth=self.compounding_growth,
                next_phase_threshold=phase_config.max_balance
            )
            
        except Exception as e:
            logger.error("Failed to get growth status", error=str(e))
            return GrowthStatus(
                current_phase=self.current_phase,
                current_balance=20.0,
                phase_progress=0.0,
                days_in_phase=0,
                total_days=0,
                projected_days_to_target=365,
                daily_income_generated=0.0,
                compounding_growth=0.0,
                next_phase_threshold=50.0
            )
    
    def get_growth_summary(self) -> Dict[str, any]:
        """Get comprehensive growth summary"""
        try:
            status = self.get_growth_status()
            phase_config = self.get_current_phase_config()
            
            return {
                "growth_status": {
                    "current_phase": status.current_phase.value,
                    "current_balance": status.current_balance,
                    "phase_progress": f"{status.phase_progress:.1%}",
                    "days_in_phase": status.days_in_phase,
                    "total_days": status.total_days,
                    "projected_days_to_target": status.projected_days_to_target,
                    "daily_income_generated": status.daily_income_generated,
                    "compounding_growth": status.compounding_growth,
                    "next_phase_threshold": status.next_phase_threshold
                },
                "phase_config": {
                    "description": phase_config.description,
                    "max_position_size": phase_config.max_position_size,
                    "kelly_fraction": phase_config.kelly_fraction,
                    "daily_income_target": phase_config.daily_income_target,
                    "compounding_rate": f"{phase_config.compounding_rate:.1%}",
                    "max_daily_risk": phase_config.max_daily_risk
                },
                "growth_phases": {
                    phase.value: {
                        "min_balance": config.min_balance,
                        "max_balance": config.max_balance,
                        "description": config.description
                    }
                    for phase, config in self.phases.items()
                },
                "realistic_timeline": {
                    "micro_start": "Days 1-30: $20-$50 (Ultra-conservative)",
                    "small_scale": "Days 31-90: $50-$200 (Small positions)",
                    "medium_scale": "Days 91-180: $200-$1000 (Medium positions)",
                    "large_scale": "Days 181-365: $1000-$5000 (Large positions)",
                    "target_scale": "Days 366+: $5000+ ($400 daily income)"
                }
            }
            
        except Exception as e:
            logger.error("Failed to get growth summary", error=str(e))
            return {"error": str(e)}
    
    def configure_growth_strategy(self, **kwargs):
        """Configure growth strategy parameters"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    logger.info("Growth strategy configured", key=key, value=value)
                    
        except Exception as e:
            logger.error("Failed to configure growth strategy", error=str(e))
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Realistic growth manager cleanup completed")


class DailyCapitalManager:
    """
    Manages daily profit allocation based on the user's three rules:
    1. Priority deposit of $400 USD for cost of living.
    2. Retention of profits above the $400 target for bankroll growth.
    3. Compound trading bankroll growth.
    
    Profit is tracked via (Realized P&L) and calculated daily at Midnight UTC.
    """

    def __init__(self, client: KalshiAPIClient):
        """Initialize the capital manager"""
        self.client = client
        self.firebase_manager = FirebaseManager(
            app_id=config.firebase.firebase_app_id,
            user_id=config.firebase.firebase_user_id,
            region=config.firebase.firebase_region
        )
        self.firebase_manager.initialize(
            config.firebase.firebase_credentials_path,
            config.firebase.firebase_database_id
        )
        
        # Initialize ACH manager (replaces PayPal)
        from src.ach_transfer_manager import ACHTransferManager
        self.paypal_manager = ACHTransferManager()  # Keep variable name for compatibility
        
        # In-memory tracking for realized P&L *since* the last benchmark reset
        # This value should be updated every time a position is closed.
        self._realized_profit_accumulator: float = 0.0
        
        # Load the start-of-day reference for profit calculation
        self.bankroll_benchmark: float = self.firebase_manager.get_bankroll_benchmark()
        if self.bankroll_benchmark == 0.0:
            logger.warning("Bankroll benchmark is 0.0. Ensure initial value is set.")
            
        logger.info("DailyCapitalManager initialized", 
                    bankroll_benchmark=self.bankroll_benchmark,
                    daily_deposit_target=config.paypal.daily_deposit_target)

    async def initialize(self):
        """Initialize async components"""
        await self.paypal_manager.initialize()

    def update_realized_profit(self, pnl_from_closed_position: float):
        """
        Rule 1 & 3: Updates the running total of profit made today. 
        This is called by the main trading loop on every closed position.
        """
        self._realized_profit_accumulator += pnl_from_closed_position
        logger.debug("Realized P&L updated", 
                     pnl_from_closed_position=pnl_from_closed_position,
                     total_daily_realized_pnl=self._realized_profit_accumulator)
        
    async def get_current_available_cash(self) -> float:
        """
        Retrieves the available cash balance from Kalshi (in dollars).
        NOTE: Simplified access to Kalshi SDK.
        """
        try:
            # We use get_portfolio which returns portfolio data
            portfolio = await self.client.get_portfolio()
            # Assuming the portfolio response has a 'balance' attribute (in cents)
            available_cash = portfolio.get('balance', 0) / 100.0  # Convert cents to dollars
            return available_cash
        except Exception as e:
            logger.error("Failed to retrieve Kalshi balance", error=str(e))
            return 0.0

    def calculate_transfer_and_bankroll(self) -> Tuple[float, float]:
        """
        Determines the amount to transfer and the resulting retained bankroll.

        Returns:
            (transfer_amount, retained_profit_for_bankroll)
        """
        
        daily_profit = self._realized_profit_accumulator
        target = config.paypal.daily_deposit_target
        transfer_amount = 0.0
        retained_profit = 0.0
        
        if daily_profit >= target:
            # Rule 1 & 2: Deposit $400, retain the rest
            transfer_amount = target
            retained_profit = daily_profit - target
            
        elif daily_profit > 0:
            # Rule 1 (Insufficient Profit Handling): Transfer whatever profit was made
            transfer_amount = daily_profit
            retained_profit = 0.0
        
        # Rule 3: The retained_profit implicitly grows the bankroll, 
        # as it remains in the account and the next day's benchmark will be set higher.
        
        logger.info("Transfer calculation completed",
                    daily_profit=daily_profit,
                    transfer_amount=transfer_amount,
                    retained_profit=retained_profit,
                    target=target)
        
        return transfer_amount, retained_profit
        
    async def manage_daily_cycle(self):
        """
        Executes the daily transfer and updates the new bankroll benchmark at Midnight UTC.
        """
        
        transfer_amount, retained_profit = self.calculate_transfer_and_bankroll()
        current_available_cash = await self.get_current_available_cash()

        if transfer_amount > 0:
            if current_available_cash >= transfer_amount:
                logger.info("Attempting PayPal transfer", 
                            transfer_amount=transfer_amount, 
                            retained_profit=retained_profit,
                            available_cash=current_available_cash)
                
                # Execute the PayPal transfer
                result = await self.paypal_manager.transfer_daily_income(transfer_amount)
                
                if result.success:
                    # The new bankroll benchmark is the current benchmark + retained profit
                    # (since the transfer_amount has been removed from the account)
                    new_bankroll_benchmark = self.bankroll_benchmark + retained_profit
                    
                    self.firebase_manager.set_bankroll_benchmark(
                        new_bankroll_benchmark, transfer_amount
                    )
                    self.bankroll_benchmark = new_bankroll_benchmark
                    self._realized_profit_accumulator = 0.0  # Reset P&L counter
                    
                    logger.info("Daily cycle complete", 
                                new_trading_capital_benchmark=new_bankroll_benchmark,
                                transfer_amount=transfer_amount,
                                retained_profit=retained_profit)
                else:
                    logger.error("PayPal transfer failed", 
                                 error=result.error_message,
                                 transfer_amount=transfer_amount)
                    # If the transfer fails, we do NOT reset the P&L accumulator 
                    # and do NOT update the benchmark. The bot will try again tomorrow.
            else:
                logger.error("Insufficient available cash for transfer", 
                             available_cash=current_available_cash, 
                             required_transfer=transfer_amount)
                
        else:
            logger.info("No transfer required", 
                        daily_profit=self._realized_profit_accumulator)

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("DailyCapitalManager cleanup completed")
