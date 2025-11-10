"""
Tutorial overlay system with coach marks.

Creates spotlight effect highlighting specific widgets with instructional text.
"""

import logging

from PyQt6.QtCore import QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QRegion
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)

logger = logging.getLogger(__name__)


class OnboardingTour(QWidget):
    """
    Tutorial overlay with coach marks.

    Shows spotlight effect on target widgets with instructional text.
    """

    finished = pyqtSignal()

    def __init__(self, steps: list[tuple[QWidget, str, str]], parent: QWidget | None = None):
        """
        Initialize tutorial tour.

        Args:
            steps: List of (widget, title, body) tuples
            parent: Parent widget (usually main window)
        """
        super().__init__(parent)
        self.steps = steps
        self.current_step = 0

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WidgetAttribute.WA_TranslucentBackground
        )

        # Overlay state
        self.target_widget: QWidget | None = None
        self.spotlight_rect: QRect | None = None

        # Control buttons
        self.skip_btn = None
        self.next_btn = None

        self._setup_ui()
        self._show_step(0)

    def _setup_ui(self):
        """Setup overlay UI elements."""
        # Buttons are created dynamically in _show_step based on position

    def _show_step(self, step_index: int):
        """Show a specific tutorial step."""
        if step_index < 0 or step_index >= len(self.steps):
            self._finish()
            return

        self.current_step = step_index
        widget, title, body = self.steps[step_index]

        # Find target widget
        if not widget or not widget.isVisible():
            logger.warning(f"Step {step_index}: widget not visible, skipping")
            QTimer.singleShot(100, lambda: self._show_step(step_index + 1))
            return

        self.target_widget = widget

        # Resize overlay to cover entire screen first
        if self.parent():
            parent_rect = self.parent().geometry()
            self.setGeometry(parent_rect)
        else:
            from PyQt6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().geometry()
            self.setGeometry(screen)

        # Calculate widget position in global coordinates, then convert to overlay coordinates
        global_pos = widget.mapToGlobal(QPoint(0, 0))
        overlay_global_pos = self.mapToGlobal(QPoint(0, 0))

        # Convert to overlay-relative coordinates
        widget_rect = QRect(
            global_pos.x() - overlay_global_pos.x(),
            global_pos.y() - overlay_global_pos.y(),
            widget.width(),
            widget.height(),
        )

        # Expand spotlight rect slightly for padding
        padding = 10
        self.spotlight_rect = QRect(
            widget_rect.x() - padding,
            widget_rect.y() - padding,
            widget_rect.width() + padding * 2,
            widget_rect.height() + padding * 2,
        )

        # Store step info for paintEvent
        self.step_title = title
        self.step_body = body

        # Create/update control buttons
        self._setup_buttons()

        self.show()
        self.raise_()
        self.activateWindow()
        self.update()

    def _setup_buttons(self):
        """Create or update navigation buttons."""
        # Remove existing buttons
        if self.skip_btn:
            self.skip_btn.deleteLater()
        if self.next_btn:
            self.next_btn.deleteLater()

        # Create Skip button
        self.skip_btn = QPushButton("Skip", self)
        self.skip_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1C1D22;
                border: 1px solid #2A2C31;
                border-radius: 4px;
                padding: 8px 20px;
                color: #E6E6E6;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #2A2C31;
            }
        """
        )
        self.skip_btn.clicked.connect(self._finish)

        # Create Next button
        btn_text = "Finish" if self.current_step >= len(self.steps) - 1 else "Next"
        self.next_btn = QPushButton(btn_text, self)
        self.next_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #D00000;
                border: 1px solid #FF0033;
                border-radius: 4px;
                padding: 8px 20px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #FF0033;
                box-shadow: 0 0 10px rgba(208, 0, 0, 0.6);
            }
        """
        )
        self.next_btn.clicked.connect(self._next_step)

        # Position buttons at bottom center
        btn_width = 100
        btn_height = 35
        btn_spacing = 15
        total_width = btn_width * 2 + btn_spacing

        x = (self.width() - total_width) // 2
        y = self.height() - btn_height - 30

        self.skip_btn.setGeometry(x, y, btn_width, btn_height)
        self.next_btn.setGeometry(x + btn_width + btn_spacing, y, btn_width, btn_height)

        self.skip_btn.show()
        self.next_btn.show()

    def paintEvent(self, event):
        """Paint overlay with spotlight effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill entire screen with semi-transparent dark overlay
        overlay_color = QColor(0, 0, 0, 200)  # Semi-transparent black
        painter.fillRect(self.rect(), overlay_color)

        if not self.spotlight_rect:
            return

        # Clear spotlight area (cutout)
        # We need to use QRegion or path to create a cutout

        # Create region for entire screen
        full_region = QRegion(self.rect())

        # Create rounded rect for spotlight
        spotlight_region = QRegion(self.spotlight_rect, QRegion.RegionType.Rectangle)

        # Subtract spotlight from overlay
        masked_region = full_region.subtracted(spotlight_region)

        # Fill masked region (everything except spotlight)
        painter.setClipRegion(masked_region)
        painter.fillRect(self.rect(), overlay_color)
        painter.setClipping(False)

        # Draw spotlight border (glow effect)
        border_pen = painter.pen()
        border_pen.setWidth(3)
        border_pen.setColor(QColor("#D00000"))
        painter.setPen(border_pen)

        # Draw rounded rectangle border around spotlight
        painter.drawRoundedRect(self.spotlight_rect, 8, 8)

        # Draw inner border (lighter)
        inner_rect = self.spotlight_rect.adjusted(2, 2, -2, -2)
        border_pen.setWidth(1)
        border_pen.setColor(QColor("#FF0033"))
        painter.setPen(border_pen)
        painter.drawRoundedRect(inner_rect, 6, 6)

        # Draw tooltip card near spotlight
        self._draw_tooltip_card(painter)

    def _draw_tooltip_card(self, painter: QPainter):
        """Draw tooltip card with title and body text."""
        if not self.spotlight_rect:
            return

        # Calculate tooltip position (prefer below, fallback to above)
        card_width = 350
        card_height = 150
        card_margin = 20

        # Try below spotlight
        tooltip_x = self.spotlight_rect.center().x() - card_width // 2
        tooltip_y = self.spotlight_rect.bottom() + card_margin

        # Check if fits on screen
        if tooltip_y + card_height > self.height():
            # Place above
            tooltip_y = self.spotlight_rect.top() - card_height - card_margin

        # Ensure tooltip stays on screen
        tooltip_x = max(10, min(tooltip_x, self.width() - card_width - 10))
        tooltip_y = max(10, min(tooltip_y, self.height() - card_height - 10))

        tooltip_rect = QRect(tooltip_x, tooltip_y, card_width, card_height)

        # Draw card background
        card_bg = QColor("#1C1D22")
        painter.setBrush(QBrush(card_bg))
        painter.setPen(QColor("#2A2C31"))
        painter.drawRoundedRect(tooltip_rect, 8, 8)

        # Draw shadow effect (simple)
        shadow_rect = tooltip_rect.translated(2, 2)
        shadow_color = QColor(0, 0, 0, 100)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 8, 8)

        # Redraw card on top
        painter.setBrush(QBrush(card_bg))
        painter.setPen(QColor("#2A2C31"))
        painter.drawRoundedRect(tooltip_rect, 8, 8)

        # Draw title
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#E6E6E6"))

        title_rect = QRect(
            tooltip_rect.x() + 15, tooltip_rect.y() + 15, tooltip_rect.width() - 30, 25
        )
        painter.drawText(
            title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.step_title
        )

        # Draw body
        body_font = QFont("Arial", 10)
        painter.setFont(body_font)
        painter.setPen(QColor("#9AA0A6"))

        body_rect = QRect(
            tooltip_rect.x() + 15,
            tooltip_rect.y() + 45,
            tooltip_rect.width() - 30,
            tooltip_rect.height() - 60,
        )
        painter.drawText(
            body_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            self.step_body,
        )

        # Draw step counter
        counter_text = f"Step {self.current_step + 1} of {len(self.steps)}"
        counter_font = QFont("Arial", 9)
        painter.setFont(counter_font)
        painter.setPen(QColor("#9AA0A6"))

        counter_rect = QRect(
            tooltip_rect.x() + 15,
            tooltip_rect.y() + tooltip_rect.height() - 25,
            tooltip_rect.width() - 30,
            20,
        )
        painter.drawText(
            counter_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, counter_text
        )

    def mousePressEvent(self, event):
        """Handle mouse clicks - only allow clicking through overlay, not on tooltip."""
        # Allow clicks outside spotlight to pass through
        if self.spotlight_rect and self.spotlight_rect.contains(event.pos()):
            # Click on spotlight - advance or do nothing
            pass
        else:
            # Click outside - could close, but we'll keep it for now
            # Users should use buttons
            pass

    def keyPressEvent(self, event):
        """Handle keyboard navigation."""
        if event.key() == Qt.Key.Key_Escape:
            self._finish()
        elif (
            event.key() == Qt.Key.Key_Return
            or event.key() == Qt.Key.Key_Enter
            or event.key() == Qt.Key.Key_Right
        ):
            self._next_step()
        elif event.key() == Qt.Key.Key_Left:
            self._prev_step()

    def _next_step(self):
        """Advance to next step."""
        if self.current_step < len(self.steps) - 1:
            self._show_step(self.current_step + 1)
        else:
            self._finish()

    def _prev_step(self):
        """Go back to previous step."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _finish(self):
        """Finish tutorial."""
        # Clean up buttons
        if self.skip_btn:
            self.skip_btn.deleteLater()
        if self.next_btn:
            self.next_btn.deleteLater()
        self.finished.emit()
        self.close()

    def show_controls(self):
        """Show navigation controls (called externally if needed)."""
        # Controls are drawn in paintEvent, but we could add actual buttons
        # For now, keyboard navigation is sufficient


# Convenience function to create buttons overlay
def create_tour_controls(parent: QWidget) -> tuple[QPushButton, QPushButton]:
    """Create Next and Skip buttons for tour controls."""
    controls_widget = QWidget(parent)
    controls_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    controls_layout = QHBoxLayout(controls_widget)

    skip_btn = QPushButton("Skip")
    skip_btn.setStyleSheet(
        """
        QPushButton {
            background-color: #1C1D22;
            border: 1px solid #2A2C31;
            border-radius: 4px;
            padding: 8px 16px;
            color: #E6E6E6;
        }
        QPushButton:hover {
            background-color: #2A2C31;
        }
    """
    )

    next_btn = QPushButton("Next")
    next_btn.setStyleSheet(
        """
        QPushButton {
            background-color: #D00000;
            border: 1px solid #FF0033;
            border-radius: 4px;
            padding: 8px 16px;
            color: #FFFFFF;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #FF0033;
            box-shadow: 0 0 10px rgba(208, 0, 0, 0.6);
        }
    """
    )

    controls_layout.addWidget(skip_btn)
    controls_layout.addWidget(next_btn)

    return skip_btn, next_btn
