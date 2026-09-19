import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
const taxonomy=JSON.parse(fs.readFileSync(path.join(here,"farm_chore_taxonomy.json"),"utf8"));
const errors=[];
const categoryIds=new Set();
const codes=new Set();

for(const category of taxonomy.categories||[]){
  if(categoryIds.has(category.id))errors.push(`duplicate category id: ${category.id}`);
  categoryIds.add(category.id);
  if(!category.tasks?.length)errors.push(`category has no tasks: ${category.id}`);
  for(const task of category.tasks||[]){
    if(codes.has(task.code))errors.push(`duplicate task code: ${task.code}`);
    codes.add(task.code);
    if(!task.code.startsWith(category.id+".")){
      errors.push(`task code ${task.code} does not match category ${category.id}`);
    }
    if(!task.label?.trim())errors.push(`task label missing: ${task.code}`);
  }
}

if(errors.length){
  for(const e of errors)console.error("ERROR:",e);
  process.exit(1);
}
console.log(`PASS: ${categoryIds.size} chore categories; ${codes.size} unique task codes`);
