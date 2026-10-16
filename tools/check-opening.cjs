const {chromium}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--enable-unsafe-swiftshader','--mute-audio']});
 try{
  const page=await browser.newPage({viewport:{width:1366,height:768}});
  await page.goto(process.env.CLAIRE_BASE_URL || 'http://127.0.0.1:4193');
  await page.waitForFunction(()=>window.claireState?.ready&&window.claireState.intro);
  await page.waitForTimeout(250);
  await page.locator('#skip-opening').click();
  await page.waitForFunction(()=>!window.claireState.intro);
  const skipWorks=await page.evaluate(()=>window.claireState.cameraScale>11&&document.querySelector('.hero').classList.contains('ready'));
  await page.locator('#replay-opening').click();
  await page.waitForFunction(()=>window.claireState.intro);
  const start=performance.now();
  await page.waitForFunction(()=>!window.claireState.intro);
  const openingMs=performance.now()-start;
  await page.locator('.nav-entry').first().click();
  await page.waitForFunction(()=>window.claireState.dialogOpen);
  await page.locator('#close-panel').click();
  await page.waitForFunction(()=>!window.claireState.dialogOpen);
  const closeDoesNotReplay=await page.evaluate(()=>!window.claireState.intro);
  const report={passed:openingMs>4200&&openingMs<5100&&skipWorks&&closeDoesNotReplay,openingMs,skipWorks,closeDoesNotReplay};
  fs.writeFileSync(path.join(__dirname,'..','checks','opening-report.json'),JSON.stringify(report,null,2));
  console.log(report);if(!report.passed)process.exitCode=1;
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
