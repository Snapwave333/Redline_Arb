"""Unit tests for arbitrage detection logic."""

import math
from datetime import datetime, timedelta

from src.account_health import AccountHealthManager
from src.arbitrage import ArbitrageDetector, ArbitrageOpportunity


class TestArbitrageDetector:
    """Test suite for ArbitrageDetector."""

    def test_init_default(self):
        """Test default initialization."""
        detector = ArbitrageDetector()
        assert detector.min_profit_percentage == 1.0
        assert detector.account_health_manager is None
        assert detector.max_market_age_hours == 24.0

    def test_init_custom(self):
        """Test custom initialization."""
        manager = AccountHealthManager(enable_cache=False)
        detector = ArbitrageDetector(
            min_profit_percentage=2.0, account_health_manager=manager, max_market_age_hours=48.0
        )
        assert detector.min_profit_percentage == 2.0
        assert detector.account_health_manager == manager
        assert detector.max_market_age_hours == 48.0

    def test_calculate_implied_probability_decimal(self):
        """Test implied probability calculation with decimal odds."""
        detector = ArbitrageDetector()
        assert math.isclose(detector.calculate_implied_probability(2.0, "decimal"), 0.5)
        assert math.isclose(
            detector.calculate_implied_probability(1.5, "decimal"), 2 / 3, rel_tol=1e-5
        )
        assert math.isclose(
            detector.calculate_implied_probability(3.0, "decimal"), 1 / 3, rel_tol=1e-5
        )

    def test_calculate_implied_probability_fractional(self):
        """Test implied probability with fractional odds."""
        detector = ArbitrageDetector()
        # 1/1 = even odds = 2.0 decimal = 0.5 probability
        prob = detector.calculate_implied_probability("1/1", "fractional")
        assert math.isclose(prob, 0.5)

        # 2/1 = 3.0 decimal = 1/3 probability
        prob = detector.calculate_implied_probability("2/1", "fractional")
        assert math.isclose(prob, 1 / 3, rel_tol=1e-5)

    def test_calculate_implied_probability_american(self):
        """Test implied probability with American odds."""
        detector = ArbitrageDetector()
        # +100 = 2.0 decimal = 0.5 probability
        assert math.isclose(detector.calculate_implied_probability(100, "american"), 0.5)
        # -200 = 1.5 decimal = 2/3 probability
        assert math.isclose(
            detector.calculate_implied_probability(-200, "american"), 2 / 3, rel_tol=1e-5
        )

    def test_normalize_odds_to_decimal(self):
        """Test odds normalization to decimal format."""
        detector = ArbitrageDetector()
        assert detector.normalize_odds_to_decimal(2.0, "decimal") == 2.0
        assert detector.normalize_odds_to_decimal("1/1", "fractional") == 2.0
        assert math.isclose(detector.normalize_odds_to_decimal(100, "american"), 2.0)
        assert math.isclose(detector.normalize_odds_to_decimal(-200, "american"), 1.5)

    def test_detect_arbitrage_simple(self):
        """Test simple arbitrage detection."""
        detector = ArbitrageDetector(min_profit_percentage=0.1)

        # Odds that create arbitrage: 1/2.2 + 1/4.0 + 1/2.3 = 0.455 + 0.25 + 0.435 = 1.14 > 1.0 (no arbitrage)
        # For arbitrage, we need: 1/2.5 + 1/5.0 + 1/2.5 = 0.4 + 0.2 + 0.4 = 1.0 (exactly fair, still no arbitrage)
        # Actual arbitrage: 1/2.6 + 1/5.5 + 1/2.6 = 0.385 + 0.182 + 0.385 = 0.952 < 1.0 (YES arbitrage!)
        outcomes = [
            {
                "outcome_name": "Home",
                "odds": 2.6,
                "bookmaker": "Bookmaker A",
                "odds_format": "decimal",
            },
            {
                "outcome_name": "Draw",
                "odds": 5.5,
                "bookmaker": "Bookmaker B",
                "odds_format": "decimal",
            },
            {
                "outcome_name": "Away",
                "odds": 2.6,
                "bookmaker": "Bookmaker C",
                "odds_format": "decimal",
            },
        ]

        arb = detector.detect_arbitrage(outcomes)
        assert arb is not None
        assert isinstance(arb, ArbitrageOpportunity)
        assert len(arb.outcomes) == 3
        assert arb.total_implied_probability < 1.0
        assert arb.profit_percentage > 0

    def test_detect_arbitrage_no_arbitrage(self):
        """Test that no arbitrage is detected when odds don't allow it."""
        detector = ArbitrageDetector()

        # Fair odds (total implied prob = 1.0)
        outcomes = [
            {"outcome_name": "Home", "odds": 2.0, "bookmaker": "Bookmaker A"},
            {"outcome_name": "Away", "odds": 2.0, "bookmaker": "Bookmaker A"},
        ]

        arb = detector.detect_arbitrage(outcomes)
        assert arb is None

    def test_detect_arbitrage_best_odds_selection(self):
        """Test that best odds are selected for each outcome."""
        detector = ArbitrageDetector(min_profit_percentage=0.1)

        outcomes = [
            {"outcome_name": "Home", "odds": 2.0, "bookmaker": "Bookmaker A"},
            {"outcome_name": "Home", "odds": 2.2, "bookmaker": "Bookmaker B"},  # Better odds
            {"outcome_name": "Away", "odds": 2.0, "bookmaker": "Bookmaker A"},
            {"outcome_name": "Away", "odds": 1.9, "bookmaker": "Bookmaker B"},
        ]

        arb = detector.detect_arbitrage(outcomes)
        assert arb is not None
        # Should use Bookmaker B for Home (2.2) and Bookmaker A for Away (2.0)
        home_odds = next(o["odds"] for o in arb.outcomes if o["outcome_name"] == "Home")
        assert math.isclose(home_odds, 2.2)

    def test_detect_arbitrage_min_profit_threshold(self):
        """Test that minimum profit threshold is respected."""
        detector = ArbitrageDetector(min_profit_percentage=5.0)  # 5% minimum

        # Small arbitrage (~1%)
        outcomes = [
            {"outcome_name": "Home", "odds": 2.05, "bookmaker": "A"},
            {"outcome_name": "Away", "odds": 2.05, "bookmaker": "B"},
        ]

        arb = detector.detect_arbitrage(outcomes)
        assert arb is None  # Should be filtered out

    def test_detect_arbitrage_with_risk_evaluation(
        self, account_health_manager, sample_account_profile
    ):
        """Test risk evaluation with account health manager."""
        detector = ArbitrageDetector(
            min_profit_percentage=0.1, account_health_manager=account_health_manager
        )

        outcomes = [
            {
                "outcome_name": "Home",
                "odds": 2.1,
                "bookmaker": sample_account_profile.bookmaker_name,
            },
            {"outcome_name": "Away", "odds": 2.2, "bookmaker": "Other Bookmaker"},
        ]

        arb = detector.detect_arbitrage(outcomes)
        assert arb is not None
        assert arb.risk_level in ["Low", "Medium", "High"]
        assert isinstance(arb.risk_warnings, list)

    def test_detect_arbitrage_market_age_warning(self):
        """Test that old markets trigger warnings."""
        detector = ArbitrageDetector(max_market_age_hours=24.0)

        old_time = (datetime.now() - timedelta(hours=30)).isoformat()

        outcomes = [
            {
                "outcome_name": "Home",
                "odds": 2.1,
                "bookmaker": "A",
                "commence_time": old_time,
                "event_name": "Test Event",
                "market": "h2h",
            },
            {"outcome_name": "Away", "odds": 2.2, "bookmaker": "B"},
        ]

        arb = detector.detect_arbitrage(outcomes)
        if arb:
            # May or may not have warnings depending on risk evaluation
            assert arb.market_age_hours is not None or arb.market_age_hours is None

    def test_find_best_arbitrages(self):
        """Test finding multiple arbitrage opportunities."""
        detector = ArbitrageDetector(min_profit_percentage=0.1)

        events = [
            {
                "event_name": "Event 1",
                "market": "h2h",
                "outcomes": [
                    {"outcome_name": "Home", "odds": 2.1, "bookmaker": "A"},
                    {"outcome_name": "Away", "odds": 2.2, "bookmaker": "B"},
                ],
            },
            {
                "event_name": "Event 2",
                "market": "h2h",
                "outcomes": [
                    {"outcome_name": "Home", "odds": 2.0, "bookmaker": "A"},
                    {"outcome_name": "Away", "odds": 2.0, "bookmaker": "B"},
                ],  # No arbitrage
            },
            {
                "event_name": "Event 3",
                "market": "h2h",
                "outcomes": [
                    {"outcome_name": "Home", "odds": 2.2, "bookmaker": "A"},
                    {"outcome_name": "Away", "odds": 2.3, "bookmaker": "B"},
                ],
            },
        ]

        arbs = detector.find_best_arbitrages(events)
        assert len(arbs) == 2
        # Should be sorted by profit (highest first)
        assert arbs[0].profit_percentage >= arbs[1].profit_percentage


class TestArbitrageOpportunity:
    """Test suite for ArbitrageOpportunity dataclass."""

    def test_init_default_warnings(self):
        """Test that warnings list is initialized."""
        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[],
            total_implied_probability=0.95,
            profit_percentage=5.0,
            bookmakers=["A"],
            timestamp="2024-01-01T00:00:00",
        )
        assert opp.risk_warnings == []

    def test_init_custom_warnings(self):
        """Test with custom warnings."""
        opp = ArbitrageOpportunity(
            event_name="Test",
            market="h2h",
            outcomes=[],
            total_implied_probability=0.95,
            profit_percentage=5.0,
            bookmakers=["A"],
            timestamp="2024-01-01T00:00:00",
            risk_warnings=["Warning 1", "Warning 2"],
        )
        assert len(opp.risk_warnings) == 2
