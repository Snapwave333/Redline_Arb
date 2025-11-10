"""
Base interface for metadata providers (team info, schedules, standings).
Metadata providers augment odds data with contextual information.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TeamMetadata:
    """Team metadata information."""

    team_id: str
    name: str
    league: str
    country: str
    logo_url: str | None = None
    website: str | None = None


@dataclass
class MatchMetadata:
    """Match/schedule metadata."""

    match_id: str
    home_team: str
    away_team: str
    league: str
    start_time: datetime
    venue: str | None = None
    referee: str | None = None
    status: str = "scheduled"  # scheduled, live, finished, cancelled


@dataclass
class InjuryReport:
    """Injury report for a team."""

    team: str
    player_name: str
    injury_type: str
    status: str  # out, doubtful, questionable
    reported_date: datetime
    expected_return: datetime | None = None


@dataclass
class LineupChange:
    """Lineup change information."""

    match_id: str
    team: str
    player_name: str
    position: str
    change_type: str  # added, removed, position_change
    timestamp: datetime
    reason: str | None = None


class MetadataProvider(ABC):
    """Abstract base class for metadata providers."""

    @abstractmethod
    def get_team_metadata(self, team_name: str, league: str = None) -> TeamMetadata | None:
        """Get metadata for a team."""

    @abstractmethod
    def get_upcoming_matches(self, sport: str, days_ahead: int = 7) -> list[MatchMetadata]:
        """Get upcoming match schedules."""

    @abstractmethod
    def get_injuries(self, team: str = None, league: str = None) -> list[InjuryReport]:
        """Get injury reports."""

    @abstractmethod
    def get_lineup_changes(self, match_id: str = None) -> list[LineupChange]:
        """Get recent lineup changes."""
