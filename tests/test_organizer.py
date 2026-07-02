from __future__ import annotations

from pathlib import Path

from core.config import Config
from core.organizer import organize


class TestOrganize:
    def test_dry_run_does_not_move_files(self, tmp_path: Path) -> None:
        (tmp_path / "photo.jpg").write_text("image", encoding="utf-8")
        (tmp_path / "doc.pdf").write_text("document", encoding="utf-8")
        cfg = Config(base_path=tmp_path, dry_run=True, create_logs=False)
        report = organize(cfg)
        assert report.total_scanned == 2
        assert report.files_moved == 0
        assert report.files_skipped == 0
        assert (tmp_path / "photo.jpg").exists()
        assert (tmp_path / "doc.pdf").exists()
        assert not (tmp_path / "Images" / "photo.jpg").exists()

    def test_apply_moves_files(self, tmp_path: Path) -> None:
        (tmp_path / "photo.jpg").write_text("image", encoding="utf-8")
        (tmp_path / "doc.pdf").write_text("document", encoding="utf-8")
        cfg = Config(base_path=tmp_path, dry_run=False, create_logs=False, remove_empty_dirs=True)
        report = organize(cfg)
        assert report.total_scanned == 2
        assert report.files_moved == 2
        assert (tmp_path / "Images" / "photo.jpg").exists()
        assert (tmp_path / "Documents" / "doc.pdf").exists()
        assert not (tmp_path / "photo.jpg").exists()

    def test_empty_directory(self, tmp_path: Path) -> None:
        cfg = Config(base_path=tmp_path, dry_run=False, create_logs=False)
        report = organize(cfg)
        assert report.total_scanned == 0
        assert report.files_moved == 0

    def test_report_contains_manifest(self, tmp_path: Path) -> None:
        (tmp_path / "song.mp3").write_text("music", encoding="utf-8")
        cfg = Config(base_path=tmp_path, dry_run=False, create_logs=False)
        report = organize(cfg)
        assert len(report.manifest_entries) == 1
        entry = report.manifest_entries[0]
        assert "src" in entry
        assert "dest" in entry

    def test_content_duplicates_detected(self, tmp_path: Path) -> None:
        content = b"identical content"
        (tmp_path / "a.txt").write_bytes(content)
        (tmp_path / "b.txt").write_bytes(content)
        cfg = Config(base_path=tmp_path, dry_run=True, create_logs=False)
        report = organize(cfg)
        assert report.content_duplicates == 2
