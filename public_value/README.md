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
