"""Tests for comic book Fountain extensions — parser, dialects, stats, and exports."""

import json
import pytest

import ecrit_core


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_comic(text: str) -> dict:
    return json.loads(ecrit_core.parse_fountain(text, "fountain+comic-dc"))

def parse_standard(text: str) -> dict:
    return json.loads(ecrit_core.parse_fountain(text))

def stats_comic(text: str) -> dict:
    return json.loads(ecrit_core.get_script_stats(text, "fountain+comic-dc"))

def elements_of_type(doc: dict, etype: str) -> list[dict]:
    return [e for e in doc["elements"] if e["type"] == etype]


# ---------------------------------------------------------------------------
# Comic element parsing
# ---------------------------------------------------------------------------

class TestPageHeader:
    def test_section_page_header(self):
        doc = parse_comic("# PAGE ONE\n")
        pages = elements_of_type(doc, "PageHeader")
        assert len(pages) == 1
        assert pages[0]["text"] == "PAGE ONE"
        assert pages[0]["page_number"] == 1

    def test_multiple_pages(self):
        doc = parse_comic("# PAGE ONE\n\nAction.\n\n# PAGE TWO\n\nMore action.\n\n# PAGE THREE\n")
        pages = elements_of_type(doc, "PageHeader")
        assert len(pages) == 3
        assert pages[0]["page_number"] == 1
        assert pages[1]["page_number"] == 2
        assert pages[2]["page_number"] == 3

    def test_page_case_insensitive(self):
        doc = parse_comic("# page one\n")
        pages = elements_of_type(doc, "PageHeader")
        assert len(pages) == 1

    def test_page_with_number(self):
        doc = parse_comic("# PAGE 7\n")
        pages = elements_of_type(doc, "PageHeader")
        assert pages[0]["text"] == "PAGE 7"

    def test_non_page_section_preserved(self):
        doc = parse_comic("# ACT ONE\n")
        sections = elements_of_type(doc, "Section")
        assert len(sections) == 1
        assert sections[0]["text"] == "ACT ONE"

    def test_standard_mode_no_page_header(self):
        doc = parse_standard("# PAGE ONE\n")
        pages = elements_of_type(doc, "PageHeader")
        assert len(pages) == 0
        sections = elements_of_type(doc, "Section")
        assert len(sections) == 1


class TestPanelHeader:
    def test_basic_panel(self):
        doc = parse_comic("# PAGE ONE\n\nPANEL 1\n")
        panels = elements_of_type(doc, "PanelHeader")
        assert len(panels) == 1
        assert panels[0]["text"] == "PANEL 1"
        assert panels[0]["panel_number"] == 1

    def test_forced_panel(self):
        doc = parse_comic("# PAGE ONE\n\n.PANEL 3\n")
        panels = elements_of_type(doc, "PanelHeader")
        assert len(panels) == 1

    def test_panel_numbering_resets_on_new_page(self):
        doc = parse_comic("# PAGE ONE\n\nPANEL 1\n\nPANEL 2\n\n# PAGE TWO\n\nPANEL 1\n")
        panels = elements_of_type(doc, "PanelHeader")
        assert len(panels) == 3
        assert panels[0]["panel_number"] == 1
        assert panels[1]["panel_number"] == 2
        assert panels[2]["panel_number"] == 1

    def test_standard_mode_no_panel(self):
        doc = parse_standard("PANEL 1\n")
        panels = elements_of_type(doc, "PanelHeader")
        assert len(panels) == 0


class TestSfx:
    def test_basic_sfx(self):
        doc = parse_comic("# PAGE ONE\n\nPANEL 1\n\nSFX: KRAKOOM\n")
        sfx = elements_of_type(doc, "Sfx")
        assert len(sfx) == 1
        assert sfx[0]["text"] == "KRAKOOM"
        assert sfx[0]["number"] == 1

    def test_sfx_case_insensitive(self):
        doc = parse_comic("# PAGE ONE\n\nsfx: boom\n")
        sfx = elements_of_type(doc, "Sfx")
        assert len(sfx) == 1
        assert sfx[0]["text"] == "boom"

    def test_sfx_numbering_shared_with_dialogue(self):
        doc = parse_comic(
            "# PAGE ONE\n\nPANEL 1\n\n"
            "BATMAN\nHello.\n\n"
            "SFX: CRASH\n\n"
            "CAP: A caption.\n"
        )
        sfx = elements_of_type(doc, "Sfx")
        caps = elements_of_type(doc, "Caption")
        assert sfx[0]["number"] == 2
        assert caps[0]["number"] == 3

    def test_sfx_numbering_resets_on_new_page(self):
        doc = parse_comic(
            "# PAGE ONE\n\nSFX: BOOM\n\n"
            "# PAGE TWO\n\nSFX: CRASH\n"
        )
        sfx = elements_of_type(doc, "Sfx")
        assert sfx[0]["number"] == 1
        assert sfx[1]["number"] == 1

    def test_standard_mode_no_sfx(self):
        doc = parse_standard("SFX: BOOM\n")
        sfx = elements_of_type(doc, "Sfx")
        assert len(sfx) == 0


class TestCaption:
    def test_basic_caption(self):
        doc = parse_comic("# PAGE ONE\n\nCAP: The city never sleeps.\n")
        caps = elements_of_type(doc, "Caption")
        assert len(caps) == 1
        assert caps[0]["text"] == "The city never sleeps."
        assert caps[0]["subtype"] == "CAPTION"
        assert caps[0]["number"] == 1

    def test_caption_long_form(self):
        doc = parse_comic("# PAGE ONE\n\nCAPTION: Longer form.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "CAPTION"

    def test_banner_subtype(self):
        doc = parse_comic("# PAGE ONE\n\nBANNER: Gotham City. Midnight.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "BANNER"

    def test_voice_over_subtype(self):
        doc = parse_comic("# PAGE ONE\n\nVOICE OVER: Narrating here.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "VOICE OVER"

    def test_vo_subtype(self):
        doc = parse_comic("# PAGE ONE\n\nVO: Short form.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "VOICE OVER"

    def test_narration_subtype(self):
        doc = parse_comic("# PAGE ONE\n\nNARRATION: The hero speaks.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "NARRATION"

    def test_internal_subtype(self):
        doc = parse_comic("# PAGE ONE\n\nINTERNAL: Thought bubble.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "INTERNAL"

    def test_editorial_subtype(self):
        doc = parse_comic("# PAGE ONE\n\nEDITORIAL: See issue #42.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "EDITORIAL"

    def test_time_place_subtype(self):
        doc = parse_comic("# PAGE ONE\n\nTIME-PLACE: New York, 1942.\n")
        caps = elements_of_type(doc, "Caption")
        assert caps[0]["subtype"] == "BANNER"


class TestLetteringNumbering:
    def test_per_page_numbering(self):
        script = (
            "# PAGE ONE\n\n"
            "PANEL 1\n\n"
            "BATMAN\nFirst line.\n\n"
            "CAP: Caption one.\n\n"
            "SFX: BOOM\n\n"
            "# PAGE TWO\n\n"
            "PANEL 1\n\n"
            "ROBIN\nSecond page first.\n\n"
            "CAP: Caption two page.\n"
        )
        doc = parse_comic(script)
        sfx = elements_of_type(doc, "Sfx")
        caps = elements_of_type(doc, "Caption")

        assert sfx[0]["number"] == 3
        assert caps[0]["number"] == 2
        assert caps[1]["number"] == 2

    def test_dialogue_increments_lettering(self):
        script = (
            "# PAGE ONE\n\n"
            "PANEL 1\n\n"
            "BATMAN\nLine one.\n\n"
            "JOKER\nLine two.\n\n"
            "SFX: HAHA\n"
        )
        doc = parse_comic(script)
        sfx = elements_of_type(doc, "Sfx")
        assert sfx[0]["number"] == 3


class TestBalloonParentheticals:
    def test_balloon_types_in_dialogue(self):
        script = (
            "# PAGE ONE\n\n"
            "PANEL 1\n\n"
            "BATMAN\n(whisper)\nI am the night.\n\n"
            "JOKER\n(burst)\nHA HA HA!\n"
        )
        doc = parse_comic(script)
        parens = elements_of_type(doc, "Parenthetical")
        assert len(parens) == 2
        assert parens[0]["text"] == "(whisper)"
        assert parens[1]["text"] == "(burst)"


# ---------------------------------------------------------------------------
# Dialect registry
# ---------------------------------------------------------------------------

class TestComicDialects:
    def test_dialects_contain_new_ids(self):
        dialects = json.loads(ecrit_core.get_dialects())
        ids = [d["id"] for d in dialects]
        assert "fountain+comic-dc" in ids
        assert "fountain+comic-dh" in ids
        assert "fountain+comic-indie" in ids

    def test_old_ids_removed(self):
        dialects = json.loads(ecrit_core.get_dialects())
        ids = [d["id"] for d in dialects]
        assert "fountain+comic-full" not in ids
        assert "fountain+comic-plot" not in ids
        assert "fountain+comic-lean" not in ids
        assert "fountain+comic-gn" not in ids

    def test_categories_updated(self):
        categories = json.loads(ecrit_core.get_format_categories())
        comic_cat = next(c for c in categories if "Comics" in c["name"])
        assert "fountain+comic-dc" in comic_cat["formats"]
        assert "fountain+comic-dh" in comic_cat["formats"]
        assert "fountain+comic-indie" in comic_cat["formats"]
        assert len(comic_cat["formats"]) == 3

    def test_dc_dialect_has_extra_elements(self):
        dialects = json.loads(ecrit_core.get_dialects())
        dc = next(d for d in dialects if d["id"] == "fountain+comic-dc")
        tags = [e["tag"] for e in dc["extra_elements"]]
        assert "page_header" in tags
        assert "panel_header" in tags
        assert "caption" in tags
        assert "sfx" in tags

    def test_all_comic_formats_activate_parsing(self):
        script = "# PAGE ONE\n\nPANEL 1\n\nSFX: BOOM\n"
        for fmt in ["fountain+comic-dc", "fountain+comic-dh", "fountain+comic-indie"]:
            doc = json.loads(ecrit_core.parse_fountain(script, fmt))
            pages = elements_of_type(doc, "PageHeader")
            assert len(pages) == 1, f"PageHeader not parsed for {fmt}"
            sfx = elements_of_type(doc, "Sfx")
            assert len(sfx) == 1, f"Sfx not parsed for {fmt}"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestComicStats:
    def test_comic_page_count(self):
        script = "# PAGE ONE\n\n# PAGE TWO\n\n# PAGE THREE\n"
        stats = stats_comic(script)
        assert stats["comic_page_count"] == 3

    def test_panel_count(self):
        script = "# PAGE ONE\n\nPANEL 1\n\nPANEL 2\n\nPANEL 3\n"
        stats = stats_comic(script)
        assert stats["panel_count"] == 3

    def test_sfx_count(self):
        script = "# PAGE ONE\n\nSFX: BOOM\n\nSFX: CRASH\n"
        stats = stats_comic(script)
        assert stats["sfx_count"] == 2

    def test_caption_count(self):
        script = "# PAGE ONE\n\nCAP: One.\n\nBANNER: Two.\n\nVO: Three.\n"
        stats = stats_comic(script)
        assert stats["caption_count"] == 3

    def test_caption_words_count_as_dialogue(self):
        script = "# PAGE ONE\n\nCAP: Three words here.\n"
        stats = stats_comic(script)
        assert stats["word_count"] >= 3
        assert stats["dialogue_percentage"] > 0

    def test_sfx_words_count_as_action(self):
        script = "# PAGE ONE\n\nSFX: KRAKKA BOOM BOOM\n"
        stats = stats_comic(script)
        assert stats["action_percentage"] > 0

    def test_standard_mode_zero_comic_stats(self):
        script = "INT. OFFICE - DAY\n\nAction here.\n"
        stats = json.loads(ecrit_core.get_script_stats(script))
        assert stats["comic_page_count"] == 0
        assert stats["panel_count"] == 0
        assert stats["sfx_count"] == 0
        assert stats["caption_count"] == 0


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_parse_fountain_no_format_id(self):
        doc = json.loads(ecrit_core.parse_fountain("INT. OFFICE - DAY\n\nAction.\n"))
        headings = elements_of_type(doc, "SceneHeading")
        assert len(headings) == 1

    def test_get_script_stats_no_format_id(self):
        stats = json.loads(ecrit_core.get_script_stats("INT. OFFICE - DAY\n\nAction.\n"))
        assert stats["scene_count"] == 1

    def test_comic_syntax_in_standard_mode_becomes_action(self):
        doc = parse_standard("INT. OFFICE - DAY\n\nSFX: BOOM\n")
        actions = elements_of_type(doc, "Action")
        assert any("SFX" in a["text"] for a in actions)

    def test_standard_elements_still_work_in_comic_mode(self):
        script = (
            "# PAGE ONE\n\n"
            "PANEL 1\n\n"
            "INT. OFFICE - DAY\n\n"
            "Action description.\n\n"
            "BATMAN\nHello.\n"
        )
        doc = parse_comic(script)
        headings = elements_of_type(doc, "SceneHeading")
        actions = elements_of_type(doc, "Action")
        chars = elements_of_type(doc, "Character")
        assert len(headings) == 1
        assert len(actions) >= 1
        assert len(chars) == 1


# ---------------------------------------------------------------------------
# Full script integration test
# ---------------------------------------------------------------------------

class TestFullComicScript:
    SCRIPT = """\
Title: The Dark Knight Returns
Credit: Written by
Author: Test Writer

# PAGE ONE

PANEL 1

Wide establishing shot of GOTHAM CITY at night. Rain hammers the skyline.
Lightning cracks the sky in the distance.

CAP: The city remembers what it was.

PANEL 2

Close on BATMAN perched on a gargoyle, cape whipping in the wind.

BATMAN
(whisper)
Tonight we end this.

SFX: KRAKOOM

PANEL 3

Below, CATWOMAN lands silently on a fire escape.

CATWOMAN
(off)
You always say that.

BANNER: Gotham City. 3:47 AM.

# PAGE TWO

PANEL 1

Interior of the Batcave. Alfred stands by the computer array.

ALFRED
Master Wayne, the signal—

PANEL 2

Batman drops from above into the cave.

BATMAN
I saw it.

CAP: He always sees it.

SFX: THWIP

VOICE OVER: Some nights you wonder if it's worth it.
"""

    def test_page_count(self):
        stats = stats_comic(self.SCRIPT)
        assert stats["comic_page_count"] == 2

    def test_panel_count(self):
        stats = stats_comic(self.SCRIPT)
        assert stats["panel_count"] == 5

    def test_sfx_count(self):
        stats = stats_comic(self.SCRIPT)
        assert stats["sfx_count"] == 2

    def test_caption_count(self):
        stats = stats_comic(self.SCRIPT)
        assert stats["caption_count"] == 4

    def test_character_count(self):
        stats = stats_comic(self.SCRIPT)
        names = [c["name"] for c in stats["characters"]]
        assert "BATMAN" in names
        assert "CATWOMAN" in names
        assert "ALFRED" in names

    def test_all_element_types_present(self):
        doc = parse_comic(self.SCRIPT)
        types = set(e["type"] for e in doc["elements"])
        assert "PageHeader" in types
        assert "PanelHeader" in types
        assert "Sfx" in types
        assert "Caption" in types
        assert "Character" in types
        assert "Dialogue" in types
        assert "Parenthetical" in types
        assert "Action" in types

    def test_lettering_numbers_reset_on_page_two(self):
        doc = parse_comic(self.SCRIPT)
        page2_elements = []
        on_page2 = False
        for e in doc["elements"]:
            if e["type"] == "PageHeader" and "TWO" in e.get("text", ""):
                on_page2 = True
                continue
            if on_page2 and e["type"] in ("Sfx", "Caption", "Character"):
                page2_elements.append(e)

        sfx_on_p2 = [e for e in page2_elements if e["type"] == "Sfx"]
        cap_on_p2 = [e for e in page2_elements if e["type"] == "Caption"]
        assert len(sfx_on_p2) == 1
        assert sfx_on_p2[0]["number"] is not None
        assert len(cap_on_p2) == 2
