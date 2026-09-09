"""Tests for the theme/design-system token layer."""

import pytest
from ecrit.ui.styles.theme import (
    ThemeTokens, NOCTURNE, ORGANIC, current, set_theme, toggle, is_dark,
)


class TestThemeTokensDataclass:
    def test_nocturne_has_all_required_fields(self):
        assert NOCTURNE.name == "nocturne"
        assert NOCTURNE.bg.startswith("#")
        assert NOCTURNE.surface.startswith("#")
        assert NOCTURNE.text.startswith("#")
        assert NOCTURNE.accent.startswith("#")

    def test_organic_has_all_required_fields(self):
        assert ORGANIC.name == "organic"
        assert ORGANIC.bg.startswith("#")
        assert ORGANIC.surface.startswith("#")
        assert ORGANIC.text.startswith("#")
        assert ORGANIC.accent.startswith("#")

    def test_both_themes_have_matching_fields(self):
        nocturne_fields = set(f.name for f in NOCTURNE.__dataclass_fields__.values())
        organic_fields = set(f.name for f in ORGANIC.__dataclass_fields__.values())
        assert nocturne_fields == organic_fields

    def test_neutral_ramp_complete(self):
        for t in (NOCTURNE, ORGANIC):
            for step in (100, 200, 300, 400, 500, 600, 700, 800, 900):
                attr = f"neutral_{step}"
                val = getattr(t, attr)
                assert val, f"{t.name} missing {attr}"
                assert val.startswith("#"), f"{t.name}.{attr} = {val!r} not a hex color"

    def test_accent_ramp_complete(self):
        for t in (NOCTURNE, ORGANIC):
            for step in (100, 200, 300, 400, 500, 600, 700, 800, 900):
                for prefix in ("accent_", "accent2_"):
                    attr = f"{prefix}{step}"
                    val = getattr(t, attr)
                    assert val.startswith("#"), f"{t.name}.{attr} = {val!r}"

    def test_radii_are_positive_integers(self):
        for t in (NOCTURNE, ORGANIC):
            assert isinstance(t.radius_sm, int) and t.radius_sm > 0
            assert isinstance(t.radius_md, int) and t.radius_md > 0
            assert isinstance(t.radius_lg, int) and t.radius_lg > 0
            assert t.radius_sm <= t.radius_md <= t.radius_lg

    def test_organic_has_larger_radii(self):
        assert ORGANIC.radius_sm >= NOCTURNE.radius_sm
        assert ORGANIC.radius_lg >= NOCTURNE.radius_lg

    def test_font_families_present(self):
        for t in (NOCTURNE, ORGANIC):
            assert "Courier Prime" in t.font_script
            assert "serif" in t.font_ui.lower() or "Serif" in t.font_ui
            assert t.font_heading_weight == 500

    def test_scrim_is_rgba(self):
        for t in (NOCTURNE, ORGANIC):
            assert t.scrim.startswith("rgba(")

    def test_bg_and_text_contrast(self):
        """Themes should have visually distinct bg and text colors."""
        assert NOCTURNE.bg != NOCTURNE.text
        assert ORGANIC.bg != ORGANIC.text

    def test_nocturne_dark_organic_light(self):
        """Nocturne bg is dark (low luminance), Organic bg is light."""
        def hex_luminance(h: str) -> float:
            h = h.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return 0.299 * r + 0.587 * g + 0.114 * b
        assert hex_luminance(NOCTURNE.bg) < 80
        assert hex_luminance(ORGANIC.bg) > 160


class TestThemeState:
    def test_default_is_nocturne(self):
        set_theme(NOCTURNE)
        assert current() is NOCTURNE
        assert is_dark() is True

    def test_set_to_organic(self):
        set_theme(ORGANIC)
        assert current() is ORGANIC
        assert is_dark() is False

    def test_toggle_from_nocturne(self):
        set_theme(NOCTURNE)
        result = toggle()
        assert result is ORGANIC
        assert current() is ORGANIC

    def test_toggle_from_organic(self):
        set_theme(ORGANIC)
        result = toggle()
        assert result is NOCTURNE
        assert current() is NOCTURNE

    def test_double_toggle_roundtrip(self):
        set_theme(NOCTURNE)
        toggle()
        toggle()
        assert current() is NOCTURNE

    def test_triple_toggle(self):
        set_theme(NOCTURNE)
        toggle()
        toggle()
        toggle()
        assert current() is ORGANIC

    def test_set_theme_with_custom_tokens(self):
        custom = ThemeTokens(
            name="custom",
            bg="#000000", surface="#111111", text="#ffffff",
            accent="#ff0000", accent_2="#00ff00", divider="#333333",
            neutral_100="#f0f0f0", neutral_200="#e0e0e0", neutral_300="#d0d0d0",
            neutral_400="#c0c0c0", neutral_500="#b0b0b0", neutral_600="#a0a0a0",
            neutral_700="#909090", neutral_800="#808080", neutral_900="#707070",
            accent_100="#ff0000", accent_200="#ee0000", accent_300="#dd0000",
            accent_400="#cc0000", accent_500="#bb0000", accent_600="#aa0000",
            accent_700="#990000", accent_800="#880000", accent_900="#770000",
            accent2_100="#00ff00", accent2_200="#00ee00", accent2_300="#00dd00",
            accent2_400="#00cc00", accent2_500="#00bb00", accent2_600="#00aa00",
            accent2_700="#009900", accent2_800="#008800", accent2_900="#007700",
        )
        set_theme(custom)
        assert current().name == "custom"
        assert current().bg == "#000000"
