import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));

function parseCSV(text){
  const rows=[];let row=[],field="",quoted=false;
  for(let i=0;i<text.length;i++){
    const ch=text[i];
    if(quoted){
      if(ch==='"'&&text[i+1]==='"'){field+='"';i++}
      else if(ch==='"')quoted=false;
      else field+=ch;
    }else{
      if(ch==='"')quoted=true;
      else if(ch===','){row.push(field);field=""}
      else if(ch==='\n'){row.push(field);rows.push(row);row=[];field=""}
      else if(ch!=='\r')field+=ch;
    }
  }
  if(field.length||row.length){row.push(field);rows.push(row)}
  return rows.filter(r=>r.some(v=>String(v).length));
}

function validatePackage(filename){
  const pkg=JSON.parse(fs.readFileSync(path.join(here,filename),"utf8"));
  const errors=[];
  if(!Array.isArray(pkg.resources)||!pkg.resources.length)errors.push("package has no resources");
  for(const resource of pkg.resources||[]){
    const resourcePath=path.join(here,resource.path);
    if(!fs.existsSync(resourcePath)){errors.push(`missing resource ${resource.path}`);continue}
    const rows=parseCSV(fs.readFileSync(resourcePath,"utf8"));
    if(rows.length<2){errors.push(`${resource.path} has no data rows`);continue}
    const headers=rows[0];
    const fields=(resource.schema?.fields||[]).map(f=>f.name);
    for(const field of fields)if(!headers.includes(field))errors.push(`${resource.path} missing declared field ${field}`);
    const primary=resource.schema?.primaryKey;
    if(primary){
      const idx=headers.indexOf(primary);
      if(idx<0)errors.push(`${resource.path} primaryKey ${primary} missing from header`);
      else{
        const values=rows.slice(1).map(r=>r[idx]);
        if(values.some(v=>!String(v||"").trim()))errors.push(`${resource.path} has blank primary key`);
        if(new Set(values).size!==values.length)errors.push(`${resource.path} has duplicate primary key values`);
      }
    }
  }
  if(errors.length){
    errors.forEach(e=>console.error(`ERROR ${filename}: ${e}`));
    return false;
  }
  console.log(`PASS: ${filename} — ${pkg.resources.length} resource(s)`);
  return true;
}

const ok=[
  validatePackage("funding_datapackage.json"),
  validatePackage("taxonomy_datapackage.json"),
].every(Boolean);

if(!ok)process.exit(1);
