"""Tests for plugin API and marketplace."""

import json
import os
import pytest

from ecrit.plugins.api import PluginAPI, PluginHook, PluginContext
from ecrit.plugins.marketplace import (
    Marketplace, PluginListing, PluginCategory, _sanitize_plugin_id,
)


class TestPluginAPI:
    def test_initial_context(self):
        api = PluginAPI()
        ctx = api.get_context()
        assert ctx.script_content == ""
        assert ctx.language == "en"

    def test_set_context(self):
        api = PluginAPI()
        api.set_context(project_path="/tmp/test", script_content="hello", phase="Manuscript")
        ctx = api.get_context()
        assert ctx.project_path == "/tmp/test"
        assert ctx.script_content == "hello"
        assert ctx.phase == "Manuscript"

    def test_set_context_ignores_unknown_keys(self):
        api = PluginAPI()
        api.set_context(nonexistent_field="value")
        ctx = api.get_context()
        assert not hasattr(ctx, "nonexistent_field")

    def test_register_and_call_hook(self):
        api = PluginAPI()
        results = []
        api.register_hook(PluginHook.BEFORE_SAVE, lambda: results.append("saved"))
        api.call_hook(PluginHook.BEFORE_SAVE)
        assert results == ["saved"]

    def test_call_hook_returns_values(self):
        api = PluginAPI()
        api.register_hook(PluginHook.ON_PARSE, lambda x: x * 2)
        ret = api.call_hook(PluginHook.ON_PARSE, 5)
        assert ret == [10]

    def test_unregister_hook(self):
        api = PluginAPI()
        cb = lambda: "x"
        api.register_hook(PluginHook.AFTER_SAVE, cb)
        api.unregister_hook(PluginHook.AFTER_SAVE, cb)
        assert api.call_hook(PluginHook.AFTER_SAVE) == []

    def test_hook_exception_logged_not_raised(self):
        api = PluginAPI()
        api.register_hook(PluginHook.BEFORE_SAVE, lambda: 1 / 0)
        api.register_hook(PluginHook.BEFORE_SAVE, lambda: "ok")
        results = api.call_hook(PluginHook.BEFORE_SAVE)
        assert results == ["ok"]

    def test_register_command(self):
        api = PluginAPI()
        cb = lambda: None
        api.register_command("test_cmd", "A test command", cb)
        cmds = api.get_commands()
        assert len(cmds) == 1
        assert cmds[0][0] == "test_cmd"
        assert cmds[0][2] is cb

    def test_register_panel(self):
        api = PluginAPI()
        widget = object()
        api.register_panel("Test Panel", widget)
        panels = api.get_panels()
        assert len(panels) == 1
        assert panels[0] == ("Test Panel", widget)

    def test_get_script_shortcut(self):
        api = PluginAPI()
        api.set_context(script_content="INT. OFFICE")
        assert api.get_script() == "INT. OFFICE"

    def test_get_project_path_shortcut(self):
        api = PluginAPI()
        api.set_context(project_path="/projects/test")
        assert api.get_project_path() == "/projects/test"


class TestPluginListing:
    def test_to_dict_roundtrip(self):
        listing = PluginListing(
            id="test-plugin", name="Test", version="1.0.0",
            author="Dev", category=PluginCategory.EXPORT,
            tags=["export", "pdf"],
        )
        d = listing.to_dict()
        restored = PluginListing.from_dict(d)
        assert restored.id == "test-plugin"
        assert restored.name == "Test"
        assert restored.category == PluginCategory.EXPORT
        assert restored.tags == ["export", "pdf"]

    def test_from_dict_defaults(self):
        listing = PluginListing.from_dict({})
        assert listing.id == ""
        assert listing.version == "0.0.0"
        assert listing.category == PluginCategory.TOOL

    def test_from_dict_invalid_category_defaults(self):
        listing = PluginListing.from_dict({"category": "nonexistent"})
        assert listing.category == PluginCategory.TOOL


class TestSanitizePluginId:
    def test_valid_id(self):
        assert _sanitize_plugin_id("my-plugin") == "my-plugin"

    def test_empty_id(self):
        assert _sanitize_plugin_id("") == ""

    def test_path_traversal(self):
        assert _sanitize_plugin_id("../evil") == ""

    def test_dotdot_in_id(self):
        assert _sanitize_plugin_id("foo..bar") == ""

    def test_slash_in_id(self):
        assert _sanitize_plugin_id("foo/bar") == ""

    def test_too_long(self):
        assert _sanitize_plugin_id("a" * 200) == ""


class TestMarketplace:
    def test_empty_marketplace(self, tmp_path):
        mp = Marketplace(plugins_dir=str(tmp_path / "plugins"))
        assert mp.get_installed() == []

    def test_install_from_directory(self, tmp_path):
        plugin_dir = tmp_path / "source" / "my-plugin"
        plugin_dir.mkdir(parents=True)
        manifest = {
            "id": "my-plugin", "name": "My Plugin", "version": "1.0.0",
            "author": "Test", "module_type": "tool",
        }
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
        (plugin_dir / "main.py").write_text("print('hello')")

        mp = Marketplace(plugins_dir=str(tmp_path / "installed"))
        result = mp.install_from_directory(str(plugin_dir))
        assert result is not None
        assert result.id == "my-plugin"
        assert result.installed is True
        assert mp.is_installed("my-plugin")

    def test_install_no_manifest(self, tmp_path):
        plugin_dir = tmp_path / "no_manifest"
        plugin_dir.mkdir()
        mp = Marketplace(plugins_dir=str(tmp_path / "installed"))
        assert mp.install_from_directory(str(plugin_dir)) is None

    def test_uninstall(self, tmp_path):
        plugin_dir = tmp_path / "source" / "rm-plugin"
        plugin_dir.mkdir(parents=True)
        manifest = {"id": "rm-plugin", "name": "Remove Me", "version": "0.1"}
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest))

        mp = Marketplace(plugins_dir=str(tmp_path / "installed"))
        mp.install_from_directory(str(plugin_dir))
        assert mp.is_installed("rm-plugin")
        assert mp.uninstall("rm-plugin") is True
        assert not mp.is_installed("rm-plugin")

    def test_uninstall_nonexistent(self, tmp_path):
        mp = Marketplace(plugins_dir=str(tmp_path / "plugins"))
        assert mp.uninstall("nope") is False

    def test_search_by_name(self, tmp_path):
        mp = Marketplace(plugins_dir=str(tmp_path / "plugins"))
        listings = [
            PluginListing(id="a", name="Spell Checker", version="1.0"),
            PluginListing(id="b", name="Word Counter", version="1.0"),
        ]
        mp.set_registry(listings)
        results = mp.search("spell")
        assert len(results) == 1
        assert results[0].id == "a"

    def test_search_by_category(self, tmp_path):
        mp = Marketplace(plugins_dir=str(tmp_path / "plugins"))
        listings = [
            PluginListing(id="a", name="Ex1", version="1.0", category=PluginCategory.EXPORT),
            PluginListing(id="b", name="Tool1", version="1.0", category=PluginCategory.TOOL),
        ]
        mp.set_registry(listings)
        results = mp.search("", category=PluginCategory.EXPORT)
        assert len(results) == 1
        assert results[0].id == "a"

    def test_load_registry_from_file(self, tmp_path):
        registry = [
            {"id": "p1", "name": "Plugin 1", "version": "1.0"},
            {"id": "p2", "name": "Plugin 2", "version": "2.0"},
        ]
        path = tmp_path / "registry.json"
        path.write_text(json.dumps(registry))

        mp = Marketplace(plugins_dir=str(tmp_path / "plugins"))
        loaded = mp.load_registry_from_file(str(path))
        assert len(loaded) == 2

    def test_load_registry_invalid_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json")
        mp = Marketplace(plugins_dir=str(tmp_path / "plugins"))
        assert mp.load_registry_from_file(str(path)) == []

    def test_get_categories(self, tmp_path):
        mp = Marketplace(plugins_dir=str(tmp_path / "plugins"))
        cats = mp.get_categories()
        assert PluginCategory.DIALECT in cats
        assert PluginCategory.THEME in cats

    def test_installed_shown_in_registry(self, tmp_path):
        plugin_dir = tmp_path / "source" / "reg-plugin"
        plugin_dir.mkdir(parents=True)
        manifest = {"id": "reg-plugin", "name": "Reg", "version": "1.0"}
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest))

        mp = Marketplace(plugins_dir=str(tmp_path / "installed"))
        mp.install_from_directory(str(plugin_dir))
        mp.set_registry([PluginListing(id="reg-plugin", name="Reg", version="2.0")])
        registry = mp.get_registry()
        match = [p for p in registry if p.id == "reg-plugin"]
        assert len(match) == 1
        assert match[0].installed is True
        assert match[0].update_available is True
