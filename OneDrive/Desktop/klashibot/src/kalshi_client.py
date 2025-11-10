"""
Kalshi API Client using Official SDK

This module provides a comprehensive client for interacting with the Kalshi API,
using the official kalshi-python SDK for authentication and API calls.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

from kalshi_python import KalshiClient, Configuration, PortfolioApi, MarketsApi
from kalshi_python.api_client import ApiClient
from .config import config

logger = structlog.get_logger(__name__)


@dataclass
class MarketData:
    """Market data structure"""
    ticker: str
    yes_price: float
    no_price: float
    volume: int
    open_interest: int
    last_price: Optional[float]
    timestamp: datetime


@dataclass
class Order:
    """Order structure"""
    order_id: str
    ticker: str
    side: str  # 'yes' or 'no'
    quantity: int
    price: float
    status: str
    created_at: datetime
    filled_at: Optional[datetime] = None
    filled_quantity: int = 0


@dataclass
class Position:
    """Position structure"""
    ticker: str
    side: str
    quantity: int
    average_price: float
    unrealized_pnl: float
    realized_pnl: float


class KalshiAPIClient:
    """Main Kalshi API client using official SDK"""
    
    def __init__(self):
        self.api_key = config.api.kalshi_api_key
        self.private_key_path = config.api.kalshi_private_key
        self.base_url = config.api.kalshi_base_url
        
        # Initialize SDK client with proper configuration
        sdk_config = Configuration(host=self.base_url)
        self.api_client = ApiClient(sdk_config)
        
        # Set authentication
        self.api_client.set_kalshi_auth(self.api_key, self.private_key_path)
        
        # Initialize API clients with the api_client
        self.portfolio_api = PortfolioApi(self.api_client)
        self.markets_api = MarketsApi(self.api_client)
        
        logger.info("Kalshi API client initialized with official SDK")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass
    
    # Market Data Methods
    
    async def get_markets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of available markets"""
        try:
            response = self.markets_api.get_markets(limit=limit)
            markets = []
            
            if response.markets:
                for market in response.markets:
                    market_dict = {
                        'ticker': market.ticker,
                        'title': market.title,
                        'status': market.status,
                        'close_time': market.close_time,
                        'volume': getattr(market, 'volume', 0),
                        'open_interest': getattr(market, 'open_interest', 0),
                        'yes_bid': getattr(market, 'yes_bid', 0),
                        'yes_ask': getattr(market, 'yes_ask', 0),
                        'no_bid': getattr(market, 'no_bid', 0),
                        'no_ask': getattr(market, 'no_ask', 0)
                    }
                    markets.append(market_dict)
            
            return markets
            
        except Exception as e:
            logger.error("Failed to get markets", error=str(e))
            return []
    
    async def get_market(self, ticker: str) -> Dict[str, Any]:
        """Get specific market data"""
        try:
            response = self.markets_api.get_market(ticker=ticker)
            market = response.market
            
            return {
                'ticker': market.ticker,
                'title': market.title,
                'status': market.status,
                'close_time': market.close_time,
                'volume': getattr(market, 'volume', 0),
                'open_interest': getattr(market, 'open_interest', 0),
                'yes_bid': getattr(market, 'yes_bid', 0),
                'yes_ask': getattr(market, 'yes_ask', 0),
                'no_bid': getattr(market, 'no_bid', 0),
                'no_ask': getattr(market, 'no_ask', 0)
            }
            
        except Exception as e:
            logger.error("Failed to get market", ticker=ticker, error=str(e))
            return {}
    
    async def get_market_orderbook(self, ticker: str) -> Dict[str, Any]:
        """Get market orderbook - uses market data since orderbook is empty"""
        try:
            # The orderbook endpoint returns empty data, so we get bid/ask from market data
            market_response = self.markets_api.get_market(ticker=ticker)
            market = market_response.market
            
            return {
                'yes': {
                    'best_price': getattr(market, 'yes_bid', 0) or 0,
                    'best_quantity': 0  # Size not available in market data
                },
                'no': {
                    'best_price': getattr(market, 'no_bid', 0) or 0,
                    'best_quantity': 0  # Size not available in market data
                }
            }
            
        except Exception as e:
            logger.error("Failed to get orderbook", ticker=ticker, error=str(e))
            return {'yes': {'best_price': 0, 'best_quantity': 0}, 'no': {'best_price': 0, 'best_quantity': 0}}
    
    # Account Methods
    
    async def get_user(self) -> Dict[str, Any]:
        """Get user account information"""
        try:
            response = self.portfolio_api.get_user()
            user = response.user
            
            return {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'balance': user.balance / 100 if user.balance else 0  # Convert cents to dollars
            }
            
        except Exception as e:
            logger.error("Failed to get user info", error=str(e))
            return {}
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio information"""
        try:
            balance_response = self.portfolio_api.get_balance()
            positions_response = self.portfolio_api.get_positions()
            
            balance = balance_response.balance / 100 if balance_response.balance else 0  # Convert cents to dollars
            
            positions = []
            if positions_response.positions:
                for pos in positions_response.positions:
                    position_dict = {
                        'ticker': pos.ticker,
                        'side': pos.side,
                        'quantity': pos.position,
                        'average_price': pos.average_price / 100 if pos.average_price else 0,
                        'unrealized_pnl': pos.unrealized_pnl / 100 if pos.unrealized_pnl else 0,
                        'realized_pnl': pos.realized_pnl / 100 if pos.realized_pnl else 0
                    }
                    positions.append(position_dict)
            
            return {
                'balance': balance,
                'positions': positions,
                'total_value': balance + sum(pos['unrealized_pnl'] for pos in positions)
            }
            
        except Exception as e:
            logger.error("Failed to get portfolio", error=str(e))
            return {'balance': 0, 'positions': [], 'total_value': 0}
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            response = self.portfolio_api.get_positions()
            positions = []
            
            if response.positions:
                for pos in response.positions:
                    position = Position(
                        ticker=pos.ticker,
                        side=pos.side,
                        quantity=pos.position,
                        average_price=pos.average_price / 100 if pos.average_price else 0,
                        unrealized_pnl=pos.unrealized_pnl / 100 if pos.unrealized_pnl else 0,
                        realized_pnl=pos.realized_pnl / 100 if pos.realized_pnl else 0
                    )
                    positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error("Failed to get positions", error=str(e))
            return []
    
    # Order Methods (Placeholder - SDK doesn't have order methods)
    
    async def create_order(self, ticker: str, side: str, quantity: int, 
                          price: float, order_type: str = "limit") -> Order:
        """Create a new order (placeholder - not implemented in SDK)"""
        logger.warning("Order creation not implemented in SDK", ticker=ticker, side=side, quantity=quantity, price=price)
        
        # Return a mock order for testing
        return Order(
            order_id=f"mock_{ticker}_{side}_{quantity}",
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=price,
            status="pending",
            created_at=datetime.now()
        )
    
    async def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """Get orders (placeholder - not implemented in SDK)"""
        logger.warning("Order retrieval not implemented in SDK")
        return []
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order (placeholder - not implemented in SDK)"""
        logger.warning("Order cancellation not implemented in SDK", order_id=order_id)
        return False
    
    # Utility Methods
    
    def calculate_probability(self, yes_price: float, no_price: float) -> float:
        """Calculate implied probability from prices"""
        total_price = yes_price + no_price
        if total_price == 0:
            return 0.5
        return yes_price / total_price
    
    def calculate_kelly_fraction(self, probability: float, odds: float) -> float:
        """Calculate Kelly criterion fraction"""
        if odds <= 0:
            return 0
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds, p = probability, q = 1 - p
        q = 1 - probability
        kelly = (odds * probability - q) / odds
        
        # Apply conservative fraction
        return max(0, min(kelly * config.trading.default_kelly_fraction, 0.25))
    
    async def get_market_data(self, ticker: str) -> MarketData:
        """Get comprehensive market data for a ticker"""
        market = await self.get_market(ticker)
        orderbook = await self.get_market_orderbook(ticker)
        
        yes_price = orderbook.get("yes", {}).get("best_price", 0)
        no_price = orderbook.get("no", {}).get("best_price", 0)
        
        return MarketData(
            ticker=ticker,
            yes_price=yes_price,
            no_price=no_price,
            volume=market.get("volume", 0),
            open_interest=market.get("open_interest", 0),
            last_price=market.get("yes_ask", 0),  # Use ask price as last price
            timestamp=datetime.now()
        )
    
    async def get_balance(self) -> float:
        """Get current account balance in dollars"""
        try:
            response = self.portfolio_api.get_balance()
            return response.balance / 100 if response.balance else 0  # Convert cents to dollars
        except Exception as e:
            logger.error("Failed to get balance", error=str(e))
            return 0.0