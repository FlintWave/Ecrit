"""Spell check results dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ecrit.ui.styles import theme


class SpellCheckDialog(QDialog):
    goto_line = Signal(int)
    word_added = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spell Check")
        self.setMinimumSize(700, 460)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Spell Check")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {t.text};")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel()
        self._count_label.setStyleSheet(f"color: {t.neutral_400}; font-size: 13px;")
        header.addWidget(self._count_label)
        layout.addLayout(header)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Word", "Line", "Suggestions", "Context"])
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table, 1)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add to Dictionary")
        add_btn.clicked.connect(self._add_word)
        btn_row.addWidget(add_btn)
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def set_issues(self, issues: list):
        self._issues = issues
        self._count_label.setText(f"{len(issues)} potential misspellings")
        self._table.setRowCount(len(issues))
        for row, issue in enumerate(issues):
            self._table.setItem(row, 0, QTableWidgetItem(issue.word))
            line_item = QTableWidgetItem(str(issue.line + 1))
            line_item.setData(Qt.ItemDataRole.UserRole, issue.line)
            self._table.setItem(row, 1, line_item)
            self._table.setItem(row, 2, QTableWidgetItem(", ".join(issue.suggestions[:5])))
            self._table.setItem(row, 3, QTableWidgetItem(issue.context[:60]))

    def _on_double_click(self, row, col):
        item = self._table.item(row, 1)
        if item:
            line = item.data(Qt.ItemDataRole.UserRole)
            if line is not None:
                self.goto_line.emit(line + 1)

    def _add_word(self):
        item = self._table.currentItem()
        if item:
            row = self._table.currentRow()
            word_item = self._table.item(row, 0)
            if word_item:
                self.word_added.emit(word_item.text())
                self._table.removeRow(row)
                self._count_label.setText(f"{self._table.rowCount()} potential misspellings")
