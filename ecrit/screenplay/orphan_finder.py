"""Orphan/widow finder — identifies lines that could be tightened to save pages."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class OrphanIssue:
    line_number: int
    issue_type: str
    text: str
    suggestion: str
    severity: str
    words_over: int = 0


_SCENE_HEADING_PREFIXES = ("INT.", "EXT.", "INT./EXT.", "I/E.")
_ELEMENT_TYPES = ("scene_heading", "character", "dialogue", "parenthetical", "action")


def _is_scene_heading(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith(".") and len(stripped) > 1 and stripped[1] != ".":
        return stripped[1:].strip().isupper()
    upper = stripped.upper()
    return any(upper.startswith(p) for p in _SCENE_HEADING_PREFIXES)


def _is_character_cue(line: str) -> bool:
    stripped = line.strip()
    if not stripped or not stripped.isupper():
        return False
    if _is_scene_heading(stripped):
        return False
    # Must contain at least one letter
    return bool(re.search(r"[A-Z]", stripped))


def _is_parenthetical(line: str) -> bool:
    return line.strip().startswith("(")


def _classify_line(line: str, prev_type: str | None) -> str:
    stripped = line.strip()
    if not stripped:
        return "blank"
    if _is_scene_heading(stripped):
        return "scene_heading"
    if _is_parenthetical(stripped):
        return "parenthetical"
    if _is_character_cue(stripped):
        return "character"
    if prev_type in ("character", "parenthetical", "dialogue"):
        return "dialogue"
    return "action"


@dataclass
class _Block:
    block_type: str
    lines: list[str] = field(default_factory=list)
    start_line: int = 0


def _parse_blocks(content: str) -> list[_Block]:
    raw_lines = content.split("\n")
    blocks: list[_Block] = []
    current: _Block | None = None
    prev_type: str | None = None

    for i, line in enumerate(raw_lines):
        line_type = _classify_line(line, prev_type)

        if line_type == "blank":
            if current is not None:
                blocks.append(current)
                current = None
            prev_type = None
            continue

        if current is None or line_type != current.block_type:
            if current is not None:
                blocks.append(current)
            current = _Block(block_type=line_type, start_line=i + 1)

        current.lines.append(line)
        prev_type = line_type

    if current is not None:
        blocks.append(current)

    return blocks


def _estimated_page(line_number: int, lines_per_page: int) -> int:
    return (line_number - 1) // lines_per_page + 1


def _line_wraps(text: str, chars_per_line: int) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, -(-len(stripped) // chars_per_line))


class OrphanFinder:
    CHARS_PER_LINE = 61
    LINES_PER_PAGE = 55

    def analyze(self, content: str) -> list[OrphanIssue]:
        blocks = _parse_blocks(content)
        issues: list[OrphanIssue] = []

        issues.extend(self._find_widows(blocks))
        issues.extend(self._find_orphans(blocks, content))
        issues.extend(self._find_long_dialogue(blocks))
        issues.extend(self._find_overlong_action_lines(blocks))
        issues.extend(self._find_splittable_action(blocks))

        issues.sort(key=lambda x: x.line_number)
        return issues

    def _find_widows(self, blocks: list[_Block]) -> list[OrphanIssue]:
        issues: list[OrphanIssue] = []
        scenes: list[list[_Block]] = []
        current_scene: list[_Block] = []

        for block in blocks:
            if block.block_type == "scene_heading":
                if current_scene:
                    scenes.append(current_scene)
                current_scene = [block]
            else:
                current_scene.append(block)
        if current_scene:
            scenes.append(current_scene)

        for scene in scenes:
            if len(scene) < 2:
                continue
            last_block = scene[-1]
            if last_block.block_type not in ("action", "dialogue"):
                continue
            if len(last_block.lines) != 1:
                continue

            text = last_block.lines[0].strip()
            word_count = len(text.split())
            if word_count <= 3:
                continue

            # The scene has other content that could absorb this line
            prev_blocks = [b for b in scene[1:] if b.block_type in ("action", "dialogue")]
            if len(prev_blocks) < 2:
                continue

            issues.append(OrphanIssue(
                line_number=last_block.start_line,
                issue_type="widow",
                text=text,
                suggestion=(
                    f"This scene ends with a single-line paragraph. "
                    f"Trimming 1-3 words from earlier lines could fold this in."
                ),
                severity="high",
                words_over=min(3, word_count),
            ))

        return issues

    def _find_orphans(self, blocks: list[_Block], content: str) -> list[OrphanIssue]:
        issues: list[OrphanIssue] = []
        running_lines = 0
        raw_lines = content.split("\n")

        for block in blocks:
            wrapped_count = 0
            for line in block.lines:
                wrapped_count += _line_wraps(line, self.CHARS_PER_LINE)

            block_start_page = _estimated_page(running_lines + 1, self.LINES_PER_PAGE)
            block_end_page = _estimated_page(running_lines + wrapped_count, self.LINES_PER_PAGE)

            if block_end_page > block_start_page and wrapped_count > 1:
                # First line lands at page bottom, rest on next page
                lines_into_page = (running_lines) % self.LINES_PER_PAGE
                lines_left_on_page = self.LINES_PER_PAGE - lines_into_page

                if lines_left_on_page == 1:
                    text = block.lines[0].strip()
                    issues.append(OrphanIssue(
                        line_number=block.start_line,
                        issue_type="orphan",
                        text=text,
                        suggestion=(
                            f"First line of this {block.block_type} block sits alone at the "
                            f"bottom of page {block_start_page}. Trimming earlier content "
                            f"could push it to the next page."
                        ),
                        severity="high",
                        words_over=0,
                    ))

            running_lines += wrapped_count
            # blank line between blocks
            running_lines += 1

        return issues

    def _find_long_dialogue(self, blocks: list[_Block]) -> list[OrphanIssue]:
        issues: list[OrphanIssue] = []

        for block in blocks:
            if block.block_type != "dialogue":
                continue

            total_wrapped = sum(
                _line_wraps(line, self.CHARS_PER_LINE) for line in block.lines
            )
            if total_wrapped > 6:
                text = block.lines[0].strip()
                issues.append(OrphanIssue(
                    line_number=block.start_line,
                    issue_type="long_dialogue",
                    text=text[:80] + ("..." if len(text) > 80 else ""),
                    suggestion="Consider breaking this dialogue into shorter exchanges.",
                    severity="medium",
                    words_over=0,
                ))

        return issues

    def _find_overlong_action_lines(self, blocks: list[_Block]) -> list[OrphanIssue]:
        issues: list[OrphanIssue] = []

        for block in blocks:
            if block.block_type != "action":
                continue

            for i, line in enumerate(block.lines):
                stripped = line.strip()
                length = len(stripped)
                if length <= self.CHARS_PER_LINE:
                    continue

                overflow = length - self.CHARS_PER_LINE
                # Only flag if overflow is small — easy to trim
                if overflow > 15:
                    continue

                overflow_text = stripped[self.CHARS_PER_LINE:]
                words_in_overflow = len(overflow_text.split())
                if words_in_overflow > 3:
                    continue

                issues.append(OrphanIssue(
                    line_number=block.start_line + i,
                    issue_type="near_full_page",
                    text=stripped[:80] + ("..." if len(stripped) > 80 else ""),
                    suggestion=(
                        f"This line wraps by only {words_in_overflow} word(s). "
                        f"Cutting {words_in_overflow} word(s) saves a line of space."
                    ),
                    severity="medium",
                    words_over=words_in_overflow,
                ))

        return issues

    def _find_splittable_action(self, blocks: list[_Block]) -> list[OrphanIssue]:
        issues: list[OrphanIssue] = []

        for block in blocks:
            if block.block_type != "action":
                continue

            total_wrapped = sum(
                _line_wraps(line, self.CHARS_PER_LINE) for line in block.lines
            )
            if total_wrapped > 4:
                text = block.lines[0].strip()
                issues.append(OrphanIssue(
                    line_number=block.start_line,
                    issue_type="splittable_action",
                    text=text[:80] + ("..." if len(text) > 80 else ""),
                    suggestion="Consider splitting this action block for readability.",
                    severity="low",
                    words_over=0,
                ))

        return issues


def get_summary(issues: list[OrphanIssue]) -> dict:
    by_severity: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for issue in issues:
        by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1

    high_count = by_severity["high"]
    medium_count = by_severity["medium"]
    # rough heuristic: each high-severity fix can save ~0.5 page,
    # medium ~0.25, low issues are readability-only
    potential_saved = high_count * 0.5 + medium_count * 0.25

    return {
        "total_issues": len(issues),
        "potential_pages_saved": round(potential_saved, 1),
        "by_severity": by_severity,
    }
