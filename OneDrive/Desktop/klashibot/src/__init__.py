"""
Kalshi Trading Bot - Package Initialization

This package provides a comprehensive trading bot for Kalshi prediction markets.
"""

__version__ = "1.0.0"
__author__ = "Kalshi Trading Bot Team"
__description__ = "A sophisticated trading bot for Kalshi prediction markets"

# Import main components for easy access
from .config import config
from .main import KalshiTradingBot

__all__ = [
    "config",
    "KalshiTradingBot"
]
