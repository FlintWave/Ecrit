"""Remote sync settings dialog — configure git remote providers."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QCheckBox, QGroupBox,
    QScrollArea, QWidget,
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme


PROVIDERS = [
    ("github", "GitHub", "https://github.com"),
    ("gitlab", "GitLab", "https://gitlab.com"),
    ("codeberg", "Codeberg", "https://codeberg.org"),
]


class SyncSettingsDialog(QDialog):
    """Configure remote sync providers for a project."""

    sync_requested = Signal(str)  # "push" or "pull"
    config_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remote Sync")
        self.setMinimumSize(500, 480)
        self.setModal(True)

        self._config: dict = {}

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel("Remote Sync")
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
        for key, name, url in PROVIDERS:
            self.provider_combo.addItem(f"{name} ({url})", key)
        form.addWidget(self.provider_combo)

        repo_label = QLabel("Repository URL")
        repo_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(repo_label)

        self.repo_url_input = QLineEdit()
        self.repo_url_input.setFixedHeight(34)
        self.repo_url_input.setPlaceholderText("https://github.com/user/project.git")
        form.addWidget(self.repo_url_input)

        user_label = QLabel("Username")
        user_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(user_label)

        self.username_input = QLineEdit()
        self.username_input.setFixedHeight(34)
        self.username_input.setPlaceholderText("Your username")
        form.addWidget(self.username_input)

        token_label = QLabel("Personal Access Token")
        token_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(token_label)

        self.token_input = QLineEdit()
        self.token_input.setFixedHeight(34)
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("ghp_... or glpat-...")
        form.addWidget(self.token_input)

        branch_label = QLabel("Branch")
        branch_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        form.addWidget(branch_label)

        self.branch_input = QLineEdit()
        self.branch_input.setFixedHeight(34)
        self.branch_input.setText("main")
        form.addWidget(self.branch_input)

        self.auto_sync_check = QCheckBox("Auto-sync on save")
        form.addWidget(self.auto_sync_check)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {t.neutral_700 if t.name == 'nocturne' else t.divider};")
        form.addWidget(divider)

        status_label = QLabel("STATUS")
        status_label.setObjectName("kicker")
        form.addWidget(status_label)

        self.status_display = QLabel("Not configured")
        self.status_display.setWordWrap(True)
        self.status_display.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px; padding: 4px 0;")
        form.addWidget(self.status_display)

        self.last_sync_label = QLabel("")
        self.last_sync_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        form.addWidget(self.last_sync_label)

        form.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(24, 8, 24, 16)

        save_btn = QPushButton("Save Config")
        save_btn.setObjectName("secondary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save_config)
        footer.addWidget(save_btn)

        footer.addStretch()

        pull_btn = QPushButton("Pull")
        pull_btn.setObjectName("secondary")
        pull_btn.setFixedHeight(36)
        pull_btn.clicked.connect(lambda: self.sync_requested.emit("pull"))
        footer.addWidget(pull_btn)

        push_btn = QPushButton("Push")
        push_btn.setObjectName("primary")
        push_btn.setFixedHeight(36)
        push_btn.clicked.connect(lambda: self.sync_requested.emit("push"))
        footer.addWidget(push_btn)

        layout.addLayout(footer)

    def set_config(self, config: dict):
        self._config = config
        provider = config.get("provider", "github")
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == provider:
                self.provider_combo.setCurrentIndex(i)
                break
        self.repo_url_input.setText(config.get("remote_url", ""))
        self.username_input.setText(config.get("username", ""))
        self.branch_input.setText(config.get("branch", "main"))
        self.auto_sync_check.setChecked(config.get("auto_sync", False))

    def set_status(self, status: str, last_sync: str = ""):
        self.status_display.setText(status)
        if last_sync:
            self.last_sync_label.setText(f"Last sync: {last_sync}")

    def get_config(self) -> dict:
        return {
            "provider": self.provider_combo.currentData(),
            "remote_url": self.repo_url_input.text(),
            "username": self.username_input.text(),
            "token": self.token_input.text(),
            "branch": self.branch_input.text(),
            "auto_sync": self.auto_sync_check.isChecked(),
        }

    def _save_config(self):
        self._config = self.get_config()
        self.config_changed.emit(self._config)
