"""Tests for new features: series UI, remote sync, cloud export, share for review."""

import os
import json
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


SAMPLE_SCRIPT = """Title: Test Script

INT. OFFICE - DAY

ALICE
Hello, world!

EXT. PARK - NIGHT

BOB
Goodbye, world!
"""


# ---------------------------------------------------------------------------
# Series Projects backend
# ---------------------------------------------------------------------------


class TestSeriesProjectsBackend:
    def test_create_series(self):
        from ecrit.screenplay.series_projects import SeriesProject
        sp = SeriesProject(title="Test Show")
        assert sp.title == "Test Show"
        assert len(sp.seasons) == 0

    def test_add_season(self):
        from ecrit.screenplay.series_projects import SeriesProject
        sp = SeriesProject(title="Test")
        s = sp.add_season("Pilot Season")
        assert s.number == 1
        assert s.title == "Pilot Season"
        assert len(sp.seasons) == 1

    def test_add_episode(self):
        from ecrit.screenplay.series_projects import SeriesProject
        sp = SeriesProject(title="Test")
        sp.add_season()
        ep = sp.add_episode(1, "Pilot", synopsis="The beginning")
        assert ep.number == 1
        assert ep.title == "Pilot"
        assert ep.script_file == "s01e01.fountain"

    def test_add_episode_invalid_season(self):
        from ecrit.screenplay.series_projects import SeriesProject
        sp = SeriesProject(title="Test")
        ep = sp.add_episode(99, "Ghost")
        assert ep is None

    def test_total_episodes(self):
        from ecrit.screenplay.series_projects import SeriesProject
        sp = SeriesProject(title="Test")
        sp.add_season()
        sp.add_episode(1, "E1")
        sp.add_episode(1, "E2")
        sp.add_season()
        sp.add_episode(2, "E1")
        assert sp.total_episodes() == 3

    def test_bible_crud(self):
        from ecrit.screenplay.series_projects import SeriesProject, BibleEntry
        sp = SeriesProject(title="Test")
        sp.bible.add_entry(BibleEntry(category="character", name="Alice", description="Lead"))
        sp.bible.add_entry(BibleEntry(category="location", name="Office", description="Main set"))
        assert len(sp.bible.get_characters()) == 1
        assert len(sp.bible.get_locations()) == 1
        assert sp.bible.get_by_name("Alice").name == "Alice"
        sp.bible.remove_entry("Alice")
        assert len(sp.bible.get_characters()) == 0

    def test_bible_search(self):
        from ecrit.screenplay.series_projects import SeriesProject, BibleEntry
        sp = SeriesProject(title="Test")
        sp.bible.add_entry(BibleEntry(category="character", name="Alice", description="Protagonist"))
        sp.bible.add_entry(BibleEntry(category="character", name="Bob", description="Antagonist"))
        results = sp.bible.search("protagonist")
        assert len(results) == 1
        assert results[0].name == "Alice"

    def test_serialization_roundtrip(self, tmp_path):
        from ecrit.screenplay.series_projects import (
            SeriesProject, BibleEntry, save_series_project, load_series_project,
        )
        sp = SeriesProject(title="Round Trip", showrunner="Test")
        sp.add_season("S1")
        sp.add_episode(1, "Pilot")
        sp.bible.add_entry(BibleEntry(category="character", name="Hero"))
        path = str(tmp_path / "series.json")
        save_series_project(sp, path)
        loaded = load_series_project(path)
        assert loaded.title == "Round Trip"
        assert loaded.total_episodes() == 1
        assert len(loaded.bible.entries) == 1

    def test_load_nonexistent(self, tmp_path):
        from ecrit.screenplay.series_projects import load_series_project
        assert load_series_project(str(tmp_path / "nope.json")) is None


# ---------------------------------------------------------------------------
# Series Panel UI
# ---------------------------------------------------------------------------


class TestSeriesPanelUI:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        panel = SeriesPanel()
        assert panel.tabs.count() == 3
        assert panel.windowTitle() == "Series Manager"

    def test_set_project(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        sp = SeriesProject(title="Test Show")
        sp.add_season("Season 1")
        sp.add_episode(1, "Pilot")
        panel.set_project(sp)
        assert panel.season_combo.count() == 1
        assert panel.episode_table.rowCount() == 1

    def test_add_season(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        sp = SeriesProject(title="Test")
        panel.set_project(sp)
        panel._add_season()
        assert panel.season_combo.count() == 1
        panel._add_season()
        assert panel.season_combo.count() == 2

    def test_add_episode(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        sp = SeriesProject(title="Test")
        sp.add_season()
        panel.set_project(sp)
        panel._add_episode()
        assert panel.episode_table.rowCount() == 1

    def test_bible_tab(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject, BibleEntry
        panel = SeriesPanel()
        sp = SeriesProject(title="Test")
        sp.bible.add_entry(BibleEntry(category="character", name="Alice"))
        panel.set_project(sp)
        panel._refresh_bible()
        assert panel.bible_table.rowCount() == 1

    def test_info_tab(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        sp = SeriesProject(title="My Show", showrunner="Boss", network="HBO")
        panel.set_project(sp)
        assert panel.title_input.text() == "My Show"
        assert panel.showrunner_input.text() == "Boss"

    def test_empty_project(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        sp = SeriesProject(title="Empty")
        panel.set_project(sp)
        assert panel.season_combo.count() == 0
        assert panel.episode_table.rowCount() == 0

    def test_episode_selected_signal(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        received = []
        panel.episode_selected.connect(lambda s, e: received.append((s, e)))
        assert hasattr(panel, "episode_selected")


# ---------------------------------------------------------------------------
# Remote Sync backend
# ---------------------------------------------------------------------------


class TestRemoteSyncBackend:
    def test_provider_enum(self):
        from ecrit.sync.remote_sync import RemoteProvider
        assert RemoteProvider.GITHUB.value == "https://github.com"
        assert RemoteProvider.GITLAB.value == "https://gitlab.com"
        assert RemoteProvider.CODEBERG.value == "https://codeberg.org"

    def test_config_creation(self):
        from ecrit.sync.remote_sync import RemoteConfig, RemoteProvider
        config = RemoteConfig(
            provider=RemoteProvider.GITHUB,
            remote_url="https://github.com/user/repo.git",
            username="user",
            token="ghp_test",
        )
        assert config.branch == "main"
        assert config.auto_sync is False

    def test_save_load_config(self, tmp_path):
        from ecrit.sync.remote_sync import (
            RemoteConfig, RemoteProvider, save_remote_config, load_remote_config,
        )
        config = RemoteConfig(
            provider=RemoteProvider.GITHUB,
            remote_url="https://github.com/user/repo.git",
            username="testuser",
            token="ghp_secret123",
        )
        save_remote_config(str(tmp_path), config)
        loaded, result = load_remote_config(str(tmp_path))
        assert loaded is not None
        assert loaded.provider == RemoteProvider.GITHUB
        assert loaded.username == "testuser"
        assert loaded.token == "ghp_secret123"

    def test_token_obfuscation(self, tmp_path):
        from ecrit.sync.remote_sync import (
            RemoteConfig, RemoteProvider, save_remote_config,
        )
        config = RemoteConfig(
            provider=RemoteProvider.GITHUB,
            remote_url="https://github.com/user/repo.git",
            username="user",
            token="supersecret",
        )
        save_remote_config(str(tmp_path), config)
        config_file = os.path.join(str(tmp_path), ".ecrit", "sync.json")
        with open(config_file) as f:
            data = json.load(f)
        assert "supersecret" not in json.dumps(data)

    def test_sync_status_enum(self):
        from ecrit.sync.remote_sync import SyncStatus
        assert SyncStatus.IDLE.value == "idle"
        assert SyncStatus.UP_TO_DATE.value == "up_to_date"

    def test_sync_result(self):
        from ecrit.sync.remote_sync import SyncResult, SyncStatus
        result = SyncResult(status=SyncStatus.ERROR, message="No remote")
        assert result.conflicts == []

    def test_get_sync_status_no_git(self, tmp_path):
        from ecrit.sync.remote_sync import get_sync_status, SyncStatus
        result = get_sync_status(str(tmp_path))
        assert result.status in (SyncStatus.ERROR, SyncStatus.IDLE)


# ---------------------------------------------------------------------------
# Remote Sync UI
# ---------------------------------------------------------------------------


class TestSyncSettingsUI:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.sync_settings import SyncSettingsDialog
        dialog = SyncSettingsDialog()
        assert dialog.windowTitle() == "Remote Sync"
        assert dialog.provider_combo.count() == 3

    def test_set_config(self, qapp):
        from ecrit.ui.overlays.sync_settings import SyncSettingsDialog
        dialog = SyncSettingsDialog()
        dialog.set_config({
            "provider": "github",
            "remote_url": "https://github.com/test/repo.git",
            "username": "testuser",
            "branch": "develop",
            "auto_sync": True,
        })
        assert dialog.repo_url_input.text() == "https://github.com/test/repo.git"
        assert dialog.username_input.text() == "testuser"
        assert dialog.branch_input.text() == "develop"
        assert dialog.auto_sync_check.isChecked()

    def test_get_config(self, qapp):
        from ecrit.ui.overlays.sync_settings import SyncSettingsDialog
        dialog = SyncSettingsDialog()
        dialog.repo_url_input.setText("https://test.git")
        dialog.username_input.setText("me")
        dialog.token_input.setText("tok")
        config = dialog.get_config()
        assert config["remote_url"] == "https://test.git"
        assert config["username"] == "me"
        assert config["token"] == "tok"

    def test_status_display(self, qapp):
        from ecrit.ui.overlays.sync_settings import SyncSettingsDialog
        dialog = SyncSettingsDialog()
        dialog.set_status("Up to date", "2025-01-01 12:00")
        assert "Up to date" in dialog.status_display.text()
        assert "12:00" in dialog.last_sync_label.text()

    def test_sync_requested_signal(self, qapp):
        from ecrit.ui.overlays.sync_settings import SyncSettingsDialog
        dialog = SyncSettingsDialog()
        received = []
        dialog.sync_requested.connect(lambda s: received.append(s))
        assert hasattr(dialog, "sync_requested")


# ---------------------------------------------------------------------------
# Cloud Export backend
# ---------------------------------------------------------------------------


class TestCloudExportBackend:
    def test_provider_enum(self):
        from ecrit.sync.cloud_export import CloudProvider
        assert len(CloudProvider) == 5

    def test_get_exporter(self):
        from ecrit.sync.cloud_export import CloudProvider, get_exporter, CloudConfig
        config = CloudConfig(provider=CloudProvider.GOOGLE_DRIVE, auth_token="", folder_path="/")
        exporter = get_exporter(CloudProvider.GOOGLE_DRIVE, config)
        assert exporter is not None
        assert not exporter.is_authenticated()

    def test_all_exporters_constructable(self):
        from ecrit.sync.cloud_export import CloudProvider, get_exporter, CloudConfig
        for provider in CloudProvider:
            config = CloudConfig(provider=provider, auth_token="", folder_path="/")
            exporter = get_exporter(provider, config)
            assert exporter is not None

    def test_save_load_configs(self, tmp_path):
        from ecrit.sync.cloud_export import (
            CloudConfig, CloudProvider, save_cloud_configs, load_cloud_configs,
        )
        configs = [
            CloudConfig(provider=CloudProvider.GOOGLE_DRIVE, auth_token="", folder_path="/test"),
            CloudConfig(provider=CloudProvider.DROPBOX, auth_token="", folder_path="/", auto_export=True),
        ]
        save_cloud_configs(str(tmp_path), configs)
        loaded = load_cloud_configs(str(tmp_path))
        assert len(loaded) == 2
        assert loaded[0].provider == CloudProvider.GOOGLE_DRIVE

    def test_export_result(self):
        from ecrit.sync.cloud_export import ExportResult
        r = ExportResult(success=True, message="ok")
        assert r.remote_url == ""


# ---------------------------------------------------------------------------
# Cloud Export UI
# ---------------------------------------------------------------------------


class TestCloudExportUI:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.cloud_export import CloudExportDialog
        dialog = CloudExportDialog()
        assert dialog.windowTitle() == "Cloud Export"
        assert dialog.provider_combo.count() == 5

    def test_format_combo(self, qapp):
        from ecrit.ui.overlays.cloud_export import CloudExportDialog
        dialog = CloudExportDialog()
        formats = set()
        for i in range(dialog.format_combo.count()):
            formats.add(dialog.format_combo.itemData(i))
        assert "pdf" in formats
        assert "fountain" in formats

    def test_export_requested_signal(self, qapp):
        from ecrit.ui.overlays.cloud_export import CloudExportDialog
        dialog = CloudExportDialog()
        received = []
        dialog.export_requested.connect(lambda p, f: received.append((p, f)))
        dialog._do_export()
        assert len(received) == 1

    def test_history_entry(self, qapp):
        from ecrit.ui.overlays.cloud_export import CloudExportDialog
        dialog = CloudExportDialog()
        dialog.add_history_entry("Test export")
        assert dialog.history_list.count() == 1


# ---------------------------------------------------------------------------
# Share for Review backend
# ---------------------------------------------------------------------------


class TestShareReviewBackend:
    def test_generate_html(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html(SAMPLE_SCRIPT, "Test", "Author", "CONFIDENTIAL")
        assert "CONFIDENTIAL" in html
        assert "Test" in html
        assert "<html" in html.lower()
        assert "Courier" in html

    def test_generate_html_empty(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html("", "Empty", "Nobody", "DRAFT")
        assert "DRAFT" in html

    def test_generate_html_unicode(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html(
            "INT. CAFÉ — JOUR\n\nHÉLOÏSE\nBonjour!\n",
            "Café Script", "José", "CONFIDENTIEL"
        )
        assert "CONFIDENTIEL" in html
        assert "Café" in html or "Caf" in html

    def test_generate_share_link(self, tmp_path):
        from ecrit.export.share_review import generate_review_html, generate_share_link
        html = generate_review_html("test", "T", "A", "W")
        path = generate_share_link(html, str(tmp_path))
        assert os.path.exists(path)
        assert path.endswith(".html")

    def test_list_shares(self, tmp_path):
        from ecrit.export.share_review import (
            generate_review_html, generate_share_link, list_shares,
        )
        html = generate_review_html("test", "Test Share", "A", "W")
        generate_share_link(html, str(tmp_path))
        shares = list_shares(str(tmp_path))
        assert len(shares) == 1
        assert "path" in shares[0]

    def test_delete_share(self, tmp_path):
        from ecrit.export.share_review import (
            generate_review_html, generate_share_link, list_shares, delete_share,
        )
        html = generate_review_html("test", "T", "A", "W")
        generate_share_link(html, str(tmp_path))
        shares = list_shares(str(tmp_path))
        assert len(shares) == 1
        deleted = delete_share(str(tmp_path), shares[0]["id"])
        assert deleted
        assert len(list_shares(str(tmp_path))) == 0

    def test_delete_nonexistent(self, tmp_path):
        from ecrit.export.share_review import delete_share
        assert delete_share(str(tmp_path), "nonexistent") is False

    def test_html_escaping(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html(
            '<script>alert("xss")</script>',
            '<img src=x>', 'Author', 'WM'
        )
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html or "script" not in html.split("<style>")[0]


# ---------------------------------------------------------------------------
# Share for Review UI
# ---------------------------------------------------------------------------


class TestShareReviewUI:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.share_review import ShareReviewDialog
        dialog = ShareReviewDialog()
        assert dialog.windowTitle() == "Share for Review"

    def test_watermark_default(self, qapp):
        from ecrit.ui.overlays.share_review import ShareReviewDialog
        dialog = ShareReviewDialog()
        assert "CONFIDENTIAL" in dialog.get_watermark()

    def test_options(self, qapp):
        from ecrit.ui.overlays.share_review import ShareReviewDialog
        dialog = ShareReviewDialog()
        opts = dialog.get_options()
        assert opts["include_title_page"] is True
        assert opts["include_page_numbers"] is True
        assert "watermark" in opts

    def test_set_shares(self, qapp):
        from ecrit.ui.overlays.share_review import ShareReviewDialog
        dialog = ShareReviewDialog()
        dialog.set_shares([
            {"title": "Draft 1", "created": "2025-01-01", "path": "/tmp/a.html"},
            {"title": "Draft 2", "created": "2025-01-02", "path": "/tmp/b.html"},
        ])
        assert dialog.shares_list.count() == 2

    def test_add_share(self, qapp):
        from ecrit.ui.overlays.share_review import ShareReviewDialog
        dialog = ShareReviewDialog()
        dialog.add_share({"title": "New", "created": "now", "path": "/x"})
        assert dialog.shares_list.count() == 1

    def test_share_created_signal(self, qapp):
        from ecrit.ui.overlays.share_review import ShareReviewDialog
        dialog = ShareReviewDialog()
        received = []
        dialog.share_created.connect(lambda s: received.append(s))
        assert hasattr(dialog, "share_created")


# ---------------------------------------------------------------------------
# Command palette new entries
# ---------------------------------------------------------------------------


class TestCommandPaletteNewEntries:
    def test_has_series_manager(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        names = [c[0] for c in COMMANDS]
        assert "Series Manager" in names

    def test_has_remote_sync(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        names = [c[0] for c in COMMANDS]
        assert "Remote Sync" in names

    def test_has_cloud_export(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        names = [c[0] for c in COMMANDS]
        assert "Cloud Export" in names

    def test_has_share_for_review(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        names = [c[0] for c in COMMANDS]
        assert "Share for Review" in names

    def test_total_commands(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        assert len(COMMANDS) >= 29


# ---------------------------------------------------------------------------
# MainWindow new features integration
# ---------------------------------------------------------------------------


class TestMainWindowNewFeatures:
    def test_has_series_panel(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_series_panel")
        win.close()
        qapp.processEvents()

    def test_has_sync_dialog(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_sync_dialog")
        win.close()
        qapp.processEvents()

    def test_has_cloud_export_dialog(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_cloud_export_dialog")
        win.close()
        qapp.processEvents()

    def test_has_share_dialog(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_share_dialog")
        win.close()
        qapp.processEvents()

    def test_handlers_wired(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_show_series_manager")
        assert hasattr(win, "_show_sync_settings")
        assert hasattr(win, "_show_cloud_export")
        assert hasattr(win, "_show_share_review")
        win.close()
        qapp.processEvents()


# ---------------------------------------------------------------------------
# Adversarial tests
# ---------------------------------------------------------------------------


class TestNewFeaturesAdversarial:
    def test_series_many_seasons(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        sp = SeriesProject(title="Long Runner")
        for i in range(20):
            sp.add_season(f"Season {i+1}")
            sp.add_episode(i+1, "Premiere")
        panel.set_project(sp)
        assert panel.season_combo.count() == 20

    def test_series_empty_bible_search(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        from ecrit.screenplay.series_projects import SeriesProject
        panel = SeriesPanel()
        sp = SeriesProject(title="Test")
        panel.set_project(sp)
        panel.bible_search.setText("nonexistent")
        panel._refresh_bible()
        assert panel.bible_table.rowCount() == 0

    def test_sync_empty_config(self, qapp):
        from ecrit.ui.overlays.sync_settings import SyncSettingsDialog
        dialog = SyncSettingsDialog()
        config = dialog.get_config()
        assert config["remote_url"] == ""
        assert config["token"] == ""

    def test_cloud_export_all_formats(self, qapp):
        from ecrit.ui.overlays.cloud_export import CloudExportDialog
        dialog = CloudExportDialog()
        received = []
        dialog.export_requested.connect(lambda p, f: received.append(f))
        for i in range(dialog.format_combo.count()):
            dialog.format_combo.setCurrentIndex(i)
            dialog._do_export()
        assert len(received) == dialog.format_combo.count()

    def test_share_review_html_large_script(self):
        from ecrit.export.share_review import generate_review_html
        big_script = "\n".join(
            f"INT. SCENE {i} - DAY\n\nCHARACTER_{i}\nDialogue {i}.\n"
            for i in range(200)
        )
        html = generate_review_html(big_script, "Big Script", "Author", "DRAFT")
        assert len(html) > 10000

    def test_share_multiple_creates(self, tmp_path):
        from ecrit.export.share_review import (
            generate_review_html, generate_share_link, list_shares,
        )
        for i in range(5):
            html = generate_review_html(f"Script {i}", f"Title {i}", "A", "W")
            generate_share_link(html, str(tmp_path))
        shares = list_shares(str(tmp_path))
        assert len(shares) == 5
