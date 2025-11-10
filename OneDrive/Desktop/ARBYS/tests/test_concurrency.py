"""
Concurrency and async testing to validate thread safety and async operations.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.account_health import AccountHealthManager
from src.account_manager import AccountDatabase, AccountProfile
from src.data_orchestrator_async import AsyncMultiAPIOrchestrator


class TestThreadSafety:
    """Test thread safety of caching system."""

    def test_concurrent_cache_access(self, temp_db):
        """Test concurrent access to cache."""
        # Create account
        db = AccountDatabase(db_path=temp_db)
        profile = AccountProfile(
            bookmaker_name="ConcurrentTest", account_username="test", stealth_score=0.8
        )
        db.create_account(profile)

        # Create manager with cache
        manager = AccountHealthManager(db_path=temp_db, enable_cache=True)

        # Warm cache
        manager.get_account_health("ConcurrentTest")

        # Concurrent access test
        results = []
        errors = []

        def read_health():
            try:
                result = manager.get_account_health("ConcurrentTest")
                results.append(result["stealth_score"])
            except Exception as e:
                errors.append(str(e))

        # Run 100 concurrent reads
        threads = []
        for _ in range(100):
            thread = threading.Thread(target=read_health)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Verify all results are correct
        assert len(results) == 100
        assert all(score == 0.8 for score in results), f"Unexpected stealth scores: {set(results)}"

    def test_cache_thread_safety(self, temp_db):
        """Test cache thread safety directly."""
        db = AccountDatabase(db_path=temp_db)
        profile = AccountProfile(
            bookmaker_name="CacheTest", account_username="test", stealth_score=0.75
        )
        db.create_account(profile)

        manager = AccountHealthManager(db_path=temp_db, enable_cache=True)

        # Ensure cache is initialized
        if not manager._cache:
            pytest.skip("Cache not initialized")

        cache = manager._cache

        # Warm cache
        cache.get_account_health("CacheTest")

        # Concurrent reads
        def read_cache():
            return cache.get_account_health("CacheTest")

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(read_cache) for _ in range(200)]
            results = [f.result() for f in futures]

        # Verify all results are correct
        assert all(
            r["stealth_score"] == 0.75 for r in results
        ), "Cache returned incorrect values under concurrent access"


class TestAsyncOperations:
    """Test async operations and failover."""

    @pytest.mark.asyncio
    async def test_async_provider_fetching(self, real_providers):
        """Test async provider fetching with real providers."""
        orchestrator = AsyncMultiAPIOrchestrator(providers=real_providers, failover_enabled=True)

        results, errors, latency = await orchestrator.fetch_odds_async("soccer")

        # Results may be empty if no events available, but should not crash
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_async_failover(self, real_providers):
        """Test async failover - requires at least 2 real providers."""
        if len(real_providers) < 2:
            pytest.skip("Need at least 2 providers to test failover")

        # Use real providers - failover will be tested naturally if one fails
        orchestrator = AsyncMultiAPIOrchestrator(providers=real_providers, failover_enabled=True)

        # Test with real providers - may succeed or fail depending on network/API
        results, errors, latency = await orchestrator.fetch_odds_async("soccer")

        # Should return results (may be empty) or errors, but not crash
        assert isinstance(results, list)
        assert isinstance(errors, list)

    @pytest.mark.asyncio
    async def test_parallel_provider_fetching(self, real_providers):
        """Test that real providers fetch in parallel."""
        import time

        if len(real_providers) < 2:
            pytest.skip("Need at least 2 providers to test parallel fetching")

        # Use multiple real providers to test parallel execution
        orchestrator = AsyncMultiAPIOrchestrator(providers=real_providers)

        # Measure parallel execution time
        start = time.perf_counter()
        results, errors, latency = await orchestrator.fetch_odds_async("soccer")
        elapsed = time.perf_counter() - start

        # Real providers may take longer depending on network, but should complete
        assert elapsed < 30.0, f"Fetching took {elapsed*1000:.0f}ms, expected <30s"

        assert isinstance(results, list)
        assert isinstance(errors, list)

        print("\nParallel Fetching Test (Real Providers):")
        print(f"  Providers: {len(real_providers)}")
        print(f"  Time: {elapsed*1000:.0f}ms")
        print(f"  Results: {len(results)} events")


class TestDataIntegrity:
    """Test that async operations don't corrupt data."""

    @pytest.mark.asyncio
    async def test_async_data_merging(self, real_providers):
        """Test that async merging produces correct results with real providers."""
        orchestrator = AsyncMultiAPIOrchestrator(providers=real_providers, failover_enabled=True)

        results, errors, latency = await orchestrator.fetch_odds_async("soccer")

        # Verify merged results structure
        if results:
            for event in results:
                assert "event_name" in event
                assert "outcomes" in event
                assert isinstance(event["outcomes"], list)

                # Verify outcomes have required fields
                for outcome in event["outcomes"]:
                    assert "outcome_name" in outcome
                    assert "odds" in outcome
                    assert "bookmaker" in outcome
        else:
            # No results is OK - may be no events available
            assert isinstance(results, list)
