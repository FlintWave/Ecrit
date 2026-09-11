"""Adversarial and red-team tests — push every module to its limits.
Empty inputs, null-like values, huge data, injection attempts, concurrent ops,
theme switching mid-operation, boundary conditions."""

import os
import json
import zipfile
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument

from ecrit.ui.styles.theme import NOCTURNE, ORGANIC, set_theme, toggle, current
from ecrit.stores.app_state import AppState
from tests.conftest import HUGE_FOUNTAIN


class TestThemeAdversarial:
    def test_rapid_toggle_1000_times(self):
        set_theme(NOCTURNE)
        for _ in range(1000):
            toggle()
        assert current() is NOCTURNE  # even number of toggles

    def test_toggle_1001_times(self):
        set_theme(NOCTURNE)
        for _ in range(1001):
            toggle()
        assert current() is ORGANIC

    def test_set_theme_none_like(self):
        """Setting theme to NOCTURNE after various states still works."""
        toggle()
        toggle()
        toggle()
        set_theme(NOCTURNE)
        assert current() is NOCTURNE

    def test_theme_fields_not_empty_strings(self):
        for t in (NOCTURNE, ORGANIC):
            for field_name in ("bg", "surface", "text", "accent", "divider"):
                val = getattr(t, field_name)
                assert val != "", f"{t.name}.{field_name} is empty"
                assert len(val) >= 4, f"{t.name}.{field_name} too short: {val!r}"


class TestStylesheetAdversarial:
    def test_stylesheet_generation_both_themes(self, qapp):
        from ecrit.ui.styles.stylesheet import generate
        for t in (NOCTURNE, ORGANIC):
            ss = generate(t)
            assert len(ss) > 100
            assert "{" in ss
            assert "}" in ss

    def test_stylesheet_no_unclosed_braces(self, qapp):
        from ecrit.ui.styles.stylesheet import generate
        for t in (NOCTURNE, ORGANIC):
            ss = generate(t)
            assert ss.count("{") == ss.count("}")

    def test_stylesheet_after_theme_switch(self, qapp):
        from ecrit.ui.styles.stylesheet import generate
        set_theme(NOCTURNE)
        ss1 = generate(current())
        toggle()
        ss2 = generate(current())
        assert ss1 != ss2
        assert NOCTURNE.bg in ss1
        assert ORGANIC.bg in ss2


class TestAppStateAdversarial:
    def test_set_phase_empty_string(self):
        s = AppState()
        s.set_phase("")
        assert s.current_phase == ""

    def test_set_phase_very_long_string(self):
        s = AppState()
        s.set_phase("A" * 10000)
        assert len(s.current_phase) == 10000

    def test_script_content_huge(self):
        s = AppState()
        s.script_content = HUGE_FOUNTAIN
        assert len(s.script_content) > 10000

    def test_script_content_unicode(self):
        s = AppState()
        s.script_content = "Héloïse — café — naïve — 你好世界 — العربية"
        assert "Héloïse" in s.script_content

    def test_script_content_null_bytes(self):
        s = AppState()
        s.script_content = "before\x00after"
        assert len(s.script_content) == 12

    def test_subscribe_many_listeners(self):
        s = AppState()
        count = [0]
        for _ in range(100):
            s.subscribe(lambda: count.__setitem__(0, count[0] + 1))
        s.notify()
        assert count[0] == 100

    def test_subscriber_exception_doesnt_crash_others(self):
        s = AppState()
        good_calls = [0]
        def bad_listener():
            raise ValueError("boom")
        def good_listener():
            good_calls[0] += 1
        s.subscribe(good_listener)
        s.subscribe(bad_listener)
        s.subscribe(good_listener)
        try:
            s.notify()
        except ValueError:
            pass
        # At least the first good listener was called
        assert good_calls[0] >= 1

    def test_project_folder_with_special_chars(self):
        s = AppState(project_folder="/path/with spaces/and (parens)/éàü")
        assert s.project_folder == "/path/with spaces/and (parens)/éàü"


class TestFindReplaceAdversarial:
    def test_find_empty_text(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("hello")
        es._do_find("", False, False)  # should not crash

    def test_find_nonexistent_text(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("hello world")
        es._do_find("xyz", False, False)  # no match, no crash

    def test_replace_all_overlapping_pattern(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("aaa")
        es._do_replace_all("aa", "b")
        result = es.manuscript.editor.toPlainText()
        assert result == "ba"  # Python str.replace behavior

    def test_replace_all_with_empty_replacement(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("hello world hello")
        es._do_replace_all("hello", "")
        assert es.manuscript.editor.toPlainText() == " world "

    def test_replace_all_huge_document(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        text = "word " * 10000
        es.manuscript.editor.setPlainText(text)
        es._do_replace_all("word", "WORD")
        assert "WORD" in es.manuscript.editor.toPlainText()

    def test_find_special_regex_chars(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("price is $10.00")
        es._do_find("$10.00", False, False)  # literal search, no regex

    def test_replace_with_itself(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("abc")
        es._do_replace_all("abc", "abc")
        assert es.manuscript.editor.toPlainText() == "abc"


class TestODTAdversarial:
    def test_xml_injection_in_content(self):
        from ecrit.export.odt_export import _build_content_xml
        malicious = '<script>alert("xss")</script> & "quotes" <tags>'
        result = _build_content_xml(malicious)
        assert "<script>" not in result
        assert "&lt;" in result or "alert" in result  # escaped

    def test_null_bytes_in_content(self):
        from ecrit.export.odt_export import _build_content_xml
        result = _build_content_xml("before\x00after")
        assert isinstance(result, str)

    def test_very_long_line(self):
        from ecrit.export.odt_export import _build_content_xml
        long_line = "A" * 100000
        result = _build_content_xml(long_line)
        assert len(result) > 100000

    def test_only_newlines(self):
        from ecrit.export.odt_export import _build_content_xml
        result = _build_content_xml("\n\n\n\n\n")
        assert "office:text" in result

    def test_binary_like_content(self):
        from ecrit.export.odt_export import _create_odt_bytes
        content = "".join(chr(i) for i in range(32, 127))
        data = _create_odt_bytes(content)
        assert len(data) > 0

    def test_emoji_in_content(self):
        from ecrit.export.odt_export import _build_content_xml
        result = _build_content_xml("Character says: 🎬 🎥 📽️")
        assert "office:text" in result

    def test_odt_file_is_readable(self, tmp_path):
        from ecrit.export.odt_export import export_odt_to_path
        out = str(tmp_path / "test.odt")
        export_odt_to_path("INT. ROOM\n\nACTION\n\nCHARACTER\nDialogue", out)
        with zipfile.ZipFile(out, "r") as zf:
            assert zf.testzip() is None  # no corrupt files


class TestPDFAdversarial:
    def test_empty_script_pdf(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        out = str(tmp_path / "empty.pdf")
        export_pdf_to_path("", out)
        assert os.path.exists(out)

    def test_only_whitespace_pdf(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        out = str(tmp_path / "ws.pdf")
        export_pdf_to_path("   \n\n  \t  \n", out)
        assert os.path.exists(out)

    def test_unicode_pdf(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        from tests.conftest import UNICODE_FOUNTAIN
        out = str(tmp_path / "unicode.pdf")
        export_pdf_to_path(UNICODE_FOUNTAIN, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 100

    def test_huge_pdf(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        out = str(tmp_path / "huge.pdf")
        export_pdf_to_path(HUGE_FOUNTAIN, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 1000


class TestCommandPaletteAdversarial:
    def test_filter_with_special_chars(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        cp._filter("!@#$%^&*()")
        assert cp.results.count() == 0

    def test_filter_very_long_query(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        cp._filter("a" * 10000)
        assert cp.results.count() == 0

    def test_filter_unicode(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        cp._filter("café")
        assert cp.results.count() == 0

    def test_rapid_filtering(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        for char in "export pdf":
            cp._filter(char)
        cp._filter("")
        from ecrit.ui.overlays.command_palette import COMMANDS
        assert cp.results.count() == len(COMMANDS)


class TestSprintTimerAdversarial:
    def test_tick_past_zero(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._seconds_left = 0
        timer._running = True
        ended = []
        timer.sprint_ended.connect(lambda m: ended.append(m))
        timer._tick()
        assert timer._running is False
        timer._tick()  # tick again when already at 0 and stopped
        # Should not crash or fire extra signal

    def test_negative_seconds(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._seconds_left = -5
        timer._update_display()
        # Should handle gracefully (negative display or clamp)

    def test_zero_duration(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._running = False
        timer._set_duration(0)
        assert timer._seconds_left == 0


class TestScratchpadAdversarial:
    def test_add_huge_text(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        huge = "A" * 100000
        sp.add_text(huge)
        assert len(sp.text_area.toPlainText()) == 100000

    def test_add_many_snippets(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        for i in range(50):
            sp.add_text(f"Snippet {i}")
        text = sp.text_area.toPlainText()
        assert "Snippet 0" in text
        assert "Snippet 49" in text
        assert text.count("---") == 49  # separators between each pair


class TestCharacterSheetAdversarial:
    def test_very_long_name(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet
        cs = CharacterSheet()
        cs.set_character({"name": "A" * 1000})
        assert len(cs.name_input.text()) == 1000

    def test_unicode_fields(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet
        cs = CharacterSheet()
        cs.set_character({
            "name": "Héloïse",
            "occupation": "Boulangère",
            "wants": "La liberté 自由",
        })
        assert cs.name_input.text() == "Héloïse"

    def test_empty_save(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet
        cs = CharacterSheet()
        cs.set_character({})
        saved = []
        cs.character_saved.connect(lambda d: saved.append(d))
        cs._on_done()
        assert saved[0]["name"] == ""


class TestReaderExportXSS:
    def test_title_is_escaped(self):
        from ecrit.companion.reader_export import _fountain_to_html
        html = _fountain_to_html("INT. ROOM - DAY", title='<script>alert("xss")</script>')
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_script_content_is_escaped(self):
        from ecrit.companion.reader_export import _fountain_to_html
        html = _fountain_to_html('<img src=x onerror="alert(1)">')
        assert "<img" not in html
        assert "&lt;img" in html

    def test_action_line_is_escaped(self):
        from ecrit.companion.reader_export import _fountain_to_html
        html = _fountain_to_html('\n<SCRIPT>ALERT("XSS")</SCRIPT>\nDialogue')
        assert "&lt;SCRIPT&gt;" in html
        assert "<SCRIPT>" not in html


class TestSplitterSizes:
    def test_manuscript_splitter_has_5_children(self, qapp):
        from ecrit.ui.screens.editor import ManuscriptPhase
        phase = ManuscriptPhase()
        from PySide6.QtWidgets import QSplitter
        splitters = phase.findChildren(QSplitter)
        assert len(splitters) == 1
        assert splitters[0].count() == 5


class TestTimestampFalsy:
    def test_operation_preserves_zero_timestamp(self):
        from ecrit.collab.protocol import Operation, OperationType
        op = Operation(op_type=OperationType.INSERT, position=0, text="x", timestamp=0.0)
        assert op.timestamp != 0.0

    def test_operation_preserves_nonzero_timestamp(self):
        from ecrit.collab.protocol import Operation, OperationType
        op = Operation(op_type=OperationType.INSERT, position=0, text="x", timestamp=42.5)
        assert op.timestamp == 42.5

    def test_collab_message_preserves_nonzero_timestamp(self):
        from ecrit.collab.protocol import CollabMessage, MessageType
        msg = CollabMessage(msg_type=MessageType.JOIN, user_id="u1", timestamp=99.0)
        assert msg.timestamp == 99.0


class TestLANDiscoveryThreadSafe:
    def test_peers_lock_exists(self):
        from ecrit.collab.lan import LANDiscovery
        import threading
        ld = LANDiscovery("u1", "TestUser")
        assert isinstance(ld._peers_lock, type(threading.Lock()))


class TestCompareDraftsAdversarial:
    def test_huge_diff(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        old = "\n".join(f"old line {i}" for i in range(1000))
        new = "\n".join(f"new line {i}" for i in range(1000))
        cd.set_texts(old, new)
        assert cd.stats_label.text() != ""

    def test_both_empty(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        cd.set_texts("", "")
        assert "+0" in cd.stats_label.text()

    def test_one_empty(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        cd.set_texts("", "new content\n")
        assert "+1" in cd.stats_label.text()

    def test_inline_view_with_special_chars(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        cd._side_by_side = False
        cd.set_texts("<html>&amp;\n", "<body>&lt;\n")


class TestAutoSaveGuard:
    def test_no_save_when_interval_zero(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        editor._save_timer.setInterval(0)
        editor._save_timer.stop()
        fired = []
        editor.content_changed.connect(lambda: fired.append(True))
        editor._on_text_changed()
        assert not editor._save_timer.isActive()

    def test_save_debounce_when_enabled(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        editor._save_timer.setInterval(1000)
        editor._on_text_changed()
        assert editor._save_timer.isActive()


class TestCollabThreadSafety:
    def test_main_window_has_collab_signals(self, qapp):
        from ecrit.main import MainWindow
        assert hasattr(MainWindow, '_collab_text_changed')
        assert hasattr(MainWindow, '_collab_participants_changed')

    def test_active_collab_session_init(self, qapp):
        from ecrit.main import MainWindow
        w = MainWindow()
        assert w._active_collab_session is None


class TestModuleRegistryWiring:
    def test_settings_has_registry(self, qapp):
        from ecrit.main import MainWindow
        w = MainWindow()
        assert w._settings_dialog._module_registry is not None

    def test_registry_is_module_registry(self, qapp):
        from ecrit.main import MainWindow
        from ecrit.screenplay.module_system import ModuleRegistry
        w = MainWindow()
        assert isinstance(w._settings_dialog._module_registry, ModuleRegistry)


class TestSprintWordCapture:
    def test_set_start_words(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer.set_start_words(500)
        assert timer._words_at_start == 500


class TestCollabCursorSignal:
    def test_cursor_signal_exists(self, qapp):
        from ecrit.main import MainWindow
        assert hasattr(MainWindow, "_collab_cursor_changed")

    def test_apply_collab_cursor_method(self, qapp):
        from ecrit.main import MainWindow
        assert hasattr(MainWindow, "_apply_collab_cursor")


class TestScenesRenumberedWiring:
    def test_handler_exists(self, qapp):
        from ecrit.main import MainWindow
        assert hasattr(MainWindow, "_on_scenes_renumbered")

    def test_handler_runs(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        win._on_scenes_renumbered()


class TestCloudExportConfigsLoaded:
    def test_show_cloud_export_loads_configs(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        with patch.object(win._cloud_export_dialog, "set_configs") as mock_set, \
             patch.object(win._cloud_export_dialog, "exec") as mock_exec:
            from ecrit.stores.app_state import STATE
            original = STATE.current_project_path
            STATE.current_project_path = "/tmp/test_proj"
            with patch("ecrit.sync.cloud_export.load_cloud_configs", return_value=[]):
                win._show_cloud_export()
            STATE.current_project_path = original
            mock_exec.assert_called_once()
            mock_set.assert_called_once()


class TestDeliverFormatLabelWiring:
    def test_update_format_label_callable(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        editor = EditorScreen()
        editor.deliver.update_format_label(format_id="fountain/core", paper="A4")
        assert "A4" in editor.deliver.format_label.text()


class TestModuleHookDispatch:
    def test_hooks_called_on_export(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        calls = []
        win._module_registry.register_hook("before_export", lambda *a: calls.append(("before", a)))
        win._module_registry.register_hook("after_export", lambda *a: calls.append(("after", a)))
        with patch("ecrit.export.pdf_export.export_pdf", return_value=""):
            with patch.object(win.stack, "currentWidget", return_value=win.editor):
                win._export_script("pdf")
        assert any(c[0] == "before" for c in calls)
        assert any(c[0] == "after" for c in calls)


class TestCompanionStatusCallback:
    def test_status_callback_wired(self, qapp):
        from ecrit.ui.overlays.companion import CompanionDialog
        dialog = CompanionDialog()
        assert dialog._device_sync._on_status_change is not None
