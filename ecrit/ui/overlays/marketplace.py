"""Plugin Marketplace overlay — browse, search, install, and manage plugins."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QTabWidget,
    QWidget, QFrame, QComboBox, QFileDialog,
)
from PySide6.QtCore import Qt, Signal

from ecrit.ui.styles import theme
from ecrit.i18n import tr
from ecrit.plugins.marketplace import Marketplace, PluginListing, PluginCategory


class MarketplaceDialog(QDialog):
    plugin_installed = Signal(str)
    plugin_uninstalled = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("marketplace.title"))
        self.setMinimumSize(640, 500)
        self.setModal(True)

        self._marketplace = Marketplace()

        t = theme.current()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel(tr("marketplace.title"))
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        search_row = QHBoxLayout()
        search_row.setContentsMargins(24, 12, 24, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("marketplace.search"))
        self.search_input.setFixedHeight(34)
        self.search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self.search_input)

        self.category_combo = QComboBox()
        self.category_combo.addItem(tr("marketplace.categories"), "")
        for cat in PluginCategory:
            self.category_combo.addItem(cat.value.capitalize(), cat.value)
        self.category_combo.setFixedHeight(34)
        self.category_combo.currentIndexChanged.connect(self._on_search)
        search_row.addWidget(self.category_combo)
        layout.addLayout(search_row)

        tabs = QTabWidget()
        tabs.setContentsMargins(0, 0, 0, 0)

        self.installed_tab = QWidget()
        i_layout = QVBoxLayout(self.installed_tab)
        i_layout.setContentsMargins(16, 12, 16, 12)
        self.installed_list = QListWidget()
        self.installed_list.currentRowChanged.connect(self._on_installed_selected)
        i_layout.addWidget(self.installed_list)

        i_btn_row = QHBoxLayout()
        self.uninstall_btn = QPushButton(tr("marketplace.uninstall"))
        self.uninstall_btn.setObjectName("secondary")
        self.uninstall_btn.setFixedHeight(34)
        self.uninstall_btn.setEnabled(False)
        self.uninstall_btn.clicked.connect(self._uninstall_selected)
        i_btn_row.addWidget(self.uninstall_btn)
        i_btn_row.addStretch()
        i_layout.addLayout(i_btn_row)
        tabs.addTab(self.installed_tab, tr("marketplace.installed"))

        self.available_tab = QWidget()
        a_layout = QVBoxLayout(self.available_tab)
        a_layout.setContentsMargins(16, 12, 16, 12)
        self.available_list = QListWidget()
        self.available_list.currentRowChanged.connect(self._on_available_selected)
        a_layout.addWidget(self.available_list)

        a_btn_row = QHBoxLayout()
        self.install_btn = QPushButton(tr("marketplace.install"))
        self.install_btn.setObjectName("primary")
        self.install_btn.setFixedHeight(34)
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self._install_from_directory)
        a_btn_row.addWidget(self.install_btn)
        a_btn_row.addStretch()
        a_layout.addLayout(a_btn_row)
        tabs.addTab(self.available_tab, tr("marketplace.available"))

        layout.addWidget(tabs, 1)

        details = QFrame()
        details.setFixedHeight(100)
        details.setStyleSheet(
            f"QFrame {{ background: {t.neutral_100}; border-top: 1px solid {t.neutral_700}; }}"
        )
        d_layout = QVBoxLayout(details)
        d_layout.setContentsMargins(24, 8, 24, 8)
        self.detail_name = QLabel("—")
        self.detail_name.setStyleSheet("font-weight: 500; font-size: 14px;")
        d_layout.addWidget(self.detail_name)
        self.detail_info = QLabel("")
        self.detail_info.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        d_layout.addWidget(self.detail_info)
        self.detail_desc = QLabel("")
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setStyleSheet("font-size: 13px;")
        d_layout.addWidget(self.detail_desc)
        layout.addWidget(details)

        self._refresh()

    def _refresh(self):
        self._refresh_installed()
        self._refresh_available()

    def _refresh_installed(self):
        self.installed_list.clear()
        for plugin in self._marketplace.get_installed():
            text = f"{plugin.name}  v{plugin.version}  [{plugin.category.value}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, plugin.id)
            self.installed_list.addItem(item)
        if self.installed_list.count() == 0:
            item = QListWidgetItem(tr("marketplace.no_plugins"))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.installed_list.addItem(item)

    def _refresh_available(self):
        self.available_list.clear()
        for plugin in self._marketplace.get_registry():
            if not plugin.installed:
                text = f"{plugin.name}  v{plugin.version}  [{plugin.category.value}]"
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, plugin.id)
                self.available_list.addItem(item)

    def _on_search(self):
        query = self.search_input.text()
        cat_val = self.category_combo.currentData()
        category = PluginCategory(cat_val) if cat_val else None
        results = self._marketplace.search(query, category)

        self.available_list.clear()
        for plugin in results:
            status = " [installed]" if plugin.installed else ""
            text = f"{plugin.name}  v{plugin.version}  [{plugin.category.value}]{status}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, plugin.id)
            self.available_list.addItem(item)

    def _on_installed_selected(self, row):
        self.uninstall_btn.setEnabled(row >= 0)
        if row >= 0:
            item = self.installed_list.item(row)
            if item:
                pid = item.data(Qt.ItemDataRole.UserRole)
                self._show_details(pid)

    def _on_available_selected(self, row):
        self.install_btn.setEnabled(row >= 0)
        if row >= 0:
            item = self.available_list.item(row)
            if item:
                pid = item.data(Qt.ItemDataRole.UserRole)
                self._show_details(pid)

    def _show_details(self, plugin_id: str):
        installed = self._marketplace.get_installed()
        registry = self._marketplace.get_registry()
        all_plugins = {p.id: p for p in installed + registry}
        plugin = all_plugins.get(plugin_id)
        if plugin:
            self.detail_name.setText(plugin.name)
            self.detail_info.setText(
                f"v{plugin.version}  ·  {plugin.category.value}  ·  "
                f"{tr('marketplace.by_author', author=plugin.author) if plugin.author else ''}"
            )
            self.detail_desc.setText(plugin.description or tr("marketplace.no_plugins"))
        else:
            self.detail_name.setText("—")
            self.detail_info.setText("")
            self.detail_desc.setText("")

    def _install_from_directory(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Plugin Directory")
        if folder:
            result = self._marketplace.install_from_directory(folder)
            if result:
                self.plugin_installed.emit(result.id)
                self._refresh()

    def _uninstall_selected(self):
        item = self.installed_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid and self._marketplace.uninstall(pid):
            self.plugin_uninstalled.emit(pid)
            self._refresh()

    def get_marketplace(self) -> Marketplace:
        return self._marketplace
