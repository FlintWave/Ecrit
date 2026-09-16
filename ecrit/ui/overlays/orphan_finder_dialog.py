"""Orphan/widow finder results dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor



class OrphanFinderDialog(QDialog):
    goto_line = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shorten Script — Orphan/Widow Finder")
        self.setMinimumSize(750, 480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Orphan / Widow Finder")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self._summary_label = QLabel()
        self._summary_label.setObjectName("countBadge")
        header.addWidget(self._summary_label)
        layout.addLayout(header)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Sev.", "Type", "Line", "Text", "Suggestion"])
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def set_issues(self, issues: list, summary: dict):
        sev_colors = {"high": "#E57373", "medium": "#FFB74D", "low": "#81C784"}
        self._summary_label.setText(
            f"{summary.get('total_issues', 0)} issues · "
            f"~{summary.get('potential_pages_saved', 0):.1f} pages saveable"
        )
        self._table.setRowCount(len(issues))
        for row, issue in enumerate(issues):
            sev_item = QTableWidgetItem(issue.severity.upper())
            sev_item.setForeground(QColor(sev_colors.get(issue.severity, "#FFFFFF")))
            self._table.setItem(row, 0, sev_item)
            self._table.setItem(row, 1, QTableWidgetItem(issue.issue_type.replace("_", " ")))
            line_item = QTableWidgetItem(str(issue.line_number + 1))
            line_item.setData(Qt.ItemDataRole.UserRole, issue.line_number)
            self._table.setItem(row, 2, line_item)
            self._table.setItem(row, 3, QTableWidgetItem(issue.text[:80]))
            self._table.setItem(row, 4, QTableWidgetItem(issue.suggestion))

    def _on_double_click(self, row, col):
        item = self._table.item(row, 2)
        if item:
            line = item.data(Qt.ItemDataRole.UserRole)
            if line is not None:
                self.goto_line.emit(line + 1)
