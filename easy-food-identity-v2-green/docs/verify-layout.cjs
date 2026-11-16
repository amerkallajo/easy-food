// Optional visual-layout check. Run with an installed Playwright package path as argv[2].
const { chromium } = require(process.argv[2] || 'playwright');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage();
  const root = path.resolve(__dirname, '..');
  const results = [];
  for (const [file, width, height] of [
    ['menu.html', 900, 1273],
    ['social-square.html', 1080, 1080],
    ['social-story.html', 1080, 1920],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto(pathToFileURL(path.join(root, 'templates', file)).href);
    await page.evaluate(() => document.fonts.ready);
    const result = await page.evaluate(() => {
      const canvas = document.querySelector('.canvas').getBoundingClientRect();
      const rows = [...document.querySelector('.canvas').children]
        .filter(el => !el.classList.contains('motif'))
        .map(el => {
          const r = el.getBoundingClientRect();
          return { element: el.className || el.tagName, top: +r.top.toFixed(2), bottom: +r.bottom.toFixed(2), left: +r.left.toFixed(2), right: +r.right.toFixed(2) };
        });
      return {
        canvas: { width: canvas.width, height: canvas.height },
        missingImages: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src),
        rows,
        overflow: rows.filter(r => r.top < canvas.top - 1 || r.bottom > canvas.bottom + 1 || r.left < canvas.left - 1 || r.right > canvas.right + 1),
      };
    });
    results.push({ file, ...result });
  }
  await browser.close();
  console.log(JSON.stringify(results, null, 2));
  if (results.some(r => r.missingImages.length || r.overflow.length)) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
