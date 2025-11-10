"""
Centralized tooltip registry for ARBYS application.

Provides consistent tooltips across the application with easy management.
"""

# Tooltip registry
# Maps widget identifier keys to tooltip text
TOOLTIPS: dict[str, str] = {
    "scan_button": (
        "Manually refresh odds data from configured API providers. "
        "The bot automatically updates every 30 seconds, but you can force "
        "an immediate refresh by clicking this button."
    ),
    "stake_input": (
        "Enter your total stake amount for the selected arbitrage opportunity. "
        "The calculator will automatically distribute this amount across all "
        "outcomes to maximize guaranteed profit."
    ),
    "account_health": (
        "Monitor the health and stealth scores of your bookmaker accounts. "
        "Green indicates healthy accounts, orange means under review, and red "
        "indicates limited or closed accounts. Stealth scores help track "
        "detection risk."
    ),
    "providers": (
        "Configure and manage API providers for odds data. ARBYS supports "
        "multiple providers with automatic failover. Set up providers like "
        "SofaScore Scraper (free) or API-Sports for reliable data feeds."
    ),
    "delay_badge": (
        "Shows the recommended delay countdown between placing bets. "
        "To minimize detection, place bets with at least 15 seconds between "
        "each bet. The countdown helps ensure proper timing."
    ),
}


def apply_tooltips(registry: dict[str, object]) -> None:
    """
    Apply tooltips to widgets in registry.

    Maps tooltip keys to widgets and sets tooltip text.
    Skips silently if widget is missing from registry or not a QWidget.

    Args:
        registry: Dictionary mapping tooltip keys to widget objects.
                 Keys should match TOOLTIPS keys (e.g., "scan_button").
                 Values should be QWidget instances or None.
    """
    from PyQt6.QtWidgets import QWidget

    for key, tooltip_text in TOOLTIPS.items():
        if key not in registry:
            continue

        widget = registry[key]
        if widget is None:
            continue

        # Check if it's a QWidget (or has setToolTip method)
        if not isinstance(widget, QWidget) and not hasattr(widget, "setToolTip"):
            continue

        try:
            widget.setToolTip(tooltip_text)
        except Exception as e:
            # Silently skip on error (widget might not support tooltips)
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Could not set tooltip for {key}: {e}")
            continue
