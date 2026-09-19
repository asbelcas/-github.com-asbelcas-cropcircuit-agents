# Public Value Changelog

## 2026-09-19 — value-first pivot

### Added
- Michigan Farm Funding Radar in JSON, CSV, Markdown, and iCalendar formats.
- JSON Schema for the funding dataset.
- JSON Feed 1.1 representation for feed readers and software consumers.
- Farm Chore Cost & Payback JavaScript module.
- CropCircuit Farm Math dependency-free utility library.
- Zero-dependency Farm Math tests.
- Single-file offline Farm Decision Calculator.
- Machine-readable public asset manifest.
- Private offline Farm Labor Log with local storage, labor-cost summaries, task ranking, CSV export, and printable reports.
- Browser-only Labor Opportunity Analyzer that imports time-study CSV, annualizes observations, ranks repeated tasks by labor cost, and exports the analysis.
- Equipment Cost Threshold Analyzer that converts measured labor economics into a maximum upfront-cost threshold under explicit simple-payback assumptions.
- Workflow Experiment Analyzer for descriptive before/after task-time comparisons, modeled annual labor value, and observed payback checks.
- Privacy-first small-farm benchmark schema, browser record builder, k-anonymous aggregator, and suppression tests. No public benchmark numbers are fabricated before real sample size exists.
- Reproducible labor-log-to-benchmark transformer that strips task-level details and emits only coarse benchmark fields.
- Private Benchmark Explorer that compares a coarse farm record with privacy-suppressed aggregate cohorts and refuses to expose statistics below the k threshold.
- End-to-end Farm Labor → Decision → Benchmark workflow guide.

### Distribution and durability
- Embeddable zero-dependency Funding Radar widget with county/status/tag filters.
- Standalone widget demo and integration documentation.
- Funding dataset validator that catches duplicate IDs, invalid URLs, expired open deadlines, and stale verification warnings.
- GitHub Actions checks on public-value changes plus a daily scheduled validation run.
- Farm Math tests are now part of automated repository checks.
- Dependency-free funding query CLI with county, tag, status, and deadline filters.
- Structured GitHub contribution form for funding additions and corrections.

### Funding radar expansion
- Michigan Good Food Fund 2026 Seed Awards.
- Michigan Craft Beverage Council FY27 Research & Education Grants.
- USDA FSA Supplemental Disaster Relief Program (SDRP).
- Michigan FSA emergency farm-loan disaster designations with October 13 deadline.
- Michigan NRCS EQIP and CSP continuous-signup status.
- REAP FY2026 pause/status warning.
- NCR-SARE Farmer Rancher Grant watch item.
- MDARD Specialty Crop and Value-Added program planning records.

### Verification policy
Every active or watch record now carries a primary source URL, a verification date, and a short verification note. Stale or paused opportunities are labeled instead of silently presented as open.

### Repository positioning
The previous RM-QPT front-page framing was archived. The public repository now leads with reusable tools, data, explicit assumptions, and utility-first design.
