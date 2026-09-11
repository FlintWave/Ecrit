"""Presence indicators — show collaborator cursors and avatars in the editor."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ecrit.ui.styles import theme


class PresenceBadge(QFrame):
    def __init__(self, user_name: str, color: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet(
            f"background: {color}; border-radius: 11px; padding: 0 8px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)

        initials = "".join(w[0].upper() for w in user_name.split()[:2]) or "?"
        label = QLabel(initials)
        label.setStyleSheet("color: white; font-size: 11px; font-weight: 600;")
        layout.addWidget(label)

        name_label = QLabel(user_name)
        name_label.setStyleSheet("color: white; font-size: 11px;")
        layout.addWidget(name_label)


class PresenceBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 2, 8, 2)
        self._layout.setSpacing(6)
        self._layout.addStretch()
        self._badges: dict[str, PresenceBadge] = {}

    def set_participants(self, participants: list[dict]) -> None:
        for badge in self._badges.values():
            badge.setParent(None)
            badge.deleteLater()
        self._badges.clear()

        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for p in participants:
            uid = p.get("user_id", "")
            name = p.get("user_name", "?")
            color = p.get("color", "#4FC3F7")
            badge = PresenceBadge(name, color, self)
            self._badges[uid] = badge
            self._layout.insertWidget(self._layout.count() - 1, badge)

    def update_cursor(self, user_id: str, position: int) -> None:
        badge = self._badges.get(user_id)
        if badge:
            badge.setToolTip(f"Cursor at position {position}")

    def clear_participants(self) -> None:
        for badge in self._badges.values():
            badge.setParent(None)
            badge.deleteLater()
        self._badges.clear()
