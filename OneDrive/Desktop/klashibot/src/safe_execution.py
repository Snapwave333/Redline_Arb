"""
Enhanced Cash Management for Kalshi Trading Bot

This module ensures the bot only uses available deposited funds and never
attempts to pull funds from external sources.
"""

import asyncio
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
class CashBalance:
    """Cash balance information"""
    available_cash: float
    total_cash: float
    pending_orders_value: float
    reserved_cash: float
    timestamp: datetime


@dataclass
class FundSafetyCheck:
    """Fund safety check result"""
    is_safe: bool
    available_for_trading: float
    reason: str
    warnings: List[str]


class CashManager:
    """Manages cash balance and ensures fund safety"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.cash_balance: Optional[CashBalance] = None
        self.min_cash_reserve: float = 10.0  # Always keep $10 minimum
        self.max_cash_usage_pct: float = 0.95  # Use max 95% of available cash
        self.last_balance_update: Optional[datetime] = None
        self.balance_update_interval: int = 30  # Update every 30 seconds
    
    async def update_cash_balance(self) -> CashBalance:
        """Update cash balance from Kalshi API"""
        try:
            # Get portfolio information
            portfolio = await self.client.get_portfolio()
            
            # Get pending orders to calculate reserved cash
            orders = await self.client.get_orders(status="pending")
            pending_value = sum(order.quantity * order.price for order in orders)
            
            # Calculate available cash
            total_cash = portfolio.get("cash_balance", 0.0)
            available_cash = max(0.0, total_cash - pending_value - self.min_cash_reserve)
            
            self.cash_balance = CashBalance(
                available_cash=available_cash,
                total_cash=total_cash,
                pending_orders_value=pending_value,
                reserved_cash=self.min_cash_reserve,
                timestamp=datetime.now()
            )
            
            self.last_balance_update = datetime.now()
            
            logger.info("Cash balance updated",
                       total_cash=total_cash,
                       available_cash=available_cash,
                       pending_value=pending_value)
            
            return self.cash_balance
            
        except Exception as e:
            logger.error("Failed to update cash balance", error=str(e))
            raise
    
    async def get_available_cash(self) -> float:
        """Get currently available cash for trading"""
        # Update balance if needed
        if (not self.cash_balance or 
            not self.last_balance_update or
            (datetime.now() - self.last_balance_update).seconds > self.balance_update_interval):
            await self.update_cash_balance()
        
        return self.cash_balance.available_cash if self.cash_balance else 0.0
    
    def check_fund_safety(self, required_amount: float) -> FundSafetyCheck:
        """
        Check if we can safely use the required amount
        
        Args:
            required_amount: Amount needed for the trade
        
        Returns:
            Fund safety check result
        """
        if not self.cash_balance:
            return FundSafetyCheck(
                is_safe=False,
                available_for_trading=0.0,
                reason="Cash balance not available",
                warnings=["Cannot determine available funds"]
            )
        
        warnings = []
        
        # Check if we have enough cash
        if required_amount > self.cash_balance.available_cash:
            return FundSafetyCheck(
                is_safe=False,
                available_for_trading=self.cash_balance.available_cash,
                reason=f"Insufficient funds: need ${required_amount:.2f}, have ${self.cash_balance.available_cash:.2f}",
                warnings=["Not enough cash available"]
            )
        
        # Check if we're using too much of our cash
        usage_pct = required_amount / self.cash_balance.total_cash if self.cash_balance.total_cash > 0 else 0
        if usage_pct > self.max_cash_usage_pct:
            warnings.append(f"Using {usage_pct:.1%} of total cash (limit: {self.max_cash_usage_pct:.1%})")
        
        # Check if we're getting close to minimum reserve
        remaining_after_trade = self.cash_balance.available_cash - required_amount
        if remaining_after_trade < self.min_cash_reserve * 2:
            warnings.append(f"Low cash reserve after trade: ${remaining_after_trade:.2f}")
        
        # Check if balance is stale
        if self.last_balance_update:
            age_minutes = (datetime.now() - self.last_balance_update).total_seconds() / 60
            if age_minutes > 5:  # Balance older than 5 minutes
                warnings.append(f"Cash balance is {age_minutes:.1f} minutes old")
        
        return FundSafetyCheck(
            is_safe=True,
            available_for_trading=self.cash_balance.available_cash,
            reason="Funds available",
            warnings=warnings
        )
    
    def calculate_safe_position_size(self, signal: TradingSignal) -> Tuple[int, List[str]]:
        """
        Calculate safe position size based on available cash
        
        Args:
            signal: Trading signal
        
        Returns:
            Tuple of (safe_quantity, warnings)
        """
        warnings = []
        
        # Get available cash
        available_cash = self.cash_balance.available_cash if self.cash_balance else 0.0
        
        if available_cash <= 0:
            return 0, ["No cash available"]
        
        # Calculate maximum safe quantity
        max_safe_quantity = int(available_cash / signal.price)
        
        # Apply additional safety limits
        max_quantity_by_cash_pct = int(available_cash * self.max_cash_usage_pct / signal.price)
        max_quantity_by_reserve = int((available_cash - self.min_cash_reserve) / signal.price)
        
        # Use the most conservative limit
        safe_quantity = min(max_safe_quantity, max_quantity_by_cash_pct, max_quantity_by_reserve)
        
        # Ensure we don't exceed the signal's requested quantity
        safe_quantity = min(safe_quantity, signal.quantity)
        
        # Add warnings if we're limiting the position
        if safe_quantity < signal.quantity:
            warnings.append(f"Reduced position size from {signal.quantity} to {safe_quantity} due to cash limits")
        
        if safe_quantity == 0:
            warnings.append("Cannot place trade: insufficient cash")
        
        return safe_quantity, warnings
    
    def get_cash_summary(self) -> Dict[str, any]:
        """Get comprehensive cash summary"""
        if not self.cash_balance:
            return {"error": "Cash balance not available"}
        
        return {
            "total_cash": self.cash_balance.total_cash,
            "available_cash": self.cash_balance.available_cash,
            "pending_orders_value": self.cash_balance.pending_orders_value,
            "reserved_cash": self.cash_balance.reserved_cash,
            "last_updated": self.cash_balance.timestamp,
            "min_reserve": self.min_cash_reserve,
            "max_usage_pct": self.max_cash_usage_pct
        }


class SafeExecutionManager:
    """Enhanced execution manager with strict cash management"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.cash_manager = CashManager(client)
        self.execution_queue: List[TradingSignal] = []
        self.is_running = False
    
    async def initialize(self):
        """Initialize safe execution manager"""
        await self.cash_manager.update_cash_balance()
        logger.info("Safe execution manager initialized")
    
    async def execute_signal_safely(self, signal: TradingSignal) -> ExecutionResult:
        """
        Execute a trading signal with strict cash safety checks
        
        Args:
            signal: Trading signal to execute
        
        Returns:
            Execution result with safety information
        """
        try:
            # Update cash balance first
            await self.cash_manager.update_cash_balance()
            
            # Check fund safety
            safety_check = self.cash_manager.check_fund_safety(signal.quantity * signal.price)
            
            if not safety_check.is_safe:
                logger.warning("Trade rejected due to insufficient funds",
                             ticker=signal.ticker,
                             reason=safety_check.reason,
                             available=safety_check.available_for_trading)
                
                return ExecutionResult(
                    success=False,
                    error_message=f"Fund safety check failed: {safety_check.reason}"
                )
            
            # Calculate safe position size
            safe_quantity, warnings = self.cash_manager.calculate_safe_position_size(signal)
            
            if safe_quantity == 0:
                logger.warning("Cannot place trade: no safe position size",
                             ticker=signal.ticker,
                             warnings=warnings)
                
                return ExecutionResult(
                    success=False,
                    error_message="No safe position size available"
                )
            
            # Create safe signal with adjusted quantity
            safe_signal = TradingSignal(
                ticker=signal.ticker,
                side=signal.side,
                quantity=safe_quantity,
                price=signal.price,
                model_probability=signal.model_probability,
                implied_probability=signal.implied_probability,
                probability_delta=signal.probability_delta,
                confidence=signal.confidence,
                kelly_fraction=signal.kelly_fraction,
                expected_value=signal.expected_value,
                timestamp=signal.timestamp,
                reason=f"{signal.reason} (Safe size: {safe_quantity})"
            )
            
            # Log warnings if any
            if warnings:
                logger.warning("Position size adjusted for safety",
                             ticker=signal.ticker,
                             original_quantity=signal.quantity,
                             safe_quantity=safe_quantity,
                             warnings=warnings)
            
            # Place order with safe signal
            result = await self._place_safe_order(safe_signal)
            
            if result.success:
                # Add to execution queue
                self.execution_queue.append(safe_signal)
                
                logger.info("Safe signal executed successfully",
                           ticker=safe_signal.ticker,
                           quantity=safe_signal.quantity,
                           price=safe_signal.price)
            
            return result
            
        except Exception as e:
            logger.error("Failed to execute signal safely",
                        ticker=signal.ticker,
                        error=str(e))
            
            return ExecutionResult(success=False, error_message=str(e))
    
    async def _place_safe_order(self, signal: TradingSignal) -> ExecutionResult:
        """Place order with additional safety checks"""
        try:
            # Final cash check before placing order
            available_cash = await self.cash_manager.get_available_cash()
            required_cash = signal.quantity * signal.price
            
            if required_cash > available_cash:
                return ExecutionResult(
                    success=False,
                    error_message=f"Cash check failed: need ${required_cash:.2f}, have ${available_cash:.2f}"
                )
            
            # Place order via API
            kalshi_order = await self.client.create_order(
                ticker=signal.ticker,
                side=signal.side,
                quantity=signal.quantity,
                price=signal.price,
                order_type="limit"
            )
            
            logger.info("Safe order placed",
                       order_id=kalshi_order.order_id,
                       ticker=signal.ticker,
                       quantity=signal.quantity,
                       price=signal.price)
            
            return ExecutionResult(
                success=True,
                order_id=kalshi_order.order_id,
                filled_quantity=0,  # Will be updated when filled
                average_price=signal.price,
                total_cost=required_cash,
                execution_time=datetime.now()
            )
            
        except Exception as e:
            logger.error("Failed to place safe order",
                        ticker=signal.ticker,
                        error=str(e))
            
            return ExecutionResult(success=False, error_message=str(e))
    
    async def monitor_cash_safety(self):
        """Monitor cash safety continuously"""
        while self.is_running:
            try:
                await self.cash_manager.update_cash_balance()
                
                # Log cash status
                cash_summary = self.cash_manager.get_cash_summary()
                logger.info("Cash safety check",
                           available_cash=cash_summary["available_cash"],
                           total_cash=cash_summary["total_cash"])
                
                # Check for low cash warnings
                if cash_summary["available_cash"] < self.cash_manager.min_cash_reserve * 2:
                    logger.warning("Low cash warning",
                                 available_cash=cash_summary["available_cash"],
                                 min_reserve=self.cash_manager.min_cash_reserve)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Error in cash safety monitoring", error=str(e))
                await asyncio.sleep(60)
    
    async def start_monitoring(self):
        """Start cash safety monitoring"""
        self.is_running = True
        asyncio.create_task(self.monitor_cash_safety())
        logger.info("Cash safety monitoring started")
    
    async def stop_monitoring(self):
        """Stop cash safety monitoring"""
        self.is_running = False
        logger.info("Cash safety monitoring stopped")
    
    def get_execution_summary(self) -> Dict[str, any]:
        """Get execution summary with cash information"""
        cash_summary = self.cash_manager.get_cash_summary()
        
        return {
            "cash_summary": cash_summary,
            "execution_queue": len(self.execution_queue),
            "monitoring_active": self.is_running,
            "safety_features": {
                "min_cash_reserve": self.cash_manager.min_cash_reserve,
                "max_cash_usage_pct": self.cash_manager.max_cash_usage_pct,
                "balance_update_interval": self.cash_manager.balance_update_interval
            }
        }
