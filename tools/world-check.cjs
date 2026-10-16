const {chromium}=require('@playwright/test');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 const out=path.resolve('checks/world-board-20261007');fs.mkdirSync(out,{recursive:true});
 const errors=[];
 try{
  for(const scenario of ['desktop','mobile','reduced','offline']){
   const context=await browser.newContext({viewport:scenario==='mobile'?{width:390,height:844}:{width:1440,height:960},reducedMotion:scenario==='reduced'?'reduce':'no-preference'});
   const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));
   await p.goto(scenario==='offline'?require('node:url').pathToFileURL(path.resolve('claire.html')).href:(process.env.CLAIRE_BASE_URL||'http://127.0.0.1:4217'));
   await p.waitForFunction(()=>window.claireState?.ready&&!window.claireState.intro);
   await p.locator('.nav-entry[data-entry="2"]').click();await p.waitForFunction(()=>document.querySelector('#content-dialog').open);
   if(scenario==='desktop'){
    for(const [delay,name] of [[80,'01-extract'],[170,'02-spread'],[260,'03-land']]){await p.waitForTimeout(delay);await p.screenshot({path:path.join(out,name+'.png')});}
   }
   await p.locator('.world-collection .world-photo img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
   assert.equal(await p.locator('.world-collection .world-photo').count(),4);
   assert.equal(await p.locator('.world-collection .world-pin').count(),4);
   assert(await p.locator('#content-dialog').evaluate(el=>getComputedStyle(el).getPropertyValue('--world-board').includes('world-cork-board')||getComputedStyle(el).getPropertyValue('--world-board').includes('data:image/jpeg')));
   await p.waitForFunction(()=>!document.querySelector('#content-dialog').classList.contains('world-unfolding'));
   assert(await p.locator('.world-photo img').evaluateAll(imgs=>imgs.every(i=>i.naturalWidth>0)));
   assert(await p.locator('#content-dialog').evaluate(el=>el.scrollWidth<=el.clientWidth+2));
   assert(await p.locator('#content-dialog').evaluate(el=>el.scrollHeight<=el.clientHeight+2));
   assert(await p.locator('.world-collection .world-photo').evaluateAll(photos=>photos.every(el=>{const r=el.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth;})));
   await p.screenshot({path:path.join(out,scenario+'.png')});
   await p.locator('.world-photo').first().click();assert(await p.locator('.world-viewer').isVisible());
   await p.keyboard.press('Escape');assert(!(await p.locator('.world-viewer').isVisible()));assert(await p.locator('#content-dialog').evaluate(el=>el.open));
   await p.locator('#close-panel').click();await p.waitForFunction(()=>!document.querySelector('#content-dialog').open);
   assert.equal(await p.locator('.world-flight').count(),0);
   await p.locator('.nav-entry[data-entry="2"]').click();await p.waitForFunction(()=>document.querySelector('#content-dialog').open);await p.waitForTimeout(100);await p.locator('#close-panel').click();await p.waitForFunction(()=>!document.querySelector('#content-dialog').open);
   assert.equal(await p.locator('.world-flight').count(),0);
   await p.locator('.nav-entry[data-entry="2"]').focus();await p.keyboard.press('Enter');await p.waitForFunction(()=>document.querySelector('#content-dialog').open);assert.equal(await p.locator('.world-flight').count(),0);await p.keyboard.press('Escape');await p.waitForFunction(()=>!document.querySelector('#content-dialog').open);
   await p.locator('.nav-entry[data-entry="1"]').click();await p.locator('#project-cards').waitFor();await p.locator('#close-panel').click();
   console.log(scenario+': photos, layout, zoom, Escape, interrupt/reopen and project navigation passed');await context.close();
  }
  assert.deepEqual(errors,[]);console.log('No browser JavaScript errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
