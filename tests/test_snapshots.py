"""Tests for the git snapshot system — adversarial edge cases."""

import os
import subprocess
import pytest
from unittest.mock import patch

from ecrit.ui.overlays.snapshots import (
    _run_git, init_repo, create_snapshot, list_snapshots,
    get_snapshot_content, restore_snapshot,
)


class TestRunGit:
    def test_run_git_in_git_repo(self, tmp_path):
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        result = _run_git(str(tmp_path), "status")
        assert result != ""

    def test_run_git_nonexistent_dir(self):
        result = _run_git("/nonexistent/path", "status")
        assert result == ""

    def test_run_git_invalid_command(self, tmp_path):
        result = _run_git(str(tmp_path), "nonexistent-subcommand")
        assert result == ""  # should not raise


class TestInitRepo:
    def test_init_creates_git_dir(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        init_repo(str(tmp_path))
        assert (tmp_path / ".git").exists()

    def test_init_idempotent(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        init_repo(str(tmp_path))
        init_repo(str(tmp_path))  # should not fail
        assert (tmp_path / ".git").exists()

    def test_init_empty_dir(self, tmp_path):
        init_repo(str(tmp_path))
        assert (tmp_path / ".git").exists()


class TestCreateSnapshot:
    def test_create_snapshot_with_changes(self, tmp_path):
        (tmp_path / "script.fountain").write_text("INT. ROOM - DAY")
        init_repo(str(tmp_path))
        (tmp_path / "script.fountain").write_text("INT. ROOM - DAY\n\nUpdated.")
        result = create_snapshot(str(tmp_path), "Test snapshot")
        assert result is True

    def test_create_snapshot_no_changes(self, tmp_path):
        (tmp_path / "script.fountain").write_text("INT. ROOM - DAY")
        init_repo(str(tmp_path))
        result = create_snapshot(str(tmp_path))
        assert result is False  # no changes since init

    def test_create_snapshot_auto_inits(self, tmp_path):
        (tmp_path / "script.fountain").write_text("content")
        result = create_snapshot(str(tmp_path), "First")
        # After auto-init, everything is already committed
        assert result is False

    def test_create_snapshot_default_message(self, tmp_path):
        (tmp_path / "file.txt").write_text("v1")
        init_repo(str(tmp_path))
        (tmp_path / "file.txt").write_text("v2")
        create_snapshot(str(tmp_path))  # default message
        snaps = list_snapshots(str(tmp_path))
        assert len(snaps) >= 2
        assert "Snapshot" in snaps[0]["label"]

    def test_create_snapshot_unicode_message(self, tmp_path):
        (tmp_path / "file.txt").write_text("v1")
        init_repo(str(tmp_path))
        (tmp_path / "file.txt").write_text("v2")
        create_snapshot(str(tmp_path), "Snapshot avec des accents: éàü")
        snaps = list_snapshots(str(tmp_path))
        assert "accents" in snaps[0]["label"]


class TestListSnapshots:
    def test_list_no_repo(self, tmp_path):
        result = list_snapshots(str(tmp_path))
        assert result == []

    def test_list_after_init(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        init_repo(str(tmp_path))
        snaps = list_snapshots(str(tmp_path))
        assert len(snaps) == 1
        assert snaps[0]["label"] == "Initial snapshot"

    def test_list_multiple(self, tmp_path):
        (tmp_path / "file.txt").write_text("v1")
        init_repo(str(tmp_path))
        for i in range(5):
            (tmp_path / "file.txt").write_text(f"v{i+2}")
            create_snapshot(str(tmp_path), f"Snapshot {i+1}")
        snaps = list_snapshots(str(tmp_path))
        assert len(snaps) == 6  # initial + 5

    def test_snapshot_has_hash(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        init_repo(str(tmp_path))
        snaps = list_snapshots(str(tmp_path))
        assert len(snaps[0]["hash"]) == 40  # full SHA

    def test_snapshot_has_date(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        init_repo(str(tmp_path))
        snaps = list_snapshots(str(tmp_path))
        assert len(snaps[0]["date"]) > 0


class TestGetSnapshotContent:
    def test_get_content(self, tmp_path):
        (tmp_path / "script.fountain").write_text("Original content")
        init_repo(str(tmp_path))
        snaps = list_snapshots(str(tmp_path))
        content = get_snapshot_content(str(tmp_path), snaps[0]["hash"])
        assert content == "Original content"

    def test_get_content_invalid_hash(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        init_repo(str(tmp_path))
        content = get_snapshot_content(str(tmp_path), "0" * 40)
        assert content == ""

    def test_get_content_nonexistent_file(self, tmp_path):
        (tmp_path / "file.txt").write_text("hello")
        init_repo(str(tmp_path))
        snaps = list_snapshots(str(tmp_path))
        content = get_snapshot_content(str(tmp_path), snaps[0]["hash"], "nonexistent.txt")
        assert content == ""


class TestRestoreSnapshot:
    def test_restore(self, tmp_path):
        (tmp_path / "script.fountain").write_text("Version 1")
        init_repo(str(tmp_path))

        (tmp_path / "script.fountain").write_text("Version 2")
        create_snapshot(str(tmp_path), "v2")

        snaps = list_snapshots(str(tmp_path))
        # Restore to initial (last in list)
        initial_hash = snaps[-1]["hash"]
        restore_snapshot(str(tmp_path), initial_hash)
        content = (tmp_path / "script.fountain").read_text()
        assert content == "Version 1"


class TestSnapshotEdgeCases:
    def test_special_chars_in_path(self, tmp_path):
        weird_dir = tmp_path / "project with spaces & (parens)"
        weird_dir.mkdir()
        (weird_dir / "file.txt").write_text("hello")
        init_repo(str(weird_dir))
        snaps = list_snapshots(str(weird_dir))
        assert len(snaps) >= 1

    def test_empty_repo(self, tmp_path):
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        snaps = list_snapshots(str(tmp_path))
        assert snaps == []

    def test_concurrent_operations(self, tmp_path):
        """Multiple rapid snapshots should not corrupt."""
        (tmp_path / "file.txt").write_text("v0")
        init_repo(str(tmp_path))
        for i in range(10):
            (tmp_path / "file.txt").write_text(f"v{i+1}")
            create_snapshot(str(tmp_path), f"snap{i}")
        snaps = list_snapshots(str(tmp_path))
        assert len(snaps) == 11  # 1 initial + 10
