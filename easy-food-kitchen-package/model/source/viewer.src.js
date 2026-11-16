// Offline viewer for the Easy Food kitchen model.
// Bundled with esbuild, then inlined into ../viewer/viewer.html by make_viewer.py (single self-contained file).
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

const q = new URLSearchParams(location.search);
let variant = q.get('m') || 'A';
let lang = q.get('lang') || 'ar';
const shot = q.get('shot') === '1';
const CX = 1.4;   // room centre across (2.79 m wide)
// model coords: x across, y up, z = -depth (street is +z, back wall is z = -5.06)
const P = (x, depth, up) => new THREE.Vector3(x, up, -depth);

const VIEWS = {
  cutaway: { en: 'Cutaway 3D - roof, right wall and shopfront removed', ar: 'مقطع ثلاثي الأبعاد - بدون السقف والجدار الأيمن والواجهة', btn: 'مقطع 3D',
    pos: P(7.2, -3.4, 6.4), tgt: P(1.3, 2.5, 0.6), fov: 34,
    hide: ['ceiling', 'wall_right', 'front', 'people_out', 'people_in', 'flow', 'context', 'site', 'highshelf'], labels: 'equip' },
  top: { en: 'Top-down cutaway (street at right)', ar: 'مسقط علوي (الشارع إلى اليمين)', btn: 'مسقط علوي',
    ortho: 2.05, pos: P(CX, 2.05, 12), tgt: P(CX, 2.05, 0), up: [1, 0, 0],
    hide: ['ceiling', 'people_out', 'flow', 'context', 'mep', 'highshelf', 'shelves'], labels: 'codes' },
  interior_front: { en: 'Interior - from the staff door looking to the back', ar: 'من الداخل - من باب الموظفين باتجاه الخلف', btn: 'داخلي من الباب',
    pos: P(1.2, 0.22, 1.66), tgt: P(1.65, 4.8, 0.95), fov: 80,
    hide: ['people_out', 'flow', 'people_in'], labels: 'none', interior: true },
  interior_back: { en: 'Interior - from the back prep area looking to the service window', ar: 'من الداخل - من منطقة التحضير باتجاه نافذة الخدمة', btn: 'داخلي من الخلف',
    pos: P(0.8, 4.3, 1.72), tgt: P(2.1, 0.0, 1.0), fov: 76,
    hide: ['flow', 'people_in'], labels: 'none', interior: true },
  exterior: { en: 'Exterior - signage, order and collect positions', ar: 'الواجهة - اللافتة ونافذتا الطلب والاستلام', btn: 'الواجهة',
    pos: P(-0.9, -5.6, 1.6), tgt: P(1.4, 0, 1.75), fov: 52,
    hide: ['flow', 'ceiling'], labels: 'ext', exterior: true },
  flow: { en: 'Staff movement and food flow', ar: 'حركة الموظفين ومسار الطعام', btn: 'مسار العمل',
    pos: P(4.6, -1.4, 9.8), tgt: P(1.35, 2.45, 0.3), fov: 34,
    hide: ['ceiling', 'wall_right', 'front', 'people_out', 'context', 'site', 'mep', 'highshelf', 'shelves'], labels: 'stations' },
};
let viewName = q.get('view') || 'cutaway';

const T = {
  note: { en: 'Concept model: 2.79 x 5.06 m from the owner + photographs. Ceiling height, wall thickness, sidewalk depth and all service points are ASSUMED.',
          ar: 'نموذج تصوّري: 2.79 × 5.06 م حسب قياس المالك + الصور. ارتفاع السقف وسماكة الجدران وعرض الرصيف ونقاط الماء والكهرباء والغاز افتراضية.' },
  raw: { en: 'Raw / incoming goods (steps 1-4)', ar: 'مواد نيئة / واردة (الخطوات 1-4)' },
  rte: { en: 'Cooked / ready-to-eat (steps 5-8)', ar: 'مطبوخ / جاهز للأكل (الخطوات 5-8)' },
  staff: { en: 'Staff positions at peak', ar: 'مواقع الموظفين وقت الذروة' },
  layout: { en: 'Layout', ar: 'المخطط' },
  view: { en: 'View', ar: 'المشهد' }, layers: { en: 'Layers', ar: 'الطبقات' },
  help: { en: 'Drag to orbit, wheel to zoom, right-drag to pan.', ar: 'اسحب للتدوير، العجلة للتكبير، الزر الأيمن للتحريك.' },
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

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(shot ? 1 : Math.min(2, devicePixelRatio));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.getElementById('stage').appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf3f1ea);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.55;

const hemi = new THREE.HemisphereLight(0xdfeaf5, 0x8a8172, 0.9);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffeccf, 2.2);
sun.castShadow = true;
sun.shadow.mapSize.set(4096, 4096);
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
Object.assign(sun.shadow.camera, { left: -7, right: 7, top: 8, bottom: -8, near: 0.5, far: 40 });
scene.add(sun); scene.add(sun.target);
const inner = [];
[[CX, 1.0], [CX, 2.6], [CX, 4.1]].forEach(([x, d]) => {
  const l = new THREE.PointLight(0xfff1dc, 0, 7, 1.6); l.position.copy(P(x, d, 2.75)); l.castShadow = d > 2 && d < 3; l.shadow.mapSize.set(1024, 1024); l.shadow.bias = -0.002; scene.add(l); inner.push(l);
});


// ---------- surface detail: procedural textures, world-space UVs, edge lines ----------
function canvasTex(size, draw, metres) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  t.userData.metres = metres;
  return t;
}
function noise(g, n, count, alpha, light) {
  for (let i = 0; i < count; i++) {
    g.fillStyle = `rgba(${light ? 255 : 0},${light ? 255 : 0},${light ? 255 : 0},${Math.random() * alpha})`;
    g.fillRect(Math.random() * n, Math.random() * n, 1 + Math.random() * 2, 1 + Math.random() * 2);
  }
}
function tiles(cols, rows, base, grout, vary, offset) {
  return (g, n) => {
    g.fillStyle = grout; g.fillRect(0, 0, n, n);
    const w = n / cols, h = n / rows;
    for (let r = 0; r < rows; r++) for (let c = -1; c < cols; c++) {
      const v = Math.round((Math.random() - 0.5) * vary);
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
  carton: canvasTex(256, (g, n) => { g.fillStyle = '#b98d5c'; g.fillRect(0, 0, n, n); for (let y = 0; y < n; y += 4) { g.fillStyle = `rgba(90,60,30,${0.05 + Math.random() * 0.06})`; g.fillRect(0, y, n, 1); } g.fillStyle = 'rgba(70,45,20,0.5)'; g.fillRect(0, n * 0.46, n, n * 0.08); }, 0.45),
  context: canvasTex(256, (g, n) => { g.fillStyle = '#cfcbc1'; g.fillRect(0, 0, n, n); noise(g, n, 4000, 0.07, false); g.fillStyle = 'rgba(0,0,0,0.10)'; g.fillRect(0, 0, n, 2); g.fillRect(0, n / 2, n, 2); }, 1.2),
  shutter: canvasTex(128, (g, n) => { for (let y = 0; y < n; y += 16) { const gr = g.createLinearGradient(0, y, 0, y + 16); gr.addColorStop(0, '#d6d6d2'); gr.addColorStop(0.7, '#a9a9a5'); gr.addColorStop(1, '#6f6f6c'); g.fillStyle = gr; g.fillRect(0, y, n, 16); } }, 0.5),
  leaf: canvasTex(128, (g, n) => { g.fillStyle = '#3d6a35'; g.fillRect(0, 0, n, n); for (let i = 0; i < 500; i++) { g.fillStyle = ['#2d5529', '#4d8243', '#6a9a50'][i % 3]; g.beginPath(); g.arc(Math.random() * n, Math.random() * n, 2 + Math.random() * 4, 0, 7); g.fill(); } }, 0.9),
  trunk: canvasTex(128, (g, n) => { g.fillStyle = '#5a4636'; g.fillRect(0, 0, n, n); for (let x = 0; x < n; x += 3) { g.fillStyle = `rgba(30,20,10,${Math.random() * 0.35})`; g.fillRect(x, 0, 1 + Math.random() * 2, n); } }, 0.5),
};
const brushed = canvasTex(256, (g, n) => { g.fillStyle = '#8c8c8c'; g.fillRect(0, 0, n, n); for (let y = 0; y < n; y++) { g.fillStyle = `rgba(${Math.random() > 0.5 ? 255 : 0},${Math.random() > 0.5 ? 255 : 0},${Math.random() > 0.5 ? 255 : 0},0.0)`; const v = Math.random(); g.fillStyle = `rgba(${v > 0.5 ? 255 : 0},${v > 0.5 ? 255 : 0},${v > 0.5 ? 255 : 0},${0.03 + Math.random() * 0.07})`; g.fillRect(0, y, n, 1); } }, 0.35);
brushed.colorSpace = THREE.NoColorSpace;
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
const matCache = {};
function polish(o) {
  const name = o.material.name;
  if (o.material.map && !TEX[name]) return;            // signage textures stay as they are
  if (!matCache[name]) {
    const m = o.material.clone();
    if (TEX[name]) { m.map = TEX[name]; m.color.set(TINT[name]); }
    if (name === 'tile') { m.roughness = 0.22; }
    if (name === 'floor') { m.roughness = 0.55; }
    if (name === 'steel' || name === 'alu') { m.color.set(name === 'steel' ? 0xc4c8cc : 0xaeb2b6); m.metalness = 0.6; m.roughness = 0.5; m.roughnessMap = brushed; m.envMapIntensity = 1.3; }
    if (name === 'steel_dark') { m.metalness = 0.5; m.roughness = 0.6; m.roughnessMap = brushed; m.envMapIntensity = 1.0; }
    if (name === 'paint') { m.color.set(0xf3ead6); m.roughness = 0.9; }
    if (name === 'glass') { m.opacity = 0.2; m.roughness = 0.03; m.metalness = 0.2; m.envMapIntensity = 2.2; m.color.set(0xa8d4d8); }
    if (name === 'forest' || name === 'lime') { m.roughness = 0.45; }
    if (name === 'white' || name === 'poly') { m.roughness = 0.35; }
    if (name === 'black') { m.roughness = 0.35; m.metalness = 0.3; }
    if (name.startsWith('f_')) { m.roughness = 0.6; }
    matCache[name] = m;
  }
  o.material = matCache[name];
  const metres = TEX[name] ? TEX[name].userData.metres : (o.material.roughnessMap ? 0.35 : 0);
  if (metres) worldUV(o.geometry, metres);
}
const edgeMat = new THREE.LineBasicMaterial({ color: 0x1c2620, transparent: true, opacity: 0.28 });
function addEdges(o, layer) {
  if (!['equip', 'mep', 'shelves', 'highshelf', 'front'].includes(layer)) return;
  if (o.material.transparent || /^(f_|cloth|skin|carton|t_)/.test(o.material.name)) return;
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 35), edgeMat);
  e.raycast = () => {}; o.add(e);
}

let camera, controls, root;
let layers = {};
const labelNodes = [];
const overlay = document.getElementById('labels');
const $ = (id) => document.getElementById(id);

function b64ToBuffer(b64) {
  const bin = atob(b64); const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return u8.buffer;
}

function applyView(name) {
  viewName = name;
  const v = VIEWS[name];
  document.documentElement.lang = lang;
  document.body.classList.toggle('rtl', lang === 'ar');
  $('title').textContent = lang === 'ar' ? `إيزي فود - المخطط ${variant} - ${v.ar}` : `Easy Food - Layout ${variant} - ${v.en}`;
  $('note').textContent = T.note[lang];
  $('lg-raw').textContent = T.raw[lang]; $('lg-rte').textContent = T.rte[lang]; $('lg-staff').textContent = T.staff[lang];
  $('t-view').textContent = T.view[lang]; $('t-layers').textContent = T.layers[lang]; $('t-help').textContent = T.help[lang];
  const w = innerWidth, h = innerHeight;
  if (v.ortho) {
    const a = w / h; let s = v.ortho; if (a < 1.75) s = v.ortho * 1.75 / a;
    camera = new THREE.OrthographicCamera(-s * a, s * a, s, -s, 0.1, 60);
  } else camera = new THREE.PerspectiveCamera(w < h ? Math.min(75, v.fov * 1.5) : v.fov, w / h, 0.05, 80);
  camera.position.copy(v.pos);
  if (v.up) camera.up.set(...v.up); else camera.up.set(0, 1, 0);
  camera.lookAt(v.tgt);
  if (controls) controls.dispose();
  controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(v.tgt); controls.update();
  for (const [ln, objs] of Object.entries(layers)) objs.forEach(o => (o.visible = !v.hide.includes(ln)));
  document.querySelectorAll('#layers button').forEach(b => b.classList.toggle('on', !v.hide.includes(b.dataset.l)));
  if (v.interior) {
    sun.intensity = 0.15; hemi.intensity = 0.16; inner.forEach(l => (l.intensity = 3.4)); scene.background.set(0xdfe8ee); scene.environmentIntensity = 0.45;
    sun.position.copy(P(-3, -8, 7));
  } else if (v.exterior) {
    sun.intensity = 3.2; hemi.intensity = 0.45; inner.forEach(l => (l.intensity = 4.0)); scene.background.set(0xbcd9ee); scene.environmentIntensity = 0.7;
    sun.position.copy(P(-5, -9, 9));
  } else {
    sun.intensity = 3.0; hemi.intensity = 0.42; inner.forEach(l => (l.intensity = 0)); scene.background.set(0xe9e4d6); scene.environmentIntensity = 0.75;
    sun.position.copy(P(5, -5, 10));
  }
  sun.target.position.copy(P(CX, 2.5, 0));
  buildLabels(v.labels);
  document.querySelectorAll('#views button').forEach(b => b.classList.toggle('on', b.dataset.v === name));
  $('legend').style.display = v.labels === 'stations' ? 'block' : 'none';
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
  } else if (mode === 'stations') {
    for (const s of window.EASYFOOD_MODELS[variant].stations) {
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

function frame() {
  renderer.setSize(innerWidth, innerHeight, false);
  renderer.domElement.style.width = '100%'; renderer.domElement.style.height = '100%';
  if (camera.isPerspectiveCamera) { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
  renderer.render(scene, camera);
  placeLabels();
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
    b.onclick = () => { const on = !layers[k][0].visible; layers[k].forEach(o => (o.visible = on)); b.classList.toggle('on', on); };
    lb.appendChild(b);
  }
  $('b-lang').textContent = lang === 'ar' ? 'English' : 'العربية';
  $('b-lang').onclick = () => { lang = lang === 'ar' ? 'en' : 'ar'; buildUi(); applyView(viewName); };
  $('b-layout').textContent = `${T.layout[lang]} ${variant === 'A' ? 'B' : 'A'}`;
  $('b-layout').onclick = () => load(variant === 'A' ? 'B' : 'A');
}

function load(v) {
  variant = v;
  if (root) scene.remove(root);
  new GLTFLoader().parse(b64ToBuffer(window.EASYFOOD_MODELS[variant].glb), '', (gltf) => {
    root = gltf.scene; scene.add(root); layers = {};
    const todoEdges = [];
    root.traverse(o => {
      if (o.userData && o.userData.layer) (layers[o.userData.layer] ||= []).push(o);
      if (o.isMesh) {
        const transparent = o.material.transparent;
        o.castShadow = !transparent; o.receiveShadow = true;
        if (o.material.map) { o.material.map.anisotropy = 8; o.castShadow = false; }
        let layer = o.userData.layer; for (let q2 = o.parent; !layer && q2; q2 = q2.parent) layer = q2.userData && q2.userData.layer;
        polish(o);
        if (transparent) o.material.depthWrite = false;
        todoEdges.push([o, layer]);
      }
    });
    todoEdges.forEach(([o, l]) => addEdges(o, l));
    if (shot) document.body.classList.add('shot');
    buildUi();
    applyView(viewName);
    renderer.setAnimationLoop(frame);
    setTimeout(() => { window.__ready = true; }, 600);
  }, (err) => { $('title').textContent = 'Model failed to load: ' + err; });
}
load(variant);
addEventListener('resize', () => applyView(viewName));
