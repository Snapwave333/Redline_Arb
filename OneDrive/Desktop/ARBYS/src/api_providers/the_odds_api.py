"""
The Odds API provider implementation.
Wraps existing OddsDataFetcher logic into provider interface.
"""

import logging
import time

import requests

from src.api_providers.base import OddsAPIProvider

logger = logging.getLogger(__name__)


# TODO(redline): disabled provider (planned re-enable) - paid service, disabled in production but kept for future use
class TheOddsAPIProvider(OddsAPIProvider):
    """Provider implementation for The Odds API."""

    def __init__(
        self,
        api_key: str,
        enabled: bool = True,
        priority: int = 1,
        api_base_url: str = "https://api.the-odds-api.com/v4",
    ):
        """
        Initialize The Odds API provider.

        Args:
            api_key: The Odds API key
            enabled: Whether provider is enabled
            priority: Priority level
            api_base_url: Base URL for API
        """
        super().__init__(api_key, enabled, priority)
        self.api_base_url = api_base_url.rstrip("/")

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "the_odds_api"

    def fetch_odds(
        self, sport: str = "soccer", regions: list[str] = None, markets: list[str] = None, **kwargs
    ) -> list[dict]:
        """
        Fetch odds data from The Odds API.

        Args:
            sport: Sport to fetch odds for
            regions: List of regions/bookmakers
            markets: List of markets
            **kwargs: Additional parameters

        Returns:
            List of standardized event dictionaries
        """
        if not self.enabled:
            return []

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

        start_time = time.time()

        try:
            response = requests.get(url, params=params, timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                normalized = self.normalize_response(data)
                self.update_health(True, response_time)
                return normalized
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                self.update_health(False, response_time, error_msg)
                return []

        except Exception as e:
            error_msg = f"Error fetching odds: {str(e)}"
            logger.error(error_msg)
            response_time = time.time() - start_time
            self.update_health(False, response_time, error_msg)
            return []

    def normalize_response(self, raw_data: list[dict]) -> list[dict]:
        """
        Normalize The Odds API response to standard format.

        Args:
            raw_data: Raw API response

        Returns:
            List of standardized event dictionaries
        """
        events = []

        for event_data in raw_data:
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
