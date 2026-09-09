"""WGA color revision tracking system.

The Writers Guild of America uses colored revision pages to track changes
during production.  Each draft beyond the original white pages advances
through a fixed sequence of colors.  This module provides data structures
and utilities for managing that sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import ClassVar

# ---------------------------------------------------------------------------
# Revision color sequence (WGA standard)
# ---------------------------------------------------------------------------

REVISION_COLORS: list[str] = [
    "White",
    "Blue",
    "Pink",
    "Yellow",
    "Green",
    "Goldenrod",
    "Buff",
    "Salmon",
    "Cherry",
    "Tan",
    "2nd Blue",
    "2nd Pink",
    "2nd Yellow",
    "2nd Green",
    "2nd Goldenrod",
    "2nd Buff",
    "2nd Salmon",
    "2nd Cherry",
    "2nd Tan",
]

# ---------------------------------------------------------------------------
# Display hex colors for each revision color
# ---------------------------------------------------------------------------

_COLOR_HEX_MAP: dict[str, str] = {
    "White": "#FFFFFF",
    "Blue": "#B0C4DE",
    "Pink": "#FFB6C1",
    "Yellow": "#FFFACD",
    "Green": "#90EE90",
    "Goldenrod": "#DAA520",
    "Buff": "#F0DC82",
    "Salmon": "#FA8072",
    "Cherry": "#DE3163",
    "Tan": "#D2B48C",
    "2nd Blue": "#B0C4DE",
    "2nd Pink": "#FFB6C1",
    "2nd Yellow": "#FFFACD",
    "2nd Green": "#90EE90",
    "2nd Goldenrod": "#DAA520",
    "2nd Buff": "#F0DC82",
    "2nd Salmon": "#FA8072",
    "2nd Cherry": "#DE3163",
    "2nd Tan": "#D2B48C",
}


def get_revision_color_hex(color_name: str) -> str:
    """Return a display hex color for a revision color name.

    Falls back to white (``#FFFFFF``) for unrecognised names.
    """
    return _COLOR_HEX_MAP.get(color_name, "#FFFFFF")


# ---------------------------------------------------------------------------
# Revision dataclass
# ---------------------------------------------------------------------------


@dataclass
class Revision:
    """A single revision entry."""

    color: str
    date: str  # ISO-8601 date string  (YYYY-MM-DD)
    pages_changed: list[int] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Revision:
        return cls(
            color=data["color"],
            date=data["date"],
            pages_changed=list(data.get("pages_changed", [])),
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Revision tracker
# ---------------------------------------------------------------------------


class RevisionTracker:
    """Manage the ordered sequence of screenplay revision drafts."""

    def __init__(self) -> None:
        """Start tracking at *White* (the original draft)."""
        today = date.today().isoformat()
        self._revisions: list[Revision] = [
            Revision(color="White", date=today, pages_changed=[], notes="Original draft")
        ]

    # -- queries -------------------------------------------------------------

    def current_revision(self) -> Revision:
        """Return the most recent (current) revision."""
        return self._revisions[-1]

    def get_revision_history(self) -> list[Revision]:
        """Return all revisions in chronological order."""
        return list(self._revisions)

    def get_page_color(self, page: int) -> str:
        """Determine the color a given page should be printed on.

        Walks the revision history in reverse; the most recent revision
        that changed *page* determines its color.  Pages that have never
        been revised are ``White``.
        """
        for rev in reversed(self._revisions):
            if page in rev.pages_changed:
                return rev.color
        return "White"

    def get_revision_header(self) -> str:
        """Format a revision header suitable for the title page.

        Example: ``BLUE REVISION - Sept. 9, 2026``
        """
        rev = self.current_revision()
        try:
            d = date.fromisoformat(rev.date)
            month_abbr = d.strftime("%b.")
            day = d.day
            year = d.year
            formatted_date = f"{month_abbr} {day}, {year}"
        except (ValueError, TypeError):
            formatted_date = rev.date

        return f"{rev.color.upper()} REVISION - {formatted_date}"

    # -- mutations -----------------------------------------------------------

    def add_revision(
        self, pages_changed: list[int], notes: str = ""
    ) -> Revision:
        """Advance to the next color and record changed pages.

        Raises ``IndexError`` if the color sequence is exhausted.
        """
        current_idx = _color_index(self.current_revision().color)
        next_idx = current_idx + 1
        if next_idx >= len(REVISION_COLORS):
            raise IndexError(
                "Revision color sequence exhausted; no more colors available."
            )
        today = date.today().isoformat()
        rev = Revision(
            color=REVISION_COLORS[next_idx],
            date=today,
            pages_changed=list(pages_changed),
            notes=notes,
        )
        self._revisions.append(rev)
        return rev

    def reset(self) -> None:
        """Reset the tracker back to the original White draft."""
        today = date.today().isoformat()
        self._revisions = [
            Revision(color="White", date=today, pages_changed=[], notes="Original draft")
        ]

    # -- serialisation -------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the tracker state to a plain dict."""
        return {
            "revisions": [r.to_dict() for r in self._revisions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> RevisionTracker:
        """Deserialize a tracker from a dict produced by :meth:`to_dict`."""
        tracker = cls.__new__(cls)
        tracker._revisions = [
            Revision.from_dict(rd) for rd in data.get("revisions", [])
        ]
        if not tracker._revisions:
            tracker.__init__()  # type: ignore[misc]
        return tracker


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def format_revision_mark(line: str, revision_color: str) -> str:
    """Return *line* with a revision asterisk (*) appended at the right margin.

    The asterisk is the industry-standard mark indicating a line was changed
    in the named revision.  The mark is right-aligned at column 60 by padding
    the line with spaces.
    """
    # Strip any existing trailing asterisk / whitespace
    clean = line.rstrip()
    if not clean:
        return clean
    # Pad to column 60 then append the asterisk
    padded = clean.ljust(60)
    return f"{padded}*"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _color_index(color: str) -> int:
    """Return the index of *color* in the revision sequence.

    Raises ``ValueError`` for unknown colors.
    """
    try:
        return REVISION_COLORS.index(color)
    except ValueError:
        raise ValueError(f"Unknown revision color: {color!r}") from None
