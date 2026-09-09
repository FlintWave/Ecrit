"""P2P connection — TCP-based peer connection with connection tokens for remote collab."""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ConnectionToken:
    host: str
    port: int
    session_id: str
    user_name: str
    project_title: str = ""
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    def encode(self) -> str:
        payload = json.dumps({
            "h": self.host,
            "p": self.port,
            "s": self.session_id,
            "u": self.user_name,
            "t": self.project_title,
        })
        return base64.urlsafe_b64encode(payload.encode()).decode()

    @classmethod
    def decode(cls, token: str) -> Optional[ConnectionToken]:
        try:
            payload = json.loads(base64.urlsafe_b64decode(token.encode()))
            return cls(
                host=payload.get("h", ""),
                port=payload.get("p", 0),
                session_id=payload.get("s", ""),
                user_name=payload.get("u", ""),
                project_title=payload.get("t", ""),
            )
        except (json.JSONDecodeError, Exception):
            return None


class P2PConnection:
    def __init__(self, user_id: str, user_name: str):
        self.user_id = user_id
        self.user_name = user_name
        self._server_socket: Optional[socket.socket] = None
        self._clients: dict[str, socket.socket] = {}
        self._running = False
        self._listen_thread: Optional[threading.Thread] = None
        self._on_message: Optional[Callable[[str, str], None]] = None
        self._on_connect: Optional[Callable[[str], None]] = None
        self._on_disconnect: Optional[Callable[[str], None]] = None
        self._port = 0
        self._session_id = ""

    def set_callbacks(
        self,
        on_message: Optional[Callable[[str, str], None]] = None,
        on_connect: Optional[Callable[[str], None]] = None,
        on_disconnect: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._on_message = on_message
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect

    def host_session(self, port: int = 0, project_title: str = "") -> ConnectionToken:
        if self._running:
            self.close()

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(("0.0.0.0", port))
        self._server_socket.listen(8)
        self._server_socket.settimeout(1.0)
        self._port = self._server_socket.getsockname()[1]
        self._session_id = base64.urlsafe_b64encode(os.urandom(6)).decode()
        self._running = True

        self._listen_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._listen_thread.start()

        host_ip = self._get_public_ip()
        return ConnectionToken(
            host=host_ip,
            port=self._port,
            session_id=self._session_id,
            user_name=self.user_name,
            project_title=project_title,
        )

    def join_session(self, token: ConnectionToken) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((token.host, token.port))

            hello = json.dumps({
                "type": "hello",
                "user_id": self.user_id,
                "user_name": self.user_name,
                "session_id": token.session_id,
            })
            self._send_frame(sock, hello)
            self._clients["host"] = sock
            self._running = True

            recv_thread = threading.Thread(
                target=self._recv_loop, args=("host", sock), daemon=True
            )
            recv_thread.start()
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False

    def send(self, peer_id: str, message: str) -> bool:
        sock = self._clients.get(peer_id)
        if sock:
            try:
                self._send_frame(sock, message)
                return True
            except OSError:
                self._remove_peer(peer_id)
                return False
        return False

    def broadcast(self, message: str) -> None:
        dead = []
        for peer_id, sock in self._clients.items():
            try:
                self._send_frame(sock, message)
            except OSError:
                dead.append(peer_id)
        for pid in dead:
            self._remove_peer(pid)

    def close(self) -> None:
        self._running = False
        for sock in self._clients.values():
            try:
                sock.close()
            except OSError:
                pass
        self._clients.clear()
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

    def is_connected(self) -> bool:
        return self._running and len(self._clients) > 0

    def get_peer_count(self) -> int:
        return len(self._clients)

    def _send_frame(self, sock: socket.socket, data: str) -> None:
        encoded = data.encode("utf-8")
        header = struct.pack("!I", len(encoded))
        sock.sendall(header + encoded)

    def _recv_frame(self, sock: socket.socket) -> Optional[str]:
        header = b""
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            if not chunk:
                return None
            header += chunk
        length = struct.unpack("!I", header)[0]
        if length > 10 * 1024 * 1024:
            return None
        data = b""
        while len(data) < length:
            chunk = sock.recv(min(length - len(data), 65536))
            if not chunk:
                return None
            data += chunk
        return data.decode("utf-8")

    def _accept_loop(self) -> None:
        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
                client_sock.settimeout(30.0)
                frame = self._recv_frame(client_sock)
                if frame:
                    hello = json.loads(frame)
                    peer_id = hello.get("user_id", addr[0])
                    if hello.get("session_id") != self._session_id:
                        client_sock.close()
                        continue
                    self._clients[peer_id] = client_sock
                    if self._on_connect:
                        self._on_connect(peer_id)
                    recv_thread = threading.Thread(
                        target=self._recv_loop, args=(peer_id, client_sock), daemon=True
                    )
                    recv_thread.start()
            except socket.timeout:
                pass
            except OSError:
                if not self._running:
                    break

    def _recv_loop(self, peer_id: str, sock: socket.socket) -> None:
        while self._running:
            try:
                frame = self._recv_frame(sock)
                if frame is None:
                    break
                if self._on_message:
                    self._on_message(peer_id, frame)
            except (socket.timeout, OSError):
                break
        self._remove_peer(peer_id)

    def _remove_peer(self, peer_id: str) -> None:
        sock = self._clients.pop(peer_id, None)
        if sock:
            try:
                sock.close()
            except OSError:
                pass
        if self._on_disconnect:
            self._on_disconnect(peer_id)

    def _get_public_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"
