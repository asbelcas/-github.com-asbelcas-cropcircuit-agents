# Assisted Farm Data Setup — Pilot Service

**Pilot price:** $149 fixed  
**Pilot capacity:** 3 setups  
**Target delivery:** within 3 business days after scope confirmation, payment, and receipt of usable source files

## Job to be done

A farm already has useful operational records, but they are trapped in spreadsheets or exports with inconsistent columns.

CropCircuit converts those existing files into a clean, portable operating package instead of asking the operator to re-enter everything.

## Included scope

Per pilot setup:

- one farm operation
- up to 3 source CSV/XLSX exports
- up to 1,500 total data rows
- mapping into supported CropCircuit operational contracts where the data actually supports it
- canonical cleaned CSV outputs
- Workspace 1.2 JSON
- mapping / data-quality note
- shareable Operations Snapshot when enough data exists
- one reasonable correction round for mapping mistakes or clarified source conventions

## Supported operational contracts

- labor
- recurring chores
- equipment maintenance
- equipment parts
- harvest
- direct-market sales

## No guessing rule

Ambiguous source fields are flagged.

CropCircuit does not silently invent:

- dates
- quantities
- labor values
- accounting categories
- service intervals
- part compatibility
- units
- missing sales values

## Excluded

This is not:

- bookkeeping
- tax preparation
- accounting cleanup
- payroll processing
- HR data processing
- banking/credit-card analysis
- customer-PII processing
- custom application development
- ongoing cloud database hosting

Do not send credentials, Social Security numbers, payment-card details, medical data, or customer personal information.

## Free alternative

The [Universal Farm CSV Mapper](universal_csv_mapper.html) remains available for anyone who wants to perform the mapping themselves.

The paid service exists for people who want the cleanup/mapping work done for them.

## Pilot request channel

DM **@asbelcas** on X with:

```text
DATA SETUP
```

Do not send private files in the first message.

Scope and transfer method should be confirmed before operational files are shared.

## Deliverable standard

A completed setup should contain:

1. source-file inventory;
2. field mapping table;
3. transformation/cleanup notes;
4. unresolved/ambiguous-field list;
5. canonical output CSVs;
6. Workspace 1.2 backup;
7. Operations Snapshot when applicable;
8. short "what to do next" note;
9. confirmation that synthetic/example data is not mixed into client files.

See [Synthetic Data Setup Deliverable](SYNTHETIC_DATA_SETUP_DELIVERABLE.md) for the format.


## Operator fulfillment controls

The pilot has a published fulfillment standard:

- [Assisted Setup Operator Runbook](ASSISTED_SETUP_OPERATOR_RUNBOOK.md)
- [Delivery validator](validate_setup_delivery.mjs)
- [Delivery validator tests](validate_setup_delivery.test.mjs)

The validator checks the final Workspace for schema errors, `demo-` IDs, sensitive-looking field names, required delivery files, canonical CSV presence, and emits SHA-256 checksums.


## Intake builder

Before sending any private source files, use the [Assisted Setup Intake Builder](assisted_setup_intake.html).

It creates a short scope request with a random request ID and explicitly excludes farm/customer identifying information.

- [Intake builder](assisted_setup_intake.html)
- [Intake documentation](ASSISTED_SETUP_INTAKE.md)

## Before → after case study

A complete synthetic case study is available at:

- [Synthetic assisted setup case](examples/assisted_setup_case/README.md)

It contains intentionally messy input CSVs plus canonical outputs, Workspace 1.2, a coarse operations snapshot, and a delivery note.

The delivery validator deliberately rejects the case-study identifiers if someone tries to treat that synthetic package as a paid client delivery.
