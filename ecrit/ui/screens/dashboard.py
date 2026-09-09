"""Dashboard — landing screen: continue writing, projects grid, quick start."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from datetime import datetime

from ecrit.ui.styles import theme


class ContinueWritingCard(QFrame):
    open_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        top = QHBoxLayout()
        kicker = QLabel("CONTINUE WRITING")
        kicker.setObjectName("kicker")
        top.addWidget(kicker)
        top.addStretch()
        self.sync_label = QLabel()
        self.sync_label.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 12px; background: transparent;")
        top.addWidget(self.sync_label)
        layout.addLayout(top)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 26px; font-weight: 500; background: transparent;")
        layout.addWidget(self.title_label)

        self.meta_label = QLabel()
        self.meta_label.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 13px; background: transparent;")
        layout.addWidget(self.meta_label)

        self.excerpt = QLabel()
        self.excerpt.setWordWrap(True)
        self.excerpt.setStyleSheet(
            f"font-family: 'Courier Prime', monospace; font-size: 13px; "
            f"color: {theme.current().neutral_400}; background: transparent; padding: 12px 0;"
        )
        layout.addWidget(self.excerpt)

        bottom = QHBoxLayout()
        self.position_label = QLabel()
        self.position_label.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 13px; background: transparent;")
        bottom.addWidget(self.position_label)
        bottom.addStretch()
        open_btn = QPushButton("Open")
        open_btn.setObjectName("primary")
        open_btn.clicked.connect(self.open_clicked.emit)
        bottom.addWidget(open_btn)
        layout.addLayout(bottom)

    def set_project(self, title, format_id="", meta_text="", excerpt_text="", position=""):
        self.title_label.setText(title)
        self.meta_label.setText(meta_text)
        self.excerpt.setText(excerpt_text)
        self.position_label.setText(position)


class WeekStatsCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)

        kicker = QLabel("THIS WEEK")
        kicker.setObjectName("kicker")
        layout.addWidget(kicker)

        self.stats = {}
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, (key, label) in enumerate([
            ("words", "Words written"),
            ("sessions", "Sessions"),
            ("pages", "Pages"),
            ("streak", "Streak"),
        ]):
            val = QLabel("0")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            val.setStyleSheet("font-family: ui-monospace, Menlo, monospace; font-size: 20px; background: transparent;")
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 12px; background: transparent;")
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            self.stats[key] = val
        layout.addLayout(grid)

    def set_stats(self, words=0, sessions=0, pages=0, streak="0 days"):
        self.stats["words"].setText(f"{words:,}")
        self.stats["sessions"].setText(str(sessions))
        self.stats["pages"].setText(str(pages))
        self.stats["streak"].setText(str(streak))


class ProjectCard(QFrame):
    clicked = Signal(str)

    def __init__(self, project_data: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._path = project_data.get("path", "")

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        t = theme.current()

        top = QHBoxLayout()
        fmt = project_data.get("format_id", "")
        category = _format_category(fmt)
        if category:
            tag = QLabel(category)
            tag.setObjectName("tagNeutral")
            top.addWidget(tag)
        fmt_label = QLabel(fmt)
        fmt_label.setStyleSheet(f"font-family: ui-monospace, Menlo, monospace; font-size: 11px; color: {t.neutral_500}; background: transparent;")
        top.addWidget(fmt_label)
        top.addStretch()
        layout.addLayout(top)

        title = QLabel(project_data.get("title", "Untitled"))
        title.setStyleSheet("font-size: 15px; font-weight: 500; background: transparent;")
        layout.addWidget(title)

        modified = project_data.get("modified_at", "")
        if modified:
            mod_label = QLabel(f"edited {_relative_time(modified)}")
            mod_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 12.5px; background: transparent;")
            layout.addWidget(mod_label)

    def mousePressEvent(self, _event):
        self.clicked.emit(self._path)


class Dashboard(QWidget):
    open_project = Signal(str)
    new_project = Signal()
    import_script = Signal()
    open_settings = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        t = theme.current()
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(44, 44, 44, 44)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        inner = QWidget()
        inner.setMaximumWidth(1060)
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(24)

        now = datetime.now()
        hour = now.hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        date_str = now.strftime("%A, %d %B")

        header = QHBoxLayout()
        greeting_label = QLabel(f"{greeting}.")
        greeting_label.setStyleSheet("font-size: 28px; font-weight: 500;")
        header.addWidget(greeting_label)
        date_label = QLabel(date_str)
        date_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 14px; padding-top: 8px;")
        header.addWidget(date_label)
        header.addStretch()
        inner_layout.addLayout(header)

        hero = QHBoxLayout()
        hero.setSpacing(22)

        self.continue_card = ContinueWritingCard()
        self.continue_card.open_clicked.connect(self._on_open_recent)
        self.continue_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        hero.addWidget(self.continue_card, 3)

        right_stack = QVBoxLayout()
        right_stack.setSpacing(12)

        new_btn = QPushButton("+ New project")
        new_btn.setObjectName("primary")
        new_btn.setFixedHeight(44)
        new_btn.clicked.connect(self.new_project.emit)
        right_stack.addWidget(new_btn)

        import_btn = QPushButton("↓ Import script")
        import_btn.setObjectName("secondary")
        import_btn.setFixedHeight(44)
        import_btn.clicked.connect(self.import_script.emit)
        right_stack.addWidget(import_btn)

        self.week_stats = WeekStatsCard()
        right_stack.addWidget(self.week_stats)
        right_stack.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_stack)
        hero.addWidget(right_widget, 2)
        inner_layout.addLayout(hero)

        projects_header = QHBoxLayout()
        projects_title = QLabel("Projects")
        projects_title.setStyleSheet("font-size: 16px; font-weight: 500;")
        projects_header.addWidget(projects_title)
        self.count_label = QLabel("0 open")
        self.count_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px;")
        projects_header.addWidget(self.count_label)
        projects_header.addStretch()
        inner_layout.addLayout(projects_header)

        self.projects_grid = QGridLayout()
        self.projects_grid.setSpacing(16)
        inner_layout.addLayout(self.projects_grid)

        inner_layout.addStretch()

        layout.addWidget(inner)
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _on_open_recent(self):
        from ecrit.stores.app_state import STATE
        if STATE.projects:
            self.open_project.emit(STATE.projects[0].get("path", ""))

    def refresh(self):
        from ecrit.stores.app_state import STATE
        t = theme.current()

        STATE.load_projects()
        projects = STATE.projects

        self.count_label.setText(f"{len(projects)} open")

        if projects:
            p = projects[0]
            self.continue_card.set_project(
                title=p.get("title", "Untitled"),
                format_id=p.get("format_id", ""),
                meta_text=f"{_format_category(p.get('format_id', ''))} · {p.get('format_id', '')}",
                position=f"edited {_relative_time(p.get('modified_at', ''))}",
            )
        else:
            self.continue_card.set_project("No projects yet", meta_text="Create a new project to get started")

        while self.projects_grid.count():
            item = self.projects_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, proj in enumerate(projects[1:], 0):
            card = ProjectCard(proj)
            card.clicked.connect(self.open_project.emit)
            self.projects_grid.addWidget(card, i // 3, i % 3)


def _format_category(format_id: str) -> str:
    cats = {
        "fountain/core": "Feature Film",
        "fountain+shooting": "Feature Film",
        "fountain+studio47": "Feature Film",
        "fountain+a4": "Feature Film",
        "fountain+multicam": "Television",
        "fountain+bbc-screen": "Television",
        "fountain+bbc-scene": "Television",
        "fountain+radio-scene": "Audio",
        "fountain+radio-cue": "Audio",
        "fountain+audio-us": "Audio",
        "fountain+comic-full": "Comics",
        "fountain+comic-plot": "Comics",
        "fountain+comic-lean": "Comics",
        "fountain+comic-gn": "Comics",
        "fountain+stage-us": "Stage",
        "fountain+stage-uk": "Stage",
        "fountain+branch": "Interactive",
        "fountain+barks": "Interactive",
    }
    return cats.get(format_id, "")


def _relative_time(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        mins = diff.seconds // 60
        return f"{mins}m ago"
    except Exception:
        return ""
