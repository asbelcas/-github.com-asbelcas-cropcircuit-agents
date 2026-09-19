# Offline Farm Sales Log

The Sales Log provides a small direct-market operating record without pretending to be accounting software.

## Each record can contain

- date
- sales channel
- optional item / note
- gross amount
- payment fees
- refunds / discounts
- direct costs the operator chooses to assign

## Derived arithmetic

```text
net receipts
  = gross amount
    − payment fees
    − refunds / discounts

contribution after direct costs
  = net receipts
    − entered direct costs
```

## Channel summaries

For a selected date range the tool totals, by sales channel:

- number of records
- gross amount
- fees
- refunds / discounts
- net receipts
- entered direct costs
- contribution after entered direct costs

## Accounting boundary

These numbers are not automatically:

- taxable income
- accounting revenue under a chosen accounting method
- net profit
- cash flow
- inventory-adjusted gross margin

Those concepts can require additional records and professional accounting/tax treatment.

The tool is intentionally an **operational sales summary**.

## Privacy

The browser storage key is:

```text
cropcircuit_sales_log_v1
```

The tool exports CSV and JSON backup files.

No server sync or analytics are required.

## Reusable math

- `sales_math.js`
- `sales_math.test.mjs`
