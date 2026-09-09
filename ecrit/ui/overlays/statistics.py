"""Statistics modal — word counts, page counts, character breakdowns."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QTabWidget, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from ecrit.ui.styles import theme


class StatRow(QFrame):
    def __init__(self, label: str, value: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        t = theme.current()
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px;")
        layout.addWidget(lbl)

        layout.addStretch()

        val = QLabel(value)
        val.setStyleSheet("font-family: ui-monospace, Menlo, monospace; font-size: 14px;")
        layout.addWidget(val)
        self._val_label = val

    def set_value(self, value: str):
        self._val_label.setText(value)


class StatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Statistics")
        self.setMinimumSize(520, 480)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Statistics")
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

        overview = QWidget()
        ov_layout = QVBoxLayout(overview)
        ov_layout.setSpacing(2)

        self.stat_rows = {}
        for key, label in [
            ("pages", "Pages"),
            ("words", "Words"),
            ("scenes", "Scenes"),
            ("characters", "Characters"),
            ("dialogue_pct", "Dialogue"),
            ("action_pct", "Action"),
        ]:
            row = StatRow(label, "—")
            ov_layout.addWidget(row)
            self.stat_rows[key] = row

        ov_layout.addStretch()
        tabs.addTab(overview, "Overview")

        chars = QWidget()
        chars_layout = QVBoxLayout(chars)

        self.char_table = QTableWidget()
        self.char_table.setColumnCount(3)
        self.char_table.setHorizontalHeaderLabels(["Character", "Lines", "Words"])
        self.char_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.char_table.verticalHeader().setVisible(False)
        self.char_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        chars_layout.addWidget(self.char_table)

        tabs.addTab(chars, "Characters")

        scenes = QWidget()
        scenes_layout = QVBoxLayout(scenes)

        self.scene_table = QTableWidget()
        self.scene_table.setColumnCount(3)
        self.scene_table.setHorizontalHeaderLabels(["Scene", "Words", "Page"])
        self.scene_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.scene_table.verticalHeader().setVisible(False)
        self.scene_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        scenes_layout.addWidget(self.scene_table)

        tabs.addTab(scenes, "Scenes")

        layout.addWidget(tabs, 1)

    def set_stats(self, stats: dict):
        self.stat_rows["pages"].set_value(str(stats.get("page_count", 0)))
        self.stat_rows["words"].set_value(f'{stats.get("word_count", 0):,}')
        self.stat_rows["scenes"].set_value(str(stats.get("scene_count", 0)))
        self.stat_rows["characters"].set_value(str(stats.get("character_count", 0)))

        d_pct = stats.get("dialogue_percentage", 0)
        a_pct = stats.get("action_percentage", 0)
        self.stat_rows["dialogue_pct"].set_value(f"{d_pct:.0f}%")
        self.stat_rows["action_pct"].set_value(f"{a_pct:.0f}%")

        characters = stats.get("characters", [])
        self.char_table.setRowCount(len(characters))
        for i, ch in enumerate(characters):
            self.char_table.setItem(i, 0, QTableWidgetItem(ch.get("name", "")))
            self.char_table.setItem(i, 1, QTableWidgetItem(str(ch.get("line_count", 0))))
            self.char_table.setItem(i, 2, QTableWidgetItem(str(ch.get("word_count", 0))))

        scenes = stats.get("scenes", [])
        self.scene_table.setRowCount(len(scenes))
        for i, sc in enumerate(scenes):
            self.scene_table.setItem(i, 0, QTableWidgetItem(sc.get("heading", "")))
            self.scene_table.setItem(i, 1, QTableWidgetItem(str(sc.get("word_count", 0))))
            self.scene_table.setItem(i, 2, QTableWidgetItem(str(sc.get("page", 0))))
