#!/usr/bin/env python3
"""Render a UTF-8 Markdown audit report to a polished PDF."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from xml.sax.saxutils import escape

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        CondPageBreak,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as error:
    raise SystemExit(
        "Для PDF установите ReportLab: python3 -m pip install reportlab"
    ) from error


FONT_CANDIDATES = [
    (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ),
]


def register_fonts() -> tuple[str, str]:
    for regular_path, bold_path in FONT_CANDIDATES:
        if Path(regular_path).exists() and Path(bold_path).exists():
            pdfmetrics.registerFont(TTFont("AuditRegular", regular_path))
            pdfmetrics.registerFont(TTFont("AuditBold", bold_path))
            return "AuditRegular", "AuditBold"
    raise SystemExit(
        "Не найден Unicode-шрифт с кириллицей. Установите DejaVu Sans или Arial."
    )


def inline_markup(text: str) -> str:
    escaped = escape(text.strip())
    escaped = re.sub(r"`([^`]+)`", r"<font name='AuditRegular' color='#334155'>\1</font>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    return escaped


def table_widths(headers: list[str], available: float) -> list[float]:
    column_count = len(headers)
    if "Code" in headers:
        ratios = [0.04, 0.09, 0.22, 0.09, 0.10, 0.46]
    elif "Источник" in headers and column_count == 6:
        ratios = [0.07, 0.27, 0.08, 0.18, 0.20, 0.20]
    elif column_count == 3:
        ratios = [0.18, 0.32, 0.50]
    elif column_count == 2:
        ratios = [0.28, 0.72]
    else:
        ratios = [1 / column_count] * column_count
    return [available * ratio for ratio in ratios]


def parse_table(lines: list[str], styles: dict[str, ParagraphStyle], available: float) -> Table:
    rows: list[list[Paragraph]] = []
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if index == 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        style = styles["table_header"] if not rows else styles["table_cell"]
        rows.append([Paragraph(inline_markup(cell), style) for cell in cells])
    table = Table(
        rows,
        colWidths=table_widths(
            [cell.strip() for cell in lines[0].strip().strip("|").split("|")],
            available,
        ),
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_styles(regular: str, bold: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "AuditTitle",
            parent=base["Title"],
            fontName=bold,
            fontSize=22,
            leading=27,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "AuditH2",
            parent=base["Heading2"],
            fontName=bold,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F766E"),
            spaceBefore=13,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "AuditH3",
            parent=base["Heading3"],
            fontName=bold,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "AuditBody",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "AuditBullet",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=8.5,
            leading=12,
            leftIndent=13,
            firstLineIndent=-8,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=3,
        ),
        "quote": ParagraphStyle(
            "AuditQuote",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=8.5,
            leading=12,
            leftIndent=10,
            rightIndent=10,
            borderColor=colors.HexColor("#0F766E"),
            borderWidth=0,
            borderPadding=7,
            backColor=colors.HexColor("#ECFDF5"),
            textColor=colors.HexColor("#134E4A"),
            spaceAfter=7,
        ),
        "table_header": ParagraphStyle(
            "AuditTableHeader",
            fontName=bold,
            fontSize=7.2,
            leading=9,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "AuditTableCell",
            fontName=regular,
            fontSize=6.8,
            leading=8.5,
            textColor=colors.HexColor("#1E293B"),
        ),
    }


def markdown_to_story(markdown: str, styles: dict[str, ParagraphStyle], available: float) -> list:
    lines = markdown.splitlines()
    story: list = []
    paragraph_buffer: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph_buffer:
            story.append(Paragraph(inline_markup(" ".join(paragraph_buffer)), styles["body"]))
            paragraph_buffer.clear()

    while index < len(lines):
        line = lines[index]
        if line.startswith("|"):
            flush_paragraph()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(parse_table(table_lines, styles, available))
            story.append(Spacer(1, 4 * mm))
            continue
        if line.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), styles["title"]))
        elif line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[3:]), styles["h2"]))
        elif line.startswith("### "):
            flush_paragraph()
            story.append(CondPageBreak(34 * mm))
            story.append(Paragraph(inline_markup(line[4:]), styles["h3"]))
        elif line.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), styles["quote"]))
        elif re.match(r"^[-*] ", line):
            flush_paragraph()
            story.append(Paragraph("• " + inline_markup(line[2:]), styles["bullet"]))
        elif re.match(r"^\d+\. ", line):
            flush_paragraph()
            number, content = line.split(". ", 1)
            story.append(Paragraph(f"{number}. " + inline_markup(content), styles["bullet"]))
        elif not line.strip():
            flush_paragraph()
        else:
            paragraph_buffer.append(line.strip())
        index += 1
    flush_paragraph()
    return story


def draw_page(canvas, document) -> None:
    canvas.saveState()
    page_width, page_height = landscape(A4)
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(18 * mm, 14 * mm, page_width - 18 * mm, 14 * mm)
    canvas.setFont("AuditRegular", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(18 * mm, 9 * mm, "ExFlow — аудит финансовых API")
    canvas.drawRightString(page_width - 18 * mm, 9 * mm, f"Страница {document.page}")
    canvas.restoreState()


def main() -> int:
    parser = argparse.ArgumentParser(description="Преобразовать Markdown-аудит ExFlow в PDF.")
    parser.add_argument("input_markdown", type=Path)
    parser.add_argument("output_pdf", type=Path)
    args = parser.parse_args()

    if not args.input_markdown.is_file():
        raise SystemExit(f"Markdown не найден: {args.input_markdown}")
    regular, bold = register_fonts()
    args.output_pdf.parent.mkdir(parents=True, exist_ok=True)
    page_size = landscape(A4)
    document = SimpleDocTemplate(
        str(args.output_pdf),
        pagesize=page_size,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=19 * mm,
        title="Отчёт об аудите финансовых API ExFlow",
        author="ExFlow API Audit Skill",
    )
    styles = build_styles(regular, bold)
    available = page_size[0] - document.leftMargin - document.rightMargin
    story = markdown_to_story(
        args.input_markdown.read_text(encoding="utf-8"), styles, available
    )
    if not story:
        story = [Paragraph("Пустой отчёт", styles["title"]), PageBreak()]
    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(args.output_pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
