"""Character sheet modal — detailed character editing with moodboard."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFrame, QGridLayout, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


class MoodboardTile(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        t = theme.current()
        self.setFixedSize(120, 120)
        self.setStyleSheet(
            f"background: {t.neutral_800 if t.name == 'nocturne' else t.neutral_200}; "
            f"border: 2px dashed {t.neutral_700 if t.name == 'nocturne' else t.neutral_300}; "
            f"border-radius: {t.radius_md}px;"
        )
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel("+")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"color: {t.neutral_500}; font-size: 24px; background: transparent;")
        layout.addWidget(icon)
        label = QLabel("Drop image")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {t.neutral_500}; font-size: 11px; background: transparent;")
        layout.addWidget(label)


class CharacterSheet(QDialog):
    character_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Character Sheet")
        self.setMinimumSize(760, 560)
        self.setModal(True)
        self._data = {}

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 16, 24, 8)

        self.name_label = QLabel("Character")
        self.name_label.setStyleSheet("font-size: 22px; font-weight: 500;")
        header.addWidget(self.name_label)

        self.role_tag = QLabel()
        self.role_tag.setObjectName("tagAccent")
        header.addWidget(self.role_tag)

        header.addStretch()

        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        grid = QHBoxLayout(content)
        grid.setContentsMargins(24, 8, 24, 24)
        grid.setSpacing(20)

        left = QVBoxLayout()
        left.setSpacing(12)

        fields = [
            ("Name", "name_input"),
            ("Age", "age_input"),
            ("Pronouns", "pronouns_input"),
            ("Occupation", "occupation_input"),
        ]
        for label_text, attr_name in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
            left.addWidget(lbl)
            inp = QLineEdit()
            inp.setFixedHeight(32)
            left.addWidget(inp)
            setattr(self, attr_name, inp)

        for label_text, attr_name in [
            ("Wants / Needs", "wants_input"),
            ("Voice notes", "voice_input"),
            ("Arc", "arc_input"),
            ("Relationships", "relationships_input"),
        ]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
            left.addWidget(lbl)
            txt = QTextEdit()
            txt.setFixedHeight(60)
            left.addWidget(txt)
            setattr(self, attr_name, txt)

        self.scenes_label = QLabel()
        self.scenes_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        left.addWidget(self.scenes_label)

        left.addStretch()
        grid.addLayout(left, 1)

        right = QVBoxLayout()
        right.setSpacing(12)

        mb_label = QLabel("MOODBOARD")
        mb_label.setObjectName("kicker")
        right.addWidget(mb_label)

        mb_grid = QGridLayout()
        mb_grid.setSpacing(8)
        for i in range(6):
            tile = MoodboardTile()
            mb_grid.addWidget(tile, i // 2, i % 2)
        right.addLayout(mb_grid)

        notes_label = QLabel("NOTES")
        notes_label.setObjectName("kicker")
        right.addWidget(notes_label)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Character notes...")
        right.addWidget(self.notes_input, 1)

        right_widget = QWidget()
        right_widget.setFixedWidth(300)
        right_widget.setLayout(right)
        grid.addWidget(right_widget)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(24, 8, 24, 16)
        footer.addStretch()
        done_btn = QPushButton("Done")
        done_btn.setObjectName("primary")
        done_btn.setFixedHeight(36)
        done_btn.clicked.connect(self._on_done)
        footer.addWidget(done_btn)
        layout.addLayout(footer)

    def set_character(self, data: dict):
        self._data = data
        self.name_label.setText(data.get("name", "Character"))
        self.name_input.setText(data.get("name", ""))
        self.age_input.setText(data.get("age", ""))
        self.pronouns_input.setText(data.get("pronouns", ""))
        self.occupation_input.setText(data.get("occupation", ""))
        self.wants_input.setPlainText(data.get("wants", ""))
        self.voice_input.setPlainText(data.get("voice", ""))
        self.arc_input.setPlainText(data.get("arc", ""))
        self.relationships_input.setPlainText(data.get("relationships", ""))
        self.notes_input.setPlainText(data.get("notes", ""))

        role = data.get("role", "")
        self.role_tag.setText(role)
        self.role_tag.setVisible(bool(role))

        scene_count = data.get("scene_count", 0)
        line_count = data.get("line_count", 0)
        self.scenes_label.setText(f"{scene_count} scenes · {line_count} lines")

    def _on_done(self):
        result = {
            **self._data,
            "name": self.name_input.text(),
            "age": self.age_input.text(),
            "pronouns": self.pronouns_input.text(),
            "occupation": self.occupation_input.text(),
            "wants": self.wants_input.toPlainText(),
            "voice": self.voice_input.toPlainText(),
            "arc": self.arc_input.toPlainText(),
            "relationships": self.relationships_input.toPlainText(),
            "notes": self.notes_input.toPlainText(),
        }
        self.character_saved.emit(result)
        self.close()
