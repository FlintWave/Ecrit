"""Import Final Draft .fdx files and convert to Fountain format."""

import xml.etree.ElementTree as ET


_FDX_TYPE_MAP = {
    "Scene Heading": "scene_heading",
    "Action": "action",
    "Character": "character",
    "Dialogue": "dialogue",
    "Parenthetical": "parenthetical",
    "Transition": "transition",
    "General": "action",
    "Shot": "action",
}


def fdx_to_fountain(fdx_content: str) -> str:
    try:
        root = ET.fromstring(fdx_content)
    except ET.ParseError:
        return ""

    lines: list[str] = []
    title_page = root.find(".//TitlePage")
    if title_page is not None:
        for para in title_page.iter("Paragraph"):
            ptype = para.get("Type", "")
            text_parts = []
            for t in para.iter("Text"):
                if t.text:
                    text_parts.append(t.text)
            text = "".join(text_parts).strip()
            if not text:
                continue
            if ptype == "Title":
                lines.append(f"Title: {text}")
            elif ptype in ("Written by", "Credit"):
                lines.append(f"Credit: {text}")
            elif ptype == "Author":
                lines.append(f"Author: {text}")
            elif ptype == "Draft":
                lines.append(f"Draft date: {text}")
            elif ptype == "Source":
                lines.append(f"Source: {text}")
            elif ptype == "Contact":
                lines.append(f"Contact: {text}")
            else:
                lines.append(f"{ptype}: {text}")
        if lines:
            lines.append("")

    content = root.find(".//Content")
    if content is None:
        return "\n".join(lines)

    prev_type = ""
    for para in content.iter("Paragraph"):
        ptype = para.get("Type", "Action")
        mapped = _FDX_TYPE_MAP.get(ptype, "action")

        text_parts = []
        for t in para.iter("Text"):
            style = t.get("Style", "")
            txt = t.text or ""
            if "Bold" in style and "Italic" in style:
                txt = f"***{txt}***"
            elif "Bold" in style:
                txt = f"**{txt}**"
            elif "Italic" in style:
                txt = f"*{txt}*"
            if "Underline" in style:
                txt = f"_{txt}_"
            text_parts.append(txt)
        text = "".join(text_parts).strip()

        if not text and mapped != "action":
            continue

        if mapped == "scene_heading":
            if prev_type:
                lines.append("")
            lines.append(text.upper() if not text.startswith(("INT", "EXT", "EST", "I/E")) else text)
        elif mapped == "character":
            lines.append("")
            lines.append(text)
        elif mapped == "dialogue":
            lines.append(text)
        elif mapped == "parenthetical":
            if not text.startswith("("):
                text = f"({text})"
            lines.append(text)
        elif mapped == "transition":
            lines.append("")
            lines.append(f"> {text}")
        else:
            if prev_type not in ("", "action"):
                lines.append("")
            lines.append(text)

        prev_type = mapped

    return "\n".join(lines) + "\n"


def import_fdx_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return fdx_to_fountain(content)
