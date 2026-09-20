"""Bidirectional sync between outline nodes and Fountain script content."""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger("ecrit.screenplay.outline_sync")

try:
    import ecrit_core
except ImportError:
    ecrit_core = None


def outline_to_script(nodes: list[dict], format_id: str = "fountain/core") -> str:
    """Generate a Fountain script skeleton from outline nodes.

    For comic formats, Page/Panel/Spread nodes produce comic Fountain syntax.
    For screenplay formats, ActBreak/Scene nodes produce standard Fountain.
    """
    is_comic = format_id.startswith("fountain+comic")
    lines: list[str] = []

    sorted_nodes = _topo_sort(nodes)

    for node in sorted_nodes:
        kind = node.get("kind", "Scene")
        label = node.get("label") or ""
        synopsis = node.get("synopsis") or ""

        if is_comic:
            if kind == "Page":
                lines.append("")
                lines.append(f"# {label.upper()}")
                if synopsis:
                    lines.append(f"= {synopsis}")
                lines.append("")
            elif kind == "Spread":
                lines.append("")
                lines.append(f"# {label.upper()}")
                if synopsis:
                    lines.append(f"= {synopsis}")
                lines.append("")
            elif kind == "Panel":
                panel_label = label
                if not panel_label.upper().startswith("PANEL"):
                    panel_label = f"PANEL {panel_label}"
                lines.append(panel_label.upper())
                if synopsis:
                    lines.append("")
                    lines.append(synopsis)
                lines.append("")
            elif kind == "Note":
                lines.append(f"[[{synopsis or label}]]")
                lines.append("")
            else:
                if synopsis:
                    lines.append(synopsis)
                    lines.append("")
        else:
            if kind == "ActBreak":
                lines.append("")
                lines.append(f"# {label}")
                if synopsis:
                    lines.append(f"= {synopsis}")
                lines.append("")
            elif kind == "Scene":
                heading = label
                if not any(heading.upper().startswith(p) for p in ("INT.", "EXT.", "INT/EXT", "EST.", "I/E.")):
                    heading = f"INT. {heading.upper()} - DAY"
                lines.append(heading)
                if synopsis:
                    lines.append(f"= {synopsis}")
                lines.append("")
                lines.append("")
            elif kind == "Transition":
                lines.append(f"{label.upper()} TO:")
                lines.append("")
            elif kind == "Note":
                lines.append(f"[[{synopsis or label}]]")
                lines.append("")

    return "\n".join(lines).strip() + "\n"


def script_to_outline(script: str, format_id: str = "fountain/core") -> list[dict]:
    """Parse a Fountain script and generate outline nodes from its structure.

    For comic formats, extracts Page/Panel/Spread structure.
    For screenplay formats, extracts Scene/ActBreak structure.
    """
    is_comic = format_id.startswith("fountain+comic")
    elements = _parse_elements(script, format_id)

    nodes: list[dict] = []
    node_id = 0
    prev_id: str | None = None

    x_start = 40
    y_start = 40
    row_height = 130
    col_width = 220
    current_row = -1
    col_in_row = 0

    if is_comic:
        for elem in elements:
            etype = elem.get("type", "")

            if etype == "PageHeader":
                current_row += 1
                col_in_row = 0
                kind = "Page"
                text = elem.get("text", "")
                if "SPREAD" in text.upper():
                    kind = "Spread"
                nid = f"sync_{node_id}"
                node_id += 1
                node = {
                    "id": nid,
                    "x": x_start,
                    "y": y_start + current_row * row_height,
                    "kind": kind,
                    "label": text,
                    "synopsis": "",
                    "connections": [],
                }
                if prev_id is not None:
                    _connect(nodes, prev_id, nid)
                nodes.append(node)
                prev_id = nid

            elif etype == "PanelHeader":
                col_in_row += 1
                nid = f"sync_{node_id}"
                node_id += 1
                node = {
                    "id": nid,
                    "x": x_start + col_in_row * col_width,
                    "y": y_start + max(current_row, 0) * row_height,
                    "kind": "Panel",
                    "label": elem.get("text", ""),
                    "synopsis": "",
                    "connections": [],
                }
                if prev_id is not None:
                    _connect(nodes, prev_id, nid)
                nodes.append(node)
                prev_id = nid

            elif etype in ("Action", "Dialogue", "Caption", "Sfx"):
                if nodes:
                    last = nodes[-1]
                    text = elem.get("text", "")
                    cur = last.get("synopsis") or ""
                    if len(cur) < 200:
                        if cur:
                            last["synopsis"] = cur + f" / {text[:60]}"
                        else:
                            last["synopsis"] = text[:80]
    else:
        for elem in elements:
            etype = elem.get("type", "")

            if etype == "Section":
                current_row += 1
                col_in_row = 0
                nid = f"sync_{node_id}"
                node_id += 1
                node = {
                    "id": nid,
                    "x": x_start,
                    "y": y_start + current_row * row_height,
                    "kind": "ActBreak",
                    "label": elem.get("text", ""),
                    "synopsis": "",
                    "connections": [],
                }
                if prev_id is not None:
                    _connect(nodes, prev_id, nid)
                nodes.append(node)
                prev_id = nid

            elif etype == "SceneHeading":
                col_in_row += 1
                nid = f"sync_{node_id}"
                node_id += 1
                node = {
                    "id": nid,
                    "x": x_start + col_in_row * col_width,
                    "y": y_start + max(current_row, 0) * row_height,
                    "kind": "Scene",
                    "label": elem.get("text", ""),
                    "synopsis": "",
                    "connections": [],
                }
                if prev_id is not None:
                    _connect(nodes, prev_id, nid)
                nodes.append(node)
                prev_id = nid

            elif etype == "Transition":
                col_in_row += 1
                nid = f"sync_{node_id}"
                node_id += 1
                node = {
                    "id": nid,
                    "x": x_start + col_in_row * col_width,
                    "y": y_start + max(current_row, 0) * row_height,
                    "kind": "Transition",
                    "label": elem.get("text", ""),
                    "synopsis": "",
                    "connections": [],
                }
                if prev_id is not None:
                    _connect(nodes, prev_id, nid)
                nodes.append(node)
                prev_id = nid

            elif etype == "Synopsis":
                if nodes:
                    nodes[-1]["synopsis"] = elem.get("text", "")

            elif etype in ("Action", "Dialogue"):
                if nodes and not nodes[-1].get("synopsis"):
                    nodes[-1]["synopsis"] = elem.get("text", "")[:80]

    return nodes


def _connect(nodes: list[dict], from_id: int, to_id: int):
    for n in nodes:
        if n["id"] == from_id:
            n["connections"].append(to_id)
            return


def _parse_elements(script: str, format_id: str) -> list[dict]:
    if ecrit_core:
        try:
            doc = json.loads(ecrit_core.parse_fountain(script, format_id))
            return doc.get("elements", [])
        except Exception:
            logger.debug("ecrit_core parse failed, using fallback", exc_info=True)
    return _parse_elements_fallback(script)


def _parse_elements_fallback(script: str) -> list[dict]:
    elements = []
    for line in script.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            text = stripped.lstrip("#").strip()
            if re.match(r"(?i)^PAGE\s", text):
                elements.append({"type": "PageHeader", "text": text})
            elif re.match(r"(?i)^SPREAD[\s(]", text):
                elements.append({"type": "PageHeader", "text": text})
            else:
                elements.append({"type": "Section", "text": text})
        elif re.match(r"(?i)^\.?PANEL\s", stripped):
            elements.append({"type": "PanelHeader", "text": stripped})
        elif stripped.startswith(("INT.", "EXT.", "INT/EXT", "EST.", "I/E.")):
            elements.append({"type": "SceneHeading", "text": stripped})
        elif stripped.startswith("="):
            elements.append({"type": "Synopsis", "text": stripped[1:].strip()})
        elif stripped.endswith("TO:") and stripped.isupper():
            elements.append({"type": "Transition", "text": stripped})
        else:
            elements.append({"type": "Action", "text": stripped})
    return elements


def _topo_sort(nodes: list[dict]) -> list[dict]:
    """Sort nodes following connection order. Falls back to position-based if no connections."""
    if not nodes:
        return []

    id_map = {n["id"]: n for n in nodes}
    has_incoming = set()
    for n in nodes:
        for cid in n.get("connections", []):
            has_incoming.add(cid)

    roots = [n for n in nodes if n["id"] not in has_incoming]
    if not roots:
        return sorted(nodes, key=lambda n: (n.get("y", 0), n.get("x", 0)))

    visited: set = set()
    result = []

    for root in sorted(roots, key=lambda n: (n.get("y", 0), n.get("x", 0))):
        stack = [root]
        while stack:
            node = stack.pop()
            nid = node["id"]
            if nid in visited:
                continue
            visited.add(nid)
            result.append(node)
            for cid in reversed(node.get("connections", [])):
                if cid in id_map and cid not in visited:
                    stack.append(id_map[cid])

    for n in nodes:
        if n["id"] not in visited:
            result.append(n)

    return result
