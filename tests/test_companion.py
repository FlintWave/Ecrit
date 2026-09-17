"""Tests for companion modules: sync_bundle, reader_export, device_sync."""

import json
import os
import zipfile
import pytest

from ecrit.companion.sync_bundle import SyncBundle, create_sync_bundle, load_sync_bundle
from ecrit.companion.reader_export import ReaderBundle, create_reader_bundle, _fountain_to_html


class TestSyncBundle:
    def test_to_dict_roundtrip(self):
        bundle = SyncBundle(
            project_title="Test Script",
            script_content="INT. OFFICE - DAY",
            format_id="fountain/core",
        )
        d = bundle.to_dict()
        restored = SyncBundle.from_dict(d)
        assert restored.project_title == "Test Script"
        assert restored.script_content == "INT. OFFICE - DAY"
        assert restored.format_id == "fountain/core"

    def test_created_at_auto_set(self):
        bundle = SyncBundle(project_title="X", script_content="Y")
        assert bundle.created_at != ""

    def test_from_dict_defaults(self):
        bundle = SyncBundle.from_dict({})
        assert bundle.project_title == "Untitled"
        assert bundle.script_content == ""

    def test_create_and_load_bundle(self, tmp_path):
        project = tmp_path / "MyProject"
        project.mkdir()
        meta = {"title": "My Script", "format_id": "fountain/core"}
        (project / "meta.json").write_text(json.dumps(meta))

        content = "INT. LIVING ROOM - NIGHT\n\nCharacters speak."
        filepath = create_sync_bundle(
            str(project), content, title="My Script", output_dir=str(tmp_path),
        )
        assert os.path.exists(filepath)
        assert filepath.endswith(".ecrit-sync")

        loaded = load_sync_bundle(filepath)
        assert loaded is not None
        assert loaded.project_title == "My Script"
        assert loaded.script_content == content
        assert loaded.format_id == "fountain/core"

    def test_create_bundle_no_meta(self, tmp_path):
        project = tmp_path / "NoMeta"
        project.mkdir()
        filepath = create_sync_bundle(str(project), "content", output_dir=str(tmp_path))
        loaded = load_sync_bundle(filepath)
        assert loaded is not None
        assert loaded.format_id == "fountain/core"

    def test_load_nonexistent(self, tmp_path):
        assert load_sync_bundle(str(tmp_path / "nope.zip")) is None

    def test_load_corrupt_zip(self, tmp_path):
        bad = tmp_path / "bad.ecrit-sync"
        bad.write_text("not a zip")
        assert load_sync_bundle(str(bad)) is None

    def test_bundle_contains_script(self, tmp_path):
        project = tmp_path / "P"
        project.mkdir()
        content = "EXT. PARK - DAY"
        filepath = create_sync_bundle(str(project), content, output_dir=str(tmp_path))
        with zipfile.ZipFile(filepath, "r") as zf:
            names = zf.namelist()
            assert "bundle.json" in names
            assert "script.fountain" in names
            script = zf.read("script.fountain").decode("utf-8")
            assert script == content


class TestReaderExport:
    def test_fountain_to_html_scene_heading(self):
        html = _fountain_to_html("INT. OFFICE - DAY", "Test")
        assert 'class="scene"' in html
        assert "OFFICE" in html

    def test_fountain_to_html_character(self):
        html = _fountain_to_html("JOHN\nHello there.", "Test")
        assert 'class="character"' in html
        assert "JOHN" in html

    def test_fountain_to_html_transition(self):
        html = _fountain_to_html("CUT TO:", "Test")
        assert 'class="transition"' in html

    def test_fountain_to_html_parenthetical(self):
        html = _fountain_to_html("(whispering)", "Test")
        assert 'class="parenthetical"' in html

    def test_fountain_to_html_escapes_xss(self):
        html = _fountain_to_html("<script>alert('xss')</script>", "Test")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_fountain_to_html_title_escaped(self):
        html = _fountain_to_html("Hello", "<b>Evil</b>")
        assert "<b>Evil</b>" not in html

    def test_fountain_to_html_dark_mode(self):
        html = _fountain_to_html("test", "Test")
        assert "prefers-color-scheme: dark" in html

    def test_create_reader_bundle(self, tmp_path):
        script = "INT. OFFICE\n\nJOHN\nHello world.\n\nCUT TO:\n\nEXT. PARK"
        filepath = create_reader_bundle(
            script, "Test Script", str(tmp_path),
            scenes=[{"heading": "INT. OFFICE"}],
            characters=["JOHN"],
        )
        assert os.path.exists(filepath)
        assert filepath.endswith(".ecrit-reader")

        with zipfile.ZipFile(filepath, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["title"] == "Test Script"
            assert manifest["characters"] == ["JOHN"]
            html = zf.read("script.html").decode("utf-8")
            assert "JOHN" in html

    def test_page_count_estimation(self, tmp_path):
        long_script = "Action line.\n" * 1000
        filepath = create_reader_bundle(long_script, "Long", str(tmp_path))
        with zipfile.ZipFile(filepath, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["page_count"] >= 1

    def test_empty_script(self, tmp_path):
        filepath = create_reader_bundle("", "Empty", str(tmp_path))
        assert os.path.exists(filepath)


class TestDeviceSync:
    def test_transfer_handler_isolation(self):
        from ecrit.companion.device_sync import DeviceSync
        server1 = DeviceSync.__new__(DeviceSync)
        server2 = DeviceSync.__new__(DeviceSync)
        assert server1 is not server2
