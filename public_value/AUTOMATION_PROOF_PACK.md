# CropCircuit Automation Proof Pack

CropCircuit's public repository contains reusable evidence for data-cleaning and workflow-automation work.

This page is intentionally evidence-based: it points to code that exists now and separates demonstrated capabilities from integration work that would still need to be built for a client.

## Demonstrated building blocks

### 1. CSV ingestion and column mapping
- Universal Farm CSV Mapper: `public_value/universal_csv_mapper.html`
- Sales CSV Import Mapper: `public_value/sales_csv_import_mapper.html`
- Labor CSV Import Mapper: `public_value/labor_csv_import_mapper.html`

These tools take inconsistent CSV columns, map them into explicit contracts, validate rows, and export normalized data.

### 2. Machine-readable schemas and contracts
- Contract registry: `public_value/data_contracts.json`
- Workspace schema: `public_value/workspace.schema.json`
- Labor-record schema: `public_value/farm_labor_record.schema.json`
- Decision-record schema: `public_value/decision_record.schema.json`

The general pattern is: define the contract first, validate inputs, preserve source fields when useful, and keep transformations inspectable.

### 3. Deterministic validation before probabilistic processing
CropCircuit uses ordinary code for rules that should not require an AI model: parsing, required fields, arithmetic, recurrence, duplicate-safe identifiers, thresholds, and schema validation.

Representative validators/tests:
- `public_value/validate_data_contracts.mjs`
- `public_value/validate_labor_contract.mjs`
- `public_value/validate_setup_delivery.mjs`
- `public_value/workspace.test.mjs`

For client automation, this same pattern keeps LLM calls focused on ambiguous or unstructured work instead of wasting tokens on deterministic checks.

### 4. Local-first review and human override
- Operations Snapshot: `public_value/operations_snapshot.html`
- Right Relationship Decision Gate: `public_value/right_relationship_gate.html`
- Assisted Setup Intake Builder: `public_value/assisted_setup_intake.html`

The design preference is to expose uncertainty, preserve review points, and avoid silently changing records when confidence is low.

### 5. Structured exports and handoff
Existing tools export or consume JSON, CSV, iCalendar, and browser-local Workspace data. The funding dataset is also published in machine-readable formats with a query CLI and integration recipes.

Relevant files:
- `public_value/FUNDING_INTEGRATIONS.md`
- `public_value/funding_query.mjs`
- `public_value/manifest.json`

## Reference automation architecture

For a typical CSV/Excel + LLM + Airtable/Sheets + Slack workflow:

```text
source file / form / API
        |
        v
input normalization
        |
        v
deterministic validation
  - required fields
  - type checks
  - duplicate keys
  - known mappings
        |
        +---- invalid/ambiguous ---> review queue
        |
        v
LLM step only where useful
  - classify
  - extract
  - summarize
  - propose mapping
        |
        v
post-LLM validation
  - schema check
  - allowlist/range rules
  - confidence threshold
        |
        +---- low confidence ------> human review
        |
        v
destination adapter
  - Airtable
  - Google Sheets
  - CRM/database
        |
        v
notification adapter
  - Slack/email/webhook
        |
        v
run log + idempotency key + retry state
```

## Reliability rules

1. **Idempotency first.** Re-running a job should not create duplicate records.
2. **One bad row should not kill the batch.** Record row-level failures and continue when safe.
3. **Secrets stay out of source files.** API keys belong in environment/secret storage.
4. **Deterministic checks bracket AI calls.** Validate both before and after model output.
5. **Human review is a feature.** Low-confidence cases should be surfaced rather than guessed.
6. **Keep a replayable log.** Record input identifier, transformation status, destination result, and error state.
7. **Measure cost per successful record.** LLM/API spend should be observable.

## What this repository does *not* claim

This public repo does **not** currently prove a production deployment to Airtable, Slack, Make, Zapier, or n8n for an external paying client.

It does prove the underlying patterns: structured ingestion, schema design, validation, local workflow tooling, deterministic calculation, exports, tests, and explicit human-review boundaries.

That distinction matters. A client integration should be scoped and verified against the client's actual systems rather than represented as already complete.

## Fast client proof path

For a prospective automation project, the fastest evidence-based pilot is:

1. obtain a small synthetic or non-sensitive sample;
2. define the target schema and success criteria;
3. build the deterministic parser/validator;
4. add the smallest necessary AI step;
5. produce a dry-run output and exception report;
6. connect one destination;
7. demonstrate safe replay without duplicates;
8. then expand to production volume.

This approach turns a vague "AI automation" project into a sequence of testable deliverables.
