import assert from "node:assert/strict";
import { salesRecordEconomics, summarizeSales } from "./sales_math.js";

assert.deepEqual(
  salesRecordEconomics({
    gross_amount:100,
    payment_fees:3,
    refunds_discounts:5,
    direct_costs:40,
  }),
  {
    grossAmount:100,
    paymentFees:3,
    refundsDiscounts:5,
    directCosts:40,
    netReceipts:92,
    contributionAfterDirectCosts:52,
  }
);

const rows=[
  {date:"2026-09-01",channel:"Farmers Market",gross_amount:300,payment_fees:9,refunds_discounts:0,direct_costs:100},
  {date:"2026-09-08",channel:"Farmers Market",gross_amount:400,payment_fees:12,refunds_discounts:10,direct_costs:120},
  {date:"2026-09-02",channel:"CSA",gross_amount:600,payment_fees:18,refunds_discounts:0,direct_costs:180},
];

const summary=summarizeSales(rows,{startDate:"2026-09-01",endDate:"2026-09-30"});
const market=summary.find(x=>x.group==="Farmers Market");
assert.equal(market.transactions,2);
assert.equal(market.grossAmount,700);
assert.equal(market.netReceipts,669);
assert.equal(market.contributionAfterDirectCosts,449);

console.log("PASS: CropCircuit sales summary math");
