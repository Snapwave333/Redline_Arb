"""
Injury and lineup change signal detection system.
Monitors for significant changes that may affect odds.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta

from src.metadata_providers.sports_open_data import SportsOpenDataProvider
from src.metadata_providers.thesportsdb import TheSportsDBProvider

logger = logging.getLogger(__name__)


class InjurySignalDetector:
    """Detects injury-related signals that may affect arbitrage opportunities."""

    def __init__(self):
        """Initialize injury signal detector."""
        self.metadata_providers = [SportsOpenDataProvider(), TheSportsDBProvider()]
        self.recent_injuries = defaultdict(list)  # team -> [injuries]
        self.injury_cache_ttl = 3600  # TODO(redline): configuration attribute for injury cache TTL

    def check_injury_signals(self, team: str, league: str = None) -> dict:
        """
        Check for recent injury signals for a team.

        Args:
            team: Team name
            league: Optional league name

        Returns:
            Signal dictionary with severity and details
        """
        signals = {
            "has_injuries": False,
            "critical_injuries": 0,
            "key_player_injuries": [],
            "severity": "none",  # none, low, medium, high
            "recommendation": "proceed",
        }

        injuries = []

        # Check all metadata providers
        for provider in self.metadata_providers:
            try:
                provider_injuries = provider.get_injuries(team=team, league=league)
                injuries.extend(provider_injuries)
            except Exception as e:
                logger.warning(f"Error fetching injuries from {provider}: {e}")

        if not injuries:
            return signals

        # Filter recent injuries (within last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_injuries = [inj for inj in injuries if inj.reported_date >= recent_cutoff]

        if not recent_injuries:
            return signals

        signals["has_injuries"] = True
        signals["key_player_injuries"] = [
            {"player": inj.player_name, "injury": inj.injury_type, "status": inj.status}
            for inj in recent_injuries
        ]

        # Count critical injuries (out status)
        critical = [inj for inj in recent_injuries if inj.status.lower() == "out"]
        signals["critical_injuries"] = len(critical)

        # Determine severity
        if len(critical) >= 2:
            signals["severity"] = "high"
            signals["recommendation"] = "caution"
        elif len(critical) == 1:
            signals["severity"] = "medium"
            signals["recommendation"] = "review"
        else:
            signals["severity"] = "low"
            signals["recommendation"] = "monitor"

        return signals

    def get_lineup_change_signals(self, match_id: str = None, team: str = None) -> dict:
        """
        Get lineup change signals.

        Args:
            match_id: Optional match ID
            team: Optional team name

        Returns:
            Signal dictionary
        """
        signals = {
            "has_changes": False,
            "recent_changes": [],
            "change_count": 0,
            "severity": "none",
        }

        changes = []

        for provider in self.metadata_providers:
            try:
                provider_changes = provider.get_lineup_changes(match_id=match_id)
                if team:
                    provider_changes = [c for c in provider_changes if c.team == team]
                changes.extend(provider_changes)
            except Exception as e:
                logger.warning(f"Error fetching lineup changes: {e}")

        if not changes:
            return signals

        # Filter recent changes (within last 2 hours before match)
        recent_cutoff = datetime.now() - timedelta(hours=2)
        recent_changes = [ch for ch in changes if ch.timestamp >= recent_cutoff]

        if recent_changes:
            signals["has_changes"] = True
            signals["change_count"] = len(recent_changes)
            signals["recent_changes"] = [
                {"player": ch.player_name, "change_type": ch.change_type, "reason": ch.reason}
                for ch in recent_changes
            ]

            if len(recent_changes) >= 2:
                signals["severity"] = "high"
            elif len(recent_changes) == 1:
                signals["severity"] = "medium"
            else:
                signals["severity"] = "low"

        return signals
