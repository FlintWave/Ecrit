"""Find & Replace overlay — slides in from top of editor."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


class FindReplaceBar(QFrame):
    find_next = Signal(str, bool, bool)
    find_prev = Signal(str, bool, bool)
    replace_one = Signal(str, str)
    replace_all = Signal(str, str)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(0)
        self._expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        find_row = QHBoxLayout()
        find_label = QLabel("Find")
        find_label.setFixedWidth(60)
        find_row.addWidget(find_label)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Search text...")
        self.find_input.returnPressed.connect(self._on_find_next)
        find_row.addWidget(self.find_input, 1)

        self.match_label = QLabel("0 / 0")
        self.match_label.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 12px;")
        self.match_label.setFixedWidth(60)
        find_row.addWidget(self.match_label)

        prev_btn = QPushButton("↑")
        prev_btn.setObjectName("secondary")
        prev_btn.setFixedSize(28, 28)
        prev_btn.clicked.connect(self._on_find_prev)
        find_row.addWidget(prev_btn)

        next_btn = QPushButton("↓")
        next_btn.setObjectName("secondary")
        next_btn.setFixedSize(28, 28)
        next_btn.clicked.connect(self._on_find_next)
        find_row.addWidget(next_btn)

        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.toggle)
        find_row.addWidget(close_btn)

        layout.addLayout(find_row)

        replace_row = QHBoxLayout()
        replace_label = QLabel("Replace")
        replace_label.setFixedWidth(60)
        replace_row.addWidget(replace_label)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        replace_row.addWidget(self.replace_input, 1)

        r_one = QPushButton("Replace")
        r_one.setObjectName("secondary")
        r_one.setFixedHeight(28)
        r_one.clicked.connect(self._on_replace_one)
        replace_row.addWidget(r_one)

        r_all = QPushButton("All")
        r_all.setObjectName("secondary")
        r_all.setFixedHeight(28)
        r_all.clicked.connect(self._on_replace_all)
        replace_row.addWidget(r_all)

        layout.addLayout(replace_row)

        options = QHBoxLayout()
        self.case_check = QCheckBox("Match case")
        options.addWidget(self.case_check)
        self.regex_check = QCheckBox("Regex")
        options.addWidget(self.regex_check)
        options.addStretch()
        layout.addLayout(options)

    def toggle(self):
        self._expanded = not self._expanded
        self.setFixedHeight(110 if self._expanded else 0)
        if self._expanded:
            self.find_input.setFocus()
        else:
            self.closed.emit()

    def _on_find_next(self):
        self.find_next.emit(
            self.find_input.text(),
            self.case_check.isChecked(),
            self.regex_check.isChecked(),
        )

    def _on_find_prev(self):
        self.find_prev.emit(
            self.find_input.text(),
            self.case_check.isChecked(),
            self.regex_check.isChecked(),
        )

    def _on_replace_one(self):
        self.replace_one.emit(self.find_input.text(), self.replace_input.text())

    def _on_replace_all(self):
        self.replace_all.emit(self.find_input.text(), self.replace_input.text())

    def set_match_count(self, current: int, total: int):
        self.match_label.setText(f"{current} / {total}")
