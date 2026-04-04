#!/usr/bin/env python3
"""
CSV Processor - Advanced CSV Manipulation Tool
Merge, split, filter, and transform CSV files.
"""

import pandas as pd
import sys

def merge_csvs(files, output):
    """Merge multiple CSV files"""
    dfs = [pd.read_csv(f) for f in files]
    merged = pd.concat(dfs, ignore_index=True)
    merged.to_csv(output, index=False)
    print(f"Merged {len(files)} files → {output} ({len(merged)} rows)")

def split_csv(input_file, rows_per_file):
    """Split CSV into multiple files"""
    df = pd.read_csv(input_file)
    chunks = [df[i:i+rows_per_file] for i in range(0, len(df), rows_per_file)]
    
    for i, chunk in enumerate(chunks):
        output = f"{input_file.replace('.csv', '')}_part{i+1}.csv"
        chunk.to_csv(output, index=False)
        print(f"Created: {output} ({len(chunk)} rows)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python csv_processor.py <command> [args]")
        sys.exit(1)
