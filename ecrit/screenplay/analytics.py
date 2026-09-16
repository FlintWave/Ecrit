"""Screenplay analytics — computes detailed statistics for visualization."""

from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass

_LINES_PER_PAGE = 55

_SCENE_HEADING_RE = re.compile(
    r"^(\.(?=\S)|(?:INT|EXT|EST|INT\./EXT|INT/EXT|I/E)[\.\s])",
    re.IGNORECASE,
)

_CHARACTER_CUE_RE = re.compile(
    r"^@?([A-Z][A-Z0-9 .\-']+?)(?:\s*\(.*\))?$"
)

_TIME_OF_DAY_TOKENS = [
    "MOMENTS LATER", "CONTINUOUS", "LATER",
    "DAWN", "DUSK", "DAY", "NIGHT",
    "MORNING", "AFTERNOON", "EVENING", "SUNSET", "SUNRISE",
]


@dataclass
class CharacterStats:
    name: str
    line_count: int
    word_count: int
    scene_count: int
    percentage: float
    avg_speech_length: float
    first_appearance: int
    last_appearance: int


@dataclass
class SceneStats:
    index: int
    heading: str
    line_count: int
    word_count: int
    character_count: int
    dialogue_percentage: float
    page_number: float
    int_ext: str
    time_of_day: str
    characters: list[str]


@dataclass
class PacingPoint:
    scene_index: int
    dialogue_density: float
    action_density: float
    scene_length: int
    tension_estimate: str


def _parse_scene_heading(heading: str) -> dict[str, str]:
    raw = heading.strip()
    if raw.startswith(".") and not raw.startswith(".."):
        raw = raw[1:].strip()

    int_ext = ""
    location = raw
    time_of_day = ""

    ie_match = re.match(
        r"^(INT\./EXT|INT/EXT|I/E|INT|EXT|EST)[.\s]+(.*)$",
        raw,
        re.IGNORECASE,
    )
    if ie_match:
        int_ext = ie_match.group(1).upper().replace(" ", "")
        if int_ext in ("INT./EXT", "INT/EXT", "I/E"):
            int_ext = "INT/EXT"
        location = ie_match.group(2).strip()

    if " - " in location:
        parts = location.rsplit(" - ", 1)
        candidate = parts[1].strip().upper()
        for token in _TIME_OF_DAY_TOKENS:
            if candidate == token or candidate.startswith(token):
                time_of_day = candidate
                location = parts[0].strip()
                break
        if not time_of_day and len(candidate.split()) <= 3:
            time_of_day = candidate
            location = parts[0].strip()

    return {"int_ext": int_ext, "location": location, "time_of_day": time_of_day}


def _is_scene_heading(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped and _SCENE_HEADING_RE.match(stripped))


def _is_transition(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(">"):
        return True
    return stripped.isupper() and stripped.endswith("TO:")


class ScriptAnalytics:

    def analyze(self, content: str) -> dict:
        lines = content.split("\n")
        scenes = self._find_scenes(lines)

        char_data: dict[str, dict] = {}
        scene_stats_list: list[SceneStats] = []
        pacing_list: list[PacingPoint] = []
        total_dialogue_words = 0
        total_action_words = 0
        total_line_index = 0

        for scene_idx, scene in enumerate(scenes):
            start, end, heading = scene["start"], scene["end"], scene["heading"]
            parsed = _parse_scene_heading(heading)
            scene_lines = lines[start:end]
            scene_line_count = end - start

            dialogue_words = 0
            action_words = 0
            scene_characters: list[str] = []
            seen_chars: set[str] = set()
            in_dialogue = False
            current_char: str | None = None
            exclamation_count = 0

            for i in range(start + 1, end):
                line = lines[i]
                stripped = line.strip()

                if not stripped:
                    in_dialogue = False
                    current_char = None
                    continue

                if _is_scene_heading(stripped):
                    continue

                if _is_transition(stripped):
                    in_dialogue = False
                    current_char = None
                    continue

                prev_blank = i == start + 1 or lines[i - 1].strip() == ""
                is_char_cue = False
                char_name: str | None = None

                if prev_blank:
                    if stripped.startswith("@"):
                        char_name = re.sub(r"\s*\(.*\)$", "", stripped[1:]).strip().upper()
                        is_char_cue = bool(char_name)
                    else:
                        m = _CHARACTER_CUE_RE.match(stripped)
                        if m:
                            char_name = m.group(1).strip().upper()
                            is_char_cue = True

                if is_char_cue and char_name:
                    current_char = char_name
                    in_dialogue = True
                    if char_name not in seen_chars:
                        seen_chars.add(char_name)
                        scene_characters.append(char_name)
                    if char_name not in char_data:
                        char_data[char_name] = {
                            "line_count": 0,
                            "word_count": 0,
                            "scenes": set(),
                            "first_appearance": scene_idx,
                            "last_appearance": scene_idx,
                            "dialogue_blocks": 0,
                        }
                    char_data[char_name]["scenes"].add(scene_idx)
                    char_data[char_name]["last_appearance"] = scene_idx
                    char_data[char_name]["dialogue_blocks"] += 1
                    continue

                if in_dialogue and stripped.startswith("("):
                    continue

                if in_dialogue and current_char:
                    wc = len(stripped.split())
                    dialogue_words += wc
                    char_data[current_char]["line_count"] += 1
                    char_data[current_char]["word_count"] += wc
                    exclamation_count += stripped.count("!")
                else:
                    wc = len(stripped.split())
                    action_words += wc
                    exclamation_count += stripped.count("!")

            scene_word_count = dialogue_words + action_words
            total_dialogue_words += dialogue_words
            total_action_words += action_words

            dial_pct = 0.0
            if scene_word_count > 0:
                dial_pct = round(dialogue_words / scene_word_count * 100, 1)

            page_num = round(total_line_index / _LINES_PER_PAGE + 1, 2)
            total_line_index += scene_line_count

            scene_stats_list.append(SceneStats(
                index=scene_idx,
                heading=heading,
                line_count=scene_line_count,
                word_count=scene_word_count,
                character_count=len(scene_characters),
                dialogue_percentage=dial_pct,
                page_number=page_num,
                int_ext=parsed["int_ext"],
                time_of_day=parsed["time_of_day"],
                characters=scene_characters,
            ))

            dial_density = 0.0
            act_density = 0.0
            if scene_word_count > 0:
                dial_density = round(dialogue_words / scene_word_count, 3)
                act_density = round(action_words / scene_word_count, 3)

            tension = "low"
            if scene_word_count < 80 and exclamation_count >= 2:
                tension = "high"
            elif scene_word_count < 150 and exclamation_count >= 1:
                tension = "medium"
            elif exclamation_count >= 3:
                tension = "medium"

            pacing_list.append(PacingPoint(
                scene_index=scene_idx,
                dialogue_density=dial_density,
                action_density=act_density,
                scene_length=scene_word_count,
                tension_estimate=tension,
            ))

        total_words = total_dialogue_words + total_action_words
        character_stats = self._build_character_stats(char_data, total_dialogue_words)
        dialogue_balance = {
            cs.name: cs.percentage for cs in character_stats
        }

        scene_word_counts = [s.word_count for s in scene_stats_list]
        scene_length_dist = self._compute_distribution(scene_word_counts)

        int_ext_ratio: dict[str, int] = {"INT": 0, "EXT": 0, "INT/EXT": 0}
        time_of_day_counts: dict[str, int] = {}
        for s in scene_stats_list:
            if s.int_ext in int_ext_ratio:
                int_ext_ratio[s.int_ext] += 1
            tod = s.time_of_day.upper() if s.time_of_day else "UNKNOWN"
            time_of_day_counts[tod] = time_of_day_counts.get(tod, 0) + 1

        total_pages = round(len(lines) / _LINES_PER_PAGE, 2)
        act_structure = self._estimate_act_structure(scene_stats_list, total_pages)

        total_characters = len(char_data)
        total_scenes = len(scene_stats_list)
        avg_scene_length = round(total_words / total_scenes, 1) if total_scenes else 0.0
        dial_action_ratio = (
            round(total_dialogue_words / total_action_words, 2)
            if total_action_words > 0 else 0.0
        )

        summary = {
            "total_pages": total_pages,
            "total_scenes": total_scenes,
            "total_characters": total_characters,
            "total_words": total_words,
            "dialogue_action_ratio": dial_action_ratio,
            "avg_scene_length": avg_scene_length,
            "estimated_runtime_minutes": round(total_pages, 0),
        }

        return {
            "character_stats": [asdict(cs) for cs in character_stats],
            "scene_stats": [asdict(ss) for ss in scene_stats_list],
            "pacing": [asdict(pp) for pp in pacing_list],
            "dialogue_balance": dialogue_balance,
            "scene_length_distribution": scene_length_dist,
            "int_ext_ratio": int_ext_ratio,
            "time_of_day": time_of_day_counts,
            "act_structure": act_structure,
            "summary": summary,
        }

    def _find_scenes(self, lines: list[str]) -> list[dict]:
        scenes: list[dict] = []
        for i, line in enumerate(lines):
            if _is_scene_heading(line):
                scenes.append({
                    "heading": line.strip(),
                    "start": i,
                    "end": len(lines),
                })
        for idx in range(len(scenes) - 1):
            scenes[idx]["end"] = scenes[idx + 1]["start"]
        return scenes

    def _build_character_stats(
        self, char_data: dict[str, dict], total_dialogue_words: int
    ) -> list[CharacterStats]:
        result: list[CharacterStats] = []
        for name, data in char_data.items():
            pct = 0.0
            if total_dialogue_words > 0:
                pct = round(data["word_count"] / total_dialogue_words * 100, 1)
            avg_len = 0.0
            if data["dialogue_blocks"] > 0:
                avg_len = round(data["word_count"] / data["dialogue_blocks"], 1)
            result.append(CharacterStats(
                name=name,
                line_count=data["line_count"],
                word_count=data["word_count"],
                scene_count=len(data["scenes"]),
                percentage=pct,
                avg_speech_length=avg_len,
                first_appearance=data["first_appearance"],
                last_appearance=data["last_appearance"],
            ))
        result.sort(key=lambda c: c.line_count, reverse=True)
        return result

    def _compute_distribution(self, values: list[int]) -> dict:
        if not values:
            return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0, "std_dev": 0.0}
        mn = min(values)
        mx = max(values)
        avg = round(statistics.mean(values), 2)
        med = round(statistics.median(values), 2)
        sd = round(statistics.stdev(values), 2) if len(values) >= 2 else 0.0
        return {"min": mn, "max": mx, "mean": avg, "median": med, "std_dev": sd}

    def _estimate_act_structure(
        self, scenes: list[SceneStats], total_pages: float
    ) -> list[dict]:
        if not scenes:
            return []

        act1_end = total_pages * 0.25
        act2_end = total_pages * 0.75

        acts: list[dict] = [
            {"act": 1, "scene_count": 0, "page_range": [1.0, round(act1_end, 2)]},
            {"act": 2, "scene_count": 0, "page_range": [round(act1_end, 2), round(act2_end, 2)]},
            {"act": 3, "scene_count": 0, "page_range": [round(act2_end, 2), round(total_pages, 2)]},
        ]

        for s in scenes:
            if s.page_number <= act1_end:
                acts[0]["scene_count"] += 1
            elif s.page_number <= act2_end:
                acts[1]["scene_count"] += 1
            else:
                acts[2]["scene_count"] += 1

        return acts
