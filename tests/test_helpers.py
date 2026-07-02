from __future__ import annotations

from pathlib import Path

from utils.helpers import ensure_dir, human_readable_size, format_duration, resolve_base_path


class TestResolveBasePath:
    def test_resolves_to_absolute(self, tmp_path: Path) -> None:
        resolved = resolve_base_path(tmp_path)
        assert resolved.is_absolute()
        assert resolved == tmp_path.resolve()


class TestEnsureDir:
    def test_creates_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "a" / "b" / "c"
        assert not d.exists()
        result = ensure_dir(d)
        assert result == d
        assert d.is_dir()

    def test_existing_directory(self, tmp_path: Path) -> None:
        result = ensure_dir(tmp_path)
        assert result == tmp_path


class TestHumanReadableSize:
    def test_bytes(self) -> None:
        assert human_readable_size(500) == "500.0 B"

    def test_kilobytes(self) -> None:
        assert human_readable_size(2048) == "2.0 KB"

    def test_megabytes(self) -> None:
        assert human_readable_size(1_048_576 * 5) == "5.0 MB"

    def test_gigabytes(self) -> None:
        assert human_readable_size(1_073_741_824 * 3) == "3.0 GB"

    def test_zero_bytes(self) -> None:
        assert human_readable_size(0) == "0.0 B"


class TestFormatDuration:
    def test_seconds(self) -> None:
        assert format_duration(5.5) == "5.50s"

    def test_minutes(self) -> None:
        assert format_duration(125.0) == "2m 5.0s"

    def test_exact_minute(self) -> None:
        assert format_duration(60.0) == "1m 0.0s"
