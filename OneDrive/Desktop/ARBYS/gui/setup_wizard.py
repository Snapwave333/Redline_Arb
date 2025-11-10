"""
Configuration wizard for initial setup and bookmaker management.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config.settings import Config
from gui.api_provider_dialog import APIProviderDialog
from src.account_manager import AccountDatabase


class SetupWizard(QDialog):
    """Initial setup wizard for first-time users."""

    def __init__(self, parent=None):
        """Initialize setup wizard."""
        super().__init__(parent)
        self.setWindowTitle("Initial Setup - Redline Arbitrage")
        self.setGeometry(200, 200, 800, 600)

        self.init_ui()

        # Check if this is first run
        if not Config.ODDS_API_KEY:
            self.show_first_run_message()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Arbitrage Bot Configuration")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header_label)

        # Create tabbed interface
        tabs = QTabWidget()

        # Tab 1: API Providers
        api_tab = QWidget()
        api_tab_layout = QVBoxLayout(api_tab)

        api_info = QLabel(
            "Configure multiple odds API providers for fault tolerance.\n"
            "The bot will automatically use backup providers if the primary fails."
        )
        api_info.setWordWrap(True)
        api_tab_layout.addWidget(api_info)

        manage_providers_btn = QPushButton("Manage API Providers")
        manage_providers_btn.clicked.connect(self.show_provider_dialog)
        api_tab_layout.addWidget(manage_providers_btn)

        # Legacy API key section (for backward compatibility)
        legacy_group = QGroupBox("Legacy Single API Configuration")
        legacy_layout = QVBoxLayout()

        legacy_layout.addWidget(QLabel("The Odds API Key:"))
        legacy_layout.addWidget(
            QLabel("Get your API key from:\n" "• The Odds API: https://the-odds-api.com/")
        )

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(Config.ODDS_API_KEY)
        self.api_key_input.setPlaceholderText("Enter your API key")
        legacy_layout.addWidget(self.api_key_input)

        legacy_btn_layout = QHBoxLayout()
        test_api_btn = QPushButton("Test API Key")
        test_api_btn.clicked.connect(self.test_api_key)
        legacy_btn_layout.addWidget(test_api_btn)

        save_api_btn = QPushButton("Save API Key")
        save_api_btn.clicked.connect(self.save_api_key)
        legacy_btn_layout.addWidget(save_api_btn)
        legacy_layout.addLayout(legacy_btn_layout)

        legacy_group.setLayout(legacy_layout)
        api_tab_layout.addWidget(legacy_group)

        api_tab_layout.addStretch()
        tabs.addTab(api_tab, "API Configuration")

        # Tab 2: Bookmaker Setup
        bookmaker_tab = QWidget()
        bookmaker_layout = QVBoxLayout(bookmaker_tab)

        bookmaker_layout.addWidget(QLabel("Configure your bookmaker accounts:"))

        # Bookmaker list
        self.bookmaker_list = QListWidget()
        self.bookmaker_list.setMaximumHeight(200)
        self.refresh_bookmaker_list()
        bookmaker_layout.addWidget(self.bookmaker_list)

        # Add bookmaker controls
        add_layout = QHBoxLayout()
        self.bookmaker_input = QLineEdit()
        self.bookmaker_input.setPlaceholderText("Bookmaker name (e.g., DraftKings)")
        add_layout.addWidget(self.bookmaker_input)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_bookmaker)
        add_layout.addWidget(add_btn)
        bookmaker_layout.addLayout(add_layout)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_bookmaker)
        bookmaker_layout.addWidget(remove_btn)

        # Quick setup buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Quick Setup:"))

        quick_us_btn = QPushButton("US Bookmakers")
        quick_us_btn.clicked.connect(
            lambda: self.quick_add_bookmakers(
                ["DraftKings", "FanDuel", "BetMGM", "Caesars", "PointsBet"]
            )
        )
        quick_layout.addWidget(quick_us_btn)

        quick_uk_btn = QPushButton("UK Bookmakers")
        quick_uk_btn.clicked.connect(
            lambda: self.quick_add_bookmakers(
                ["Bet365", "William Hill", "Paddy Power", "Betfair", "Sky Bet"]
            )
        )
        quick_layout.addWidget(quick_uk_btn)

        bookmaker_layout.addLayout(quick_layout)

        # Create accounts button
        create_accounts_btn = QPushButton("Create Account Profiles")
        create_accounts_btn.clicked.connect(self.create_account_profiles)
        bookmaker_layout.addWidget(create_accounts_btn)

        bookmaker_layout.addStretch()
        tabs.addTab(bookmaker_tab, "Bookmaker Setup")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def show_first_run_message(self):
        """Show first-run welcome message."""
        QMessageBox.information(
            self,
            "Welcome!",
            "Welcome to the Arbitrage Betting Bot!\n\n"
            "To get started:\n"
            "1. Enter your Odds API key\n"
            "2. Add your bookmaker accounts\n"
            "3. Create account profiles\n\n"
            "Configure at least one API provider to use real data sources.",
        )

    def refresh_bookmaker_list(self):
        """Refresh the bookmaker list display."""
        self.bookmaker_list.clear()
        bookmakers = Config.get_bookmakers()

        for bm in bookmakers:
            name = bm.get("name", "")
            username = bm.get("username", "")
            display_text = f"{name}"
            if username:
                display_text += f" ({username})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, bm)
            self.bookmaker_list.addItem(item)

    def add_bookmaker(self):
        """Add a bookmaker to the list."""
        name = self.bookmaker_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a bookmaker name")
            return

        Config.add_bookmaker(name)
        self.bookmaker_input.clear()
        self.refresh_bookmaker_list()

    def remove_bookmaker(self):
        """Remove selected bookmaker."""
        current_item = self.bookmaker_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Please select a bookmaker to remove")
            return

        bm_data = current_item.data(Qt.ItemDataRole.UserRole)
        name = bm_data.get("name", "")

        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Remove {name} from bookmaker list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            Config.remove_bookmaker(name)
            self.refresh_bookmaker_list()

    def quick_add_bookmakers(self, bookmakers: list):
        """Quickly add multiple bookmakers."""
        for name in bookmakers:
            Config.add_bookmaker(name)
        self.refresh_bookmaker_list()
        QMessageBox.information(self, "Success", f"Added {len(bookmakers)} bookmakers")

    def create_account_profiles(self):
        """Create account profiles for all bookmakers."""
        bookmakers = Config.get_bookmakers()

        if not bookmakers:
            QMessageBox.warning(self, "Error", "No bookmakers configured. Add bookmakers first.")
            return

        db = AccountDatabase()
        created = 0
        skipped = 0

        for bm in bookmakers:
            name = bm.get("name", "")
            username = bm.get("username", "")

            # Check if account already exists
            existing = db.get_account(name, username)
            if existing:
                skipped += 1
                continue

            # Create new account
            from src.account_manager import AccountProfile

            profile = AccountProfile(
                bookmaker_name=name, account_username=username or f"{name}_account"
            )
            db.create_account(profile)
            created += 1

        message = f"Created {created} account profile(s)"
        if skipped > 0:
            message += f"\nSkipped {skipped} (already exist)"

        QMessageBox.information(self, "Success", message)

    def test_api_key(self):
        """Test the API key."""
        api_key = self.api_key_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter an API key")
            return

        try:
            from src.data_acquisition import OddsDataFetcher

            fetcher = OddsDataFetcher(api_key=api_key)

            # Try to get available sports
            sports = fetcher.get_available_sports()

            if sports:
                QMessageBox.information(
                    self,
                    "API Key Valid",
                    f"API key is valid!\n\nFound {len(sports)} available sports.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "API Key Test",
                    "API key test completed, but no sports were returned.\n"
                    "The key may be invalid or rate-limited.",
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to test API key:\n{str(e)}")

    def save_api_key(self):
        """Save the API key."""
        api_key = self.api_key_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "Error", "Please enter an API key")
            return

        Config.save_api_key(api_key)
        QMessageBox.information(self, "Success", "API key saved successfully!")

    def show_provider_dialog(self):
        """Show API provider management dialog."""
        dialog = APIProviderDialog(self)
        dialog.exec()
        # Refresh if providers were changed
        # The dialog handles its own refresh
