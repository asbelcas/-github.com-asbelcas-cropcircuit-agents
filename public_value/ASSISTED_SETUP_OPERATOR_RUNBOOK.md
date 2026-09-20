# Assisted Farm Data Setup — Operator Runbook

This runbook keeps the $149 pilot bounded, repeatable, and honest.

It is an internal fulfillment standard published openly so the customer can see what "setup" means.

## Service boundary

A pilot job is:

- one farm operation;
- up to 3 source CSV/XLSX exports;
- up to 1,500 total rows;
- supported operational data only;
- one correction round.

If the work clearly exceeds this scope, stop and rescope before accepting payment.

## 0. Before payment

Confirm:

- source-file count;
- approximate total rows;
- which contracts are likely involved;
- whether the files contain customer PII, credentials, banking data, payroll/HR data, medical data, or payment-card data.

If sensitive excluded data is present, ask the client to remove it before transfer.

Do not ask for passwords or account credentials.

## 1. Create a working copy

Never transform the only copy of a client's file.

Use a working copy and keep original filenames recorded in the delivery note.

## 2. Inventory the source package

For each source file record:

- original filename;
- row count;
- tabs/sheets if applicable;
- likely target contract;
- obvious ambiguities;
- excluded columns.

## 3. Map only supported facts

Supported target contracts:

- labor
- recurring chores
- equipment maintenance
- parts inventory
- harvest
- direct-market sales

Use the published data-contract registry.

Do not invent values to satisfy a schema.

If a required field is missing or ambiguous, put the record in the unresolved note rather than guessing.

## 4. Normalize conservatively

Allowed mechanical cleanup includes:

- column-name normalization;
- whitespace cleanup;
- date-format normalization when the source date is unambiguous;
- supported recurrence normalization such as `weekly` → `WEEKLY`;
- worker-hours derived from supplied minutes × workers;
- optional zero defaults where the contract explicitly defines them.

Do not infer accounting categories, service intervals, part compatibility, harvest conversion factors, or missing farm measurements.

## 5. Build canonical outputs

Create relevant files such as:

```text
labor.csv
chore_schedule.csv
equipment_maintenance.csv
parts_inventory.csv
harvest.csv
sales.csv
workspace.json
delivery_note.md
operations_snapshot.json   # when applicable
```

The final Workspace filename for validation is `workspace.json`.

## 6. Write the delivery note

The note should contain:

- source inventory;
- mapping table;
- transformations performed;
- excluded columns;
- unresolved items;
- records omitted and why;
- outputs produced;
- any customer decisions needed;
- statement that domain assumptions were not silently added.

Do not copy unnecessary private source rows into the note.

## 7. Run validation

Run:

```bash
node public_value/validate_setup_delivery.mjs /path/to/delivery-folder
```

A paid delivery must not ship with:

- Workspace schema errors;
- `demo-` IDs;
- sensitive-looking keys such as passwords, SSNs, card numbers, CVV/CVC, bank-account or routing-number fields;
- missing `workspace.json`;
- missing `delivery_note.md`.

The validator also emits SHA-256 checksums for the delivery files.

## 8. Human QA

Open the Workspace in a browser and inspect:

- record counts;
- dates;
- units;
- categories;
- sales fields;
- maintenance intervals;
- parts thresholds.

Spot-check at least 5 transformed records against the source when the job has 5 or more rows.

For smaller jobs, spot-check every record.

## 9. Build the coarse snapshot

If the source supports it, generate the Shareable Farm Operations Snapshot.

Default:

- no raw rows;
- no free-text notes;
- no exact transaction dates;
- no sales-dollar summary unless the client requested it.

## 10. Delivery

Deliver:

- canonical files;
- Workspace;
- delivery note;
- snapshot if applicable;
- a short explanation of how to restore/open the Workspace.

Remind the customer to keep their original source files.

## 11. Correction round

One correction round covers:

- a mapping mistake;
- a misunderstood source convention;
- an omitted supported file/field that was already inside agreed scope.

New source systems, materially larger row counts, custom software, bookkeeping, or consulting are new scope.

## 12. Revenue ledger

Count revenue only when an external customer payment tied to the job is confirmed.

Do not count:

- inquiries;
- DMs;
- scope confirmations;
- payment links sent;
- transfers between Casey's own accounts;
- synthetic/demo jobs.

## Quality rule

**A smaller delivery with explicit unresolved fields is better than a polished package containing invented facts.**
