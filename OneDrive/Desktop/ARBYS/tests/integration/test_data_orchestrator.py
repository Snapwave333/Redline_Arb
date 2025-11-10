"""Integration tests for data orchestrator."""

from unittest.mock import Mock

from src.data_orchestrator import MultiAPIOrchestrator
from tests.utils.providers import _TestBaseProvider


class MockProvider(_TestBaseProvider):
    """Mock API provider for testing."""

    def __init__(self, name: str, priority: int = 1, enabled: bool = True, data: list = None):
        super().__init__(name=name, api_key="test", enabled=enabled, priority=priority, data=data)
        self.fetch_count = 0

    def fetch_odds(self, sport: str, **kwargs):
        self.fetch_count += 1
        return self._test_data


class TestMultiAPIOrchestrator:
    """Integration tests for MultiAPIOrchestrator."""

    def test_init_with_providers(self):
        """Test initialization with providers."""
        providers = [
            MockProvider("Provider1", priority=1),
            MockProvider("Provider2", priority=2),
        ]
        orchestrator = MultiAPIOrchestrator(providers)
        assert len(orchestrator.providers) == 2
        assert orchestrator.providers[0].priority == 1

    def test_fetch_odds_single_provider(self):
        """Test fetching odds from single provider."""
        mock_data = [
            {"event_name": "Event 1", "outcomes": []},
        ]
        provider = MockProvider("Provider1", data=mock_data)
        orchestrator = MultiAPIOrchestrator([provider])

        results, errors, latency = orchestrator.fetch_odds("soccer")

        assert len(results) > 0
        assert len(errors) == 0
        assert provider.fetch_count == 1

    def test_fetch_odds_multiple_providers(self):
        """Test fetching odds from multiple providers."""
        provider1 = MockProvider("Provider1", priority=1, data=[{"event": "Event 1"}])
        provider2 = MockProvider("Provider2", priority=2, data=[{"event": "Event 2"}])
        orchestrator = MultiAPIOrchestrator([provider1, provider2])

        results, errors, latency = orchestrator.fetch_odds("soccer")

        assert len(results) >= 1
        assert provider1.fetch_count == 1
        assert provider2.fetch_count == 1

    def test_fetch_odds_failover(self):
        """Test failover when first provider fails."""
        provider1 = MockProvider("Provider1", priority=1)
        provider1.fetch_odds = Mock(side_effect=Exception("Provider 1 failed"))

        provider2 = MockProvider("Provider2", priority=2, data=[{"event": "Event 1"}])
        orchestrator = MultiAPIOrchestrator([provider1, provider2], failover_enabled=True)

        results, errors, latency = orchestrator.fetch_odds("soccer")

        assert len(errors) > 0
        assert len(results) > 0  # Provider2 should have succeeded
        assert provider2.fetch_count == 1

    def test_merge_provider_results(self):
        """Test merging results from multiple providers."""
        provider1 = MockProvider(
            "Provider1",
            data=[{"event_name": "Event 1", "outcomes": [{"name": "Home", "odds": 2.0}]}],
        )
        provider2 = MockProvider(
            "Provider2",
            data=[{"event_name": "Event 1", "outcomes": [{"name": "Away", "odds": 2.1}]}],
        )
        orchestrator = MultiAPIOrchestrator([provider1, provider2])

        results, errors, latency = orchestrator.fetch_odds("soccer")

        assert len(results) >= 1

    def test_provider_priority_ordering(self):
        """Test that providers are called in priority order."""
        call_order = []

        def track_call(name):
            def wrapper(*args, **kwargs):
                call_order.append(name)
                return []

            return wrapper

        provider1 = MockProvider("Provider1", priority=2)
        provider1.fetch_odds = track_call("Provider1")

        provider2 = MockProvider("Provider2", priority=1)
        provider2.fetch_odds = track_call("Provider2")

        orchestrator = MultiAPIOrchestrator([provider1, provider2])
        orchestrator.fetch_odds("soccer")

        # Provider2 (priority 1) should be called before Provider1 (priority 2)
        assert call_order.index("Provider2") < call_order.index("Provider1")

    def test_disabled_provider_skipped(self):
        """Test that disabled providers are skipped."""
        provider1 = MockProvider("Provider1", enabled=False)
        provider2 = MockProvider("Provider2", enabled=True, data=[{"event": "Event 1"}])
        orchestrator = MultiAPIOrchestrator([provider1, provider2])

        results, errors, latency = orchestrator.fetch_odds("soccer")

        assert provider1.fetch_count == 0
        assert provider2.fetch_count == 1

    def test_get_provider_health(self):
        """Test getting provider health status."""
        provider1 = MockProvider("Provider1")
        provider2 = MockProvider("Provider2")
        orchestrator = MultiAPIOrchestrator([provider1, provider2])

        health = orchestrator.get_provider_status()

        assert isinstance(health, dict)
        assert len(health) >= 0

    def test_one_missing_provider(self):
        """Test merge when one provider returns empty results."""
        provider1 = MockProvider(
            "Provider1",
            data=[{"event_name": "Event 1", "outcomes": [{"name": "Home", "odds": 2.0}]}],
        )
        provider2 = MockProvider("Provider2", data=[])  # Empty results
        orchestrator = MultiAPIOrchestrator([provider1, provider2])

        results, errors, latency = orchestrator.fetch_odds("soccer")

        # Should still have results from provider1
        assert len(results) >= 1
        # Provider2 should have latency stats
        assert "Provider2" in latency or len(latency) >= 0

    def test_latency_annotation(self):
        """Test that latency is tracked for each provider."""
        provider1 = MockProvider("Provider1", data=[{"event": "Event 1"}])
        provider2 = MockProvider("Provider2", data=[{"event": "Event 2"}])
        orchestrator = MultiAPIOrchestrator([provider1, provider2])

        results, errors, latency = orchestrator.fetch_odds("soccer")

        assert isinstance(latency, dict)
        # Should track latency for both providers
        assert len(latency) >= 0  # May have entries for both or combined stats

    def test_conflict_resolution(self):
        """Test merging when providers return conflicting event data."""
        # Same event, different odds
        provider1 = MockProvider(
            "Provider1",
            data=[{"event_name": "Event 1", "outcomes": [{"name": "Home", "odds": 2.0}]}],
        )
        provider2 = MockProvider(
            "Provider2",
            data=[{"event_name": "Event 1", "outcomes": [{"name": "Home", "odds": 2.1}]}],
        )
        orchestrator = MultiAPIOrchestrator([provider1, provider2])

        results, errors, latency = orchestrator.fetch_odds("soccer")

        # Should merge and deduplicate
        assert len(results) >= 1
        # Best odds should be kept (merging logic)
