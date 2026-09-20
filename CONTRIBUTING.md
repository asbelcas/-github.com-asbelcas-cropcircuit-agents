# Contributing to CropCircuit Open Farm Utilities

CropCircuit is trying to make small, inspectable farm-management utilities that do useful arithmetic or recordkeeping without demanding a central farm-data account.

Contributions are welcome when they make the tools **simpler, more portable, more truthful, or more interoperable**.

## Before adding a new tool

Ask:

1. Is there a concrete farm workflow/problem?
2. Can an existing tool handle it with a small extension?
3. Are the assumptions visible?
4. Can the useful calculation be separated from opinion or prescription?
5. Can the tool work locally without requiring a new account?
6. Does it preserve existing CSV / Workspace compatibility?
7. Is there a testable reusable core if the tool contains nontrivial math?

Avoid adding a new dashboard merely because another metric can be displayed.

## Good contribution shapes

Examples:

- bug fixes
- accessibility improvements
- clearer error messages
- additional CSV import compatibility
- tests
- data-contract validators
- format converters
- documentation
- translation/localization structure
- portable exports
- privacy-preserving workflow improvements
- farm arithmetic with explicit inputs and no hidden assumptions

## Funding opportunity submissions

Funding records should use a primary source whenever possible: the administering government agency, university, foundation, or program owner.

Include the current status, deadline/timezone where relevant, funding mechanism/amount when stated, intended audience, geographic limits, neutral summary, verification date, and primary-source URL.

Do not use scraped grant-directory summaries as the sole evidence for an opportunity.

Corrections are as valuable as additions: flag expired deadlines, changed amounts, pauses/cancellations, eligibility changes, broken links, or duplicates.

## Data and evidence

Do not add private farm records to the repository.

Synthetic examples should be clearly labeled synthetic.

External factual data should include provenance and verification dates where appropriate.

Community discussions can justify exploring a workflow, but should not be presented as representative market research unless the evidence actually supports that claim.

## Safety-sensitive domains

Do not invent generic safety-critical defaults.

Examples include equipment inspection requirements, maintenance intervals, electrical capacity, structural design, pesticide rates, veterinary treatment, or worker safety procedures.

A tool may record operator/manufacturer-supplied values and perform transparent arithmetic on them.

Documentation should state the boundary.

## JavaScript modules and validation

Public reusable modules are zero-dependency ES modules where practical.

Add or update tests when changing calculations.

Root package validation is:

```bash
npm run test:public
```

GitHub Actions execution is not yet verified for this repository, so local/pass claims should not be inferred solely from the presence of the workflow file.

## Local workspace compatibility

Current Workspace version is 1.2.

Older Workspace 1.0 and 1.1 imports remain supported.

If a new workspace collection is added:

- bump the workspace version;
- preserve old import compatibility where feasible;
- update `workspace.js`;
- update `workspace.schema.json`;
- update TypeScript declarations;
- update backup/restore UI;
- add compatibility tests;
- document exactly what older replace imports preserve.

## Privacy

Raw Workspace backups can contain private farm operational information.

Never paste a real Workspace backup into a public issue.

When reproducing a bug, use the smallest synthetic record that demonstrates it.

## Pull requests

Prefer one coherent change over a large unrelated bundle.

Explain the farm problem, what changed, assumptions, tests performed, compatibility impact, and privacy/safety impact if any.
