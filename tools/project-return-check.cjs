const {chromium}=require('@playwright/test');
const assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 try{
  for(const width of [1440,390]){
   const p=await b.newPage({viewport:{width,height:960}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
   await p.goto('http://127.0.0.1:4198');await p.waitForFunction(()=>window.claireState?.ready&&!window.claireState.intro);
   await p.locator('.nav-entry[data-entry="1"]').click();await p.waitForTimeout(1300);
   await p.locator('[data-project="1"]').click();await p.waitForTimeout(650);
   await p.evaluate(()=>{window.returnSamples=[];function sample(){const c=document.querySelector('[data-project="1"]'),r=c.getBoundingClientRect();window.returnSamples.push({x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,reading:document.getElementById('project-cards').classList.contains('project-reading')});if(window.returnSamples.length<160)requestAnimationFrame(sample);}requestAnimationFrame(sample);});
   await p.locator('.project-detail:not([hidden]) .project-back').click();await p.waitForTimeout(800);
   const samples=await p.evaluate(()=>window.returnSamples),end=samples.findIndex((s,i)=>i>0&&!s.reading&&samples[i-1].reading);
   console.log({errors,end,first:samples[0],last:samples.at(-1)});assert.ok(end>0,'Return completes');
   const delta=Math.hypot(samples[end].x-samples[end-1].x,samples[end].y-samples[end-1].y);
   console.log({width,commitDelta:delta});assert.ok(delta<12,'No jump at layout handoff');assert.deepEqual(errors,[]);
   await p.close();
  }
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

