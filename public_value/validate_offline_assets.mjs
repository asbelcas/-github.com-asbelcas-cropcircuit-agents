import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const sw=fs.readFileSync(path.join(root,"sw.js"),"utf8");
const block=sw.match(/const STATIC_ASSETS = \[([\s\S]*?)\];/);
if(!block){
  console.error("ERROR: STATIC_ASSETS block not found");
  process.exit(1);
}
const matches=[...block[1].matchAll(/"\.\/([^"]*)"/g)].map(m=>m[1]||"index.html");
const missing=[];
for(const rel of matches){
  const normalized=rel===""?"index.html":rel;
  if(!fs.existsSync(path.join(root,normalized)))missing.push(normalized);
}
if(!fs.existsSync(path.join(root,"site.webmanifest")))missing.push("site.webmanifest");
if(missing.length){
  missing.forEach(x=>console.error("ERROR: missing offline asset:",x));
  process.exit(1);
}
console.log(`PASS: ${matches.length} service-worker static assets exist`);
