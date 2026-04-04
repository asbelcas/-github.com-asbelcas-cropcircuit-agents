# Data Cleaner — Clean CSV, JSON & Excel Files with Audit Report

One command to clean a messy data file and see exactly what changed.

## Install

```bash
pip install pandas openpyxl
```

## Basic usage

```bash
# Clean a CSV (writes data_clean.csv)
python product.py data.csv

# Clean and see what changed
python product.py data.csv --report

# Specify output path
python product.py data.csv --output cleaned/data.csv --report
```

## Supported formats

```bash
# CSV (auto-detected by extension)
python product.py export.csv --report

# JSON or JSONL (newline-delimited JSON)
python product.py records.json --format json --report

# Excel
python product.py report.xlsx --format excel --report

# Excel — specific sheet
python product.py report.xlsx --format excel --sheet "Q1 Data" --report
```

## What it cleans (always on)

- Removes fully empty rows and columns
- Strips leading/trailing whitespace from every text cell
- Replaces blank strings (`""`, `"  "`) with proper null values
- Removes duplicate rows

## Optional cleaning steps

```bash
# Fill missing values forward (useful for merged cells exported from Excel)
python product.py data.csv --fill-method ffill

# Fill missing values backward
python product.py data.csv --fill-method bfill

# Fill missing numbers with 0
python product.py data.csv --fill-method zero

# Lowercase all text and collapse extra whitespace
python product.py data.csv --normalize-text

# Convert column names to snake_case (e.g. "First Name" → "first_name")
python product.py data.csv --normalize-headers

# Skip duplicate removal
python product.py data.csv --keep-dupes
```

## Audit report

`--report` prints a summary of every change made:

```
───────────────────────────────────────────────────────
  Data Cleaning Report
───────────────────────────────────────────────────────
  Input:   contacts.csv
  Output:  contacts_clean.csv
───────────────────────────────────────────────────────
  Rows:    10,432  →  9,891  (541 removed)
  Columns: 18  →  16  (2 removed)
  Empty rows removed:    48
  Empty cols removed:    2
  Duplicates removed:    493
  Null cells remaining:  1,204
───────────────────────────────────────────────────────
```

## All options

| Flag | Description |
|------|-------------|
| `--output FILE` | Output path (default: `<input>_clean.<ext>`) |
| `--format csv\|json\|excel` | Force format (auto-detected by default) |
| `--sheet NAME` | Excel sheet name (default: first sheet) |
| `--fill-method ffill\|bfill\|zero` | How to fill missing values |
| `--normalize-text` | Lowercase + collapse whitespace in text columns |
| `--normalize-headers` | Convert column names to snake_case |
| `--keep-dupes` | Skip duplicate removal |
| `--report` | Print audit report after cleaning |

## License

Commercial use license included with purchase. You may use this script in
your own projects and for clients. Redistribution for resale is not permitted.
