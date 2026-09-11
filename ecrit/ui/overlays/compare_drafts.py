"""Compare drafts — side-by-side or inline diff of two snapshots."""

import difflib
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


class CompareDrafts(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compare Drafts")
        self.setMinimumSize(820, 560)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Compare Drafts")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()

        self.view_mode = QPushButton("Side by side")
        self.view_mode.setObjectName("secondary")
        self.view_mode.setFixedHeight(28)
        self.view_mode.clicked.connect(self._toggle_view)
        header.addWidget(self.view_mode)

        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        selectors = QHBoxLayout()
        selectors.addWidget(QLabel("From:"))
        self.from_select = QComboBox()
        self.from_select.setFixedHeight(30)
        selectors.addWidget(self.from_select, 1)
        selectors.addWidget(QLabel("To:"))
        self.to_select = QComboBox()
        self.to_select.setFixedHeight(30)
        selectors.addWidget(self.to_select, 1)
        compare_btn = QPushButton("Compare")
        compare_btn.setObjectName("primary")
        compare_btn.setFixedHeight(30)
        compare_btn.clicked.connect(self._run_compare)
        selectors.addWidget(compare_btn)
        layout.addLayout(selectors)

        self._side_by_side = True

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.left_view = QTextEdit()
        self.left_view.setReadOnly(True)
        self.left_view.setStyleSheet(
            f"font-family: 'Courier Prime', Courier, monospace; font-size: 13px; "
            f"background: {t.surface}; border: 1px solid {t.divider}; border-radius: 6px;"
        )
        self.splitter.addWidget(self.left_view)

        self.right_view = QTextEdit()
        self.right_view.setReadOnly(True)
        self.right_view.setStyleSheet(
            f"font-family: 'Courier Prime', Courier, monospace; font-size: 13px; "
            f"background: {t.surface}; border: 1px solid {t.divider}; border-radius: 6px;"
        )
        self.splitter.addWidget(self.right_view)

        self.inline_view = QTextEdit()
        self.inline_view.setReadOnly(True)
        self.inline_view.setStyleSheet(
            f"font-family: 'Courier Prime', Courier, monospace; font-size: 13px; "
            f"background: {t.surface}; border: 1px solid {t.divider}; border-radius: 6px;"
        )
        self.inline_view.hide()

        layout.addWidget(self.splitter, 1)
        layout.addWidget(self.inline_view, 1)

        stats = QHBoxLayout()
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        stats.addWidget(self.stats_label)
        stats.addStretch()
        layout.addLayout(stats)

        self._from_text = ""
        self._to_text = ""
        self._snapshots = []

    def set_snapshots(self, snapshots: list):
        self._snapshots = snapshots
        self.from_select.clear()
        self.to_select.clear()
        for s in snapshots:
            label = s.get("label", s.get("hash", "")[:8])
            date = s.get("date", "")
            display = f"{label} ({date})" if date else label
            self.from_select.addItem(display, s)
            self.to_select.addItem(display, s)
        if len(snapshots) >= 2:
            self.from_select.setCurrentIndex(1)
            self.to_select.setCurrentIndex(0)

    def set_texts(self, from_text: str, to_text: str):
        self._from_text = from_text
        self._to_text = to_text
        self._show_diff()

    def _run_compare(self):
        from_data = self.from_select.currentData()
        to_data = self.to_select.currentData()
        if from_data and to_data and self._snapshots:
            from_hash = from_data.get("hash", "")
            to_hash = to_data.get("hash", "")
            if from_hash or to_hash:
                try:
                    from ecrit.stores.app_state import STATE
                    from ecrit.ui.overlays.snapshots import get_snapshot_content
                    if STATE.current_project_path:
                        if from_hash:
                            self._from_text = get_snapshot_content(STATE.current_project_path, from_hash)
                        if to_hash:
                            self._to_text = get_snapshot_content(STATE.current_project_path, to_hash)
                except Exception as exc:
                    import logging
                    logging.getLogger("ecrit.compare").warning(
                        "Failed to load snapshot: %s", exc,
                    )
        self._show_diff()

    def _show_diff(self):
        t = theme.current()
        from_lines = self._from_text.splitlines(keepends=True)
        to_lines = self._to_text.splitlines(keepends=True)

        differ = difflib.unified_diff(from_lines, to_lines, lineterm='')
        diff_lines = list(differ)

        additions = sum(1 for l in diff_lines if l.startswith('+') and not l.startswith('+++'))
        deletions = sum(1 for l in diff_lines if l.startswith('-') and not l.startswith('---'))
        self.stats_label.setText(f"+{additions} additions, -{deletions} deletions")

        add_color = t.accent2_800 if t.name == "nocturne" else t.accent2_200
        del_color = t.neutral_800 if t.name == "nocturne" else t.neutral_200

        if self._side_by_side:
            self.left_view.setPlainText(self._from_text)
            self.right_view.setPlainText(self._to_text)
        else:
            html_parts = []
            for line in diff_lines:
                escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if line.startswith('+') and not line.startswith('+++'):
                    html_parts.append(f'<div style="background:{add_color}">{escaped}</div>')
                elif line.startswith('-') and not line.startswith('---'):
                    html_parts.append(
                        f'<div style="background:{del_color};text-decoration:line-through">{escaped}</div>'
                    )
                elif line.startswith('@@'):
                    html_parts.append(f'<div style="color:{t.accent}">{escaped}</div>')
                else:
                    html_parts.append(f'<div>{escaped}</div>')
            self.inline_view.setHtml(''.join(html_parts))

    def _toggle_view(self):
        self._side_by_side = not self._side_by_side
        self.view_mode.setText("Inline" if self._side_by_side else "Side by side")
        self.splitter.setVisible(self._side_by_side)
        self.inline_view.setVisible(not self._side_by_side)
        self._show_diff()
