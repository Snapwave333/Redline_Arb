"""Unit tests for account health management."""

from src.account_health import AccountHealthManager
from src.account_manager import AccountProfile


class TestAccountHealthManager:
    """Test suite for AccountHealthManager."""

    def test_init_default(self, temp_db):
        """Test default initialization."""
        manager = AccountHealthManager(db_path=temp_db, enable_cache=False)
        assert manager.db is not None
        assert manager._cache_enabled is False

    def test_init_with_cache(self, temp_db):
        """Test initialization with cache enabled."""
        manager = AccountHealthManager(db_path=temp_db, enable_cache=True)
        # Cache may or may not be available depending on imports
        assert manager.db is not None

    def test_get_account_health_nonexistent(self, temp_db):
        """Test getting health for non-existent account."""
        manager = AccountHealthManager(db_path=temp_db, enable_cache=False)
        health = manager.get_account_health("Nonexistent Bookmaker")

        assert health["exists"] is False
        assert health["status"] == "Unknown"
        assert health["stealth_score"] == 1.0
        assert health["risk_level"] == "Low"

    def test_get_account_health_existing(self, account_health_manager, sample_account_profile):
        """Test getting health for existing account."""
        health = account_health_manager.get_account_health(
            sample_account_profile.bookmaker_name, use_cache=False
        )

        assert health["exists"] is True
        assert health["status"] == sample_account_profile.account_status
        assert "stealth_score" in health
        assert 0.0 <= health["stealth_score"] <= 1.0

    def test_adjust_stake_for_account_health_healthy(
        self, account_health_manager, sample_account_profile
    ):
        """Test stake adjustment for healthy account."""
        original_stake = 100.0
        adjusted = account_health_manager.adjust_stake_for_account_health(
            sample_account_profile.bookmaker_name, original_stake
        )

        # Healthy accounts should have minimal adjustment
        assert adjusted > 0
        assert adjusted <= original_stake * 1.5  # Shouldn't increase too much

    def test_adjust_stake_for_account_health_low_stealth(
        self, account_health_manager, low_stealth_account_profile
    ):
        """Test stake adjustment for low stealth account."""
        original_stake = 100.0
        adjusted = account_health_manager.adjust_stake_for_account_health(
            low_stealth_account_profile.bookmaker_name, original_stake
        )

        # Low stealth should reduce stake
        assert adjusted < original_stake

    def test_update_account_after_bet(self, account_health_manager, sample_account_profile):
        """Test updating account after placing a bet."""
        initial_health = account_health_manager.get_account_health(
            sample_account_profile.bookmaker_name, use_cache=False
        )
        initial_bets = initial_health.get("total_bets", 0)

        # Place an arbitrage bet
        account_health_manager.update_account_after_bet(
            sample_account_profile.bookmaker_name, stake=50.0, is_arbitrage=True, profit_loss=5.0
        )

        updated_health = account_health_manager.get_account_health(
            sample_account_profile.bookmaker_name, use_cache=False
        )

        # Should have updated bet count
        assert updated_health.get("total_bets", 0) > initial_bets

    def test_calculate_stake_multiplier(self, account_health_manager, sample_account_profile):
        """Test stake multiplier calculation."""
        health = account_health_manager.get_account_health(
            sample_account_profile.bookmaker_name, use_cache=False
        )

        multiplier = health.get("recommended_stake_multiplier", 1.0)
        assert 0.0 <= multiplier <= 2.0  # Reasonable range

    def test_assess_risk_level(self, account_health_manager, sample_account_profile):
        """Test risk level assessment."""
        health = account_health_manager.get_account_health(
            sample_account_profile.bookmaker_name, use_cache=False
        )

        risk_level = health.get("risk_level", "Unknown")
        assert risk_level in ["Low", "Medium", "High"]

    def test_get_all_accounts_health(
        self, account_health_manager, sample_account_profile, low_stealth_account_profile
    ):
        """Test getting health for all accounts."""
        all_health = account_health_manager.get_all_accounts_health(use_cache=False)

        assert isinstance(all_health, list)
        assert len(all_health) >= 2  # At least our test accounts

        # Should contain our test accounts
        bookmaker_names = [h["bookmaker_name"] for h in all_health if "bookmaker_name" in h]
        assert sample_account_profile.bookmaker_name in bookmaker_names or any(
            sample_account_profile.bookmaker_name in str(h) for h in all_health
        )

    def test_stealth_score_buckets(self, account_health_manager, account_db):
        """Test stealth score buckets map to correct multipliers."""
        # Create accounts with different stealth scores
        high_stealth = AccountProfile(
            bookmaker_name="HighStealth", stealth_score=0.9, account_status="Healthy"
        )
        mid_stealth = AccountProfile(
            bookmaker_name="MidStealth", stealth_score=0.5, account_status="Healthy"
        )
        low_stealth = AccountProfile(
            bookmaker_name="LowStealth", stealth_score=0.2, account_status="Under Review"
        )

        account_db.create_account(high_stealth)
        account_db.create_account(mid_stealth)
        account_db.create_account(low_stealth)

        # Check multipliers
        high_health = account_health_manager.get_account_health("HighStealth", use_cache=False)
        mid_health = account_health_manager.get_account_health("MidStealth", use_cache=False)
        low_health = account_health_manager.get_account_health("LowStealth", use_cache=False)

        # High stealth should have higher multiplier
        assert high_health.get("recommended_stake_multiplier", 0) >= mid_health.get(
            "recommended_stake_multiplier", 0
        )
        assert mid_health.get("recommended_stake_multiplier", 0) >= low_health.get(
            "recommended_stake_multiplier", 0
        )

    def test_update_account_after_bet_balance_mutation(
        self, account_health_manager, sample_account_profile
    ):
        """Test that update_account_after_bet mutates balance correctly."""
        # Get initial profile
        profile = account_health_manager.db.get_account(sample_account_profile.bookmaker_name)
        initial_balance = profile.total_profit_loss if profile else 0.0
        initial_bets = profile.total_bets_placed if profile else 0

        # Place a winning bet
        account_health_manager.update_account_after_bet(
            sample_account_profile.bookmaker_name, stake=100.0, is_arbitrage=True, profit_loss=10.0
        )

        # Check balance increased
        updated_profile = account_health_manager.db.get_account(
            sample_account_profile.bookmaker_name
        )
        assert updated_profile.total_profit_loss == initial_balance + 10.0
        assert updated_profile.total_bets_placed == initial_bets + 1
        assert updated_profile.total_arb_bets == (profile.total_arb_bets if profile else 0) + 1

        # Place a losing bet
        new_balance = updated_profile.total_profit_loss
        account_health_manager.update_account_after_bet(
            sample_account_profile.bookmaker_name, stake=50.0, is_arbitrage=False, profit_loss=-5.0
        )

        final_profile = account_health_manager.db.get_account(sample_account_profile.bookmaker_name)
        assert final_profile.total_profit_loss == new_balance - 5.0
        assert (
            final_profile.total_non_arb_bets
            == (updated_profile.total_non_arb_bets if updated_profile else 0) + 1
        )
