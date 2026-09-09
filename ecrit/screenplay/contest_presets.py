"""Screenplay competition formatting presets."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContestPreset:
    """Formatting requirements for a specific screenplay contest."""

    name: str
    organization: str
    formats_accepted: list[str] = field(default_factory=list)
    page_range: tuple[int | None, int | None] = (None, None)
    paper: str = "USLetter"  # "USLetter" or "A4"
    font_size: int = 12
    scene_numbers: bool = False
    title_page_required: bool = True
    notes: str = ""
    url: str = ""


# ---------------------------------------------------------------------------
# Built-in presets
# ---------------------------------------------------------------------------

CONTEST_PRESETS: dict[str, ContestPreset] = {
    "nicholl": ContestPreset(
        name="Nicholl Fellowship",
        organization="Academy of Motion Picture Arts and Sciences",
        formats_accepted=["Feature"],
        page_range=(70, 160),
        paper="USLetter",
        font_size=12,
        scene_numbers=False,
        title_page_required=True,
        notes=(
            "No scene numbers on first submission. "
            "No WGA registration number on the title page."
        ),
        url="https://www.oscars.org/nicholl",
    ),
    "bbc_writersroom": ContestPreset(
        name="BBC Writersroom",
        organization="BBC",
        formats_accepted=["Feature", "TV Pilot", "TV Spec"],
        page_range=(90, 120),
        paper="A4",
        font_size=12,
        scene_numbers=False,  # optional
        title_page_required=True,
        notes=(
            "Page range is for feature-length scripts; TV scripts follow "
            "per-slot lengths. Scene numbers are optional. Use UK date format "
            "(DD/MM/YYYY) on the title page."
        ),
        url="https://www.bbc.co.uk/writersroom",
    ),
    "austin": ContestPreset(
        name="Austin Film Festival",
        organization="Austin Film Festival",
        formats_accepted=["Feature"],
        page_range=(70, 130),
        paper="USLetter",
        font_size=12,
        scene_numbers=False,
        title_page_required=True,
        notes="Standard Fountain format accepted. 12pt Courier Prime recommended.",
        url="https://www.austinfilmfestival.com",
    ),
    "page_international": ContestPreset(
        name="PAGE International Screenwriting Awards",
        organization="PAGE International",
        formats_accepted=["Feature"],
        page_range=(70, 120),
        paper="USLetter",
        font_size=12,
        scene_numbers=False,
        title_page_required=True,
        notes=(
            "No bold or italic formatting in scene headings. "
            "12pt Courier required."
        ),
        url="https://pageawards.com",
    ),
    "bluecat": ContestPreset(
        name="BlueCat Screenplay Competition",
        organization="BlueCat",
        formats_accepted=["Feature"],
        page_range=(70, 130),  # recommended, not enforced
        paper="USLetter",
        font_size=12,
        scene_numbers=False,
        title_page_required=True,
        notes=(
            "No strict page limit, but 70-130 pages is the recommended range. "
            "Standard screenplay format."
        ),
        url="https://www.bluecatscreenplay.com",
    ),
    "sundance_lab": ContestPreset(
        name="Sundance Screenwriters Lab",
        organization="Sundance Institute",
        formats_accepted=["Feature"],
        page_range=(70, 130),
        paper="USLetter",
        font_size=12,
        scene_numbers=False,
        title_page_required=True,
        notes="A synopsis must be included with the submission.",
        url="https://www.sundance.org",
    ),
    "big_break": ContestPreset(
        name="Final Draft Big Break",
        organization="Final Draft",
        formats_accepted=["Feature"],
        page_range=(80, 130),
        paper="USLetter",
        font_size=12,
        scene_numbers=False,
        title_page_required=True,
        notes="Standard screenplay format. Final Draft (.fdx) format accepted.",
        url="https://www.finaldraft.com/big-break",
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_CHARS_PER_PAGE = 3500  # rough estimate for standard screenplay formatting


def list_presets() -> list[tuple[str, str]]:
    """Return a list of (key, human-readable name) pairs for all presets."""
    return [(key, preset.name) for key, preset in CONTEST_PRESETS.items()]


def get_preset(key: str) -> ContestPreset | None:
    """Return the preset for *key*, or ``None`` if not found."""
    return CONTEST_PRESETS.get(key)


def validate_against_preset(script: str, preset_key: str) -> list[str]:
    """Validate *script* text against the contest preset identified by *preset_key*.

    Returns a list of human-readable warning strings. An empty list means
    no issues were detected.  The checks are intentionally conservative:
    page count is estimated from character count using a rough
    characters-per-page heuristic.

    Raises ``KeyError`` if *preset_key* is not a known preset.
    """
    preset = CONTEST_PRESETS.get(preset_key)
    if preset is None:
        raise KeyError(f"Unknown preset: {preset_key!r}")

    warnings: list[str] = []

    # Estimate page count from character length.
    char_count = len(script)
    estimated_pages = max(1, round(char_count / _CHARS_PER_PAGE))

    min_pages, max_pages = preset.page_range
    if min_pages is not None and estimated_pages < min_pages:
        warnings.append(
            f"Script is approximately {estimated_pages} pages, "
            f"which is below the {min_pages}-page minimum for {preset.name}."
        )
    if max_pages is not None and estimated_pages > max_pages:
        warnings.append(
            f"Script is approximately {estimated_pages} pages, "
            f"which exceeds the {max_pages}-page maximum for {preset.name}."
        )

    # Check for scene numbers when the preset says none.
    if not preset.scene_numbers:
        # A simple heuristic: lines starting with "INT." or "EXT." that end
        # with a number (possibly preceded by whitespace) likely have scene numbers.
        import re

        scene_heading_pattern = re.compile(
            r"^\s*(INT\.|EXT\.|INT\./EXT\.|I/E\.)\s+.+\s+#?\d+\s*$",
            re.MULTILINE | re.IGNORECASE,
        )
        if scene_heading_pattern.search(script):
            warnings.append(
                f"{preset.name} does not accept scene numbers in the submission."
            )

    # Check for title page marker (Fountain-style).
    has_title_page = script.lstrip().startswith("Title:")
    if preset.title_page_required and not has_title_page:
        warnings.append(
            f"{preset.name} requires a title page. "
            "No Fountain-style title page detected."
        )

    return warnings
