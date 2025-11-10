"""Performance benchmarks for arbitrage detection."""

import pytest

from src.arbitrage import ArbitrageDetector, ArbitrageOpportunity


@pytest.mark.benchmark
class TestArbitragePerformance:
    """Performance tests for arbitrage detection."""

    def test_detect_arbitrage_small_dataset(self, benchmark):
        """Benchmark arbitrage detection with small dataset."""
        detector = ArbitrageDetector(min_profit_percentage=0.1)
        outcomes = [
            {"outcome_name": f"Outcome{i}", "odds": 2.0 + (i * 0.1), "bookmaker": f"Bookmaker{i}"}
            for i in range(3)
        ]

        result = benchmark(detector.detect_arbitrage, outcomes)
        assert result is None or isinstance(result, ArbitrageOpportunity)

    def test_detect_arbitrage_large_dataset(self, benchmark):
        """Benchmark arbitrage detection with large dataset."""
        detector = ArbitrageDetector(min_profit_percentage=0.1)
        # Create 100 outcomes across 10 events
        outcomes = [
            {
                "outcome_name": f"Event{i//10}_Outcome{j}",
                "odds": 2.0 + (j * 0.01),
                "bookmaker": f"Bookmaker{j}",
                "event_name": f"Event{i//10}",
                "market": "h2h",
            }
            for i, j in enumerate(range(100))
        ]

        result = benchmark(detector.detect_arbitrage, outcomes)
        # Should complete in reasonable time
        assert result is None or isinstance(result, ArbitrageOpportunity)

    def test_find_best_arbitrages_performance(self, benchmark):
        """Benchmark finding multiple arbitrages."""
        detector = ArbitrageDetector(min_profit_percentage=0.1)

        events = [
            {
                "event_name": f"Event{i}",
                "market": "h2h",
                "outcomes": [
                    {"outcome_name": "Home", "odds": 2.1 + (i * 0.01), "bookmaker": "A"},
                    {"outcome_name": "Away", "odds": 2.2 + (i * 0.01), "bookmaker": "B"},
                ],
            }
            for i in range(50)
        ]

        results = benchmark(detector.find_best_arbitrages, events)
        assert isinstance(results, list)
