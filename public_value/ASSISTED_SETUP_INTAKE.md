# Assisted Setup Intake Builder

The intake builder creates a **scope brief**, not a farm-data upload.

It is designed for the period before CropCircuit and the operator have agreed that the $149 Assisted Farm Data Setup pilot fits.

## What it captures

- source-file count
- approximate row-count band
- file format
- operational domains present
- column consistency
- whether excluded sensitive data has been removed
- whether sales-dollar totals should appear in the shareable snapshot
- desired turnaround
- one short non-sensitive structure note
- a random request ID

## What it must not contain

Do not enter:

- farm name
- street address
- customer names
- bank or card data
- payroll / HR data
- credentials or passwords
- Social Security numbers
- medical data

## Request ID

The browser creates a random request ID such as:

```text
DS-20260920-A1B2C3D4
```

The ID is useful for tying together:

- the initial scope request;
- a future payment memo/record;
- fulfillment files;
- the operator's local service-order ledger.

It is not authentication and should not be treated as a secret.

## Transfer rule

The generated brief explicitly says that private source files have **not** been attached.

A safe transfer method should be agreed only after scope is confirmed.

## Privacy

This is a standalone browser page.

It performs no upload and has no analytics/network submission logic.

The optional X link simply opens the public `@asbelcas` profile so the user can send the generated text manually.
