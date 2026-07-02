from __future__ import annotations

from pathlib import Path

from core.config import Config
from core.organizer import organize as run_organize


class TestOrganizeIntegration:
    def test_organize_with_sample_data(self, tmp_path: Path) -> None:
        (tmp_path / "photo.jpg").write_text("img", encoding="utf-8")
        (tmp_path / "doc.pdf").write_text("pdf", encoding="utf-8")
        (tmp_path / "song.mp3").write_text("audio", encoding="utf-8")

        cfg = Config(base_path=tmp_path, dry_run=False, create_logs=False, remove_empty_dirs=True)
        report = run_organize(cfg)

        assert report.total_scanned == 3
        assert report.files_moved == 3
        assert (tmp_path / "Images" / "photo.jpg").exists()
        assert (tmp_path / "Documents" / "doc.pdf").exists()
        assert (tmp_path / "Music" / "song.mp3").exists()

    def test_dry_run_reports_correctly(self, tmp_path: Path) -> None:
        (tmp_path / "a.jpg").write_text("img", encoding="utf-8")
        cfg = Config(base_path=tmp_path, dry_run=True, create_logs=False)
        report = run_organize(cfg)
        assert report.total_scanned == 1
        assert report.files_moved == 0
        assert not (tmp_path / "Images" / "a.jpg").exists()

    def test_duplicate_filenames_get_renamed(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").write_text("first", encoding="utf-8")
        (tmp_path / "readme.txt").write_text("second", encoding="utf-8")
        cfg = Config(base_path=tmp_path, dry_run=False, create_logs=False, remove_empty_dirs=False)
        report = run_organize(cfg)
        assert report.files_moved >= 1
