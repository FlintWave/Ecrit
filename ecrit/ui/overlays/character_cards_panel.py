"""Character cards panel — browse and edit character cards with bios and relationships."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QTextEdit, QComboBox, QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap

from ecrit.ui.styles import theme
from ecrit.screenplay.character_cards import (
    CharacterCardManager, CharacterCard, CharacterBio, RELATIONSHIP_TYPES,
)


class CharacterCardsPanel(QDialog):
    card_updated = Signal()

    def __init__(self, manager: CharacterCardManager, parent=None):
        super().__init__(parent)
        self._mgr = manager
        self.setWindowTitle("Character Cards")
        self.setMinimumSize(800, 560)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Character Cards")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {t.text};")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel()
        self._count_label.setStyleSheet(f"color: {t.neutral_400}; font-size: 13px;")
        header.addWidget(self._count_label)
        layout.addLayout(header)

        body = QHBoxLayout()
        left = QVBoxLayout()
        self._card_list = QListWidget()
        self._card_list.setMaximumWidth(200)
        self._card_list.currentItemChanged.connect(self._on_card_selected)
        left.addWidget(self._card_list)

        add_btn = QPushButton("+ New Card")
        add_btn.clicked.connect(self._add_card)
        left.addWidget(add_btn)

        auto_btn = QPushButton("Auto-populate")
        auto_btn.setToolTip("Scan script for character names")
        auto_btn.clicked.connect(self._auto_populate)
        left.addWidget(auto_btn)

        body.addLayout(left)

        self._tabs = QTabWidget()

        self._bio_tab = QWidget()
        self._rel_tab = QWidget()
        self._arc_tab = QWidget()

        self._tabs.addTab(self._bio_tab, "Bio")
        self._tabs.addTab(self._rel_tab, "Relationships")
        self._tabs.addTab(self._arc_tab, "Arc & Notes")

        body.addWidget(self._tabs, 1)
        layout.addLayout(body, 1)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_current)
        btn_row.addWidget(save_btn)

        del_btn = QPushButton("Delete Card")
        del_btn.clicked.connect(self._delete_current)
        btn_row.addWidget(del_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._build_bio_tab()
        self._build_rel_tab()
        self._build_arc_tab()

    def set_script_content(self, content: str):
        self._script_content = content

    def refresh(self):
        self._card_list.clear()
        cards = self._mgr.get_all_cards()
        self._count_label.setText(f"{len(cards)} characters")
        for card in cards:
            item = QListWidgetItem(card.name)
            item.setData(Qt.ItemDataRole.UserRole, card.name)
            item.setForeground(QColor(card.color))
            self._card_list.addItem(item)
        if self._card_list.count():
            self._card_list.setCurrentRow(0)

    def _build_bio_tab(self):
        layout = QFormLayout(self._bio_tab)
        self._bio_full_name = QLineEdit()
        self._bio_nickname = QLineEdit()
        self._bio_age = QLineEdit()
        self._bio_gender = QLineEdit()
        self._bio_occupation = QLineEdit()
        self._bio_physical = QLineEdit()
        self._bio_backstory = QTextEdit()
        self._bio_backstory.setMaximumHeight(80)
        self._bio_motivation = QLineEdit()
        self._bio_speech = QLineEdit()

        layout.addRow("Full Name:", self._bio_full_name)
        layout.addRow("Nickname:", self._bio_nickname)
        layout.addRow("Age:", self._bio_age)
        layout.addRow("Gender:", self._bio_gender)
        layout.addRow("Occupation:", self._bio_occupation)
        layout.addRow("Physical:", self._bio_physical)
        layout.addRow("Backstory:", self._bio_backstory)
        layout.addRow("Motivation:", self._bio_motivation)
        layout.addRow("Speech Pattern:", self._bio_speech)

    def _build_rel_tab(self):
        layout = QVBoxLayout(self._rel_tab)
        self._rel_list = QListWidget()
        layout.addWidget(self._rel_list)

        add_row = QHBoxLayout()
        self._rel_target = QLineEdit()
        self._rel_target.setPlaceholderText("Character name...")
        add_row.addWidget(self._rel_target)

        self._rel_type = QComboBox()
        self._rel_type.addItems(RELATIONSHIP_TYPES)
        add_row.addWidget(self._rel_type)

        add_rel_btn = QPushButton("Add")
        add_rel_btn.clicked.connect(self._add_relationship)
        add_row.addWidget(add_rel_btn)
        layout.addLayout(add_row)

    def _build_arc_tab(self):
        layout = QFormLayout(self._arc_tab)
        self._arc_wants = QLineEdit()
        self._arc_needs = QLineEdit()
        self._arc_flaw = QLineEdit()
        self._arc_summary = QTextEdit()
        self._arc_summary.setMaximumHeight(80)
        self._arc_notes = QTextEdit()
        self._arc_notes.setMaximumHeight(80)

        layout.addRow("Wants:", self._arc_wants)
        layout.addRow("Needs:", self._arc_needs)
        layout.addRow("Flaw:", self._arc_flaw)
        layout.addRow("Arc Summary:", self._arc_summary)
        layout.addRow("Notes:", self._arc_notes)

    def _on_card_selected(self, current, previous):
        if not current:
            return
        name = current.data(Qt.ItemDataRole.UserRole)
        card = self._mgr.get_card(name)
        if not card:
            return
        self._load_card(card)

    def _load_card(self, card: CharacterCard):
        bio = card.bio
        self._bio_full_name.setText(bio.full_name)
        self._bio_nickname.setText(bio.nickname)
        self._bio_age.setText(bio.age)
        self._bio_gender.setText(bio.gender)
        self._bio_occupation.setText(bio.occupation)
        self._bio_physical.setText(bio.physical_description)
        self._bio_backstory.setPlainText(bio.backstory)
        self._bio_motivation.setText(bio.motivation)
        self._bio_speech.setText(bio.speech_pattern)

        self._rel_list.clear()
        for rel in card.relationships:
            self._rel_list.addItem(f"{rel.target_name} ({rel.relationship_type})")

        self._arc_wants.setText(card.wants)
        self._arc_needs.setText(card.needs)
        self._arc_flaw.setText(card.flaw)
        self._arc_summary.setPlainText(card.arc_summary)
        self._arc_notes.setPlainText(card.notes)

    def _save_current(self):
        item = self._card_list.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        card = self._mgr.get_card(name)
        if not card:
            return
        card.bio.full_name = self._bio_full_name.text()
        card.bio.nickname = self._bio_nickname.text()
        card.bio.age = self._bio_age.text()
        card.bio.gender = self._bio_gender.text()
        card.bio.occupation = self._bio_occupation.text()
        card.bio.physical_description = self._bio_physical.text()
        card.bio.backstory = self._bio_backstory.toPlainText()
        card.bio.motivation = self._bio_motivation.text()
        card.bio.speech_pattern = self._bio_speech.text()

        card.wants = self._arc_wants.text()
        card.needs = self._arc_needs.text()
        card.flaw = self._arc_flaw.text()
        card.arc_summary = self._arc_summary.toPlainText()
        card.notes = self._arc_notes.toPlainText()

        self._mgr.update_card(card)
        self.card_updated.emit()

    def _add_card(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Character", "Character name:")
        if ok and name.strip():
            self._mgr.add_card(name.strip())
            self.refresh()

    def _delete_current(self):
        item = self._card_list.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        self._mgr.remove_card(name)
        self.refresh()
        self.card_updated.emit()

    def _auto_populate(self):
        content = getattr(self, '_script_content', '')
        if content:
            self._mgr.auto_populate_from_script(content)
            self.refresh()

    def _add_relationship(self):
        target = self._rel_target.text().strip()
        rel_type = self._rel_type.currentText()
        if not target:
            return
        item = self._card_list.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        card = self._mgr.get_card(name)
        if card:
            card.add_relationship(target.upper(), rel_type)
            self._rel_list.addItem(f"{target.upper()} ({rel_type})")
            self._rel_target.clear()
