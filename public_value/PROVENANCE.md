# Data Provenance and Truthfulness Policy

CropCircuit's public-value repository contains several different kinds of material. They should not be confused.

## 1. Primary-source-linked funding facts

The Michigan Farm Funding Radar summarizes program status from primary or administering sources whenever possible.

Each funding record is intended to include:

- primary-source URL
- verification date
- short verification note
- explicit status such as open, continuous, watch, paused, or closed

A CropCircuit funding record is a navigation and normalization layer, not the authoritative program record.

**Users should verify current details at the linked primary source before applying or making a financial decision.**

## 2. CropCircuit-authored utility code

Calculators, analyzers, validators, schemas, and browser tools are written as general-purpose decision-support infrastructure.

Their formulas are documented and assumptions are intended to remain explicit.

The tools should not be described as externally validated unless external validation actually occurs.

## 3. Synthetic demonstration data

Files under `public_value/examples/` are fabricated demonstration records.

They exist so users can test the toolchain without contributing real farm data.

They must not be represented as:

- observed farm performance
- benchmark evidence
- customer data
- research results

## 4. Benchmark specification versus benchmark data

CropCircuit publishes:

- an anonymous benchmark record schema
- a local benchmark builder
- a privacy transform
- an aggregation tool
- a private comparison explorer

CropCircuit **does not currently publish a populated farm operations benchmark dataset**.

No median, percentile, "typical farm," or peer-performance claim should be inferred from the existence of the benchmark tooling.

## 5. Derived calculations

Outputs such as annualized labor cost, hypothetical savings, equipment thresholds, and before/after labor value are derived from user-supplied assumptions or observations.

They are model outputs, not guaranteed outcomes.

## 6. Corrections

When a factual funding record is found to be stale or wrong:

1. correct the public data;
2. update verification metadata;
3. preserve a truthful changelog entry when the correction is material;
4. do not silently preserve an "open" label after a known deadline has passed.

The repository favors being visibly incomplete over appearing complete through invented data.
