from __future__ import annotations

import pytest

from core.categories import classify_file, get_category_folders, _get_extension
from core.config import DEFAULT_CATEGORIES


class TestClassifyFile:
    def test_image_file(self) -> None:
        assert classify_file("photo.jpg") == "Images"
        assert classify_file("photo.jpeg") == "Images"
        assert classify_file("photo.png") == "Images"

    def test_document_file(self) -> None:
        assert classify_file("report.pdf") == "Documents"
        assert classify_file("notes.txt") == "Documents"
        assert classify_file("spreadsheet.xlsx") == "Documents"

    def test_video_file(self) -> None:
        assert classify_file("clip.mp4") == "Videos"
        assert classify_file("movie.mkv") == "Videos"

    def test_music_file(self) -> None:
        assert classify_file("song.mp3") == "Music"
        assert classify_file("track.wav") == "Music"

    def test_archive_file(self) -> None:
        assert classify_file("archive.zip") == "Archives"
        assert classify_file("backup.rar") == "Archives"

    def test_code_file(self) -> None:
        assert classify_file("script.py") == "Code"
        assert classify_file("app.js") == "Code"

    def test_unknown_extension_returns_others(self) -> None:
        assert classify_file("unknown.xyz") == "Others"
        assert classify_file("file.abc123") == "Others"

    def test_no_extension_returns_others(self) -> None:
        assert classify_file("Makefile") == "Others"
        assert classify_file("README") == "Others"

    def test_case_insensitive(self) -> None:
        assert classify_file("PHOTO.JPG") == "Images"
        assert classify_file("Report.PDF") == "Documents"
        assert classify_file("Script.PY") == "Code"

    def test_custom_categories(self) -> None:
        custom = {"CustomImages": ["raw", "cr2"]}
        assert classify_file("photo.raw", custom) == "CustomImages"
        assert classify_file("photo.jpg", custom) == "Others"

    def test_dotfile(self) -> None:
        assert classify_file(".hidden") == "Others"

    def test_multiple_dots(self) -> None:
        assert classify_file("archive.tar.gz") == "Archives"
        assert classify_file("backup.tar.gz", {"Archives": ["gz"]}) == "Archives"
        assert classify_file("backup.tar.gz", {"Archives": ["tar"]}) == "Others"


class TestGetCategoryFolders:
    def test_includes_others(self) -> None:
        folders = get_category_folders()
        assert "Others" in folders
        assert all(c in folders for c in DEFAULT_CATEGORIES)


class TestGetExtension:
    def test_simple_ext(self) -> None:
        assert _get_extension("file.txt") == "txt"

    def test_no_ext(self) -> None:
        assert _get_extension("Makefile") is None

    def test_dotfile_suffix(self) -> None:
        assert _get_extension(".gitignore") is None
        assert _get_extension(".hidden.txt") == "txt"

    def test_multiple_ext(self) -> None:
        assert _get_extension("archive.tar.gz") == "gz"
