"""LAN discovery — find Écrit peers on the local network via UDP broadcast."""

from __future__ import annotations

import json
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


DISCOVERY_PORT = 8740
BROADCAST_INTERVAL = 3.0
SERVICE_ID = "ecrit-collab-v1"


@dataclass
class LANPeer:
    user_id: str
    user_name: str
    ip_address: str
    port: int
    project_title: str = ""
    last_seen: float = 0.0

    def is_stale(self, timeout: float = 10.0) -> bool:
        return (time.time() - self.last_seen) > timeout


class LANDiscovery:
    def __init__(self, user_id: str, user_name: str, port: int = 8741):
        self.user_id = user_id
        self.user_name = user_name
        self.port = port
        self._peers: dict[str, LANPeer] = {}
        self._running = False
        self._broadcast_thread: Optional[threading.Thread] = None
        self._listen_thread: Optional[threading.Thread] = None
        self._on_peer_found: Optional[Callable[[LANPeer], None]] = None
        self._on_peer_lost: Optional[Callable[[str], None]] = None
        self._project_title = ""

    def set_project_title(self, title: str) -> None:
        self._project_title = title

    def set_callbacks(
        self,
        on_peer_found: Optional[Callable[[LANPeer], None]] = None,
        on_peer_lost: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._on_peer_found = on_peer_found
        self._on_peer_lost = on_peer_lost

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._broadcast_thread.start()
        self._listen_thread.start()

    def stop(self) -> None:
        self._running = False
        self._peers.clear()

    def get_peers(self) -> list[LANPeer]:
        now = time.time()
        stale = [uid for uid, p in self._peers.items() if p.is_stale()]
        for uid in stale:
            del self._peers[uid]
            if self._on_peer_lost:
                self._on_peer_lost(uid)
        return list(self._peers.values())

    def _make_announce(self) -> bytes:
        payload = json.dumps({
            "service": SERVICE_ID,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "port": self.port,
            "project_title": self._project_title,
        })
        return payload.encode("utf-8")

    def _broadcast_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1.0)

        while self._running:
            try:
                data = self._make_announce()
                sock.sendto(data, ("<broadcast>", DISCOVERY_PORT))
            except OSError:
                pass
            time.sleep(BROADCAST_INTERVAL)

        sock.close()

    def _listen_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        try:
            sock.bind(("", DISCOVERY_PORT))
        except OSError:
            return

        while self._running:
            try:
                data, addr = sock.recvfrom(4096)
                payload = json.loads(data.decode("utf-8"))
                if payload.get("service") != SERVICE_ID:
                    continue
                uid = payload.get("user_id", "")
                if uid == self.user_id:
                    continue
                peer = LANPeer(
                    user_id=uid,
                    user_name=payload.get("user_name", ""),
                    ip_address=addr[0],
                    port=payload.get("port", 8741),
                    project_title=payload.get("project_title", ""),
                    last_seen=time.time(),
                )
                is_new = uid not in self._peers
                self._peers[uid] = peer
                if is_new and self._on_peer_found:
                    self._on_peer_found(peer)
            except (socket.timeout, json.JSONDecodeError, OSError):
                pass

        sock.close()
