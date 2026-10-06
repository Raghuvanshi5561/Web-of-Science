"""Command-line interface for merging Web of Science export files."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from .merge import deduplicate, find_wos_files, merge_wos_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wos-merge",
        description=(
            "Parse Web of Science (WoS) plain-text export files and merge them "
            "into a single de-duplicated CSV. Point it at a folder and it finds "
            "every export inside automatically."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  wos-merge ./Data_Aditya_Sir\n"
            "      Find and merge every WoS export under the folder.\n\n"
            "  wos-merge ./batch1 ./batch2 extra.txt\n"
            "      Merge several folders and/or individual files at once.\n\n"
            "  wos-merge ./exports --list\n"
            "      Preview which files would be merged, without writing anything.\n\n"
            "  wos-merge ./exports --pattern 'save*'\n"
            "      Restrict to files whose name matches a glob, if you prefer."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="PATH",
        help="One or more folders and/or files. Folders are searched for WoS exports.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Path to the output CSV. Defaults to 'Merge_WOS.csv' inside the first "
            "input folder (or the current directory if no folder is given)."
        ),
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default=None,
        help=(
            "Optional filename glob (e.g. 'save*' or '*.txt'). By default files "
            "are detected automatically by their content, so no pattern is needed."
        ),
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only look in each folder's top level instead of searching sub-folders.",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List the files that would be merged and exit without writing output.",
    )
    parser.add_argument(
        "--title-col",
        default="TI",
        help="Column used for title de-duplication (default: %(default)s).",
    )
    parser.add_argument(
        "--doi-col",
        default="DI",
        help="Column used for DOI de-duplication (default: %(default)s).",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Keep all records instead of removing duplicates.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Encoding for the output CSV (default: %(default)s).",
    )
    return parser


def _default_output(inputs: List[str]) -> str:
    for path in inputs:
        if os.path.isdir(path):
            return os.path.join(path, "Merge_WOS.csv")
    return os.path.join(os.getcwd(), "Merge_WOS.csv")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    missing = [p for p in args.inputs if not os.path.exists(p)]
    if missing:
        for path in missing:
            print(f"Error: path not found: {path!r}", file=sys.stderr)
        return 2

    files = find_wos_files(
        args.inputs,
        pattern=args.pattern,
        recursive=not args.no_recursive,
    )

    if not files:
        where = ", ".join(repr(p) for p in args.inputs)
        hint = (
            f" matching pattern {args.pattern!r}" if args.pattern else ""
        )
        print(f"No Web of Science export files found in {where}{hint}.", file=sys.stderr)
        return 1

    print(f"Found {len(files)} Web of Science file(s):")
    for path in files:
        print(f"  - {path}")

    # Preview mode: show what was found and stop.
    if args.list:
        return 0

    df = merge_wos_files(files)
    if df.empty:
        print("Error: no records were parsed from the input files.", file=sys.stderr)
        return 1

    total = len(df)
    if not args.no_dedup:
        df = deduplicate(df, title_col=args.title_col, doi_col=args.doi_col)
        print(f"\nParsed {total} record(s); {len(df)} remain after de-duplication.")
    else:
        print(f"\nParsed {total} record(s) (de-duplication disabled).")

    output = args.output or _default_output(args.inputs)
    output_dir = os.path.dirname(output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output, index=False, encoding=args.encoding)
    print(f"Wrote merged data to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
