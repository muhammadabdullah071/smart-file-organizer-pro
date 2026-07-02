from __future__ import annotations

import json
from pathlib import Path

from core.reporter import Report, save_report, save_report_json, load_report


class TestReport:
    def test_summary_contains_all_fields(self) -> None:
        report = Report(
            base_path=Path("."),
            total_scanned=100,
            files_moved=50,
            files_skipped=30,
            duplicates_handled=10,
            content_duplicates=5,
            errors=["file.txt: not found"],
            time_taken=1.5,
        )
        lines = "\n".join(report.summary_lines())
        assert "Total files scanned:  100" in lines
        assert "Files moved:           50" in lines
        assert "Files skipped:         30" in lines
        assert "Duplicates handled:    10" in lines
        assert "Content duplicates:     5" in lines
        assert "Errors:                 1" in lines
        assert "Time taken:" in lines

    def test_report_to_dict(self) -> None:
        report = Report(base_path=Path("C:\\test"), total_scanned=5)
        d = report.to_dict()
        assert d["base_path"] == "C:\\test"
        assert d["total_scanned"] == 5
        assert "timestamp" in d

    def test_defaults(self) -> None:
        report = Report(base_path=Path("."))
        assert report.files_moved == 0
        assert report.errors == []


class TestSaveReport:
    def test_saves_text_report(self, tmp_path: Path) -> None:
        report = Report(base_path=tmp_path, total_scanned=10, files_moved=5)
        path = tmp_path / "report.txt"
        save_report(report, path)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "SMART FILE ORGANIZER PRO" in content
        assert "10" in content

    def test_saves_json_report(self, tmp_path: Path) -> None:
        report = Report(base_path=tmp_path, total_scanned=10)
        path = tmp_path / "report.json"
        save_report_json(report, path)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["total_scanned"] == 10
        assert data["base_path"] == str(tmp_path)


class TestLoadReport:
    def test_load_valid_report(self, tmp_path: Path) -> None:
        path = tmp_path / "report.json"
        data = {
            "base_path": str(tmp_path),
            "total_scanned": 10,
            "files_moved": 5,
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        report = load_report(path)
        assert report is not None
        assert report.total_scanned == 10
        assert report.files_moved == 5

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        report = load_report(tmp_path / "nonexistent.json")
        assert report is None

    def test_load_invalid_json_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        report = load_report(path)
        assert report is None
