"""
Sports Open Data provider - free metadata API for team info and schedules.
API: https://sportsopendata.net/
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


class SportsOpenDataProvider(MetadataProvider):
    """Sports Open Data metadata provider."""

    BASE_URL = "https://sportsopendata.net/api/v1"

    def __init__(self, api_key: str = None):
        """
        Initialize Sports Open Data provider.

        Args:
            api_key: Optional API key (many endpoints are free without key)
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get_team_metadata(self, team_name: str, league: str = None) -> TeamMetadata | None:
        """Get metadata for a team."""
        try:
            # Search for team
            url = f"{self.BASE_URL}/teams/search"
            params = {"q": team_name}
            if league:
                params["league"] = league

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    team_data = data["results"][0]
                    return TeamMetadata(
                        team_id=str(team_data.get("id", "")),
                        name=team_data.get("name", team_name),
                        league=team_data.get("league", league or ""),
                        country=team_data.get("country", ""),
                        logo_url=team_data.get("logo"),
                        website=team_data.get("website"),
                    )
        except Exception as e:
            logger.warning(f"Error fetching team metadata from Sports Open Data: {e}")

        return None

    def get_upcoming_matches(self, sport: str, days_ahead: int = 7) -> list[MatchMetadata]:
        """Get upcoming match schedules."""
        matches = []
        try:
            # Map sport name
            sport_map = {
                "soccer": "football",
                "basketball": "basketball",
                "baseball": "baseball",
                "hockey": "hockey",
                "tennis": "tennis",
            }
            api_sport = sport_map.get(sport.lower(), "football")

            url = f"{self.BASE_URL}/matches"
            end_date = datetime.now() + timedelta(days=days_ahead)

            params = {
                "sport": api_sport,
                "date_from": datetime.now().strftime("%Y-%m-%d"),
                "date_to": end_date.strftime("%Y-%m-%d"),
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for match_data in data.get("matches", []):
                    try:
                        start_time = datetime.fromisoformat(
                            match_data["date"].replace("Z", "+00:00")
                        )

                        matches.append(
                            MatchMetadata(
                                match_id=str(match_data.get("id", "")),
                                home_team=match_data.get("home_team", {}).get("name", ""),
                                away_team=match_data.get("away_team", {}).get("name", ""),
                                league=match_data.get("competition", {}).get("name", ""),
                                start_time=start_time,
                                venue=match_data.get("venue"),
                                status=match_data.get("status", "scheduled"),
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Error parsing match data: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Error fetching matches from Sports Open Data: {e}")

        return matches

    def get_injuries(self, team: str = None, league: str = None) -> list[InjuryReport]:
        """Get injury reports."""
        injuries = []
        try:
            url = f"{self.BASE_URL}/injuries"
            params = {}
            if team:
                params["team"] = team
            if league:
                params["league"] = league

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                for injury_data in data.get("injuries", []):
                    try:
                        reported_date = datetime.fromisoformat(
                            injury_data["date"].replace("Z", "+00:00")
                        )

                        expected_return = None
                        if injury_data.get("expected_return"):
                            expected_return = datetime.fromisoformat(
                                injury_data["expected_return"].replace("Z", "+00:00")
                            )

                        injuries.append(
                            InjuryReport(
                                team=injury_data.get("team", ""),
                                player_name=injury_data.get("player", ""),
                                injury_type=injury_data.get("injury", ""),
                                status=injury_data.get("status", "out"),
                                reported_date=reported_date,
                                expected_return=expected_return,
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Error parsing injury data: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Error fetching injuries from Sports Open Data: {e}")

        return injuries

    def get_lineup_changes(self, match_id: str = None) -> list[LineupChange]:
        """Get recent lineup changes."""
        changes = []
        try:
            url = f"{self.BASE_URL}/lineups/changes"
            params = {}
            if match_id:
                params["match_id"] = match_id

            response = self.session.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                for change_data in data.get("changes", []):
                    try:
                        timestamp = datetime.fromisoformat(
                            change_data["timestamp"].replace("Z", "+00:00")
                        )

                        changes.append(
                            LineupChange(
                                match_id=str(change_data.get("match_id", "")),
                                team=change_data.get("team", ""),
                                player_name=change_data.get("player", ""),
                                position=change_data.get("position", ""),
                                change_type=change_data.get("type", "added"),
                                timestamp=timestamp,
                                reason=change_data.get("reason"),
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Error parsing lineup change: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Error fetching lineup changes from Sports Open Data: {e}")

        return changes
