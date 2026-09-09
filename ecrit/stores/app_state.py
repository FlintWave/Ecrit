"""Central app state management."""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path
from datetime import datetime, timezone

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
    language: str = "en"

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
                self.projects = self._load_projects_py()
        else:
            self.projects = self._load_projects_py()
        self.notify()

    def _load_projects_py(self) -> list:
        folder = Path(self.project_folder)
        if not folder.exists():
            return []
        projects = []
        for item in sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime if p.is_dir() else 0, reverse=True):
            meta_file = item / "meta.json"
            if item.is_dir() and meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    meta["path"] = str(item)
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                    meta["modified_at"] = mtime.isoformat()
                    projects.append(meta)
                except Exception:
                    pass
        return projects

    def open_project(self, path: str):
        if ecrit_core:
            try:
                data = json.loads(ecrit_core.open_project(path))
                self.current_project_path = path
                self.script_content = data.get("script", "")
                self.notify()
                return data
            except Exception:
                pass
        return self._open_project_py(path)

    def _open_project_py(self, path: str):
        project_dir = Path(path)
        meta_file = project_dir / "meta.json"
        if not meta_file.exists():
            return None
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            return None
        script_file = project_dir / "script.fountain"
        script = ""
        if script_file.exists():
            try:
                script = script_file.read_text(encoding="utf-8")
            except Exception:
                pass
        self.current_project_path = path
        self.script_content = script
        self.notify()
        return {"meta": meta, "script": script}

    def save_script(self) -> bool:
        if ecrit_core and self.current_project_path:
            try:
                ecrit_core.save_script(self.current_project_path, self.script_content)
                return True
            except Exception:
                pass
        if self.current_project_path:
            script_file = Path(self.current_project_path) / "script.fountain"
            try:
                script_file.write_text(self.script_content, encoding="utf-8")
                return True
            except Exception:
                return False
        return False

    def create_project(self, title: str, author: str, format_id: str, paper: str, kind: str = "Single"):
        if ecrit_core:
            try:
                Path(self.project_folder).mkdir(parents=True, exist_ok=True)
                result = ecrit_core.create_project(
                    self.project_folder, title, author, format_id, paper, kind
                )
                meta = json.loads(result)
                self.load_projects()
                return meta
            except Exception:
                pass
        return self._create_project_py(title, author, format_id, paper, kind)

    def _create_project_py(self, title: str, author: str, format_id: str, paper: str, kind: str = "Single"):
        folder = Path(self.project_folder)
        folder.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-')[:50] or "Untitled"
        project_dir = folder / safe_title
        counter = 1
        while project_dir.exists():
            project_dir = folder / f"{safe_title}-{counter}"
            counter += 1
        project_dir.mkdir(parents=True)
        now = datetime.now(timezone.utc).isoformat()
        meta = {
            "title": title,
            "author": author,
            "format_id": format_id,
            "paper": paper,
            "kind": kind,
            "created_at": now,
            "path": str(project_dir),
        }
        (project_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        header = f"Title: {title}\nCredit: Written by\nAuthor: {author}\nDraft date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        (project_dir / "script.fountain").write_text(header, encoding="utf-8")
        import subprocess
        try:
            subprocess.run(["git", "init", str(project_dir)], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        self.load_projects()
        return meta

    def parse_script(self) -> dict:
        if ecrit_core and self.script_content:
            try:
                return json.loads(ecrit_core.parse_fountain(self.script_content))
            except Exception:
                pass
        return self._parse_script_py()

    def _parse_script_py(self) -> dict:
        if not self.script_content:
            return {"elements": []}
        elements = []
        for line in self.script_content.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("INT.") or stripped.startswith("EXT.") or stripped.startswith("INT/EXT"):
                elements.append({"type": "scene_heading", "text": stripped})
            elif stripped.isupper() and len(stripped) < 50 and not stripped.startswith("Title:"):
                elements.append({"type": "character", "text": stripped})
            else:
                elements.append({"type": "action", "text": stripped})
        return {"elements": elements}

    def get_stats(self) -> dict:
        if ecrit_core and self.script_content:
            try:
                return json.loads(ecrit_core.get_script_stats(self.script_content))
            except Exception:
                pass
        return self._get_stats_py()

    def _get_stats_py(self) -> dict:
        text = self.script_content
        if not text:
            return {
                "word_count": 0, "page_count": 0, "scene_count": 0,
                "character_count": 0, "dialogue_percentage": 0,
                "action_percentage": 0, "characters": [], "scenes": [],
            }
        all_lines = text.split('\n')
        words = len(text.split())
        lines_count = len(all_lines)
        pages = max(1, lines_count // 55)

        scene_list = []
        char_lines: dict[str, dict] = {}
        current_char = ""
        in_dialogue = False
        dialogue_lines = 0
        action_lines = 0
        scene_word_count = 0
        scene_heading = ""
        scene_page = 1

        for i, line in enumerate(all_lines):
            stripped = line.strip()
            if not stripped:
                in_dialogue = False
                current_char = ""
                continue

            is_heading = stripped.startswith(("INT.", "EXT.", "INT/EXT", "EST.", "INT./EXT.", "I/E."))
            if is_heading:
                if scene_heading:
                    scene_list.append({
                        "heading": scene_heading,
                        "word_count": scene_word_count,
                        "page": scene_page,
                    })
                scene_heading = stripped
                scene_page = max(1, (i + 1) // 55)
                scene_word_count = 0
                in_dialogue = False
                current_char = ""
                continue

            line_words = len(stripped.split())
            scene_word_count += line_words

            if stripped.isupper() and len(stripped) < 50 and not stripped.startswith(("Title:", "Credit:", "Author:", "Draft")):
                current_char = stripped.split("(")[0].strip()
                in_dialogue = True
                if current_char not in char_lines:
                    char_lines[current_char] = {"name": current_char, "line_count": 0, "word_count": 0}
                continue

            if in_dialogue and current_char:
                char_lines[current_char]["line_count"] += 1
                char_lines[current_char]["word_count"] += line_words
                dialogue_lines += 1
            else:
                action_lines += 1

        if scene_heading:
            scene_list.append({
                "heading": scene_heading,
                "word_count": scene_word_count,
                "page": scene_page,
            })

        total_content = dialogue_lines + action_lines
        dialogue_pct = (dialogue_lines / total_content * 100) if total_content else 0
        action_pct = (action_lines / total_content * 100) if total_content else 0

        characters_list = sorted(char_lines.values(), key=lambda c: c["line_count"], reverse=True)

        return {
            "word_count": words,
            "page_count": pages,
            "scene_count": len(scene_list),
            "character_count": len(characters_list),
            "dialogue_percentage": dialogue_pct,
            "action_percentage": action_pct,
            "characters": characters_list,
            "scenes": scene_list,
        }

    def set_phase(self, phase: str):
        self.current_phase = phase
        self.notify()

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.notify()


STATE = AppState()
