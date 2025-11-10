"""
Account health manager for optimizing stake allocation.
Includes caching support for performance optimization.
"""

import logging

from src.account_manager import AccountDatabase, AccountProfile

logger = logging.getLogger(__name__)


class AccountHealthManager:
    """Manages account health and optimizes stake allocation."""

    def __init__(self, db_path: str = "config/accounts.db", enable_cache: bool = True):
        """
        Initialize the account health manager.

        Args:
            db_path: Path to the database file
            enable_cache: Enable in-memory caching for performance
        """
        self.db = AccountDatabase(db_path)
        self._cache_enabled = enable_cache

        # Initialize cache if enabled
        if enable_cache:
            try:
                from src.account_health_cache import AccountHealthCache

                self._cache = AccountHealthCache(self, cache_ttl_seconds=60)
            except ImportError:
                logger.warning("AccountHealthCache not available, caching disabled")
                self._cache = None
                self._cache_enabled = False
        else:
            self._cache = None

    def get_account_health(self, bookmaker_name: str, use_cache: bool = True) -> dict[str, any]:
        """
        Get account health metrics for a bookmaker.

        Uses caching if enabled to reduce database I/O latency.

        Args:
            bookmaker_name: Name of the bookmaker
            use_cache: Use cache if available (default: True)

        Returns:
            Dictionary with health metrics
        """
        # Use cache if available and enabled
        if self._cache_enabled and self._cache and use_cache:
            return self._cache.get_account_health(bookmaker_name)

        # Fallback to direct database access
        profile = self.db.get_account(bookmaker_name)

        if not profile:
            return {
                "exists": False,
                "status": "Unknown",
                "stealth_score": 1.0,  # Default to 1.0 (perfect) for new accounts
                "recommended_stake_multiplier": 1.0,
                "risk_level": "Low",
            }

        # Calculate recommended stake multiplier based on health
        multiplier = self._calculate_stake_multiplier(profile)
        risk_level = self._assess_risk_level(profile)

        return {
            "exists": True,
            "profile": profile,
            "status": profile.account_status,
            "stealth_score": profile.stealth_score,  # Now returns 0.0-1.0 scale
            "total_bets": profile.total_bets_placed,
            "arb_percentage": (
                (profile.total_arb_bets / profile.total_bets_placed * 100)
                if profile.total_bets_placed > 0
                else 0
            ),
            "total_profit_loss": profile.total_profit_loss,
            "recommended_stake_multiplier": multiplier,
            "risk_level": risk_level,
        }

    def _calculate_stake_multiplier(self, profile: AccountProfile) -> float:
        """
        Calculate stake multiplier based on account health.

        Returns:
            Multiplier (0.0 to 1.5) - higher means safer to bet more
        """
        multiplier = 1.0

        # Reduce stake if stealth score is low (now using 0.0-1.0 scale)
        if profile.stealth_score < 0.3:
            multiplier = 0.3  # Very risky
        elif profile.stealth_score < 0.5:
            multiplier = 0.6  # Risky
        elif profile.stealth_score < 0.7:
            multiplier = 0.8  # Caution

        # Reduce stake if account status is poor
        if profile.account_status == "Closed":
            multiplier = 0.0
        elif profile.account_status == "Limited":
            multiplier = min(multiplier, 0.4)
        elif profile.account_status == "Under Review":
            multiplier = min(multiplier, 0.7)

        # Increase stake if account is healthy and has good mix
        if (
            profile.account_status == "Healthy"
            and profile.stealth_score >= 0.8
            and profile.total_bets_placed > 0
        ):
            arb_percentage = (profile.total_arb_bets / profile.total_bets_placed) * 100
            if 30 <= arb_percentage <= 60:  # Good mix of arb and non-arb bets
                multiplier = min(multiplier * 1.2, 1.5)  # Can bet more aggressively

        return multiplier

    def _assess_risk_level(self, profile: AccountProfile) -> str:
        """Assess risk level of account."""
        if profile.account_status == "Closed":
            return "Critical"
        elif profile.account_status == "Limited":
            return "High"
        elif profile.account_status == "Under Review":
            return "Medium"
        elif profile.stealth_score < 0.3:  # Fixed: use 0.0-1.0 scale
            return "High"
        elif profile.stealth_score < 0.7:  # Fixed: use 0.0-1.0 scale
            return "Medium"
        else:
            return "Low"

    def get_all_accounts_health(self, use_cache: bool = True) -> list[dict[str, any]]:
        """
        Get health status for all accounts.

        Args:
            use_cache: Use cache if available (default: True)

        Returns:
            List of health dictionaries for all accounts
        """
        accounts = self.db.get_all_accounts()
        health_list = []
        for acc in accounts:
            health = self.get_account_health(acc.bookmaker_name, use_cache=use_cache)
            health["bookmaker_name"] = acc.bookmaker_name
            health_list.append(health)
        return health_list

    def update_account_after_bet(
        self,
        bookmaker_name: str,
        stake: float,
        is_arbitrage: bool = False,
        profit_loss: float = 0.0,
    ):
        """
        Update account health after placing a bet.

        Args:
            bookmaker_name: Name of the bookmaker
            stake: Stake amount
            is_arbitrage: Whether this was an arbitrage bet
            profit_loss: Profit or loss from the bet
        """
        profile = self.db.get_account(bookmaker_name)
        if not profile:
            return

        # Update profile
        profile.total_bets_placed += 1
        profile.total_staked += stake
        profile.total_profit_loss += profit_loss

        if is_arbitrage:
            profile.total_arb_bets += 1
        else:
            profile.total_non_arb_bets += 1

        # Recalculate stealth score using account database method
        profile.stealth_score = self.db._calculate_stealth_score(profile)

        # Save updated profile
        self.db.update_account(profile)

        # Invalidate cache
        if self._cache_enabled and self._cache:
            self._cache.invalidate(bookmaker_name)

    def adjust_stake_for_account_health(self, bookmaker_name: str, original_stake: float) -> float:
        """
        Adjust stake based on account health.

        Args:
            bookmaker_name: Name of the bookmaker
            original_stake: Original calculated stake

        Returns:
            Adjusted stake amount
        """
        health = self.get_account_health(bookmaker_name)
        multiplier = health["recommended_stake_multiplier"]

        adjusted_stake = original_stake * multiplier

        logger.info(
            f"Stake adjusted for {bookmaker_name}: "
            f"${original_stake:.2f} -> ${adjusted_stake:.2f} "
            f"(multiplier: {multiplier:.2f}, status: {health['status']})"
        )

        return adjusted_stake

    def invalidate_cache(self, bookmaker_name: str = None):
        """
        Invalidate account health cache.

        Args:
            bookmaker_name: Specific bookmaker to invalidate (None = all)
        """
        if self._cache:
            self._cache.invalidate(bookmaker_name)

    def warm_cache(self, bookmaker_names: list[str]):
        """
        Pre-load cache for given bookmakers.

        Args:
            bookmaker_names: List of bookmaker names to cache
        """
        if self._cache:
            self._cache.warm_cache(bookmaker_names)

    def log_arbitrage_bet(
        self,
        bookmaker_name: str,
        stake_amount: float,
        outcome: str,
        odds: float,
        profit: float,
        event_name: str,
    ):
        """
        Log an arbitrage bet.

        Args:
            bookmaker_name: Name of the bookmaker
            stake_amount: Amount staked
            outcome: Outcome name
            odds: Odds used
            profit: Profit from this bet
            event_name: Event name
        """
        profile = self.db.get_account(bookmaker_name)

        if not profile:
            logger.warning(f"No account profile found for {bookmaker_name}")
            return

        self.db.log_bet(
            account_id=profile.id,
            bet_type="arb",
            stake_amount=stake_amount,
            outcome=outcome,
            odds=odds,
            profit_loss=profit,
            bookmaker_name=bookmaker_name,
            event_name=event_name,
        )

        # Invalidate cache after logging bet (data changed)
        self.invalidate_cache(bookmaker_name)

        logger.info(f"Logged arbitrage bet: {bookmaker_name} - ${stake_amount:.2f} on {outcome}")

    def refresh_account_health(self):
        """Refresh account health data (placeholder for GUI updates)."""
        # This is handled by the GUI refresh
