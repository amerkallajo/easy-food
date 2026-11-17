// Exercise the delivered file offline using a separate, temporary Chrome profile.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--allow-file-access-from-files'] });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, offline: true });
    const page = await context.newPage();
    const errors = [], network = [];
    page.on('pageerror', err => errors.push(err.message));
    page.on('console', msg => { if (['error', 'warning'].includes(msg.type())) errors.push(msg.text()); });
    page.on('request', req => { if (/^https?:/.test(req.url())) network.push(req.url()); });
    const url = pathToFileURL(path.resolve(__dirname, '../viewer/viewer.html')).href;
    await page.goto(url + '?lang=en');
    await page.waitForFunction(() => window.__ready === true);
    // The controls sit behind a menu button and collapsible groups; open them so their buttons can be exercised.
    const openMenus = async () => {
      if (await page.locator('#ui').isHidden()) await page.locator('#b-menu').click();
      await page.evaluate(() => document.querySelectorAll('#ui details').forEach(d => { d.open = true; }));
    };
    await openMenus();
    for (const variant of ['A', 'B', 'A']) {
      if (variant !== 'A' || (await page.locator('#title').textContent()).includes('Layout B')) {
        await page.locator('#b-layout').click();
        await page.waitForFunction(() => window.__ready === true);
        await openMenus();
      }
      assert.match(await page.locator('#title').textContent(), new RegExp('Layout ' + variant));
      for (const view of ['cutaway', 'top', 'interior_front', 'interior_back', 'exterior', 'flow', 'equipment', 'hood_detail', 'wc']) {
        await page.locator(`#views button[data-v="${view}"]`).click();
        assert.equal(await page.locator(`#views button[data-v="${view}"]`).getAttribute('class'), 'on');
        const canvas = await page.locator('canvas').first().evaluate(c => ({ width: c.width, height: c.height }));
        assert(canvas.width > 0 && canvas.height > 0);
        if (view === 'cutaway') {
          const labels = await page.locator('#labels').textContent();
          assert(labels.includes('E03') && labels.includes('E08') && labels.includes('E13'));
          assert(labels.includes('WC'));
        }
        if (variant === 'B' && ['equipment', 'hood_detail'].includes(view)) {
          const review = path.resolve(__dirname, '../../renders/review');
          fs.mkdirSync(review, { recursive: true });
          await page.screenshot({ path: path.join(review, `B-${view}.png`) });
        }
      }
      console.log(`${variant}: nine camera views, retained WC and equipment labels OK`);
    }
    await page.locator('#b-lang').click();
    assert.equal(await page.locator('html').getAttribute('lang'), 'ar');
    assert.match(await page.locator('#title').textContent(), /إيزي فود/);
    await page.locator('#views button[data-v="cutaway"]').click();
    assert.match(await page.locator('#labels').textContent(), /برّاد/);
    const layer = page.locator('#layers button[data-l="people_in"]');
    await layer.click(); assert.equal(await layer.getAttribute('class'), 'on');
    await layer.click(); assert.equal(await layer.getAttribute('class'), '');
    await page.setViewportSize({ width: 390, height: 844 });
    await openMenus();
    await page.locator('#views button[data-v="exterior"]').click();
    await openMenus();   // choosing a view may close the panel on a phone-sized screen
    assert(await page.locator('#b-lang').isVisible());
    const mobile = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: innerWidth }));
    assert.equal(mobile.width, mobile.viewport);
    await openMenus();
    await page.locator('#b-lang').click();
    assert.equal(await page.locator('html').getAttribute('lang'), 'en');
    assert.deepEqual(network, [], 'Single-file viewer must have no network dependencies');
    assert.deepEqual(errors, [], 'Viewer console must remain clean');
    console.log('Arabic/English, layout switching, layer toggles, mobile viewport, zero network dependencies and clean console OK');
  } finally { await browser.close(); }
})().catch(err => { console.error(err); process.exitCode = 1; });
