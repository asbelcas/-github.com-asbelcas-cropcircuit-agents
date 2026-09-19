import assert from "node:assert/strict";
import { aggregate, median, percentile } from "./benchmark_aggregate.mjs";

assert.equal(median([1,2,3]),2);
assert.equal(median([1,2,3,4]),2.5);
assert.equal(percentile([10,20,30,40,50],0.25),20);
assert.equal(percentile([10,20,30,40,50],0.75),40);

const base=(hours,livestock)=>({
  schema_version:"1.0",
  period:"year-round",
  region:"Michigan",
  acreage_band:"5-19.9",
  enterprise_types:["mixed"],
  operator_count_band:"1",
  weekly_worker_hours:hours,
  labor_cost_band:"20-24.99",
  category_share_percent:{
    livestock,field_crop:20,harvest:10,wash_pack:5,market_sales:5,
    maintenance:10,fencing:5,water:5,admin:10,other:30-livestock
  },
  source:"manual"
});

const four=[base(30,10),base(40,20),base(50,30),base(60,40)];
const suppressed=aggregate(four,{groupBy:["region","acreage_band"],k:5});
assert.equal(suppressed.length,1);
assert.equal(suppressed[0].suppressed,true);
assert.equal("weekly_worker_hours" in suppressed[0],false);

const five=[...four,base(70,50)];
const published=aggregate(five,{groupBy:["region","acreage_band"],k:5});
assert.equal(published[0].suppressed,false);
assert.equal(published[0].sample_size,5);
assert.equal(published[0].weekly_worker_hours.median,50);
assert.equal(published[0].weekly_worker_hours.p25,40);
assert.equal(published[0].weekly_worker_hours.p75,60);
assert.equal(published[0].category_share_percent.livestock.median,30);

console.log("PASS: CropCircuit benchmark aggregation privacy tests");
