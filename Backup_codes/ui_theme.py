#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# FUNCTIONS / METHODS LIST:
# - qtype_code(qtype) -> "MCQ" | "TF"
# - qtype_label(qtype) -> "Multiple Choice Question" | "True or False"
# - is_mcq(question_or_qtype) -> bool
# - tf_choices() -> ["True", "False"]
# - apply_app_theme(app)
# - start_yellow_canvas(widget)
#
# CLASSES & METHODS:
# - GradientButton: __init__(), enterEvent(), leaveEvent(), mousePressEvent(),
#                   mouseReleaseEvent(), _tick(), paintEvent(), sizeHint()
# - QuizizzChoiceButton: __init__(), set_choice_text(), set_selected(),
#                        enterEvent(), leaveEvent(), mousePressEvent(),
#                        mouseReleaseEvent(), _tick(), paintEvent()
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#
# Shared yellow / Quizizz look for every window. Question types are stored as
# MCQ / TF in JSON (old quizzes still open), but the UI always says
# "Multiple Choice Question" and "True or False".

from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QSize, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QFont, QPainterPath, QBrush,
)

MCQ_LABEL = "Multiple Choice Question"
TF_LABEL = "True or False"
TF_CHOICES = ["True", "False"]

# Quizizz-style answer tiles: red triangle, blue diamond, yellow circle, teal square
QUIZIZZ_TILES = [
    {"fill": QColor("#E21B3C"), "fill2": QColor("#FF5A74"), "shape": "triangle"},
    {"fill": QColor("#1368CE"), "fill2": QColor("#4C9AFF"), "shape": "diamond"},
    {"fill": QColor("#D89E00"), "fill2": QColor("#FFD54F"), "shape": "circle"},
    {"fill": QColor("#26890C"), "fill2": QColor("#66BB6A"), "shape": "square"},
]

APP_QSS = """
QWidget {
    color: #4E342E;
    font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
    font-size: 13px;
}
QLabel {
    background: transparent;
    color: #4E342E;
}
QLineEdit, QSpinBox, QComboBox, QTextEdit, QListWidget, QTableWidget, QAbstractSpinBox {
    background: rgba(255, 253, 231, 0.94);
    border: 2px solid #FFC107;
    border-radius: 10px;
    padding: 6px 10px;
    selection-background-color: #FFD54F;
    color: #3E2723;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border: 2px solid #FF8F00;
    background: #FFFDE7;
}
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #FFE082, stop:0.5 #FFC107, stop:1 #FFB300);
    color: #3E2723;
    font-weight: bold;
    padding: 6px;
    border: none;
    border-right: 1px solid #FFECB3;
}
QTableWidget, QListWidget {
    background: rgba(255, 253, 231, 0.88);
    alternate-background-color: rgba(255, 236, 179, 0.55);
    gridline-color: #FFE082;
}
QTableWidget::item:selected, QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #FFD54F, stop:1 #FFC107);
    color: #3E2723;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFE082, stop:0.5 #FFC107, stop:1 #FFB300);
    color: #3E2723;
    font-weight: 700;
    border: none;
    border-radius: 12px;
    padding: 9px 16px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFF59D, stop:0.45 #FFD54F, stop:1 #FFA000);
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFB300, stop:1 #FF8F00);
    padding-top: 11px;
    padding-bottom: 7px;
}
QDialogButtonBox QPushButton {
    min-width: 90px;
}
QComboBox QAbstractItemView {
    background: #FFFDE7;
    selection-background-color: #FFD54F;
    border: 1px solid #FFC107;
}
QMessageBox {
    background-color: #FFF8E1;
}
QScrollBar:vertical {
    background: #FFF8E1;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #FFC107;
    border-radius: 6px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #FFB300;
}
"""


def qtype_code(qtype):
    text = (qtype or "").strip()
    if text in ("MCQ", MCQ_LABEL, "Multiple Choice"):
        return "MCQ"
    return "TF"


def qtype_label(qtype):
    return MCQ_LABEL if qtype_code(qtype) == "MCQ" else TF_LABEL


def is_mcq(question_or_qtype):
    if isinstance(question_or_qtype, dict):
        return qtype_code(question_or_qtype.get("qtype", "MCQ")) == "MCQ"
    return qtype_code(question_or_qtype) == "MCQ"


def tf_choices():
    return TF_CHOICES.copy()


def apply_app_theme(app):
    app.setStyleSheet(APP_QSS)


def start_yellow_canvas(widget):
    """Slow drifting gold gradient behind a window. Call once after super().__init__."""
    widget._gold_shift = 0.0
    widget._gold_timer = QTimer(widget)
    widget._gold_timer.setInterval(40)
    widget._gold_timer.timeout.connect(lambda: _advance_gold(widget))
    widget._gold_timer.start()
    widget.setAutoFillBackground(False)

    def paintEvent(event):
        _paint_gold(widget)

    widget.paintEvent = paintEvent


def _advance_gold(widget):
    widget._gold_shift = (getattr(widget, "_gold_shift", 0.0) + 0.004) % 1.0
    widget.update()


def _paint_gold(widget):
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    shift = getattr(widget, "_gold_shift", 0.0)
    gradient = QLinearGradient(0, 0, widget.width(), widget.height())
    stops = [
        ((0.00 + shift) % 1.0, QColor("#FFFDE7")),
        ((0.28 + shift) % 1.0, QColor("#FFE082")),
        ((0.55 + shift) % 1.0, QColor("#FFD54F")),
        ((0.82 + shift) % 1.0, QColor("#FFC107")),
    ]
    stops.sort(key=lambda item: item[0])
    gradient.setColorAt(0.0, stops[0][1])
    for pos, color in stops:
        gradient.setColorAt(pos, color)
    gradient.setColorAt(1.0, QColor("#FFECB3"))
    painter.fillRect(widget.rect(), gradient)
    painter.end()


class GradientButton(QPushButton):
    """Yellow pill button whose gradient slides on hover and flashes on click."""

    def __init__(self, text="", parent=None, clicked=None):
        super().__init__(text, parent)
        self._shift = 0.0
        self._hover = 0.0
        self._press = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent; border: none; color: #3E2723;")
        if clicked is not None:
            super().clicked.connect(clicked)

    def sizeHint(self):
        return QSize(180, 42)

    def enterEvent(self, event):
        self._timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._timer.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._press = 1.0
        self._timer.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def _tick(self):
        target = 1.0 if self.underMouse() else 0.0
        self._hover += (target - self._hover) * 0.16
        if self.underMouse():
            self._shift = (self._shift + 0.018) % 1.0
        self._press *= 0.82
        if self._hover < 0.01 and self._press < 0.01 and not self.underMouse():
            self._hover = 0.0
            self._press = 0.0
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(2, 2 - self._hover * 2, -2, -2 - self._hover * 2)
        shift = self._shift
        glow = 30 * self._hover
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        c1 = QColor(255, 224, 130 + int(glow))
        c2 = QColor(255, 193, 7)
        c3 = QColor(255, 160 + int(20 * self._press), 0)
        pairs = [
            ((0.0 + shift) % 1.0, c1),
            ((0.5 + shift) % 1.0, c2),
            ((0.85 + shift) % 1.0, c3),
        ]
        pairs.sort(key=lambda item: item[0])
        gradient.setColorAt(0.0, pairs[0][1])
        for pos, color in pairs:
            gradient.setColorAt(min(pos, 0.999), color)
        gradient.setColorAt(1.0, pairs[-1][1])
        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        painter.fillPath(path, QBrush(gradient))
        if self._hover > 0.05:
            painter.setPen(QPen(QColor(255, 255, 255, int(90 * self._hover)), 2))
            painter.drawPath(path)
        painter.setPen(QColor("#3E2723"))
        font = QFont(self.font())
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()


class QuizizzChoiceButton(QPushButton):
    """One Quizizz-style answer tile (colored shape + choice text)."""

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self._tile = QUIZIZZ_TILES[index % 4]
        self._choice_text = ""
        self._selected = False
        self._hover = 0.0
        self._press = 0.0
        self._shift = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: transparent; border: none; color: white;")

    def set_choice_text(self, text):
        self._choice_text = text
        self.setText(text)
        self.update()

    def set_selected(self, selected):
        self._selected = selected
        self.setChecked(selected)
        self.update()

    def enterEvent(self, event):
        self._timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._timer.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._press = 1.0
        self._timer.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def _tick(self):
        target = 1.0 if self.underMouse() or self._selected else 0.0
        self._hover += (target - self._hover) * 0.18
        if self.underMouse() or self._selected:
            self._shift = (self._shift + 0.02) % 1.0
        self._press *= 0.8
        if self._hover < 0.01 and self._press < 0.01 and not self.underMouse() and not self._selected:
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        lift = 3 * self._hover
        rect = QRectF(self.rect()).adjusted(4, 4 - lift, -4, -4 - lift * 0.3)
        base = self._tile["fill"]
        lite = self._tile["fill2"]
        if self._press > 0.05:
            base = base.darker(110 + int(20 * self._press))
        gradient = QLinearGradient(rect.topLeft(), QPointF(rect.right(), rect.bottom()))
        pairs = [
            ((0.0 + self._shift) % 1.0, lite),
            ((0.55 + self._shift) % 1.0, base),
            ((0.9 + self._shift) % 1.0, base.darker(115)),
        ]
        pairs.sort(key=lambda item: item[0])
        gradient.setColorAt(0.0, pairs[0][1])
        for pos, color in pairs:
            gradient.setColorAt(min(pos, 0.999), color)
        gradient.setColorAt(1.0, pairs[-1][1])
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)
        painter.fillPath(path, QBrush(gradient))
        if self._selected:
            painter.setPen(QPen(QColor("#FFFDE7"), 4))
            painter.drawPath(path)
        elif self._hover > 0.2:
            painter.setPen(QPen(QColor(255, 255, 255, int(160 * self._hover)), 3))
            painter.drawPath(path)

        shape_box = QRectF(rect.left() + 16, rect.center().y() - 16, 32, 32)
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.setPen(Qt.PenStyle.NoPen)
        self._draw_shape(painter, shape_box, self._tile["shape"])

        text_rect = QRectF(rect.left() + 58, rect.top() + 8, rect.width() - 70, rect.height() - 16)
        painter.setPen(QColor("white"))
        font = QFont(self.font())
        font.setBold(True)
        font.setPointSize(13)
        painter.setFont(font)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
            self._choice_text,
        )
        painter.end()

    def _draw_shape(self, painter, box, shape):
        path = QPainterPath()
        if shape == "triangle":
            path.moveTo(box.center().x(), box.top())
            path.lineTo(box.right(), box.bottom())
            path.lineTo(box.left(), box.bottom())
            path.closeSubpath()
        elif shape == "diamond":
            path.moveTo(box.center().x(), box.top())
            path.lineTo(box.right(), box.center().y())
            path.lineTo(box.center().x(), box.bottom())
            path.lineTo(box.left(), box.center().y())
            path.closeSubpath()
        elif shape == "circle":
            path.addEllipse(box)
        else:
            path.addRoundedRect(box, 4, 4)
        painter.drawPath(path)
