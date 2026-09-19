import assert from "node:assert/strict";
import {
  countyMatches,
  filterFunding,
  parseArgs,
  renderMarkdown,
} from "./funding_query.mjs";

const radar = {
  name: "Test Radar",
  verified_at: "2026-09-19",
  opportunities: [
    {
      id: "statewide",
      title: "Statewide",
      status: "open",
      deadline: "2026-09-28T17:00:00-04:00",
      deadline_label: "Sep 28",
      funding: "$1",
      provider: "A",
      tags: ["soil health"],
      county_scope: [],
      source_url: "https://example.com/a",
    },
    {
      id: "kalamazoo",
      title: "Kalamazoo only",
      status: "open",
      deadline: "2026-10-13T23:59:59-04:00",
      deadline_label: "Oct 13",
      funding: "$2",
      provider: "B",
      tags: ["disaster"],
      county_scope: ["Kalamazoo"],
      source_url: "https://example.com/b",
    },
    {
      id: "kent",
      title: "Kent only",
      status: "continuous",
      deadline: null,
      deadline_label: "Continuous",
      funding: "$3",
      provider: "C",
      tags: ["soil health"],
      county_scope: ["Kent"],
      source_url: "https://example.com/c",
    },
  ],
};

assert.equal(countyMatches(radar.opportunities[0], "Kalamazoo"), true);
assert.equal(countyMatches(radar.opportunities[1], "Kalamazoo"), true);
assert.equal(countyMatches(radar.opportunities[2], "Kalamazoo"), false);

const parsed = parseArgs(["--status", "open,continuous", "--county", "Kalamazoo", "--format", "json", "--as-of", "2026-09-19"]);
assert.deepEqual(parsed.status, ["open", "continuous"]);
assert.equal(parsed.county, "Kalamazoo");
assert.equal(parsed.format, "json");

const county = filterFunding(radar, {
  status: ["open", "continuous"],
  county: "Kalamazoo",
  tag: [],
  dueWithin: null,
  asOf: new Date("2026-09-19T00:00:00Z"),
});
assert.deepEqual(county.map((x) => x.id), ["statewide", "kalamazoo"]);

const due10 = filterFunding(radar, {
  status: ["open"],
  county: "",
  tag: [],
  dueWithin: 10,
  asOf: new Date("2026-09-19T00:00:00Z"),
});
assert.deepEqual(due10.map((x) => x.id), ["statewide"]);

const soil = filterFunding(radar, {
  status: [],
  county: "",
  tag: ["soil health"],
  dueWithin: null,
  asOf: new Date("2026-09-19T00:00:00Z"),
});
assert.deepEqual(soil.map((x) => x.id), ["statewide", "kent"]);

assert.match(renderMarkdown(county, radar), /Kalamazoo only/);

console.log("PASS: CropCircuit funding query");
