"""
Optimized arbitrage detection with vectorized operations.
"""

from datetime import datetime

import numpy as np
from dateutil import parser

from src.arbitrage import ArbitrageDetector, ArbitrageOpportunity


# TODO(redline): kept for perf alt in tests - optimized implementation used for performance testing
class OptimizedArbitrageDetector(ArbitrageDetector):
    """
    Performance-optimized arbitrage detector.

    Optimizations:
    - Vectorized odds processing using NumPy
    - Reduced redundant calculations
    - Batch processing for multiple events
    """

    def detect_arbitrage_vectorized(
        self, outcomes_data: list[dict[str, any]]
    ) -> ArbitrageOpportunity | None:
        """
        Vectorized arbitrage detection for improved performance.

        This method uses NumPy vectorization to process odds faster,
        reducing computation time for high-volume markets.

        Args:
            outcomes_data: List of outcome dictionaries

        Returns:
            ArbitrageOpportunity if found, None otherwise
        """
        if not outcomes_data or len(outcomes_data) < 2:
            return None

        # Convert to NumPy arrays for vectorized operations
        outcome_names = []
        odds_values = []
        bookmakers = []
        odds_formats = []

        for outcome in outcomes_data:
            outcome_names.append(outcome.get("outcome_name", ""))
            odds_values.append(outcome.get("odds"))
            bookmakers.append(outcome.get("bookmaker", "Unknown"))
            odds_formats.append(outcome.get("odds_format", "decimal"))

        # Filter out None odds
        valid_indices = [i for i, odds in enumerate(odds_values) if odds is not None]
        if len(valid_indices) < 2:
            return None

        # Normalize odds to decimal (vectorized where possible)
        decimal_odds = np.array(
            [self.normalize_odds_to_decimal(odds_values[i], odds_formats[i]) for i in valid_indices]
        )

        # Group by outcome name and find best odds (vectorized)
        outcome_groups = {}
        for idx in valid_indices:
            outcome_name = outcome_names[idx]
            decimal_odd = decimal_odds[valid_indices.index(idx)]

            if outcome_name not in outcome_groups:
                outcome_groups[outcome_name] = {"odds": decimal_odd, "index": idx}
            else:
                # Keep best (highest) odds
                if decimal_odd > outcome_groups[outcome_name]["odds"]:
                    outcome_groups[outcome_name] = {"odds": decimal_odd, "index": idx}

        if len(outcome_groups) < 2:
            return None

        # Vectorized implied probability calculation
        best_odds_array = np.array([group["odds"] for group in outcome_groups.values()])
        implied_probs = 1.0 / best_odds_array
        total_implied_prob = np.sum(implied_probs)

        # Check if arbitrage exists
        if total_implied_prob >= 1.0:
            return None

        # Calculate profit percentage
        profit_percentage = ((1.0 / total_implied_prob) - 1.0) * 100

        if profit_percentage < self.min_profit_percentage:
            return None

        # Prepare outcomes list with best odds
        outcomes = []
        bookmaker_set = set()

        for outcome_name, group_data in outcome_groups.items():
            idx = group_data["index"]
            outcomes.append(
                {
                    "outcome_name": outcome_name,
                    "odds": group_data["odds"],
                    "original_odds": odds_values[idx],
                    "original_format": odds_formats[idx],
                    "bookmaker": bookmakers[idx],
                }
            )
            bookmaker_set.add(bookmakers[idx])

        # Extract metadata
        event_name = outcomes_data[0].get("event_name", "Unknown Event")
        market = outcomes_data[0].get("market", "Match Result")
        commence_time = outcomes_data[0].get("commence_time")

        # Calculate market age
        market_age_hours = None
        if commence_time:
            try:
                market_time = parser.parse(commence_time)
                now = datetime.now(market_time.tzinfo) if market_time.tzinfo else datetime.now()
                market_age_hours = (now - market_time.replace(tzinfo=None)).total_seconds() / 3600
            except Exception:
                pass

        # Risk evaluation (now uses cached health manager)
        risk_level, risk_warnings = self._evaluate_risk(list(bookmaker_set), market_age_hours)

        return ArbitrageOpportunity(
            event_name=event_name,
            market=market,
            outcomes=outcomes,
            total_implied_probability=float(total_implied_prob),
            profit_percentage=float(profit_percentage),
            bookmakers=list(bookmaker_set),
            timestamp=datetime.now().isoformat(),
            risk_level=risk_level,
            risk_warnings=risk_warnings,
            market_age_hours=market_age_hours,
        )

    # TODO(redline): public API method - batch processing for multiple events
    def find_best_arbitrages_batch(
        self, events_data: list[dict[str, any]]
    ) -> list[ArbitrageOpportunity]:
        """
        Batch-process multiple events for improved performance.

        Args:
            events_data: List of event dictionaries

        Returns:
            List of ArbitrageOpportunity objects sorted by profit percentage
        """
        arbitrages = []

        # Process events in batch
        for event in events_data:
            outcomes = event.get("outcomes", [])
            if not outcomes:
                continue

            # Use optimized detection
            arb = self.detect_arbitrage_vectorized(outcomes)
            if arb:
                arbitrages.append(arb)

        # Sort by profit percentage (highest first)
        if arbitrages:
            # Use NumPy for faster sorting on large lists
            profit_array = np.array([a.profit_percentage for a in arbitrages])
            sorted_indices = np.argsort(profit_array)[::-1]
            arbitrages = [arbitrages[i] for i in sorted_indices]

        return arbitrages
