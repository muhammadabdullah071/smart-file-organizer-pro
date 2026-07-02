from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.helpers import human_readable_size, format_duration, ensure_dir

REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "last_report.json"
TEXT_REPORT_FILE = REPORT_DIR / "report.txt"


@dataclass
class Report:
    base_path: Path
    total_scanned: int = 0
    files_moved: int = 0
    files_skipped: int = 0
    duplicates_handled: int = 0
    content_duplicates: int = 0
    errors: list[str] = field(default_factory=list)
    time_taken: float = 0.0
    manifest_entries: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def summary_lines(self) -> list[str]:
        return [
            f"Base path:          {self.base_path}",
            f"Timestamp:          {self.timestamp}",
            f"Total files scanned:{self.total_scanned:>5}",
            f"Files moved:        {self.files_moved:>5}",
            f"Files skipped:      {self.files_skipped:>5}",
            f"Duplicates handled: {self.duplicates_handled:>5}",
            f"Content duplicates: {self.content_duplicates:>5}",
            f"Errors:             {len(self.errors):>5}",
            f"Time taken:         {format_duration(self.time_taken)}",
        ]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["base_path"] = str(d["base_path"])
        return d


def save_report(report: Report, path: Path) -> None:
    ensure_dir(path.parent)
    lines = ["=" * 50, "SMART FILE ORGANIZER PRO — REPORT", "=" * 50, ""]
    lines.extend(report.summary_lines())
    lines.append("")
    if report.errors:
        lines.append("ERRORS:")
        for err in report.errors:
            lines.append(f"  - {err}")
        lines.append("")
    if report.manifest_entries:
        lines.append("MANIFEST:")
        for entry in report.manifest_entries[:20]:
            lines.append(f"  {entry.get('src', '?')}  →  {entry.get('dest', '?')}")
        if len(report.manifest_entries) > 20:
            lines.append(f"  ... and {len(report.manifest_entries) - 20} more")
        lines.append("")
    lines.append("=" * 50)
    path.write_text("\n".join(lines), encoding="utf-8")


def load_report(path: Path) -> Report | None:
    if not path.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return Report(**data)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def save_report_json(report: Report, path: Path) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
