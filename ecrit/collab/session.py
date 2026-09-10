"""Collaboration session — orchestrates LAN discovery, P2P connection, and CRDT editing."""

from __future__ import annotations

import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Optional

from ecrit.collab.protocol import CollabMessage, MessageType, Operation
from ecrit.collab.crdt import TextCRDT
from ecrit.collab.lan import LANDiscovery, LANPeer
from ecrit.collab.p2p import P2PConnection, ConnectionToken


class CollabRole(str, Enum):
    HOST = "host"
    GUEST = "guest"


class SessionState(str, Enum):
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"


@dataclass
class Participant:
    user_id: str
    user_name: str
    cursor_position: int = 0
    selection_end: int = -1
    color: str = "#4FC3F7"


_PEER_COLORS = [
    "#4FC3F7", "#81C784", "#FFB74D", "#E57373",
    "#BA68C8", "#4DD0E1", "#AED581", "#FF8A65",
]


class CollabSession:
    def __init__(self, user_name: str = ""):
        self.user_id = str(uuid.uuid4())[:8]
        self.user_name = user_name or f"User-{self.user_id[:4]}"
        self.role = CollabRole.GUEST
        self.state = SessionState.DISCONNECTED
        self.project_title = ""

        self._crdt = TextCRDT(user_id=self.user_id)
        self._lan = LANDiscovery(self.user_id, self.user_name)
        self._p2p = P2PConnection(self.user_id, self.user_name)
        self._participants: dict[str, Participant] = {}
        self._pending_ops: list = []
        self._color_index = 0

        self._on_state_change: Optional[Callable[[SessionState], None]] = None
        self._on_text_change: Optional[Callable[[str], None]] = None
        self._on_participant_change: Optional[Callable[[], None]] = None
        self._on_cursor_change: Optional[Callable[[str, int, int], None]] = None

        self._p2p.set_callbacks(
            on_message=self._handle_message,
            on_connect=self._handle_connect,
            on_disconnect=self._handle_disconnect,
        )

    def set_callbacks(
        self,
        on_state_change: Optional[Callable] = None,
        on_text_change: Optional[Callable] = None,
        on_participant_change: Optional[Callable] = None,
        on_cursor_change: Optional[Callable] = None,
    ) -> None:
        self._on_state_change = on_state_change
        self._on_text_change = on_text_change
        self._on_participant_change = on_participant_change
        self._on_cursor_change = on_cursor_change

    def _set_state(self, state: SessionState) -> None:
        self.state = state
        if self._on_state_change:
            self._on_state_change(state)

    def _next_color(self) -> str:
        color = _PEER_COLORS[self._color_index % len(_PEER_COLORS)]
        self._color_index += 1
        return color

    # ── Host methods ──

    def host(self, content: str, project_title: str = "", port: int = 0) -> ConnectionToken:
        self.role = CollabRole.HOST
        self.project_title = project_title
        self._crdt.set_text(content)

        self._participants[self.user_id] = Participant(
            user_id=self.user_id,
            user_name=self.user_name,
            color=self._next_color(),
        )

        token = self._p2p.host_session(port=port, project_title=project_title)
        self._lan.set_project_title(project_title)
        self._lan.start()
        self._set_state(SessionState.CONNECTED)
        return token

    def join_lan(self, peer: LANPeer) -> bool:
        self.role = CollabRole.GUEST
        token = ConnectionToken(
            host=peer.ip_address,
            port=peer.port,
            session_id="",
            user_name=peer.user_name,
            project_title=peer.project_title,
        )
        return self._join(token)

    def join_token(self, token_str: str) -> bool:
        self.role = CollabRole.GUEST
        token = ConnectionToken.decode(token_str)
        if not token:
            return False
        return self._join(token)

    def _join(self, token: ConnectionToken) -> bool:
        self._set_state(SessionState.CONNECTING)
        self._participants[self.user_id] = Participant(
            user_id=self.user_id,
            user_name=self.user_name,
            color=self._next_color(),
        )

        success = self._p2p.join_session(token)
        if success:
            join_msg = CollabMessage.join(self.user_id, self.user_name)
            self._p2p.send("host", join_msg.to_json())

            sync_msg = CollabMessage.sync_request(self.user_id)
            self._p2p.send("host", sync_msg.to_json())

            self._set_state(SessionState.CONNECTED)
        else:
            self._set_state(SessionState.DISCONNECTED)
        return success

    def leave(self) -> None:
        if self.state == SessionState.CONNECTED:
            leave_msg = CollabMessage.leave(self.user_id)
            self._p2p.broadcast(leave_msg.to_json())

        self._p2p.close()
        self._lan.stop()
        self._participants.clear()
        self._set_state(SessionState.DISCONNECTED)

    # ── Editing methods ──

    def apply_local_insert(self, position: int, text: str) -> None:
        op = self._crdt.insert(position, text)
        self._pending_ops.append(op)
        msg = CollabMessage.operation(self.user_id, op)
        self._p2p.broadcast(msg.to_json())

    def apply_local_delete(self, position: int, length: int) -> None:
        op = self._crdt.delete(position, length)
        self._pending_ops.append(op)
        msg = CollabMessage.operation(self.user_id, op)
        self._p2p.broadcast(msg.to_json())

    def update_cursor(self, position: int, selection_end: int = -1) -> None:
        if self.user_id in self._participants:
            self._participants[self.user_id].cursor_position = position
            self._participants[self.user_id].selection_end = selection_end
        msg = CollabMessage.cursor_update(self.user_id, position, selection_end)
        self._p2p.broadcast(msg.to_json())

    def get_text(self) -> str:
        return self._crdt.get_text()

    def get_participants(self) -> list[Participant]:
        return list(self._participants.values())

    # ── LAN scanning ──

    def start_lan_scan(self) -> None:
        self._lan.start()
        self._set_state(SessionState.SCANNING)

    def stop_lan_scan(self) -> None:
        self._lan.stop()
        if self.state == SessionState.SCANNING:
            self._set_state(SessionState.DISCONNECTED)

    def get_lan_peers(self) -> list[LANPeer]:
        return self._lan.get_peers()

    # ── Message handling ──

    def _handle_message(self, peer_id: str, raw: str) -> None:
        try:
            msg = CollabMessage.from_json(raw)
        except Exception:
            return

        if msg.msg_type == MessageType.JOIN:
            self._participants[msg.user_id] = Participant(
                user_id=msg.user_id,
                user_name=msg.user_name,
                color=self._next_color(),
            )
            if self._on_participant_change:
                self._on_participant_change()

        elif msg.msg_type == MessageType.LEAVE:
            self._participants.pop(msg.user_id, None)
            if self._on_participant_change:
                self._on_participant_change()

        elif msg.msg_type == MessageType.OPERATION:
            op = Operation.from_dict(msg.payload)
            for pending in self._pending_ops:
                op = self._crdt.transform(op, pending)
            self._pending_ops.clear()
            self._crdt.apply_operation(op)
            if self._on_text_change:
                self._on_text_change(self._crdt.get_text())
            if self.role == CollabRole.HOST:
                for pid in self._p2p._clients:
                    if pid != peer_id:
                        self._p2p.send(pid, raw)

        elif msg.msg_type == MessageType.CURSOR_UPDATE:
            p = self._participants.get(msg.user_id)
            if p:
                p.cursor_position = msg.payload.get("position", 0)
                p.selection_end = msg.payload.get("selection_end", -1)
            if self._on_cursor_change:
                self._on_cursor_change(
                    msg.user_id,
                    msg.payload.get("position", 0),
                    msg.payload.get("selection_end", -1),
                )
            if self.role == CollabRole.HOST:
                for pid in self._p2p._clients:
                    if pid != peer_id:
                        self._p2p.send(pid, raw)

        elif msg.msg_type == MessageType.SYNC_REQUEST:
            if self.role == CollabRole.HOST:
                resp = CollabMessage.sync_response(
                    self.user_id, self._crdt.get_text(), self._crdt.revision
                )
                self._p2p.send(peer_id, resp.to_json())

        elif msg.msg_type == MessageType.SYNC_RESPONSE:
            content = msg.payload.get("content", "")
            self._crdt.set_text(content)
            if self._on_text_change:
                self._on_text_change(content)

    def _handle_connect(self, peer_id: str) -> None:
        if self._on_participant_change:
            self._on_participant_change()

    def _handle_disconnect(self, peer_id: str) -> None:
        self._participants.pop(peer_id, None)
        if self._on_participant_change:
            self._on_participant_change()
