"""
Account health cache for performance optimization.
Reduces database I/O by caching frequently accessed stealth scores.
"""

import logging
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AccountHealthCache:
    """
    In-memory cache for account health data to reduce database latency.

    Critical for performance: Stealth scores are accessed frequently during
    arbitrage detection and stake calculation, but change relatively slowly.
    """

    def __init__(self, account_health_manager, cache_ttl_seconds: int = 60):
        """
        Initialize account health cache.

        Args:
            account_health_manager: AccountHealthManager instance
            cache_ttl_seconds: Time-to-live for cache entries (default: 60 seconds)
        """
        self.account_health_manager = account_health_manager
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache: dict[str, tuple] = {}  # {bookmaker: (health_data, timestamp)}
        self._lock = threading.RLock()  # Thread-safe access

    def get_account_health(self, bookmaker_name: str, force_refresh: bool = False) -> dict:
        """
        Get account health with caching.

        Args:
            bookmaker_name: Name of the bookmaker
            force_refresh: Force cache refresh

        Returns:
            Account health dictionary
        """
        with self._lock:
            now = datetime.now()

            # Check cache
            if not force_refresh and bookmaker_name in self._cache:
                health_data, timestamp = self._cache[bookmaker_name]

                # Check if cache is still valid
                if now - timestamp < self.cache_ttl:
                    return health_data

            # Cache miss or expired - fetch from database (bypass cache to avoid recursion)
            health_data = self.account_health_manager.get_account_health(
                bookmaker_name, use_cache=False
            )

            # Store in cache
            self._cache[bookmaker_name] = (health_data, now)

            return health_data

    def get_stealth_score(self, bookmaker_name: str) -> float:
        """
        Get stealth score only (fast path for common use case).

        Args:
            bookmaker_name: Name of the bookmaker

        Returns:
            Stealth score (0.0-1.0)
        """
        health = self.get_account_health(bookmaker_name)
        return health.get("stealth_score", 1.0)

    def invalidate(self, bookmaker_name: str = None):
        """
        Invalidate cache entries.

        Args:
            bookmaker_name: Specific bookmaker to invalidate (None = all)
        """
        with self._lock:
            if bookmaker_name:
                self._cache.pop(bookmaker_name, None)
            else:
                self._cache.clear()

    def warm_cache(self, bookmaker_names: list):
        """
        Pre-load cache for given bookmakers.

        Args:
            bookmaker_names: List of bookmaker names to cache
        """
        for bookmaker in bookmaker_names:
            self.get_account_health(bookmaker)
