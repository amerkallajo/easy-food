// Generates signage textures (PNG) used by build_model.py.
// Run:  node make_textures.cjs      (needs the global Playwright package + Chrome)
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const brand = path.resolve(__dirname, '../../../easy-food-identity-v2-green/assets');
const out = path.join(__dirname, 'textures');
fs.mkdirSync(out, { recursive: true });
const font = (f) => pathToFileURL(path.join(brand, 'fonts', f)).href;
const logo = fs.readFileSync(path.join(brand, 'logos', 'logo-horizontal-cream.svg'), 'utf8');
const logoForest = fs.readFileSync(path.join(brand, 'logos', 'logo-horizontal-forest.svg'), 'utf8');

const css = `
@font-face{font-family:Cairo;src:url('${font('Cairo-Variable.ttf')}');font-weight:200 1000}
@font-face{font-family:Manrope;src:url('${font('Manrope-Variable.ttf')}');font-weight:200 800}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Manrope,Cairo,sans-serif;overflow:hidden}
.ar{font-family:Cairo,sans-serif;direction:rtl}
`;
const slashes = (c, w) => `<svg viewBox="0 0 120 74" width="${w}"><g stroke="${c}" stroke-width="17" stroke-linecap="round"><path d="M9 64 L36 10"/><path d="M45 64 L72 10"/><path d="M81 64 L108 10"/></g></svg>`;

const pages = {
  'sign_fascia': { w: 1800, h: 480, html: `
    <div style="width:1800px;height:480px;background:#146B45;display:flex;align-items:center;justify-content:space-between;padding:0 70px">
      <div style="width:900px;margin-left:-40px">${logo.replace('width="1060" height="400"', 'width="900" height="340"')}</div>
      <div class="ar" style="text-align:right;color:#FFF8EA">
        <div style="font-size:170px;font-weight:800;line-height:1.15">إيزي فود</div>
        <div style="font-size:54px;font-weight:600;color:#DDF45B;margin-top:4px">أكلك الصحي، بكل بساطة</div>
      </div>
    </div>` },
  'label_order': { w: 900, h: 220, html: `
    <div style="width:900px;height:220px;background:#DDF45B;color:#17251C;display:flex;align-items:center;justify-content:center;gap:36px">
      <div style="font-size:150px;font-weight:800;color:#146B45">1</div>
      <div><div class="ar" style="font-size:78px;font-weight:800;line-height:1.1">اطلب وادفع</div>
      <div style="font-size:50px;font-weight:800;letter-spacing:2px">ORDER &amp; PAY</div></div>
    </div>` },
  'label_collect': { w: 900, h: 220, html: `
    <div style="width:900px;height:220px;background:#146B45;color:#FFF8EA;display:flex;align-items:center;justify-content:center;gap:36px">
      <div style="font-size:150px;font-weight:800;color:#DDF45B">2</div>
      <div><div class="ar" style="font-size:78px;font-weight:800;line-height:1.1">استلم طلبك</div>
      <div style="font-size:50px;font-weight:800;letter-spacing:2px">COLLECT</div></div>
    </div>` },
  'apron': { w: 1500, h: 900, html: `
    <div style="width:1500px;height:900px;background:#146B45;position:relative;overflow:hidden">
      <div style="position:absolute;right:-60px;bottom:-140px;opacity:.95">${slashes('#DDF45B', 900)}</div>
      <div style="position:absolute;left:70px;top:70px;color:#FFF8EA">
        <div style="font-size:92px;font-weight:800">Eat smart. Live easy.</div>
        <div class="ar" style="font-size:80px;font-weight:700;color:#DDF45B;text-align:left;direction:rtl;width:900px;text-align:right">أكلك الصحي، بكل بساطة</div>
      </div>
    </div>` },
  'menu_board': { w: 700, h: 1100, html: `
    <div style="width:700px;height:1100px;background:#FFF8EA;color:#17251C;padding:44px 46px">
      <div style="width:330px;margin-left:-22px">${logoForest.replace('width="1060" height="400"', 'width="330" height="125"')}</div>
      <div style="height:6px;background:#DDF45B;margin:10px 0 26px"></div>
      ${[['Easy Rice', 'رز + بروتين + خضار', 'Chicken / Beef'], ['Easy Wrap', 'لفّة مشوية', 'Chicken / Beef'], ['Easy Salad', 'سلطة + بروتين', 'Chicken / Beef / Veg'], ['Easy Bites', 'كرات بروتين · براوني', 'Protein balls · Brownie']]
        .map(r => `<div style="margin-bottom:34px"><div style="display:flex;justify-content:space-between;align-items:baseline">
          <div style="font-size:60px;font-weight:800;color:#146B45">${r[0]}</div></div>
          <div class="ar" style="font-size:40px;font-weight:700">${r[1]}</div>
          <div style="font-size:30px;font-weight:600;opacity:.7">${r[2]}</div></div>`).join('')}
      <div style="font-size:26px;font-weight:700;color:#146B45;margin-top:10px">Prices &amp; calories: set after recipe costing</div>
    </div>` },
  'blade': { w: 500, h: 500, html: `
    <div style="width:500px;height:500px;background:#DDF45B;display:flex;align-items:center;justify-content:center">${slashes('#146B45', 360)}</div>` },
};

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  for (const [name, p] of Object.entries(pages)) {
    const page = await browser.newPage({ viewport: { width: p.w, height: p.h }, deviceScaleFactor: 1 });
    await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body>${p.html}</body></html>`);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(250);
    await page.screenshot({ path: path.join(out, name + '.png') });
    await page.close();
    console.log('texture', name);
  }
  await browser.close();
})();
