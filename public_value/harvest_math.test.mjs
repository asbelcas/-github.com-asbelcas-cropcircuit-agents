import assert from "node:assert/strict";
import { summarizeHarvest, compareHarvest } from "./harvest_math.js";

const rows=[
  {date:"2025-08-01",item:"Tomato",quantity:10,unit:"lb"},
  {date:"2025-08-02",item:"Tomato",quantity:12.5,unit:"lb"},
  {date:"2025-08-02",item:"Cucumber",quantity:8,unit:"count"},
  {date:"2026-08-01",item:"Tomato",quantity:30,unit:"lb"},
  {date:"2026-08-01",item:"Cucumber",quantity:10,unit:"count"},
  {date:"2026-08-02",item:"Tomato",quantity:3,unit:"count"},
];

assert.deepEqual(
  summarizeHarvest(rows,{startDate:"2025-08-01",endDate:"2025-08-31"}),
  [
    {item:"Cucumber",unit:"count",entries:1,quantity:8},
    {item:"Tomato",unit:"lb",entries:2,quantity:22.5},
  ]
);

const compared=compareHarvest(rows,{
  periodA:{startDate:"2025-08-01",endDate:"2025-08-31"},
  periodB:{startDate:"2026-08-01",endDate:"2026-08-31"},
});
const tomatoLb=compared.find(x=>x.item==="Tomato"&&x.unit==="lb");
assert.equal(tomatoLb.quantityA,22.5);
assert.equal(tomatoLb.quantityB,30);
assert.equal(tomatoLb.change,7.5);
assert.equal(tomatoLb.changePercent,33.3);

const tomatoCount=compared.find(x=>x.item==="Tomato"&&x.unit==="count");
assert.equal(tomatoCount.quantityA,0);
assert.equal(tomatoCount.changePercent,null);

console.log("PASS: CropCircuit harvest math");
