import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { validateSetupDelivery } from "./validate_setup_delivery.mjs";

function makeDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(),"cropcircuit-setup-"));
}

const validDir=makeDir();
fs.writeFileSync(path.join(validDir,"workspace.json"),JSON.stringify({
  schema_version:"1.2",
  labor_entries:[{id:"real-1",date:"2026-09-01",category:"Harvest",task:"Pick",minutes:60,workers:1}],
  labor_settings:{},
  chore_schedule:[],
  equipment_maintenance:[],
  harvest_entries:[],
  sales_entries:[],
  parts_inventory:[]
}));
fs.writeFileSync(path.join(validDir,"delivery_note.md"),"# Delivery note\n");
fs.writeFileSync(path.join(validDir,"labor.csv"),"date,category,task,minutes,workers\n2026-09-01,Harvest,Pick,60,1\n");

const valid=validateSetupDelivery(validDir);
assert.equal(valid.ok,true);
assert.equal(valid.canonical_csv_files.length,1);
assert.equal(valid.workspace_counts.labor_entries,1);
assert.ok(valid.checksums["workspace.json"]);

const demoDir=makeDir();
fs.writeFileSync(path.join(demoDir,"workspace.json"),JSON.stringify({
  schema_version:"1.2",
  labor_entries:[{id:"demo-1"}],
  labor_settings:{},
  chore_schedule:[],
  equipment_maintenance:[],
  harvest_entries:[],
  sales_entries:[],
  parts_inventory:[]
}));
fs.writeFileSync(path.join(demoDir,"delivery_note.md"),"# Delivery note\n");
assert.equal(validateSetupDelivery(demoDir).ok,false);
assert.ok(validateSetupDelivery(demoDir).errors.some(x=>x.includes("demo")));

const caseDir=makeDir();
fs.writeFileSync(path.join(caseDir,"workspace.json"),JSON.stringify({
  schema_version:"1.2",
  labor_entries:[{id:"case-1"}],
  labor_settings:{},
  chore_schedule:[],
  equipment_maintenance:[],
  harvest_entries:[],
  sales_entries:[],
  parts_inventory:[]
}));
fs.writeFileSync(path.join(caseDir,"delivery_note.md"),"# Delivery note\n");
assert.equal(validateSetupDelivery(caseDir).ok,false);
assert.ok(validateSetupDelivery(caseDir).errors.some(x=>x.includes("synthetic/example")));

const sensitiveDir=makeDir();
fs.writeFileSync(path.join(sensitiveDir,"workspace.json"),JSON.stringify({
  schema_version:"1.2",
  labor_entries:[],
  labor_settings:{password:"should-not-be-here"},
  chore_schedule:[],
  equipment_maintenance:[],
  harvest_entries:[],
  sales_entries:[],
  parts_inventory:[]
}));
fs.writeFileSync(path.join(sensitiveDir,"delivery_note.md"),"# Delivery note\n");
assert.equal(validateSetupDelivery(sensitiveDir).ok,false);
assert.ok(validateSetupDelivery(sensitiveDir).errors.some(x=>x.includes("sensitive-looking")));

console.log("PASS: CropCircuit assisted-setup delivery validator");
