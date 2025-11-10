"""
Data acquisition module for fetching odds from APIs.
Supports both single-API and multi-API orchestrator modes.
"""

import logging

import aiohttp
import requests

logger = logging.getLogger(__name__)


class OddsDataFetcher:
    """
    Legacy single-API fetcher for backward compatibility.

    For new implementations, use MultiAPIOrchestrator with provider instances.
    This class is maintained for backward compatibility.
    """

    """Fetches odds data from betting APIs."""

    def __init__(self, api_key: str, api_base_url: str = "https://api.the-odds-api.com/v4"):
        """
        Initialize the odds data fetcher.

        Args:
            api_key: API key for the odds service
            api_base_url: Base URL for the API
        """
        self.api_key = api_key
        self.api_base_url = api_base_url.rstrip("/")
        self.session = None

    async def fetch_odds_async(
        self, sport: str = "soccer", regions: list[str] = None, markets: list[str] = None
    ) -> list[dict]:
        """
        Asynchronously fetch odds data from the API.

        Args:
            sport: Sport to fetch odds for (default: 'soccer')
            regions: List of regions/bookmakers (default: ['us', 'uk'])
            markets: List of markets (default: ['h2h'] for head-to-head)

        Returns:
            List of event dictionaries with odds data
        """
        if regions is None:
            regions = ["us", "uk"]
        if markets is None:
            markets = ["h2h"]

        url = f"{self.api_base_url}/sports/{sport}/odds"

        params = {
            "apiKey": self.api_key,
            "regions": ",".join(regions),
            "markets": ",".join(markets),
            "oddsFormat": "decimal",
        }

        try:
            async with aiohttp.ClientSession() as session:  # noqa: SIM117
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_odds_data(data)
                    else:
                        error_text = await response.text()
                        logger.error(f"API request failed: {response.status} - {error_text}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching odds: {str(e)}")
            return []

    def fetch_odds_sync(
        self, sport: str = "soccer", regions: list[str] = None, markets: list[str] = None
    ) -> list[dict]:
        """
        Synchronously fetch odds data from the API.

        Args:
            sport: Sport to fetch odds for
            regions: List of regions/bookmakers
            markets: List of markets

        Returns:
            List of event dictionaries with odds data
        """
        if regions is None:
            regions = ["us", "uk"]
        if markets is None:
            markets = ["h2h"]

        url = f"{self.api_base_url}/sports/{sport}/odds"

        params = {
            "apiKey": self.api_key,
            "regions": ",".join(regions),
            "markets": ",".join(markets),
            "oddsFormat": "decimal",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._parse_odds_data(data)
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching odds: {str(e)}")
            return []

    def _parse_odds_data(self, api_response: list[dict]) -> list[dict]:
        """
        Parse API response into standardized format.

        Args:
            api_response: Raw API response

        Returns:
            List of standardized event dictionaries
        """
        events = []

        for event_data in api_response:
            event_name = (
                event_data.get("sport_title", "Unknown")
                + " - "
                + event_data.get("home_team", "")
                + " vs "
                + event_data.get("away_team", "")
            )

            # Extract outcomes from bookmakers
            outcomes = []

            for bookmaker in event_data.get("bookmakers", []):
                bookmaker_name = bookmaker.get("title", "Unknown")

                for market in bookmaker.get("markets", []):
                    market_key = market.get("key", "h2h")

                    for outcome in market.get("outcomes", []):
                        outcome_name = outcome.get("name", "")
                        odds = outcome.get("price", 0)

                        if odds > 0:
                            outcomes.append(
                                {
                                    "event_name": event_name,
                                    "market": market_key,
                                    "outcome_name": outcome_name,
                                    "odds": odds,
                                    "odds_format": "decimal",
                                    "bookmaker": bookmaker_name,
                                }
                            )

            if outcomes:
                events.append(
                    {
                        "event_name": event_name,
                        "sport": event_data.get("sport_title", "Unknown"),
                        "home_team": event_data.get("home_team", ""),
                        "away_team": event_data.get("away_team", ""),
                        "commence_time": event_data.get("commence_time", ""),
                        "outcomes": outcomes,
                    }
                )

        return events

    def get_available_sports(self) -> list[str]:
        """
        Get list of available sports from the API.

        Returns:
            List of sport keys
        """
        url = f"{self.api_base_url}/sports"
        params = {"apiKey": self.api_key}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                sports_data = response.json()
                return [sport.get("key", "") for sport in sports_data]
            return []
        except Exception as e:
            logger.error(f"Error fetching sports list: {str(e)}")
            return []


class OrchestratedDataFetcher:
    """
    Wrapper that provides backward-compatible interface to MultiAPIOrchestrator.

    This allows existing code to work with the orchestrator without changes.
    """

    def __init__(self, orchestrator):
        """
        Initialize with orchestrator instance.

        Args:
            orchestrator: MultiAPIOrchestrator instance
        """
        self.orchestrator = orchestrator

    def fetch_odds_sync(self, sport: str = "soccer", **kwargs) -> list[dict]:
        """
        Fetch odds synchronously (backward-compatible interface).

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional parameters

        Returns:
            List of event dictionaries
        """
        result = self.orchestrator.fetch_odds(sport, **kwargs)

        # Handle both old (2-tuple) and new (3-tuple) return signatures
        if len(result) == 3:
            results, errors, latency_stats = result
        else:
            results, errors = result
            latency_stats = {}

        # Log errors but don't fail
        if errors:
            for error in errors:
                logger.warning(f"Provider error: {error['provider']} - {error['error']}")

        # Log latency stats if available
        if latency_stats:
            for provider, stats in latency_stats.items():
                if stats.get("success"):
                    logger.debug(f"{provider} latency: {stats['response_time']:.2f}s")

        return results

    def get_available_sports(self) -> list[str]:
        """
        Get available sports from primary provider.

        Returns:
            List of sport keys
        """
        # Try to get from first enabled provider
        for provider in self.orchestrator.providers:
            if provider.is_enabled() and hasattr(provider, "get_available_sports"):
                try:
                    return provider.get_available_sports()
                except Exception:
                    continue

        return []
