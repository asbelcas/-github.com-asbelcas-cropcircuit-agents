# Weekly Farm Operations Brief

The Weekly Farm Operations Brief is a browser-local report built from the CropCircuit workspace.

It combines five operational views without sending the raw workspace to a server.

## Report window

The user chooses:

- start date
- end date
- number of future days to inspect for recurring scheduled work

## Labor

The brief shows:

- labor entry count
- total worker-hours
- canonical chore-code coverage
- worker-hours by category
- highest-time repeated work

"Highest-time" is descriptive, not an efficiency score.

## Harvest

Harvest entries inside the report window are summarized by:

- crop / item
- unit
- entry count
- total quantity

Unlike units remain separate.

Harvest quantity is **not** converted into revenue.

## Direct-market sales

Sales records inside the report window are summarized by channel:

- gross amount
- fees and refunds / discounts
- net receipts
- entered direct costs
- contribution after entered direct costs

That last value is operational arithmetic, not accounting profit or taxable income.

## Equipment maintenance

The brief checks the current maintenance records as of the report end date.

Due / overdue status uses only the meter-hour and calendar intervals stored by the operator.

CropCircuit does not supply maintenance intervals.

## Parts inventory

The brief also shows the local equipment-parts inventory and flags rows at or below the operator-entered reorder threshold.

The report does not assert that alternate part numbers are compatible substitutes.

## Upcoming recurring work

The brief expands the local chore schedule after the report end date using the same recurrence logic as `schedule_math.js`.

## Privacy

The report is generated entirely in the browser from Workspace 1.2 data.

Free-text notes are deliberately not shown.

Printing or saving the brief creates a file outside the browser, so exported reports should be handled according to the farm's own privacy/recordkeeping practices.
