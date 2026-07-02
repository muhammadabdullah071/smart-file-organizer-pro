from __future__ import annotations

from pathlib import Path

from core.config import DEFAULT_CATEGORIES


def classify_file(filename: str, categories: dict[str, list[str]] | None = None) -> str:
    cats = categories if categories is not None else DEFAULT_CATEGORIES
    ext = _get_extension(filename)
    if ext is None:
        return "Others"
    for category_name, extensions in cats.items():
        for known_ext in extensions:
            if ext == known_ext.lower():
                return category_name
    return "Others"


def get_category_folders(categories: dict[str, list[str]] | None = None) -> list[str]:
    cats = categories if categories is not None else DEFAULT_CATEGORIES
    return list(cats.keys()) + ["Others"]


def _get_extension(filename: str) -> str | None:
    p = Path(filename)
    ext = p.suffix
    if not ext:
        return None
    return ext.lstrip(".").lower()
