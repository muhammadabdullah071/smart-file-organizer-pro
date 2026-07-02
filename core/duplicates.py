from __future__ import annotations

import hashlib
from pathlib import Path

from core.scanner import FileInfo

_CHUNK_SIZE = 65536  # 64KB


def compute_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_conflict(dest_dir: Path, filename: str) -> str:
    if not (dest_dir / filename).exists():
        return filename
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        if not (dest_dir / new_name).exists():
            return new_name
        counter += 1


def find_content_duplicates(files: list[FileInfo]) -> dict[str, list[FileInfo]]:
    hash_map: dict[str, list[FileInfo]] = {}
    for fi in files:
        h = compute_hash(fi.path)
        hash_map.setdefault(h, []).append(fi)
    return {h: group for h, group in hash_map.items() if len(group) > 1}
