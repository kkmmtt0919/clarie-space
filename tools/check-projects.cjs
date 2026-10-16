const { chromium } = require('@playwright/test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const out = path.resolve(__dirname, '../reviews/project-cards-2026-10-06');
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true, args: ['--enable-unsafe-swiftshader'] });
  const checks = [], errors = [];
  try {
    for (const [name, width, offline] of [['desktop',1440,false],['mobile',390,false],['offline',1440,true]]) {
      const page = await browser.newPage({ viewport: { width, height: 960 }, reducedMotion: 'reduce' });
      page.on('pageerror', e => errors.push(e.message));
      await page.goto(offline ? 'file:///' + path.resolve(__dirname, '../claire.html').replace(/\\/g, '/') : (process.env.CLAIRE_BASE_URL || 'http://127.0.0.1:4197'));
      await page.locator('.nav-entry[data-entry="1"]').focus();
      await page.keyboard.press('Enter');
      await page.waitForSelector('.project-card');
      assert.deepEqual(await page.locator('.project-card h3').allTextContents(), ['成长回路','my test-rag','番茄专注组件']);
      assert.equal(await page.locator('.project-kind').count(), 3);
      for (const id of ['growth-loop','test-rag','pomodoro']) {
        await page.locator(`.project-card[href="#${id}"]`).click();
        assert.equal(await page.evaluate(() => document.activeElement.id), id);
        assert.equal(await page.locator(`#${id} dt`).count(), 4);
        await page.locator(`#${id} a[href="#project-cards"]`).click();
      }
      assert(await page.locator('#content-dialog').evaluate(el => el.scrollWidth <= el.clientWidth + 1));
      await page.locator('#growth-loop img').evaluateAll(imgs => Promise.all(imgs.map(img => img.decode())));
      await page.screenshot({ path: path.join(out, name + '.png') });
      await page.keyboard.press('Escape');
      await page.locator('.nav-entry[data-entry="1"]').press('Enter');
      await page.waitForSelector('.project-card');
      assert.equal(await page.locator('.project-card').count(), 3);
      checks.push(name + ': order, labels, detail links, keyboard focus, images, overflow, reopen');
      await page.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({ passed: true, checks, errors },null,2));
    console.log(checks.join('\n'));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
