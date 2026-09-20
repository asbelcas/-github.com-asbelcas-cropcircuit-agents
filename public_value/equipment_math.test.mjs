import assert from "node:assert/strict";
import {
  hourServiceStatus,
  dateServiceStatus,
  combinedServiceStatus,
} from "./equipment_math.js";

assert.deepEqual(
  hourServiceStatus({
    currentHours: 1425,
    lastServiceHours: 1255,
    intervalHours: 200,
  }),
  {
    configured: true,
    nextDueHours: 1455,
    hoursRemaining: 30,
    status: "not-due",
  }
);

assert.equal(
  hourServiceStatus({
    currentHours: 1500,
    lastServiceHours: 1255,
    intervalHours: 200,
  }).status,
  "overdue"
);

assert.equal(
  hourServiceStatus({
    currentHours: "",
    lastServiceHours: 1255,
    intervalHours: 200,
  }).status,
  "not-configured"
);

assert.equal(
  dateServiceStatus({
    lastServiceDate: "2026-01-01",
    intervalDays: " ",
    asOfDate: "2026-01-31",
  }).status,
  "not-configured"
);

assert.equal(
  hourServiceStatus({
    currentHours: -1,
    lastServiceHours: 0,
    intervalHours: 100,
  }).status,
  "not-configured"
);

assert.deepEqual(
  dateServiceStatus({
    lastServiceDate: "2026-01-01",
    intervalDays: 30,
    asOfDate: "2026-01-31",
  }),
  {
    configured: true,
    nextDueDate: "2026-01-31",
    daysRemaining: 0,
    status: "due",
  }
);

const combined = combinedServiceStatus({
  currentHours: 1300,
  lastServiceHours: 1200,
  intervalHours: 250,
  lastServiceDate: "2026-01-01",
  intervalDays: 30,
  asOfDate: "2026-02-15",
});
assert.equal(combined.overall,"overdue");
assert.equal(combined.hours.status,"not-due");
assert.equal(combined.date.status,"overdue");

console.log("PASS: CropCircuit equipment maintenance math");
