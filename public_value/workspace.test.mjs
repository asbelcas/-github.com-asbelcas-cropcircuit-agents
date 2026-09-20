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
storage.setItem(WORKSPACE_KEYS.partsInventory, JSON.stringify([{id:"p1",part_name:"Oil filter"}]));

assert.equal(WORKSPACE_VERSION,"1.2");
assert.deepEqual([...SUPPORTED_WORKSPACE_VERSIONS],["1.0","1.1","1.2"]);

const exported=readWorkspace(storage);
assert.equal(exported.schema_version,"1.2");
assert.equal(exported.parts_inventory.length,1);
assert.deepEqual(validateWorkspace(exported),[]);

// Workspace 1.0 preserves all newer collections on replace.
const legacy10={
  schema_version:"1.0",
  labor_entries:[{id:"b",task:"Water"}],
  labor_settings:{hourly:25},
  chore_schedule:[{id:"s2",task:"Water"}],
};
assert.equal(writeWorkspace(storage,legacy10).ok,true);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.partsInventory)).map(x=>x.id),["p1"]);

// Workspace 1.1 may replace equipment/harvest/sales, but preserves parts added in 1.2.
const legacy11={
  schema_version:"1.1",
  labor_entries:[{id:"c",task:"Fence"}],
  labor_settings:{hourly:30},
  chore_schedule:[{id:"s3",task:"Fence"}],
  equipment_maintenance:[{id:"e2",equipment:"Mower"}],
  harvest_entries:[{id:"h2",item:"Cucumber"}],
  sales_entries:[{id:"x2",channel:"CSA"}],
};
const legacy11Result=writeWorkspace(storage,legacy11);
assert.equal(legacy11Result.ok,true);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.partsInventory)).map(x=>x.id),["p1"]);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.equipmentMaintenance)).map(x=>x.id),["e2"]);

// Workspace 1.2 updates the full workspace.
const replacement={
  schema_version:"1.2",
  labor_entries:[{id:"d",task:"Harvest"}],
  labor_settings:{hourly:35},
  chore_schedule:[{id:"s4",task:"Harvest"}],
  equipment_maintenance:[{id:"e3",equipment:"Seeder"}],
  harvest_entries:[{id:"h3",item:"Pepper"}],
  sales_entries:[{id:"x3",channel:"Farm Stand"}],
  parts_inventory:[{id:"p2",part_name:"Belt"}],
};
const replaceResult=writeWorkspace(storage,replacement);
assert.equal(replaceResult.ok,true);
assert.equal(replaceResult.parts_inventory,1);

// Merge mode deduplicates IDs across every collection.
const merge={
  schema_version:"1.2",
  labor_entries:[{id:"d",task:"Duplicate"},{id:"e",task:"Pack"}],
  labor_settings:{hourly:40},
  chore_schedule:[{id:"s4",task:"Duplicate"},{id:"s5",task:"Pack"}],
  equipment_maintenance:[{id:"e3",equipment:"Duplicate"},{id:"e4",equipment:"Truck"}],
  harvest_entries:[{id:"h3",item:"Duplicate"},{id:"h4",item:"Squash"}],
  sales_entries:[{id:"x3",channel:"Duplicate"},{id:"x4",channel:"Wholesale"}],
  parts_inventory:[{id:"p2",part_name:"Duplicate"},{id:"p3",part_name:"Bearing"}],
};
const merged=writeWorkspace(storage,merge,{mode:"merge"});
assert.equal(merged.ok,true);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.partsInventory)).map(x=>x.id),["p2","p3"]);
assert.equal(JSON.parse(storage.getItem(WORKSPACE_KEYS.laborSettings)).hourly,40);

// v1.2 requires parts inventory; v1.1 does not.
assert.ok(validateWorkspace({
  schema_version:"1.2",
  labor_entries:[],
  labor_settings:{},
  chore_schedule:[],
  equipment_maintenance:[],
  harvest_entries:[],
  sales_entries:[],
}).some(x=>x.includes("parts_inventory")));

assert.deepEqual(validateWorkspace({
  schema_version:"1.1",
  labor_entries:[],
  labor_settings:{},
  chore_schedule:[],
  equipment_maintenance:[],
  harvest_entries:[],
  sales_entries:[],
}),[]);

console.log("PASS: CropCircuit local workspace helpers v1.2 + v1.0/v1.1 compatibility");
