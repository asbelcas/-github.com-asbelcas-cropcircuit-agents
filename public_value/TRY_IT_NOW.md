# Try CropCircuit Now

GitHub Pages is not enabled on this repository yet.

Until that repository-admin step is completed, the public HTML tools can be previewed through **raw.githack.com**, a third-party caching proxy that serves GitHub-hosted HTML with browser-renderable content types.

CropCircuit does not operate raw.githack.

Its own documentation says HTML pages may show a one-time confirmation screen and that the development URL follows a branch while the CDN URL should use a fixed commit/tag.

Source: https://raw.githack.com/

## Current-development previews

These follow `main` and can change as CropCircuit changes.

- [Farm Ops Pocket Console](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/farm_ops_console.html)
- [Universal Farm CSV Mapper](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/universal_csv_mapper.html)
- [Weekly Farm Operations Brief](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/weekly_ops_brief.html)
- [Offline Farm Labor Log](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/farm_labor_log.html)
- [Equipment Maintenance Log](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/equipment_maintenance.html)
- [Equipment Parts Inventory](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/parts_inventory.html)
- [Harvest Log](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/harvest_log.html)
- [Farm Sales Log](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/sales_log.html)
- [Farmers Market Break-Even](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/market_day_break_even.html)
- [CSA Share Price & Break-Even](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/csa_break_even.html)
- [Funding Explorer](https://raw.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_explorer.html)

## Fixed 0.15.0 preview URLs

These point to commit `3cc0d81e523b72b63213bcbb571d5802470089bb`, so the files behind the URLs do not change.

- [Farm Ops Pocket Console — 0.15.0](https://rawcdn.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/3cc0d81e523b72b63213bcbb571d5802470089bb/public_value/farm_ops_console.html)
- [Universal Farm CSV Mapper — 0.15.0](https://rawcdn.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/3cc0d81e523b72b63213bcbb571d5802470089bb/public_value/universal_csv_mapper.html)
- [Weekly Farm Operations Brief — 0.15.0](https://rawcdn.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/3cc0d81e523b72b63213bcbb571d5802470089bb/public_value/weekly_ops_brief.html)
- [Farmers Market Break-Even — 0.15.0](https://rawcdn.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/3cc0d81e523b72b63213bcbb571d5802470089bb/public_value/market_day_break_even.html)
- [CSA Share Price & Break-Even — 0.15.0](https://rawcdn.githack.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/3cc0d81e523b72b63213bcbb571d5802470089bb/public_value/csa_break_even.html)

## Important local-storage caveat

Browser-local records are scoped to the web origin serving the page.

That means data entered while using a `raw.githack.com` preview will **not automatically appear** later under a GitHub Pages or CropCircuit production origin.

Before moving between origins:

1. export a Workspace JSON backup;
2. open the tool at the new origin;
3. restore or merge the backup there.

This is one reason CropCircuit keeps the workspace format portable.

## Prefer a local file?

For single-file tools such as the Pocket Console and standalone calculators, you can also open the source file on GitHub and use **Download raw file / Save as**.

Browser behavior for `file://` local storage varies, so export JSON/CSV backups if the record matters.

## Status

These preview links are a **temporary distribution bridge**, not a replacement for enabling GitHub Pages.

The repository-admin backlog still includes:

- enable Pages
- clean the malformed repository description
- add useful repository topics
- verify GitHub Actions execution
