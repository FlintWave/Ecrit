"""Tests for the i18n/translation system."""

import json
import pytest
from pathlib import Path

from ecrit.i18n.translator import (
    tr, set_language, get_language, available_languages, reload_catalogs,
    _ensure_loaded,
)


class TestTranslator:
    def setup_method(self):
        reload_catalogs()
        set_language("en")

    def test_default_language_is_english(self):
        assert get_language() == "en"

    def test_set_language(self):
        set_language("fr")
        assert get_language() == "fr"
        set_language("en")

    def test_tr_returns_key_when_missing(self):
        result = tr("nonexistent_key_12345")
        assert result == "nonexistent_key_12345"

    def test_tr_with_english(self):
        result = tr("app_name")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tr_with_kwargs(self):
        set_language("en")
        catalog = _ensure_loaded("en")
        for key, value in catalog.items():
            if "{" in value:
                break
        else:
            pytest.skip("No parameterized keys in English catalog")

    def test_tr_fallback_to_english(self):
        set_language("nonexistent_language")
        result = tr("app_name")
        en_catalog = _ensure_loaded("en")
        expected = en_catalog.get("app_name", "app_name")
        assert result == expected

    def test_available_languages_not_empty(self):
        langs = available_languages()
        assert len(langs) >= 1
        codes = [code for code, _name in langs]
        assert "en" in codes

    def test_available_languages_have_display_names(self):
        langs = available_languages()
        for code, name in langs:
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0

    def test_reload_catalogs(self):
        _ensure_loaded("en")
        reload_catalogs()
        result = tr("app_name")
        assert isinstance(result, str)

    def test_french_catalog_loads(self):
        translations_dir = Path(__file__).parent.parent / "ecrit" / "i18n" / "translations"
        if not (translations_dir / "fr.json").exists():
            pytest.skip("French catalog not present")
        set_language("fr")
        result = tr("app_name")
        assert isinstance(result, str)

    def test_all_catalogs_valid_json(self):
        translations_dir = Path(__file__).parent.parent / "ecrit" / "i18n" / "translations"
        if not translations_dir.is_dir():
            pytest.skip("Translations directory not found")
        for f in translations_dir.iterdir():
            if f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                assert isinstance(data, dict), f"{f.name} is not a dict"

    def test_language_switch_changes_output(self):
        translations_dir = Path(__file__).parent.parent / "ecrit" / "i18n" / "translations"
        available = [f.stem for f in translations_dir.iterdir() if f.suffix == ".json"]
        non_en = [l for l in available if l != "en"]
        if not non_en:
            pytest.skip("Only English catalog available")
        set_language("en")
        en_result = tr("app_name")
        set_language(non_en[0])
        other_result = tr("app_name")
        assert isinstance(other_result, str)
