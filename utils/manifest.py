from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from utils.helpers import ensure_dir

MANIFEST_DIR = Path(".sfop") / "manifests"


@dataclass
class ManifestEntry:
    src: str
    dest: str
    timestamp: str = ""
    error: bool = False


@dataclass
class Manifest:
    entries: list[ManifestEntry] = field(default_factory=list)
    run_id: str = ""


def save_manifest(entries: list[ManifestEntry], run_id: str) -> Path:
    ensure_dir(MANIFEST_DIR)
    path = MANIFEST_DIR / f"run_{run_id}.json"
    data = {
        "run_id": run_id,
        "entries": [
            {
                "src": e.src,
                "dest": e.dest,
                "timestamp": e.timestamp,
                "error": e.error,
            }
            for e in entries
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_latest_manifest() -> Manifest | None:
    if not MANIFEST_DIR.exists():
        return None
    manifest_files = sorted(MANIFEST_DIR.glob("run_*.json"), reverse=True)
    if not manifest_files:
        return None
    return _load_manifest(manifest_files[0])


def load_manifest(path: Path) -> Manifest | None:
    if not path.exists():
        return None
    return _load_manifest(path)


def _load_manifest(path: Path) -> Manifest | None:
    try:
        raw = path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(raw)
        entries = [
            ManifestEntry(
                src=e["src"],
                dest=e["dest"],
                timestamp=e.get("timestamp", ""),
                error=e.get("error", False),
            )
            for e in data.get("entries", [])
        ]
        return Manifest(entries=entries, run_id=data.get("run_id", ""))
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def undo_manifest(manifest: Manifest) -> dict[str, int]:
    restored = 0
    failed = 0
    errors: list[str] = []
    for entry in reversed(manifest.entries):
        if entry.error:
            continue
        src = Path(entry.src)
        dest = Path(entry.dest)
        if not dest.exists():
            failed += 1
            errors.append(f"Destination not found: {dest}")
            continue
        try:
            ensure_dir(src.parent)
            dest.rename(src)
            restored += 1
        except OSError as e:
            failed += 1
            errors.append(f"Failed to restore {dest} → {src}: {e}")
    return {"restored": restored, "failed": failed}
