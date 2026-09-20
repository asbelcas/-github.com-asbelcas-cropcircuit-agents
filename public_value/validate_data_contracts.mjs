import fs from "node:fs";

const path = process.argv[2] || "public_value/data_contracts.json";
const data = JSON.parse(fs.readFileSync(path, "utf8"));
const errors = [];

if (!data || typeof data !== "object") errors.push("root must be an object");
if (!Array.isArray(data.contracts) || data.contracts.length === 0) {
  errors.push("contracts must be a non-empty array");
}

const ids = new Set();

for (const contract of data.contracts ?? []) {
  const id = String(contract?.id ?? "").trim();
  if (!id) errors.push("contract missing id");
  else if (ids.has(id)) errors.push(`duplicate contract id ${id}`);
  else ids.add(id);

  if (!String(contract?.label ?? "").trim()) errors.push(`${id || "(unknown)"}: missing label`);
  if (!String(contract?.workspace_collection ?? "").trim()) errors.push(`${id || "(unknown)"}: missing workspace_collection`);
  if (!String(contract?.storage_key ?? "").trim()) errors.push(`${id || "(unknown)"}: missing storage_key`);
  if (!Array.isArray(contract?.fields) || !contract.fields.length) {
    errors.push(`${id || "(unknown)"}: fields must be non-empty`);
    continue;
  }

  const names = new Set();
  for (const field of contract.fields) {
    const name = String(field?.name ?? "").trim();
    if (!name) errors.push(`${id}: field missing name`);
    else if (names.has(name)) errors.push(`${id}: duplicate field ${name}`);
    else names.add(name);

    if (!["string","date","number","integer","enum"].includes(field?.type)) {
      errors.push(`${id}.${name}: unsupported type ${field?.type}`);
    }

    if (field?.type === "enum" && (!Array.isArray(field.values) || !field.values.length)) {
      errors.push(`${id}.${name}: enum requires values`);
    }
  }

  for (const required of contract.required ?? []) {
    if (!names.has(required)) errors.push(`${id}: required field ${required} not declared`);
  }
}

if (errors.length) {
  for (const error of errors) console.error(`FAIL: ${error}`);
  process.exit(1);
}

console.log(`PASS: ${data.contracts.length} CropCircuit data contracts; all IDs and field names unique`);
