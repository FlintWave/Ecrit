"""Tests for the stylesheet generator."""

import pytest
from ecrit.ui.styles.theme import NOCTURNE, ORGANIC, ThemeTokens
from ecrit.ui.styles.stylesheet import generate


class TestStylesheetGeneration:
    def test_generates_nonempty_string(self):
        result = generate(NOCTURNE)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_generates_for_both_themes(self):
        dark = generate(NOCTURNE)
        light = generate(ORGANIC)
        assert dark != light

    def test_contains_widget_selectors(self):
        ss = generate(NOCTURNE)
        for selector in [
            "QWidget", "QPushButton", "QLineEdit", "QLabel",
            "#statusBar", "#scriptEditor", "#rail",
        ]:
            assert selector in ss, f"Missing selector: {selector}"

    def test_uses_theme_colors(self):
        ss = generate(NOCTURNE)
        assert NOCTURNE.bg in ss
        assert NOCTURNE.surface in ss
        assert NOCTURNE.text in ss

    def test_uses_organic_colors_for_organic(self):
        ss = generate(ORGANIC)
        assert ORGANIC.bg in ss
        assert ORGANIC.surface in ss

    def test_uses_radius_tokens(self):
        ss = generate(NOCTURNE)
        assert f"{NOCTURNE.radius_sm}px" in ss or f"{NOCTURNE.radius_md}px" in ss

    def test_no_hardcoded_colors_from_wrong_theme(self):
        """Stylesheet for nocturne shouldn't contain organic-specific bg."""
        ss = generate(NOCTURNE)
        assert ORGANIC.bg not in ss

    def test_returns_valid_qt_stylesheet(self):
        """Basic structural check: balanced braces."""
        ss = generate(NOCTURNE)
        assert ss.count("{") == ss.count("}")
