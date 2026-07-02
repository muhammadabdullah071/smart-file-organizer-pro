from __future__ import annotations

import json
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"],
    "Documents": ["pdf", "docx", "doc", "txt", "xlsx", "pptx", "csv"],
    "Videos": ["mp4", "mkv", "avi", "mov", "wmv"],
    "Music": ["mp3", "wav", "flac", "aac", "ogg"],
    "Archives": ["zip", "rar", "7z", "tar", "gz"],
    "Code": ["py", "js", "ts", "java", "cpp", "html", "css"],
}

CONFIG_FILENAME = "config.json"


@dataclass
class Config:
    base_path: Path = Path(".")
    dry_run: bool = True
    recursive: bool = False
    create_logs: bool = True
    log_level: str = "DEBUG"
    remove_empty_dirs: bool = True
    watch_interval: int = 2
    categories: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_CATEGORIES))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        return cls(
            base_path=Path(data.get("base_path", ".")),
            dry_run=data.get("dry_run", True),
            recursive=data.get("recursive", False),
            create_logs=data.get("create_logs", True),
            log_level=data.get("log_level", "DEBUG"),
            remove_empty_dirs=data.get("remove_empty_dirs", True),
            watch_interval=data.get("watch_interval", 2),
            categories=data.get("categories", dict(DEFAULT_CATEGORIES)),
        )

    def merge_cli(
        self,
        *,
        path: Optional[str] = None,
        apply: Optional[bool] = None,
        recursive: Optional[bool] = None,
        no_logs: Optional[bool] = None,
    ) -> Config:
        new = copy(self)
        if path is not None:
            new.base_path = Path(path)
        if apply is not None:
            new.dry_run = not apply
        if recursive is not None:
            new.recursive = recursive
        if no_logs is True:
            new.create_logs = False
        return new

    def resolved_path(self) -> Path:
        return self.base_path.resolve()


def load_config(path: Optional[Path] = None) -> Config:
    if path is None:
        path = Path(CONFIG_FILENAME)
    if not path.exists():
        return Config()
    try:
        raw = path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(raw)
        return Config.from_dict(data)
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"Failed to load config from {path}: {e}")


def save_default_config(path: Path) -> None:
    cfg = Config()
    data = {
        "base_path": str(cfg.base_path),
        "dry_run": cfg.dry_run,
        "recursive": cfg.recursive,
        "create_logs": cfg.create_logs,
        "log_level": cfg.log_level,
        "remove_empty_dirs": cfg.remove_empty_dirs,
        "watch_interval": cfg.watch_interval,
        "categories": cfg.categories,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
