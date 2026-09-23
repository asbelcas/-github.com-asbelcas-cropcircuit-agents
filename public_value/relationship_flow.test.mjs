import assert from "node:assert/strict";
import {
  summarizeRelationshipMap,
  traceRelationships,
  validateRelationshipMap,
} from "./relationship_flow.js";

const map = {
  schema_version: "0.1",
  map_id: "synthetic-farm-map",
  updated_at: "2026-09-23T22:00:00Z",
  nodes: [
    {
      id: "flock",
      label: "Sheep flock",
      kind: "animals",
      state: "watch",
      evidence_refs: ["synthetic:obs-flock"],
      unknowns: [],
    },
    {
      id: "paddock-4",
      label: "Paddock 4",
      kind: "pasture",
      state: "unknown",
      evidence_refs: [],
      unknowns: ["Cause of avoidance is unresolved."],
    },
    {
      id: "water-line",
      label: "North water line",
      kind: "water",
      state: "healthy",
      evidence_refs: ["synthetic:water-check"],
      unknowns: [],
    },
    {
      id: "labor-window",
      label: "Morning labor window",
      kind: "labor",
      state: "healthy",
      evidence_refs: ["synthetic:labor-log"],
      unknowns: [],
    },
    {
      id: "unused-node",
      label: "Synthetic isolated node",
      kind: "other",
      state: "unknown",
      evidence_refs: [],
      unknowns: [],
    },
  ],
  edges: [
    {
      id: "flock-paddock",
      from: "flock",
      to: "paddock-4",
      relationship: "grazes",
      flow_kind: "animals",
      state: "stressed",
      evidence_refs: ["synthetic:avoidance"],
      unknowns: ["Why use of the corner declined."],
      note: "",
    },
    {
      id: "water-paddock",
      from: "water-line",
      to: "paddock-4",
      relationship: "supplies water",
      flow_kind: "water",
      state: "watch",
      evidence_refs: ["synthetic:water-check"],
      unknowns: [],
      note: "",
    },
    {
      id: "labor-flock",
      from: "labor-window",
      to: "flock",
      relationship: "supports move",
      flow_kind: "labor",
      state: "healthy",
      evidence_refs: ["synthetic:labor-log"],
      unknowns: [],
      note: "",
    },
  ],
};

assert.equal(validateRelationshipMap(map).valid, true);

const summary = summarizeRelationshipMap(map);
assert.equal(summary.valid, true);
assert.equal(summary.counts.nodes, 5);
assert.equal(summary.counts.edges, 3);
assert.equal(summary.counts.stressed_edges, 1);
assert.equal(summary.counts.unknown_nodes, 2);
assert.ok(summary.focus.some(x => x.id === "flock-paddock"));
assert.deepEqual(summary.isolated_nodes, ["unused-node"]);

const trace = traceRelationships(map, "paddock-4", 1);
assert.deepEqual(
  trace.nodes.map(x => x.id).sort(),
  ["flock", "paddock-4", "water-line"]
);
assert.deepEqual(
  trace.edges.map(x => x.id).sort(),
  ["flock-paddock", "water-paddock"]
);
assert.match(trace.note, /not proven causal effects/);

const invalid = structuredClone(map);
invalid.edges[0].to = "missing-node";
assert.equal(validateRelationshipMap(invalid).valid, false);

console.log("PASS: CropCircuit relationship flow v0.1");
