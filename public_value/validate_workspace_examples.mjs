import fs from "node:fs";
import { validateWorkspace } from "./workspace.js";

const files = process.argv.slice(2);
const targets = files.length ? files : [
  "public_value/examples/synthetic_workspace_1_2.json",
  "public_value/templates/workspace_1_2_empty.json",
];

let failed = false;

for (const path of targets) {
  try {
    const data = JSON.parse(fs.readFileSync(path, "utf8"));
    const errors = validateWorkspace(data);
    if (errors.length) {
      failed = true;
      console.error(`FAIL ${path}: ${errors.join("; ")}`);
    } else {
      console.log(`PASS ${path}: Workspace ${data.schema_version}`);
    }
  } catch (error) {
    failed = true;
    console.error(`FAIL ${path}: ${error.message}`);
  }
}

if (failed) process.exit(1);
