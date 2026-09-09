"""Settings dialog — General, Editor, Theme, About, Modules tabs."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QTabWidget, QWidget,
    QFrame, QFileDialog, QListWidget, QListWidgetItem, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme
from ecrit.i18n import tr, set_language, get_language, available_languages


class _FormGroup(QFrame):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        t = theme.current()
        self.setStyleSheet(
            f"QFrame {{ background: {t.neutral_100 if t.name == 'organic' else t.neutral_900}; "
            f"border-radius: 8px; padding: 0; }}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 12)
        self._layout.setSpacing(10)
        if label:
            heading = QLabel(label)
            heading.setStyleSheet("font-size: 13px; font-weight: 600; background: transparent;")
            self._layout.addWidget(heading)

    def add_row(self, label_text: str, widget):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = QLabel(label_text)
        lbl.setFixedWidth(140)
        lbl.setStyleSheet("font-size: 13px; background: transparent;")
        row.addWidget(lbl)
        row.addWidget(widget, 1)
        self._layout.addLayout(row)

    def add_widget(self, widget):
        self._layout.addWidget(widget)


class SettingsDialog(QDialog):
    theme_changed = Signal()
    project_folder_changed = Signal(str)
    language_changed = Signal(str)
    settings_applied = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(580, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        t = theme.current()

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 12)
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        tabs = QTabWidget()

        # ── General tab ──
        general = QWidget()
        g_layout = QVBoxLayout(general)
        g_layout.setContentsMargins(20, 16, 20, 16)
        g_layout.setSpacing(16)

        identity_group = _FormGroup("Identity")
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Your name")
        self.author_input.setFixedHeight(34)
        identity_group.add_row("Author Name", self.author_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@example.com")
        self.email_input.setFixedHeight(34)
        identity_group.add_row("Author Email", self.email_input)
        g_layout.addWidget(identity_group)

        locale_group = _FormGroup("Locale")
        self.language_combo = QComboBox()
        self.language_combo.setFixedHeight(34)
        self.language_combo.setMinimumWidth(180)
        for code, display_name in available_languages():
            self.language_combo.addItem(display_name, code)
        current = get_language()
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current:
                self.language_combo.setCurrentIndex(i)
                break
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        locale_group.add_row("Language", self.language_combo)
        g_layout.addWidget(locale_group)

        storage_group = _FormGroup("Storage")
        folder_widget = QWidget()
        folder_layout = QHBoxLayout(folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(8)
        self.folder_label = QLabel()
        self.folder_label.setStyleSheet(
            f"font-family: ui-monospace, Menlo, monospace; font-size: 12px; "
            f"color: {t.neutral_500}; background: transparent;"
        )
        folder_layout.addWidget(self.folder_label, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondary")
        browse_btn.setFixedSize(80, 30)
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout.addWidget(browse_btn)
        storage_group.add_row("Project Folder", folder_widget)
        g_layout.addWidget(storage_group)

        g_layout.addStretch()
        tabs.addTab(general, "General")

        # ── Editor tab ──
        editor = QWidget()
        e_layout = QVBoxLayout(editor)
        e_layout.setContentsMargins(20, 16, 20, 16)
        e_layout.setSpacing(16)

        behavior_group = _FormGroup("Behavior")
        self.typewriter_check = QCheckBox("Typewriter scrolling")
        self.typewriter_check.setStyleSheet("background: transparent;")
        self.typewriter_check.setChecked(True)
        behavior_group.add_widget(self.typewriter_check)

        self.line_numbers_check = QCheckBox("Show line numbers")
        self.line_numbers_check.setStyleSheet("background: transparent;")
        behavior_group.add_widget(self.line_numbers_check)

        self.auto_save_check = QCheckBox("Auto-save every 60 seconds")
        self.auto_save_check.setStyleSheet("background: transparent;")
        self.auto_save_check.setChecked(True)
        behavior_group.add_widget(self.auto_save_check)
        e_layout.addWidget(behavior_group)

        typography_group = _FormGroup("Typography & Goals")
        self.font_size = QComboBox()
        self.font_size.setFixedHeight(34)
        self.font_size.setMinimumWidth(100)
        for s in ["12", "13", "14", "15", "16", "18"]:
            self.font_size.addItem(f"{s}pt", int(s))
        self.font_size.setCurrentText("15pt")
        typography_group.add_row("Script Font Size", self.font_size)

        self.word_target = QLineEdit("2500")
        self.word_target.setFixedHeight(34)
        self.word_target.setFixedWidth(100)
        typography_group.add_row("Daily Word Target", self.word_target)
        e_layout.addWidget(typography_group)

        e_layout.addStretch()
        tabs.addTab(editor, "Editor")

        # ── Theme tab ──
        theme_tab = QWidget()
        t_layout = QVBoxLayout(theme_tab)
        t_layout.setContentsMargins(20, 16, 20, 16)
        t_layout.setSpacing(16)

        appearance_group = _FormGroup("Appearance")
        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)
        self.dark_btn = QPushButton("Nocturne (Dark)")
        self.dark_btn.setObjectName("primary" if t.name == "nocturne" else "secondary")
        self.dark_btn.setFixedHeight(44)
        self.dark_btn.clicked.connect(lambda: self._set_theme("nocturne"))
        theme_row.addWidget(self.dark_btn)

        self.light_btn = QPushButton("Organic (Light)")
        self.light_btn.setObjectName("primary" if t.name == "organic" else "secondary")
        self.light_btn.setFixedHeight(44)
        self.light_btn.clicked.connect(lambda: self._set_theme("organic"))
        theme_row.addWidget(self.light_btn)
        appearance_group._layout.addLayout(theme_row)
        t_layout.addWidget(appearance_group)

        t_layout.addStretch()
        tabs.addTab(theme_tab, "Theme")

        # ── About tab ──
        about = QWidget()
        a_layout = QVBoxLayout(about)
        a_layout.setContentsMargins(20, 16, 20, 16)
        a_layout.setSpacing(8)

        about_group = _FormGroup("")
        app_name = QLabel("Écrit")
        app_name.setStyleSheet("font-size: 22px; font-weight: 500; background: transparent;")
        about_group.add_widget(app_name)

        ver = QLabel("v26.9.1 — Cross-platform Screenplay Editor")
        ver.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px; background: transparent;")
        about_group.add_widget(ver)

        desc = QLabel(
            "A cross-platform desktop screenplay editor for Fountain "
            "and Fountain-derived dialects. Built with Rust and PySide6."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 14px; background: transparent;")
        about_group.add_widget(desc)
        a_layout.addWidget(about_group)

        a_layout.addStretch()
        tabs.addTab(about, "About")

        # ── Modules tab ──
        modules_tab = QWidget()
        m_layout = QVBoxLayout(modules_tab)
        m_layout.setContentsMargins(20, 16, 20, 16)
        m_layout.setSpacing(12)

        modules_group = _FormGroup("Loaded Modules")
        self.modules_list = QListWidget()
        self.modules_list.setFixedHeight(140)
        self.modules_list.currentRowChanged.connect(self._on_module_selected)
        modules_group.add_widget(self.modules_list)

        mod_btn_row = QHBoxLayout()
        self.toggle_module_btn = QPushButton("Enable/Disable")
        self.toggle_module_btn.setObjectName("secondary")
        self.toggle_module_btn.setFixedHeight(34)
        self.toggle_module_btn.setEnabled(False)
        self.toggle_module_btn.clicked.connect(self._toggle_module)
        mod_btn_row.addWidget(self.toggle_module_btn)

        self.scan_dir_btn = QPushButton("Scan Directory")
        self.scan_dir_btn.setObjectName("secondary")
        self.scan_dir_btn.setFixedHeight(34)
        self.scan_dir_btn.clicked.connect(self._scan_modules_directory)
        mod_btn_row.addWidget(self.scan_dir_btn)
        mod_btn_row.addStretch()
        modules_group._layout.addLayout(mod_btn_row)
        m_layout.addWidget(modules_group)

        details_group = _FormGroup("Module Details")

        self.mod_detail_name = QLabel("—")
        self.mod_detail_name.setStyleSheet("font-weight: 500; font-size: 14px; background: transparent;")
        details_group.add_widget(self.mod_detail_name)

        self.mod_detail_version = QLabel("")
        self.mod_detail_version.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px; background: transparent;")
        details_group.add_widget(self.mod_detail_version)

        self.mod_detail_author = QLabel("")
        self.mod_detail_author.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px; background: transparent;")
        details_group.add_widget(self.mod_detail_author)

        self.mod_detail_desc = QLabel("")
        self.mod_detail_desc.setWordWrap(True)
        self.mod_detail_desc.setStyleSheet("font-size: 13px; background: transparent;")
        details_group.add_widget(self.mod_detail_desc)

        self.mod_detail_type = QLabel("")
        self.mod_detail_type.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px; background: transparent;")
        details_group.add_widget(self.mod_detail_type)

        self.mod_detail_path = QLabel("")
        self.mod_detail_path.setWordWrap(True)
        self.mod_detail_path.setStyleSheet(
            f"font-family: ui-monospace, Menlo, monospace; font-size: 11px; "
            f"color: {t.neutral_500}; background: transparent;"
        )
        details_group.add_widget(self.mod_detail_path)

        self.mod_detail_error = QLabel("")
        self.mod_detail_error.setWordWrap(True)
        self.mod_detail_error.setStyleSheet("color: #c0392b; font-size: 12px; background: transparent;")
        self.mod_detail_error.setVisible(False)
        details_group.add_widget(self.mod_detail_error)

        m_layout.addWidget(details_group)
        m_layout.addStretch()
        tabs.addTab(modules_tab, "Modules")

        self._module_registry = None

        layout.addWidget(tabs, 1)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")
        if folder:
            self.folder_label.setText(folder)
            self.project_folder_changed.emit(folder)

    def _set_theme(self, name: str):
        from ecrit.ui.styles.theme import NOCTURNE, ORGANIC, set_theme
        if name == "nocturne":
            set_theme(NOCTURNE)
        else:
            set_theme(ORGANIC)
        self.theme_changed.emit()

    def set_registry(self, registry):
        from ecrit.screenplay.module_system import ModuleRegistry
        self._module_registry = registry
        self._refresh_modules_list()

    def _refresh_modules_list(self):
        self.modules_list.clear()
        self._clear_module_details()
        self.toggle_module_btn.setEnabled(False)
        if not self._module_registry:
            return
        for mod in self._module_registry.list_modules():
            status = "Enabled" if mod.enabled else "Disabled"
            text = f"{mod.manifest.name}  v{mod.manifest.version}  [{mod.manifest.module_type}]  ({status})"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, mod.manifest.name)
            self.modules_list.addItem(item)

    def _on_module_selected(self, row):
        if row < 0 or not self._module_registry:
            self.toggle_module_btn.setEnabled(False)
            self._clear_module_details()
            return
        item = self.modules_list.item(row)
        if not item:
            return
        name = item.data(Qt.UserRole)
        mod = self._module_registry.get_module(name)
        if not mod:
            return
        self.toggle_module_btn.setEnabled(True)
        self.toggle_module_btn.setText("Disable" if mod.enabled else "Enable")
        self.mod_detail_name.setText(mod.manifest.name)
        self.mod_detail_version.setText(f"Version: {mod.manifest.version}")
        self.mod_detail_author.setText(f"Author: {mod.manifest.author}" if mod.manifest.author else "")
        self.mod_detail_desc.setText(mod.manifest.description if mod.manifest.description else "No description.")
        self.mod_detail_type.setText(f"Type: {mod.manifest.module_type}")
        self.mod_detail_path.setText(f"Path: {mod.path}")
        if mod.error:
            self.mod_detail_error.setText(f"Error: {mod.error}")
            self.mod_detail_error.setVisible(True)
        else:
            self.mod_detail_error.setVisible(False)

    def _clear_module_details(self):
        self.mod_detail_name.setText("—")
        self.mod_detail_version.setText("")
        self.mod_detail_author.setText("")
        self.mod_detail_desc.setText("")
        self.mod_detail_type.setText("")
        self.mod_detail_path.setText("")
        self.mod_detail_error.setVisible(False)

    def _toggle_module(self):
        if not self._module_registry:
            return
        item = self.modules_list.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        mod = self._module_registry.get_module(name)
        if not mod:
            return
        if mod.enabled:
            self._module_registry.disable_module(name)
        else:
            self._module_registry.enable_module(name)
        current_row = self.modules_list.currentRow()
        self._refresh_modules_list()
        if current_row < self.modules_list.count():
            self.modules_list.setCurrentRow(current_row)

    def _scan_modules_directory(self):
        if not self._module_registry:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Modules Directory")
        if folder:
            self._module_registry.scan_directory(folder)
            self._module_registry.load_all(folder)
            self._refresh_modules_list()

    def _on_language_changed(self, index: int):
        lang_code = self.language_combo.itemData(index)
        if lang_code:
            set_language(lang_code)
            from ecrit.stores.app_state import STATE
            STATE.language = lang_code
            self.language_changed.emit(lang_code)

    def load_state(self):
        from ecrit.stores.app_state import STATE
        self.author_input.setText(STATE.author_name)
        self.email_input.setText(STATE.author_email)
        self.folder_label.setText(STATE.project_folder)
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == STATE.language:
                self.language_combo.setCurrentIndex(i)
                break

    def closeEvent(self, event):
        try:
            word_target = int(self.word_target.text())
        except (ValueError, TypeError):
            word_target = 2500
        self.settings_applied.emit({
            "author_name": self.author_input.text(),
            "author_email": self.email_input.text(),
            "font_size": self.font_size.currentData() or 15,
            "word_target": word_target,
            "typewriter": self.typewriter_check.isChecked(),
            "line_numbers": self.line_numbers_check.isChecked(),
            "auto_save": self.auto_save_check.isChecked(),
        })
        super().closeEvent(event)
