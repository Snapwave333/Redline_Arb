"""
PayPal Transfer Manager

This module handles automatic daily transfers of withdrawable amounts to PayPal accounts.
Integrates with the dual strategy to automatically send daily income to your PayPal.
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import paypalrestsdk
from paypalrestsdk import Payout, PayoutItem, ResourceNotFound

from src.config import config

logger = logging.getLogger(__name__)


class TransferStatus(Enum):
    """Transfer status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TransferResult:
    """Result of a PayPal transfer"""
    success: bool
    transfer_id: Optional[str] = None
    amount: float = 0.0
    status: TransferStatus = TransferStatus.PENDING
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    fees: float = 0.0


@dataclass
class DailyTransferSummary:
    """Daily transfer summary"""
    date: datetime
    total_transferred: float
    total_fees: float
    transfers_count: int
    successful_transfers: int
    failed_transfers: int
    transfers: List[TransferResult]


class PayPalTransferManager:
    """
    Manages automatic PayPal transfers for daily income
    """
    
    def __init__(self):
        """Initialize PayPal transfer manager"""
        self.config = config.paypal
        self.is_initialized = False
        self.transfer_history: List[TransferResult] = []
        self.daily_summaries: List[DailyTransferSummary] = []
        
        # Initialize PayPal SDK
        self._setup_paypal()
    
    def _setup_paypal(self):
        """Setup PayPal SDK configuration"""
        try:
            if not self.config.paypal_enabled:
                logger.info("PayPal transfers disabled in configuration")
                return
            
            if not self.config.paypal_client_id or not self.config.paypal_client_secret:
                logger.warning("PayPal credentials not configured")
                return
            
            # Configure PayPal SDK
            paypalrestsdk.configure({
                "mode": self.config.paypal_mode,  # "sandbox" or "live"
                "client_id": self.config.paypal_client_id,
                "client_secret": self.config.paypal_client_secret
            })
            
            self.is_initialized = True
            logger.info("PayPal SDK initialized successfully", mode=self.config.paypal_mode)
            
        except Exception as e:
            logger.error("Failed to initialize PayPal SDK", error=str(e))
            self.is_initialized = False
    
    async def initialize(self):
        """Initialize the transfer manager"""
        if not self.config.paypal_enabled:
            logger.info("PayPal transfers disabled")
            return
        
        if not self.is_initialized:
            logger.warning("PayPal SDK not initialized, transfers will be disabled")
            return
        
        logger.info("PayPal Transfer Manager initialized successfully")
    
    async def transfer_daily_income(self, transfer_amount: float, 
                                  recipient_email: Optional[str] = None) -> TransferResult:
        """
        Transfer daily income to PayPal with calculated transfer amount
        
        Args:
            transfer_amount: Pre-calculated amount to transfer
            recipient_email: Override recipient email (optional)
            
        Returns:
            TransferResult with transfer details
        """
        if not self.config.daily_transfer_enabled:
            logger.info("Daily transfers disabled")
            return TransferResult(
                success=False,
                error_message="Daily transfers disabled"
            )
        
        if not self.is_initialized:
            logger.error("PayPal SDK not initialized")
            return TransferResult(
                success=False,
                error_message="PayPal SDK not initialized"
            )
        
        # Validate transfer amount
        if transfer_amount <= 0:
            logger.warning("Transfer amount is zero or negative", amount=transfer_amount)
            return TransferResult(
                success=False,
                error_message=f"Invalid transfer amount: ${transfer_amount:.2f}"
            )
        
        # Check minimum transfer threshold
        if transfer_amount < self.config.min_transfer_amount:
            logger.info("Transfer amount below minimum threshold",
                       amount=transfer_amount,
                       min_amount=self.config.min_transfer_amount)
            return TransferResult(
                success=False,
                error_message=f"Amount ${transfer_amount:.2f} below minimum ${self.config.min_transfer_amount:.2f}"
            )
        
        # Use configured recipient email if not provided
        if not recipient_email:
            recipient_email = self.config.paypal_recipient_email
        
        if not recipient_email:
            logger.error("No recipient email configured")
            return TransferResult(
                success=False,
                error_message="No recipient email configured"
            )
        
        try:
            # Create PayPal payout
            result = await self._create_paypal_payout(transfer_amount, recipient_email)
            
            # Add to history
            self.transfer_history.append(result)
            
            logger.info("Daily income transfer completed",
                       amount=transfer_amount,
                       recipient=recipient_email,
                       success=result.success,
                       transfer_id=result.transfer_id)
            
            return result
            
        except Exception as e:
            logger.error("Failed to transfer daily income", error=str(e))
            result = TransferResult(
                success=False,
                error_message=str(e),
                amount=transfer_amount
            )
            self.transfer_history.append(result)
            return result
    
    async def _create_paypal_payout(self, amount: float, recipient_email: str) -> TransferResult:
        """
        Create PayPal payout using the SDK
        
        Args:
            amount: Amount to transfer
            recipient_email: Recipient's email
            
        Returns:
            TransferResult with payout details
        """
        try:
            # Calculate PayPal fees (typically 2.9% + $0.30)
            paypal_fee = (amount * 0.029) + 0.30
            net_amount = amount - paypal_fee
            
            # Create payout item
            payout_item = PayoutItem({
                "recipient_type": "EMAIL",
                "amount": {
                    "value": f"{net_amount:.2f}",
                    "currency": "USD"
                },
                "receiver": recipient_email,
                "note": f"Daily trading income - ${amount:.2f}",
                "sender_item_id": f"daily_income_{datetime.now().strftime('%Y%m%d')}"
            })
            
            # Create payout
            payout = Payout({
                "sender_batch_header": {
                    "sender_batch_id": f"daily_income_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "email_subject": "Daily Trading Income Transfer"
                },
                "items": [payout_item]
            })
            
            # Send payout
            if payout.create():
                logger.info("PayPal payout created successfully",
                           payout_id=payout.batch_header.payout_batch_id,
                           amount=amount,
                           net_amount=net_amount,
                           fees=paypal_fee)
                
                return TransferResult(
                    success=True,
                    transfer_id=payout.batch_header.payout_batch_id,
                    amount=amount,
                    status=TransferStatus.SUCCESS,
                    timestamp=datetime.now(),
                    fees=paypal_fee
                )
            else:
                error_msg = f"PayPal payout failed: {payout.error}"
                logger.error("PayPal payout creation failed", error=error_msg)
                
                return TransferResult(
                    success=False,
                    error_message=error_msg,
                    amount=amount
                )
                
        except Exception as e:
            logger.error("Exception during PayPal payout creation", error=str(e))
            return TransferResult(
                success=False,
                error_message=str(e),
                amount=amount
            )
    
    async def check_transfer_status(self, transfer_id: str) -> TransferStatus:
        """
        Check the status of a PayPal transfer
        
        Args:
            transfer_id: PayPal transfer/batch ID
            
        Returns:
            TransferStatus of the transfer
        """
        try:
            payout = Payout.find(transfer_id)
            
            if payout.batch_header.batch_status == "SUCCESS":
                return TransferStatus.SUCCESS
            elif payout.batch_header.batch_status == "PENDING":
                return TransferStatus.PENDING
            elif payout.batch_header.batch_status == "PROCESSING":
                return TransferStatus.PROCESSING
            elif payout.batch_header.batch_status == "CANCELED":
                return TransferStatus.CANCELLED
            else:
                return TransferStatus.FAILED
                
        except ResourceNotFound:
            logger.warning("Transfer not found", transfer_id=transfer_id)
            return TransferStatus.FAILED
        except Exception as e:
            logger.error("Failed to check transfer status", error=str(e))
            return TransferStatus.FAILED
    
    async def get_daily_transfer_summary(self, date: Optional[datetime] = None) -> DailyTransferSummary:
        """
        Get summary of transfers for a specific day
        
        Args:
            date: Date to get summary for (defaults to today)
            
        Returns:
            DailyTransferSummary for the specified date
        """
        if not date:
            date = datetime.now().date()
        
        # Filter transfers for the specified date
        daily_transfers = [
            transfer for transfer in self.transfer_history
            if transfer.timestamp and transfer.timestamp.date() == date
        ]
        
        successful_transfers = [t for t in daily_transfers if t.success]
        failed_transfers = [t for t in daily_transfers if not t.success]
        
        total_transferred = sum(t.amount for t in successful_transfers)
        total_fees = sum(t.fees for t in successful_transfers)
        
        summary = DailyTransferSummary(
            date=datetime.combine(date, time.min),
            total_transferred=total_transferred,
            total_fees=total_fees,
            transfers_count=len(daily_transfers),
            successful_transfers=len(successful_transfers),
            failed_transfers=len(failed_transfers),
            transfers=daily_transfers
        )
        
        return summary
    
    async def schedule_daily_transfer(self, withdrawable_amount: float):
        """
        Schedule daily $400 transfer at configured time
        
        Args:
            withdrawable_amount: Amount available to transfer
        """
        if not self.config.daily_transfer_enabled:
            logger.info("Daily transfers disabled")
            return
        
        if not self.config.auto_transfer_enabled:
            logger.info("Auto transfers disabled")
            return
        
        # Parse transfer time
        try:
            transfer_hour, transfer_minute = map(int, self.config.transfer_time.split(':'))
            transfer_time = time(transfer_hour, transfer_minute)
        except ValueError:
            logger.error("Invalid transfer time format", time=self.config.transfer_time)
            transfer_time = time(18, 0)  # Default to 6 PM
        
        # Check if it's time for transfer
        current_time = datetime.now().time()
        if current_time >= transfer_time:
            logger.info("Time for daily $400 transfer", 
                       current_time=current_time.strftime('%H:%M'),
                       transfer_time=transfer_time.strftime('%H:%M'))
            
            # Check if we already transferred today
            today_summary = await self.get_daily_transfer_summary()
            if today_summary.successful_transfers > 0:
                logger.info("Daily $400 transfer already completed today")
                return
            
            # Execute $400 transfer
            await self.transfer_daily_income(withdrawable_amount)
    
    def get_transfer_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive transfer summary
        
        Returns:
            Dictionary with transfer statistics
        """
        if not self.transfer_history:
            return {
                "total_transfers": 0,
                "successful_transfers": 0,
                "failed_transfers": 0,
                "total_amount_transferred": 0.0,
                "total_fees_paid": 0.0,
                "average_transfer_amount": 0.0,
                "success_rate": 0.0,
                "last_transfer": None,
                "paypal_enabled": self.config.paypal_enabled,
                "daily_transfer_enabled": self.config.daily_transfer_enabled
            }
        
        successful_transfers = [t for t in self.transfer_history if t.success]
        failed_transfers = [t for t in self.transfer_history if not t.success]
        
        total_amount = sum(t.amount for t in successful_transfers)
        total_fees = sum(t.fees for t in successful_transfers)
        
        return {
            "total_transfers": len(self.transfer_history),
            "successful_transfers": len(successful_transfers),
            "failed_transfers": len(failed_transfers),
            "total_amount_transferred": total_amount,
            "total_fees_paid": total_fees,
            "average_transfer_amount": total_amount / len(successful_transfers) if successful_transfers else 0.0,
            "success_rate": len(successful_transfers) / len(self.transfer_history) if self.transfer_history else 0.0,
            "last_transfer": self.transfer_history[-1].timestamp.isoformat() if self.transfer_history else None,
            "paypal_enabled": self.config.paypal_enabled,
            "daily_transfer_enabled": self.config.daily_transfer_enabled,
            "min_transfer_amount": self.config.min_transfer_amount,
            "max_transfer_amount": self.config.max_transfer_amount,
            "transfer_time": self.config.transfer_time,
            "recipient_email": self.config.paypal_recipient_email
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("PayPal Transfer Manager cleanup completed")
