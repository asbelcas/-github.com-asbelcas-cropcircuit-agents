#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const CATEGORY_MAP = new Map([
  ["livestock","livestock"],
  ["field / crop","field_crop"],
  ["field/crop","field_crop"],
  ["field_crop","field_crop"],
  ["harvest","harvest"],
  ["wash / pack","wash_pack"],
  ["wash/pack","wash_pack"],
  ["wash_pack","wash_pack"],
  ["market / sales","market_sales"],
  ["market/sales","market_sales"],
  ["market_sales","market_sales"],
  ["maintenance","maintenance"],
  ["fencing","fencing"],
  ["water","water"],
  ["admin","admin"],
  ["other","other"],
]);

const ENTERPRISES = new Set([
  "vegetables","fruit","orchard","flowers","poultry","small-ruminants",
  "cattle","pigs","dairy","hay-forage","grain","agroforestry",
  "farm-stand","CSA","farmers-market","education","mixed","other"
]);

function csvRows(text) {
  const rows=[];
  let row=[],field="",quoted=false;
  for(let i=0;i<text.length;i++){
    const ch=text[i];
    if(quoted){
      if(ch==='"' && text[i+1]==='"'){field+='"';i+=1}
      else if(ch==='"'){quoted=false}
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
  return rows.slice(1).filter(r=>r.some(v=>String(v).trim())).map(r=>{
    const out={};
    headers.forEach((h,i)=>out[h]=r[i]??"");
    return out;
  });
}

function normalizeEnterpriseList(value) {
  const values=String(value||"").split(",").map(x=>x.trim()).filter(Boolean);
  if(!values.length) throw new Error("--enterprises requires at least one value");
  for(const item of values){
    if(!ENTERPRISES.has(item)) throw new Error(`unsupported enterprise type: ${item}`);
  }
  return [...new Set(values)];
}

function round1(n){return Math.round((n+Number.EPSILON)*10)/10}

export function buildBenchmarkFromRows(rows, options) {
  const days=Number(options.days);
  if(!Number.isFinite(days)||days<=0) throw new Error("days must be greater than zero");

  const totalByCategory={
    livestock:0,field_crop:0,harvest:0,wash_pack:0,market_sales:0,
    maintenance:0,fencing:0,water:0,admin:0,other:0
  };
  let totalHours=0;

  for(const row of rows){
    let hours=Number(row.worker_hours);
    if(!Number.isFinite(hours)){
      const minutes=Number(row.minutes),workers=Number(row.workers);
      hours=(Number.isFinite(minutes)&&Number.isFinite(workers))
        ? Math.max(minutes,0)/60*Math.max(workers,0)
        : 0;
    }
    hours=Math.max(hours||0,0);
    totalHours+=hours;

    const raw=String(row.category||"other").trim().toLowerCase();
    const key=CATEGORY_MAP.get(raw)||"other";
    totalByCategory[key]+=hours;
  }

  if(totalHours<=0) throw new Error("input contains no positive worker-hours");

  const shares={};
  let allocated=0;
  const keys=Object.keys(totalByCategory);
  for(let i=0;i<keys.length;i++){
    const key=keys[i];
    if(i===keys.length-1){
      shares[key]=round1(100-allocated);
    }else{
      shares[key]=round1(totalByCategory[key]/totalHours*100);
      allocated+=shares[key];
    }
  }

  const weeklyHours=totalHours/days*7;

  return {
    schema_version:"1.0",
    period:options.period,
    region:options.region,
    acreage_band:options.acreageBand,
    enterprise_types:options.enterprises,
    operator_count_band:options.operators,
    weekly_worker_hours:round1(weeklyHours),
    labor_cost_band:options.laborCostBand,
    category_share_percent:shares,
    source:"cropcircuit-labor-log",
    created_with:"CropCircuit labor_log_to_benchmark.mjs 1.0"
  };
}

function parseArgs(argv){
  const out={
    input:null,days:null,period:"year-round",region:"Michigan",
    acreageBand:null,operators:"1",laborCostBand:"not-provided",enterprises:null
  };
  for(let i=0;i<argv.length;i++){
    const arg=argv[i];
    const next=()=>{if(i+1>=argv.length)throw new Error(`missing value after ${arg}`);return argv[++i]};
    if(arg==="--input")out.input=next();
    else if(arg==="--days")out.days=Number(next());
    else if(arg==="--period")out.period=next();
    else if(arg==="--region")out.region=next();
    else if(arg==="--acreage-band")out.acreageBand=next();
    else if(arg==="--operators")out.operators=next();
    else if(arg==="--labor-cost-band")out.laborCostBand=next();
    else if(arg==="--enterprises")out.enterprises=normalizeEnterpriseList(next());
    else if(arg==="--help"||arg==="-h")out.help=true;
    else throw new Error(`unknown argument: ${arg}`);
  }
  return out;
}

function help(){
  return `CropCircuit labor-log to benchmark transformer

Usage:
  node public_value/labor_log_to_benchmark.mjs \
    --input cropcircuit-farm-labor-log.csv \
    --days 14 \
    --period summer \
    --region Michigan \
    --acreage-band 5-19.9 \
    --operators 1 \
    --labor-cost-band 20-24.99 \
    --enterprises vegetables,CSA

Required:
  --input FILE
  --days N
  --acreage-band BAND
  --enterprises LIST

The output contains no task names, dates, notes, county, farm name, or contact information.
`;
}

async function main(){
  const args=parseArgs(process.argv.slice(2));
  if(args.help){process.stdout.write(help());return}
  if(!args.input)throw new Error("--input is required");
  if(!args.acreageBand)throw new Error("--acreage-band is required");
  if(!args.enterprises)throw new Error("--enterprises is required");

  const rows=csvRows(fs.readFileSync(args.input,"utf8"));
  const record=buildBenchmarkFromRows(rows,args);
  process.stdout.write(JSON.stringify(record,null,2)+"\n");
}

const invokedDirectly=process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(invokedDirectly){
  main().catch(e=>{console.error("ERROR:",e.message);process.exit(1)});
}
