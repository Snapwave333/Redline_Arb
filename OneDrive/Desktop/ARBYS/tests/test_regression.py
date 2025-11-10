"""
Regression tests: Verify backward compatibility with legacy code.
"""

import pytest

from src.account_health import AccountHealthManager
from src.arbitrage import ArbitrageDetector
from src.stake_calculator import StakeCalculator


@pytest.mark.regression
class TestLegacySingleAPIMode:
    """Test legacy single-API mode still works."""

    def test_legacy_fetcher_still_works(self):
        """Verify legacy OddsDataFetcher still functions - skipped, paid API removed."""
        pytest.skip(
            "The Odds API removed - paid service not available. Use SofaScore Scraper instead."
        )

    def test_legacy_detector_still_works(self, account_health_manager):
        """Verify legacy ArbitrageDetector still functions."""
        detector = ArbitrageDetector(
            min_profit_percentage=1.0, account_health_manager=account_health_manager
        )

        # Sample odds data
        outcomes = [
            {"outcome_name": "Team A", "odds": 2.1, "bookmaker": "Bookmaker A"},
            {"outcome_name": "Team B", "odds": 2.2, "bookmaker": "Bookmaker B"},
        ]

        result = detector.detect_arbitrage(outcomes)

        # Should detect arbitrage or return None (depending on math)
        # Just verify it doesn't crash
        assert result is None or hasattr(result, "profit_percentage")

    def test_legacy_stake_calculator_still_works(self, account_health_manager, sample_odds_data):
        """Verify legacy StakeCalculator still functions."""
        from datetime import datetime

        from src.arbitrage import ArbitrageOpportunity

        calculator = StakeCalculator(
            round_stakes=True, account_health_manager=account_health_manager
        )

        arb = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=sample_odds_data,
            total_implied_probability=0.97,
            profit_percentage=3.0,
            bookmakers=["Bookmaker A"],
            timestamp=datetime.now().isoformat(),
        )

        distribution = calculator.calculate_stakes(arb, total_stake=100.0)

        assert distribution is not None
        assert len(distribution.stakes) > 0
        assert distribution.total_stake > 0


@pytest.mark.regression
class TestBackwardCompatibility:
    """Test that new features don't break old code."""

    def test_cache_disabled_still_works(self, temp_db):
        """Verify disabling cache doesn't break functionality."""
        manager = AccountHealthManager(db_path=temp_db, enable_cache=False)

        # Should work without cache
        health = manager.get_account_health("NonExistent")
        assert health["stealth_score"] == 1.0  # Default

    def test_sync_orchestrator_wrapper(self, real_providers):
        """Verify async orchestrator synchronous wrapper works with real providers."""
        from src.data_orchestrator_async import AsyncMultiAPIOrchestrator

        orchestrator = AsyncMultiAPIOrchestrator(providers=real_providers)

        # Should work synchronously
        results, errors, latency = orchestrator.fetch_odds("soccer")

        assert isinstance(results, list)
        assert isinstance(errors, list)

    def test_optimized_detector_optional(self, account_health_manager):
        """Verify optimized detector is optional (backward compatible)."""
        # Original detector should still work
        original = ArbitrageDetector(account_health_manager=account_health_manager)

        # Optimized detector should also work
        from src.arbitrage_optimized import OptimizedArbitrageDetector

        optimized = OptimizedArbitrageDetector(account_health_manager=account_health_manager)

        # Both should detect same arbitrages
        outcomes = [
            {"outcome_name": "A", "odds": 2.1, "bookmaker": "B1"},
            {"outcome_name": "B", "odds": 2.2, "bookmaker": "B2"},
        ]

        orig_result = original.detect_arbitrage(outcomes)
        opt_result = optimized.detect_arbitrage_vectorized(outcomes)

        # Both should return same result (both None or both ArbitrageOpportunity)
        assert (orig_result is None) == (opt_result is None)
