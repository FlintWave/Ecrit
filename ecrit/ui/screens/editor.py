"""Editor screen — five phases: Plan, Outline, Manuscript, Proofread, Deliver."""

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QListWidget, QListWidgetItem,
    QPlainTextEdit, QSizePolicy, QTextEdit, QScrollArea,
    QComboBox, QMenu,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import (
    QFont, QTextCharFormat, QColor, QSyntaxHighlighter,
    QTextDocument, QTextCursor, QPainter, QPen, QKeySequence, QShortcut
)

from ecrit.ui.styles import theme
from ecrit.ui.components.status_bar import StatusBar
from ecrit.ui.overlays.find_replace import FindReplaceBar
from ecrit.ui.overlays.reading_mode import ReadingMode
from ecrit.ui.overlays.scratchpad import Scratchpad

from ecrit.screenplay.structure_templates import (
    TEMPLATES, generate_outline_nodes, list_templates,
)
from ecrit.screenplay.scene_numbers import (
    SceneNumber, assign_scene_numbers, lock_scene, unlock_scene,
    renumber_scenes, format_scene_heading,
)
from ecrit.screenplay.revisions import (
    RevisionTracker, REVISION_COLORS, get_revision_color_hex,
)
from ecrit.screenplay.contest_presets import CONTEST_PRESETS, validate_against_preset


class FountainHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._update_formats()

    def _update_formats(self):
        t = theme.current()

        self.scene_fmt = QTextCharFormat()
        self.scene_fmt.setFontWeight(QFont.Weight.Bold)
        self.scene_fmt.setFontCapitalization(QFont.Capitalization.AllUppercase)

        self.char_fmt = QTextCharFormat()
        self.char_fmt.setFontCapitalization(QFont.Capitalization.AllUppercase)

        self.paren_fmt = QTextCharFormat()
        self.paren_fmt.setForeground(QColor(t.neutral_500))

        self.transition_fmt = QTextCharFormat()
        self.transition_fmt.setFontCapitalization(QFont.Capitalization.AllUppercase)
        self.transition_fmt.setForeground(QColor(t.neutral_400))

        self.note_fmt = QTextCharFormat()
        self.note_fmt.setForeground(QColor(t.accent_700))
        self.note_fmt.setBackground(QColor(t.accent_900))

        self.section_fmt = QTextCharFormat()
        self.section_fmt.setFontWeight(QFont.Weight.Bold)
        self.section_fmt.setForeground(QColor(t.accent_300))

    def highlightBlock(self, text: str):
        stripped = text.strip()
        if not stripped:
            return

        if stripped.startswith(("INT.", "EXT.", "EST.", "INT./EXT.", "I/E.")) or stripped.startswith("."):
            self.setFormat(0, len(text), self.scene_fmt)
        elif stripped.startswith("#"):
            self.setFormat(0, len(text), self.section_fmt)
        elif stripped.startswith("(") and stripped.endswith(")"):
            self.setFormat(0, len(text), self.paren_fmt)
        elif stripped.endswith("TO:") and stripped == stripped.upper():
            self.setFormat(0, len(text), self.transition_fmt)
        elif stripped.startswith("[[") and stripped.endswith("]]"):
            self.setFormat(0, len(text), self.note_fmt)
        elif stripped == stripped.upper() and stripped[0].isalpha() and len(stripped) > 1:
            prev_block = self.currentBlock().previous()
            if prev_block.isValid() and prev_block.text().strip() == "":
                self.setFormat(0, len(text), self.char_fmt)


class LineNumberArea(QWidget):
    """Gutter widget that draws line numbers beside the script editor."""

    def __init__(self, editor: "ScriptEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint(event)


class ScriptEditor(QPlainTextEdit):
    """Courier Prime script editor with typewriter scrolling."""

    content_changed = Signal()
    text_modified = Signal()
    text_cut = Signal(str)
    cursor_info_changed = Signal(int, str)  # (page_number, scene_heading)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("scriptEditor")

        font = QFont("Courier Prime", 15)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setTabStopDistance(40)

        self.highlighter = FountainHighlighter(self.document())

        self._typewriter = True
        self._show_line_numbers = False
        self._line_number_area = LineNumberArea(self)

        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(1000)
        self._save_timer.timeout.connect(self.content_changed.emit)

        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._on_cursor_moved)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)

        self._update_line_number_area_width()

    def set_line_numbers_visible(self, visible: bool):
        self._show_line_numbers = visible
        self._update_line_number_area_width()
        self._line_number_area.setVisible(visible)

    def line_number_area_width(self) -> int:
        if not self._show_line_numbers:
            return 0
        digits = max(1, len(str(self.blockCount())))
        return 8 + self.fontMetrics().horizontalAdvance("9") * (digits + 1)

    def _update_line_number_area_width(self, _new_count: int = 0):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(cr.left(), cr.top(), self.line_number_area_width(), cr.height())

    def line_number_area_paint(self, event):
        if not self._show_line_numbers:
            return
        p = QPainter(self._line_number_area)
        t = theme.current()
        p.fillRect(event.rect(), QColor(t.surface))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                p.setPen(QColor(t.neutral_500))
                p.drawText(
                    0, top, self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
        p.end()

    def _on_text_changed(self):
        self.text_modified.emit()
        if self._save_timer.interval() > 0:
            self._save_timer.start()

    def _on_cursor_moved(self):
        if self._typewriter:
            cursor = self.cursorRect()
            viewport_center = self.viewport().height() // 2
            scroll_bar = self.verticalScrollBar()
            current = scroll_bar.value()
            target = current + cursor.top() - viewport_center
            scroll_bar.setValue(target)

        block_num = self.textCursor().blockNumber()
        page = max(1, (block_num // 55) + 1)
        scene_heading = ""
        block = self.document().findBlockByNumber(block_num)
        while block.isValid():
            text = block.text().strip()
            if text.startswith(("INT.", "EXT.", "INT/EXT", "EST.", "INT./EXT.", "I/E.")):
                scene_heading = text
                break
            block = block.previous()
        self.cursor_info_changed.emit(page, scene_heading)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self._cycle_element_type()
            return
        if event.matches(QKeySequence.StandardKey.Cut) and self.textCursor().hasSelection():
            cut_text = self.textCursor().selectedText().replace(' ', '\n')
            self.text_cut.emit(cut_text)
        super().keyPressEvent(event)

    def _cycle_element_type(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        line = cursor.selectedText().strip()
        if not line:
            return

        prefixes = ["INT. ", "EXT. ", ""]
        transitions = ["CUT TO:", "FADE OUT.", "SMASH CUT TO:", ""]

        if line.startswith(("INT.", "EXT.", "INT/EXT")):
            for i, pfx in enumerate(prefixes):
                if line.startswith(pfx.strip()) and pfx:
                    next_pfx = prefixes[(i + 1) % len(prefixes)]
                    bare = line.split(".", 1)[1].strip() if "." in line else line
                    cursor.removeSelectedText()
                    cursor.insertText(f"{next_pfx}{bare}" if next_pfx else bare)
                    return
        elif line.startswith("(") and line.endswith(")"):
            cursor.removeSelectedText()
            cursor.insertText(line[1:-1] if len(line) > 2 else line)
        elif line.endswith(("TO:", "OUT.")):
            for i, tr in enumerate(transitions):
                if line == tr:
                    next_tr = transitions[(i + 1) % len(transitions)]
                    cursor.removeSelectedText()
                    cursor.insertText(next_tr if next_tr else line)
                    return
        else:
            cursor.removeSelectedText()
            cursor.insertText(f"({line})")


class SceneNavigator(QFrame):
    """Left rail: scene list with scene number management."""

    scene_selected = Signal(int)
    scenes_renumbered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rail")
        self._scene_numbers: list[SceneNumber] = []
        self._scenes_data: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(0)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(12, 0, 8, 4)
        header = QLabel("SCENES")
        header.setObjectName("kicker")
        header_row.addWidget(header)
        header_row.addStretch()

        self.renumber_btn = QPushButton("Renumber")
        self.renumber_btn.setObjectName("ghost")
        self.renumber_btn.setFixedHeight(24)
        self.renumber_btn.clicked.connect(self._renumber_all)
        header_row.addWidget(self.renumber_btn)
        layout.addLayout(header_row)

        self.scene_list = QListWidget()
        self.scene_list.currentRowChanged.connect(self.scene_selected.emit)
        self.scene_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.scene_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.scene_list)

    def set_script(self, script: str):
        self._scene_numbers = assign_scene_numbers(script)

    def update_scenes(self, scenes: list):
        self._scenes_data = scenes
        self.scene_list.clear()
        for i, sc in enumerate(scenes):
            heading = sc.get("heading", "")
            page = sc.get("page", 0)
            num_str = ""
            lock_mark = ""
            if i < len(self._scene_numbers):
                sn = self._scene_numbers[i]
                num_str = f"#{sn.number}  "
                lock_mark = " \U0001f512" if sn.locked else ""
            item = QListWidgetItem(f"{num_str}{heading}  p.{page}{lock_mark}")
            self.scene_list.addItem(item)

    def _show_context_menu(self, pos):
        row = self.scene_list.currentRow()
        if row < 0 or row >= len(self._scene_numbers):
            return
        sn = self._scene_numbers[row]
        menu = QMenu(self)
        if sn.locked:
            action = menu.addAction("Unlock Scene Number")
            action.triggered.connect(lambda: self._toggle_lock(row, lock=False))
        else:
            action = menu.addAction("Lock Scene Number")
            action.triggered.connect(lambda: self._toggle_lock(row, lock=True))
        menu.addSeparator()
        renumber_action = menu.addAction("Renumber All Unlocked")
        renumber_action.triggered.connect(self._renumber_all)
        menu.exec(self.scene_list.mapToGlobal(pos))

    def _toggle_lock(self, index: int, lock: bool):
        if lock:
            self._scene_numbers = lock_scene(self._scene_numbers, index)
        else:
            self._scene_numbers = unlock_scene(self._scene_numbers, index)
        self.update_scenes(self._scenes_data)

    def _renumber_all(self):
        if self._scene_numbers:
            self._scene_numbers = renumber_scenes(self._scene_numbers)
            self.update_scenes(self._scenes_data)
            self.scenes_renumbered.emit()

    def get_scene_numbers(self) -> list[SceneNumber]:
        return list(self._scene_numbers)


class CharacterRail(QFrame):
    """Right rail: character list."""

    character_activated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rail")
        self._characters = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        top = QHBoxLayout()
        header = QLabel("CHARACTERS")
        header.setObjectName("kicker")
        top.addWidget(header)
        top.addStretch()
        layout.addLayout(top)

        self.char_list = QListWidget()
        self.char_list.itemDoubleClicked.connect(self._on_activate)
        layout.addWidget(self.char_list)

    def update_characters(self, characters: list):
        self._characters = characters
        self.char_list.clear()
        for ch in characters:
            name = ch.get("name", "")
            lines = ch.get("line_count", 0)
            item = QListWidgetItem(f"{name}  ({lines} lines)")
            self.char_list.addItem(item)

    def _on_activate(self, item):
        row = self.char_list.row(item)
        if 0 <= row < len(self._characters):
            self.character_activated.emit(self._characters[row])


class PlanPhase(QWidget):
    """Plan phase: document list + prose editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.doc_rail = QFrame()
        self.doc_rail.setObjectName("rail")
        self.doc_rail.setFixedWidth(216)
        rail_layout = QVBoxLayout(self.doc_rail)
        rail_layout.setContentsMargins(0, 8, 0, 0)

        header = QLabel("DOCUMENTS")
        header.setObjectName("kicker")
        header.setStyleSheet("padding: 8px 12px;")
        rail_layout.addWidget(header)

        self.doc_list = QListWidget()
        self._doc_content = {}
        docs = ["Logline", "Synopsis", "One-page pitch", "Treatment"]
        for d in docs:
            self.doc_list.addItem(d)
            self._doc_content[d] = ""
        self.doc_list.currentRowChanged.connect(self._on_doc_selected)
        rail_layout.addWidget(self.doc_list)

        add_btn = QPushButton("+ New document")
        add_btn.setObjectName("ghost")
        add_btn.clicked.connect(self._add_document)
        rail_layout.addWidget(add_btn)

        layout.addWidget(self.doc_rail)

        divider = QFrame()
        divider.setObjectName("railDivider")
        divider.setFixedWidth(1)
        layout.addWidget(divider)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(40, 20, 40, 20)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        editor_container = QWidget()
        editor_container.setMaximumWidth(620)
        ec_layout = QVBoxLayout(editor_container)

        self.doc_header = QLabel("LOGLINE")
        self.doc_header.setObjectName("kicker")
        ec_layout.addWidget(self.doc_header)
        self._current_doc = "Logline"

        self.editor = QTextEdit()
        self.editor.setObjectName("planEditor")
        font = QFont("Liberation Serif", 16)
        self.editor.setFont(font)
        self.editor.setPlaceholderText("Start writing...")
        ec_layout.addWidget(self.editor)

        center_layout.addWidget(editor_container)
        layout.addWidget(center, 1)

        self.doc_list.setCurrentRow(0)

    def _on_doc_selected(self, row):
        if row < 0:
            return
        if self._current_doc in self._doc_content:
            self._doc_content[self._current_doc] = self.editor.toPlainText()
        item = self.doc_list.item(row)
        if item:
            name = item.text()
            self._current_doc = name
            self.doc_header.setText(name.upper())
            self.editor.setPlainText(self._doc_content.get(name, ""))

    def _add_document(self):
        count = self.doc_list.count()
        name = f"Document {count + 1}"
        self.doc_list.addItem(name)
        self._doc_content[name] = ""
        self.doc_list.setCurrentRow(self.doc_list.count() - 1)


class OutlinePhase(QWidget):
    """Outline phase: node graph with structure template support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(20, 12, 20, 0)

        title = QLabel("Outline")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        toolbar.addWidget(title)

        layout_h = QPushButton("→")
        layout_h.setObjectName("secondary")
        layout_h.setFixedSize(28, 28)
        layout_h.setToolTip("Horizontal layout")
        layout_h.clicked.connect(lambda: self._relayout("horizontal"))
        toolbar.addWidget(layout_h)

        layout_v = QPushButton("↓")
        layout_v.setObjectName("secondary")
        layout_v.setFixedSize(28, 28)
        layout_v.setToolTip("Vertical layout")
        layout_v.clicked.connect(lambda: self._relayout("vertical"))
        toolbar.addWidget(layout_v)

        toolbar.addStretch()

        self.template_combo = QComboBox()
        self.template_combo.addItem("— Structure Template —", "")
        for key, display_name in list_templates():
            self.template_combo.addItem(display_name, key)
        self.template_combo.setFixedHeight(30)
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        toolbar.addWidget(self.template_combo)

        add_btn = QPushButton("+ Add node")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._add_node)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.canvas = OutlineCanvas()
        layout.addWidget(self.canvas, 1)

        zoom_bar = QHBoxLayout()
        zoom_bar.setContentsMargins(20, 0, 20, 12)
        zoom_bar.addStretch()
        self.zoom_out = QPushButton("−")
        self.zoom_out.setObjectName("secondary")
        self.zoom_out.setFixedSize(28, 28)
        self.zoom_out.clicked.connect(lambda: self._zoom(-0.1))
        zoom_bar.addWidget(self.zoom_out)
        self.zoom_label = QLabel("100%")
        zoom_bar.addWidget(self.zoom_label)
        self.zoom_in = QPushButton("+")
        self.zoom_in.setObjectName("secondary")
        self.zoom_in.setFixedSize(28, 28)
        self.zoom_in.clicked.connect(lambda: self._zoom(0.1))
        zoom_bar.addWidget(self.zoom_in)
        fit_btn = QPushButton("Fit")
        fit_btn.setObjectName("secondary")
        fit_btn.clicked.connect(self._fit_view)
        zoom_bar.addWidget(fit_btn)
        zoom_bar.addStretch()
        info = QLabel("Right-click to add nodes")
        info.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 12px;")
        zoom_bar.addWidget(info)
        layout.addLayout(zoom_bar)

    def _on_template_selected(self, index: int):
        key = self.template_combo.itemData(index)
        if not key:
            return
        tpl = TEMPLATES.get(key)
        if tpl:
            nodes = generate_outline_nodes(tpl)
            self.canvas.set_nodes(nodes)
        self.template_combo.setCurrentIndex(0)

    def apply_template(self, key: str):
        """Programmatically apply a structure template by key."""
        tpl = TEMPLATES.get(key)
        if tpl:
            nodes = generate_outline_nodes(tpl)
            self.canvas.set_nodes(nodes)

    def _add_node(self):
        nodes = list(self.canvas._nodes)
        new_id = f"node_{len(nodes)+1}"
        x = 40 + (len(nodes) % 4) * 210
        y = 40 + (len(nodes) // 4) * 120
        nodes.append({"id": new_id, "kind": "Scene", "label": f"Scene {len(nodes)+1}", "synopsis": "", "x": x, "y": y, "connections": []})
        self.canvas.set_nodes(nodes)

    def _zoom(self, delta: float):
        self.canvas._zoom = max(0.5, min(1.6, self.canvas._zoom + delta))
        self.zoom_label.setText(f"{int(self.canvas._zoom * 100)}%")
        self.canvas.update()

    def _fit_view(self):
        self.canvas._zoom = 1.0
        self.canvas._pan_x = 0.0
        self.canvas._pan_y = 0.0
        self.zoom_label.setText("100%")
        self.canvas.update()

    def _relayout(self, direction: str):
        nodes = self.canvas._nodes
        for i, node in enumerate(nodes):
            if direction == "horizontal":
                node["x"] = 40 + i * 210
                node["y"] = 60
            else:
                node["x"] = 120
                node["y"] = 40 + i * 120
        self.canvas.update()


class OutlineCanvas(QWidget):
    """Pannable, zoomable node graph canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self._nodes = []
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._dragging = False
        self._last_pos = None
        self._dot_spacing = 22

    def set_nodes(self, nodes: list):
        self._nodes = nodes
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = theme.current()
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, QColor(t.bg))

        p.setPen(QPen(QColor(t.neutral_800), 1))
        spacing = int(self._dot_spacing * self._zoom)
        if spacing > 4:
            ox = int(self._pan_x) % spacing
            oy = int(self._pan_y) % spacing
            for x in range(ox, w, spacing):
                for y in range(oy, h, spacing):
                    p.drawPoint(x, y)

        p.save()
        p.translate(self._pan_x, self._pan_y)
        p.scale(self._zoom, self._zoom)

        for node in self._nodes:
            self._draw_node(p, node, t)

        for node in self._nodes:
            for conn_id in node.get("connections", []):
                target = next((n for n in self._nodes if n["id"] == conn_id), None)
                if target:
                    self._draw_connector(p, node, target, t)

        p.restore()
        p.end()

    def _draw_node(self, p: QPainter, node: dict, t):
        x, y = node.get("x", 0), node.get("y", 0)
        kind = node.get("kind", "Scene")

        if kind == "ActBreak":
            w, h = 220, 44
            p.setBrush(QColor(t.accent_900))
            p.setPen(QPen(QColor(t.accent_700), 1))
            p.drawRoundedRect(int(x), int(y), w, h, 6, 6)
            p.setPen(QPen(QColor(t.text), 1))
            p.drawText(int(x) + 12, int(y) + 28, node.get("label", ""))
        elif kind == "Scene":
            w, h = 190, 92
            p.setBrush(QColor(t.surface))
            p.setPen(QPen(QColor(t.neutral_800), 1))
            p.drawRoundedRect(int(x), int(y), w, h, 6, 6)
            p.setPen(QPen(QColor(t.text), 1))
            font = p.font()
            font.setPointSize(10)
            font.setBold(True)
            p.setFont(font)
            p.drawText(int(x) + 8, int(y) + 20, node.get("label", ""))
            font.setBold(False)
            font.setPointSize(9)
            p.setFont(font)
            p.setPen(QPen(QColor(t.neutral_400), 1))
            synopsis = node.get("synopsis", "")
            if synopsis:
                p.drawText(int(x) + 8, int(y) + 40, int(w) - 16, 40, Qt.TextFlag.TextWordWrap, synopsis[:80])
        elif kind == "Transition":
            w, h = 110, 36
            p.setBrush(QColor(t.surface))
            p.setPen(QPen(QColor(t.neutral_700), 1))
            p.drawRoundedRect(int(x), int(y), w, h, 18, 18)
            p.setPen(QPen(QColor(t.neutral_400), 1))
            p.drawText(int(x) + 12, int(y) + 23, node.get("label", ""))
        elif kind == "Note":
            w, h = 160, 60
            pen = QPen(QColor(t.neutral_600), 1, Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.setBrush(QColor(t.bg))
            p.drawRoundedRect(int(x), int(y), w, h, 6, 6)
            p.setPen(QPen(QColor(t.neutral_400), 1))
            font = p.font()
            font.setItalic(True)
            p.setFont(font)
            p.drawText(int(x) + 8, int(y) + 30, node.get("label", ""))
            font.setItalic(False)
            p.setFont(font)

    def _draw_connector(self, p: QPainter, src: dict, dst: dict, t):
        x1 = src.get("x", 0) + 190
        y1 = src.get("y", 0) + 46
        x2 = dst.get("x", 0)
        y2 = dst.get("y", 0) + 46
        p.setPen(QPen(QColor(t.neutral_600), 1.5))
        p.drawLine(int(x1), int(y1), int(x2), int(y2))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        new_zoom = max(0.5, min(1.6, self._zoom * factor))
        self._zoom = new_zoom
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._last_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.position(), event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseMoveEvent(self, event):
        if self._dragging and self._last_pos:
            delta = event.position() - self._last_pos
            self._pan_x += delta.x()
            self._pan_y += delta.y()
            self._last_pos = event.position()
            self.update()

    def _show_context_menu(self, local_pos, global_pos):
        canvas_x = (local_pos.x() - self._pan_x) / self._zoom
        canvas_y = (local_pos.y() - self._pan_y) / self._zoom

        menu = QMenu(self)
        add_scene = menu.addAction("Add Scene")
        add_act = menu.addAction("Add Act Break")
        add_note = menu.addAction("Add Note")
        add_transition = menu.addAction("Add Transition")

        action = menu.exec(global_pos)
        if action == add_scene:
            self._add_node_at(canvas_x, canvas_y, "Scene", f"Scene {len(self._nodes) + 1}")
        elif action == add_act:
            self._add_node_at(canvas_x, canvas_y, "ActBreak", f"Act {len(self._nodes) + 1}")
        elif action == add_note:
            self._add_node_at(canvas_x, canvas_y, "Note", "Note")
        elif action == add_transition:
            self._add_node_at(canvas_x, canvas_y, "Transition", "Transition")

    def _add_node_at(self, x: float, y: float, kind: str, label: str):
        new_id = f"node_{len(self._nodes) + 1}"
        self._nodes.append({
            "id": new_id, "kind": kind, "label": label,
            "synopsis": "", "x": x, "y": y, "connections": [],
        })
        self.update()


class ManuscriptPhase(QWidget):
    """Manuscript phase: scene nav + script editor + character rail."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scene_nav = SceneNavigator()
        self.scene_nav.setFixedWidth(216)

        self.divider_l = QFrame()
        self.divider_l.setObjectName("railDivider")
        self.divider_l.setFixedWidth(1)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        from ecrit.ui.components.presence_indicators import PresenceBar
        self.presence_bar = PresenceBar()
        self.presence_bar.setVisible(False)
        center_layout.addWidget(self.presence_bar)

        self.page_frame = QFrame()
        self.page_frame.setStyleSheet(f"background: {theme.current().surface}; border-radius: 4px;")
        self.page_frame.setMaximumWidth(680)
        self.page_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        page_layout = QVBoxLayout(self.page_frame)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.editor = ScriptEditor()
        page_layout.addWidget(self.editor)

        center_layout.addWidget(self.page_frame)

        self.divider_r = QFrame()
        self.divider_r.setObjectName("railDivider")
        self.divider_r.setFixedWidth(1)

        self.char_rail = CharacterRail()
        self.char_rail.setFixedWidth(264)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.scene_nav)
        splitter.addWidget(self.divider_l)
        splitter.addWidget(center)
        splitter.addWidget(self.divider_r)
        splitter.addWidget(self.char_rail)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)
        splitter.setStretchFactor(3, 0)
        splitter.setStretchFactor(4, 0)
        splitter.setSizes([216, 1, 600, 1, 264])

        layout.addWidget(splitter)


class ProofreadPhase(QWidget):
    """Proofread phase: script view + issues rail with automated checks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.script_view = QPlainTextEdit()
        self.script_view.setObjectName("scriptEditor")
        self.script_view.setReadOnly(True)
        font = QFont("Courier Prime", 15)
        self.script_view.setFont(font)
        layout.addWidget(self.script_view, 1)

        divider = QFrame()
        divider.setObjectName("railDivider")
        divider.setFixedWidth(1)
        layout.addWidget(divider)

        rail = QFrame()
        rail.setObjectName("rail")
        rail.setFixedWidth(300)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(12, 12, 12, 12)

        header = QHBoxLayout()
        title = QLabel("PROOF PASS")
        title.setObjectName("kicker")
        header.addWidget(title)
        header.addStretch()
        self.count_label = QLabel("0 flags")
        self.count_label.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 12px;")
        header.addWidget(self.count_label)
        rail_layout.addLayout(header)

        self.run_btn = QPushButton("Run Proofread")
        self.run_btn.setObjectName("primary")
        self.run_btn.setFixedHeight(32)
        self.run_btn.clicked.connect(self.run_proofread)
        rail_layout.addWidget(self.run_btn)

        self.issues_list = QListWidget()
        self.issues_list.currentRowChanged.connect(self._on_issue_selected)
        rail_layout.addWidget(self.issues_list)

        layout.addWidget(rail)
        self._issues: list[dict] = []

    def run_proofread(self):
        text = self.script_view.toPlainText()
        self._issues = self._check_script(text)
        self.issues_list.clear()
        for issue in self._issues:
            self.issues_list.addItem(f"L{issue['line']}: {issue['message']}")
        self.count_label.setText(f"{len(self._issues)} flag{'s' if len(self._issues) != 1 else ''}")

    def _on_issue_selected(self, row):
        if row < 0 or row >= len(self._issues):
            return
        line_num = self._issues[row]["line"]
        block = self.script_view.document().findBlockByLineNumber(line_num - 1)
        if block.isValid():
            cursor = self.script_view.textCursor()
            cursor.setPosition(block.position())
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            self.script_view.setTextCursor(cursor)
            self.script_view.centerCursor()

    @staticmethod
    def _check_script(text: str) -> list[dict]:
        import re
        issues = []
        lines = text.split("\n")
        prev_blank = False
        for i, line in enumerate(lines, 1):
            if "  " in line.strip():
                issues.append({"line": i, "message": "Double space"})
            if line.rstrip() != line:
                issues.append({"line": i, "message": "Trailing whitespace"})
            stripped = line.strip()
            is_blank = not stripped
            if is_blank and prev_blank:
                issues.append({"line": i, "message": "Consecutive blank lines"})
            prev_blank = is_blank
            if stripped.startswith("(") and not stripped.endswith(")"):
                issues.append({"line": i, "message": "Unclosed parenthetical"})
            if stripped.endswith(")") and not stripped.startswith("(") and stripped.count("(") == 0:
                issues.append({"line": i, "message": "Orphan closing parenthesis"})
            if stripped.isupper() and len(stripped) > 1 and stripped[0].isalpha():
                if i < len(lines):
                    next_line = lines[i].strip() if i < len(lines) else ""
                    if not next_line:
                        is_heading = stripped.startswith(("INT.", "EXT.", "EST.", "INT/EXT", "I/E."))
                        is_transition = stripped.endswith("TO:")
                        if not is_heading and not is_transition:
                            issues.append({"line": i, "message": "Character cue with no dialogue"})
            if re.search(r'[.!?]{2,}', stripped) and not stripped.startswith(("INT.", "EXT.", "EST.", "INT/EXT", "I/E.")):
                if ".." in stripped and "..." not in stripped:
                    issues.append({"line": i, "message": "Incomplete ellipsis (use three dots)"})
        return issues


class DeliverPhase(QWidget):
    """Deliver phase: print preview + export rail with revision tracking and contest validation."""

    export_pdf_requested = Signal()
    export_odt_requested = Signal()
    export_fountain_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._script = ""
        self._revision_tracker = RevisionTracker()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(40, 20, 40, 20)

        top = QHBoxLayout()
        title = QLabel("Deliver")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        top.addWidget(title)
        top.addStretch()

        self._view_mode = "script"
        self.view_seg = QHBoxLayout()
        self._cover_btn = QPushButton("Cover page")
        self._cover_btn.setObjectName("secondary")
        self._cover_btn.clicked.connect(lambda: self._set_view("cover"))
        self.view_seg.addWidget(self._cover_btn)
        self._script_btn = QPushButton("Script pages")
        self._script_btn.setObjectName("primary")
        self._script_btn.clicked.connect(lambda: self._set_view("script"))
        self.view_seg.addWidget(self._script_btn)
        top.addLayout(self.view_seg)
        center_layout.addLayout(top)

        self.format_label = QLabel("Paginated against fountain/core · US Letter · Courier Prime 12pt")
        self.format_label.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 13px;")
        center_layout.addWidget(self.format_label)

        self.preview_area = QPlainTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setFont(QFont("Courier Prime", 12))
        self.preview_area.setStyleSheet(
            f"background: {theme.current().surface}; border-radius: 8px; "
            f"min-height: 400px; color: {theme.current().text}; padding: 24px;"
        )
        self.preview_area.setPlaceholderText("Script preview will appear when a project is loaded")
        center_layout.addWidget(self.preview_area, 1)
        center_layout.addStretch()
        layout.addWidget(center, 1)

        divider = QFrame()
        divider.setObjectName("railDivider")
        divider.setFixedWidth(1)
        layout.addWidget(divider)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(360)
        scroll.setObjectName("rail")

        rail = QWidget()
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(16, 16, 16, 16)
        rail_layout.setSpacing(12)

        export_title = QLabel("EXPORT")
        export_title.setObjectName("kicker")
        rail_layout.addWidget(export_title)

        self._export_opts = {"title_page": True, "scene_numbers": True, "revision_marks": True}
        self._toggle_btns = {}
        for key, label_text, seg_options in [
            ("title_page", "Title page", ["Include", "Omit"]),
            ("scene_numbers", "Scene numbers", ["On", "Off"]),
            ("revision_marks", "Revision marks", ["Show", "Clean"]),
        ]:
            row = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 13px;")
            row.addWidget(lbl)
            seg = QHBoxLayout()
            btns = []
            for i, opt in enumerate(seg_options):
                btn = QPushButton(opt)
                btn.setObjectName("primary" if i == 0 else "secondary")
                btn.setFixedHeight(30)
                opt_key = key
                opt_val = i == 0
                btn.clicked.connect(lambda checked=False, k=opt_key, v=opt_val, bs=None: self._toggle_export_opt(k, v))
                seg.addWidget(btn)
                btns.append(btn)
            self._toggle_btns[key] = btns
            row.addLayout(seg)
            rail_layout.addLayout(row)

        rev_section = QLabel("REVISIONS")
        rev_section.setObjectName("kicker")
        rail_layout.addWidget(rev_section)

        self.revision_color_label = QLabel("Current: White")
        self.revision_color_label.setStyleSheet("font-size: 13px;")
        rail_layout.addWidget(self.revision_color_label)

        self.revision_color_swatch = QLabel()
        self.revision_color_swatch.setFixedSize(120, 20)
        self._update_revision_swatch()
        rail_layout.addWidget(self.revision_color_swatch)

        rev_btn_row = QHBoxLayout()
        self.new_revision_btn = QPushButton("New Revision")
        self.new_revision_btn.setObjectName("secondary")
        self.new_revision_btn.setFixedHeight(30)
        self.new_revision_btn.clicked.connect(self._add_revision)
        rev_btn_row.addWidget(self.new_revision_btn)
        rail_layout.addLayout(rev_btn_row)

        self.revision_history_label = QLabel("No revisions yet")
        self.revision_history_label.setStyleSheet(
            f"color: {theme.current().neutral_500}; font-size: 12px;"
        )
        self.revision_history_label.setWordWrap(True)
        rail_layout.addWidget(self.revision_history_label)

        contest_section = QLabel("CONTEST VALIDATION")
        contest_section.setObjectName("kicker")
        rail_layout.addWidget(contest_section)

        self.contest_combo = QComboBox()
        self.contest_combo.addItem("-- Select contest --", "")
        for key, preset in CONTEST_PRESETS.items():
            self.contest_combo.addItem(preset.name, key)
        self.contest_combo.setFixedHeight(30)
        self.contest_combo.currentIndexChanged.connect(self._on_contest_selected)
        rail_layout.addWidget(self.contest_combo)

        self.contest_result_label = QLabel()
        self.contest_result_label.setWordWrap(True)
        self.contest_result_label.setStyleSheet(
            f"color: {theme.current().neutral_500}; font-size: 12px;"
        )
        rail_layout.addWidget(self.contest_result_label)

        rail_layout.addStretch()

        export_btn = QPushButton("Export PDF")
        export_btn.setObjectName("primary")
        export_btn.setFixedHeight(40)
        export_btn.clicked.connect(self.export_pdf_requested.emit)
        rail_layout.addWidget(export_btn)

        odt_btn = QPushButton("Export ODT")
        odt_btn.setObjectName("secondary")
        odt_btn.setFixedHeight(36)
        odt_btn.clicked.connect(self.export_odt_requested.emit)
        rail_layout.addWidget(odt_btn)

        fountain_btn = QPushButton("Fountain (.fountain)")
        fountain_btn.setObjectName("secondary")
        fountain_btn.setFixedHeight(36)
        fountain_btn.clicked.connect(self.export_fountain_requested.emit)
        rail_layout.addWidget(fountain_btn)

        scroll.setWidget(rail)
        layout.addWidget(scroll)

    def set_script(self, script: str):
        self._script = script
        self._update_preview()

    def _update_revision_swatch(self):
        color_name = self._revision_tracker.current_revision().color
        hex_color = get_revision_color_hex(color_name)
        self.revision_color_swatch.setStyleSheet(
            f"background: {hex_color}; border-radius: 4px; border: 1px solid {theme.current().neutral_700};"
        )
        self.revision_color_label.setText(f"Current: {color_name}")

    def _add_revision(self):
        try:
            self._revision_tracker.add_revision(pages_changed=[])
            self._update_revision_swatch()
            history = self._revision_tracker.get_revision_header()
            self.revision_history_label.setText(history)
        except IndexError:
            self.revision_history_label.setText("All revision colors exhausted.")

    def _on_contest_selected(self, index: int):
        key = self.contest_combo.itemData(index)
        if not key:
            self.contest_result_label.setText("")
            return
        script = getattr(self, "_script", "")
        try:
            warnings = validate_against_preset(script, key)
        except KeyError:
            self.contest_result_label.setText("Unknown contest preset.")
            return
        if not warnings:
            self.contest_result_label.setText("✅ All checks passed!")
        else:
            lines = [f"⚠️ {w}" for w in warnings]
            self.contest_result_label.setText("\n".join(lines))

    def _set_view(self, mode: str):
        self._view_mode = mode
        if mode == "cover":
            self._cover_btn.setObjectName("primary")
            self._script_btn.setObjectName("secondary")
        else:
            self._cover_btn.setObjectName("secondary")
            self._script_btn.setObjectName("primary")
        self._cover_btn.style().unpolish(self._cover_btn)
        self._cover_btn.style().polish(self._cover_btn)
        self._script_btn.style().unpolish(self._script_btn)
        self._script_btn.style().polish(self._script_btn)
        self._update_preview()

    def _update_preview(self):
        script = getattr(self, "_script", "")
        if not script:
            return
        if self._view_mode == "cover":
            lines = script.split("\n")
            title_page = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(("Title:", "Credit:", "Author:", "Source:", "Draft date:", "Contact:", "Copyright:")):
                    title_page.append(stripped)
                elif stripped.startswith(("INT.", "EXT.", "EST.")) or (title_page and not stripped and len(title_page) > 1):
                    break
            self.preview_area.setPlainText("\n".join(title_page) if title_page else "No title page metadata found")
        else:
            self.preview_area.setPlainText(script)

    def _toggle_export_opt(self, key: str, value: bool):
        self._export_opts[key] = value
        btns = self._toggle_btns.get(key, [])
        if len(btns) == 2:
            btns[0].setObjectName("primary" if value else "secondary")
            btns[1].setObjectName("secondary" if value else "primary")
            for b in btns:
                b.style().unpolish(b)
                b.style().polish(b)

    def update_format_label(self, format_id: str = "", paper: str = ""):
        if format_id or paper:
            self.format_label.setText(
                f"Paginated against {format_id or 'fountain/core'} · "
                f"{paper or 'US Letter'} · Courier Prime 12pt"
            )

    def get_revision_tracker(self) -> RevisionTracker:
        return self._revision_tracker

    def set_revision_tracker(self, tracker: RevisionTracker):
        self._revision_tracker = tracker
        self._update_revision_swatch()
        revisions = tracker.get_revision_history()
        if len(revisions) > 1:
            self.revision_history_label.setText(tracker.get_revision_header())


class EditorScreen(QWidget):
    """Main editor with phase switching."""

    go_home = Signal()
    sprint_clicked = Signal()
    theme_toggle_requested = Signal()
    character_activated = Signal(dict)
    export_pdf_requested = Signal()
    export_odt_requested = Signal()
    export_fountain_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_phase = "Manuscript"
        self._total_pages = 1
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.find_bar = FindReplaceBar()
        self.find_bar.find_next.connect(self._do_find)
        self.find_bar.find_prev.connect(self._do_find_prev)
        self.find_bar.replace_one.connect(self._do_replace)
        self.find_bar.replace_all.connect(self._do_replace_all)
        self.find_bar.closed.connect(self._on_find_closed)
        layout.addWidget(self.find_bar)

        self.plan = PlanPhase()
        self.outline = OutlinePhase()
        self.manuscript = ManuscriptPhase()
        self.proofread = ProofreadPhase()
        self.deliver = DeliverPhase()
        self.deliver.export_pdf_requested.connect(self.export_pdf_requested.emit)
        self.deliver.export_odt_requested.connect(self.export_odt_requested.emit)
        self.deliver.export_fountain_requested.connect(self.export_fountain_requested.emit)

        self.manuscript.char_rail.character_activated.connect(self.character_activated.emit)

        self.phases = {
            "Plan": self.plan,
            "Outline": self.outline,
            "Manuscript": self.manuscript,
            "Proofread": self.proofread,
            "Deliver": self.deliver,
        }

        self.reading_mode = ReadingMode()
        self.reading_mode.exit_requested.connect(self.exit_reading_mode)

        self.phase_stack = QWidget()
        self.phase_layout = QVBoxLayout(self.phase_stack)
        self.phase_layout.setContentsMargins(0, 0, 0, 0)
        for phase_widget in self.phases.values():
            self.phase_layout.addWidget(phase_widget)
            phase_widget.hide()
        self.phase_layout.addWidget(self.reading_mode)
        self.reading_mode.hide()
        self.manuscript.show()

        self.scratchpad = Scratchpad()
        self.scratchpad.closed.connect(self.scratchpad.hide)
        self.scratchpad.paste_requested.connect(self._on_scratchpad_paste)
        self.scratchpad.hide()

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        content_row.addWidget(self.phase_stack, 1)
        content_row.addWidget(self.scratchpad)
        layout.addLayout(content_row, 1)

        self.status_bar = StatusBar()
        self.status_bar.home_clicked.connect(self.go_home.emit)
        self.status_bar.theme_clicked.connect(self.theme_toggle_requested.emit)
        self.status_bar.find_clicked.connect(self._toggle_find)
        self.status_bar.reading_mode_clicked.connect(self.enter_reading_mode)
        self.status_bar.sprint_clicked.connect(self.sprint_clicked.emit)
        layout.addWidget(self.status_bar)

        self._scratchpad_shortcut = QShortcut(QKeySequence("Ctrl+Shift+X"), self)
        self._scratchpad_shortcut.activated.connect(self.toggle_scratchpad)
        self.manuscript.editor.text_cut.connect(self.scratchpad.add_text)
        self.manuscript.editor.cursor_info_changed.connect(self._on_cursor_info_changed)
        self.manuscript.scene_nav.scene_selected.connect(self._on_scene_selected)

    def switch_phase(self, phase: str):
        self._current_phase = phase
        self.reading_mode.hide()
        if phase == "Proofread":
            self.proofread.script_view.setPlainText(
                self.manuscript.editor.toPlainText()
            )
        elif phase == "Deliver":
            self.deliver.set_script(self.manuscript.editor.toPlainText())
        for name, widget in self.phases.items():
            widget.setVisible(name == phase)

    def enter_reading_mode(self):
        text = self.manuscript.editor.toPlainText()
        self.reading_mode.set_content(text, page=1, total_pages=self._total_pages)
        for widget in self.phases.values():
            widget.hide()
        self.reading_mode.show()
        self.reading_mode.setFocus()

    def exit_reading_mode(self):
        self.reading_mode.hide()
        for name, widget in self.phases.items():
            widget.setVisible(name == self._current_phase)

    def toggle_scratchpad(self):
        self.scratchpad.setVisible(not self.scratchpad.isVisible())

    def _on_scratchpad_paste(self, text: str):
        cursor = self.manuscript.editor.textCursor()
        cursor.insertText(text)
        self.manuscript.editor.setFocus()

    def _on_cursor_info_changed(self, page: int, scene_heading: str):
        self.status_bar.page_label.setText(f"Page {page} of {self._total_pages}")
        self.status_bar.scene_label.setText(scene_heading)

    def _on_scene_selected(self, row: int):
        scenes = self.manuscript.scene_nav._scenes_data
        if row < 0 or row >= len(scenes):
            return
        heading = scenes[row].get("heading", "")
        if not heading:
            return
        doc = self.manuscript.editor.document()
        block = doc.begin()
        while block.isValid():
            if block.text().strip() == heading:
                cursor = self.manuscript.editor.textCursor()
                cursor.setPosition(block.position())
                self.manuscript.editor.setTextCursor(cursor)
                self.manuscript.editor.centerCursor()
                self.manuscript.editor.setFocus()
                return
            block = block.next()

    def load_project(self, project_data: dict):
        script = project_data.get("script", "")
        self.manuscript.editor.setPlainText(script)

        self.manuscript.scene_nav.set_script(script)
        self.deliver.set_script(script)

        from ecrit.stores.app_state import STATE
        stats = STATE.get_stats()
        scenes = stats.get("scenes", [])
        characters = stats.get("characters", [])
        self._total_pages = stats.get("page_count", 1)
        self.manuscript.scene_nav.update_scenes(scenes)
        self.manuscript.char_rail.update_characters(characters)
        self.status_bar.update_info(
            page=1,
            total_pages=stats.get("page_count", 1),
            scene=scenes[0]["heading"] if scenes else "",
            dialect=project_data.get("meta", {}).get("format_id", "fountain/core"),
        )

        plans = project_data.get("plan_documents", [])
        if plans:
            self.plan.editor.setPlainText(plans[0].get("content", ""))

        self.proofread.script_view.setPlainText(script)

    def _toggle_find(self):
        self.find_bar.toggle()

    def _on_find_closed(self):
        self.manuscript.editor.setFocus()

    def _find_in_direction(self, text, case_sensitive, regex, backward=False):
        if not text:
            return
        editor = self.manuscript.editor
        if regex:
            from PySide6.QtCore import QRegularExpression
            opts = QRegularExpression.PatternOption.NoPatternOption
            if not case_sensitive:
                opts |= QRegularExpression.PatternOption.CaseInsensitiveOption
            qre = QRegularExpression(text)
            qre.setPatternOptions(opts)
            if not qre.isValid():
                return
            flags = QTextDocument.FindFlag.FindBackward if backward else QTextDocument.FindFlag(0)
            found = editor.find(qre, flags)
            if not found:
                cursor = editor.textCursor()
                wrap_to = QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start
                cursor.movePosition(wrap_to)
                editor.setTextCursor(cursor)
                editor.find(qre, flags)
        else:
            flags = QTextDocument.FindFlag.FindBackward if backward else QTextDocument.FindFlag(0)
            if case_sensitive:
                flags |= QTextDocument.FindFlag.FindCaseSensitively
            found = editor.find(text, flags)
            if not found:
                cursor = editor.textCursor()
                wrap_to = QTextCursor.MoveOperation.End if backward else QTextCursor.MoveOperation.Start
                cursor.movePosition(wrap_to)
                editor.setTextCursor(cursor)
                editor.find(text, flags)

    def _do_find(self, text, case_sensitive, regex):
        self._find_in_direction(text, case_sensitive, regex, backward=False)

    def _do_find_prev(self, text, case_sensitive, regex):
        self._find_in_direction(text, case_sensitive, regex, backward=True)

    def _do_replace(self, find_text, replace_text):
        editor = self.manuscript.editor
        cursor = editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == find_text:
            cursor.insertText(replace_text)
        self._do_find(find_text, False, False)

    def _do_replace_all(self, find_text, replace_text):
        if not find_text:
            return
        editor = self.manuscript.editor
        content = editor.toPlainText()
        count = content.count(find_text)
        if count > 0:
            new_content = content.replace(find_text, replace_text)
            editor.setPlainText(new_content)
            self.find_bar.set_match_count(0, 0)
