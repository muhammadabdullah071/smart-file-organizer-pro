from __future__ import annotations

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.config import Config
from core.organizer import organize as run_organize
from utils.logger import get_logger


class OrganizeHandler(FileSystemEventHandler):
    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = get_logger()
        self._last_trigger: float = 0.0

    def on_created(self, event: FileSystemEventHandler) -> None:
        if event.is_directory:
            return
        self._debounced_organize()

    def on_moved(self, event: FileSystemEventHandler) -> None:
        if event.is_directory:
            return
        self._debounced_organize()

    def _debounced_organize(self) -> None:
        now = time.time()
        if now - self._last_trigger < 1.0:
            return
        self._last_trigger = now
        try:
            dry_run = self.config.dry_run
            self.config.dry_run = False
            report = run_organize(self.config)
            self.logger.info(
                "Watch organize — moved=%d, skipped=%d",
                report.files_moved,
                report.files_skipped,
            )
        except Exception as e:
            self.logger.error("Watch organize failed: %s", e)
        finally:
            self.config.dry_run = dry_run


def start_watching(config: Config) -> None:
    logger = get_logger()
    target = config.base_path.resolve()
    if not target.exists():
        raise FileNotFoundError(f"Watch target not found: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Watch target is not a directory: {target}")

    event_handler = OrganizeHandler(config)
    observer = Observer()
    observer.schedule(event_handler, str(target), recursive=config.recursive)
    observer.start()
    logger.info("Watching %s for new files...", target)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
