"""New Project wizard — title, author, format selection, paper size."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme

try:
    import ecrit_core
    import json
    _DIALECTS = json.loads(ecrit_core.get_dialects())
    _CATEGORIES = json.loads(ecrit_core.get_format_categories())
except Exception:
    _DIALECTS = []
    _CATEGORIES = {}

CATEGORIES_ORDER = [
    ("Feature Film", ["fountain/core", "fountain+shooting", "fountain+studio47", "fountain+a4"]),
    ("Television", ["fountain+multicam", "fountain+bbc-screen", "fountain+bbc-scene"]),
    ("Audio & Radio", ["fountain+radio-scene", "fountain+radio-cue", "fountain+audio-us"]),
    ("Comics", ["fountain+comic-full", "fountain+comic-plot", "fountain+comic-lean", "fountain+comic-gn"]),
    ("Stage", ["fountain+stage-us", "fountain+stage-uk"]),
    ("Interactive", ["fountain+branch", "fountain+barks"]),
]

FORMAT_LABELS = {
    "fountain/core": "Fountain Core",
    "fountain+shooting": "Shooting Script",
    "fountain+studio47": "Studio 47",
    "fountain+a4": "Fountain A4",
    "fountain+multicam": "Multi-Camera",
    "fountain+bbc-screen": "BBC Screen",
    "fountain+bbc-scene": "BBC Scene",
    "fountain+radio-scene": "Radio Scene",
    "fountain+radio-cue": "Radio Cue",
    "fountain+audio-us": "Audio US",
    "fountain+comic-full": "Comic Full",
    "fountain+comic-plot": "Comic Plot",
    "fountain+comic-lean": "Comic Lean",
    "fountain+comic-gn": "Graphic Novel",
    "fountain+stage-us": "Stage US",
    "fountain+stage-uk": "Stage UK",
    "fountain+branch": "Branch",
    "fountain+barks": "Barks",
}


class FormatCard(QFrame):
    clicked = Signal(str)

    def __init__(self, format_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._format_id = format_id
        self._selected = False

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        t = theme.current()

        label = FORMAT_LABELS.get(format_id, format_id)
        name = QLabel(label)
        name.setStyleSheet("font-size: 14px; font-weight: 500; background: transparent;")
        layout.addWidget(name)

        fid = QLabel(format_id)
        fid.setStyleSheet(
            f"font-family: ui-monospace, Menlo, monospace; font-size: 11px; "
            f"color: {t.neutral_500}; background: transparent;"
        )
        layout.addWidget(fid)

    def set_selected(self, selected: bool):
        self._selected = selected
        t = theme.current()
        if selected:
            self.setStyleSheet(
                f"QFrame#card {{ border-color: {t.accent}; background: {t.accent_900 if t.name == 'nocturne' else t.accent_100}; }}"
            )
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, _event):
        self.clicked.emit(self._format_id)


class NewProjectWizard(QWidget):
    project_created = Signal(str)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_format = "fountain/core"
        self._selected_paper = "USLetter"
        self._format_cards = {}
        self._paper_buttons = {}
        self._build_ui()

    def _build_ui(self):
        t = theme.current()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(44, 32, 44, 44)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        inner = QWidget()
        inner.setMaximumWidth(780)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(24)

        title = QLabel("New Project")
        title.setStyleSheet("font-size: 26px; font-weight: 500;")
        inner_layout.addWidget(title)

        subtitle = QLabel("Set up your screenplay, then start writing.")
        subtitle.setStyleSheet(f"color: {t.neutral_500}; font-size: 14px;")
        inner_layout.addWidget(subtitle)

        inner_layout.addSpacing(8)

        title_label = QLabel("Title")
        title_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        inner_layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. The Great Screenplay")
        self.title_input.setFixedHeight(38)
        inner_layout.addWidget(self.title_input)

        author_label = QLabel("Author")
        author_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        inner_layout.addWidget(author_label)

        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Your name")
        self.author_input.setFixedHeight(38)
        inner_layout.addWidget(self.author_input)

        inner_layout.addSpacing(12)

        format_label = QLabel("Format")
        format_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        inner_layout.addWidget(format_label)

        for cat_name, format_ids in CATEGORIES_ORDER:
            cat_label = QLabel(cat_name)
            cat_label.setObjectName("kicker")
            inner_layout.addWidget(cat_label)

            grid = QGridLayout()
            grid.setSpacing(10)
            for i, fid in enumerate(format_ids):
                card = FormatCard(fid)
                card.clicked.connect(self._on_format_selected)
                grid.addWidget(card, i // 3, i % 3)
                self._format_cards[fid] = card
            inner_layout.addLayout(grid)

        self._format_cards.get("fountain/core", FormatCard("")).set_selected(True)

        inner_layout.addSpacing(12)

        paper_label = QLabel("Paper Size")
        paper_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        inner_layout.addWidget(paper_label)

        paper_row = QHBoxLayout()
        for pid, plabel in [("USLetter", "US Letter"), ("A4", "A4")]:
            btn = QPushButton(plabel)
            btn.setObjectName("primary" if pid == self._selected_paper else "secondary")
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda checked=False, p=pid: self._on_paper_selected(p))
            paper_row.addWidget(btn)
            self._paper_buttons[pid] = btn
        paper_row.addStretch()
        inner_layout.addLayout(paper_row)

        inner_layout.addSpacing(24)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.cancelled.emit)
        buttons.addWidget(cancel_btn)

        self.create_btn = QPushButton("Create Project")
        self.create_btn.setObjectName("primary")
        self.create_btn.setFixedHeight(40)
        self.create_btn.clicked.connect(self._on_create)
        buttons.addWidget(self.create_btn)

        inner_layout.addLayout(buttons)
        inner_layout.addStretch()

        layout.addWidget(inner)
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _on_format_selected(self, format_id: str):
        self._selected_format = format_id
        for fid, card in self._format_cards.items():
            card.set_selected(fid == format_id)

    def _on_paper_selected(self, paper: str):
        self._selected_paper = paper
        for pid, btn in self._paper_buttons.items():
            btn.setObjectName("primary" if pid == paper else "secondary")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_create(self):
        title = self.title_input.text().strip() or "Untitled"
        author = self.author_input.text().strip()

        from ecrit.stores.app_state import STATE
        meta = STATE.create_project(
            title=title,
            author=author,
            format_id=self._selected_format,
            paper=self._selected_paper,
        )
        if meta:
            self.project_created.emit(meta.get("path", ""))

    def reset(self):
        self.title_input.clear()
        self.author_input.clear()
        self._on_format_selected("fountain/core")
        self._on_paper_selected("USLetter")
