"""Generate self-contained HTML from Fountain screenplay for read-only review sharing."""

import os
import re
import uuid
from datetime import datetime, timezone
from html import escape


def _parse_fountain_to_elements(content: str) -> list[dict]:
    """Simple regex-based Fountain parser that returns a list of typed elements.

    Each element is {"type": str, "text": str} where type is one of:
    SceneHeading, Character, Dialogue, Parenthetical, Action,
    Transition, Section, Synopsis, Note, PageBreak.
    """
    elements: list[dict] = []

    # Strip title page (everything before the first blank line after key: value pairs)
    title_page_re = re.compile(
        r"\A([ \t]*[A-Za-z ]+:.*\n(?:(?:[ \t]+.*|[ \t]*[A-Za-z ]+:.*)?\n)*)\n",
        re.MULTILINE,
    )
    m = title_page_re.match(content)
    body = content[m.end():] if m else content

    lines = body.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Page break: === (three or more equals)
        if re.match(r"^={3,}\s*$", stripped):
            elements.append({"type": "PageBreak", "text": ""})
            i += 1
            continue

        # Blank line — skip
        if stripped == "":
            i += 1
            continue

        # Section heading: starts with #
        if stripped.startswith("#"):
            text = stripped.lstrip("#").strip()
            elements.append({"type": "Section", "text": text})
            i += 1
            continue

        # Synopsis: starts with =
        if stripped.startswith("=") and not stripped.startswith("=="):
            text = stripped[1:].strip()
            elements.append({"type": "Synopsis", "text": text})
            i += 1
            continue

        # Note: [[...]]
        if stripped.startswith("[[") and stripped.endswith("]]"):
            text = stripped[2:-2].strip()
            elements.append({"type": "Note", "text": text})
            i += 1
            continue

        # Transition: > at start of line, or a line ending in TO:
        if stripped.startswith(">") and not stripped.startswith(">>"):
            text = stripped[1:].strip()
            elements.append({"type": "Transition", "text": text})
            i += 1
            continue
        if re.match(r"^[A-Z ]+TO:\s*$", stripped):
            elements.append({"type": "Transition", "text": stripped})
            i += 1
            continue

        # Scene heading: INT./EXT./EST./INT/EXT or forced with .
        if re.match(
            r"^(INT\.|EXT\.|EST\.|INT |EXT |INT/EXT[ .]|I/E[ .]|\.(?![.]))",
            stripped,
            re.IGNORECASE,
        ):
            text = stripped
            if text.startswith("."):
                text = text[1:]
            elements.append({"type": "SceneHeading", "text": text})
            i += 1
            continue

        # Character name: ALL CAPS line possibly with (V.O.), (O.S.), (CONT'D)
        # followed by dialogue or parenthetical on next non-blank line.
        # Also forced with @ prefix.
        char_match = re.match(
            r"^(@?.+)$", stripped
        )
        if char_match:
            candidate = stripped
            forced = candidate.startswith("@")
            if forced:
                candidate = candidate[1:].strip()

            is_upper = (
                forced
                or (
                    re.match(r"^[A-Z][A-Z0-9 \-_.\']+(\s*\(.*\))?\s*$", candidate)
                    and len(candidate) > 1
                )
            )

            if is_upper:
                # Peek ahead: skip blank lines then check for dialogue/parenthetical
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and lines[j].strip():
                    # This looks like a character cue
                    elements.append({"type": "Character", "text": candidate})
                    # Skip to dialogue start (past any blank lines)
                    i = j

                    # Collect dialogue and parentheticals
                    while i < len(lines):
                        dline = lines[i]
                        dstripped = dline.strip()

                        if dstripped == "":
                            break

                        if dstripped.startswith("(") and dstripped.endswith(")"):
                            elements.append(
                                {"type": "Parenthetical", "text": dstripped}
                            )
                        else:
                            elements.append({"type": "Dialogue", "text": dstripped})
                        i += 1
                    continue

        # Default: Action
        elements.append({"type": "Action", "text": stripped})
        i += 1

    return elements


_CSS = """\
:root {
    --bg: #ffffff;
    --fg: #1a1a1a;
    --muted: #666666;
    --border: #cccccc;
    --watermark: rgba(0, 0, 0, 0.04);
    --header-bg: #f5f5f5;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg: #1a1a1a;
        --fg: #e0e0e0;
        --muted: #999999;
        --border: #444444;
        --watermark: rgba(255, 255, 255, 0.04);
        --header-bg: #242424;
    }
}
*, *::before, *::after { box-sizing: border-box; }
body {
    font-family: "Courier Prime", "Courier New", Courier, monospace;
    font-size: 12pt;
    line-height: 1.5;
    color: var(--fg);
    background: var(--bg);
    margin: 0;
    padding: 0;
    -webkit-font-smoothing: antialiased;
}
.watermark-layer {
    position: fixed;
    inset: 0;
    z-index: 9999;
    pointer-events: none;
    overflow: hidden;
}
.watermark-inner {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    transform: rotate(-35deg);
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 80px 120px;
}
.watermark-inner span {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: var(--watermark);
    white-space: nowrap;
    user-select: none;
}
.header {
    background: var(--header-bg);
    border-bottom: 1px solid var(--border);
    padding: 24px 32px;
    text-align: center;
}
.header h1 {
    margin: 0 0 4px;
    font-size: 20pt;
    font-weight: bold;
}
.header .author {
    margin: 0 0 12px;
    font-size: 11pt;
    color: var(--muted);
}
.header .notice {
    display: inline-block;
    padding: 4px 16px;
    border: 2px solid var(--muted);
    font-size: 9pt;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
}
.screenplay {
    max-width: 650px;
    margin: 32px auto;
    padding: 0 24px 64px;
}
.scene-heading {
    font-weight: bold;
    text-decoration: underline;
    text-transform: uppercase;
    margin-top: 24px;
    margin-bottom: 12px;
}
.action {
    margin: 12px 0;
}
.character {
    text-align: center;
    text-transform: uppercase;
    margin-top: 12px;
    margin-bottom: 0;
    padding-left: 20%;
    padding-right: 20%;
}
.dialogue {
    text-align: center;
    margin: 0;
    padding-left: 15%;
    padding-right: 15%;
}
.parenthetical {
    text-align: center;
    font-style: italic;
    margin: 0;
    padding-left: 18%;
    padding-right: 18%;
}
.transition {
    text-align: right;
    text-transform: uppercase;
    margin: 12px 0;
}
.section {
    font-weight: bold;
    margin-top: 18px;
    margin-bottom: 6px;
}
.synopsis {
    font-style: italic;
    color: var(--muted);
    margin: 6px 0;
}
.note {
    font-style: italic;
    color: var(--muted);
    margin: 6px 0;
}
@media print {
    .watermark-layer { position: fixed; }
    .header { break-after: page; }
    .screenplay { max-width: 100%; margin: 0; padding: 0; }
    .scene-heading { break-after: avoid; }
    .character { break-after: avoid; }
    body { background: white; color: black; }
}
@media (max-width: 600px) {
    .screenplay { padding: 0 12px 32px; }
    .character { padding-left: 10%; padding-right: 10%; }
    .dialogue { padding-left: 8%; padding-right: 8%; }
    .parenthetical { padding-left: 10%; padding-right: 10%; }
    .header { padding: 16px; }
    .header h1 { font-size: 16pt; }
}
"""

_ELEMENT_CLASS = {
    "SceneHeading": "scene-heading",
    "Action": "action",
    "Character": "character",
    "Dialogue": "dialogue",
    "Parenthetical": "parenthetical",
    "Transition": "transition",
    "Section": "section",
    "Synopsis": "synopsis",
    "Note": "note",
}


def generate_review_html(
    content: str,
    title: str = "Untitled",
    author: str = "",
    watermark_text: str = "CONFIDENTIAL",
    include_title_page: bool = True,
    include_page_numbers: bool = True,
) -> str:
    """Return a complete self-contained HTML document for read-only review.

    Parameters
    ----------
    content:
        Raw Fountain screenplay text.
    title:
        Title shown in the header and ``<title>``.
    author:
        Author credit shown in the header.
    watermark_text:
        Text repeated diagonally across the page as a low-opacity watermark.
    include_title_page:
        Whether to include the title/author header block.
    include_page_numbers:
        Whether to include CSS-generated page numbers for print.
    """
    elements = _parse_fountain_to_elements(content)

    body_parts: list[str] = []
    for elem in elements:
        kind = elem["type"]
        if kind == "PageBreak":
            body_parts.append('<hr class="page-break" aria-hidden="true">')
            continue
        css_class = _ELEMENT_CLASS.get(kind, "action")
        body_parts.append(f'<p class="{css_class}">{escape(elem["text"])}</p>')

    screenplay_html = "\n".join(body_parts)

    wm_escaped = escape(watermark_text)
    watermark_spans = (f"<span>{wm_escaped}</span>" * 200) if watermark_text else ""

    header_html = ""
    if include_title_page:
        header_html = f"""\
<div class="header">
  <h1>{escape(title)}</h1>
  <p class="author">{escape(author)}</p>
  <p class="notice">Confidential — For Review Only</p>
</div>"""

    page_number_css = ""
    if include_page_numbers:
        page_number_css = """
@media print {
  @page { @bottom-right { content: counter(page); font-size: 10pt; color: var(--muted); } }
  .screenplay { counter-reset: page; }
}
.screenplay { counter-reset: screenplay-page; }
.page-break { counter-increment: screenplay-page; }
"""

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — Review</title>
<style>
{_CSS}
{page_number_css}
</style>
</head>
<body>
<div class="watermark-layer" aria-hidden="true">
  <div class="watermark-inner">
    {watermark_spans}
  </div>
</div>
{header_html}
<div class="screenplay">
{screenplay_html}
</div>
</body>
</html>
"""
    return html


def generate_share_link(html_content: str, project_path: str) -> str:
    """Save *html_content* to ``.ecrit/shares/`` and return the file path.

    The file is named with a UUID so each share is unique. A future server
    component can turn the local path into a URL.
    """
    shares_dir = os.path.join(project_path, ".ecrit", "shares")
    os.makedirs(shares_dir, exist_ok=True)

    share_id = uuid.uuid4().hex
    filename = f"{share_id}.html"
    filepath = os.path.join(shares_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filepath


def list_shares(project_path: str) -> list[dict]:
    """Return metadata for all shares in the project.

    Each dict has keys: ``id``, ``title``, ``created``, ``path``.
    """
    shares_dir = os.path.join(project_path, ".ecrit", "shares")
    if not os.path.isdir(shares_dir):
        return []

    results: list[dict] = []
    for name in os.listdir(shares_dir):
        if not name.endswith(".html"):
            continue

        share_id = name[:-5]  # strip .html
        filepath = os.path.join(shares_dir, name)

        # Extract title from the HTML <title> tag
        title = "Untitled"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                head = f.read(4096)
            m = re.search(r"<title>(.*?)</title>", head)
            if m:
                raw_title = m.group(1)
                # Strip the " — Review" suffix if present
                title = re.sub(r"\s*—\s*Review$", "", raw_title)
        except OSError:
            pass

        # File creation time
        try:
            stat = os.stat(filepath)
            created = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        except OSError:
            created = ""

        results.append({
            "id": share_id,
            "title": title,
            "created": created,
            "path": filepath,
        })

    # Sort newest first
    results.sort(key=lambda r: r["created"], reverse=True)
    return results


def delete_share(project_path: str, share_id: str) -> bool:
    """Delete a share by its id. Returns True if the file was removed."""
    safe_id = os.path.basename(share_id)
    if not safe_id or safe_id != share_id:
        return False
    shares_dir = os.path.join(project_path, ".ecrit", "shares")
    filepath = os.path.join(shares_dir, f"{safe_id}.html")
    if not os.path.realpath(filepath).startswith(os.path.realpath(shares_dir)):
        return False
    try:
        os.remove(filepath)
        return True
    except OSError:
        return False
