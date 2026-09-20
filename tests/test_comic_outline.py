"""Tests for comic-specific outline nodes, templates, and outline-manuscript sync."""

import json
import pytest

from ecrit.screenplay.structure_templates import (
    COMIC_TEMPLATES, ComicTemplate, ComicBeat,
    generate_comic_outline_nodes,
)
from ecrit.screenplay.outline_sync import (
    outline_to_script, script_to_outline,
)

try:
    import ecrit_core
    HAS_CORE = True
except ImportError:
    HAS_CORE = False


# ---------------------------------------------------------------------------
# Comic structure templates
# ---------------------------------------------------------------------------

class TestComicTemplates:
    def test_22_page_template_exists(self):
        assert "comic_22_page" in COMIC_TEMPLATES

    def test_short_template_exists(self):
        assert "comic_short" in COMIC_TEMPLATES

    def test_gn_chapter_template_exists(self):
        assert "comic_gn_chapter" in COMIC_TEMPLATES

    def test_22_page_has_pages_and_panels(self):
        tpl = COMIC_TEMPLATES["comic_22_page"]
        kinds = {b.kind for b in tpl.beats}
        assert "Page" in kinds
        assert "Panel" in kinds
        assert "Spread" in kinds

    def test_short_has_5_pages(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        pages = [b for b in tpl.beats if b.kind == "Page"]
        assert len(pages) == 5

    def test_gn_chapter_has_spread(self):
        tpl = COMIC_TEMPLATES["comic_gn_chapter"]
        spreads = [b for b in tpl.beats if b.kind == "Spread"]
        assert len(spreads) >= 1

    def test_all_templates_have_names(self):
        for key, tpl in COMIC_TEMPLATES.items():
            assert tpl.name, f"Template {key} has no name"
            assert tpl.description, f"Template {key} has no description"


class TestGenerateComicOutlineNodes:
    def test_generates_nodes(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        assert len(nodes) == len(tpl.beats)

    def test_node_kinds_match_beats(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        for node, beat in zip(nodes, tpl.beats):
            assert node["kind"] == beat.kind

    def test_nodes_have_connections(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        connected = sum(1 for n in nodes if n["connections"])
        assert connected >= len(nodes) - 1

    def test_page_nodes_at_row_start(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        page_nodes = [n for n in nodes if n["kind"] == "Page"]
        for pn in page_nodes:
            assert pn["x"] == 40

    def test_panel_nodes_offset_from_page(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        panel_nodes = [n for n in nodes if n["kind"] == "Panel"]
        for pn in panel_nodes:
            assert pn["x"] > 40

    def test_empty_template_returns_empty(self):
        tpl = ComicTemplate(name="Empty", description="Nothing", beats=[])
        assert generate_comic_outline_nodes(tpl) == []

    def test_spread_node_created(self):
        tpl = COMIC_TEMPLATES["comic_22_page"]
        nodes = generate_comic_outline_nodes(tpl)
        spreads = [n for n in nodes if n["kind"] == "Spread"]
        assert len(spreads) >= 1

    def test_all_nodes_have_required_fields(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        for n in nodes:
            assert "id" in n
            assert "x" in n
            assert "y" in n
            assert "kind" in n
            assert "label" in n
            assert "connections" in n


# ---------------------------------------------------------------------------
# Outline → Script (comic mode)
# ---------------------------------------------------------------------------

class TestOutlineToScriptComic:
    def test_page_becomes_section_header(self):
        nodes = [
            {"id": 0, "kind": "Page", "label": "PAGE 1", "synopsis": "Hook", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain+comic-dc")
        assert "# PAGE 1" in script

    def test_panel_becomes_panel_header(self):
        nodes = [
            {"id": 0, "kind": "Page", "label": "PAGE 1", "synopsis": "", "x": 0, "y": 0, "connections": [1]},
            {"id": 1, "kind": "Panel", "label": "Panel 1", "synopsis": "Action here", "x": 220, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain+comic-dc")
        assert "PANEL 1" in script
        assert "Action here" in script

    def test_spread_becomes_section_header(self):
        nodes = [
            {"id": 0, "kind": "Spread", "label": "SPREAD (4-5)", "synopsis": "Big moment", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain+comic-dc")
        assert "# SPREAD (4-5)" in script

    def test_note_becomes_fountain_note(self):
        nodes = [
            {"id": 0, "kind": "Note", "label": "Remember the cape", "synopsis": "", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain+comic-dc")
        assert "[[Remember the cape]]" in script

    def test_full_page_structure(self):
        nodes = [
            {"id": 0, "kind": "Page", "label": "PAGE 1", "synopsis": "Splash", "x": 0, "y": 0, "connections": [1]},
            {"id": 1, "kind": "Panel", "label": "Panel 1", "synopsis": "Hero lands", "x": 220, "y": 0, "connections": [2]},
            {"id": 2, "kind": "Panel", "label": "Panel 2", "synopsis": "Villain reacts", "x": 440, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain+comic-dc")
        assert "# PAGE 1" in script
        assert "PANEL 1" in script
        assert "PANEL 2" in script
        lines = script.split("\n")
        page_idx = next(i for i, l in enumerate(lines) if "PAGE 1" in l)
        panel1_idx = next(i for i, l in enumerate(lines) if "PANEL 1" in l)
        panel2_idx = next(i for i, l in enumerate(lines) if "PANEL 2" in l)
        assert page_idx < panel1_idx < panel2_idx


# ---------------------------------------------------------------------------
# Outline → Script (screenplay mode)
# ---------------------------------------------------------------------------

class TestOutlineToScriptScreenplay:
    def test_act_break_becomes_section(self):
        nodes = [
            {"id": 0, "kind": "ActBreak", "label": "Act 1", "synopsis": "", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain/core")
        assert "# Act 1" in script

    def test_scene_becomes_heading(self):
        nodes = [
            {"id": 0, "kind": "Scene", "label": "INT. OFFICE - DAY", "synopsis": "", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain/core")
        assert "INT. OFFICE - DAY" in script

    def test_scene_without_prefix_gets_int(self):
        nodes = [
            {"id": 0, "kind": "Scene", "label": "The Chase", "synopsis": "", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain/core")
        assert "INT. THE CHASE - DAY" in script

    def test_transition_produces_to(self):
        nodes = [
            {"id": 0, "kind": "Transition", "label": "CUT", "synopsis": "", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain/core")
        assert "CUT TO:" in script

    def test_synopsis_preserved(self):
        nodes = [
            {"id": 0, "kind": "Scene", "label": "INT. BAR - NIGHT", "synopsis": "A tense meeting.", "x": 0, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain/core")
        assert "= A tense meeting." in script


# ---------------------------------------------------------------------------
# Script → Outline (comic mode)
# ---------------------------------------------------------------------------

class TestScriptToOutlineComic:
    @pytest.fixture()
    def comic_script(self):
        return (
            "# PAGE ONE\n\n"
            "PANEL 1\n\n"
            "Hero leaps from rooftop.\n\n"
            "PANEL 2\n\n"
            "Villain looks up.\n\n"
            "# PAGE TWO\n\n"
            "PANEL 1\n\n"
            "The confrontation.\n\n"
        )

    def test_extracts_pages(self, comic_script):
        nodes = script_to_outline(comic_script, "fountain+comic-dc")
        pages = [n for n in nodes if n["kind"] == "Page"]
        assert len(pages) == 2

    def test_extracts_panels(self, comic_script):
        nodes = script_to_outline(comic_script, "fountain+comic-dc")
        panels = [n for n in nodes if n["kind"] == "Panel"]
        assert len(panels) == 3

    def test_panels_get_synopsis_from_content(self, comic_script):
        nodes = script_to_outline(comic_script, "fountain+comic-dc")
        panels = [n for n in nodes if n["kind"] == "Panel"]
        assert any("Hero leaps" in p.get("synopsis", "") for p in panels)

    def test_page_nodes_at_row_start(self, comic_script):
        nodes = script_to_outline(comic_script, "fountain+comic-dc")
        pages = [n for n in nodes if n["kind"] == "Page"]
        for p in pages:
            assert p["x"] == 40

    def test_nodes_connected(self, comic_script):
        nodes = script_to_outline(comic_script, "fountain+comic-dc")
        connected_count = sum(1 for n in nodes if n["connections"])
        assert connected_count >= len(nodes) - 1


# ---------------------------------------------------------------------------
# Script → Outline (screenplay mode)
# ---------------------------------------------------------------------------

class TestScriptToOutlineScreenplay:
    @pytest.fixture()
    def screenplay(self):
        return (
            "# Act 1\n\n"
            "INT. COFFEE SHOP - DAY\n\n"
            "= The hero meets a stranger.\n\n"
            "They talk.\n\n"
            "INT. STREET - NIGHT\n\n"
            "A chase begins.\n\n"
        )

    def test_extracts_act(self, screenplay):
        nodes = script_to_outline(screenplay, "fountain/core")
        acts = [n for n in nodes if n["kind"] == "ActBreak"]
        assert len(acts) == 1

    def test_extracts_scenes(self, screenplay):
        nodes = script_to_outline(screenplay, "fountain/core")
        scenes = [n for n in nodes if n["kind"] == "Scene"]
        assert len(scenes) == 2

    def test_synopsis_from_marker(self, screenplay):
        nodes = script_to_outline(screenplay, "fountain/core")
        scenes = [n for n in nodes if n["kind"] == "Scene"]
        assert any("stranger" in s.get("synopsis", "") for s in scenes)

    def test_nodes_connected(self, screenplay):
        nodes = script_to_outline(screenplay, "fountain/core")
        connected_count = sum(1 for n in nodes if n["connections"])
        assert connected_count >= len(nodes) - 1


# ---------------------------------------------------------------------------
# Round-trip: outline → script → outline
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_comic_round_trip_preserves_page_count(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        script = outline_to_script(nodes, "fountain+comic-dc")
        nodes2 = script_to_outline(script, "fountain+comic-dc")
        pages_orig = sum(1 for n in nodes if n["kind"] == "Page")
        pages_rt = sum(1 for n in nodes2 if n["kind"] == "Page")
        assert pages_rt == pages_orig

    def test_comic_round_trip_preserves_panel_count(self):
        tpl = COMIC_TEMPLATES["comic_short"]
        nodes = generate_comic_outline_nodes(tpl)
        script = outline_to_script(nodes, "fountain+comic-dc")
        nodes2 = script_to_outline(script, "fountain+comic-dc")
        panels_orig = sum(1 for n in nodes if n["kind"] == "Panel")
        panels_rt = sum(1 for n in nodes2 if n["kind"] == "Panel")
        assert panels_rt == panels_orig

    def test_screenplay_round_trip_preserves_scene_count(self):
        nodes = [
            {"id": 0, "kind": "ActBreak", "label": "Act 1", "synopsis": "", "x": 0, "y": 0, "connections": [1]},
            {"id": 1, "kind": "Scene", "label": "INT. OFFICE - DAY", "synopsis": "Meeting.", "x": 220, "y": 0, "connections": [2]},
            {"id": 2, "kind": "Scene", "label": "EXT. PARK - NIGHT", "synopsis": "Discovery.", "x": 440, "y": 0, "connections": []},
        ]
        script = outline_to_script(nodes, "fountain/core")
        nodes2 = script_to_outline(script, "fountain/core")
        scenes_orig = sum(1 for n in nodes if n["kind"] == "Scene")
        scenes_rt = sum(1 for n in nodes2 if n["kind"] == "Scene")
        assert scenes_rt == scenes_orig


# ---------------------------------------------------------------------------
# Canvas node types
# ---------------------------------------------------------------------------

class TestCanvasNodeTypes:
    def test_node_sizes_include_comic_types(self):
        from ecrit.ui.screens.editor import OutlineCanvas
        assert "Page" in OutlineCanvas.NODE_SIZES
        assert "Panel" in OutlineCanvas.NODE_SIZES
        assert "Spread" in OutlineCanvas.NODE_SIZES

    def test_page_wider_than_scene(self):
        from ecrit.ui.screens.editor import OutlineCanvas
        page_w = OutlineCanvas.NODE_SIZES["Page"][0]
        scene_w = OutlineCanvas.NODE_SIZES["Scene"][0]
        assert page_w > scene_w

    def test_spread_widest(self):
        from ecrit.ui.screens.editor import OutlineCanvas
        spread_w = OutlineCanvas.NODE_SIZES["Spread"][0]
        for kind, (w, h) in OutlineCanvas.NODE_SIZES.items():
            if kind != "Spread":
                assert spread_w >= w


# ---------------------------------------------------------------------------
# Outline phase format awareness
# ---------------------------------------------------------------------------

class TestOutlinePhaseFormatAware:
    def test_outline_phase_has_set_format_id(self):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase.set_format_id("fountain+comic-dc")
        assert phase._format_id == "fountain+comic-dc"
        assert phase.canvas._comic_mode is True

    def test_outline_phase_standard_mode(self):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase.set_format_id("fountain/core")
        assert phase.canvas._comic_mode is False

    def test_template_combo_changes_with_format(self):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase.set_format_id("fountain+comic-dc")
        items = [phase.template_combo.itemText(i) for i in range(phase.template_combo.count())]
        assert any("Page" in item or "Issue" in item or "Short" in item or "Chapter" in item for item in items)

    def test_template_combo_screenplay_mode(self):
        from ecrit.ui.screens.editor import OutlinePhase
        phase = OutlinePhase()
        phase.set_format_id("fountain/core")
        items = [phase.template_combo.itemText(i) for i in range(phase.template_combo.count())]
        assert any("Three-Act" in item for item in items)
