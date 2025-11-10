"""
Theme utility functions for consistent theme application across the GUI.
"""

import logging
import os

from PyQt6.QtWidgets import QPushButton

logger = logging.getLogger(__name__)


def load_theme_stylesheet(project_root: str = None) -> str:
    """
    Load the carbon fiber + red theme stylesheet.

    Args:
        project_root: Root directory of the project. If None, attempts to auto-detect.

    Returns:
        Stylesheet string, or empty string if theme not found.
    """
    if project_root is None:
        # Try to detect project root
        current_file = os.path.abspath(__file__)
        # Assuming we're in gui/theme_utils.py, go up one level to project root
        project_root = os.path.dirname(os.path.dirname(current_file))

    theme_path = os.path.join(project_root, "looks", "themes", "carbon_red.qss")

    if not os.path.exists(theme_path):
        logger.warning(f"Theme file not found at: {theme_path}")
        return ""

    try:
        with open(theme_path, encoding="utf-8") as f:
            stylesheet = f.read()

        # Replace relative SVG path with absolute path
        svg_path = os.path.join(project_root, "looks", "assets", "carbon_fiber_tile.svg")
        if os.path.exists(svg_path):
            svg_path = svg_path.replace("\\", "/")
            stylesheet = stylesheet.replace(
                "url(../assets/carbon_fiber_tile.svg)", f"url({svg_path})"
            )

        logger.info("Theme loaded successfully")
        return stylesheet
    except Exception as e:
        logger.error(f"Error loading theme: {e}")
        return ""


def apply_accent_button(button: QPushButton):
    """
    Apply accent styling to a button (red glow on hover).

    Args:
        button: QPushButton to style
    """
    if button:
        button.setProperty("accent", True)
        button.style().unpolish(button)
        button.style().polish(button)


def polish_widget(widget):
    """
    Helper to polish a widget to apply property-based styles.

    Args:
        widget: Widget to polish
    """
    if widget:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
