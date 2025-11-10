"""Extended GUI smoke tests for main window features."""

import sys
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from src.arbitrage import ArbitrageOpportunity


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for GUI tests."""
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    yield app


@pytest.mark.gui
def test_opportunities_table_population(qtbot, qapp):
    """Test that opportunities table populates with fake events."""
    from config.settings import Config
    from gui.main_window import ArbitrageBotGUI

    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    window = ArbitrageBotGUI()
    window.set_update_thread_enabled(False)

    # Create fake arbitrage opportunities
    fake_arb1 = ArbitrageOpportunity(
        event_name="Test Event 1",
        market="h2h",
        outcomes=[
            {"outcome_name": "Home", "odds": 2.1, "bookmaker": "A"},
            {"outcome_name": "Away", "odds": 2.15, "bookmaker": "B"},
        ],
        total_implied_probability=0.95,
        profit_percentage=5.26,
        bookmakers=["A", "B"],
        timestamp="2024-01-01T12:00:00",
    )

    fake_arb2 = ArbitrageOpportunity(
        event_name="Test Event 2",
        market="h2h",
        outcomes=[
            {"outcome_name": "Home", "odds": 2.2, "bookmaker": "C"},
            {"outcome_name": "Away", "odds": 2.3, "bookmaker": "D"},
        ],
        total_implied_probability=0.97,
        profit_percentage=3.09,
        bookmakers=["C", "D"],
        timestamp="2024-01-01T13:00:00",
    )

    # Populate table
    window.current_arbitrages = [fake_arb1, fake_arb2]
    window.update_arbitrage_table()

    # Verify table has rows
    assert window.arbitrage_table.rowCount() == 2
    assert window.arbitrage_table.item(0, 0) is not None
    assert window.arbitrage_table.item(0, 0).text() == "Test Event 1"


@pytest.mark.gui
def test_stake_calculator_interaction(qtbot, qapp):
    """Test stake calculator interaction when arbitrage is selected."""
    from config.settings import Config
    from gui.main_window import ArbitrageBotGUI

    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    window = ArbitrageBotGUI()
    window.set_update_thread_enabled(False)

    # Create and select a fake arbitrage
    fake_arb = ArbitrageOpportunity(
        event_name="Test Event",
        market="h2h",
        outcomes=[
            {"outcome_name": "Home", "odds": 2.1, "bookmaker": "A"},
            {"outcome_name": "Away", "odds": 2.15, "bookmaker": "B"},
        ],
        total_implied_probability=0.95,
        profit_percentage=5.26,
        bookmakers=["A", "B"],
        timestamp="2024-01-01T12:00:00",
    )

    window.current_arbitrages = [fake_arb]
    window.selected_arbitrage = fake_arb
    if hasattr(window, "on_arbitrage_selected"):
        window.on_arbitrage_selected(0, 0)

    # Verify stake input exists and can be interacted with
    assert hasattr(window, "stake_input")
    if hasattr(window, "stake_input"):
        # Widget exists and can be set
        window.stake_input.setValue(100.0)
        qtbot.wait(100)  # Allow signal processing

        # Calculate stakes button should exist and be enabled if it exists
        if hasattr(window, "calc_btn") and window.calc_btn is not None:
            assert window.calc_btn.isEnabled()


@pytest.mark.gui
def test_help_slideshow_action(qtbot, qapp):
    """Test Help→First-Day Slideshow action (skip WebEngine in CI)."""
    from config.settings import Config
    from gui.main_window import ArbitrageBotGUI

    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    window = ArbitrageBotGUI()
    window.set_update_thread_enabled(False)

    # Check if WebEngine is available
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401

        webengine_available = True
    except ImportError:
        webengine_available = False

    # In test mode or if WebEngine unavailable, should handle gracefully
    if not webengine_available or Config.TEST_MODE:
        # Should not crash
        try:
            window.show_firstday_slideshow()
        except Exception as e:
            # Expected to fail gracefully
            assert "WebEngine" in str(e) or "slideshow" in str(e).lower()
    else:
        # If WebEngine available and not in test mode, try to show
        with patch("gui.ui_firstday_slideshow.QWebEngineView") as mock_web:
            mock_web.return_value.load = Mock()
            window.show_firstday_slideshow()
