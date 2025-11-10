"""
Racing-style tachometer widget for displaying stealth scores with needle-sweep animation.
"""

import math

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtProperty
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class TachometerWidget(QWidget):
    """
    Racing tachometer-style gauge for displaying stealth scores (0.0-1.0).
    Features needle-sweep animation and racing telemetry aesthetics.
    """

    def __init__(self, parent=None, label: str = "Stealth", size: int = 120):
        super().__init__(parent)
        self.label = label
        self.size = size
        self._value = 0.0  # 0.0 to 1.0
        self._display_value = 0.0  # Animated value for smooth needle movement

        # Animation for needle sweep
        self.needle_animation = QPropertyAnimation(self, b"displayValue")
        self.needle_animation.setDuration(800)  # 800ms sweep
        self.needle_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setMinimumSize(size, size + 30)  # Extra space for label
        self.setMaximumSize(size, size + 30)

    def setValue(self, value: float, animated: bool = True):
        """
        Set the tachometer value (0.0 to 1.0).

        Args:
            value: Value between 0.0 and 1.0
            animated: Whether to animate the needle sweep
        """
        value = max(0.0, min(1.0, value))  # Clamp to [0, 1]
        self._value = value

        if animated:
            self.needle_animation.setStartValue(self._display_value)
            self.needle_animation.setEndValue(value)
            self.needle_animation.start()
        else:
            self._display_value = value
            self.update()

    def getDisplayValue(self) -> float:
        """Get the current animated display value."""
        return self._display_value

    def setDisplayValue(self, value: float):
        """Set the animated display value (used by QPropertyAnimation)."""
        self._display_value = value
        self.update()

    # Property for animation
    displayValue = pyqtProperty(float, getDisplayValue, setDisplayValue)

    def paintEvent(self, event):  # pragma: no cover
        """Paint the tachometer gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height() - 30  # Reserve space for label
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 10

        # Calculate angle for needle (0° at left, 180° at right)
        # Map 0.0-1.0 to 180° range (0° to 180°)
        angle = 180.0 * self._display_value

        # Draw gauge arc background
        self._draw_gauge_arc(painter, center_x, center_y, radius, angle)

        # Draw gauge markings
        self._draw_gauge_markings(painter, center_x, center_y, radius)

        # Draw needle
        self._draw_needle(painter, center_x, center_y, radius, angle)

        # Draw center dot
        painter.setBrush(QBrush(QColor(40, 40, 45)))
        painter.setPen(QPen(QColor(255, 0, 51), 2))
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)

        # Draw value text and label
        painter.setPen(QColor(230, 230, 230))

        # Value as percentage
        value_pct = self._display_value * 100
        font = QFont("Rajdhani", 14, QFont.Weight.Bold)
        painter.setFont(font)
        value_text = f"{value_pct:.0f}%"
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(value_text)
        painter.drawText(center_x - text_width // 2, center_y + 5, value_text)

        # Label below gauge
        label_font = QFont("Rajdhani", 9, QFont.Weight.Normal)
        painter.setFont(label_font)
        label_metrics = QFontMetrics(label_font)
        label_width = label_metrics.horizontalAdvance(self.label)
        painter.setPen(QColor(154, 160, 166))  # Muted color
        painter.drawText(center_x - label_width // 2, height + 20, self.label)

    def _draw_gauge_arc(
        self, painter: QPainter, cx: int, cy: int, radius: int, current_angle: float
    ):
        """Draw the gauge arc with color zones."""
        # Draw background arc (full 180°)
        pen = QPen(QColor(42, 44, 49), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        start_angle = 0 * 16  # Start at 0° (left)
        span_angle = 180 * 16  # 180° arc

        # Background arc
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, start_angle, span_angle)

        # Draw colored zones based on value
        # Red zone: 0-60° (0.0-0.33)
        # Orange zone: 60-120° (0.33-0.67)
        # Green zone: 120-180° (0.67-1.0)

        if current_angle <= 60:
            # Red zone
            color = QColor(208, 0, 0)  # Theme red
        elif current_angle <= 120:
            # Orange zone
            color = QColor(255, 152, 0)  # Theme orange
        else:
            # Green zone
            color = QColor(76, 175, 80)  # Theme green

        # Draw filled arc up to current angle
        pen = QPen(color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        filled_span = int(current_angle * 16)
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, start_angle, filled_span)

        # Add glow effect for red zone (danger)
        if current_angle <= 60:
            glow_pen = QPen(
                QColor(255, 0, 51, 100), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
            )
            painter.setPen(glow_pen)
            painter.drawArc(
                cx - radius, cy - radius, radius * 2, radius * 2, start_angle, filled_span
            )

    def _draw_gauge_markings(self, painter: QPainter, cx: int, cy: int, radius: int):
        """Draw gauge markings and numbers."""
        painter.setPen(QPen(QColor(154, 160, 166), 1))
        font = QFont("Rajdhani", 8, QFont.Weight.Normal)
        painter.setFont(font)

        # Draw major markings at 0%, 25%, 50%, 75%, 100%
        for i in range(5):
            angle = i * 45  # 0, 45, 90, 135, 180 degrees
            math.radians(angle)

            # Marking line
            x1 = cx + (radius - 15) * math.cos(math.radians(180 - angle))
            y1 = cy - (radius - 15) * math.sin(math.radians(180 - angle))
            x2 = cx + (radius - 5) * math.cos(math.radians(180 - angle))
            y2 = cy - (radius - 5) * math.sin(math.radians(180 - angle))

            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            # Number label
            value_pct = i * 25
            label_text = f"{value_pct}%"
            label_metrics = QFontMetrics(font)
            label_width = label_metrics.horizontalAdvance(label_text)
            label_height = label_metrics.height()

            label_x = cx + (radius - 25) * math.cos(math.radians(180 - angle)) - label_width // 2
            label_y = cy - (radius - 25) * math.sin(math.radians(180 - angle)) + label_height // 2

            painter.drawText(int(label_x), int(label_y), label_text)

        # Draw minor markings
        for i in range(21):  # Every 5% increment
            if i % 5 != 0:  # Skip major markings
                angle = i * 9  # 9° per 5% increment
                math.radians(angle)

                x1 = cx + (radius - 10) * math.cos(math.radians(180 - angle))
                y1 = cy - (radius - 10) * math.sin(math.radians(180 - angle))
                x2 = cx + (radius - 5) * math.cos(math.radians(180 - angle))
                y2 = cy - (radius - 5) * math.sin(math.radians(180 - angle))

                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_needle(self, painter: QPainter, cx: int, cy: int, radius: int, angle: float):
        """Draw the needle with racing-style appearance."""
        # Convert angle to radians (needle starts at left, 0°)
        angle_rad = math.radians(180 - angle)

        # Needle length (80% of radius)
        needle_length = radius * 0.8

        # Needle tip
        tip_x = cx + needle_length * math.cos(angle_rad)
        tip_y = cy - needle_length * math.sin(angle_rad)

        # Needle base (slightly offset from center for visual effect)
        base_offset = 3
        base_x1 = cx + base_offset * math.cos(angle_rad + math.pi / 2)
        base_y1 = cy - base_offset * math.sin(angle_rad + math.pi / 2)
        base_x2 = cx + base_offset * math.cos(angle_rad - math.pi / 2)
        base_y2 = cy - base_offset * math.sin(angle_rad - math.pi / 2)

        # Draw needle body with gradient-like effect
        # Red needle for low values, transitions to green for high values
        if angle <= 60:
            needle_color = QColor(255, 0, 51)  # Bright red
        elif angle <= 120:
            needle_color = QColor(255, 152, 0)  # Orange
        else:
            needle_color = QColor(76, 175, 80)  # Green

        pen = QPen(needle_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Draw needle as triangle
        from PyQt6.QtCore import QPoint
        from PyQt6.QtGui import QPolygon

        needle_poly = QPolygon(
            [
                QPoint(int(tip_x), int(tip_y)),
                QPoint(int(base_x1), int(base_y1)),
                QPoint(int(base_x2), int(base_y2)),
            ]
        )

        # Fill needle
        brush = QBrush(needle_color)
        painter.setBrush(brush)
        painter.drawPolygon(needle_poly)

        # Add glow effect
        glow_pen = QPen(
            QColor(needle_color.red(), needle_color.green(), needle_color.blue(), 60), 4
        )
        painter.setPen(glow_pen)
        painter.drawLine(cx, cy, int(tip_x), int(tip_y))
