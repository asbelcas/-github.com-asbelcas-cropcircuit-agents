import assert from "node:assert/strict";
import { partStockStatus, summarizePartInventory } from "./inventory_math.js";

assert.deepEqual(
  partStockStatus({
    quantityOnHand: 2,
    reorderThreshold: 3,
    preferredOrderQuantity: 6,
  }),
  {
    configured: true,
    status: "reorder",
    quantityOnHand: 2,
    reorderThreshold: 3,
    suggestedOrderQuantity: 6,
  }
);

assert.equal(
  partStockStatus({
    quantityOnHand: 10,
    reorderThreshold: 3,
  }).status,
  "ok"
);

assert.equal(
  partStockStatus({
    quantityOnHand: "",
    reorderThreshold: 3,
  }).status,
  "not-configured"
);

assert.equal(
  partStockStatus({
    quantityOnHand: 3,
    reorderThreshold: "   ",
  }).status,
  "not-configured"
);

assert.equal(
  partStockStatus({
    quantityOnHand: -1,
    reorderThreshold: 2,
  }).status,
  "not-configured"
);

assert.deepEqual(
  summarizePartInventory([
    {quantity_on_hand:1,reorder_threshold:2},
    {quantity_on_hand:5,reorder_threshold:2},
    {quantity_on_hand:"",reorder_threshold:""},
  ]),
  {
    totalParts:3,
    configuredParts:2,
    reorderParts:1,
    okParts:1,
  }
);

console.log("PASS: CropCircuit equipment-parts inventory math");
