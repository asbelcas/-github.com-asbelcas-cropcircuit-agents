#!/usr/bin/env python3
"""
Data Cleaner - Professional Data Cleaning Tool
Cleans and standardizes CSV, JSON, and Excel files.

Usage:
  python data_cleaner.py data.csv
  python data_cleaner.py data.csv --output clean.csv
  python data_cleaner.py data.json --format json
  python data_cleaner.py data.xlsx --format excel --sheet Sheet1
  python data_cleaner.py data.csv --fill-method ffill --normalize-text --report
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Missing dependency: pip install pandas openpyxl")
    sys.exit(1)


def load_file(path, fmt, sheet=None):
    """Load CSV, JSON, or Excel into a DataFrame."""
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    if fmt == "csv":
        # Try to detect encoding
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        print("Error: could not detect file encoding.")
        sys.exit(1)

    elif fmt == "json":
        try:
            return pd.read_json(path)
        except ValueError:
            print("Error reading JSON. If this is newline-delimited JSON, use --format jsonl.")
            sys.exit(1)

    elif fmt == "jsonl":
        try:
            return pd.read_json(path, lines=True)
        except Exception as e:
            print(f"Error reading JSONL: {e}")
            sys.exit(1)

    elif fmt == "excel":
        try:
            return pd.read_excel(path, sheet_name=sheet or 0)
        except Exception as e:
            print(f"Error reading Excel: {e}")
            sys.exit(1)

    else:
        print(f"Unsupported format: {fmt}")
        sys.exit(1)


def save_file(df, path, fmt):
    """Save DataFrame to the appropriate format."""
    if fmt == "csv":
        df.to_csv(path, index=False, encoding="utf-8")
    elif fmt == "json":
        df.to_json(path, orient="records", indent=2, force_ascii=False)
    elif fmt == "jsonl":
        df.to_json(path, orient="records", lines=True, force_ascii=False)
    elif fmt == "excel":
        df.to_excel(path, index=False)
    print(f"Saved: {path}")


def clean(df, fill_method=None, normalize_text=False, normalize_headers=False,
          drop_empty_cols=True, drop_dupes=True):
    """
    Apply a sequence of cleaning steps and return (cleaned_df, report_dict).
    """
    report = {}
    original_rows = len(df)
    original_cols = len(df.columns)

    # 1. Drop fully-empty rows
    before = len(df)
    df = df.dropna(how="all")
    report["empty_rows_removed"] = before - len(df)

    # 2. Drop fully-empty columns
    if drop_empty_cols:
        before_cols = len(df.columns)
        df = df.dropna(axis=1, how="all")
        report["empty_cols_removed"] = before_cols - len(df.columns)

    # 3. Strip leading/trailing whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # 4. Replace empty strings with NaN (consistent nulls)
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    # 5. Normalize text (lowercase + collapse internal whitespace)
    if normalize_text:
        for col in str_cols:
            df[col] = df[col].str.lower().str.replace(r"\s+", " ", regex=True)
        report["text_normalized"] = True

    # 6. Normalize column headers
    if normalize_headers:
        df.columns = (
            pd.Index(df.columns)
            .str.strip()
            .str.lower()
            .str.replace(r"[\s\-/]+", "_", regex=True)
            .str.replace(r"[^\w]", "", regex=True)
        )
        report["headers_normalized"] = True

    # 7. Fill missing values
    if fill_method == "ffill":
        df = df.ffill()
        report["fill_method"] = "forward-fill"
    elif fill_method == "bfill":
        df = df.bfill()
        report["fill_method"] = "backward-fill"
    elif fill_method == "zero":
        num_cols = df.select_dtypes(include="number").columns
        df[num_cols] = df[num_cols].fillna(0)
        report["fill_method"] = "zero (numeric columns)"

    # 8. Remove duplicate rows
    if drop_dupes:
        before = len(df)
        df = df.drop_duplicates()
        report["duplicates_removed"] = before - len(df)

    report["rows_before"] = original_rows
    report["rows_after"] = len(df)
    report["cols_before"] = original_cols
    report["cols_after"] = len(df.columns)
    report["null_cells_remaining"] = int(df.isna().sum().sum())

    return df, report


def print_report(report, input_path, output_path):
    print(f"\n{'─'*55}")
    print(f"  Data Cleaning Report")
    print(f"{'─'*55}")
    print(f"  Input:   {input_path}")
    print(f"  Output:  {output_path}")
    print(f"{'─'*55}")
    print(f"  Rows:    {report['rows_before']:,}  →  {report['rows_after']:,}"
          f"  ({report['rows_before'] - report['rows_after']:,} removed)")
    print(f"  Columns: {report['cols_before']}  →  {report['cols_after']}"
          f"  ({report['cols_before'] - report['cols_after']} removed)")

    if report.get("empty_rows_removed"):
        print(f"  Empty rows removed:    {report['empty_rows_removed']:,}")
    if report.get("empty_cols_removed"):
        print(f"  Empty cols removed:    {report['empty_cols_removed']}")
    if report.get("duplicates_removed"):
        print(f"  Duplicates removed:    {report['duplicates_removed']:,}")
    if report.get("fill_method"):
        print(f"  Null fill method:      {report['fill_method']}")
    if report.get("text_normalized"):
        print(f"  Text normalized:       yes (lowercase, whitespace)")
    if report.get("headers_normalized"):
        print(f"  Headers normalized:    yes (snake_case)")

    print(f"  Null cells remaining:  {report['null_cells_remaining']:,}")
    print(f"{'─'*55}\n")


def detect_format(path):
    ext = Path(path).suffix.lower()
    return {"csv": "csv", ".csv": "csv", ".json": "json", ".jsonl": "jsonl",
            ".xlsx": "excel", ".xls": "excel"}.get(ext, "csv")


def main():
    parser = argparse.ArgumentParser(
        description="Clean and standardize CSV, JSON, and Excel files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", help="Input file (CSV, JSON, or Excel)")
    parser.add_argument("--output", help="Output file path (default: <input>_clean.<ext>)")
    parser.add_argument("--format", choices=["csv", "json", "jsonl", "excel"],
                        help="Force input format (auto-detected by default)")
    parser.add_argument("--sheet", help="Excel sheet name (default: first sheet)")
    parser.add_argument("--fill-method", choices=["ffill", "bfill", "zero"],
                        help="How to fill missing values")
    parser.add_argument("--normalize-text", action="store_true",
                        help="Lowercase and collapse whitespace in text columns")
    parser.add_argument("--normalize-headers", action="store_true",
                        help="Convert column names to snake_case")
    parser.add_argument("--keep-dupes", action="store_true",
                        help="Do not remove duplicate rows")
    parser.add_argument("--report", action="store_true",
                        help="Print a detailed cleaning report")

    args = parser.parse_args()

    fmt = args.format or detect_format(args.input)

    # Determine output path
    if args.output:
        out_path = args.output
    else:
        p = Path(args.input)
        out_path = str(p.parent / f"{p.stem}_clean{p.suffix}")

    df = load_file(args.input, fmt, args.sheet)
    print(f"Loaded {args.input}: {len(df):,} rows, {len(df.columns)} columns")

    df, report = clean(
        df,
        fill_method=args.fill_method,
        normalize_text=args.normalize_text,
        normalize_headers=args.normalize_headers,
        drop_dupes=not args.keep_dupes,
    )

    save_file(df, out_path, fmt)

    if args.report:
        print_report(report, args.input, out_path)
    else:
        removed = report["rows_before"] - report["rows_after"]
        dupes = report.get("duplicates_removed", 0)
        print(f"Cleaned: {removed:,} rows removed ({dupes:,} duplicates)")


if __name__ == "__main__":
    main()
