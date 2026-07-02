from __future__ import annotations

from pathlib import Path

from core.mover import safe_move


class TestSafeMove:
    def test_basic_move(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        dest_dir = tmp_path / "dest"
        src.write_text("hello", encoding="utf-8")
        result = safe_move(src, dest_dir, "src.txt")
        assert result.status == "moved"
        assert (dest_dir / "src.txt").exists()
        assert not src.exists()

    def test_auto_creates_dest_dir(self, tmp_path: Path) -> None:
        src = tmp_path / "file.txt"
        dest_dir = tmp_path / "a" / "b" / "c"
        src.write_text("test", encoding="utf-8")
        result = safe_move(src, dest_dir, "file.txt")
        assert result.status == "moved"
        assert (dest_dir / "file.txt").exists()

    def test_renames_on_conflict(self, tmp_path: Path) -> None:
        src = tmp_path / "file.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        (dest_dir / "file.txt").write_text("existing", encoding="utf-8")
        src.write_text("new", encoding="utf-8")
        result = safe_move(src, dest_dir, "file.txt")
        assert result.status == "renamed"
        assert result.filename == "file_1.txt"
        assert (dest_dir / "file_1.txt").exists()
        assert (dest_dir / "file.txt").exists()

    def test_skips_same_file(self, tmp_path: Path) -> None:
        src = tmp_path / "file.txt"
        src.write_text("test", encoding="utf-8")
        result = safe_move(src, tmp_path, "file.txt")
        assert result.status == "skipped"
        assert src.exists()

    def test_error_on_invalid_src(self, tmp_path: Path) -> None:
        src = tmp_path / "nonexistent.txt"
        dest_dir = tmp_path / "dest"
        result = safe_move(src, dest_dir, "nonexistent.txt")
        assert result.status == "error"

    def test_return_type(self, tmp_path: Path) -> None:
        src = tmp_path / "test.txt"
        dest_dir = tmp_path / "dest"
        src.write_text("data", encoding="utf-8")
        result = safe_move(src, dest_dir, "test.txt")
        assert result.src == src
        assert result.dest == (dest_dir / "test.txt").resolve()
        assert isinstance(result.filename, str)
        assert isinstance(result.status, str)
