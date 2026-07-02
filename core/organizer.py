from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from core.config import Config
from core.scanner import scan_directory, FileInfo
from core.mover import safe_move
from core.duplicates import find_content_duplicates
from core.reporter import Report, save_report, save_report_json, REPORT_FILE, TEXT_REPORT_FILE
from utils.helpers import resolve_base_path, ensure_dir
from utils.manifest import MANIFEST_DIR


def organize(config: Config) -> Report:
    start_time = perf_counter()
    target = resolve_base_path(config.base_path)

    files = scan_directory(target, config.categories, recursive=config.recursive)
    total_scanned = len(files)

    content_dups = find_content_duplicates(files)
    total_content_dup_files = sum(len(v) for v in content_dups.values())

    grouped: dict[str, list[FileInfo]] = {}
    for fi in files:
        grouped.setdefault(fi.category, []).append(fi)

    manifest_entries: list[dict[str, Any]] = []
    moved_count = 0
    skipped_count = 0
    dup_count = 0
    errors: list[str] = []

    if not config.dry_run:
        for category, cat_files in grouped.items():
            dest_dir = target / category
            for fi in cat_files:
                result = safe_move(fi.path, dest_dir, fi.name)
                if result.status == "moved":
                    moved_count += 1
                    manifest_entries.append(_manifest_entry(result.src, result.dest))
                elif result.status == "renamed":
                    moved_count += 1
                    dup_count += 1
                    manifest_entries.append(_manifest_entry(result.src, result.dest))
                elif result.status == "skipped":
                    skipped_count += 1
                elif result.status == "error":
                    errors.append(f"{fi.name}: {result.reason}")
                    manifest_entries.append(_manifest_entry(result.src, result.dest, error=True))

        if config.remove_empty_dirs:
            _remove_empty_dirs(target, set(config.categories.keys()) | {"Others"})

    elapsed = perf_counter() - start_time

    report = Report(
        base_path=target,
        total_scanned=total_scanned,
        files_moved=moved_count,
        files_skipped=skipped_count,
        duplicates_handled=dup_count,
        content_duplicates=total_content_dup_files,
        errors=errors,
        time_taken=elapsed,
        manifest_entries=manifest_entries,
    )

    if config.create_logs:
        save_report_json(report, REPORT_FILE)
        save_report(report, TEXT_REPORT_FILE)
        if manifest_entries:
            _save_manifest(manifest_entries)

    return report


def _remove_empty_dirs(target: Path, keep_dirs: set[str]) -> None:
    for child in target.iterdir():
        if child.is_dir() and child.name not in keep_dirs:
            try:
                child.rmdir()
            except OSError:
                pass


def _manifest_entry(src: Path, dest: Path, error: bool = False) -> dict[str, Any]:
    return {
        "src": str(src),
        "dest": str(dest),
        "timestamp": datetime.now().isoformat(),
        "error": error,
    }


def _save_manifest(entries: list[dict[str, Any]]) -> None:
    manifest_dir = Path(".sfop") / "manifests"
    ensure_dir(manifest_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = manifest_dir / f"run_{ts}.json"
    path.write_text(json.dumps({"entries": entries, "run_id": ts}, indent=2), encoding="utf-8")
