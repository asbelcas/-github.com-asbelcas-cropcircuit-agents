# Sales CSV Import Mapper

Many farms already have sales data in another system or spreadsheet.

The Sales CSV Import Mapper converts a generic CSV export into the record format used by CropCircuit's [Offline Farm Sales Log](SALES_LOG.md).

## Why it is generic

CropCircuit does not claim a vendor-specific integration unless one has actually been tested against that vendor's documented/exported format.

Instead, the mapper lets the operator explicitly map columns from the file they have.

That means it can often work with exports from:

- point-of-sale systems
- invoice systems
- online storefronts
- spreadsheets
- manually consolidated sales records

without pretending those sources all use the same schema.

## Fields

The mapper supports:

- date — required
- channel
- item / description
- gross amount — required
- payment fees
- refunds / discounts
- direct costs

If no channel column exists, the operator can supply one fixed channel label for the imported file.

## Currency parsing

The mapper strips common formatting characters such as dollar signs and commas before parsing numeric values.

It does not perform currency conversion.

## Outputs

- canonical CropCircuit sales CSV
- JSON backup directly compatible with the Offline Farm Sales Log

## Privacy

The source CSV stays in the browser.

No upload, analytics, or server processing is required.

## Accounting boundary

The mapper transforms fields only.

It does not determine whether a column is revenue, taxable income, cost of goods sold, a deductible expense, or another accounting category.
