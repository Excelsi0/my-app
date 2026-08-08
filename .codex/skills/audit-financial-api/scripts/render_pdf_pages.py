#!/usr/bin/env python3
"""Render every PDF page to PNG for visual QA when Poppler is unavailable."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    import pymupdf
except ImportError as error:
    raise SystemExit(
        "Установите PyMuPDF: python3 -m pip install pymupdf"
    ) from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Отрисовать все PDF-страницы в PNG.")
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--scale", type=float, default=1.5)
    args = parser.parse_args()

    if not args.input_pdf.is_file():
        raise SystemExit(f"PDF не найден: {args.input_pdf}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open(args.input_pdf)
    matrix = pymupdf.Matrix(args.scale, args.scale)
    for index, page in enumerate(document, 1):
        output = args.output_dir / f"page-{index:02d}.png"
        page.get_pixmap(matrix=matrix, alpha=False).save(output)
        print(output)
    print(f"pages={len(document)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
