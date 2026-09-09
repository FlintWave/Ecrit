"""Tests for screenplay modules: logline builder, contest presets,
production reports, revisions, scene numbers, structure templates."""

import pytest
from datetime import date

from tests.conftest import SAMPLE_FOUNTAIN, UNICODE_FOUNTAIN, HUGE_FOUNTAIN


class TestLoglineBuilder:
    def test_list_templates(self):
        from ecrit.screenplay.logline_builder import list_logline_templates
        templates = list_logline_templates()
        assert len(templates) >= 5
        keys = [k for k, _ in templates]
        assert "classic" in keys
        assert "with_antagonist" in keys

    def test_get_fields(self):
        from ecrit.screenplay.logline_builder import get_logline_fields
        fields = get_logline_fields("classic")
        assert "protagonist" in fields
        assert "inciting_incident" in fields

    def test_get_fields_unknown(self):
        from ecrit.screenplay.logline_builder import get_logline_fields
        with pytest.raises(KeyError):
            get_logline_fields("nonexistent")

    def test_build_classic(self):
        from ecrit.screenplay.logline_builder import build_logline
        result = build_logline("classic", {
            "inciting_incident": "aliens invade",
            "protagonist": "retired pilot",
            "objective": "save Earth",
            "stakes": "all is lost",
        })
        assert "aliens invade" in result
        assert "retired pilot" in result

    def test_build_unknown_template(self):
        from ecrit.screenplay.logline_builder import build_logline
        with pytest.raises(KeyError):
            build_logline("nope", {})

    def test_build_all_templates(self):
        from ecrit.screenplay.logline_builder import (
            LOGLINE_TEMPLATES, build_logline, get_logline_fields
        )
        for key, tmpl in LOGLINE_TEMPLATES.items():
            fields = get_logline_fields(key)
            values = {f: f"test_{f}" for f in fields}
            result = build_logline(key, values)
            assert len(result) > 0
            for f in fields:
                assert f"test_{f}" in result

    def test_validate_short(self):
        from ecrit.screenplay.logline_builder import validate_logline
        result = validate_logline("Short text")
        assert result["word_count"] == 2
        assert result["length"] == "short"

    def test_validate_good(self):
        from ecrit.screenplay.logline_builder import validate_logline
        result = validate_logline(" ".join(["word"] * 25))
        assert result["length"] == "good"

    def test_validate_long(self):
        from ecrit.screenplay.logline_builder import validate_logline
        result = validate_logline(" ".join(["word"] * 60))
        assert result["length"] == "long"

    def test_validate_empty(self):
        from ecrit.screenplay.logline_builder import validate_logline
        result = validate_logline("")
        assert result["word_count"] == 0

    def test_unicode_values(self):
        from ecrit.screenplay.logline_builder import build_logline
        result = build_logline("classic", {
            "inciting_incident": "Héloïse disparaît",
            "protagonist": "détective français",
            "objective": "la retrouver",
            "stakes": "le café ferme",
        })
        assert "Héloïse" in result
        assert "détective" in result


class TestContestPresets:
    def test_list_presets(self):
        from ecrit.screenplay.contest_presets import list_presets
        presets = list_presets()
        assert len(presets) >= 7

    def test_get_preset(self):
        from ecrit.screenplay.contest_presets import get_preset
        nicholl = get_preset("nicholl")
        assert nicholl is not None
        assert nicholl.name == "Nicholl Fellowship"
        assert nicholl.paper == "USLetter"

    def test_get_preset_none(self):
        from ecrit.screenplay.contest_presets import get_preset
        assert get_preset("nonexistent") is None

    def test_all_presets_have_required_fields(self):
        from ecrit.screenplay.contest_presets import CONTEST_PRESETS
        for key, preset in CONTEST_PRESETS.items():
            assert preset.name, f"{key} missing name"
            assert preset.organization, f"{key} missing organization"
            assert preset.paper in ("USLetter", "A4"), f"{key} bad paper: {preset.paper}"
            assert preset.font_size > 0, f"{key} bad font_size"

    def test_validate_short_script(self):
        from ecrit.screenplay.contest_presets import validate_against_preset
        warnings = validate_against_preset("INT. ROOM\n\nHello\n", "nicholl")
        assert any("below" in w.lower() for w in warnings)

    def test_validate_unknown_preset(self):
        from ecrit.screenplay.contest_presets import validate_against_preset
        with pytest.raises(KeyError):
            validate_against_preset("text", "nonexistent")

    def test_bbc_uses_a4(self):
        from ecrit.screenplay.contest_presets import get_preset
        bbc = get_preset("bbc_writersroom")
        assert bbc.paper == "A4"

    def test_nicholl_no_scene_numbers(self):
        from ecrit.screenplay.contest_presets import get_preset
        nicholl = get_preset("nicholl")
        assert nicholl.scene_numbers is False


class TestProductionReports:
    def test_scene_report_basic(self):
        from ecrit.screenplay.production_reports import generate_scene_report
        script = "INT. ROOM - DAY\n\nAction\n\nCHARACTER\nDialogue\n"
        scenes = generate_scene_report(script)
        assert len(scenes) >= 1
        assert scenes[0]["heading"] == "INT. ROOM - DAY"
        assert scenes[0]["int_ext"] == "INT"
        assert scenes[0]["time_of_day"] == "DAY"

    def test_scene_report_multiple(self):
        from ecrit.screenplay.production_reports import generate_scene_report
        scenes = generate_scene_report(SAMPLE_FOUNTAIN)
        assert len(scenes) >= 1

    def test_scene_report_empty(self):
        from ecrit.screenplay.production_reports import generate_scene_report
        scenes = generate_scene_report("")
        assert scenes == []

    def test_cast_report(self):
        from ecrit.screenplay.production_reports import generate_cast_report
        script = "INT. ROOM - DAY\n\nALICE\nHello\n\nBOB\nHi there\n\nALICE\nBye\n"
        cast = generate_cast_report(script)
        names = [c["name"] for c in cast]
        assert "ALICE" in names
        assert "BOB" in names
        alice = next(c for c in cast if c["name"] == "ALICE")
        assert alice["dialogue_lines"] >= 2

    def test_cast_report_empty(self):
        from ecrit.screenplay.production_reports import generate_cast_report
        assert generate_cast_report("") == []

    def test_location_report(self):
        from ecrit.screenplay.production_reports import generate_location_report
        script = "INT. OFFICE - DAY\n\nAction\n\nEXT. PARK - NIGHT\n\nAction\n\nINT. OFFICE - NIGHT\n\nAction\n"
        locs = generate_location_report(script)
        loc_names = [l["location"] for l in locs]
        assert "OFFICE" in loc_names
        assert "PARK" in loc_names
        office = next(l for l in locs if l["location"] == "OFFICE")
        assert office["scene_count"] == 2

    def test_location_report_empty(self):
        from ecrit.screenplay.production_reports import generate_location_report
        assert generate_location_report("") == []

    def test_day_night_report(self):
        from ecrit.screenplay.production_reports import generate_day_night_report
        script = "INT. A - DAY\n\nX\n\nEXT. B - NIGHT\n\nY\n\nINT. C - DAY\n\nZ\n"
        dn = generate_day_night_report(script)
        assert "DAY" in dn
        assert "NIGHT" in dn
        assert len(dn["DAY"]) == 2
        assert len(dn["NIGHT"]) == 1

    def test_one_liner(self):
        from ecrit.screenplay.production_reports import generate_one_liner
        script = "INT. ROOM - DAY\n\nAlice enters the room nervously.\n"
        liners = generate_one_liner(script)
        assert len(liners) >= 1
        assert "INT. ROOM" in liners[0]["heading"]

    def test_one_liner_empty(self):
        from ecrit.screenplay.production_reports import generate_one_liner
        assert generate_one_liner("") == []

    def test_parse_scene_heading(self):
        from ecrit.screenplay.production_reports import _parse_scene_heading
        result = _parse_scene_heading("INT. COFFEE SHOP - DAY")
        assert result["int_ext"] == "INT"
        assert result["location"] == "COFFEE SHOP"
        assert result["time_of_day"] == "DAY"

    def test_parse_ext_heading(self):
        from ecrit.screenplay.production_reports import _parse_scene_heading
        result = _parse_scene_heading("EXT. BEACH - SUNSET")
        assert result["int_ext"] == "EXT"
        assert result["location"] == "BEACH"

    def test_parse_int_ext_heading(self):
        from ecrit.screenplay.production_reports import _parse_scene_heading
        result = _parse_scene_heading("INT./EXT. CAR - MOVING - DAY")
        assert "INT" in result["int_ext"] and "EXT" in result["int_ext"]

    def test_reports_with_unicode(self):
        from ecrit.screenplay.production_reports import generate_scene_report
        scenes = generate_scene_report(UNICODE_FOUNTAIN)
        assert len(scenes) >= 1

    def test_reports_with_huge_script(self):
        from ecrit.screenplay.production_reports import generate_scene_report
        scenes = generate_scene_report(HUGE_FOUNTAIN)
        assert len(scenes) > 100


class TestRevisions:
    def test_initial_state(self):
        from ecrit.screenplay.revisions import RevisionTracker
        tracker = RevisionTracker()
        assert tracker.current_revision().color == "White"

    def test_add_revision(self):
        from ecrit.screenplay.revisions import RevisionTracker
        tracker = RevisionTracker()
        r = tracker.add_revision([1, 2, 3])
        assert r.color == "Blue"

    def test_revision_sequence(self):
        from ecrit.screenplay.revisions import RevisionTracker, REVISION_COLORS
        tracker = RevisionTracker()
        for i in range(5):
            r = tracker.add_revision([1])
        assert r.color == REVISION_COLORS[5]

    def test_get_page_color(self):
        from ecrit.screenplay.revisions import RevisionTracker
        tracker = RevisionTracker()
        tracker.add_revision([1, 5])
        assert tracker.get_page_color(1) == "Blue"
        assert tracker.get_page_color(5) == "Blue"
        assert tracker.get_page_color(3) == "White"

    def test_revision_header(self):
        from ecrit.screenplay.revisions import RevisionTracker
        tracker = RevisionTracker()
        tracker.add_revision([1])
        header = tracker.get_revision_header()
        assert "BLUE" in header

    def test_revision_history(self):
        from ecrit.screenplay.revisions import RevisionTracker
        tracker = RevisionTracker()
        tracker.add_revision([1], "First revision")
        tracker.add_revision([2], "Second revision")
        history = tracker.get_revision_history()
        assert len(history) == 3  # White + Blue + Pink
        assert history[0].color == "White"

    def test_reset(self):
        from ecrit.screenplay.revisions import RevisionTracker
        tracker = RevisionTracker()
        tracker.add_revision([1])
        tracker.add_revision([2])
        tracker.reset()
        assert tracker.current_revision().color == "White"
        assert len(tracker.get_revision_history()) == 1

    def test_roundtrip(self):
        from ecrit.screenplay.revisions import RevisionTracker
        tracker = RevisionTracker()
        tracker.add_revision([1, 5, 10], "Scene changes")
        tracker.add_revision([3, 7])
        data = tracker.to_dict()
        restored = RevisionTracker.from_dict(data)
        assert restored.current_revision().color == tracker.current_revision().color
        assert len(restored.get_revision_history()) == len(tracker.get_revision_history())

    def test_format_revision_mark(self):
        from ecrit.screenplay.revisions import format_revision_mark
        result = format_revision_mark("Hello", "Blue")
        assert result.endswith("*")
        assert "Hello" in result

    def test_get_revision_color_hex(self):
        from ecrit.screenplay.revisions import get_revision_color_hex
        assert get_revision_color_hex("Blue").startswith("#")
        assert get_revision_color_hex("Pink").startswith("#")
        assert get_revision_color_hex("White").startswith("#")

    def test_color_hex_unknown(self):
        from ecrit.screenplay.revisions import get_revision_color_hex
        result = get_revision_color_hex("nonexistent")
        assert result.startswith("#")

    def test_revision_colors_order(self):
        from ecrit.screenplay.revisions import REVISION_COLORS
        assert REVISION_COLORS[0] == "White"
        assert REVISION_COLORS[1] == "Blue"
        assert REVISION_COLORS[2] == "Pink"
        assert len(REVISION_COLORS) >= 10

    def test_many_revisions_exhausts(self):
        from ecrit.screenplay.revisions import RevisionTracker, REVISION_COLORS
        tracker = RevisionTracker()
        for i in range(len(REVISION_COLORS) - 1):
            tracker.add_revision([1])
        assert tracker.current_revision().color == REVISION_COLORS[-1]
        with pytest.raises(IndexError):
            tracker.add_revision([1])


class TestStructureTemplates:
    def test_list_templates(self):
        from ecrit.screenplay.structure_templates import list_templates
        templates = list_templates()
        assert len(templates) >= 7
        keys = [k for k, _ in templates]
        assert "three_act" in keys
        assert "save_the_cat" in keys
        assert "heros_journey" in keys
        assert "story_circle" in keys
        assert "five_act" in keys
        assert "kishotenketsu" in keys
        assert "sequence_approach" in keys

    def test_get_template(self):
        from ecrit.screenplay.structure_templates import get_template
        t = get_template("three_act")
        assert t is not None
        assert t.name == "Three-Act Structure"
        assert len(t.beats) > 0

    def test_get_template_none(self):
        from ecrit.screenplay.structure_templates import get_template
        assert get_template("nonexistent") is None

    def test_all_templates_have_beats(self):
        from ecrit.screenplay.structure_templates import TEMPLATES
        for key, tmpl in TEMPLATES.items():
            assert len(tmpl.beats) > 0, f"{key} has no beats"
            assert tmpl.name, f"{key} has no name"
            assert tmpl.description, f"{key} has no description"

    def test_beats_have_required_fields(self):
        from ecrit.screenplay.structure_templates import TEMPLATES
        for key, tmpl in TEMPLATES.items():
            for beat in tmpl.beats:
                assert beat.name, f"{key} beat missing name"
                assert beat.act >= 1, f"{key} beat {beat.name} bad act"
                assert 0 <= beat.percentage <= 100, f"{key} beat {beat.name} bad %"

    def test_save_the_cat_has_15_beats(self):
        from ecrit.screenplay.structure_templates import get_template
        stc = get_template("save_the_cat")
        assert len(stc.beats) == 15

    def test_heros_journey_has_12_beats(self):
        from ecrit.screenplay.structure_templates import get_template
        hj = get_template("heros_journey")
        assert len(hj.beats) == 12

    def test_story_circle_has_8_beats(self):
        from ecrit.screenplay.structure_templates import get_template
        sc = get_template("story_circle")
        assert len(sc.beats) == 8

    def test_generate_outline_nodes(self):
        from ecrit.screenplay.structure_templates import get_template, generate_outline_nodes
        tmpl = get_template("three_act")
        nodes = generate_outline_nodes(tmpl)
        assert len(nodes) > 0
        kinds = {n["kind"] for n in nodes}
        assert "ActBreak" in kinds
        assert "Scene" in kinds

    def test_outline_nodes_have_positions(self):
        from ecrit.screenplay.structure_templates import get_template, generate_outline_nodes
        tmpl = get_template("save_the_cat")
        nodes = generate_outline_nodes(tmpl)
        for node in nodes:
            assert "x" in node
            assert "y" in node
            assert "id" in node
            assert "label" in node
            assert "kind" in node

    def test_generate_nodes_all_templates(self):
        from ecrit.screenplay.structure_templates import TEMPLATES, generate_outline_nodes
        for key, tmpl in TEMPLATES.items():
            nodes = generate_outline_nodes(tmpl)
            assert len(nodes) > 0, f"{key} generated no nodes"

    def test_beats_percentage_order(self):
        from ecrit.screenplay.structure_templates import TEMPLATES
        for key, tmpl in TEMPLATES.items():
            percentages = [b.percentage for b in tmpl.beats]
            assert percentages == sorted(percentages), f"{key} beats not in order"


class TestSceneNumbers:
    def test_assign_basic(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers
        script = "INT. ROOM - DAY\n\nAction\n\nEXT. PARK - NIGHT\n\nMore action\n"
        scenes = assign_scene_numbers(script)
        assert len(scenes) == 2
        assert scenes[0].number == "1"
        assert scenes[1].number == "2"
        assert scenes[0].locked is False

    def test_assign_empty(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers
        assert assign_scene_numbers("") == []

    def test_assign_no_scenes(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers
        assert assign_scene_numbers("Just plain text\nNo scenes here\n") == []

    def test_assign_forced_heading(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers
        script = ".CUSTOM HEADING\n\nAction\n"
        scenes = assign_scene_numbers(script)
        assert len(scenes) >= 1

    def test_lock_scene(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers, lock_scene
        script = "INT. A - DAY\n\nINT. B - DAY\n"
        scenes = assign_scene_numbers(script)
        locked = lock_scene(scenes, 0)
        assert locked[0].locked is True
        assert locked[1].locked is False

    def test_lock_out_of_range(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers, lock_scene
        script = "INT. A - DAY\n"
        scenes = assign_scene_numbers(script)
        result = lock_scene(scenes, 99)
        assert len(result) == len(scenes)

    def test_unlock_scene(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers, lock_scene, unlock_scene
        script = "INT. A - DAY\n"
        scenes = assign_scene_numbers(script)
        locked = lock_scene(scenes, 0)
        assert locked[0].locked is True
        unlocked = unlock_scene(locked, 0)
        assert unlocked[0].locked is False

    def test_insert_scene_after(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers, insert_scene_after
        script = "INT. A - DAY\n\nEXT. B - NIGHT\n"
        scenes = assign_scene_numbers(script)
        result = insert_scene_after(scenes, 0)
        assert len(result) == 3
        assert result[1].number == "1A"

    def test_insert_multiple(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers, insert_scene_after
        script = "INT. A - DAY\n\nEXT. B - NIGHT\n"
        scenes = assign_scene_numbers(script)
        result = insert_scene_after(scenes, 0)
        result = insert_scene_after(result, 1)
        assert "1A" in [s.number for s in result]

    def test_insert_out_of_range(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers, insert_scene_after
        script = "INT. A - DAY\n"
        scenes = assign_scene_numbers(script)
        result = insert_scene_after(scenes, 99)
        assert len(result) == len(scenes)

    def test_renumber_all_unlocked(self):
        from ecrit.screenplay.scene_numbers import SceneNumber, renumber_scenes
        scenes = [
            SceneNumber("5", False, 0),
            SceneNumber("10", False, 5),
            SceneNumber("15", False, 10),
        ]
        result = renumber_scenes(scenes)
        assert result[0].number == "1"
        assert result[1].number == "2"
        assert result[2].number == "3"

    def test_renumber_with_locks(self):
        from ecrit.screenplay.scene_numbers import SceneNumber, renumber_scenes
        scenes = [
            SceneNumber("1", False, 0),
            SceneNumber("5", True, 5),
            SceneNumber("6", False, 10),
        ]
        result = renumber_scenes(scenes)
        assert result[1].number == "5"  # locked, unchanged
        assert result[1].locked is True

    def test_renumber_empty(self):
        from ecrit.screenplay.scene_numbers import renumber_scenes
        assert renumber_scenes([]) == []

    def test_renumber_all_locked(self):
        from ecrit.screenplay.scene_numbers import SceneNumber, renumber_scenes
        scenes = [
            SceneNumber("10", True, 0),
            SceneNumber("20", True, 5),
        ]
        result = renumber_scenes(scenes)
        assert result[0].number == "10"
        assert result[1].number == "20"

    def test_format_heading_left_only(self):
        from ecrit.screenplay.scene_numbers import SceneNumber, format_scene_heading
        sn = SceneNumber("5", False, 0)
        result = format_scene_heading("INT. OFFICE - DAY", sn, both_sides=False)
        assert "#5#" in result
        assert result.count("#5#") == 1

    def test_format_heading_both_sides(self):
        from ecrit.screenplay.scene_numbers import SceneNumber, format_scene_heading
        sn = SceneNumber("5A", True, 0)
        result = format_scene_heading("INT. OFFICE - DAY", sn, both_sides=True)
        assert result.count("#5A#") == 2

    def test_unicode_headings(self):
        from ecrit.screenplay.scene_numbers import assign_scene_numbers
        script = "INT. CAFÉ - JOUR\n\nAction\n\nEXT. CHÂTEAU - NUIT\n\nMore\n"
        scenes = assign_scene_numbers(script)
        assert len(scenes) == 2


class TestProductionReportsAdversarial:
    def test_scene_heading_no_dash(self):
        from ecrit.screenplay.production_reports import _parse_scene_heading
        result = _parse_scene_heading("INT. ROOM")
        assert result["int_ext"] == "INT"

    def test_malformed_heading(self):
        from ecrit.screenplay.production_reports import _parse_scene_heading
        result = _parse_scene_heading("Not a real heading")
        assert result["int_ext"] == ""

    def test_empty_heading(self):
        from ecrit.screenplay.production_reports import _parse_scene_heading
        result = _parse_scene_heading("")
        assert result["int_ext"] == ""

    def test_reports_only_headings_no_content(self):
        from ecrit.screenplay.production_reports import generate_scene_report
        script = "INT. A - DAY\n\nINT. B - NIGHT\n\nINT. C - DAWN\n"
        scenes = generate_scene_report(script)
        assert len(scenes) == 3
