"""
Splash screen for ARBYS application startup.

Frameless window with carbon-dark theme, ARBYS branding, and progress indication.
"""

import logging
import os

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class Splash(QWidget):
    """
    Frameless splash screen with carbon-dark theme.

    Shows ARBYS branding and optional progress bar.
    """

    def __init__(self, parent=None):
        """Initialize splash screen."""
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Window properties
        self.setFixedSize(500, 350)

        # Load carbon fiber pattern if available
        self.carbon_pattern = None
        self._load_carbon_pattern()

        self._setup_ui()
        self._center_on_screen()

        # Animation state
        self.fade_animation: QPropertyAnimation | None = None
        self.target_window = None

    def _load_carbon_pattern(self):
        """Load carbon fiber pattern from assets if available."""
        try:
            # Try to find carbon fiber tile SVG
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            svg_path = os.path.join(project_root, "looks", "assets", "carbon_fiber_tile.svg")

            if os.path.exists(svg_path):
                # For simplicity, we'll recreate the pattern in code
                # SVG rendering would require QSvgRenderer which adds complexity
                self.carbon_pattern = self._create_carbon_pattern()
            else:
                self.carbon_pattern = self._create_carbon_pattern()
        except Exception as e:
            logger.warning(f"Could not load carbon pattern: {e}")
            self.carbon_pattern = None

    def _create_carbon_pattern(self) -> QBrush:
        """Create carbon fiber pattern programmatically."""
        from PyQt6.QtGui import QPainter

        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#0D0D0F"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw weave pattern
        painter.setPen(Qt.PenStyle.NoPen)

        # Diagonal weave
        painter.setBrush(QBrush(QColor("#16171A")))
        painter.setOpacity(0.3)
        painter.drawPolygon([(0, 0), (32, 0), (64, 32), (32, 64), (0, 64)])
        painter.drawPolygon([(64, 0), (32, 0), (0, 32), (32, 64), (64, 64)])

        # Fiber lines
        painter.setOpacity(0.4)
        painter.setPen(QColor("#1C1D22"))
        for y in [8, 16, 24, 32, 40, 48, 56]:
            painter.drawLine(0, y, 64, y)
        for x in [8, 16, 24, 32, 40, 48, 56]:
            painter.drawLine(x, 0, x, 64)

        # Diagonal highlights
        painter.setPen(QColor("#2A2C31"))
        painter.setOpacity(0.2)
        painter.drawLine(0, 0, 64, 64)
        painter.drawLine(64, 0, 0, 64)

        painter.end()

        brush = QBrush(pixmap)
        return brush

    def _setup_ui(self):
        """Setup splash screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Title
        title_label = QLabel("ARBYS")
        title_font = QFont("Arial", 48, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #E6E6E6;")
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Arbitrage Betting Bot")
        subtitle_font = QFont("Arial", 14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #9AA0A6;")
        layout.addWidget(subtitle_label)

        layout.addStretch()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                background-color: #16171A;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #D00000;
                border-radius: 3px;
            }
        """
        )
        layout.addWidget(self.progress_bar)

        # Status label (optional)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #9AA0A6; font-size: 10pt;")
        layout.addWidget(self.status_label)

    def _center_on_screen(self):
        """Center splash screen on primary screen."""
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def paintEvent(self, event):
        """Paint carbon fiber background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill with carbon pattern or solid color
        if self.carbon_pattern:
            painter.fillRect(self.rect(), self.carbon_pattern)
        else:
            painter.fillRect(self.rect(), QColor("#0D0D0F"))

        # Border
        painter.setPen(QColor("#2A2C31"))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)

    def start(self, duration_ms: int = 2000):
        """
        Start splash screen with auto-close timer.

        Args:
            duration_ms: Duration in milliseconds before auto-closing
        """
        self.show()

        # Force immediate paint
        QTimer.singleShot(100, lambda: self.update())

        # Auto-close timer (if not finished manually)
        if duration_ms > 0:
            QTimer.singleShot(duration_ms, lambda: self._auto_finish())

    def _auto_finish(self):
        """Auto-finish if not already finished."""
        if self.isVisible() and not self.fade_animation:
            # If no target window set, just close
            if self.target_window:
                self.finish(self.target_window)
            else:
                self.close()

    def finish(self, window):
        """
        Crossfade from splash to main window.

        Args:
            window: Main window to transition to
        """
        self.target_window = window

        # Start fade out
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.finished.connect(self._on_fade_finished)
        self.fade_animation.start()

    def _on_fade_finished(self):
        """Handle fade animation completion."""
        self.close()
        if self.target_window:
            self.target_window.show()
            # Fade in main window
            self.target_window.setWindowOpacity(0.0)
            fade_in = QPropertyAnimation(self.target_window, b"windowOpacity")
            fade_in.setDuration(200)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.start()
