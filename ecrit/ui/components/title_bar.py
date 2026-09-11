"""Custom title bar matching Écrit design: decorative dots, wordmark, phase tabs, save indicator."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QPen

from ecrit.ui.styles import theme


class WindowButton(QWidget):
    clicked = Signal()

    def __init__(self, role: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._hovered = False
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = {"close": "#FF5F57", "minimize": "#FEBC2E", "maximize": "#28C840"}
        color = QColor(colors.get(self._role, "#888888"))
        if not self._hovered:
            t = theme.current()
            color = QColor(t.neutral_700)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 14, 14)
        if self._hovered:
            p.setPen(QPen(QColor("#4a3030" if self._role == "close" else "#5a4a10" if self._role == "minimize" else "#1a4a1a"), 1.5))
            if self._role == "close":
                p.drawLine(4, 4, 10, 10)
                p.drawLine(10, 4, 4, 10)
            elif self._role == "minimize":
                p.drawLine(3, 7, 11, 7)
            elif self._role == "maximize":
                p.drawRect(3, 3, 8, 8)
        p.end()


class WindowControls(QWidget):
    close_clicked = Signal()
    minimize_clicked = Signal()
    maximize_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(68, 44)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(8)

        self._close = WindowButton("close")
        self._close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self._close)

        self._minimize = WindowButton("minimize")
        self._minimize.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self._minimize)

        self._maximize = WindowButton("maximize")
        self._maximize.clicked.connect(self.maximize_clicked.emit)
        layout.addWidget(self._maximize)

        layout.addStretch()


class PhaseTabBar(QWidget):
    phase_changed = Signal(str)

    PHASES = ["Plan", "Outline", "Manuscript", "Proofread", "Deliver"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("phaseTabs")
        self._active = "Manuscript"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._buttons = {}
        for phase in self.PHASES:
            btn = QPushButton(phase)
            btn.setProperty("active", phase == self._active)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, p=phase: self._on_click(p))
            layout.addWidget(btn)
            self._buttons[phase] = btn

    def _on_click(self, phase: str):
        self._active = phase
        for name, btn in self._buttons.items():
            btn.setProperty("active", name == phase)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.phase_changed.emit(phase)

    def set_active(self, phase: str):
        self._on_click(phase)


class SaveIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 16)
        self._saved = True

    def set_saved(self, saved: bool):
        self._saved = saved
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = theme.current()
        color = QColor(t.accent2_500 if self._saved else t.accent_500)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(4, 4, 8, 8)
        p.end()


class TitleBar(QWidget):
    settings_clicked = Signal()
    home_clicked = Signal()
    phase_changed = Signal(str)
    close_requested = Signal()
    minimize_requested = Signal()
    maximize_requested = Signal()

    def __init__(self, show_phases=False, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(8)

        self.window_controls = WindowControls()
        self.window_controls.close_clicked.connect(self.close_requested.emit)
        self.window_controls.minimize_clicked.connect(self.minimize_requested.emit)
        self.window_controls.maximize_clicked.connect(self.maximize_requested.emit)
        layout.addWidget(self.window_controls)

        self.home_btn = QPushButton("⌂")
        self.home_btn.setObjectName("homeBtn")
        self.home_btn.setFixedSize(28, 28)
        self.home_btn.setToolTip("Dashboard")
        self.home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.home_btn.clicked.connect(self.home_clicked.emit)
        layout.addWidget(self.home_btn)

        self.wordmark = QLabel("Écrit")
        self.wordmark.setObjectName("wordmark")
        layout.addWidget(self.wordmark)

        self.context_label = QLabel()
        self.context_label.setObjectName("titleContext")
        layout.addWidget(self.context_label)

        layout.addStretch()

        if show_phases:
            self.phase_tabs = PhaseTabBar()
            self.phase_tabs.phase_changed.connect(self.phase_changed.emit)
            layout.addWidget(self.phase_tabs)
            layout.addStretch()
        else:
            self.phase_tabs = None

        self.cmd_chip = QPushButton("⌘K  open anything")
        self.cmd_chip.setObjectName("secondary")
        self.cmd_chip.setFixedHeight(28)
        layout.addWidget(self.cmd_chip)

        self.save_dot = SaveIndicator()
        layout.addWidget(self.save_dot)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("iconBtn")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)

    def set_context(self, text: str):
        self.context_label.setText(text)

    def set_wordmark_accent(self):
        from PySide6.QtCore import Qt
        t = theme.current()
        self.wordmark.setTextFormat(Qt.TextFormat.RichText)
        self.wordmark.setText(f"<span style='color:{t.text}'>Écrit</span>"
                              f"<span style='color:{t.accent}'>.</span>")
