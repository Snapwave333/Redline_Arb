"""
API Provider Management Dialog for multi-API configuration.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from config.settings import Config


class APIProviderDialog(QDialog):
    """Dialog for managing API providers."""

    def __init__(self, parent=None):
        """Initialize API provider dialog."""
        super().__init__(parent)
        self.setWindowTitle("API Provider Management - Redline Arbitrage")
        self.setGeometry(200, 200, 800, 600)

        self.init_ui()
        self.refresh_provider_list()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Manage API Providers")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Info label
        info = QLabel(
            "Configure multiple odds API providers for fault tolerance and better coverage.\n"
            "The bot will automatically failover to backup providers if the primary fails."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Provider list table
        self.provider_table = QTableWidget()
        self.provider_table.setColumnCount(5)
        self.provider_table.setHorizontalHeaderLabels(
            ["Provider", "API Key", "Priority", "Status", "Health"]
        )
        self.provider_table.horizontalHeader().setStretchLastSection(True)
        self.provider_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.provider_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.provider_table)

        # Add provider group
        add_group = QGroupBox("Add/Edit Provider")
        add_layout = QVBoxLayout()

        # Provider type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.provider_type_combo = QComboBox()
        self.provider_type_combo.addItems(
            [
                "SofaScore Scraper",  # Free, unlimited, no API key required
                "API-Sports",  # Free plan: 100 requests/day, API key required
                # Future: "OddsJam", etc.
            ]
        )
        type_layout.addWidget(self.provider_type_combo)
        add_layout.addLayout(type_layout)

        # API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter API key")
        key_layout.addWidget(self.api_key_input)
        add_layout.addLayout(key_layout)

        # Priority and Enabled
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priority:"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setMinimum(1)
        self.priority_spin.setMaximum(100)
        self.priority_spin.setValue(1)
        self.priority_spin.setToolTip("Lower number = higher priority (used first)")
        priority_layout.addWidget(self.priority_spin)

        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        priority_layout.addWidget(self.enabled_checkbox)
        add_layout.addLayout(priority_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Provider")
        add_btn.clicked.connect(self.add_provider)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Update Selected")
        edit_btn.clicked.connect(self.update_provider)
        btn_layout.addWidget(edit_btn)

        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_provider)
        btn_layout.addWidget(test_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_provider)
        btn_layout.addWidget(remove_btn)

        add_layout.addLayout(btn_layout)
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        # Status info
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def refresh_provider_list(self):
        """Refresh provider list display."""
        providers = Config.get_api_providers()

        self.provider_table.setRowCount(len(providers))

        for row, provider in enumerate(providers):
            name = provider.get("name", "Unknown")
            provider_type = provider.get("type", "unknown")
            api_key = provider.get("api_key", "")
            priority = provider.get("priority", 999)
            enabled = provider.get("enabled", True)

            # Display name
            name_item = QTableWidgetItem(f"{name} ({provider_type})")
            name_item.setData(Qt.ItemDataRole.UserRole, provider)
            self.provider_table.setItem(row, 0, name_item)

            # API Key (masked)
            masked_key = "*" * min(len(api_key), 20) if api_key else "Not set"
            key_item = QTableWidgetItem(masked_key)
            self.provider_table.setItem(row, 1, key_item)

            # Priority
            priority_item = QTableWidgetItem(str(priority))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.provider_table.setItem(row, 2, priority_item)

            # Status
            status_text = "✓ Enabled" if enabled else "✗ Disabled"
            status_item = QTableWidgetItem(status_text)
            if enabled:
                status_item.setForeground(QColor(0, 128, 0))
            else:
                status_item.setForeground(QColor(128, 0, 0))
            self.provider_table.setItem(row, 3, status_item)

            # Health (placeholder - will be updated with real data)
            health_item = QTableWidgetItem("Unknown")
            self.provider_table.setItem(row, 4, health_item)

        self.provider_table.resizeColumnsToContents()

        # Update status label
        enabled_count = sum(1 for p in providers if p.get("enabled", False))
        self.status_label.setText(
            f"Total providers: {len(providers)} | "
            f"Enabled: {enabled_count} | "
            f"Disabled: {len(providers) - enabled_count}"
        )

    def get_selected_provider(self):
        """Get currently selected provider data."""
        current_row = self.provider_table.currentRow()
        if current_row < 0:
            return None

        item = self.provider_table.item(current_row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def add_provider(self):
        """Add a new provider."""
        provider_type = self.provider_type_combo.currentText()
        api_key = self.api_key_input.text().strip()

        # Map display name to internal type
        type_map = {"SofaScore Scraper": "sofascore_scraper", "API-Sports": "api_sports"}
        internal_type = type_map.get(provider_type, "sofascore_scraper")

        # SofaScore scraper doesn't require API key, API-Sports does
        if internal_type == "api_sports" and not api_key:
            QMessageBox.warning(
                self,
                "API Key Required",
                "API-Sports requires an API key.\n\n"
                "Get your free API key (100 requests/day) at:\n"
                "https://www.api-sports.io/",
            )
            return

        priority = self.priority_spin.value()
        enabled = self.enabled_checkbox.isChecked()

        providers = Config.get_api_providers()

        # Check if provider type already exists
        for provider in providers:
            if provider.get("type") == internal_type:
                reply = QMessageBox.question(
                    self,
                    "Provider Exists",
                    f"A {provider_type} provider already exists. Update it instead?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    # Update existing
                    provider["api_key"] = api_key
                    provider["priority"] = priority
                    provider["enabled"] = enabled
                    Config.save_api_providers(providers)
                    self.refresh_provider_list()
                    self.api_key_input.clear()
                    QMessageBox.information(self, "Success", "Provider updated successfully")
                return

        # Add new provider
        new_provider = {
            "name": provider_type.lower().replace(" ", "_"),
            "type": internal_type,
            "api_key": api_key,
            "priority": priority,
            "enabled": enabled,
        }

        providers.append(new_provider)
        Config.save_api_providers(providers)
        self.refresh_provider_list()
        self.api_key_input.clear()
        QMessageBox.information(self, "Success", "Provider added successfully")

    def update_provider(self):
        """Update selected provider."""
        provider = self.get_selected_provider()
        if not provider:
            QMessageBox.warning(self, "Error", "Please select a provider to update")
            return

        api_key = self.api_key_input.text().strip()
        priority = self.priority_spin.value()
        enabled = self.enabled_checkbox.isChecked()

        # Update provider
        if api_key:
            provider["api_key"] = api_key
        provider["priority"] = priority
        provider["enabled"] = enabled

        providers = Config.get_api_providers()
        Config.save_api_providers(providers)
        self.refresh_provider_list()
        self.api_key_input.clear()
        QMessageBox.information(self, "Success", "Provider updated successfully")

    def remove_provider(self):
        """Remove selected provider."""
        provider = self.get_selected_provider()
        if not provider:
            QMessageBox.warning(self, "Error", "Please select a provider to remove")
            return

        provider_name = provider.get("name", "Unknown")

        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Remove provider '{provider_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            providers = Config.get_api_providers()
            providers = [p for p in providers if p.get("name") != provider.get("name")]
            Config.save_api_providers(providers)
            self.refresh_provider_list()
            QMessageBox.information(self, "Success", "Provider removed")

    def test_provider(self):
        """Test selected provider connection."""
        provider = self.get_selected_provider()
        if not provider:
            QMessageBox.warning(self, "Error", "Please select a provider to test")
            return

        provider_type = provider.get("type", "")
        api_key = self.api_key_input.text().strip() or provider.get("api_key", "")

        # Check API key requirements
        if provider_type == "api_sports" and not api_key:
            QMessageBox.warning(self, "Error", "Please enter an API key to test")
            return

        try:
            if provider_type == "api_sports":
                from src.api_providers.api_sports import APISportsProvider

                test_provider = APISportsProvider(api_key=api_key)
                # Test by trying to fetch odds
                try:
                    test_provider.fetch_odds(sport="soccer")
                    remaining = test_provider.get_remaining_requests()
                    reset_time = test_provider.get_reset_time()

                    QMessageBox.information(
                        self,
                        "Connection Test Successful",
                        f"✓ API-Sports connection successful!\n\n"
                        f"Remaining requests today: {remaining}/100\n"
                        f"Resets at: {reset_time.strftime('%H:%M:%S')} UTC",
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Connection Test",
                        f"API-Sports test failed:\n{str(e)}\n\n"
                        "Please verify:\n"
                        "• API key is correct\n"
                        "• You haven't exceeded 100 requests/day\n"
                        "• Internet connection is working",
                    )
            elif provider_type == "sofascore_scraper":
                from src.api_providers.sofascore_scraper import SofaScoreScraperProvider

                test_provider = SofaScoreScraperProvider(api_key="test")
                # Test by trying to fetch a simple request
                try:
                    test_provider.fetch_odds(sport="soccer")
                    QMessageBox.information(
                        self,
                        "Connection Test Successful",
                        "✓ SofaScore Scraper is working!\n\n"
                        "This free scraper doesn't require an API key.",
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Connection Test",
                        f"SofaScore Scraper test failed:\n{str(e)}\n\n"
                        "This may be temporary - check your internet connection.",
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Not Supported",
                    f"Connection testing not yet implemented for {provider_type}",
                )
        except Exception as e:
            QMessageBox.warning(
                self, "Connection Test Failed", f"Failed to test provider:\n{str(e)}"
            )
