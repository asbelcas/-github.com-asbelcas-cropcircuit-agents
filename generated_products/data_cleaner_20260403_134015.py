#!/usr/bin/env python3
"""
Data Cleaner - Professional Data Processing Tool
Cleans and standardizes CSV, JSON, and Excel files.
"""

import pandas as pd
import json
from pathlib import Path

def clean_csv(input_file, output_file=None):
    """Clean and standardize CSV file"""
    df = pd.read_csv(input_file)
    
    # Remove empty rows and columns
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')
    
    # Trim whitespace from strings
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    if output_file is None:
        output_file = input_file.replace('.csv', '_cleaned.csv')
    
    df.to_csv(output_file, index=False)
    print(f"Cleaned: {input_file} → {output_file}")
    print(f"Records: {len(df)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        clean_csv(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print("Usage: python data_cleaner.py <input.csv> [output.csv]")
