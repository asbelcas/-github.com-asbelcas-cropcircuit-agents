import assert from "node:assert/strict";
import { expandScheduleItem, buildDailyLoad } from "./schedule_math.js";

assert.deepEqual(
  expandScheduleItem(
    { first_date:"2026-09-01", frequency:"WEEKLY", interval:1 },
    { startDate:"2026-09-01", endDate:"2026-09-20" }
  ),
  ["2026-09-01","2026-09-08","2026-09-15"]
);

assert.deepEqual(
  expandScheduleItem(
    { first_date:"2026-01-31", frequency:"MONTHLY", interval:1 },
    { startDate:"2026-01-01", endDate:"2026-04-30" }
  ),
  ["2026-01-31","2026-03-31"]
);

assert.deepEqual(
  expandScheduleItem(
    { first_date:"2024-02-29", frequency:"YEARLY", interval:1 },
    { startDate:"2024-01-01", endDate:"2028-12-31" }
  ),
  ["2024-02-29","2028-02-29"]
);

const load = buildDailyLoad([
  { task:"Move fence", chore_code:"fencing.move", first_date:"2026-09-01", frequency:"WEEKLY", interval:1, estimated_minutes:30 },
  { task:"Records", chore_code:"admin.recordkeeping", first_date:"2026-09-08", frequency:"WEEKLY", interval:1, estimated_minutes:15 },
], { startDate:"2026-09-01", endDate:"2026-09-15" });

assert.equal(load.length,3);
assert.equal(load[1].date,"2026-09-08");
assert.equal(load[1].total_estimated_minutes,45);
assert.equal(load[1].tasks.length,2);

console.log("PASS: CropCircuit schedule math");
