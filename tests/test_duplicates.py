from __future__ import annotations

import hashlib
from pathlib import Path

from core.duplicates import compute_hash, resolve_conflict, find_content_duplicates
from core.scanner import FileInfo


class TestComputeHash:
    def test_identical_content_same_hash(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello world", encoding="utf-8")
        b.write_text("hello world", encoding="utf-8")
        assert compute_hash(a) == compute_hash(b)

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello", encoding="utf-8")
        b.write_text("world", encoding="utf-8")
        assert compute_hash(a) != compute_hash(b)

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        h = compute_hash(f)
        assert h == hashlib.sha256(b"").hexdigest()

    def test_large_file(self, tmp_path: Path) -> None:
        f = tmp_path / "large.bin"
        data = b"x" * 200_000
        f.write_bytes(data)
        h = compute_hash(f)
        assert len(h) == 64

class TestResolveConflict:
    def test_no_conflict(self, tmp_path: Path) -> None:
        name = resolve_conflict(tmp_path, "file.txt")
        assert name == "file.txt"

    def test_basic_conflict(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").write_text("original", encoding="utf-8")
        name = resolve_conflict(tmp_path, "file.txt")
        assert name == "file_1.txt"

    def test_multiple_conflicts(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").write_text("", encoding="utf-8")
        (tmp_path / "file_1.txt").write_text("", encoding="utf-8")
        (tmp_path / "file_2.txt").write_text("", encoding="utf-8")
        name = resolve_conflict(tmp_path, "file.txt")
        assert name == "file_3.txt"

    def test_no_extension(self, tmp_path: Path) -> None:
        (tmp_path / "Makefile").write_text("", encoding="utf-8")
        name = resolve_conflict(tmp_path, "Makefile")
        assert name == "Makefile_1"


class TestFindContentDuplicates:
    def test_no_duplicates(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello", encoding="utf-8")
        b.write_text("world", encoding="utf-8")
        files = [
            FileInfo(path=a, name="a.txt", extension="txt", size=5, category="Documents"),
            FileInfo(path=b, name="b.txt", extension="txt", size=5, category="Documents"),
        ]
        dups = find_content_duplicates(files)
        assert dups == {}

    def test_finds_duplicates(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        content = b"same content"
        a.write_bytes(content)
        b.write_bytes(content)
        files = [
            FileInfo(path=a, name="a.txt", extension="txt", size=len(content), category="Documents"),
            FileInfo(path=b, name="b.txt", extension="txt", size=len(content), category="Documents"),
        ]
        dups = find_content_duplicates(files)
        assert len(dups) == 1
        group = list(dups.values())[0]
        assert len(group) == 2
        names = {fi.name for fi in group}
        assert names == {"a.txt", "b.txt"}
