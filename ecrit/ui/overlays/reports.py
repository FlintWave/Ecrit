"""Production Reports dialog — scene breakdown, cast, locations, day/night, one-liner."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt

from ecrit.ui.styles import theme
from ecrit.screenplay.production_reports import (
    generate_scene_report,
    generate_cast_report,
    generate_location_report,
    generate_day_night_report,
    generate_one_liner,
)


def _make_table(columns: list[str], stretch_col: int = 0) -> QTableWidget:
    """Create a consistently styled read-only table."""
    table = QTableWidget()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.horizontalHeader().setSectionResizeMode(
        stretch_col, QHeaderView.ResizeMode.Stretch
    )
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setAlternatingRowColors(True)
    return table


class ReportsDialog(QDialog):
    """Modal dialog displaying production reports for a Fountain screenplay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Production Reports")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Header ──────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Production Reports")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # ── Tab widget ──────────────────────────────────────────
        self._tabs = QTabWidget()

        # Scene Report tab
        scene_tab = QWidget()
        scene_layout = QVBoxLayout(scene_tab)
        self._scene_table = _make_table(
            ["#", "Heading", "Location", "Int/Ext", "Time", "Characters",
             "Pg Start", "Pg End", "Est. Min"],
            stretch_col=1,
        )
        scene_layout.addWidget(self._scene_table)
        self._tabs.addTab(scene_tab, "Scene Report")

        # Cast Report tab
        cast_tab = QWidget()
        cast_layout = QVBoxLayout(cast_tab)
        self._cast_table = _make_table(
            ["Name", "Scenes", "Lines", "Words", "First Scene", "Last Scene"],
            stretch_col=0,
        )
        cast_layout.addWidget(self._cast_table)
        self._tabs.addTab(cast_tab, "Cast Report")

        # Location Report tab
        loc_tab = QWidget()
        loc_layout = QVBoxLayout(loc_tab)
        self._loc_table = _make_table(
            ["Location", "Scene Count", "Scenes", "Total Pages"],
            stretch_col=0,
        )
        loc_layout.addWidget(self._loc_table)
        self._tabs.addTab(loc_tab, "Location Report")

        # Day/Night tab
        dn_tab = QWidget()
        dn_layout = QVBoxLayout(dn_tab)
        self._dn_table = _make_table(
            ["Time of Day", "Scene Count", "Scenes"],
            stretch_col=2,
        )
        dn_layout.addWidget(self._dn_table)
        self._tabs.addTab(dn_tab, "Day/Night")

        # One-Liner tab
        ol_tab = QWidget()
        ol_layout = QVBoxLayout(ol_tab)
        self._ol_table = _make_table(
            ["#", "Heading", "Summary"],
            stretch_col=2,
        )
        ol_layout.addWidget(self._ol_table)
        self._tabs.addTab(ol_tab, "One-Liner")

        layout.addWidget(self._tabs, 1)

    # ── Public API ──────────────────────────────────────────────

    def set_script(self, script: str) -> None:
        """Generate all production reports from *script* and populate the tables."""
        self._populate_scene_report(generate_scene_report(script))
        self._populate_cast_report(generate_cast_report(script))
        self._populate_location_report(generate_location_report(script))
        self._populate_day_night_report(generate_day_night_report(script))
        self._populate_one_liner(generate_one_liner(script))

    # ── Private helpers ─────────────────────────────────────────

    @staticmethod
    def _right_aligned(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _populate_scene_report(self, data: list[dict]) -> None:
        tbl = self._scene_table
        tbl.setRowCount(len(data))
        for i, row in enumerate(data):
            tbl.setItem(i, 0, self._right_aligned(str(row["number"])))
            tbl.setItem(i, 1, QTableWidgetItem(row["heading"]))
            tbl.setItem(i, 2, QTableWidgetItem(row["location"]))
            tbl.setItem(i, 3, QTableWidgetItem(row["int_ext"]))
            tbl.setItem(i, 4, QTableWidgetItem(row["time_of_day"]))
            tbl.setItem(i, 5, QTableWidgetItem(", ".join(row["characters"])))
            tbl.setItem(i, 6, self._right_aligned(str(row["page_start"])))
            tbl.setItem(i, 7, self._right_aligned(str(row["page_end"])))
            tbl.setItem(i, 8, self._right_aligned(str(row["estimated_minutes"])))

    def _populate_cast_report(self, data: list[dict]) -> None:
        tbl = self._cast_table
        tbl.setRowCount(len(data))
        for i, row in enumerate(data):
            tbl.setItem(i, 0, QTableWidgetItem(row["name"]))
            tbl.setItem(i, 1, self._right_aligned(str(row["scene_count"])))
            tbl.setItem(i, 2, self._right_aligned(str(row["dialogue_lines"])))
            tbl.setItem(i, 3, self._right_aligned(str(row["dialogue_words"])))
            tbl.setItem(i, 4, self._right_aligned(str(row["first_scene"])))
            tbl.setItem(i, 5, self._right_aligned(str(row["last_scene"])))

    def _populate_location_report(self, data: list[dict]) -> None:
        tbl = self._loc_table
        tbl.setRowCount(len(data))
        for i, row in enumerate(data):
            tbl.setItem(i, 0, QTableWidgetItem(row["location"]))
            tbl.setItem(i, 1, self._right_aligned(str(row["scene_count"])))
            tbl.setItem(i, 2, QTableWidgetItem(
                ", ".join(str(s) for s in row["scenes"])
            ))
            tbl.setItem(i, 3, self._right_aligned(str(row["total_pages"])))

    def _populate_day_night_report(self, data: dict[str, list[int]]) -> None:
        tbl = self._dn_table
        sorted_keys = sorted(data.keys())
        tbl.setRowCount(len(sorted_keys))
        for i, category in enumerate(sorted_keys):
            scenes = data[category]
            tbl.setItem(i, 0, QTableWidgetItem(category))
            tbl.setItem(i, 1, self._right_aligned(str(len(scenes))))
            tbl.setItem(i, 2, QTableWidgetItem(
                ", ".join(str(s) for s in scenes)
            ))

    def _populate_one_liner(self, data: list[dict]) -> None:
        tbl = self._ol_table
        tbl.setRowCount(len(data))
        for i, row in enumerate(data):
            tbl.setItem(i, 0, self._right_aligned(str(row["number"])))
            tbl.setItem(i, 1, QTableWidgetItem(row["heading"]))
            tbl.setItem(i, 2, QTableWidgetItem(row["summary"]))
