"""Collaboration overlay — start/join sessions via LAN or P2P token."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QTabWidget,
    QWidget, QFrame, QTextEdit,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QGuiApplication

from ecrit.ui.styles import theme
from ecrit.i18n import tr
from ecrit.collab.session import CollabSession, SessionState, CollabRole
from ecrit.collab.p2p import ConnectionToken


class CollaborationDialog(QDialog):
    session_started = Signal(object)
    session_joined = Signal(object)
    session_left = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("collab.title"))
        self.setMinimumSize(520, 460)
        self.setModal(True)

        self._session: CollabSession | None = None
        t = theme.current()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(24, 20, 24, 0)
        title = QLabel(tr("collab.title"))
        title.setStyleSheet("font-size: 20px; font-weight: 500;")
        header.addWidget(title)
        header.addStretch()

        self.status_label = QLabel(tr("collab.disconnected"))
        self.status_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 13px;")
        header.addWidget(self.status_label)

        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        tabs = QTabWidget()

        # LAN tab
        lan_tab = QWidget()
        l_layout = QVBoxLayout(lan_tab)
        l_layout.setContentsMargins(16, 12, 16, 12)
        l_layout.setSpacing(12)

        l_layout.addWidget(QLabel(tr("collab.lan_discovery")))

        self.peers_list = QListWidget()
        self.peers_list.setFixedHeight(160)
        l_layout.addWidget(self.peers_list)

        scan_row = QHBoxLayout()
        self.scan_btn = QPushButton(tr("collab.scanning"))
        self.scan_btn.setObjectName("secondary")
        self.scan_btn.setFixedHeight(34)
        self.scan_btn.clicked.connect(self._toggle_scan)
        scan_row.addWidget(self.scan_btn)

        self.join_lan_btn = QPushButton(tr("collab.join_session"))
        self.join_lan_btn.setObjectName("primary")
        self.join_lan_btn.setFixedHeight(34)
        self.join_lan_btn.setEnabled(False)
        self.join_lan_btn.clicked.connect(self._join_lan_peer)
        scan_row.addWidget(self.join_lan_btn)
        l_layout.addLayout(scan_row)

        self.peer_count_label = QLabel(tr("collab.no_peers"))
        self.peer_count_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        l_layout.addWidget(self.peer_count_label)

        l_layout.addStretch()
        tabs.addTab(lan_tab, tr("collab.lan_discovery"))

        # P2P tab
        p2p_tab = QWidget()
        p_layout = QVBoxLayout(p2p_tab)
        p_layout.setContentsMargins(16, 12, 16, 12)
        p_layout.setSpacing(12)

        p_layout.addWidget(QLabel(tr("collab.remote_p2p")))

        host_frame = QFrame()
        host_frame.setStyleSheet(
            f"QFrame {{ background: {t.neutral_100}; border-radius: 8px; padding: 12px; }}"
        )
        h_layout = QVBoxLayout(host_frame)
        h_layout.setSpacing(8)
        h_layout.addWidget(QLabel(tr("collab.host")))

        self.token_display = QTextEdit()
        self.token_display.setReadOnly(True)
        self.token_display.setFixedHeight(60)
        self.token_display.setStyleSheet(
            f"font-family: ui-monospace, Menlo, monospace; font-size: 11px; "
            f"background: {t.bg}; border: 1px solid {t.neutral_700}; border-radius: 4px;"
        )
        self.token_display.setPlaceholderText(tr("collab.connection_token"))
        h_layout.addWidget(self.token_display)

        host_btn_row = QHBoxLayout()
        self.start_btn = QPushButton(tr("collab.start_session"))
        self.start_btn.setObjectName("primary")
        self.start_btn.setFixedHeight(34)
        self.start_btn.clicked.connect(self._start_host)
        host_btn_row.addWidget(self.start_btn)

        self.copy_token_btn = QPushButton(tr("collab.copy_token"))
        self.copy_token_btn.setObjectName("secondary")
        self.copy_token_btn.setFixedHeight(34)
        self.copy_token_btn.setEnabled(False)
        self.copy_token_btn.clicked.connect(self._copy_token)
        host_btn_row.addWidget(self.copy_token_btn)
        h_layout.addLayout(host_btn_row)
        p_layout.addWidget(host_frame)

        join_frame = QFrame()
        join_frame.setStyleSheet(
            f"QFrame {{ background: {t.neutral_100}; border-radius: 8px; padding: 12px; }}"
        )
        j_layout = QVBoxLayout(join_frame)
        j_layout.setSpacing(8)
        j_layout.addWidget(QLabel(tr("collab.guest")))

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText(tr("collab.paste_token"))
        self.token_input.setFixedHeight(34)
        j_layout.addWidget(self.token_input)

        self.join_btn = QPushButton(tr("collab.join_session"))
        self.join_btn.setObjectName("primary")
        self.join_btn.setFixedHeight(34)
        self.join_btn.clicked.connect(self._join_with_token)
        j_layout.addWidget(self.join_btn)
        p_layout.addWidget(join_frame)

        p_layout.addStretch()
        tabs.addTab(p2p_tab, tr("collab.remote_p2p"))

        layout.addWidget(tabs, 1)

        leave_row = QHBoxLayout()
        leave_row.setContentsMargins(16, 8, 16, 12)
        self.leave_btn = QPushButton(tr("collab.leave_session"))
        self.leave_btn.setObjectName("secondary")
        self.leave_btn.setFixedHeight(36)
        self.leave_btn.setEnabled(False)
        self.leave_btn.clicked.connect(self._leave_session)
        leave_row.addWidget(self.leave_btn)
        leave_row.addStretch()

        self.participants_label = QLabel("")
        self.participants_label.setStyleSheet(f"color: {t.neutral_500}; font-size: 12px;")
        leave_row.addWidget(self.participants_label)
        layout.addLayout(leave_row)

        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(2000)
        self._scan_timer.timeout.connect(self._refresh_peers)
        self._scanning = False
        self._token = ""

    def set_session(self, session: CollabSession) -> None:
        self._session = session

    def _toggle_scan(self):
        if not self._session:
            return
        if self._scanning:
            self._session.stop_lan_scan()
            self._scan_timer.stop()
            self._scanning = False
            self.scan_btn.setText(tr("collab.scanning"))
        else:
            self._session.start_lan_scan()
            self._scan_timer.start()
            self._scanning = True
            self.scan_btn.setText("Stop Scan")

    def _refresh_peers(self):
        if not self._session:
            return
        peers = self._session.get_lan_peers()
        self.peers_list.clear()
        for peer in peers:
            text = f"{peer.user_name}  ({peer.ip_address})  —  {peer.project_title}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, peer)
            self.peers_list.addItem(item)

        count = len(peers)
        if count > 0:
            self.peer_count_label.setText(tr("collab.peers_found", count=count))
            self.join_lan_btn.setEnabled(True)
        else:
            self.peer_count_label.setText(tr("collab.no_peers"))
            self.join_lan_btn.setEnabled(False)

    def _join_lan_peer(self):
        if not self._session:
            return
        item = self.peers_list.currentItem()
        if not item:
            return
        peer = item.data(Qt.ItemDataRole.UserRole)
        if peer and self._session.join_lan(peer):
            self._on_connected()
            self.session_joined.emit(self._session)

    def _start_host(self):
        if not self._session:
            return
        token = self._session.host(content="", project_title="")
        self._token = token.encode()
        self.token_display.setText(self._token)
        self.copy_token_btn.setEnabled(True)
        self._on_connected()
        self.session_started.emit(self._session)

    def _copy_token(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard and self._token:
            clipboard.setText(self._token)

    def _join_with_token(self):
        if not self._session:
            return
        token_str = self.token_input.text().strip()
        if not token_str:
            return
        if self._session.join_token(token_str):
            self._on_connected()
            self.session_joined.emit(self._session)

    def _on_connected(self):
        self.status_label.setText(tr("collab.connected"))
        self.leave_btn.setEnabled(True)
        self.start_btn.setEnabled(False)
        self.join_btn.setEnabled(False)

    def _leave_session(self):
        if self._session:
            self._session.leave()
        self.status_label.setText(tr("collab.disconnected"))
        self.leave_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.join_btn.setEnabled(True)
        self.copy_token_btn.setEnabled(False)
        self.token_display.clear()
        self.participants_label.setText("")
        self._token = ""
        self.session_left.emit()

    def update_participants(self, count: int):
        self.participants_label.setText(tr("collab.users_editing", count=count))
