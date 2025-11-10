"""
Multi-API orchestrator for managing multiple odds API providers.
"""

import logging
from datetime import datetime

from src.api_providers.base import OddsAPIProvider, ProviderHealth

logger = logging.getLogger(__name__)


class MultiAPIOrchestrator:
    """Orchestrates multiple API providers with failover and data merging."""

    def __init__(
        self,
        providers: list[OddsAPIProvider],
        failover_enabled: bool = True,
        require_all_providers: bool = False,
    ):
        """
        Initialize multi-API orchestrator.

        Args:
            providers: List of API provider instances
            failover_enabled: Enable automatic failover
            require_all_providers: Require all providers to succeed
        """
        self.providers = providers
        self.failover_enabled = failover_enabled
        self.require_all_providers = require_all_providers

        # Sort providers by priority
        self.providers.sort(key=lambda p: p.priority)

    def fetch_odds(self, sport: str, **kwargs) -> tuple[list[dict], list[dict], dict]:
        """
        Fetch odds from all enabled providers with failover support and latency tracking.

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional parameters to pass to providers

        Returns:
            Tuple of (merged_results, errors, latency_stats)
        """
        import time

        results = []
        errors = []
        latency_stats = {}

        # Try each provider in priority order
        for provider in self.providers:
            if not provider.is_enabled():
                continue

            provider_name = provider.get_provider_name()
            start_time = time.time()

            try:
                provider_results = provider.fetch_odds(sport, **kwargs)
                response_time = time.time() - start_time

                # Track latency
                latency_stats[provider_name] = {
                    "response_time": response_time,
                    "success": True,
                    "result_count": len(provider_results) if provider_results else 0,
                }

                if provider_results:
                    results.append(
                        {
                            "provider": provider_name,
                            "data": provider_results,
                            "timestamp": datetime.now().isoformat(),
                            "latency": response_time,
                        }
                    )

                    # If failover enabled and we have results, optionally break
                    if self.failover_enabled and not self.require_all_providers:
                        # Continue to get more data from other providers
                        # But we have at least one successful response
                        pass

            except Exception as e:
                response_time = time.time() - start_time
                error_info = {
                    "provider": provider_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                errors.append(error_info)

                # Track latency even for failures
                latency_stats[provider_name] = {
                    "response_time": response_time,
                    "success": False,
                    "error": str(e),
                }

                logger.warning(f"Provider {provider_name} failed: {str(e)}")

                # Continue to next provider (failover)
                continue

        # Merge results from all providers
        merged_results = self._merge_results(results)

        return merged_results, errors, latency_stats

    def _merge_results(self, provider_results: list[dict]) -> list[dict]:
        """
        Merge and deduplicate results from multiple providers.

        Args:
            provider_results: List of provider result dictionaries

        Returns:
            Merged list of event dictionaries
        """
        if not provider_results:
            return []

        # Group events by unique identifier (sport + teams + commence_time)
        event_map = {}

        for provider_result in provider_results:
            provider_name = provider_result["provider"]
            events = provider_result["data"]

            for event in events:
                # Create unique key for event
                event_key = self._create_event_key(event)

                if event_key not in event_map:
                    # New event - add to map
                    event_map[event_key] = {
                        "event": event,
                        "outcomes": {},
                        "sources": {provider_name},
                    }
                else:
                    # Existing event - merge outcomes
                    event_map[event_key]["sources"].add(provider_name)

                # Merge outcomes, keeping best odds
                for outcome in event.get("outcomes", []):
                    outcome_key = self._create_outcome_key(outcome)

                    if outcome_key not in event_map[event_key]["outcomes"]:
                        event_map[event_key]["outcomes"][outcome_key] = outcome
                    else:
                        # Keep outcome with better (higher) odds
                        existing_odds = event_map[event_key]["outcomes"][outcome_key]["odds"]
                        new_odds = outcome["odds"]

                        if new_odds > existing_odds:
                            event_map[event_key]["outcomes"][outcome_key] = outcome

        # Convert back to list format
        merged_events = []
        for _event_key, event_data in event_map.items():
            event = event_data["event"].copy()
            event["outcomes"] = list(event_data["outcomes"].values())
            event["source_apis"] = list(event_data["sources"])
            merged_events.append(event)

        return merged_events

    def _create_event_key(self, event: dict) -> str:
        """
        Create unique key for event matching.

        Args:
            event: Event dictionary

        Returns:
            Unique key string
        """
        sport = event.get("sport", "unknown")
        home_team = event.get("home_team", "").lower().strip()
        away_team = event.get("away_team", "").lower().strip()
        commence_time = event.get("commence_time", "")

        # Normalize commence_time (remove timezone, round to hour)
        try:
            from dateutil import parser

            dt = parser.parse(commence_time)
            commence_normalized = dt.strftime("%Y-%m-%d-%H")
        except Exception:
            commence_normalized = commence_time

        return f"{sport}|{home_team}|{away_team}|{commence_normalized}"

    def _create_outcome_key(self, outcome: dict) -> str:
        """
        Create unique key for outcome matching.

        Args:
            outcome: Outcome dictionary

        Returns:
            Unique key string
        """
        outcome_name = outcome.get("outcome_name", "").lower().strip()
        market = outcome.get("market", "h2h")
        bookmaker = outcome.get("bookmaker", "").lower().strip()

        return f"{market}|{outcome_name}|{bookmaker}"

    def get_provider_status(self) -> dict[str, ProviderHealth]:
        """
        Get health status of all providers.

        Returns:
            Dictionary mapping provider names to health status
        """
        return {provider.get_provider_name(): provider.get_health() for provider in self.providers}

    def add_provider(self, provider: OddsAPIProvider):
        """
        Add a new provider to the orchestrator.

        Args:
            provider: Provider instance to add
        """
        self.providers.append(provider)
        self.providers.sort(key=lambda p: p.priority)

    def remove_provider(self, provider_name: str):
        """
        Remove a provider from the orchestrator.

        Args:
            provider_name: Name of provider to remove
        """
        self.providers = [p for p in self.providers if p.get_provider_name() != provider_name]
