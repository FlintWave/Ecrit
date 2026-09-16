"""Scene/beat tagging — metadata tags for tone, subplot, act, and custom categories."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SceneTag:
    name: str
    color: str
    category: str = ""


_DEFAULT_TAGS: list[SceneTag] = [
    SceneTag("Tense", "#e06c75", "tone"),
    SceneTag("Comic", "#e5c07b", "tone"),
    SceneTag("Romantic", "#c678dd", "tone"),
    SceneTag("Dark", "#5c6370", "tone"),
    SceneTag("Hopeful", "#98c379", "tone"),
    SceneTag("Action", "#d19a66", "tone"),

    SceneTag("A-Story", "#61afef", "subplot"),
    SceneTag("B-Story", "#56b6c2", "subplot"),
    SceneTag("C-Story", "#be5046", "subplot"),

    SceneTag("Setup", "#e5c07b", "act"),
    SceneTag("Confrontation", "#e06c75", "act"),
    SceneTag("Resolution", "#98c379", "act"),
    SceneTag("Midpoint", "#c678dd", "act"),
    SceneTag("Climax", "#d19a66", "act"),
]


class SceneTagManager:
    def __init__(self):
        self._scene_tags: dict[int, list[SceneTag]] = {}
        self._available_tags: list[SceneTag] = list(_DEFAULT_TAGS)

    def add_tag(self, scene_index: int, tag: SceneTag) -> None:
        tags = self._scene_tags.setdefault(scene_index, [])
        if not any(t.name == tag.name for t in tags):
            tags.append(tag)

    def remove_tag(self, scene_index: int, tag_name: str) -> None:
        if scene_index not in self._scene_tags:
            return
        self._scene_tags[scene_index] = [
            t for t in self._scene_tags[scene_index] if t.name != tag_name
        ]
        if not self._scene_tags[scene_index]:
            del self._scene_tags[scene_index]

    def get_tags(self, scene_index: int) -> list[SceneTag]:
        return list(self._scene_tags.get(scene_index, []))

    def get_scenes_by_tag(self, tag_name: str) -> list[int]:
        return [
            idx for idx, tags in self._scene_tags.items()
            if any(t.name == tag_name for t in tags)
        ]

    def create_custom_tag(self, name: str, color: str, category: str = "custom") -> SceneTag:
        tag = SceneTag(name=name, color=color, category=category)
        if not any(t.name == name for t in self._available_tags):
            self._available_tags.append(tag)
        return tag

    def get_available_tags(self) -> list[SceneTag]:
        return list(self._available_tags)

    def to_dict(self) -> dict:
        return {
            "scene_tags": {
                str(idx): [
                    {"name": t.name, "color": t.color, "category": t.category}
                    for t in tags
                ]
                for idx, tags in self._scene_tags.items()
            },
            "custom_tags": [
                {"name": t.name, "color": t.color, "category": t.category}
                for t in self._available_tags
                if t not in _DEFAULT_TAGS
            ],
        }

    def from_dict(self, data: dict) -> None:
        self._scene_tags.clear()
        for idx_str, tag_dicts in data.get("scene_tags", {}).items():
            idx = int(idx_str)
            self._scene_tags[idx] = [
                SceneTag(**td) for td in tag_dicts
            ]
        self._available_tags = list(_DEFAULT_TAGS)
        for td in data.get("custom_tags", []):
            tag = SceneTag(**td)
            if not any(t.name == tag.name for t in self._available_tags):
                self._available_tags.append(tag)
