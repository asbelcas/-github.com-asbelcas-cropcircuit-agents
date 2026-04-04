# CSV Processor — Merge, Split, Filter, Transform, Dedup & Profile

A command-line toolkit for every common CSV task. Run one command instead
of wrestling with a large file in Excel.

## Install

```bash
pip install pandas
```

## Commands

### merge — combine multiple CSVs into one
```bash
python product.py merge output.csv jan.csv feb.csv mar.csv
```

### split — break a large file into N-row chunks
```bash
python product.py split big_file.csv --rows 1000
# Creates: big_file_part001.csv, big_file_part002.csv, ...
```

### filter — keep only rows matching conditions
```bash
python product.py filter leads.csv --where "status=active"
python product.py filter leads.csv --where "status=active" "country=US"
```

### transform — rename columns, drop columns, normalize headers
```bash
# Rename columns
python product.py transform data.csv --rename "First Name:first_name" "Last Name:last_name"

# Drop unwanted columns
python product.py transform data.csv --drop "internal_id" "temp_flag"

# Convert all headers to snake_case
python product.py transform data.csv --lowercase-headers

# All at once
python product.py transform data.csv --rename "Full Name:name" --drop "junk" --lowercase-headers
```

### dedup — remove duplicate rows
```bash
# Remove fully duplicate rows
python product.py dedup contacts.csv

# Deduplicate by a specific column (e.g. email)
python product.py dedup contacts.csv --key email

# Deduplicate by multiple columns
python product.py dedup contacts.csv --key email company

# Keep last occurrence instead of first
python product.py dedup contacts.csv --key email --keep last
```

### stats — profile a CSV file
```bash
python product.py stats data.csv
```
Output shows: row count, column types, null counts, unique counts, top values,
duplicate row count. Useful for understanding a file before processing it.

## Output files

By default each command writes to `<input>_<command>.csv` (e.g. `data_filtered.csv`).
Use `--output myfile.csv` to specify a custom path.

## License

Commercial use license included with purchase. You may use this script in
your own projects and for clients. Redistribution for resale is not permitted.
