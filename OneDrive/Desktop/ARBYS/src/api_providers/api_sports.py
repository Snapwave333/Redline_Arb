"""
API-Sports provider implementation.
Free plan: 100 requests per day (resets at 00:00 UTC)

Documentation: https://www.api-sports.io/documentation
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from src.api_providers.base import OddsAPIProvider

logger = logging.getLogger(__name__)


class DailyRateLimiter:
    """Tracks daily API requests and enforces 100 requests/day limit."""

    def __init__(self, cache_file: str = None):
        """
        Initialize daily rate limiter.

        Args:
            cache_file: Path to file to store daily request count
        """
        if cache_file is None:
            # Default to config directory
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            cache_file = str(config_dir / "api_sports_requests.json")

        self.cache_file = cache_file
        self.max_requests_per_day = 100
        self._load_request_count()

    def _load_request_count(self):
        """Load current request count from cache file."""
        self.request_count = 0
        self.last_request_date = None

        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file) as f:
                    data = json.load(f)
                    stored_date = data.get("date", "")
                    stored_count = data.get("count", 0)

                    # Check if stored date is today (UTC)
                    today_utc = datetime.now(timezone.utc).date().isoformat()

                    if stored_date == today_utc:
                        self.request_count = stored_count
                        self.last_request_date = stored_date
                    else:
                        # Different day, reset counter
                        self.request_count = 0
                        self.last_request_date = today_utc
            except Exception as e:
                logger.warning(f"Error loading API-Sports request count: {e}")
                self._reset_for_new_day()
        else:
            self._reset_for_new_day()

    def _reset_for_new_day(self):
        """Reset counter for new UTC day."""
        self.last_request_date = datetime.now(timezone.utc).date().isoformat()
        self.request_count = 0
        self._save_request_count()

    def _save_request_count(self):
        """Save current request count to cache file."""
        try:
            data = {"date": self.last_request_date, "count": self.request_count}
            with open(self.cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving API-Sports request count: {e}")

    def can_make_request(self) -> bool:
        """
        Check if we can make a request (under daily limit).

        Returns:
            True if under limit, False if limit reached
        """
        # Check if new UTC day
        today_utc = datetime.now(timezone.utc).date().isoformat()
        if self.last_request_date != today_utc:
            self._reset_for_new_day()

        return self.request_count < self.max_requests_per_day

    def record_request(self):
        """Record that a request was made."""
        # Check if new UTC day
        today_utc = datetime.now(timezone.utc).date().isoformat()
        if self.last_request_date != today_utc:
            self._reset_for_new_day()

        self.request_count += 1
        self._save_request_count()

    def get_remaining_requests(self) -> int:
        """Get number of remaining requests today."""
        if not self.can_make_request():
            return 0
        return self.max_requests_per_day - self.request_count

    def get_reset_time(self) -> datetime | None:
        """Get UTC datetime when the daily limit resets."""
        now = datetime.now(timezone.utc)
        tomorrow = (now.date() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return tomorrow.replace(tzinfo=timezone.utc)


class APISportsProvider(OddsAPIProvider):
    """API-Sports provider (free plan: 100 requests/day)."""

    BASE_URL = "https://api.api-sports.io/v3"

    # Sport mapping from our sport names to API-Sports IDs
    SPORT_MAPPING = {
        "soccer": "football",
        "basketball": "basketball",
        "baseball": "baseball",
        "hockey": "hockey",
        "tennis": "tennis",
        "americanfootball": "americanfootball",
        "cricket": "cricket",
        "rugby": "rugby",
    }

    def __init__(self, api_key: str, enabled: bool = True, priority: int = 1):
        """
        Initialize API-Sports provider.

        Args:
            api_key: API-Sports API key (required)
            enabled: Whether provider is enabled
            priority: Priority level
        """
        super().__init__(api_key, enabled, priority)
        self.rate_limiter = DailyRateLimiter()

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "api_sports"

    def fetch_odds(self, sport: str = "soccer", **kwargs) -> list[dict]:
        """
        Fetch odds data from API-Sports.

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional parameters

        Returns:
            List of standardized event dictionaries
        """
        if not self.enabled:
            return []

        if not self.api_key:
            logger.error("API-Sports API key not configured")
            return []

        # Check rate limit
        if not self.rate_limiter.can_make_request():
            reset_time = self.rate_limiter.get_reset_time()
            logger.warning(
                f"API-Sports daily limit reached (100 requests/day). " f"Resets at {reset_time} UTC"
            )
            return []

        # Map sport name to API-Sports sport
        api_sport = self.SPORT_MAPPING.get(sport.lower(), "football")

        # API-Sports uses /odds endpoint
        url = f"{self.BASE_URL}/odds"

        params = {"sport": api_sport}

        # Add date parameter for upcoming matches (default to today)
        if "date" not in kwargs:
            params["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        else:
            params["date"] = kwargs["date"]

        headers = {
            "x-apisports-key": self.api_key,  # API-Sports uses this header format
        }

        try:
            start_time = time.time()
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response_time = time.time() - start_time

            # Record the request
            self.rate_limiter.record_request()

            if response.status_code == 200:
                data = response.json()
                results = self.normalize_response(data)
                self.update_health(success=True, response_time=response_time)
                return results
            elif response.status_code == 429:
                # Rate limit exceeded
                logger.error("API-Sports rate limit exceeded")
                self.update_health(
                    success=False,
                    response_time=response_time,
                    error=f"Rate limit: {response.status_code}",
                )
                return []
            elif response.status_code == 401:
                # Invalid API key
                logger.error("API-Sports API key invalid")
                self.update_health(
                    success=False, response_time=response_time, error="Invalid API key"
                )
                return []
            else:
                logger.error(
                    f"API-Sports request failed: {response.status_code} - {response.text[:200]}"
                )
                self.update_health(
                    success=False, response_time=response_time, error=f"HTTP {response.status_code}"
                )
                return []

        except Exception as e:
            logger.error(f"Error fetching odds from API-Sports: {str(e)}")
            self.update_health(success=False, error=str(e))
            return []

    def normalize_response(self, raw_data: Any) -> list[dict]:
        """
        Normalize API-Sports response to standard format.

        Args:
            raw_data: Raw JSON response from API-Sports

        Returns:
            List of standardized event dictionaries
        """
        if not raw_data or "response" not in raw_data:
            return []

        events = []

        for fixture in raw_data.get("response", []):
            try:
                fixture_data = fixture.get("fixture", {})
                teams = fixture.get("teams", {})
                bookmakers = fixture.get("bookmakers", [])

                event_name = f"{teams.get('home', {}).get('name', 'Team A')} vs {teams.get('away', {}).get('name', 'Team B')}"

                # Extract outcomes from bookmakers
                outcomes = []
                for bookmaker in bookmakers:
                    bookmaker_name = bookmaker.get("name", "Unknown")

                    # Get odds for match result (1X2)
                    bets = bookmaker.get("bets", [])
                    for bet in bets:
                        if bet.get("id") == 1:  # 1X2 market
                            values = bet.get("values", [])
                            for value in values:
                                outcome_name = value.get("odd", "").capitalize()
                                odd = value.get("value")

                                if odd and outcome_name:
                                    # Map 1/X/2 to home/draw/away
                                    if outcome_name.lower() == "1":
                                        outcome_name = teams.get("home", {}).get("name", "Home")
                                    elif outcome_name.lower() == "x":
                                        outcome_name = "Draw"
                                    elif outcome_name.lower() == "2":
                                        outcome_name = teams.get("away", {}).get("name", "Away")

                                    outcomes.append(
                                        {
                                            "event_name": event_name,
                                            "market": "h2h",
                                            "outcome_name": outcome_name,
                                            "odds": float(odd),
                                            "odds_format": "decimal",
                                            "bookmaker": bookmaker_name,
                                        }
                                    )

                if outcomes:
                    # Get commence time
                    commence_time = fixture_data.get("date")
                    if commence_time:
                        try:
                            # Parse ISO format datetime
                            dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
                            commence_time = dt.isoformat()
                        except Exception:
                            commence_time = datetime.now(timezone.utc).isoformat()
                    else:
                        commence_time = datetime.now(timezone.utc).isoformat()

                    events.append(
                        {
                            "event_name": event_name,
                            "sport": "soccer",  # Default, could be extracted from fixture
                            "home_team": teams.get("home", {}).get("name", ""),
                            "away_team": teams.get("away", {}).get("name", ""),
                            "commence_time": commence_time,
                            "outcomes": outcomes,
                        }
                    )
            except Exception as e:
                logger.warning(f"Error parsing API-Sports fixture: {e}")
                continue

        return events

    def get_remaining_requests(self) -> int:
        """Get remaining requests for today."""
        return self.rate_limiter.get_remaining_requests()

    def get_reset_time(self) -> datetime | None:
        """Get UTC datetime when daily limit resets."""
        return self.rate_limiter.get_reset_time()
