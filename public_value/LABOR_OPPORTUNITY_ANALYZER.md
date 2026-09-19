# Farm Labor Opportunity Analyzer

This browser-only tool turns a short time study into a ranked list of repeated work by estimated annual labor cost.

It is designed to pair with the [Offline Farm Labor Log](farm_labor_log.html).

## Workflow

1. Use the labor log for a real observation period.
2. Export the log as CSV.
3. Open `labor_opportunity_analyzer.html`.
4. Choose the CSV.
5. Enter the number of days represented by the observation period.
6. Enter a labor-cost rate.
7. Enter a hypothetical percentage reduction.
8. Review which repeated tasks dominate annualized labor cost.

## Why annualize?

A 15-minute task can look trivial when viewed once. Repetition makes it expensive.

Annualization makes frequency visible, but it introduces an assumption: **the sample period is representative**. A two-week harvest sample should not be treated as a whole-year livestock sample. Seasonal operations should repeat the exercise across seasons.

## Privacy

All CSV parsing and calculations happen locally in the browser.

- no upload
- no account
- no analytics
- no network request

## What the "hypothetical savings" number means

It is simply:

```text
annualized labor cost × chosen reduction percentage
```

It does not assume that a particular machine, layout, or automation can actually produce that reduction. The point is to identify which tasks are economically worth investigating first.
