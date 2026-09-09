"""Settings dialog — General, Editor, Theme, About, Modules tabs."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QTabWidget, QWidget,
    QFrame, QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


class SettingsDialog(QDialog):
    theme_changed = Signal()
    project_folder_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(560, 440)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        t = theme.current()

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
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

        # General tab
        general = QWidget()
        g_layout = QVBoxLayout(general)
        g_layout.setContentsMargins(20, 16, 20, 16)
        g_layout.setSpacing(16)

        g_layout.addWidget(QLabel("Author Name"))
        self.author_input = QLineEdit()
        self.author_input.setFixedHeight(34)
        g_layout.addWidget(self.author_input)

        g_layout.addWidget(QLabel("Author Email"))
        self.email_input = QLineEdit()
        self.email_input.setFixedHeight(34)
        g_layout.addWidget(self.email_input)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Project Folder"))
        folder_row.addStretch()
        self.folder_label = QLabel()
        self.folder_label.setStyleSheet(
            f"font-family: ui-monospace, Menlo, monospace; font-size: 12px; "
            f"color: {t.neutral_500};"
        )
        folder_row.addWidget(self.folder_label)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondary")
        browse_btn.setFixedHeight(28)
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)
        g_layout.addLayout(folder_row)

        g_layout.addStretch()
        tabs.addTab(general, "General")

        # Editor tab
        editor = QWidget()
        e_layout = QVBoxLayout(editor)
        e_layout.setContentsMargins(20, 16, 20, 16)
        e_layout.setSpacing(12)

        self.typewriter_check = QCheckBox("Typewriter scrolling")
        self.typewriter_check.setChecked(True)
        e_layout.addWidget(self.typewriter_check)

        self.line_numbers_check = QCheckBox("Show line numbers")
        e_layout.addWidget(self.line_numbers_check)

        self.auto_save_check = QCheckBox("Auto-save every 60 seconds")
        self.auto_save_check.setChecked(True)
        e_layout.addWidget(self.auto_save_check)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Script font size"))
        self.font_size = QComboBox()
        for s in ["12", "13", "14", "15", "16", "18"]:
            self.font_size.addItem(f"{s}pt", int(s))
        self.font_size.setCurrentText("15pt")
        font_row.addWidget(self.font_size)
        font_row.addStretch()
        e_layout.addLayout(font_row)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Daily word target"))
        self.word_target = QLineEdit("2500")
        self.word_target.setFixedWidth(80)
        self.word_target.setFixedHeight(30)
        target_row.addWidget(self.word_target)
        target_row.addStretch()
        e_layout.addLayout(target_row)

        e_layout.addStretch()
        tabs.addTab(editor, "Editor")

        # Theme tab
        theme_tab = QWidget()
        t_layout = QVBoxLayout(theme_tab)
        t_layout.setContentsMargins(20, 16, 20, 16)
        t_layout.setSpacing(16)

        t_layout.addWidget(QLabel("Appearance"))

        theme_row = QHBoxLayout()
        self.dark_btn = QPushButton("Nocturne (Dark)")
        self.dark_btn.setObjectName("primary" if t.name == "nocturne" else "secondary")
        self.dark_btn.setFixedHeight(40)
        self.dark_btn.clicked.connect(lambda: self._set_theme("nocturne"))
        theme_row.addWidget(self.dark_btn)

        self.light_btn = QPushButton("Organic (Light)")
        self.light_btn.setObjectName("primary" if t.name == "organic" else "secondary")
        self.light_btn.setFixedHeight(40)
        self.light_btn.clicked.connect(lambda: self._set_theme("organic"))
        theme_row.addWidget(self.light_btn)
        t_layout.addLayout(theme_row)

        t_layout.addStretch()
        tabs.addTab(theme_tab, "Theme")

        # About tab
        about = QWidget()
        a_layout = QVBoxLayout(about)
        a_layout.setContentsMargins(20, 16, 20, 16)
        a_layout.setSpacing(8)

        a_layout.addWidget(QLabel("Écrit"))
        ver = QLabel("v0.1.0 — Foundation")
        ver.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px;")
        a_layout.addWidget(ver)

        a_layout.addSpacing(12)
        desc = QLabel(
            "A cross-platform desktop screenplay editor for Fountain "
            "and Fountain-derived dialects. Built with Rust and PySide6."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 14px;")
        a_layout.addWidget(desc)

        a_layout.addStretch()
        tabs.addTab(about, "About")

        # Modules tab
        modules_tab = QWidget()
        m_layout = QVBoxLayout(modules_tab)
        m_layout.setContentsMargins(20, 16, 20, 16)
        m_layout.setSpacing(12)

        m_layout.addWidget(QLabel("Loaded Modules"))

        self.modules_list = QListWidget()
        self.modules_list.setFixedHeight(140)
        self.modules_list.currentRowChanged.connect(self._on_module_selected)
        m_layout.addWidget(self.modules_list)

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
        m_layout.addLayout(mod_btn_row)

        details_label = QLabel("Module Details")
        details_label.setStyleSheet("font-weight: 500; margin-top: 4px;")
        m_layout.addWidget(details_label)

        details_frame = QFrame()
        details_frame.setStyleSheet(
            f"QFrame {{ background: {t.neutral_100}; border-radius: 6px; "
            f"padding: 10px; }}"
        )
        d_layout = QVBoxLayout(details_frame)
        d_layout.setContentsMargins(10, 8, 10, 8)
        d_layout.setSpacing(4)

        self.mod_detail_name = QLabel("—")
        self.mod_detail_name.setStyleSheet("font-weight: 500; font-size: 14px;")
        d_layout.addWidget(self.mod_detail_name)

        self.mod_detail_version = QLabel("")
        self.mod_detail_version.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        d_layout.addWidget(self.mod_detail_version)

        self.mod_detail_author = QLabel("")
        self.mod_detail_author.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        d_layout.addWidget(self.mod_detail_author)

        self.mod_detail_desc = QLabel("")
        self.mod_detail_desc.setWordWrap(True)
        self.mod_detail_desc.setStyleSheet("font-size: 13px;")
        d_layout.addWidget(self.mod_detail_desc)

        self.mod_detail_type = QLabel("")
        self.mod_detail_type.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        d_layout.addWidget(self.mod_detail_type)

        self.mod_detail_path = QLabel("")
        self.mod_detail_path.setWordWrap(True)
        self.mod_detail_path.setStyleSheet(
            f"font-family: ui-monospace, Menlo, monospace; font-size: 11px; "
            f"color: {t.neutral_500};"
        )
        d_layout.addWidget(self.mod_detail_path)

        self.mod_detail_error = QLabel("")
        self.mod_detail_error.setWordWrap(True)
        self.mod_detail_error.setStyleSheet("color: #c0392b; font-size: 12px;")
        self.mod_detail_error.setVisible(False)
        d_layout.addWidget(self.mod_detail_error)

        m_layout.addWidget(details_frame)
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
        """Connect a ModuleRegistry instance to the Modules tab."""
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

    def load_state(self):
        from ecrit.stores.app_state import STATE
        self.author_input.setText(STATE.author_name)
        self.email_input.setText(STATE.author_email)
        self.folder_label.setText(STATE.project_folder)
