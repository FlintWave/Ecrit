"""Heroicons (MIT, Tailwind Labs) — outline 24x24, rendered as QIcon for Écrit UI."""

from PySide6.QtCore import QByteArray, QEvent, QRectF, QSize
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QPushButton

_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"'
    ' stroke-width="1.5" stroke="{color}">{paths}</svg>'
)

_PATHS: dict[str, str] = {
    "x-mark": '<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12"/>',
    "cog-6-tooth": (
        '<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94'
        " 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147"
        ".083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296"
        " 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723"
        " 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298"
        " 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47"
        " 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11"
        " .94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52"
        " 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0"
        " 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613"
        ".43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125"
        ' 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133'
        '.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z"/>'
        '<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>'
    ),
    "home": (
        '<path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439'
        " 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875"
        "c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0"
        ' 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/>'
    ),
    "chevron-up": '<path stroke-linecap="round" stroke-linejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5"/>',
    "chevron-down": '<path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5"/>',
    "arrow-right": '<path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"/>',
    "arrow-down": '<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3"/>',
    "minus": '<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14"/>',
    "plus": '<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>',
    "arrow-down-tray": (
        '<path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0'
        " 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5"
        ' 4.5V3"/>'
    ),
    "magnifying-glass": (
        '<path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5'
        ' 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"/>'
    ),
    "command-line": (
        '<path stroke-linecap="round" stroke-linejoin="round" d="m6.75 7.5 3 2.25-3 2.25m4.5 0h3M2.25'
        " 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75"
        ' 9.75S2.25 17.385 2.25 12Z"/>'
    ),
    "document-arrow-down": (
        '<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375'
        " 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0"
        " 0-3.375-3.375H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125"
        ' 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"/>'
    ),
}


def icon(name: str, color: str = "#ffffff", size: int = 20) -> QIcon:
    svg = _TEMPLATE.format(color=color, paths=_PATHS[name])
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)


class IconButton(QPushButton):
    """QPushButton that renders a Heroicon and auto-refreshes on theme change."""

    def __init__(self, icon_name: str, icon_size: int = 18, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._icon_size = icon_size
        self._refresh()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.StyleChange:
            self._refresh()
        super().changeEvent(event)

    def _refresh(self):
        from ecrit.ui.styles import theme
        t = theme.current()
        color = t.neutral_300 if t.name == "nocturne" else t.neutral_600
        self.setIcon(icon(self._icon_name, color, self._icon_size))
        self.setIconSize(QSize(self._icon_size, self._icon_size))
