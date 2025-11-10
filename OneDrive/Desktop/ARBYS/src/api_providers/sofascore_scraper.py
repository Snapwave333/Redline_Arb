"""
SofaScore scraper provider implementation.
Scrapes free, unlimited odds data from SofaScore's public JSON endpoints.

WARNING: This uses undocumented endpoints that may change without notice.
Use responsibly with rate limiting and caching.

Legal/TOS Note: Using undocumented endpoints may violate SofaScore's Terms of Service.
This is provided for educational/research purposes. Review legal implications in your jurisdiction.
"""

import hashlib
import json
import logging
import random
import time
from datetime import datetime
from threading import Lock
from typing import Any

import requests

from src.api_providers.base import OddsAPIProvider

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter with exponential backoff."""

    def __init__(self, max_requests_per_second: float = 2.0, backoff_factor: float = 2.0):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_second: Maximum requests per second
            backoff_factor: Factor for exponential backoff on failures
        """
        self.max_requests_per_second = max_requests_per_second
        self.min_delay = 1.0 / max_requests_per_second
        self.backoff_factor = backoff_factor
        self.last_request_time = 0.0
        self.consecutive_failures = 0
        self.lock = Lock()

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time

            # Apply backoff if we've had failures
            delay = self.min_delay * (self.backoff_factor**self.consecutive_failures)

            if elapsed < delay:
                sleep_time = delay - elapsed
                time.sleep(sleep_time)

            self.last_request_time = time.time()

    def record_success(self):
        """Record a successful request."""
        with self.lock:
            self.consecutive_failures = 0

    def record_failure(self):
        """Record a failed request."""
        with self.lock:
            self.consecutive_failures += 1


class SimpleCache:
    """Simple in-memory cache with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.cache = {}
        self.ttl = ttl_seconds
        self.lock = Lock()

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                else:
                    del self.cache[key]
            return None

    def set(self, key: str, value: Any):
        """Set value in cache."""
        with self.lock:
            self.cache[key] = (value, time.time())

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()


class SofaScoreScraperProvider(OddsAPIProvider):
    """
    Scraper provider for SofaScore using undocumented JSON endpoints.

    This provider:
    - Uses SofaScore's public JSON endpoints (reverse-engineered)
    - Implements rate limiting and caching
    - Rotates user agents
    - Normalizes data to ARBYS standard format

    WARNING: Undocumented endpoints may change. Use with caution.
    """

    # Common user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ]

    # SofaScore API base URL (undocumented, may change)
    API_BASE_URL = "https://api.sofascore.com/api/v1"

    def __init__(
        self,
        api_key: str = "scraper",
        enabled: bool = True,
        priority: int = 1,
        cache_ttl: int = 300,
        max_requests_per_second: float = 2.0,
        use_headless_browser: bool = False,
    ):
        """
        Initialize SofaScore scraper provider.

        Args:
            api_key: Not used for scraping, kept for interface compatibility
            enabled: Whether provider is enabled
            priority: Priority level (lower = higher priority)
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
            max_requests_per_second: Max requests per second (default: 2.0)
            use_headless_browser: Whether to use Playwright (not implemented yet)
        """
        super().__init__(api_key, enabled, priority)
        self.cache = SimpleCache(ttl_seconds=cache_ttl)
        self.rate_limiter = RateLimiter(max_requests_per_second=max_requests_per_second)
        self.use_headless_browser = use_headless_browser
        self.session = requests.Session()

        # Sport ID mapping (SofaScore uses numeric sport IDs)
        self.sport_id_map = {
            "soccer": 1,
            "basketball": 5,
            "tennis": 6,
            "hockey": 4,
            "baseball": 3,
            "football": 16,  # American football
            "cricket": 19,
            "rugby": 13,
        }

    def get_provider_name(self) -> str:
        """Return provider identifier."""
        return "sofascore_scraper"

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers with random user agent."""
        user_agent = random.choice(self.USER_AGENTS)
        return {
            "User-Agent": user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
        }

    def _get_cache_key(self, sport: str, **kwargs) -> str:
        """Generate cache key for request."""
        key_data = f"{sport}_{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def fetch_odds(self, sport: str = "soccer", **kwargs) -> list[dict]:
        """
        Fetch odds data from SofaScore.

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional parameters (date, league_id, etc.)

        Returns:
            List of standardized event dictionaries
        """
        if not self.enabled:
            return []

        # Check cache first
        cache_key = self._get_cache_key(sport, **kwargs)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for {sport}")
            return cached_data

        # Respect rate limits
        self.rate_limiter.wait_if_needed()

        start_time = time.time()

        try:
            # Get sport ID
            sport_id = self.sport_id_map.get(sport.lower(), 1)

            # Get date (default: today)
            date_str = kwargs.get("date")
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")

            # Fetch events for the sport and date
            events_data = self._fetch_events(sport_id, date_str)

            if not events_data:
                self.rate_limiter.record_failure()
                response_time = time.time() - start_time
                self.update_health(False, response_time, "No events found")
                return []

            # Fetch odds for each event
            normalized_events = []
            for event_data in events_data[:50]:  # Limit to 50 events per request
                try:
                    event_id = event_data.get("id")
                    if event_id:
                        odds_data = self._fetch_event_odds(event_id)
                        if odds_data:
                            normalized = self.normalize_response(
                                {"event": event_data, "odds": odds_data}
                            )
                            if normalized:
                                normalized_events.extend(normalized)
                        # Small delay between event requests
                        time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Error fetching odds for event {event_data.get('id')}: {e}")
                    continue

            # Cache results
            self.cache.set(cache_key, normalized_events)
            self.rate_limiter.record_success()
            response_time = time.time() - start_time
            self.update_health(True, response_time)

            return normalized_events

        except Exception as e:
            error_msg = f"Error fetching odds: {str(e)}"
            logger.error(error_msg)
            response_time = time.time() - start_time
            self.rate_limiter.record_failure()
            self.update_health(False, response_time, error_msg)
            return []

    def _fetch_events(self, sport_id: int, date_str: str) -> list[dict]:
        """
        Fetch events list for a sport and date.

        Args:
            sport_id: SofaScore sport ID
            date_str: Date string in YYYY-MM-DD format

        Returns:
            List of event dictionaries
        """
        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")

            # SofaScore endpoint format: /sport/{sport_id}/scheduled-events/{date}
            # Date format: YYYY-MM-DD
            url = f"{self.API_BASE_URL}/sport/{sport_id}/scheduled-events/{date_str}"

            response = self.session.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                data = response.json()
                # SofaScore returns events in 'events' key
                return data.get("events", [])
            elif response.status_code == 404:
                logger.warning(f"No events found for sport {sport_id} on {date_str}")
                return []
            else:
                logger.warning(f"Unexpected status code {response.status_code} from SofaScore")
                return []

        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    def _fetch_event_odds(self, event_id: int) -> dict | None:
        """
        Fetch odds for a specific event.

        Args:
            event_id: SofaScore event ID

        Returns:
            Dictionary with odds data, or None if not found
        """
        try:
            # SofaScore odds endpoint: /event/{event_id}/odds/1x2
            # Market ID 1 is typically 1X2 (match result)
            url = f"{self.API_BASE_URL}/event/{event_id}/odds/1"

            response = self.session.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # No odds available for this event
                return None
            else:
                logger.debug(f"Status {response.status_code} for event {event_id} odds")
                return None

        except Exception as e:
            logger.debug(f"Error fetching odds for event {event_id}: {e}")
            return None

    def normalize_response(self, raw_data: dict) -> list[dict]:
        """
        Normalize SofaScore response to standard ARBYS format.

        Args:
            raw_data: Dictionary with 'event' and 'odds' keys

        Returns:
            List of standardized event dictionaries
        """
        events = []

        try:
            event_data = raw_data.get("event", {})
            odds_data = raw_data.get("odds", {})

            if not event_data or not odds_data:
                return []

            # Extract event information
            # event_id = event_data.get('id', '')  # Available if needed
            tournament = event_data.get("tournament", {})
            sport = tournament.get("category", {}).get("sport", {}).get("name", "Unknown")

            # Extract teams
            home_team = event_data.get("homeTeam", {}).get("name", "Home")
            away_team = event_data.get("awayTeam", {}).get("name", "Away")

            # Extract commence time
            start_timestamp = event_data.get("startTimestamp", 0)
            if start_timestamp:
                commence_time = datetime.fromtimestamp(start_timestamp).isoformat()
            else:
                commence_time = datetime.now().isoformat()

            # Extract odds from SofaScore format
            # SofaScore odds structure: {'bookmaker': {...}, 'markets': [{...}]}
            outcomes = []

            # SofaScore returns odds in markets array
            markets = odds_data.get("markets", [])
            for market in markets:
                # Market ID 1 is typically 1X2 (match result)
                if market.get("id") != 1:
                    continue

                # Get bookmakers from market
                bookmakers = market.get("bookmakers", [])

                for bookmaker_data in bookmakers:
                    bookmaker_name = bookmaker_data.get("name", "Unknown")

                    # Get outcomes from bookmaker
                    bookmaker_outcomes = bookmaker_data.get("outcomes", [])

                    # Map SofaScore outcome labels to standard format
                    outcome_mapping = {
                        "1": home_team,  # Home win
                        "2": away_team,  # Away win
                        "X": "Draw",  # Draw
                    }

                    for outcome_data in bookmaker_outcomes:
                        outcome_label = str(outcome_data.get("outcome", ""))
                        odds_value = outcome_data.get("price", 0)

                        # Skip invalid odds
                        if odds_value <= 1.0:
                            continue

                        outcome_name = outcome_mapping.get(outcome_label, outcome_label)

                        outcomes.append(
                            {
                                "event_name": f"{sport} - {home_team} vs {away_team}",
                                "market": "h2h",
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
                        "commence_time": commence_time,
                        "outcomes": outcomes,
                    }
                )

        except Exception as e:
            logger.warning(f"Error normalizing SofaScore data: {e}")

        return events

    def get_available_sports(self) -> list[str]:
        """Get list of available sports."""
        return list(self.sport_id_map.keys())

    def test_connection(self) -> dict[str, any]:
        """
        Test connection to SofaScore.

        Returns:
            Dictionary with test results
        """
        try:
            # Try fetching today's soccer events
            url = f"{self.API_BASE_URL}/sport/1/scheduled-events/{datetime.now().strftime('%Y-%m-%d')}"
            response = self.session.get(url, headers=self._get_headers(), timeout=10)

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
