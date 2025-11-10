"""Performance benchmarks for account health caching."""

import pytest

from src.account_health import AccountHealthManager
from src.account_manager import AccountProfile


@pytest.mark.benchmark
class TestCachePerformance:
    """Performance tests for account health caching."""

    def test_cached_lookup_performance(self, benchmark, temp_db):
        """Benchmark cached account health lookups."""
        manager = AccountHealthManager(db_path=temp_db, enable_cache=True)

        # Create test account
        profile = AccountProfile(
            bookmaker_name="TestBookmaker", account_username="test", stealth_score=0.8
        )
        manager.db.create_account(profile)

        # Warm cache
        manager.get_account_health("TestBookmaker", use_cache=True)

        def lookup():
            return manager.get_account_health("TestBookmaker", use_cache=True)

        result = benchmark(lookup)
        assert result is not None
        # Cached lookups should be very fast (<1ms)

    def test_uncached_lookup_performance(self, benchmark, temp_db):
        """Benchmark uncached account health lookups."""
        manager = AccountHealthManager(db_path=temp_db, enable_cache=False)

        profile = AccountProfile(
            bookmaker_name="TestBookmaker2", account_username="test", stealth_score=0.8
        )
        manager.db.create_account(profile)

        def lookup():
            return manager.get_account_health("TestBookmaker2", use_cache=False)

        result = benchmark(lookup)
        assert result is not None
        # Uncached lookups involve DB access, should still be reasonable
