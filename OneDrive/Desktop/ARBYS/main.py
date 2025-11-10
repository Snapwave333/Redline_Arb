"""
Main entry point for the Arbitrage Betting Bot.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

from gui.main_window import ArbitrageBotGUI
from onboarding.wiring_example import bootstrap_app


def main_window_factory():
    """Factory function to create main window instance."""
    return ArbitrageBotGUI()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bootstrap_app(app, main_window_factory)
    sys.exit(app.exec())
