"""Tests for the module system — registry, loading, hooks."""

import os
import json
import pytest

from ecrit.screenplay.module_system import (
    ModuleManifest, LoadedModule, ModuleRegistry,
    HOOK_BEFORE_SAVE, HOOK_AFTER_SAVE,
)


class TestModuleManifest:
    def test_defaults(self):
        m = ModuleManifest(name="test", version="1.0.0")
        assert m.module_type == "dialect"
        assert m.entry_point == "main.py"
        assert m.requires == []

    def test_roundtrip(self):
        m = ModuleManifest(
            name="my-dialect",
            version="2.1.0",
            author="Jane",
            description="A custom dialect",
            module_type="export",
            requires=["fountain-parser"],
            settings={"output_format": "html"},
        )
        data = m.to_dict()
        restored = ModuleManifest.from_dict(data)
        assert restored.name == "my-dialect"
        assert restored.module_type == "export"
        assert restored.settings["output_format"] == "html"

    def test_from_dict_defaults(self):
        m = ModuleManifest.from_dict({})
        assert m.name == ""
        assert m.version == "0.0.0"


class TestModuleRegistry:
    def test_empty_registry(self):
        reg = ModuleRegistry()
        assert reg.list_modules() == []

    def test_scan_empty_dir(self, tmp_path):
        reg = ModuleRegistry(str(tmp_path))
        assert reg.scan_directory() == []

    def test_scan_nonexistent_dir(self):
        reg = ModuleRegistry("/nonexistent/path")
        assert reg.scan_directory() == []

    def test_scan_finds_modules(self, tmp_path):
        mod_dir = tmp_path / "my_module"
        mod_dir.mkdir()
        manifest = {
            "name": "test-module",
            "version": "1.0.0",
            "description": "A test",
        }
        (mod_dir / "manifest.json").write_text(json.dumps(manifest))
        reg = ModuleRegistry(str(tmp_path))
        found = reg.scan_directory()
        assert len(found) == 1
        assert found[0].name == "test-module"

    def test_scan_ignores_invalid_json(self, tmp_path):
        mod_dir = tmp_path / "bad_module"
        mod_dir.mkdir()
        (mod_dir / "manifest.json").write_text("not json{{{")
        reg = ModuleRegistry(str(tmp_path))
        assert reg.scan_directory() == []

    def test_load_module(self, tmp_path):
        mod_dir = tmp_path / "my_mod"
        mod_dir.mkdir()
        manifest = {"name": "loadable", "version": "1.0.0"}
        (mod_dir / "manifest.json").write_text(json.dumps(manifest))
        (mod_dir / "main.py").write_text("VALUE = 42\n")

        reg = ModuleRegistry()
        loaded = reg.load_module(str(mod_dir))
        assert loaded is not None
        assert loaded.name == "loadable"
        assert loaded.module is not None
        assert loaded.module.VALUE == 42

    def test_load_module_no_entry_point(self, tmp_path):
        mod_dir = tmp_path / "no_entry"
        mod_dir.mkdir()
        manifest = {"name": "noentry", "version": "1.0.0"}
        (mod_dir / "manifest.json").write_text(json.dumps(manifest))

        reg = ModuleRegistry()
        loaded = reg.load_module(str(mod_dir))
        assert loaded is not None
        assert loaded.module is None
        assert loaded.enabled is True

    def test_load_module_bad_entry(self, tmp_path):
        mod_dir = tmp_path / "bad_entry"
        mod_dir.mkdir()
        manifest = {"name": "badentry", "version": "1.0.0"}
        (mod_dir / "manifest.json").write_text(json.dumps(manifest))
        (mod_dir / "main.py").write_text("raise RuntimeError('boom')\n")

        reg = ModuleRegistry()
        loaded = reg.load_module(str(mod_dir))
        assert loaded is not None
        assert loaded.error != ""
        assert loaded.enabled is False

    def test_load_module_no_manifest(self, tmp_path):
        mod_dir = tmp_path / "empty"
        mod_dir.mkdir()
        reg = ModuleRegistry()
        assert reg.load_module(str(mod_dir)) is None

    def test_unload(self, tmp_path):
        mod_dir = tmp_path / "unloadable"
        mod_dir.mkdir()
        (mod_dir / "manifest.json").write_text(json.dumps({"name": "x", "version": "1.0.0"}))

        reg = ModuleRegistry()
        reg.load_module(str(mod_dir))
        assert len(reg.list_modules()) == 1
        assert reg.unload_module("x") is True
        assert len(reg.list_modules()) == 0

    def test_unload_nonexistent(self):
        reg = ModuleRegistry()
        assert reg.unload_module("nope") is False

    def test_enable_disable(self, tmp_path):
        mod_dir = tmp_path / "toggleable"
        mod_dir.mkdir()
        (mod_dir / "manifest.json").write_text(
            json.dumps({"name": "toggle", "version": "1.0.0"})
        )

        reg = ModuleRegistry()
        reg.load_module(str(mod_dir))
        assert reg.disable_module("toggle") is True
        assert reg.get_module("toggle").enabled is False
        assert reg.enable_module("toggle") is True
        assert reg.get_module("toggle").enabled is True

    def test_enable_errored_module(self, tmp_path):
        mod_dir = tmp_path / "errored"
        mod_dir.mkdir()
        (mod_dir / "manifest.json").write_text(
            json.dumps({"name": "err", "version": "1.0.0"})
        )
        (mod_dir / "main.py").write_text("raise Exception('fail')\n")

        reg = ModuleRegistry()
        reg.load_module(str(mod_dir))
        assert reg.enable_module("err") is False

    def test_list_by_type(self, tmp_path):
        for name, mtype in [("d1", "dialect"), ("e1", "export"), ("d2", "dialect")]:
            mod_dir = tmp_path / name
            mod_dir.mkdir()
            (mod_dir / "manifest.json").write_text(
                json.dumps({"name": name, "version": "1.0.0", "module_type": mtype})
            )

        reg = ModuleRegistry()
        for name in ["d1", "e1", "d2"]:
            reg.load_module(str(tmp_path / name))

        assert len(reg.list_modules("dialect")) == 2
        assert len(reg.list_modules("export")) == 1
        assert len(reg.list_modules()) == 3

    def test_hooks(self):
        reg = ModuleRegistry()
        results = []
        reg.register_hook(HOOK_BEFORE_SAVE, lambda: results.append("save"))
        reg.call_hook(HOOK_BEFORE_SAVE)
        assert results == ["save"]

    def test_hooks_with_args(self):
        reg = ModuleRegistry()
        reg.register_hook("test", lambda x, y: x + y)
        results = reg.call_hook("test", 3, 4)
        assert results == [7]

    def test_hooks_exception_isolated(self):
        reg = ModuleRegistry()
        reg.register_hook("test", lambda: 1 / 0)
        reg.register_hook("test", lambda: 42)
        results = reg.call_hook("test")
        assert 42 in results

    def test_hooks_empty(self):
        reg = ModuleRegistry()
        assert reg.call_hook("nonexistent") == []

    def test_load_all(self, tmp_path):
        for name in ["mod1", "mod2", "mod3"]:
            mod_dir = tmp_path / name
            mod_dir.mkdir()
            (mod_dir / "manifest.json").write_text(
                json.dumps({"name": name, "version": "1.0.0"})
            )

        reg = ModuleRegistry(str(tmp_path))
        count = reg.load_all()
        assert count == 3
        assert len(reg.list_modules()) == 3

    def test_load_all_empty(self, tmp_path):
        reg = ModuleRegistry(str(tmp_path))
        assert reg.load_all() == 0

    def test_to_dict(self, tmp_path):
        mod_dir = tmp_path / "serializable"
        mod_dir.mkdir()
        (mod_dir / "manifest.json").write_text(
            json.dumps({"name": "ser", "version": "1.0.0"})
        )

        reg = ModuleRegistry(str(tmp_path))
        reg.load_module(str(mod_dir))
        data = reg.to_dict()
        assert "ser" in data["modules"]
        assert data["modules"]["ser"]["enabled"] is True

    def test_convenience_getters(self, tmp_path):
        for name, mtype in [("d", "dialect"), ("e", "export"), ("t", "tool"), ("r", "report")]:
            mod_dir = tmp_path / name
            mod_dir.mkdir()
            (mod_dir / "manifest.json").write_text(
                json.dumps({"name": name, "version": "1.0.0", "module_type": mtype})
            )

        reg = ModuleRegistry()
        for name in ["d", "e", "t", "r"]:
            reg.load_module(str(tmp_path / name))

        assert len(reg.get_dialects()) == 1
        assert len(reg.get_exporters()) == 1
        assert len(reg.get_tools()) == 1
        assert len(reg.get_reports()) == 1
