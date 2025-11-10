"""
Account management dialog for adding/editing bookmaker accounts.
"""

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from gui.theme_utils import apply_accent_button
from src.account_manager import AccountDatabase, AccountProfile


class AccountDialog(QDialog):
    """Dialog for adding/editing account profiles."""

    def __init__(self, parent=None, account_profile=None):
        """
        Initialize account dialog.

        Args:
            parent: Parent window
            account_profile: Optional AccountProfile to edit
        """
        super().__init__(parent)
        self.account_profile = account_profile
        self.db = AccountDatabase()

        if account_profile:
            self.setWindowTitle("Edit Account - Redline Arbitrage")
        else:
            self.setWindowTitle("Add Account - Redline Arbitrage")

        self.init_ui()

        if account_profile:
            self.load_account_data()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Bookmaker name
        layout.addWidget(QLabel("Bookmaker Name:"))
        self.bookmaker_input = QLineEdit()
        self.bookmaker_input.setPlaceholderText("e.g., DraftKings, FanDuel")
        layout.addWidget(self.bookmaker_input)

        # Account username
        layout.addWidget(QLabel("Account Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Your account username/email")
        layout.addWidget(self.username_input)

        # Account status
        layout.addWidget(QLabel("Account Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Healthy", "Under Review", "Limited", "Closed"])
        layout.addWidget(self.status_combo)

        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addWidget(self.notes_input)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_account)
        apply_accent_button(self.save_btn)  # Apply accent styling
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_account_data(self):
        """Load account data into form."""
        if self.account_profile:
            self.bookmaker_input.setText(self.account_profile.bookmaker_name)
            self.username_input.setText(self.account_profile.account_username)
            index = self.status_combo.findText(self.account_profile.account_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            self.notes_input.setText(self.account_profile.notes)

    def save_account(self):
        """Save account profile."""
        bookmaker = self.bookmaker_input.text().strip()
        username = self.username_input.text().strip()

        if not bookmaker:
            QMessageBox.warning(self, "Error", "Bookmaker name is required")
            return

        if not username:
            QMessageBox.warning(self, "Error", "Account username is required")
            return

        if self.account_profile:
            # Update existing
            self.account_profile.bookmaker_name = bookmaker
            self.account_profile.account_username = username
            self.account_profile.account_status = self.status_combo.currentText()
            self.account_profile.notes = self.notes_input.toPlainText()
            self.db.update_account(self.account_profile)
        else:
            # Create new
            profile = AccountProfile(
                bookmaker_name=bookmaker,
                account_username=username,
                account_status=self.status_combo.currentText(),
                notes=self.notes_input.toPlainText(),
            )
            self.db.create_account(profile)

        self.accept()
