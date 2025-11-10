"""
Test utilities for API provider testing.
"""

from typing import Any

from src.api_providers.base import OddsAPIProvider


class _TestBaseProvider(OddsAPIProvider):
    """Base provider class for testing with default normalize_response implementation."""

    def __init__(
        self,
        name: str = "test_provider",
        api_key: str = "test",
        enabled: bool = True,
        priority: int = 1,
        data: list[dict] = None,
    ):
        """
        Initialize test provider.

        Args:
            name: Provider name
            api_key: API key (not used for tests)
            enabled: Whether enabled
            priority: Priority level
            data: Optional test data to return
        """
        self._name = name
        self._test_data = data or []
        super().__init__(api_key=api_key, enabled=enabled, priority=priority)

    def get_provider_name(self) -> str:
        """Return provider name."""
        return self._name

    def fetch_odds(self, sport: str, **kwargs) -> list[dict]:
        """Return test data."""
        return self._test_data

    def normalize_response(self, raw_data: Any) -> list[dict]:
        """
        Normalize response to standard format.

        Args:
            raw_data: Raw response data (dict or list)

        Returns:
            List of standardized event dictionaries
        """
        if isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, dict):
            # Extract events if present
            events = raw_data.get("events", [])
            if events:
                return events
            # If it's a single event dict, wrap it
            if "event" in raw_data or "event_name" in raw_data:
                return [raw_data]
            # Otherwise return empty
            return []
        return []
