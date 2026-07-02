from __future__ import annotations

from pathlib import Path

import pytest

from core.scanner import scan_directory, FileInfo, SKIP_DIRS


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("test", encoding="utf-8")


class TestScanDirectory:
    def test_flat_scan(self, tmp_path: Path) -> None:
        _touch(tmp_path / "a.jpg")
        _touch(tmp_path / "b.pdf")
        _touch(tmp_path / "c.mp3")
        result = scan_directory(tmp_path)
        assert len(result) == 3
        names = {f.name for f in result}
        assert names == {"a.jpg", "b.pdf", "c.mp3"}
        cats = {f.category for f in result}
        assert "Images" in cats
        assert "Documents" in cats
        assert "Music" in cats

    def test_recursive_scan(self, tmp_path: Path) -> None:
        _touch(tmp_path / "a.jpg")
        _touch(tmp_path / "sub" / "b.pdf")
        _touch(tmp_path / "sub" / "deep" / "c.mp3")
        result = scan_directory(tmp_path, recursive=True)
        assert len(result) == 3

    def test_non_recursive_skips_subdirs(self, tmp_path: Path) -> None:
        _touch(tmp_path / "a.jpg")
        _touch(tmp_path / "sub" / "b.pdf")
        result = scan_directory(tmp_path, recursive=False)
        assert len(result) == 1
        assert result[0].name == "a.jpg"

    def test_skip_category_folders(self, tmp_path: Path) -> None:
        _touch(tmp_path / "a.jpg")
        _touch(tmp_path / "Images" / "b.jpg")
        _touch(tmp_path / "Images" / "sub" / "c.jpg")
        result = scan_directory(tmp_path, recursive=True)
        names = {f.name for f in result}
        assert names == {"a.jpg"}

    def test_skip_system_folders(self, tmp_path: Path) -> None:
        for d in SKIP_DIRS:
            _touch(tmp_path / d / "file.txt")
        _touch(tmp_path / "real.txt")
        result = scan_directory(tmp_path, recursive=True)
        assert len(result) == 1
        assert result[0].name == "real.txt"

    def test_missing_directory_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            scan_directory(Path("/nonexistent/path"))

    def test_file_path_not_directory(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("test", encoding="utf-8")
        with pytest.raises(NotADirectoryError):
            scan_directory(f)

    def test_file_info_dataclass(self, tmp_path: Path) -> None:
        _touch(tmp_path / "test.jpg")
        result = scan_directory(tmp_path)
        fi = result[0]
        assert isinstance(fi, FileInfo)
        assert fi.extension == "jpg"
        assert fi.category == "Images"
        assert fi.size > 0
        assert fi.name == "test.jpg"
        assert fi.path == (tmp_path / "test.jpg").resolve()

    def test_empty_directory(self, tmp_path: Path) -> None:
        result = scan_directory(tmp_path)
        assert result == []

    def test_hidden_files_are_scanned(self, tmp_path: Path) -> None:
        _touch(tmp_path / ".hidden.txt")
        result = scan_directory(tmp_path)
        assert len(result) == 1
        assert result[0].extension == "txt"
