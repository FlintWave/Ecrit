"""Tests for all overlay widgets: find/replace, stats, shortcuts, settings,
command palette, sprint timer, reading mode, scratchpad, character sheet,
compare drafts, snapshots."""

import os
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from ecrit.ui.styles.theme import NOCTURNE, ORGANIC, set_theme
from tests.conftest import SAMPLE_FOUNTAIN


class TestFindReplaceBar:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        assert bar.height() == 0  # starts collapsed

    def test_toggle_expand(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        bar.toggle()
        assert bar._expanded is True
        assert bar.height() == 110

    def test_toggle_collapse(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        bar.toggle()
        bar.toggle()
        assert bar._expanded is False
        assert bar.height() == 0

    def test_find_next_signal(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        received = []
        bar.find_next.connect(lambda t, c, r: received.append((t, c, r)))
        bar.find_input.setText("test")
        bar._on_find_next()
        assert len(received) == 1
        assert received[0][0] == "test"

    def test_find_prev_signal(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        received = []
        bar.find_prev.connect(lambda t, c, r: received.append((t, c, r)))
        bar.find_input.setText("hello")
        bar.case_check.setChecked(True)
        bar._on_find_prev()
        assert received[0] == ("hello", True, False)

    def test_replace_signals(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        replace_one_calls = []
        replace_all_calls = []
        bar.replace_one.connect(lambda f, r: replace_one_calls.append((f, r)))
        bar.replace_all.connect(lambda f, r: replace_all_calls.append((f, r)))
        bar.find_input.setText("old")
        bar.replace_input.setText("new")
        bar._on_replace_one()
        bar._on_replace_all()
        assert replace_one_calls == [("old", "new")]
        assert replace_all_calls == [("old", "new")]

    def test_set_match_count(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        bar.set_match_count(3, 10)
        assert bar.match_label.text() == "3 / 10"

    def test_set_match_count_zero(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        bar.set_match_count(0, 0)
        assert bar.match_label.text() == "0 / 0"

    def test_closed_signal_on_collapse(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        closed_calls = []
        bar.closed.connect(lambda: closed_calls.append(True))
        bar.toggle()  # expand
        bar.toggle()  # collapse
        assert len(closed_calls) == 1

    def test_regex_checkbox(self, qapp):
        from ecrit.ui.overlays.find_replace import FindReplaceBar
        bar = FindReplaceBar()
        received = []
        bar.find_next.connect(lambda t, c, r: received.append((t, c, r)))
        bar.find_input.setText("pattern")
        bar.regex_check.setChecked(True)
        bar._on_find_next()
        assert received[0] == ("pattern", False, True)


class TestStatsDialog:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.statistics import StatsDialog
        dlg = StatsDialog()
        assert dlg.windowTitle() == "Statistics"

    def test_set_stats(self, qapp):
        from ecrit.ui.overlays.statistics import StatsDialog
        dlg = StatsDialog()
        dlg.set_stats({
            "page_count": 42,
            "word_count": 12345,
            "scene_count": 15,
            "character_count": 7,
            "dialogue_percentage": 55.5,
            "action_percentage": 44.5,
            "characters": [
                {"name": "ALICE", "line_count": 30, "word_count": 500},
                {"name": "BOB", "line_count": 20, "word_count": 300},
            ],
            "scenes": [
                {"heading": "INT. ROOM", "word_count": 200, "page": 1},
            ],
        })
        assert dlg.stat_rows["pages"]._val_label.text() == "42"
        assert dlg.stat_rows["words"]._val_label.text() == "12,345"
        assert dlg.char_table.rowCount() == 2
        assert dlg.scene_table.rowCount() == 1

    def test_set_empty_stats(self, qapp):
        from ecrit.ui.overlays.statistics import StatsDialog
        dlg = StatsDialog()
        dlg.set_stats({})
        assert dlg.stat_rows["pages"]._val_label.text() == "0"
        assert dlg.char_table.rowCount() == 0

    def test_stat_row_update(self, qapp):
        from ecrit.ui.overlays.statistics import StatRow
        row = StatRow("Test", "initial")
        assert row._val_label.text() == "initial"
        row.set_value("updated")
        assert row._val_label.text() == "updated"


class TestShortcutsDialog:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.shortcuts import ShortcutsDialog
        dlg = ShortcutsDialog()
        assert dlg.windowTitle() == "Keyboard Shortcuts"
        assert dlg.minimumWidth() >= 400


class TestSettingsDialog:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.settings import SettingsDialog
        dlg = SettingsDialog()
        assert dlg.windowTitle() == "Settings"

    def test_has_theme_changed_signal(self, qapp):
        from ecrit.ui.overlays.settings import SettingsDialog
        dlg = SettingsDialog()
        called = []
        dlg.theme_changed.connect(lambda: called.append(True))


class TestCommandPalette:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette, COMMANDS
        cp = CommandPalette()
        assert cp.results.count() == len(COMMANDS)

    def test_filter_narrows_results(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        cp._filter("export")
        assert cp.results.count() < 22
        assert cp.results.count() >= 3  # PDF, ODT, Fountain

    def test_filter_empty_restores_all(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette, COMMANDS
        cp = CommandPalette()
        cp._filter("export")
        cp._filter("")
        assert cp.results.count() == len(COMMANDS)

    def test_filter_no_match(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        cp._filter("xyznonexistent")
        assert cp.results.count() == 0

    def test_command_selected_signal(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        received = []
        cp.command_selected.connect(lambda name: received.append(name))
        item = cp.results.item(0)
        cp._on_select(item)
        assert len(received) == 1

    def test_filter_case_insensitive(self, qapp):
        from ecrit.ui.overlays.command_palette import CommandPalette
        cp = CommandPalette()
        cp._filter("EXPORT")
        assert cp.results.count() >= 3

    def test_all_commands_have_category(self, qapp):
        from ecrit.ui.overlays.command_palette import COMMANDS
        valid_cats = {"file", "nav", "phase", "tool", "export"}
        for name, cat, desc in COMMANDS:
            assert cat in valid_cats, f"Command {name!r} has invalid category {cat!r}"

    def test_all_commands_have_description(self, qapp):
        from ecrit.ui.overlays.command_palette import COMMANDS
        for name, cat, desc in COMMANDS:
            assert desc, f"Command {name!r} missing description"


class TestSprintTimer:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        assert timer._seconds_left == 25 * 60
        assert timer._running is False

    def test_set_duration(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._set_duration(15)
        assert timer._seconds_left == 15 * 60
        assert timer._total_seconds == 15 * 60

    def test_set_duration_while_running_ignored(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._running = True
        timer._set_duration(45)
        assert timer._seconds_left == 25 * 60  # unchanged

    def test_toggle_start(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._toggle()
        assert timer._running is True
        assert timer.start_btn.text() == "Pause"
        timer._timer.stop()  # cleanup

    def test_toggle_pause(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._toggle()  # start
        timer._toggle()  # pause
        assert timer._running is False
        assert timer.start_btn.text() == "Resume"

    def test_reset(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._set_duration(15)
        timer._toggle()  # start
        timer._seconds_left = 100  # simulate time passing
        timer._reset()
        assert timer._running is False
        assert timer._seconds_left == 15 * 60
        assert timer.start_btn.text() == "Start"

    def test_tick_decrements(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._set_duration(1)  # 1 minute
        timer._seconds_left = 5
        timer._tick()
        assert timer._seconds_left == 4

    def test_tick_at_zero_fires_signal(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._set_duration(25)
        timer._seconds_left = 0
        timer._running = True
        ended = []
        timer.sprint_ended.connect(lambda mins: ended.append(mins))
        timer._tick()
        assert len(ended) == 1
        assert ended[0] == 25
        assert timer._running is False

    def test_display_format(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._seconds_left = 65
        timer._update_display()
        assert timer.time_label.text() == "01:05"

    def test_display_zero(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._seconds_left = 0
        timer._update_display()
        assert timer.time_label.text() == "00:00"

    def test_status_text_when_running(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._running = True
        timer._seconds_left = 130
        text = timer.get_status_text()
        assert "02:10" in text

    def test_status_text_when_stopped(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        timer = SprintTimerWidget()
        timer._running = False
        assert timer.get_status_text() == ""

    def test_presets(self, qapp):
        from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
        assert SprintTimerWidget.PRESETS == [15, 25, 45]


class TestReadingMode:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.reading_mode import ReadingMode
        rm = ReadingMode()
        assert rm.text_view.isReadOnly()

    def test_set_content(self, qapp):
        from ecrit.ui.overlays.reading_mode import ReadingMode
        rm = ReadingMode()
        rm.set_content("Hello world", page=3, total_pages=10)
        assert rm.text_view.toPlainText() == "Hello world"
        assert "3" in rm.page_label.text()
        assert "10" in rm.page_label.text()

    def test_exit_signal(self, qapp):
        from ecrit.ui.overlays.reading_mode import ReadingMode
        rm = ReadingMode()
        exited = []
        rm.exit_requested.connect(lambda: exited.append(True))
        rm.exit_requested.emit()
        assert len(exited) == 1

    def test_empty_content(self, qapp):
        from ecrit.ui.overlays.reading_mode import ReadingMode
        rm = ReadingMode()
        rm.set_content("")
        assert rm.text_view.toPlainText() == ""

    def test_unicode_content(self, qapp):
        from ecrit.ui.overlays.reading_mode import ReadingMode
        rm = ReadingMode()
        rm.set_content("Héloïse — café — naïve")
        assert "Héloïse" in rm.text_view.toPlainText()


class TestScratchpad:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        assert sp.width() == 300

    def test_add_text(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        sp.add_text("first")
        assert sp.text_area.toPlainText() == "first"

    def test_add_text_appends_with_separator(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        sp.add_text("first")
        sp.add_text("second")
        text = sp.text_area.toPlainText()
        assert "first" in text
        assert "second" in text
        assert "---" in text

    def test_paste_signal(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        sp.add_text("clipboard text")
        received = []
        sp.paste_requested.connect(lambda t: received.append(t))
        sp._on_paste()
        assert received == ["clipboard text"]

    def test_paste_empty(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        received = []
        sp.paste_requested.connect(lambda t: received.append(t))
        sp._on_paste()
        assert received == []  # no signal for empty

    def test_clear(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        sp.add_text("some text")
        sp._on_clear()
        assert sp.text_area.toPlainText() == ""

    def test_closed_signal(self, qapp):
        from ecrit.ui.overlays.scratchpad import Scratchpad
        sp = Scratchpad()
        closed = []
        sp.closed.connect(lambda: closed.append(True))
        sp.closed.emit()
        assert len(closed) == 1


class TestCharacterSheet:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet
        cs = CharacterSheet()
        assert cs.windowTitle() == "Character Sheet"

    def test_set_character(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet
        cs = CharacterSheet()
        data = {
            "name": "ALICE",
            "age": "32",
            "pronouns": "she/her",
            "occupation": "Detective",
            "wants": "Justice",
            "voice": "Sharp, witty",
            "arc": "From cynicism to hope",
            "relationships": "Bob (partner)",
            "notes": "Based on real person",
            "role": "Protagonist",
            "scene_count": 15,
            "line_count": 120,
        }
        cs.set_character(data)
        assert cs.name_input.text() == "ALICE"
        assert cs.age_input.text() == "32"
        assert cs.pronouns_input.text() == "she/her"
        assert cs.occupation_input.text() == "Detective"
        assert "Justice" in cs.wants_input.toPlainText()
        assert cs.role_tag.text() == "Protagonist"
        assert "15" in cs.scenes_label.text()

    def test_save_signal(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet
        cs = CharacterSheet()
        cs.set_character({"name": "BOB"})
        cs.name_input.setText("ROBERT")
        saved = []
        cs.character_saved.connect(lambda d: saved.append(d))
        cs._on_done()
        assert len(saved) == 1
        assert saved[0]["name"] == "ROBERT"

    def test_empty_character(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet
        cs = CharacterSheet()
        cs.set_character({})
        assert cs.name_input.text() == ""
        assert cs.role_tag.isVisible() is False

    def test_moodboard_tiles_exist(self, qapp):
        from ecrit.ui.overlays.character_sheet import CharacterSheet, MoodboardTile
        cs = CharacterSheet()
        tiles = cs.findChildren(MoodboardTile)
        assert len(tiles) == 6


class TestCompareDrafts:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        assert cd.windowTitle() == "Compare Drafts"

    def test_set_texts(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        cd.set_texts("line one\nline two\n", "line one\nline three\n")
        assert "1" in cd.stats_label.text()  # at least one addition/deletion

    def test_set_identical_texts(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        cd.set_texts("same\n", "same\n")
        assert "+0" in cd.stats_label.text()
        assert "-0" in cd.stats_label.text()

    def test_toggle_view_mode(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        cd.set_texts("a\n", "b\n")
        assert cd._side_by_side is True
        cd._toggle_view()
        assert cd._side_by_side is False
        cd._toggle_view()
        assert cd._side_by_side is True

    def test_set_snapshots(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        snapshots = [
            {"hash": "abc123", "label": "Snapshot 1", "date": "2024-01-01"},
            {"hash": "def456", "label": "Snapshot 2", "date": "2024-01-02"},
            {"hash": "ghi789", "label": "Snapshot 3", "date": "2024-01-03"},
        ]
        cd.set_snapshots(snapshots)
        assert cd.from_select.count() == 3
        assert cd.to_select.count() == 3

    def test_empty_snapshots(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        cd.set_snapshots([])
        assert cd.from_select.count() == 0

    def test_large_diff(self, qapp):
        from ecrit.ui.overlays.compare_drafts import CompareDrafts
        cd = CompareDrafts()
        old = "\n".join(f"line {i}" for i in range(100))
        new = "\n".join(f"line {i}" for i in range(50, 150))
        cd.set_texts(old, new)
        assert cd.stats_label.text() != ""


class TestSnapshotsDialog:
    def test_construction(self, qapp):
        from ecrit.ui.overlays.snapshots import SnapshotsDialog
        dlg = SnapshotsDialog()
        assert dlg.windowTitle() == "Snapshots"

    def test_set_project(self, qapp, tmp_path):
        from ecrit.ui.overlays.snapshots import SnapshotsDialog
        dlg = SnapshotsDialog()
        dlg.set_project(str(tmp_path))
        assert dlg._project_path == str(tmp_path)
