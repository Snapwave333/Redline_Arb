"""
Base interface for odds API providers.
All API providers must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class StandardizedOdds:
    """Standardized format for odds data from any provider."""

    event_id: str
    sport: str
    home_team: str
    away_team: str
    commence_time: str  # ISO format datetime
    outcomes: list[dict[str, Any]]


@dataclass
class ProviderHealth:
    """Health status for an API provider."""

    provider_name: str
    status: str = "unknown"  # "healthy", "degraded", "down", "unknown"
    last_success: str | None = None
    last_error: str | None = None
    success_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority


class OddsAPIProvider(ABC):
    """Abstract base class for all odds API providers."""

    def __init__(self, api_key: str, enabled: bool = True, priority: int = 1):
        """
        Initialize API provider.

        Args:
            api_key: API key for this provider
            enabled: Whether provider is enabled
            priority: Priority level (lower = higher priority)
        """
        self.api_key = api_key
        self.enabled = enabled
        self.priority = priority
        self.health = ProviderHealth(
            provider_name=self.get_provider_name(), enabled=enabled, priority=priority
        )

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Return provider identifier.

        Returns:
            Provider name (e.g., "the_odds_api", "sportradar")
        """

    @abstractmethod
    def fetch_odds(self, sport: str, **kwargs) -> list[dict]:
        """
        Fetch odds data from this provider.

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional provider-specific parameters

        Returns:
            List of standardized event dictionaries
        """

    @abstractmethod
    def normalize_response(self, raw_data: Any) -> list[dict]:
        """
        Normalize provider-specific format to standard format.

        Args:
            raw_data: Raw response from provider API

        Returns:
            List of standardized event dictionaries
        """

    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self.enabled

    def get_health(self) -> ProviderHealth:
        """Get provider health status."""
        return self.health

    def update_health(self, success: bool, response_time: float = 0.0, error: str = None):
        """
        Update provider health metrics.

        Args:
            success: Whether request was successful
            response_time: Response time in seconds
            error: Error message if failed
        """
        now = datetime.now().isoformat()

        if success:
            self.health.last_success = now
            self.health.success_count += 1

            # Update average response time
            total_requests = self.health.success_count + self.health.error_count
            if total_requests == 1:
                self.health.avg_response_time = response_time
            else:
                self.health.avg_response_time = (
                    self.health.avg_response_time * (total_requests - 1) + response_time
                ) / total_requests

            # Update status based on success rate
            success_rate = self.health.success_count / total_requests if total_requests > 0 else 1.0
            if success_rate > 0.95:
                self.health.status = "healthy"
            elif success_rate > 0.80:
                self.health.status = "degraded"
            else:
                self.health.status = "down"
        else:
            self.health.last_error = now
            self.health.error_count += 1

            # Update status based on error rate
            total_requests = self.health.success_count + self.health.error_count
            error_rate = self.health.error_count / total_requests if total_requests > 0 else 0.0

            if error_rate > 0.5:
                self.health.status = "down"
            elif error_rate > 0.2:
                self.health.status = "degraded"
            else:
                self.health.status = "healthy"

        if error:
            self.health.last_error = f"{now}: {error}"
