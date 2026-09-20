import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";
import { validateWorkspace } from "./workspace.js";

const SENSITIVE_KEY_PATTERN = /(password|passwd|secret|api[_-]?key|ssn|social[_-]?security|card[_-]?number|cvv|cvc|routing[_-]?number|bank[_-]?account)/i;

function walkKeys(value, trail = [], findings = []) {
  if (Array.isArray(value)) {
    value.forEach((item,i)=>walkKeys(item,[...trail,String(i)],findings));
    return findings;
  }
  if (!value || typeof value !== "object") return findings;
  for (const [key,val] of Object.entries(value)) {
    const next=[...trail,key];
    if (SENSITIVE_KEY_PATTERN.test(key)) findings.push(next.join("."));
    walkKeys(val,next,findings);
  }
  return findings;
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

export function validateSetupDelivery(dir) {
  const errors=[];
  const warnings=[];
  const root=path.resolve(dir);
  const workspacePath=path.join(root,"workspace.json");
  const notePath=path.join(root,"delivery_note.md");

  if (!fs.existsSync(workspacePath)) errors.push("missing workspace.json");
  if (!fs.existsSync(notePath)) errors.push("missing delivery_note.md");

  let workspace=null;
  if (fs.existsSync(workspacePath)) {
    try {
      workspace=JSON.parse(fs.readFileSync(workspacePath,"utf8"));
      const workspaceErrors=validateWorkspace(workspace);
      errors.push(...workspaceErrors.map(x=>`workspace: ${x}`));

      const sensitive=walkKeys(workspace);
      if (sensitive.length) {
        errors.push(`workspace contains sensitive-looking field name(s): ${sensitive.join(", ")}`);
      }

      const json=JSON.stringify(workspace);
      if (/(?:demo|case|synthetic)-/i.test(json)) errors.push("workspace contains synthetic/example identifiers (demo- / case- / synthetic-)");
      if (/synthetic case-study|synthetic demo|demonstration only/i.test(json)) errors.push("workspace appears to contain synthetic/example content");
    } catch (error) {
      errors.push(`workspace.json parse failed: ${error.message}`);
    }
  }

  const canonicalFiles=fs.existsSync(root)
    ? fs.readdirSync(root).filter(name=>name.endsWith(".csv")).sort()
    : [];

  if (!canonicalFiles.length) warnings.push("no canonical CSV files found");

  const checksums={};
  for (const name of ["workspace.json","delivery_note.md",...canonicalFiles]) {
    const file=path.join(root,name);
    if (fs.existsSync(file) && fs.statSync(file).isFile()) checksums[name]=sha256(file);
  }

  return {
    ok:errors.length===0,
    errors,
    warnings,
    canonical_csv_files:canonicalFiles,
    checksums,
    workspace_counts: workspace ? {
      labor_entries:workspace.labor_entries?.length ?? 0,
      chore_schedule:workspace.chore_schedule?.length ?? 0,
      equipment_maintenance:workspace.equipment_maintenance?.length ?? 0,
      parts_inventory:workspace.parts_inventory?.length ?? 0,
      harvest_entries:workspace.harvest_entries?.length ?? 0,
      sales_entries:workspace.sales_entries?.length ?? 0,
    } : null,
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const dir=process.argv[2];
  if (!dir) {
    console.error("Usage: node public_value/validate_setup_delivery.mjs <delivery-directory>");
    process.exit(2);
  }
  const result=validateSetupDelivery(dir);
  console.log(JSON.stringify(result,null,2));
  if (!result.ok) process.exit(1);
}
