// Exercise the delivered viewer in a fresh browser profile.
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium, webkit, devices } = require('playwright');

const site = process.argv[2];
const viewerPath = 'easy-food-kitchen-package/model/viewer/viewer.html';
const offlineUrl = pathToFileURL(path.resolve(__dirname, '../viewer/viewer-offline.html'));
const chrome = process.platform === 'win32' ? { channel: 'chrome' } : {};
const graphics = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const ready = page => page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });

async function openSection(page, section) {
  if (await page.locator('#ui').isHidden()) await page.locator('#b-menu').click();
  const details = page.locator('#' + section + '-group');
  if (await details.getAttribute('open') === null) await details.locator('summary').click();
}

async function verifyOffline(browser) {
  const context = await browser.newContext({ viewport: { width: 1000, height: 800 }, offline: true });
  try {
    const page = await context.newPage();
    const errors = [], network = [];
    page.on('pageerror', err => errors.push(err.message));
    page.on('console', msg => { if (['error', 'warning'].includes(msg.type())) errors.push(msg.text()); });
    page.on('request', req => { if (/^https?:/.test(req.url())) network.push(req.url()); });

    await page.goto(offlineUrl.href + '?lang=en');
    for (const [index, variant] of ['A', 'B', 'A'].entries()) {
      if (index > 0) {
        await openSection(page, 'settings');
        await page.locator('#b-layout').click();
      }
      await ready(page);
      assert.match(await page.locator('#title').textContent(), new RegExp('Layout ' + variant));
      await openSection(page, 'view');
      for (const view of ['cutaway', 'top', 'interior_front', 'interior_back', 'exterior', 'flow', 'equipment', 'hood_detail', 'wc']) {
        const choice = page.locator('#views button[data-v="' + view + '"]');
        await choice.click();
        assert.equal(await choice.getAttribute('class'), 'on');
        const canvas = await page.locator('#stage canvas').evaluate(c => ({ width: c.width, height: c.height }));
        assert(canvas.width > 0 && canvas.height > 0);
        if (view === 'cutaway') {
          const labels = await page.locator('#labels').textContent();
          assert(labels.includes('E03') && labels.includes('E08') && labels.includes('E13') && labels.includes('WC'));
        }
      }
      console.log(variant + ': all nine offline camera views available');
    }
    await openSection(page, 'settings');
    await page.locator('#b-lang').click();
    assert.equal(await page.locator('html').getAttribute('lang'), 'ar');
    await openSection(page, 'view');
    await page.locator('#views button[data-v="cutaway"]').click();
    assert.match(await page.locator('#labels').textContent(), /برّاد/);
    await openSection(page, 'layer');
    const layer = page.locator('#layers button[data-l="people_in"]');
    await layer.click();
    assert.equal(await layer.getAttribute('class'), 'on');
    await layer.click();
    assert.equal(await layer.getAttribute('class'), '');
    await openSection(page, 'settings');
    await page.locator('#b-labels').click();
    assert(await page.locator('#labels').isHidden());

    await page.setViewportSize({ width: 390, height: 844 });
    await openSection(page, 'view');
    await page.locator('#views button[data-v="exterior"]').click();
    assert(await page.locator('#ui').isHidden());
    assert(await page.evaluate(() => document.documentElement.scrollWidth === innerWidth));
    await openSection(page, 'settings');
    await page.locator('#b-lang').click();
    assert.equal(await page.locator('html').getAttribute('lang'), 'en');
    assert.deepEqual(network, [], 'Single-file viewer must have no network dependencies');
    assert.deepEqual(errors, [], 'Offline viewer console must remain clean');
    console.log('Offline layout switching, Arabic and English, layers, labels, and mobile controls passed');
  } finally {
    await context.close();
  }
}

async function verifyOnline(browser) {
  const context = await browser.newContext(devices['Pixel 7']);
  try {
    const page = await context.newPage();
    const requested = [], pageErrors = [], logs = [];
    page.on('request', req => { if (req.url().endsWith('.glb')) requested.push(path.basename(req.url())); });
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('console', msg => { if (['error', 'warning'].includes(msg.type())) logs.push(msg.text()); });
    await page.goto(site, { waitUntil: 'domcontentloaded' });
    await page.locator('.header-cta:visible, .hero a[href$="viewer.html"]:visible').first().click();
    await ready(page);
    assert.deepEqual(requested, ['easy-food-kitchen-A.glb']);
    assert.deepEqual(logs, []);
    assert.match(await page.locator('#title').textContent(), /المخطط A/);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await ready(page);
    await openSection(page, 'settings');
    await page.locator('#b-lang').click();
    let releaseDownload;
    const heldDownload = new Promise(resolve => { releaseDownload = resolve; });
    await page.route('**/easy-food-kitchen-B.glb', async route => {
      await heldDownload;
      await route.fulfill({ status: 503 });
    });
    try {
      await page.locator('#b-layout').click();
      assert.match(await page.locator('#status').textContent(), /Downloading/);
      assert(await page.locator('#b-retry').isHidden(), 'Retry must stay hidden during downloading');
    } finally {
      releaseDownload();
    }
    await page.locator('#b-retry').waitFor({ state: 'visible' });
    assert.match(await page.locator('#status').textContent(), /could not load/);
    assert.match(await page.locator('#preview-link').getAttribute('href'), /layout-B\.png$/);
    await page.waitForFunction(() => document.querySelector('#preview').naturalWidth > 0);
    assert(await page.locator('#offline-link').isVisible());
    await page.locator('#b-resume').click();
    await ready(page);
    assert.match(await page.locator('#title').textContent(), /Layout A/);

    await openSection(page, 'settings');
    await page.locator('#b-layout').click();
    await page.locator('#b-retry').waitFor({ state: 'visible' });
    await page.unroute('**/easy-food-kitchen-B.glb');
    await page.locator('#b-retry').click();
    await ready(page);
    assert.match(await page.locator('#title').textContent(), /Layout B/);


    await page.goto(new URL(viewerPath + '?m=invalid&lang=invalid&view=__proto__', site).href);
    await ready(page);
    assert.equal(await page.locator('html').getAttribute('lang'), 'ar');
    assert.match(await page.locator('#title').textContent(), /المخطط A/);
    assert.deepEqual(pageErrors, []);
    // The HTTP diagnostic can arrive after the fallback has already become visible.
    assert.deepEqual(logs.filter(log => !/status of 503|model failed to load Error: Model download returned HTTP 503/.test(log)), []);
    console.log('Online mobile entry, lazy models, failed switch, retry, and invalid links passed');
  } finally {
    await context.close();
  }
}

// WebKit can present a blank canvas after rendering stops unless the last frame is retained.
async function verifyIdleWebKit() {
  const browser = await webkit.launch();
  try {
    const page = await browser.newPage(devices['iPhone 13']);
    await page.goto(new URL(viewerPath + '?m=B&lang=en', site).href);
    await ready(page);
    await page.waitForFunction(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true)))));
    const colors = await page.locator('#stage canvas').evaluate(canvas => {
      const sample = document.createElement('canvas');
      sample.width = sample.height = 32;
      const ctx = sample.getContext('2d');
      ctx.drawImage(canvas, 0, 0, 32, 32);
      const pixels = ctx.getImageData(0, 0, 32, 32).data;
      const colors = new Set();
      for (let offset = 0; offset < pixels.length; offset += 4) {
        colors.add(pixels.slice(offset, offset + 4).join(','));
      }
      return colors.size;
    });
    assert(colors > 20, 'The idle WebKit canvas must retain the kitchen scene');
    console.log('iPhone WebKit: rendered layout remains visible when idle');
  } finally {
    await browser.close();
  }
}

async function verifyWithoutWebGL() {
  const browser = await chromium.launch({ ...chrome, args: ['--disable-webgl'] });
  try {
    const page = await browser.newPage(devices['Pixel 7']);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(new URL(viewerPath + '?m=B&lang=en', site).href);
    await page.locator('#preview-link').waitFor({ state: 'visible' });
    assert.match(await page.locator('#status').textContent(), /3D rendering is unavailable/);
    assert.match(await page.locator('#preview-link').getAttribute('href'), /layout-B\.png$/);
    assert.match(await page.locator('#offline-link').getAttribute('href'), /viewer-offline\.html$/);
    assert(await page.locator('#b-menu').isHidden());
    assert.deepEqual(errors, []);
    console.log('WebGL disabled: correct layout preview and offline download available');
  } finally {
    await browser.close();
  }
}

(async () => {
  const browser = await chromium.launch({ ...chrome, args: graphics });
  try {
    if (!process.argv.includes('--online-only')) await verifyOffline(browser);
    if (site) await verifyOnline(browser);
  } finally {
    await browser.close();
  }
  if (site) {
    await verifyWithoutWebGL();
    if (process.argv.includes('--webkit')) await verifyIdleWebKit();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
