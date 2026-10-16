const { chromium } = require('@playwright/test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root=path.resolve(__dirname,'..');
const out=process.env.CLAIRE_CHECK_DIR || path.join(root,'checks');fs.mkdirSync(out,{recursive:true});
const base=process.env.CLAIRE_BASE_URL || 'http://127.0.0.1:4193';
const report={passed:false,checks:[],errors:[],warnings:[]};
const check=(name,condition)=>{assert.ok(condition,name);report.checks.push(name);};
const state=p=>p.evaluate(()=>window.claireState);
const settle=p=>p.waitForFunction(()=>window.claireState?.ready&&!window.claireState.intro,{timeout:30000});
const close=p=>p.locator('#close-panel').click().then(()=>p.waitForFunction(()=>!window.claireState.dialogOpen));
async function shot(p,name){if(await p.locator('.reveal-about').isVisible()){await p.locator('.reveal-about').click();await p.waitForTimeout(550);}await p.locator('img:visible').evaluateAll(images=>Promise.all(images.map(image=>image.decode().catch(()=>{}))));await p.screenshot({path:path.join(out,name+'.png'),fullPage:true,animations:'disabled'});}
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-unsafe-swiftshader','--mute-audio']});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:960},deviceScaleFactor:1});
  const p=await context.newPage();p.on('pageerror',error=>report.errors.push(error.message));
  p.on('console',message=>{if(message.type()==='error')report.errors.push(message.text());if(message.type()==='warning')report.warnings.push(message.text());});
  await p.goto(base);await settle(p);await shot(p,'desktop');
  check('WebGL scene loads with exactly three discs',(await state(p)).discCount===3);
  check('No audio autoplay',await p.locator('#audio').evaluate(a=>a.paused&&!a.src));
  const baseline=(await state(p)).discPositions[0];
  for(let index=0;index<3;index++){
   await p.locator(`.nav-entry[data-entry="${index}"]`).hover();await p.waitForTimeout(350);
   const s=await state(p);check('Hover selects entry '+index,s.hovered===index&&s.active===0);
   check('Playing disc remains in place during hover '+index,s.discPositions[0].every((v,i)=>Math.abs(v-baseline[i])<1e-6));
   await shot(p,'hover-'+index);
  }
  for(let index=0;index<3;index++){await p.locator(`.nav-entry[data-entry="${index}"]`).hover();await p.waitForTimeout(30);}
  await p.mouse.move(40,450);await p.waitForTimeout(500);
  check('Rapid hover exit restores all cards',(await state(p)).cardProgress.every(v=>Math.abs(v)<.001));
  // The actual exposed card areas are accessible, stable three-dimensional hits.
  for(let index=0;index<3;index++){
   const stage=await p.locator('#stage').boundingBox();
   const point=await p.evaluate(index=>{
    const s=window.claireState,rect=document.getElementById('stage').getBoundingClientRect();
    function inside(x,y,poly){let hit=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;}
    const points=[];
    for(let y=8;y<rect.height;y+=12)for(let x=8;x<rect.width;x+=12){
     for(let i=2;i>=0;i--)if(inside(x,y,s.hitPolygons[i])||(i!==s.active&&inside(x,y,s.discPolygons[i]))){if(i===index)points.push([x,y]);break;}
    }
    return points[Math.floor(points.length/2)]||null;
   },index);
   check('Entry '+index+' has projected hit area',Boolean(point));
   await p.mouse.move(stage.x+point[0],stage.y+point[1]);await p.waitForTimeout(200);
   check('Actual scene pointer selects entry '+index,(await state(p)).hovered===index);
  }
  await p.locator('.nav-entry[data-entry="1"]').click();
  await p.waitForFunction(()=>window.claireState.busy);await p.waitForTimeout(600);await shot(p,'swap-out');
  await p.waitForFunction(()=>window.claireState.dialogOpen);check('Disc swap activates projects',(await state(p)).active===1);
  check('Swap never duplicates discs',(await state(p)).discCount===3);await shot(p,'panel-projects');await close(p);
  await p.locator('.nav-entry[data-entry="2"]').click();await p.waitForFunction(()=>window.claireState.dialogOpen);
  check('Second swap activates world',(await state(p)).active===2);await shot(p,'panel-world');await close(p);
  await p.locator('.nav-entry[data-entry="0"]').focus();await p.keyboard.press('Enter');await p.waitForFunction(()=>window.claireState.dialogOpen);
  check('Keyboard selection is immediate and activates about',!(await state(p)).busy&&(await state(p)).active===0);await shot(p,'panel-about');
  await p.keyboard.press('Escape');await p.waitForFunction(()=>!window.claireState.dialogOpen);
  check('Closing restores trigger focus',await p.locator('.nav-entry[data-entry="0"]').evaluate(el=>el===document.activeElement));
  // Last choice wins during a running swap.
  await p.locator('.nav-entry[data-entry="1"]').click();await p.waitForFunction(()=>window.claireState.busy);
  await p.locator('.nav-entry[data-entry="2"]').click();await p.waitForFunction(()=>window.claireState.dialogOpen,{},{timeout:15000});
  check('Queued quick selection resolves to last target',(await state(p)).active===2);await close(p);
  await p.emulateMedia({reducedMotion:'reduce'});await p.locator('.nav-entry[data-entry="1"]').click();await p.waitForFunction(()=>window.claireState.dialogOpen);
  check('Reduced motion switches without flight',(await state(p)).active===1&&!(await state(p)).busy);await close(p);
  await p.locator('.nav-entry[data-entry="2"]').hover();await p.waitForTimeout(100);
  check('Reduced motion has no spring movement',(await state(p)).cardProgress.every(v=>v===0));
  check('Desktop has no horizontal overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await p.locator('#sound-toggle').click();await p.waitForFunction(()=>!document.getElementById('audio').paused);
  check('Built-in playlist starts with ThankuNext',await p.locator('#audio').evaluate(a=>decodeURIComponent(a.src).endsWith('/music/ThankuNext.MP3')));
  await p.locator('#sound-toggle').click();check('Audio pause control works',await p.locator('#audio').evaluate(a=>a.paused));
  await p.locator('#sound-toggle').click();await p.waitForFunction(()=>!document.getElementById('audio').paused);
  for(const file of ['carelseewhisper.MP3','creepinuponyou.MP3','Mr.Broken_Heart.MP3','ThankuNext.MP3']){
    await p.locator('#change-track').click();await p.waitForFunction(file=>{const a=document.getElementById('audio');return !a.paused&&decodeURIComponent(a.src).endsWith('/music/'+file);},file);
    check('Next track plays '+file,true);
  }
  await p.waitForFunction(()=>Number.isFinite(document.getElementById('audio').duration));
  await p.locator('#audio').evaluate(a=>{a.currentTime=a.duration-.15;});
  await p.waitForFunction(()=>decodeURIComponent(document.getElementById('audio').src).endsWith('/music/carelseewhisper.MP3')&&!document.getElementById('audio').paused);
  check('Track ending automatically advances playlist',true);
  check('No file picker remains',await p.locator('#audio-file').count()===0);
  await context.close();
  const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
  const m=await mobile.newPage();m.on('pageerror',e=>report.errors.push(e.message));await m.goto(base);await settle(m);await shot(m,'mobile');
  check('Mobile opens directly at hero',!(await state(m)).intro);
  check('Mobile has no horizontal overflow',await m.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await m.locator('.nav-entry[data-entry="2"]').tap();await m.waitForFunction(()=>window.claireState.dialogOpen);await shot(m,'mobile-panel');
  check('Touch selects in one tap',(await state(m)).active===2);await close(m);await mobile.close();
  const fallback=await browser.newContext({viewport:{width:1280,height:800}});await fallback.route('**/assets/claire-v3.glb',route=>route.abort());
  const f=await fallback.newPage();await f.goto(base);await f.waitForFunction(()=>document.getElementById('stage').classList.contains('failed'));
  await f.locator('.nav-entry[data-entry="0"]').click();await f.waitForFunction(()=>document.getElementById('content-dialog').open);
  await f.locator('.reveal-about').click();
  check('Failed model still permits content navigation',await f.locator('#panel-title').innerText()==='第一章 · 关于我');await fallback.close();
  const offline=await browser.newContext({viewport:{width:1440,height:960}});const o=await offline.newPage();const remote=[];
  o.on('request',request=>{if(/^https?:/.test(request.url()))remote.push(request.url());});o.on('pageerror',e=>report.errors.push(e.message));
  await o.goto(require('node:url').pathToFileURL(path.join(root,'claire.html')).href);await settle(o);
  check('Standalone HTML loads from file without a server',(await state(o)).discCount===3);
  check('Standalone makes no external requests',remote.length===0);await shot(o,'standalone');
  await o.locator('#sound-toggle').click();await o.waitForFunction(()=>!document.getElementById('audio').paused);
  check('Standalone plays embedded music',await o.locator('#audio').evaluate(a=>a.src.startsWith('data:audio/mpeg;')));
  await o.locator('.nav-entry[data-entry="0"]').click();await o.waitForFunction(()=>window.claireState.dialogOpen);await shot(o,'standalone-panel');await offline.close();
  const early=await browser.newContext({viewport:{width:1280,height:800}});
  await early.route('**/assets/claire-v3.glb',async route=>{await new Promise(resolve=>setTimeout(resolve,1200));await route.continue();});
  const e=await early.newPage();e.on('pageerror',error=>report.errors.push(error.message));await e.goto(base);
  await e.locator('.nav-entry[data-entry="1"]').click();await e.waitForFunction(()=>window.claireState.dialogOpen);await settle(e);
  check('Navigation during loading remains functional',(await state(e)).active===1&&(await state(e)).dialogOpen);
  const earlyState=await state(e);
  check('Early selection puts only selected disc in player',earlyState.discPositions[1].every((value,i)=>Math.abs(value-baseline[i])<1e-6)&&earlyState.discPositions[0].some((value,i)=>Math.abs(value-baseline[i])>.5));
  await early.close();
  check('No browser JavaScript errors',report.errors.length===0);
  report.passed=true;
 }finally{await browser.close();fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));}
})().catch(error=>{console.error(error);process.exitCode=1;});
