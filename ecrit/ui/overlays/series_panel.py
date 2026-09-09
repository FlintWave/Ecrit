"""Series project panel — episode switcher, season management, series bible."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QFrame, QScrollArea, QWidget, QTextEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme
from ecrit.screenplay.series_projects import (
    SeriesProject, SeriesSeason, Episode, BibleEntry, SeriesBible,
)


class SeriesPanel(QDialog):
    """Episode switcher and series management dialog."""

    episode_selected = Signal(int, int)  # season_number, episode_number
    project_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Series Manager")
        self.setMinimumSize(680, 520)
        self.setModal(True)

        self._project: SeriesProject | None = None

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel("Series Manager")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_episodes_tab()
        self._build_bible_tab()
        self._build_info_tab()

        footer = QHBoxLayout()
        footer.setContentsMargins(24, 8, 24, 16)
        footer.addStretch()
        close_btn2 = QPushButton("Close")
        close_btn2.setObjectName("secondary")
        close_btn2.setFixedHeight(36)
        close_btn2.clicked.connect(self.close)
        footer.addWidget(close_btn2)
        layout.addLayout(footer)

    def _build_episodes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 16, 24, 12)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        season_label = QLabel("Season:")
        season_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        top_row.addWidget(season_label)

        self.season_combo = QComboBox()
        self.season_combo.setFixedHeight(32)
        self.season_combo.setMinimumWidth(160)
        self.season_combo.currentIndexChanged.connect(self._on_season_changed)
        top_row.addWidget(self.season_combo)

        add_season_btn = QPushButton("+ Season")
        add_season_btn.setObjectName("secondary")
        add_season_btn.setFixedHeight(32)
        add_season_btn.clicked.connect(self._add_season)
        top_row.addWidget(add_season_btn)

        top_row.addStretch()

        add_ep_btn = QPushButton("+ Episode")
        add_ep_btn.setObjectName("primary")
        add_ep_btn.setFixedHeight(32)
        add_ep_btn.clicked.connect(self._add_episode)
        top_row.addWidget(add_ep_btn)

        layout.addLayout(top_row)

        self.episode_table = QTableWidget()
        self.episode_table.setColumnCount(5)
        self.episode_table.setHorizontalHeaderLabels(["#", "Title", "Status", "Pages", "Script File"])
        self.episode_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.episode_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.episode_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.episode_table.doubleClicked.connect(self._on_episode_double_click)
        layout.addWidget(self.episode_table, 1)

        self.tabs.addTab(tab, "Episodes")

    def _build_bible_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 16, 24, 12)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        cat_label = QLabel("Category:")
        cat_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        top_row.addWidget(cat_label)

        self.bible_category_combo = QComboBox()
        self.bible_category_combo.setFixedHeight(32)
        for cat in ["all", "character", "location", "prop", "theme", "backstory"]:
            self.bible_category_combo.addItem(cat.title(), cat)
        self.bible_category_combo.currentIndexChanged.connect(self._refresh_bible)
        top_row.addWidget(self.bible_category_combo)

        top_row.addStretch()

        self.bible_search = QLineEdit()
        self.bible_search.setPlaceholderText("Search bible...")
        self.bible_search.setFixedHeight(32)
        self.bible_search.setFixedWidth(200)
        self.bible_search.textChanged.connect(self._refresh_bible)
        top_row.addWidget(self.bible_search)

        add_entry_btn = QPushButton("+ Entry")
        add_entry_btn.setObjectName("primary")
        add_entry_btn.setFixedHeight(32)
        add_entry_btn.clicked.connect(self._add_bible_entry)
        top_row.addWidget(add_entry_btn)

        layout.addLayout(top_row)

        self.bible_table = QTableWidget()
        self.bible_table.setColumnCount(4)
        self.bible_table.setHorizontalHeaderLabels(["Name", "Category", "Description", "Episodes"])
        self.bible_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.bible_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.bible_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.bible_table, 1)

        self.tabs.addTab(tab, "Series Bible")

    def _build_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 16, 24, 12)
        layout.setSpacing(10)

        fields = [
            ("Title", "title_input"),
            ("Showrunner", "showrunner_input"),
            ("Network", "network_input"),
            ("Genre", "genre_input"),
        ]
        for label_text, attr in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
            layout.addWidget(lbl)
            inp = QLineEdit()
            inp.setFixedHeight(32)
            setattr(self, attr, inp)
            layout.addWidget(inp)

        lbl = QLabel("Logline")
        lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        layout.addWidget(lbl)
        self.logline_input = QTextEdit()
        self.logline_input.setFixedHeight(72)
        layout.addWidget(self.logline_input)

        layout.addStretch()

        save_btn = QPushButton("Save Info")
        save_btn.setObjectName("primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save_info)
        layout.addWidget(save_btn)

        self.tabs.addTab(tab, "Series Info")

    def set_project(self, project: SeriesProject):
        self._project = project
        self._refresh_seasons()
        self._refresh_info()

    def get_project(self) -> SeriesProject | None:
        return self._project

    def _refresh_seasons(self):
        self.season_combo.blockSignals(True)
        self.season_combo.clear()
        if self._project:
            for season in self._project.seasons:
                label = f"S{season.number}: {season.title}" if season.title else f"Season {season.number}"
                self.season_combo.addItem(label, season.number)
        self.season_combo.blockSignals(False)
        self._refresh_episodes()

    def _refresh_episodes(self):
        self.episode_table.setRowCount(0)
        if not self._project:
            return
        season_num = self.season_combo.currentData()
        if season_num is None:
            return
        season = self._project.get_season(season_num)
        if not season:
            return
        self.episode_table.setRowCount(len(season.episodes))
        for i, ep in enumerate(season.episodes):
            self.episode_table.setItem(i, 0, QTableWidgetItem(str(ep.number)))
            self.episode_table.setItem(i, 1, QTableWidgetItem(ep.title))
            status_item = QTableWidgetItem(ep.status.title())
            self.episode_table.setItem(i, 2, status_item)
            self.episode_table.setItem(i, 3, QTableWidgetItem(str(ep.page_count)))
            self.episode_table.setItem(i, 4, QTableWidgetItem(ep.script_file))

    def _refresh_bible(self):
        self.bible_table.setRowCount(0)
        if not self._project:
            return
        cat = self.bible_category_combo.currentData()
        query = self.bible_search.text().strip().lower()
        entries = self._project.bible.entries
        if cat and cat != "all":
            entries = [e for e in entries if e.category == cat]
        if query:
            entries = [
                e for e in entries
                if query in e.name.lower() or query in e.description.lower()
            ]
        self.bible_table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            self.bible_table.setItem(i, 0, QTableWidgetItem(entry.name))
            self.bible_table.setItem(i, 1, QTableWidgetItem(entry.category.title()))
            desc = entry.description[:80] + "..." if len(entry.description) > 80 else entry.description
            self.bible_table.setItem(i, 2, QTableWidgetItem(desc))
            eps = ", ".join(str(e) for e in entry.episodes) if entry.episodes else "—"
            self.bible_table.setItem(i, 3, QTableWidgetItem(eps))

    def _refresh_info(self):
        if not self._project:
            return
        self.title_input.setText(self._project.title)
        self.showrunner_input.setText(self._project.showrunner)
        self.network_input.setText(self._project.network)
        self.genre_input.setText(self._project.genre)
        self.logline_input.setPlainText(self._project.logline)

    def _on_season_changed(self, index: int):
        self._refresh_episodes()

    def _on_episode_double_click(self, index):
        row = index.row()
        season_num = self.season_combo.currentData()
        if season_num is None:
            return
        season = self._project.get_season(season_num)
        if season and row < len(season.episodes):
            ep = season.episodes[row]
            self.episode_selected.emit(season_num, ep.number)
            self.close()

    def _add_season(self):
        if not self._project:
            return
        self._project.add_season()
        self._refresh_seasons()
        self.season_combo.setCurrentIndex(self.season_combo.count() - 1)
        self.project_changed.emit()

    def _add_episode(self):
        if not self._project:
            return
        season_num = self.season_combo.currentData()
        if season_num is None:
            return
        num = len(self._project.get_season(season_num).episodes) + 1
        self._project.add_episode(season_num, f"Episode {num}")
        self._refresh_episodes()
        self.project_changed.emit()

    def _add_bible_entry(self):
        if not self._project:
            return
        cat = self.bible_category_combo.currentData()
        if cat == "all":
            cat = "character"
        entry = BibleEntry(category=cat, name="New Entry", description="")
        self._project.bible.add_entry(entry)
        self._refresh_bible()
        self.project_changed.emit()

    def _save_info(self):
        if not self._project:
            return
        self._project.title = self.title_input.text()
        self._project.showrunner = self.showrunner_input.text()
        self._project.network = self.network_input.text()
        self._project.genre = self.genre_input.text()
        self._project.logline = self.logline_input.toPlainText()
        self.project_changed.emit()
