"""
Execution Manager for Kalshi Trading Bot

This module handles order placement, execution, and position management,
including smart order routing and slippage minimization.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import structlog
import aiohttp

from .config import config
from .kalshi_client import KalshiAPIClient, Order, Position, MarketData
from .strategy import TradingSignal

logger = structlog.get_logger(__name__)


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class ExecutionOrder:
    """Execution order structure"""
    order_id: str
    ticker: str
    side: str
    quantity: int
    price: float
    order_type: OrderType
    status: OrderStatus
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    created_at: datetime = None
    updated_at: datetime = None
    signal: Optional[TradingSignal] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class ExecutionResult:
    """Execution result structure"""
    success: bool
    order_id: Optional[str] = None
    filled_quantity: int = 0
    average_price: float = 0.0
    total_cost: float = 0.0
    error_message: Optional[str] = None
    execution_time: Optional[datetime] = None


class OrderManager:
    """Manages order lifecycle and execution"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.active_orders: Dict[str, ExecutionOrder] = {}
        self.order_history: List[ExecutionOrder] = []
        self.position_tracker: Dict[str, Position] = {}
    
    async def place_order(self, signal: TradingSignal, 
                         order_type: OrderType = OrderType.LIMIT) -> ExecutionResult:
        """
        Place an order based on trading signal
        
        Args:
            signal: Trading signal
            order_type: Type of order to place
        
        Returns:
            Execution result
        """
        try:
            # Calculate optimal price
            optimal_price = await self._calculate_optimal_price(signal)
            
            # Create execution order
            execution_order = ExecutionOrder(
                order_id="",  # Will be set by API response
                ticker=signal.ticker,
                side=signal.side,
                quantity=signal.quantity,
                price=optimal_price,
                order_type=order_type,
                status=OrderStatus.PENDING,
                signal=signal
            )
            
            # Place order via API
            kalshi_order = await self.client.create_order(
                ticker=signal.ticker,
                side=signal.side,
                quantity=signal.quantity,
                price=optimal_price,
                order_type=order_type.value
            )
            
            # Update execution order with API response
            execution_order.order_id = kalshi_order.order_id
            execution_order.status = OrderStatus.SUBMITTED
            execution_order.updated_at = datetime.now()
            
            # Track order
            self.active_orders[kalshi_order.order_id] = execution_order
            
            logger.info("Order placed successfully", 
                       order_id=kalshi_order.order_id,
                       ticker=signal.ticker,
                       side=signal.side,
                       quantity=signal.quantity,
                       price=optimal_price)
            # Push trade to portfolio server for LiveTradesTerminal
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "timestamp": datetime.now().isoformat(),
                        "order_id": kalshi_order.order_id,
                        "direction": signal.side.upper(),
                        "ticker": signal.ticker,
                        "shares": int(signal.quantity),
                        "price": float(optimal_price),
                        "pnl": 0.0,
                        "status": "submitted",
                    }
                    await session.post("http://localhost:3002/trades/push", json=payload, timeout=5)
            except Exception as e:
                self.logger.warning("Failed to push trade to dashboard", error=str(e))
            return execution_order
            
            return ExecutionResult(
                success=True,
                order_id=kalshi_order.order_id,
                execution_time=datetime.now()
            )
            
        except Exception as e:
            logger.error("Failed to place order", 
                        ticker=signal.ticker,
                        error=str(e))
            
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=datetime.now()
            )
    
    async def _calculate_optimal_price(self, signal: TradingSignal) -> float:
        """Calculate optimal price for order placement"""
        try:
            # Get current market data
            market_data = await self.client.get_market_data(signal.ticker)
            
            if signal.side == "yes":
                current_price = market_data.yes_price
                # Place slightly inside the spread for better execution
                optimal_price = current_price * 1.01  # 1% above current price
            else:
                current_price = market_data.no_price
                optimal_price = current_price * 1.01  # 1% above current price
            
            # Ensure price is within reasonable bounds
            optimal_price = max(0.01, min(optimal_price, 0.99))
            
            return optimal_price
            
        except Exception as e:
            logger.error("Failed to calculate optimal price", 
                        ticker=signal.ticker,
                        error=str(e))
            # Fallback to signal price
            return signal.price
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order"""
        try:
            success = await self.client.cancel_order(order_id)
            
            if success and order_id in self.active_orders:
                self.active_orders[order_id].status = OrderStatus.CANCELLED
                self.active_orders[order_id].updated_at = datetime.now()
                
                logger.info("Order cancelled", order_id=order_id)
            
            return success
            
        except Exception as e:
            logger.error("Failed to cancel order", 
                        order_id=order_id,
                        error=str(e))
            return False
    
    async def update_order_status(self, order_id: str):
        """Update order status from API"""
        try:
            orders = await self.client.get_orders()
            
            for order in orders:
                if order.order_id == order_id:
                    if order_id in self.active_orders:
                        execution_order = self.active_orders[order_id]
                        
                        # Update status
                        if order.status == "filled":
                            execution_order.status = OrderStatus.FILLED
                            execution_order.filled_quantity = order.filled_quantity
                            execution_order.average_fill_price = order.price
                        elif order.status == "partially_filled":
                            execution_order.status = OrderStatus.PARTIALLY_FILLED
                            execution_order.filled_quantity = order.filled_quantity
                        elif order.status == "cancelled":
                            execution_order.status = OrderStatus.CANCELLED
                        elif order.status == "rejected":
                            execution_order.status = OrderStatus.REJECTED
                        
                        execution_order.updated_at = datetime.now()
                        
                        # Move to history if completed
                        if execution_order.status in [OrderStatus.FILLED, 
                                                     OrderStatus.CANCELLED, 
                                                     OrderStatus.REJECTED]:
                            self.order_history.append(execution_order)
                            del self.active_orders[order_id]
                        
                        logger.info("Order status updated", 
                                   order_id=order_id,
                                   status=execution_order.status.value)
                    
                    break
                    
        except Exception as e:
            logger.error("Failed to update order status", 
                        order_id=order_id,
                        error=str(e))
    
    async def update_all_order_statuses(self):
        """Update status of all active orders"""
        for order_id in list(self.active_orders.keys()):
            await self.update_order_status(order_id)
    
    def get_active_orders(self) -> Dict[str, ExecutionOrder]:
        """Get all active orders"""
        return self.active_orders
    
    def get_order_history(self, limit: int = 100) -> List[ExecutionOrder]:
        """Get order history"""
        return self.order_history[-limit:] if self.order_history else []


class PositionManager:
    """Manages positions and portfolio tracking"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.positions: Dict[str, Position] = {}
        self.portfolio_value: float = 0.0
        self.cash_balance: float = 0.0
    
    async def update_positions(self):
        """Update positions from API"""
        try:
            positions = await self.client.get_positions()
            
            # Update position tracker
            self.positions = {}
            for position in positions:
                self.positions[position.ticker] = position
            
            logger.info("Positions updated", 
                       n_positions=len(self.positions))
            
        except Exception as e:
            logger.error("Failed to update positions", error=str(e))
    
    async def update_portfolio(self):
        """Update portfolio information"""
        try:
            portfolio = await self.client.get_portfolio()
            
            self.portfolio_value = portfolio.get("total_value", 0.0)
            self.cash_balance = portfolio.get("cash_balance", 0.0)
            
            logger.info("Portfolio updated", 
                       total_value=self.portfolio_value,
                       cash_balance=self.cash_balance)
            
        except Exception as e:
            logger.error("Failed to update portfolio", error=str(e))
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for specific ticker"""
        return self.positions.get(ticker)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all positions"""
        return self.positions
    
    def calculate_position_pnl(self, ticker: str, current_price: float) -> float:
        """Calculate P&L for a position"""
        position = self.get_position(ticker)
        
        if not position:
            return 0.0
        
        if position.side == "yes":
            pnl = (current_price - position.average_price) * position.quantity
        else:
            pnl = (position.average_price - current_price) * position.quantity
        
        return pnl
    
    def get_portfolio_summary(self) -> Dict[str, float]:
        """Get portfolio summary"""
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        
        return {
            "total_value": self.portfolio_value,
            "cash_balance": self.cash_balance,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "n_positions": len(self.positions)
        }


class ExecutionManager:
    """Main execution manager that coordinates order and position management"""
    
    def __init__(self, client: KalshiAPIClient):
        self.client = client
        self.order_manager = OrderManager(client)
        self.position_manager = PositionManager(client)
        self.execution_queue: List[TradingSignal] = []
        self.is_running = False
    
    async def initialize(self):
        """Initialize execution manager"""
        await self.position_manager.update_portfolio()
        await self.position_manager.update_positions()
        logger.info("Execution manager initialized")
    
    async def execute_signal(self, signal: TradingSignal) -> ExecutionResult:
        """
        Execute a trading signal with enhanced cash safety checks
        """
        try:
            # Update portfolio and positions first
            await self.position_manager.update_portfolio()
            await self.position_manager.update_positions()
            
            # Check if we already have a position
            existing_position = self.position_manager.get_position(signal.ticker)
            if existing_position:
                logger.info("Position already exists, skipping signal", 
                           ticker=signal.ticker)
                return ExecutionResult(success=False, 
                                     error_message="Position already exists")
            
            # Enhanced cash safety checks
            required_cash = signal.quantity * signal.price
            available_cash = self.position_manager.cash_balance
            
            # Safety check 1: Basic cash availability
            if required_cash > available_cash:
                logger.warning("Insufficient cash for order", 
                             required=required_cash,
                             available=available_cash)
                return ExecutionResult(success=False, 
                                     error_message="Insufficient cash")
            
            # Safety check 2: Reserve minimum cash (never use all funds)
            min_reserve = 10.0  # Always keep $10 minimum
            usable_cash = max(0.0, available_cash - min_reserve)
            
            if required_cash > usable_cash:
                logger.warning("Trade would exceed safe cash limit", 
                             required=required_cash,
                             usable_cash=usable_cash,
                             min_reserve=min_reserve)
                return ExecutionResult(success=False, 
                                     error_message="Would exceed safe cash limit")
            
            # Safety check 3: Maximum cash usage percentage
            max_usage_pct = 0.95  # Use max 95% of available cash
            max_safe_amount = available_cash * max_usage_pct
            
            if required_cash > max_safe_amount:
                logger.warning("Trade exceeds maximum safe cash usage", 
                             required=required_cash,
                             max_safe=max_safe_amount,
                             usage_pct=max_usage_pct)
                return ExecutionResult(success=False, 
                                     error_message="Exceeds maximum safe cash usage")
            
            # Safety check 4: Check for pending orders that might reduce available cash
            try:
                pending_orders = await self.client.get_orders(status="pending")
                pending_value = sum(order.quantity * order.price for order in pending_orders)
                net_available = available_cash - pending_value - min_reserve
                
                if required_cash > net_available:
                    logger.warning("Insufficient cash considering pending orders", 
                                 required=required_cash,
                                 net_available=net_available,
                                 pending_value=pending_value)
                    return ExecutionResult(success=False, 
                                         error_message="Insufficient cash considering pending orders")
                
            except Exception as e:
                logger.warning("Could not check pending orders, proceeding with caution", error=str(e))
            
            # Enforce minimum $10 notional per trade
            try:
                price_for_calc = max(float(signal.price), 0.01)
            except Exception:
                price_for_calc = 0.01
            min_notional = config.trading.min_trade_notional if hasattr(config.trading, 'min_trade_notional') else 10.0
            min_qty_required = max(config.trading.min_position_size, math.ceil(min_notional / price_for_calc))
            if signal.quantity < min_qty_required:
                # Determine max quantity permitted by cash and position limits
                max_qty_by_cash = int(usable_cash // price_for_calc)
                adjusted_qty = min(min_qty_required, max_qty_by_cash, int(config.trading.max_position_size))
                if adjusted_qty < min_qty_required:
                    logger.warning("Below minimum trade notional and cannot increase due to limits", 
                                   ticker=signal.ticker,
                                   qty=signal.quantity,
                                   min_qty_required=min_qty_required,
                                   usable_cash=usable_cash,
                                   price=price_for_calc)
                    return ExecutionResult(success=False, error_message="Below minimum trade notional")
                else:
                    logger.info("Adjusting quantity to meet $10 minimum notional", 
                                old_qty=signal.quantity,
                                new_qty=adjusted_qty,
                                price=price_for_calc)
                    signal.quantity = adjusted_qty
            # Recompute required cash with possibly adjusted quantity
            required_cash = signal.quantity * price_for_calc
            if required_cash > usable_cash:
                logger.warning("Adjusted trade exceeds usable cash", required=required_cash, usable_cash=usable_cash)
                return ExecutionResult(success=False, error_message="Adjusted trade exceeds usable cash")
            # All safety checks passed - place order
            result = await self.order_manager.place_order(signal)
            
            if result.success:
                # Add to execution queue for monitoring
                self.execution_queue.append(signal)
                
                logger.info("Signal executed successfully with cash safety checks", 
                           ticker=signal.ticker,
                           order_id=result.order_id,
                           required_cash=required_cash,
                           remaining_cash=available_cash - required_cash)
            
            return result
            
        except Exception as e:
            logger.error("Failed to execute signal", 
                        ticker=signal.ticker,
                        error=str(e))
            
            return ExecutionResult(success=False, error_message=str(e))
    
    async def monitor_executions(self):
        """Monitor active orders and update their status"""
        while self.is_running:
            try:
                # Update order statuses
                await self.order_manager.update_all_order_statuses()
                
                # Update positions
                await self.position_manager.update_positions()
                
                # Update portfolio
                await self.position_manager.update_portfolio()
                
                # Sleep before next update
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error("Error in execution monitoring", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def start_monitoring(self):
        """Start execution monitoring"""
        self.is_running = True
        logger.info("Started execution monitoring")
        
        # Start monitoring task
        asyncio.create_task(self.monitor_executions())
    
    async def stop_monitoring(self):
        """Stop execution monitoring"""
        self.is_running = False
        logger.info("Stopped execution monitoring")
    
    async def cancel_all_orders(self):
        """Cancel all active orders"""
        active_orders = self.order_manager.get_active_orders()
        
        for order_id in active_orders.keys():
            await self.order_manager.cancel_order(order_id)
        
        logger.info("Cancelled all active orders", 
                   n_orders=len(active_orders))
    
    def get_execution_summary(self) -> Dict[str, any]:
        """Get execution summary"""
        active_orders = self.order_manager.get_active_orders()
        order_history = self.order_manager.get_order_history(limit=50)
        portfolio_summary = self.position_manager.get_portfolio_summary()
        
        return {
            "active_orders": len(active_orders),
            "total_orders": len(order_history),
            "portfolio": portfolio_summary,
            "execution_queue": len(self.execution_queue)
        }
    
    async def handle_signal_timeout(self, signal: TradingSignal, 
                                  timeout_hours: int = 24):
        """Handle signal timeout - cancel if not filled"""
        timeout_duration = timedelta(hours=timeout_hours)
        
        # Find the order for this signal
        for order in self.order_manager.active_orders.values():
            if (order.signal and 
                order.signal.ticker == signal.ticker and
                order.signal.timestamp == signal.timestamp):
                
                # Check if order is still pending after timeout
                if (datetime.now() - order.created_at) > timeout_duration:
                    if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
                        await self.order_manager.cancel_order(order.order_id)
                        logger.info("Cancelled timed out order", 
                                   order_id=order.order_id,
                                   ticker=signal.ticker)
                
                break
