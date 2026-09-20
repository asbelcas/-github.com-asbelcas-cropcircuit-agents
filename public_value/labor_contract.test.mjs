import assert from "node:assert/strict";
import {
  workerHours,
  normalizeLaborIdentity,
  normalizeDate,
  normalizeLaborRecord,
  validateLaborRecord,
} from "./labor_contract.js";

assert.equal(workerHours({ minutes: 30, workers: 2 }), 1);
assert.equal(workerHours({ minutes: "15", workers: "1" }), 0.25);
assert.equal(workerHours({ minutes: "bad", workers: 1 }), null);
assert.equal(workerHours({ minutes: "", workers: 1 }), null);
assert.equal(normalizeLaborRecord({ minutes: "", workers: "1" }).minutes, null);

assert.deepEqual(
  normalizeLaborIdentity({
    category: "Fencing",
    task: "Move portable fence",
    chore_code: "fencing.move",
  }),
  {
    key: "code:fencing.move",
    method: "chore_code",
    chore_code: "fencing.move",
  }
);

assert.equal(
  normalizeLaborIdentity({
    category: "Fencing",
    task: "Move portable fence",
  }).key,
  "text:fencing\u0000move portable fence"
);

assert.equal(normalizeDate("2026-09-19"), "2026-09-19");
assert.equal(normalizeDate("not-a-date"), "");

const record = normalizeLaborRecord({
  date: "2026-09-19",
  category: " Livestock ",
  task: " Fill trough ",
  chore_code: "livestock.water",
  minutes: "30",
  workers: "2",
  notes: "  demo  ",
});
assert.equal(record.worker_hours, 1);
assert.equal(record.category, "Livestock");
assert.equal(record.task, "Fill trough");
assert.equal(record.notes, "demo");

assert.deepEqual(
  validateLaborRecord(record, {
    knownChoreCodes: new Set(["livestock.water"]),
  }),
  []
);

assert.ok(
  validateLaborRecord({
    ...record,
    worker_hours: 99,
  }).some(x => x.includes("worker_hours differs"))
);

console.log("PASS: CropCircuit farm labor data contract helpers");
