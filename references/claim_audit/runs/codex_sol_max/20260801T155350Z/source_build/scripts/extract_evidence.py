#!/usr/bin/env python3
"""Extract one-based physical PDF pages without altering the source."""

from __future__ import annotations

import argparse
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("start", type=int, nargs="?", help="First physical PDF page, one-based")
    parser.add_argument("end", type=int, nargs="?", help="Last physical PDF page, one-based and inclusive")
    parser.add_argument("--pages", type=int, nargs="+", help="Discrete physical PDF pages, one-based")
    args = parser.parse_args()
    reader = PdfReader(str(args.source))
    if args.pages:
        if args.start is not None or args.end is not None:
            raise SystemExit("Use either start/end or --pages, not both")
        selected_pages = list(dict.fromkeys(args.pages))
    else:
        if args.start is None or args.end is None:
            raise SystemExit("Provide start/end or --pages")
        if args.end < args.start:
            raise SystemExit(f"Invalid descending page range {args.start}-{args.end}")
        selected_pages = list(range(args.start, args.end + 1))
    if not selected_pages or min(selected_pages) < 1 or max(selected_pages) > len(reader.pages):
        raise SystemExit(f"Invalid physical pages {selected_pages}; source has {len(reader.pages)} pages")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    for physical_page in selected_pages:
        writer.add_page(reader.pages[physical_page - 1])
    temporary_output = args.output.with_suffix(args.output.suffix + ".tmp")
    with temporary_output.open("wb") as handle:
        writer.write(handle)
    temporary_output.replace(args.output)
    print(f"Extracted physical PDF pages {selected_pages} to {args.output}")


if __name__ == "__main__":
    main()
