"""Editor screen — five phases: Plan, Outline, Manuscript, Proofread, Deliver."""

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QListWidget, QListWidgetItem,
    QPlainTextEdit, QSizePolicy, QTextEdit, QScrollArea
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


class ScriptEditor(QPlainTextEdit):
    """Courier Prime script editor with typewriter scrolling."""

    content_changed = Signal()
    text_cut = Signal(str)

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
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(1000)
        self._save_timer.timeout.connect(self.content_changed.emit)

        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._on_cursor_moved)

    def _on_text_changed(self):
        self._save_timer.start()

    def _on_cursor_moved(self):
        if self._typewriter:
            cursor = self.cursorRect()
            viewport_center = self.viewport().height() // 2
            scroll_bar = self.verticalScrollBar()
            current = scroll_bar.value()
            target = current + cursor.top() - viewport_center
            scroll_bar.setValue(target)

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

        types = [
            ("Scene Heading", "INT. "),
            ("Action", ""),
            ("Character", ""),
            ("Dialogue", ""),
            ("Parenthetical", "("),
            ("Transition", "CUT TO:"),
        ]

        if line.startswith(("INT.", "EXT.")):
            cursor.removeSelectedText()
            cursor.insertText(line)
        elif line.startswith("(") and line.endswith(")"):
            cursor.removeSelectedText()
            cursor.insertText(line[1:-1] if len(line) > 2 else line)
        else:
            pass


class SceneNavigator(QFrame):
    """Left rail: scene list from parsed Fountain."""

    scene_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("rail")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(0)

        header = QLabel("SCENES")
        header.setObjectName("kicker")
        header.setStyleSheet("padding: 8px 12px;")
        layout.addWidget(header)

        self.scene_list = QListWidget()
        self.scene_list.currentRowChanged.connect(self.scene_selected.emit)
        layout.addWidget(self.scene_list)

    def update_scenes(self, scenes: list):
        self.scene_list.clear()
        for sc in scenes:
            num = sc.get("number", str(sc.get("index", 0) + 1))
            heading = sc.get("heading", "")
            page = sc.get("page", 0)
            item = QListWidgetItem(f"{num}  {heading}  {page}")
            self.scene_list.addItem(item)


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
        docs = ["Logline", "Synopsis", "One-page pitch", "Treatment"]
        for d in docs:
            self.doc_list.addItem(d)
        rail_layout.addWidget(self.doc_list)

        add_btn = QPushButton("+ New document")
        add_btn.setObjectName("ghost")
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

        self.doc_header = QLabel("SYNOPSIS · DRAFT 1")
        self.doc_header.setObjectName("kicker")
        ec_layout.addWidget(self.doc_header)

        self.editor = QTextEdit()
        self.editor.setObjectName("planEditor")
        font = QFont("Liberation Serif", 16)
        self.editor.setFont(font)
        self.editor.setPlaceholderText("Start writing...")
        ec_layout.addWidget(self.editor)

        center_layout.addWidget(editor_container)
        layout.addWidget(center, 1)


class OutlinePhase(QWidget):
    """Outline phase: node graph placeholder (full graph requires canvas)."""

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
        toolbar.addWidget(layout_h)

        layout_v = QPushButton("↓")
        layout_v.setObjectName("secondary")
        layout_v.setFixedSize(28, 28)
        layout_v.setToolTip("Vertical layout")
        toolbar.addWidget(layout_v)

        toolbar.addStretch()

        add_btn = QPushButton("+ Add node")
        add_btn.setObjectName("primary")
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
        zoom_bar.addWidget(self.zoom_out)
        self.zoom_label = QLabel("100%")
        zoom_bar.addWidget(self.zoom_label)
        self.zoom_in = QPushButton("+")
        self.zoom_in.setObjectName("secondary")
        self.zoom_in.setFixedSize(28, 28)
        zoom_bar.addWidget(self.zoom_in)
        fit_btn = QPushButton("Fit")
        fit_btn.setObjectName("secondary")
        zoom_bar.addWidget(fit_btn)
        zoom_bar.addStretch()
        info = QLabel("Right-click to add nodes")
        info.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 12px;")
        zoom_bar.addWidget(info)
        layout.addLayout(zoom_bar)


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


class ManuscriptPhase(QWidget):
    """Manuscript phase: scene nav + script editor + character rail."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scene_nav = SceneNavigator()
        self.scene_nav.setFixedWidth(216)

        divider_l = QFrame()
        divider_l.setObjectName("railDivider")
        divider_l.setFixedWidth(1)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.page_frame = QFrame()
        self.page_frame.setStyleSheet(f"background: {theme.current().surface}; border-radius: 4px;")
        self.page_frame.setMaximumWidth(680)
        self.page_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        page_layout = QVBoxLayout(self.page_frame)
        page_layout.setContentsMargins(0, 0, 0, 0)

        self.editor = ScriptEditor()
        page_layout.addWidget(self.editor)

        center_layout.addWidget(self.page_frame)

        divider_r = QFrame()
        divider_r.setObjectName("railDivider")
        divider_r.setFixedWidth(1)

        self.char_rail = CharacterRail()
        self.char_rail.setFixedWidth(264)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.scene_nav)
        splitter.addWidget(center)
        splitter.addWidget(self.char_rail)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([216, 600, 264])

        layout.addWidget(splitter)


class ProofreadPhase(QWidget):
    """Proofread phase: script view + issues rail."""

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

        self.issues_list = QListWidget()
        rail_layout.addWidget(self.issues_list)

        layout.addWidget(rail)


class DeliverPhase(QWidget):
    """Deliver phase: print preview + export rail."""

    export_pdf_requested = Signal()
    export_odt_requested = Signal()
    export_fountain_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
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

        self.view_seg = QHBoxLayout()
        cover_btn = QPushButton("Cover page")
        cover_btn.setObjectName("secondary")
        self.view_seg.addWidget(cover_btn)
        script_btn = QPushButton("Script pages")
        script_btn.setObjectName("primary")
        self.view_seg.addWidget(script_btn)
        top.addLayout(self.view_seg)
        center_layout.addLayout(top)

        self.format_label = QLabel("Paginated against fountain/core · US Letter · Courier Prime 12pt")
        self.format_label.setStyleSheet(f"color: {theme.current().neutral_500}; font-size: 13px;")
        center_layout.addWidget(self.format_label)

        self.preview_area = QLabel("Print preview will appear here")
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setStyleSheet(
            f"background: {theme.current().surface}; border-radius: 8px; "
            f"min-height: 400px; color: {theme.current().neutral_500};"
        )
        center_layout.addWidget(self.preview_area, 1)
        center_layout.addStretch()
        layout.addWidget(center, 1)

        divider = QFrame()
        divider.setObjectName("railDivider")
        divider.setFixedWidth(1)
        layout.addWidget(divider)

        rail = QFrame()
        rail.setObjectName("rail")
        rail.setFixedWidth(360)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(16, 16, 16, 16)
        rail_layout.setSpacing(16)

        export_title = QLabel("EXPORT")
        export_title.setObjectName("kicker")
        rail_layout.addWidget(export_title)

        for label_text, seg_options in [
            ("Title page", ["Include", "Omit"]),
            ("Scene numbers", ["On", "Off"]),
            ("Revision marks", ["Show", "Clean"]),
        ]:
            row = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 13px;")
            row.addWidget(lbl)
            seg = QHBoxLayout()
            for opt in seg_options:
                btn = QPushButton(opt)
                btn.setObjectName("secondary")
                btn.setFixedHeight(30)
                seg.addWidget(btn)
            row.addLayout(seg)
            rail_layout.addLayout(row)

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

        layout.addWidget(rail)


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

    def switch_phase(self, phase: str):
        self._current_phase = phase
        self.reading_mode.hide()
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

    def load_project(self, project_data: dict):
        script = project_data.get("script", "")
        self.manuscript.editor.setPlainText(script)

        try:
            import ecrit_core
            stats = json.loads(ecrit_core.get_script_stats(script))
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
        except Exception:
            pass

        plans = project_data.get("plan_documents", [])
        if plans:
            self.plan.editor.setPlainText(plans[0].get("content", ""))

        self.proofread.script_view.setPlainText(script)

    def _toggle_find(self):
        self.find_bar.toggle()

    def _do_find(self, text, case_sensitive, regex):
        if not text:
            return
        editor = self.manuscript.editor
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        found = editor.find(text, flags)
        if not found:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            editor.setTextCursor(cursor)
            editor.find(text, flags)

    def _do_find_prev(self, text, case_sensitive, regex):
        if not text:
            return
        editor = self.manuscript.editor
        flags = QTextDocument.FindFlag.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        found = editor.find(text, flags)
        if not found:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            editor.setTextCursor(cursor)
            editor.find(text, flags)

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
