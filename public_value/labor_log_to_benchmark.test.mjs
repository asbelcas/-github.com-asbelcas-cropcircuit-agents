import assert from "node:assert/strict";
import { buildBenchmarkFromRows } from "./labor_log_to_benchmark.mjs";

const rows=[
  {category:"Livestock",worker_hours:"10"},
  {category:"Field / Crop",worker_hours:"5"},
  {category:"Harvest",worker_hours:"3"},
  {category:"Wash / Pack",worker_hours:"2"},
];

const record=buildBenchmarkFromRows(rows,{
  days:7,
  period:"summer",
  region:"Michigan",
  acreageBand:"5-19.9",
  enterprises:["vegetables","mixed"],
  operators:"2",
  laborCostBand:"20-24.99"
});

assert.equal(record.weekly_worker_hours,20);
assert.equal(record.category_share_percent.livestock,50);
assert.equal(record.category_share_percent.field_crop,25);
assert.equal(record.category_share_percent.harvest,15);
assert.equal(record.category_share_percent.wash_pack,10);
assert.equal(record.source,"cropcircuit-labor-log");
assert.equal("task" in record,false);
assert.equal("date" in record,false);
assert.equal("notes" in record,false);

const pct=Object.values(record.category_share_percent).reduce((a,b)=>a+b,0);
assert.ok(Math.abs(pct-100)<0.2);

console.log("PASS: CropCircuit labor-log benchmark transform");
