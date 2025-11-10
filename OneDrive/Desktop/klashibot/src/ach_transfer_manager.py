"""
ACH Transfer Manager

This module handles automatic daily transfers of withdrawable amounts to ACH-linked bank accounts.
Replaces legacy PayPal integration with secure Plaid + Dwolla ACH transfers.
"""

import logging
from datetime import datetime, time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from src.config import config
from src.ach_client import get_ach_client, ACHTransferResult

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
    """Result of an ACH transfer"""
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


class ACHTransferManager:
    """
    Manages automatic ACH transfers for daily income
    
    This manager integrates with the Node.js ACH microservice to handle
    secure bank transfers via Plaid + Dwolla instead of PayPal.
    """
    
    def __init__(self):
        """Initialize ACH transfer manager"""
        self.config = config.paypal  # Reuse PayPal config structure
        self.is_initialized = False
        self.transfer_history: List[TransferResult] = []
        self.daily_summaries: List[DailyTransferSummary] = []
        self.ach_client = get_ach_client()
        
        # Check if ACH service is available
        self._check_service()
    
    def _check_service(self):
        """Check if ACH service is available"""
        try:
            if self.ach_client.check_service_status():
                self.is_initialized = True
                logger.info("ACH Transfer Manager initialized successfully")
            else:
                logger.warning("ACH service not available")
                self.is_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize ACH Transfer Manager: {e}")
            self.is_initialized = False
    
    async def initialize(self):
        """Initialize the transfer manager"""
        if not self.config.paypal_enabled:
            logger.info("ACH transfers disabled in configuration")
            return
        
        if not self.is_initialized:
            logger.warning("ACH service not initialized, transfers will be disabled")
            return
        
        logger.info("ACH Transfer Manager initialized successfully")
    
    async def transfer_daily_income(self, transfer_amount: float, 
                                  recipient_email: Optional[str] = None) -> TransferResult:
        """
        Transfer daily income via ACH
        
        Args:
            transfer_amount: Pre-calculated amount to transfer
            recipient_email: Not used for ACH (for API compatibility)
            
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
            logger.error("ACH service not initialized")
            return TransferResult(
                success=False,
                error_message="ACH service not initialized"
            )
        
        # Validate transfer amount
        if transfer_amount <= 0:
            logger.warning(f"Transfer amount is zero or negative: ${transfer_amount:.2f}")
            return TransferResult(
                success=False,
                error_message=f"Invalid transfer amount: ${transfer_amount:.2f}"
            )
        
        # Check minimum transfer threshold
        if transfer_amount < self.config.min_transfer_amount:
            logger.info(f"Transfer amount ${transfer_amount:.2f} below minimum ${self.config.min_transfer_amount:.2f}")
            return TransferResult(
                success=False,
                error_message=f"Amount ${transfer_amount:.2f} below minimum ${self.config.min_transfer_amount:.2f}"
            )
        
        try:
            # Initiate ACH transfer via microservice
            result = self.ach_client.initiate_transfer(
                amount=transfer_amount,
                metadata={"description": "Daily trading income"}
            )
            
            # Convert to our TransferResult format
            if result.success:
                transfer_result = TransferResult(
                    success=True,
                    transfer_id=result.transfer_id,
                    amount=result.amount,
                    status=TransferStatus.PENDING if result.status == "pending" else TransferStatus.SUCCESS,
                    timestamp=datetime.now(),
                    fees=0.0  # ACH transfers have different fee structure
                )
                
                self.transfer_history.append(transfer_result)
                
                logger.info(f"ACH transfer initiated successfully",
                           amount=transfer_amount,
                           transfer_id=result.transfer_id,
                           status=result.status)
                
                return transfer_result
            else:
                transfer_result = TransferResult(
                    success=False,
                    amount=transfer_amount,
                    error_message=result.error_message
                )
                
                self.transfer_history.append(transfer_result)
                
                logger.error(f"ACH transfer failed: {result.error_message}")
                return transfer_result
                
        except Exception as e:
            logger.error(f"Exception during ACH transfer: {e}")
            result = TransferResult(
                success=False,
                error_message=str(e),
                amount=transfer_amount
            )
            self.transfer_history.append(result)
            return result
    
    async def check_transfer_status(self, transfer_id: str) -> TransferStatus:
        """
        Check the status of an ACH transfer
        
        Note: Webhooks handle status updates automatically
        """
        # Status is managed via webhooks
        # Return last known status from history
        for transfer in reversed(self.transfer_history):
            if transfer.transfer_id == transfer_id:
                return transfer.status
        
        return TransferStatus.PENDING
    
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
                "transfer_enabled": self.config.paypal_enabled,
                "daily_transfer_enabled": self.config.daily_transfer_enabled,
                "transfer_method": "ACH (Plaid + Dwolla)"
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
            "transfer_enabled": self.config.paypal_enabled,
            "daily_transfer_enabled": self.config.daily_transfer_enabled,
            "min_transfer_amount": self.config.min_transfer_amount,
            "max_transfer_amount": self.config.max_transfer_amount,
            "transfer_time": self.config.transfer_time,
            "transfer_method": "ACH (Plaid + Dwolla)"
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("ACH Transfer Manager cleanup completed")
