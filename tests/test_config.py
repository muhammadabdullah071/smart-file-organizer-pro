from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.config import Config, load_config, save_default_config, DEFAULT_CATEGORIES


class TestLoadConfig:
    def test_load_defaults_when_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.json"
        cfg = load_config(missing)
        assert cfg.dry_run is True
        assert cfg.recursive is False
        assert cfg.base_path == Path(".")

    def test_load_valid_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.json"
        data = {
            "base_path": "test_folder",
            "dry_run": False,
            "recursive": True,
            "create_logs": False,
            "log_level": "INFO",
            "remove_empty_dirs": False,
            "watch_interval": 5,
            "categories": {"Videos": ["mp4"]},
        }
        config_file.write_text(json.dumps(data), encoding="utf-8")
        cfg = load_config(config_file)
        assert cfg.base_path == Path("test_folder")
        assert cfg.dry_run is False
        assert cfg.recursive is True
        assert cfg.create_logs is False
        assert cfg.log_level == "INFO"
        assert cfg.remove_empty_dirs is False
        assert cfg.watch_interval == 5
        assert cfg.categories == {"Videos": ["mp4"]}

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.json"
        config_file.write_text("not json", encoding="utf-8")
        with pytest.raises(RuntimeError, match="Failed to load config"):
            load_config(config_file)

    def test_load_partial_config_uses_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / "partial.json"
        config_file.write_text(json.dumps({"dry_run": False}), encoding="utf-8")
        cfg = load_config(config_file)
        assert cfg.dry_run is False
        assert cfg.recursive is False
        assert cfg.base_path == Path(".")


class TestSaveDefaultConfig:
    def test_save_creates_valid_config(self, tmp_path: Path) -> None:
        out = tmp_path / "new_config.json"
        save_default_config(out)
        assert out.exists()
        raw = json.loads(out.read_text(encoding="utf-8"))
        assert raw["dry_run"] is True
        assert "Images" in raw["categories"]


class TestConfigMergeCLI:
    def test_merge_path(self) -> None:
        cfg = Config()
        merged = cfg.merge_cli(path="my_folder")
        assert merged.base_path == Path("my_folder")
        assert merged.dry_run is True

    def test_merge_apply_disables_dry_run(self) -> None:
        cfg = Config()
        merged = cfg.merge_cli(apply=True)
        assert merged.dry_run is False

    def test_merge_recursive(self) -> None:
        cfg = Config()
        merged = cfg.merge_cli(recursive=True)
        assert merged.recursive is True

    def test_merge_no_logs(self) -> None:
        cfg = Config()
        merged = cfg.merge_cli(no_logs=True)
        assert merged.create_logs is False

    def test_merge_preserves_unset(self) -> None:
        cfg = Config(dry_run=False, recursive=True)
        merged = cfg.merge_cli(path="x")
        assert merged.base_path == Path("x")
        assert merged.dry_run is False
        assert merged.recursive is True


class TestConfigDefaults:
    def test_default_categories_present(self) -> None:
        assert "Images" in DEFAULT_CATEGORIES
        assert "Documents" in DEFAULT_CATEGORIES
        assert "Videos" in DEFAULT_CATEGORIES
        assert "Music" in DEFAULT_CATEGORIES
        assert "Archives" in DEFAULT_CATEGORIES
        assert "Code" in DEFAULT_CATEGORIES

    def test_default_config_dry_run_true(self) -> None:
        cfg = Config()
        assert cfg.dry_run is True
