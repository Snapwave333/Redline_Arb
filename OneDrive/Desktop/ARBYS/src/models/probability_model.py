"""
Probability models for feed mashups.
Combines odds with statistical models to detect value discrepancies.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProbabilityModel:
    """Base probability model for calculating implied probabilities."""

    def calculate_implied_probability(self, odds: float) -> float:
        """
        Calculate implied probability from decimal odds.

        Args:
            odds: Decimal odds

        Returns:
            Implied probability (0.0 to 1.0)
        """
        if odds <= 0:
            return 0.0
        return 1.0 / odds

    def calculate_implied_probabilities(self, outcomes: list[dict]) -> dict[str, float]:
        """
        Calculate implied probabilities for all outcomes.

        Args:
            outcomes: List of outcome dictionaries with 'odds' key

        Returns:
            Dictionary mapping outcome names to probabilities
        """
        probabilities = {}

        for outcome in outcomes:
            outcome_name = outcome.get("outcome_name", "")
            odds = outcome.get("odds", 0)
            if odds > 0:
                probabilities[outcome_name] = self.calculate_implied_probability(odds)

        return probabilities

    def calculate_market_efficiency(self, outcomes: list[dict]) -> float:
        """
        Calculate market efficiency (sum of implied probabilities).
        Perfect efficiency = 1.0, inefficiency > 1.0 indicates arbitrage opportunity.

        Args:
            outcomes: List of outcome dictionaries

        Returns:
            Market efficiency score
        """
        total_probability = sum(
            self.calculate_implied_probability(outcome.get("odds", 0)) for outcome in outcomes
        )
        return total_probability

    def detect_value_discrepancy(
        self, odds_data: dict, statistical_probability: float
    ) -> dict | None:
        """
        Detect value discrepancy between odds and statistical model.

        Args:
            odds_data: Event odds data
            statistical_probability: Probability from statistical model

        Returns:
            Value discrepancy info if detected, None otherwise
        """
        outcomes = odds_data.get("outcomes", [])
        if not outcomes:
            return None

        # Calculate implied probabilities from odds
        implied_probs = self.calculate_implied_probabilities(outcomes)

        # Find best odds (highest implied probability)
        best_implied = max(implied_probs.values()) if implied_probs else 0.0

        # Check for value (statistical model suggests different probability)
        discrepancy = abs(statistical_probability - best_implied)

        if discrepancy > 0.05:  # 5% threshold
            return {
                "event_name": odds_data.get("event_name", ""),
                "statistical_probability": statistical_probability,
                "odds_implied_probability": best_implied,
                "discrepancy": discrepancy,
                "value_direction": (
                    "favorite" if statistical_probability > best_implied else "underdog"
                ),
            }

        return None


class SimpleHistoricalModel(ProbabilityModel):
    """Simple model based on historical win rates."""

    def __init__(self, historical_data):
        """
        Initialize with historical data.

        Args:
            historical_data: HistoricalDataStorage instance
        """
        self.historical_data = historical_data

    def estimate_win_probability(
        self, home_team: str, away_team: str, league: str = None
    ) -> float | None:
        """
        Estimate win probability based on historical performance.

        Args:
            home_team: Home team name
            away_team: Away team name
            league: Optional league name

        Returns:
            Estimated probability for home team win (0.0 to 1.0), or None
        """
        # Get historical matches
        historical_matches = self.historical_data.get_historical_odds(
            sport=league or "soccer", start_date=datetime.now() - timedelta(days=365)
        )

        if not historical_matches:
            return None

        # Count home team wins (simplified - would need actual results)
        # This is a placeholder - actual implementation would track results
        home_wins = 0
        total_matches = 0

        for match in historical_matches:
            if match.get("home_team") == home_team or match.get("away_team") == home_team:
                total_matches += 1
                # In real implementation, check final_result field
                # home_wins += (1 if match['final_result'] == 'home_win' else 0)

        if total_matches == 0:
            return None

        # Default to 0.5 (50%) if no historical data
        win_rate = 0.5
        if total_matches > 0:
            win_rate = home_wins / total_matches

        return win_rate


class FeedMashupAnalyzer:
    """Combines odds feeds with probability models to detect value."""

    def __init__(self, probability_model: ProbabilityModel):
        """
        Initialize feed mashup analyzer.

        Args:
            probability_model: Probability model instance
        """
        self.probability_model = probability_model

    def analyze_odds_with_model(
        self, odds_events: list[dict], team_metadata: dict = None
    ) -> list[dict]:
        """
        Analyze odds events using probability model.

        Args:
            odds_events: List of odds event dictionaries
            team_metadata: Optional team metadata for model input

        Returns:
            List of events with value analysis
        """
        analyzed_events = []

        for event in odds_events:
            analysis = {
                **event,
                "market_efficiency": self.probability_model.calculate_market_efficiency(
                    event.get("outcomes", [])
                ),
                "value_discrepancies": [],
            }

            # If we have metadata/model predictions, check for value
            if team_metadata:
                home_team = event.get("home_team", "")
                away_team = event.get("away_team", "")

                if isinstance(self.probability_model, SimpleHistoricalModel):
                    est_prob = self.probability_model.estimate_win_probability(home_team, away_team)

                    if est_prob:
                        discrepancy = self.probability_model.detect_value_discrepancy(
                            event, est_prob
                        )
                        if discrepancy:
                            analysis["value_discrepancies"].append(discrepancy)

            analyzed_events.append(analysis)

        return analyzed_events
