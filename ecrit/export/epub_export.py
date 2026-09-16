"""EPUB 3 export — generate a valid EPUB ebook from Fountain screenplay content."""

import os
import re
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape
from io import BytesIO

from PySide6.QtWidgets import QFileDialog


def _parse_title_page(content: str) -> dict[str, str]:
    """Extract Fountain title page key-value pairs."""
    fields: dict[str, str] = {}
    title_page_re = re.compile(
        r"\A([ \t]*[A-Za-z ]+:.*\n(?:(?:[ \t]+.*|[ \t]*[A-Za-z ]+:.*)?\n)*)\n",
        re.MULTILINE,
    )
    m = title_page_re.match(content)
    if not m:
        return fields

    current_key = ""
    for line in m.group(1).split("\n"):
        kv = re.match(r"^[ \t]*([A-Za-z ]+):\s*(.*)", line)
        if kv:
            current_key = kv.group(1).strip().lower()
            fields[current_key] = kv.group(2).strip()
        elif current_key and line.strip():
            fields[current_key] += " " + line.strip()

    return fields


def _parse_fountain_to_elements(content: str) -> list[dict]:
    """Simple regex-based Fountain parser returning typed elements.

    Each element is {"type": str, "text": str} where type is one of:
    SceneHeading, Character, Dialogue, Parenthetical, Action,
    Transition, Section, Synopsis, Note, PageBreak.
    """
    elements: list[dict] = []

    # Strip title page
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

        # Synopsis: starts with = (but not ==)
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

        # Character name: ALL CAPS possibly with (V.O.), (O.S.), (CONT'D)
        char_match = re.match(r"^(@?.+)$", stripped)
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
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and lines[j].strip():
                    elements.append({"type": "Character", "text": candidate})
                    i = j

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


def _generate_css() -> str:
    """Return screenplay-appropriate CSS for e-readers."""
    return """\
body {
    font-family: "Courier New", Courier, monospace;
    font-size: 12pt;
    line-height: 1.5;
    margin: 1em;
    padding: 0;
}
h1.title {
    font-family: "Courier New", Courier, monospace;
    font-size: 24pt;
    text-align: center;
    margin-top: 30%;
    margin-bottom: 0.5em;
}
p.author {
    font-family: "Courier New", Courier, monospace;
    font-size: 14pt;
    text-align: center;
    margin-top: 1em;
}
p.title-field {
    font-family: "Courier New", Courier, monospace;
    font-size: 11pt;
    text-align: center;
    margin: 0.3em 0;
}
h2.scene-heading {
    font-family: "Courier New", Courier, monospace;
    font-size: 12pt;
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    page-break-before: always;
}
h2.scene-heading:first-of-type {
    page-break-before: avoid;
}
p.action {
    margin: 0.8em 0;
}
p.character {
    text-align: center;
    text-transform: uppercase;
    margin-top: 1em;
    margin-bottom: 0;
}
p.dialogue {
    margin: 0;
    margin-left: 25%;
    max-width: 50%;
}
p.parenthetical {
    margin: 0;
    margin-left: 30%;
    font-style: italic;
}
p.transition {
    text-align: right;
    text-transform: uppercase;
    margin: 1em 0;
}
p.section {
    font-weight: bold;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
}
p.synopsis {
    font-style: italic;
    color: #666666;
    margin: 0.4em 0;
}
p.note {
    font-style: italic;
    color: #666666;
    margin: 0.4em 0;
}
hr.page-break {
    border: none;
    page-break-after: always;
}
"""


def _generate_container_xml() -> str:
    """Return META-INF/container.xml content."""
    return '<?xml version="1.0" encoding="UTF-8"?>\n' \
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n' \
        '  <rootfiles>\n' \
        '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n' \
        '  </rootfiles>\n' \
        '</container>'


def _generate_content_opf(title: str, author: str, uid: str) -> str:
    """Return OEBPS/content.opf package document."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n' \
        f'<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">\n' \
        f'  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n' \
        f'    <dc:identifier id="uid">urn:uuid:{escape(uid)}</dc:identifier>\n' \
        f'    <dc:title>{escape(title)}</dc:title>\n' \
        f'    <dc:creator>{escape(author)}</dc:creator>\n' \
        f'    <dc:language>en</dc:language>\n' \
        f'    <meta property="dcterms:modified">{now}</meta>\n' \
        f'  </metadata>\n' \
        f'  <manifest>\n' \
        f'    <item id="style" href="stylesheet.css" media-type="text/css"/>\n' \
        f'    <item id="nav" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n' \
        f'    <item id="titlepage" href="title.xhtml" media-type="application/xhtml+xml"/>\n' \
        f'    <item id="script" href="script.xhtml" media-type="application/xhtml+xml"/>\n' \
        f'  </manifest>\n' \
        f'  <spine>\n' \
        f'    <itemref idref="titlepage"/>\n' \
        f'    <itemref idref="script"/>\n' \
        f'  </spine>\n' \
        f'</package>'


def _generate_toc(title: str, scenes: list[dict]) -> str:
    """Return OEBPS/toc.xhtml navigation document.

    *scenes* is a list of {"id": str, "text": str} dicts for scene headings.
    """
    nav_items = f'      <li><a href="title.xhtml">Title Page</a></li>\n'
    nav_items += f'      <li><a href="script.xhtml">Script</a></li>\n'
    for scene in scenes:
        sid = escape(scene["id"])
        stext = escape(scene["text"])
        nav_items += f'      <li><a href="script.xhtml#{sid}">{stext}</a></li>\n'

    return f'<?xml version="1.0" encoding="UTF-8"?>\n' \
        f'<!DOCTYPE html>\n' \
        f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n' \
        f'<head>\n' \
        f'  <meta charset="utf-8"/>\n' \
        f'  <title>{escape(title)}</title>\n' \
        f'  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>\n' \
        f'</head>\n' \
        f'<body>\n' \
        f'  <nav epub:type="toc" id="toc">\n' \
        f'    <h1>Table of Contents</h1>\n' \
        f'    <ol>\n' \
        f'{nav_items}' \
        f'    </ol>\n' \
        f'  </nav>\n' \
        f'</body>\n' \
        f'</html>'


def _generate_title_page(title: str, author: str, extra_fields: dict[str, str] | None = None) -> str:
    """Return OEBPS/title.xhtml content."""
    extra_html = ""
    if extra_fields:
        for key, value in extra_fields.items():
            if key in ("title", "author"):
                continue
            label = key.replace("_", " ").title()
            extra_html += f'  <p class="title-field">{escape(label)}: {escape(value)}</p>\n'

    return f'<?xml version="1.0" encoding="UTF-8"?>\n' \
        f'<!DOCTYPE html>\n' \
        f'<html xmlns="http://www.w3.org/1999/xhtml">\n' \
        f'<head>\n' \
        f'  <meta charset="utf-8"/>\n' \
        f'  <title>{escape(title)}</title>\n' \
        f'  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>\n' \
        f'</head>\n' \
        f'<body>\n' \
        f'  <h1 class="title">{escape(title)}</h1>\n' \
        f'  <p class="author">{escape(author)}</p>\n' \
        f'{extra_html}' \
        f'</body>\n' \
        f'</html>'


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


def _parse_fountain_to_xhtml(content: str) -> tuple[str, list[dict]]:
    """Convert Fountain text to XHTML body content.

    Returns a tuple of (xhtml_body_content, scenes) where scenes is a list
    of {"id": str, "text": str} dicts for the table of contents.
    """
    elements = _parse_fountain_to_elements(content)

    parts: list[str] = []
    scenes: list[dict] = []
    scene_count = 0

    for elem in elements:
        kind = elem["type"]
        text = escape(elem["text"])

        if kind == "PageBreak":
            parts.append('  <hr class="page-break"/>')
            continue

        if kind == "SceneHeading":
            scene_count += 1
            scene_id = f"scene-{scene_count}"
            scenes.append({"id": scene_id, "text": elem["text"]})
            parts.append(f'  <h2 class="scene-heading" id="{scene_id}">{text}</h2>')
            continue

        css_class = _ELEMENT_CLASS.get(kind, "action")
        parts.append(f'  <p class="{css_class}">{text}</p>')

    return "\n".join(parts), scenes


def _generate_script_xhtml(title: str, body_content: str) -> str:
    """Return OEBPS/script.xhtml with the screenplay body."""
    return f'<?xml version="1.0" encoding="UTF-8"?>\n' \
        f'<!DOCTYPE html>\n' \
        f'<html xmlns="http://www.w3.org/1999/xhtml">\n' \
        f'<head>\n' \
        f'  <meta charset="utf-8"/>\n' \
        f'  <title>{escape(title)}</title>\n' \
        f'  <link rel="stylesheet" type="text/css" href="stylesheet.css"/>\n' \
        f'</head>\n' \
        f'<body>\n' \
        f'{body_content}\n' \
        f'</body>\n' \
        f'</html>'


def _create_epub_bytes(content: str, title: str = "", author: str = "") -> bytes:
    """Build a complete EPUB 3 file in memory and return the bytes."""
    # Extract title page fields from the Fountain content
    tp_fields = _parse_title_page(content)

    if not title:
        title = tp_fields.get("title", "Untitled Screenplay")
    if not author:
        author = tp_fields.get("author", "")

    uid = str(uuid.uuid4())

    # Parse screenplay body into XHTML
    body_content, scenes = _parse_fountain_to_xhtml(content)

    # Build the EPUB ZIP
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be first entry, stored (not compressed)
        zf.writestr(
            zipfile.ZipInfo("mimetype", date_time=(2020, 1, 1, 0, 0, 0)),
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )

        zf.writestr("META-INF/container.xml", _generate_container_xml())
        zf.writestr("OEBPS/content.opf", _generate_content_opf(title, author, uid))
        zf.writestr("OEBPS/toc.xhtml", _generate_toc(title, scenes))
        zf.writestr("OEBPS/stylesheet.css", _generate_css())
        zf.writestr("OEBPS/title.xhtml", _generate_title_page(title, author, tp_fields))
        zf.writestr(
            "OEBPS/script.xhtml",
            _generate_script_xhtml(title, body_content),
        )

    return buf.getvalue()


def export_epub(content: str, title: str = "", author: str = "", output_path: str = "", parent=None) -> str:
    """Export Fountain content as an EPUB file.

    If *output_path* is empty, opens a file-save dialog. Returns the path
    written, or an empty string if cancelled.
    """
    if not title:
        tp = _parse_title_page(content)
        title = tp.get("title", "Untitled")

    if not output_path:
        default_name = f"{title}.epub"
        path, _ = QFileDialog.getSaveFileName(
            parent, "Export EPUB",
            default_name,
            "EPUB files (*.epub);;All files (*)",
        )
        if not path:
            return ""
        output_path = path

    if not output_path.endswith(".epub"):
        output_path += ".epub"

    data = _create_epub_bytes(content, title=title, author=author)
    with open(output_path, "wb") as f:
        f.write(data)

    return output_path


def export_epub_to_path(content: str, path: str, title: str = "", author: str = "") -> bool:
    """Export Fountain content as an EPUB to a specific path.

    Returns True on success, False on failure.
    """
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        data = _create_epub_bytes(content, title=title, author=author)
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False
