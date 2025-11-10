"""
Core arbitrage detection and calculation logic.
"""

from dataclasses import dataclass
from datetime import datetime

from dateutil import parser


@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity."""

    event_name: str
    market: str
    outcomes: list[dict[str, any]]
    total_implied_probability: float
    profit_percentage: float
    bookmakers: list[str]
    timestamp: str
    risk_level: str = "Low"  # Low, Medium, High
    risk_warnings: list[str] = None
    market_age_hours: float | None = None

    def __post_init__(self):
        if self.risk_warnings is None:
            self.risk_warnings = []


class ArbitrageDetector:
    """Detects arbitrage opportunities from odds data."""

    def __init__(
        self,
        min_profit_percentage: float = 1.0,
        account_health_manager=None,
        max_market_age_hours: float = 24.0,
        critical_stealth_threshold: float = 0.2,
    ):
        """
        Initialize the arbitrage detector.

        Args:
            min_profit_percentage: Minimum profit percentage to consider (default: 1.0%)
            account_health_manager: Optional AccountHealthManager for risk evaluation
            max_market_age_hours: Maximum market age in hours before flagging as suspicious (default: 24)
            critical_stealth_threshold: Critical stealth score threshold (default: 0.2)
        """
        self.min_profit_percentage = min_profit_percentage
        self.account_health_manager = account_health_manager
        self.max_market_age_hours = max_market_age_hours
        self.critical_stealth_threshold = critical_stealth_threshold

    def calculate_implied_probability(self, odds: float, odds_format: str = "decimal") -> float:
        """
        Calculate implied probability from odds.

        Args:
            odds: The odds value
            odds_format: Format of odds ('decimal', 'fractional', 'american')

        Returns:
            Implied probability as a decimal (0.0 to 1.0)
        """
        if odds_format == "decimal":
            return 1.0 / odds
        elif odds_format == "fractional":
            # Convert fractional to decimal first
            if "/" in str(odds):
                num, den = map(float, str(odds).split("/"))
                decimal_odds = (num / den) + 1
            else:
                decimal_odds = float(odds) + 1
            return 1.0 / decimal_odds
        elif odds_format == "american":
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)
        else:
            raise ValueError(f"Unsupported odds format: {odds_format}")

    def normalize_odds_to_decimal(self, odds: float, odds_format: str = "decimal") -> float:
        """
        Normalize odds to decimal format.

        Args:
            odds: The odds value
            odds_format: Current format of odds

        Returns:
            Decimal odds
        """
        if odds_format == "decimal":
            return odds
        elif odds_format == "fractional":
            if "/" in str(odds):
                num, den = map(float, str(odds).split("/"))
                return (num / den) + 1
            return float(odds) + 1
        elif odds_format == "american":
            if odds > 0:
                return (odds / 100) + 1
            else:
                return (100 / abs(odds)) + 1
        else:
            raise ValueError(f"Unsupported odds format: {odds_format}")

    def detect_arbitrage(self, outcomes_data: list[dict[str, any]]) -> ArbitrageOpportunity | None:
        """
        Detect arbitrage opportunity from outcomes data.

        Args:
            outcomes_data: List of dictionaries containing:
                - 'outcome_name': Name of the outcome
                - 'odds': The odds value
                - 'bookmaker': Name of the bookmaker
                - 'odds_format': Format of the odds (default: 'decimal')

        Returns:
            ArbitrageOpportunity if found, None otherwise
        """
        if not outcomes_data or len(outcomes_data) < 2:
            return None

        # Group outcomes by outcome name and find best odds for each
        outcome_groups = {}
        for outcome in outcomes_data:
            outcome_name = outcome.get("outcome_name", "")
            odds = outcome.get("odds")
            odds_format = outcome.get("odds_format", "decimal")

            if odds is None:
                continue

            # Normalize to decimal
            decimal_odds = self.normalize_odds_to_decimal(odds, odds_format)

            if outcome_name not in outcome_groups:
                outcome_groups[outcome_name] = {
                    "odds": decimal_odds,
                    "bookmaker": outcome.get("bookmaker", "Unknown"),
                    "original_odds": odds,
                    "original_format": odds_format,
                }
            else:
                # Keep the best (highest) odds
                if decimal_odds > outcome_groups[outcome_name]["odds"]:
                    outcome_groups[outcome_name] = {
                        "odds": decimal_odds,
                        "bookmaker": outcome.get("bookmaker", "Unknown"),
                        "original_odds": odds,
                        "original_format": odds_format,
                    }

        if len(outcome_groups) < 2:
            return None

        # Calculate total implied probability
        best_odds = [outcome["odds"] for outcome in outcome_groups.values()]
        total_implied_prob = sum(1.0 / odds for odds in best_odds)

        # Check if arbitrage exists (total implied prob < 1.0)
        if total_implied_prob >= 1.0:
            return None

        # Calculate profit percentage
        profit_percentage = ((1.0 / total_implied_prob) - 1.0) * 100

        if profit_percentage < self.min_profit_percentage:
            return None

        # Prepare outcomes list with best odds
        outcomes = []
        bookmakers = set()

        for outcome_name, data in outcome_groups.items():
            outcomes.append(
                {
                    "outcome_name": outcome_name,
                    "odds": data["odds"],
                    "original_odds": data["original_odds"],
                    "original_format": data["original_format"],
                    "bookmaker": data["bookmaker"],
                }
            )
            bookmakers.add(data["bookmaker"])

        # Extract event name and metadata (assuming first outcome has it)
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

        # Risk evaluation
        risk_level, risk_warnings = self._evaluate_risk(bookmakers, market_age_hours)

        return ArbitrageOpportunity(
            event_name=event_name,
            market=market,
            outcomes=outcomes,
            total_implied_probability=total_implied_prob,
            profit_percentage=profit_percentage,
            bookmakers=list(bookmakers),
            timestamp=datetime.now().isoformat(),
            risk_level=risk_level,
            risk_warnings=risk_warnings,
            market_age_hours=market_age_hours,
        )

    def _evaluate_risk(
        self, bookmakers: list[str], market_age_hours: float | None
    ) -> tuple[str, list[str]]:
        """
        Evaluate risk level for an arbitrage opportunity.

        Optimized: Uses batch health lookup to reduce database calls.

        Args:
            bookmakers: List of bookmaker names involved
            market_age_hours: Age of market in hours (None if unknown)

        Returns:
            Tuple of (risk_level, risk_warnings)
        """
        risk_level = "Low"
        risk_warnings = []

        # Check account stealth scores (optimized with caching)
        if self.account_health_manager:
            # Batch fetch health data if cache supports it
            critical_accounts = []
            low_score_accounts = []

            for bookmaker in bookmakers:
                health = self.account_health_manager.get_account_health(bookmaker, use_cache=True)
                stealth_score = health.get("stealth_score", 1.0)

                if stealth_score < self.critical_stealth_threshold:
                    critical_accounts.append((bookmaker, stealth_score))
                elif stealth_score < 0.5:
                    low_score_accounts.append(bookmaker)

            if critical_accounts:
                risk_level = "High"
                for bookmaker, score in critical_accounts:
                    risk_warnings.append(
                        f"HIGH RISK: {bookmaker} has critical stealth score ({score:.2f}). "
                        f"Account may be flagged or limited."
                    )
            elif low_score_accounts:
                risk_level = "Medium"
                risk_warnings.append("Some accounts have low stealth scores. Exercise caution.")

        # Check market age
        if market_age_hours is not None:
            if market_age_hours > self.max_market_age_hours:
                if risk_level == "Low":
                    risk_level = "Medium"
                risk_warnings.append(
                    f"Market age: {market_age_hours:.1f} hours. "
                    f"Opportunities on old markets may be errors or have stale odds."
                )
            elif market_age_hours < 0:
                # Future event
                pass
            else:
                # Recent market - this is good
                pass

        return risk_level, risk_warnings

    def find_best_arbitrages(self, events_data: list[dict[str, any]]) -> list[ArbitrageOpportunity]:
        """
        Find all arbitrage opportunities from a list of events.

        Args:
            events_data: List of event dictionaries containing outcomes

        Returns:
            List of ArbitrageOpportunity objects sorted by profit percentage
        """
        arbitrages = []

        for event in events_data:
            outcomes = event.get("outcomes", [])
            arb = self.detect_arbitrage(outcomes)
            if arb:
                arbitrages.append(arb)

        # Sort by profit percentage (highest first)
        arbitrages.sort(key=lambda x: x.profit_percentage, reverse=True)

        return arbitrages
