"""Title page templates -- reusable layouts for screenplay title pages."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class TitleField:
    key: str
    label: str
    default_value: str = ""
    alignment: str = "center"
    position: str = "upper"
    bold: bool = False
    italic: bool = False
    font_size: int = 12
    uppercase: bool = False


@dataclass
class TitleTemplate:
    id: str
    name: str
    description: str = ""
    fields: list[TitleField] = field(default_factory=list)
    builtin: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> TitleTemplate:
        fields = [TitleField(**f) for f in data.get("fields", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            fields=fields,
            builtin=data.get("builtin", False),
        )

    def render_fountain(self, values: dict[str, str]) -> str:
        _FOUNTAIN_KEY_MAP = {
            "title": "Title",
            "show_title": "Title",
            "author": "Author",
            "pen_name": "Author",
            "credit": "Credit",
            "written_by": "Credit",
            "art_by": "Credit",
            "source": "Source",
            "date": "Draft date",
            "draft_date": "Draft date",
            "draft": "Draft date",
            "contact": "Contact",
            "contact_info": "Contact",
            "copyright": "Copyright",
            "notes": "Notes",
            "revision": "Revision",
        }

        lines: list[str] = []
        used_fountain_keys: set[str] = set()

        for f in self.fields:
            raw = values.get(f.key, f.default_value)
            if not raw:
                continue

            text = raw.upper() if f.uppercase else raw

            fountain_key = _FOUNTAIN_KEY_MAP.get(f.key, f.key.replace("_", " ").title())

            # Fountain allows duplicate keys, but we de-duplicate standard ones
            # by appending to existing values with a newline.
            if fountain_key in used_fountain_keys:
                for i, line in enumerate(lines):
                    if line.startswith(f"{fountain_key}:"):
                        lines[i] = f"{line}\n   {text}"
                        break
            else:
                lines.append(f"{fountain_key}: {text}")
                used_fountain_keys.add(fountain_key)

        return "\n".join(lines) + "\n" if lines else ""


# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

SPEC_SCRIPT = TitleTemplate(
    id="spec_script",
    name="Standard Spec Script",
    description="The standard format for speculative screenplays sent to agents and producers.",
    fields=[
        TitleField(
            key="title", label="Title",
            position="middle", alignment="center",
            bold=True, uppercase=True, font_size=24,
        ),
        TitleField(
            key="written_by", label="Credit",
            default_value="written by",
            position="middle", alignment="center",
        ),
        TitleField(
            key="author", label="Author",
            position="middle", alignment="center",
        ),
        TitleField(
            key="contact_info", label="Contact Info",
            position="lower", alignment="left",
        ),
        TitleField(
            key="date", label="Date",
            position="lower", alignment="right",
        ),
    ],
)

SHOOTING_SCRIPT = TitleTemplate(
    id="shooting_script",
    name="Shooting Script",
    description="Production-ready format with draft tracking and revision colors.",
    fields=[
        TitleField(
            key="title", label="Title",
            position="upper", alignment="center",
            bold=True, uppercase=True, font_size=24,
        ),
        TitleField(
            key="draft", label="Draft Info",
            position="upper", alignment="center",
            italic=True,
        ),
        TitleField(
            key="written_by", label="Credit",
            default_value="written by",
            position="middle", alignment="center",
        ),
        TitleField(
            key="author", label="Author",
            position="middle", alignment="center",
        ),
        TitleField(
            key="production_company", label="Production Company",
            position="lower", alignment="left",
        ),
        TitleField(
            key="date", label="Date",
            position="lower", alignment="left",
        ),
        TitleField(
            key="draft_number", label="Draft Number",
            position="lower", alignment="right",
        ),
        TitleField(
            key="revision_color", label="Revision Color",
            position="lower", alignment="right",
        ),
    ],
)

TV_PILOT = TitleTemplate(
    id="tv_pilot",
    name="TV Pilot",
    description="Television pilot script with show title, episode title, and network info.",
    fields=[
        TitleField(
            key="show_title", label="Show Title",
            position="upper", alignment="center",
            bold=True, uppercase=True, font_size=24,
        ),
        TitleField(
            key="episode_title", label="Episode Title",
            position="upper", alignment="center",
            italic=True, font_size=14,
        ),
        TitleField(
            key="written_by", label="Credit",
            default_value="written by",
            position="middle", alignment="center",
        ),
        TitleField(
            key="author", label="Author",
            position="middle", alignment="center",
        ),
        TitleField(
            key="network", label="Network/Studio",
            position="lower", alignment="left",
        ),
        TitleField(
            key="contact", label="Contact",
            position="lower", alignment="left",
        ),
        TitleField(
            key="date", label="Date",
            position="lower", alignment="right",
        ),
    ],
)

MINIMAL = TitleTemplate(
    id="minimal",
    name="Minimal",
    description="A stripped-down title page with just the essentials.",
    fields=[
        TitleField(
            key="title", label="Title",
            position="middle", alignment="center",
            bold=True, font_size=18,
        ),
        TitleField(
            key="author", label="Author",
            position="middle", alignment="center",
        ),
    ],
)

CONTEST = TitleTemplate(
    id="contest",
    name="Contest Submission",
    description="Clean layout for screenplay competitions -- no dates or draft numbers.",
    fields=[
        TitleField(
            key="title", label="Title",
            position="middle", alignment="center",
            bold=True, uppercase=True, font_size=24,
        ),
        TitleField(
            key="written_by", label="Credit",
            default_value="by",
            position="middle", alignment="center",
        ),
        TitleField(
            key="pen_name", label="Pen Name",
            position="middle", alignment="center",
        ),
        TitleField(
            key="contact_info", label="Contact Info",
            position="lower", alignment="right",
        ),
    ],
)

COMIC_BOOK = TitleTemplate(
    id="comic_book",
    name="Comic Book Script",
    description="Format for comic book scripts with issue number and artist credits.",
    fields=[
        TitleField(
            key="title", label="Title",
            position="upper", alignment="center",
            bold=True, uppercase=True, font_size=20,
        ),
        TitleField(
            key="issue_number", label="Issue #",
            position="upper", alignment="center",
            font_size=14,
        ),
        TitleField(
            key="written_by", label="Written by",
            default_value="Written by",
            position="middle", alignment="center",
        ),
        TitleField(
            key="author", label="Author",
            position="middle", alignment="center",
        ),
        TitleField(
            key="art_by", label="Art by",
            default_value="Art by",
            position="middle", alignment="center",
        ),
        TitleField(
            key="artist", label="Artist",
            position="middle", alignment="center",
        ),
        TitleField(
            key="publisher", label="Publisher",
            position="lower", alignment="left",
        ),
        TitleField(
            key="date", label="Date",
            position="lower", alignment="right",
        ),
    ],
)

_BUILTIN_TEMPLATES: list[TitleTemplate] = [
    SPEC_SCRIPT,
    SHOOTING_SCRIPT,
    TV_PILOT,
    MINIMAL,
    CONTEST,
    COMIC_BOOK,
]


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class TitleTemplateManager:
    def __init__(self, custom_dir: str = "") -> None:
        self._templates: dict[str, TitleTemplate] = {}
        self._custom_dir = custom_dir

        for t in _BUILTIN_TEMPLATES:
            self._templates[t.id] = t

        if custom_dir:
            self._load_custom_templates()

    def _load_custom_templates(self) -> None:
        if not os.path.isdir(self._custom_dir):
            return
        for fname in sorted(os.listdir(self._custom_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._custom_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                template = TitleTemplate.from_dict(data)
                template.builtin = False
                self._templates[template.id] = template
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    def get_template(self, template_id: str) -> Optional[TitleTemplate]:
        return self._templates.get(template_id)

    def list_templates(self) -> list[TitleTemplate]:
        builtins = [t for t in self._templates.values() if t.builtin]
        custom = [t for t in self._templates.values() if not t.builtin]
        return builtins + custom

    def save_custom(self, template: TitleTemplate) -> None:
        template.builtin = False
        self._templates[template.id] = template
        if not self._custom_dir:
            return
        os.makedirs(self._custom_dir, exist_ok=True)
        path = os.path.join(self._custom_dir, f"{template.id}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(template.to_dict(), fh, indent=2)

    def delete_custom(self, template_id: str) -> bool:
        template = self._templates.get(template_id)
        if template is None or template.builtin:
            return False
        del self._templates[template_id]
        if self._custom_dir:
            path = os.path.join(self._custom_dir, f"{template_id}.json")
            if os.path.exists(path):
                os.remove(path)
        return True

    def create_custom(
        self,
        name: str,
        fields: list[TitleField],
        description: str = "",
    ) -> TitleTemplate:
        template_id = f"custom_{uuid.uuid4().hex[:8]}"
        template = TitleTemplate(
            id=template_id,
            name=name,
            description=description,
            fields=list(fields),
            builtin=False,
        )
        self.save_custom(template)
        return template

    def render(self, template_id: str, values: dict[str, str]) -> str:
        template = self._templates.get(template_id)
        if template is None:
            raise KeyError(f"Unknown template: {template_id}")
        return template.render_fountain(values)
