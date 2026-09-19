# CropCircuit Privacy Model

CropCircuit's public farm tools are designed to minimize unnecessary data collection, but **local-first does not mean risk-free or magically anonymous**.

This document states what the current architecture protects, what it does not, and where the privacy boundary changes.

## 1. Local operational data

Tools such as the Labor Log, Chore Scheduler, Workspace Backup, Opportunity Analyzer, Schedule Calibrator, Chore Load Planner, and Weekly Operations Brief are designed to work with browser-local data.

CropCircuit does not require a central account for these workflows.

### What this reduces

When a tool runs entirely in the browser and does not transmit the farm record:

- CropCircuit does not need to receive the raw task log
- exact dates do not need to leave the device
- free-text notes do not need to leave the device
- a central CropCircuit database does not become a necessary point of compromise

### What this does not protect against

Local data can still be exposed through:

- a compromised or shared device
- malicious browser extensions
- someone with access to the browser profile
- browser sync behavior outside CropCircuit's control
- exported CSV or JSON files
- screenshots or printed reports
- backups stored insecurely
- operating-system or disk compromise

Users should treat workspace backups and raw labor CSVs as private farm records.

## 2. Browser storage

The current local workspace uses browser `localStorage`.

That is convenient and widely available, but it is not an encrypted vault.

Clearing browser/site data can delete records.

The Workspace Backup tool exists so users can make their own portable backups.

CropCircuit does not claim browser storage is appropriate for highly sensitive secrets.

Do not put passwords, account credentials, government identifiers, medical information, or similar secrets into free-text farm notes.

## 3. Static hosting and network logs

A tool may contain no analytics while the infrastructure serving the file still produces ordinary server/network logs.

For example, a static host, CDN, internet provider, or browser vendor may observe normal web requests according to its own policies.

"No analytics in the tool" means CropCircuit's code does not add tracking scripts or intentionally transmit the farm record. It does not mean the internet becomes invisible.

## 4. Funding data

The Michigan Farm Funding Radar is public information normalized from linked sources.

It does not contain a user's application history.

The embedded funding widget fetches public funding data. A host serving that data may therefore see a normal request for the public file.

## 5. Anonymous benchmark records

The benchmark layer is separate from the raw workspace.

The privacy transform deliberately drops fields such as:

- farm name
- person name
- email and phone
- street address
- county and ZIP
- exact acreage
- exact wage
- exact revenue
- exact dates
- free-text task names
- free-text notes

The benchmark uses coarse bands and category shares instead.

## 6. k-anonymity floor

CropCircuit's benchmark aggregator defaults to suppressing cohort statistics until at least **5 records** are present.

This reduces singling-out risk.

It does **not** prove perfect anonymity.

Risks can remain when:

- a cohort is socially obvious despite coarse fields
- outside information can be combined with the published statistics
- many overlapping queries reveal information indirectly
- records are not genuinely independent

Therefore the current k=5 rule is a publication floor, not a mathematical privacy guarantee.

## 7. No public benchmark dataset yet

CropCircuit currently publishes benchmark **tooling and a specification**, not a populated public farm benchmark dataset.

That is intentional.

Privacy controls should be evaluated before real contributed benchmark data is released.

## 8. Future institutional deployments

If an institution later hosts shared farm data, that changes the threat model substantially.

A server-backed deployment should have its own documented:

- data controller / processor roles
- retention policy
- access controls
- encryption strategy
- deletion process
- incident response
- consent and contribution terms
- minimum cohort and query controls

The local-first public toolkit should not be used to imply those server-side controls already exist.

## Design rule

**Collect the least data necessary for the useful calculation. Keep raw operational detail local whenever possible. Do not call coarse aggregation "anonymous" without stating its limits.**
