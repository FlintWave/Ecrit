"""Logline Builder dialog -- madlibs-style logline construction."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QScrollArea, QWidget, QTextEdit
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme
from ecrit.screenplay.logline_builder import (
    LOGLINE_TEMPLATES,
    build_logline,
    validate_logline,
)


def _field_display_name(field_name: str) -> str:
    """Turn a snake_case placeholder name into a readable label."""
    return field_name.replace("_", " ").title()


class LoglineBuilderDialog(QDialog):
    """Modal dialog for building a screenplay logline from templates."""

    logline_ready = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logline Builder")
        self.setMinimumSize(520, 400)
        self.setModal(True)

        self._field_inputs: dict[str, QLineEdit] = {}
        self._current_key: str = ""

        t = theme.current()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Header ---
        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel("Logline Builder")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # --- Template selector ---
        selector_area = QVBoxLayout()
        selector_area.setContentsMargins(24, 16, 24, 0)
        selector_area.setSpacing(6)

        selector_label = QLabel("Template")
        selector_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        selector_area.addWidget(selector_label)

        self._template_combo = QComboBox()
        self._template_combo.setFixedHeight(34)
        for key, tmpl in LOGLINE_TEMPLATES.items():
            self._template_combo.addItem(tmpl.name, key)
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        selector_area.addWidget(self._template_combo)

        self._example_label = QLabel()
        self._example_label.setWordWrap(True)
        self._example_label.setStyleSheet(
            f"color: {t.neutral_500}; font-size: 12px; font-style: italic; "
            f"padding: 4px 0;"
        )
        selector_area.addWidget(self._example_label)

        layout.addLayout(selector_area)

        # --- Scrollable fields area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._fields_container = QWidget()
        self._fields_layout = QVBoxLayout(self._fields_container)
        self._fields_layout.setContentsMargins(24, 12, 24, 12)
        self._fields_layout.setSpacing(10)

        scroll.setWidget(self._fields_container)
        layout.addWidget(scroll, 1)

        # --- Divider ---
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(
            f"color: {t.neutral_700 if t.name == 'nocturne' else t.divider};"
        )
        layout.addWidget(divider)

        # --- Preview area ---
        preview_area = QVBoxLayout()
        preview_area.setContentsMargins(24, 12, 24, 0)
        preview_area.setSpacing(6)

        preview_header = QLabel("PREVIEW")
        preview_header.setObjectName("kicker")
        preview_area.addWidget(preview_header)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFixedHeight(72)
        self._preview.setStyleSheet(
            f"background: {t.neutral_800 if t.name == 'nocturne' else t.neutral_200}; "
            f"border: 1px solid {t.neutral_700 if t.name == 'nocturne' else t.neutral_300}; "
            f"border-radius: {t.radius_sm}px; "
            f"padding: 8px; font-size: 13px;"
        )
        preview_area.addWidget(self._preview)

        # --- Validation indicator ---
        self._validation_label = QLabel()
        self._validation_label.setStyleSheet(
            f"color: {t.neutral_500}; font-size: 12px; padding: 2px 0;"
        )
        preview_area.addWidget(self._validation_label)

        layout.addLayout(preview_area)

        # --- Footer buttons ---
        footer = QHBoxLayout()
        footer.setContentsMargins(24, 8, 24, 16)
        footer.addStretch()

        cancel_btn = QPushButton("Close")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.close)
        footer.addWidget(cancel_btn)

        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setObjectName("primary")
        self._apply_btn.setFixedHeight(36)
        self._apply_btn.clicked.connect(self._on_apply)
        footer.addWidget(self._apply_btn)

        layout.addLayout(footer)

        # Initialize with the first template
        self._on_template_changed(0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_template_changed(self, index: int) -> None:
        """Rebuild the dynamic field inputs when the template selection changes."""
        key = self._template_combo.itemData(index)
        if key is None:
            return
        self._current_key = key
        tmpl = LOGLINE_TEMPLATES[key]

        # Show the example text
        if tmpl.example:
            self._example_label.setText(f"e.g. {tmpl.example}")
            self._example_label.setVisible(True)
        else:
            self._example_label.setVisible(False)

        # Clear existing field widgets
        self._field_inputs.clear()
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Create a QLineEdit for each placeholder in the template
        for field_name in tmpl.fields:
            label = QLabel(_field_display_name(field_name))
            label.setStyleSheet("font-size: 13px; font-weight: 500;")
            self._fields_layout.addWidget(label)

            inp = QLineEdit()
            inp.setFixedHeight(32)
            inp.setPlaceholderText(f"Enter {_field_display_name(field_name).lower()}...")
            inp.textChanged.connect(self._update_preview)
            self._fields_layout.addWidget(inp)
            self._field_inputs[field_name] = inp

        self._fields_layout.addStretch()
        self._update_preview()

    def _gather_values(self) -> dict[str, str]:
        """Collect current text from all field inputs."""
        return {name: inp.text() for name, inp in self._field_inputs.items()}

    def _update_preview(self) -> None:
        """Rebuild the preview text and validation indicator."""
        t = theme.current()
        values = self._gather_values()
        all_filled = all(v.strip() for v in values.values())

        if all_filled and values:
            try:
                logline = build_logline(self._current_key, values)
            except KeyError:
                logline = ""
        else:
            # Partial preview: fill blanks with bracketed placeholders
            display_values = {}
            for name, val in values.items():
                display_values[name] = val if val.strip() else f"[{_field_display_name(name)}]"
            tmpl = LOGLINE_TEMPLATES.get(self._current_key)
            if tmpl:
                logline = tmpl.pattern.format(**display_values)
            else:
                logline = ""

        self._preview.setPlainText(logline)

        # Validation
        if logline:
            info = validate_logline(logline)
            word_count = info["word_count"]
            assessment = info["length"]
            if assessment == "short":
                color = t.accent_400
                label = "Short"
            elif assessment == "good":
                color = t.accent_2
                label = "Good"
            else:
                color = t.accent
                label = "Long"
            self._validation_label.setText(f"{word_count} words · {label}")
            self._validation_label.setStyleSheet(
                f"color: {color}; font-size: 12px; padding: 2px 0;"
            )
        else:
            self._validation_label.setText("")

        # Enable Apply only when all fields are filled
        self._apply_btn.setEnabled(all_filled and bool(values))

    def _on_apply(self) -> None:
        """Emit the finished logline and close the dialog."""
        values = self._gather_values()
        if not all(v.strip() for v in values.values()):
            return
        try:
            logline = build_logline(self._current_key, values)
        except KeyError:
            return
        self.logline_ready.emit(logline)
        self.close()
