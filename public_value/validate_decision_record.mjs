import fs from "node:fs";

const GATES = new Set(["pass_to_review","hold","reject"]);
const OUTCOMES = new Set(["proceed","hold","reject","experiment"]);
const STATUSES = new Set(["pass","fail","unknown"]);
const REVERSIBILITY = new Set(["high","medium","low","unknown"]);

export function validateDecisionRecord(record) {
  const errors=[];
  if (!record || typeof record !== "object" || Array.isArray(record)) return ["record must be an object"];
  if (record.schema_version !== "1.0") errors.push("schema_version must be 1.0");
  for (const key of ["decision_id","created_at","decision","purpose","reciprocity","enoughness","wider_system_effects","review_trigger"]) {
    if (typeof record[key] !== "string" || !record[key].trim()) errors.push(`${key} must be a non-empty string`);
  }
  if (!Array.isArray(record.hard_constraints)) errors.push("hard_constraints must be an array");
  else {
    record.hard_constraints.forEach((c,i)=>{
      if (!c || typeof c !== "object") { errors.push(`hard_constraints[${i}] must be an object`); return; }
      if (typeof c.id !== "string" || !c.id.trim()) errors.push(`hard_constraints[${i}].id must be non-empty`);
      if (typeof c.required !== "boolean") errors.push(`hard_constraints[${i}].required must be boolean`);
      if (!STATUSES.has(c.status)) errors.push(`hard_constraints[${i}].status is invalid`);
      if (typeof c.evidence !== "string") errors.push(`hard_constraints[${i}].evidence must be a string`);
    });
  }
  if (!record.viability || typeof record.viability !== "object") errors.push("viability must be an object");
  else for (const key of ["financial","operational","legal","technical","biological_ecological"]) {
    if (typeof record.viability[key] !== "string") errors.push(`viability.${key} must be a string`);
  }
  if (!Array.isArray(record.unknowns) || record.unknowns.some(x=>typeof x!=="string")) errors.push("unknowns must be an array of strings");
  if (!record.reversibility || typeof record.reversibility !== "object") errors.push("reversibility must be an object");
  else {
    if (!REVERSIBILITY.has(record.reversibility.level)) errors.push("reversibility.level is invalid");
    if (typeof record.reversibility.note !== "string") errors.push("reversibility.note must be a string");
  }
  if (!GATES.has(record.gate)) errors.push("gate is invalid");
  if (!OUTCOMES.has(record.decision_outcome)) errors.push("decision_outcome is invalid");

  if (Array.isArray(record.hard_constraints)) {
    const required=record.hard_constraints.filter(c=>c?.required===true);
    const hasFail=required.some(c=>c.status==="fail");
    const hasUnknown=required.some(c=>c.status==="unknown");
    const hasOtherUnknown=Array.isArray(record.unknowns) && record.unknowns.some(x=>String(x).trim());

    if (hasFail && record.gate!=="reject") errors.push("gate must be reject when a required hard constraint fails");
    if (!hasFail && (hasUnknown || hasOtherUnknown) && record.gate!=="hold") errors.push("gate must be hold when required constraints or important effects remain unknown");
    if (!hasFail && !hasUnknown && !hasOtherUnknown && record.gate!=="pass_to_review") errors.push("gate must be pass_to_review when no required hard constraint fails or remains unknown");
    if (record.gate==="reject" && record.decision_outcome==="proceed") errors.push("decision_outcome cannot be proceed when gate is reject");
    if (record.gate==="hold" && record.decision_outcome==="proceed") errors.push("decision_outcome cannot be proceed when gate is hold");
  }

  return errors;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const file=process.argv[2];
  if (!file) {
    console.error("Usage: node public_value/validate_decision_record.mjs <record.json> [more.json]");
    process.exit(2);
  }
  let failed=false;
  for (const path of process.argv.slice(2)) {
    try {
      const record=JSON.parse(fs.readFileSync(path,"utf8"));
      const errors=validateDecisionRecord(record);
      if (errors.length) {
        failed=true;
        console.error(`FAIL ${path}`);
        errors.forEach(e=>console.error(" - "+e));
      } else console.log(`PASS ${path}`);
    } catch (e) {
      failed=true; console.error(`FAIL ${path}: ${e.message}`);
    }
  }
  if (failed) process.exit(1);
}
