"""
Nocturne (dark) and Organic (light) design system tokens.
Every color in the app comes from here — theming is a single token swap.
"""

from dataclasses import dataclass, field


@dataclass
class ThemeTokens:
    name: str

    bg: str
    surface: str
    text: str
    accent: str
    accent_2: str
    divider: str

    neutral_100: str
    neutral_200: str
    neutral_300: str
    neutral_400: str
    neutral_500: str
    neutral_600: str
    neutral_700: str
    neutral_800: str
    neutral_900: str

    accent_100: str
    accent_200: str
    accent_300: str
    accent_400: str
    accent_500: str
    accent_600: str
    accent_700: str
    accent_800: str
    accent_900: str

    accent2_100: str
    accent2_200: str
    accent2_300: str
    accent2_400: str
    accent2_500: str
    accent2_600: str
    accent2_700: str
    accent2_800: str
    accent2_900: str

    radius_sm: int = 6
    radius_md: int = 8
    radius_lg: int = 12

    shadow_sm: str = ""
    shadow_md: str = ""
    shadow_lg: str = ""

    scrim: str = "rgba(0,0,0,0.55)"

    # Fonts
    font_ui: str = "'Liberation Serif', 'Tinos', 'Times New Roman', serif"
    font_script: str = "'Courier Prime', Courier, monospace"
    font_mono: str = "ui-monospace, Menlo, monospace"
    font_heading_weight: int = 500


NOCTURNE = ThemeTokens(
    name="nocturne",
    bg="#161826",
    surface="#232532",
    text="#e9e9ed",
    accent="#9184d9",
    accent_2="#a7a1db",
    divider="rgba(233,233,237,0.16)",
    neutral_100="#f3f5fe",
    neutral_200="#e4e7f5",
    neutral_300="#cfd3e5",
    neutral_400="#b2b6ca",
    neutral_500="#9397ab",
    neutral_600="#75798c",
    neutral_700="#595d6c",
    neutral_800="#3f424d",
    neutral_900="#292b31",
    accent_100="#f5f4ff",
    accent_200="#e7e5fe",
    accent_300="#d2cefd",
    accent_400="#b5abfc",
    accent_500="#968ae0",
    accent_600="#796cbf",
    accent_700="#5d5294",
    accent_800="#423a6a",
    accent_900="#2b2741",
    accent2_100="#f5f4ff",
    accent2_200="#e7e5fe",
    accent2_300="#d2cefd",
    accent2_400="#b5afe8",
    accent2_500="#9690c9",
    accent2_600="#7972a9",
    accent2_700="#5c5783",
    accent2_800="#423e5d",
    accent2_900="#2b293a",
    radius_sm=6,
    radius_md=8,
    radius_lg=12,
    scrim="rgba(0,0,0,0.55)",
)

ORGANIC = ThemeTokens(
    name="organic",
    bg="#f5ead8",
    surface="#ebddc5",
    text="#201e1d",
    accent="#c67139",
    accent_2="#7a8a5e",
    divider="rgba(32,30,29,0.16)",
    neutral_100="#f9f4ed",
    neutral_200="#eee7db",
    neutral_300="#dcd3c4",
    neutral_400="#c0b6a5",
    neutral_500="#a19786",
    neutral_600="#82796a",
    neutral_700="#645c50",
    neutral_800="#474238",
    neutral_900="#2e2b25",
    accent_100="#fff2eb",
    accent_200="#ffe1d0",
    accent_300="#ffc6a5",
    accent_400="#f6a06b",
    accent_500="#d67f48",
    accent_600="#b2622d",
    accent_700="#8c491a",
    accent_800="#643312",
    accent_900="#402310",
    accent2_100="#f0fae1",
    accent2_200="#e1eecc",
    accent2_300="#ccdbb2",
    accent2_400="#aebf92",
    accent2_500="#8fa073",
    accent2_600="#728157",
    accent2_700="#56633f",
    accent2_800="#3d472b",
    accent2_900="#272e1b",
    radius_sm=12,
    radius_md=16,
    radius_lg=20,
    scrim="rgba(0,0,0,0.25)",
)


_current_theme: ThemeTokens = NOCTURNE


def current() -> ThemeTokens:
    return _current_theme


def set_theme(theme: ThemeTokens):
    global _current_theme
    _current_theme = theme


def toggle():
    global _current_theme
    _current_theme = ORGANIC if _current_theme is NOCTURNE else NOCTURNE
    return _current_theme


def is_dark() -> bool:
    return _current_theme is NOCTURNE
