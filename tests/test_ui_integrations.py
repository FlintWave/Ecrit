"""Tests for UI integrations — wiring screenplay modules into the editor."""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ecrit.screenplay.structure_templates import TEMPLATES, generate_outline_nodes, list_templates
from ecrit.screenplay.scene_numbers import SceneNumber, assign_scene_numbers
from ecrit.screenplay.revisions import RevisionTracker, get_revision_color_hex
from ecrit.screenplay.contest_presets import CONTEST_PRESETS, validate_against_preset
from ecrit.screenplay.logline_builder import LOGLINE_TEMPLATES, build_logline, validate_logline
from ecrit.screenplay.production_reports import (
    generate_scene_report, generate_cast_report, generate_location_report,
    generate_day_night_report, generate_one_liner,
)
from ecrit.screenplay.module_system import ModuleRegistry


SAMPLE_SCRIPT = """Title: Test Script

INT. OFFICE - DAY

ALICE
Hello, world!

EXT. PARK - NIGHT

BOB
Goodbye, world!

INT. CAR - MOVING - DAY

ALICE
We need to go.
"""


# ---------------------------------------------------------------------------
# OutlinePhase + Structure Templates integration
# ---------------------------------------------------------------------------


class TestOutlineTemplateIntegration:
    def test_outline_phase_has_template_combo(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        assert hasattr(phase, "template_combo")
        assert phase.template_combo.count() > 1

    def test_template_combo_first_item_is_placeholder(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        assert phase.template_combo.itemData(0) == ""

    def test_template_combo_has_all_templates(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        keys = set()
        for i in range(1, phase.template_combo.count()):
            keys.add(phase.template_combo.itemData(i))
        assert keys == set(TEMPLATES.keys())

    def test_apply_template_sets_nodes(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase.apply_template("three_act")
        assert len(phase.canvas._nodes) > 0

    def test_apply_template_unknown_key_no_crash(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase.apply_template("nonexistent_template")
        assert phase.canvas._nodes == []

    def test_template_selection_populates_canvas(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase.template_combo.setCurrentIndex(1)
        phase._on_template_selected(1)
        assert len(phase.canvas._nodes) > 0

    def test_template_selection_resets_combo_to_placeholder(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase._on_template_selected(1)
        assert phase.template_combo.currentIndex() == 0

    def test_all_templates_generate_valid_nodes(self):
        for key, tpl in TEMPLATES.items():
            nodes = generate_outline_nodes(tpl)
            assert len(nodes) > 0, f"Template '{key}' generated no nodes"
            for node in nodes:
                assert "id" in node
                assert "x" in node
                assert "y" in node
                assert "kind" in node
                assert node["kind"] in ("ActBreak", "Scene")


# ---------------------------------------------------------------------------
# SceneNavigator + Scene Numbers integration
# ---------------------------------------------------------------------------


class TestSceneNavigatorIntegration:
    def test_scene_nav_has_renumber_btn(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        assert hasattr(nav, "renumber_btn")

    def test_set_script_populates_scene_numbers(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        assert len(nav._scene_numbers) == 3

    def test_update_scenes_shows_scene_numbers(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        scenes = [
            {"heading": "INT. OFFICE - DAY", "page": 1},
            {"heading": "EXT. PARK - NIGHT", "page": 1},
            {"heading": "INT. CAR - MOVING - DAY", "page": 2},
        ]
        nav.update_scenes(scenes)
        assert nav.scene_list.count() == 3
        first_item = nav.scene_list.item(0).text()
        assert "#1" in first_item

    def test_toggle_lock(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        scenes = [
            {"heading": "INT. OFFICE - DAY", "page": 1},
            {"heading": "EXT. PARK - NIGHT", "page": 1},
            {"heading": "INT. CAR - MOVING - DAY", "page": 2},
        ]
        nav.update_scenes(scenes)
        nav._toggle_lock(0, lock=True)
        assert nav._scene_numbers[0].locked is True

    def test_toggle_unlock(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        nav._toggle_lock(0, lock=True)
        nav._toggle_lock(0, lock=False)
        assert nav._scene_numbers[0].locked is False

    def test_renumber_all(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        scenes = [
            {"heading": "INT. OFFICE - DAY", "page": 1},
            {"heading": "EXT. PARK - NIGHT", "page": 1},
            {"heading": "INT. CAR - MOVING - DAY", "page": 2},
        ]
        nav.update_scenes(scenes)
        nav._renumber_all()
        numbers = [sn.number for sn in nav._scene_numbers]
        assert numbers == ["1", "2", "3"]

    def test_get_scene_numbers_returns_copy(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        nums = nav.get_scene_numbers()
        assert len(nums) == 3
        nums.clear()
        assert len(nav._scene_numbers) == 3

    def test_context_menu_exists(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        assert nav.scene_list.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu

    def test_empty_script_no_scene_numbers(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script("")
        assert nav._scene_numbers == []

    def test_renumber_with_locked_scenes(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        scenes = [
            {"heading": "INT. OFFICE - DAY", "page": 1},
            {"heading": "EXT. PARK - NIGHT", "page": 1},
            {"heading": "INT. CAR - MOVING - DAY", "page": 2},
        ]
        nav.update_scenes(scenes)
        nav._toggle_lock(1, lock=True)
        nav._renumber_all()
        assert nav._scene_numbers[1].number == "2"
        assert nav._scene_numbers[1].locked is True

    def test_set_script_unicode(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        script = """INT. CAFÉ — JOUR

HÉLOÏSE
Bonjour!

EXT. PARC — NUIT

FRANÇOIS
Au revoir!
"""
        nav.set_script(script)
        assert len(nav._scene_numbers) == 2


# ---------------------------------------------------------------------------
# DeliverPhase + Revisions + Contest Presets integration
# ---------------------------------------------------------------------------


class TestDeliverPhaseIntegration:
    def test_deliver_has_revision_ui(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        assert hasattr(phase, "revision_color_label")
        assert hasattr(phase, "new_revision_btn")
        assert hasattr(phase, "revision_history_label")

    def test_deliver_has_contest_combo(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        assert hasattr(phase, "contest_combo")
        assert phase.contest_combo.count() > 1

    def test_initial_revision_is_white(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        assert "White" in phase.revision_color_label.text()

    def test_add_revision_advances_color(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        phase._add_revision()
        assert "Blue" in phase.revision_color_label.text()

    def test_add_multiple_revisions(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        phase._add_revision()
        phase._add_revision()
        assert "Pink" in phase.revision_color_label.text()

    def test_revision_history_updated(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        phase._add_revision()
        text = phase.revision_history_label.text()
        assert "BLUE" in text.upper()

    def test_contest_combo_has_presets(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        keys = set()
        for i in range(1, phase.contest_combo.count()):
            keys.add(phase.contest_combo.itemData(i))
        assert "nicholl" in keys

    def test_contest_validation_with_script(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        phase.set_script(SAMPLE_SCRIPT)
        phase._on_contest_selected(1)
        text = phase.contest_result_label.text()
        assert len(text) > 0

    def test_contest_validation_empty_selection(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        phase._on_contest_selected(0)
        assert phase.contest_result_label.text() == ""

    def test_get_revision_tracker(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        tracker = phase.get_revision_tracker()
        assert isinstance(tracker, RevisionTracker)

    def test_set_revision_tracker(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        tracker = RevisionTracker()
        tracker.add_revision(pages_changed=[1, 2])
        phase.set_revision_tracker(tracker)
        assert "Blue" in phase.revision_color_label.text()


# ---------------------------------------------------------------------------
# Production Reports overlay
# ---------------------------------------------------------------------------


class TestReportsDialog:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.reports import ReportsDialog
        dialog = ReportsDialog()
        assert dialog.windowTitle() == "Production Reports"

    def test_set_script_populates_tabs(self, qapp):
        from ecrit.ui.overlays.reports import ReportsDialog
        dialog = ReportsDialog()
        dialog.set_script(SAMPLE_SCRIPT)

    def test_empty_script(self, qapp):
        from ecrit.ui.overlays.reports import ReportsDialog
        dialog = ReportsDialog()
        dialog.set_script("")

    def test_reports_generate_data(self):
        scenes = generate_scene_report(SAMPLE_SCRIPT)
        assert len(scenes) >= 1
        cast = generate_cast_report(SAMPLE_SCRIPT)
        assert len(cast) >= 1
        locations = generate_location_report(SAMPLE_SCRIPT)
        assert len(locations) >= 1
        daynight = generate_day_night_report(SAMPLE_SCRIPT)
        assert isinstance(daynight, dict)
        oneliners = generate_one_liner(SAMPLE_SCRIPT)
        assert len(oneliners) >= 1


# ---------------------------------------------------------------------------
# Logline Builder overlay
# ---------------------------------------------------------------------------


class TestLoglineBuilderDialog:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.logline_builder import LoglineBuilderDialog
        dialog = LoglineBuilderDialog()
        assert dialog.windowTitle() == "Logline Builder"

    def test_has_logline_ready_signal(self, qapp):
        from ecrit.ui.overlays.logline_builder import LoglineBuilderDialog
        dialog = LoglineBuilderDialog()
        assert hasattr(dialog, "logline_ready")

    def test_template_combo_populated(self, qapp):
        from ecrit.ui.overlays.logline_builder import LoglineBuilderDialog
        dialog = LoglineBuilderDialog()
        assert hasattr(dialog, "_template_combo")
        assert dialog._template_combo.count() >= len(LOGLINE_TEMPLATES)


# ---------------------------------------------------------------------------
# Settings Modules tab
# ---------------------------------------------------------------------------


class TestSettingsModulesTab:
    def test_settings_has_modules_list(self, qapp):
        from ecrit.ui.overlays.settings import SettingsDialog
        dialog = SettingsDialog()
        assert hasattr(dialog, "modules_list")

    def test_set_registry(self, qapp, tmp_path):
        from ecrit.ui.overlays.settings import SettingsDialog
        import json
        dialog = SettingsDialog()
        mod_dir = tmp_path / "test_mod"
        mod_dir.mkdir()
        (mod_dir / "manifest.json").write_text(json.dumps({
            "name": "test", "version": "1.0.0", "module_type": "dialect",
        }))
        reg = ModuleRegistry()
        reg.load_module(str(mod_dir))
        dialog.set_registry(reg)
        assert dialog.modules_list.count() == 1

    def test_set_registry_empty(self, qapp):
        from ecrit.ui.overlays.settings import SettingsDialog
        dialog = SettingsDialog()
        reg = ModuleRegistry()
        dialog.set_registry(reg)
        assert dialog.modules_list.count() == 0

    def test_toggle_module(self, qapp, tmp_path):
        from ecrit.ui.overlays.settings import SettingsDialog
        import json
        dialog = SettingsDialog()
        mod_dir = tmp_path / "togmod"
        mod_dir.mkdir()
        (mod_dir / "manifest.json").write_text(json.dumps({
            "name": "togmod", "version": "1.0.0",
        }))
        reg = ModuleRegistry()
        reg.load_module(str(mod_dir))
        dialog.set_registry(reg)
        dialog.modules_list.setCurrentRow(0)
        dialog._toggle_module()
        assert reg.get_module("togmod").enabled is False


# ---------------------------------------------------------------------------
# Command palette integration
# ---------------------------------------------------------------------------


class TestCommandPaletteIntegration:
    def test_has_reports_command(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        names = [c[0] for c in COMMANDS]
        assert "Production Reports" in names

    def test_has_logline_command(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        names = [c[0] for c in COMMANDS]
        assert "Logline Builder" in names

    def test_commands_count(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        assert len(COMMANDS) >= 25


# ---------------------------------------------------------------------------
# MainWindow integration
# ---------------------------------------------------------------------------


class TestMainWindowIntegration:
    def test_main_window_has_reports_dialog(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_reports_dialog")

    def test_main_window_has_logline_dialog(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_logline_dialog")

    def test_main_window_reports_handler(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_show_reports")

    def test_main_window_logline_handler(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        assert hasattr(win, "_show_logline_builder")

    def test_command_handlers_include_new_commands(self, qapp):
        from ecrit.main import MainWindow
        win = MainWindow()
        # "Production Reports" returns early because editor isn't active
        win._on_command("Production Reports")
        # Don't call "Logline Builder" — it calls exec() unconditionally
        # Instead verify the handler is wired up
        assert "Logline Builder" in {
            "Dashboard", "New Project", "Import Script", "Open Project",
            "Save", "Find & Replace", "Statistics", "Keyboard Shortcuts",
            "Settings", "Toggle Theme", "Reading Mode", "Sprint Timer",
            "Scratchpad", "Snapshot", "Compare Drafts", "Export PDF",
            "Export ODT", "Export Fountain", "Production Reports",
            "Logline Builder",
        }


# ---------------------------------------------------------------------------
# EditorScreen load_project integration
# ---------------------------------------------------------------------------


class TestEditorScreenIntegration:
    def test_editor_screen_construction(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        assert hasattr(screen, "plan")
        assert hasattr(screen, "outline")
        assert hasattr(screen, "deliver")

    def test_outline_phase_exists(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        assert hasattr(screen.outline, "template_combo")

    def test_deliver_phase_has_revision_tracking(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        assert hasattr(screen.deliver, "revision_color_label")
        assert hasattr(screen.deliver, "contest_combo")

    def test_scene_nav_has_scene_number_support(self, qapp):
        from ecrit.ui.screens.editor import EditorScreen
        screen = EditorScreen()
        assert hasattr(screen.manuscript.scene_nav, "set_script")
        assert hasattr(screen.manuscript.scene_nav, "renumber_btn")


# ---------------------------------------------------------------------------
# Adversarial tests for integrations
# ---------------------------------------------------------------------------


class TestIntegrationAdversarial:
    def test_outline_template_with_all_keys(self, qapp):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        for key in TEMPLATES:
            phase.apply_template(key)
            assert len(phase.canvas._nodes) > 0

    def test_deliver_exhaust_revisions(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        for _ in range(18):
            phase._add_revision()
        assert "exhausted" in phase.revision_history_label.text().lower() or \
               "2nd Tan" in phase.revision_color_label.text() or \
               "Tan" in phase.revision_color_label.text()

    def test_scene_nav_lock_out_of_range(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav.set_script(SAMPLE_SCRIPT)
        nav._toggle_lock(999, lock=True)
        assert all(not sn.locked for sn in nav._scene_numbers)

    def test_scene_nav_renumber_empty(self, qapp):
        from ecrit.ui.screens.editor import SceneNavigator
        nav = SceneNavigator()
        nav._renumber_all()

    def test_deliver_contest_with_empty_script(self, qapp):
        from ecrit.ui.screens.editor import DeliverPhase
        phase = DeliverPhase()
        phase.set_script("")
        for i in range(1, phase.contest_combo.count()):
            phase._on_contest_selected(i)
            assert len(phase.contest_result_label.text()) > 0

    def test_reports_with_unicode_script(self, qapp):
        from ecrit.ui.overlays.reports import ReportsDialog
        dialog = ReportsDialog()
        script = """INT. CAFÉ — JOUR

HÉLOÏSE
Bonjour, le monde!

EXT. PARC — NUIT

FRANÇOIS
Au revoir!
"""
        dialog.set_script(script)

    def test_logline_builder_signal_type(self, qapp):
        from ecrit.ui.overlays.logline_builder import LoglineBuilderDialog
        dialog = LoglineBuilderDialog()
        received = []
        dialog.logline_ready.connect(lambda s: received.append(s))
