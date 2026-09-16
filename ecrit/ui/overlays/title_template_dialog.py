"""Title page template picker dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QTextEdit,
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme
from ecrit.screenplay.title_templates import TitleTemplateManager


class TitleTemplateDialog(QDialog):
    template_applied = Signal(str)

    def __init__(self, manager: TitleTemplateManager, parent=None):
        super().__init__(parent)
        self._mgr = manager
        self._fields: dict[str, QLineEdit] = {}
        self.setWindowTitle("Title Page Template")
        self.setMinimumSize(660, 520)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QLabel("Title Page Template")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {t.text};")
        layout.addWidget(header)

        body = QHBoxLayout()

        self._template_list = QListWidget()
        self._template_list.setMaximumWidth(220)
        self._template_list.currentItemChanged.connect(self._on_template_selected)
        body.addWidget(self._template_list)

        right = QVBoxLayout()
        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet(f"color: {t.neutral_400}; font-size: 12px;")
        right.addWidget(self._desc_label)

        self._form_layout = QFormLayout()
        right.addLayout(self._form_layout)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(120)
        self._preview.setStyleSheet(f"font-family: 'Courier Prime', monospace; font-size: 12px; color: {t.text};")
        right.addWidget(self._preview)
        right.addStretch()
        body.addLayout(right, 1)

        layout.addLayout(body, 1)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply Template")
        apply_btn.clicked.connect(self._apply)
        btn_row.addWidget(apply_btn)
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._populate()

    def _populate(self):
        self._template_list.clear()
        for tmpl in self._mgr.list_templates():
            item = QListWidgetItem(tmpl.name)
            item.setData(Qt.ItemDataRole.UserRole, tmpl.id)
            self._template_list.addItem(item)
        if self._template_list.count():
            self._template_list.setCurrentRow(0)

    def _on_template_selected(self, current, previous):
        if not current:
            return
        tid = current.data(Qt.ItemDataRole.UserRole)
        tmpl = self._mgr.get_template(tid)
        if not tmpl:
            return
        self._desc_label.setText(tmpl.description)

        while self._form_layout.count():
            child = self._form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._fields.clear()

        for f in tmpl.fields:
            le = QLineEdit()
            le.setPlaceholderText(f.default_value or f.label)
            le.textChanged.connect(self._update_preview)
            self._form_layout.addRow(f.label + ":", le)
            self._fields[f.key] = le

        self._update_preview()

    def _get_values(self) -> dict[str, str]:
        return {key: le.text() for key, le in self._fields.items()}

    def _update_preview(self):
        item = self._template_list.currentItem()
        if not item:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        tmpl = self._mgr.get_template(tid)
        if not tmpl:
            return
        values = self._get_values()
        fountain = tmpl.render_fountain(values)
        self._preview.setPlainText(fountain)

    def _apply(self):
        item = self._template_list.currentItem()
        if not item:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        tmpl = self._mgr.get_template(tid)
        if not tmpl:
            return
        values = self._get_values()
        fountain = tmpl.render_fountain(values)
        self.template_applied.emit(fountain)
        self.close()
