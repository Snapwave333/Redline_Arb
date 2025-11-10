"""Integration tests for API providers."""

import pytest

from src.api_providers.sofascore_scraper import SofaScoreScraperProvider


class TestSofaScoreScraperProvider:
    """Integration tests for SofaScore scraper provider."""

    def test_init(self):
        """Test provider initialization."""
        provider = SofaScoreScraperProvider(api_key="test", enabled=True, priority=1)
        assert provider.enabled is True
        assert provider.priority == 1

    def test_get_provider_name(self):
        """Test provider name."""
        provider = SofaScoreScraperProvider(api_key="test", enabled=True, priority=1)
        assert "sofascore" in provider.get_provider_name().lower()

    @pytest.mark.skip(reason="Requires network access - run manually")
    def test_fetch_odds_real(self):
        """Test fetching real odds from SofaScore (requires network)."""
        provider = SofaScoreScraperProvider(api_key="test", enabled=True, priority=1)
        results = provider.fetch_odds("soccer")

        # Results may be empty if no data available
        assert isinstance(results, list)

    def test_is_enabled(self):
        """Test enabled status."""
        provider = SofaScoreScraperProvider(api_key="test", enabled=True, priority=1)
        assert provider.is_enabled() is True

        provider.enabled = False
        assert provider.is_enabled() is False
