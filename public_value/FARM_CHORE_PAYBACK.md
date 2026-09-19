# Farm Chore Cost & Payback — JavaScript utility

A dependency-free function for turning a repeated farm chore into an annual labor cost and evaluating whether a workflow, equipment, or automation change pays back.

## Browser / ES module example

```js
import { calculateChorePayback } from "https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@main/public_value/farm_chore_payback.js";

const result = calculateChorePayback({
  minutes: 15,
  occurrences: 14,
  workers: 1,
  hourlyCost: 20,
  weeks: 52,
  fixCost: 750,
  reductionPercent: 60
});

console.log(result);
```

Expected fields:

- `annualHours`
- `annualLaborCost`
- `annualSavings`
- `paybackMonths`
- `threeYearNetSavings`

The calculator intentionally does not tell a farmer what to buy. It makes the hidden labor economics visible so the operator can decide.

Use conservative assumptions. This is general decision support, not financial advice.
