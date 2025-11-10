"""Property-based tests for stake calculator using hypothesis."""

from hypothesis import given
from hypothesis import strategies as st

from src.arbitrage import ArbitrageOpportunity
from src.stake_calculator import StakeCalculator


@given(
    total_stake=st.floats(min_value=10.0, max_value=10000.0),
    odds1=st.floats(min_value=1.01, max_value=10.0),
    odds2=st.floats(min_value=1.01, max_value=10.0),
)
def test_stake_distribution_sum_property(total_stake, odds1, odds2):
    """Property: Sum of stakes should approximately equal total stake."""
    calc = StakeCalculator(round_stakes=False)

    # Create arbitrage opportunity
    total_implied_prob = (1.0 / odds1) + (1.0 / odds2)

    # Only test if arbitrage exists
    if total_implied_prob < 1.0:
        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[
                {"outcome_name": "Home", "odds": odds1, "bookmaker": "A"},
                {"outcome_name": "Away", "odds": odds2, "bookmaker": "B"},
            ],
            total_implied_probability=total_implied_prob,
            profit_percentage=((1.0 / total_implied_prob) - 1.0) * 100,
            bookmakers=["A", "B"],
            timestamp="2024-01-01T00:00:00",
        )

        dist = calc.calculate_stakes(opp, total_stake=total_stake)

        # Sum of stakes should be approximately equal to total stake
        stake_sum = sum(s["stake"] for s in dist.stakes)
        assert abs(stake_sum - dist.total_stake) < dist.total_stake * 0.1  # Within 10%


@given(
    odds=st.floats(min_value=1.01, max_value=10.0),
    stealth_score=st.floats(min_value=0.0, max_value=1.0),
)
def test_dynamic_rounding_property(odds, stealth_score):
    """Property: Rounded stake should be within reasonable bounds."""
    calc = StakeCalculator(round_stakes=True)
    original_stake = 100.0 / odds  # Simulate a stake

    rounded = calc._round_stake_dynamic(original_stake, stealth_score)

    # Rounded stake should be positive and reasonable
    assert rounded > 0
    assert rounded < original_stake * 2  # Shouldn't double
    assert rounded > original_stake * 0.5  # Shouldn't halve


@given(
    total_stake=st.floats(min_value=10.0, max_value=1000.0),
    variation_percent=st.floats(min_value=0.0, max_value=10.0),
)
def test_stake_variation_property(total_stake, variation_percent):
    """Property: Varied stakes should maintain profit guarantee."""
    calc = StakeCalculator(round_stakes=False)

    opp = ArbitrageOpportunity(
        event_name="Test",
        market="h2h",
        outcomes=[
            {"outcome_name": "Home", "odds": 2.0, "bookmaker": "A"},
            {"outcome_name": "Away", "odds": 2.1, "bookmaker": "B"},
        ],
        total_implied_probability=0.95,
        profit_percentage=5.0,
        bookmakers=["A", "B"],
        timestamp="2024-01-01T00:00:00",
    )

    original = calc.calculate_stakes(opp, total_stake=total_stake)
    varied = calc.vary_stakes(original, variation_percent=variation_percent)

    # Varied stakes should still guarantee profit (within rounding)
    assert varied.guaranteed_profit >= 0
    assert varied.total_stake == original.total_stake
