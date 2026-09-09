"""Cloud drive export dialog — export scripts to cloud storage providers."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QCheckBox, QListWidget,
    QListWidgetItem, QScrollArea, QWidget,
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme
from ecrit.sync.cloud_export import CloudProvider, CloudConfig


CLOUD_PROVIDERS = [
    (CloudProvider.GOOGLE_DRIVE, "Google Drive", "Export to Google Drive"),
    (CloudProvider.DROPBOX, "Dropbox", "Export to Dropbox"),
    (CloudProvider.ONEDRIVE, "OneDrive", "Export to Microsoft OneDrive"),
    (CloudProvider.ICLOUD, "iCloud", "Export to Apple iCloud Drive"),
    (CloudProvider.NEXTCLOUD, "Nextcloud", "Export to self-hosted Nextcloud"),
]


class CloudExportDialog(QDialog):
    """Configure and trigger cloud drive exports."""

    export_requested = Signal(str, str)  # provider_key, format

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cloud Export")
        self.setMinimumSize(480, 440)
        self.setModal(True)

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel("Cloud Export")
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

        provider_label = QLabel("Provider")
        provider_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.setFixedHeight(34)
        for provider, name, desc in CLOUD_PROVIDERS:
            self.provider_combo.addItem(f"{name} — {desc}", provider.value)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form.addWidget(self.provider_combo)

        self.auth_status = QLabel("Not authenticated")
        self.auth_status.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        form.addWidget(self.auth_status)

        auth_btn = QPushButton("Authenticate...")
        auth_btn.setObjectName("secondary")
        auth_btn.setFixedHeight(34)
        auth_btn.clicked.connect(self._authenticate)
        form.addWidget(auth_btn)

        divider1 = QFrame()
        divider1.setFrameShape(QFrame.Shape.HLine)
        form.addWidget(divider1)

        folder_label = QLabel("Remote Folder")
        folder_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(folder_label)

        self.folder_input = QLineEdit()
        self.folder_input.setFixedHeight(34)
        self.folder_input.setPlaceholderText("/Écrit/Exports")
        self.folder_input.setText("/Écrit/Exports")
        form.addWidget(self.folder_input)

        format_label = QLabel("Export Format")
        format_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.setFixedHeight(34)
        self.format_combo.addItem("PDF", "pdf")
        self.format_combo.addItem("ODT (LibreOffice)", "odt")
        self.format_combo.addItem("Fountain (.fountain)", "fountain")
        self.format_combo.addItem("HTML (Review)", "html")
        form.addWidget(self.format_combo)

        self.auto_export_check = QCheckBox("Auto-export on save")
        form.addWidget(self.auto_export_check)

        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        form.addWidget(divider2)

        history_label = QLabel("EXPORT HISTORY")
        history_label.setObjectName("kicker")
        form.addWidget(history_label)

        self.history_list = QListWidget()
        self.history_list.setFixedHeight(100)
        form.addWidget(self.history_list)

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

        self.export_btn = QPushButton("Export Now")
        self.export_btn.setObjectName("primary")
        self.export_btn.setFixedHeight(36)
        self.export_btn.clicked.connect(self._do_export)
        footer.addWidget(self.export_btn)

        layout.addLayout(footer)

    def _on_provider_changed(self, index: int):
        self.auth_status.setText("Not authenticated")

    def _authenticate(self):
        provider = self.provider_combo.currentData()
        self.auth_status.setText(f"Authentication required — open browser to authorize (stub)")

    def _do_export(self):
        provider = self.provider_combo.currentData()
        fmt = self.format_combo.currentData()
        self.export_requested.emit(provider, fmt)
        self.history_list.insertItem(0, f"Exported as {fmt.upper()} to {self.provider_combo.currentText().split(' —')[0]}")

    def set_configs(self, configs: list):
        pass

    def add_history_entry(self, text: str):
        self.history_list.insertItem(0, text)
