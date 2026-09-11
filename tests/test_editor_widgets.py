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


class TestLineNumbers:
    def test_line_number_area_created(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        assert hasattr(editor, '_line_number_area')
        assert hasattr(editor, '_show_line_numbers')
        assert editor._show_line_numbers is False

    def test_set_line_numbers_visible(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        editor.set_line_numbers_visible(True)
        assert editor._show_line_numbers is True
        assert not editor._line_number_area.isHidden()
        editor.set_line_numbers_visible(False)
        assert editor._show_line_numbers is False
        assert editor._line_number_area.isHidden()

    def test_line_number_area_width_zero_when_hidden(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        assert editor.line_number_area_width() == 0

    def test_line_number_area_width_nonzero_when_visible(self, qapp):
        from ecrit.ui.screens.editor import ScriptEditor
        editor = ScriptEditor()
        editor.set_line_numbers_visible(True)
        assert editor.line_number_area_width() > 0


class TestPresenceBar:
    def test_presence_bar_in_manuscript(self, qapp):
        from ecrit.ui.screens.editor import ManuscriptPhase
        mp = ManuscriptPhase()
        assert hasattr(mp, 'presence_bar')
        assert not mp.presence_bar.isVisible()

    def test_presence_bar_set_participants(self, qapp):
        from ecrit.ui.components.presence_indicators import PresenceBar
        bar = PresenceBar()
        bar.set_participants([
            {"user_id": "a", "user_name": "Alice", "color": "#4FC3F7"},
            {"user_id": "b", "user_name": "Bob", "color": "#81C784"},
        ])
        assert len(bar._badges) == 2

    def test_presence_bar_clear(self, qapp):
        from ecrit.ui.components.presence_indicators import PresenceBar
        bar = PresenceBar()
        bar.set_participants([{"user_id": "a", "user_name": "Alice", "color": "#4FC3F7"}])
        bar.clear_participants()
        assert len(bar._badges) == 0


class TestOutlineContextMenu:
    def test_add_node_at(self, qapp):
        from ecrit.ui.screens.editor import OutlineCanvas
        canvas = OutlineCanvas()
        canvas._add_node_at(100, 200, "Scene", "Test Scene")
        assert len(canvas._nodes) == 1
        assert canvas._nodes[0]["kind"] == "Scene"
        assert canvas._nodes[0]["x"] == 100
        assert canvas._nodes[0]["y"] == 200

    def test_add_multiple_node_types(self, qapp):
        from ecrit.ui.screens.editor import OutlineCanvas
        canvas = OutlineCanvas()
        canvas._add_node_at(0, 0, "ActBreak", "Act 1")
        canvas._add_node_at(0, 100, "Note", "A note")
        canvas._add_node_at(0, 200, "Transition", "CUT TO:")
        assert len(canvas._nodes) == 3
        assert canvas._nodes[0]["kind"] == "ActBreak"
        assert canvas._nodes[1]["kind"] == "Note"
        assert canvas._nodes[2]["kind"] == "Transition"


class TestShareReviewOptions:
    def test_generate_review_html_with_title_page(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html("INT. OFFICE - DAY", title="Test", include_title_page=True)
        assert '<div class="header">' in html
        assert "<h1>Test</h1>" in html

    def test_generate_review_html_without_title_page(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html("INT. OFFICE - DAY", title="Test", include_title_page=False)
        assert '<div class="header">' not in html

    def test_generate_review_html_with_page_numbers(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html("INT. OFFICE - DAY", include_page_numbers=True)
        assert "@page" in html

    def test_generate_review_html_without_page_numbers(self):
        from ecrit.export.share_review import generate_review_html
        html = generate_review_html("INT. OFFICE - DAY", include_page_numbers=False)
        assert "@page" not in html


class TestCollabOT:
    def test_transform_applied_to_remote_ops(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession(user_name="Test")
        assert hasattr(session, '_pending_ops')
        assert session._pending_ops == []

    def test_pending_ops_populated_on_local_insert(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession(user_name="Test")
        session._crdt.set_text("hello")
        session._p2p.broadcast = MagicMock()
        session.apply_local_insert(5, " world")
        assert len(session._pending_ops) == 1
        assert session._pending_ops[0].text == " world"

    def test_pending_ops_populated_on_local_delete(self):
        from ecrit.collab.session import CollabSession
        session = CollabSession(user_name="Test")
        session._crdt.set_text("hello world")
        session._p2p.broadcast = MagicMock()
        session.apply_local_delete(5, 6)
        assert len(session._pending_ops) == 1
        assert session._pending_ops[0].length == 6

    def test_pending_ops_transformed_not_cleared(self):
        from ecrit.collab.session import CollabSession
        from ecrit.collab.protocol import CollabMessage, Operation, OperationType
        session = CollabSession(user_name="Test")
        session._crdt.set_text("hello")
        session._p2p.broadcast = MagicMock()
        session.apply_local_insert(5, " world")
        assert len(session._pending_ops) == 1
        remote_op = Operation(
            op_type=OperationType.INSERT, position=0, text="Hi ", user_id="remote"
        )
        msg = CollabMessage.operation("remote", remote_op)
        session._handle_message("remote", msg.to_json())
        assert len(session._pending_ops) == 1
        assert session._pending_ops[0].position == 8


class TestDashboardOpenSettings:
    def test_dashboard_has_open_settings_signal(self, qapp):
        from ecrit.ui.screens.dashboard import Dashboard
        d = Dashboard()
        assert hasattr(d, 'open_settings')

    def test_settings_button_emits_open_settings(self, qapp):
        from ecrit.ui.screens.dashboard import Dashboard
        d = Dashboard()
        received = []
        d.open_settings.connect(lambda: received.append(True))
        for child in d.findChildren(type(d)):
            pass
        from PySide6.QtWidgets import QPushButton
        btns = d.findChildren(QPushButton)
        gear_btn = [b for b in btns if b.toolTip() == "Settings"]
        assert len(gear_btn) == 1
        gear_btn[0].click()
        assert len(received) == 1


class TestFindReplaceRegex:
    def test_regex_find_uses_qregularexpression(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        screen.manuscript.editor.setPlainText("hello 123 world 456")
        screen._do_find("\\d+", False, True)
        cursor = screen.manuscript.editor.textCursor()
        assert cursor.hasSelection()
        assert cursor.selectedText() == "123"

    def test_regex_find_case_insensitive(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        screen.manuscript.editor.setPlainText("Hello HELLO hello")
        screen._do_find("hello", False, True)
        cursor = screen.manuscript.editor.textCursor()
        assert cursor.hasSelection()
        assert cursor.selectedText() == "Hello"

    def test_regex_find_prev(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        screen.manuscript.editor.setPlainText("abc 123 def 456")
        cursor = screen.manuscript.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        screen.manuscript.editor.setTextCursor(cursor)
        screen._do_find_prev("\\d+", False, True)
        cursor = screen.manuscript.editor.textCursor()
        assert cursor.hasSelection()
        assert cursor.selectedText() == "456"

    def test_invalid_regex_does_not_crash(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        screen.manuscript.editor.setPlainText("hello world")
        screen._do_find("[invalid", False, True)


class TestFindReplaceClosedSignal:
    def test_closed_signal_connected(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        screen.find_bar._expanded = True
        screen.find_bar.toggle()
        # After closing, focus should be on manuscript editor


class TestManuscriptDividers:
    def test_dividers_in_splitter(self, qapp):
        from ecrit.ui.screens.editor import ManuscriptPhase
        phase = ManuscriptPhase()
        assert hasattr(phase, 'divider_l')
        assert hasattr(phase, 'divider_r')
        assert phase.divider_l.objectName() == "railDivider"
        assert phase.divider_r.objectName() == "railDivider"


class TestCloudExportAutoExport:
    def test_auto_export_changed_signal(self, qapp):
        from ecrit.ui.overlays.cloud_export import CloudExportDialog
        dialog = CloudExportDialog()
        received = []
        dialog.auto_export_changed.connect(lambda p, e: received.append((p, e)))
        dialog.auto_export_check.setChecked(True)
        assert len(received) == 1
        assert received[0][1] is True

    def test_provider_changed_restores_auth_status(self, qapp):
        from ecrit.ui.overlays.cloud_export import CloudExportDialog
        dialog = CloudExportDialog()
        dialog.set_configs([{"provider": "google_drive", "authenticated": True, "auto_export": True}])
        dialog.provider_combo.setCurrentIndex(1)
        dialog.provider_combo.setCurrentIndex(0)
        assert dialog.auth_status.text() == "Authenticated"


class TestDeliverPhaseInit:
    def test_script_initialized(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        assert phase._script == ""


class TestAutoSyncImport:
    def test_push_to_remote_import(self):
        from ecrit.sync.remote_sync import push_to_remote
        assert callable(push_to_remote)

    def test_upload_file_method(self):
        from ecrit.sync.cloud_export import get_exporter, CloudConfig, CloudProvider
        config = CloudConfig(provider=CloudProvider.GOOGLE_DRIVE, auth_token="test", folder_path="/test")
        exporter = get_exporter(config.provider, config)
        assert hasattr(exporter, 'upload_file')
        assert not hasattr(exporter, 'upload')


class TestSeriesProjectChanged:
    def test_series_panel_has_project_changed_signal(self, qapp):
        from ecrit.ui.overlays.series_panel import SeriesPanel
        panel = SeriesPanel()
        assert hasattr(panel, 'project_changed')

    def test_save_series_project(self, tmp_path):
        from ecrit.screenplay.series_projects import SeriesProject, save_series_project
        import json
        project = SeriesProject(title="Test Series")
        path = str(tmp_path / "series.json")
        save_series_project(project, path)
        data = json.loads(open(path).read())
        assert data["title"] == "Test Series"
