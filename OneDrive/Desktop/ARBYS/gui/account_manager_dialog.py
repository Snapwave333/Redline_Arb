"""
Account manager dialog for viewing and managing all accounts.
"""

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from gui.account_dialog import AccountDialog
from src.account_manager import AccountDatabase
from src.utils import format_currency


class AccountManagerDialog(QDialog):
    """Dialog for managing all bookmaker accounts."""

    def __init__(self, parent=None, account_health_manager=None):
        """
        Initialize account manager dialog.

        Args:
            parent: Parent window
            account_health_manager: AccountHealthManager instance
        """
        super().__init__(parent)
        self.setWindowTitle("Account Manager - Redline Arbitrage")
        self.setGeometry(200, 200, 900, 600)
        self.account_health_manager = account_health_manager
        self.db = AccountDatabase()

        self.init_ui()
        self.refresh_table()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Bookmaker Account Profiles")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add Account")
        self.add_btn.clicked.connect(self.add_account)
        button_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_account)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_account)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        # Accounts table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(8)
        self.accounts_table.setHorizontalHeaderLabels(
            ["Bookmaker", "Username", "Status", "Stealth", "Total Bets", "Arb %", "P/L", "Last Bet"]
        )
        self.accounts_table.horizontalHeader().setStretchLastSection(True)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounts_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.accounts_table.setSortingEnabled(True)
        layout.addWidget(self.accounts_table)

        # Info label
        info_label = QLabel(
            "Tip: Keep stealth scores high by mixing arbitrage bets with regular bets.\n"
            "Monitor accounts regularly to avoid limitations."
        )
        info_label.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

    def refresh_table(self):
        """Refresh accounts table."""
        try:
            accounts = self.db.get_all_accounts()

            self.accounts_table.setRowCount(len(accounts))

            for row, account in enumerate(accounts):
                # Bookmaker name
                self.accounts_table.setItem(row, 0, QTableWidgetItem(account.bookmaker_name))

                # Username
                self.accounts_table.setItem(row, 1, QTableWidgetItem(account.account_username))

                # Status (color-coded)
                status_item = QTableWidgetItem(account.account_status)
                if account.account_status == "Healthy":
                    status_item.setForeground(QColor(0, 150, 0))
                elif account.account_status == "Under Review":
                    status_item.setForeground(QColor(255, 140, 0))
                elif account.account_status == "Limited":
                    status_item.setForeground(QColor(255, 100, 0))
                else:
                    status_item.setForeground(QColor(200, 0, 0))
                self.accounts_table.setItem(row, 2, status_item)

                # Stealth score (now 0.0-1.0 scale, display as percentage)
                stealth_pct = account.stealth_score * 100
                stealth_item = QTableWidgetItem(f"{stealth_pct:.1f}%")
                if account.stealth_score >= 0.8:
                    stealth_item.setForeground(QColor(0, 150, 0))
                elif account.stealth_score >= 0.6:
                    stealth_item.setForeground(QColor(255, 140, 0))
                else:
                    stealth_item.setForeground(QColor(200, 0, 0))
                self.accounts_table.setItem(row, 3, stealth_item)

                # Total bets
                self.accounts_table.setItem(
                    row, 4, QTableWidgetItem(str(account.total_bets_placed))
                )

                # Arb percentage
                if account.total_bets_placed > 0:
                    arb_pct = (account.total_arb_bets / account.total_bets_placed) * 100
                    arb_item = QTableWidgetItem(f"{arb_pct:.1f}%")
                else:
                    arb_item = QTableWidgetItem("0%")
                self.accounts_table.setItem(row, 5, arb_item)

                # Profit/Loss
                pl_item = QTableWidgetItem(format_currency(account.total_profit_loss))
                if account.total_profit_loss > 0:
                    pl_item.setForeground(QColor(0, 150, 0))
                elif account.total_profit_loss < 0:
                    pl_item.setForeground(QColor(200, 0, 0))
                self.accounts_table.setItem(row, 6, pl_item)

                # Last bet
                if account.last_bet_date:
                    date_str = (
                        account.last_bet_date.split("T")[0]
                        if "T" in account.last_bet_date
                        else account.last_bet_date
                    )
                    self.accounts_table.setItem(row, 7, QTableWidgetItem(date_str))
                else:
                    self.accounts_table.setItem(row, 7, QTableWidgetItem("Never"))

            self.accounts_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load accounts: {str(e)}")

    def get_selected_account(self):
        """Get selected account profile."""
        current_row = self.accounts_table.currentRow()
        if current_row < 0:
            return None

        bookmaker_name = self.accounts_table.item(current_row, 0).text()
        username = self.accounts_table.item(current_row, 1).text()

        return self.db.get_account(bookmaker_name, username)

    def add_account(self):
        """Add new account."""
        dialog = AccountDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.account_health_manager:
                self.account_health_manager.refresh_account_health()

    def edit_account(self):
        """Edit selected account."""
        account = self.get_selected_account()
        if not account:
            QMessageBox.warning(self, "Error", "Please select an account to edit")
            return

        dialog = AccountDialog(self, account)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.account_health_manager:
                self.account_health_manager.refresh_account_health()

    def delete_account(self):
        """Delete selected account."""
        account = self.get_selected_account()
        if not account:
            QMessageBox.warning(self, "Error", "Please select an account to delete")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete account for {account.bookmaker_name}?\n"
            f"This will also delete all bet history for this account.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete bet log entries first (foreign key constraint)
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bet_log WHERE account_id = ?", (account.id,))
                cursor.execute("DELETE FROM accounts WHERE id = ?", (account.id,))
                conn.commit()
                conn.close()

                self.refresh_table()
                if self.account_health_manager:
                    self.account_health_manager.refresh_account_health()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete account: {str(e)}")
