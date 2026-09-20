# Spreadsheet Starter Kit

CropCircuit's browser tools are useful, but many farms already live in Excel, Google Sheets, LibreOffice, or another spreadsheet.

The starter kit provides **blank CSV templates** matching CropCircuit's open local data shapes so a farm can begin with ordinary spreadsheets and still move into the browser tools later.

## Templates

- [Labor log](templates/labor_log_template.csv)
- [Recurring chore schedule](templates/chore_schedule_template.csv)
- [Equipment maintenance](templates/equipment_maintenance_template.csv)
- [Equipment parts inventory](templates/parts_inventory_template.csv)
- [Harvest log](templates/harvest_log_template.csv)
- [Farm sales log](templates/sales_log_template.csv)
- [Empty Workspace 1.2 JSON](templates/workspace_1_2_empty.json)

## Why CSV

CSV is intentionally boring.

It can be opened by common spreadsheet software, inspected with a text editor, versioned, transformed with scripts, and imported by many systems.

CropCircuit does not require a proprietary workbook format to keep the basic operational record portable.

## Labor log columns

```text
date
category
task
chore_code
minutes
workers
worker_hours
notes
```

`chore_code` is optional.

`worker_hours` can be calculated from minutes and workers by CropCircuit tools.

## Chore schedule columns

```text
task
chore_code
category
first_date
frequency
interval
estimated_minutes
notes
```

Supported recurring frequencies in the current scheduler are:

- ONCE
- DAILY
- WEEKLY
- MONTHLY
- YEARLY

## Equipment maintenance columns

```text
equipment
service
current_hours
last_service_hours
interval_hours
last_service_date
interval_days
```

Intervals are operator/manufacturer-supplied.

## Parts inventory columns

```text
equipment
part_name
primary_part_number
alternate_part_numbers
supplier
storage_location
quantity_on_hand
reorder_threshold
preferred_order_quantity
```

Alternate part numbers are references only; CropCircuit does not assert compatibility.

## Harvest columns

```text
date
item
quantity
unit
destination
```

Unlike units should remain separate unless the operator has a valid conversion method.

## Sales columns

```text
date
channel
item
gross_amount
payment_fees
refunds_discounts
direct_costs
```

This is an operational sales record, not an accounting or tax schema.

## Migration path

A farm can start with the blank CSV files, then later use:

- Labor CSV Import Mapper
- Sales CSV Import Mapper
- Offline Farm Labor Log
- Offline Farm Sales Log
- Workspace Backup

without abandoning the original spreadsheet workflow.
