'use strict';
const fs=require('node:fs');const path=require('node:path');const os=require('node:os');const crypto=require('node:crypto');const cp=require('node:child_process');
const root=path.resolve(__dirname,'../..');const isolated=fs.mkdtempSync(path.join(os.tmpdir(),'collective_engine_repro_'));
for(const rel of ['web/assets/trading-engine.js','tests/test_trading_engine.cjs']){const target=path.join(isolated,rel);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(root,rel),target);}
const log=path.join(isolated,'run.log');const fd=fs.openSync(log,'w');
try{cp.execFileSync(process.execPath,[path.join(isolated,'tests/test_trading_engine.cjs')],{stdio:['ignore',fd,fd]});}finally{fs.closeSync(fd);}
const files=['simulation_runs.csv','simulation_summary.csv','simulation_paired_ablations.csv','guided_demo_paths.csv'];const results=[];
for(const name of files){const rel=path.join('results/tables/collective_trading_v1',name);const a=fs.readFileSync(path.join(root,rel));const b=fs.readFileSync(path.join(isolated,rel));if(!a.equals(b))throw new Error('Reproduction mismatch: '+rel);results.push({file:rel,sha256:crypto.createHash('sha256').update(a).digest('hex'),exact_match:true});}
const report={status:'pass',isolated_directory:isolated,source_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'web/assets/trading-engine.js'))).digest('hex'),tables:results.length,results};
fs.writeFileSync(path.join(root,'results/checks/collective_trading_engine_reproduction_v1.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
