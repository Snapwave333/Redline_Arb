"""
Base scraper interface for web scraping odds from aggregator sites.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseOddsScraper(ABC):
    """Abstract base class for odds scrapers."""

    def __init__(self, rate_limit_delay: float = 2.0):
        """
        Initialize scraper.

        Args:
            rate_limit_delay: Delay between requests in seconds
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return scraper identifier."""

    @abstractmethod
    def scrape_odds(self, sport: str = "soccer", **kwargs) -> list[dict]:
        """
        Scrape odds from the aggregator site.

        Args:
            sport: Sport to scrape odds for
            **kwargs: Additional parameters

        Returns:
            List of standardized event dictionaries with odds
        """

    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        import time

        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    def _normalize_odds_format(self, odds_data: dict) -> dict:
        """
        Normalize scraped odds data to standard format.

        Args:
            odds_data: Raw scraped data

        Returns:
            Normalized event dictionary
        """
        # Base normalization - subclasses can override
        return {
            "event_name": odds_data.get("event_name", ""),
            "sport": odds_data.get("sport", ""),
            "home_team": odds_data.get("home_team", ""),
            "away_team": odds_data.get("away_team", ""),
            "commence_time": odds_data.get("commence_time", datetime.now().isoformat()),
            "outcomes": odds_data.get("outcomes", []),
        }
