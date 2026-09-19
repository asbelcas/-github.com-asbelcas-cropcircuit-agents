# CropCircuit Farm Math

Small, dependency-free calculations for farm operations and farm-business decisions.

The design rule is simple: **the code exposes arithmetic, not prescriptions**. Biological rates, costs, reserve margins, and other assumptions stay explicit and user-supplied.

## Import from a browser or ES module

```js
import {
  annualTaskCost,
  simplePayback,
  fenceEstimate,
  waterStorage,
  breakEvenTransactions,
  rectangleAcres
} from "https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@main/public_value/farm_math.js";
```

## Examples

### Annual labor cost

```js
annualTaskCost({
  minutes: 15,
  occurrencesPerWeek: 14,
  workers: 1,
  hourlyCost: 20,
  weeksPerYear: 52
})
```

Returns annual hours and annual labor cost.

### Fence estimate

```js
fenceEstimate({
  acres: 10,
  installedCostPerFoot: 4.25,
  shapeFactor: 1.15,
  internalFenceFeet: 1200,
  gateCost: 800
})
```

The acreage calculation starts with the perimeter of a square parcel. `shapeFactor` deliberately makes geometry visible instead of pretending every parcel has the same perimeter.

### Water storage

```js
waterStorage({
  animals: 20,
  gallonsPerAnimalPerDay: 5,
  autonomyDays: 2,
  reservePercent: 25
})
```

No animal-species defaults are embedded. Use a consumption value appropriate to the species, weather, production stage, water source, and local guidance.

### Break-even transactions

```js
breakEvenTransactions({
  fixedCosts: 600,
  averageSale: 35,
  variableCostPerTransaction: 12
})
```

Useful for farm stands, events, CSA add-ons, pop-ups, or other selling channels.

## Tests

With a recent Node.js installation:

```bash
node public_value/farm_math.test.mjs
```

These are general planning calculations, not financial, engineering, veterinary, or agronomic advice.
