"""Cloud drive export scaffolding for Ecrit.

Provides an abstraction layer for exporting screenplays to cloud storage
providers (Google Drive, iCloud, Dropbox, OneDrive, Nextcloud). Each
provider has a stub implementation that returns placeholder results;
swap in real API calls once credentials and SDKs are available.
"""

from __future__ import annotations

import base64
import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import ClassVar


# ---------------------------------------------------------------------------
# Enums and data classes
# ---------------------------------------------------------------------------

class CloudProvider(Enum):
    """Supported cloud storage providers."""

    GOOGLE_DRIVE = "google_drive"
    ICLOUD = "icloud"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    NEXTCLOUD = "nextcloud"


@dataclass
class CloudConfig:
    """Per-provider configuration stored in a project's .ecrit/cloud.json."""

    provider: CloudProvider
    auth_token: str
    folder_path: str
    auto_export: bool = False
    last_export_time: str = ""

    # -- serialisation helpers ------------------------------------------------

    def to_dict(self) -> dict:
        token_b64 = base64.b64encode(self.auth_token.encode("utf-8")).decode("ascii") if self.auth_token else ""
        return {
            "provider": self.provider.value,
            "auth_token_b64": token_b64,
            "folder_path": self.folder_path,
            "auto_export": self.auto_export,
            "last_export_time": self.last_export_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CloudConfig:
        token_b64 = data.get("auth_token_b64", "")
        if token_b64:
            auth_token = base64.b64decode(token_b64.encode("ascii")).decode("utf-8")
        else:
            auth_token = data.get("auth_token", "")
        return cls(
            provider=CloudProvider(data["provider"]),
            auth_token=auth_token,
            folder_path=data.get("folder_path", "/"),
            auto_export=data.get("auto_export", False),
            last_export_time=data.get("last_export_time", ""),
        )


@dataclass
class ExportResult:
    """Outcome of a single cloud export attempt."""

    success: bool
    message: str
    remote_url: str = ""


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class CloudExporter(ABC):
    """Interface every cloud-provider exporter must implement."""

    PROVIDER_NAME: ClassVar[str] = ""
    AUTH_URL: ClassVar[str] = ""

    def __init__(self, config: CloudConfig) -> None:
        self.config = config
        self._authenticated = False

    @abstractmethod
    def authenticate(self) -> bool:
        """Attempt to authenticate with the provider.  Returns True on success."""
        ...

    @abstractmethod
    def upload_file(self, local_path: str, remote_folder: str) -> ExportResult:
        """Upload *local_path* into *remote_folder* on the provider."""
        ...

    @abstractmethod
    def list_files(self, remote_folder: str) -> list[dict]:
        """Return a list of file metadata dicts in *remote_folder*."""
        ...

    def is_authenticated(self) -> bool:
        """Whether the exporter currently holds a valid session."""
        return self._authenticated


# ---------------------------------------------------------------------------
# Concrete stub implementations
# ---------------------------------------------------------------------------

class GoogleDriveExporter(CloudExporter):
    PROVIDER_NAME = "Google Drive"
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

    def authenticate(self) -> bool:
        if self.config.auth_token:
            self._authenticated = True
            return True
        self._authenticated = False
        return False

    def upload_file(self, local_path: str, remote_folder: str) -> ExportResult:
        if not self._authenticated:
            return ExportResult(False, "Not authenticated with Google Drive")
        filename = os.path.basename(local_path)
        url = f"https://drive.google.com/file/d/stub-id/{filename}"
        return ExportResult(True, f"Uploaded {filename} to Google Drive", url)

    def list_files(self, remote_folder: str) -> list[dict]:
        if not self._authenticated:
            return []
        return [
            {"name": "example_script.fountain", "id": "stub-1", "size": 24000},
            {"name": "example_script.pdf", "id": "stub-2", "size": 180000},
        ]


class ICloudExporter(CloudExporter):
    PROVIDER_NAME = "iCloud Drive"
    AUTH_URL = "https://appleid.apple.com/auth/authorize"

    def authenticate(self) -> bool:
        if self.config.auth_token:
            self._authenticated = True
            return True
        self._authenticated = False
        return False

    def upload_file(self, local_path: str, remote_folder: str) -> ExportResult:
        if not self._authenticated:
            return ExportResult(False, "Not authenticated with iCloud Drive")
        filename = os.path.basename(local_path)
        return ExportResult(
            True,
            f"Uploaded {filename} to iCloud Drive",
            f"icloud://stub/{remote_folder}/{filename}",
        )

    def list_files(self, remote_folder: str) -> list[dict]:
        if not self._authenticated:
            return []
        return [
            {"name": "example_script.fountain", "type": "file", "size": 24000},
        ]


class DropboxExporter(CloudExporter):
    PROVIDER_NAME = "Dropbox"
    AUTH_URL = "https://www.dropbox.com/oauth2/authorize"

    def authenticate(self) -> bool:
        if self.config.auth_token:
            self._authenticated = True
            return True
        self._authenticated = False
        return False

    def upload_file(self, local_path: str, remote_folder: str) -> ExportResult:
        if not self._authenticated:
            return ExportResult(False, "Not authenticated with Dropbox")
        filename = os.path.basename(local_path)
        url = f"https://www.dropbox.com/home{remote_folder}/{filename}"
        return ExportResult(True, f"Uploaded {filename} to Dropbox", url)

    def list_files(self, remote_folder: str) -> list[dict]:
        if not self._authenticated:
            return []
        return [
            {"name": "example_script.fountain", "path": f"{remote_folder}/example_script.fountain", "size": 24000},
        ]


class OneDriveExporter(CloudExporter):
    PROVIDER_NAME = "OneDrive"
    AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"

    def authenticate(self) -> bool:
        if self.config.auth_token:
            self._authenticated = True
            return True
        self._authenticated = False
        return False

    def upload_file(self, local_path: str, remote_folder: str) -> ExportResult:
        if not self._authenticated:
            return ExportResult(False, "Not authenticated with OneDrive")
        filename = os.path.basename(local_path)
        url = f"https://onedrive.live.com/stub/{remote_folder}/{filename}"
        return ExportResult(True, f"Uploaded {filename} to OneDrive", url)

    def list_files(self, remote_folder: str) -> list[dict]:
        if not self._authenticated:
            return []
        return [
            {"name": "example_script.fountain", "id": "stub-onedrive-1", "size": 24000},
        ]


class NextcloudExporter(CloudExporter):
    PROVIDER_NAME = "Nextcloud"
    AUTH_URL = "https://cloud.example.com/index.php/apps/oauth2/authorize"

    def authenticate(self) -> bool:
        if self.config.auth_token:
            self._authenticated = True
            return True
        self._authenticated = False
        return False

    def upload_file(self, local_path: str, remote_folder: str) -> ExportResult:
        if not self._authenticated:
            return ExportResult(False, "Not authenticated with Nextcloud")
        filename = os.path.basename(local_path)
        url = f"https://cloud.example.com/remote.php/dav/files/user{remote_folder}/{filename}"
        return ExportResult(True, f"Uploaded {filename} to Nextcloud", url)

    def list_files(self, remote_folder: str) -> list[dict]:
        if not self._authenticated:
            return []
        return [
            {"name": "example_script.fountain", "href": f"{remote_folder}/example_script.fountain", "size": 24000},
        ]


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_EXPORTERS: dict[CloudProvider, type[CloudExporter]] = {
    CloudProvider.GOOGLE_DRIVE: GoogleDriveExporter,
    CloudProvider.ICLOUD: ICloudExporter,
    CloudProvider.DROPBOX: DropboxExporter,
    CloudProvider.ONEDRIVE: OneDriveExporter,
    CloudProvider.NEXTCLOUD: NextcloudExporter,
}


def get_exporter(provider: CloudProvider, config: CloudConfig | None = None) -> CloudExporter:
    """Return an exporter instance for *provider*.

    If *config* is ``None`` a default (empty-token) config is created so the
    caller can still inspect ``PROVIDER_NAME`` / ``AUTH_URL`` etc.
    """
    exporter_cls = _EXPORTERS.get(provider)
    if exporter_cls is None:
        raise ValueError(f"Unsupported cloud provider: {provider}")
    if config is None:
        config = CloudConfig(provider=provider, auth_token="", folder_path="/")
    return exporter_cls(config)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def export_script(
    project_path: str,
    provider: CloudProvider,
    content: str,
    filename: str,
    fmt: str = "fountain",
) -> ExportResult:
    """Export a screenplay to a cloud provider.

    1. Writes *content* to a temporary local file inside the project's
       ``.ecrit/`` directory.
    2. Loads the matching :class:`CloudConfig` (if any) from the project.
    3. Authenticates and uploads via the provider's exporter.

    Parameters
    ----------
    project_path:
        Root directory of the Ecrit project.
    provider:
        Target cloud provider.
    content:
        The screenplay text to export.
    filename:
        Desired remote filename (without extension unless already present).
    fmt:
        Export format hint (e.g. ``"fountain"``, ``"pdf"``).  Used to pick the
        file extension when *filename* lacks one.
    """
    configs = load_cloud_configs(project_path)
    config = next((c for c in configs if c.provider == provider), None)
    if config is None:
        return ExportResult(False, f"No configuration found for {provider.value}")

    exporter = get_exporter(provider, config)
    if not exporter.authenticate():
        return ExportResult(False, f"Authentication failed for {exporter.PROVIDER_NAME}")

    # Sanitize filename to prevent path traversal
    filename = os.path.basename(filename)
    if not filename:
        filename = "export"

    # Ensure the filename has an extension
    if "." not in filename:
        filename = f"{filename}.{fmt}"

    # Write content to a staging file
    staging_dir = os.path.join(project_path, ".ecrit", "staging")
    os.makedirs(staging_dir, exist_ok=True)
    local_path = os.path.join(staging_dir, filename)
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(content)

    try:
        result = exporter.upload_file(local_path, config.folder_path)
    finally:
        try:
            os.remove(local_path)
        except OSError:
            pass

    return result


# ---------------------------------------------------------------------------
# Config persistence  (.ecrit/cloud.json)
# ---------------------------------------------------------------------------

def _cloud_config_path(project_path: str) -> str:
    return os.path.join(project_path, ".ecrit", "cloud.json")


def save_cloud_configs(project_path: str, configs: list[CloudConfig]) -> None:
    """Persist *configs* to ``.ecrit/cloud.json`` inside *project_path*."""
    path = _cloud_config_path(project_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in configs], f, indent=2)


def load_cloud_configs(project_path: str) -> list[CloudConfig]:
    """Load cloud configs from ``.ecrit/cloud.json``, or return ``[]``."""
    path = _cloud_config_path(project_path)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [CloudConfig.from_dict(entry) for entry in data]
