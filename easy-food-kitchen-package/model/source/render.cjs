// Renders the PNG views from the offline viewer and rasterises the SVG plans.
// Run:  node render.cjs     (after build_model.py and bundling viewer.src.js)
const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const pkg = path.resolve(__dirname, '../..');
const viewer = pathToFileURL(path.join(pkg, 'model/viewer/viewer.html')).href;
const out = path.join(pkg, 'renders');
fs.mkdirSync(out, { recursive: true });

const shots = [
  ['A', 'cutaway', '01-A-cutaway-3d.png'],
  ['A', 'top', '02-A-top-down-cutaway.png'],
  ['A', 'interior_front', '03-A-interior-from-door.png'],
  ['A', 'interior_back', '04-A-interior-from-back.png'],
  ['A', 'exterior', '05-A-exterior-signage-order-collect.png'],
  ['A', 'flow', '06-A-staff-and-food-flow.png'],
  ['B', 'cutaway', '07-B-cutaway-3d.png'],
  ['B', 'flow', '08-B-staff-and-food-flow.png'],
  ['A', 'equipment', '09-A-equipment-detail.png'],
  ['A', 'hood_detail', '10-A-hood-filters-detail.png'],
];
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--allow-file-access-from-files'] });
  const only = process.argv[2];
  for (const lang of ['ar', 'en']) for (const [m, view, file] of shots) {
    if (only && !file.includes(only)) continue;
    fs.mkdirSync(path.join(out, lang), { recursive: true });
    const page = await browser.newPage({ viewport: { width: 1920, height: 1200 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error' || msg.type() === 'warning') errors.push(msg.text()); });
    page.on('pageerror', err => errors.push(err.message));
    page.on('request', req => { if (/^https?:/.test(req.url())) errors.push('Unexpected network dependency: ' + req.url()); });
    await page.goto(`${viewer}?m=${m}&view=${view}&shot=1&lang=${lang}`);
    await page.waitForFunction('window.__ready === true', null, { timeout: 60000 });
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(out, lang, file) });
    if (errors.length) throw new Error(`${lang}/${file}: ${errors.join('; ')}`);
    await page.close();
    console.log('render', lang, file);
  }
  if (!only) for (const m of ['A', 'B']) {
    const svg = path.join(pkg, 'plans', `layout-${m}.svg`);
    const txt = fs.readFileSync(svg, 'utf8');
    const [, w, h] = txt.match(/width="(\d+)" height="(\d+)"/);
    const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1.5 });
    await page.goto(pathToFileURL(svg).href);
    await page.screenshot({ path: path.join(pkg, 'plans', `layout-${m}.png`) });
    await page.close();
    console.log('plan', m);
  }
  if (!only) fs.copyFileSync(path.join(out, 'en', '06-A-staff-and-food-flow.png'), path.join(pkg, 'plans', 'flow-A.png'));
  await browser.close();
})().catch(err => { console.error(err); process.exit(1); });
