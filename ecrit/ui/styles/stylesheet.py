"""Generate Qt stylesheet from theme tokens."""

from .theme import ThemeTokens


def generate(t: ThemeTokens) -> str:
    btn_primary_bg = t.accent if t.name == "organic" else "transparent"
    btn_primary_text = t.bg if t.name == "organic" else t.accent
    btn_primary_border = t.accent

    return f"""
/* ═══ Global ═══ */
QWidget {{
    background-color: {t.bg};
    color: {t.text};
    font-family: 'Liberation Serif', 'Tinos', 'Times New Roman', serif;
    font-size: 13px;
}}
QWidget:focus {{
    outline: none;
}}

/* ═══ Title Bar ═══ */
#titleBar {{
    background-color: {t.surface};
    border-bottom: 1px solid {t.divider};
    min-height: 44px;
    max-height: 44px;
}}
#titleBar QLabel {{
    background: transparent;
}}
#wordmark {{
    font-size: 16px;
    font-weight: 500;
    color: {t.text};
}}
#titleContext {{
    font-size: 13px;
    color: {t.neutral_500};
}}

/* ═══ Phase Tabs ═══ */
#phaseTabs QPushButton {{
    background: transparent;
    border: none;
    color: {t.neutral_500};
    font-size: 13px;
    padding: 8px 12px;
    font-weight: 500;
}}
#phaseTabs QPushButton:hover {{
    color: {t.neutral_200};
}}
#phaseTabs QPushButton[active="true"] {{
    color: {t.accent_200 if t.name == "nocturne" else t.accent};
    border-bottom: 2px solid {t.accent};
}}

/* ═══ Buttons ═══ */
QPushButton {{
    font-family: 'Liberation Serif', 'Tinos', 'Times New Roman', serif;
    font-weight: 500;
    font-size: 14px;
    border-radius: {t.radius_md}px;
    padding: 6px 14px;
    border: 1px solid transparent;
    background: transparent;
    color: {t.text};
    white-space: nowrap;
}}
QPushButton:disabled {{
    opacity: 0.45;
}}
QPushButton#primary {{
    background: {btn_primary_bg};
    color: {btn_primary_text};
    border-color: {btn_primary_border};
}}
QPushButton#primary:hover {{
    background: {t.accent_600 if t.name == "organic" else t.accent_900};
}}
QPushButton#secondary {{
    border-color: {t.divider};
}}
QPushButton#secondary:hover {{
    background: rgba(255,255,255,0.07);
}}
QPushButton#ghost {{
    color: {t.accent};
    padding-left: 4px;
    padding-right: 4px;
}}
QPushButton#ghost:hover {{
    background: rgba({_hex_to_rgb_str(t.accent)},0.10);
}}
QPushButton#iconBtn {{
    width: 22px;
    height: 22px;
    padding: 0;
    border: none;
    background: transparent;
}}
QPushButton#iconBtn:hover {{
    background: rgba(255,255,255,0.08);
    border-radius: {t.radius_sm}px;
}}

/* ═══ Line Edits / Inputs ═══ */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {t.surface};
    color: {t.text};
    border: 1px solid {t.divider};
    border-radius: {t.radius_md}px;
    padding: 6px 10px;
    font-size: 14px;
    selection-background-color: rgba({_hex_to_rgb_str(t.accent)},0.30);
}}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
    border-color: rgba({_hex_to_rgb_str(t.text)},0.45);
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t.accent};
}}

/* ═══ Scroll Bars ═══ */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.neutral_700};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.neutral_600};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {t.neutral_700};
    border-radius: 4px;
    min-width: 24px;
}}

/* ═══ Cards ═══ */
QFrame#card {{
    background: {t.surface};
    border: 1px solid {t.neutral_800 if t.name == "nocturne" else t.divider};
    border-radius: {t.radius_md}px;
    padding: 16px 18px;
}}
QFrame#card:hover {{
    border-color: {t.accent_700};
}}

/* ═══ Tags ═══ */
QLabel#tagNeutral {{
    background: {t.neutral_800 if t.name == "nocturne" else t.neutral_100};
    color: {t.neutral_100 if t.name == "nocturne" else t.neutral_800};
    font-size: 11px;
    padding: 3px 10px;
    border-radius: {int(t.radius_md * 0.75)}px;
}}
QLabel#tagAccent {{
    background: {t.accent_800 if t.name == "nocturne" else t.accent_100};
    color: {t.accent_100 if t.name == "nocturne" else t.accent_800};
    font-size: 11px;
    padding: 3px 10px;
    border-radius: {int(t.radius_md * 0.75)}px;
}}

/* ═══ Kicker Labels ═══ */
QLabel#kicker {{
    font-size: 12px;
    letter-spacing: 1px;
    color: {t.neutral_500};
    text-transform: uppercase;
    background: transparent;
}}

/* ═══ Status Bar ═══ */
#statusBar {{
    background: {t.surface};
    border-top: 1px solid {t.divider};
    min-height: 28px;
    max-height: 28px;
    font-size: 12px;
    color: {t.neutral_500};
}}
#statusBar QLabel {{
    background: transparent;
    color: {t.neutral_500};
    font-size: 12px;
}}

/* ═══ Rails (side panels) ═══ */
QFrame#rail {{
    background: {t.surface};
    border: none;
}}
#railDivider {{
    background: {t.divider};
    min-width: 1px;
    max-width: 1px;
}}

/* ═══ Scene Navigator ═══ */
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
    font-family: 'Courier Prime', Courier, monospace;
    font-size: 12px;
}}
QListWidget::item {{
    padding: 6px 12px;
    border: none;
    color: {t.neutral_400};
}}
QListWidget::item:selected {{
    background: {t.accent_900 if t.name == "nocturne" else t.accent_100};
    color: {t.text};
    border-radius: {t.radius_sm}px;
}}
QListWidget::item:hover:!selected {{
    background: rgba(255,255,255,0.04);
}}

/* ═══ Modal / Dialog ═══ */
QDialog {{
    background: {t.surface};
    border-radius: {t.radius_lg}px;
}}

/* ═══ Tab Bar (Settings) ═══ */
QTabWidget::pane {{
    border: none;
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {t.neutral_500};
    padding: 10px 16px;
    font-size: 13.5px;
    border: none;
    border-radius: {t.radius_sm}px;
}}
QTabBar::tab:selected {{
    background: {t.accent_900 if t.name == "nocturne" else t.accent_100};
    color: {t.accent_200 if t.name == "nocturne" else t.accent};
}}
QTabBar::tab:hover:!selected {{
    background: rgba(255,255,255,0.05);
}}

/* ═══ Combo Box ═══ */
QComboBox {{
    background: {t.surface};
    color: {t.text};
    border: 1px solid {t.divider};
    border-radius: {t.radius_md}px;
    padding: 6px 10px;
    font-size: 14px;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {t.surface};
    color: {t.text};
    border: 1px solid {t.neutral_700};
    selection-background-color: {t.accent_900 if t.name == "nocturne" else t.accent_100};
}}

/* ═══ Check Box ═══ */
QCheckBox {{
    spacing: 8px;
    font-size: 14px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {t.divider};
    border-radius: 3px;
    background: transparent;
}}
QCheckBox::indicator:checked {{
    background: {t.accent};
    border-color: {t.accent};
}}

/* ═══ Splitter ═══ */
QSplitter::handle {{
    background: transparent;
    width: 5px;
}}
QSplitter::handle:hover {{
    background: {t.accent_700};
}}

/* ═══ Tool Tips ═══ */
QToolTip {{
    background: {t.surface};
    color: {t.text};
    border: 1px solid {t.neutral_700};
    border-radius: {t.radius_sm}px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* ═══ Menu ═══ */
QMenu {{
    background: {t.surface};
    color: {t.text};
    border: 1px solid {t.neutral_700};
    border-radius: {t.radius_md}px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: {t.radius_sm}px;
}}
QMenu::item:selected {{
    background: {t.accent_900 if t.name == "nocturne" else t.accent_100};
}}
QMenu::separator {{
    height: 1px;
    background: {t.divider};
    margin: 4px 8px;
}}

/* ═══ Home Button ═══ */
#homeBtn {{
    background: {t.surface};
    border: 1px solid {t.neutral_800 if t.name == "nocturne" else t.divider};
    border-radius: {t.radius_sm}px;
    width: 34px;
    height: 34px;
    padding: 0;
}}
#homeBtn:hover {{
    border-color: {t.accent};
}}

/* ═══ Script Editor ═══ */
#scriptEditor {{
    background: {t.surface};
    color: {t.text};
    border: none;
    font-family: 'Courier Prime', Courier, monospace;
    font-size: 15px;
    line-height: 1.6;
    padding: 40px;
    selection-background-color: rgba({_hex_to_rgb_str(t.accent)},0.25);
}}

/* ═══ Plan Editor ═══ */
#planEditor {{
    background: transparent;
    color: {t.text};
    border: none;
    font-family: 'Liberation Serif', 'Tinos', 'Times New Roman', serif;
    font-size: 16px;
    padding: 20px;
    selection-background-color: rgba({_hex_to_rgb_str(t.accent)},0.25);
}}
"""


def _hex_to_rgb_str(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r},{g},{b}"
    return "255,255,255"
