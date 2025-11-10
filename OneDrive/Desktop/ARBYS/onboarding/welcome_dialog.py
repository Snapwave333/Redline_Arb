"""
Welcome dialog for first-time users.

Rich modal dialog introducing ARBYS features with action buttons.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class WelcomeDialog(QDialog):
    """
    Welcome dialog for first-time users.

    Shows introduction text, feature cards, and action buttons.
    """

    start_tutorial_requested = pyqtSignal()
    open_setup_wizard_requested = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize welcome dialog."""
        super().__init__(parent)
        self.setWindowTitle("Welcome to ARBYS")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.setMaximumSize(900, 750)

        self.show_on_startup = True

        self._setup_ui()
        self._center_on_screen()

    def _center_on_screen(self):
        """Center dialog on parent window or screen."""
        from PyQt6.QtWidgets import QApplication

        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2,
            )
        else:
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def _setup_ui(self):
        """Setup welcome dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_label = QLabel("Welcome to ARBYS")
        header_font = QFont("Arial", 24, QFont.Weight.Bold)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #E6E6E6; margin-bottom: 10px;")
        layout.addWidget(header_label)

        # Subtitle
        subtitle_label = QLabel("Your Arbitrage Betting Assistant")
        subtitle_font = QFont("Arial", 12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #9AA0A6; margin-bottom: 20px;")
        layout.addWidget(subtitle_label)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # Introduction text
        intro_text = QTextEdit()
        intro_text.setReadOnly(True)
        intro_text.setMaximumHeight(120)
        intro_text.setHtml(
            """
            <p style="color: #E6E6E6; line-height: 1.6;">
                ARBYS is a powerful arbitrage betting bot that helps you identify 
                and capitalize on profitable opportunities across multiple sportsbooks. 
                The application automatically scans for arbitrage opportunities, calculates 
                optimal stake distributions, and monitors your account health to minimize 
                detection risks.
            </p>
        """
        )
        intro_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #16171A;
                border: 1px solid #2A2C31;
                border-radius: 4px;
                padding: 10px;
            }
        """
        )
        content_layout.addWidget(intro_text)

        # Feature cards
        features_label = QLabel("Key Features")
        features_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        features_label.setStyleSheet("color: #E6E6E6; margin-top: 10px;")
        content_layout.addWidget(features_label)

        # Feature cards container
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(10)

        self._add_feature_card(
            cards_layout,
            "🔌 Providers",
            "Configure multiple odds API providers (SofaScore, API-Sports) for fault tolerance. The bot automatically switches to backup providers if the primary fails.",
        )

        self._add_feature_card(
            cards_layout,
            "📚 Bookmakers",
            "Add and manage your bookmaker accounts. Track account health, stealth scores, and betting history across all your accounts.",
        )

        self._add_feature_card(
            cards_layout,
            "💰 Bankroll & Stakes",
            "Intelligent stake calculator determines optimal bet distribution for maximum guaranteed profit. Supports dynamic rounding and variation for anti-detection.",
        )

        self._add_feature_card(
            cards_layout,
            "🛡️ Safety",
            "Advanced account health monitoring with stealth scores, risk warnings, and automatic stake adjustments to minimize account closure risk.",
        )

        content_layout.addLayout(cards_layout)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Checkbox
        self.show_on_startup_checkbox = QCheckBox("Show this screen on startup")
        self.show_on_startup_checkbox.setChecked(True)
        self.show_on_startup_checkbox.setStyleSheet("color: #E6E6E6;")
        self.show_on_startup_checkbox.toggled.connect(
            lambda checked: setattr(self, "show_on_startup", checked)
        )
        layout.addWidget(self.show_on_startup_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        tutorial_btn = QPushButton("Start Guided Tutorial")
        tutorial_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #D00000;
                border: 1px solid #FF0033;
                border-radius: 4px;
                padding: 10px 20px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF0033;
                box-shadow: 0 0 10px rgba(208, 0, 0, 0.6);
            }
        """
        )
        tutorial_btn.clicked.connect(self._on_start_tutorial)
        button_layout.addWidget(tutorial_btn)

        setup_btn = QPushButton("Open Setup Wizard")
        setup_btn.clicked.connect(self._on_open_setup_wizard)
        button_layout.addWidget(setup_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _add_feature_card(self, layout, title: str, description: str):
        """Add a feature card to the layout."""
        card = QWidget()
        card.setProperty("card", True)
        card.setStyleSheet(
            """
            QWidget[card="true"] {
                background-color: #1C1D22;
                border: 1px solid #2A2C31;
                border-radius: 6px;
                padding: 15px;
            }
        """
        )

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #E6E6E6;")
        card_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #9AA0A6;")
        card_layout.addWidget(desc_label)

        layout.addWidget(card)

    def _on_start_tutorial(self):
        """Handle Start Tutorial button click."""
        self.start_tutorial_requested.emit()
        self.accept()

    def _on_open_setup_wizard(self):
        """Handle Open Setup Wizard button click."""
        self.open_setup_wizard_requested.emit()
        # Don't close dialog - user might want to continue after setup

    def should_show_on_startup(self) -> bool:
        """Check if dialog should be shown on startup."""
        return self.show_on_startup
