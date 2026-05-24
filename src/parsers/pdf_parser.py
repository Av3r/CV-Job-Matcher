"""
src/parsers/pdf_parser.py
=========================
Robust PDF text extractor with multi-column layout support.

Strategy for multi-column detection
-------------------------------------
Instead of relying on pdfplumber's default "naive" left-to-right text
concatenation, we extract individual *words* together with their bounding-box
coordinates (x0, top, x1, bottom).  We then:

1. Cluster words into "visual rows" by grouping words whose vertical midpoints
   are within a configurable tolerance of each other.
2. Within each row we sort words by their x0 coordinate (left edge).
3. We join sorted words with spaces, then join rows with newlines.

This approach produces a reading order that closely mirrors how a human would
read a two- (or three-) column résumé, without needing prior knowledge of how
many columns exist on a given page.
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

#: Vertical tolerance (in PDF points, 1 pt ≈ 0.353 mm) used to decide
#: whether two words belong to the same visual row.
DEFAULT_ROW_TOLERANCE: Final[float] = 3.0

#: Horizontal gap (in PDF points) between two words that triggers insertion
#: of an extra space in the output, helping to separate column content.
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

    Parameters
    ----------
    row_tolerance:
        Maximum vertical distance (in PDF points) between the midpoints of two
        words for them to be considered part of the same text row.
        Increase this value for PDFs with large leading; decrease for dense
        layouts.  Default: ``3.0`` pt.
    word_gap_threshold:
        Horizontal distance (in PDF points) between the right edge of one word
        and the left edge of the next word in the same row, above which an
        extra space character is inserted in the output.  This helps to visually
        separate content from adjacent columns.  Default: ``10.0`` pt.

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

        The algorithm works as follows:

        1. Extract all words with their bounding boxes via
           ``page.extract_words()``.
        2. Group words into visual rows using :meth:`_cluster_into_rows`.
        3. Within each row, sort words left-to-right by x0 coordinate.
        4. Join words in a row with a single space (inserting an extra space
           when the gap between adjacent words exceeds
           :attr:`word_gap_threshold`).
        5. Join rows with newline characters.

        If ``extract_words`` returns nothing, fall back to
        ``page.extract_text()`` so that simple single-column PDFs always
        produce output.

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
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            use_text_flow=False,  # we do our own ordering
            extra_attrs=["fontname", "size"],
        )

        if not words:
            # Fallback: try the simple extractor (works fine for single-column)
            fallback = page.extract_text(x_tolerance=3, y_tolerance=3)
            return (fallback or "").strip()

        rows = self._cluster_into_rows(words)
        lines: list[str] = []

        for row in rows:
            # Sort left → right within the row
            row_sorted = sorted(row, key=lambda w: w["x0"])
            line_parts: list[str] = []

            for idx, word in enumerate(row_sorted):
                if idx > 0:
                    gap = word["x0"] - row_sorted[idx - 1]["x1"]
                    if gap > self.word_gap_threshold:
                        # Column separator — add extra whitespace for clarity
                        line_parts.append("  ")
                line_parts.append(word["text"])

            lines.append(" ".join(line_parts))

        return "\n".join(lines).strip()

    def _cluster_into_rows(
        self, words: list[dict]
    ) -> list[list[dict]]:
        """
        Group extracted word dicts into visual rows based on vertical position.

        Two words are placed in the same row when the absolute difference
        between their vertical midpoints is ≤ :attr:`row_tolerance`.

        The returned list is ordered top-to-bottom (ascending ``top`` value of
        the first word in each row).

        Parameters
        ----------
        words:
            List of word dicts as returned by
            ``pdfplumber.Page.extract_words()``.  Each dict must contain at
            least ``"top"`` and ``"bottom"`` keys.

        Returns
        -------
        list[list[dict]]
            A list of rows, where each row is itself a list of word dicts.
        """
        if not words:
            return []

        # Sort words top-to-bottom first so we iterate in page order
        sorted_words = sorted(words, key=lambda w: (w["top"] + w["bottom"]) / 2)

        rows: list[list[dict]] = []
        current_row: list[dict] = [sorted_words[0]]
        current_mid = (sorted_words[0]["top"] + sorted_words[0]["bottom"]) / 2

        for word in sorted_words[1:]:
            word_mid = (word["top"] + word["bottom"]) / 2
            if abs(word_mid - current_mid) <= self.row_tolerance:
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
                current_mid = word_mid

        rows.append(current_row)
        return rows

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
