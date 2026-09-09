"""Backend module for git remote synchronization.

Provides functions to add/remove remotes, push/pull changes, check sync
status, resolve conflicts, and persist remote configuration to disk.  All
git operations use subprocess with a 30-second timeout and return a
SyncResult instead of raising exceptions.
"""

from __future__ import annotations

import base64
import json
import logging
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RemoteProvider(Enum):
    """Supported git hosting providers."""

    GITHUB = "https://github.com"
    GITLAB = "https://gitlab.com"
    CODEBERG = "https://codeberg.org"


class SyncStatus(Enum):
    """Possible states of the sync engine."""

    IDLE = "idle"
    SYNCING = "syncing"
    CONFLICT = "conflict"
    ERROR = "error"
    UP_TO_DATE = "up_to_date"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RemoteConfig:
    """Configuration for a single remote connection."""

    provider: RemoteProvider
    remote_url: str
    username: str
    token: str  # stored obfuscated on disk, plaintext in memory
    branch: str = "main"
    auto_sync: bool = False


@dataclass
class SyncResult:
    """Outcome of a sync operation."""

    status: SyncStatus
    message: str
    conflicts: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_GIT_TIMEOUT = 30  # seconds


def _run_git(
    args: List[str],
    cwd: Path,
    env_extra: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    """Run a git command and return the CompletedProcess.

    Raises subprocess.TimeoutExpired or subprocess.SubprocessError on
    failure so callers can translate them into SyncResult.
    """
    import os

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT,
        env=env,
    )


def _credential_url(config: RemoteConfig) -> str:
    """Build a remote URL that embeds credentials for HTTPS push/pull."""
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(config.remote_url)
    if not parsed.hostname:
        return config.remote_url
    netloc = f"{config.username}:{config.token}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _sanitize_stderr(stderr: str, config: RemoteConfig) -> str:
    """Strip embedded credentials from git stderr before surfacing it."""
    if config.token and config.token in stderr:
        stderr = stderr.replace(config.token, "***")
    if config.username and config.username in stderr:
        stderr = stderr.replace(f"{config.username}:***@", "***@")
    return stderr


def _obfuscate(token: str) -> str:
    """Base64-encode a token for on-disk storage (not encryption)."""
    return base64.b64encode(token.encode("utf-8")).decode("ascii")


def _deobfuscate(data: str) -> str:
    """Reverse the base64 obfuscation."""
    return base64.b64decode(data.encode("ascii")).decode("utf-8")


def _config_path(project_path: Path) -> Path:
    """Return the path to the sync config file."""
    return project_path / ".ecrit" / "sync.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def add_remote(
    project_path: str | Path,
    config: RemoteConfig,
    name: str = "origin",
) -> SyncResult:
    """Add a git remote to the repository at *project_path*."""
    project_path = Path(project_path)
    try:
        proc = _run_git(
            ["remote", "add", name, config.remote_url],
            cwd=project_path,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            return SyncResult(SyncStatus.ERROR, f"git remote add failed: {stderr}")
        return SyncResult(SyncStatus.IDLE, f"Remote '{name}' added successfully.")
    except subprocess.TimeoutExpired:
        return SyncResult(SyncStatus.ERROR, "git remote add timed out.")
    except Exception as exc:
        return SyncResult(SyncStatus.ERROR, f"Unexpected error: {exc}")


def remove_remote(
    project_path: str | Path,
    name: str = "origin",
) -> SyncResult:
    """Remove the named git remote."""
    project_path = Path(project_path)
    try:
        proc = _run_git(["remote", "remove", name], cwd=project_path)
        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            return SyncResult(SyncStatus.ERROR, f"git remote remove failed: {stderr}")
        return SyncResult(SyncStatus.IDLE, f"Remote '{name}' removed successfully.")
    except subprocess.TimeoutExpired:
        return SyncResult(SyncStatus.ERROR, "git remote remove timed out.")
    except Exception as exc:
        return SyncResult(SyncStatus.ERROR, f"Unexpected error: {exc}")


def push_to_remote(
    project_path: str | Path,
    config: RemoteConfig,
    remote_name: str = "origin",
) -> SyncResult:
    """Push the current branch to the remote using embedded credentials."""
    project_path = Path(project_path)
    cred_url = _credential_url(config)
    try:
        # Temporarily set the push URL to the credential-bearing one, push,
        # then restore.  This avoids persisting the token in .git/config.
        set_proc = _run_git(
            ["remote", "set-url", "--push", remote_name, cred_url],
            cwd=project_path,
        )
        if set_proc.returncode != 0:
            return SyncResult(
                SyncStatus.ERROR,
                f"Failed to set push URL: {set_proc.stderr.strip()}",
            )

        proc = _run_git(
            ["push", remote_name, config.branch],
            cwd=project_path,
        )

        # Restore the non-credential URL.
        _run_git(
            ["remote", "set-url", "--push", remote_name, config.remote_url],
            cwd=project_path,
        )

        if proc.returncode != 0:
            stderr = _sanitize_stderr(proc.stderr.strip(), config)
            return SyncResult(SyncStatus.ERROR, f"git push failed: {stderr}")
        return SyncResult(SyncStatus.UP_TO_DATE, "Push completed successfully.")
    except subprocess.TimeoutExpired:
        # Best-effort URL restore.
        _try_restore_push_url(project_path, remote_name, config.remote_url)
        return SyncResult(SyncStatus.ERROR, "git push timed out.")
    except Exception as exc:
        _try_restore_push_url(project_path, remote_name, config.remote_url)
        return SyncResult(SyncStatus.ERROR, f"Unexpected error: {exc}")


def _try_restore_push_url(
    project_path: Path, remote_name: str, url: str
) -> None:
    """Best-effort restore of the push URL after a failure."""
    try:
        _run_git(
            ["remote", "set-url", "--push", remote_name, url],
            cwd=project_path,
        )
    except Exception:
        logger.warning("Could not restore push URL for remote '%s'.", remote_name)


def pull_from_remote(
    project_path: str | Path,
    config: RemoteConfig,
    remote_name: str = "origin",
) -> SyncResult:
    """Pull from the remote (merge strategy) using embedded credentials."""
    project_path = Path(project_path)
    cred_url = _credential_url(config)
    try:
        # Temporarily swap the fetch URL.
        set_proc = _run_git(
            ["remote", "set-url", remote_name, cred_url],
            cwd=project_path,
        )
        if set_proc.returncode != 0:
            return SyncResult(
                SyncStatus.ERROR,
                f"Failed to set fetch URL: {set_proc.stderr.strip()}",
            )

        proc = _run_git(
            ["pull", remote_name, config.branch],
            cwd=project_path,
        )

        # Restore the clean URL.
        _run_git(
            ["remote", "set-url", remote_name, config.remote_url],
            cwd=project_path,
        )

        if proc.returncode != 0:
            stderr = proc.stderr.strip()
            # Detect merge conflicts.
            if "CONFLICT" in (proc.stdout + proc.stderr):
                conflict_files = _list_conflict_files(project_path)
                return SyncResult(
                    SyncStatus.CONFLICT,
                    "Pull completed with merge conflicts.",
                    conflicts=conflict_files,
                )
            return SyncResult(SyncStatus.ERROR, f"git pull failed: {_sanitize_stderr(stderr, config)}")
        return SyncResult(SyncStatus.UP_TO_DATE, "Pull completed successfully.")
    except subprocess.TimeoutExpired:
        _try_restore_fetch_url(project_path, remote_name, config.remote_url)
        return SyncResult(SyncStatus.ERROR, "git pull timed out.")
    except Exception as exc:
        _try_restore_fetch_url(project_path, remote_name, config.remote_url)
        return SyncResult(SyncStatus.ERROR, f"Unexpected error: {exc}")


def _try_restore_fetch_url(
    project_path: Path, remote_name: str, url: str
) -> None:
    """Best-effort restore of the fetch URL after a failure."""
    try:
        _run_git(
            ["remote", "set-url", remote_name, url],
            cwd=project_path,
        )
    except Exception:
        logger.warning("Could not restore fetch URL for remote '%s'.", remote_name)


def _list_conflict_files(project_path: Path) -> List[str]:
    """Return a list of files currently in a conflicted state."""
    try:
        proc = _run_git(["diff", "--name-only", "--diff-filter=U"], cwd=project_path)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip().splitlines()
    except Exception:
        pass
    return []


def get_sync_status(
    project_path: str | Path,
    remote_name: str = "origin",
    branch: str = "main",
) -> SyncResult:
    """Check whether the local branch is ahead, behind, or diverged.

    Runs ``git fetch`` first (dry-run is not reliable for status), then
    compares revisions.
    """
    project_path = Path(project_path)
    try:
        # Check for unresolved conflicts first.
        conflicts = _list_conflict_files(project_path)
        if conflicts:
            return SyncResult(
                SyncStatus.CONFLICT,
                "There are unresolved merge conflicts.",
                conflicts=conflicts,
            )

        # Fetch without credentials (status check only — remote may be
        # public, or the credential helper may be configured).
        fetch_proc = _run_git(["fetch", remote_name], cwd=project_path)
        if fetch_proc.returncode != 0:
            return SyncResult(
                SyncStatus.ERROR,
                f"git fetch failed: {fetch_proc.stderr.strip()}",
            )

        rev_proc = _run_git(
            ["rev-list", "--left-right", "--count", f"{branch}...{remote_name}/{branch}"],
            cwd=project_path,
        )
        if rev_proc.returncode != 0:
            return SyncResult(
                SyncStatus.ERROR,
                f"Could not compare revisions: {rev_proc.stderr.strip()}",
            )

        parts = rev_proc.stdout.strip().split()
        if len(parts) != 2:
            return SyncResult(SyncStatus.ERROR, "Unexpected rev-list output.")

        ahead, behind = int(parts[0]), int(parts[1])
        if ahead == 0 and behind == 0:
            return SyncResult(SyncStatus.UP_TO_DATE, "Branch is up to date.")
        if ahead > 0 and behind > 0:
            return SyncResult(
                SyncStatus.CONFLICT,
                f"Branch has diverged: {ahead} ahead, {behind} behind.",
            )
        if ahead > 0:
            return SyncResult(
                SyncStatus.IDLE,
                f"Local branch is {ahead} commit(s) ahead.",
            )
        return SyncResult(
            SyncStatus.IDLE,
            f"Local branch is {behind} commit(s) behind.",
        )
    except subprocess.TimeoutExpired:
        return SyncResult(SyncStatus.ERROR, "Status check timed out.")
    except Exception as exc:
        return SyncResult(SyncStatus.ERROR, f"Unexpected error: {exc}")


def resolve_conflict(
    project_path: str | Path,
    strategy: str = "manual",
) -> SyncResult:
    """Resolve merge conflicts using the given strategy.

    *strategy* must be one of ``"ours"``, ``"theirs"``, or ``"manual"``.
    The ``"manual"`` strategy simply reports the conflicting files and
    leaves the working tree untouched for the user to resolve by hand.
    """
    project_path = Path(project_path)
    strategy = strategy.lower()
    if strategy not in ("ours", "theirs", "manual"):
        return SyncResult(
            SyncStatus.ERROR,
            f"Unknown conflict strategy: '{strategy}'. Use 'ours', 'theirs', or 'manual'.",
        )

    conflicts = _list_conflict_files(project_path)
    if not conflicts:
        return SyncResult(SyncStatus.UP_TO_DATE, "No conflicts to resolve.")

    if strategy == "manual":
        return SyncResult(
            SyncStatus.CONFLICT,
            "Conflicts left for manual resolution.",
            conflicts=conflicts,
        )

    try:
        # Checkout using the chosen strategy for every conflicted file.
        checkout_flag = f"--{strategy}"
        proc = _run_git(
            ["checkout", checkout_flag, "--"] + conflicts,
            cwd=project_path,
        )
        if proc.returncode != 0:
            return SyncResult(
                SyncStatus.ERROR,
                f"git checkout {checkout_flag} failed: {proc.stderr.strip()}",
            )

        # Stage the resolved files.
        add_proc = _run_git(["add", "--"] + conflicts, cwd=project_path)
        if add_proc.returncode != 0:
            return SyncResult(
                SyncStatus.ERROR,
                f"git add failed: {add_proc.stderr.strip()}",
            )

        return SyncResult(
            SyncStatus.UP_TO_DATE,
            f"Conflicts resolved using '{strategy}' strategy.",
        )
    except subprocess.TimeoutExpired:
        return SyncResult(SyncStatus.ERROR, "Conflict resolution timed out.")
    except Exception as exc:
        return SyncResult(SyncStatus.ERROR, f"Unexpected error: {exc}")


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------


def save_remote_config(
    project_path: str | Path,
    config: RemoteConfig,
) -> SyncResult:
    """Persist *config* to ``.ecrit/sync.json`` inside *project_path*.

    The token is base64-encoded on disk so it is not stored in plaintext.
    """
    project_path = Path(project_path)
    cfg_path = _config_path(project_path)
    try:
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "provider": config.provider.name,
            "remote_url": config.remote_url,
            "username": config.username,
            "token_b64": _obfuscate(config.token),
            "branch": config.branch,
            "auto_sync": config.auto_sync,
        }
        cfg_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return SyncResult(SyncStatus.IDLE, f"Config saved to {cfg_path}.")
    except Exception as exc:
        return SyncResult(SyncStatus.ERROR, f"Failed to save config: {exc}")


def load_remote_config(
    project_path: str | Path,
) -> tuple[Optional[RemoteConfig], SyncResult]:
    """Load a RemoteConfig from ``.ecrit/sync.json``.

    Returns a ``(config, result)`` tuple.  *config* is ``None`` when the
    file is missing or cannot be parsed.
    """
    project_path = Path(project_path)
    cfg_path = _config_path(project_path)
    if not cfg_path.exists():
        return None, SyncResult(SyncStatus.IDLE, "No remote config found.")
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        config = RemoteConfig(
            provider=RemoteProvider[data["provider"]],
            remote_url=data["remote_url"],
            username=data["username"],
            token=_deobfuscate(data["token_b64"]),
            branch=data.get("branch", "main"),
            auto_sync=data.get("auto_sync", False),
        )
        return config, SyncResult(SyncStatus.IDLE, "Config loaded successfully.")
    except Exception as exc:
        return None, SyncResult(SyncStatus.ERROR, f"Failed to load config: {exc}")
