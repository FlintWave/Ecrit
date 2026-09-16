"""Periodic autosave snapshots independent from git commits."""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AutosaveSnapshot:
    timestamp: str
    content: str
    word_count: int
    label: str = ""


class AutosaveManager:
    def __init__(self):
        self._interval_minutes: int = 5
        self._max_snapshots: int = 50
        self._enabled: bool = True

    def set_interval(self, minutes: int) -> None:
        self._interval_minutes = max(1, min(60, minutes))

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def get_snapshot_path(self, project_path: str) -> str:
        return os.path.join(project_path, ".ecrit", "autosaves")

    def create_snapshot(self, content: str, project_path: str, label: str = "") -> AutosaveSnapshot:
        snapshots_dir = self.get_snapshot_path(project_path)
        os.makedirs(snapshots_dir, exist_ok=True)

        now = datetime.now()
        timestamp = now.isoformat(timespec="seconds")
        filename = now.strftime("%Y-%m-%dT%H-%M-%S") + ".json"
        word_count = len(content.split())

        snapshot = AutosaveSnapshot(
            timestamp=timestamp,
            content=content,
            word_count=word_count,
            label=label,
        )

        data = {
            "timestamp": snapshot.timestamp,
            "content": snapshot.content,
            "word_count": snapshot.word_count,
            "label": snapshot.label,
        }

        filepath = os.path.join(snapshots_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

        self.cleanup_old(project_path)
        return snapshot

    def list_snapshots(self, project_path: str) -> list[AutosaveSnapshot]:
        snapshots_dir = self.get_snapshot_path(project_path)
        if not os.path.isdir(snapshots_dir):
            return []

        snapshots = []
        for name in os.listdir(snapshots_dir):
            if not name.endswith(".json"):
                continue
            filepath = os.path.join(snapshots_dir, name)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                snapshots.append(AutosaveSnapshot(
                    timestamp=data["timestamp"],
                    content=data["content"],
                    word_count=data.get("word_count", 0),
                    label=data.get("label", ""),
                ))
            except (json.JSONDecodeError, KeyError, OSError):
                continue

        snapshots.sort(key=lambda s: s.timestamp, reverse=True)
        return snapshots

    def restore_snapshot(self, project_path: str, timestamp: str) -> Optional[str]:
        for snap in self.list_snapshots(project_path):
            if snap.timestamp == timestamp:
                return snap.content
        return None

    def delete_snapshot(self, project_path: str, timestamp: str) -> bool:
        snapshots_dir = self.get_snapshot_path(project_path)
        if not os.path.isdir(snapshots_dir):
            return False

        for name in os.listdir(snapshots_dir):
            if not name.endswith(".json"):
                continue
            filepath = os.path.join(snapshots_dir, name)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("timestamp") == timestamp:
                    os.remove(filepath)
                    return True
            except (json.JSONDecodeError, KeyError, OSError):
                continue
        return False

    def cleanup_old(self, project_path: str) -> int:
        snapshots_dir = self.get_snapshot_path(project_path)
        if not os.path.isdir(snapshots_dir):
            return 0

        files = []
        for name in os.listdir(snapshots_dir):
            if name.endswith(".json"):
                filepath = os.path.join(snapshots_dir, name)
                try:
                    mtime = os.path.getmtime(filepath)
                    files.append((mtime, filepath))
                except OSError:
                    continue

        files.sort(reverse=True)
        removed = 0
        for _mtime, filepath in files[self._max_snapshots:]:
            try:
                os.remove(filepath)
                removed += 1
            except OSError:
                continue
        return removed
