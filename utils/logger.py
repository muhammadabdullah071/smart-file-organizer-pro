from __future__ import annotations

import logging
from pathlib import Path

from utils.helpers import ensure_dir

LOG_DIR = Path("logs")
APP_LOG_FILE = LOG_DIR / "app.log"
ACTIONS_LOG_FILE = LOG_DIR / "actions.log"


def setup_logging(
    *,
    create_logs: bool = True,
    log_level: str = "DEBUG",
) -> logging.Logger:
    logger = logging.getLogger("sfop")
    logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if create_logs:
        ensure_dir(LOG_DIR)

        app_handler = logging.FileHandler(str(APP_LOG_FILE), encoding="utf-8")
        app_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
        app_handler.setFormatter(formatter)
        logger.addHandler(app_handler)

        actions_handler = logging.FileHandler(str(ACTIONS_LOG_FILE), encoding="utf-8")
        actions_handler.setLevel(logging.INFO)
        actions_handler.setFormatter(formatter)
        logger.addHandler(actions_handler)

    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("sfop")
