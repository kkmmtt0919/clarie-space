const {chromium}=require('@playwright/test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 fs.mkdirSync('checks/world-label',{recursive:true});
 try{for(const width of [1440,390]){
  const p=await b.newPage({viewport:{width,height:960}});
  await p.addInitScript(()=>{
   window.worldFlightHeightReads=0;
   const native=Object.getOwnPropertyDescriptor(HTMLElement.prototype,'offsetHeight');
   Object.defineProperty(HTMLElement.prototype,'offsetHeight',{...native,get(){if(this.classList.contains('world-flying-photo'))window.worldFlightHeightReads++;return native.get.call(this);}});
  });
  await p.goto('http://127.0.0.1:4198');await p.waitForFunction(()=>window.claireState?.ready&&!window.claireState.intro);
  await p.locator('.nav-entry[data-entry="2"]').click();await p.waitForTimeout(1700);
  const label=await p.locator('.world-intro').evaluate(el=>{
   const r=el.getBoundingClientRect(),c=document.getElementById('panel-content').getBoundingClientRect(),s=getComputedStyle(el,'::before');
   return {pinTop:r.top+parseFloat(s.top),clipTop:c.top,texture:getComputedStyle(el).backgroundImage};
  });
  assert.ok(label.pinTop>=label.clipTop+2,'Complete heading pin stays inside clipping boundary');
  assert.ok(label.texture.includes('world-label-paper'),'Lightweight paper texture loads');
  assert.equal(await p.evaluate(()=>window.worldFlightHeightReads),0,'Flight frames do not force height measurement');
  await p.screenshot({path:`checks/world-label/${width}.png`});await p.close();
 }}finally{await b.close();}
 console.log('World label checks passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
