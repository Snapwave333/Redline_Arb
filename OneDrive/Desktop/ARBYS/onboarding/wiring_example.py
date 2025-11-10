"""
Bootstrap function for ARBYS application startup.

Orchestrates splash screen, welcome dialog, tutorial, and tooltips.
"""

import logging
import os
from collections.abc import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow

from gui.theme_utils import load_theme_stylesheet
from onboarding.first_run_manager import load_flags, save_flags
from onboarding.splash_screen import Splash
from onboarding.tooltips import apply_tooltips
from onboarding.tutorial_overlay import OnboardingTour
from onboarding.welcome_dialog import WelcomeDialog

logger = logging.getLogger(__name__)


def bootstrap_app(app: QApplication, main_window_factory: Callable[[], QMainWindow]) -> None:
    """
    Bootstrap ARBYS application with onboarding flow.

    Flow:
    1. Show splash screen
    2. Construct main window (hidden)
    3. Load first-run flags
    4. Show welcome dialog if first run
    5. Start tutorial if not completed
    6. Apply tooltips
    7. Finish splash and show main window

    Args:
        app: QApplication instance
        main_window_factory: Callable that returns QMainWindow instance
    """
    # Setup theme
    app.setStyle("Fusion")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stylesheet = load_theme_stylesheet(project_root)
    if stylesheet:
        app.setStyleSheet(stylesheet)
    else:
        logger.warning("Theme not loaded, using default Fusion style")

    # Create and show splash screen
    splash = Splash()
    splash.start(2500)  # Show for 2.5 seconds minimum

    # Construct main window (hidden)
    main_window = main_window_factory()

    # Load first-run flags
    flags = load_flags()

    # Prepare tutorial steps (will be used if needed)
    tutorial_steps = []
    tour: OnboardingTour = None

    def prepare_tutorial_steps():
        """Prepare tutorial steps from main window widgets."""
        nonlocal tutorial_steps, tour

        steps = []

        # Get widget registry from main window
        if hasattr(main_window, "get_widget_registry"):
            registry = main_window.get_widget_registry()
        else:
            registry = {}

        # Step 1: Scan button
        if "btn_scan" in registry and registry["btn_scan"]:
            steps.append(
                (
                    registry["btn_scan"],
                    "Scan for Opportunities",
                    "Click the 'Refresh Now' button to manually scan for arbitrage opportunities. "
                    "The bot automatically updates every 30 seconds, but you can force an immediate refresh.",
                )
            )

        # Step 2: Opportunities table
        if "tbl_opportunities" in registry and registry["tbl_opportunities"]:
            steps.append(
                (
                    registry["tbl_opportunities"],
                    "Opportunities Table",
                    "This table shows all available arbitrage opportunities. Select any row to see "
                    "stake calculations. Opportunities are sorted by profit percentage.",
                )
            )

        # Step 3: Stake calculator
        if "panel_calc" in registry and registry["panel_calc"]:
            steps.append(
                (
                    registry["panel_calc"],
                    "Stake Calculator",
                    "Enter your total stake amount and click 'Calculate Stakes' to see the optimal "
                    "distribution across all outcomes. The calculator ensures maximum guaranteed profit.",
                )
            )

        # Step 4: Account health (optional)
        if "panel_health" in registry and registry["panel_health"]:
            steps.append(
                (
                    registry["panel_health"],
                    "Account Health",
                    "Monitor your bookmaker account health and stealth scores. Green indicates healthy "
                    "accounts, while orange or red means increased risk. Keep stealth scores high to "
                    "minimize account closure risk.",
                )
            )

        tutorial_steps = steps
        return steps

    # Show welcome dialog if first run
    should_show_welcome = not flags.get("has_seen_welcome", False) or flags.get(
        "show_welcome_on_startup", True
    )

    if should_show_welcome and len(flags.get("last_version_seen", "")) == 0:
        welcome = WelcomeDialog(main_window)

        # Handle welcome dialog signals
        def on_start_tutorial():
            """Handle start tutorial from welcome dialog."""
            prepare_tutorial_steps()
            if tutorial_steps:
                start_tutorial()
            else:
                logger.warning("No tutorial steps available")

        def on_open_setup_wizard():
            """Handle open setup wizard from welcome dialog."""
            if hasattr(main_window, "open_setup_wizard"):
                main_window.open_setup_wizard()
            elif hasattr(main_window, "show_setup_wizard"):
                main_window.show_setup_wizard()
            else:
                logger.warning("Setup wizard method not found")

        welcome.start_tutorial_requested.connect(on_start_tutorial)
        welcome.open_setup_wizard_requested.connect(on_open_setup_wizard)

        # Show welcome dialog (modal)
        welcome.exec()

        # Update flags
        flags["has_seen_welcome"] = True
        flags["show_welcome_on_startup"] = welcome.should_show_on_startup()
        save_flags(flags)

    # Start tutorial if not completed
    should_show_tutorial = not flags.get("has_completed_tutorial", False)

    def start_tutorial():
        """Start the tutorial tour."""
        nonlocal tour

        if not tutorial_steps:
            prepare_tutorial_steps()

        if not tutorial_steps:
            logger.warning("No tutorial steps available")
            finish_bootstrap()
            return

        tour = OnboardingTour(tutorial_steps, main_window)

        def on_tutorial_finished():
            """Handle tutorial completion."""
            flags["has_completed_tutorial"] = True
            save_flags(flags)
            finish_bootstrap()

        tour.finished.connect(on_tutorial_finished)

        # Small delay to ensure main window is ready
        QTimer.singleShot(300, lambda: tour.show())

    def finish_bootstrap():
        """Finish bootstrap and show main window."""
        # Apply tooltips
        if hasattr(main_window, "get_widget_registry"):
            registry = main_window.get_widget_registry()
            # Map registry keys to tooltip keys
            tooltip_registry = {
                "scan_button": registry.get("btn_scan"),
                "stake_input": registry.get("stake_input"),
                "account_health": registry.get("panel_health"),
                "providers": registry.get("btn_providers"),
                "delay_badge": registry.get("badge_delay"),
            }
            apply_tooltips(tooltip_registry)

        # Finish splash and show main window
        splash.finish(main_window)

    # Determine if we should show tutorial
    if should_show_tutorial:
        # Prepare steps
        prepare_tutorial_steps()

        # Wait a bit for splash, then start tutorial
        def delayed_tutorial_start():
            if tutorial_steps:
                start_tutorial()
            else:
                finish_bootstrap()

        # Wait for splash to finish or timeout
        QTimer.singleShot(2800, delayed_tutorial_start)
    else:
        # No tutorial, just finish bootstrap
        QTimer.singleShot(2800, finish_bootstrap)

    # Run application event loop
    # Note: app.exec() should be called by caller (main.py)
    # We just set everything up here
