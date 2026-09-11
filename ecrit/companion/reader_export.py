"""Reader bundle — lightweight read-only export for companion app."""

from __future__ import annotations

import json
import os
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class ReaderBundle:
    title: str
    script_html: str
    page_count: int = 1
    scenes: list[dict] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


def _fountain_to_html(script: str, title: str = "") -> str:
    import html
    lines = script.split("\n")
    escaped_title = html.escape(title)
    html_parts = [
        "<!DOCTYPE html><html><head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{escaped_title}</title>",
        "<style>",
        "body { font-family: 'Courier Prime', 'Courier New', monospace; ",
        "font-size: 12pt; max-width: 8in; margin: 0 auto; padding: 1in; ",
        "background: #fff; color: #000; }",
        ".scene { font-weight: bold; text-transform: uppercase; margin-top: 2em; }",
        ".character { text-transform: uppercase; margin-left: 2.5in; margin-top: 1em; }",
        ".dialogue { margin-left: 1.5in; margin-right: 1.5in; }",
        ".parenthetical { margin-left: 2in; margin-right: 2in; font-style: italic; }",
        ".transition { text-align: right; text-transform: uppercase; }",
        ".action { margin-top: 1em; }",
        "@media (prefers-color-scheme: dark) {",
        "body { background: #1a1a1a; color: #e0e0e0; }",
        "}",
        "</style></head><body>",
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_parts.append("<p>&nbsp;</p>")
            continue
        escaped = html.escape(stripped)
        if stripped.startswith(("INT.", "EXT.", "EST.", "INT./EXT.", "I/E.", ".")):
            html_parts.append(f'<p class="scene">{escaped}</p>')
        elif stripped.startswith("(") and stripped.endswith(")"):
            html_parts.append(f'<p class="parenthetical">{escaped}</p>')
        elif stripped.endswith("TO:") and stripped == stripped.upper():
            html_parts.append(f'<p class="transition">{escaped}</p>')
        elif stripped == stripped.upper() and stripped[0:1].isalpha() and len(stripped) > 1:
            html_parts.append(f'<p class="character">{escaped}</p>')
        else:
            html_parts.append(f'<p class="action">{escaped}</p>')

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def create_reader_bundle(
    script: str,
    title: str,
    output_dir: str,
    scenes: list[dict] | None = None,
    characters: list[str] | None = None,
) -> str:
    html = _fountain_to_html(script, title)
    page_count = max(1, len(script) // 3500)

    bundle = ReaderBundle(
        title=title,
        script_html=html,
        page_count=page_count,
        scenes=scenes or [],
        characters=characters or [],
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    filename = f"{safe_title}_{timestamp}.ecrit-reader"
    filepath = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(bundle.to_dict(), indent=2))
        zf.writestr("script.html", html)

    return filepath
