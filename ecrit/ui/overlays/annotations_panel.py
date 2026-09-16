"""Annotations panel — view and manage line-anchored notes."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QTextEdit, QInputDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ecrit.screenplay.annotations import AnnotationManager, Annotation


class AnnotationsPanel(QDialog):
    goto_line = Signal(int)

    def __init__(self, annotation_manager: AnnotationManager, parent=None):
        super().__init__(parent)
        self._mgr = annotation_manager
        self.setWindowTitle("Annotations")
        self.setMinimumSize(420, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Annotations")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel()
        self._count_label.setObjectName("countBadge")
        header.addWidget(self._count_label)
        layout.addLayout(header)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self._filter = QComboBox()
        self._filter.addItems(["All", "note", "todo", "question", "fix", "praise", "resolved"])
        self._filter.currentTextChanged.connect(lambda _: self._refresh())
        filter_row.addWidget(self._filter, 1)
        layout.addLayout(filter_row)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_goto)
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        resolve_btn = QPushButton("Resolve")
        resolve_btn.clicked.connect(self._resolve_selected)
        btn_row.addWidget(resolve_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(delete_btn)

        clear_btn = QPushButton("Clear Resolved")
        clear_btn.clicked.connect(self._clear_resolved)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        self._list.clear()
        filter_text = self._filter.currentText()
        if filter_text == "resolved":
            annotations = [a for a in self._mgr.get_all(include_resolved=True) if a.resolved]
        elif filter_text != "All":
            annotations = self._mgr.get_by_category(filter_text)
        else:
            annotations = self._mgr.get_all(include_resolved=False)

        cat_icons = {"note": "📝", "todo": "☑", "question": "❓", "fix": "🔧", "praise": "⭐"}
        for ann in annotations:
            icon = cat_icons.get(ann.category, "📝")
            prefix = "✓ " if ann.resolved else ""
            item = QListWidgetItem(f"{prefix}{icon} L{ann.line + 1}: {ann.text[:60]}")
            item.setData(Qt.ItemDataRole.UserRole, ann)
            item.setForeground(QColor(ann.color))
            self._list.addItem(item)

        summary = self._mgr.get_summary()
        self._count_label.setText(
            f"{summary.get('total', 0)} total · {summary.get('resolved', 0)} resolved"
        )

    def _on_goto(self, item):
        ann = item.data(Qt.ItemDataRole.UserRole)
        if ann:
            self.goto_line.emit(ann.line + 1)

    def _resolve_selected(self):
        item = self._list.currentItem()
        if item:
            ann = item.data(Qt.ItemDataRole.UserRole)
            if ann and not ann.resolved:
                self._mgr.resolve(ann.id)
                self._refresh()

    def _delete_selected(self):
        item = self._list.currentItem()
        if item:
            ann = item.data(Qt.ItemDataRole.UserRole)
            if ann:
                self._mgr.remove(ann.id)
                self._refresh()

    def _clear_resolved(self):
        self._mgr.clear_resolved()
        self._refresh()
