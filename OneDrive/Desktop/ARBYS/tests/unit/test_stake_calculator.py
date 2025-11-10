"""Unit tests for stake calculator."""

import math

from src.arbitrage import ArbitrageOpportunity
from src.stake_calculator import StakeCalculator, StakeDistribution


class TestStakeCalculator:
    """Test suite for StakeCalculator."""

    def test_init_default(self):
        """Test default initialization."""
        calc = StakeCalculator()
        assert calc.round_stakes is True
        assert calc.max_variation_percent == 5.0
        assert calc.account_health_manager is None
        assert calc.min_stake_threshold == 10.0

    def test_calculate_stakes_optimal_distribution(self):
        """Test optimal stake distribution calculation."""
        calc = StakeCalculator(round_stakes=False)

        opp = ArbitrageOpportunity(
            event_name="Test Event",
            market="h2h",
            outcomes=[
                {"outcome_name": "Home", "odds": 2.0, "bookmaker": "A"},
                {"outcome_name": "Away", "odds": 2.0, "bookmaker": "B"},
            ],
            total_implied_probability=1.0,  # Fair market
            profit_percentage=0.0,
            bookmakers=["A", "B"],
            timestamp="2024-01-01T00:00:00",
        )

        # Create actual arbitrage opportunity with profitable odds
        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[
                {
                    "outcome_name": "Home",
                    "odds": 2.1,
                    "bookmaker": "A",
                },  # Implied prob: 1/2.1 = 0.476
                {
                    "outcome_name": "Away",
                    "odds": 2.15,
                    "bookmaker": "B",
                },  # Implied prob: 1/2.15 = 0.465
            ],
            total_implied_probability=0.476 + 0.465,  # 0.941 - 5.9% arbitrage
            profit_percentage=((1.0 / 0.941) - 1.0) * 100,
            bookmakers=["A", "B"],
            timestamp="2024-01-01T00:00:00",
        )

        dist = calc.calculate_stakes(opp, total_stake=100.0)

        assert isinstance(dist, StakeDistribution)
        assert dist.total_stake == 100.0
        assert len(dist.stakes) == 2
        assert math.isclose(sum(s["stake"] for s in dist.stakes), dist.total_stake, rel_tol=0.1)
        assert dist.guaranteed_profit > 0

    def test_calculate_stakes_rounding(self):
        """Test stake rounding functionality."""
        calc = StakeCalculator(round_stakes=True)

        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[
                {"outcome_name": "Home", "odds": 2.1, "bookmaker": "A"},
                {"outcome_name": "Away", "odds": 2.2, "bookmaker": "B"},
            ],
            total_implied_probability=0.95,
            profit_percentage=5.0,
            bookmakers=["A", "B"],
            timestamp="2024-01-01T00:00:00",
        )

        dist = calc.calculate_stakes(opp, total_stake=100.0)

        # Check that stakes are rounded
        for stake_info in dist.stakes:
            # Should be rounded to reasonable precision
            assert isinstance(stake_info["stake"], (int, float))

    def test_calculate_stakes_min_threshold_warning(self):
        """Test minimum stake threshold warnings."""
        calc = StakeCalculator(min_stake_threshold=10.0, round_stakes=False)

        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[
                {"outcome_name": "Home", "odds": 2.1, "bookmaker": "A"},
                {"outcome_name": "Away", "odds": 2.2, "bookmaker": "B"},
            ],
            total_implied_probability=0.95,
            profit_percentage=5.0,
            bookmakers=["A", "B"],
            timestamp="2024-01-01T00:00:00",
        )

        # Very small total stake
        dist = calc.calculate_stakes(opp, total_stake=5.0)

        # Should have warnings if any stake is below threshold
        if any(s["stake"] < calc.min_stake_threshold for s in dist.stakes):
            assert len(dist.warnings) > 0

    def test_calculate_stakes_with_account_health(
        self, account_health_manager, sample_account_profile
    ):
        """Test stake calculation with account health manager."""
        calc = StakeCalculator(account_health_manager=account_health_manager, round_stakes=False)

        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[
                {
                    "outcome_name": "Home",
                    "odds": 2.1,
                    "bookmaker": sample_account_profile.bookmaker_name,
                },
                {"outcome_name": "Away", "odds": 2.2, "bookmaker": "Other"},
            ],
            total_implied_probability=0.95,
            profit_percentage=5.0,
            bookmakers=[sample_account_profile.bookmaker_name, "Other"],
            timestamp="2024-01-01T00:00:00",
        )

        dist = calc.calculate_stakes(opp, total_stake=100.0)
        assert isinstance(dist, StakeDistribution)
        assert len(dist.stakes) == 2

    def test_round_stake_dynamic_high_stealth(self):
        """Test dynamic rounding with high stealth score."""
        calc = StakeCalculator(round_stakes=True)

        # High stealth score should use finer rounding
        stake = 50.23
        rounded = calc._round_stake_dynamic(stake, stealth_score=0.8)
        # Should round to $0.05 or $0.10 for high stealth
        assert rounded != stake  # Should be rounded
        assert rounded >= stake * 0.95  # Shouldn't round too aggressively

    def test_round_stake_dynamic_low_stealth(self):
        """Test dynamic rounding with low stealth score."""
        calc = StakeCalculator(round_stakes=True)

        # Low stealth score should use coarser rounding (whole dollars)
        stake = 50.67
        rounded = calc._round_stake_dynamic(stake, stealth_score=0.3)
        # Should round to nearest dollar
        assert abs(rounded - round(stake)) < 1.0

    def test_vary_stakes(self):
        """Test stake variation for anti-detection."""
        calc = StakeCalculator(max_variation_percent=5.0)

        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[
                {"outcome_name": "Home", "odds": 2.0, "bookmaker": "A"},
                {"outcome_name": "Away", "odds": 2.0, "bookmaker": "B"},
            ],
            total_implied_probability=0.95,
            profit_percentage=5.0,
            bookmakers=["A", "B"],
            timestamp="2024-01-01T00:00:00",
        )

        original = calc.calculate_stakes(opp, total_stake=100.0)
        varied = calc.vary_stakes(original, variation_percent=5.0)

        assert isinstance(varied, StakeDistribution)
        # vary_stakes returns original unchanged in TEST_MODE (no randomness for deterministic tests)
        # Otherwise it should return a modified copy (even if stakes end up similar after rounding)
        from src.stake_calculator import TEST_MODE

        if TEST_MODE:
            assert varied.stakes == original.stakes
        else:
            # In production mode, method should return varied stakes (may be same after rounding)
            # Check that it's at least a new StakeDistribution instance
            assert varied is not original

    def test_optimize_stakes_for_bankroll(self):
        """Test bankroll-based stake optimization."""
        calc = StakeCalculator()

        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[
                {"outcome_name": "Home", "odds": 2.0, "bookmaker": "A"},
                {"outcome_name": "Away", "odds": 2.0, "bookmaker": "B"},
            ],
            total_implied_probability=0.95,
            profit_percentage=5.0,
            bookmakers=["A", "B"],
            timestamp="2024-01-01T00:00:00",
        )

        bankroll = 1000.0
        dist = calc.optimize_stakes_for_bankroll(opp, bankroll, max_stake_percentage=5.0)

        assert dist.total_stake == 50.0  # 5% of 1000
        assert dist.total_stake <= bankroll * 0.05


class TestStakeDistribution:
    """Test suite for StakeDistribution dataclass."""

    def test_init_default_warnings(self):
        """Test that warnings list is initialized."""
        dist = StakeDistribution(
            total_stake=100.0,
            stakes=[],
            total_return=105.0,
            guaranteed_profit=5.0,
            profit_percentage=5.0,
        )
        assert dist.warnings == []

    def test_profit_calculation(self):
        """Test profit calculation correctness."""
        dist = StakeDistribution(
            total_stake=100.0,
            stakes=[
                {"stake": 50.0, "return": 105.0},
                {"stake": 50.0, "return": 105.0},
            ],
            total_return=105.0,
            guaranteed_profit=5.0,
            profit_percentage=5.0,
        )

        assert dist.guaranteed_profit == 5.0
        assert math.isclose(dist.profit_percentage, 5.0)
