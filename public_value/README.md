# CropCircuit Public Value Assets

This directory contains reusable, machine-readable farm decision resources published for anyone to use without a sales call.

## Michigan Farm Funding Radar

`funding_radar.json` is a source-linked dataset of Michigan farm, food-system, conservation, and rural-business funding opportunities. It distinguishes:

- open opportunities
- continuous-signup programs
- paused programs / status warnings
- recently closed cycles worth planning for

Every record includes a primary source URL and a verification date.

Raw JSON:

`https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.json`

The dataset is deliberately useful before monetization. If it earns repeated external use, CropCircuit can later build alerts, calendar feeds, API access, or institution-facing versions around actual demand.

## Farm Chore Cost formula

A repeated chore can be valued before buying equipment or building automation:

`annual_hours = (minutes_per_occurrence / 60) × occurrences_per_week × weeks_per_year × workers`

`annual_labor_cost = annual_hours × hourly_labor_cost`

`annual_savings = annual_labor_cost × expected_time_reduction`

`payback_months = (one_time_fix_cost / annual_savings) × 12`

This is decision support, not financial or agronomic advice. Use conservative assumptions and verify program details at the linked primary sources.


## CropCircuit Farm Math

`farm_math.js` is a dependency-free ES module with reusable calculations for:

- annual task/labor cost
- simple equipment or workflow payback
- acreage-to-fence-line estimation
- user-supplied livestock water storage sizing
- sales-channel break-even transactions
- rectangular acreage conversion

CDN import:

`https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@main/public_value/farm_math.js`

The library deliberately avoids hidden biological or financial assumptions. Rates and costs are supplied by the caller.

## Licensing

Code in `public_value/` is available under the MIT license in `LICENSE-CODE.txt`.

The CropCircuit-authored arrangement, normalization, and metadata in the funding dataset are dedicated under CC0 1.0 to the extent CropCircuit has rights in them. Primary-source content remains subject to its original source terms.
