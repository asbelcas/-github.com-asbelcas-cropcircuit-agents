# Start Here

CropCircuit now contains many utilities. **You do not need to use all of them.**

Pick the smallest path that matches the problem you already have.

## Path A — "I already use spreadsheets"

Use this when your records already live in Excel, Google Sheets, LibreOffice, a POS export, or CSV files.

1. Keep your existing spreadsheet.
2. Read the [Spreadsheet Starter Kit](SPREADSHEET_STARTER_KIT.md) only if you want CropCircuit-compatible blank columns.
3. Open the [Universal Farm CSV Mapper](universal_csv_mapper.html).
4. Choose one target:
   - labor
   - recurring chores
   - equipment maintenance
   - parts inventory
   - harvest
   - sales
5. Map the source columns.
6. Export canonical CSV/JSON or add the valid rows to the local workspace.

**Do not retype records that already exist.**

## Path B — "I want one simple offline farm tool"

Start with the [Farm Ops Pocket Console](farm_ops_console.html).

It gives you:

- labor observations
- recurring chore schedule
- seven-day dashboard
- Workspace backup

Use it for a week before deciding whether another tool is useful.

Then add a specialized tool only when the farm actually has that problem.

Examples:

- repeated labor feels expensive → Labor Opportunity Analyzer
- planned chore times are wrong → Schedule Estimate Calibrator
- recurring chores bunch onto the same day → Chore Load Planner
- equipment service gets forgotten → Equipment Maintenance Log
- filters/belts/parts are hard to find → Parts Inventory
- crop quantities are scattered → Harvest Log
- sales channels are hard to compare → Sales Log

## Path C — "I just want to test the idea"

Start with the [Synthetic Demo Workspace](demo_workspace.html) if you want to see the local workflow without entering real records.

The demo can merge fictional `demo-` records into the local workspace and later remove only those demo IDs.

Then use the temporary runnable preview links in [Try CropCircuit Now](TRY_IT_NOW.md).

### If you do not want to load demo records

Use the temporary runnable preview links in [Try CropCircuit Now](TRY_IT_NOW.md).

GitHub Pages is not enabled yet, so those previews use a third-party static-file proxy.

Do not enter records you care about without exporting a backup.

## The core loop

CropCircuit is designed around a small operating loop:

```text
plan
  ↓
observe
  ↓
summarize
  ↓
find repeated cost / friction
  ↓
change one thing
  ↓
measure again
```

That is enough.

The benchmark, package exports, schemas, feeds, and machine-readable layers exist for people who need them. They are not prerequisites for using the farm tools.

## Useful next steps by problem

| Problem | Start with |
| --- | --- |
| "I don't know where my time goes." | Offline Farm Labor Log |
| "I already have a labor spreadsheet." | Universal Farm CSV Mapper |
| "I want someone else to clean/map my farm spreadsheets." | Assisted Farm Data Setup |
| "Our schedule is unrealistic." | Schedule Estimate Calibrator |
| "Too many chores land on the same day." | Farm Chore Load Planner |
| "I don't know whether an equipment purchase saves enough labor." | Equipment Cost Threshold Analyzer |
| "Maintenance gets missed." | Equipment Maintenance Log |
| "I can't find the right spare part." | Equipment Parts Inventory |
| "Workers need our established machine checks in one place." | Equipment Checklist |
| "I need harvest totals by crop." | Harvest Log |
| "Sales data is split across systems." | Universal Farm CSV Mapper or Sales CSV Import Mapper |
| "I want market-day break-even math." | Farmers Market Break-Even |
| "I need to pressure-test CSA pricing." | CSA Share Price & Break-Even |
| "I want a weekly operating picture." | Weekly Farm Operations Brief |
| "I need to share a summary without sending raw farm records." | Shareable Farm Operations Snapshot |
| "I need Michigan funding deadlines." | Michigan Farm Funding Explorer |

## Data ownership

The local-first tools are deliberately usable without a CropCircuit account.

Export the Workspace backup periodically if the data matters.

The backup is portable, but it is also private operational data. Store it accordingly.

## Commercial status

These tools are public utility work.

They do not imply CropCircuit has paying customers, product-market fit, or validated willingness to pay.

Usage and actual external payment are separate evidence.


## Optional assisted setup

If the free mapping tools solve the problem but you do not want to do the cleanup yourself, see [Assisted Farm Data Setup](farm_data_setup.html).

The pilot is a fixed $149 implementation job: up to three source exports / 1,500 rows, cleaned canonical files, Workspace 1.2, a mapping-quality note, and an Operations Snapshot when the data supports one.
