"""
src/parsers/pdf_parser.py
=========================
Robust PDF text extractor with multi-column layout support.

Strategy
--------
Uses ``pdfplumber``'s built-in ``page.extract_text(layout=True)`` which
renders the page into a character grid, preserving the visual spacing between
columns.  This is simpler and more reliable than manual word-clustering for
the vast majority of CV layouts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final, Optional

import pdfplumber
from pdfplumber.page import Page
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Passed to ``pdfplumber`` for character-grid snapping during layout extraction.
DEFAULT_ROW_TOLERANCE: Final[float] = 3.0
DEFAULT_WORD_GAP_THRESHOLD: Final[float] = 10.0


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class ParsedCV(BaseModel):
    """Structured result returned by :class:`CVParser`."""

    file_path: str = Field(..., description="Absolute path of the source PDF file.")
    total_pages: int = Field(..., ge=1, description="Total number of pages in the PDF.")
    raw_text: str = Field(..., description="Cleaned, reading-order text extracted from all pages.")
    pages_text: list[str] = Field(
        default_factory=list,
        description="Per-page extracted text (same ordering as the PDF).",
    )

    @property
    def word_count(self) -> int:
        """Approximate word count of the extracted text."""
        return len(self.raw_text.split())


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class CVParser:
    """
    Extracts plain text from PDF-based CVs using *pdfplumber*, with built-in
    support for single- and multi-column layouts.

    ``page.extract_text(layout=True)`` is used for each page; it maps every
    character to a grid position so that column whitespace is preserved in the
    output text without any custom clustering logic.

    Parameters
    ----------
    row_tolerance:
        Passed through to pdfplumber's y_tolerance parameter.  Default: ``3.0``.
    word_gap_threshold:
        Retained for API compatibility but unused by the layout extractor.

    Examples
    --------
    >>> from src.parsers.pdf_parser import CVParser
    >>> parser = CVParser()
    >>> result = parser.parse("data/sample_cv.pdf")
    >>> print(result.raw_text[:200])
    """

    def __init__(
        self,
        row_tolerance: float = DEFAULT_ROW_TOLERANCE,
        word_gap_threshold: float = DEFAULT_WORD_GAP_THRESHOLD,
    ) -> None:
        self.row_tolerance = row_tolerance
        self.word_gap_threshold = word_gap_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, file_path: str | Path) -> ParsedCV:
        """
        Parse a PDF file and return structured text content.

        Parameters
        ----------
        file_path:
            Path to the PDF file.  Accepts both ``str`` and
            :class:`pathlib.Path`.

        Returns
        -------
        ParsedCV
            A Pydantic model containing the full extracted text and
            per-page breakdown.

        Raises
        ------
        FileNotFoundError
            If *file_path* does not point to an existing file.
        ValueError
            If the file extension is not ``.pdf``.
        RuntimeError
            If pdfplumber fails to open or read the PDF (e.g. the file is
            corrupted or password-protected).
        """
        path = self._validate_path(file_path)
        logger.info("Starting PDF parse: %s", path)

        pages_text: list[str] = []

        try:
            with pdfplumber.open(str(path)) as pdf:
                total_pages = len(pdf.pages)
                logger.debug("PDF opened successfully — %d page(s).", total_pages)

                for page_number, page in enumerate(pdf.pages, start=1):
                    try:
                        page_text = self._extract_page_text(page)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Page %d/%d could not be fully extracted: %s",
                            page_number,
                            total_pages,
                            exc,
                        )
                        page_text = ""
                    pages_text.append(page_text)

        except pdfplumber.utils.exceptions.PDFSyntaxError as exc:  # type: ignore[attr-defined]
            raise RuntimeError(
                f"PDF is malformed or corrupted and cannot be parsed: {path}"
            ) from exc
        except Exception as exc:
            # Catch-all for password-protected PDFs, IO errors, etc.
            raise RuntimeError(
                f"Unexpected error while opening PDF '{path}': {exc}"
            ) from exc

        raw_text = self._join_pages(pages_text)
        logger.info(
            "Parse complete — %d page(s), ~%d words.",
            total_pages,
            len(raw_text.split()),
        )

        return ParsedCV(
            file_path=str(path.resolve()),
            total_pages=total_pages,
            raw_text=raw_text,
            pages_text=pages_text,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_path(self, file_path: str | Path) -> Path:
        """
        Validate that *file_path* exists and has a ``.pdf`` extension.

        Parameters
        ----------
        file_path:
            Raw path supplied by the caller.

        Returns
        -------
        Path
            Resolved :class:`pathlib.Path` object.

        Raises
        ------
        FileNotFoundError
            If the path does not exist.
        ValueError
            If the extension is not ``.pdf``.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: '{path}'")
        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a .pdf file, got '{path.suffix}' for path: '{path}'"
            )
        return path

    def _extract_page_text(self, page: Page) -> str:
        """
        Extract and return reading-order text from a single PDF page.

        Delegates entirely to ``pdfplumber``'s ``extract_text(layout=True)``
        which builds a character grid for the page, so visual column spacing
        is preserved automatically without any custom clustering.

        Parameters
        ----------
        page:
            A pdfplumber :class:`~pdfplumber.page.Page` object.

        Returns
        -------
        str
            Extracted text for this page, or an empty string if no text could
            be found.
        """
        text = page.extract_text(layout=True, y_tolerance=self.row_tolerance)
        return (text or "").strip()

    @staticmethod
    def _join_pages(pages_text: list[str]) -> str:
        """
        Combine per-page text strings into one document-level string.

        Pages are separated by a form-feed character (``\\f``) followed by a
        newline, matching the convention used by many text-processing tools.

        Parameters
        ----------
        pages_text:
            Ordered list of per-page text strings.

        Returns
        -------
        str
            Single string containing all page content.
        """
        separator = "\n\f\n"
        return separator.join(p for p in pages_text if p).strip()


# ---------------------------------------------------------------------------
# Optional convenience function
# ---------------------------------------------------------------------------


def parse_cv(
    file_path: str | Path,
    row_tolerance: float = DEFAULT_ROW_TOLERANCE,
    word_gap_threshold: float = DEFAULT_WORD_GAP_THRESHOLD,
) -> ParsedCV:
    """
    Module-level convenience wrapper around :class:`CVParser`.

    Parameters
    ----------
    file_path:
        Path to the PDF file.
    row_tolerance:
        Forwarded to :class:`CVParser`.
    word_gap_threshold:
        Forwarded to :class:`CVParser`.

    Returns
    -------
    ParsedCV
        Parsed CV result.
    """
    parser = CVParser(
        row_tolerance=row_tolerance,
        word_gap_threshold=word_gap_threshold,
    )
    return parser.parse(file_path)
