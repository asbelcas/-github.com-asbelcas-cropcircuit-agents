# User-Need Evidence — 2026-09-20

This note records the public community signals used to choose the next CropCircuit utilities.

It is **not market validation**, not a representative farmer survey, and not evidence of willingness to pay.

The purpose is narrower: stop inventing product ideas in a vacuum and document why a utility was built.

## Signal 1 — equipment maintenance still lives in simple systems

A July 2024 r/farming discussion asked how people manage equipment maintenance. Responses included:

- a barn whiteboard showing maintenance done / needed
- notes kept in operator manuals
- Excel / Office spreadsheets
- phone notes
- tracking filters, belts, seals, bearings, rebuild kits, and alternate vendor part numbers

Source:

https://www.reddit.com/r/farming/comments/1dvw8u5

A separate April 2026 r/tractors thread asked for a "more foolproof" small-farm system for preventive maintenance, fuel usage, and money spent; the existing plan was a spreadsheet updated monthly.

Source:

https://www.reddit.com/r/tractors/comments/1si7upt/how_do_you_track_maintenance_on_multiple_machines/

### CropCircuit response

This signal motivated:

- Offline Equipment Maintenance Log
- Equipment Parts Inventory
- reusable maintenance due-status math
- operator-entered part cross references
- JSON/CSV portability

CropCircuit still does not supply generic service intervals or assert that alternate parts are compatible.

## Signal 2 — spreadsheets remain a core farm recordkeeping surface

A January 2025 r/farming recordkeeping discussion includes farmers describing Excel as the place they track equipment, maintenance, seeding/harvest results, soil tests, crop plans, load tickets, bin contents, and financial records.

Source:

https://www.reddit.com/r/farming/comments/1ich8qw

A follow-up recordkeeping thread describes sales data living in several systems — accounting software, point of sale, and an online marketplace — and then being consolidated into spreadsheet raw-data tabs for crop-level comparisons.

Source:

https://www.reddit.com/r/farming/comments/1id1uon

### CropCircuit response

This signal motivated:

- Spreadsheet Starter Kit
- Labor CSV Import Mapper
- Sales CSV Import Mapper
- stable CSV contracts
- Workspace JSON backup
- package/data-schema documentation

The design goal is not "replace Excel."

It is:

**let a farm keep spreadsheets if that is what works, while making the data more portable and reusable.**

## Signal 3 — farms want checklist accountability without expensive complexity

A November 2023 r/farming post asked about a machine startup/service checklist app where workers can tick required checks and produce a report.

Source:

https://www.reddit.com/r/farming/comments/185vflv

### CropCircuit response

This signal motivated the Offline Equipment Checklist.

However, safety-critical checklist content is deliberately left to the operator's established manufacturer, regulatory, employer, or qualified service guidance.

CropCircuit records the checklist; it does not invent or certify it.

## Signal 4 — direct-market selling has meaningful time and fixed costs

A discussion about farmers markets highlights vendor fees, travel, and hours spent selling as costs that materially affect whether a market is worthwhile.

Source:

https://ru.reddit.com/r/homestead/comments/10quhnx/do_you_sell_products_at_local_farmers_markets_if/

### CropCircuit response

This signal supports explicit direct-market unit-economics tools:

- Farmers Market Break-Even Calculator
- CSA Share Price & Break-Even Calculator
- Offline Farm Sales Log

The calculators require the user to supply labor value, mileage cost, fees, variable costs, and price assumptions rather than embedding a "correct" answer.

## Current conclusion

The strongest repeated pattern is not "farmers need more dashboards."

It is:

- information lives in someone's head, a notebook, a whiteboard, or several spreadsheets;
- existing systems often do not interoperate cleanly;
- farmers value simple records that do not create more work than the task itself;
- equipment and direct-market decisions benefit from transparent arithmetic;
- portability matters.

That is why the current CropCircuit direction is:

**small local-first utilities + open data contracts + spreadsheet compatibility + optional machine-readable layers.**

## Commercial evidence status

As of this note:

- these public discussions are evidence of problems and workflows;
- they are not evidence that CropCircuit has product-market fit;
- they are not evidence that anyone will pay CropCircuit;
- no new earned revenue should be attributed to this research or the resulting tools until actual external payment is confirmed.
