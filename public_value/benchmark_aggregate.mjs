#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export function median(values) {
  const sorted=[...values].sort((a,b)=>a-b);
  if(!sorted.length) return null;
  const mid=Math.floor(sorted.length/2);
  return sorted.length%2 ? sorted[mid] : (sorted[mid-1]+sorted[mid])/2;
}

export function percentile(values,p) {
  const sorted=[...values].sort((a,b)=>a-b);
  if(!sorted.length) return null;
  if(sorted.length===1) return sorted[0];
  const idx=(sorted.length-1)*p;
  const lo=Math.floor(idx),hi=Math.ceil(idx);
  if(lo===hi) return sorted[lo];
  return sorted[lo]+(sorted[hi]-sorted[lo])*(idx-lo);
}

function cohortKey(record, fields) {
  return fields.map((f)=>{
    const v=record[f];
    if(Array.isArray(v)) return v.slice().sort().join("+");
    return String(v);
  }).join("|");
}

export function aggregate(records,{groupBy=["region","acreage_band"],k=5}={}) {
  const groups=new Map();
  for(const record of records){
    const key=cohortKey(record,groupBy);
    const bucket=groups.get(key)||[];
    bucket.push(record);groups.set(key,bucket);
  }

  const result=[];
  for(const [key,rows] of groups){
    if(rows.length<k){
      result.push({
        cohort:key,
        group_by:Object.fromEntries(groupBy.map((f,i)=>[f,key.split("|")[i]])),
        sample_size:rows.length,
        suppressed:true,
        reason:`sample_size_below_k_${k}`
      });
      continue;
    }

    const weekly=rows.map(r=>Number(r.weekly_worker_hours)||0);
    const shares={};
    const categoryKeys=Object.keys(rows[0].category_share_percent||{});
    for(const c of categoryKeys){
      const vals=rows.map(r=>Number(r.category_share_percent?.[c])||0);
      shares[c]={
        median:Number(median(vals).toFixed(1)),
        p25:Number(percentile(vals,0.25).toFixed(1)),
        p75:Number(percentile(vals,0.75).toFixed(1))
      };
    }

    result.push({
      cohort:key,
      group_by:Object.fromEntries(groupBy.map((f,i)=>[f,key.split("|")[i]])),
      sample_size:rows.length,
      suppressed:false,
      weekly_worker_hours:{
        median:Number(median(weekly).toFixed(1)),
        p25:Number(percentile(weekly,0.25).toFixed(1)),
        p75:Number(percentile(weekly,0.75).toFixed(1))
      },
      category_share_percent:shares
    });
  }

  return result.sort((a,b)=>a.cohort.localeCompare(b.cohort));
}

function parseJsonl(text){
  return text.split(/\r?\n/).map(x=>x.trim()).filter(Boolean).map((line,i)=>{
    try{return JSON.parse(line)}catch{throw new Error(`invalid JSON on line ${i+1}`)}
  });
}

function parseArgs(argv){
  const out={input:null,groupBy:["region","acreage_band"],k:5};
  for(let i=0;i<argv.length;i++){
    const arg=argv[i];
    const next=()=>{if(i+1>=argv.length)throw new Error(`missing value after ${arg}`);return argv[++i]};
    if(arg==="--input") out.input=next();
    else if(arg==="--group-by") out.groupBy=next().split(",").map(x=>x.trim()).filter(Boolean);
    else if(arg==="--k") out.k=Math.max(2,Number(next())||5);
    else if(arg==="--help"||arg==="-h") out.help=true;
    else throw new Error(`unknown argument: ${arg}`);
  }
  return out;
}

function help(){
  return `CropCircuit benchmark aggregator

Usage:
  node public_value/benchmark_aggregate.mjs --input records.jsonl [options]

Options:
  --group-by region,acreage_band   Cohort fields
  --k 5                            Minimum sample size before statistics publish
  -h, --help                       Show help

Input format:
  One benchmark JSON object per line.

The output always reports sample size. Cohorts below k are suppressed and contain no median or percentile statistics.
`;
}

async function main(){
  const args=parseArgs(process.argv.slice(2));
  if(args.help){process.stdout.write(help());return}
  if(!args.input) throw new Error("--input is required");
  const records=parseJsonl(fs.readFileSync(args.input,"utf8"));
  process.stdout.write(JSON.stringify({
    schema_version:"1.0",
    privacy_floor_k:args.k,
    group_by:args.groupBy,
    cohort_count:new Set(records.map(r=>cohortKey(r,args.groupBy))).size,
    record_count:records.length,
    cohorts:aggregate(records,{groupBy:args.groupBy,k:args.k})
  },null,2)+"\n");
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if(invokedDirectly){
  main().catch(e=>{console.error("ERROR:",e.message);process.exit(1)});
}
