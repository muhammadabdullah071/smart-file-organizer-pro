from __future__ import annotations

from pathlib import Path

from utils.manifest import (
    save_manifest,
    load_latest_manifest,
    load_manifest,
    undo_manifest,
    ManifestEntry,
    Manifest,
    MANIFEST_DIR,
)


class TestSaveAndLoadManifest:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            entries = [ManifestEntry(src="C:\\a.txt", dest="C:\\b.txt")]
            path = save_manifest(entries, "test001")
            assert path.exists()
            assert MANIFEST_DIR.exists()
        finally:
            __import__("os").chdir(str(original))

    def test_load_latest_returns_none_when_empty(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            manifest = load_latest_manifest()
            assert manifest is None
        finally:
            __import__("os").chdir(str(original))

    def test_load_latest_returns_most_recent(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            save_manifest([], "run_001")
            save_manifest([], "run_002")
            manifest = load_latest_manifest()
            assert manifest is not None
            assert manifest.run_id == "run_002"
        finally:
            __import__("os").chdir(str(original))

    def test_load_specific_manifest(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            save_manifest([ManifestEntry(src="a", dest="b")], "test001")
            path = MANIFEST_DIR / "run_test001.json"
            manifest = load_manifest(path)
            assert manifest is not None
            assert len(manifest.entries) == 1
            assert manifest.entries[0].src == "a"
        finally:
            __import__("os").chdir(str(original))

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            manifest = load_manifest(Path("nonexistent.json"))
            assert manifest is None
        finally:
            __import__("os").chdir(str(original))


class TestUndoManifest:
    def test_undo_restores_files(self, tmp_path: Path) -> None:
        original = Path.cwd()
        try:
            __import__("os").chdir(str(tmp_path))
            src = tmp_path / "original.txt"
            dest_dir = tmp_path / "dest"
            dest_dir.mkdir()
            dest = dest_dir / "original.txt"
            src.write_text("content", encoding="utf-8")
            src.rename(dest)
            entries = [ManifestEntry(src=str(src), dest=str(dest))]
            manifest = Manifest(entries=entries)
            result = undo_manifest(manifest)
            assert result["restored"] == 1
            assert src.exists()
            assert not dest.exists()
        finally:
            __import__("os").chdir(str(original))

    def test_undo_skips_missing_dest(self, tmp_path: Path) -> None:
        entries = [ManifestEntry(src="C:\\nonexistent_src.txt", dest="C:\\nonexistent_dest.txt")]
        manifest = Manifest(entries=entries)
        result = undo_manifest(manifest)
        assert result["restored"] == 0
        assert result["failed"] == 1

    def test_undo_skips_errors(self, tmp_path: Path) -> None:
        entries = [ManifestEntry(src="a.txt", dest="b.txt", error=True)]
        manifest = Manifest(entries=entries)
        result = undo_manifest(manifest)
        assert result["restored"] == 0
