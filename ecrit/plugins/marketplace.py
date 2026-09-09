"""Marketplace — browse, install, and manage plugin listings."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class PluginCategory(str, Enum):
    DIALECT = "dialect"
    EXPORT = "export"
    TOOL = "tool"
    REPORT = "report"
    THEME = "theme"
    INTEGRATION = "integration"


@dataclass
class PluginListing:
    id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    category: PluginCategory = PluginCategory.TOOL
    download_url: str = ""
    homepage: str = ""
    icon: str = ""
    tags: list[str] = field(default_factory=list)
    installed: bool = False
    installed_version: str = ""
    update_available: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "category": self.category.value,
            "download_url": self.download_url,
            "homepage": self.homepage,
            "icon": self.icon,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PluginListing:
        cat = data.get("category", "tool")
        try:
            category = PluginCategory(cat)
        except ValueError:
            category = PluginCategory.TOOL
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            category=category,
            download_url=data.get("download_url", ""),
            homepage=data.get("homepage", ""),
            icon=data.get("icon", ""),
            tags=data.get("tags", []),
        )


class Marketplace:
    def __init__(self, plugins_dir: str = ""):
        if not plugins_dir:
            plugins_dir = str(Path.home() / ".ecrit" / "plugins")
        self.plugins_dir = plugins_dir
        self._registry_cache: list[PluginListing] = []
        self._installed: dict[str, PluginListing] = {}
        self._load_installed()

    def _load_installed(self) -> None:
        self._installed.clear()
        if not os.path.isdir(self.plugins_dir):
            return
        for entry in os.listdir(self.plugins_dir):
            manifest_path = os.path.join(self.plugins_dir, entry, "manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    listing = PluginListing.from_dict(data)
                    listing.id = listing.id or entry
                    listing.installed = True
                    listing.installed_version = listing.version
                    self._installed[listing.id] = listing
                except (json.JSONDecodeError, OSError):
                    pass

    def get_installed(self) -> list[PluginListing]:
        return list(self._installed.values())

    def is_installed(self, plugin_id: str) -> bool:
        return plugin_id in self._installed

    def get_registry(self) -> list[PluginListing]:
        listings = list(self._registry_cache)
        for listing in listings:
            if listing.id in self._installed:
                listing.installed = True
                listing.installed_version = self._installed[listing.id].installed_version
                if listing.version != listing.installed_version:
                    listing.update_available = True
        return listings

    def set_registry(self, listings: list[PluginListing]) -> None:
        self._registry_cache = listings

    def load_registry_from_file(self, path: str) -> list[PluginListing]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            listings = [PluginListing.from_dict(item) for item in data]
            self._registry_cache = listings
            return listings
        except (json.JSONDecodeError, OSError):
            return []

    def install_from_directory(self, source_dir: str) -> Optional[PluginListing]:
        manifest_path = os.path.join(source_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            return None
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        listing = PluginListing.from_dict(data)
        if not listing.id:
            listing.id = os.path.basename(source_dir)

        dest = os.path.join(self.plugins_dir, listing.id)
        os.makedirs(dest, exist_ok=True)

        for item in os.listdir(source_dir):
            src = os.path.join(source_dir, item)
            dst = os.path.join(dest, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        listing.installed = True
        listing.installed_version = listing.version
        self._installed[listing.id] = listing
        return listing

    def uninstall(self, plugin_id: str) -> bool:
        if plugin_id not in self._installed:
            return False
        plugin_dir = os.path.join(self.plugins_dir, plugin_id)
        if os.path.isdir(plugin_dir):
            shutil.rmtree(plugin_dir)
        del self._installed[plugin_id]
        return True

    def search(self, query: str, category: Optional[PluginCategory] = None) -> list[PluginListing]:
        results = self.get_registry() + self.get_installed()
        seen = set()
        unique = []
        for listing in results:
            if listing.id not in seen:
                seen.add(listing.id)
                unique.append(listing)

        query_lower = query.lower().strip()
        if query_lower:
            unique = [
                p for p in unique
                if query_lower in p.name.lower()
                or query_lower in p.description.lower()
                or any(query_lower in tag.lower() for tag in p.tags)
            ]
        if category:
            unique = [p for p in unique if p.category == category]
        return unique

    def get_categories(self) -> list[PluginCategory]:
        return list(PluginCategory)
