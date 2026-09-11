"""Sprint timer — timed writing sessions from the status bar."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer

from ecrit.ui.styles import theme


class SprintTimerWidget(QFrame):
    sprint_ended = Signal(int, int)

    PRESETS = [15, 25, 45]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedSize(280, 180)
        self.setWindowFlags(Qt.WindowType.Popup)

        self._running = False
        self._seconds_left = 0
        self._total_seconds = 0
        self._words_at_start = 0

        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        header = QLabel("WRITING SPRINT")
        header.setObjectName("kicker")
        layout.addWidget(header)

        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(
            "font-family: ui-monospace, Menlo, monospace; font-size: 32px; font-weight: 500;"
        )
        layout.addWidget(self.time_label)

        presets = QHBoxLayout()
        for mins in self.PRESETS:
            btn = QPushButton(f"{mins}m")
            btn.setObjectName("secondary")
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked=False, m=mins: self._set_duration(m))
            presets.addWidget(btn)
        layout.addLayout(presets)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primary")
        self.start_btn.setFixedHeight(34)
        self.start_btn.clicked.connect(self._toggle)
        controls.addWidget(self.start_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("secondary")
        self.reset_btn.setFixedHeight(34)
        self.reset_btn.clicked.connect(self._reset)
        controls.addWidget(self.reset_btn)
        layout.addLayout(controls)

        self._set_duration(25)

    def _set_duration(self, minutes: int):
        if self._running:
            return
        self._total_seconds = minutes * 60
        self._seconds_left = self._total_seconds
        self._update_display()

    def _toggle(self):
        if self._running:
            self._running = False
            self._timer.stop()
            self.start_btn.setText("Resume")
        else:
            self._running = True
            self._timer.start()
            self.start_btn.setText("Pause")

    def _reset(self):
        self._running = False
        self._timer.stop()
        self._seconds_left = self._total_seconds
        self.start_btn.setText("Start")
        self._update_display()

    def _tick(self):
        if self._seconds_left > 0:
            self._seconds_left -= 1
            self._update_display()
        else:
            self._running = False
            self._timer.stop()
            self.start_btn.setText("Start")
            self.sprint_ended.emit(self._total_seconds // 60, self._words_at_start)

    def _update_display(self):
        mins = self._seconds_left // 60
        secs = self._seconds_left % 60
        self.time_label.setText(f"{mins:02d}:{secs:02d}")

    def get_status_text(self) -> str:
        if self._running:
            mins = self._seconds_left // 60
            secs = self._seconds_left % 60
            return f"⏱ {mins:02d}:{secs:02d}"
        return ""

    def set_start_words(self, count: int):
        self._words_at_start = count
