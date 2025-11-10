"""
Sportradar API provider implementation.
Note: Requires Sportradar API credentials and subscription.
"""

import logging
import time
from datetime import datetime

import requests

from src.api_providers.base import OddsAPIProvider

logger = logging.getLogger(__name__)


# TODO(redline): disabled provider (planned re-enable) - paid service, disabled in production but kept for future use
class SportradarAPIProvider(OddsAPIProvider):
    """
    Provider implementation for Sportradar API.

    Sportradar offers comprehensive sports data including odds.
    This provider requires:
    - Sportradar API key (subscription required)
    - API access level (free tier may have limited endpoints)

    Documentation: https://sportradar.com/us/developers/
    """

    def __init__(
        self,
        api_key: str,
        enabled: bool = True,
        priority: int = 1,
        api_base_url: str = "https://api.sportradar.com",
    ):
        """
        Initialize Sportradar API provider.

        Args:
            api_key: Sportradar API key
            enabled: Whether provider is enabled
            priority: Priority level
            api_base_url: Base URL for API (may vary by region)
        """
        super().__init__(api_key, enabled, priority)
        self.api_base_url = api_base_url.rstrip("/")
        # Sportradar uses different API versions - odds typically in v2 or v3
        self.api_version = "v2"  # Adjust based on subscription

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "sportradar"

    def fetch_odds(self, sport: str = "soccer", **kwargs) -> list[dict]:
        """
        Fetch odds data from Sportradar API.

        Args:
            sport: Sport to fetch odds for (sportradar uses different keys)
            **kwargs: Additional parameters

        Returns:
            List of standardized event dictionaries
        """
        if not self.enabled:
            return []

        # Map sport names to Sportradar format
        sport_map = {
            "soccer": "soccer",
            "basketball": "basketball",
            "baseball": "baseball",
            "hockey": "icehockey",
            "tennis": "tennis",
        }
        sportradar_sport = sport_map.get(sport.lower(), sport.lower())

        # Sportradar odds endpoint structure (example)
        # Actual endpoint may vary based on subscription level
        url = f"{self.api_base_url}/{sportradar_sport}/odds/{self.api_version}/events"

        params = {"api_key": self.api_key, "format": "json"}

        # Add region if specified (e.g., 'us', 'eu')
        if "regions" in kwargs:
            # Sportradar may use different region parameters
            pass

        start_time = time.time()

        try:
            response = requests.get(url, params=params, timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                normalized = self.normalize_response(data)
                self.update_health(True, response_time)
                return normalized
            elif response.status_code == 401:
                error_msg = "Unauthorized: Invalid API key or subscription expired"
                logger.error(error_msg)
                self.update_health(False, response_time, error_msg)
                return []
            elif response.status_code == 403:
                error_msg = "Forbidden: API key does not have access to this endpoint"
                logger.error(error_msg)
                self.update_health(False, response_time, error_msg)
                return []
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded: Too many requests"
                logger.error(error_msg)
                self.update_health(False, response_time, error_msg)
                return []
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text[:200]}"
                logger.error(error_msg)
                self.update_health(False, response_time, error_msg)
                return []

        except requests.exceptions.Timeout:
            error_msg = "Request timeout: Sportradar API did not respond"
            response_time = time.time() - start_time
            logger.error(error_msg)
            self.update_health(False, response_time, error_msg)
            return []
        except Exception as e:
            error_msg = f"Error fetching odds: {str(e)}"
            response_time = time.time() - start_time
            logger.error(error_msg)
            self.update_health(False, response_time, error_msg)
            return []

    def normalize_response(self, raw_data: dict) -> list[dict]:
        """
        Normalize Sportradar API response to standard format.

        Sportradar API structure varies by endpoint and subscription level.
        This is a generalized parser - adjust based on actual API response.

        Args:
            raw_data: Raw API response

        Returns:
            List of standardized event dictionaries
        """
        events = []

        # Sportradar typically returns events in different structures
        # Common patterns:
        # 1. {'events': [...]} or {'sport_events': [...]}
        # 2. Direct array of events

        event_list = []

        if isinstance(raw_data, dict):
            # Try common keys
            if "events" in raw_data:
                event_list = raw_data["events"]
            elif "sport_events" in raw_data:
                event_list = raw_data["sport_events"]
            elif "data" in raw_data:
                event_list = raw_data["data"]
            else:
                # May be a single event
                event_list = [raw_data]
        elif isinstance(raw_data, list):
            event_list = raw_data

        for event_data in event_list:
            try:
                # Extract event information
                # Sportradar field names vary - adjust based on actual API
                # event_id = event_data.get('id', event_data.get('event_id', ''))  # Available if needed
                sport = event_data.get("sport", {}).get("name", "Unknown")

                # Extract teams/competitors
                competitors = event_data.get("competitors", event_data.get("teams", []))
                home_team = ""
                away_team = ""

                if competitors and len(competitors) >= 2:
                    # Usually ordered as home/away
                    home_team = competitors[0].get("name", competitors[0].get("team", ""))
                    away_team = competitors[1].get("name", competitors[1].get("team", ""))

                # Extract commence time
                commence_time = event_data.get("scheduled", event_data.get("start_time", ""))
                if commence_time:
                    # Sportradar may return ISO format or Unix timestamp
                    try:
                        # Try parsing as ISO
                        from dateutil import parser

                        dt = parser.parse(commence_time)
                        commence_time = dt.isoformat()
                    except Exception:
                        pass

                # Extract odds/markets
                outcomes = []

                # Sportradar odds structure varies - adjust based on actual API
                markets = event_data.get("markets", event_data.get("odds", []))

                if not markets:
                    # Try alternative structure
                    markets = event_data.get("bookmakers", [])

                for market_data in markets:
                    # Extract bookmaker
                    bookmaker_name = market_data.get("bookmaker", {}).get(
                        "name", market_data.get("bookmaker_name", "Unknown")
                    )

                    # Extract market type
                    market_type = market_data.get("market_type", market_data.get("type", "h2h"))

                    # Extract outcomes
                    market_outcomes = market_data.get("outcomes", market_data.get("selections", []))

                    for outcome_data in market_outcomes:
                        outcome_name = outcome_data.get("name", outcome_data.get("label", ""))
                        # Sportradar may return decimal or fractional odds
                        odds_value = outcome_data.get("odds", outcome_data.get("price", 0))

                        # Convert to decimal if needed
                        if isinstance(odds_value, str):
                            # May be fractional like "5/2"
                            try:
                                if "/" in odds_value:
                                    num, den = odds_value.split("/")
                                    odds_value = float(num) / float(den) + 1
                                else:
                                    odds_value = float(odds_value)
                            except Exception:
                                odds_value = 0

                        if odds_value > 0:
                            outcomes.append(
                                {
                                    "event_name": f"{sport} - {home_team} vs {away_team}",
                                    "market": market_type,
                                    "outcome_name": outcome_name,
                                    "odds": float(odds_value),
                                    "odds_format": "decimal",
                                    "bookmaker": bookmaker_name,
                                }
                            )

                if outcomes:
                    events.append(
                        {
                            "event_name": f"{sport} - {home_team} vs {away_team}",
                            "sport": sport,
                            "home_team": home_team,
                            "away_team": away_team,
                            "commence_time": commence_time or datetime.now().isoformat(),
                            "outcomes": outcomes,
                        }
                    )

            except Exception as e:
                logger.warning(f"Error parsing Sportradar event: {e}")
                continue

        return events

    def get_available_sports(self) -> list[str]:
        """
        Get list of available sports from Sportradar API.

        Note: Sportradar may require a different endpoint for this.

        Returns:
            List of sport keys
        """
        # Sportradar may not have a simple sports list endpoint
        # Common sports based on typical Sportradar coverage:
        return [
            "soccer",
            "basketball",
            "baseball",
            "hockey",
            "tennis",
            "football",
            "cricket",
            "rugby",
            "golf",
            "boxing",
        ]

    def test_connection(self) -> dict[str, any]:
        """
        Test connection to Sportradar API.

        Returns:
            Dictionary with test results
        """
        try:
            # Try a simple endpoint (adjust based on Sportradar API)
            # Common test endpoint: version info or health check
            test_url = f"{self.api_base_url}/version"
            response = requests.get(test_url, params={"api_key": self.api_key}, timeout=5)

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "status_code": response.status_code,
                }
            else:
                return {
                    "success": False,
                    "message": f"API returned status {response.status_code}",
                    "status_code": response.status_code,
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "status_code": None,
            }
