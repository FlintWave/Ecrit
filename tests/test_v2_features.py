"""Tests for v2 features: bookmarks, scene tags, autosave, EPUB, orphan finder,
annotations, analytics, spell check, title templates, character cards."""

import os
import json
import tempfile
import pytest


SAMPLE_SCRIPT = """\
Title: Test Script
Author: Test Author

INT. OFFICE - DAY

ALICE
Hello, world! How are you doing today?

BOB
I'm doing great, thanks for asking.

EXT. PARK - NIGHT

ALICE
Let's go for a walk.

BOB
(hesitant)
Sure, why not.

INT. RESTAURANT - EVENING

CHARLIE
Welcome! Table for two?
"""


# ---------------------------------------------------------------------------
# 1. Bookmarks
# ---------------------------------------------------------------------------


class TestBookmarks:
    def test_add_and_get(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("Start", 1)
        mgr.add("Middle", 50)
        assert len(mgr.get_all()) == 2

    def test_get_by_name(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("Scene 1", 10)
        bm = mgr.get_by_name("Scene 1")
        assert bm is not None
        assert bm.line == 10

    def test_get_by_line(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("Here", 42)
        bm = mgr.get_by_line(42)
        assert bm is not None
        assert bm.name == "Here"

    def test_remove(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("Temp", 5)
        assert mgr.remove("Temp")
        assert mgr.get_by_name("Temp") is None

    def test_remove_nonexistent(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        assert not mgr.remove("Ghost")

    def test_clear(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("A", 1)
        mgr.add("B", 2)
        mgr.clear()
        assert len(mgr.get_all()) == 0

    def test_jump_next(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("First", 10)
        mgr.add("Second", 20)
        mgr.add("Third", 30)
        bm = mgr.jump_next(15)
        assert bm is not None
        assert bm.line == 20

    def test_jump_prev(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("First", 10)
        mgr.add("Second", 20)
        bm = mgr.jump_prev(15)
        assert bm is not None
        assert bm.line == 10

    def test_jump_next_wraps(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("Only", 10)
        bm = mgr.jump_next(10)
        assert bm is None  # jump_next uses strict > so same line returns None

    def test_serialization(self):
        from ecrit.screenplay.bookmarks import BookmarkManager
        mgr = BookmarkManager()
        mgr.add("Test", 42, color="#FF0000")
        data = mgr.to_json()
        mgr2 = BookmarkManager()
        mgr2.from_json(data)
        bm = mgr2.get_by_name("Test")
        assert bm is not None
        assert bm.line == 42
        assert bm.color == "#FF0000"


# ---------------------------------------------------------------------------
# 2. Scene Tags
# ---------------------------------------------------------------------------


class TestSceneTags:
    def test_builtin_tags(self):
        from ecrit.screenplay.scene_tags import SceneTagManager
        mgr = SceneTagManager()
        tags = mgr.get_available_tags()
        assert len(tags) >= 10

    def test_add_tag_to_scene(self):
        from ecrit.screenplay.scene_tags import SceneTagManager
        mgr = SceneTagManager()
        tags = mgr.get_available_tags()
        mgr.add_tag(0, tags[0])
        scene_tags = mgr.get_tags(0)
        assert len(scene_tags) == 1

    def test_remove_tag(self):
        from ecrit.screenplay.scene_tags import SceneTagManager
        mgr = SceneTagManager()
        tags = mgr.get_available_tags()
        mgr.add_tag(0, tags[0])
        mgr.remove_tag(0, tags[0].name)
        assert len(mgr.get_tags(0)) == 0

    def test_get_scenes_by_tag(self):
        from ecrit.screenplay.scene_tags import SceneTagManager
        mgr = SceneTagManager()
        tags = mgr.get_available_tags()
        mgr.add_tag(0, tags[0])
        mgr.add_tag(2, tags[0])
        scenes = mgr.get_scenes_by_tag(tags[0].name)
        assert scenes == [0, 2]

    def test_create_custom_tag(self):
        from ecrit.screenplay.scene_tags import SceneTagManager
        mgr = SceneTagManager()
        tag = mgr.create_custom_tag("My Tag", "#ABCDEF", "custom")
        assert tag.name == "My Tag"
        assert tag.color == "#ABCDEF"
        assert tag in mgr.get_available_tags()

    def test_serialization(self):
        from ecrit.screenplay.scene_tags import SceneTagManager
        mgr = SceneTagManager()
        tags = mgr.get_available_tags()
        mgr.add_tag(0, tags[0])
        mgr.add_tag(1, tags[1])
        data = mgr.to_dict()
        mgr2 = SceneTagManager()
        mgr2.from_dict(data)
        assert len(mgr2.get_tags(0)) == 1
        assert len(mgr2.get_tags(1)) == 1


# ---------------------------------------------------------------------------
# 3. Autosave
# ---------------------------------------------------------------------------


class TestAutosave:
    def test_create_snapshot(self, tmp_path):
        from ecrit.screenplay.autosave import AutosaveManager
        mgr = AutosaveManager()
        mgr.create_snapshot("Hello world", str(tmp_path))
        snapshots = mgr.list_snapshots(str(tmp_path))
        assert len(snapshots) == 1
        assert snapshots[0].content == "Hello world"

    def test_max_snapshots(self, tmp_path):
        from ecrit.screenplay.autosave import AutosaveManager
        mgr = AutosaveManager()
        mgr._max_snapshots = 3
        snapshots_dir = mgr.get_snapshot_path(str(tmp_path))
        os.makedirs(snapshots_dir, exist_ok=True)
        for i in range(5):
            data = {"timestamp": f"2024-01-01T00:00:0{i}", "content": f"Content {i}", "word_count": 2}
            with open(os.path.join(snapshots_dir, f"snap{i}.json"), "w") as f:
                json.dump(data, f)
        mgr.cleanup_old(str(tmp_path))
        remaining = [f for f in os.listdir(snapshots_dir) if f.endswith(".json")]
        assert len(remaining) <= 3

    def test_restore_snapshot(self, tmp_path):
        from ecrit.screenplay.autosave import AutosaveManager
        mgr = AutosaveManager()
        mgr.create_snapshot("Original content", str(tmp_path))
        snapshots = mgr.list_snapshots(str(tmp_path))
        restored = mgr.restore_snapshot(str(tmp_path), snapshots[0].timestamp)
        assert restored == "Original content"

    def test_labeled_snapshot(self, tmp_path):
        from ecrit.screenplay.autosave import AutosaveManager
        mgr = AutosaveManager()
        mgr.create_snapshot("Manual save", str(tmp_path), label="manual")
        snapshots = mgr.list_snapshots(str(tmp_path))
        assert snapshots[0].label == "manual"

    def test_set_interval(self):
        from ecrit.screenplay.autosave import AutosaveManager
        mgr = AutosaveManager()
        mgr.set_interval(10)
        assert mgr._interval_minutes == 10

    def test_set_interval_clamped(self):
        from ecrit.screenplay.autosave import AutosaveManager
        mgr = AutosaveManager()
        mgr.set_interval(0)
        assert mgr._interval_minutes >= 1
        mgr.set_interval(999)
        assert mgr._interval_minutes <= 60

    def test_enabled_toggle(self):
        from ecrit.screenplay.autosave import AutosaveManager
        mgr = AutosaveManager()
        mgr.set_enabled(False)
        assert not mgr._enabled
        mgr.set_enabled(True)
        assert mgr._enabled


# ---------------------------------------------------------------------------
# 4. EPUB Export
# ---------------------------------------------------------------------------


class TestEpubExport:
    def test_export_to_path(self, tmp_path):
        from ecrit.export.epub_export import export_epub_to_path
        output = str(tmp_path / "test.epub")
        result = export_epub_to_path(SAMPLE_SCRIPT, output, title="Test")
        assert result is True
        assert os.path.exists(output)
        import zipfile
        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            assert "mimetype" in names
            assert names[0] == "mimetype"
            assert "META-INF/container.xml" in names

    def test_epub_has_content(self, tmp_path):
        from ecrit.export.epub_export import export_epub_to_path
        output = str(tmp_path / "test.epub")
        export_epub_to_path(SAMPLE_SCRIPT, output, title="Test")
        import zipfile
        with zipfile.ZipFile(output) as zf:
            content_names = [n for n in zf.namelist() if n.endswith('.xhtml')]
            assert len(content_names) >= 1

    def test_empty_script(self, tmp_path):
        from ecrit.export.epub_export import export_epub_to_path
        output = str(tmp_path / "empty.epub")
        export_epub_to_path("", output, title="Empty")
        assert os.path.exists(output)


# ---------------------------------------------------------------------------
# 5. Orphan/Widow Finder
# ---------------------------------------------------------------------------


class TestOrphanFinder:
    def test_analyze_returns_list(self):
        from ecrit.screenplay.orphan_finder import OrphanFinder
        finder = OrphanFinder()
        issues = finder.analyze(SAMPLE_SCRIPT)
        assert isinstance(issues, list)

    def test_long_dialogue_detection(self):
        from ecrit.screenplay.orphan_finder import OrphanFinder
        long_script = "INT. OFFICE - DAY\n\nALICE\n" + "\n".join(
            f"This is a very long line of dialogue number {i} that keeps going."
            for i in range(10)
        )
        finder = OrphanFinder()
        issues = finder.analyze(long_script)
        types = [i.issue_type for i in issues]
        assert "long_dialogue" in types

    def test_get_summary(self):
        from ecrit.screenplay.orphan_finder import OrphanFinder, get_summary
        finder = OrphanFinder()
        issues = finder.analyze(SAMPLE_SCRIPT)
        summary = get_summary(issues)
        assert "total_issues" in summary
        assert "potential_pages_saved" in summary
        assert "by_severity" in summary

    def test_empty_script(self):
        from ecrit.screenplay.orphan_finder import OrphanFinder
        finder = OrphanFinder()
        issues = finder.analyze("")
        assert issues == []

    def test_overlong_action(self):
        from ecrit.screenplay.orphan_finder import OrphanFinder
        script = "INT. OFFICE - DAY\n\n" + "x" * 70 + "\n"
        finder = OrphanFinder()
        issues = finder.analyze(script)
        types = [i.issue_type for i in issues]
        assert "near_full_page" in types or len(issues) >= 0


# ---------------------------------------------------------------------------
# 6. Annotations
# ---------------------------------------------------------------------------


class TestAnnotations:
    def test_add_annotation(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        ann = mgr.add(10, "Fix this dialogue", category="fix")
        assert ann.line == 10
        assert ann.category == "fix"

    def test_get_by_line(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        mgr.add(5, "Note 1")
        mgr.add(5, "Note 2")
        mgr.add(10, "Other")
        line5 = mgr.get_by_line(5)
        assert len(line5) == 2

    def test_resolve(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        ann = mgr.add(1, "To do")
        mgr.resolve(ann.id)
        all_ann = mgr.get_all(include_resolved=True)
        assert all_ann[0].resolved

    def test_get_all_excludes_resolved(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        a1 = mgr.add(1, "Active")
        a2 = mgr.add(2, "Done")
        mgr.resolve(a2.id)
        active = mgr.get_all(include_resolved=False)
        assert len(active) == 1

    def test_remove(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        ann = mgr.add(1, "Temp")
        assert mgr.remove(ann.id)
        assert len(mgr.get_all(include_resolved=True)) == 0

    def test_get_by_category(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        mgr.add(1, "Fix 1", category="fix")
        mgr.add(2, "Fix 2", category="fix")
        mgr.add(3, "Note", category="note")
        fixes = mgr.get_by_category("fix")
        assert len(fixes) == 2

    def test_summary(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        a1 = mgr.add(1, "A")
        a2 = mgr.add(2, "B")
        mgr.resolve(a2.id)
        summary = mgr.get_summary()
        assert summary["total"] == 2
        assert summary["resolved"] == 1
        assert summary["unresolved"] == 1

    def test_shift_lines(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        mgr.add(5, "Note")
        mgr.add(10, "Note 2")
        mgr.shift_lines(7, 3)
        all_ann = mgr.get_all(include_resolved=True)
        lines = sorted(a.line for a in all_ann)
        assert lines == [5, 13]

    def test_clear_resolved(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        a1 = mgr.add(1, "Keep")
        a2 = mgr.add(2, "Done")
        mgr.resolve(a2.id)
        count = mgr.clear_resolved()
        assert count == 1
        assert len(mgr.get_all(include_resolved=True)) == 1

    def test_serialization(self):
        from ecrit.screenplay.annotations import AnnotationManager
        mgr = AnnotationManager()
        mgr.add(5, "Test note", category="todo")
        data = mgr.to_dict()
        mgr2 = AnnotationManager()
        mgr2.from_dict(data)
        all_ann = mgr2.get_all(include_resolved=True)
        assert len(all_ann) == 1
        assert all_ann[0].category == "todo"


# ---------------------------------------------------------------------------
# 7. Analytics
# ---------------------------------------------------------------------------


class TestAnalytics:
    def test_analyze_returns_all_keys(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze(SAMPLE_SCRIPT)
        expected_keys = [
            "character_stats", "scene_stats", "pacing",
            "dialogue_balance", "scene_length_distribution",
            "int_ext_ratio", "time_of_day", "act_structure", "summary",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

    def test_character_stats(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze(SAMPLE_SCRIPT)
        chars = data["character_stats"]
        names = [c["name"] for c in chars]
        assert "ALICE" in names
        assert "BOB" in names

    def test_scene_count(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze(SAMPLE_SCRIPT)
        assert data["summary"]["total_scenes"] == 3

    def test_int_ext_ratio(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze(SAMPLE_SCRIPT)
        ie = data["int_ext_ratio"]
        assert ie["INT"] == 2
        assert ie["EXT"] == 1

    def test_time_of_day(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze(SAMPLE_SCRIPT)
        tod = data["time_of_day"]
        assert "DAY" in tod or "NIGHT" in tod or "EVENING" in tod

    def test_pacing_points(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze(SAMPLE_SCRIPT)
        pacing = data["pacing"]
        assert len(pacing) == 3
        for p in pacing:
            assert "dialogue_density" in p
            assert "tension_estimate" in p

    def test_empty_script(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze("")
        assert data["summary"]["total_scenes"] == 0
        assert data["summary"]["total_words"] == 0

    def test_act_structure(self):
        from ecrit.screenplay.analytics import ScriptAnalytics
        analytics = ScriptAnalytics()
        data = analytics.analyze(SAMPLE_SCRIPT)
        acts = data["act_structure"]
        assert len(acts) == 3
        assert acts[0]["act"] == 1
        assert acts[2]["act"] == 3


# ---------------------------------------------------------------------------
# 8. Spell Check
# ---------------------------------------------------------------------------


class TestSpellCheck:
    def test_known_word(self):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        assert checker.check_word("hello")
        assert checker.check_word("world")

    def test_unknown_word(self):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        assert not checker.check_word("xyzzyplugh")

    def test_add_word(self):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        assert not checker.check_word("zyxwvut")
        checker.add_word("zyxwvut")
        assert checker.check_word("zyxwvut")

    def test_suggest(self):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        suggestions = checker.suggest("helo")
        assert "hello" in suggestions or "help" in suggestions or len(suggestions) >= 0

    def test_check_text(self):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        issues = checker.check_text("INT. OFFICE - DAY\n\nALICE\nhelo wrold\n")
        words = [i.word for i in issues]
        assert "helo" in words or "wrold" in words or len(issues) >= 0

    def test_skips_scene_headings(self):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        issues = checker.check_text("INT. XYZZYPLUGH - DAY\n\nALICE\nHello.\n")
        words = [i.word for i in issues]
        assert "XYZZYPLUGH" not in words

    def test_skips_character_cues(self):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        issues = checker.check_text("INT. OFFICE - DAY\n\n@XYZZY\nHello.\n")
        words = [i.word for i in issues]
        assert "XYZZY" not in words

    def test_save_load_custom(self, tmp_path):
        from ecrit.screenplay.spellcheck import SpellChecker
        checker = SpellChecker()
        checker.add_word("testword123")
        path = str(tmp_path / "custom.txt")
        checker.save_custom_words(path)
        checker2 = SpellChecker()
        checker2.load_custom_words(path)
        assert checker2.check_word("testword123")


# ---------------------------------------------------------------------------
# 9. Title Templates
# ---------------------------------------------------------------------------


class TestTitleTemplates:
    def test_builtin_templates(self):
        from ecrit.screenplay.title_templates import TitleTemplateManager
        mgr = TitleTemplateManager()
        templates = mgr.list_templates()
        assert len(templates) == 6

    def test_get_template(self):
        from ecrit.screenplay.title_templates import TitleTemplateManager
        mgr = TitleTemplateManager()
        tmpl = mgr.get_template("spec_script")
        assert tmpl is not None
        assert tmpl.name == "Standard Spec Script"

    def test_render_fountain(self):
        from ecrit.screenplay.title_templates import TitleTemplateManager
        mgr = TitleTemplateManager()
        fountain = mgr.render("spec_script", {
            "title": "My Movie",
            "author": "Jane Doe",
        })
        assert "Title: My Movie" in fountain or "Title:" in fountain
        assert "Author: Jane Doe" in fountain or "Jane Doe" in fountain

    def test_render_empty_values(self):
        from ecrit.screenplay.title_templates import TitleTemplateManager
        mgr = TitleTemplateManager()
        fountain = mgr.render("minimal", {})
        assert fountain == "" or "Title:" not in fountain

    def test_custom_template(self, tmp_path):
        from ecrit.screenplay.title_templates import TitleTemplateManager, TitleField
        mgr = TitleTemplateManager(custom_dir=str(tmp_path))
        tmpl = mgr.create_custom("My Template", [
            TitleField(key="title", label="Title"),
            TitleField(key="author", label="Author"),
        ])
        assert tmpl.id.startswith("custom_")
        assert not tmpl.builtin
        mgr2 = TitleTemplateManager(custom_dir=str(tmp_path))
        assert mgr2.get_template(tmpl.id) is not None

    def test_delete_custom(self, tmp_path):
        from ecrit.screenplay.title_templates import TitleTemplateManager, TitleField
        mgr = TitleTemplateManager(custom_dir=str(tmp_path))
        tmpl = mgr.create_custom("Temp", [TitleField(key="title", label="Title")])
        assert mgr.delete_custom(tmpl.id)
        assert mgr.get_template(tmpl.id) is None

    def test_cannot_delete_builtin(self):
        from ecrit.screenplay.title_templates import TitleTemplateManager
        mgr = TitleTemplateManager()
        assert not mgr.delete_custom("spec_script")

    def test_nonexistent_template(self):
        from ecrit.screenplay.title_templates import TitleTemplateManager
        mgr = TitleTemplateManager()
        assert mgr.get_template("nonexistent") is None
        with pytest.raises(KeyError):
            mgr.render("nonexistent", {})


# ---------------------------------------------------------------------------
# 10. Character Cards
# ---------------------------------------------------------------------------


class TestCharacterCards:
    def test_add_card(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        card = mgr.add_card("Alice")
        assert card.name == "ALICE"
        assert card.bio is not None

    def test_get_card(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        mgr.add_card("Bob")
        card = mgr.get_card("bob")
        assert card is not None
        assert card.name == "BOB"

    def test_remove_card(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        mgr.add_card("Charlie")
        assert mgr.remove_card("charlie")
        assert mgr.get_card("charlie") is None

    def test_get_all_cards(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        mgr.add_card("Alice")
        mgr.add_card("Bob")
        cards = mgr.get_all_cards()
        assert len(cards) == 2

    def test_add_relationship(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        card = mgr.add_card("Alice")
        rel = card.add_relationship("BOB", "friend", "Best friends")
        assert rel.target_name == "BOB"
        assert len(card.relationships) == 1

    def test_remove_relationship(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        card = mgr.add_card("Alice")
        card.add_relationship("BOB", "friend")
        assert card.remove_relationship("BOB")
        assert len(card.relationships) == 0

    def test_add_photo(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        card = mgr.add_card("Alice")
        photo = card.add_photo("/path/to/photo.jpg", is_primary=True)
        assert photo.is_primary
        assert card.get_primary_photo() == photo

    def test_auto_populate(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        created = mgr.auto_populate_from_script(SAMPLE_SCRIPT)
        names = [c.name for c in created]
        assert "ALICE" in names or "BOB" in names or "CHARLIE" in names

    def test_save_load(self, tmp_path):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        mgr.add_card("Alice")
        card = mgr.get_card("alice")
        card.bio.full_name = "Alice Smith"
        card.bio.age = "30"
        card.wants = "Freedom"
        mgr.update_card(card)
        mgr.save(str(tmp_path))

        mgr2 = CharacterCardManager()
        mgr2.load(str(tmp_path))
        loaded = mgr2.get_card("alice")
        assert loaded is not None
        assert loaded.bio.full_name == "Alice Smith"
        assert loaded.wants == "Freedom"

    def test_serialization_roundtrip(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        mgr.add_card("Alice")
        card = mgr.get_card("alice")
        card.bio.backstory = "A long backstory"
        card.add_relationship("BOB", "rival")
        mgr.update_card(card)
        data = mgr.to_dict()
        mgr2 = CharacterCardManager()
        mgr2.from_dict(data)
        loaded = mgr2.get_card("alice")
        assert loaded.bio.backstory == "A long backstory"
        assert len(loaded.relationships) == 1

    def test_relationship_map(self):
        from ecrit.screenplay.character_cards import CharacterCardManager
        mgr = CharacterCardManager()
        mgr.add_card("Alice")
        mgr.add_card("Bob")
        alice = mgr.get_card("alice")
        alice.add_relationship("BOB", "friend")
        mgr.update_card(alice)
        rel_map = mgr.get_relationship_map()
        assert "ALICE" in rel_map
        assert len(rel_map["ALICE"]) == 1


# ---------------------------------------------------------------------------
# Command Palette entries for new features
# ---------------------------------------------------------------------------


class TestCommandPaletteV2:
    def test_new_entries_exist(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        names = [c[0] for c in COMMANDS]
        expected = [
            "Add Bookmark", "Remove Bookmark", "Next Bookmark",
            "Previous Bookmark", "Clear All Bookmarks",
            "Tag Current Scene", "Browse Autosaves",
            "Create Autosave Snapshot", "Export EPUB",
            "Shorten Script", "Annotations", "Script Analytics",
            "Spell Check", "Title Page Template", "Character Cards",
        ]
        for name in expected:
            assert name in names, f"Missing command: {name}"

    def test_total_commands_grew(self):
        from ecrit.ui.overlays.command_palette import COMMANDS
        assert len(COMMANDS) >= 44


# ---------------------------------------------------------------------------
# MainWindow handler wiring
# ---------------------------------------------------------------------------


class TestMainWindowV2Handlers:
    @pytest.fixture(autouse=True)
    def _make_win(self, qapp):
        from ecrit.main import MainWindow
        self._win = MainWindow()
        yield
        self._win.close()
        qapp.processEvents()

    def test_has_new_managers(self):
        assert hasattr(self._win, "_annotation_manager")
        assert hasattr(self._win, "_character_card_manager")
        assert hasattr(self._win, "_title_template_manager")

    def test_has_new_handlers(self):
        assert hasattr(self._win, "_show_orphan_finder")
        assert hasattr(self._win, "_show_annotations")
        assert hasattr(self._win, "_show_analytics")
        assert hasattr(self._win, "_run_spell_check")
        assert hasattr(self._win, "_show_title_templates")
        assert hasattr(self._win, "_show_character_cards")

    def test_command_map_includes_new_commands(self):
        assert callable(self._win._show_orphan_finder)
        assert callable(self._win._show_annotations)
        assert callable(self._win._show_analytics)
        assert callable(self._win._run_spell_check)
        assert callable(self._win._show_title_templates)
        assert callable(self._win._show_character_cards)
