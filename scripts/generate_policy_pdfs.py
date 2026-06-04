"""
generate_policy_pdfs.py

Generates Redis Eats workshop PDFs from the Markdown source files in
data/source_markdown/. Outputs PDFs to data/pdfs/.

Usage:
    python scripts/generate_policy_pdfs.py

Requirements:
    pip install reportlab
"""

import re
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolve paths relative to this script's location so the script can be run
# from anywhere in the repo.
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
SOURCE_DIR = REPO_ROOT / "data" / "source_markdown"
OUTPUT_DIR = REPO_ROOT / "data" / "pdfs"

# ---------------------------------------------------------------------------
# PDF styling constants
# ---------------------------------------------------------------------------

# Page margins in points (1 inch = 72 points)
MARGIN = 54

# Font sizes for each element type
FONT_TITLE = 18
FONT_H2 = 13
FONT_H3 = 11
FONT_BODY = 10
FONT_TABLE_HEADER = 9
FONT_TABLE_BODY = 9

# Line spacing multipliers
LEADING_BODY = 14
LEADING_H2 = 18
LEADING_H3 = 15

# Brand colour (Redis red)
REDIS_RED = (0.87, 0.11, 0.11)


def build_pdf(md_path: Path, pdf_path: Path) -> None:
    """
    Convert a single Markdown file to a styled PDF using reportlab.

    Handles the following Markdown elements:
    - # H1 title
    - ## H2 section headings
    - ### H3 sub-headings
    - Paragraph text
    - Bullet lists (lines starting with -)
    - Horizontal rules (---)
    - Simple pipe tables (| col | col |)

    Args:
        md_path: Path to the input Markdown file.
        pdf_path: Path to write the output PDF.
    """
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, ListFlowable, ListItem,
    )

    # -----------------------------------------------------------------------
    # Read and pre-process Markdown source
    # -----------------------------------------------------------------------
    raw_text = md_path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()

    # -----------------------------------------------------------------------
    # Define paragraph styles
    # -----------------------------------------------------------------------
    base_styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "WorkshopTitle",
        parent=base_styles["Heading1"],
        fontSize=FONT_TITLE,
        leading=22,
        textColor=colors.Color(*REDIS_RED),
        spaceAfter=12,
    )

    style_h2 = ParagraphStyle(
        "WorkshopH2",
        parent=base_styles["Heading2"],
        fontSize=FONT_H2,
        leading=LEADING_H2,
        textColor=colors.Color(*REDIS_RED),
        spaceBefore=14,
        spaceAfter=4,
    )

    style_h3 = ParagraphStyle(
        "WorkshopH3",
        parent=base_styles["Heading3"],
        fontSize=FONT_H3,
        leading=LEADING_H3,
        textColor=colors.Color(0.2, 0.2, 0.2),
        spaceBefore=10,
        spaceAfter=2,
    )

    style_body = ParagraphStyle(
        "WorkshopBody",
        parent=base_styles["Normal"],
        fontSize=FONT_BODY,
        leading=LEADING_BODY,
        spaceAfter=6,
    )

    style_bullet = ParagraphStyle(
        "WorkshopBullet",
        parent=style_body,
        leftIndent=14,
        spaceAfter=3,
    )

    # -----------------------------------------------------------------------
    # Parse lines into reportlab flowables
    # -----------------------------------------------------------------------
    story = []

    # Collect bullet runs so they can be emitted as a ListFlowable
    bullet_buffer: list[str] = []

    def flush_bullets():
        """Emit accumulated bullet items as a ListFlowable and clear buffer."""
        nonlocal bullet_buffer
        if bullet_buffer:
            items = [
                ListItem(Paragraph(_escape(b), style_bullet), leftIndent=18)
                for b in bullet_buffer
            ]
            story.append(ListFlowable(items, bulletType="bullet", start="•"))
            story.append(Spacer(1, 4))
            bullet_buffer = []

    # Collect table rows for pipe-table detection
    table_buffer: list[list[str]] = []

    def flush_table():
        """Emit accumulated table rows as a styled Table and clear buffer."""
        nonlocal table_buffer
        if not table_buffer:
            return

        # Remove separator rows (lines of dashes/pipes with no real content)
        data_rows = [r for r in table_buffer if not all(
            re.match(r"^[-: ]+$", cell) for cell in r
        )]

        if not data_rows:
            table_buffer = []
            return

        # Build the Table
        col_count = max(len(r) for r in data_rows)
        # Pad short rows
        padded = [r + [""] * (col_count - len(r)) for r in data_rows]

        # Style: first row is the header
        tbl = Table(padded, repeatRows=1, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.93, 0.93, 0.93)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.Color(*REDIS_RED)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), FONT_TABLE_HEADER),
            ("FONTSIZE", (0, 1), (-1, -1), FONT_TABLE_BODY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 8))
        table_buffer = []

    def _escape(text: str) -> str:
        """Escape special XML characters for use inside reportlab Paragraphs."""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

    def _strip_inline(text: str) -> str:
        """Remove basic Markdown inline formatting (bold, italic, inline code)."""
        # Bold+italic ***text***
        text = re.sub(r"\*{3}(.+?)\*{3}", r"\1", text)
        # Bold **text**
        text = re.sub(r"\*{2}(.+?)\*{2}", r"\1", text)
        # Italic *text*
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        # Inline code `text`
        text = re.sub(r"`(.+?)`", r"\1", text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i]

        # -------------------------------------------------------------------
        # Pipe table rows
        # -------------------------------------------------------------------
        if line.strip().startswith("|"):
            flush_bullets()
            # Parse pipe-separated cells, stripping leading/trailing pipes
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table_buffer.append(cells)
            i += 1
            continue
        else:
            flush_table()

        # -------------------------------------------------------------------
        # Horizontal rule
        # -------------------------------------------------------------------
        if re.match(r"^-{3,}$", line.strip()):
            flush_bullets()
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.Color(0.75, 0.75, 0.75),
                                    spaceAfter=6, spaceBefore=6))
            i += 1
            continue

        # -------------------------------------------------------------------
        # H1 title
        # -------------------------------------------------------------------
        if line.startswith("# ") and not line.startswith("## "):
            flush_bullets()
            title_text = _escape(_strip_inline(line[2:].strip()))
            story.append(Paragraph(title_text, style_title))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # -------------------------------------------------------------------
        # H2 section heading
        # -------------------------------------------------------------------
        if line.startswith("## ") and not line.startswith("### "):
            flush_bullets()
            heading_text = _escape(_strip_inline(line[3:].strip()))
            story.append(Paragraph(heading_text, style_h2))
            i += 1
            continue

        # -------------------------------------------------------------------
        # H3 sub-heading
        # -------------------------------------------------------------------
        if line.startswith("### "):
            flush_bullets()
            heading_text = _escape(_strip_inline(line[4:].strip()))
            story.append(Paragraph(heading_text, style_h3))
            i += 1
            continue

        # -------------------------------------------------------------------
        # Bullet list item (- text)
        # -------------------------------------------------------------------
        if re.match(r"^[-*] ", line):
            # Strip the leading "- " or "* "
            item_text = _strip_inline(line[2:].strip())
            bullet_buffer.append(item_text)
            i += 1
            continue

        # -------------------------------------------------------------------
        # Empty line — flush bullets and add vertical space
        # -------------------------------------------------------------------
        if line.strip() == "":
            flush_bullets()
            story.append(Spacer(1, 4))
            i += 1
            continue

        # -------------------------------------------------------------------
        # Regular paragraph text
        # -------------------------------------------------------------------
        flush_bullets()
        para_text = _escape(_strip_inline(line.strip()))
        if para_text:
            story.append(Paragraph(para_text, style_body))
        i += 1

    # Flush anything remaining
    flush_bullets()
    flush_table()

    # -----------------------------------------------------------------------
    # Build PDF
    # -----------------------------------------------------------------------
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=LETTER,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=md_path.stem.replace("_", " ").title(),
        author="Redis Eats",
    )
    doc.build(story)
    print(f"  ✓ {pdf_path.name}")


def main():
    """Convert all Markdown files in SOURCE_DIR to PDFs in OUTPUT_DIR."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted(SOURCE_DIR.glob("*.md"))
    if not md_files:
        print(f"No Markdown files found in {SOURCE_DIR}")
        return

    print(f"Generating {len(md_files)} PDFs → {OUTPUT_DIR}\n")
    for md_path in md_files:
        pdf_path = OUTPUT_DIR / (md_path.stem + ".pdf")
        build_pdf(md_path, pdf_path)

    print(f"\nDone. {len(md_files)} PDFs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
