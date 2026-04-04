#!/usr/bin/env python3
"""
CSV Processor - Advanced CSV Manipulation Tool
Merge, split, filter, transform, deduplicate, and profile CSV files.

Usage:
  python csv_processor.py merge output.csv file1.csv file2.csv file3.csv
  python csv_processor.py split big_file.csv --rows 1000
  python csv_processor.py filter data.csv --where "status=active"
  python csv_processor.py transform data.csv --rename "old_col:new_col" --drop "junk_col"
  python csv_processor.py dedup data.csv --key "email"
  python csv_processor.py stats data.csv
"""

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Missing dependency: pip install pandas openpyxl")
    sys.exit(1)


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_merge(args):
    """Merge multiple CSV files into one."""
    if len(args.inputs) < 2:
        print("Error: provide at least 2 input files to merge.")
        sys.exit(1)

    dfs = []
    for f in args.inputs:
        df = pd.read_csv(f)
        print(f"  Read {f}: {len(df):,} rows, {len(df.columns)} cols")
        dfs.append(df)

    merged = pd.concat(dfs, ignore_index=True)
    merged.to_csv(args.output, index=False)
    print(f"\nMerged {len(args.inputs)} files → {args.output}")
    print(f"Total rows: {len(merged):,}  |  Columns: {list(merged.columns)}")


def cmd_split(args):
    """Split a CSV into multiple files of N rows each."""
    df = pd.read_csv(args.input)
    rows = args.rows
    stem = Path(args.input).stem
    ext = Path(args.input).suffix
    out_dir = Path(args.input).parent

    chunks = [df[i:i + rows] for i in range(0, len(df), rows)]
    for i, chunk in enumerate(chunks, start=1):
        out = out_dir / f"{stem}_part{i:03d}{ext}"
        chunk.to_csv(out, index=False)
        print(f"  Created {out}  ({len(chunk):,} rows)")

    print(f"\nSplit into {len(chunks)} files of up to {rows:,} rows each.")


def cmd_filter(args):
    """Filter rows by one or more column conditions."""
    df = pd.read_csv(args.input)
    original_len = len(df)

    for condition in args.where:
        if "=" not in condition:
            print(f"Error: condition must be col=value, got: {condition!r}")
            sys.exit(1)
        col, value = condition.split("=", 1)
        col = col.strip()
        value = value.strip()
        if col not in df.columns:
            print(f"Error: column {col!r} not found. Available: {list(df.columns)}")
            sys.exit(1)
        # Try numeric comparison first
        try:
            df = df[df[col] == float(value)]
        except (ValueError, TypeError):
            df = df[df[col].astype(str).str.lower() == value.lower()]

    out = args.output or args.input.replace(".csv", "_filtered.csv")
    df.to_csv(out, index=False)
    print(f"Filtered: {original_len:,} → {len(df):,} rows  ({original_len - len(df):,} removed)")
    print(f"Output: {out}")


def cmd_transform(args):
    """Rename columns, drop columns, reorder, or add a computed column."""
    df = pd.read_csv(args.input)

    if args.rename:
        for mapping in args.rename:
            if ":" not in mapping:
                print(f"Error: --rename expects old:new format, got {mapping!r}")
                sys.exit(1)
            old, new = mapping.split(":", 1)
            if old not in df.columns:
                print(f"Warning: column {old!r} not found, skipping rename.")
            else:
                df = df.rename(columns={old: new})
                print(f"  Renamed: {old!r} → {new!r}")

    if args.drop:
        for col in args.drop:
            if col in df.columns:
                df = df.drop(columns=[col])
                print(f"  Dropped: {col!r}")
            else:
                print(f"  Warning: column {col!r} not found, skipping drop.")

    if args.lowercase_headers:
        df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
        print(f"  Headers lowercased and snake_cased.")

    out = args.output or args.input.replace(".csv", "_transformed.csv")
    df.to_csv(out, index=False)
    print(f"Output: {out}  ({len(df):,} rows, {len(df.columns)} cols)")


def cmd_dedup(args):
    """Remove duplicate rows, optionally keyed on specific columns."""
    df = pd.read_csv(args.input)
    original_len = len(df)

    subset = args.key if args.key else None
    if subset:
        missing = [c for c in subset if c not in df.columns]
        if missing:
            print(f"Error: key columns not found: {missing}")
            print(f"Available: {list(df.columns)}")
            sys.exit(1)

    keep = args.keep or "first"
    df = df.drop_duplicates(subset=subset, keep=keep)
    removed = original_len - len(df)

    out = args.output or args.input.replace(".csv", "_deduped.csv")
    df.to_csv(out, index=False)
    print(f"Deduplicated: {original_len:,} → {len(df):,} rows  ({removed:,} duplicates removed)")
    if subset:
        print(f"Key columns: {subset}")
    print(f"Output: {out}")


def cmd_stats(args):
    """Print a profile/summary of a CSV file."""
    df = pd.read_csv(args.input)
    print(f"\n{'─'*60}")
    print(f"File:     {args.input}")
    print(f"Rows:     {len(df):,}")
    print(f"Columns:  {len(df.columns)}")
    print(f"Size:     {Path(args.input).stat().st_size / 1024:.1f} KB")
    print(f"{'─'*60}")

    for col in df.columns:
        series = df[col]
        nulls = series.isna().sum()
        unique = series.nunique()
        null_pct = f"{nulls / len(df) * 100:.0f}%" if len(df) else "0%"

        if pd.api.types.is_numeric_dtype(series):
            print(f"  {col:<30} numeric   unique={unique:>6,}  nulls={nulls:>5,} ({null_pct})"
                  f"  min={series.min():.2g}  max={series.max():.2g}  mean={series.mean():.2g}")
        else:
            top = series.value_counts().index[0] if unique > 0 else "—"
            print(f"  {col:<30} text      unique={unique:>6,}  nulls={nulls:>5,} ({null_pct})"
                  f"  top={str(top)[:20]!r}")

    dupes = df.duplicated().sum()
    print(f"{'─'*60}")
    print(f"Duplicate rows: {dupes:,}")
    print()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CSV Processor — merge, split, filter, transform, dedup, profile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # merge
    p_merge = sub.add_parser("merge", help="Merge multiple CSVs into one")
    p_merge.add_argument("output", help="Output CSV file")
    p_merge.add_argument("inputs", nargs="+", help="Input CSV files")

    # split
    p_split = sub.add_parser("split", help="Split a CSV into N-row chunks")
    p_split.add_argument("input", help="Input CSV file")
    p_split.add_argument("--rows", type=int, default=1000,
                         help="Rows per output file (default: 1000)")

    # filter
    p_filter = sub.add_parser("filter", help="Filter rows by column values")
    p_filter.add_argument("input", help="Input CSV file")
    p_filter.add_argument("--where", nargs="+", required=True,
                          metavar="col=value",
                          help="One or more conditions: col=value")
    p_filter.add_argument("--output", help="Output file (default: <input>_filtered.csv)")

    # transform
    p_transform = sub.add_parser("transform", help="Rename/drop/clean columns")
    p_transform.add_argument("input", help="Input CSV file")
    p_transform.add_argument("--rename", nargs="+", metavar="old:new",
                             help="Rename columns, e.g. --rename 'First Name:first_name'")
    p_transform.add_argument("--drop", nargs="+", metavar="col",
                             help="Drop columns by name")
    p_transform.add_argument("--lowercase-headers", action="store_true",
                             help="Lowercase + snake_case all column names")
    p_transform.add_argument("--output", help="Output file (default: <input>_transformed.csv)")

    # dedup
    p_dedup = sub.add_parser("dedup", help="Remove duplicate rows")
    p_dedup.add_argument("input", help="Input CSV file")
    p_dedup.add_argument("--key", nargs="+", metavar="col",
                         help="Consider only these columns when finding duplicates")
    p_dedup.add_argument("--keep", choices=["first", "last", "none"], default="first",
                         help="Which duplicate to keep (default: first)")
    p_dedup.add_argument("--output", help="Output file (default: <input>_deduped.csv)")

    # stats
    p_stats = sub.add_parser("stats", help="Print a profile/summary of a CSV")
    p_stats.add_argument("input", help="Input CSV file")

    args = parser.parse_args()
    commands = {
        "merge": cmd_merge,
        "split": cmd_split,
        "filter": cmd_filter,
        "transform": cmd_transform,
        "dedup": cmd_dedup,
        "stats": cmd_stats,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
