"""Plugin API — interface plugins use to interact with Écrit."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class PluginHook(str, Enum):
    BEFORE_SAVE = "before_save"
    AFTER_SAVE = "after_save"
    BEFORE_EXPORT = "before_export"
    AFTER_EXPORT = "after_export"
    ON_PARSE = "on_parse"
    ON_FORMAT = "on_format"
    ON_LOAD = "on_load"
    ON_UNLOAD = "on_unload"
    TOOLBAR_ACTION = "toolbar_action"
    MENU_ACTION = "menu_action"
    STATUS_BAR = "status_bar"


@dataclass
class PluginContext:
    project_path: str = ""
    script_content: str = ""
    phase: str = ""
    theme: str = ""
    language: str = "en"


class PluginAPI:
    def __init__(self):
        self._hooks: dict[str, list[Callable]] = {}
        self._commands: list[tuple[str, str, Callable]] = []
        self._panels: list[tuple[str, Any]] = []
        self._context = PluginContext()

    def set_context(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)

    def get_context(self) -> PluginContext:
        return self._context

    def register_hook(self, hook: PluginHook, callback: Callable) -> None:
        key = hook.value
        if key not in self._hooks:
            self._hooks[key] = []
        self._hooks[key].append(callback)

    def unregister_hook(self, hook: PluginHook, callback: Callable) -> None:
        key = hook.value
        if key in self._hooks:
            self._hooks[key] = [cb for cb in self._hooks[key] if cb is not callback]

    def call_hook(self, hook: PluginHook, *args, **kwargs) -> list[Any]:
        results = []
        for cb in self._hooks.get(hook.value, []):
            try:
                results.append(cb(*args, **kwargs))
            except Exception:
                pass
        return results

    def register_command(self, name: str, description: str, callback: Callable) -> None:
        self._commands.append((name, description, callback))

    def get_commands(self) -> list[tuple[str, str, Callable]]:
        return list(self._commands)

    def register_panel(self, title: str, widget: Any) -> None:
        self._panels.append((title, widget))

    def get_panels(self) -> list[tuple[str, Any]]:
        return list(self._panels)

    def get_script(self) -> str:
        return self._context.script_content

    def get_project_path(self) -> str:
        return self._context.project_path
