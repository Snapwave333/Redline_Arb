"""
Stake calculation for arbitrage opportunities.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check test mode
TEST_MODE = os.getenv("TEST_MODE", "0") == "1"


@dataclass
class StakeDistribution:
    """Represents stake distribution across outcomes."""

    total_stake: float
    stakes: list[dict[str, any]]
    total_return: float
    guaranteed_profit: float
    profit_percentage: float
    warnings: list[str] = None  # List of warnings (e.g., "RISK: TOO SMALL")

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class StakeCalculator:
    """Calculates optimal stake distribution for arbitrage opportunities."""

    def __init__(
        self,
        round_stakes: bool = True,
        max_variation_percent: float = 5.0,
        account_health_manager=None,
        min_stake_threshold: float = 10.0,
    ):
        """
        Initialize the stake calculator.

        Args:
            round_stakes: Whether to round stakes to look more natural
            max_variation_percent: Maximum percentage to vary stakes for anti-detection
            account_health_manager: Optional AccountHealthManager instance
            min_stake_threshold: Minimum stake amount to avoid detection (default: $10)
        """
        self.round_stakes = round_stakes
        self.max_variation_percent = max_variation_percent
        self.account_health_manager = account_health_manager
        self.min_stake_threshold = min_stake_threshold

    def calculate_stakes(self, arbitrage_opportunity, total_stake: float) -> StakeDistribution:
        """
        Calculate optimal stake distribution for an arbitrage opportunity.

        Args:
            arbitrage_opportunity: ArbitrageOpportunity object
            total_stake: Total amount to stake across all outcomes

        Returns:
            StakeDistribution object with calculated stakes
        """
        if not arbitrage_opportunity.outcomes:
            raise ValueError("No outcomes in arbitrage opportunity")

        # Calculate total return (same for all outcomes)
        total_return = total_stake / arbitrage_opportunity.total_implied_probability

        # Calculate stake for each outcome
        stakes = []
        warnings = []

        for outcome in arbitrage_opportunity.outcomes:
            odds = outcome["odds"]
            stake = total_return / odds

            # Apply account health adjustment if available
            if self.account_health_manager:
                stake = self.account_health_manager.adjust_stake_for_account_health(
                    outcome["bookmaker"], stake
                )

            # Get stealth score for dynamic rounding (use cache if available)
            stealth_score = 1.0
            if self.account_health_manager:
                health = self.account_health_manager.get_account_health(
                    outcome["bookmaker"], use_cache=True  # Use cache for performance
                )
                stealth_score = health.get("stealth_score", 1.0)

            # Check minimum stake threshold
            if stake < self.min_stake_threshold:
                warnings.append(
                    f"RISK: TOO SMALL - {outcome['bookmaker']} stake is ${stake:.2f}. "
                    f"Consider increasing total stake or skipping this opportunity."
                )

            # Apply dynamic rounding based on stealth score
            if self.round_stakes:
                stake = self._round_stake_dynamic(stake, stealth_score)

            stakes.append(
                {
                    "outcome_name": outcome["outcome_name"],
                    "stake": stake,
                    "odds": odds,
                    "bookmaker": outcome["bookmaker"],
                    "return": stake * odds,
                    "profit": stake * odds - total_stake,
                    "stealth_score": stealth_score,
                }
            )

        # Adjust for rounding if needed (ensure total doesn't exceed budget)
        total_calculated_stake = sum(s["stake"] for s in stakes)
        if total_calculated_stake > total_stake:
            # Scale down proportionally
            scale_factor = total_stake / total_calculated_stake
            for stake_info in stakes:
                stake_info["stake"] *= scale_factor
                if self.round_stakes:
                    stake_info["stake"] = self._round_stake(stake_info["stake"])
                stake_info["return"] = stake_info["stake"] * stake_info["odds"]
                stake_info["profit"] = stake_info["return"] - total_stake

        # Recalculate total return based on actual stakes
        actual_total_return = min(s["return"] for s in stakes)
        guaranteed_profit = actual_total_return - total_stake
        profit_percentage = (guaranteed_profit / total_stake) * 100

        return StakeDistribution(
            total_stake=total_stake,
            stakes=stakes,
            total_return=actual_total_return,
            guaranteed_profit=guaranteed_profit,
            profit_percentage=profit_percentage,
            warnings=warnings,
        )

    def _round_stake(self, stake: float, rounding_unit: float = 1.0) -> float:
        """
        Round stake to look more natural (e.g., round to nearest dollar).

        Args:
            stake: Original stake amount
            rounding_unit: Unit to round to (default: 1.0 for dollars)

        Returns:
            Rounded stake
        """
        return round(stake / rounding_unit) * rounding_unit

    def _round_stake_dynamic(self, stake: float, stealth_score: float) -> float:
        """
        Dynamically round stake based on stealth score.

        Args:
            stake: Original stake amount
            stealth_score: Stealth score (0.0-1.0)

        Returns:
            Rounded stake

        Rules:
        - If stealth_score < 0.5: Round to nearest whole dollar (more suspicious)
        - If stealth_score >= 0.5: Round to nearest $0.05 or $0.10 (less suspicious)
        """
        if stealth_score < 0.5:
            # High risk: Round to nearest dollar (more suspicious but safer)
            return round(stake)
        else:
            # Low risk: Round to nearest $0.05 or $0.10 (less suspicious)
            # Use $0.10 for stakes > $50, $0.05 otherwise
            rounding_unit = 0.10 if stake > 50 else 0.05
            return round(stake / rounding_unit) * rounding_unit

    def vary_stakes(
        self, stake_distribution: StakeDistribution, variation_percent: float = None
    ) -> StakeDistribution:
        """
        Add slight variation to stakes for anti-detection.

        Args:
            stake_distribution: Original StakeDistribution
            variation_percent: Percentage to vary (uses max_variation_percent if None)

        Returns:
            New StakeDistribution with varied stakes
        """
        if variation_percent is None:
            variation_percent = self.max_variation_percent

        # Disable randomness in test mode for deterministic results
        if TEST_MODE:
            return stake_distribution

        import random

        varied_stakes = []
        for stake_info in stake_distribution.stakes:
            # Add random variation within the specified percentage
            variation = random.uniform(-variation_percent, variation_percent) / 100
            varied_stake = stake_info["stake"] * (1 + variation)

            if self.round_stakes:
                varied_stake = self._round_stake(varied_stake)

            varied_stakes.append(
                {
                    **stake_info,
                    "stake": varied_stake,
                    "return": varied_stake * stake_info["odds"],
                    "profit": varied_stake * stake_info["odds"] - stake_distribution.total_stake,
                }
            )

        # Recalculate minimum return
        actual_total_return = min(s["return"] for s in varied_stakes)
        guaranteed_profit = actual_total_return - stake_distribution.total_stake
        profit_percentage = (guaranteed_profit / stake_distribution.total_stake) * 100

        return StakeDistribution(
            total_stake=stake_distribution.total_stake,
            stakes=varied_stakes,
            total_return=actual_total_return,
            guaranteed_profit=guaranteed_profit,
            profit_percentage=profit_percentage,
        )

    def optimize_stakes_for_bankroll(
        self, arbitrage_opportunity, bankroll: float, max_stake_percentage: float = 5.0
    ) -> StakeDistribution:
        """
        Calculate optimal stake size based on bankroll and risk management.

        Args:
            arbitrage_opportunity: ArbitrageOpportunity object
            bankroll: Total available bankroll
            max_stake_percentage: Maximum percentage of bankroll to stake (default: 5%)

        Returns:
            StakeDistribution with optimized stakes
        """
        max_stake = bankroll * (max_stake_percentage / 100)
        return self.calculate_stakes(arbitrage_opportunity, max_stake)
