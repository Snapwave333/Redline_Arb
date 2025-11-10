"""GUI smoke tests for main window."""

import sys

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for GUI tests."""
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    yield app
    # Cleanup handled by pytest-qt


@pytest.mark.gui
def test_main_window_creation(qtbot, qapp):
    """Test that main window can be created."""
    from config.settings import Config
    from gui.main_window import ArbitrageBotGUI

    # Ensure Config has ODDS_API_KEY attribute (should be set by conftest)
    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    window = ArbitrageBotGUI()
    window.set_update_thread_enabled(False)  # Disable thread for test stability

    assert window is not None
    assert hasattr(window, "show")


@pytest.mark.gui
def test_main_window_visibility(qtbot, qapp):
    """Test that main window can be shown."""
    from config.settings import Config
    from gui.main_window import ArbitrageBotGUI

    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    window = ArbitrageBotGUI()
    window.set_update_thread_enabled(False)
    window.show()

    assert window.isVisible()


@pytest.mark.gui
def test_main_window_widgets_initialized(qtbot, qapp):
    """Test that main window widgets are initialized."""
    from config.settings import Config
    from gui.main_window import ArbitrageBotGUI

    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    window = ArbitrageBotGUI()
    window.set_update_thread_enabled(False)

    # Check for key widgets
    assert hasattr(window, "account_health_manager")
    assert hasattr(window, "arbitrage_detector")
    assert hasattr(window, "stake_calculator")


@pytest.mark.gui
@pytest.mark.slow
def test_main_window_close(qtbot, qapp):
    """Test that main window can be closed."""
    from config.settings import Config
    from gui.main_window import ArbitrageBotGUI

    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    window = ArbitrageBotGUI()
    window.set_update_thread_enabled(False)
    window.show()

    # Close window
    window.close()

    assert window.isHidden() or not window.isVisible()
