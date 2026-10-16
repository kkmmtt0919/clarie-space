const {chromium}=require('@playwright/test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const out='checks/label-loader';fs.mkdirSync(out,{recursive:true});
const base=process.env.CLAIRE_BASE_URL || 'http://127.0.0.1:4198';
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 const errors=[];
 try {
  // Hold back the application bundle to inspect the very first HTML paint.
  const first=await browser.newContext({viewport:{width:1920,height:930}});
  let releaseBundle;
  const bundleGate=new Promise(resolve=>releaseBundle=resolve);
  await first.route('**/app.js',async route=>{await bundleGate;await route.continue();});
  const earlyPage=await first.newPage();
  await earlyPage.goto(base,{waitUntil:'domcontentloaded',timeout:1000}).catch(()=>{});
  assert.equal(await earlyPage.locator('#loading').isVisible(),false,'Unpositioned label never paints');
  releaseBundle();
  await earlyPage.waitForFunction(()=>document.getElementById('loading').dataset.positioned==='true');
  assert.ok(await earlyPage.locator('.loading-label').evaluate(el=>el.style.transform.startsWith('matrix')),'First visible label has its projected position');
  await first.close();
  const context=await browser.newContext({viewport:{width:1440,height:960}});
  await context.route('**/assets/claire-v3.glb',async route=>{await new Promise(r=>setTimeout(r,1600));await route.continue();});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{
    window.loaderProgressSamples=[];
    function sample(now){
      const ring=document.querySelector('.loading-ring-progress');
      if(ring?.style.strokeDashoffset)window.loaderProgressSamples.push({time:now,value:1-Number(ring.style.strokeDashoffset)});
      if(!document.getElementById('loading')?.hidden)requestAnimationFrame(sample);
    }
    requestAnimationFrame(sample);
  });
  await page.goto(base);
  await page.waitForFunction(()=>document.querySelector('.loading-label').style.transform.startsWith('matrix'));
  await page.screenshot({path:out+'/loading.png'});
  assert.ok(await page.locator('.loading-ring-progress').evaluate(el=>parseFloat(getComputedStyle(el).strokeWidth)>=16),'Progress outline is thicker');
  assert.equal(await page.locator('.loading-ring-progress').getAttribute('rx'),'149','Capsule corners');
  const initialWidth=await page.locator('.loading-label-art').evaluate(el=>el.getBoundingClientRect().width);
  assert.ok(await page.locator('.loading-label-art').evaluate(el=>Number(getComputedStyle(el).transform.split('(')[1].split(',')[0])>1),'Loading print is enlarged');
  const anchor=await page.locator('.loading-label').getAttribute('style');
  await page.waitForFunction(()=>window.claireState?.ready);
  await page.waitForFunction(()=>document.querySelector('.loading-ring-progress').style.strokeDashoffset==='0');
  const fullRingTime=await page.evaluate(()=>performance.now());
  const samples=await page.evaluate(()=>window.loaderProgressSamples);
  assert.ok(samples.every((s,i)=>i===0||s.value>=samples[i-1].value),'Spring progress never moves backwards');
  const moving=samples.filter(s=>s.value>0);
  assert.ok(moving.at(-1).time-moving[0].time>=1150,'Spring preserves the minimum loading pace');
  assert.equal(await page.locator('.loading-label-art').evaluate(el=>el.getAnimations().length),0,'Full ring is shown before shrinking');
  await page.waitForFunction(()=>document.querySelector('.loading-label-art').getAnimations().length>0);
  assert.ok(await page.evaluate(()=>performance.now())-fullRingTime>=100,'Completed outline pauses before handoff');
  await page.waitForTimeout(250);
  await page.screenshot({path:out+'/handoff.png'});
  assert.ok(await page.locator('.loading-label-art').evaluate(el=>el.getBoundingClientRect().width)<initialWidth,'Print shrinks during handoff');
  assert.equal(await page.locator('.loading-label').getAttribute('style'),anchor,'Loader anchor stays fixed');
  await page.waitForFunction(()=>document.getElementById('loading').hidden);
  assert.equal((await page.evaluate(()=>window.claireState)).intro,true,'Opening starts after handoff');
  await page.locator('#skip-opening').click();
  await page.waitForFunction(()=>!window.claireState.intro);
  await page.reload();await page.waitForFunction(()=>window.claireState?.ready);
  await page.waitForFunction(()=>document.getElementById('loading').hidden);
  assert.equal((await page.evaluate(()=>window.claireState)).intro,true,'Refresh keeps the label-to-opening sequence');
  await context.close();
  for(const options of [{viewport:{width:390,height:844}},{viewport:{width:1440,height:960},reducedMotion:'reduce'}]){
   const c=await browser.newContext(options),p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));
   await p.goto(base);await p.waitForFunction(()=>window.claireState?.ready&&!window.claireState.intro);
   assert.equal(await p.locator('#loading').isVisible(),false);
   await p.screenshot({path:out+'/'+(options.reducedMotion?'reduced':'mobile')+'.png'});await c.close();
  }
  const c=await browser.newContext();await c.route('**/assets/claire-v3.glb',async route=>{await new Promise(r=>setTimeout(r,1000));await route.continue();});
  const p=await c.newPage();await p.goto(base);await p.locator('#skip-opening').click();
  assert.equal(await p.locator('#loading').isVisible(),false,'Skip responds during loading');
  await p.waitForFunction(()=>window.claireState?.ready&&!window.claireState.intro);await c.close();
  assert.deepEqual(errors,[]);console.log('Label loader checks passed');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

