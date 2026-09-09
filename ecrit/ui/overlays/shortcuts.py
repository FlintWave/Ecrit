"""Keyboard shortcuts reference panel."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QWidget
)
from PySide6.QtCore import Qt

from ecrit.ui.styles import theme

SHORTCUT_GROUPS = [
    ("File", [
        ("Ctrl+N", "New project"),
        ("Ctrl+O", "Open project"),
        ("Ctrl+S", "Save"),
        ("Ctrl+Shift+S", "Save as"),
    ]),
    ("Edit", [
        ("Ctrl+Z", "Undo"),
        ("Ctrl+Shift+Z", "Redo"),
        ("Ctrl+X", "Cut"),
        ("Ctrl+C", "Copy"),
        ("Ctrl+V", "Paste"),
        ("Ctrl+A", "Select all"),
    ]),
    ("Navigation", [
        ("Ctrl+F", "Find & Replace"),
        ("Ctrl+G", "Go to page"),
        ("Ctrl+K", "Command palette"),
        ("Ctrl+1-5", "Switch phase"),
    ]),
    ("Editor", [
        ("Tab", "Cycle element type"),
        ("Enter", "Smart line break"),
        ("Ctrl+B", "Bold (notes)"),
        ("Ctrl+I", "Italic (notes)"),
    ]),
    ("View", [
        ("Ctrl+=", "Zoom in"),
        ("Ctrl+-", "Zoom out"),
        ("Ctrl+0", "Reset zoom"),
        ("F11", "Full screen"),
        ("Ctrl+Shift+T", "Toggle theme"),
    ]),
]


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(480, 520)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        for group_name, shortcuts in SHORTCUT_GROUPS:
            group_label = QLabel(group_name)
            group_label.setObjectName("kicker")
            content_layout.addWidget(group_label)

            grid = QGridLayout()
            grid.setSpacing(6)
            for i, (key, desc) in enumerate(shortcuts):
                key_label = QLabel(key)
                key_label.setStyleSheet(
                    f"font-family: ui-monospace, Menlo, monospace; font-size: 12px; "
                    f"background: {t.neutral_800 if t.name == 'nocturne' else t.neutral_200}; "
                    f"padding: 3px 8px; border-radius: 4px;"
                )
                key_label.setFixedWidth(140)
                grid.addWidget(key_label, i, 0)

                desc_label = QLabel(desc)
                desc_label.setStyleSheet("font-size: 13px;")
                grid.addWidget(desc_label, i, 1)
            content_layout.addLayout(grid)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
