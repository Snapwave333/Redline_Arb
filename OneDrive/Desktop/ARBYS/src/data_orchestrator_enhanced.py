"""
Enhanced orchestrator with latency comparison and feed mashups.
"""

import logging
from datetime import datetime

from src.api_providers.base import OddsAPIProvider
from src.data_orchestrator import MultiAPIOrchestrator
from src.metadata_providers.base import MetadataProvider
from src.models.probability_model import FeedMashupAnalyzer, ProbabilityModel
from src.signals.injury_signal import InjurySignalDetector

logger = logging.getLogger(__name__)


# TODO(redline): kept for enhanced features - latency tracking and feed mashup analysis (future feature)
class EnhancedMultiAPIOrchestrator(MultiAPIOrchestrator):
    """Enhanced orchestrator with latency tracking, signals, and mashups."""

    def __init__(
        self,
        providers: list[OddsAPIProvider],
        metadata_providers: list[MetadataProvider] = None,
        probability_model: ProbabilityModel = None,
        **kwargs,
    ):
        """
        Initialize enhanced orchestrator.

        Args:
            providers: List of odds API providers
            metadata_providers: Optional list of metadata providers
            probability_model: Optional probability model for feed mashup
            **kwargs: Additional arguments for base orchestrator
        """
        super().__init__(providers, **kwargs)
        self.metadata_providers = metadata_providers or []
        self.probability_model = probability_model
        self.injury_detector = InjurySignalDetector()
        self.latency_history = {}  # provider_name -> [latency_values]

    # TODO(redline): future feature - enhanced odds fetching with analysis
    def fetch_odds_with_analysis(self, sport: str, **kwargs) -> dict:
        """
        Fetch odds with full analysis including latency, signals, and mashups.

        Args:
            sport: Sport to fetch odds for
            **kwargs: Additional parameters

        Returns:
            Comprehensive analysis dictionary
        """
        # Fetch odds with latency tracking
        results, errors, latency_stats = super().fetch_odds(sport, **kwargs)

        # Update latency history
        for provider_name, stats in latency_stats.items():
            if provider_name not in self.latency_history:
                self.latency_history[provider_name] = []
            self.latency_history[provider_name].append(stats["response_time"])
            # Keep only last 100 measurements
            if len(self.latency_history[provider_name]) > 100:
                self.latency_history[provider_name] = self.latency_history[provider_name][-100:]

        # Analyze results with probability model if available
        analyzed_results = results
        mashup_analysis = None

        if self.probability_model and results:
            mashup = FeedMashupAnalyzer(self.probability_model)
            analyzed_results = mashup.analyze_odds_with_model(results)
            mashup_analysis = {
                "model_used": self.probability_model.__class__.__name__,
                "events_analyzed": len(analyzed_results),
                "value_opportunities": sum(
                    1 for event in analyzed_results if event.get("value_discrepancies")
                ),
            }

        # Check for injury/lineup signals
        signal_analysis = self._check_signals(results)

        # Latency comparison
        latency_comparison = self._compare_latencies()

        return {
            "odds_results": analyzed_results,
            "errors": errors,
            "latency_stats": latency_stats,
            "latency_comparison": latency_comparison,
            "signal_analysis": signal_analysis,
            "mashup_analysis": mashup_analysis,
            "timestamp": datetime.now().isoformat(),
        }

    def _check_signals(self, events: list[dict]) -> dict:
        """Check for injury and lineup change signals."""
        signals = {"injuries_detected": [], "lineup_changes": [], "affected_events": []}

        for event in events:
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")

            # Check injuries
            for team in [home_team, away_team]:
                if team:
                    injury_signal = self.injury_detector.check_injury_signals(team)
                    if injury_signal.get("has_injuries"):
                        signals["injuries_detected"].append(
                            {
                                "team": team,
                                "signal": injury_signal,
                                "event": event.get("event_name", ""),
                            }
                        )

            # Check lineup changes
            match_id = event.get("match_id")
            if match_id:
                lineup_signal = self.injury_detector.get_lineup_change_signals(match_id=match_id)
                if lineup_signal.get("has_changes"):
                    signals["lineup_changes"].append(
                        {"event": event.get("event_name", ""), "signal": lineup_signal}
                    )

        # Identify affected events
        affected = []
        for event in events:
            event_name = event.get("event_name", "")
            for injury in signals["injuries_detected"]:
                if injury["event"] == event_name:
                    affected.append(event_name)
                    break
            for change in signals["lineup_changes"]:
                if change["event"] == event_name:
                    if event_name not in affected:
                        affected.append(event_name)
                    break

        signals["affected_events"] = affected

        return signals

    def _compare_latencies(self) -> dict:
        """Compare latencies across providers."""
        comparison = {"providers": {}, "fastest": None, "slowest": None, "avg_latency": {}}

        for provider_name, latencies in self.latency_history.items():
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)

                comparison["providers"][provider_name] = {
                    "avg_latency": avg_latency,
                    "min_latency": min_latency,
                    "max_latency": max_latency,
                    "samples": len(latencies),
                }
                comparison["avg_latency"][provider_name] = avg_latency

        if comparison["avg_latency"]:
            comparison["fastest"] = min(comparison["avg_latency"].items(), key=lambda x: x[1])[0]
            comparison["slowest"] = max(comparison["avg_latency"].items(), key=lambda x: x[1])[0]

        return comparison

    # TODO(redline): future feature - latency-based arbitrage opportunity detection
    def get_latency_arbitrage_opportunity(self, event_name: str) -> dict | None:
        """
        Detect latency-based arbitrage opportunities.
        If Provider A updates slower than B, there may be a micro-arb window.

        Args:
            event_name: Event to check

        Returns:
            Latency arbitrage opportunity if detected
        """
        if len(self.latency_history) < 2:
            return None

        # Find providers with significant latency difference
        avg_latencies = {}
        for provider_name, latencies in self.latency_history.items():
            if latencies:
                avg_latencies[provider_name] = sum(latencies) / len(latencies)

        if len(avg_latencies) < 2:
            return None

        sorted_providers = sorted(avg_latencies.items(), key=lambda x: x[1])
        fastest_provider = sorted_providers[0][0]
        fastest_latency = sorted_providers[0][1]
        slowest_provider = sorted_providers[-1][0]
        slowest_latency = sorted_providers[-1][1]

        latency_diff = slowest_latency - fastest_latency

        # If latency difference > 1 second, there may be arbitrage window
        if latency_diff > 1.0:
            return {
                "event_name": event_name,
                "fastest_provider": fastest_provider,
                "fastest_latency": fastest_latency,
                "slowest_provider": slowest_provider,
                "slowest_latency": slowest_latency,
                "latency_difference": latency_diff,
                "opportunity_type": "latency_arbitrage",
                "recommendation": f"Use {fastest_provider} for faster updates, {slowest_provider} may have stale odds",
            }

        return None
