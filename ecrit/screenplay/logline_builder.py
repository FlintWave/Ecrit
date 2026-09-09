"""Madlibs-style logline builder with multiple template shapes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class LoglineTemplate:
    """A fill-in-the-blanks logline template."""

    name: str
    pattern: str  # String with {field_name} placeholders
    fields: list[str] = field(default_factory=list)
    example: str = ""

    def __post_init__(self):
        if not self.fields:
            self.fields = _extract_fields(self.pattern)


def _extract_fields(pattern: str) -> list[str]:
    """Extract {field_name} placeholders from a pattern string, in order."""
    seen: set[str] = set()
    result: list[str] = []
    for match in re.finditer(r"\{(\w+)\}", pattern):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

LOGLINE_TEMPLATES: dict[str, LoglineTemplate] = {
    "classic": LoglineTemplate(
        name="Classic",
        pattern="When {inciting_incident}, a {protagonist} must {objective} before {stakes}.",
        example=(
            "When a great white shark begins terrorizing a small beach town, "
            "a hydrophobic police chief must hunt down the beast before "
            "the summer tourist season is destroyed."
        ),
    ),
    "with_antagonist": LoglineTemplate(
        name="With Antagonist",
        pattern=(
            "A {protagonist} must {objective} when {inciting_incident}, "
            "but {antagonist} stands in the way."
        ),
        example=(
            "A down-on-his-luck boxer must fight for the heavyweight title "
            "when he gets a once-in-a-lifetime shot, but the reigning "
            "champion stands in the way."
        ),
    ),
    "ironic": LoglineTemplate(
        name="Ironic",
        pattern=(
            "{protagonist}, who {ironic_trait}, must {objective} "
            "when {inciting_incident}."
        ),
        example=(
            "A germophobic health inspector, who has never eaten "
            "at a restaurant, must go undercover as a food critic "
            "when a chain of mysterious poisonings hits the city."
        ),
    ),
    "high_concept": LoglineTemplate(
        name="High Concept",
        pattern=(
            "What if {high_concept}? A {protagonist} discovers "
            "{discovery} and must {objective}."
        ),
        example=(
            "What if you could erase someone from your memory? "
            "A heartbroken introvert discovers his ex-girlfriend "
            "has already done it and must race through his own "
            "vanishing memories to hold on to her."
        ),
    ),
    "character_driven": LoglineTemplate(
        name="Character-Driven",
        pattern=(
            "After {inciting_incident}, {protagonist} — a {description} "
            "struggling with {flaw} — must {objective} or face {consequences}."
        ),
        example=(
            "After his wife's sudden death, Tom — a once-celebrated "
            "pianist struggling with stage fright — must perform one "
            "last concert or face losing the family home."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_logline_templates() -> list[tuple[str, str]]:
    """Return a list of (key, human-readable name) pairs for all templates."""
    return [(key, tmpl.name) for key, tmpl in LOGLINE_TEMPLATES.items()]


def get_logline_fields(template_key: str) -> list[str]:
    """Return the ordered list of field names required by *template_key*.

    Raises ``KeyError`` if the template key is not found.
    """
    return list(LOGLINE_TEMPLATES[template_key].fields)


def build_logline(template_key: str, values: dict[str, str]) -> str:
    """Fill in the template identified by *template_key* with *values*.

    Every placeholder field must have a corresponding entry in *values*;
    extra keys are silently ignored.

    Raises ``KeyError`` if the template key is not found or a required
    field is missing from *values*.
    """
    tmpl = LOGLINE_TEMPLATES[template_key]
    missing = [f for f in tmpl.fields if f not in values]
    if missing:
        raise KeyError(f"Missing fields for template '{template_key}': {missing}")
    return tmpl.pattern.format(**{f: values[f] for f in tmpl.fields})


def validate_logline(logline: str) -> dict:
    """Return basic quality metrics for a finished logline string.

    Returns a dict with:
        word_count (int): number of words
        length (str): "short", "good", or "long"
    """
    words = logline.split()
    word_count = len(words)

    if word_count < 15:
        length = "short"
    elif word_count > 50:
        length = "long"
    else:
        length = "good"

    return {
        "word_count": word_count,
        "length": length,
    }
