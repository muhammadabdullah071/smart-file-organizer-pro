from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from core.duplicates import resolve_conflict
from utils.helpers import ensure_dir


@dataclass
class MoveResult:
    src: Path
    dest: Path
    filename: str
    status: str
    reason: str = ""


def safe_move(src: Path, dest_dir: Path, filename: str) -> MoveResult:
    ensure_dir(dest_dir)
    dest_path = (dest_dir / filename).resolve()
    original_name = filename

    if dest_path.exists():
        if dest_path.resolve() == src.resolve():
            return MoveResult(
                src=src,
                dest=dest_path,
                filename=filename,
                status="skipped",
                reason="Source and destination are the same file",
            )
        new_name = resolve_conflict(dest_dir, filename)
        dest_path = (dest_dir / new_name).resolve()
        filename = new_name

    try:
        shutil.move(str(src), str(dest_path))
        return MoveResult(
            src=src,
            dest=dest_path,
            filename=filename,
            status="moved" if filename == original_name else "renamed",
            reason="",
        )
    except OSError as e:
        return MoveResult(
            src=src,
            dest=dest_path,
            filename=filename,
            status="error",
            reason=str(e),
        )
