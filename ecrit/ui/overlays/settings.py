"""Settings dialog — General, Editor, Theme, About tabs."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QTabWidget, QWidget,
    QFrame, QFileDialog
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

    def load_state(self):
        from ecrit.stores.app_state import STATE
        self.author_input.setText(STATE.author_name)
        self.email_input.setText(STATE.author_email)
        self.folder_label.setText(STATE.project_folder)
