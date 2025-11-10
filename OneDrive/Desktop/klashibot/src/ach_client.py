"""
ACH Transfer Client for Python Bot

This module provides a Python interface to the ACH Transfer microservice,
allowing the Python trading bot to initiate transfers via HTTP calls.
"""

import logging
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ACHTransferResult:
    """Result of an ACH transfer"""
    success: bool
    transfer_id: Optional[str] = None
    amount: float = 0.0
    status: str = "pending"
    error_message: Optional[str] = None
    idempotency_key: Optional[str] = None


class ACHClient:
    """Client for interacting with the ACH Transfer microservice"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Initialize the ACH client
        
        Args:
            base_url: Base URL of the ACH microservice
        """
        self.base_url = base_url
        self.timeout = 30
        
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the ACH service
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response JSON
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, timeout=self.timeout)
            elif method == "GET":
                response = requests.get(url, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to ACH service at {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check if the ACH service is healthy
        
        Returns:
            Health check response
        """
        try:
            return self._request("GET", "/health")
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return {"status": "unhealthy"}
    
    def initiate_transfer(self, amount: float, metadata: Optional[Dict] = None) -> ACHTransferResult:
        """
        Initiate an ACH transfer
        
        Args:
            amount: Transfer amount
            metadata: Optional metadata for the transfer
            
        Returns:
            ACHTransferResult with transfer details
        """
        try:
            request_data = {"amount": amount}
            if metadata:
                request_data["metadata"] = metadata
            
            response = self._request("POST", "/dwolla/transfers", data=request_data)
            
            if response.get("success"):
                return ACHTransferResult(
                    success=True,
                    transfer_id=response.get("transfer_id"),
                    amount=response.get("amount", 0.0),
                    status=response.get("status", "pending"),
                    idempotency_key=response.get("idempotency_key")
                )
            else:
                return ACHTransferResult(
                    success=False,
                    error_message=response.get("error", "Unknown error")
                )
                
        except Exception as e:
            logger.error(f"Failed to initiate ACH transfer: {e}")
            return ACHTransferResult(
                success=False,
                error_message=str(e)
            )
    
    def check_service_status(self) -> bool:
        """
        Check if the ACH service is available
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            health = self.check_health()
            return health.get("status") == "healthy"
        except Exception:
            return False


# Global client instance (for backward compatibility)
_global_ach_client = None


def get_ach_client() -> ACHClient:
    """
    Get the global ACH client instance
    
    Returns:
        ACHClient instance
    """
    global _global_ach_client
    if _global_ach_client is None:
        import os
        base_url = os.getenv("ACH_SERVICE_URL", "http://localhost:3000")
        _global_ach_client = ACHClient(base_url)
    return _global_ach_client


def initiate_ach_transfer(amount: float, metadata: Optional[Dict] = None) -> ACHTransferResult:
    """
    Convenience function to initiate an ACH transfer
    
    Args:
        amount: Transfer amount
        metadata: Optional metadata
        
    Returns:
        ACHTransferResult
    """
    return get_ach_client().initiate_transfer(amount, metadata)
