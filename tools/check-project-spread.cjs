const {chromium}=require('@playwright/test');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const out=path.resolve(__dirname,'../reviews/project-spread-2026-10-07');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 const checks=[],errors=[];
 try {
  for(const [name,width,offline,reduce] of [['desktop',1440,false,false],['mobile',390,false,false],['reduced',1440,false,true],['offline',1440,true,true]]) {
   const p=await browser.newPage({viewport:{width,height:960},reducedMotion:reduce?'reduce':'no-preference',hasTouch:width===390,isMobile:width===390});p.on('pageerror',e=>errors.push(e.message));
   await p.goto(offline?'file:///'+path.resolve(__dirname,'../claire.html').replace(/\\/g,'/'):(process.env.CLAIRE_BASE_URL||'http://127.0.0.1:4198'));
   await p.locator('.nav-entry[data-entry="1"]').press('Enter');await p.waitForSelector('.project-cover');
   assert.deepEqual(await p.locator('.project-cover strong').allTextContents(),['成长回路','my test-rag','番茄专注组件']);
   await p.locator('.project-cover svg image').evaluateAll(imgs=>Promise.all(imgs.map(img=>new Promise((res,rej)=>{const test=new Image();test.onload=res;test.onerror=rej;test.src=img.getAttribute('href');}))));
   const before=await p.locator('.project-cover').evaluateAll(els=>els.map(e=>e.style.transform));
   if(width!==390) {
    await p.locator('.project-cover').nth(1).hover();await p.waitForTimeout(240);
    assert.equal(await p.locator('.project-preview h3').textContent(),'my test-rag');
    const after=await p.locator('.project-cover').evaluateAll(els=>els.map(e=>e.style.transform));
    assert(reduce?before.every((v,i)=>v===after[i]):before.every((v,i)=>v!==after[i]));
    await p.screenshot({path:path.join(out,name+'-hover.png')});
    await p.mouse.move(20,20);await p.waitForTimeout(500);
    assert.equal(await p.locator('.project-preview h3').textContent(),'成长回路');
   }
   for(let i=0;i<3;i++) {
    await p.locator(`[data-preview="${i}"]`).click();assert.equal(await p.locator('.project-preview h3').textContent(),['成长回路','my test-rag','番茄专注组件'][i]);
    await p.locator('.project-preview .project-cta').click();assert.equal(await p.evaluate(()=>document.activeElement.id),['growth-loop','test-rag','pomodoro'][i]);
    assert.equal(await p.locator('.project-detail').nth(i).locator('dt').count(),4);
    await p.locator('.project-detail').nth(i).locator('a[href="#project-cards"]').click();
   }
   await p.locator('.project-cover').nth(0).focus();assert.equal(await p.locator('.project-preview h3').textContent(),'成长回路');
   assert(await p.locator('#content-dialog').evaluate(e=>e.scrollWidth<=e.clientWidth+1));
   await p.locator('#content-dialog').evaluate(e=>e.scrollTop=0);await p.screenshot({path:path.join(out,name+'.png')});
   await p.keyboard.press('Escape');await p.waitForTimeout(200);await p.locator('.nav-entry[data-entry="1"]').press('Enter');await p.waitForSelector('.project-cover');assert.equal(await p.locator('.project-cover').count(),3);
   checks.push(name+': fan, preview, navigation, focus, images, overflow, reopen');await p.close();
  }
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:true,checks,errors},null,2));console.log(checks.join('\n'));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
