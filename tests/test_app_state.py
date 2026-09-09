"""Tests for the central app state management."""

import os
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from ecrit.stores.app_state import AppState, STATE


class TestAppStateInit:
    def test_default_state(self):
        s = AppState()
        assert s.current_project_path is None
        assert s.current_phase == "Manuscript"
        assert s.script_content == ""
        assert s.projects == []
        assert s.theme == "dark"

    def test_default_project_folder(self):
        s = AppState()
        assert s.project_folder != ""
        assert "crit" in s.project_folder.lower() or "Écrit" in s.project_folder

    def test_custom_project_folder(self):
        s = AppState(project_folder="/custom/path")
        assert s.project_folder == "/custom/path"


class TestAppStateSubscription:
    def test_subscribe_and_notify(self):
        s = AppState()
        called = []
        s.subscribe(lambda: called.append(True))
        s.notify()
        assert len(called) == 1

    def test_multiple_subscribers(self):
        s = AppState()
        calls = {"a": 0, "b": 0}
        s.subscribe(lambda: calls.__setitem__("a", calls["a"] + 1))
        s.subscribe(lambda: calls.__setitem__("b", calls["b"] + 1))
        s.notify()
        assert calls["a"] == 1
        assert calls["b"] == 1

    def test_notify_without_subscribers(self):
        s = AppState()
        s.notify()  # should not raise


class TestPhaseManagement:
    def test_set_phase(self):
        s = AppState()
        s.set_phase("Plan")
        assert s.current_phase == "Plan"

    def test_set_phase_notifies(self):
        s = AppState()
        called = []
        s.subscribe(lambda: called.append(True))
        s.set_phase("Outline")
        assert len(called) == 1

    def test_all_phases(self):
        s = AppState()
        for phase in ("Plan", "Outline", "Manuscript", "Proofread", "Deliver"):
            s.set_phase(phase)
            assert s.current_phase == phase

    def test_set_invalid_phase_still_works(self):
        """AppState doesn't validate phase names — it's a plain store."""
        s = AppState()
        s.set_phase("Nonexistent")
        assert s.current_phase == "Nonexistent"


class TestThemeToggle:
    def test_toggle_from_dark(self):
        s = AppState()
        s.theme = "dark"
        s.toggle_theme()
        assert s.theme == "light"

    def test_toggle_from_light(self):
        s = AppState()
        s.theme = "light"
        s.toggle_theme()
        assert s.theme == "dark"

    def test_toggle_notifies(self):
        s = AppState()
        called = []
        s.subscribe(lambda: called.append(1))
        s.toggle_theme()
        assert len(called) == 1


class TestParseScript:
    def test_parse_empty_without_core(self):
        s = AppState()
        s.script_content = ""
        result = s.parse_script()
        assert result == {"elements": []}

    def test_parse_with_content_no_core(self):
        s = AppState()
        s.script_content = "INT. ROOM - DAY\n\nHello"
        with patch.object(type(s), 'parse_script', return_value={"elements": []}):
            pass
        result = s.parse_script()
        assert "elements" in result


class TestGetStats:
    def test_stats_empty_without_core(self):
        s = AppState()
        result = s.get_stats()
        assert result["word_count"] == 0
        assert result["page_count"] == 0
        assert result["scene_count"] == 0
        assert result["character_count"] == 0
        assert result["dialogue_percentage"] == 0
        assert result["action_percentage"] == 0
        assert result["characters"] == []
        assert result["scenes"] == []

    def test_stats_with_script(self):
        s = AppState()
        s.script_content = "Title: Test\n\nINT. OFFICE - DAY\n\nJOHN\nHello there.\n\nEXT. PARK - NIGHT\n\nAction line here.\n"
        result = s.get_stats()
        assert result["word_count"] > 0
        assert result["scene_count"] == 2
        assert result["page_count"] >= 1
        assert len(result["scenes"]) == 2
        assert result["scenes"][0]["heading"] == "INT. OFFICE - DAY"
        assert len(result["characters"]) >= 1


class TestSaveScript:
    def test_save_without_project_path(self):
        s = AppState()
        s.script_content = "test"
        s.save_script()  # should not raise

    def test_save_without_core(self):
        s = AppState()
        s.current_project_path = "/fake/path"
        s.script_content = "test"
        s.save_script()  # should not raise (ecrit_core may be None)


class TestSingletonState:
    def test_state_is_app_state(self):
        assert isinstance(STATE, AppState)

    def test_state_is_singleton_reference(self):
        from ecrit.stores.app_state import STATE as s2
        assert STATE is s2
