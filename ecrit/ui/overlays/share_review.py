"""Share for review dialog — generate watermarked HTML review links."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QListWidget, QListWidgetItem,
    QCheckBox, QScrollArea, QWidget, QApplication,
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


class ShareReviewDialog(QDialog):
    """Generate and manage shareable review links."""

    share_created = Signal(str)  # path to HTML file

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Share for Review")
        self.setMinimumSize(480, 420)
        self.setModal(True)

        self._shares: list[dict] = []

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel("Share for Review")
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
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
        form = QVBoxLayout(content)
        form.setContentsMargins(24, 16, 24, 16)
        form.setSpacing(12)

        desc = QLabel(
            "Generate a self-contained HTML file for sharing your script.\n"
            "Includes a watermark overlay for confidentiality."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px;")
        form.addWidget(desc)

        watermark_label = QLabel("Watermark Text")
        watermark_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(watermark_label)

        self.watermark_input = QLineEdit()
        self.watermark_input.setFixedHeight(34)
        self.watermark_input.setText("CONFIDENTIAL — FOR REVIEW ONLY")
        self.watermark_input.setPlaceholderText("e.g. CONFIDENTIAL — FOR REVIEW ONLY")
        form.addWidget(self.watermark_input)

        self.include_title_page = QCheckBox("Include title page")
        self.include_title_page.setChecked(True)
        form.addWidget(self.include_title_page)

        self.include_page_numbers = QCheckBox("Include page numbers")
        self.include_page_numbers.setChecked(True)
        form.addWidget(self.include_page_numbers)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        form.addWidget(divider)

        shares_header = QLabel("GENERATED SHARES")
        shares_header.setObjectName("kicker")
        form.addWidget(shares_header)

        self.shares_list = QListWidget()
        self.shares_list.setFixedHeight(120)
        form.addWidget(self.shares_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        copy_btn = QPushButton("Copy Path")
        copy_btn.setObjectName("secondary")
        copy_btn.setFixedHeight(30)
        copy_btn.clicked.connect(self._copy_selected_path)
        btn_row.addWidget(copy_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("secondary")
        delete_btn.setFixedHeight(30)
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(delete_btn)

        btn_row.addStretch()
        form.addLayout(btn_row)

        form.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(24, 8, 24, 16)
        footer.addStretch()

        cancel_btn = QPushButton("Close")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.close)
        footer.addWidget(cancel_btn)

        self.generate_btn = QPushButton("Generate Review Link")
        self.generate_btn.setObjectName("primary")
        self.generate_btn.setFixedHeight(36)
        self.generate_btn.clicked.connect(self._generate)
        footer.addWidget(self.generate_btn)

        layout.addLayout(footer)

    def set_shares(self, shares: list[dict]):
        self._shares = shares
        self.shares_list.clear()
        for share in shares:
            item = QListWidgetItem()
            item.setText(f"{share.get('title', 'Untitled')} — {share.get('created', '')}")
            item.setData(Qt.ItemDataRole.UserRole, share)
            self.shares_list.addItem(item)

    def get_watermark(self) -> str:
        return self.watermark_input.text()

    def get_options(self) -> dict:
        return {
            "watermark": self.watermark_input.text(),
            "include_title_page": self.include_title_page.isChecked(),
            "include_page_numbers": self.include_page_numbers.isChecked(),
        }

    def _generate(self):
        self.share_created.emit(self.watermark_input.text())

    def _copy_selected_path(self):
        current = self.shares_list.currentItem()
        if current:
            data = current.data(Qt.ItemDataRole.UserRole)
            path = data.get("path", "") if data else ""
            if path:
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(path)

    def _delete_selected(self):
        row = self.shares_list.currentRow()
        if row >= 0:
            self.shares_list.takeItem(row)
            if row < len(self._shares):
                self._shares.pop(row)

    def add_share(self, share: dict):
        self._shares.insert(0, share)
        item = QListWidgetItem()
        item.setText(f"{share.get('title', 'Untitled')} — {share.get('created', '')}")
        item.setData(Qt.ItemDataRole.UserRole, share)
        self.shares_list.insertItem(0, item)
