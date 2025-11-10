"""
OddsPortal scraper - scrapes odds from OddsPortal aggregator site.
WARNING: Web scraping may violate Terms of Service. Use responsibly.
"""

import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseOddsScraper

logger = logging.getLogger(__name__)


class OddsPortalScraper(BaseOddsScraper):
    """Scraper for OddsPortal odds aggregator."""

    BASE_URL = "https://www.oddsportal.com"

    def __init__(self, rate_limit_delay: float = 3.0):
        """
        Initialize OddsPortal scraper.

        Args:
            rate_limit_delay: Delay between requests (default: 3s to be respectful)
        """
        super().__init__(rate_limit_delay)
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

    def get_provider_name(self) -> str:
        """Return scraper identifier."""
        return "oddsportal_scraper"

    def scrape_odds(self, sport: str = "soccer", **kwargs) -> list[dict]:
        """
        Scrape odds from OddsPortal.

        Args:
            sport: Sport to scrape (mapped to OddsPortal sport URLs)
            **kwargs: Additional parameters

        Returns:
            List of standardized event dictionaries
        """
        self._wait_for_rate_limit()

        # Map sport names to OddsPortal URLs
        sport_map = {
            "soccer": "soccer",
            "basketball": "basketball",
            "tennis": "tennis",
            "hockey": "hockey",
            "baseball": "baseball",
        }

        sport_path = sport_map.get(sport.lower(), "soccer")
        url = f"{self.BASE_URL}/{sport_path}/"

        events = []

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")

                # Find match rows (structure may vary - this is a template)
                match_rows = soup.find_all("tr", class_=re.compile(r"match"))

                for row in match_rows:
                    try:
                        event_data = self._parse_match_row(row, sport)
                        if event_data:
                            events.append(event_data)
                    except Exception as e:
                        logger.warning(f"Error parsing match row: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping OddsPortal: {e}")

        return events

    def _parse_match_row(self, row, sport: str) -> dict | None:
        """Parse a single match row from OddsPortal."""
        try:
            # Extract team names
            teams = row.find_all("a", class_=re.compile(r"team"))
            if len(teams) < 2:
                return None

            home_team = teams[0].text.strip()
            away_team = teams[1].text.strip()
            event_name = f"{home_team} vs {away_team}"

            # Extract odds (structure varies - simplified example)
            odds_cells = row.find_all("td", class_=re.compile(r"odds"))
            outcomes = []

            # Look for bookmaker odds in cells
            for cell in odds_cells:
                odds_links = cell.find_all("a", class_=re.compile(r"odds"))
                if len(odds_links) >= 3:  # Home, Draw, Away
                    bookmaker = cell.get("data-bookmaker", "Unknown")

                    # Parse odds values (format: "2.10" or "2.10 (1.85)")
                    home_odd = self._parse_odd(odds_links[0].text)
                    draw_odd = self._parse_odd(odds_links[1].text) if len(odds_links) > 1 else None
                    away_odd = self._parse_odd(odds_links[2].text) if len(odds_links) > 2 else None

                    if home_odd:
                        outcomes.append(
                            {
                                "event_name": event_name,
                                "market": "h2h",
                                "outcome_name": home_team,
                                "odds": home_odd,
                                "odds_format": "decimal",
                                "bookmaker": bookmaker,
                            }
                        )

                    if draw_odd:
                        outcomes.append(
                            {
                                "event_name": event_name,
                                "market": "h2h",
                                "outcome_name": "Draw",
                                "odds": draw_odd,
                                "odds_format": "decimal",
                                "bookmaker": bookmaker,
                            }
                        )

                    if away_odd:
                        outcomes.append(
                            {
                                "event_name": event_name,
                                "market": "h2h",
                                "outcome_name": away_team,
                                "odds": away_odd,
                                "odds_format": "decimal",
                                "bookmaker": bookmaker,
                            }
                        )

            if outcomes:
                # Extract match time (if available)
                time_cell = row.find("td", class_=re.compile(r"time"))
                commence_time = datetime.now().isoformat()
                if time_cell:
                    try:
                        time_cell.text.strip()
                        # Parse time format (implementation depends on OddsPortal's format)
                        commence_time = datetime.now().isoformat()  # Simplified
                    except Exception:
                        pass

                return {
                    "event_name": event_name,
                    "sport": sport,
                    "home_team": home_team,
                    "away_team": away_team,
                    "commence_time": commence_time,
                    "outcomes": outcomes,
                }

        except Exception as e:
            logger.warning(f"Error parsing match row: {e}")

        return None

    def _parse_odd(self, text: str) -> float | None:
        """Parse odds value from text."""
        try:
            # Extract number (handles formats like "2.10" or "2.10 (1.85)")
            match = re.search(r"(\d+\.?\d*)", text)
            if match:
                return float(match.group(1))
        except Exception:
            pass
        return None
