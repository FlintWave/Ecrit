"""Browse and restore autosave snapshots."""

from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.icons import IconButton
from ecrit.screenplay.autosave import AutosaveManager


class AutosaveBrowserDialog(QDialog):
    snapshot_restored = Signal(str)

    def __init__(self, manager: AutosaveManager, project_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Autosave Snapshots")
        self.setMinimumSize(520, 460)
        self.setModal(True)

        self._manager = manager
        self._project_path = project_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Autosave Snapshots")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = IconButton("x-mark")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.setAccessibleName("Close")
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        info = QLabel(f"Snapshots saved every {manager._interval_minutes} min")
        info.setObjectName("dashMutedSmall")
        layout.addWidget(info)

        self.snap_list = QListWidget()
        self.snap_list.setAccessibleName("Autosave Snapshots")
        layout.addWidget(self.snap_list, 1)

        btn_row = QHBoxLayout()
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("secondary")
        self.delete_btn.setFixedHeight(34)
        self.delete_btn.setAccessibleName("Delete Snapshot")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch()
        self.restore_btn = QPushButton("Restore selected")
        self.restore_btn.setObjectName("primary")
        self.restore_btn.setFixedHeight(34)
        self.restore_btn.setAccessibleName("Restore Selected Snapshot")
        self.restore_btn.clicked.connect(self._restore_selected)
        btn_row.addWidget(self.restore_btn)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        self.snap_list.clear()
        snapshots = self._manager.list_snapshots(self._project_path)
        for snap in snapshots:
            try:
                dt = datetime.fromisoformat(snap.timestamp)
                display_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                display_time = snap.timestamp
            label_suffix = f"  [{snap.label}]" if snap.label else ""
            text = f"{display_time}  —  {snap.word_count:,} words{label_suffix}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, snap.timestamp)
            self.snap_list.addItem(item)

    def _restore_selected(self):
        current = self.snap_list.currentItem()
        if not current:
            return
        timestamp = current.data(Qt.ItemDataRole.UserRole)
        content = self._manager.restore_snapshot(self._project_path, timestamp)
        if content is not None:
            self.snapshot_restored.emit(content)
            self.close()

    def _delete_selected(self):
        current = self.snap_list.currentItem()
        if not current:
            return
        timestamp = current.data(Qt.ItemDataRole.UserRole)
        self._manager.delete_snapshot(self._project_path, timestamp)
        self._refresh()
