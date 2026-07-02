from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.categories import _get_extension, classify_file
from core.config import DEFAULT_CATEGORIES

SKIP_DIRS: set[str] = {"logs", "reports", ".sfop", ".git", "__pycache__"}


@dataclass
class FileInfo:
    path: Path
    name: str
    extension: str | None
    size: int
    category: str


def scan_directory(
    path: Path,
    categories: dict[str, list[str]] | None = None,
    *,
    recursive: bool = False,
) -> list[FileInfo]:
    cats = categories if categories is not None else DEFAULT_CATEGORIES
    target = path.resolve()

    if not target.exists():
        raise FileNotFoundError(f"Directory not found: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {target}")

    category_folders: set[str] = set(cats.keys()) | {"Others"}
    all_skip_lower: set[str] = {s.lower() for s in category_folders | SKIP_DIRS}

    files: list[FileInfo] = []

    if recursive:
        iterator = target.rglob("*")
    else:
        iterator = target.iterdir()

    for entry in iterator:
        if not entry.is_file():
            continue

        rel = entry.relative_to(target)
        parts = rel.parts
        if len(parts) > 1 and parts[0].lower() in all_skip_lower:
            continue

        ext = _get_extension(entry.name)
        category = classify_file(entry.name, cats)

        files.append(
            FileInfo(
                path=entry,
                name=entry.name,
                extension=ext,
                size=entry.stat().st_size,
                category=category,
            )
        )

    return files
