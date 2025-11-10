"""
First-Day Slideshow dialog for onboarding new users.
Displays the Reveal.js HTML slideshow in a modal dialog.
"""

import logging
import os

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logger.warning("PyQt6.QtWebEngineWidgets not available. Install PyQt6-WebEngine package.")


class FirstDaySlideshowDialog(QDialog):
    """Modal dialog displaying the first-day onboarding slideshow."""

    def __init__(self, parent=None):
        """
        Initialize the slideshow dialog.

        Args:
            parent: Parent window for modal behavior
        """
        super().__init__(parent)

        if not WEBENGINE_AVAILABLE:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "WebEngine Not Available",
                "PyQt6-WebEngine is required to display the slideshow.\n\n"
                "Please install it with:\n"
                "  pip install PyQt6-WebEngine",
            )
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            return

        self.setWindowTitle("Redline Arbitrage - First Day Slideshow")
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Set window size to 90% width and 70% height of parent
        if parent:
            parent_size = parent.size()
            width = int(parent_size.width() * 0.9)
            height = int(parent_size.height() * 0.7)
        else:
            # Default size if no parent
            width = 1280
            height = 720

        self.resize(width, height)

        # Center on parent window
        if parent:
            parent_geometry = parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - width) // 2
            y = parent_geometry.y() + (parent_geometry.height() - height) // 2
            self.move(x, y)

        # Set borderless window with dark theme styling
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        # Apply dark styling to match carbon-fiber/red theme
        self.setStyleSheet(
            """
            QDialog {
                background-color: #0D0D0F;
                border: 2px solid #D00000;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #1C1D22;
                border: 1px solid #2A2C31;
                border-radius: 4px;
                padding: 4px 12px;
                color: #E6E6E6;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2A2C31;
                border-color: #D00000;
            }
            QPushButton:pressed {
                background-color: #16171A;
            }
            QLabel {
                color: #E6E6E6;
                font-weight: 600;
                font-size: 14pt;
            }
        """
        )

        self.init_ui()

    def init_ui(self):
        """Initialize the UI with QWebEngineView."""
        if not WEBENGINE_AVAILABLE:
            return

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar with close button
        title_bar = QWidget(self)
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet(
            """
            QWidget {
                background-color: #1C1D22;
                border-bottom: 1px solid #2A2C31;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """
        )
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 8, 0)
        title_layout.setSpacing(12)

        title_label = QLabel("First-Day Slideshow")
        title_label.setStyleSheet("color: #E6E6E6; font-weight: 600; font-size: 13pt;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 16pt;
                font-weight: 600;
                color: #E6E6E6;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #D00000;
                border-color: #D00000;
            }
        """
        )
        close_btn.clicked.connect(self.close)
        close_btn.setToolTip("Close (ESC)")
        title_layout.addWidget(close_btn)

        main_layout.addWidget(title_bar)

        # Create web engine view
        self.web_view = QWebEngineView(self)

        # Load the HTML file
        html_path = self._get_html_path()
        if html_path and os.path.exists(html_path):
            # Convert to file:// URL
            file_url = QUrl.fromLocalFile(html_path)
            # In test mode, load about:blank to avoid file system dependencies
            test_mode = os.getenv("TEST_MODE", "0") == "1"
            if test_mode:
                self.web_view.load(QUrl("about:blank"))
            else:
                self.web_view.load(file_url)
            logger.info(f"Loaded slideshow from: {html_path}")
        else:
            # Show error message in the web view
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{
                        background-color: #0D0D0F;
                        color: #E6E6E6;
                        font-family: "Rajdhani", "Segoe UI", sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .error {{
                        text-align: center;
                        padding: 40px;
                        border: 2px solid #D00000;
                        border-radius: 8px;
                        background: rgba(22, 23, 26, 0.9);
                    }}
                    h1 {{ color: #D00000; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>Slideshow Not Found</h1>
                    <p>Could not find the slideshow HTML file.</p>
                    <p>Expected location: {html_path or 'unknown'}</p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)
            logger.error(f"Slideshow HTML not found at: {html_path}")

        main_layout.addWidget(self.web_view)

        # Ensure keyboard navigation works (Reveal.js handles this automatically)
        self.web_view.setFocus()

    def _get_html_path(self) -> str:
        """
        Get the absolute path to the slideshow index.html file.

        Returns:
            Absolute path to index.html, or None if not found
        """
        # Get project root (assuming this file is in gui/)
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(current_file))

        # Construct path to slideshow HTML
        slideshow_dir = os.path.join(
            project_root, "Redline_FirstDay_Slideshow_HTML(1)", "redline_slideshow"
        )
        html_path = os.path.join(slideshow_dir, "index.html")

        # Normalize path separators
        html_path = os.path.normpath(html_path)

        return html_path if os.path.exists(html_path) else None

    def keyPressEvent(self, event):
        """
        Handle keyboard events.
        Allow ESC to close, other keys pass through to Reveal.js.
        """
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            # Pass other keys to web view for Reveal.js navigation
            super().keyPressEvent(event)

    def showEvent(self, event):
        """Focus web view when dialog is shown."""
        super().showEvent(event)
        if WEBENGINE_AVAILABLE and hasattr(self, "web_view"):
            self.web_view.setFocus()
