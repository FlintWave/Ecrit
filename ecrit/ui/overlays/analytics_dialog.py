"""Script analytics dialog — charts and statistics for screenplay analysis."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea,
)
from PySide6.QtCore import Qt

from ecrit.ui.styles import theme


class AnalyticsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Script Analytics")
        self.setMinimumSize(800, 560)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Script Analytics")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        self._summary_tab = QWidget()
        self._characters_tab = QWidget()
        self._scenes_tab = QWidget()
        self._pacing_tab = QWidget()

        self._tabs.addTab(self._summary_tab, "Summary")
        self._tabs.addTab(self._characters_tab, "Characters")
        self._tabs.addTab(self._scenes_tab, "Scenes")
        self._tabs.addTab(self._pacing_tab, "Pacing")

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def set_analytics(self, data: dict):
        self._build_summary(data)
        self._build_characters(data)
        self._build_scenes(data)
        self._build_pacing(data)

    def _build_summary(self, data: dict):
        t = theme.current()
        layout = QVBoxLayout(self._summary_tab)
        if self._summary_tab.layout():
            while self._summary_tab.layout().count():
                child = self._summary_tab.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            self._summary_tab.setLayout(layout)

        summary = data.get("summary", {})
        stat_style = f"font-size: 14px; color: {t.text}; padding: 4px 0;"
        val_style = f"font-size: 20px; font-weight: bold; color: {t.accent};"

        grid = QHBoxLayout()
        for label, key, fmt in [
            ("Pages", "total_pages", "{}"),
            ("Scenes", "total_scenes", "{}"),
            ("Characters", "total_characters", "{}"),
            ("Words", "total_words", "{:,}"),
            ("Runtime", "estimated_runtime_minutes", "{}m"),
        ]:
            col = QVBoxLayout()
            val = QLabel(fmt.format(summary.get(key, 0)))
            val.setStyleSheet(val_style)
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(val)
            lbl = QLabel(label)
            lbl.setStyleSheet(stat_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            grid.addLayout(col)
        layout.addLayout(grid)

        ratio = summary.get("dialogue_action_ratio", 0)
        layout.addWidget(QLabel(f"Dialogue/Action ratio: {ratio:.1%}"))

        ie = data.get("int_ext_ratio", {})
        parts = [f"{k}: {v}" for k, v in ie.items()]
        layout.addWidget(QLabel(f"INT/EXT: {', '.join(parts)}"))

        tod = data.get("time_of_day", {})
        parts = [f"{k}: {v}" for k, v in tod.items()]
        layout.addWidget(QLabel(f"Time of day: {', '.join(parts)}"))

        dist = data.get("scene_length_distribution", {})
        if dist:
            layout.addWidget(QLabel(
                f"Scene length: min={dist.get('min', 0)}, max={dist.get('max', 0)}, "
                f"mean={dist.get('mean', 0):.0f}, median={dist.get('median', 0):.0f}"
            ))
        layout.addStretch()

    def _build_characters(self, data: dict):
        layout = QVBoxLayout()
        if self._characters_tab.layout():
            while self._characters_tab.layout().count():
                child = self._characters_tab.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            self._characters_tab.setLayout(layout)

        chars = data.get("character_stats", [])
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Character", "Lines", "Words", "Scenes", "% Dialogue", "Avg Speech"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setRowCount(len(chars))

        for row, ch in enumerate(chars):
            table.setItem(row, 0, QTableWidgetItem(ch.get("name", "")))
            table.setItem(row, 1, QTableWidgetItem(str(ch.get("line_count", 0))))
            table.setItem(row, 2, QTableWidgetItem(str(ch.get("word_count", 0))))
            table.setItem(row, 3, QTableWidgetItem(str(ch.get("scene_count", 0))))
            table.setItem(row, 4, QTableWidgetItem(f"{ch.get('percentage', 0):.1f}%"))
            table.setItem(row, 5, QTableWidgetItem(f"{ch.get('avg_speech_length', 0):.1f}"))
        layout.addWidget(table)

    def _build_scenes(self, data: dict):
        layout = QVBoxLayout()
        if self._scenes_tab.layout():
            while self._scenes_tab.layout().count():
                child = self._scenes_tab.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            self._scenes_tab.setLayout(layout)

        scenes = data.get("scene_stats", [])
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["#", "Heading", "Words", "Chars", "% Dialogue", "Page"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setRowCount(len(scenes))

        for row, sc in enumerate(scenes):
            table.setItem(row, 0, QTableWidgetItem(str(sc.get("index", 0) + 1)))
            table.setItem(row, 1, QTableWidgetItem(sc.get("heading", "")))
            table.setItem(row, 2, QTableWidgetItem(str(sc.get("word_count", 0))))
            table.setItem(row, 3, QTableWidgetItem(str(sc.get("character_count", 0))))
            table.setItem(row, 4, QTableWidgetItem(f"{sc.get('dialogue_percentage', 0):.0f}%"))
            table.setItem(row, 5, QTableWidgetItem(f"{sc.get('page_number', 0):.1f}"))
        layout.addWidget(table)

    def _build_pacing(self, data: dict):
        layout = QVBoxLayout()
        if self._pacing_tab.layout():
            while self._pacing_tab.layout().count():
                child = self._pacing_tab.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            self._pacing_tab.setLayout(layout)

        pacing = data.get("pacing", [])
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Scene", "Dialogue %", "Action %", "Length", "Tension"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setRowCount(len(pacing))

        for row, p in enumerate(pacing):
            table.setItem(row, 0, QTableWidgetItem(str(p.get("scene_index", 0) + 1)))
            table.setItem(row, 1, QTableWidgetItem(f"{p.get('dialogue_density', 0):.0%}"))
            table.setItem(row, 2, QTableWidgetItem(f"{p.get('action_density', 0):.0%}"))
            table.setItem(row, 3, QTableWidgetItem(str(p.get("scene_length", 0))))
            table.setItem(row, 4, QTableWidgetItem(p.get("tension_estimate", "")))
        layout.addWidget(table)

        acts = data.get("act_structure", [])
        if acts:
            act_row = QHBoxLayout()
            for act in acts:
                pr = act.get("page_range", [0, 0])
                lbl = QLabel(f"Act {act.get('act', '?')}: {act.get('scene_count', 0)} scenes (pp. {pr[0]}-{pr[1]})")
                lbl.setStyleSheet("padding: 4px 8px;")
                act_row.addWidget(lbl)
            act_row.addStretch()
            layout.addLayout(act_row)
