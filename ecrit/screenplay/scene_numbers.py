"""Scene number assignment, locking, and renumbering for Fountain scripts.

Production screenplays assign each scene heading a unique number.  Once a
script is "locked" for production, scene numbers become immutable references
used across every department.  When new scenes are inserted between locked
numbers, they receive letter suffixes -- so-called *A-numbers* -- to
preserve the surrounding locked numbering (e.g. a scene between 5 and 6
becomes 5A, then 5B, and so on).  Deeper nesting is supported for inserts
between existing A-numbers (5A and 5B become 5AA, 5AB, ...).

This module provides pure-data utilities for managing the full lifecycle:
initial assignment, lock/unlock, A-number insertion, renumbering, and
display formatting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Iterator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fountain scene heading prefixes (case-insensitive).
# Matches the standard keywords and the forced-heading dot prefix.
_SCENE_HEADING_RE = re.compile(
    r"^(\.(?![.\s])|(?:INT|EXT|EST|INT\./EXT|INT/EXT|I/E)[\.\s])",
    re.IGNORECASE,
)

# Fountain inline scene-number markers: ``INT. OFFICE - DAY #5#``
_EXISTING_SCENE_NUMBER_RE = re.compile(r"\s*#([^#]+)#\s*$")

# Decompose a scene number string into its integer base and letter suffix.
_NUMBER_PARTS_RE = re.compile(r"^(\d+)([A-Z]*)$")

# ---------------------------------------------------------------------------
# SceneNumber dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SceneNumber:
    """A single scene's number and metadata.

    Attributes
    ----------
    number:
        Display string such as ``"5"`` or ``"5A"``.
    locked:
        ``True`` when this number has been locked for production and must
        not change during renumbering.
    line_index:
        Zero-based line index in the source script where the scene
        heading appears.
    """

    number: str
    locked: bool
    line_index: int


# ---------------------------------------------------------------------------
# Scene heading detection
# ---------------------------------------------------------------------------


def _is_scene_heading(line: str) -> bool:
    """Return ``True`` if *line* is a Fountain scene heading.

    Recognises the standard prefixes (INT., EXT., EST., INT./EXT., I/E.)
    and the forced-heading dot prefix (``.HEADING``), but not a line that
    starts with ``..`` (a Fountain ellipsis).
    """
    stripped = line.strip()
    if not stripped:
        return False
    return _SCENE_HEADING_RE.match(stripped) is not None


def _strip_scene_number_tag(heading: str) -> str:
    """Remove a trailing ``#NUMBER#`` tag from a heading, if present."""
    return _EXISTING_SCENE_NUMBER_RE.sub("", heading)


# ---------------------------------------------------------------------------
# Number parsing and arithmetic
# ---------------------------------------------------------------------------


def _parse_number(number: str) -> tuple[str, str]:
    """Split a scene number into *(integer_base, letter_suffix)*.

    Examples::

        "5"   -> ("5", "")
        "5A"  -> ("5", "A")
        "12BC" -> ("12", "BC")

    If the number does not match the expected pattern the whole string is
    returned as the base with an empty suffix.
    """
    m = _NUMBER_PARTS_RE.match(number)
    if m:
        return m.group(1), m.group(2)
    return number, ""


def _increment_suffix(suffix: str) -> str:
    """Increment a letter suffix in a base-26-like scheme.

    The progression mirrors spreadsheet column naming::

        ""   -> "A"
        "A"  -> "B"
        "Z"  -> "AA"
        "AA" -> "AB"
        "AZ" -> "BA"
        "ZZ" -> "AAA"
    """
    if not suffix:
        return "A"

    chars = list(suffix)
    carry = True
    for i in range(len(chars) - 1, -1, -1):
        if not carry:
            break
        if chars[i] == "Z":
            chars[i] = "A"
            # carry remains True
        else:
            chars[i] = chr(ord(chars[i]) + 1)
            carry = False

    if carry:
        chars.insert(0, "A")

    return "".join(chars)


def _scene_number_sort_key(number: str) -> tuple[int | float, ...]:
    """Return a tuple that sorts scene numbers in production order.

    Ordering example::

        1 < 1A < 1AA < 1AB < 1B < 2 < 2A < 3 ...

    This is essentially a pre-order traversal of a 26-ary tree rooted at
    each integer.  The tuple representation achieves this naturally with
    Python's built-in tuple comparison.
    """
    base_str, suffix = _parse_number(number)
    try:
        base_int: int | float = int(base_str)
    except ValueError:
        base_int = float("inf")

    if not suffix:
        return (base_int,)

    return (base_int,) + tuple(ord(ch) - ord("A") for ch in suffix)


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


def assign_scene_numbers(script: str) -> list[SceneNumber]:
    """Parse a Fountain script and assign sequential scene numbers.

    Each scene heading receives the next integer number starting from 1.
    All assigned numbers start unlocked.

    A scene heading is recognised when:
    * It starts with a standard prefix (INT., EXT., etc.) or a forced
      dot prefix, **and**
    * It is either the very first line or is preceded by a blank line
      (per the Fountain specification).

    If *script* is empty or contains no scene headings, an empty list is
    returned.
    """
    if not script:
        return []

    lines = script.split("\n")
    scenes: list[SceneNumber] = []
    counter = 1

    for i, line in enumerate(lines):
        if not _is_scene_heading(line):
            continue
        # Fountain spec: the heading must be the first line or preceded
        # by an empty line.
        if i > 0 and lines[i - 1].strip() != "":
            continue

        scenes.append(
            SceneNumber(number=str(counter), locked=False, line_index=i)
        )
        counter += 1

    return scenes


# ---------------------------------------------------------------------------
# Lock / unlock
# ---------------------------------------------------------------------------


def lock_scene(scenes: list[SceneNumber], index: int) -> list[SceneNumber]:
    """Return a copy of *scenes* with the scene at *index* locked.

    Out-of-range indices return an unchanged copy.
    """
    if not (0 <= index < len(scenes)):
        return list(scenes)
    result = list(scenes)
    result[index] = replace(result[index], locked=True)
    return result


def unlock_scene(scenes: list[SceneNumber], index: int) -> list[SceneNumber]:
    """Return a copy of *scenes* with the scene at *index* unlocked.

    Out-of-range indices return an unchanged copy.
    """
    if not (0 <= index < len(scenes)):
        return list(scenes)
    result = list(scenes)
    result[index] = replace(result[index], locked=False)
    return result


# ---------------------------------------------------------------------------
# Renumbering
# ---------------------------------------------------------------------------


def _generate_segment_numbers(
    prev_number: str | None,
    next_number: str | None,
    count: int,
) -> list[str]:
    """Generate *count* scene numbers that sort between two boundaries.

    *prev_number* is the number of the locked scene just before the
    segment (``None`` when the segment begins the list).  *next_number*
    is the locked scene just after (``None`` at the end).

    The strategy is to fill with plain integers first, then fall back to
    A-number suffixes when the integer range between boundaries is
    exhausted.
    """
    if count == 0:
        return []

    # -- determine the starting integer ------------------------------------

    if prev_number is None:
        start_int = 1
        prev_suffix = ""
    else:
        prev_base, prev_suffix = _parse_number(prev_number)
        try:
            start_int = int(prev_base) + 1
        except ValueError:
            start_int = 1

    # -- no upper bound: simple sequential integers ------------------------

    if next_number is None:
        return [str(start_int + i) for i in range(count)]

    # -- upper bound exists ------------------------------------------------

    next_base, _next_suffix = _parse_number(next_number)
    try:
        next_int = int(next_base)
    except ValueError:
        # Fallback: treat as unbounded
        return [str(start_int + i) for i in range(count)]

    available_ints = next_int - start_int  # integers strictly below next_int

    if count <= available_ints:
        # Plenty of room -- use plain integers.
        return [str(start_int + i) for i in range(count)]

    if available_ints > 0:
        # Use all available integers, then append A-numbers on the last
        # integer to accommodate the overflow.
        result = [str(start_int + i) for i in range(available_ints)]
        last_int = start_int + available_ints - 1
        suffix = ""
        for _ in range(count - available_ints):
            suffix = _increment_suffix(suffix)
            result.append(f"{last_int}{suffix}")
        return result

    # No integer slots available (e.g. between 5 and 6, or between 5A
    # and 6).  Use A-number suffixes on the previous scene's base.
    if prev_number is not None:
        p_base, p_suffix = _parse_number(prev_number)
        try:
            base_for_a = int(p_base)
        except ValueError:
            base_for_a = 0
    else:
        base_for_a = 0
        p_suffix = ""

    result: list[str] = []
    suffix = p_suffix
    for _ in range(count):
        suffix = _increment_suffix(suffix)
        result.append(f"{base_for_a}{suffix}")
    return result


def renumber_scenes(scenes: list[SceneNumber]) -> list[SceneNumber]:
    """Renumber all unlocked scenes, respecting locked numbers.

    Locked scenes keep their exact number.  Unlocked scenes receive new
    sequential numbers that fit between the surrounding locked
    boundaries, using A-number suffixes where the integer range is
    exhausted.

    When no scenes are locked the result is a clean 1..N sequence.

    Returns a new list; the input is not modified.
    """
    if not scenes:
        return []

    result = list(scenes)
    locked_indices = [i for i, s in enumerate(result) if s.locked]

    # -- fast path: nothing locked -----------------------------------------
    if not locked_indices:
        return [replace(s, number=str(i + 1)) for i, s in enumerate(result)]

    # -- fast path: everything locked --------------------------------------
    if len(locked_indices) == len(result):
        return list(result)

    # -- general case: process segments between locked boundaries ----------

    # Boundaries are the positions of locked scenes, bookended by virtual
    # sentinels at -1 (before the list) and len(result) (after the list).
    boundaries = [-1] + locked_indices + [len(result)]

    for seg_idx in range(len(boundaries) - 1):
        seg_start = boundaries[seg_idx] + 1
        seg_end = boundaries[seg_idx + 1]

        unlocked = [i for i in range(seg_start, seg_end) if not result[i].locked]
        if not unlocked:
            continue

        # Determine the locked neighbours for this segment.
        prev_number: str | None = None
        next_number: str | None = None

        if seg_idx > 0:
            prev_number = result[boundaries[seg_idx]].number
        if seg_idx < len(boundaries) - 2:
            next_number = result[boundaries[seg_idx + 1]].number

        numbers = _generate_segment_numbers(prev_number, next_number, len(unlocked))

        for list_idx, num in zip(unlocked, numbers):
            result[list_idx] = replace(result[list_idx], number=num)

    return result


# ---------------------------------------------------------------------------
# Insertion
# ---------------------------------------------------------------------------


def insert_scene_after(
    scenes: list[SceneNumber], after_index: int
) -> list[SceneNumber]:
    """Insert a new unlocked scene immediately after *after_index*.

    The new scene receives an A-number derived from the scene it follows:

    * After ``"5"`` (with ``"6"`` next): ``"5A"``
    * After ``"5A"`` (with ``"5B"`` next): ``"5AA"``
    * After ``"5B"`` (with ``"6"`` next): ``"5C"``

    If the natural candidate is already taken, the suffix is incremented
    until a free number is found.  If all siblings at the current depth
    are occupied, the algorithm descends one level (appends ``"A"``).

    The new scene's ``line_index`` is set to one past the predecessor's;
    the caller should update it to the actual script position.

    Returns a new list; the input is not modified.
    """
    if not scenes:
        return list(scenes)
    if not (0 <= after_index < len(scenes)):
        return list(scenes)

    prev = scenes[after_index]
    existing_numbers = {s.number for s in scenes}

    new_number = _generate_insert_number(prev.number, existing_numbers)

    new_scene = SceneNumber(
        number=new_number,
        locked=False,
        line_index=prev.line_index + 1,
    )

    result = list(scenes)
    result.insert(after_index + 1, new_scene)
    return result


def _generate_insert_number(prev_number: str, existing: set[str]) -> str:
    """Compute the A-number for a scene inserted after *prev_number*.

    Strategy:

    1. Try incrementing the suffix at the current level (``"5"`` -> ``"5A"``,
       ``"5A"`` -> ``"5B"``).
    2. If that candidate already exists, continue incrementing the suffix.
    3. If 26 siblings at the current level are exhausted, descend one level
       deeper by appending ``"A"`` to the previous suffix (``"5A"`` ->
       ``"5AA"``), then repeat.

    This guarantees a unique number can always be found.
    """
    base, suffix = _parse_number(prev_number)

    # -- try siblings at the current level ---------------------------------

    candidate_suffix = _increment_suffix(suffix)
    candidate = f"{base}{candidate_suffix}"
    if candidate not in existing:
        return candidate

    # Keep trying at the same level (e.g. 5B, 5C, ... 5Z).
    for _ in range(25):  # A..Z minus the one we already tried
        candidate_suffix = _increment_suffix(candidate_suffix)
        candidate = f"{base}{candidate_suffix}"
        if candidate not in existing:
            return candidate

    # -- descend one level deeper ------------------------------------------

    deeper_suffix = suffix + "A"
    candidate = f"{base}{deeper_suffix}"
    while candidate in existing:
        deeper_suffix = _increment_suffix(deeper_suffix)
        candidate = f"{base}{deeper_suffix}"

    return candidate


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_scene_heading(
    heading: str,
    number: SceneNumber,
    both_sides: bool = False,
) -> str:
    """Format a scene heading with scene number markers.

    Parameters
    ----------
    heading:
        The raw heading text (e.g. ``"INT. OFFICE - DAY"``).  Any
        existing ``#NUMBER#`` tags are stripped before formatting.
    number:
        The :class:`SceneNumber` to display.
    both_sides:
        If ``False`` (default), the number is placed on the right only,
        matching the Fountain ``#N#`` convention
        (``INT. OFFICE - DAY #5#``).
        If ``True``, the number appears on both sides -- the standard
        for production drafts
        (``#5# INT. OFFICE - DAY #5#``).

    Returns the formatted heading string.
    """
    clean = _strip_scene_number_tag(heading).strip()
    tag = f"#{number.number}#"

    if both_sides:
        return f"{tag} {clean} {tag}"
    return f"{clean} {tag}"
