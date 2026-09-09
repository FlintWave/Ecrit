"""Scratchpad — right-rail tab for holding cut text (Ctrl+Shift+X)."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


class Scratchpad(QFrame):
    closed = Signal()
    paste_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rail")
        self.setFixedWidth(300)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("SCRATCHPAD")
        title.setObjectName("kicker")
        header.addWidget(title)
        header.addStretch()

        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(22, 22)
        close_btn.clicked.connect(self.closed.emit)
        header.addWidget(close_btn)
        layout.addLayout(header)

        hint = QLabel("Cut text lands here. Drag back to the script when ready.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        layout.addWidget(hint)

        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Nothing here yet...")
        self.text_area.setStyleSheet(
            f"font-family: 'Courier Prime', Courier, monospace; font-size: 13px; "
            f"background: transparent; border: 1px solid {t.divider}; border-radius: 6px; "
            f"padding: 8px;"
        )
        layout.addWidget(self.text_area, 1)

        buttons = QHBoxLayout()
        paste_btn = QPushButton("Paste to script")
        paste_btn.setObjectName("primary")
        paste_btn.setFixedHeight(30)
        paste_btn.clicked.connect(self._on_paste)
        buttons.addWidget(paste_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondary")
        clear_btn.setFixedHeight(30)
        clear_btn.clicked.connect(self._on_clear)
        buttons.addWidget(clear_btn)
        layout.addLayout(buttons)

    def add_text(self, text: str):
        current = self.text_area.toPlainText()
        if current:
            self.text_area.setPlainText(current + "\n\n---\n\n" + text)
        else:
            self.text_area.setPlainText(text)

    def _on_paste(self):
        text = self.text_area.toPlainText()
        if text:
            self.paste_requested.emit(text)

    def _on_clear(self):
        self.text_area.clear()
