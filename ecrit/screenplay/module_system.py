"""Module system — extensibility via loadable plugin modules."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Optional


@dataclass
class ModuleManifest:
    name: str
    version: str
    author: str = ""
    description: str = ""
    module_type: str = "dialect"  # dialect | export | tool | report
    entry_point: str = "main.py"
    requires: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ModuleManifest:
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            module_type=data.get("module_type", "dialect"),
            entry_point=data.get("entry_point", "main.py"),
            requires=data.get("requires", []),
            settings=data.get("settings", {}),
        )


@dataclass
class LoadedModule:
    manifest: ModuleManifest
    path: str
    module: Any = None
    enabled: bool = True
    error: str = ""

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def module_type(self) -> str:
        return self.manifest.module_type


class ModuleRegistry:
    def __init__(self, modules_dir: str = ""):
        self._modules: dict[str, LoadedModule] = {}
        self._hooks: dict[str, list[Callable]] = {}
        self.modules_dir = modules_dir

    def scan_directory(self, path: str = "") -> list[ModuleManifest]:
        scan_path = path or self.modules_dir
        if not scan_path or not os.path.isdir(scan_path):
            return []

        manifests = []
        for entry in os.listdir(scan_path):
            mod_dir = os.path.join(scan_path, entry)
            manifest_path = os.path.join(mod_dir, "manifest.json")
            if os.path.isdir(mod_dir) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    manifests.append(ModuleManifest.from_dict(data))
                except (json.JSONDecodeError, OSError):
                    pass
        return manifests

    def load_module(self, module_dir: str) -> Optional[LoadedModule]:
        manifest_path = os.path.join(module_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            return None

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = ModuleManifest.from_dict(json.load(f))
        except (json.JSONDecodeError, OSError):
            return None

        entry = os.path.join(module_dir, manifest.entry_point)
        loaded = LoadedModule(manifest=manifest, path=module_dir)

        if os.path.exists(entry):
            try:
                spec = importlib.util.spec_from_file_location(
                    f"ecrit_module_{manifest.name}", entry
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    loaded.module = mod
            except Exception as e:
                loaded.error = str(e)
                loaded.enabled = False

        self._modules[manifest.name] = loaded
        return loaded

    def unload_module(self, name: str) -> bool:
        if name in self._modules:
            self._unhook_module(name)
            del self._modules[name]
            return True
        return False

    def enable_module(self, name: str) -> bool:
        mod = self._modules.get(name)
        if mod and not mod.error:
            mod.enabled = True
            return True
        return False

    def disable_module(self, name: str) -> bool:
        mod = self._modules.get(name)
        if mod:
            mod.enabled = False
            self._unhook_module(name)
            return True
        return False

    def get_module(self, name: str) -> Optional[LoadedModule]:
        return self._modules.get(name)

    def list_modules(self, module_type: str = "") -> list[LoadedModule]:
        modules = list(self._modules.values())
        if module_type:
            modules = [m for m in modules if m.module_type == module_type]
        return modules

    def list_enabled(self, module_type: str = "") -> list[LoadedModule]:
        return [m for m in self.list_modules(module_type) if m.enabled]

    def register_hook(self, hook_name: str, callback: Callable) -> None:
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def call_hook(self, hook_name: str, *args, **kwargs) -> list[Any]:
        results = []
        for callback in self._hooks.get(hook_name, []):
            try:
                results.append(callback(*args, **kwargs))
            except Exception:
                pass
        return results

    def _unhook_module(self, name: str) -> None:
        mod = self._modules.get(name)
        if not mod or not mod.module:
            return
        for hook_name in list(self._hooks.keys()):
            self._hooks[hook_name] = [
                cb for cb in self._hooks[hook_name]
                if not (hasattr(cb, "__module__") and
                        cb.__module__ == f"ecrit_module_{name}")
            ]

    def get_dialects(self) -> list[LoadedModule]:
        return self.list_enabled("dialect")

    def get_exporters(self) -> list[LoadedModule]:
        return self.list_enabled("export")

    def get_tools(self) -> list[LoadedModule]:
        return self.list_enabled("tool")

    def get_reports(self) -> list[LoadedModule]:
        return self.list_enabled("report")

    def to_dict(self) -> dict:
        return {
            "modules_dir": self.modules_dir,
            "modules": {
                name: {
                    "path": mod.path,
                    "enabled": mod.enabled,
                    "manifest": mod.manifest.to_dict(),
                }
                for name, mod in self._modules.items()
            },
        }

    def load_all(self, path: str = "") -> int:
        scan_path = path or self.modules_dir
        if not scan_path or not os.path.isdir(scan_path):
            return 0
        count = 0
        for entry in os.listdir(scan_path):
            mod_dir = os.path.join(scan_path, entry)
            if os.path.isdir(mod_dir) and os.path.exists(
                os.path.join(mod_dir, "manifest.json")
            ):
                loaded = self.load_module(mod_dir)
                if loaded:
                    count += 1
        return count


HOOK_BEFORE_SAVE = "before_save"
HOOK_AFTER_SAVE = "after_save"
HOOK_BEFORE_EXPORT = "before_export"
HOOK_AFTER_EXPORT = "after_export"
HOOK_ON_PARSE = "on_parse"
HOOK_ON_FORMAT = "on_format"
