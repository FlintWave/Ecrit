"""Tests for cloud export stubs and config persistence."""

import base64
import json
import os
import pytest

from ecrit.sync.cloud_export import (
    CloudProvider, CloudConfig, ExportResult,
    GoogleDriveExporter, ICloudExporter, DropboxExporter,
    OneDriveExporter, NextcloudExporter,
    get_exporter, export_script,
    save_cloud_configs, load_cloud_configs,
)


class TestCloudConfig:
    def test_to_dict_roundtrip(self):
        config = CloudConfig(
            provider=CloudProvider.GOOGLE_DRIVE,
            auth_token="secret-token",
            folder_path="/scripts",
            auto_export=True,
            last_export_time="2026-01-01T00:00:00",
        )
        d = config.to_dict()
        restored = CloudConfig.from_dict(d)
        assert restored.provider == CloudProvider.GOOGLE_DRIVE
        assert restored.auth_token == "secret-token"
        assert restored.folder_path == "/scripts"
        assert restored.auto_export is True
        assert restored.last_export_time == "2026-01-01T00:00:00"

    def test_to_dict_base64_encodes_token(self):
        config = CloudConfig(
            provider=CloudProvider.DROPBOX, auth_token="my-token", folder_path="/",
        )
        d = config.to_dict()
        assert "auth_token" not in d
        decoded = base64.b64decode(d["auth_token_b64"]).decode("utf-8")
        assert decoded == "my-token"

    def test_from_dict_empty_token(self):
        config = CloudConfig.from_dict({
            "provider": "dropbox", "auth_token_b64": "", "folder_path": "/",
        })
        assert config.auth_token == ""

    def test_from_dict_defaults(self):
        config = CloudConfig.from_dict({"provider": "icloud"})
        assert config.folder_path == "/"
        assert config.auto_export is False


class TestStubExporters:
    @pytest.mark.parametrize("cls,name", [
        (GoogleDriveExporter, "Google Drive"),
        (ICloudExporter, "iCloud Drive"),
        (DropboxExporter, "Dropbox"),
        (OneDriveExporter, "OneDrive"),
        (NextcloudExporter, "Nextcloud"),
    ])
    def test_authenticate_returns_false(self, cls, name):
        config = CloudConfig(
            provider=CloudProvider.GOOGLE_DRIVE, auth_token="tok", folder_path="/",
        )
        exporter = cls(config)
        assert exporter.authenticate() is False
        assert exporter.PROVIDER_NAME == name

    @pytest.mark.parametrize("cls", [
        GoogleDriveExporter, ICloudExporter, DropboxExporter,
        OneDriveExporter, NextcloudExporter,
    ])
    def test_upload_returns_failure(self, cls):
        config = CloudConfig(
            provider=CloudProvider.GOOGLE_DRIVE, auth_token="", folder_path="/",
        )
        exporter = cls(config)
        result = exporter.upload_file("/fake/path.fountain", "/remote")
        assert result.success is False
        assert "not yet available" in result.message

    @pytest.mark.parametrize("cls", [
        GoogleDriveExporter, ICloudExporter, DropboxExporter,
        OneDriveExporter, NextcloudExporter,
    ])
    def test_list_files_returns_empty(self, cls):
        config = CloudConfig(
            provider=CloudProvider.GOOGLE_DRIVE, auth_token="", folder_path="/",
        )
        exporter = cls(config)
        assert exporter.list_files("/") == []

    def test_is_authenticated_default_false(self):
        config = CloudConfig(
            provider=CloudProvider.DROPBOX, auth_token="", folder_path="/",
        )
        exporter = DropboxExporter(config)
        assert exporter.is_authenticated() is False


class TestGetExporter:
    def test_returns_correct_type(self):
        exporter = get_exporter(CloudProvider.GOOGLE_DRIVE)
        assert isinstance(exporter, GoogleDriveExporter)

    def test_with_config(self):
        config = CloudConfig(
            provider=CloudProvider.DROPBOX, auth_token="t", folder_path="/x",
        )
        exporter = get_exporter(CloudProvider.DROPBOX, config)
        assert exporter.config.folder_path == "/x"

    def test_unsupported_provider_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_exporter("not_a_provider")


class TestExportScript:
    def test_no_config_returns_failure(self, tmp_path):
        result = export_script(
            str(tmp_path), CloudProvider.GOOGLE_DRIVE,
            "INT. OFFICE", "script",
        )
        assert result.success is False
        assert "No configuration" in result.message

    def test_auth_failure_returns_failure(self, tmp_path):
        ecrit_dir = tmp_path / ".ecrit"
        ecrit_dir.mkdir()
        config = CloudConfig(
            provider=CloudProvider.DROPBOX, auth_token="bad", folder_path="/",
        )
        save_cloud_configs(str(tmp_path), [config])
        result = export_script(
            str(tmp_path), CloudProvider.DROPBOX,
            "INT. OFFICE", "script",
        )
        assert result.success is False
        assert "Authentication failed" in result.message


class TestConfigPersistence:
    def test_save_and_load(self, tmp_path):
        configs = [
            CloudConfig(
                provider=CloudProvider.GOOGLE_DRIVE,
                auth_token="tok1", folder_path="/a",
            ),
            CloudConfig(
                provider=CloudProvider.DROPBOX,
                auth_token="tok2", folder_path="/b",
                auto_export=True,
            ),
        ]
        save_cloud_configs(str(tmp_path), configs)
        loaded = load_cloud_configs(str(tmp_path))
        assert len(loaded) == 2
        assert loaded[0].provider == CloudProvider.GOOGLE_DRIVE
        assert loaded[0].auth_token == "tok1"
        assert loaded[1].auto_export is True

    def test_load_nonexistent(self, tmp_path):
        assert load_cloud_configs(str(tmp_path / "nope")) == []

    def test_save_creates_directory(self, tmp_path):
        project = tmp_path / "deep" / "project"
        save_cloud_configs(str(project), [])
        assert os.path.isfile(os.path.join(str(project), ".ecrit", "cloud.json"))
