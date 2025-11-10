"""GUI smoke tests for dialogs."""

import contextlib
import sys

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for GUI tests."""
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    yield app


@pytest.mark.gui
def test_account_dialog_creation(qtbot, qapp):
    """Test that account dialog can be created."""
    from gui.account_dialog import AccountDialog

    dialog = AccountDialog(parent=None)
    # QDialog is a QWidget, so we can add it
    if hasattr(qtbot, "addWidget"):
        with contextlib.suppress(TypeError):
            # Some pytest-qt versions require QWidget explicitly
            qtbot.addWidget(dialog)

    assert dialog is not None
    assert dialog.isWidgetType()


@pytest.mark.gui
def test_setup_wizard_creation(qtbot, qapp):
    """Test that setup wizard can be created."""
    from config.settings import Config
    from gui.setup_wizard import SetupWizard

    # Ensure Config has ODDS_API_KEY attribute (should be set by conftest)
    if not hasattr(Config, "ODDS_API_KEY"):
        Config.ODDS_API_KEY = ""

    wizard = SetupWizard(parent=None)
    if hasattr(qtbot, "addWidget"):
        with contextlib.suppress(TypeError):
            qtbot.addWidget(wizard)

    assert wizard is not None
    assert wizard.isWidgetType()


@pytest.mark.gui
def test_api_provider_dialog_creation(qtbot, qapp):
    """Test that API provider dialog can be created."""
    from gui.api_provider_dialog import APIProviderDialog

    dialog = APIProviderDialog(parent=None)
    if hasattr(qtbot, "addWidget"):
        with contextlib.suppress(TypeError):
            qtbot.addWidget(dialog)

    assert dialog is not None
    assert dialog.isWidgetType()
