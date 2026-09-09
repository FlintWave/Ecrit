"""Series project management — multi-episode support with shared bible."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Episode:
    number: int
    title: str
    script_file: str = ""
    synopsis: str = ""
    status: str = "outline"  # outline | draft | revision | locked
    page_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Episode:
        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            script_file=data.get("script_file", ""),
            synopsis=data.get("synopsis", ""),
            status=data.get("status", "outline"),
            page_count=data.get("page_count", 0),
        )


@dataclass
class SeriesSeason:
    number: int
    title: str = ""
    episodes: list[Episode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "title": self.title,
            "episodes": [ep.to_dict() for ep in self.episodes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> SeriesSeason:
        return cls(
            number=data.get("number", 1),
            title=data.get("title", ""),
            episodes=[Episode.from_dict(ep) for ep in data.get("episodes", [])],
        )


@dataclass
class BibleEntry:
    category: str  # "character" | "location" | "prop" | "theme" | "backstory"
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    episodes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> BibleEntry:
        return cls(
            category=data.get("category", "character"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            episodes=data.get("episodes", []),
        )


@dataclass
class SeriesBible:
    entries: list[BibleEntry] = field(default_factory=list)

    def add_entry(self, entry: BibleEntry) -> None:
        self.entries.append(entry)

    def remove_entry(self, name: str) -> bool:
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.name != name]
        return len(self.entries) < before

    def get_by_category(self, category: str) -> list[BibleEntry]:
        return [e for e in self.entries if e.category == category]

    def get_by_name(self, name: str) -> Optional[BibleEntry]:
        for e in self.entries:
            if e.name == name:
                return e
        return None

    def search(self, query: str) -> list[BibleEntry]:
        q = query.lower()
        return [
            e for e in self.entries
            if q in e.name.lower() or q in e.description.lower()
            or any(q in tag.lower() for tag in e.tags)
        ]

    def get_characters(self) -> list[BibleEntry]:
        return self.get_by_category("character")

    def get_locations(self) -> list[BibleEntry]:
        return self.get_by_category("location")

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    @classmethod
    def from_dict(cls, data: dict) -> SeriesBible:
        return cls(
            entries=[BibleEntry.from_dict(e) for e in data.get("entries", [])],
        )


@dataclass
class SeriesProject:
    title: str
    showrunner: str = ""
    network: str = ""
    genre: str = ""
    logline: str = ""
    seasons: list[SeriesSeason] = field(default_factory=list)
    bible: SeriesBible = field(default_factory=SeriesBible)

    def add_season(self, title: str = "") -> SeriesSeason:
        num = len(self.seasons) + 1
        season = SeriesSeason(number=num, title=title or f"Season {num}")
        self.seasons.append(season)
        return season

    def get_season(self, number: int) -> Optional[SeriesSeason]:
        for s in self.seasons:
            if s.number == number:
                return s
        return None

    def add_episode(self, season_number: int, title: str, synopsis: str = "") -> Optional[Episode]:
        season = self.get_season(season_number)
        if season is None:
            return None
        num = max((ep.number for ep in season.episodes), default=0) + 1
        ep = Episode(
            number=num,
            title=title,
            script_file=f"s{season_number:02d}e{num:02d}.fountain",
            synopsis=synopsis,
        )
        season.episodes.append(ep)
        return ep

    def get_episode(self, season_number: int, episode_number: int) -> Optional[Episode]:
        season = self.get_season(season_number)
        if season is None:
            return None
        for ep in season.episodes:
            if ep.number == episode_number:
                return ep
        return None

    def total_episodes(self) -> int:
        return sum(len(s.episodes) for s in self.seasons)

    def total_pages(self) -> int:
        return sum(
            ep.page_count
            for s in self.seasons
            for ep in s.episodes
        )

    def get_all_characters(self) -> list[BibleEntry]:
        return self.bible.get_characters()

    def get_all_locations(self) -> list[BibleEntry]:
        return self.bible.get_locations()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "showrunner": self.showrunner,
            "network": self.network,
            "genre": self.genre,
            "logline": self.logline,
            "seasons": [s.to_dict() for s in self.seasons],
            "bible": self.bible.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> SeriesProject:
        return cls(
            title=data.get("title", ""),
            showrunner=data.get("showrunner", ""),
            network=data.get("network", ""),
            genre=data.get("genre", ""),
            logline=data.get("logline", ""),
            seasons=[SeriesSeason.from_dict(s) for s in data.get("seasons", [])],
            bible=SeriesBible.from_dict(data.get("bible", {})),
        )


def save_series_project(project: SeriesProject, path: str) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)


def load_series_project(path: str) -> Optional[SeriesProject]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SeriesProject.from_dict(data)
