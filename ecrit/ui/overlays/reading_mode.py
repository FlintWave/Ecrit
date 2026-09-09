"""Reading mode — distraction-free full-screen script view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from ecrit.ui.styles import theme


class ReadingMode(QWidget):
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        t = theme.current()
        self.setStyleSheet(f"background: {t.bg};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 12, 20, 0)
        top_bar.addStretch()

        self.page_label = QLabel()
        self.page_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        top_bar.addWidget(self.page_label)

        top_bar.addStretch()

        exit_btn = QPushButton("Exit Reading Mode")
        exit_btn.setObjectName("secondary")
        exit_btn.setFixedHeight(28)
        exit_btn.clicked.connect(self.exit_requested.emit)
        top_bar.addWidget(exit_btn)
        layout.addLayout(top_bar)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.text_view = QPlainTextEdit()
        self.text_view.setObjectName("scriptEditor")
        self.text_view.setReadOnly(True)
        font = QFont("Courier Prime", 15)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_view.setFont(font)
        self.text_view.setMaximumWidth(680)
        self.text_view.setStyleSheet(
            f"background: {t.surface}; color: {t.text}; border: none; "
            f"font-family: 'Courier Prime', Courier, monospace; font-size: 15px; padding: 40px;"
        )
        center_layout.addWidget(self.text_view)
        layout.addWidget(center, 1)

        hint = QLabel("Press Esc to exit reading mode")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {t.neutral_600}; font-size: 12px; padding: 8px;")
        layout.addWidget(hint)

    def set_content(self, text: str, page: int = 1, total_pages: int = 1):
        self.text_view.setPlainText(text)
        self.page_label.setText(f"Page {page} of {total_pages}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.exit_requested.emit()
        else:
            super().keyPressEvent(event)
