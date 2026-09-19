import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here=path.dirname(fileURLToPath(import.meta.url));
const taxonomy=JSON.parse(fs.readFileSync(path.join(here,"farm_chore_taxonomy.json"),"utf8"));
const validCodes=new Set(taxonomy.categories.flatMap(c=>c.tasks.map(t=>t.code)));

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
  if(!rows.length)return [];
  const headers=rows[0].map(x=>x.trim().toLowerCase());
  return rows.slice(1).filter(r=>r.some(v=>String(v).trim())).map((r,index)=>{
    const out={_line:index+2};headers.forEach((h,i)=>out[h]=r[i]??"");return out;
  });
}

export function validateRows(rows){
  const errors=[];
  for(const r of rows){
    const p=`line ${r._line||"?"}`;
    if(!/^\d{4}-\d{2}-\d{2}$/.test(String(r.date||"")))errors.push(`${p}: invalid date`);
    if(!String(r.category||"").trim())errors.push(`${p}: missing category`);
    if(!String(r.task||"").trim())errors.push(`${p}: missing task`);
    const code=String(r.chore_code||"").trim();
    if(code&&!validCodes.has(code))errors.push(`${p}: unknown chore_code ${code}`);
    const minutes=Number(r.minutes),workers=Number(r.workers),hours=Number(r.worker_hours);
    if(!Number.isFinite(minutes)||minutes<=0)errors.push(`${p}: minutes must be > 0`);
    if(!Number.isFinite(workers)||workers<=0)errors.push(`${p}: workers must be > 0`);
    if(!Number.isFinite(hours)||hours<0)errors.push(`${p}: worker_hours must be >= 0`);
    if(Number.isFinite(minutes)&&Number.isFinite(workers)&&Number.isFinite(hours)){
      const expected=minutes/60*workers;
      if(Math.abs(expected-hours)>0.011)errors.push(`${p}: worker_hours ${hours} differs from minutes/workers calculation ${expected.toFixed(2)}`);
    }
  }
  return errors;
}

function main(){
  const files=process.argv.slice(2);
  if(!files.length){
    console.error("Usage: node public_value/validate_labor_contract.mjs FILE.csv [FILE2.csv ...]");
    process.exit(2);
  }
  let failures=0;
  for(const file of files){
    const rows=parseCSV(fs.readFileSync(file,"utf8"));
    const errors=validateRows(rows);
    if(errors.length){
      failures+=errors.length;
      for(const e of errors)console.error(`ERROR ${file}: ${e}`);
    }else{
      console.log(`PASS: ${file} — ${rows.length} labor rows`);
    }
  }
  if(failures)process.exit(1);
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main();
