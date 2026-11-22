// Shared by the online and self-contained offline kitchen viewers.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { RectAreaLightUniformsLib } from 'three/examples/jsm/lights/RectAreaLightUniformsLib.js';

const q = new URLSearchParams(location.search);
let variant = q.get('m')?.toUpperCase() === 'B' ? 'B' : 'A';
let lang = q.get('lang')?.toLowerCase() === 'en' ? 'en' : 'ar';
const shot = q.get('shot') === '1';
const modelStore = window.EASYFOOD_MODELS || window.EASYFOOD_META;
const site = modelStore.A.site;
const CX = site.W / 2;
// model coords: x across, y up, z = -depth (street is +z, back wall is z = -5.06)
const P = (x, depth, up) => new THREE.Vector3(x, up, -depth);

const VIEWS = {
  cutaway: { en: 'Cutaway 3D - roof, right wall and shopfront removed', ar: 'مقطع ثلاثي الأبعاد - بدون السقف والجدار الأيمن والواجهة', btn: 'مقطع 3D',
    pos: P(7.2, -3.4, 6.4), tgt: P(1.3, 2.5, 0.6), fov: 34,
    hide: ['ceiling', 'wall_right', 'front', 'people_out', 'people_in', 'flow', 'context', 'site', 'highshelf', 'wc_upper'], labels: 'equip' },
  top: { en: 'Top-down cutaway (street at right)', ar: 'مسقط علوي (الشارع إلى اليمين)', btn: 'مسقط علوي',
    ortho: 2.05, pos: P(CX, 2.05, 12), tgt: P(CX, 2.05, 0), up: [1, 0, 0],
    hide: ['ceiling', 'people_out', 'flow', 'context', 'mep', 'highshelf', 'shelves', 'wc_upper'], labels: 'codes' },
  interior_front: { en: 'Interior - from the staff door looking to the back', ar: 'من الداخل - من باب الموظفين باتجاه الخلف', btn: 'داخلي من الباب',
    pos: P(1.2, 0.22, 1.66), tgt: P(1.65, 4.8, 0.95), fov: 80,
    hide: ['people_out', 'flow', 'people_in'], labels: 'none', interior: true },
  interior_back: { en: 'Interior - from the back prep area looking to the service window', ar: 'من الداخل - من منطقة التحضير باتجاه نافذة الخدمة', btn: 'داخلي من الخلف',
    pos: P(1.68, 4.30, 1.72), tgt: P(1.65, 0.0, 1.0), fov: 78,
    hide: ['flow', 'people_in'], labels: 'none', interior: true },
  exterior: { en: 'Exterior - signage, order and collect positions', ar: 'الواجهة - اللافتة ونافذتا الطلب والاستلام', btn: 'الواجهة',
    pos: P(-0.7, -6.8, 1.85), tgt: P(1.5, 0, 1.80), fov: 56,
    hide: ['flow', 'ceiling'], labels: 'ext', exterior: true },
  flow: { en: 'Staff movement and food flow', ar: 'حركة الموظفين ومسار الطعام', btn: 'مسار العمل',
    pos: P(4.6, -1.4, 9.8), tgt: P(1.35, 2.45, 0.3), fov: 34,
    hide: ['ceiling', 'wall_right', 'front', 'people_out', 'context', 'site', 'mep', 'highshelf', 'shelves', 'wc_upper'], labels: 'stations' },
  equipment: { en: 'Equipment detail - recessed doors, handles and worktop edges', ar: 'تفاصيل المعدات - الأبواب والمقابض وحواف الأسطح', btn: 'تفاصيل المعدات',
    pos: P(1.05, 0.95, 1.32), tgt: P(2.35, 2.35, 0.77), fov: 58,
    posB: P(1.05, 1.90, 1.32), tgtB: P(2.35, 3.15, 0.77),
    hide: ['people_out', 'people_in', 'flow', 'highshelf'], labels: 'none', interior: true },
  hood_detail: { en: 'Hood detail - baffle filters, rolled lip and duct joints', ar: 'تفاصيل الشفّاط - فلاتر الدهون والحافة ووصلات المجرى', btn: 'تفاصيل الشفّاط',
    pos: P(1.30, 2.20, 1.43), tgt: P(2.35, 3.70, 2.10), fov: 56,
    posB: P(1.15, 2.10, 1.40), tgtB: P(2.35, 0.90, 2.10),
    hide: ['people_out', 'people_in', 'flow', 'highshelf'], labels: 'none', interior: true },
  wc: { en: 'Retained rear-left WC - provisional size / accordion door', ar: 'الحمّام الخلفي اليساري - مقاس افتراضي وباب أكورديون', btn: 'الحمّام',
    pos: P(3.90, 1.50, 5.20), tgt: P(0.80, 4.10, 0.55), fov: 44,
    hide: ['ceiling', 'wall_right', 'front', 'people_out', 'people_in', 'context', 'site', 'flow', 'mep', 'highshelf', 'shelves', 'wc_upper'], labels: 'wc' },
};
const requestedView = q.get('view');
let viewName = Object.prototype.hasOwnProperty.call(VIEWS, requestedView) ? requestedView : 'cutaway';

const T = {
  note: { en: `Concept model: ${site.W.toFixed(2)} x ${site.D.toFixed(2)} m from the owner + photographs. Ceiling ${site.H.toFixed(2)} m, wall thickness, sidewalk depth and service points are ASSUMED. Rear-left WC retained; its size is provisional.`,
          ar: `نموذج تصوّري: ${site.W.toFixed(2)} × ${site.D.toFixed(2)} م حسب قياس المالك + الصور. السقف ${site.H.toFixed(2)} م وسماكة الجدران وعرض الرصيف ونقاط الخدمات افتراضية. الحمّام محفوظ ومقاسه افتراضي.` },
  raw: { en: 'Raw / incoming goods (steps 1-4)', ar: 'مواد نيئة / واردة (الخطوات 1-4)' },
  rte: { en: 'Cooked / ready-to-eat (steps 5-8)', ar: 'مطبوخ / جاهز للأكل (الخطوات 5-8)' },
  staff: { en: 'Staff positions at peak', ar: 'مواقع الموظفين وقت الذروة' },
  layout: { en: 'Layout', ar: 'المخطط' },
  view: { en: 'View', ar: 'المشهد' }, layers: { en: 'Layers', ar: 'الطبقات' },
  help: { en: 'Drag to orbit. Pinch or scroll to zoom. Drag with two fingers or the right mouse button to pan.',
          ar: 'اسحب للتدوير. قرّب أو باعد بإصبعين أو استخدم عجلة الفأرة للتكبير. اسحب بإصبعين أو بالزر الأيمن للتحريك.' },
  loading: { en: 'Downloading the 3D kitchen model…', ar: 'جار تنزيل نموذج المطبخ ثلاثي الأبعاد…' },
  slow: { en: 'Still downloading. This can take longer on a slow connection.', ar: 'التنزيل مستمر. قد يستغرق وقتاً أطول عند بطء الاتصال.' },
  preparing: { en: 'Preparing the 3D view…', ar: 'جار تجهيز العرض ثلاثي الأبعاد…' },
  failed: { en: 'The model could not load. Try again or open the kitchen plan.', ar: 'تعذّر تحميل النموذج. أعد المحاولة أو افتح مخطط المطبخ.' },
  webgl: { en: '3D rendering is unavailable in this browser. You can still open the kitchen plan.', ar: 'العرض ثلاثي الأبعاد غير متاح في هذا المتصفح. يمكنك فتح مخطط المطبخ.' },
  context: { en: 'The 3D view stopped. Reload it or open the kitchen plan.', ar: 'توقف العرض ثلاثي الأبعاد. أعد تحميله أو افتح مخطط المطبخ.' },
  local: { en: 'Open the self-contained viewer to use 3D offline.', ar: 'افتح نسخة العارض المخصصة للعمل دون اتصال لتشغيل النموذج.' },
  retry: { en: 'Try again', ar: 'أعد المحاولة' },
  reload: { en: 'Reload 3D viewer', ar: 'أعد تحميل العارض' },
  resume: { en: 'Keep current layout', ar: 'ابق على المخطط الحالي' },
  plan: { en: 'Open plan', ar: 'افتح المخطط' },
  offline: { en: 'Download offline viewer', ar: 'نزّل العارض دون اتصال' },
};
const EXT = [  // exterior annotations: x, depth, up, en, ar
  [1.42, -0.25, 2.25, '1 Order + pay window', '1 نافذة الطلب والدفع'],
  [2.27, -0.25, 2.25, '2 Collect window', '2 نافذة الاستلام'],
  [0.52, -0.25, 1.2, 'Staff door + deliveries', 'باب الموظفين والتوريد'],
  [2.35, -0.25, 0.35, 'LPG locker (opens outward)', 'خزانة الغاز (تُفتح للخارج)'],
  [2.38, -0.3, 2.45, 'Kitchen exhaust louvre', 'مخرج شفط المطبخ'],
  [0.5, -0.3, 2.45, 'Fresh-air intake', 'مدخل هواء نقي'],
  [3.25, -3.1, 1.75, 'Delivery riders wait here', 'انتظار عمال التوصيل'],
];

const mobileGraphics = !shot && matchMedia('(max-width: 800px), (pointer: coarse)').matches;
const scene = new THREE.Scene();
const inner = [], strips = [];
let renderer, hemi, sun;

function initGraphics() {
  // Keep the last frame visible when WebKit composites an idle canvas.
  renderer = new THREE.WebGLRenderer({ antialias: !mobileGraphics, preserveDrawingBuffer: true });
  renderer.setPixelRatio(shot ? 1 : Math.min(mobileGraphics ? 1 : 2, devicePixelRatio));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  document.getElementById('stage').appendChild(renderer.domElement);

  scene.background = new THREE.Color(0xf3f1ea);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const environment = new RoomEnvironment();
  // Long neutral reflection cards reveal curved steel edges without external HDR files.
  for (const [x, y, z, w, h, d] of [[-7, 5, 2, 0.1, 7, 1.5], [5, 6, -3, 0.1, 8, 2], [0, 9, 0, 5, 0.1, 2]]) {
    const card = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 5, 5) }));
    card.position.set(x, y, z); environment.add(card);
  }
  scene.environment = pmrem.fromScene(environment, 0.025).texture;
  environment.dispose(); pmrem.dispose();
  scene.environmentIntensity = 0.55;

  hemi = new THREE.HemisphereLight(0xdfeaf5, 0x8a8172, 0.9);
  scene.add(hemi);
  sun = new THREE.DirectionalLight(0xffeccf, 2.2);
  sun.castShadow = true;
  sun.shadow.mapSize.set(mobileGraphics ? 1024 : 2048, mobileGraphics ? 1024 : 2048);
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
  Object.assign(sun.shadow.camera, { left: -7, right: 7, top: 8, bottom: -8, near: 0.5, far: 40 });
  scene.add(sun); scene.add(sun.target);
  RectAreaLightUniformsLib.init();
  for (const depth of [1.15, 3.45]) {
    const light = new THREE.RectAreaLight(0xfff4e3, 0, 1.8, 0.24);
    light.position.copy(P(CX, depth, site.H - 0.08)); light.lookAt(P(CX, depth, 0)); scene.add(light); strips.push(light);
  }
  [[CX, 1.0], [CX, 2.6], [CX, 4.1]].forEach(([x, d]) => {
    const l = new THREE.PointLight(0xfff1dc, 0, 7, 1.6); l.position.copy(P(x, d, 2.75)); l.castShadow = !mobileGraphics && d > 2 && d < 3; l.shadow.mapSize.set(1024, 1024); l.shadow.bias = -0.002; scene.add(l); inner.push(l);
  });
  renderer.domElement.addEventListener('webglcontextlost', () => {
    graphicsAvailable = false;
    activeDownload?.abort();
    showFailure('context', variant, () => location.reload(), 'reload');
  });
}

// ---------- surface detail: procedural textures, world-space UVs, edge lines ----------
function canvasTex(size, draw, metres) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  t.userData.metres = metres;
  return t;
}
let seed = 27112026;
function random() { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; }
function noise(g, n, count, alpha, light) {
  for (let i = 0; i < count; i++) {
    g.fillStyle = `rgba(${light ? 255 : 0},${light ? 255 : 0},${light ? 255 : 0},${random() * alpha})`;
    g.fillRect(random() * n, random() * n, 1 + random() * 2, 1 + random() * 2);
  }
}
function tiles(cols, rows, base, grout, vary, offset) {
  return (g, n) => {
    g.fillStyle = grout; g.fillRect(0, 0, n, n);
    const w = n / cols, h = n / rows;
    for (let r = 0; r < rows; r++) for (let c = -1; c < cols; c++) {
      const v = Math.round((random() - 0.5) * vary);
      g.fillStyle = `rgb(${base[0] + v},${base[1] + v},${base[2] + v})`;
      const x = c * w + (offset && r % 2 ? w / 2 : 0);
      g.fillRect(x + 1.5, r * h + 1.5, w - 3, h - 3);
      g.fillStyle = 'rgba(255,255,255,0.10)'; g.fillRect(x + 1.5, r * h + 1.5, w - 3, 2);
    }
    noise(g, n, 1500, 0.04, false);
  };
}
const TEX = {
  tile: canvasTex(512, tiles(4, 8, [236, 240, 236], '#9aa39c', 8, true), 0.8),           // 20 x 10 cm wall tile
  floor: canvasTex(512, tiles(2, 2, [112, 118, 116], '#4c5150', 14, false), 0.6),        // 30 cm floor tile
  pave: canvasTex(512, tiles(4, 4, [176, 172, 162], '#8f8b82', 22, true), 0.8),          // 20 cm pavers
  stone: canvasTex(256, (g, n) => { g.fillStyle = '#3a3b40'; g.fillRect(0, 0, n, n); noise(g, n, 5000, 0.18, true); noise(g, n, 3000, 0.25, false); }, 0.5),
  asphalt: canvasTex(256, (g, n) => { g.fillStyle = '#3d3d40'; g.fillRect(0, 0, n, n); noise(g, n, 7000, 0.2, true); noise(g, n, 5000, 0.3, false); }, 0.6),
  carton: canvasTex(256, (g, n) => { g.fillStyle = '#b98d5c'; g.fillRect(0, 0, n, n); for (let y = 0; y < n; y += 4) { g.fillStyle = `rgba(90,60,30,${0.05 + random() * 0.06})`; g.fillRect(0, y, n, 1); } g.fillStyle = 'rgba(70,45,20,0.5)'; g.fillRect(0, n * 0.46, n, n * 0.08); }, 0.45),
  context: canvasTex(256, (g, n) => { g.fillStyle = '#cfcbc1'; g.fillRect(0, 0, n, n); noise(g, n, 4000, 0.07, false); g.fillStyle = 'rgba(0,0,0,0.10)'; g.fillRect(0, 0, n, 2); g.fillRect(0, n / 2, n, 2); }, 1.2),
  shutter: canvasTex(128, (g, n) => { for (let y = 0; y < n; y += 16) { const gr = g.createLinearGradient(0, y, 0, y + 16); gr.addColorStop(0, '#d6d6d2'); gr.addColorStop(0.7, '#a9a9a5'); gr.addColorStop(1, '#6f6f6c'); g.fillStyle = gr; g.fillRect(0, y, n, 16); } }, 0.5),
  leaf: canvasTex(128, (g, n) => { g.fillStyle = '#3d6a35'; g.fillRect(0, 0, n, n); for (let i = 0; i < 500; i++) { g.fillStyle = ['#2d5529', '#4d8243', '#6a9a50'][i % 3]; g.beginPath(); g.arc(random() * n, random() * n, 2 + random() * 4, 0, 7); g.fill(); } }, 0.9),
  trunk: canvasTex(128, (g, n) => { g.fillStyle = '#5a4636'; g.fillRect(0, 0, n, n); for (let x = 0; x < n; x += 3) { g.fillStyle = `rgba(30,20,10,${random() * 0.35})`; g.fillRect(x, 0, 1 + random() * 2, n); } }, 0.5),
};
const TINT = { tile: 0xffffff, floor: 0xffffff, pave: 0xffffff, stone: 0xffffff, asphalt: 0xffffff, carton: 0xffffff, context: 0xffffff, shutter: 0xffffff, leaf: 0xffffff, trunk: 0xffffff };

function worldUV(geo, metres) {
  const pos = geo.attributes.position, nor = geo.attributes.normal;
  const uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) {
    const ax = Math.abs(nor.getX(i)), ay = Math.abs(nor.getY(i)), az = Math.abs(nor.getZ(i));
    let u, v;
    if (ay >= ax && ay >= az) { u = pos.getX(i); v = pos.getZ(i); }
    else if (ax >= az) { u = pos.getZ(i); v = pos.getY(i); }
    else { u = pos.getX(i); v = pos.getY(i); }
    uv[i * 2] = u / metres; uv[i * 2 + 1] = v / metres;
  }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}
function polish(o, matCache) {
  const name = o.material.name;
  if (o.material.map && !TEX[name]) return;            // signage textures stay as they are
  if (!matCache[name]) {
    const m = o.material.clone();
    if (TEX[name]) { m.map = TEX[name]; m.color.set(TINT[name]); }
    if (name === 'tile') { m.roughness = 0.22; }
    if (name === 'floor') { m.roughness = 0.55; }
    if (['steel', 'steel_edge', 'steel_dark', 'alu'].includes(name)) {
      m.metalness = name === 'alu' ? 0.88 : 0.96;
      m.roughness = { steel: 0.34, steel_edge: 0.20, steel_dark: 0.44, alu: 0.38 }[name];
      m.envMapIntensity = name === 'steel_dark' ? 0.9 : 1.15;
      // Packed glTF roughness/metalness and brush normals come from build_model.py.
      for (const t of [m.roughnessMap, m.metalnessMap, m.normalMap]) if (t) { t.colorSpace = THREE.NoColorSpace; t.anisotropy = 8; }
    }
    if (name === 'paint') { m.color.set(0xf3ead6); m.roughness = 0.9; }
    if (name === 'glass') { m.opacity = 0.13; m.roughness = 0.06; m.metalness = 0; m.envMapIntensity = 0.7; m.color.set(0xc1dce0); }
    if (name === 'display') { m.emissive.set(0x41ccb0); m.emissiveIntensity = 0.7; }
    if (name === 'forest' || name === 'lime') { m.roughness = 0.45; }
    if (name === 'white' || name === 'poly') { m.roughness = 0.35; }
    if (name === 'black') { m.roughness = 0.35; m.metalness = 0.3; }
    if (name.startsWith('f_')) { m.roughness = 0.6; }
    matCache[name] = m;
  }
  o.material = matCache[name];
  const metres = TEX[name] ? TEX[name].userData.metres : 0;
  if (metres) worldUV(o.geometry, metres);
}
const edgeMat = new THREE.LineBasicMaterial({ color: 0x1c2620, transparent: true, opacity: 0.12 });
function addEdges(o, layer) {
  if (!['equip', 'mep', 'shelves', 'highshelf', 'front'].includes(layer)) return;
  if (o.material.transparent || /^(f_|cloth|skin|carton|t_|steel_edge)/.test(o.material.name)) return;
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 50), edgeMat);
  e.raycast = () => {}; o.add(e);
}

let camera, controls, root;
let layers = {};
const labelNodes = [];
const $ = (id) => document.getElementById(id);
const overlay = $('labels');
const offline = Boolean(window.EASYFOOD_MODELS);
let graphicsAvailable = false;
let activeDownload;
let releaseModel;
let renderPending = false;

function setControlsEnabled(enabled) {
  $('b-menu').hidden = !enabled;
  $('ui').inert = !enabled;
  $('ui').style.visibility = enabled ? '' : 'hidden';
}

function setStatus(message) {
  $('loading').firstElementChild.dir = lang === 'ar' ? 'rtl' : 'ltr';
  $('status').textContent = T[message][lang];
  $('loading').hidden = false;
}

function showFailure(message, layout, retry, retryLabel = 'retry', canResume = false) {
  window.__ready = false;
  setControlsEnabled(false);
  setStatus(message);
  const base = location.protocol === 'file:'
    ? 'https://amerkallajo.github.io/easy-food/easy-food-kitchen-package/model/viewer/'
    : location.href;
  const preview = $('preview');
  // Use sibling plans online and keep the downloaded viewer self-contained.
  preview.hidden = offline || location.protocol === 'file:';
  const plan = $('preview-link');
  plan.href = new URL('../../plans/layout-' + layout + '.png', base);
  plan.textContent = T.plan[lang] + ' ' + layout;
  if (!preview.hidden) {
    preview.src = plan.href;
    preview.alt = plan.textContent;
  }
  const offlineLink = $('offline-link');
  offlineLink.hidden = offline;
  offlineLink.href = new URL('viewer-offline.html', base);
  offlineLink.textContent = T.offline[lang];
  const button = $('b-retry');
  button.hidden = !retry;
  button.onclick = retry;
  button.textContent = T[retryLabel][lang];
  const resume = $('b-resume');
  resume.hidden = !canResume;
  resume.textContent = T.resume[lang];
  resume.onclick = () => {
    window.__ready = true;
    $('loading').hidden = true;
    setControlsEnabled(true);
    $('b-menu').focus();
  };
  $('recovery').hidden = false;
}

function b64ToBuffer(b64) {
  const bin = atob(b64); const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return u8.buffer;
}

function applyView(name) {
  viewName = name;
  const v = VIEWS[name];
  const pos = variant === 'B' && v.posB ? v.posB : v.pos;
  const target = variant === 'B' && v.tgtB ? v.tgtB : v.tgt;
  document.documentElement.lang = lang;
  document.body.classList.toggle('rtl', lang === 'ar');
  $('title').textContent = lang === 'ar' ? `إيزي فود - المخطط ${variant} - ${v.ar}` : `Easy Food - Layout ${variant} - ${v.en}`;
  $('note').textContent = $('mobile-note').textContent = T.note[lang];
  $('lg-raw').textContent = T.raw[lang]; $('lg-rte').textContent = T.rte[lang]; $('lg-staff').textContent = T.staff[lang];
  $('t-view').textContent = T.view[lang]; $('t-layers').textContent = T.layers[lang]; $('t-help').textContent = T.help[lang];
  camera = v.ortho
    ? new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 60)
    : new THREE.PerspectiveCamera(v.fov, 1, 0.05, 80);
  camera.position.copy(pos);
  if (v.up) camera.up.set(...v.up); else camera.up.set(0, 1, 0);
  camera.lookAt(target);
  if (controls) controls.dispose();
  controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(target); controls.update();
  for (const [ln, objs] of Object.entries(layers)) objs.forEach(o => (o.visible = !v.hide.includes(ln)));
  document.querySelectorAll('#layers button').forEach(b => b.classList.toggle('on', !v.hide.includes(b.dataset.l)));
  if (v.interior) {
    sun.intensity = 0.15; hemi.intensity = 0.24; inner.forEach(l => (l.intensity = 2.7)); strips.forEach(l => (l.intensity = 3.0)); scene.background.set(0xdfe8ee); scene.environmentIntensity = 0.8;
    sun.position.copy(P(-3, -8, 7));
  } else if (v.exterior) {
    sun.intensity = 3.2; hemi.intensity = 0.45; inner.forEach(l => (l.intensity = 4.0)); scene.background.set(0xbcd9ee); scene.environmentIntensity = 0.7;
    strips.forEach(l => (l.intensity = 2.0));
    sun.position.copy(P(-5, -9, 9));
  } else {
    sun.intensity = 3.0; hemi.intensity = 0.42; inner.forEach(l => (l.intensity = 0)); scene.background.set(0xe9e4d6); scene.environmentIntensity = 0.75;
    strips.forEach(l => (l.intensity = 0));
    sun.position.copy(P(5, -5, 10));
  }
  sun.target.position.copy(P(CX, 2.5, 0));
  buildLabels(v.labels);
  document.querySelectorAll('#views button').forEach(b => b.classList.toggle('on', b.dataset.v === name));
  $('legend').style.display = v.labels === 'stations' ? 'block' : 'none';
  renderer.shadowMap.needsUpdate = true;
  resize();
  controls.addEventListener('change', requestRender);
}

function mk(html, cls, pos, obj) {
  const el = document.createElement('div'); el.className = 'lab ' + (cls || '');
  el.dir = lang === 'ar' ? 'rtl' : 'ltr';
  el.innerHTML = html; overlay.appendChild(el);
  labelNodes.push({ el, pos, obj });
}

function buildLabels(mode) {
  overlay.innerHTML = ''; labelNodes.length = 0;
  if (mode === 'equip' || mode === 'codes') {
    root.traverse(o => {
      const e = o.userData;
      if (e && e.code && e.anchor) {
        const name = lang === 'ar' ? e.label_ar : e.label;
        mk(mode === 'codes' ? `<b>${e.code}</b>` : `<b>${e.code}</b> ${name}`, '', new THREE.Vector3(...e.anchor), o);
      }
    });
  } else if (mode === 'wc') {
    mk(lang === 'ar' ? `حمّام محفوظ · ${site.wc_w.toFixed(2)} × ${site.wc_d.toFixed(2)} م افتراضي` : `Retained WC · ${site.wc_w.toFixed(2)} × ${site.wc_d.toFixed(2)} m assumed`, 'ex', P(site.wc_w / 2, site.wc_y0 + 0.65, 1.28));
    mk(lang === 'ar' ? 'باب أكورديون · بلا قوس فتح بالممر' : 'Accordion door · no hinged aisle sweep', '', P(site.wc_w, site.wc_y0 + 0.48, 1.05));
  } else if (mode === 'stations') {
    for (const s of modelStore[variant].stations) {
      const txt = lang === 'ar' ? s[4] : s[3];
      const n = txt.split(' ')[0]; const cooked = +n >= 5;
      mk(`<i class="${cooked ? 'rte' : 'raw'}">${n}</i>${txt.slice(n.length)}`, 'st', new THREE.Vector3(s[0], s[1], s[2]));
    }
  } else if (mode === 'ext' && variant === 'A') {
    for (const e of EXT) mk(lang === 'ar' ? e[4] : e[3], 'ex', P(e[0], e[1], e[2]));
  }
}

function placeLabels() {
  const w = innerWidth, h = innerHeight;
  for (const L of labelNodes) {
    const p = L.pos.clone().project(camera);
    const vis = p.z < 1 && (!L.obj || L.obj.visible);
    L.el.style.display = vis ? 'block' : 'none';
    L.el.style.left = ((p.x * 0.5 + 0.5) * w) + 'px';
    L.el.style.top = ((-p.y * 0.5 + 0.5) * h) + 'px';
  }
}

function resize() {
  if (!camera || !graphicsAvailable) return;
  const w = innerWidth, h = innerHeight, aspect = w / h;
  const view = VIEWS[viewName];
  if (camera.isOrthographicCamera) {
    const extent = view.ortho * Math.max(1, 1.75 / aspect);
    Object.assign(camera, { left: -extent * aspect, right: extent * aspect, top: extent, bottom: -extent });
  } else {
    camera.aspect = aspect;
    // Fit the overview across a portrait screen without moving the orbit target.
    if (aspect < 1 && view.fov <= 44) {
      const halfWidth = Math.tan(THREE.MathUtils.degToRad(Math.max(40, view.fov) / 2));
      camera.fov = Math.min(85, THREE.MathUtils.radToDeg(2 * Math.atan(halfWidth / aspect)));
    } else {
      camera.fov = aspect < 1 ? Math.min(75, view.fov * 1.5) : view.fov;
    }
  }
  camera.updateProjectionMatrix();
  const size = renderer.getSize(new THREE.Vector2());
  if (size.x !== w || size.y !== h) renderer.setSize(w, h, false);
  requestRender();
}

function requestRender() {
  if (renderPending || !graphicsAvailable) return;
  renderPending = true;
  requestAnimationFrame(() => {
    renderPending = false;
    if (!graphicsAvailable) return;
    try {
      renderer.render(scene, camera);
      placeLabels();
      if ($('loading').hidden || !$('recovery').hidden || activeDownload) return;
      $('loading').hidden = true;
      setControlsEnabled(true);
      window.__ready = true;
    } catch (error) {
      console.error('Easy Food 3D rendering failed', error);
      graphicsAvailable = false;
      activeDownload?.abort();
      showFailure('context', variant, () => location.reload(), 'reload');
    }
  });
}

function buildUi() {
  const vb = $('views'); vb.innerHTML = '';
  for (const [k, v] of Object.entries(VIEWS)) {
    const b = document.createElement('button'); b.textContent = lang === 'ar' ? v.btn : k.replace('_', ' '); b.dataset.v = k;
    b.onclick = () => applyView(k); vb.appendChild(b);
  }
  const lb = $('layers'); lb.innerHTML = '';
  for (const k of Object.keys(layers).sort()) {
    const b = document.createElement('button'); b.textContent = k; b.dataset.l = k;
    b.onclick = () => {
      const on = !layers[k][0].visible;
      layers[k].forEach(o => (o.visible = on));
      b.classList.toggle('on', on);
      renderer.shadowMap.needsUpdate = true;
      requestRender();
    };
    lb.appendChild(b);
  }
  $('b-lang').textContent = lang === 'ar' ? 'English' : 'العربية';
  $('b-lang').onclick = () => {
    lang = lang === 'ar' ? 'en' : 'ar';
    buildUi();
    applyView(viewName);
  };
  $('b-layout').textContent = `${T.layout[lang]} ${variant === 'A' ? 'B' : 'A'}`;
  $('b-layout').onclick = () => load(variant === 'A' ? 'B' : 'A');
}

function installModel(model, layout) {
  const materials = new Set(), geometries = new Set();
  const materialCache = Object.create(null);
  const edges = [];
  const modelLayers = {};
  model.traverse(o => {
    const layer = o.userData.layer;
    if (layer) (modelLayers[layer] ||= []).push(o);
    if (!o.isMesh) return;
    materials.add(o.material);
    geometries.add(o.geometry);
    o.castShadow = !o.material.transparent && !o.material.map;
    o.receiveShadow = true;
    if (o.material.map) o.material.map.anisotropy = 8;
    polish(o, materialCache);
    if (o.material.transparent) o.material.depthWrite = false;
    if (!mobileGraphics) {
      let parent = o;
      while (parent && !parent.userData.layer) parent = parent.parent;
      edges.push([o, parent?.userData.layer]);
    }
  });
  for (const [mesh, layer] of edges) {
    addEdges(mesh, layer);
    for (const child of mesh.children) {
      if (child.isLineSegments && child.material === edgeMat) geometries.add(child.geometry);
    }
  }
  const textures = new Set();
  for (const material of materials) {
    for (const value of Object.values(material)) {
      if (value?.isTexture) textures.add(value);
    }
  }

  if (root) releaseModel();
  releaseModel = () => {
    scene.remove(model);
    for (const geometry of geometries) geometry.dispose();
    for (const material of [...materials, ...Object.values(materialCache)]) material.dispose();
    const bitmaps = new Set();
    for (const texture of textures) {
      if (typeof texture.image?.close === 'function') bitmaps.add(texture.image);
      texture.dispose();
    }
    for (const bitmap of bitmaps) bitmap.close();
  };
  root = model;
  variant = layout;
  layers = modelLayers;
  scene.add(root);
  buildUi();
  applyView(viewName);
}

async function downloadModel(layout, signal) {
  const response = await fetch('../easy-food-kitchen-' + layout + '.glb', { signal });
  if (!response.ok) throw new Error('Model download returned HTTP ' + response.status);
  return response.arrayBuffer();
}

async function load(layout) {
  if (activeDownload || !graphicsAvailable) return;
  window.__ready = false;
  setControlsEnabled(false);
  $('preview').hidden = true;
  $('recovery').hidden = true;
  setStatus(offline ? 'preparing' : 'loading');
  const controller = new AbortController();
  activeDownload = controller;
  const slow = offline ? undefined : setTimeout(() => setStatus('slow'), 12000);
  const deadline = offline ? undefined : setTimeout(() => controller.abort(), 90000);
  let gltf;
  try {
    const data = offline
      ? b64ToBuffer(modelStore[layout].glb)
      : await downloadModel(layout, controller.signal);
    clearTimeout(slow);
    clearTimeout(deadline);
    if (!graphicsAvailable) return;
    setStatus('preparing');
    gltf = await new GLTFLoader().parseAsync(data, '');
  } catch (error) {
    if (graphicsAvailable) {
      console.error('Easy Food 3D model failed to load', error);
      showFailure('failed', layout, () => load(layout), 'retry', Boolean(root));
      if (root) $('b-retry').focus();
    }
    return;
  } finally {
    clearTimeout(slow);
    clearTimeout(deadline);
    activeDownload = undefined;
  }
  if (!graphicsAvailable) return;
  try {
    installModel(gltf.scene, layout);
  } catch (error) {
    console.error('Easy Food 3D scene setup failed', error);
    graphicsAvailable = false;
    showFailure('context', layout, () => location.reload(), 'reload');
  }
}

document.documentElement.lang = lang;
document.body.classList.toggle('rtl', lang === 'ar');
document.body.classList.toggle('shot', shot);
if (!offline && location.protocol === 'file:') {
  showFailure('local', variant);
} else {
  try {
    initGraphics();
    graphicsAvailable = true;
    addEventListener('resize', resize);
    load(variant);
  } catch (error) {
    console.warn('Easy Food 3D graphics unavailable', error);
    showFailure('webgl', variant, () => location.reload(), 'reload');
  }
}
