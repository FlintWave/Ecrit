"""Production reports generated from Fountain screenplay scripts.

Parses raw Fountain text and produces structured data for common
pre-production and production reports: scene breakdown, cast list,
location summary, day/night tally, and one-liner / sides.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LINES_PER_PAGE = 55

# Fountain scene heading prefixes (case-insensitive)
_SCENE_HEADING_RE = re.compile(
    r"^(\.(?=\S)|(?:INT|EXT|EST|INT\./EXT|INT/EXT|I/E)[\.\s])",
    re.IGNORECASE,
)

# Character cue: an all-caps line (possibly with a parenthetical extension)
# preceded by a blank line.  Fountain spec says the line must be uppercase
# (letters only; digits allowed but the line must contain at least one letter).
_CHARACTER_CUE_RE = re.compile(
    r"^@?([A-Z][A-Z0-9 .\-']+?)(?:\s*\(.*\))?$"
)

# Time-of-day tokens commonly found at the end of scene headings after " - "
_TIME_OF_DAY_TOKENS = [
    "MOMENTS LATER",
    "CONTINUOUS",
    "LATER",
    "DAWN",
    "DUSK",
    "DAY",
    "NIGHT",
    "MORNING",
    "AFTERNOON",
    "EVENING",
    "SUNSET",
    "SUNRISE",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _parse_scene_heading(heading: str) -> dict[str, str]:
    """Extract int_ext, location, and time_of_day from a scene heading.

    Example
    -------
    >>> _parse_scene_heading("INT. COFFEE SHOP - DAY")
    {'int_ext': 'INT', 'location': 'COFFEE SHOP', 'time_of_day': 'DAY'}
    """
    raw = heading.strip()
    # Strip forced scene heading marker
    if raw.startswith(".") and not raw.startswith(".."):
        raw = raw[1:].strip()

    int_ext = ""
    location = raw
    time_of_day = ""

    # Detect INT/EXT prefix
    ie_match = re.match(
        r"^(INT\./EXT|INT/EXT|I/E|INT|EXT|EST)[.\s]+(.*)$",
        raw,
        re.IGNORECASE,
    )
    if ie_match:
        int_ext = ie_match.group(1).upper().replace(" ", "")
        # Normalize compound forms
        if int_ext in ("INT./EXT", "INT/EXT", "I/E"):
            int_ext = "INT/EXT"
        location = ie_match.group(2).strip()

    # Split on last " - " to isolate time of day
    if " - " in location:
        parts = location.rsplit(" - ", 1)
        candidate = parts[1].strip().upper()
        # Accept known tokens or anything that looks like a time marker
        for token in _TIME_OF_DAY_TOKENS:
            if candidate == token or candidate.startswith(token):
                time_of_day = candidate
                location = parts[0].strip()
                break
        if not time_of_day:
            # Still treat the trailing segment as time of day if it is short
            # (a common screenplay convention even for unusual descriptors).
            if len(candidate.split()) <= 3:
                time_of_day = candidate
                location = parts[0].strip()

    # Clean up location
    location = location.strip().rstrip("-").strip()

    return {
        "int_ext": int_ext,
        "location": location,
        "time_of_day": time_of_day,
    }


def _estimate_page(line_index: int, total_lines: int) -> float:
    """Return a rough page number for a given line index.

    Uses 55 lines per page (standard screenplay pagination).
    """
    if total_lines == 0:
        return 1.0
    return round(line_index / _LINES_PER_PAGE + 1, 2)


def _is_scene_heading(line: str) -> bool:
    """Return True if *line* is a Fountain scene heading."""
    stripped = line.strip()
    if not stripped:
        return False
    return bool(_SCENE_HEADING_RE.match(stripped))


def _extract_characters_in_scene(
    lines: list[str], start: int, end: int
) -> list[str]:
    """Find unique character names between *start* and *end* line indices.

    A character cue in Fountain is an all-uppercase line that follows an
    empty line (we also accept the ``@`` forced-character prefix).
    """
    characters: list[str] = []
    seen: set[str] = set()

    for i in range(start, min(end, len(lines))):
        line = lines[i].strip()
        if not line:
            continue

        # Must follow a blank line (or be the first line of the scene body)
        prev_blank = i == start or (i > 0 and lines[i - 1].strip() == "")
        if not prev_blank:
            continue

        # Check for forced character marker
        if line.startswith("@"):
            name = line[1:].strip()
            # Strip parenthetical extension
            name = re.sub(r"\s*\(.*\)$", "", name).strip()
            if name:
                key = name.upper()
                if key not in seen:
                    seen.add(key)
                    characters.append(key)
            continue

        m = _CHARACTER_CUE_RE.match(line)
        if m:
            name = m.group(1).strip()
            key = name.upper()
            if key not in seen:
                seen.add(key)
                characters.append(key)

    return characters


def _find_scene_boundaries(lines: list[str]) -> list[dict[str, Any]]:
    """Return a list of scenes with their line boundaries and headings."""
    scenes: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        if _is_scene_heading(line):
            scenes.append({
                "heading": line.strip(),
                "start": i,
                "end": len(lines),  # will be patched below
            })
    # Patch end boundaries
    for idx in range(len(scenes) - 1):
        scenes[idx]["end"] = scenes[idx + 1]["start"]
    return scenes


# ---------------------------------------------------------------------------
# Public report generators
# ---------------------------------------------------------------------------


def generate_scene_report(script: str) -> list[dict]:
    """Generate a per-scene breakdown report.

    Each dict contains:
        number, heading, location, time_of_day, int_ext, characters,
        page_start, page_end, estimated_minutes
    """
    lines = script.split("\n")
    total_lines = len(lines)
    scenes = _find_scene_boundaries(lines)
    report: list[dict] = []

    for idx, sc in enumerate(scenes, start=1):
        parsed = _parse_scene_heading(sc["heading"])
        characters = _extract_characters_in_scene(lines, sc["start"] + 1, sc["end"])
        page_start = _estimate_page(sc["start"], total_lines)
        page_end = _estimate_page(sc["end"] - 1, total_lines)
        scene_lines = sc["end"] - sc["start"]
        estimated_minutes = round(scene_lines / _LINES_PER_PAGE, 2)

        report.append({
            "number": idx,
            "heading": sc["heading"],
            "location": parsed["location"],
            "time_of_day": parsed["time_of_day"],
            "int_ext": parsed["int_ext"],
            "characters": characters,
            "page_start": page_start,
            "page_end": page_end,
            "estimated_minutes": estimated_minutes,
        })

    return report


def generate_cast_report(script: str) -> list[dict]:
    """Generate a per-character cast report.

    Each dict contains:
        name, scene_count, dialogue_lines, dialogue_words,
        first_scene, last_scene
    """
    lines = script.split("\n")
    scenes = _find_scene_boundaries(lines)

    # Track per-character data
    cast: dict[str, dict] = {}

    for scene_num, sc in enumerate(scenes, start=1):
        in_dialogue = False
        current_character: str | None = None

        for i in range(sc["start"] + 1, sc["end"]):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                in_dialogue = False
                current_character = None
                continue

            # Check for character cue
            prev_blank = i == sc["start"] + 1 or lines[i - 1].strip() == ""
            is_char_cue = False
            char_name: str | None = None

            if prev_blank:
                if stripped.startswith("@"):
                    char_name = re.sub(r"\s*\(.*\)$", "", stripped[1:]).strip().upper()
                    is_char_cue = True
                else:
                    m = _CHARACTER_CUE_RE.match(stripped)
                    if m:
                        char_name = m.group(1).strip().upper()
                        is_char_cue = True

            if is_char_cue and char_name:
                current_character = char_name
                in_dialogue = True

                if char_name not in cast:
                    cast[char_name] = {
                        "name": char_name,
                        "scenes": set(),
                        "dialogue_lines": 0,
                        "dialogue_words": 0,
                        "first_scene": scene_num,
                        "last_scene": scene_num,
                    }
                cast[char_name]["scenes"].add(scene_num)
                cast[char_name]["last_scene"] = scene_num
                continue

            # Parenthetical — skip but keep dialogue context
            if in_dialogue and stripped.startswith("(") and stripped.endswith(")"):
                continue

            # Dialogue line
            if in_dialogue and current_character and current_character in cast:
                cast[current_character]["dialogue_lines"] += 1
                cast[current_character]["dialogue_words"] += len(stripped.split())

    # Build sorted report
    report: list[dict] = []
    for name in sorted(cast):
        info = cast[name]
        report.append({
            "name": info["name"],
            "scene_count": len(info["scenes"]),
            "dialogue_lines": info["dialogue_lines"],
            "dialogue_words": info["dialogue_words"],
            "first_scene": info["first_scene"],
            "last_scene": info["last_scene"],
        })

    return report


def generate_location_report(script: str) -> list[dict]:
    """Generate a location summary report.

    Each dict contains:
        location, scene_count, scenes (list of scene numbers), total_pages
    """
    lines = script.split("\n")
    total_lines = len(lines)
    scenes = _find_scene_boundaries(lines)

    locations: dict[str, dict] = {}

    for idx, sc in enumerate(scenes, start=1):
        parsed = _parse_scene_heading(sc["heading"])
        loc = parsed["location"].upper()
        if not loc:
            continue

        scene_pages = (sc["end"] - sc["start"]) / _LINES_PER_PAGE

        if loc not in locations:
            locations[loc] = {
                "location": loc,
                "scene_count": 0,
                "scenes": [],
                "total_pages": 0.0,
            }
        locations[loc]["scene_count"] += 1
        locations[loc]["scenes"].append(idx)
        locations[loc]["total_pages"] += scene_pages

    report: list[dict] = []
    for loc in sorted(locations):
        entry = locations[loc]
        entry["total_pages"] = round(entry["total_pages"], 2)
        report.append(entry)

    return report


def generate_day_night_report(script: str) -> dict[str, list[int]]:
    """Generate a day/night tally.

    Returns a dict mapping time-of-day categories to lists of scene numbers.
    """
    lines = script.split("\n")
    scenes = _find_scene_boundaries(lines)

    result: dict[str, list[int]] = {}

    for idx, sc in enumerate(scenes, start=1):
        parsed = _parse_scene_heading(sc["heading"])
        tod = parsed["time_of_day"].upper() if parsed["time_of_day"] else "UNKNOWN"
        result.setdefault(tod, []).append(idx)

    return result


def generate_one_liner(script: str) -> list[dict]:
    """Generate a one-liner / sides report.

    Each dict contains:
        number, heading, summary
    The summary is the scene heading followed by the first action line,
    truncated to 80 characters.
    """
    lines = script.split("\n")
    scenes = _find_scene_boundaries(lines)
    report: list[dict] = []

    for idx, sc in enumerate(scenes, start=1):
        heading = sc["heading"]
        # Find the first non-empty, non-heading, non-character-cue action line
        first_action = ""
        for i in range(sc["start"] + 1, sc["end"]):
            stripped = lines[i].strip()
            if not stripped:
                continue
            # Skip character cues and parentheticals and dialogue (heuristic)
            if _CHARACTER_CUE_RE.match(stripped):
                continue
            if stripped.startswith("@"):
                continue
            if stripped.startswith("(") and stripped.endswith(")"):
                continue
            # Skip transition lines
            if stripped.endswith("TO:") and stripped.isupper():
                continue
            first_action = stripped
            break

        if first_action:
            summary = f"{heading} -- {first_action}"
        else:
            summary = heading

        if len(summary) > 80:
            summary = summary[:77] + "..."

        report.append({
            "number": idx,
            "heading": heading,
            "summary": summary,
        })

    return report
