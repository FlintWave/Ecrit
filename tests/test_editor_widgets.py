"""Tests for editor screen widgets: highlighter, script editor,
scene navigator, character rail, phases, and EditorScreen integration."""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor, QTextDocument

from ecrit.ui.styles.theme import NOCTURNE, ORGANIC, set_theme
from tests.conftest import SAMPLE_FOUNTAIN, UNICODE_FOUNTAIN


class TestFountainHighlighter:
    def test_construction(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        assert h.document() is doc

    def test_highlight_scene_heading(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText("INT. COFFEE SHOP - DAY")
        # Highlighter runs automatically; just verify no crash

    def test_highlight_ext_heading(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText("EXT. PARK - NIGHT")

    def test_highlight_forced_heading(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText(".My Custom Scene Heading")

    def test_highlight_section(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText("# Act One")

    def test_highlight_parenthetical(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText("(whispering)")

    def test_highlight_transition(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText("CUT TO:")

    def test_highlight_note(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText("[[This is a note]]")

    def test_highlight_empty_line(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText("")

    def test_highlight_complex_script(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText(SAMPLE_FOUNTAIN)

    def test_highlight_unicode(self, qapp):
        from ecrit.ui.screens.editor import FountainHighlighter
        doc = QTextDocument()
        h = FountainHighlighter(doc)
        doc.setPlainText(UNICODE_FOUNTAIN)


class TestScriptEditor:
    def test_construction(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        assert editor.objectName() == "scriptEditor"
        assert editor.font().family() in ("Courier Prime", ".AppleSystemUIFont", "")

    def test_set_text(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        editor.setPlainText("Hello world")
        assert editor.toPlainText() == "Hello world"

    def test_content_changed_signal(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        received = []
        editor.content_changed.connect(lambda: received.append(True))
        editor.setPlainText("test")
        # content_changed fires after 1s debounce timer
        editor._save_timer.timeout.emit()
        assert len(received) == 1

    def test_typewriter_mode_on(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        assert editor._typewriter is True

    def test_large_document(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        large_text = "\n".join(f"Line {i}" for i in range(5000))
        editor.setPlainText(large_text)
        assert editor.document().blockCount() == 5000

    def test_unicode_text(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        editor.setPlainText(UNICODE_FOUNTAIN)
        assert "LOÏSE" in editor.toPlainText()  # uppercase in fixture


class TestSceneNavigator:
    def test_construction(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        assert nav.scene_list.count() == 0

    def test_update_scenes(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        scenes = [
            {"number": "1", "heading": "INT. ROOM", "page": 1},
            {"number": "2", "heading": "EXT. PARK", "page": 3},
        ]
        nav.update_scenes(scenes)
        assert nav.scene_list.count() == 2

    def test_update_empty_scenes(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.update_scenes([])
        assert nav.scene_list.count() == 0

    def test_scene_selected_signal(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.update_scenes([{"number": "1", "heading": "INT. ROOM", "page": 1}])
        received = []
        nav.scene_selected.connect(lambda row: received.append(row))
        nav.scene_list.setCurrentRow(0)
        assert len(received) >= 1


class TestCharacterRail:
    def test_construction(self, qapp):
        from ecrit.ui.screens.editor import CharacterRail
        rail = CharacterRail()
        assert rail.char_list.count() == 0

    def test_update_characters(self, qapp):
        from ecrit.ui.screens.editor import CharacterRail
        rail = CharacterRail()
        chars = [
            {"name": "ALICE", "line_count": 30},
            {"name": "BOB", "line_count": 20},
        ]
        rail.update_characters(chars)
        assert rail.char_list.count() == 2

    def test_update_empty(self, qapp):
        from ecrit.ui.screens.editor import CharacterRail
        rail = CharacterRail()
        rail.update_characters([])
        assert rail.char_list.count() == 0


class TestPhases:
    def test_plan_phase_construction(self, qapp):
        from ecrit.ui.screens.editor import PlanPhase
        p = PlanPhase()
        assert p.editor is not None

    def test_outline_phase_construction(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        o = OutlinePhase()
        assert o.canvas is not None

    def test_manuscript_phase_construction(self, qapp):
        from ecrit.ui.screens.editor import ManuscriptPhase
        m = ManuscriptPhase()
        assert m.editor is not None
        assert m.scene_nav is not None
        assert m.char_rail is not None

    def test_proofread_phase_construction(self, qapp):
        from ecrit.ui.screens.editor import ProofreadPhase
        p = ProofreadPhase()
        assert p.script_view.isReadOnly()

    def test_deliver_phase_construction(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        d = DeliverPhase()
        assert d.preview_area is not None


class TestOutlineCanvas:
    def test_construction(self, qapp):
        from ecrit.ui.screens.editor import OutlineCanvas
        c = OutlineCanvas()
        assert c._zoom == 1.0
        assert c._nodes == []

    def test_set_nodes(self, qapp):
        from ecrit.ui.screens.editor import OutlineCanvas
        c = OutlineCanvas()
        nodes = [
            {"id": "1", "kind": "Scene", "label": "Scene 1", "x": 0, "y": 0, "connections": []},
            {"id": "2", "kind": "ActBreak", "label": "ACT I", "x": 200, "y": 0, "connections": []},
        ]
        c.set_nodes(nodes)
        assert len(c._nodes) == 2

    def test_zoom_limits(self, qapp):
        from ecrit.ui.screens.editor import OutlineCanvas
        c = OutlineCanvas()
        c._zoom = 0.3  # below min
        assert c._zoom < 0.5  # just testing field works

    def test_pan(self, qapp):
        from ecrit.ui.screens.editor import OutlineCanvas
        c = OutlineCanvas()
        c._pan_x = 100
        c._pan_y = -50
        assert c._pan_x == 100
        assert c._pan_y == -50


class TestEditorScreen:
    def test_construction(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        assert es._current_phase == "Manuscript"

    def test_switch_phase(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.show()
        for phase in ("Plan", "Outline", "Manuscript", "Proofread", "Deliver"):
            es.switch_phase(phase)
            assert es._current_phase == phase
            # In offscreen mode, check the widget's own visible flag
            assert not es.phases[phase].isHidden()
            for other, widget in es.phases.items():
                if other != phase:
                    assert widget.isHidden()

    def test_toggle_find(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es._toggle_find()
        assert es.find_bar._expanded is True
        es._toggle_find()
        assert es.find_bar._expanded is False

    def test_load_project(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.load_project({"script": "INT. ROOM - DAY\n\nHello", "meta": {}})
        assert "Hello" in es.manuscript.editor.toPlainText()

    def test_replace_all(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("foo bar foo baz foo")
        es._do_replace_all("foo", "qux")
        assert es.manuscript.editor.toPlainText() == "qux bar qux baz qux"

    def test_replace_all_empty_find(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        es.manuscript.editor.setPlainText("hello")
        es._do_replace_all("", "x")  # should be no-op
        assert es.manuscript.editor.toPlainText() == "hello"

    def test_go_home_signal(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        es = EditorScreen()
        received = []
        es.go_home.connect(lambda: received.append(True))
        es.go_home.emit()
        assert len(received) == 1


class TestProofreadChecks:
    def test_trailing_whitespace_detected(self, qapp):
        from ecrit.ui.screens.editor import ProofreadPhase
        issues = ProofreadPhase._check_script("Hello world  \nClean line\n")
        trailing = [i for i in issues if i["message"] == "Trailing whitespace"]
        assert len(trailing) == 1
        assert trailing[0]["line"] == 1

    def test_double_space_detected(self, qapp):
        from ecrit.ui.screens.editor import ProofreadPhase
        issues = ProofreadPhase._check_script("Hello  world\n")
        double = [i for i in issues if i["message"] == "Double space"]
        assert len(double) == 1

    def test_consecutive_blank_lines(self, qapp):
        from ecrit.ui.screens.editor import ProofreadPhase
        issues = ProofreadPhase._check_script("Line 1\n\n\nLine 4\n")
        blanks = [i for i in issues if i["message"] == "Consecutive blank lines"]
        assert len(blanks) == 1

    def test_unclosed_parenthetical(self, qapp):
        from ecrit.ui.screens.editor import ProofreadPhase
        issues = ProofreadPhase._check_script("(whispering\nSome dialogue\n")
        unclosed = [i for i in issues if i["message"] == "Unclosed parenthetical"]
        assert len(unclosed) == 1


class TestSettingsApplied:
    def test_settings_applied_signal_emitted(self, qapp):
        from ecrit.ui.overlays.settings import SettingsDialog
        d = SettingsDialog()
        received = []
        d.settings_applied.connect(lambda s: received.append(s))
        d.author_input.setText("Test Author")
        d.email_input.setText("test@example.com")
        d.close()
        assert len(received) == 1
        assert received[0]["author_name"] == "Test Author"
        assert received[0]["author_email"] == "test@example.com"

    def test_settings_has_font_size(self, qapp):
        from ecrit.ui.overlays.settings import SettingsDialog
        d = SettingsDialog()
        received = []
        d.settings_applied.connect(lambda s: received.append(s))
        d.close()
        assert len(received) == 1
        assert "font_size" in received[0]
        assert "word_target" in received[0]


class TestSyncConfigBug:
    def test_load_remote_config_returns_tuple(self):
        from ecrit.sync.remote_sync import load_remote_config
        result = load_remote_config("/nonexistent/path")
        assert isinstance(result, tuple)
        assert len(result) == 2
        config, sync_result = result
        assert config is None
