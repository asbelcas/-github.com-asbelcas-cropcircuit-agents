import assert from "node:assert/strict";
import { evaluateRightRelationship } from "./right_relationship.js";

assert.equal(evaluateRightRelationship({
  hard_constraints:[
    {id:"animal_welfare",status:"pass"},
    {id:"water",status:"pass"}
  ]
}).gate,"pass");

const rejected=evaluateRightRelationship({
  hard_constraints:[
    {id:"profit",status:"pass"},
    {id:"water",status:"fail"}
  ]
});
assert.equal(rejected.gate,"reject");
assert.deepEqual(rejected.failed_hard_constraints,["water"]);

assert.equal(evaluateRightRelationship({
  hard_constraints:[{id:"soil",status:"unknown"}]
}).gate,"hold");

assert.equal(evaluateRightRelationship({
  hard_constraints:[{id:"soil",status:"pass"}],
  unknowns:["pollinator effect"]
}).gate,"hold");

console.log("PASS: CropCircuit right relationship gate");
