"""Command palette (Ctrl+K) — fuzzy search for actions, files, navigation."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QShortcut, QKeySequence

from ecrit.ui.styles import theme


COMMANDS = [
    ("New Project", "file", "Create a new project"),
    ("Open Project", "file", "Open an existing project"),
    ("Import Script", "file", "Import a .fountain file"),
    ("Save", "file", "Save current script"),
    ("Dashboard", "nav", "Go to Dashboard"),
    ("Plan", "phase", "Switch to Plan phase"),
    ("Outline", "phase", "Switch to Outline phase"),
    ("Manuscript", "phase", "Switch to Manuscript phase"),
    ("Proofread", "phase", "Switch to Proofread phase"),
    ("Deliver", "phase", "Switch to Deliver phase"),
    ("Find & Replace", "tool", "Open Find & Replace"),
    ("Statistics", "tool", "Show script statistics"),
    ("Keyboard Shortcuts", "tool", "Show keyboard shortcuts"),
    ("Settings", "tool", "Open settings"),
    ("Toggle Theme", "tool", "Switch between Nocturne and Organic"),
    ("Reading Mode", "tool", "Enter distraction-free reading mode"),
    ("Sprint Timer", "tool", "Start a writing sprint"),
    ("Scratchpad", "tool", "Open scratchpad for cut text"),
    ("Snapshot", "tool", "Create a git snapshot"),
    ("Compare Drafts", "tool", "Compare two script snapshots"),
    ("Export PDF", "export", "Export script as PDF"),
    ("Export ODT", "export", "Export script as ODT"),
    ("Export Fountain", "export", "Export as .fountain file"),
    ("Production Reports", "tool", "Generate scene, cast, location reports"),
    ("Logline Builder", "tool", "Build a logline from templates"),
]


class CommandPalette(QDialog):
    command_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setFixedSize(520, 400)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

        t = theme.current()
        self.setStyleSheet(
            f"background: {t.surface}; border: 1px solid {t.neutral_700}; "
            f"border-radius: {t.radius_lg}px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command...")
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self._filter)
        layout.addWidget(self.search_input)

        self.results = QListWidget()
        self.results.itemActivated.connect(self._on_select)
        layout.addWidget(self.results, 1)

        hint = QLabel("↑↓ navigate  ⏎ select  Esc close")
        hint.setStyleSheet(f"color: {t.neutral_500}; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self._populate(COMMANDS)

    def _populate(self, commands):
        self.results.clear()
        t = theme.current()
        for name, category, desc in commands:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, name)
            cat_prefix = {"file": "📄", "nav": "🏠", "phase": "📑", "tool": "🔧", "export": "📦"}.get(category, "")
            item.setText(f"{cat_prefix}  {name}  —  {desc}")
            self.results.addItem(item)
        if self.results.count() > 0:
            self.results.setCurrentRow(0)

    def _filter(self, text):
        query = text.lower().strip()
        if not query:
            self._populate(COMMANDS)
            return
        filtered = [
            (name, cat, desc) for name, cat, desc in COMMANDS
            if query in name.lower() or query in desc.lower() or query in cat.lower()
        ]
        self._populate(filtered)

    def _on_select(self, item):
        name = item.data(Qt.ItemDataRole.UserRole)
        self.command_selected.emit(name)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current = self.results.currentItem()
            if current:
                self._on_select(current)
        elif event.key() == Qt.Key.Key_Down:
            row = self.results.currentRow()
            if row < self.results.count() - 1:
                self.results.setCurrentRow(row + 1)
        elif event.key() == Qt.Key.Key_Up:
            row = self.results.currentRow()
            if row > 0:
                self.results.setCurrentRow(row - 1)
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.search_input.clear()
        self.search_input.setFocus()
        self._populate(COMMANDS)
