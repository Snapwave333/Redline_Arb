"""
Utility functions for the arbitrage bot.
"""

import logging
import os

from dotenv import load_dotenv

# Ensure logs directory exists before configuring logging
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/arbitrage_bot.log"), logging.StreamHandler()],
)

# Load environment variables
load_dotenv()


def get_env_variable(key: str, default: str | None = None) -> str | None:
    """
    Get environment variable with optional default.

    Args:
        key: Environment variable key
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency string.

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    return f"${amount:.2f}" if currency == "USD" else f"{amount:.2f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage string.

    Args:
        value: Value to format (as decimal, e.g., 0.05 for 5%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def calculate_time_until_event(event_time: str) -> str | None:
    """
    Calculate time until event starts.

    Args:
        event_time: ISO format datetime string

    Returns:
        Human-readable time string or None
    """
    try:
        from datetime import datetime

        from dateutil import parser

        event_dt = parser.parse(event_time)
        now = datetime.now(event_dt.tzinfo) if event_dt.tzinfo else datetime.now()
        delta = event_dt - now

        if delta.total_seconds() < 0:
            return "Event started"

        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)

        return f"{hours}h {minutes}m"
    except Exception:
        return None
