import assert from "node:assert/strict";
import { validateDecisionRecord } from "./validate_decision_record.mjs";

const base={
  schema_version:"1.0",
  decision_id:"synthetic-1",
  created_at:"2026-09-20T13:20:00Z",
  decision:"Synthetic automation decision",
  purpose:"Reduce repetitive labor without crossing declared boundaries.",
  hard_constraints:[
    {id:"safety",required:true,status:"pass",evidence:"synthetic evidence"}
  ],
  viability:{financial:"synthetic",operational:"synthetic",legal:"synthetic",technical:"synthetic",biological_ecological:"synthetic"},
  reciprocity:"Returns time to operator.",
  enoughness:"Twenty percent labor reduction is sufficient for this synthetic case.",
  wider_system_effects:"No material synthetic effect identified.",
  unknowns:[],
  reversibility:{level:"high",note:"Synthetic pilot can be removed."},
  gate:"pass_to_review",
  decision_outcome:"experiment",
  review_trigger:"Review after synthetic pilot."
};
assert.deepEqual(validateDecisionRecord(base),[]);

const fail={...base,hard_constraints:[{id:"water",required:true,status:"fail",evidence:"synthetic"}],gate:"pass_to_review",decision_outcome:"proceed"};
assert.ok(validateDecisionRecord(fail).some(x=>x.includes("gate must be reject")));

const hold={...base,hard_constraints:[{id:"water",required:true,status:"unknown",evidence:""}],gate:"pass_to_review"};
assert.ok(validateDecisionRecord(hold).some(x=>x.includes("gate must be hold")));

const hold2={...base,unknowns:["pollinator effect"],gate:"hold",decision_outcome:"experiment"};
assert.deepEqual(validateDecisionRecord(hold2),[]);

console.log("PASS: CropCircuit high-impact decision record validation");
