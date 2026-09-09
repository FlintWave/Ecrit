"""Git snapshots — local version history using git commits."""

import subprocess
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


def _run_git(project_path: str, *args) -> str:
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _ensure_git_identity(project_path: str):
    name = _run_git(project_path, "config", "user.name")
    if not name:
        _run_git(project_path, "config", "user.name", "Ecrit")
        _run_git(project_path, "config", "user.email", "ecrit@localhost")


def init_repo(project_path: str):
    if not os.path.exists(os.path.join(project_path, ".git")):
        _run_git(project_path, "init")
        _ensure_git_identity(project_path)
        _run_git(project_path, "add", "-A")
        _run_git(project_path, "commit", "-m", "Initial snapshot")


def create_snapshot(project_path: str, message: str = "") -> bool:
    if not os.path.exists(os.path.join(project_path, ".git")):
        init_repo(project_path)
    else:
        _ensure_git_identity(project_path)

    _run_git(project_path, "add", "-A")

    status = _run_git(project_path, "status", "--porcelain")
    if not status:
        return False

    if not message:
        message = f"Snapshot {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    _run_git(project_path, "commit", "-m", message)
    return True


def list_snapshots(project_path: str) -> list:
    if not os.path.exists(os.path.join(project_path, ".git")):
        return []

    log = _run_git(
        project_path, "log",
        "--pretty=format:%H|%s|%ai",
        "-50"
    )
    if not log:
        return []

    snapshots = []
    for line in log.strip().split("\n"):
        parts = line.split("|", 2)
        if len(parts) >= 3:
            snapshots.append({
                "hash": parts[0],
                "label": parts[1],
                "date": parts[2][:16],
            })
    return snapshots


def get_snapshot_content(project_path: str, commit_hash: str, filename: str = "script.fountain") -> str:
    return _run_git(project_path, "show", f"{commit_hash}:{filename}")


def restore_snapshot(project_path: str, commit_hash: str):
    _run_git(project_path, "checkout", commit_hash, "--", ".")


class SnapshotsDialog(QDialog):
    snapshot_restored = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Snapshots")
        self.setMinimumSize(480, 440)
        self.setModal(True)

        self._project_path = ""

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Snapshots")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        create_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Snapshot message (optional)")
        self.message_input.setFixedHeight(34)
        create_row.addWidget(self.message_input, 1)

        snap_btn = QPushButton("Snapshot")
        snap_btn.setObjectName("primary")
        snap_btn.setFixedHeight(34)
        snap_btn.clicked.connect(self._create_snapshot)
        create_row.addWidget(snap_btn)
        layout.addLayout(create_row)

        self.snap_list = QListWidget()
        layout.addWidget(self.snap_list, 1)

        restore_row = QHBoxLayout()
        restore_row.addStretch()
        self.restore_btn = QPushButton("Restore selected")
        self.restore_btn.setObjectName("secondary")
        self.restore_btn.setFixedHeight(34)
        self.restore_btn.clicked.connect(self._restore_snapshot)
        restore_row.addWidget(self.restore_btn)
        layout.addLayout(restore_row)

    def set_project(self, project_path: str):
        self._project_path = project_path
        self._refresh()

    def _refresh(self):
        self.snap_list.clear()
        t = theme.current()
        snapshots = list_snapshots(self._project_path)
        for s in snapshots:
            item = QListWidgetItem(f"{s['date']}  —  {s['label']}")
            item.setData(Qt.ItemDataRole.UserRole, s["hash"])
            self.snap_list.addItem(item)

    def _create_snapshot(self):
        msg = self.message_input.text().strip()
        created = create_snapshot(self._project_path, msg)
        self.message_input.clear()
        self._refresh()

    def _restore_snapshot(self):
        current = self.snap_list.currentItem()
        if current:
            commit_hash = current.data(Qt.ItemDataRole.UserRole)
            restore_snapshot(self._project_path, commit_hash)
            content = get_snapshot_content(self._project_path, commit_hash)
            self.snapshot_restored.emit(content)
            self.close()
