"""
main.py
=======
Quick-start entry point for testing the CVParser manually.

Usage
-----
1. Place a PDF file inside the `data/` directory.
2. Run:
       python main.py data/your_cv.pdf

If you don't have a PDF handy, the script will run a short self-test using
a synthetic (programmatically created) PDF that does not require any
external file.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# ── Optional: generate a minimal test PDF if fpdf2 is available ────────────
try:
    from fpdf import FPDF  # type: ignore

    _FPDF_AVAILABLE = True
except ImportError:
    _FPDF_AVAILABLE = False

from src.parsers.pdf_parser import CVParser, ParsedCV

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Demo helpers
# ---------------------------------------------------------------------------


def _create_demo_pdf(output_path: Path) -> None:
    """
    Generate a minimal two-column demo PDF using fpdf2 (optional dependency).
    The file is written to *output_path*.
    """
    if not _FPDF_AVAILABLE:
        raise RuntimeError(
            "fpdf2 is not installed.  Run `pip install fpdf2` to enable "
            "automatic demo-PDF generation."
        )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # ── Left column ──────────────────────────────────────────────
    left_col_x = 10
    pdf.set_xy(left_col_x, 20)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Jane Doe", ln=True)

    pdf.set_xy(left_col_x, 30)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(90, 6, "Senior Python Engineer\njane.doe@example.com\n+48 600 000 000")

    pdf.set_xy(left_col_x, 60)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Skills", ln=True)
    pdf.set_xy(left_col_x, 70)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(90, 6, "Python  •  FastAPI  •  pdfplumber\nPydantic  •  PostgreSQL  •  Docker")

    # ── Right column ─────────────────────────────────────────────
    right_col_x = 115
    pdf.set_xy(right_col_x, 20)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Experience", ln=True)

    pdf.set_xy(right_col_x, 30)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(85, 6, (
        "2022–present  TechCorp — Lead Engineer\n"
        "2019–2022     DataLab — Python Developer\n"
        "2017–2019     StartupXYZ — Junior Dev"
    ))

    pdf.set_xy(right_col_x, 70)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Education", ln=True)
    pdf.set_xy(right_col_x, 80)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(85, 6, "M.Sc. Computer Science\nUniversity of Warsaw, 2017")

    pdf.output(str(output_path))
    logger.info("Demo PDF created at: %s", output_path)


def _print_result(result: ParsedCV) -> None:
    """Pretty-print a :class:`ParsedCV` to stdout."""
    separator = "─" * 60
    print(f"\n{separator}")
    print(f"  File       : {result.file_path}")
    print(f"  Pages      : {result.total_pages}")
    print(f"  Word count : {result.word_count}")
    print(separator)
    for i, page_text in enumerate(result.pages_text, start=1):
        print(f"\n[ Page {i} ]\n")
        print(page_text)
    print(f"\n{separator}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point.

    Parameters
    ----------
    argv:
        Command-line arguments.  Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code (0 = success, 1 = error).
    """
    args = argv if argv is not None else sys.argv[1:]

    if args:
        # User supplied a path on the command line
        pdf_path = Path(args[0])
    else:
        # No argument → try to generate (or reuse) a demo PDF
        demo_path = Path("data") / "demo_cv.pdf"
        if not demo_path.exists():
            if _FPDF_AVAILABLE:
                logger.info("No PDF path supplied — generating demo PDF …")
                demo_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    _create_demo_pdf(demo_path)
                except Exception as exc:
                    logger.error("Could not create demo PDF: %s", exc)
                    print(
                        "\n[ERROR] Could not generate a demo PDF.\n"
                        "Usage: python main.py data/your_cv.pdf\n"
                    )
                    return 1
            else:
                print(
                    "\n[INFO] No PDF path supplied and fpdf2 is not installed.\n"
                    "Usage: python main.py data/your_cv.pdf\n"
                    "       pip install fpdf2   # to enable auto demo generation\n"
                )
                return 1
        pdf_path = demo_path

    parser = CVParser()
    try:
        result = parser.parse(pdf_path)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except (ValueError, RuntimeError) as exc:
        logger.error("%s", exc)
        return 1

    _print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
