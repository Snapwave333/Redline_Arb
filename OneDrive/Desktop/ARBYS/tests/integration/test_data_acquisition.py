"""Integration tests for data acquisition."""

from unittest.mock import Mock

import pytest

from src.data_acquisition import OddsDataFetcher, OrchestratedDataFetcher


class TestOddsDataFetcher:
    """Integration tests for OddsDataFetcher."""

    def test_init(self):
        """Test fetcher initialization."""
        fetcher = OddsDataFetcher(api_key="test")
        assert fetcher.api_key == "test"

    @pytest.mark.skip(reason="Requires API key and network access")
    def test_fetch_odds_real(self):
        """Test fetching real odds (requires API key)."""
        fetcher = OddsDataFetcher(api_key="test")
        results = fetcher.fetch_odds("soccer")
        assert isinstance(results, list)


class TestOrchestratedDataFetcher:
    """Integration tests for OrchestratedDataFetcher."""

    def test_init_with_orchestrator(self):
        """Test initialization with orchestrator."""
        from unittest.mock import MagicMock

        orchestrator = MagicMock()
        fetcher = OrchestratedDataFetcher(orchestrator)
        assert fetcher.orchestrator == orchestrator

    def test_fetch_odds_with_orchestrator(self):
        """Test fetching odds via orchestrator."""
        import os

        # Use OrchestratorStub in TEST_MODE
        if os.getenv("TEST_MODE") == "1":
            from tests.utils.orchestrator_stub import OrchestratorStub

            orchestrator = OrchestratorStub()
            fetcher = OrchestratedDataFetcher(orchestrator)
            results = fetcher.fetch_odds_sync("soccer")
            assert isinstance(results, list)
        else:
            from src.data_orchestrator import MultiAPIOrchestrator

            mock_orchestrator = Mock(spec=MultiAPIOrchestrator)
            mock_orchestrator.fetch_odds.return_value = ([{"event": "Test"}], [], {})
            fetcher = OrchestratedDataFetcher(mock_orchestrator)
            results = fetcher.fetch_odds_sync("soccer")
            assert isinstance(results, list)
            mock_orchestrator.fetch_odds.assert_called_once_with("soccer")
