"""Translation engine — loads JSON language packs and provides tr() lookup."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

_TRANSLATIONS_DIR = Path(__file__).parent / "translations"
_current_language = "en"
_catalogs: dict[str, dict[str, str]] = {}
_fallback = "en"


def _load_catalog(lang: str) -> dict[str, str]:
    path = _TRANSLATIONS_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _ensure_loaded(lang: str) -> dict[str, str]:
    if lang not in _catalogs:
        _catalogs[lang] = _load_catalog(lang)
    return _catalogs[lang]


def tr(key: str, **kwargs) -> str:
    catalog = _ensure_loaded(_current_language)
    text = catalog.get(key)
    if text is None:
        fallback_catalog = _ensure_loaded(_fallback)
        text = fallback_catalog.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def set_language(lang: str) -> None:
    global _current_language
    _current_language = lang
    _ensure_loaded(lang)


def get_language() -> str:
    return _current_language


def available_languages() -> list[tuple[str, str]]:
    langs = []
    if _TRANSLATIONS_DIR.is_dir():
        for f in sorted(_TRANSLATIONS_DIR.iterdir()):
            if f.suffix == ".json" and f.stem != "":
                catalog = _ensure_loaded(f.stem)
                display = catalog.get("_language_name", f.stem)
                langs.append((f.stem, display))
    if not langs:
        langs.append(("en", "English"))
    return langs


def reload_catalogs() -> None:
    _catalogs.clear()
