/* Easy Food — homepage interactions: header, mobile menu, section spy, reveal, lightbox. */
(() => {
  'use strict';
  const root = document.documentElement;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- Header state + section spy ---------- */
  const header = document.querySelector('[data-header]');
  const navLinks = [...document.querySelectorAll('[data-nav-link]')];
  const sections = navLinks.map((a) => document.getElementById(a.hash.slice(1))).filter(Boolean);
  let ticking = false;

  const update = () => {
    ticking = false;
    header?.classList.toggle('is-scrolled', window.scrollY > 8);
    const line = window.innerHeight * 0.35;
    let current = null;
    for (const s of sections) if (s.getBoundingClientRect().top <= line) current = s;
    if (current && current.getBoundingClientRect().bottom < 0) current = null;
    navLinks.forEach((a) => {
      const on = !!current && a.hash === `#${current.id}`;
      a.classList.toggle('is-active', on);
      if (on) a.setAttribute('aria-current', 'location');
      else a.removeAttribute('aria-current');
    });
  };
  const requestUpdate = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
  window.addEventListener('scroll', requestUpdate, { passive: true });
  window.addEventListener('resize', requestUpdate);
  update();

  /* ---------- Mobile menu ---------- */
  const toggle = document.querySelector('[data-menu-toggle]');
  const nav = document.querySelector('[data-nav]');
  const phone = window.matchMedia('(max-width: 759.98px)');

  const setMenu = (open, returnFocus = false) => {
    if (!toggle || !nav) return;
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
    if (open) nav.querySelector('a')?.focus({ preventScroll: true });
    else if (returnFocus) toggle.focus();
  };
  const isOpen = () => toggle?.getAttribute('aria-expanded') === 'true';

  toggle?.addEventListener('click', () => setMenu(!isOpen()));
  nav?.addEventListener('click', (e) => { if (e.target.closest('a') && phone.matches) setMenu(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen()) { e.preventDefault(); setMenu(false, true); }
  });
  document.addEventListener('click', (e) => { if (isOpen() && !header.contains(e.target)) setMenu(false); });
  nav?.addEventListener('focusout', (e) => {
    if (isOpen() && e.relatedTarget && !header.contains(e.relatedTarget)) setMenu(false);
  });
  phone.addEventListener('change', () => setMenu(false));

  /* ---------- Reveal on scroll ---------- */
  const reveals = [...document.querySelectorAll('[data-reveal]')];
  if ('IntersectionObserver' in window && !reduceMotion.matches) {
    // Anything already on screen is shown immediately so nothing flickers.
    reveals.forEach((el) => { if (el.getBoundingClientRect().top < window.innerHeight * 0.95) el.classList.add('is-in'); });
    root.classList.add('reveal-ready');
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add('is-in'); io.unobserve(entry.target); }
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.06 });
    reveals.filter((el) => !el.classList.contains('is-in')).forEach((el) => io.observe(el));
  }

  /* ---------- Lightbox ---------- */
  const dlg = document.querySelector('[data-lightbox-dialog]');
  if (!dlg || typeof dlg.showModal !== 'function') return; // links still open the original files

  const q = (s) => dlg.querySelector(s);
  const img = q('[data-lb-img]');
  const stage = q('[data-lb-stage]');
  const title = q('[data-lb-title]');
  const caption = q('[data-lb-caption]');
  const indexEl = q('[data-lb-index]');
  const totalEl = q('[data-lb-total]');
  const original = q('[data-lb-original]');
  const zoomBtn = q('[data-lb-zoom]');
  const zoomLabel = q('[data-lb-zoom-label]');
  const loading = q('[data-lb-loading]');
  const prevBtn = q('[data-lb-prev]');
  const nextBtn = q('[data-lb-next]');
  const triggers = [...document.querySelectorAll('[data-lightbox]')];

  let group = [];
  let index = 0;
  let opener = null;
  let token = 0;

  const zoomed = () => dlg.classList.contains('is-zoomed');

  const setZoom = (on, point) => {
    dlg.classList.toggle('is-zoomed', on);
    zoomBtn.setAttribute('aria-pressed', String(on));
    zoomLabel.textContent = on ? 'ملاءمة الشاشة' : 'تكبير';
    if (!on) { img.style.width = ''; stage.scrollTo(0, 0); return; }
    const target = Math.max(img.naturalWidth || 0, stage.clientWidth * 1.6);
    img.style.width = `${Math.round(target)}px`;
    requestAnimationFrame(() => {
      const fx = point ? point.x : 0.5;
      const fy = point ? point.y : 0.5;
      stage.scrollTo(img.offsetWidth * fx - stage.clientWidth / 2, img.offsetHeight * fy - stage.clientHeight / 2);
    });
  };

  const show = (n) => {
    index = (n + group.length) % group.length;
    const t = group[index];
    const thumb = t.querySelector('img') || t.closest('figure')?.querySelector('img');
    const full = t.getAttribute('href');
    const my = ++token;

    if (zoomed()) setZoom(false);
    title.textContent = t.dataset.title || '';
    caption.textContent = t.dataset.caption || '';
    indexEl.textContent = String(index + 1).padStart(2, '0');
    totalEl.textContent = String(group.length).padStart(2, '0');
    original.href = full;
    dlg.classList.toggle('is-doc', t.hasAttribute('data-doc'));
    img.alt = thumb?.alt || t.dataset.title || '';
    img.src = t.dataset.preview || full;
    prevBtn.hidden = nextBtn.hidden = group.length < 2;

    loading.hidden = false;
    const hi = new Image();
    hi.decoding = 'async';
    hi.onload = () => { if (my === token) { img.src = full; loading.hidden = true; } };
    hi.onerror = () => { if (my === token) loading.hidden = true; };
    hi.src = full;
  };

  const open = (t) => {
    opener = t;
    group = triggers.filter((x) => x.dataset.lightbox === t.dataset.lightbox);
    show(group.indexOf(t));
    root.classList.add('has-lightbox');
    dlg.showModal();
  };

  triggers.forEach((t) => t.addEventListener('click', (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    open(t);
  }));

  // Cleanup runs directly when we close, and again (harmlessly) from the native close event.
  const cleanup = () => {
    if (!root.classList.contains('has-lightbox')) return;
    token++;
    setZoom(false);
    img.removeAttribute('src');
    root.classList.remove('has-lightbox');
    opener?.focus({ preventScroll: true });
  };
  const closeBox = () => { if (dlg.open) dlg.close(); cleanup(); };
  dlg.addEventListener('close', cleanup);
  dlg.addEventListener('cancel', (e) => { e.preventDefault(); closeBox(); }); // Escape
  q('[data-lb-close]').addEventListener('click', closeBox);
  prevBtn.addEventListener('click', () => show(index - 1));
  nextBtn.addEventListener('click', () => show(index + 1));
  zoomBtn.addEventListener('click', () => setZoom(!zoomed()));

  img.addEventListener('click', (e) => {
    const r = img.getBoundingClientRect();
    setZoom(!zoomed(), { x: (e.clientX - r.left) / r.width, y: (e.clientY - r.top) / r.height });
  });

  // Clicking the empty area around the picture closes the preview.
  dlg.addEventListener('click', (e) => { if ((e.target === dlg || e.target === stage) && !zoomed()) closeBox(); });

  // Keep Tab inside the preview, and in right-to-left order the next item sits to the left.
  dlg.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      const items = [...dlg.querySelectorAll('button, a[href]')].filter((el) => !el.hidden && el.offsetParent !== null);
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && (document.activeElement === first || !dlg.contains(document.activeElement))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      return;
    }
    if (zoomed() || group.length < 2) return;
    if (e.key === 'ArrowLeft') { e.preventDefault(); show(index + 1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); show(index - 1); }
  });

  let startX = null;
  stage.addEventListener('pointerdown', (e) => { if (e.pointerType !== 'mouse' && !zoomed()) startX = e.clientX; });
  stage.addEventListener('pointerup', (e) => {
    if (startX === null) return;
    const dx = e.clientX - startX;
    startX = null;
    if (Math.abs(dx) > 50 && group.length > 1) show(dx > 0 ? index + 1 : index - 1);
  });
  stage.addEventListener('pointercancel', () => { startX = null; });
})();
