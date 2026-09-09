"""Custom title bar matching Écrit design: decorative dots, wordmark, phase tabs, save indicator."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QPen

from ecrit.ui.styles import theme


class TitleDots(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(60, 44)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = theme.current()
        color = QColor(t.neutral_800)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        for i, x in enumerate([16, 28, 40]):
            p.drawEllipse(x - 5, 17, 11, 11)
        p.end()


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

    def __init__(self, show_phases=False, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(8)

        self.dots = TitleDots()
        layout.addWidget(self.dots)

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
        t = theme.current()
        self.wordmark.setText(f"<span style='color:{t.text}'>Écrit</span>"
                              f"<span style='color:{t.accent}'>.</span>")
