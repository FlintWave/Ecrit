"""Central app state management."""

import json
from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path

try:
    import ecrit_core
except ImportError:
    ecrit_core = None


@dataclass
class AppState:
    current_project_path: Optional[str] = None
    current_phase: str = "Manuscript"
    script_content: str = ""
    projects: list = field(default_factory=list)
    theme: str = "dark"
    project_folder: str = ""
    author_name: str = ""
    author_email: str = ""

    _listeners: list = field(default_factory=list, repr=False)

    def __post_init__(self):
        if not self.project_folder:
            home = Path.home()
            self.project_folder = str(home / "Écrit Projects")

    def subscribe(self, listener: Callable):
        self._listeners.append(listener)

    def notify(self):
        for fn in self._listeners:
            fn()

    def load_projects(self):
        if ecrit_core:
            try:
                data = ecrit_core.list_projects(self.project_folder)
                self.projects = json.loads(data)
            except Exception:
                self.projects = []
        self.notify()

    def open_project(self, path: str):
        if ecrit_core:
            data = json.loads(ecrit_core.open_project(path))
            self.current_project_path = path
            self.script_content = data.get("script", "")
            self.notify()
            return data
        return None

    def save_script(self):
        if ecrit_core and self.current_project_path:
            ecrit_core.save_script(self.current_project_path, self.script_content)

    def create_project(self, title: str, author: str, format_id: str, paper: str, kind: str = "Single"):
        if ecrit_core:
            Path(self.project_folder).mkdir(parents=True, exist_ok=True)
            result = ecrit_core.create_project(
                self.project_folder, title, author, format_id, paper, kind
            )
            meta = json.loads(result)
            self.load_projects()
            return meta
        return None

    def parse_script(self) -> dict:
        if ecrit_core and self.script_content:
            return json.loads(ecrit_core.parse_fountain(self.script_content))
        return {"elements": []}

    def get_stats(self) -> dict:
        if ecrit_core and self.script_content:
            return json.loads(ecrit_core.get_script_stats(self.script_content))
        return {}

    def set_phase(self, phase: str):
        self.current_phase = phase
        self.notify()

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.notify()


STATE = AppState()
