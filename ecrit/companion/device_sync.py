"""Device sync — pair, discover, and transfer bundles over Wi-Fi."""

from __future__ import annotations

import json
import os
import socket
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Callable


class SyncStatus(str, Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    TRANSFERRING = "transferring"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class PairedDevice:
    name: str
    device_id: str
    last_sync: str = ""
    ip_address: str = ""
    platform: str = "android"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PairedDevice:
        return cls(
            name=data.get("name", ""),
            device_id=data.get("device_id", ""),
            last_sync=data.get("last_sync", ""),
            ip_address=data.get("ip_address", ""),
            platform=data.get("platform", "android"),
        )


class _TransferHandler(BaseHTTPRequestHandler):
    bundle_path: str = ""

    def do_GET(self):
        if self.path == "/bundle" and self.bundle_path and os.path.exists(self.bundle_path):
            with open(self.bundle_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/info":
            info = json.dumps({"app": "ecrit", "version": "1.0"})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(info.encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


class DeviceSync:
    def __init__(self, config_dir: str = ""):
        if not config_dir:
            config_dir = str(Path.home() / ".ecrit" / "companion")
        self.config_dir = config_dir
        self._devices: list[PairedDevice] = []
        self._status = SyncStatus.IDLE
        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._on_status_change: Optional[Callable] = None
        self._load_devices()

    def _load_devices(self) -> None:
        path = os.path.join(self.config_dir, "devices.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._devices = [PairedDevice.from_dict(d) for d in data]
            except (json.JSONDecodeError, OSError):
                pass

    def _save_devices(self) -> None:
        os.makedirs(self.config_dir, exist_ok=True)
        path = os.path.join(self.config_dir, "devices.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([d.to_dict() for d in self._devices], f, indent=2)

    def get_devices(self) -> list[PairedDevice]:
        return list(self._devices)

    def pair_device(self, name: str, device_id: str, ip_address: str = "") -> PairedDevice:
        for d in self._devices:
            if d.device_id == device_id:
                d.name = name
                d.ip_address = ip_address
                self._save_devices()
                return d
        device = PairedDevice(name=name, device_id=device_id, ip_address=ip_address)
        self._devices.append(device)
        self._save_devices()
        return device

    def unpair_device(self, device_id: str) -> bool:
        before = len(self._devices)
        self._devices = [d for d in self._devices if d.device_id != device_id]
        if len(self._devices) < before:
            self._save_devices()
            return True
        return False

    def get_status(self) -> SyncStatus:
        return self._status

    def set_status_callback(self, callback: Callable) -> None:
        self._on_status_change = callback

    def _set_status(self, status: SyncStatus) -> None:
        self._status = status
        if self._on_status_change:
            self._on_status_change(status)

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"

    def start_transfer_server(self, bundle_path: str, port: int = 8739) -> str:
        if self._server:
            self.stop_transfer_server()

        _TransferHandler.bundle_path = bundle_path
        self._server = HTTPServer(("0.0.0.0", port), _TransferHandler)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()
        self._set_status(SyncStatus.TRANSFERRING)

        ip = self.get_local_ip()
        return f"http://{ip}:{port}/bundle"

    def stop_transfer_server(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
            self._server_thread = None
            self._set_status(SyncStatus.IDLE)

    def mark_synced(self, device_id: str) -> None:
        for d in self._devices:
            if d.device_id == device_id:
                d.last_sync = datetime.now().isoformat()
                self._save_devices()
                break

    def generate_pairing_payload(self) -> dict:
        ip = self.get_local_ip()
        hostname = socket.gethostname()
        return {
            "app": "ecrit",
            "version": "1.0",
            "host": hostname,
            "ip": ip,
            "port": 8739,
        }
