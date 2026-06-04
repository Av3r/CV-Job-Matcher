"""
tests/test_parser.py
====================
Unit tests for CVParser.

Run with:
    pytest tests/ -v
or with coverage:
    pytest tests/ -v --cov=src --cov-report=term-missing
"""

from __future__ import annotations

import io
import os
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parsers.pdf_parser import CVParser, ParsedCV, parse_cv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_word(text: str, x0: float, top: float, x1: float, bottom: float) -> dict:
    """Return a minimal word-dict compatible with pdfplumber output."""
    return {"text": text, "x0": x0, "top": top, "x1": x1, "bottom": bottom}


# ---------------------------------------------------------------------------
# CVParser._validate_path
# ---------------------------------------------------------------------------


class TestValidatePath:
    def test_raises_file_not_found_for_missing_file(self, tmp_path: Path) -> None:
        parser = CVParser()
        with pytest.raises(FileNotFoundError, match="not found"):
            parser._validate_path(tmp_path / "nonexistent.pdf")

    def test_raises_value_error_for_wrong_extension(self, tmp_path: Path) -> None:
        txt_file = tmp_path / "resume.txt"
        txt_file.write_text("hello")
        parser = CVParser()
        with pytest.raises(ValueError, match=r"\.pdf"):
            parser._validate_path(txt_file)

    def test_returns_path_object_for_valid_pdf(self, tmp_path: Path) -> None:
        pdf_file = tmp_path / "cv.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")
        parser = CVParser()
        result = parser._validate_path(pdf_file)
        assert isinstance(result, Path)
        assert result == pdf_file


# ---------------------------------------------------------------------------
# CVParser._cluster_into_rows
# ---------------------------------------------------------------------------


class TestClusterIntoRows:
    def test_empty_input_returns_empty_list(self) -> None:
        parser = CVParser()
        assert parser._cluster_into_rows([]) == []

    def test_single_word_forms_one_row(self) -> None:
        parser = CVParser()
        words = [_make_word("Hello", 0, 10, 30, 20)]
        rows = parser._cluster_into_rows(words)
        assert len(rows) == 1
        assert rows[0][0]["text"] == "Hello"

    def test_words_on_same_line_grouped_together(self) -> None:
        parser = CVParser(row_tolerance=3.0)
        words = [
            _make_word("Name", 0, 10, 40, 20),
            _make_word("John", 50, 11, 90, 21),  # midpoint diff = 0.5 < 3.0
        ]
        rows = parser._cluster_into_rows(words)
        assert len(rows) == 1
        assert {w["text"] for w in rows[0]} == {"Name", "John"}

    def test_words_on_different_lines_form_separate_rows(self) -> None:
        parser = CVParser(row_tolerance=3.0)
        words = [
            _make_word("Line1", 0, 10, 50, 20),   # mid = 15
            _make_word("Line2", 0, 40, 50, 50),   # mid = 45
        ]
        rows = parser._cluster_into_rows(words)
        assert len(rows) == 2

    def test_rows_are_ordered_top_to_bottom(self) -> None:
        parser = CVParser(row_tolerance=3.0)
        words = [
            _make_word("Second", 0, 50, 60, 60),
            _make_word("First", 0, 10, 60, 20),
        ]
        rows = parser._cluster_into_rows(words)
        assert rows[0][0]["text"] == "First"
        assert rows[1][0]["text"] == "Second"


# ---------------------------------------------------------------------------
# CVParser._extract_page_text  (mocked pdfplumber page)
# ---------------------------------------------------------------------------


class TestExtractPageText:
    def _make_mock_page(self, words: list[dict], fallback_text: str = "") -> MagicMock:
        page = MagicMock()
        page.extract_words.return_value = words
        page.extract_text.return_value = fallback_text
        return page

    def test_single_column_order_preserved(self) -> None:
        parser = CVParser()
        words = [
            _make_word("Alice", 0, 10, 40, 20),
            _make_word("Developer", 0, 30, 70, 40),
        ]
        page = self._make_mock_page(words)
        text = parser._extract_page_text(page)
        lines = text.splitlines()
        assert lines[0] == "Alice"
        assert lines[1] == "Developer"

    def test_two_column_words_on_same_row_sorted_left_to_right(self) -> None:
        parser = CVParser(row_tolerance=3.0, word_gap_threshold=10.0)
        # Simulate two-column layout: left col at x≈0, right col at x≈300
        words = [
            _make_word("RightCol", 300, 10, 360, 20),
            _make_word("LeftCol", 0, 11, 60, 21),
        ]
        page = self._make_mock_page(words)
        text = parser._extract_page_text(page)
        # LeftCol must appear before RightCol
        assert text.index("LeftCol") < text.index("RightCol")

    def test_fallback_used_when_no_words_extracted(self) -> None:
        parser = CVParser()
        page = self._make_mock_page(words=[], fallback_text="Fallback text")
        text = parser._extract_page_text(page)
        assert text == "Fallback text"

    def test_empty_page_returns_empty_string(self) -> None:
        parser = CVParser()
        page = self._make_mock_page(words=[], fallback_text="")
        text = parser._extract_page_text(page)
        assert text == ""


# ---------------------------------------------------------------------------
# CVParser._join_pages
# ---------------------------------------------------------------------------


class TestJoinPages:
    def test_empty_pages_filtered_out(self) -> None:
        result = CVParser._join_pages(["Page1", "", "Page3"])
        assert "Page1" in result
        assert "Page3" in result
        # Empty page should not introduce double separators
        assert "\f\n\f" not in result

    def test_single_page_no_separator(self) -> None:
        result = CVParser._join_pages(["Only page"])
        assert result == "Only page"

    def test_all_empty_returns_empty_string(self) -> None:
        result = CVParser._join_pages(["", "", ""])
        assert result == ""


# ---------------------------------------------------------------------------
# CVParser.parse  (integration-level, fully mocked pdfplumber)
# ---------------------------------------------------------------------------


class TestCVParserParse:
    def _make_mock_pdf(self, pages_words: list[list[dict]]) -> MagicMock:
        """Build a mock pdfplumber PDF context manager."""
        mock_pages = []
        for words in pages_words:
            page = MagicMock()
            page.extract_words.return_value = words
            page.extract_text.return_value = " ".join(w["text"] for w in words)
            mock_pages.append(page)

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = mock_pages
        return mock_pdf

    def test_returns_parsed_cv_instance(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "cv.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        words = [_make_word("Engineer", 0, 10, 60, 20)]
        mock_pdf = self._make_mock_pdf([words])

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = CVParser().parse(pdf_path)

        assert isinstance(result, ParsedCV)
        assert result.total_pages == 1
        assert "Engineer" in result.raw_text

    def test_total_pages_matches_pdf(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "cv.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_pdf = self._make_mock_pdf([
            [_make_word("Page1", 0, 10, 50, 20)],
            [_make_word("Page2", 0, 10, 50, 20)],
        ])

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = CVParser().parse(pdf_path)

        assert result.total_pages == 2
        assert len(result.pages_text) == 2

    def test_raises_file_not_found_for_missing_pdf(self, tmp_path: Path) -> None:
        parser = CVParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(tmp_path / "ghost.pdf")

    def test_raises_value_error_for_non_pdf(self, tmp_path: Path) -> None:
        txt = tmp_path / "cv.docx"
        txt.write_bytes(b"PK fake docx")
        parser = CVParser()
        with pytest.raises(ValueError):
            parser.parse(txt)

    def test_word_count_property(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "cv.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        words = [
            _make_word("Hello", 0, 10, 40, 20),
            _make_word("World", 50, 10, 90, 20),
        ]
        mock_pdf = self._make_mock_pdf([words])

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = CVParser().parse(pdf_path)

        assert result.word_count == 2


# ---------------------------------------------------------------------------
# Module-level parse_cv convenience function
# ---------------------------------------------------------------------------


class TestParseCVFunction:
    def test_parse_cv_delegates_to_cvparser(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "cv.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        words = [_make_word("Python", 0, 10, 50, 20)]
        page = MagicMock()
        page.extract_words.return_value = words
        page.extract_text.return_value = "Python"

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = parse_cv(pdf_path)

        assert isinstance(result, ParsedCV)
        assert "Python" in result.raw_text
