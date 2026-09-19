# JavaScript / npm-style package usage

CropCircuit's reusable JavaScript utilities now have a root `package.json` and module exports.

The repository is **not being claimed as published to the npm registry**. The package metadata exists so developers can:

- install directly from the GitHub repository
- import stable modules through package exports
- run the public validation suite with one command
- prepare for registry publication later if real demand appears

## TypeScript

The package now includes `public_value/index.d.ts`, and root `package.json` exposes it through the `types` field.

No TypeScript runtime dependency is required.

## Exports

```js
import {
  annualTaskCost,
  simplePayback,
  fenceEstimate,
  waterStorage,
  breakEvenTransactions,
  rectangleAcres,
  compareSamples,
  annualizeObservedChange
} from "cropcircuit-open-farm-utils";
```

Direct export paths:

```js
import { annualTaskCost } from "cropcircuit-open-farm-utils/farm-math";
import { compareSamples } from "cropcircuit-open-farm-utils/workflow-experiment";
```

## Repository install

Because the current GitHub repository slug is awkward, this is mostly a developer convenience until repository identity cleanup is complete.

A consumer can install directly from GitHub using the normal npm GitHub dependency syntax and pin a stable release branch or commit.

## CLI

The package metadata exposes:

```text
cropcircuit-funding
```

which maps to `public_value/funding_query.mjs`.

## Validation

From a repository checkout:

```bash
npm test
```

runs the zero-dependency public-value validators and tests.

## Farm sales economics exports

```js
import {
  marketDayEconomics,
  csaEconomics
} from "cropcircuit-open-farm-utils";
```

Direct export paths are also available:

```js
import { marketDayEconomics } from "cropcircuit-open-farm-utils/market-math";
import { csaEconomics } from "cropcircuit-open-farm-utils/csa-math";
```

## Equipment maintenance math

```js
import {
  hourServiceStatus,
  dateServiceStatus,
  combinedServiceStatus
} from "cropcircuit-open-farm-utils/equipment-math";
```

No maintenance interval is embedded in the library; the caller supplies all hour/day intervals.

## Harvest summary math

```js
import {
  summarizeHarvest,
  compareHarvest
} from "cropcircuit-open-farm-utils/harvest-math";
```

CropCircuit does not automatically convert unlike harvest units or infer sales revenue from harvest quantity.

## Sales summary math

```js
import {
  salesRecordEconomics,
  summarizeSales
} from "cropcircuit-open-farm-utils/sales-math";
```

These helpers describe entered sales records; they do not determine accounting or tax treatment.

## Registry status

No npm registry publication is claimed.

Publishing should happen only after:

1. repository identity is cleaned up;
2. package behavior is verified in a clean install;
3. there is evidence someone wants the package form.
