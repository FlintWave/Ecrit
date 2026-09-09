"""Sync bundle — portable project snapshot for companion device transfer."""

from __future__ import annotations

import json
import os
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SyncBundle:
    project_title: str
    script_content: str
    format_id: str = "fountain/core"
    created_at: str = ""
    plan_documents: list[dict] = field(default_factory=list)
    characters: list[dict] = field(default_factory=list)
    outline_nodes: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> SyncBundle:
        return cls(
            project_title=data.get("project_title", "Untitled"),
            script_content=data.get("script_content", ""),
            format_id=data.get("format_id", "fountain/core"),
            created_at=data.get("created_at", ""),
            plan_documents=data.get("plan_documents", []),
            characters=data.get("characters", []),
            outline_nodes=data.get("outline_nodes", []),
            metadata=data.get("metadata", {}),
        )


def create_sync_bundle(
    project_path: str,
    script_content: str,
    title: str = "",
    output_dir: str = "",
) -> str:
    if not title:
        title = os.path.basename(project_path)
    if not output_dir:
        output_dir = os.path.dirname(project_path)

    bundle = SyncBundle(project_title=title, script_content=script_content)

    meta_path = os.path.join(project_path, "meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            bundle.format_id = meta.get("format_id", "fountain/core")
            bundle.metadata = meta
        except (json.JSONDecodeError, OSError):
            pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    filename = f"{safe_title}_{timestamp}.ecrit-sync"
    filepath = os.path.join(output_dir, filename)

    with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bundle.json", json.dumps(bundle.to_dict(), indent=2))
        zf.writestr("script.fountain", script_content)

    return filepath


def load_sync_bundle(bundle_path: str) -> Optional[SyncBundle]:
    if not os.path.exists(bundle_path):
        return None
    try:
        with zipfile.ZipFile(bundle_path, "r") as zf:
            data = json.loads(zf.read("bundle.json"))
            return SyncBundle.from_dict(data)
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, OSError):
        return None
