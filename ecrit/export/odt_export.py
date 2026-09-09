"""ODT export — generate Open Document Text from Fountain script."""

import json
import os
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape

from PySide6.QtWidgets import QFileDialog


CONTENT_XML_HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  office:version="1.2">
<office:automatic-styles>
  <style:style style:name="SceneHeading" style:family="paragraph">
    <style:paragraph-properties fo:margin-top="0.25in" fo:margin-bottom="0in"/>
    <style:text-properties fo:font-weight="bold" fo:text-transform="uppercase"
      style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="Action" style:family="paragraph">
    <style:paragraph-properties fo:margin-top="0.12in" fo:margin-bottom="0in"/>
    <style:text-properties style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="Character" style:family="paragraph">
    <style:paragraph-properties fo:margin-top="0.12in" fo:margin-left="2in" fo:text-align="left"/>
    <style:text-properties fo:text-transform="uppercase" style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="Dialogue" style:family="paragraph">
    <style:paragraph-properties fo:margin-left="1in" fo:margin-right="1.5in"/>
    <style:text-properties style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="Parenthetical" style:family="paragraph">
    <style:paragraph-properties fo:margin-left="1.5in"/>
    <style:text-properties style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="Transition" style:family="paragraph">
    <style:paragraph-properties fo:margin-top="0.12in" fo:text-align="right"/>
    <style:text-properties fo:text-transform="uppercase" style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="Section" style:family="paragraph">
    <style:paragraph-properties fo:margin-top="0.2in"/>
    <style:text-properties fo:font-weight="bold" style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
  <style:style style:name="Note" style:family="paragraph">
    <style:text-properties fo:font-style="italic" style:font-name="Courier Prime" fo:font-size="12pt"/>
  </style:style>
</office:automatic-styles>
<office:body>
<office:text>
"""

CONTENT_XML_TAIL = """</office:text>
</office:body>
</office:document-content>"""

MANIFEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
  manifest:version="1.2">
  <manifest:file-entry manifest:full-path="/" manifest:version="1.2"
    manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml"
    manifest:media-type="text/xml"/>
</manifest:manifest>"""

STYLE_MAP = {
    "SceneHeading": "SceneHeading",
    "Action": "Action",
    "Character": "Character",
    "Dialogue": "Dialogue",
    "Parenthetical": "Parenthetical",
    "Transition": "Transition",
    "Section": "Section",
    "Synopsis": "Note",
    "Note": "Note",
    "Lyric": "Dialogue",
    "BlankLine": "Action",
}


def _build_content_xml(script_content: str) -> str:
    try:
        import ecrit_core
        parsed = json.loads(ecrit_core.parse_fountain(script_content))
    except Exception:
        return CONTENT_XML_HEAD + f"<text:p>{escape(script_content)}</text:p>" + CONTENT_XML_TAIL

    parts = [CONTENT_XML_HEAD]

    for elem in parsed.get("elements", []):
        kind = elem.get("type", "Action")
        text = elem.get("text", "")
        style = STYLE_MAP.get(kind, "Action")

        if kind == "PageBreak":
            parts.append('<text:p text:style-name="Action"/>')
            continue
        if kind == "BlankLine":
            parts.append(f'<text:p text:style-name="Action"/>')
            continue

        parts.append(f'<text:p text:style-name="{style}">{escape(text)}</text:p>')

    parts.append(CONTENT_XML_TAIL)
    return "\n".join(parts)


def _create_odt_bytes(script_content: str) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        zf.writestr("META-INF/manifest.xml", MANIFEST_XML)
        zf.writestr("content.xml", _build_content_xml(script_content))
    return buf.getvalue()


def export_odt(script_content: str, title: str = "Untitled", parent=None) -> str:
    default_name = f"{title}.odt"
    path, _ = QFileDialog.getSaveFileName(
        parent, "Export ODT",
        default_name,
        "OpenDocument Text (*.odt);;All files (*)"
    )
    if not path:
        return ""

    if not path.endswith(".odt"):
        path += ".odt"

    data = _create_odt_bytes(script_content)
    with open(path, 'wb') as f:
        f.write(data)
    return path


def export_odt_to_path(script_content: str, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = _create_odt_bytes(script_content)
    with open(path, 'wb') as f:
        f.write(data)
