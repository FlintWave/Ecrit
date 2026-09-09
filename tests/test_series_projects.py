"""Tests for series project management — episodes, seasons, bible."""

import os
import json
import pytest

from ecrit.screenplay.series_projects import (
    Episode, SeriesSeason, BibleEntry, SeriesBible,
    SeriesProject, save_series_project, load_series_project,
)


class TestEpisode:
    def test_create_default(self):
        ep = Episode(number=1, title="Pilot")
        assert ep.number == 1
        assert ep.title == "Pilot"
        assert ep.status == "outline"
        assert ep.page_count == 0

    def test_roundtrip_dict(self):
        ep = Episode(number=3, title="The One", script_file="s01e03.fountain",
                     synopsis="Things happen", status="draft", page_count=42)
        data = ep.to_dict()
        restored = Episode.from_dict(data)
        assert restored.number == 3
        assert restored.title == "The One"
        assert restored.page_count == 42

    def test_from_dict_defaults(self):
        ep = Episode.from_dict({})
        assert ep.number == 0
        assert ep.title == ""


class TestSeriesSeason:
    def test_create(self):
        season = SeriesSeason(number=1, title="Season 1")
        assert season.number == 1
        assert season.episodes == []

    def test_roundtrip(self):
        season = SeriesSeason(number=2, title="Revenge", episodes=[
            Episode(number=1, title="Ep 1"),
            Episode(number=2, title="Ep 2"),
        ])
        data = season.to_dict()
        restored = SeriesSeason.from_dict(data)
        assert len(restored.episodes) == 2
        assert restored.episodes[1].title == "Ep 2"


class TestSeriesBible:
    def test_empty(self):
        bible = SeriesBible()
        assert bible.entries == []

    def test_add_entry(self):
        bible = SeriesBible()
        entry = BibleEntry(category="character", name="ALICE", description="Protagonist")
        bible.add_entry(entry)
        assert len(bible.entries) == 1

    def test_remove_entry(self):
        bible = SeriesBible(entries=[
            BibleEntry(category="character", name="ALICE"),
            BibleEntry(category="character", name="BOB"),
        ])
        assert bible.remove_entry("ALICE") is True
        assert len(bible.entries) == 1
        assert bible.entries[0].name == "BOB"

    def test_remove_nonexistent(self):
        bible = SeriesBible()
        assert bible.remove_entry("NOBODY") is False

    def test_get_by_category(self):
        bible = SeriesBible(entries=[
            BibleEntry(category="character", name="ALICE"),
            BibleEntry(category="location", name="OFFICE"),
            BibleEntry(category="character", name="BOB"),
        ])
        chars = bible.get_by_category("character")
        assert len(chars) == 2
        locs = bible.get_by_category("location")
        assert len(locs) == 1

    def test_get_by_name(self):
        bible = SeriesBible(entries=[
            BibleEntry(category="character", name="ALICE"),
        ])
        assert bible.get_by_name("ALICE") is not None
        assert bible.get_by_name("BOB") is None

    def test_search(self):
        bible = SeriesBible(entries=[
            BibleEntry(category="character", name="ALICE", description="Detective", tags=["lead"]),
            BibleEntry(category="location", name="OFFICE", description="Corporate HQ"),
        ])
        assert len(bible.search("alice")) == 1
        assert len(bible.search("detective")) == 1
        assert len(bible.search("lead")) == 1
        assert len(bible.search("xyz")) == 0

    def test_roundtrip(self):
        bible = SeriesBible(entries=[
            BibleEntry(category="character", name="ALICE", tags=["lead", "detective"]),
        ])
        data = bible.to_dict()
        restored = SeriesBible.from_dict(data)
        assert len(restored.entries) == 1
        assert restored.entries[0].tags == ["lead", "detective"]

    def test_unicode_entries(self):
        bible = SeriesBible()
        bible.add_entry(BibleEntry(
            category="character", name="HÉLOÏSE",
            description="Boulangère française",
        ))
        results = bible.search("héloïse")
        assert len(results) == 1


class TestSeriesProject:
    def test_create(self):
        project = SeriesProject(title="Breaking Bad")
        assert project.title == "Breaking Bad"
        assert project.seasons == []
        assert project.total_episodes() == 0

    def test_add_season(self):
        project = SeriesProject(title="Test")
        s = project.add_season("Season One")
        assert s.number == 1
        assert s.title == "Season One"
        assert len(project.seasons) == 1

    def test_add_season_auto_number(self):
        project = SeriesProject(title="Test")
        project.add_season()
        project.add_season()
        assert project.seasons[0].number == 1
        assert project.seasons[1].number == 2

    def test_get_season(self):
        project = SeriesProject(title="Test")
        project.add_season("S1")
        assert project.get_season(1) is not None
        assert project.get_season(99) is None

    def test_add_episode(self):
        project = SeriesProject(title="Test")
        project.add_season()
        ep = project.add_episode(1, "Pilot", "The beginning")
        assert ep is not None
        assert ep.number == 1
        assert ep.title == "Pilot"
        assert ep.script_file == "s01e01.fountain"

    def test_add_episode_bad_season(self):
        project = SeriesProject(title="Test")
        assert project.add_episode(99, "Ghost") is None

    def test_get_episode(self):
        project = SeriesProject(title="Test")
        project.add_season()
        project.add_episode(1, "Pilot")
        project.add_episode(1, "Second")
        assert project.get_episode(1, 2).title == "Second"
        assert project.get_episode(1, 99) is None
        assert project.get_episode(99, 1) is None

    def test_total_episodes(self):
        project = SeriesProject(title="Test")
        project.add_season()
        project.add_season()
        project.add_episode(1, "S1E1")
        project.add_episode(1, "S1E2")
        project.add_episode(2, "S2E1")
        assert project.total_episodes() == 3

    def test_total_pages(self):
        project = SeriesProject(title="Test")
        project.add_season()
        ep1 = project.add_episode(1, "Ep1")
        ep1.page_count = 55
        ep2 = project.add_episode(1, "Ep2")
        ep2.page_count = 48
        assert project.total_pages() == 103

    def test_bible_integration(self):
        project = SeriesProject(title="Test")
        project.bible.add_entry(BibleEntry(
            category="character", name="WALT",
            description="Chemistry teacher",
        ))
        assert len(project.get_all_characters()) == 1
        assert len(project.get_all_locations()) == 0

    def test_full_roundtrip(self):
        project = SeriesProject(
            title="Test Show",
            showrunner="Jane Doe",
            network="HBO",
            genre="Drama",
            logline="A test show.",
        )
        project.add_season("Season 1")
        project.add_episode(1, "Pilot", "It begins")
        project.bible.add_entry(BibleEntry(
            category="character", name="LEAD",
            description="The main character",
            tags=["protagonist"],
            episodes=[1],
        ))
        data = project.to_dict()
        restored = SeriesProject.from_dict(data)
        assert restored.title == "Test Show"
        assert restored.showrunner == "Jane Doe"
        assert len(restored.seasons) == 1
        assert len(restored.seasons[0].episodes) == 1
        assert restored.seasons[0].episodes[0].title == "Pilot"
        assert len(restored.bible.entries) == 1


class TestSeriesProjectIO:
    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "series.json")
        project = SeriesProject(title="IO Test")
        project.add_season()
        project.add_episode(1, "Pilot")
        save_series_project(project, path)
        assert os.path.exists(path)

        loaded = load_series_project(path)
        assert loaded is not None
        assert loaded.title == "IO Test"
        assert loaded.total_episodes() == 1

    def test_load_nonexistent(self, tmp_path):
        assert load_series_project(str(tmp_path / "nope.json")) is None

    def test_save_creates_dirs(self, tmp_path):
        path = str(tmp_path / "deep" / "nested" / "series.json")
        project = SeriesProject(title="Nested")
        save_series_project(project, path)
        assert os.path.exists(path)

    def test_unicode_roundtrip(self, tmp_path):
        path = str(tmp_path / "unicode.json")
        project = SeriesProject(title="Café Müller")
        project.bible.add_entry(BibleEntry(
            category="character", name="HÉLOÏSE",
            description="Artiste — 你好",
        ))
        save_series_project(project, path)
        loaded = load_series_project(path)
        assert loaded.title == "Café Müller"
        assert loaded.bible.entries[0].name == "HÉLOÏSE"
