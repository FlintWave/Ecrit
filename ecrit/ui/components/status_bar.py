"""Status bar for the editor — page, slugline, daily words, sprint, toolbar."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal


class StatusBar(QWidget):
    find_clicked = Signal()
    stats_clicked = Signal()
    shortcuts_clicked = Signal()
    theme_clicked = Signal()
    reading_mode_clicked = Signal()
    sprint_clicked = Signal()
    home_clicked = Signal()
    typewriter_toggled = Signal(bool)
    focus_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusBar")
        self.setFixedHeight(28)
        self._typewriter_on = True
        self._focus_on = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(12)

        self.page_label = QLabel("Page 1 of 1")
        layout.addWidget(self.page_label)

        self.scene_label = QLabel()
        self.scene_label.setStyleSheet("font-family: 'Courier Prime', monospace;")
        layout.addWidget(self.scene_label)

        layout.addStretch()

        self.words_label = QLabel("0 / 2,500 today")
        layout.addWidget(self.words_label)

        self.sprint_label = QLabel()
        layout.addWidget(self.sprint_label)

        self.mode_label = QPushButton("typewriter")
        self.mode_label.setObjectName("iconBtn")
        self.mode_label.setFixedHeight(22)
        self.mode_label.setToolTip("Toggle typewriter scrolling")
        self.mode_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_label.clicked.connect(self._toggle_typewriter)
        layout.addWidget(self.mode_label)

        self.focus_label = QPushButton("focus")
        self.focus_label.setObjectName("iconBtn")
        self.focus_label.setFixedHeight(22)
        self.focus_label.setToolTip("Toggle focus mode (dim inactive paragraphs)")
        self.focus_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.focus_label.clicked.connect(self._toggle_focus)
        layout.addWidget(self.focus_label)

        sep = QLabel("|")
        sep.setFixedWidth(8)
        layout.addWidget(sep)

        buttons = [
            ("Find", self.find_clicked),
            ("Stats", self.stats_clicked),
            ("KB", self.shortcuts_clicked),
            ("Theme", self.theme_clicked),
            ("Read", self.reading_mode_clicked),
            ("Sprint", self.sprint_clicked),
        ]
        for label, signal in buttons:
            btn = QPushButton(label)
            btn.setObjectName("iconBtn")
            btn.setFixedSize(QLabel(label).sizeHint().width() + 12, 22)
            btn.setToolTip(label)
            btn.clicked.connect(signal.emit)
            layout.addWidget(btn)

        sep2 = QLabel("|")
        sep2.setFixedWidth(8)
        layout.addWidget(sep2)

        self.dialect_label = QLabel("fountain/core")
        self.dialect_label.setStyleSheet("font-family: ui-monospace, Menlo, monospace; font-size: 11px;")
        layout.addWidget(self.dialect_label)

        self.home_btn = QPushButton("⌂")
        self.home_btn.setObjectName("homeBtn")
        self.home_btn.setFixedSize(34, 22)
        self.home_btn.setToolTip("Dashboard")
        self.home_btn.clicked.connect(self.home_clicked.emit)
        layout.addWidget(self.home_btn)

    def _toggle_typewriter(self):
        self._typewriter_on = not self._typewriter_on
        self.mode_label.setText("typewriter" if self._typewriter_on else "standard")
        self.typewriter_toggled.emit(self._typewriter_on)

    def _toggle_focus(self):
        self._focus_on = not self._focus_on
        self.focus_label.setText("focus" if not self._focus_on else "focus*")
        self.focus_toggled.emit(self._focus_on)

    def update_info(self, page=1, total_pages=1, scene="", words_today=0, target=2500, dialect="fountain/core"):
        self.page_label.setText(f"Page {page} of {total_pages}")
        self.scene_label.setText(scene)
        self.words_label.setText(f"{words_today:,} / {target:,} today")
        self.dialect_label.setText(dialect)
