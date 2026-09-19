import assert from "node:assert/strict";
import {
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

const exported = readWorkspace(storage);
assert.equal(exported.schema_version,"1.0");
assert.equal(exported.labor_entries.length,1);
assert.equal(exported.chore_schedule.length,1);
assert.deepEqual(validateWorkspace(exported),[]);

const replacement = {
  schema_version:"1.0",
  labor_entries:[{id:"b",task:"Water"}],
  labor_settings:{hourly:25},
  chore_schedule:[{id:"s2",task:"Water"}],
};
assert.equal(writeWorkspace(storage,replacement).ok,true);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.laborEntries)).map(x=>x.id),["b"]);

const merge = {
  schema_version:"1.0",
  labor_entries:[{id:"b",task:"Duplicate"},{id:"c",task:"Fence"}],
  labor_settings:{hourly:30},
  chore_schedule:[{id:"s2",task:"Duplicate"},{id:"s3",task:"Fence"}],
};
const merged = writeWorkspace(storage,merge,{mode:"merge"});
assert.equal(merged.ok,true);
assert.deepEqual(JSON.parse(storage.getItem(WORKSPACE_KEYS.laborEntries)).map(x=>x.id),["b","c"]);
assert.equal(JSON.parse(storage.getItem(WORKSPACE_KEYS.laborSettings)).hourly,30);

console.log("PASS: CropCircuit local workspace helpers");
