"""
Test configuration and fixtures for ARBYS bot testing.
"""

import os
import sys
from pathlib import Path

import pytest
from hypothesis import Verbosity, settings

# Set test environment variables before any imports
os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("ODDS_API_KEY", "TEST_KEY")
os.environ.setdefault("ARBYS_SUPPRESS_WIZARD", "1")

# Set QTWEBENGINE flags for test stability
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--single-process --disable-gpu")

# Note: WebEngine tests will be skipped individually if module missing
# Don't skip entire test suite just because WebEngine is unavailable

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Hypothesis settings (must be before imports that use it)
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=50, verbosity=Verbosity.quiet)
settings.load_profile("default")

# Import test dependencies (after hypothesis settings)
from src.account_health import AccountHealthManager  # noqa: E402
from src.account_manager import AccountDatabase, AccountProfile  # noqa: E402
from src.api_providers.sofascore_scraper import SofaScoreScraperProvider  # noqa: E402
from src.arbitrage import ArbitrageDetector  # noqa: E402
from src.arbitrage_optimized import OptimizedArbitrageDetector  # noqa: E402
from src.data_orchestrator import MultiAPIOrchestrator  # noqa: E402
from src.data_orchestrator_async import AsyncMultiAPIOrchestrator  # noqa: E402
from src.stake_calculator import StakeCalculator  # noqa: E402


@pytest.fixture(autouse=True)
def _ensure_logs(tmp_path, monkeypatch):
    """Ensure logs and data directories exist for all tests."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ARBYS_LOG_DIR", str(log_dir))

    # Ensure config/data dirs exist
    data_dir = tmp_path / "config"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ARBYS_DATA_DIR", str(data_dir))


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing."""
    db_path = tmp_path / "test_accounts.db"
    yield str(db_path)


@pytest.fixture
def account_health_manager(temp_db):
    """Create AccountHealthManager with temporary database."""
    return AccountHealthManager(db_path=temp_db, enable_cache=True)


@pytest.fixture
def account_db(temp_db):
    """Create AccountDatabase with temporary database."""
    return AccountDatabase(db_path=temp_db)


@pytest.fixture
def sample_account_profile(account_db):
    """Create sample account profile for testing."""
    profile = AccountProfile(
        bookmaker_name="TestBookmaker",
        account_username="test_account",
        stealth_score=0.9,
        account_status="Healthy",
    )
    account_id = account_db.create_account(profile)
    profile.id = account_id
    return profile


@pytest.fixture
def low_stealth_account_profile(account_db):
    """Create low stealth score account for testing."""
    profile = AccountProfile(
        bookmaker_name="LowStealthBookmaker",
        account_username="low_stealth_account",
        stealth_score=0.15,  # Critical level
        account_status="Under Review",
    )
    account_id = account_db.create_account(profile)
    profile.id = account_id
    return profile


@pytest.fixture
def sample_odds_data():
    """Sample odds data for testing arbitrage detection."""
    return [
        {
            "event_name": "Soccer - Team A vs Team B",
            "market": "h2h",
            "outcome_name": "Team A",
            "odds": 2.10,
            "odds_format": "decimal",
            "bookmaker": "Bookmaker A",
        },
        {
            "event_name": "Soccer - Team A vs Team B",
            "market": "h2h",
            "outcome_name": "Draw",
            "odds": 3.50,
            "odds_format": "decimal",
            "bookmaker": "Bookmaker B",
        },
        {
            "event_name": "Soccer - Team A vs Team B",
            "market": "h2h",
            "outcome_name": "Team B",
            "odds": 2.20,
            "odds_format": "decimal",
            "bookmaker": "Bookmaker C",
        },
    ]


@pytest.fixture
def arbitrage_detector(account_health_manager):
    """Create ArbitrageDetector instance."""
    return ArbitrageDetector(
        min_profit_percentage=1.0, account_health_manager=account_health_manager
    )


@pytest.fixture
def optimized_detector(account_health_manager):
    """Create OptimizedArbitrageDetector instance."""
    return OptimizedArbitrageDetector(
        min_profit_percentage=1.0, account_health_manager=account_health_manager
    )


@pytest.fixture
def stake_calculator(account_health_manager):
    """Create StakeCalculator instance."""
    return StakeCalculator(
        round_stakes=True,
        max_variation_percent=5.0,
        account_health_manager=account_health_manager,
        min_stake_threshold=10.0,
    )


@pytest.fixture
def real_providers():
    """Create real API providers for testing - requires API keys or SofaScore."""
    providers = []

    # SofaScore scraper (free, no API key needed)
    try:
        provider = SofaScoreScraperProvider(api_key="test", enabled=True, priority=1)
        providers.append(provider)
    except Exception:
        pass

    # Add other real providers if API keys are available
    import os

    if os.getenv("ODDS_API_KEY"):
        from src.api_providers.the_odds_api import TheOddsAPIProvider

        try:
            provider = TheOddsAPIProvider(
                api_key=os.getenv("ODDS_API_KEY"), enabled=True, priority=2
            )
            providers.append(provider)
        except Exception:
            pass

    if not providers:
        pytest.skip("SofaScore Scraper not available - check internet connection")

    return providers


@pytest.fixture
def orchestrator(real_providers):
    """Create MultiAPIOrchestrator with real providers."""
    return MultiAPIOrchestrator(providers=real_providers, failover_enabled=True)


@pytest.fixture
def async_orchestrator(real_providers):
    """Create AsyncMultiAPIOrchestrator with real providers."""
    return AsyncMultiAPIOrchestrator(providers=real_providers, failover_enabled=True, max_workers=5)
