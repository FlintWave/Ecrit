"""Named bookmark markers for script lines."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Bookmark:
    name: str
    line: int
    color: str = "#FFB74D"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BookmarkManager:
    def __init__(self):
        self._bookmarks: list[Bookmark] = []

    def add(self, name: str, line: int, color: str = "#FFB74D") -> Bookmark:
        for bm in self._bookmarks:
            if bm.name == name:
                bm.line = line
                bm.color = color
                return bm
        bm = Bookmark(name=name, line=line, color=color)
        self._bookmarks.append(bm)
        self._bookmarks.sort(key=lambda b: b.line)
        return bm

    def remove(self, name: str) -> bool:
        for i, bm in enumerate(self._bookmarks):
            if bm.name == name:
                self._bookmarks.pop(i)
                return True
        return False

    def get_all(self) -> list[Bookmark]:
        return list(self._bookmarks)

    def get_by_name(self, name: str) -> Optional[Bookmark]:
        for bm in self._bookmarks:
            if bm.name == name:
                return bm
        return None

    def get_by_line(self, line: int) -> Optional[Bookmark]:
        for bm in self._bookmarks:
            if bm.line == line:
                return bm
        return None

    def clear(self) -> None:
        self._bookmarks.clear()

    def jump_next(self, current_line: int) -> Optional[Bookmark]:
        for bm in self._bookmarks:
            if bm.line > current_line:
                return bm
        return None

    def jump_prev(self, current_line: int) -> Optional[Bookmark]:
        result = None
        for bm in self._bookmarks:
            if bm.line < current_line:
                result = bm
            else:
                break
        return result

    def to_json(self) -> str:
        return json.dumps(
            [{"name": b.name, "line": b.line, "color": b.color, "created_at": b.created_at}
             for b in self._bookmarks]
        )

    def from_json(self, data: str) -> None:
        self._bookmarks.clear()
        try:
            items = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return
        for item in items:
            self._bookmarks.append(Bookmark(
                name=item["name"],
                line=item["line"],
                color=item.get("color", "#FFB74D"),
                created_at=item.get("created_at", ""),
            ))
        self._bookmarks.sort(key=lambda b: b.line)

    def update_lines(self, old_line: int, delta: int) -> None:
        for bm in self._bookmarks:
            if bm.line >= old_line:
                bm.line = max(1, bm.line + delta)
        self._bookmarks.sort(key=lambda b: b.line)
