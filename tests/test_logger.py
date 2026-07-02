from __future__ import annotations

import logging
from pathlib import Path

from utils.logger import setup_logging, get_logger, APP_LOG_FILE, ACTIONS_LOG_FILE


class TestSetupLogging:
    def test_creates_log_files(self, tmp_path: Path) -> None:
        # Change to tmp_path so logs are created there
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            logger = setup_logging(create_logs=True, log_level="DEBUG")
            logger.info("test message")
            for handler in logger.handlers:
                handler.flush()
            app_log = tmp_path / "logs" / "app.log"
            actions_log = tmp_path / "logs" / "actions.log"
            assert app_log.exists()
            assert actions_log.exists()
            content = app_log.read_text(encoding="utf-8")
            assert "test message" in content
        finally:
            __import__("os").chdir(str(original))

    def test_no_logs_when_disabled(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            logger = setup_logging(create_logs=False)
            assert len(logger.handlers) == 0
            app_log = tmp_path / "logs" / "app.log"
            assert not app_log.exists()
        finally:
            __import__("os").chdir(str(original))

    def test_get_logger(self) -> None:
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "sfop"


class TestLoggerIntegration:
    def test_actions_log_only_info(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            logger = setup_logging(create_logs=True, log_level="DEBUG")
            logger.debug("debug message")
            logger.info("info message")
            for handler in logger.handlers:
                handler.flush()
            actions_log = tmp_path / "logs" / "actions.log"
            content = actions_log.read_text(encoding="utf-8")
            assert "info message" in content
            assert "debug message" not in content
        finally:
            __import__("os").chdir(str(original))
