"""
Performance benchmarks to validate optimization improvements.
"""

import statistics
import time

import pytest

from src.account_health import AccountHealthManager
from src.data_orchestrator_async import AsyncMultiAPIOrchestrator


@pytest.mark.benchmark
class TestIOLatency:
    """Test database I/O latency improvements."""

    def test_cached_lookup_latency(self, account_health_manager, sample_account_profile):
        """Verify cached lookups are below 0.5ms threshold."""
        bookmaker_name = sample_account_profile.bookmaker_name

        # Warm cache
        account_health_manager.get_account_health(bookmaker_name)

        # Measure cached lookup time
        import time

        times = []
        for _ in range(1000):
            start = time.perf_counter()
            result = account_health_manager.get_account_health(bookmaker_name)
            times.append(time.perf_counter() - start)

        avg_time_ms = (sum(times) / len(times)) * 1000

        # Verify result is correct
        assert result["stealth_score"] == pytest.approx(0.9, rel=0.01)

        # Verify performance (cached should be < 0.5ms)
        assert avg_time_ms < 0.5, f"Cached lookup took {avg_time_ms:.3f}ms, expected < 0.5ms"

        print(f"\nCached Lookup Performance: {avg_time_ms:.3f}ms (avg over 1000 iterations)")

    def test_database_vs_cache_performance(self, temp_db, sample_account_profile):
        """Compare database lookup vs cached lookup performance."""
        bookmaker_name = sample_account_profile.bookmaker_name

        # Create manager with cache
        manager_with_cache = AccountHealthManager(db_path=temp_db, enable_cache=True)

        # Create manager without cache
        manager_no_cache = AccountHealthManager(db_path=temp_db, enable_cache=False)

        # Warm cache
        manager_with_cache.get_account_health(bookmaker_name)

        # Benchmark cached (1000 iterations)
        cached_times = []
        for _ in range(1000):
            start = time.perf_counter()
            manager_with_cache.get_account_health(bookmaker_name)
            cached_times.append(time.perf_counter() - start)

        cached_avg = statistics.mean(cached_times) * 1000  # Convert to ms

        # Benchmark uncached (1000 iterations)
        uncached_times = []
        for _ in range(1000):
            start = time.perf_counter()
            manager_no_cache.get_account_health(bookmaker_name)
            uncached_times.append(time.perf_counter() - start)

        uncached_avg = statistics.mean(uncached_times) * 1000  # Convert to ms

        # Cached should be significantly faster
        assert cached_avg < 0.5, f"Cached lookup took {cached_avg:.3f}ms, expected < 0.5ms"
        assert (
            cached_avg < uncached_avg / 10
        ), f"Cache should be >10x faster: cached={cached_avg:.3f}ms, uncached={uncached_avg:.3f}ms"

        print("\nPerformance Results:")
        print(f"  Cached lookup:   {cached_avg:.3f}ms (avg)")
        print(f"  Uncached lookup: {uncached_avg:.3f}ms (avg)")
        print(f"  Speedup: {uncached_avg/cached_avg:.1f}x")


@pytest.mark.benchmark
class TestArbitrageDetectionPerformance:
    """Test arbitrage detection performance."""

    def test_vectorized_detection_speed(
        self, arbitrage_detector, optimized_detector, sample_odds_data
    ):
        """Benchmark vectorized detection speed."""
        import time

        # Benchmark original
        original_times = []
        for _ in range(100):
            start = time.perf_counter()
            arbitrage_detector.detect_arbitrage(sample_odds_data)
            original_times.append(time.perf_counter() - start)

        # Benchmark optimized
        optimized_times = []
        for _ in range(100):
            start = time.perf_counter()
            optimized_detector.detect_arbitrage_vectorized(sample_odds_data)
            optimized_times.append(time.perf_counter() - start)

        original_avg = sum(original_times) / len(original_times) * 1000
        optimized_avg = sum(optimized_times) / len(optimized_times) * 1000

        # Verify results are identical
        orig_arb = arbitrage_detector.detect_arbitrage(sample_odds_data)
        opt_arb = optimized_detector.detect_arbitrage_vectorized(sample_odds_data)

        if orig_arb is None:
            assert opt_arb is None
        else:
            assert abs(orig_arb.profit_percentage - opt_arb.profit_percentage) < 0.001

        print("\nDetection Performance:")
        print(f"  Original:  {original_avg:.3f}ms (avg)")
        print(f"  Optimized: {optimized_avg:.3f}ms (avg)")
        if original_avg > 0:
            print(f"  Speedup: {original_avg/optimized_avg:.2f}x")

    def test_large_dataset_performance(self, optimized_detector):
        """Test performance with large dataset."""
        # Create large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append(
                {
                    "event_name": f"Event {i}",
                    "market": "h2h",
                    "outcome_name": f"Outcome {i % 3}",
                    "odds": 2.0 + (i % 10) * 0.1,
                    "odds_format": "decimal",
                    "bookmaker": f"Bookmaker {i % 5}",
                }
            )

        # Measure processing time
        start = time.perf_counter()
        optimized_detector.detect_arbitrage_vectorized(large_dataset)
        elapsed = time.perf_counter() - start

        # Should process 1000 outcomes in reasonable time (< 100ms)
        assert (
            elapsed < 0.1
        ), f"Large dataset processing took {elapsed*1000:.1f}ms, expected < 100ms"

        print("\nLarge Dataset Performance:")
        print("  Dataset size: 1000 outcomes")
        print(f"  Processing time: {elapsed*1000:.2f}ms")


@pytest.mark.benchmark
class TestOrchestratorPerformance:
    """Test orchestrator performance improvements."""

    @pytest.mark.asyncio
    async def test_async_vs_sync_performance(self, real_providers):
        """Compare async vs sync provider fetching with real providers."""
        from src.data_orchestrator import MultiAPIOrchestrator

        sync_orch = MultiAPIOrchestrator(providers=real_providers)
        async_orch = AsyncMultiAPIOrchestrator(providers=real_providers)

        # Benchmark sync
        sync_start = time.perf_counter()
        sync_results, sync_errors, sync_latency = sync_orch.fetch_odds("soccer")
        sync_time = time.perf_counter() - sync_start

        # Benchmark async
        async_start = time.perf_counter()
        async_results, async_errors, async_latency = await async_orch.fetch_odds_async("soccer")
        async_time = time.perf_counter() - async_start

        # Both should return results (may be empty)
        assert isinstance(sync_results, list)
        assert isinstance(async_results, list)

        # Real providers may vary, but should complete reasonably
        assert async_time < 60.0, f"Async ({async_time*1000:.0f}ms) took too long"
        assert sync_time < 60.0, f"Sync ({sync_time*1000:.0f}ms) took too long"

        print("\nOrchestrator Performance (Real Providers):")
        print(f"  Sync time:  {sync_time*1000:.2f}ms")
        print(f"  Async time: {async_time*1000:.2f}ms")
        if async_time > 0:
            print(f"  Speedup: {sync_time/async_time:.2f}x")
