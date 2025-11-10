"""
TheSportsDB provider - free crowd-sourced sports metadata API.
API: https://www.thesportsdb.com/
"""

import logging
from datetime import datetime, timedelta

import requests

from src.metadata_providers.base import (
    InjuryReport,
    LineupChange,
    MatchMetadata,
    MetadataProvider,
    TeamMetadata,
)

logger = logging.getLogger(__name__)


class TheSportsDBProvider(MetadataProvider):
    """TheSportsDB metadata provider."""

    BASE_URL = "https://www.thesportsdb.com/api/v1/json"

    # TheSportsDB API key (free tier)
    API_KEY = "3"  # Public demo key, users can get their own

    def __init__(self, api_key: str = None):
        """
        Initialize TheSportsDB provider.

        Args:
            api_key: Optional API key (demo key used if not provided)
        """
        self.api_key = api_key or self.API_KEY

    def get_team_metadata(self, team_name: str, league: str = None) -> TeamMetadata | None:
        """Get metadata for a team."""
        try:
            url = f"{self.BASE_URL}/{self.api_key}/searchteams.php"
            params = {"t": team_name}

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("teams"):
                    team_data = data["teams"][0]
                    return TeamMetadata(
                        team_id=team_data.get("idTeam", ""),
                        name=team_data.get("strTeam", team_name),
                        league=team_data.get("strLeague", league or ""),
                        country=team_data.get("strCountry", ""),
                        logo_url=team_data.get("strTeamBadge"),
                        website=team_data.get("strWebsite"),
                    )
        except Exception as e:
            logger.warning(f"Error fetching team metadata from TheSportsDB: {e}")

        return None

    def get_upcoming_matches(self, sport: str, days_ahead: int = 7) -> list[MatchMetadata]:
        """Get upcoming match schedules."""
        matches = []
        try:
            # TheSportsDB uses league IDs, we'll search by league name
            url = f"{self.BASE_URL}/{self.api_key}/eventsseason.php"

            # Map sport to league (simplified - would need league IDs in production)
            sport_map = {
                "soccer": "4328",  # Premier League (example)
                "basketball": "4387",  # NBA (example)
            }

            league_id = sport_map.get(sport.lower())
            if not league_id:
                return matches

            current_season = datetime.now().year
            params = {"id": league_id, "s": f"{current_season}-{current_season+1}"}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for event_data in data.get("events", []):
                    try:
                        date_str = event_data.get("dateEvent", "")
                        time_str = event_data.get("strTime", "00:00:00")
                        start_time = datetime.strptime(
                            f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"
                        )

                        # Only include upcoming matches
                        if start_time > datetime.now() and start_time <= datetime.now() + timedelta(
                            days=days_ahead
                        ):
                            matches.append(
                                MatchMetadata(
                                    match_id=event_data.get("idEvent", ""),
                                    home_team=event_data.get("strHomeTeam", ""),
                                    away_team=event_data.get("strAwayTeam", ""),
                                    league=event_data.get("strLeague", ""),
                                    start_time=start_time,
                                    venue=event_data.get("strVenue"),
                                    status="scheduled",
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Error parsing match data: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Error fetching matches from TheSportsDB: {e}")

        return matches

    def get_injuries(self, team: str = None, league: str = None) -> list[InjuryReport]:
        """Get injury reports - not available in free tier."""
        # TheSportsDB free tier doesn't provide injury data
        logger.debug("Injury reports not available in TheSportsDB free tier")
        return []

    def get_lineup_changes(self, match_id: str = None) -> list[LineupChange]:
        """Get lineup changes - limited in free tier."""
        changes = []
        try:
            if match_id:
                url = f"{self.BASE_URL}/{self.api_key}/lookuplineup.php"
                params = {"id": match_id}

                response = requests.get(url, params=params, timeout=5)

                if response.status_code == 200:
                    # TheSportsDB provides lineups but not change history
                    # Would need to track changes manually
                    # data = response.json()  # Available if needed
                    logger.debug("Lineup changes tracking not fully supported in free tier")
        except Exception as e:
            logger.warning(f"Error fetching lineup from TheSportsDB: {e}")

        return changes
