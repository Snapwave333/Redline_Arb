"""
Main GUI window for the arbitrage bot.
"""

import logging
import os
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.settings import Config
from gui.tachometer_widget import TachometerWidget
from gui.theme_utils import apply_accent_button, load_theme_stylesheet, polish_widget
from src.account_health import AccountHealthManager
from src.arbitrage import ArbitrageDetector, ArbitrageOpportunity
from src.stake_calculator import StakeCalculator
from src.utils import format_currency

logger = logging.getLogger(__name__)


class OddsUpdateThread(QThread):
    """Thread for fetching odds data without blocking UI."""

    odds_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, data_fetcher, sport="soccer"):
        super().__init__()
        self.data_fetcher = data_fetcher
        self.sport = sport
        self.running = True

    def run(self):
        """Fetch odds data."""
        try:
            if not self.data_fetcher:
                if self.running:
                    self.error_occurred.emit(
                        "No data source configured. Please configure API providers in Settings."
                    )
                return
            events = self.data_fetcher.fetch_odds_sync(sport=self.sport)
            if self.running:
                self.odds_updated.emit(events)
        except Exception as e:
            if self.running:
                self.error_occurred.emit(str(e))

    def stop(self):
        """Stop the thread."""
        self.running = False


class ArbitrageBotGUI(QMainWindow):
    """Main GUI window for the arbitrage bot."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Redline Arbitrage - Profit at the limit")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize components
        self.account_health_manager = AccountHealthManager()
        self.arbitrage_detector = ArbitrageDetector(
            min_profit_percentage=Config.MIN_PROFIT_PERCENTAGE,
            account_health_manager=self.account_health_manager,
        )
        self.stake_calculator = StakeCalculator(
            round_stakes=Config.ROUND_STAKES,
            max_variation_percent=Config.MAX_BET_VARIATION_PERCENT,
            account_health_manager=self.account_health_manager,
            min_stake_threshold=10.0,
        )

        # Time-delay tracking
        self.bet_delay_timer = QTimer()
        self.bet_delay_seconds = 0
        self.current_bet_index = 0

        # Initialize multi-API orchestrator
        self.orchestrator = None
        self.data_fetcher = None
        self.last_primary_provider = None
        self.initialize_data_fetcher()

        self.selected_arbitrage = None
        self.current_stake_distribution = None
        self.current_arbitrages = []

        # Thread management: disable in test mode for stability
        self.update_thread = None
        self._enable_update_thread = not (
            Config.TEST_MODE or os.getenv("ARBYS_SUPPRESS_WIZARD") == "1"
        )

        # Suppress wizard in test mode
        self.suppress_wizard = Config.TEST_MODE or os.getenv("ARBYS_SUPPRESS_WIZARD") == "1"

        # Setup UI
        self.init_ui()

        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.fetch_odds)
        if self._enable_update_thread:
            self.update_timer.start(Config.UPDATE_INTERVAL * 1000)

        # Setup delay timer
        self.bet_delay_timer.timeout.connect(self.update_delay_countdown)
        self.bet_delay_timer.start(1000)  # Update every second

        # Setup provider health check timer
        self.provider_health_timer = QTimer()
        self.provider_health_timer.timeout.connect(self.update_provider_status)
        self.provider_health_timer.start(60000)  # Check every 60 seconds

        # Initial provider status update
        self.update_provider_status()

        # Check if first run (no providers configured) or no data fetcher
        if not self.data_fetcher and not self.suppress_wizard:
            self.show_setup_wizard()
        elif self.data_fetcher and not self.suppress_wizard:
            # Initial fetch
            self.fetch_odds()

    def show_setup_wizard(self):
        """Show setup wizard."""
        # Lazy import for startup optimization
        from gui.setup_wizard import SetupWizard

        wizard = SetupWizard(self)
        wizard.exec()

        # Refresh account health if accounts were created
        if hasattr(self, "account_health_manager"):
            self.refresh_account_health()

        # Reinitialize data fetcher if API key changed
        self.initialize_data_fetcher()
        if self.data_fetcher:
            logger.info("Data fetcher reinitialized after setup")
            # Fetch odds after setup
            self.fetch_odds()
        else:
            logger.error("No API configured - production mode requires real data providers")
            QMessageBox.critical(
                None,
                "No Data Source Configured",
                "No API provider is configured. Please configure at least one data provider:\n\n"
                "• The Odds API\n"
                "• Sportradar API\n"
                "• SofaScore Scraper (free)\n\n"
                "Go to: Settings → Configure API Providers",
            )

    def open_setup_wizard(self):
        """Alias for show_setup_wizard() for compatibility with onboarding system."""
        self.show_setup_wizard()

    def init_ui(self):
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Controls and arbitrage list
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Middle panel - Stake calculator
        middle_panel = self.create_right_panel()
        splitter.addWidget(middle_panel)

        # Right panel - Account health
        right_panel = self.create_account_health_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        main_layout.addWidget(splitter)

        # Provider status panel (footer)
        provider_status_panel = self.create_provider_status_panel()
        main_layout.addWidget(provider_status_panel)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Create menu bar
        self.create_menu_bar()

        # Apply theme properties (accent buttons, cards, etc.)
        self.apply_theme_styles()

    def create_header(self) -> QWidget:
        """Create header section."""
        header = QGroupBox("Redline Arbitrage Control Panel")
        layout = QHBoxLayout()

        # Sport selector
        layout.addWidget(QLabel("Sport:"))
        self.sport_combo = QComboBox()
        self.sport_combo.addItems(["soccer", "basketball", "baseball", "hockey", "tennis"])
        layout.addWidget(self.sport_combo)

        layout.addSpacing(20)

        # Control buttons
        self.refresh_btn = QPushButton("Refresh Now")
        self.refresh_btn.clicked.connect(self.fetch_odds)
        layout.addWidget(self.refresh_btn)

        self.pause_btn = QPushButton("Pause Updates")
        self.pause_btn.clicked.connect(self.toggle_updates)
        layout.addWidget(self.pause_btn)

        self.manage_accounts_btn = QPushButton("Manage Accounts")
        self.manage_accounts_btn.clicked.connect(self.show_account_manager)
        layout.addWidget(self.manage_accounts_btn)

        self.config_btn = QPushButton("⚙️ Setup")
        self.config_btn.clicked.connect(self.show_setup_wizard)
        layout.addWidget(self.config_btn)

        layout.addStretch()

        # Status indicator
        self.status_label = QLabel("● Active")
        self.status_label.setProperty("status", "active")
        self.status_label.setStyleSheet("font-weight: bold;")

        # Provider status will be shown in footer panel
        layout.addWidget(self.status_label)

        header.setLayout(layout)
        return header

    def create_left_panel(self) -> QWidget:
        """Create left panel with arbitrage opportunities table."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Table for arbitrage opportunities
        table_label = QLabel("Arbitrage Opportunities")
        table_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(table_label)

        self.arbitrage_table = QTableWidget()
        self.arbitrage_table.setColumnCount(6)
        self.arbitrage_table.setHorizontalHeaderLabels(
            ["Event", "Profit %", "Outcomes", "Bookmakers", "Time", "Action"]
        )
        self.arbitrage_table.horizontalHeader().setStretchLastSection(True)
        self.arbitrage_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.arbitrage_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.arbitrage_table.cellClicked.connect(self.on_arbitrage_selected)
        layout.addWidget(self.arbitrage_table)

        # Log area
        log_label = QLabel("Activity Log")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        return panel

    def create_right_panel(self) -> QWidget:
        """Create right panel with stake calculator."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        calc_group = QGroupBox("Stake Calculator")
        calc_layout = QVBoxLayout()

        # Selected arbitrage info (card style)
        self.selected_arb_label = QLabel("Select an arbitrage opportunity")
        self.selected_arb_label.setWordWrap(True)
        self.selected_arb_label.setProperty("card", True)
        calc_layout.addWidget(self.selected_arb_label)

        calc_layout.addSpacing(10)

        # Stake input
        stake_layout = QHBoxLayout()
        stake_layout.addWidget(QLabel("Total Stake:"))
        self.stake_input = QDoubleSpinBox()
        self.stake_input.setRange(1.0, Config.MAX_STAKE)
        self.stake_input.setValue(Config.DEFAULT_STAKE)
        self.stake_input.setPrefix("$ ")
        self.stake_input.setDecimals(2)
        self.stake_input.valueChanged.connect(self.calculate_stakes)
        stake_layout.addWidget(self.stake_input)
        calc_layout.addLayout(stake_layout)

        calc_layout.addSpacing(10)

        # Calculate button
        self.calc_btn = QPushButton("Calculate Stakes")
        self.calc_btn.clicked.connect(self.calculate_stakes)
        calc_layout.addWidget(self.calc_btn)

        # Log bet button
        self.log_bet_btn = QPushButton("Log Bet as Placed")
        self.log_bet_btn.clicked.connect(self.log_bet_placed)
        self.log_bet_btn.setEnabled(False)
        calc_layout.addWidget(self.log_bet_btn)

        calc_layout.addSpacing(10)

        # Results table
        results_label = QLabel("Stake Distribution")
        results_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        calc_layout.addWidget(results_label)

        self.stake_table = QTableWidget()
        self.stake_table.setColumnCount(4)
        self.stake_table.setHorizontalHeaderLabels(["Outcome", "Bookmaker", "Stake", "Return"])
        self.stake_table.horizontalHeader().setStretchLastSection(True)
        self.stake_table.setMaximumHeight(200)
        calc_layout.addWidget(self.stake_table)

        calc_layout.addSpacing(10)

        # Summary (card style with success indicator)
        self.summary_label = QLabel("")
        self.summary_label.setProperty("card", True)
        self.summary_label.setProperty("status", "success")
        calc_layout.addWidget(self.summary_label)

        # Warnings/Risk display (card style)
        self.warnings_label = QLabel("")
        self.warnings_label.setWordWrap(True)
        self.warnings_label.setProperty("card", True)
        self.warnings_label.setMaximumHeight(100)
        calc_layout.addWidget(self.warnings_label)

        # Time-delay countdown (card style)
        self.delay_label = QLabel("")
        self.delay_label.setProperty("card", True)
        self.delay_label.setMaximumHeight(60)
        calc_layout.addWidget(self.delay_label)

        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)

        layout.addStretch()

        return panel

    def create_account_health_panel(self) -> QWidget:
        """Create account health monitoring panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        health_group = QGroupBox("Account Health")
        health_layout = QVBoxLayout()

        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_accounts_btn = QPushButton("Refresh")
        self.refresh_accounts_btn.clicked.connect(self.refresh_account_health)
        apply_accent_button(self.refresh_accounts_btn)
        refresh_layout.addWidget(self.refresh_accounts_btn)
        refresh_layout.addStretch()
        health_layout.addLayout(refresh_layout)

        # Tachometer dashboard for stealth scores
        self.tachometer_container = QWidget()
        self.tachometer_layout = QHBoxLayout(self.tachometer_container)
        self.tachometer_layout.setContentsMargins(0, 0, 0, 0)
        self.tachometer_widgets = {}  # Store tachometer widgets by bookmaker name
        health_layout.addWidget(self.tachometer_container)

        # Account health table
        self.account_health_table = QTableWidget()
        self.account_health_table.setColumnCount(5)
        self.account_health_table.setHorizontalHeaderLabels(
            ["Bookmaker", "Status", "Stealth", "Bets", "P/L"]
        )
        self.account_health_table.horizontalHeader().setStretchLastSection(True)
        self.account_health_table.setMaximumHeight(300)
        self.account_health_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        health_layout.addWidget(self.account_health_table)

        # Account health summary (card style)
        self.account_summary_label = QLabel("No accounts configured")
        self.account_summary_label.setWordWrap(True)
        self.account_summary_label.setProperty("card", True)
        health_layout.addWidget(self.account_summary_label)

        health_group.setLayout(health_layout)
        layout.addWidget(health_group)

        # Initial refresh
        self.refresh_account_health()

        return panel

    def refresh_account_health(self):  # pragma: no cover
        """Refresh account health display."""
        try:
            accounts_health = self.account_health_manager.get_all_accounts_health()

            self.account_health_table.setRowCount(len(accounts_health))

            total_accounts = len(accounts_health)
            healthy_count = sum(1 for acc in accounts_health if acc["status"] == "Healthy")
            avg_stealth = (
                sum(acc["stealth_score"] for acc in accounts_health) / total_accounts
                if total_accounts > 0
                else 0
            )

            # Clear existing tachometers
            for i in reversed(range(self.tachometer_layout.count())):
                self.tachometer_layout.itemAt(i).widget().setParent(None)
            self.tachometer_widgets.clear()

            # Show/hide tachometer container based on account count
            if total_accounts == 0:
                self.tachometer_container.hide()
            else:
                self.tachometer_container.show()

            for row, health in enumerate(accounts_health):
                profile = health.get("profile")
                if not profile:
                    continue

                # Bookmaker name
                self.account_health_table.setItem(row, 0, QTableWidgetItem(profile.bookmaker_name))

                # Status (color-coded with theme colors)
                status_item = QTableWidgetItem(health["status"])
                if health["status"] == "Healthy":
                    status_item.setForeground(QColor(76, 175, 80))  # Theme green
                elif health["status"] == "Under Review" or health["status"] == "Limited":
                    status_item.setForeground(QColor(255, 152, 0))  # Theme orange
                else:
                    status_item.setForeground(QColor(208, 0, 0))  # Theme red
                self.account_health_table.setItem(row, 1, status_item)

                # Stealth score (now 0.0-1.0 scale, display as percentage)
                stealth_score = health["stealth_score"]
                stealth_pct = stealth_score * 100
                stealth_item = QTableWidgetItem(f"{stealth_pct:.1f}%")
                if stealth_score >= 0.8:
                    stealth_item.setForeground(QColor(76, 175, 80))  # Theme green
                elif stealth_score >= 0.6:
                    stealth_item.setForeground(QColor(255, 152, 0))  # Theme orange
                else:
                    stealth_item.setForeground(QColor(208, 0, 0))  # Theme red
                self.account_health_table.setItem(row, 2, stealth_item)

                # Create tachometer for this account
                tachometer = TachometerWidget(label=profile.bookmaker_name[:12], size=100)
                tachometer.setValue(stealth_score, animated=True)
                self.tachometer_widgets[profile.bookmaker_name] = tachometer
                self.tachometer_layout.addWidget(tachometer)

                # Total bets
                self.account_health_table.setItem(
                    row, 3, QTableWidgetItem(str(health["total_bets"]))
                )

                # Profit/Loss (theme colors)
                pl_item = QTableWidgetItem(format_currency(health["total_profit_loss"]))
                if health["total_profit_loss"] > 0:
                    pl_item.setForeground(QColor(76, 175, 80))  # Theme green
                elif health["total_profit_loss"] < 0:
                    pl_item.setForeground(QColor(208, 0, 0))  # Theme red
                self.account_health_table.setItem(row, 4, pl_item)

            self.account_health_table.resizeColumnsToContents()

            # Update summary
            if total_accounts > 0:
                summary_text = f"<b>Total Accounts:</b> {total_accounts}<br>"
                summary_text += f"<b>Healthy:</b> {healthy_count}<br>"
                avg_stealth_pct = avg_stealth * 100
                summary_text += f"<b>Avg Stealth Score:</b> {avg_stealth_pct:.1f}%"
                self.account_summary_label.setText(summary_text)
            else:
                self.account_summary_label.setText(
                    "No accounts configured. Click 'Manage Accounts' to add accounts."
                )

        except Exception as e:
            logger.error(f"Error refreshing account health: {str(e)}")
            self.account_summary_label.setText(f"Error loading accounts: {str(e)}")

    def show_account_manager(self):
        """Show account management dialog."""
        from gui.account_manager_dialog import AccountManagerDialog

        dialog = AccountManagerDialog(self, self.account_health_manager)
        if dialog.exec():
            self.refresh_account_health()

    def set_update_thread_enabled(self, enabled: bool):
        """Enable or disable update thread (for testing)."""
        self._enable_update_thread = enabled
        if not enabled and self.update_thread:
            if self.update_thread.isRunning():
                self.update_thread.stop()
                self.update_thread.quit()
                self.update_thread.wait(1000)  # Wait max 1 second
            self.update_thread = None

    def closeEvent(self, event):  # pragma: no cover
        """Handle window close event - cleanup threads and timers."""
        if self._enable_update_thread and self.update_thread and self.update_thread.isRunning():
            self.update_thread.stop()
            self.update_thread.quit()
            self.update_thread.wait(1000)
        if hasattr(self, "update_timer"):
            self.update_timer.stop()
        if hasattr(self, "provider_health_timer"):
            self.provider_health_timer.stop()
        super().closeEvent(event)

    def fetch_odds(self):
        """Fetch odds data and update arbitrage opportunities."""
        if not self._enable_update_thread:
            # In test mode or when disabled, fetch synchronously
            if not self.data_fetcher:
                return
            try:
                events = self.data_fetcher.fetch_odds(self.sport_combo.currentText())
                self.on_odds_updated(events if events else [])
            except Exception as e:
                self.on_error(str(e))
            return

        if self.update_thread and self.update_thread.isRunning():
            return

        self.statusBar().showMessage("Fetching odds...")
        self.log_message("Fetching latest odds data...")

        if self.data_fetcher:
            self.update_thread = OddsUpdateThread(self.data_fetcher, self.sport_combo.currentText())
            self.update_thread.odds_updated.connect(self.on_odds_updated)
            self.update_thread.error_occurred.connect(self.on_error)
            self.update_thread.start()

    def on_odds_updated(self, events: list):
        """Handle updated odds data."""
        try:
            # Find arbitrage opportunities
            arbitrages = self.arbitrage_detector.find_best_arbitrages(events)
            self.current_arbitrages = arbitrages

            # Update table
            self.update_arbitrage_table()

            # Check for high-profit alerts
            for arb in arbitrages:
                if arb.profit_percentage >= Config.PROFIT_THRESHOLD_ALERT:
                    self.alert_high_profit(arb)

            self.statusBar().showMessage(f"Found {len(arbitrages)} arbitrage opportunities")
            self.log_message(f"Found {len(arbitrages)} arbitrage opportunities")

        except Exception as e:
            logger.error(f"Error processing odds: {str(e)}")
            self.on_error(str(e))

    def on_error(self, error_msg: str):
        """Handle errors."""
        self.statusBar().showMessage(f"Error: {error_msg}")
        self.log_message(f"ERROR: {error_msg}")
        QMessageBox.warning(self, "Error", f"Failed to fetch odds:\n{error_msg}")

    def update_arbitrage_table(self):
        """Update the arbitrage opportunities table."""
        self.arbitrage_table.setRowCount(len(self.current_arbitrages))

        for row, arb in enumerate(self.current_arbitrages):
            # Event name
            self.arbitrage_table.setItem(row, 0, QTableWidgetItem(arb.event_name))

            # Profit percentage (color-coded with theme colors)
            profit_item = QTableWidgetItem(f"{arb.profit_percentage:.2f}%")
            if arb.profit_percentage >= 5.0:
                profit_item.setForeground(QColor(76, 175, 80))  # Theme green
            elif arb.profit_percentage >= 2.0:
                profit_item.setForeground(QColor(255, 152, 0))  # Theme orange
            self.arbitrage_table.setItem(row, 1, profit_item)

            # Outcomes
            outcomes_str = ", ".join([o["outcome_name"] for o in arb.outcomes])
            self.arbitrage_table.setItem(row, 2, QTableWidgetItem(outcomes_str))

            # Bookmakers
            bookmakers_str = ", ".join(arb.bookmakers)
            self.arbitrage_table.setItem(row, 3, QTableWidgetItem(bookmakers_str))

            # Time (simplified)
            time_str = (
                arb.timestamp.split("T")[1].split(".")[0] if "T" in arb.timestamp else arb.timestamp
            )
            self.arbitrage_table.setItem(row, 4, QTableWidgetItem(time_str))

            # Action button
            action_btn = QPushButton("Select")
            action_btn.clicked.connect(lambda *, r=row: self.select_arbitrage(r))
            apply_accent_button(action_btn)  # Apply accent styling
            self.arbitrage_table.setCellWidget(row, 5, action_btn)

            # Display risk level (color code entire row)
            if hasattr(arb, "risk_level"):
                if arb.risk_level == "High":
                    for col in range(6):
                        item = self.arbitrage_table.item(row, col)
                        if item:
                            item.setForeground(QColor(200, 0, 0))
                        else:
                            # For widgets, we can't change color easily
                            pass
                elif arb.risk_level == "Medium":
                    for col in range(6):
                        item = self.arbitrage_table.item(row, col)
                        if item:
                            item.setForeground(QColor(255, 140, 0))

        self.arbitrage_table.resizeColumnsToContents()

    def on_arbitrage_selected(self, row: int, col: int):
        """Handle arbitrage selection from table."""
        self.select_arbitrage(row)

    def select_arbitrage(self, row: int):
        """Select an arbitrage opportunity for stake calculation."""
        if hasattr(self, "current_arbitrages") and 0 <= row < len(self.current_arbitrages):
            self.selected_arbitrage = self.current_arbitrages[row]
            self.update_selected_arbitrage_display()
            self.calculate_stakes()

    def update_selected_arbitrage_display(self):
        """Update the display for selected arbitrage."""
        if not hasattr(self, "selected_arbitrage"):
            return

        arb = self.selected_arbitrage
        info_text = f"<b>{arb.event_name}</b><br>"
        info_text += f"Profit: <span style='color: green;'>{arb.profit_percentage:.2f}%</span><br>"
        info_text += f"Outcomes: {', '.join([o['outcome_name'] for o in arb.outcomes])}<br>"
        info_text += f"Bookmakers: {', '.join(arb.bookmakers)}"

        self.selected_arb_label.setText(info_text)

    def calculate_stakes(self):
        """Calculate stake distribution for selected arbitrage."""
        if not hasattr(self, "selected_arbitrage"):
            self.summary_label.setText("Please select an arbitrage opportunity")
            return

        try:
            total_stake = self.stake_input.value()

            # Calculate stakes
            stake_dist = self.stake_calculator.calculate_stakes(
                self.selected_arbitrage, total_stake
            )

            # Update stake table
            self.stake_table.setRowCount(len(stake_dist.stakes))

            for row, stake_info in enumerate(stake_dist.stakes):
                self.stake_table.setItem(row, 0, QTableWidgetItem(stake_info["outcome_name"]))
                self.stake_table.setItem(row, 1, QTableWidgetItem(stake_info["bookmaker"]))
                self.stake_table.setItem(
                    row, 2, QTableWidgetItem(format_currency(stake_info["stake"]))
                )
                self.stake_table.setItem(
                    row, 3, QTableWidgetItem(format_currency(stake_info["return"]))
                )

            self.stake_table.resizeColumnsToContents()

            # Store stake distribution for logging
            self.current_stake_distribution = stake_dist

            # Update summary
            summary_text = (
                f"<b>Guaranteed Profit:</b> {format_currency(stake_dist.guaranteed_profit)}<br>"
            )
            summary_text += f"<b>Total Return:</b> {format_currency(stake_dist.total_return)}<br>"
            summary_text += f"<b>Profit %:</b> {stake_dist.profit_percentage:.2f}%"
            self.summary_label.setText(summary_text)

            # Display warnings
            warnings_text = ""
            if stake_dist.warnings:
                warnings_text = "<b>⚠️ Warnings:</b><br>"
                warnings_text += "<br>".join([f"• {w}" for w in stake_dist.warnings])

            # Add risk warnings from arbitrage opportunity
            if (
                hasattr(self.selected_arbitrage, "risk_warnings")
                and self.selected_arbitrage.risk_warnings
            ):
                if warnings_text:
                    warnings_text += "<br>"
                warnings_text += "<b>⚠️ Risk Warnings:</b><br>"
                warnings_text += "<br>".join(
                    [f"• {w}" for w in self.selected_arbitrage.risk_warnings]
                )

            if warnings_text:
                self.warnings_label.setText(warnings_text)
                self.warnings_label.setProperty("status", "warning")
            else:
                self.warnings_label.setText("")
                self.warnings_label.setProperty("status", "")

            self._polish_widget(self.warnings_label)

            # Reset delay tracking
            self.current_bet_index = 0
            self.bet_delay_seconds = 0
            self.update_delay_display()

            # Enable log bet button
            self.log_bet_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Error calculating stakes: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to calculate stakes:\n{str(e)}")
            self.log_bet_btn.setEnabled(False)

    def log_bet_placed(self):
        """Log arbitrage bet as placed."""
        if not self.selected_arbitrage or not self.current_stake_distribution:
            QMessageBox.warning(self, "Error", "No arbitrage selected or stakes not calculated")
            return

        try:
            # Log each bet for each bookmaker
            # Note: In arbitrage betting, only one outcome wins, but we log all bets
            # The profit is the guaranteed profit regardless of which outcome wins

            for stake_info in self.current_stake_distribution.stakes:
                bookmaker = stake_info["bookmaker"]
                outcome = stake_info["outcome_name"]
                stake = stake_info["stake"]
                odds = stake_info["odds"]

                # Profit if this outcome wins: return - total_stake
                # Since all outcomes have same return, profit is the same
                profit = self.current_stake_distribution.guaranteed_profit

                self.account_health_manager.log_arbitrage_bet(
                    bookmaker_name=bookmaker,
                    stake_amount=stake,
                    outcome=outcome,
                    odds=odds,
                    profit=profit,
                    event_name=self.selected_arbitrage.event_name,
                )

            # Refresh account health display
            self.refresh_account_health()

            QMessageBox.information(
                self,
                "Bet Logged",
                f"Successfully logged arbitrage bet for {self.selected_arbitrage.event_name}\n"
                f"Profit: {format_currency(self.current_stake_distribution.guaranteed_profit)}",
            )

            self.log_message(
                f"Logged arbitrage bet: {self.selected_arbitrage.event_name} - "
                f"{format_currency(self.current_stake_distribution.guaranteed_profit)} profit"
            )

            # Advance to next bet delay
            self.current_bet_index += 1
            self.bet_delay_seconds = 0
            self.update_delay_display()

            # Disable button until delay expires
            if self.current_bet_index < len(self.current_stake_distribution.stakes):
                self.log_bet_btn.setEnabled(False)
            else:
                # All bets logged
                self.log_bet_btn.setEnabled(False)
                self.current_stake_distribution = None

        except Exception as e:
            logger.error(f"Error logging bet: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to log bet:\n{str(e)}")

    def alert_high_profit(self, arb: ArbitrageOpportunity):
        """Alert user about high-profit arbitrage opportunity."""
        self.log_message(
            f"🚨 HIGH PROFIT ALERT: {arb.profit_percentage:.2f}% profit on {arb.event_name}"
        )

        if Config.ENABLE_SOUND_ALERTS:
            # Cross-platform beep sound
            try:
                import sys

                if sys.platform == "win32":
                    import winsound

                    winsound.Beep(1000, 500)
                else:
                    # Linux/Mac: use system bell
                    print("\a", end="", flush=True)
            except Exception:
                pass  # Silently fail if sound not available

    def toggle_updates(self):
        """Toggle automatic updates."""
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.pause_btn.setText("Resume Updates")
            self.status_label.setText("● Paused")
            self.status_label.setProperty("status", "paused")
            self._polish_widget(self.status_label)
            self.log_message("Updates paused")
        else:
            self.update_timer.start(Config.UPDATE_INTERVAL * 1000)
            self.pause_btn.setText("Pause Updates")
            self.status_label.setText("● Active")
            self.status_label.setProperty("status", "active")
            self._polish_widget(self.status_label)
            self.log_message("Updates resumed")
            self.fetch_odds()

    def log_message(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def update_delay_display(self):
        """Update the delay countdown display."""
        if not hasattr(self, "current_stake_distribution") or not self.current_stake_distribution:
            self.delay_label.setText("")
            return

        num_bets = len(self.current_stake_distribution.stakes)

        if self.current_bet_index >= num_bets:
            self.delay_label.setText("✅ All bets can be placed")
            self.delay_label.setProperty("status", "success")
            self._polish_widget(self.delay_label)
            return

        if self.current_bet_index == 0:
            # First bet can be placed immediately
            self.delay_label.setText("✅ Ready to place Bet 1 of " + str(num_bets))
            self.delay_label.setProperty("status", "ready")
            self._polish_widget(self.delay_label)
        else:
            # Calculate recommended delay (15 seconds between bets)
            recommended_delay = 15
            remaining = recommended_delay - self.bet_delay_seconds

            if remaining <= 0:
                self.delay_label.setText(
                    f"✅ Ready to place Bet {self.current_bet_index + 1} of {num_bets}"
                )
                self.delay_label.setProperty("status", "ready")
                self.delay_label.setToolTip("Pit stop complete. Ready to place bet.")
            else:
                self.delay_label.setText(
                    f"⏳ Wait {remaining} seconds before placing Bet {self.current_bet_index + 1} of {num_bets}<br>"
                    f"<small>(Recommended delay: {recommended_delay}s between bets)</small>"
                )
                self.delay_label.setProperty("status", "waiting")
                self.delay_label.setToolTip(
                    f"PIT STOP: {remaining}s remaining\n"
                    f"Preventing simultaneous bet placement to maintain stealth.\n"
                    f"Next bet available in {remaining} seconds."
                )
            self._polish_widget(self.delay_label)

    def update_delay_countdown(self):
        """Update delay countdown timer."""
        if (
            hasattr(self, "current_stake_distribution")
            and self.current_stake_distribution
            and self.current_bet_index > 0
            and self.current_bet_index < len(self.current_stake_distribution.stakes)
        ):
            self.bet_delay_seconds += 1
            recommended_delay = 15
            if self.bet_delay_seconds >= recommended_delay:
                # Delay expired, enable button
                self.log_bet_btn.setEnabled(True)
            self.update_delay_display()

    def initialize_data_fetcher(self):
        """Initialize data fetcher with orchestrator or legacy single API."""
        # Lazy imports for startup optimization
        from src.api_providers.api_sports import APISportsProvider
        from src.api_providers.sofascore_scraper import SofaScoreScraperProvider
        from src.data_acquisition import OrchestratedDataFetcher
        from src.data_orchestrator import MultiAPIOrchestrator

        try:
            # Get configured providers
            providers_config = Config.get_api_providers()

            if not providers_config or not any(p.get("enabled", False) for p in providers_config):
                # Production mode: No providers configured - show error
                logger.error("No API providers configured - production mode requires real data")
                self.data_fetcher = None
                self.orchestrator = None
                QMessageBox.critical(
                    None,
                    "No Data Source Configured",
                    "No API provider is configured. Production mode requires real data sources.\n\n"
                    "Please configure a data provider:\n\n"
                    "• SofaScore Scraper (free, unlimited, no API key)\n"
                    "• API-Sports (free, 100 requests/day, API key required)\n\n"
                    "Go to: Settings → Configure API Providers",
                )
                return

            # Create provider instances
            providers = []
            for provider_config in providers_config:
                if not provider_config.get("enabled", False):
                    continue

                provider_type = provider_config.get("type", "sofascore_scraper")
                api_key = provider_config.get("api_key", "")
                priority = provider_config.get("priority", 999)

                # Paid API providers removed - skip them
                if provider_type == "the_odds_api":
                    logger.warning("The Odds API removed - paid service not available, skipping")
                    continue
                elif provider_type == "sportradar":
                    logger.warning("Sportradar API removed - paid service not available, skipping")
                    continue
                elif provider_type == "mock":
                    # Mock providers removed - skip if found in config
                    logger.warning("Mock provider removed from production - skipping")
                    continue
                elif provider_type == "api_sports":
                    if api_key:
                        providers.append(
                            APISportsProvider(api_key=api_key, enabled=True, priority=priority)
                        )
                elif provider_type == "sofascore_scraper":
                    # SofaScore scraper doesn't require an API key (free unlimited)
                    # Can optionally configure cache_ttl and rate_limiting in config
                    cache_ttl = provider_config.get("cache_ttl", 300)
                    max_rps = provider_config.get("max_requests_per_second", 2.0)
                    providers.append(
                        SofaScoreScraperProvider(
                            api_key="scraper",  # Not used, kept for interface compatibility
                            enabled=True,
                            priority=priority,
                            cache_ttl=cache_ttl,
                            max_requests_per_second=max_rps,
                        )
                    )

            if not providers:
                # Production mode: No valid providers - show error
                logger.error(
                    "No valid API providers configured - production mode requires real data"
                )
                self.data_fetcher = None
                self.orchestrator = None
                QMessageBox.critical(
                    None,
                    "No Data Source Available",
                    "No valid API provider is configured. Production mode requires real data sources.\n\n"
                    "Please configure a data provider:\n\n"
                    "• SofaScore Scraper (free, unlimited, no API key)\n"
                    "• API-Sports (free, 100 requests/day, API key required)\n\n"
                    "Go to: Settings → Configure API Providers",
                )
                return

            # Create orchestrator
            self.orchestrator = MultiAPIOrchestrator(
                providers=providers, failover_enabled=True, require_all_providers=False
            )

            # Wrap in backward-compatible interface
            self.data_fetcher = OrchestratedDataFetcher(self.orchestrator)
            logger.info(f"Initialized orchestrator with {len(providers)} provider(s)")

            # Track primary provider
            if providers:
                self.last_primary_provider = providers[0].get_provider_name()

        except Exception as e:
            logger.error(f"Error initializing data fetcher: {e}")
            self.data_fetcher = None
            self.orchestrator = None
            QMessageBox.critical(
                None,
                "Data Fetcher Initialization Failed",
                f"Failed to initialize data fetcher:\n\n{str(e)}\n\n"
                "Please check your API provider configuration.",
            )

    def apply_theme_styles(self):  # pragma: no cover
        """Apply theme-specific properties (accent buttons, cards, etc.)."""
        # Mark important buttons as accent (red glow on hover)
        accent_buttons = [
            self.refresh_btn,
            self.calc_btn,
            self.log_bet_btn,
            self.manage_accounts_btn,
            self.config_btn,
            self.refresh_accounts_btn,
        ]

        for btn in accent_buttons:
            if btn:
                apply_accent_button(btn)

        # Apply card properties and polish all widgets with card property
        self._polish_widget(self.selected_arb_label)
        self._polish_widget(self.summary_label)
        self._polish_widget(self.warnings_label)
        self._polish_widget(self.delay_label)
        self._polish_widget(self.account_summary_label)
        self._polish_widget(self.status_label)

    def _polish_widget(self, widget):
        """Helper to polish a widget to apply property-based styles."""
        polish_widget(widget)

    def create_provider_status_panel(self) -> QWidget:
        """Create provider status panel footer."""
        panel = QGroupBox("API Provider Status")
        panel.setMaximumHeight(120)
        layout = QVBoxLayout(panel)

        # Status container
        status_layout = QHBoxLayout()

        # Provider status container
        self.provider_status_container = QWidget()
        self.provider_status_container_layout = QHBoxLayout(self.provider_status_container)
        self.provider_status_container_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self.provider_status_container)

        status_layout.addStretch()

        # Failover alert label
        self.failover_alert_label = QLabel("")
        self.failover_alert_label.setProperty("glow", "red")
        self.failover_alert_label.setStyleSheet("font-weight: bold;")
        self.failover_alert_label.setVisible(False)
        self._polish_widget(self.failover_alert_label)
        status_layout.addWidget(self.failover_alert_label)

        layout.addLayout(status_layout)

        # Info label (muted text style)
        info_label = QLabel("Provider health is checked every 60 seconds")
        info_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(info_label)

        return panel

    def update_provider_status(self):  # pragma: no cover
        """Update provider status display."""
        if not self.orchestrator:
            # No orchestrator, show legacy status
            if hasattr(self, "provider_status_container"):
                # Clear existing labels
                for i in reversed(range(self.provider_status_container_layout.count())):
                    self.provider_status_container_layout.itemAt(i).widget().setParent(None)

                # No orchestrator - show error
                label = QLabel("● No Data Source Configured")
                label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
                self.provider_status_container_layout.addWidget(label)
            return

        # Get provider statuses
        provider_statuses = self.orchestrator.get_provider_status()

        # Clear existing labels
        if hasattr(self, "provider_status_container"):
            for i in reversed(range(self.provider_status_container_layout.count())):
                widget = self.provider_status_container_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Detect current primary provider
            enabled_providers = [
                (name, health) for name, health in provider_statuses.items() if health.enabled
            ]

            if not enabled_providers:
                label = QLabel("● No Providers Enabled")
                label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
                self.provider_status_container_layout.addWidget(label)
                return

            # Sort by priority
            enabled_providers.sort(key=lambda x: x[1].priority)
            current_primary = enabled_providers[0][0]

            # Check for failover
            if self.last_primary_provider and current_primary != self.last_primary_provider:
                self.show_failover_alert(self.last_primary_provider, current_primary)
                self.last_primary_provider = current_primary

            # Display status for each provider
            all_healthy = True
            any_degraded = False

            for provider_name, health in enabled_providers:
                status = health.status

                # Determine color
                if status == "healthy":
                    status_text = "●"
                elif status == "degraded":
                    status_text = "⚠"
                    any_degraded = True
                elif status == "down":
                    status_text = "✗"
                    all_healthy = False
                else:
                    status_text = "?"

                # Create status label
                display_name = provider_name.replace("_", " ").title()
                if provider_name == current_primary:
                    display_name += " (Primary)"

                label_text = f"{status_text} {display_name}"
                if health.last_success:
                    # Add success count
                    total = health.success_count + health.error_count
                    if total > 0:
                        success_rate = (health.success_count / total) * 100
                        label_text += f" ({success_rate:.0f}%)"

                label = QLabel(label_text)
                # Use theme colors instead of hardcoded colors
                label.setProperty("provider_status", status)
                label.setStyleSheet(
                    "font-weight: bold; padding: 5px; border: 1px solid; border-radius: 3px; margin: 2px;"
                )
                self.provider_status_container_layout.addWidget(label)

            # Update overall status
            if not all_healthy:
                self.statusBar().showMessage("Warning: Some API providers are down", 5000)
            elif any_degraded:
                self.statusBar().showMessage("Notice: Some API providers are degraded", 5000)

    def show_failover_alert(self, old_provider: str, new_provider: str):
        """Show failover alert message."""
        old_name = old_provider.replace("_", " ").title()
        new_name = new_provider.replace("_", " ").title()

        alert_text = f"⚠️ FAILOVER: {old_name} → {new_name}"
        self.failover_alert_label.setText(alert_text)
        self.failover_alert_label.setVisible(True)

        # Hide after 10 seconds
        QTimer.singleShot(10000, lambda: self.failover_alert_label.setVisible(False))

        # Log to status bar
        self.statusBar().showMessage(
            f"Failover detected: Switched from {old_name} to {new_name}", 10000
        )

        logger.warning(f"Provider failover: {old_provider} → {new_provider}")

    def create_menu_bar(self):
        """Create menu bar with Help menu."""
        menubar = self.menuBar()

        # Help menu
        help_menu = menubar.addMenu("Help")

        # Run Tutorial action
        run_tutorial_action = help_menu.addAction("Run Tutorial")
        run_tutorial_action.triggered.connect(self.run_tutorial)

        # First-Day Slideshow action
        slideshow_action = help_menu.addAction("First-Day Slideshow")
        slideshow_action.triggered.connect(self.show_firstday_slideshow)

        # Separator
        help_menu.addSeparator()

        # About action (optional, can add later)
        # about_action = help_menu.addAction("About")
        # about_action.triggered.connect(self.show_about)

    def run_tutorial(self):
        """Run the onboarding tutorial again."""
        try:
            from onboarding.first_run_manager import load_flags, save_flags
            from onboarding.tutorial_overlay import OnboardingTour

            # Reset tutorial completion flag
            flags = load_flags()
            flags["has_completed_tutorial"] = False
            save_flags(flags)

            # Prepare tutorial steps
            steps = []
            registry = self.get_widget_registry()

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

            if steps:
                tour = OnboardingTour(steps, self)

                def on_tutorial_finished():
                    flags = load_flags()
                    flags["has_completed_tutorial"] = True
                    save_flags(flags)

                tour.finished.connect(on_tutorial_finished)
                tour.show()
            else:
                QMessageBox.information(
                    self,
                    "Tutorial",
                    "Tutorial steps are not available. Please ensure all UI components are initialized.",
                )
        except ImportError as e:
            logger.error(f"Could not import onboarding modules: {e}")
            QMessageBox.warning(
                self, "Error", "Onboarding system not available. Please restart the application."
            )
        except Exception as e:
            logger.error(f"Error running tutorial: {e}")
            QMessageBox.warning(self, "Error", f"Failed to run tutorial: {str(e)}")

    def get_widget_registry(self) -> dict:
        """
        Get widget registry for onboarding system.

        Returns:
            Dictionary mapping tooltip keys to widget instances:
            - btn_scan: Refresh button
            - tbl_opportunities: Arbitrage opportunities table
            - panel_calc: Stake calculator panel/widget
            - panel_health: Account health panel/widget
            - btn_providers: Setup/configuration button
            - badge_delay: Delay countdown label
            - stake_input: Stake input spinbox
        """
        registry = {}

        # Map tooltip keys to widget attributes
        if hasattr(self, "refresh_btn"):
            registry["btn_scan"] = self.refresh_btn

        if hasattr(self, "arbitrage_table"):
            registry["tbl_opportunities"] = self.arbitrage_table

        # Stake calculator panel - get the middle panel or the calc group
        if hasattr(self, "stake_input"):
            registry["stake_input"] = self.stake_input
            # Try to get the parent group or panel
            calc_widget = self.stake_input.parent()
            while calc_widget and not isinstance(calc_widget, QGroupBox):
                calc_widget = calc_widget.parent()
            if calc_widget:
                registry["panel_calc"] = calc_widget

        # Account health panel
        if hasattr(self, "account_health_table"):
            # Try to get the parent group
            health_widget = self.account_health_table.parent()
            while health_widget and not isinstance(health_widget, QGroupBox):
                health_widget = health_widget.parent()
            if health_widget:
                registry["panel_health"] = health_widget

        if hasattr(self, "config_btn"):
            registry["btn_providers"] = self.config_btn

        if hasattr(self, "delay_label"):
            registry["badge_delay"] = self.delay_label

        return registry

    def show_firstday_slideshow(self):
        """Show the first-day slideshow dialog."""
        try:
            from gui.ui_firstday_slideshow import FirstDaySlideshowDialog

            dialog = FirstDaySlideshowDialog(self)
            dialog.exec()
        except ImportError as e:
            logger.error(f"Could not import slideshow dialog: {e}")
            QMessageBox.warning(
                self,
                "Slideshow Unavailable",
                "The first-day slideshow requires PyQt6-WebEngine.\n\n"
                "Please install it with:\n"
                "  pip install PyQt6-WebEngine",
            )
        except Exception as e:
            logger.error(f"Error showing slideshow: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open slideshow:\n{str(e)}")


def main():
    """Main entry point for the GUI application."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern look

    # Load carbon fiber + red theme
    project_root = os.path.dirname(os.path.dirname(__file__))
    stylesheet = load_theme_stylesheet(project_root)
    if stylesheet:
        app.setStyleSheet(stylesheet)
    else:
        logger.warning("Theme not loaded, using default Fusion style")

    window = ArbitrageBotGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
