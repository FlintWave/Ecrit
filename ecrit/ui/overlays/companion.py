"""Companion sync overlay — pair devices, sync bundles, export reader mode."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QFrame, QLineEdit, QFileDialog,
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme
from ecrit.i18n import tr
from ecrit.companion.device_sync import DeviceSync, PairedDevice, SyncStatus


class CompanionDialog(QDialog):
    sync_bundle_requested = Signal()
    reader_export_requested = Signal()
    wifi_transfer_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("companion.title"))
        self.setMinimumSize(520, 440)
        self.setModal(True)

        self._device_sync = DeviceSync()
        self._device_sync.set_status_callback(self._on_sync_status_change)
        t = theme.current()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel(tr("companion.title"))
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        tabs = QTabWidget()

        # Devices tab
        devices_tab = QWidget()
        d_layout = QVBoxLayout(devices_tab)
        d_layout.setContentsMargins(16, 12, 16, 12)
        d_layout.setSpacing(12)

        d_layout.addWidget(QLabel(tr("companion.paired_devices")))
        self.devices_list = QListWidget()
        self.devices_list.setFixedHeight(140)
        d_layout.addWidget(self.devices_list)

        pair_row = QHBoxLayout()
        self.device_name_input = QLineEdit()
        self.device_name_input.setPlaceholderText(tr("companion.device_name"))
        self.device_name_input.setFixedHeight(34)
        pair_row.addWidget(self.device_name_input)

        pair_btn = QPushButton(tr("companion.pair_new"))
        pair_btn.setObjectName("primary")
        pair_btn.setFixedHeight(34)
        pair_btn.clicked.connect(self._pair_new_device)
        pair_row.addWidget(pair_btn)
        d_layout.addLayout(pair_row)

        unpair_btn = QPushButton("Unpair Selected")
        unpair_btn.setObjectName("secondary")
        unpair_btn.setFixedHeight(30)
        unpair_btn.clicked.connect(self._unpair_selected)
        d_layout.addWidget(unpair_btn)

        d_layout.addStretch()
        tabs.addTab(devices_tab, tr("companion.paired_devices"))

        # Sync tab
        sync_tab = QWidget()
        s_layout = QVBoxLayout(sync_tab)
        s_layout.setContentsMargins(16, 12, 16, 12)
        s_layout.setSpacing(12)

        self.sync_status_label = QLabel(tr("companion.never_synced"))
        self.sync_status_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px;")
        s_layout.addWidget(self.sync_status_label)

        sync_btn = QPushButton(tr("companion.full_sync"))
        sync_btn.setObjectName("primary")
        sync_btn.setFixedHeight(40)
        sync_btn.clicked.connect(self.sync_bundle_requested.emit)
        s_layout.addWidget(sync_btn)

        reader_btn = QPushButton(tr("companion.reader_mode"))
        reader_btn.setObjectName("secondary")
        reader_btn.setFixedHeight(36)
        reader_btn.clicked.connect(self.reader_export_requested.emit)
        s_layout.addWidget(reader_btn)

        s_layout.addSpacing(8)
        transfer_label = QLabel(tr("companion.wifi_transfer"))
        transfer_label.setStyleSheet("font-weight: 500;")
        s_layout.addWidget(transfer_label)

        self.transfer_url_label = QLabel("")
        self.transfer_url_label.setStyleSheet(
            f"font-family: ui-monospace, Menlo, monospace; font-size: 12px; "
            f"color: {t.accent_300};"
        )
        self.transfer_url_label.setWordWrap(True)
        self.transfer_url_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        s_layout.addWidget(self.transfer_url_label)

        wifi_btn = QPushButton(tr("companion.wifi_transfer"))
        wifi_btn.setObjectName("secondary")
        wifi_btn.setFixedHeight(36)
        wifi_btn.clicked.connect(self._start_wifi_transfer)
        s_layout.addWidget(wifi_btn)

        s_layout.addStretch()
        tabs.addTab(sync_tab, "Sync")

        layout.addWidget(tabs, 1)

        self._refresh_devices()

    def _refresh_devices(self):
        self.devices_list.clear()
        devices = self._device_sync.get_devices()
        if not devices:
            item = QListWidgetItem(tr("companion.no_devices"))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.devices_list.addItem(item)
        else:
            for device in devices:
                sync_info = device.last_sync or tr("companion.never_synced")
                text = f"{device.name}  ({device.platform})  —  {sync_info}"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, device.device_id)
                self.devices_list.addItem(item)

    def _pair_new_device(self):
        name = self.device_name_input.text().strip()
        if not name:
            return
        import uuid
        device_id = str(uuid.uuid4())[:8]
        self._device_sync.pair_device(name, device_id)
        self.device_name_input.clear()
        self._refresh_devices()

    def _unpair_selected(self):
        item = self.devices_list.currentItem()
        if not item:
            return
        device_id = item.data(Qt.ItemDataRole.UserRole)
        if device_id:
            self._device_sync.unpair_device(device_id)
            self._refresh_devices()

    def _start_wifi_transfer(self):
        self.wifi_transfer_requested.emit("")

    def set_transfer_url(self, url: str):
        self.transfer_url_label.setText(url)

    def set_sync_status(self, status: str):
        self.sync_status_label.setText(status)

    def _on_sync_status_change(self, status):
        self.sync_status_label.setText(status.value)

    def get_device_sync(self) -> DeviceSync:
        return self._device_sync
