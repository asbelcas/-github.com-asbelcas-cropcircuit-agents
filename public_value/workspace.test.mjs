import assert from "node:assert/strict";
import {
  WORKSPACE_VERSION,
  SUPPORTED_WORKSPACE_VERSIONS,
  WORKSPACE_KEYS,
  readWorkspace,
  validateWorkspace,
  writeWorkspace,
} from "./workspace.js";

class MemoryStorage {
  constructor() { this.map = new Map(); }
  getItem(k) { return this.map.has(k) ? this.map.get(k) : null; }
  setItem(k,v) { this.map.set(k,String(v)); }
}

const storage = new MemoryStorage();
storage.setItem(WORKSPACE_KEYS.laborEntries, JSON.stringify([{id:"a",task:"Feed"}]));
storage.setItem(WORKSPACE_KEYS.laborSettings, JSON.stringify({hourly:20}));
storage.setItem(WORKSPACE_KEYS.choreSchedule, JSON.stringify([{id:"s1",task:"Feed"}]));
storage.setItem(WORKSPACE_KEYS.equipmentMaintenance, JSON.stringify([{id:"e1",equipment:"Tractor"}]));
storage.setItem(WORKSPACE_KEYS.harvestEntries, JSON.stringify([{id:"h1",item:"Tomato"}]));
storage.setItem(WORKSPACE_KEYS.salesEntries, JSON.stringify([{id:"x1",channel:"Farmers Market"}]));

assert.equal(WORKSPACE_VERSION,"1.1");
assert.deepEqual([...SUPPORTED_WORKSPACE_VERSIONS],["1.0","1.1"]);

const exported = readWorkspace(storage);
assert.equal(exported.schema_version,"1.1");
assert.equal(exported.labor_entries.length,1);
assert.equal(exported.chore_schedule.length,1);
assert.equal(exported.equipment_maintenance.length,1);
assert.equal(exported.harvest_entries.length,1);
assert.equal(exported.sales_entries.length,1);
assert.deepEqual(validateWorkspace(exported),[]);

// A v1.0 backup remains valid and must not erase datasets added in v1.1.
const legacyReplacement = {
  schema_version:"1.0",
  labor_entries:[{id:"b",task:"Water"}],
  labor_settings:{hourly:25},
  chore_schedule:[{id:"s2",task:"Water"}],
};
const legacyResult = writeWorkspace(storage,legacyReplacement);
assert.equal(legacyResult.ok,true);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.laborEntries)).map(x=>x.id),["b"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.equipmentMaintenance)).map(x=>x.id),["e1"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.harvestEntries)).map(x=>x.id),["h1"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.salesEntries)).map(x=>x.id),["x1"]);

// A v1.1 replacement updates the full workspace.
const replacement = {
  schema_version:"1.1",
  labor_entries:[{id:"c",task:"Fence"}],
  labor_settings:{hourly:30},
  chore_schedule:[{id:"s3",task:"Fence"}],
  equipment_maintenance:[{id:"e2",equipment:"Mower"}],
  harvest_entries:[{id:"h2",item:"Cucumber"}],
  sales_entries:[{id:"x2",channel:"CSA"}],
};
const replaceResult=writeWorkspace(storage,replacement);
assert.equal(replaceResult.ok,true);
assert.equal(replaceResult.equipment_maintenance,1);
assert.equal(replaceResult.harvest_entries,1);
assert.equal(replaceResult.sales_entries,1);

// Merge mode deduplicates matching non-empty IDs across every record collection.
const merge = {
  schema_version:"1.1",
  labor_entries:[{id:"c",task:"Duplicate"},{id:"d",task:"Harvest"}],
  labor_settings:{hourly:35},
  chore_schedule:[{id:"s3",task:"Duplicate"},{id:"s4",task:"Harvest"}],
  equipment_maintenance:[{id:"e2",equipment:"Duplicate"},{id:"e3",equipment:"Seeder"}],
  harvest_entries:[{id:"h2",item:"Duplicate"},{id:"h3",item:"Pepper"}],
  sales_entries:[{id:"x2",channel:"Duplicate"},{id:"x3",channel:"Farm Stand"}],
};
const merged = writeWorkspace(storage,merge,{mode:"merge"});
assert.equal(merged.ok,true);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.laborEntries)).map(x=>x.id),["c","d"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.choreSchedule)).map(x=>x.id),["s3","s4"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.equipmentMaintenance)).map(x=>x.id),["e2","e3"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.harvestEntries)).map(x=>x.id),["h2","h3"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.salesEntries)).map(x=>x.id),["x2","x3"]);
assert.equal(JSON.parse(storage.getItem(WORKSPACE_KEYS.laborSettings)).hourly,35);

// v1.1 workspaces require the three v1.1 record collections.
assert.ok(validateWorkspace({
  schema_version:"1.1",
  labor_entries:[],
  labor_settings:{},
  chore_schedule:[],
}).some(x=>x.includes("equipment_maintenance")));

console.log("PASS: CropCircuit local workspace helpers v1.1 + v1.0 compatibility");
