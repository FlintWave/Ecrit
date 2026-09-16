"""Line-anchored annotations for screenplay review and notes."""

import uuid
import datetime
from dataclasses import dataclass, field


CATEGORY_COLORS = {
    "note": "#FFD54F",
    "todo": "#FF8A65",
    "question": "#4FC3F7",
    "fix": "#E57373",
    "praise": "#81C784",
}

VALID_CATEGORIES = list(CATEGORY_COLORS.keys())


@dataclass
class Annotation:
    id: str
    line: int
    text: str
    author: str = ""
    color: str = "#FFD54F"
    category: str = "note"
    created_at: str = ""
    resolved: bool = False


class AnnotationManager:

    def __init__(self):
        self._annotations: dict[str, Annotation] = {}

    def add(self, line: int, text: str, author: str = "", category: str = "note", color: str = "") -> Annotation:
        ann_id = uuid.uuid4().hex[:8]
        if not color:
            color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["note"])
        annotation = Annotation(
            id=ann_id,
            line=line,
            text=text,
            author=author,
            color=color,
            category=category,
            created_at=datetime.datetime.now().isoformat(),
        )
        self._annotations[ann_id] = annotation
        return annotation

    def remove(self, annotation_id: str) -> bool:
        return self._annotations.pop(annotation_id, None) is not None

    def get_by_line(self, line: int) -> list[Annotation]:
        return [a for a in self._annotations.values() if a.line == line]

    def get_all(self, include_resolved: bool = False) -> list[Annotation]:
        annotations = list(self._annotations.values())
        if not include_resolved:
            annotations = [a for a in annotations if not a.resolved]
        return sorted(annotations, key=lambda a: a.line)

    def resolve(self, annotation_id: str) -> bool:
        if annotation_id in self._annotations:
            self._annotations[annotation_id].resolved = True
            return True
        return False

    def unresolve(self, annotation_id: str) -> bool:
        if annotation_id in self._annotations:
            self._annotations[annotation_id].resolved = False
            return True
        return False

    def update_text(self, annotation_id: str, text: str) -> bool:
        if annotation_id in self._annotations:
            self._annotations[annotation_id].text = text
            return True
        return False

    def get_by_category(self, category: str) -> list[Annotation]:
        return [a for a in self._annotations.values() if a.category == category]

    def get_summary(self) -> dict:
        by_category = {}
        resolved = 0
        unresolved = 0
        for a in self._annotations.values():
            by_category[a.category] = by_category.get(a.category, 0) + 1
            if a.resolved:
                resolved += 1
            else:
                unresolved += 1
        return {
            "total": len(self._annotations),
            "resolved": resolved,
            "unresolved": unresolved,
            "by_category": by_category,
        }

    def shift_lines(self, from_line: int, delta: int) -> None:
        for annotation in self._annotations.values():
            if annotation.line >= from_line:
                annotation.line = max(0, annotation.line + delta)

    def to_dict(self) -> dict:
        return {
            "annotations": {
                ann_id: {
                    "id": a.id,
                    "line": a.line,
                    "text": a.text,
                    "author": a.author,
                    "color": a.color,
                    "category": a.category,
                    "created_at": a.created_at,
                    "resolved": a.resolved,
                }
                for ann_id, a in self._annotations.items()
            }
        }

    def from_dict(self, data: dict) -> None:
        self._annotations.clear()
        for ann_id, fields in data.get("annotations", {}).items():
            self._annotations[ann_id] = Annotation(
                id=fields["id"],
                line=fields["line"],
                text=fields["text"],
                author=fields.get("author", ""),
                color=fields.get("color", "#FFD54F"),
                category=fields.get("category", "note"),
                created_at=fields.get("created_at", ""),
                resolved=fields.get("resolved", False),
            )

    def clear_resolved(self) -> int:
        resolved_ids = [aid for aid, a in self._annotations.items() if a.resolved]
        for aid in resolved_ids:
            del self._annotations[aid]
        return len(resolved_ids)

    def get_categories(self) -> list[str]:
        return list(VALID_CATEGORIES)
