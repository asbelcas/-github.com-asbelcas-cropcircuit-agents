import assert from "node:assert/strict";
import { buildOperationsSnapshot } from "./ops_snapshot.js";

const workspace={
  labor_entries:[
    {date:"2026-09-01",category:"Harvest",worker_hours:2,notes:"private"},
    {date:"2026-09-02",category:"Harvest",minutes:30,workers:2,notes:"private"},
    {date:"2026-08-01",category:"Admin",worker_hours:5},
  ],
  chore_schedule:[{id:"c1"},{id:"c2"}],
  equipment_maintenance:[
    {interval_hours:100},
    {interval_hours:"",interval_days:""},
  ],
  parts_inventory:[
    {quantity_on_hand:1,reorder_threshold:2},
    {quantity_on_hand:4,reorder_threshold:2},
  ],
  harvest_entries:[
    {date:"2026-09-01",item:"Tomato",quantity:10,unit:"lb"},
    {date:"2026-09-02",item:"Tomato",quantity:5,unit:"lb"},
  ],
  sales_entries:[
    {date:"2026-09-01",channel:"Market",gross_amount:100,payment_fees:3,refunds_discounts:2,direct_costs:25},
    {date:"2026-09-02",channel:"CSA",gross_amount:200,payment_fees:6,refunds_discounts:0,direct_costs:50},
  ],
};

const privateSnapshot=buildOperationsSnapshot(workspace,{
  startDate:"2026-09-01",
  endDate:"2026-09-30",
});
assert.equal(privateSnapshot.labor.entries,2);
assert.equal(privateSnapshot.labor.worker_hours,3);
assert.equal(privateSnapshot.labor.categories[0].category,"Harvest");
assert.equal(privateSnapshot.harvest.totals_by_item_unit[0].quantity,15);
assert.equal(privateSnapshot.sales.channels[0].gross_amount,undefined);
assert.equal(privateSnapshot.equipment.parts_at_or_below_threshold,1);
assert.equal(JSON.stringify(privateSnapshot).includes("private"),false);

const dollarSnapshot=buildOperationsSnapshot(workspace,{
  startDate:"2026-09-01",
  endDate:"2026-09-30",
  includeSalesDollars:true,
});
const market=dollarSnapshot.sales.channels.find(x=>x.channel==="Market");
assert.equal(market.gross_amount,100);
assert.equal(market.net_receipts,95);
assert.equal(dollarSnapshot.privacy.sales_dollars_included,true);

console.log("PASS: CropCircuit operations snapshot");
