/* Viewport tests without forcing a layout: media queries are cached by the browser (reading innerWidth after a DOM change
 * recalculated the whole page each time). */
window.SW_MQ = window.SW_MQ || matchMedia('(max-width: 860px)');
/* the app added to the Home Screen: html.pwa (19 Oct., Mateo's recording: on his iPhone « display-mode: standalone » does not
   match there, navigator.standalone does) — the installed app's header, bars and pull to refresh follow this mark */
try { if ((window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true) document.documentElement.classList.add('pwa'); } catch (e) { /* no mark */ }
/* never a zoom (20 Oct., Mateo: a double tap by mistake zoomed): Safari ignores user-scalable=no, its pinch is stopped here; ctrl/⌘ + wheel or trackpad pinch and ctrl/⌘ + − / = / 0 on a computer */
(() => { const no = (e) => e.preventDefault(); ['gesturestart', 'gesturechange', 'gestureend'].forEach((t) => document.addEventListener(t, no, { passive: false })); addEventListener('wheel', (e) => { if (e.ctrlKey || e.metaKey) e.preventDefault(); }, { passive: false }); addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && !e.altKey && ['+', '=', '-', '_', '0'].includes(e.key)) e.preventDefault(); }); document.addEventListener('touchmove', (e) => { if (e.touches.length > 1 || (e.scale && e.scale !== 1)) e.preventDefault(); }, { passive: false }); })();
window.SW_MQ6 = window.SW_MQ6 || matchMedia('(max-width: 600px)');
/* (31 Oct., C4) only the sample data so far (no account or trade of the trader's own) */
window.sampleOnly = () => typeof S !== 'undefined' && (S.accounts || []).some((a) => a.demo) && !(S.accounts || []).some((a) => !a.demo) && !(S.trades || []).some((x) => !x.demo);
/* Performance: every DOM watcher of this file is batched to one call per frame (they used to run on every
 * single DOM change: 13 watchers × hundreds of changes when a page renders). The callback still runs before the
 * next paint, so nothing flashes. */
window.SweepMO = window.SweepMO || class {
  constructor(cb) {
    let q = [], pending = false;
    this.o = new MutationObserver((recs) => {
      for (const r of recs) q.push(r);
      if (pending) return; pending = true;
      requestAnimationFrame(() => { pending = false; const b = q; q = []; if (!b.length) return; try { cb(b, this); } catch (e) { /* never blocks */ } });
    });
    // (1 Nov.) a page just drawn: what waits for the next frame runs now, before its first image (SweepMO.flushAll)
    this.flush = () => { const b = q.concat(this.o.takeRecords()); q = []; if (!b.length) return false; try { cb(b, this); } catch (e) { /* never blocks */ } return true; };
    (window.__swMOs || (window.__swMOs = [])).push(this);
  }
  static flushAll() { for (let k = 0; k < 3; k++) { let any = false; (window.__swMOs || []).forEach((m) => { if (m.flush()) any = true; }); if (!any) return; } }
  observe(t, o) { this.o.observe(t, o); }
  disconnect() { this.o.disconnect(); }
  takeRecords() { return this.o.takeRecords(); }
};
/*
 * Sweep — navigation (one place for it).
 * Structure: Today · Trades (List · Calendar · Journal) · Stats · Accounts (Accounts · Payouts & expenses) · Progression.
 * Avatar menu (phone and desktop): the header line (first name · plan: the subscription), My progress, What's new, Settings,
 * Referral, Give feedback, Help, [Traders], Log out (SWEEP.md step 6: no second « Subscription » entry).
 * Hashes stay the official addresses (old links keep working); aliases: #today, #stats, #subscription, #progress.
 * Every sub-page has a back chevron to its parent; Android back / iOS swipe closes an open sheet first.
 */
(function () {
  'use strict';
  if (typeof render !== 'function' || typeof route !== 'function') return;
  const T = {
    en: { list: 'List', cal: 'Calendar', jour: 'Journal', acc: 'Accounts', pay: 'My money', today: 'Today', trades: 'Trades', stats: 'Stats',
      prog: 'My progress', news: 'What’s new', settings: 'Settings', sub: 'Subscription', ref: 'Referral', fb: 'Give feedback', help: 'Help', admin: 'Traders', mail: 'Emails', out: 'Log out', back: 'Back', menu: 'Menu', search: 'Search' },
    fr: { list: 'Liste', cal: 'Calendrier', jour: 'Journal', acc: 'Comptes', pay: 'Mon argent', today: 'Aujourd’hui', trades: 'Trades', stats: 'Stats',
      prog: 'Ma progression', news: 'Quoi de neuf', settings: 'Réglages', sub: 'Abonnement', ref: 'Parrainage', fb: 'Donner mon avis', help: 'Aide', admin: 'Traders', mail: 'Courriels', out: 'Déconnexion', back: 'Retour', menu: 'Menu', search: 'Rechercher' },
    es: { list: 'Lista', cal: 'Calendario', jour: 'Diario', acc: 'Cuentas', pay: 'Mi dinero', today: 'Hoy', trades: 'Operaciones', stats: 'Stats',
      prog: 'Mi progreso', news: 'Novedades', settings: 'Ajustes', sub: 'Suscripción', ref: 'Referidos', fb: 'Dar mi opinión', help: 'Ayuda', admin: 'Traders', mail: 'Correos', out: 'Cerrar sesión', back: 'Atrás', menu: 'Menú', search: 'Buscar' },
  };
  const t = () => T[LANG] || T.en;
  const SEG = {
    trades: [['trades', 'list'], ['calendar', 'cal'], ['journal', 'jour']],
    accounts: [['accounts', 'acc'], ['payouts', 'pay']],
  };
  const GROUP = { trades: 'trades', calendar: 'trades', journal: 'trades', accounts: 'accounts', payouts: 'accounts' };
  // parent of each sub-page (the back chevron)
  const PARENT = { trade: ['#trades', 'trades'], import: ['#trades', 'trades'], account: ['#accounts', 'acc'], news: ['#dashboard', 'today'],
    settings: ['#dashboard', 'today'], plan: ['#dashboard', 'today'], referral: ['#settings', 'settings'], feedback: ['#settings', 'settings'], admin: ['#dashboard', 'today'], mail: ['#admin', 'admin'] };
  const IC = {
    news: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>',
    back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>',
    prog: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.6"/></svg>',
    settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
    sub: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="M3 10h18M7 15h4"/></svg>',
    ref: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="8" width="17" height="12" rx="2"/><path d="M12 8v12M3.5 12h17M12 8c-1.5-3-5-3.5-5-1.2C7 8 9.5 8 12 8zm0 0c1.5-3 5-3.5 5-1.2C17 8 14.5 8 12 8z"/></svg>',
    fb: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 0 1-11.8 7L4 20l1-4.2A8 8 0 1 1 20 12z"/></svg>',
    help: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.2-2.4 3.6M12 17h.01"/></svg>',
    mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="m4 7 8 6 8-6"/></svg>',
    admin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20c-.5-2.6-2-4.3-4-5"/></svg>',
    out: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l5-5-5-5M15 12H4"/></svg>',
  };

  const OVERLAYS = '#gSheet.open, .evp.open, #navMenu.open, .gd-help-ov.open, #tkSlide.open, #cmd:not([hidden]), .wr, .sheet:not([hidden])';

  /* ───────────── segmented controls + back chevron (drawn with each page) ───────────── */
  function chrome() {
    const v = route().v, main = document.getElementById('main'); if (!main) return;
    // (10 Nov., brief « produit final » step 3) a trade's or an account's page: no floating AI button on a phone (it covered the
    // cards); the AI stays in the search and the « ⋯ » menu
    document.body.classList.toggle('nav-detail', v === 'trade' || v === 'account');
    if ((v === 'trade' || v === 'account') && document.body.classList.contains('ask-on') && typeof askToggle === 'function') {
      const pop = main.querySelector('details.menu > .menu-pop');
      if (pop && !pop.querySelector('.nav-ask-m')) {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'nav-ask-m'; b.setAttribute('data-noi18n', '');
        b.textContent = ({ en: 'Ask Sweep AI', fr: 'Demander à Sweep AI', es: 'Preguntar a Sweep AI' })[LANG] || 'Ask Sweep AI';
        b.addEventListener('click', () => { const d = b.closest('details'); if (d) d.open = false; askToggle(true); });
        pop.prepend(b);
      }
    }
    const g = GROUP[v];
    if (g && !main.querySelector('.nav-seg')) {
      const el = document.createElement('div'); el.className = 'seg nav-seg'; el.setAttribute('role', 'tablist'); el.setAttribute('data-noi18n', '');
      el.innerHTML = SEG[g].map(([r, k]) => `<a href="#${r}" role="tab" class="${r === v ? 'on' : ''}" aria-selected="${r === v}">${t()[k]}</a>`).join('');
      main.prepend(el);
    }
    const NT = { en: 'Add a trade (N)', fr: 'Ajouter un trade (N)', es: 'Añadir una operación (N)' };
    // (2 Nov., audit « transfuge » G2) one name for the action, everywhere: « Add a trade » (it was « New trade » here)
    const NA = { en: 'Add a trade', fr: 'Ajouter un trade', es: 'Añadir una operación' }, na = NA[LANG] || NA.en;
    document.querySelectorAll('aside.side .new, #bottomnav .plus').forEach((b) => { b.title = NT[LANG] || NT.en; b.setAttribute('aria-keyshortcuts', 'N'); b.setAttribute('aria-label', na); if (b.dataset.label) b.dataset.label = na; const l = b.querySelector('.lbl'); if (l && l.textContent !== na) { l.setAttribute('data-noi18n', ''); l.textContent = na; } });
    const p = PARENT[v];
    if (p && !main.querySelector('.nav-back') && !main.querySelector('.crumbs, .bc, .back-link')) {
      const has = [...main.querySelectorAll('a')].slice(0, 6).some((a) => /^\s*[‹<]/.test(a.textContent) || a.classList.contains('crumb'));
      if (!has) {
        const a = document.createElement('a'); a.className = 'nav-back'; a.href = p[0]; a.setAttribute('data-noi18n', '');
        a.innerHTML = `${IC.back}<span>${t()[p[1]]}</span>`; main.prepend(a);
      }
    }
    topBack(main, p);
  }
  /* (1 Nov., brief visuel iOS 27.2, C1) one back link, as on iOS: « ‹ Trades » in blue, above the large title, on the left, the
     same on every page; the page's own (« ‹ Trades » grey on a trade, « ‹ Accounts » blue under the title…) is hidden, its
     place and target kept */
  function topBack(main, p) {
    const top = document.querySelector('.main-wrap .top'); if (!top) return;
    // (2 Nov.) on a phone the link is in the header row itself, in place of the logo: under it (inside the title's block) the
    // header's frosted glass covered it and it looked faded
    const side = matchMedia('(max-width:860px)').matches && document.querySelector('aside.side'), host = side || top;
    let tb = document.querySelector('.top-back');
    if (tb && tb.parentElement !== host) tb.remove(), tb = null;
    const own = main.querySelector(':scope > .nav-back, .tr-top > a.back');
    const href = own ? own.getAttribute('href') : '';
    const label = own ? own.textContent.replace(/^\s*[‹<]\s*/, '').trim() : '';
    if (!tb) { tb = document.createElement('a'); tb.className = 'top-back'; tb.setAttribute('data-noi18n', ''); host.prepend(tb); }
    // a page without a parent keeps the row, empty (as iOS's navigation bar above a large title): the header has one height on
    // every page, the content never moves when going from a tab to a sub-page
    // (2 Nov.) « ‹ Today » is not a way back: Today is a tab, always in the tab bar (and the sidebar); the link showed over the
    // logo on a phone, on Settings, News, My progress… — only a real sub-page (a trade, an account) has one
    if (own && href === '#dashboard') own.classList.add('sw-own-back');
    if (!href || !label || href === '#dashboard') { tb.classList.add('off'); tb.removeAttribute('href'); tb.setAttribute('aria-hidden', 'true'); tb.tabIndex = -1; document.body.classList.remove('sw-top-back'); return; }
    tb.classList.remove('off'); tb.removeAttribute('aria-hidden'); tb.removeAttribute('tabindex');
    const html = `${IC.back}<span>${esc(label)}</span>`;
    if (tb.getAttribute('href') !== href) tb.setAttribute('href', href);
    if (tb._h !== html) { tb.innerHTML = html; tb._h = html; }
    own.classList.add('sw-own-back'); document.body.classList.add('sw-top-back');
  }

  /* ───────────── avatar menu (same on phone and desktop) ───────────── */
  const PL = { en: '{p} · {d} days left', fr: '{p} · {d} jours restants', es: '{p} · quedan {d} días' };
  function planLine() {
    try {
      const st = typeof BILL !== 'undefined' && BILL.on && BILL.st; if (!st) return '';
      const name = { free: 'Free', pro: 'Pro', elite: 'Elite' }[st.plan] || '';
      const tr = st.trial && st.trial.days_left != null ? (PL[LANG] || PL.en).replace('{p}', name).replace('{d}', st.trial.days_left) : name;
      return tr ? `<small class="nav-plan ${st.plan || ''}">${esc(tr)}</small>` : '';
    } catch (e) { return ''; }
  }
  function openMenu(anchor) {
    closeMenu(true);
    const x = t(), admin = S.me && S.me.is_admin;
    const el = document.createElement('div'); el.id = 'navMenu'; el.className = 'nav-menu'; el.setAttribute('data-noi18n', '');
    const item = (k, ic, label, cls = '') => `<button type="button" role="menuitem" class="${cls}" data-navm="${k}">${ic}<span>${label}</span></button>`;
    el.innerHTML = `<div class="nav-menu-bg" data-navm="close"></div><div class="nav-menu-panel" role="menu">
      ${S.me ? ((nm) => `<button type="button" class="nav-menu-who" data-navm="plan"><span class="av">${esc(nm.slice(0, 1).toUpperCase())}</span><span class="nm"><b>${esc(nm)}</b>${planLine()}</span></button>`)(String(S.me.first_name || S.me.username || '').trim() || S.me.username) : ''}
      <div class="nav-mg">${item('prog', IC.prog, x.prog)}${item('news', IC.news, x.news)}</div>
      <div class="nav-mg">${item('settings', IC.settings, x.settings)}</div>
      <div class="nav-mg">${item('help', IC.help, x.help)}</div>
      ${admin ? `<div class="nav-mg">${item('admin', IC.admin, x.admin)}${item('mail', IC.mail, x.mail)}</div>` : ''}
</div>`;   // (31 Oct., fluidity 14) 4 lines: My progress, What's new, Settings, Help — Referral, Give feedback and Log out are in Settings
    document.body.append(el);
    const r = anchor && anchor.getBoundingClientRect(), panel = el.querySelector('.nav-menu-panel');
    if (r && !window.SW_MQ.matches) { panel.style.left = Math.max(12, r.left) + 'px'; panel.style.bottom = Math.max(12, innerHeight - r.top + 8) + 'px'; panel.style.maxHeight = (r.top - 20) + 'px'; panel.classList.add('up'); }
    requestAnimationFrame(() => el.classList.add('open'));
    overlayOpened();
    const first = panel.querySelector('button'); if (first && kbdUser) first.focus({ preventScroll: true });
  }
  function closeMenu(now) {
    const el = document.getElementById('navMenu'); if (!el) return;
    const back = el.contains(document.activeElement) ? document.querySelector('aside.side .who') : null;   // focus returns to the avatar
    el.classList.remove('open'); if (now) el.remove(); else setTimeout(() => el.remove(), 200);
    if (back && back.offsetParent !== null) back.focus({ preventScroll: true });
  }

  document.addEventListener('click', (e) => {
    const who = e.target.closest && e.target.closest('[data-nav="menu"]');
    if (who) { e.preventDefault(); openMenu(who); return; }
    const pr = e.target.closest && e.target.closest('[data-nav="progress"]');
    if (pr) { e.preventDefault(); window.SweepGame && SweepGame.open('hub'); return; }
    const m = e.target.closest && e.target.closest('[data-navm]');
    if (m) {
      const k = m.dataset.navm; closeMenu();
      if (k === 'prog') window.SweepGame && SweepGame.open('hub');
      else if (k === 'help') window.SweepGuide && SweepGuide.open();
      else if (k === 'news') window.SweepNews && SweepNews.open();
      else if (k !== 'close') location.hash = '#' + k;
      return;
    }
    if (e.target.closest && e.target.closest('#navMenu [data-act="logout"]')) closeMenu(true);
  });
  let lastTrigger = null, trapped = null, kbdUser = false;
  addEventListener('keydown', (e) => { if (e.key === 'Tab' || e.key === 'Enter' || e.key === ' ' || String(e.key || '').startsWith('Arrow')) kbdUser = true; }, true);   // (a browser's autofill sends keydown without a key: Admin › Errors, 13 and 8 Oct.)
  addEventListener('pointerdown', () => { kbdUser = false; }, true);
  document.addEventListener('focusin', (e) => { const top = [...document.querySelectorAll(OVERLAYS)].pop(); if (!top) lastTrigger = e.target; });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { if (document.getElementById('navMenu')) closeMenu(); else if (document.querySelector(OVERLAYS)) { e.preventDefault(); closeTop(); } return; }
    if (e.key === 'Tab') {
      const top = [...document.querySelectorAll(OVERLAYS)].pop(); if (!top) return;
      const f = [...top.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select, textarea, [tabindex]:not([tabindex="-1"])')].filter((x) => x.offsetParent !== null);
      if (!f.length) return;
      const i = f.indexOf(document.activeElement);
      if (e.shiftKey && (i <= 0)) { e.preventDefault(); f[f.length - 1].focus(); } else if (!e.shiftKey && (i === -1 || i === f.length - 1)) { e.preventDefault(); f[0].focus(); }
    }
    if ((e.key === 'ArrowRight' || e.key === 'ArrowLeft') && e.target.matches && e.target.matches('[role=tab]')) {
      const tabs = [...e.target.parentElement.querySelectorAll('[role=tab]')], i = tabs.indexOf(e.target);
      const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length]; if (n) { e.preventDefault(); n.focus(); n.click(); }
    }
  });
  // focus goes back to whatever opened the layer
  new window.SweepMO(() => {
    const top = [...document.querySelectorAll(OVERLAYS)].pop();
    if (top && trapped !== top) { trapped = top; const f = top.querySelector('[autofocus], .nav-menu-panel button, button, a[href], input'); if (f && kbdUser && !top.contains(document.activeElement)) setTimeout(() => f.focus({ preventScroll: true }), 60); }
    else if (!top && trapped) { trapped = null; if (lastTrigger && document.contains(lastTrigger)) lastTrigger.focus({ preventScroll: true }); }
  }).observe(document.body, { childList: true, attributes: true, attributeFilter: ['class'] });

  /* ───────────── aliases (#today, #stats, #subscription, #progress) ───────────── */
  const ALIAS = { today: 'dashboard', stats: 'analytics', subscription: 'plan', abonnement: 'plan', progress: 'dashboard', progression: 'dashboard' };
  function alias() {
    const h = decodeURIComponent(location.hash.slice(1)).split('/')[0];
    if (!ALIAS[h]) return false;
    history.replaceState(history.state, '', '#' + ALIAS[h]);
    render();
    if (h === 'progress' || h === 'progression') setTimeout(() => window.SweepGame && SweepGame.open('hub'), 400);
    return true;
  }
  addEventListener('hashchange', alias);

  /* ───────────── Android back / iOS swipe: close the open sheet first, then go up one level ───────────── */
  let guard = false;
  function overlayOpened() { if (!history.state || !history.state.navOv) history.pushState({ navOv: 1 }, '', location.href); }
  function closeTop() {
    const el = [...document.querySelectorAll(OVERLAYS)].pop(); if (!el) return false;
    if (el.id === 'navMenu') closeMenu();
    else if (el.id === 'tkSlide' && typeof closeTicket === 'function') closeTicket();
    else if (el.id === 'cmd' && typeof closeCmd === 'function') closeCmd();
    else if (el.id === 'shPanel' && typeof closeShare === 'function') closeShare();   // its veil too (audit of 16 Oct.: the veil stayed, the app was stuck)
    else if (el.classList.contains('gd-help-ov')) { const x = el.querySelector('.gd-x'); x && x.click(); }
    else if (el.classList.contains('wr')) { const x = el.querySelector('.wr-x'); x && x.click(); }
    else { const x = el.querySelector('[data-g="close"], [data-act="close-drawer"], .sheet-bg'); if (x) x.click(); else el.classList.remove('open'); }
    return true;
  }
  let backPending = false;   // history.back() is asynchronous: never ask twice before the first one has happened
  // a link inside a sheet (« Open the trade », a day…): the sheet closes first (its history step is removed),
  // then we go to the page — otherwise the removal of that step would cancel the navigation and leave us on Today
  let pendingNav = null, pendingT = 0;
  const goPending = () => { if (!pendingNav) return; const h = pendingNav; pendingNav = null; clearTimeout(pendingT); if (location.hash !== h) location.hash = h; };
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('a[href^="#"]'); if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey) return;
    if (!a.closest(OVERLAYS)) return;
    e.preventDefault();
    pendingNav = a.getAttribute('href'); clearTimeout(pendingT); pendingT = setTimeout(goPending, 450);
    setTimeout(() => { const el = a.closest(OVERLAYS); if (el && document.contains(el)) closeTop(); }, 0);   // close it if nothing else did
  }, true);
  addEventListener('popstate', () => { backPending = false; if (guard) { guard = false; setTimeout(goPending, 0); return; } if (document.querySelector(OVERLAYS)) closeTop(); setTimeout(goPending, 0); });
  // a sheet opened anywhere gets a history step, so « back » closes it instead of leaving the page
  new window.SweepMO(() => {
    const open = !!document.querySelector(OVERLAYS);
    if (open) overlayOpened();
    else if (history.state && history.state.navOv && !backPending) { guard = true; backPending = true; history.back(); }
  }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'hidden'] });


  /* ───────────── search also finds every feature and setting (labels follow the glossary, keywords in EN/FR/ES) ───────────── */
  const FIND = [
    { l: { en: 'My progress', fr: 'Ma progression', es: 'Mi progreso' }, k: 'progression progress progreso rang rank rango streak racha', go: () => SweepGame.open('hub') },
    // (29 Oct., searches that found nothing in Admin: « routine », « coach », « appeareance », « how to insert my setups »)
    { l: { en: 'My routine (checklist, setups, risk rules)', fr: 'Ma routine (checklist, setups, règles de risque)', es: 'Mi rutina (checklist, setups, reglas de riesgo)' }, k: 'routine rutina checklist setup setups insert inserer insertar ajouter add anadir create creer crear regles rules reglas risque risk riesgo parcours gameplan verrouillage lock bloqueo discipline disciplina', go: () => { try { const o = new Set(JSON.parse(sessionStorage.getItem('sw.sgd') || '[0]')); o.add(1); sessionStorage.setItem('sw.sgd', JSON.stringify([...o])); } catch (e) { /* private mode */ } location.hash = '#settings'; } },
    { l: { en: 'Your coach', fr: 'Ton coach', es: 'Tu coach' }, k: 'coach coaching entraineur entrenador conseil conseils advice consejo consejos lecon lesson leccion', go: '#dashboard' },
    { l: { en: 'Appearance (theme, language)', fr: 'Apparence (thème, langue)', es: 'Apariencia (tema, idioma)' }, k: 'appearance appeareance apearance apparence apariencia theme tema sombre dark clair light oscuro claro mode langue language idioma', go: '#settings' },
    { l: { en: 'Weekly recap', fr: 'Bilan de la semaine', es: 'Resumen semanal' }, k: 'weekly recap bilan semaine resumen semanal', go: () => SweepGame.open('weekly') },
    { l: { en: 'Plan of the day', fr: 'Plan du jour', es: 'Plan del día' }, k: 'plan du jour plan of the day plan del dia biais bias sesgo', go: () => SweepGame.open('plan') },
    { l: { en: 'Daily review', fr: 'Revue du jour', es: 'Revisión del día' }, k: 'daily review revue du jour revision del dia', go: () => SweepGame.open('review') },
    { l: { en: 'Badges', fr: 'Badges', es: 'Insignias' }, k: 'badge badges insignia insignias collection coleccion', go: () => SweepGame.open('hub') },
    { l: { en: 'Subscription', fr: 'Abonnement', es: 'Suscripción' }, k: 'subscription abonnement suscripcion forfait billing facturation facturacion pro elite upgrade', go: '#plan' },
    { l: { en: 'Export all my data (ZIP)', fr: 'Exporter toutes mes données (ZIP)', es: 'Exportar todos mis datos (ZIP)' }, k: 'export exporter exportar zip donnees data datos sauvegarde backup', go: '#settings' },
    { l: { en: 'Import trades (Tradovate, Rithmic, TopstepX)', fr: 'Importer des trades (Tradovate, Rithmic, TopstepX)', es: 'Importar operaciones (Tradovate, Rithmic, TopstepX)' }, k: 'import importer importar csv tradovate rithmic topstepx topstep', go: '#import' },
    { l: { en: 'Add a payout', fr: 'Ajouter un payout', es: 'Añadir un payout' }, k: 'ajouter add anadir enregistrer record registrar payout payouts retrait withdrawal retiro demande request solicitud', go: () => { try { sessionStorage.setItem('sw.openPayout', '1'); } catch (e) { /* private mode */ } location.hash = '#payouts'; } },
    { l: { en: 'Add a trade', fr: 'Ajouter un trade', es: 'Añadir una operación' }, k: 'ajouter add anadir nouveau new nuevo trade trades operacion operaciones saisir enter capture screenshot', go: () => { if (typeof openTicket === 'function') openTicket(); } },
    { l: { en: 'My best and worst hours', fr: 'Mes meilleures et pires heures', es: 'Mis mejores y peores horas' }, k: 'heure heures hour hours hora horas moment time pire pires worst peor peores meilleure meilleures best mejor mejores', go: '#analytics/time' },
    { l: { en: 'My money', fr: 'Mon argent', es: 'Mi dinero' }, k: 'argent money dinero payout payouts depenses expenses gastos retrait withdrawal retiro frais fees', go: '#payouts' },
    { l: { en: 'Accounts', fr: 'Comptes', es: 'Cuentas' }, k: 'accounts comptes cuentas compte account cuenta prop drawdown regles rules reglas rouge red rojo limite limit perte loss perdida brule breached', go: '#accounts' },
    { l: { en: 'Economic news', fr: 'Nouvelles économiques', es: 'Noticias económicas' }, k: 'news nouvelles noticias calendrier economique economic calendar calendario economico cpi nfp fomc', go: '#news' },
    { l: { en: 'Stats', fr: 'Stats', es: 'Stats' }, k: 'stats statistiques statistics estadisticas analyses analytics insights analisis', go: '#analytics' },
    { l: { en: 'Calendar', fr: 'Calendrier', es: 'Calendario' }, k: 'calendar calendrier calendario', go: '#calendar' },
    { l: { en: 'Journal', fr: 'Journal', es: 'Diario' }, k: 'journal diario notes notas', go: '#journal' },
    { l: { en: 'Referral', fr: 'Parrainage', es: 'Referidos' }, k: 'referral parrainage referidos inviter invite invitar', go: '#referral' },
    { l: { en: 'Give feedback', fr: 'Donner mon avis', es: 'Dar mi opinión' }, k: 'feedback avis opinion idee idea bug probleme problem', go: '#feedback' },
    { l: { en: 'Settings', fr: 'Réglages', es: 'Ajustes' }, k: 'settings reglages ajustes parametres preferences', go: '#settings' },
    { l: { en: 'Notifications', fr: 'Notifications', es: 'Notificaciones' }, k: 'notifications notificaciones rappels reminders recordatorios', go: '#settings' },
    { l: { en: 'Help', fr: 'Aide', es: 'Ayuda' }, k: 'help aide ayuda guide guia comment how como', go: () => window.SweepGuide && SweepGuide.open() },
    { l: { en: 'Sweep AI', fr: 'Sweep AI', es: 'Sweep AI' }, k: 'ai ia sweep assistant ask demander preguntar question pregunta', go: () => typeof askToggle === 'function' && askToggle(true), when: () => document.body.classList.contains('ask-on') },
  ];
  function askWith(q) {
    if (typeof askToggle !== 'function') return;
    askToggle(true);
    setTimeout(() => { const ta = document.querySelector('#askPanel textarea'); if (ta) { ta.value = q; ta.dispatchEvent(new Event('input', { bubbles: true })); ta.focus(); } }, 420);
  }
  // searches that find nothing are counted (text + language) for the admin dashboard
  let missT = 0, missLast = '';
  function missed(q) {
    const v = String(q).trim().slice(0, 80); if (v.length < 2 || v === missLast) return;
    clearTimeout(missT);
    missT = setTimeout(() => { missLast = v; try { fetch('api/search-miss', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ q: v, lang: LANG }) }).catch(() => {}); } catch (e) { /* offline */ } }, 1500);
  }
  const norm = (v) => String(v || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  /* brief 02 part 9: a question in several words (« comment ajouter un payout », « pourquoi mon compte est rouge ») finds the
     features and the help articles it is about — the search, the help's own search, and Sweep AI when it cannot answer */
  const STOP = new Set('comment pourquoi quoi quel quelle quels quelles est sont mon mes ton tes son ses une des les dans pour avec sur par que qui plus moins faire fait voir how why what which where when does the and for with your you can are this that como por que cual cuales donde cuando mis tus una los las del con para esta este son'.split(' '));
  const tokens = (q) => norm(q).split(/[^a-z0-9]+/).filter((w) => w.length >= 3 && !STOP.has(w));
  const fits = (t, w) => w.length >= 3 && (w.startsWith(t) || (t.length >= 4 && t.startsWith(w)));
  function helpFind(q, n) {
    const ts = tokens(q), s = norm(q).trim(); if (!s) return [];
    const out = [];
    // a question with no word left to search (« how to », « comment ») : the help, never nothing
    if (!ts.length && /^(how|comment|como|why|pourquoi|por que|what|quoi|que)\b/.test(s)) { const h = FIND.find((f) => /^help\b/i.test(f.l.en)); if (h) return [{ sc: 1, kind: 'page', t: h.l[LANG] || h.l.en, run: h.go }]; }
    FIND.forEach((f, i) => {
      if (f.when && !f.when()) return;
      const words = (norm(f.l[LANG] || f.l.en) + ' ' + norm(f.k)).split(/[^a-z0-9]+/);
      let sc = ts.filter((t) => words.some((w) => fits(t, w))).length;
      if (norm(f.l[LANG] || f.l.en).includes(s)) sc += 3;
      if (sc) out.push({ sc: sc + 0.5, i, kind: 'page', t: f.l[LANG] || f.l.en, run: typeof f.go === 'string' ? () => { location.hash = f.go; } : f.go });
    });
    const arts = window.SweepGuide && SweepGuide.list ? SweepGuide.list() : [];
    arts.forEach((a) => {
      const ti = norm(a.title).split(/[^a-z0-9]+/), bo = norm(a.body).split(/[^a-z0-9]+/);
      const sc = ts.filter((t) => ti.some((w) => fits(t, w))).length + ts.filter((t) => bo.some((w) => fits(t, w))).length * 0.2;   // (a page first, its help article right after)
      if (sc >= 1) out.push({ sc, kind: 'help', t: a.title, run: () => SweepGuide.article(a.id) });
    });
    return out.sort((x, y) => y.sc - x.sc || (x.i ?? 99) - (y.i ?? 99)).slice(0, n || 6);
  }
  window.SweepHelp = { find: helpFind, tokens, norm };
  if (typeof cmdItems === 'function') {
    const orig = cmdItems;
    cmdItems = function (q) {
      const base = orig.apply(this, arguments), s = norm(q).trim();
      if (!s) return base;
      const g = { en: 'Features', fr: 'Fonctions', es: 'Funciones' }[LANG] || 'Features', gh = { en: 'Help', fr: 'Aide', es: 'Ayuda' }[LANG] || 'Help';
      const hits = helpFind(q, 8).map((h) => ({ g: h.kind === 'help' ? gh : g, t: h.t, run: h.run }));   // best first, the help articles too
      const seen = new Set(hits.map((h) => norm(h.t)));
      const all = [...hits, ...base.filter((b) => !seen.has(norm(b.t)))];
      if (!all.length) missed(q);
      // last line, always: ask Sweep the same question (plan limits apply as usual)
      if (typeof AI !== 'undefined' && AI && AI.on) {
        const qq = String(q).trim().slice(0, 300), L2 = { en: ['Sweep AI', 'Ask Sweep: « {q} »'], fr: ['Sweep AI', 'Demander à Sweep : « {q} »'], es: ['Sweep AI', 'Preguntar a Sweep: « {q} »'] }[LANG] || ['Sweep AI', 'Ask Sweep: « {q} »'];
        all.push({ g: L2[0], t: L2[1].replace('{q}', qq), run: () => askWith(qq) });
      }
      return all;
    };
  }


  /* ───────────── Today: main card first, then checklist, KPIs (day + week), rank + streak, economic context ───────────── */
  const TD = {
    en: { week: 'This week', net: 'Net P&L', trades: 'Trades', win: 'Win rate', all: 'See my stats', streak: 'Streak', ctx: 'Economic context', more: 'See all', days: '{n} days', best: 'best {n}' },
    fr: { week: 'Cette semaine', net: 'P&L net', trades: 'Trades', win: 'Taux de réussite', all: 'Voir mes stats', streak: 'Streak', ctx: 'Contexte économique', more: 'Tout voir', days: '{n} jours', best: 'record {n}' },
    es: { week: 'Esta semana', net: 'P&L neto', trades: 'Operaciones', win: 'Tasa de acierto', all: 'Ver mis stats', streak: 'Racha', ctx: 'Contexto económico', more: 'Ver todo', days: '{n} días', best: 'récord {n}' },
  };
  const td = () => TD[LANG] || TD.en;
  const KT = {
    en: { day: 'Day', week: 'Week', net: 'Net P&L', trades: 'Trades', win: 'Win rate', all: 'See my stats' },
    fr: { day: 'Jour', week: 'Semaine', net: 'P&L net', trades: 'Trades', win: 'Taux de réussite', all: 'Voir mes stats' },
    es: { day: 'Día', week: 'Semana', net: 'P&L neto', trades: 'Operaciones', win: 'Tasa de acierto', all: 'Ver mis stats' },
  };
  const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  function byDecision(list) {   // trades copied on several accounts are one trade decision
    const n1 = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0));
    // counted like everywhere else (mergeCopies, audit of 16 Oct.): the main copy's P&L, once (before: the copies added up)
    if (typeof mergeCopies === 'function') return mergeCopies(list).map((t) => ({ t, n: (t._copies || [t]).length, net: n1(t) }));
    const out = [], seen = new Map(), merge = !(typeof S !== 'undefined' && S.settings && S.settings.mergeCopies === false);   // the app's « count a copied trade once » setting
    for (const t of list) {
      const k = (merge && t.copy_group) || t.id;
      if (seen.has(k)) { const g = seen.get(k); g.n++; g.net += n1(t); continue; }
      const g = { t, n: 1, net: n1(t) }; seen.set(k, g); out.push(g);
    }
    return out;
  }
  let SELDAY = null;   // phone: the day picked in the strip of the Today card (null = today)
  // today = the current futures session at New York time (from 18:00 ET, the next day's session): same date as the trades
  const etToday = () => (typeof todayStr === 'function' ? todayStr() : ymd(new Date(new Date().toLocaleString('en-US', { timeZone: 'America/New_York' }))));
  function span(tab) {   // the day, or its week (Monday → that day, or Friday for a past week)
    const today = etToday(), d = SELDAY || today, dd = new Date(d + 'T12:00:00');
    if (tab !== 'week') return [d, d];
    const mon = new Date(dd); mon.setDate(dd.getDate() - ((dd.getDay() + 6) % 7)); const fri = new Date(mon); fri.setDate(mon.getDate() + 4);
    const to = ymd(fri) < today ? ymd(fri) : today;
    const sunBefore = new Date(mon); sunBefore.setDate(mon.getDate() - 1);   // Sunday-evening trades belong to Monday
    return [ymd(sunBefore), to];
  }
  function kpis(tab) {
    const all = (S.trades || []).filter((x) => (typeof F === 'undefined' || !F.account || F.account === 'all' || x.account_id === F.account) && (!window.mtypeKeep || window.mtypeKeep(x))), real = all.filter((x) => !x.demo), pool = real.length ? real : all;
    if (SELDAY) { const [a, b] = span(tab); const tr = pool.filter((x) => x.date >= a && x.date <= b); const n1 = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0)); const gs = byDecision(tr), w = gs.filter((g) => g.net > 0).length, l = gs.filter((g) => g.net < 0).length; return { net: gs.reduce((a2, g) => a2 + g.net, 0), n: gs.length, win: w + l ? Math.round(w / (w + l) * 100) : null }; }   // sample trades only when there is nothing else; active account filter respected
    const now = new Date(etToday() + 'T12:00:00');   // the current session
    const mon = new Date(now); mon.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    const from = tab === 'week' ? ymd(mon) : ymd(now);
    const tr = pool.filter((x) => x.date >= from && x.date <= ymd(now));
    const gs = byDecision(tr), gw = gs.filter((g) => g.net > 0).length, gl = gs.filter((g) => g.net < 0).length;
    return { net: gs.reduce((a, g) => a + g.net, 0), n: gs.length, win: gw + gl ? Math.round(gw / (gw + gl) * 100) : null };
  }
  /* performance of the period, by account type (« of which Eval +600 · Funded +400 · Live +100 »): a copied trade counts once */
  const MT = { en: { of: 'of which', eval: 'Eval', funded: 'Funded', live: 'Live', personal: 'Personal', simulation: 'Sim', perf: 'Performance', sim: 'Simulated', real: 'Real' },
    fr: { of: 'dont', eval: 'Éval', funded: 'Financé', live: 'Live', personal: 'Perso', simulation: 'Simu', perf: 'Performance', sim: 'Simulé', real: 'Réel' },
    es: { of: 'de lo cual', eval: 'Eval', funded: 'Financiada', live: 'Live', personal: 'Personal', simulation: 'Simu', perf: 'Rendimiento', sim: 'Simulado', real: 'Real' } };
  function perfOf(tab) {
    if (!window.SweepMoney) return null;
    let a, b;
    if (SELDAY) [a, b] = span(tab);
    else { const now = new Date(etToday() + 'T12:00:00'), mon = new Date(now); mon.setDate(now.getDate() - ((now.getDay() + 6) % 7)); a = tab === 'week' ? ymd(mon) : ymd(now); b = ymd(now); }
    return SweepMoney.moneyOf({ from: a, to: b, realOnly: true, mtype: (typeof U !== 'undefined' && U.mtype) || 'all', account: typeof F !== 'undefined' && F.account && F.account !== 'all' ? F.account : '' }).perf;
  }
  function splitHtml(pf) {
    if (!pf) return '';
    const y = MT[LANG] || MT.en, fm = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(0));
    const parts = ['eval', 'funded', 'live', 'personal', 'simulation'].filter((k) => pf.byType[k]).map((k) => `<span class="nav-split-${k}">${y[k]} <b>${fm(pf.byType[k])}</b></span>`);
    return parts.length > 1 || (parts.length === 1 && (pf.byType.live || pf.byType.personal)) ? `<p class="nav-split" data-noi18n>${y.of} ${parts.join(' · ')}</p>` : '';
  }
  function kpiHtml(tab) {
    const x = KT[LANG] || KT.en, k = kpis(tab);
    const pf = perfOf(tab); if (pf) k.net = pf.total;   // the same performance as Stats: a copied trade counts once
    const fmt = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));   // same formatter as Stats and Trades
    return `<div class="nav-kpi-g"><div><small>${x.net} ${window.SweepTypeTag ? SweepTypeTag() : ''}</small><b class="${k.net > 0 ? 'pos' : k.net < 0 ? 'neg' : ''}">${fmt(k.net)}</b></div><div><small>${x.trades}</small><b>${k.n}</b></div><div><small>${x.win}</small><b>${k.win == null || k.n < 5 ? '—' : k.win + ' %'}</b></div></div>${splitHtml(pf)}`;   // (2 Nov., analyse débutant C5) « — » under 5 trades, as Stats (« 0 % » after one trade)
  }
  const TL = { en: { none_d: 'No trade today yet.', none_w: 'No trade this week yet.', all: 'See all ›', tolog: 'Checklist to do', perf: 'Performance' },
    fr: { none_d: 'Aucun trade aujourd’hui pour l’instant.', none_w: 'Aucun trade cette semaine pour l’instant.', all: 'Tout voir ›', tolog: 'Checklist à faire', perf: 'Performance' },
    es: { none_d: 'Aún no hay operaciones hoy.', none_w: 'Aún no hay operaciones esta semana.', all: 'Ver todo ›', tolog: 'Checklist pendiente', perf: 'Rendimiento' } };
  function periodTrades(tab) {
    const all = (S.trades || []).filter((x) => (typeof F === 'undefined' || !F.account || F.account === 'all' || x.account_id === F.account) && (!window.mtypeKeep || window.mtypeKeep(x))), real = all.filter((x) => !x.demo), pool = real.length ? real : all;
    if (SELDAY) { const [a, b] = span(tab); return pool.filter((x) => x.date >= a && x.date <= b).sort((p, q) => ((q.date || '') + (q.entry_time || '')).localeCompare((p.date || '') + (p.entry_time || ''))); }
    const now = new Date(etToday() + 'T12:00:00'), mon = new Date(now); mon.setDate(now.getDate() - ((now.getDay() + 6) % 7));   // the current session
    const from = tab === 'week' ? ymd(mon) : ymd(now);
    return pool.filter((x) => x.date >= from && x.date <= ymd(now)).sort((a, b) => ((b.date || '') + (b.entry_time || '')).localeCompare((a.date || '') + (a.entry_time || '')));
  }
  function tradesHtml(tab) {
    const x = TL[LANG] || TL.en, list = periodTrades(tab), n1 = (t) => (typeof tNet === 'function' ? tNet(t) : (t.pnl_c || 0) - (t.fees_c || 0));
    if (!list.length) return `<p class="nav-empty">${tab === 'week' ? x.none_w : x.none_d}</p>`;
    const max = window.SW_MQ.matches ? 5 : 8, groups = byDecision(list);
    const COPY = { en: 'copy traded on {n} accounts', fr: 'copié sur {n} comptes', es: 'copiado en {n} cuentas' };
    const toLog = new Set();   // (31 Oct., B5) « Checklist to do » once a day: on its last trade without one (newest first here)
    const rows = groups.slice(0, max).map((g) => {
      const t = g.t, net = g.net, unj = !t.notes && !(t.discipline && Object.keys(t.discipline).length) && !toLog.has(t.date) && !!toLog.add(t.date);
      // (29 Oct., tour T5) the same line for every trade, an evening one too: the clock time, then the setup (the trade's page says
      // « session of Oct 8 · entered on the 7th at 23:36 »; here it ran past the row)
      const when = tab === 'week' ? `${typeof fdate === 'function' ? fdate(t.date, { weekday: 'short' }) : t.date} · ${(t.entry_time || '').slice(0, 5)}` : (t.entry_time || '').slice(0, 5);
      return `<a class="nav-tr" href="#trade/${esc(t.id)}"><span class="nav-tr-d ${t.direction === 'short' ? 's' : 'l'}">${t.direction === 'short' ? 'S' : 'L'}</span>
        <span class="nav-tr-m"><b>${esc(t.instrument || '')} · ${esc(String(t.contracts || ''))}${g.n > 1 ? ` <em class="nav-tr-copy" title="${(COPY[LANG] || COPY.en).replace('{n}', g.n)}" aria-label="${(COPY[LANG] || COPY.en).replace('{n}', g.n)}">+${g.n - 1}</em>` : ''}</b><small>${esc(when)}${t.setup ? ' · ' + esc(t.setup) : ''}</small></span>
        ${unj ? `<span class="nav-tolog">${x.tolog}</span>` : ''}<span class="nav-tr-p ${net > 0 ? 'pos' : net < 0 ? 'neg' : ''}">${typeof money === 'function' ? money(net) : net}</span></a>`;
    }).join('');
    return `<div class="nav-trs">${rows}</div>${groups.length > max ? `<a class="nav-more" href="#trades">+${groups.length - max} · ${x.all}</a>` : ''}`;
  }
  let DESK_TAB = 'day';   // computer: the tab shown by the performance card (the news card follows it)
  // the account-type selector on Today: once the trader has two types of accounts, or a filter set (never a hidden filter)
  function typeSeg() {
    if (!window.SweepTypeSeg) return '';
    const set = typeof U !== 'undefined' && U.mtype && U.mtype !== 'all';
    const live = (S.accounts || []).filter((a) => a.status !== 'archived'), own = live.filter((a) => !a.demo);   // (the sample accounts count while there is no real one)
    const kinds = new Set((own.length ? own : live).map((a) => (typeof moneyTypeOf === 'function' ? moneyTypeOf(a) : a.money_type)));
    return set || kinds.size >= 2 ? SweepTypeSeg() : '';
  }
  function kpiCard() {
    const x = KT[LANG] || KT.en; let tab = 'day'; try { tab = localStorage.getItem('sw.kpiTab') === 'week' ? 'week' : 'day'; } catch (e) { /* private mode */ }
    if (tab === 'day' && kpis('day').n === 0 && !window.SW_MQ.matches) tab = 'week';   // computer: nothing today → the week (the phone shows the day with its news)
    if (window.SW_MQ.matches) return feedCard(tab);
    DESK_TAB = tab;
    return `<section class="surface nav-kpi nav-card d-perf" data-noi18n><div class="nav-kpi-h"><div class="seg nav-kseg" role="tablist"><button type="button" role="tab" aria-selected="${tab === 'day'}" data-kt="day" class="${tab === 'day' ? 'on' : ''}">${x.day}</button><button type="button" role="tab" aria-selected="${tab === 'week'}" data-kt="week" class="${tab === 'week' ? 'on' : ''}">${x.week}</button></div>${typeSeg()}<a class="nav-all" href="#trades">${(TL[LANG] || TL.en).all}</a></div><div class="nav-kpi-b">${kpiHtml(tab)}</div><div class="nav-kpi-t">${tradesHtml(tab)}</div></section>`;
  }
  /* ───── phone: one card for the day — scroll the days (P&L, news dot), see the day's numbers, releases and trades ───── */
  const FD = { en: { news: 'Releases', none: 'No important US release.', loading: 'Loading the releases…', fc: 'Fcst', act: 'Act', cal: 'Calendar ›', jr: 'Journal ›', all: 'All ›' }, fr: { news: 'Annonces', none: 'Aucune annonce américaine importante.', loading: 'Chargement des annonces…', fc: 'Prév.', act: 'Réel', cal: 'Calendrier ›', jr: 'Journal ›', all: 'Tout voir ›' }, es: { news: 'Publicaciones', none: 'Sin publicaciones importantes de EE. UU.', loading: 'Cargando publicaciones…', fc: 'Prev.', act: 'Real', cal: 'Calendario ›', jr: 'Diario ›', all: 'Ver todo ›' } };
  // (1 Nov., brief dans le temps B3) the strip starts on the trader's first day — the session of the sign-up, or the first trade when
  // imported ones are older —, not three empty weeks before he was there (still 3 weeks at most)
  function firstDay() {
    const c = S.me && S.me.created_at; let f = '';
    if (c != null && c !== '') { const ms = /^\d+$/.test(String(c)) ? +c * 1000 : Date.parse(String(c).replace(' ', 'T') + (/[zZ]$|[+-]\d\d:?\d\d$/.test(String(c)) ? '' : 'Z')); if (isFinite(ms)) f = new Date(ms + 216e5).toLocaleDateString('en-CA', { timeZone: 'America/New_York' }); }
    (S.trades || []).forEach((t) => { if (t.date && (!f || t.date < f)) f = t.date; });
    return f;
  }
  function stripDays() {
    const today = etToday(), out = [], t0 = new Date(today + 'T12:00:00'), f = firstDay();
    for (let i = -21; i <= 7; i++) { const d = new Date(t0); d.setDate(t0.getDate() + i); if (d.getDay() === 0 || d.getDay() === 6) continue; const k = ymd(d); if (f && k < f && k < today) continue; out.push(k); }
    return out;
  }
  function feedStrip() {
    const days = stripDays(), today = etToday(), sel = SELDAY || today;
    econFor(days[0], days[days.length - 1]);
    const once = (l) => (typeof mergeCopies === 'function' ? mergeCopies(l) : l);   // a copied trade counts once (audit of 16 Oct.)
    const tr = pool(), byDay = typeof dayMap === 'function' ? dayMap(once(tr.filter((t) => t.date >= days[0]))) : new Map();
    const short = (c) => (typeof moneyShort === 'function' ? moneyShort(c) : (c / 100).toFixed(0));
    return days.map((k) => {
      const d = new Date(k + 'T12:00:00'), day = byDay.get ? byDay.get(k) : null, net = day ? day.net : null;
      const hi = typeof ECON !== 'undefined' && ECON.days[k] ? ECON.days[k].some((e) => e.impact === 'high') : false;
      const wd = d.toLocaleDateString(LANG === 'en' ? 'en-US' : LANG === 'es' ? 'es-ES' : 'fr-CA', { weekday: 'short' }).replace('.', '');
      return `<button type="button" class="nav-fd ${k === sel ? 'sel' : ''} ${k === today ? 'today' : ''} ${k > today ? 'fut' : ''} ${net == null ? '' : net > 0 ? 'p' : net < 0 ? 'n' : 'z'}" data-fd="${k}"><small>${wd}</small><b>${d.getDate()}</b><span class="nav-fd-p">${net != null ? short(net) : ''}</span>${hi ? '<i class="nav-fd-e" aria-hidden="true"></i>' : ''}</button>`;
    }).join('');
  }
  function feedNews() {
    const x = FD[LANG] || FD.en, k = SELDAY || etToday(), ev = econFor(k);
    const hd = `<div class="nav-fh"><b>${x.news}</b><a href="#news">${x.all}</a></div>`;
    if (ev == null) return `<div class="nav-fnews">${hd}<small class="muted">${x.loading}</small></div>`;
    const list = ev.filter((e) => e.impact === 'high' || e.impact === 'medium');
    if (!list.length) return `<div class="nav-fnews">${hd}<small class="muted">${x.none}</small></div>`;
    const now = Date.now() / 1000;
    return `<div class="nav-fnews">${hd}${list.map((e) => { const hm = typeof etStr === 'function' ? etStr(e.ts).slice(11, 16) : ''; const past = e.ts <= now && e.actual != null && e.actual !== '';
      return `<button type="button" class="nav-fev ${e.impact}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-fev-t">${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-fev-n">${esc(tr(e.event))}</span>${(/\b(minutes|speech|speaks|testimony|press conference|beige book|statement|remarks)\b/i.test(e.event || '')) ? `<span class="nav-nonum nav-nonum-r" data-noi18n>${({ en: 'No number', fr: 'Sans chiffre', es: 'Sin cifra' })[LANG] || 'No number'}</span>` : `<span class="nav-fev-v nav-ev-v3"><span><small>${x.act || ({ fr: 'Réel', es: 'Real' })[LANG] || 'Act.'}</small><b>${e.actual != null && e.actual !== '' ? esc(String(econL(e.actual))) : '—'}</b></span><span><small>${x.fc || ({ fr: 'Prév.', es: 'Prev.' })[LANG] || 'Fcst'}</small><b>${esc(String(econL(e.forecast || '—')))}</b></span><span><small>${x.prev || ({ fr: 'Préc.', es: 'Ant.' })[LANG] || 'Prev.'}</small><b>${esc(String(econL(e.previous || '—')))}</b></span></span>`}</button>`; }).join('')}</div>`;
  }
  /** Week tab: the week's U.S. releases (Monday to Friday) — past ones dimmed, upcoming ones bright */
  function feedWeekNews() {
    const x = FD[LANG] || FD.en, k = SELDAY || etToday();
    const d0 = new Date(k + 'T12:00:00'); d0.setDate(d0.getDate() - ((d0.getDay() + 6) % 7));
    const days = [...Array(5)].map((_, i) => { const d = new Date(d0); d.setDate(d0.getDate() + i); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; });
    const hd = `<div class="nav-fh"><b>${x.news}</b><a href="#news/week">${x.all}</a></div>`;
    const now = Date.now() / 1000; let loading = false; const rows = [];
    days.forEach((day) => {
      const ev = econFor(day); if (ev == null) { loading = true; return; }
      ev.filter((e) => e.impact === 'high' || e.impact === 'medium').forEach((e) => {
        const hm = typeof etStr === 'function' ? etStr(e.ts).slice(11, 16) : '';
        const wd = new Date(day + 'T12:00:00').toLocaleDateString(LANG === 'en' ? 'en-US' : LANG === 'es' ? 'es-ES' : 'fr-CA', { weekday: 'short' });
        rows.push(`<button type="button" class="nav-fev ${e.impact} ${e.ts < now - 60 ? 'nav-fev-past' : ''}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-fev-t"><small class="nav-fev-d">${esc(wd)}</small> ${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-fev-n">${esc(tr(e.event))}</span>${(/\b(minutes|speech|speaks|testimony|press conference|beige book|statement|remarks)\b/i.test(e.event || '')) ? `<span class="nav-nonum nav-nonum-r" data-noi18n>${({ en: 'No number', fr: 'Sans chiffre', es: 'Sin cifra' })[LANG] || 'No number'}</span>` : `<span class="nav-fev-v nav-ev-v3"><span><small>${({ en: 'Act.', fr: 'Réel', es: 'Real' })[LANG] || 'Act.'}</small><b>${e.actual != null && e.actual !== '' ? esc(String(econL(e.actual))) : '—'}</b></span><span><small>${({ en: 'Fcst', fr: 'Prév.', es: 'Prev.' })[LANG] || 'Fcst'}</small><b>${esc(String(econL(e.forecast || '—')))}</b></span><span><small>${({ en: 'Prev.', fr: 'Préc.', es: 'Ant.' })[LANG] || 'Prev.'}</small><b>${esc(String(econL(e.previous || '—')))}</b></span></span>`}</button>`);
      });
    });
    if (!rows.length) return `<div class="nav-fnews">${hd}<small class="muted">${loading ? x.loading : x.none}</small></div>`;
    return `<div class="nav-fnews nav-fnews-w">${hd}${rows.join('')}</div>`;
  }
  function feedDate() {
    const x = FD[LANG] || FD.en, k = SELDAY || etToday();
    const lab = new Date(k + 'T12:00:00').toLocaleDateString(LANG === 'en' ? 'en-US' : LANG === 'es' ? 'es-ES' : 'fr-CA', { weekday: 'long', day: 'numeric', month: 'long' });
    return `<b>${esc(lab.charAt(0).toUpperCase() + lab.slice(1))}</b><a href="#journal/${k}">${x.jr}</a>`;
  }
  function feedCard(tab) {
    const x = KT[LANG] || KT.en;
    return `<section class="surface nav-kpi nav-card d-perf nav-feed" data-noi18n><div class="nav-kpi-h"><div class="seg nav-kseg" role="tablist"><button type="button" role="tab" aria-selected="${tab === 'day'}" data-kt="day" class="${tab === 'day' ? 'on' : ''}">${x.day}</button><button type="button" role="tab" aria-selected="${tab === 'week'}" data-kt="week" class="${tab === 'week' ? 'on' : ''}">${x.week}</button></div>${typeSeg()}<a class="nav-all" href="#calendar">${(FD[LANG] || FD.en).cal}</a></div>
      ${((fs) => `<div class="nav-fstrip" role="list">${fs}</div>${fs.includes('nav-fd-e') && typeof econLegend === 'function' ? econLegend() : ''}`)(feedStrip())}
      <div class="nav-fdate">${feedDate()}</div>
      <div class="nav-kpi-b">${kpiHtml(tab)}</div><div class="nav-kpi-t">${tradesHtml(tab)}</div></section>`;   // (the releases: the « Now » line and News, SWEEP.md step 3)
  }
  function feedRefresh(card, keepScroll) {
    const tab = (card.querySelector('[data-kt].on') || {}).dataset?.kt || 'day';
    const st = card.querySelector('.nav-fstrip'), sl = st ? st.scrollLeft : 0;
    if (st) { st.innerHTML = feedStrip(); if (keepScroll) st.scrollLeft = sl; }
    const fdt = card.querySelector('.nav-fdate'); if (fdt) fdt.innerHTML = feedDate();
    card.querySelector('.nav-kpi-b').innerHTML = kpiHtml(tab);
    const fn = card.querySelector('.nav-fn'); if (fn) fn.innerHTML = tab === 'day' ? feedNews() : feedWeekNews();
    card.querySelector('.nav-kpi-t').innerHTML = tradesHtml(tab);
  }
  function centerSel(card, smooth, again) {
    const st = card && card.querySelector('.nav-fstrip'), el = st && st.querySelector('.nav-fd.sel'); if (!el) return;
    const left = el.offsetLeft - (st.clientWidth - el.offsetWidth) / 2;
    st.scrollTo({ left: Math.max(0, left), behavior: smooth ? 'smooth' : 'auto' });
    // the first paint can happen under a window or before the fonts (audit of 16 Oct., R23: the strip showed another week):
    // checked again a moment later, unless the trader has moved the strip himself
    if (!again && !st.dataset.navUser) {
      if (!st.dataset.navWatch) { st.dataset.navWatch = '1'; st.addEventListener('pointerdown', () => { st.dataset.navUser = '1'; }, { passive: true }); }
      [700, 2500].forEach((ms) => setTimeout(() => {
        if (st.dataset.navUser || !document.contains(st)) return;
        const r = el.getBoundingClientRect(), b = st.getBoundingClientRect();
        if (b.width && (r.left < b.left || r.right > b.right)) centerSel(card, false, true);
      }, ms));
    }
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-fd]'); if (!b) return;
    const card = b.closest('.nav-feed'); SELDAY = b.dataset.fd === etToday() ? null : b.dataset.fd;
    feedRefresh(card, true); centerSel(card, true);
  });
  // the releases arrive after the card: refresh it in place (and once, put today in the middle)
  new window.SweepMO(() => {
    const card = document.querySelector('#main .nav-feed'); if (!card) return;
    if (!card.dataset.centered) { card.dataset.centered = '1'; requestAnimationFrame(() => centerSel(card, false)); }
  }).observe(document.body, { childList: true, subtree: true });
  setInterval(() => { const card = document.querySelector('#main .nav-feed'); if (!card) return; const k = SELDAY || etToday(); const f = card.querySelector('.nav-fn'); if (f && f.querySelector('.muted') && typeof ECON !== 'undefined' && ECON.days[k]) feedRefresh(card, true); }, 1500);
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-kt]'); if (!b) return;
    if (b.closest('.nav-feed')) { try { localStorage.setItem('sw.kpiTab', b.dataset.kt); } catch (x) { /* private mode */ } const card = b.closest('.nav-feed'); card.querySelectorAll('[data-kt]').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-selected', x === b); }); feedRefresh(card, true); return; }
    try { localStorage.setItem('sw.kpiTab', b.dataset.kt); } catch (x) { /* private mode */ }
    const card = b.closest('.nav-kpi'); card.querySelectorAll('[data-kt]').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-selected', x === b); });
    card.querySelector('.nav-kpi-b').innerHTML = kpiHtml(b.dataset.kt);
    const tl = card.querySelector('.nav-kpi-t'); if (tl) tl.innerHTML = tradesHtml(b.dataset.kt);
    DESK_TAB = b.dataset.kt; const nc = document.querySelector('#main .d-news'); if (nc) nc.outerHTML = newsCard();   // Day → the day's releases, Week → the whole week
  });
  const report = (msg) => { try { fetch('api/client-error', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ msg, page: '#dashboard', src: 'nav.js' }) }).catch(() => {}); } catch (e) { /* offline */ } };
  let reported = false;
  // a suggested question is sent as soon as it is tapped (no « Ask » needed); keeping the focus avoids the keyboard closing and moving the button under the finger
  document.addEventListener('pointerdown', (e) => { if (e.target.closest && e.target.closest('#askPanel [data-ask-q], .sai .sai-chip[data-act="ask-ex"]')) e.preventDefault(); }, true);
  function newsUnderDay(dash) {
    if (!dash || window.SW_MQ.matches) return;
    const col = dash.querySelector('.d-col-a'); if (!col) return;
    const parts = ['.d-perf', '.d-news', '.d-cal', '.d-pay'].map((q) => dash.querySelector(q)).filter((el) => el && !el.dataset.balMoved); if (!parts.length) return;   // a card the balance moved stays where it went (pulling it back made the page jump)
    let box = col.querySelector(':scope > .nav-merge');
    if (!box) { box = document.createElement('section'); box.className = 'surface nav-card nav-merge'; const today = col.querySelector(':scope > .nav-trial') || col.querySelector(':scope > .d-today'); today ? today.after(box) : col.prepend(box); }   // (the end-of-trial card stays right under the day card)
    parts.forEach((el, i) => { if (el.parentElement !== box || box.children[i] !== el) box.insertBefore(el, box.children[i] || null); });
  }
  new window.SweepMO(() => { try { newsUnderDay(document.querySelector('#main .nav-dash')); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
  /* Today grows with the trader (brief 03 step 1): first the routine; the cards come when they have something to show */
  // an account added « already running » (its balance moved by an adjustment) is worth seeing from the first day (R18)
  const running = () => (S.accounts || []).some((a) => !a.demo && a.status !== 'archived' && a.status !== 'closed' && Array.isArray(a.adjustments) && a.adjustments.some((x) => +x.amount_c));
  // (SWEEP.md step 3: the accounts from the first one — their room is the risk allowed; « This month », the news card, the trends
  // and the rank left Today: Trades › Calendar, the « Now » line, Stats, the routine's level)
  const stage = () => { const n = (S.trades || []).length; return { n, perf: n >= 1, acc: true, more: n >= 5, money: (S.payouts || []).length > 0 || (S.expenses || []).length > 0 || !!(n >= 5 && window.SweepRealNet && SweepRealNet.pending && SweepRealNet.pending()) }; };   // (10 Nov., brief « produit final » step 2) « My money » from the first payout or expense, or from 5 trades while its « real net in 1 minute » invitation is due: before, a card of $0
  function deskToday(dash) {
    if (dash && !stage().more) return;   // the rank in the day card: from the 5th trade (« Quick access » removed: audit of 18 Oct.)
    if (!dash || window.SW_MQ.matches) return;
    const rank = dash.querySelector('.d-col-b > .d-rank'), today = dash.querySelector('.d-today');
    if (rank && today) { today.append(rank); dash.classList.add('rank-in'); }
    const pay = dash.querySelector('.d-col-b > .d-pay:not([data-bal-moved])'), cal = dash.querySelector('.d-col-a > .d-cal:not([data-bal-moved])');
    const perf = dash.querySelector('.d-col-a > .d-perf');
    if (pay && perf) { perf.after(pay); dash.classList.add('pay-left'); }
  }

  /* ───────────── the welcome line, as one sentence that continues the title ───────────── */
  function greetLine(el) {
    if (!el) return;
    const h = new Date().getHours(), part = h < 12 ? 0 : h < 18 ? 1 : 2;
    const raw = (S.me && (S.me.first_name || S.me.username)) || '';   // the first name once the profile is complete
    const name = raw ? raw.charAt(0).toUpperCase() + raw.slice(1) : '';
    const loc = LANG === 'en' ? 'en-US' : LANG === 'es' ? 'es-ES' : 'fr-CA';
    const hi = ({ en: ['Good morning', 'Good afternoon', 'Good evening'], fr: ['Bonjour', 'Bon après-midi', 'Bonsoir'], es: ['Buenos días', 'Buenas tardes', 'Buenas noches'] }[LANG] || ['Hello', 'Hello', 'Hello'])[part];
    // the date of the current session (New York, 18:00 rule), the same as the trades and the strip of days — not the device's date
    let day = new Date((typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10)) + 'T12:00:00').toLocaleDateString(loc, { weekday: 'long', month: 'long', day: 'numeric' });
    day = day.charAt(0).toUpperCase() + day.slice(1);
    // three lines: « Good afternoon, Mateo » (small) / Today (title) / the date (small)
    const title = document.querySelector('.main-wrap .top #title'), top = title && title.closest('.top');
    if (title) { const v = hi + (name ? ' ' + name : '') + ' · ' + day; if (title.dataset.hi !== v) title.dataset.hi = v; /* « Bonjour Mateo · Vendredi 9 octobre » (no comma before the dot) */ top.classList.add('nav-3l'); document.documentElement.setAttribute('data-home', ''); }
    el.setAttribute('data-noi18n', '');
    if (el.textContent !== day) el.textContent = day;
    el.classList.add('nav-date');
  }
  function greetOff() {
    if (route().v === 'dashboard') return;
    document.documentElement.removeAttribute('data-home');
    const top = document.querySelector('.main-wrap .top.nav-3l'); if (!top) return;
    top.classList.remove('nav-3l'); const t = top.querySelector('#title'); if (t) delete t.dataset.hi;
  }

  /* ───────────── no weekends: futures do not trade then, so empty Saturdays and Sundays are not shown ───────────── */
  const isWeekend = (k) => { const d = new Date(k + 'T12:00:00'); const w = d.getDay(); return w === 0 || w === 6; };
  const hasTrades = (k) => (S.trades || []).some((t) => t.date === k);
  function hideWeekends() {
    document.querySelectorAll('#main .jlist a[href^="#journal/"], #main .jstrip a[href^="#journal/"]').forEach((a) => {
      const k = a.getAttribute('href').slice(9, 19);
      if (/^\d{4}-\d{2}-\d{2}$/.test(k) && isWeekend(k) && !hasTrades(k)) a.remove();
    });
  }
  // Sunday-evening trades (the futures week opens Sunday 6 pm ET) belong to Monday's session: the calendars count them on Monday
  const nextMonday = (k) => { const d = new Date(k + 'T12:00:00'); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10); };
  (function wrapDayMap(n) {
    if (typeof window.dayMap !== 'function') { if (n < 40) setTimeout(() => wrapDayMap(n + 1), 100); return; }
    if (window.dayMap.__wk) return;
    const orig = window.dayMap;
    const w = function (trades) {
      const list = Array.isArray(trades) ? trades.map((t) => (t && t.date && new Date(t.date + 'T12:00:00').getDay() === 0 ? Object.assign({}, t, { date: nextMonday(t.date) }) : t)) : trades;
      return orig.call(this, list);
    };
    w.__wk = true; window.dayMap = w;
  })(0);
  // the calendars show 5 columns (Mon–Fri); 7 only if a weekend day really holds trades
  (function wrapCal(n) {
    if (typeof window.calDays !== 'function') { if (n < 40) setTimeout(() => wrapCal(n + 1), 100); return; }
    if (window.calDays.__wk) return;
    const w = function (map, month) {
      for (const [k, v] of map.entries ? map.entries() : []) {
        if (!String(k).startsWith(month) || !isWeekend(String(k))) continue;
        const n = v && (Array.isArray(v.trades) ? v.trades.length : Array.isArray(v) ? v.length : 0);
        if (n > 0) return 7;
      }
      return 5;
    };
    w.__wk = true; window.calDays = w;
  })(0);

  /* ───────────── phone: the day in the title row — small rings (next step) and a « + » ───────────── */
  const HD = { en: ['Your day', 'Add a trade'], fr: ['Ta journée', 'Ajouter un trade'], es: ['Tu día', 'Añadir una operación'] };
  function headDay() {
    const top = document.querySelector('.main-wrap .top'), title = top && top.querySelector('#title');
    let w = top && top.querySelector('.nav-hday');
    if (route().v !== 'dashboard' || !window.SW_MQ.matches) { if (w) w.hidden = true; return; }   // phones only
    if (!top || !title) return;
    if (!w) {
      const x = HD[LANG] || HD.en;
      w = document.createElement('div'); w.className = 'nav-hday'; w.setAttribute('data-noi18n', '');
      w.innerHTML = `<button type="button" class="nav-hstreak" data-g="hub"></button><button type="button" class="nav-hring" aria-label="${x[0]}"></button><button type="button" class="nav-hplus" aria-label="${x[1]}" title="${x[1]} (N)"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/></svg></button>`;
      title.after(w);
      w.querySelector('.nav-hplus').addEventListener('click', () => { if (typeof openTicket === 'function') openTicket(null); });
      w.querySelector('.nav-hring').addEventListener('click', () => {
        // the ring does the next step of the day (plan, journal, review…), or opens the day's detail
        const card = document.getElementById('gToday'), cta = card && card.querySelector('.gc-cta');
        const k = cta && cta.dataset.g;
        if (cta && k && k !== 'add' && k !== 'swept' && k !== 'detail') cta.click();
        else { const r = card && card.querySelector('.g-ringbtn'); if (r) r.click(); }
      });
    }
    w.hidden = false;
    syncHeadDay();
  }
  function syncHeadDay() {
    const w = document.querySelector('.main-wrap .top .nav-hday'), card = document.getElementById('gToday');
    if (!w || !card) return;
    const svgEl = card.querySelector('.g-ringbtn svg'), ring = w.querySelector('.nav-hring');
    if (svgEl && svgEl.outerHTML !== ring.dataset.src) { ring.dataset.src = svgEl.outerHTML; const c = svgEl.cloneNode(true); c.removeAttribute('id'); c.querySelectorAll('[id]').forEach((n) => n.removeAttribute('id')); ring.replaceChildren(c); }
    // the streak stays visible: a small candle + number, which opens Progression
    const stEl = card.querySelector('.g-streak'), sb = w.querySelector('.nav-hstreak');
    if (stEl && sb) { const html = stEl.innerHTML; if (sb.dataset.src !== html) { sb.dataset.src = html; sb.innerHTML = html; } sb.hidden = false; sb.classList.toggle('on', stEl.classList.contains('on')); sb.title = stEl.title || ''; sb.setAttribute('aria-label', (stEl.title || 'Streak') + ' ' + stEl.textContent.trim()); }
    const cta = card.querySelector('.gc-cta'), k = cta && cta.dataset.g;
    const pending = !!(k && k !== 'add' && k !== 'swept' && k !== 'detail');
    ring.classList.toggle('due', pending);
    ring.title = cta ? cta.textContent.trim() : '';
    ring.setAttribute('aria-label', ((HD[LANG] || HD.en)[0]) + (cta ? ' · ' + cta.textContent.trim() : ''));
  }
  // the day card is redrawn by the game: keep the small rings in step
  let hdRaf = 0;
  new window.SweepMO((recs) => {
    if (route().v !== 'dashboard' || hdRaf) return;
    if (!recs.some((r) => { const t = r.target; return t.id === 'gToday' || (t.closest && t.closest('#gToday')); })) return;   // only the day card matters
    hdRaf = requestAnimationFrame(() => { hdRaf = 0; syncHeadDay(); });
  }).observe(document.body, { childList: true, subtree: true });

  // the old Overview sections, named one by one (CSS hides them from the first frame; this list is the fallback without :has())
  const OLD = [['day', (x) => x.matches('section.surface') && x.querySelector('.today')], ['accounts', (x) => x.matches('section.sec') && x.querySelector('.acards')],
    ['period', (x) => x.matches('section.sec') && x.querySelector('.fbars, [data-act="period"]')], ['curve', (x) => x.matches('section.sec') && x.querySelector('[data-act="eq"], .chartbox')],
    ['trends', (x) => x.matches('section.sec') && x.querySelector(':scope > .sec-h a[href^="#analytics"]')], ['recent', (x) => x.matches('section.sec') && x.querySelector(':scope > .sec-h a[href="#trades"]')]];
  const HAS = (() => { try { return CSS.supports('selector(:has(*))'); } catch (e) { return false; } })();
  function hideOld(main) {
    if (HAS) return;
    for (const sec of main.querySelectorAll(':scope > section')) for (const [k, test] of OLD) if (test(sec)) { sec.classList.add('nav-old'); sec.dataset.old = k; }
  }

  /* ───────────── Today = the dashboard: one « window » card per section of the app ───────────── */
  const DT = {
    en: { all: 'See all ›', acc: 'Accounts', pay: 'Payouts & expenses', recv: 'Received', exp: 'Expenses', net: 'Net (prop ROI)', last: 'Last payout: {a} · {d}', nopay: 'No payouts or expenses yet.', addpay: 'Log one',
      dd: 'Drawdown room', ready: 'Ready for payout', cal: 'This month', nocal: 'Your month lights up here once you log trades.', notrade: 'Nothing to show yet: log your first trade.', log: 'Log a trade',
      curve: 'Equity curve', recent: 'Recent trades', trends: 'Trend of the week', news: 'Economic news', tolog: 'Checklist to do', swept: 'Swept', moretr: 'Trends appear after a few more trades.' },
    fr: { all: 'Tout voir ›', acc: 'Comptes', pay: 'Payouts et dépenses', recv: 'Reçus', exp: 'Dépenses', net: 'Net (ROI prop)', last: 'Dernier payout : {a} · {d}', nopay: 'Aucun payout ni dépense pour l’instant.', addpay: 'En noter un',
      dd: 'Marge de drawdown', ready: 'Prêt pour le payout', cal: 'Ce mois-ci', nocal: 'Ton mois s’allumera ici dès tes premiers trades.', notrade: 'Rien à afficher pour l’instant : journalise ton premier trade.', log: 'Ajouter un trade',
      curve: 'Courbe de capital', recent: 'Trades récents', trends: 'La tendance de la semaine', news: 'Nouvelles économiques', tolog: 'Checklist à faire', swept: 'Balayée', moretr: 'Les tendances apparaissent après quelques trades de plus.' },
    es: { all: 'Ver todo ›', acc: 'Cuentas', pay: 'Payouts y gastos', recv: 'Recibidos', exp: 'Gastos', net: 'Neto (ROI prop)', last: 'Último payout: {a} · {d}', nopay: 'Aún no hay payouts ni gastos.', addpay: 'Registrar uno',
      dd: 'Margen de drawdown', ready: 'Listo para el payout', cal: 'Este mes', nocal: 'Tu mes se iluminará aquí con tus primeras operaciones.', notrade: 'Nada que mostrar aún: registra tu primera operación.', log: 'Añadir una operación',
      curve: 'Curva de capital', recent: 'Operaciones recientes', trends: 'La tendencia de la semana', news: 'Noticias económicas', tolog: 'Checklist pendiente', swept: 'Barrido', moretr: 'Las tendencias aparecen tras algunas operaciones más.' },
  };
  const dt = () => DT[LANG] || DT.en;
  const head = (title, href, extra = '') => `<div class="nav-ch" role="link" tabindex="0" data-href="${href}"><h2>${esc(title)}${extra ? `<span class="nav-ch-sub">${extra}</span>` : ''}</h2><span class="nav-all">${dt().all}</span></div>`;
  const fmtU = (c) => (typeof moneyU === 'function' ? moneyU(c) : (c / 100).toFixed(2));
  const pool = () => { const all = (S.trades || []).filter((x) => !window.mtypeKeep || window.mtypeKeep(x)), real = all.filter((x) => !x.demo); return real.length ? real : all; };
  const empty = (msg, href, label) => `<p class="nav-empty">${esc(msg)}${href ? ` <a class="link" href="${href}">${esc(label)}</a>` : ''}</p>`;
  // header click anywhere (but not on its own buttons) opens the page
  document.addEventListener('click', (e) => {
    const h = e.target.closest && e.target.closest('.nav-ch'); if (!h || e.target.closest('button, select, input, .seg')) return;
    location.hash = h.dataset.href;
  });
  document.addEventListener('keydown', (e) => { if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('.nav-ch')) { e.preventDefault(); location.hash = e.target.dataset.href; } });

  function accountsCard() {
    const x = dt(), accs0 = (S.accounts || []).filter((a) => a.status !== 'archived' && a.status !== 'closed');
    const accs = typeof acctSortBreachLast === 'function' ? acctSortBreachLast(accs0) : accs0;   // exceeded accounts at the bottom
    // 6 accounts in good standing, then every exceeded / daily-limit account (always visible, at the bottom)
    const flagged = accs.filter((a) => typeof acctFlag === 'function' && (acctFlag(a) || {}).k);
    const shown = accs.filter((a) => !flagged.includes(a)).slice(0, 6).concat(flagged);
    const items = shown.map((a) => {
      let st = null; try { st = typeof acctState === 'function' ? acctState(a) : null; } catch (err) { st = null; }
      // an exceeded account: room 0 $, and its bar empty too (the text said 0 $ while the bar stayed full)
      const room = st && st.dd ? (st.breached ? 0 : Math.max(0, Math.min(1, (st.buffer || 0) / st.dd))) : null;
      const ps = window.SweepPayout && SweepPayout.status(a);   // the firm's payout conditions when they are set
      const evalA = a.phase === 'eval' || (!a.phase && a.rules && a.rules.target_c);
      const ready = evalA ? !!(st && st.passed) : ps ? ps.ready : false;   // an evaluation is passed only when target + consistency + minimum days are all met
      return `<a class="nav-acc" href="#account/${esc(a.id)}"><span class="nav-acc-t"><b>${esc(a.name || '')}</b><small>${esc((typeof firm === 'function' && firm(a.firm_id) && firm(a.firm_id).name) || '')}</small></span>
        <span class="nav-acc-bal">${st ? fmtU(st.bal) : '—'}</span>
        ${(() => { const f = typeof acctFlag === 'function' ? acctFlag(a) : null; return f && f.k ? `<span class="nav-acc-flag">${esc(f.t)}</span>` : ''; })()}
        ${room != null ? `<span class="nav-acc-dd"><small>${evalA && st.target && !ready ? (({ en: 'Target {a} / {b} · room {m}', fr: 'Objectif {a} / {b} · marge {m}', es: 'Objetivo {a} / {b} · margen {m}' })[LANG] || 'Target {a} / {b} · room {m}').replace('{a}', fmtU(Math.max(0, st.net))).replace('{b}', fmtU(st.target)).replace('{m}', fmtU(st.breached ? 0 : Math.max(0, st.buffer))) : `${x.dd} · ${fmtU(st.breached ? 0 : Math.max(0, st.buffer))}`}</small><i><s class="${room < 0.25 ? 'neg' : 'pos'}" style="width:${(room * 100).toFixed(0)}%"></s></i></span>` : ''}
        ${ready ? `<span class="nav-ready">${(a.phase === 'eval' || (!a.phase && !ps && a.rules && a.rules.target_c)) ? ({ en: 'Objectives reached', fr: 'Objectifs atteints', es: 'Objetivos alcanzados' }[LANG] || 'Objectives reached') + (a.pass_asked && window.SweepPass ? ' · ' + SweepPass.wait() : '') : x.ready}</span>` : ''}</a>`;   // (1 Nov., brief dans le temps F) after « Not yet »: waiting for the firm   // an evaluation is « passed », not « ready for payout »
    }).join('');
    const more = accs.length - shown.length;   // the full list is one tap away
    const MORE = { en: 'See the {n} other accounts ›', fr: 'Voir les {n} autres comptes ›', es: 'Ver las {n} otras cuentas ›' };
    return `<section class="surface nav-card d-acc">${head(x.acc, '#accounts')}<div class="nav-accs">${items || empty('', '', '')}</div>${more > 0 ? `<a class="link nav-acc-more" href="#accounts">${(MORE[LANG] || MORE.en).replace('{n}', more)}</a>` : ''}</section>`;
  }
  /* « My money » (E1): this month's net real money, withdrawable now, expenses, pending payouts — never simulated P&L */
  function payoutsCard() {
    const x = dt(), y = { en: { t: 'My money', net: 'Net real money · this month', wd: 'Withdrawable now', exp: 'Expenses this month', pend: 'Pending payouts', real: 'Real', sim: 'Simulated' },
      fr: { t: 'Mon argent', net: 'Net réel du mois', wd: 'Retirable maintenant', exp: 'Dépenses du mois', pend: 'Payouts en attente', real: 'Réel', sim: 'Simulé' },
      es: { t: 'Mi dinero', net: 'Neto real del mes', wd: 'Retirable ahora', exp: 'Gastos del mes', pend: 'Payouts pendientes', real: 'Real', sim: 'Simulado' } }[LANG] || null;
    const z = y || { t: 'My money', net: 'Net real money · this month', wd: 'Withdrawable now', exp: 'Expenses this month', pend: 'Pending payouts', real: 'Real', sim: 'Simulated' };
    const since = ({ en: 'Net real money · since {p}', fr: 'Net réel depuis {p}', es: 'Neto real desde {p}' })[LANG] || 'Net real money · since {p}';
    if (!window.SweepMoney) return `<section class="surface nav-card d-pay">${head(x.pay, '#payouts')}</section>`;
    const [a, b] = SweepMoney.periodOf('month'), m = SweepMoney.moneyOf({ from: a, to: b });
    const fm = (c) => (typeof money === 'function' ? money(c, { dec: 0 }) : (c / 100).toFixed(0));
    // nothing yet this month, and « Your real net » was done over a longer period: that one stays in sight (audit of 16 Oct.,
    // R17: the card said « $0 this month » right after the trader saw his real net)
    let lab = z.net, val = m.real.net;
    const quiet = !m.real.net && !m.real.expenses && !m.real.payouts && !m.real.live, f0 = quiet && window.SweepRealNet && SweepRealNet.from ? SweepRealNet.from() : null;
    if (f0 && f0 < a) {
      const m2 = SweepMoney.moneyOf({ from: f0, to: b }), loc = LANG === 'en' ? 'en-US' : LANG === 'es' ? 'es-ES' : 'fr-CA', d0 = new Date(f0 + 'T12:00:00');
      const p = f0.slice(5) === '01-01' ? d0.toLocaleDateString(loc, { month: 'long' }) : d0.toLocaleDateString(loc, { day: 'numeric', month: 'long' });
      if (m2.real.net) { val = m2.real.net; lab = since.replace('{p}', p); }
    }
    return `<section class="surface nav-card d-pay d-money" data-noi18n>${head(z.t, '#payouts')}
      <div class="nav-mny-l">${lab} <span class="mny-tag real">${z.real}</span></div><div class="nav-mny-big ${val >= 0 ? 'pos' : 'neg'}">${fm(val)}</div>
      <div class="nav-kpi-g nav-mny-g"><div><small>${z.wd} <span class="mny-tag sim">${z.sim}</span></small><b class="mny-dim">${fmtU(m.withdrawable)}</b></div><div><small>${z.exp}</small><b>${fm(-m.real.expenses)}</b></div><div><small>${z.pend}</small><b>${fmtU(m.real.pending)}</b></div></div>${window.SweepRealNet ? SweepRealNet.invite() : ''}</section>`;
  }
  const NW = {
    en: { title: 'What to watch', today: 'Today', next: 'Next session', none: 'No major U.S. release today.', nextOne: 'Next big one: {e} · {d} {t}', in: 'in {m}', now: 'now', act: 'Act.', fc: 'Fcst', prev: 'Prev.' },
    fr: { title: 'À surveiller', today: 'Aujourd’hui', next: 'Prochaine séance', none: 'Aucune annonce américaine importante aujourd’hui.', nextOne: 'Prochaine importante : {e} · {d} {t}', in: 'dans {m}', now: 'maintenant', act: 'Réel', fc: 'Prév.', prev: 'Préc.' },
    es: { title: 'Para vigilar', today: 'Hoy', next: 'Próxima sesión', none: 'No hay publicaciones importantes de EE. UU. hoy.', nextOne: 'Próxima importante: {e} · {d} {t}', in: 'en {m}', now: 'ahora', act: 'Real', fc: 'Prev.', prev: 'Ant.' } };
  const dur = (sec) => { const m = Math.round(sec / 60); if (m < 60) return `${m} min`; if (m < 1440) return `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, '0')}`; const d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60); return `${d} ${LANG === 'en' ? 'd' : 'j'.replace('j', LANG === 'es' ? 'd' : 'j')} ${h} h`; };
  let econAsked = {}, econReady = {};

  function econFor(day, to) {
    if (typeof ECON === 'undefined') return null;
    if (typeof S !== 'undefined' && S.mode !== 'server' && !S.me) return null;   // still starting: asking now would get sample data
    // an empty list can mean « not loaded yet »: only trust it once our own request for that day has answered
    if (econReady[day] || (ECON.days[day] && ECON.days[day].length)) return ECON.days[day] || [];
    if (!econAsked[day] && typeof loadEcon === 'function') { econAsked[day] = 1; loadEcon(day, to || day).then(() => { for (let d = day; d <= (to || day); d = ymd(new Date(new Date(d + 'T12:00:00').getTime() + 864e5))) econReady[d] = 1; const c = document.querySelector('#main .d-news'); if (c) c.outerHTML = newsCard(); const cal = document.querySelector('#main .d-cal'); if (cal) cal.outerHTML = calCard(); }).catch(() => {}); }
    return null;
  }
  /** Actual · Forecast · Previous of a release, always in view (« No number » for minutes and speeches) — day and week (1.3) */
  function evNums(e, x, now) {
    const past = e.ts <= now, diff = past && typeof econDiff === 'function' ? econDiff(e.actual, e.forecast) : null;
    const hasAct = e.actual != null && e.actual !== '';
    return (/\b(minutes|speech|speaks|testimony|press conference|beige book|statement|remarks)\b/i.test(e.event || '')) ? `<span class="nav-nonum nav-nonum-r" data-noi18n>${({ en: 'No number', fr: 'Sans chiffre', es: 'Sin cifra' })[LANG] || 'No number'}</span>` : `<span class="nav-ev-v nav-ev-v3"><span><small>${x.act || 'Act.'}</small><b class="${hasAct && diff ? diff.direction : ''}">${hasAct ? esc(String(econL(e.actual))) : '—'}</b></span><span><small>${x.fc}</small><b>${esc(String(econL(e.forecast || '—')))}</b></span><span><small>${x.prev}</small><b>${esc(String(econL(e.previous || '—')))}</b></span></span>`;
  }
  function newsCard() {
    // the day is the session (New York): the day ends at 17:00 and the next one starts at 18:00, so from 18:00 the next day's releases show
    const x = NW[LANG] || NW.en, today = etToday();
    if (DESK_TAB === 'week' && !window.SW_MQ.matches) return newsWeekCard();
    let day = today; const dd = new Date(day + 'T12:00:00');
    while (dd.getDay() === 0 || dd.getDay() === 6) dd.setDate(dd.getDate() + 1);   // weekend: the next session (Monday)
    day = ymd(dd);
    const ev = econFor(day); let moreN = 0;
    const label = day === today ? x.today : x.next + ' · ' + (typeof fdate === 'function' ? fdate(day, { weekday: 'long' }) : day);
    let body;
    // while loading: as many placeholder rows as last time for that day (3 the first time), so nothing below moves
    let rows = 3; try { const c = JSON.parse(localStorage.getItem('sw.newsRows') || '{}'); if (c[day] != null) rows = Math.max(1, c[day]); } catch (e) { /* private mode */ }
    if (ev == null) body = `<div class="nav-evs nav-evs-sk">${'<div class="skel"></div>'.repeat(rows)}</div>`;
    else {
      const all = ev.filter((e) => e.impact === 'high' || e.impact === 'medium');
      const now = Date.now() / 1000, nextUp = all.find((e) => e.ts > now - 60);
      // 3 rows: the next releases first (with the last one before them for context); the rest is one tap away (News)
      const at = nextUp ? Math.max(0, all.indexOf(nextUp) - 1) : Math.max(0, all.length - 3);
      const list = all.slice(Math.min(at, Math.max(0, all.length - 3)), Math.min(at, Math.max(0, all.length - 3)) + 3);
      if (all.length > 3) moreN = all.length - 3;
      try { const c = JSON.parse(localStorage.getItem('sw.newsRows') || '{}'); c[day] = Math.max(1, list.length); for (const k of Object.keys(c)) if (k < ymd(new Date(Date.now() - 864e5 * 3))) delete c[k]; localStorage.setItem('sw.newsRows', JSON.stringify(c)); } catch (e) { /* private mode */ }
      if (!list.length) body = `<p class="nav-empty">${x.none}</p>`;
      else body = `<div class="nav-evs">${list.map((e) => {
        const hm = typeof etStr === 'function' ? etStr(e.ts).slice(11, 16) : '';
        const past = e.ts <= now, diff = past && typeof econDiff === 'function' ? econDiff(e.actual, e.forecast) : null;
        const hasAct = e.actual != null && e.actual !== '';
        const right = evNums(e, x, now);
        const cd = e === nextUp && e.ts > now ? `<span class="nav-ev-cd" data-ts="${e.ts}">${x.in.replace('{m}', dur(e.ts - now))}</span>` : '';
        return `<button type="button" class="nav-ev ${e.impact} ${past ? 'past' : ''} ${e === nextUp ? 'next' : ''}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-ev-t">${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-ev-n">${esc(tr(e.event))}${cd}</span>${right}</button>`;
      }).join('')}</div>`;
    }
    const MORE = { en: '+{n} more', fr: '+{n} autres', es: '+{n} más' };
    return `<section class="surface nav-card d-news" data-noi18n>${head(x.title, '#news', esc(label) + (moreN ? ' · ' + (MORE[LANG] || MORE.en).replace('{n}', moreN) : ''))}${body}</section>`;
  }
  function newsWeekCard() {
    const x = NW[LANG] || NW.en, today = etToday();
    const d0 = new Date(today + 'T12:00:00'); if (d0.getDay() === 6) d0.setDate(d0.getDate() + 2); else if (d0.getDay() === 0) d0.setDate(d0.getDate() + 1);   // weekend: the coming week
    d0.setDate(d0.getDate() - ((d0.getDay() + 6) % 7));
    const days = [...Array(5)].map((_, i) => { const d = new Date(d0); d.setDate(d0.getDate() + i); return ymd(d); });
    const now = Date.now() / 1000; let loading = false; const rows = [];
    const ev0 = econFor(days[0], days[4]);
    days.forEach((day) => {
      const ev = ev0 == null ? null : econFor(day); if (ev == null) { loading = true; return; }
      ev.filter((e) => e.impact === 'high' || e.impact === 'medium').forEach((e) => {
        const hm = typeof etStr === 'function' ? etStr(e.ts).slice(11, 16) : '';
        const wd = new Date(day + 'T12:00:00').toLocaleDateString(LANG === 'en' ? 'en-US' : LANG === 'es' ? 'es-ES' : 'fr-CA', { weekday: 'short' }).replace('.', '');
        const past = e.ts < now - 60;
        rows.push(`<button type="button" class="nav-ev ${e.impact} ${past ? 'past nav-ev-wpast' : 'nav-ev-wnext'}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-ev-t"><small class="nav-ev-d">${esc(wd)}</small>${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-ev-n">${esc(tr(e.event))}</span>${evNums(e, x, now)}</button>`);
      });
    });
    const W = { en: 'This week', fr: 'Cette semaine', es: 'Esta semana' };
    const body = loading && !rows.length ? `<div class="nav-evs nav-evs-sk">${'<div class="skel"></div>'.repeat(3)}</div>` : rows.length ? `<div class="nav-evs nav-evs-w">${rows.join('')}</div>` : `<p class="nav-empty">${x.none}</p>`;
    return `<section class="surface nav-card d-news" data-noi18n>${head(x.title, '#news/week', W[LANG] || W.en)}${body}</section>`;
  }
  // countdown to the next release, refreshed every 30 s
  setInterval(() => {
    const x = NW[LANG] || NW.en, now = Date.now() / 1000;
    document.querySelectorAll('#main .nav-ev-cd[data-ts]').forEach((c) => { const t = +c.dataset.ts; c.textContent = t > now ? x.in.replace('{m}', dur(t - now)) : x.now; });
  }, 30000);
  let histMonth = null, histDays = {};
  function calCard() {
    const x = dt(), now = new Date(etToday() + 'T12:00:00');   // the current session
    const y = now.getFullYear(), m = now.getMonth(), first = new Date(y, m, 1), last = new Date(y, m + 1, 0);
    const key = ymd(first).slice(0, 7);
    const tr = pool().filter((t) => t.date && t.date.slice(0, 7) === key);
    const byDay = typeof dayMap === 'function' ? dayMap(typeof mergeCopies === 'function' ? mergeCopies(tr) : tr) : new Map();   // a copied trade counts once (audit of 16 Oct.)
    if (histMonth !== key) { histMonth = key; histDays = {}; apiJSON(`api/game/history?from=${ymd(first)}&to=${ymd(last)}`).then((r) => { (r.days || []).forEach((d) => { if (+d.is_swept) histDays[d.trading_day] = 1; }); document.querySelectorAll('.nav-cal [data-day]').forEach((c) => c.classList.toggle('nav-sw', !!histDays[c.dataset.day])); }).catch(() => {}); }
    econFor(ymd(first), ymd(last));
    const evDay = (k) => (typeof ECON !== 'undefined' && ECON.days[k] ? ECON.days[k].filter((e) => e.impact === 'high') : []);
    const short = (c) => (typeof moneyShort === 'function' ? moneyShort(c) : (c / 100).toFixed(0));
    const cells = [], strip = []; const lead = (first.getDay() + 6) % 7;
    const WD = LANG === 'en' ? ['S', 'M', 'T', 'W', 'T', 'F', 'S'] : LANG === 'es' ? ['D', 'L', 'M', 'X', 'J', 'V', 'S'] : ['D', 'L', 'M', 'M', 'J', 'V', 'S'];
    for (let i = 0; i < Math.min(lead, 5); i++) cells.push('<span class="nav-cd x"></span>');
    for (let d = 1; d <= last.getDate(); d++) {
      const dd = new Date(y, m, d), wd = dd.getDay(); if (wd === 0 || wd === 6) continue;
      const k = ymd(dd), day = byDay.get ? byDay.get(k) : null;
      const n = day ? (day.trades || []).length : 0;
      const net = day ? (day.net != null ? day.net : (day.trades || []).reduce((a, t) => a + (typeof tNet === 'function' ? tNet(t) : 0), 0)) : null;
      const evs = evDay(k);
      const tip = [k, net != null ? `${typeof money === 'function' ? money(net) : net} · ${n} trade${n > 1 ? 's' : ''}` : '', ...evs.map((e) => `${etStr(e.ts).slice(11, 16)} ${typeof tr === 'function' ? tr(e.event) : e.event}`)].filter(Boolean).join('\n');
      cells.push(`<a class="nav-cd ${net == null ? '' : net > 0 ? 'p' : net < 0 ? 'n' : 'z'} ${histDays[k] ? 'nav-sw' : ''} ${k === ymd(now) ? 'today' : ''} ${k < ymd(now) ? 'past' : ''}" href="#journal/${k}" data-day="${k}" title="${esc(tip)}">
        <b>${d}</b>${net != null ? `<span class="nav-cd-p">${short(net)}</span><span class="nav-cd-n">${n} trade${n > 1 ? 's' : ''}</span>` : ''}
        ${evs.length ? `<span class="nav-cd-e"><i></i>${esc(typeof shortEv === 'function' ? shortEv(evs[0].event) : evs[0].event.replace(/\s*\(.*?\)/g, '').split(' ').slice(0, 2).join(' '))}${evs.length > 1 ? ` +${evs.length - 1}` : ''}</span>` : ''}</a>`);
      strip.push(`<a class="nav-sd ${net == null ? '' : net > 0 ? 'p' : net < 0 ? 'n' : 'z'} ${histDays[k] ? 'nav-sw' : ''} ${k === ymd(now) ? 'today' : ''} ${k < ymd(now) ? 'past' : ''}" href="#journal/${k}" data-day="${k}" title="${esc(tip)}"><small>${WD[wd]}</small><b>${d}</b><span>${net != null ? short(net) : evs.length ? '<i></i>' : '·'}</span></a>`);
    }
    const wk = LANG === 'en' ? ['M', 'T', 'W', 'T', 'F'] : LANG === 'es' ? ['L', 'M', 'X', 'J', 'V'] : ['L', 'M', 'M', 'J', 'V'];
    return `<section class="surface nav-card d-cal" data-noi18n>${head(x.cal, '#calendar')}<div class="nav-strip" role="list">${strip.join('')}</div><div class="nav-cal"><div class="nav-cw">${wk.map((w) => `<span>${w}</span>`).join('')}</div><div class="nav-cg">${cells.join('')}</div></div>${typeof econLegend === 'function' && /nav-cd-e|<i><\/i><\/span><\/a>/.test(cells.join('') + strip.join('')) ? econLegend() : ''}</section>`;
  }
  // an existing section of the app becomes a card: whole header clickable, one « See all », short empty state
  function asCard(sec, cls, title, href, emptyMsg) {
    if (!sec) return null;
    sec.classList.add('nav-card', 'surface', cls);
    const h = sec.querySelector(':scope > .sec-h');
    if (h && !h.classList.contains('nav-ch')) {
      h.classList.add('nav-ch'); h.setAttribute('role', 'link'); h.tabIndex = 0; h.dataset.href = href;
      h.querySelectorAll(':scope > a.link').forEach((l) => l.remove());
      const t = h.querySelector('h2'); if (t) t.textContent = title;
      h.insertAdjacentHTML('beforeend', `<span class="nav-all">${dt().all}</span>`);
    }
    if (emptyMsg && !pool().length) {
      [...sec.children].forEach((c) => { if (c !== h) c.remove(); });
      sec.insertAdjacentHTML('beforeend', empty(emptyMsg, '', ''));
    }
    return sec;
  }
  function composeToday() {
    if (route().v !== 'dashboard') return;
    const main = document.getElementById('main'); if (!main) return;
    if (!main.querySelector(':scope > .greet')) return;
    hideOld(main);
    if (main.querySelector(':scope > .nav-dash')) return;
    if (!(S.accounts || []).length) { document.documentElement.classList.remove('nav-js'); return; }   // before the first account: the app's own setup screen
    document.documentElement.classList.add('nav-js');
    const x = dt(), kids = [...main.querySelectorAll(':scope > section')];
    const find = (test) => kids.find(test) || null;
    const curve = find((k) => k.querySelector('[data-act="eq"], .chartbox'));
    const period = find((k) => k.querySelector('.fbars, [data-act="period"]'));
    const trends = find((k) => k.querySelector(':scope > .sec-h a[href^="#analytics"]'));
    const recent = find((k) => k.querySelector(':scope > .sec-h a[href="#trades"]'));
    const econ = find((k) => k.querySelector('a[href="#news"]'));
    const missing = [!trends && 'trends'].filter(Boolean);   // the news, curve and recent-trades sections are replaced by cards: not needed
    if (missing.length && !reported) { reported = true; report('Today: section(s) not found: ' + missing.join(', ')); }
    const card = document.getElementById('gToday');
    const dash = document.createElement('div'); dash.className = 'nav-dash';
    // two columns on a computer, each card at its natural height (no stretched empty cards); one list on a phone (CSS order)
    const sg = stage();
    dash.innerHTML = `<div class="d-col d-col-a">${typeof window.SweepGuardCard === 'function' ? window.SweepGuardCard() : ''}<div class="d-today"></div>${typeof window.SweepTrialCard === 'function' ? window.SweepTrialCard() : ''}${sg.perf ? kpiCard() : ''}</div><div class="d-col d-col-b">${sg.acc ? accountsCard() : ''}${sg.money ? payoutsCard() : ''}</div>`;
    const greetEl = main.querySelector(':scope > .greet');
    // computer: the news, calendar and payouts go under the day card before the first paint (no card jumping a frame later)
    try { if (typeof newsUnderDay === 'function') newsUnderDay(dash); if (typeof deskToday === 'function') deskToday(dash); } catch (e) { /* the observers do it */ }
    greetEl.after(dash);
    greetLine(greetEl);
    // the welcome line follows the title directly; a plan banner (founding price…) comes after it
    const bb = main.querySelector(':scope > .bill-banner, :scope > .sb-banner');
    if (bb && bb.compareDocumentPosition(greetEl) & Node.DOCUMENT_POSITION_FOLLOWING) greetEl.after(bb);
    if (card) dash.querySelector('.d-today').append(card);
    // trends: only when there is something to show (no data = no card)
    if (trends) trends.classList.add('nav-old');   // (the week's trend: Stats, SWEEP.md step 3)
    // the old economic section, equity curve and recent trades are replaced (news card, performance card with its trades)
    [econ, curve, recent].forEach((sec) => sec && sec.classList.add('nav-old'));

    headDay();
    deskToday(dash);
    const sp = dash.querySelector('.nav-strip'), td = sp && sp.querySelector('.today');
    if (sp && td) sp.scrollLeft = Math.max(0, td.offsetLeft - sp.clientWidth / 2 + td.offsetWidth / 2);
  }

  /* ───────────── Settings in 5 groups: My routine · Notifications · Data · Advanced · Account; at the bottom: Appearance, Sweep AI,
   * About (SWEEP.md step 6, 4.5: « Discipline » became « My routine », with the 90-day gameplan, the plan mode, the lock time and
   * the risk rules) ───────────── */
  const SG = {
    en: ['Account', 'My routine', 'Notifications', 'Data', 'Advanced'], fr: ['Compte', 'Ma routine', 'Notifications', 'Données', 'Avancé'], es: ['Cuenta', 'Mi rutina', 'Notificaciones', 'Datos', 'Avanzado'],
  };
  // which section goes where (matched on the section title in any language)
  const SMAP = [
    [0, /^(your account|ton compte|tu cuenta)/i],
    [1, /^(90-day gameplan|parcours de 90 jours|recorrido de 90 días|discipline|disciplina|checklist|discipline checklist|checklist de discipline|checklist de disciplina|setups|risk rules|règles de risque|reglas de riesgo)/i],
    // brief 03 step 5: the advanced options together, folded (nothing removed)
    [4, /^(keyboard shortcuts|raccourcis clavier|atajos de teclado|prop firms|copied trades|trades copiés|operaciones copiadas|✦?\s*sweep ai)/i],   // (10 Nov., step 6) Sweep AI too
    [2, /^(notifications|notificaciones)/i],
    [3, /^(data|données|datos|connections|connexions|conexiones)/i],
  ];
  function groupSettings() {
    if (route().v !== 'settings') return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-sgrp')) return;
    const secs = [...main.querySelectorAll(':scope > section')];
    const buckets = [[], [], [], [], []], rest = [];
    for (const sec of secs) {
      const hd = sec.querySelector('h2, h3');
      if (hd && /^(discipline|disciplina)$/i.test(hd.textContent.trim())) hd.textContent = (SG[LANG] || SG.en)[1];   // its own title: the group's
      if (hd && /^(discipline checklist|checklist de discipline|checklist de disciplina)$/i.test(hd.textContent.trim())) hd.textContent = 'Checklist';   // (D7b) the average of the checklist is « Checklist »
      const h = ((sec.querySelector('h2, h3') || {}).textContent || '').trim();
      const m = sec.classList.contains('gp-set') ? [1] : SMAP.find(([, re]) => re.test(h));   // the gameplan, even while its section waits for its text
      (m ? buckets[m[0]] : rest).push(sec);
    }
    const names = SG[LANG] || SG.en;
    const anchor = main.querySelector('.nav-back');
    let at = anchor || null;
    // B15: foldable groups (Account, Discipline, Notifications, Data, Advanced); the open ones stay open while you navigate
    // (30 Oct., tour W3) all folded on arrival; « Account » last, before « About »
    let openSet; try { openSet = new Set(JSON.parse(sessionStorage.getItem('sw.sgd') || '[]')); } catch (e) { openSet = new Set(); }
    [1, 2, 3, 4, 0].forEach((i) => {
      const list = buckets[i];
      if (!list.length) return;
      const d = document.createElement('details'); d.className = 'nav-sgd'; d.dataset.i = i; d.open = openSet.has(i);
      d.innerHTML = `<summary class="nav-sgrp" data-noi18n><h2>${names[i]}</h2></summary>`;
      d.addEventListener('toggle', () => { d.open ? openSet.add(i) : openSet.delete(i); try { sessionStorage.setItem('sw.sgd', JSON.stringify([...openSet])); } catch (e) { /* private mode */ } });
      at ? at.after(d) : main.prepend(d); at = d;
      for (const sec of list) d.append(sec);
    });
    for (const sec of rest) main.append(sec);   // Appearance, « About » and legal notes stay at the end
    const VL = { fr: 'Libellé si non respectée', es: 'Etiqueta si no se cumple' }[LANG];
    if (VL) main.querySelectorAll('.q-tbl td[data-l]').forEach((td) => { td.dataset.l = VL; });
    if (matchMedia('(pointer:coarse)').matches) main.querySelectorAll(':scope > section').forEach((sec) => { if (/^(keyboard shortcuts|raccourcis clavier|atajos de teclado)/i.test(((sec.querySelector('h2,h3') || {}).textContent || '').trim())) sec.hidden = true; });
    main.querySelectorAll('.nav-sgrp').forEach((g) => { const n = g.nextElementSibling, h = n && (n.querySelector('h2,h3') || {}).textContent; const next2 = n && n.nextElementSibling; if (h && h.trim().toLowerCase() === g.textContent.trim().toLowerCase() && (!next2 || next2.classList.contains('nav-sgrp') || next2.tagName !== 'SECTION')) { const hh = n.querySelector('h2,h3'); if (hh) hh.hidden = true; } });   // one section with the group's name: its own title goes, the group stays foldable
    // (10 Nov., step 6) the chart's data credit at the end of « About Sweep », inside its card
    const legal = main.querySelector(':scope > .sc-legal'), ab = main.querySelector('section.about .surface'); if (legal) (ab || main).append(legal);
    // B15: « Log out » at the very bottom, on its own
    const out = main.querySelector('[data-act="logout"]');
    if (out) { const w = document.createElement('div'); w.className = 'nav-logout'; out.style.marginLeft = ''; w.append(out); main.append(w); }
  }

  /* ───────────── Add a trade: the last account and instrument you used are pre-selected ───────────── */
  if (typeof openTicket === 'function') {
    const origOpen = openTicket;
    openTicket = function (arg) {
      const out = origOpen.apply(this, arguments);
      if (!arg) setTimeout(() => {
        try {
          const last = (S.trades || []).filter((x) => !x.demo).sort((a, b) => ((b.date || '') + (b.entry_time || '')).localeCompare((a.date || '') + (a.entry_time || '')))[0];
          if (!last) return;
          const pick = (sel, val) => { const el = document.querySelector(sel); if (el && val && [...el.options].some((o) => o.value === val) && el.value !== val) { el.value = val; el.dispatchEvent(new Event('change', { bubbles: true })); } };
          pick('#tkSlide select[data-tk="account"]', last.account_id);
          pick('#tkSlide select[data-tk="inst"]', last.instrument);
        } catch (e) { /* the form works as before */ }
      }, 30);
      return out;
    };
  }


  /* ───────────── header height → sticky elements sit right under it (never under it) ───────────── */
  // the phone header's height, from a ResizeObserver on the header itself: no layout read on every render (it was one of the
  // slowest steps when a page opens on a phone)
  let hdrH = -1, hdrBox = 0;
  const setHdr = () => { const h = window.SW_MQ.matches ? hdrBox : 0; if (h !== hdrH) { hdrH = h; document.documentElement.style.setProperty('--nav-hdr', h + 'px'); } };
  function measureHeader() { setHdr(); }
  (function watchHeader() {
    const side = document.querySelector('aside.side'); if (!side) { setTimeout(watchHeader, 100); return; }
    new ResizeObserver((es) => { const e = es[es.length - 1]; const b = e.borderBoxSize && e.borderBoxSize[0]; hdrBox = Math.round(b ? b.blockSize : e.target.offsetHeight); setHdr(); }).observe(side);
  })();
  if (window.SW_MQ.addEventListener) window.SW_MQ.addEventListener('change', setHdr);

  /* ───────────── segmented controls: the selection slides from where it was ───────────── */
  let segPrev = {};
  function animateSeg() {
    document.querySelectorAll('#main .nav-seg').forEach((seg) => {
      if (seg.querySelector('.nav-thumb')) return;
      const on = seg.querySelector('.on'); if (!on) return;
      seg.classList.add('has-thumb');   // positioned first: the thumb is measured inside the control, never against the page
      const th = document.createElement('i'); th.className = 'nav-thumb'; th.setAttribute('aria-hidden', 'true'); seg.prepend(th);
      const key = [...seg.querySelectorAll('a')].map((a) => a.getAttribute('href')).join();
      const place = (el, anim) => { th.style.transition = anim ? '' : 'none'; const r = el.getBoundingClientRect(), b = seg.getBoundingClientRect(); th.style.width = r.width + 'px'; th.style.transform = `translateX(${r.left - b.left - seg.clientLeft}px)`; };
      const prev = segPrev[key]; const from = prev != null && seg.children[prev + 1];
      if (from && from !== on) { place(from, false); requestAnimationFrame(() => requestAnimationFrame(() => place(on, true))); } else place(on, false);
      segPrev[key] = [...seg.children].indexOf(on) - 1;
      seg.classList.add('has-thumb');
      seg.addEventListener('click', (e) => { const b = e.target.closest('a, button'); if (b && b.parentElement === seg) { segPrev[key] = [...seg.children].indexOf(b) - 1; place(b, true); } });
    });
  }


  /* ───────────── the tapped control stays under the finger (trade review page, phones), 15 Oct. ─────────────
   * Safari has no scroll anchoring: when a tap changes the height of something above it (the coach's verdict after a Yes / No,
   * a block that opens), the page jumped under the finger. For 0.7 s after a tap, if the control moved on the screen, the
   * page scrolls by as much — unless the trader scrolls himself. */
  let userMoved = 0;
  ['touchmove', 'wheel', 'keydown'].forEach((k) => addEventListener(k, () => { userMoved = performance.now(); }, { passive: true, capture: true }));
  addEventListener('click', (e) => {
    if (route().v !== 'trade' || !window.SW_MQ.matches) return;
    const main = document.getElementById('main'); if (!main || !main.contains(e.target)) return;
    if (e.target.closest('[data-sc="full"]')) return;   // (8 Nov.) the chart's full screen moves its button on purpose: following it scrolled the page 323 px
    const key = e.target.closest('[data-v],[data-act],[data-path]') || e.target, h0 = location.hash, t0 = performance.now();
    const sel = ['data-act', 'data-path', 'data-v', 'data-id', 'data-col'].filter((a) => key.hasAttribute && key.hasAttribute(a)).map((a) => `[${a}="${CSS.escape(key.getAttribute(a))}"]`).join('');
    const y0 = key.getBoundingClientRect().top;
    // (1 Nov.) the same control in the same card only: an answer given in « Answer your coach » moves the coach to its next
    // question, and the checklist's button of that question further down is another control (the page jumped 171 px to it)
    const zone = (x) => { const z = x.closest('section, .surface'); return z ? z.className.split(' ').filter((c) => !/^(open|on|is-|has-)/.test(c)).sort().join(' ') : ''; }, z0 = zone(key);
    const find = () => (document.contains(key) ? key : sel ? [...main.querySelectorAll(sel)].filter((c) => zone(c) === z0).sort((a, b) => Math.abs(a.getBoundingClientRect().top - y0) - Math.abs(b.getBoundingClientRect().top - y0))[0] : null);
    const fix = () => {
      if (location.hash !== h0 || userMoved > t0) return;
      const el = find();
      if (el) { const d = el.getBoundingClientRect().top - y0; if (Math.abs(d) >= 0.5) window.scrollBy(0, d); }   // (2 Nov.: 1 px left was still seen)
    };
    const tick = () => { fix(); if (performance.now() - t0 < 700) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
    // (1 Nov.) and as soon as the page is redrawn (a redraw scheduled in a later frame moved it for one image before the tick)
    const mo = new MutationObserver(fix); mo.observe(main, { childList: true, subtree: true, attributes: true, characterData: true }); setTimeout(() => mo.disconnect(), 700);   // (2 Nov.: a text or a class changed after the redraw left 10 px for one image)
  }, true);

  /* ───────────── jump report (trade review page, phones) ─────────────
   * After a tap, any block ABOVE what you are looking at that changes height for a moment makes the page jump on iOS
   * (Safari has no scroll anchoring). This samples the blocks for 0.7 s after each tap and, if one changes, sends a short
   * report to the admin dashboard (Errors): which block, how many pixels, for how long. At most 5 reports per visit.
   * (15 Oct.) A tap only — a click, not the touch that starts a scroll —, and never when the trader scrolls himself or the
   * tap opens another page: the reports of 4-14 Oct. were mostly that (« none changed height », up to 2,000 px). */
  let jumpReports = 0;
  addEventListener('click', (e) => {
    if (jumpReports >= 5 || route().v !== 'trade' || !window.SW_MQ.matches) return;
    const main = document.getElementById('main'); if (!main || !main.contains(e.target)) return;
    if (e.target.closest('[data-sc="full"]')) return;   // (8 Nov.) entering or leaving the chart's full screen is not a jump
    const blocks = () => [...main.children].map((c, i) => { const r = c.getBoundingClientRect(); return { k: (c.className || c.tagName).toString().split(' ').slice(0, 2).join('.') || ('#' + i), h: Math.round(r.height), top: Math.round(r.top) }; });
    const base = blocks(), t0 = performance.now(), seen = {}, key = (e.target.closest('[data-v],[data-act],[data-path]') || e.target);
    const at = (x) => x.getBoundingClientRect().top, h0 = location.hash;   // (on the screen: what the trader sees, after the anchoring above)
    const y0 = at(key); let worst = 0, worstAt = 0;
    const find = () => { if (document.contains(key)) return key; const k = ['data-act', 'data-path', 'data-v', 'data-id'].filter((a) => key.hasAttribute && key.hasAttribute(a)).map((a) => `[${a}="${CSS.escape(key.getAttribute(a))}"]`).join(''); if (!k) return null;
      // the same control redrawn: the copy nearest to where it was (« Answer your coach » repeats some of the review's buttons)
      return [...main.querySelectorAll(k)].sort((a, b) => Math.abs(at(a) - y0) - Math.abs(at(b) - y0))[0] || null; };
    const tick = () => {
      if (location.hash !== h0 || userMoved > t0) return;   // the tap opened another page, or the trader scrolled: not a jump
      const ms = Math.round(performance.now() - t0), el = find();
      if (el) { const d = Math.round(at(el) - y0); if (Math.abs(d) > Math.abs(worst)) { worst = d; worstAt = ms; } }
      blocks().forEach((b) => {
        const o = base.find((x) => x.k === b.k);
        if (!o) { if (!seen['+' + b.k]) seen['+' + b.k] = { d: b.h, ms }; return; }
        const d = b.h - o.h; if (Math.abs(d) >= 6 && !seen[b.k]) seen[b.k] = { d, ms };
      });
      if (performance.now() - t0 < 700) requestAnimationFrame(tick);
      else {
        if (Math.abs(worst) < 6) return;          // what you touched did not move: nothing to report
        jumpReports++;
        const list = Object.entries(seen);
        const msg = `Trade page jump: tapped control moved ${worst > 0 ? '+' : ''}${worst}px at ${worstAt}ms | blocks: ` + (list.map(([k, v]) => `${k} ${v.d > 0 ? '+' : ''}${v.d}px at ${v.ms}ms`).join('; ') || 'none changed height') + ` | tapped ${(key.dataset && (key.dataset.act || key.dataset.path)) || key.tagName} | ${innerWidth}x${innerHeight}`;
        try { fetch('api/client-error', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ msg: msg.slice(0, 480), page: '#trade', src: 'nav.js jump report' }) }).catch(() => {}); } catch (x) { /* offline */ }
      }
    };
    requestAnimationFrame(tick);
  }, true);

  /* sticky bars know when they are stuck (their background band is drawn only then) */
  let stuckRaf = 0;
  function markStuck() {
    stuckRaf = 0;
    document.querySelectorAll('#main .nav-seg').forEach((b) => {
      const top = parseFloat(getComputedStyle(b).top) || 0;
      b.classList.toggle('is-stuck', scrollY > 0 && Math.abs(b.getBoundingClientRect().top - top) < 3);   // (iOS rounds the sticky position: 1.5 px missed it)
    });
  }
  addEventListener('scroll', () => { if (!stuckRaf) stuckRaf = requestAnimationFrame(markStuck); }, { passive: true });

  /* ───────────── always the latest version ─────────────
   * The page knows its version (meta sweep-build). Open tabs check the server's version when you come back to the app,
   * when you change page, and every 10 minutes. If a new version was deployed:
   *   - coming back to the app after 30 s away, or changing page → it reloads itself right away (nothing is lost: the data is on the server);
   *   - while you are typing or have a sheet open → a small banner « New version · Update » waits for you. */
  const VT = { en: ['A new version of Sweep is ready.', 'Update'], fr: ['Une nouvelle version de Sweep est prête.', 'Mettre à jour'], es: ['Hay una nueva versión de Sweep.', 'Actualizar'] };
  const myBuild = (document.querySelector('meta[name="sweep-build"]') || {}).content || '';
  let newBuild = '', hiddenAt = 0, lastCheck = 0;
  const busy = () => { const a = document.activeElement; return (a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)) || !!document.querySelector(OVERLAYS); };
  async function checkVersion() {
    if (!myBuild || Date.now() - lastCheck < 20000) return newBuild;
    lastCheck = Date.now();
    try { const r = await fetch('api/version', { cache: 'no-store', credentials: 'same-origin' }); const j = await r.json(); if (j.build && j.build !== myBuild) newBuild = j.build; } catch (e) { /* offline: try later */ }
    return newBuild;
  }
  function offerUpdate() {
    if (document.getElementById('navUpdate')) return;
    const x = VT[LANG] || VT.en, el = document.createElement('div'); el.id = 'navUpdate'; el.className = 'nav-update'; el.setAttribute('role', 'status'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<span>${x[0]}</span><button type="button" class="btn sm primary">${x[1]}</button>`;
    el.querySelector('button').addEventListener('click', () => location.reload());
    document.body.append(el); requestAnimationFrame(() => el.classList.add('on'));
  }
  async function maybeUpdate(reason) {
    const nb = await checkVersion(); if (!nb) return;
    if (!busy() && (reason === 'nav' || reason === 'back')) { location.reload(); return; }
    offerUpdate();
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { hiddenAt = Date.now(); return; }
    maybeUpdate(hiddenAt && Date.now() - hiddenAt > 30000 ? 'back' : 'focus');
  });
  addEventListener('hashchange', () => { if (newBuild && !busy()) location.reload(); else maybeUpdate('nav'); });
  setInterval(() => { if (!document.hidden) maybeUpdate('timer'); }, 600000);

  // Settings › About shows which version is running (to check a deploy)
  function versionLine() {
    if (route().v !== 'settings' || !myBuild) return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-ver')) return;
    const about = main.querySelector('section.about') || main.lastElementChild; if (!about) return;
    const at = (document.querySelector('meta[name="sweep-build"]') || {}).dataset; const when = at && at.at ? new Date(at.at) : null;
    const L = { en: 'Version', fr: 'Version', es: 'Versión' }[LANG] || 'Version';
    const p = document.createElement('p'); p.className = 'nav-ver muted'; p.setAttribute('data-noi18n', '');
    p.textContent = `${L} ${myBuild.slice(0, 7)}${when ? ' · ' + when.toLocaleString(LANG === 'en' ? 'en-US' : LANG + '-CA', { dateStyle: 'medium', timeStyle: 'short' }) : ''}`;
    (about.querySelector(':scope > .surface') || about).append(p);   // (10 Nov., step 6) inside the card
  }

  /* any « ⋯ » menu stays inside the screen, whatever wraps around it */
  document.addEventListener('toggle', (e) => {
    const d = e.target; if (!d.matches || !d.matches('details.menu') || !d.open) return;
    const pop = d.querySelector('.menu-pop'); if (!pop) return;
    pop.style.left = ''; pop.style.right = '';
    const r = pop.getBoundingClientRect();
    if (r.left < 12) { pop.style.right = 'auto'; pop.style.left = (12 - d.getBoundingClientRect().left) + 'px'; }
    else if (r.right > innerWidth - 12) { pop.style.left = 'auto'; pop.style.right = (d.getBoundingClientRect().right - (innerWidth - 12)) + 'px'; }
  }, true);
  // the app's accessible names stay (the buttons show only their icon on phones)
  function iconLabels() {
    // #10 the sidebar's « Progression » button shows only its icon: it carries its name for screen readers
    document.querySelectorAll('.nav-prog').forEach((b) => { if (!b.getAttribute('aria-label')) b.setAttribute('aria-label', t().prog || 'Progression'); });
    document.querySelectorAll('#main .tr-top .ai-btn, #main .tr-top [data-act="edit-trade"]').forEach((b) => { if (!b.getAttribute('aria-label')) { const t = b.textContent.replace('✦', '').trim(); b.setAttribute('aria-label', t); b.title = t; } });
  }
  /* toggle report: a chip that does not stay selected after a tap is reported to the admin dashboard (Errors) */
  let toggleReports = 0;
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-act="toggle"][data-path][data-v], [data-g="j-emo"][data-v]'); if (!b || toggleReports >= 3 || e.detail > 1) return;   // (the 2nd click of a double-click changes nothing, on purpose)
    const quick = b.dataset.g === 'j-emo', car = quick && b.closest('.g-car');   // the quick « Journal » sheet
    const id = quick ? (car && car.dataset.id) : b.dataset.id, col = quick ? 'trades' : b.dataset.col, path = quick ? 'emo.before' : b.dataset.path, v = b.dataset.v;
    if (!id) return;
    const read = () => { try { const d = getDoc(col, id); return path.split('.').reduce((a, k) => (a == null ? a : a[k]), d); } catch (x) { return undefined; } };
    const before = JSON.stringify(read());
    setTimeout(() => {
      const after = read(), chip = quick ? document.querySelector(`#gSheet .g-car[data-id="${CSS.escape(id)}"] [data-g="j-emo"][data-v="${CSS.escape(v)}"]`) : document.querySelector(`[data-act="toggle"][data-id="${CSS.escape(id)}"][data-path="${CSS.escape(path)}"][data-v="${CSS.escape(v)}"]`);
      const inDoc = Array.isArray(after) && after.includes(v), shown = !!(chip && chip.classList.contains('on'));
      if (JSON.stringify(after) === before || inDoc !== shown) {
        toggleReports++;
        const msg = `Toggle did not stick${quick ? ' (quick journal)' : ''}: ${path}=${v} | before ${before} | after ${JSON.stringify(after)} | shown ${shown} | doc ${getDoc(col, id) ? 'found' : 'missing'} | id ${id}`;
        try { fetch('api/client-error', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ msg: msg.slice(0, 480), page: '#trade', src: 'nav.js toggle report' }) }).catch(() => {}); } catch (x) { /* offline */ }
      }
    }, 900);
  }, true);
  /* ───────────── add a checklist question right from the trade review (it applies to this and every next trade) ───────────── */
  const QA = { en: ['Add a question, e.g. Did I wait for my level?', 'Add', 'Saved for this trade and all the next ones.', 'No: '],
    fr: ['Ajouter une question, ex. Ai-je attendu mon niveau ?', 'Ajouter', 'Ajoutée à ce trade et à tous les suivants.', 'Non : '],
    es: ['Añadir una pregunta, p. ej. ¿Esperé mi nivel?', 'Añadir', 'Se añade a esta operación y a las siguientes.', 'No: '] };
  function questionAdd() {
    if (route().v !== 'trade') return;
    const score = document.querySelector('#main .score'); if (!score) return;
    const box = score.closest('.surface') || score.parentElement; if (!box || box.querySelector('.nav-qadd')) return;
    const x = QA[LANG] || QA.en, f = document.createElement('form'); f.className = 'nav-qadd'; f.setAttribute('data-noi18n', '');
    f.innerHTML = `<input type="text" maxlength="120" placeholder="${esc(x[0])}" aria-label="${esc(x[0])}"><button type="submit" class="btn">${x[1]}</button>`;
    f.addEventListener('submit', (e) => {
      e.preventDefault();
      const v = f.querySelector('input').value.trim(); if (!v) return;
      editDoc('settings', 'settings', (r) => { r.questions = r.questions || []; r.questions.push({ id: 'q' + (typeof uid === 'function' ? uid() : Date.now().toString(36)), text: v, viol: x[3] + v.replace(/\s*\?$/, ''), active: true }); });
      if (typeof toast === 'function') toast(x[2]);
      render();
    });
    box.append(f);
  }
  /* ───────────── swipe down closes the Guide & help sheet (like the other sheets) ───────────── */
  (function () {
    let y0 = 0, dy = 0, panel = null, drag = false;
    document.addEventListener('touchstart', (e) => {
      const p = e.target.closest && e.target.closest('.gd-help-ov.open .gd-panel'); if (!p) return;
      const body = p.querySelector('.gd-body'); if (body && body.scrollTop > 0 && !e.target.closest('.gd-grab')) return;
      panel = p; y0 = e.touches[0].clientY; dy = 0; drag = true; p.style.transition = 'none';
    }, { passive: true });
    document.addEventListener('touchmove', (e) => {
      if (!drag || !panel) return; dy = Math.max(0, e.touches[0].clientY - y0);
      if (dy > 0) panel.style.transform = `translateY(${dy}px)`;
    }, { passive: true });
    document.addEventListener('touchend', () => {
      if (!drag || !panel) return; drag = false; const p = panel; panel = null;
      p.style.transition = 'transform .28s var(--sw-ease)';
      if (dy > 90) { const x = document.querySelector('.gd-help-ov .gd-x'); p.style.transform = 'translateY(100%)'; setTimeout(() => { if (x) x.click(); p.style.transform = ''; p.style.transition = ''; }, 200); }
      else { p.style.transform = ''; setTimeout(() => { p.style.transition = ''; }, 300); }
    });
  })();
  /* ───────────── draw with each page ───────────── */
  const appRender = render;
  render = function () {
    const out = appRender.apply(this, arguments);
    // each step on its own: one failing never stops the others
    [chrome, greetOff, composeToday, groupSettings, measureHeader, animateSeg, markStuck, versionLine, iconLabels, questionAdd, headDay, hideWeekends].forEach((f) => { try { f(); } catch (e) { /* never blocks */ } });
    return out;
  };
  window.SweepNav = { openMenu, t };
  // fetch the next session's releases as soon as the app knows it is signed in (the card is then ready when Today draws)
  (function prefetch(n) { try { if (typeof S !== 'undefined' && S.mode === 'server') { econFor(etToday()); return; } } catch (e) { return; } if (n < 40) setTimeout(() => prefetch(n + 1), 50); })(0);
  if (!alias()) try { chrome(); } catch (e) { /* first paint */ }
})();

/* ───────────── trade fields stored in an older shape are repaired before any edit ─────────────
 * Trades saved before the server kept {} as {} may hold « review », « discipline » or « emo » as a list ([]) or a text.
 * Writing a note, a checklist answer, an emotion or a score into a list is lost on save — so every edit of a trade
 * first turns these fields back into objects (emotions keep their values). Also done once on load for all trades. */
(function () {
  'use strict';
  const OBJ = ['review', 'discipline', 'emo'];
  const badField = (v) => v != null && (typeof v !== 'object' || Array.isArray(v));
  const bad = (t) => t && (OBJ.some((k) => badField(t[k])) || (t.emo && typeof t.emo === 'object' && !Array.isArray(t.emo) && ((t.emo.before != null && !Array.isArray(t.emo.before)) || (t.emo.after != null && !Array.isArray(t.emo.after)))));
  const fix = (d) => {
    let e = d.emo;
    if (Array.isArray(e)) e = { before: e.filter((x) => typeof x === 'string') };
    else if (typeof e === 'string') e = { before: e ? [e] : [] };
    else if (!e || typeof e !== 'object') e = {};
    ['before', 'after'].forEach((k) => { const v = e[k]; if (v != null && !Array.isArray(v)) e[k] = typeof v === 'string' && v ? [v] : []; });
    d.emo = e;
    ['review', 'discipline'].forEach((k) => { const v = d[k]; if (v != null && (typeof v !== 'object' || Array.isArray(v))) d[k] = typeof v === 'string' && v && k === 'review' ? { why_in: v } : {}; });
  };
  // every edit of a trade goes through the repair first (notes, answers, emotions, scores — typed or tapped)
  (function wrapEdit(n) {
    if (typeof window.editDoc !== 'function') { if (n < 60) setTimeout(() => wrapEdit(n + 1), 100); return; }
    if (window.editDoc.__fix) return;
    const orig = window.editDoc;
    const w = function (col, id, fn, opts) {
      if (col === 'trades' && typeof fn === 'function') { const f0 = fn; fn = function (d) { if (bad(d)) fix(d); return f0.apply(this, arguments); }; }
      return orig.call(this, col, id, fn, opts);
    };
    w.__fix = true; window.editDoc = w;
  })(0);
  // once the trades are loaded: repair every trade still in an older shape
  let done = false;
  (function sweep(n) {
    if (done) return;
    if (typeof S === 'undefined' || !Array.isArray(S.trades) || !S.trades.length || typeof editDoc !== 'function') { if (n < 60) setTimeout(() => sweep(n + 1), 500); return; }
    done = true;
    S.trades.filter((t) => !t.demo && bad(t)).slice(0, 300).forEach((t) => editDoc('trades', t.id, fix));
  })(0);
})();

/* ───────────── real P&L, slippage and fees ─────────────
 * Stops fill worse than planned on fast moves, and fees are debited by the firm: the P&L computed from the prices
 * then differs from the platform's. The trader can type the platform's P&L for a trade (« Real P&L ») — it becomes the
 * truth everywhere (balance, drawdown, stats), the prices still drive the chart and the R. Each account can hold a
 * commission per contract (round trip), deducted automatically. Stats show the slippage this costs.
 *   real_pnl_c   P&L shown by the platform (fees included), cents
 *   pnl_calc_c   P&L from the prices (gross), cents — kept to measure the slippage
 *   pnl_c        = real_pnl_c + fees_c when a real P&L exists, so the app's net (pnl_c − fees_c) equals the platform */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const TXT = {
    en: { real: 'Real P&L (platform)', realPh: 'As shown by your platform', calc: 'From your prices', gap: 'Slippage', fees: 'Fees', feeAcc: 'Commission per contract (round trip)', feeHelp: 'Deducted from every new trade on this account.', cpct: 'Size of copies on this account (%)', cpctHelp: '50%: 1 contract here for 2 on the original account. 100% by default.', grpLine: 'Copy group: {x}', grpLeave: 'Leave the group', acc1: '1 account', accN: '{k} accounts', st: 'Slippage and fees', stSub: 'On {n} trade{s} with the real P&L entered', tot: 'Slippage', avg: 'Average per trade', avgR: 'Average in R', worst: 'Worst', feesT: 'Fees (all trades)', none: 'Enter the platform\'s P&L on a trade (form or trade review) to measure your slippage.', hint: 'Fees included, as in your account.' },
    fr: { real: 'P&L réel (plateforme)', realPh: 'Comme affiché par ta plateforme', calc: 'Selon tes prix', gap: 'Glissement', fees: 'Frais', feeAcc: 'Commission par contrat (aller-retour)', feeHelp: 'Déduite de chaque nouveau trade sur ce compte.', cpct: 'Taille des copies sur ce compte (%)', cpctHelp: '50 % : 1 contrat ici pour 2 sur le compte d’origine. 100 % par défaut.', grpLine: 'Groupe de copie : {x}', grpLeave: 'Retirer du groupe', acc1: '1 compte', accN: '{k} comptes', st: 'Glissement et frais', stSub: 'Sur {n} trade{s} avec le P&L réel entré', tot: 'Glissement', avg: 'Moyenne par trade', avgR: 'Moyenne en R', worst: 'Pire', feesT: 'Frais (tous les trades)', none: 'Entre le P&L de ta plateforme sur un trade (formulaire ou bilan) pour mesurer ton glissement.', hint: 'Frais inclus, comme dans ton compte.' },
    es: { real: 'P&L real (plataforma)', realPh: 'Como lo muestra tu plataforma', calc: 'Según tus precios', gap: 'Deslizamiento', fees: 'Comisiones', feeAcc: 'Comisión por contrato (ida y vuelta)', feeHelp: 'Se descuenta de cada nueva operación en esta cuenta.', cpct: 'Tamaño de las copias en esta cuenta (%)', cpctHelp: '50 %: 1 contrato aquí por 2 en la cuenta de origen. 100 % por defecto.', grpLine: 'Grupo de copia: {x}', grpLeave: 'Quitar del grupo', acc1: '1 cuenta', accN: '{k} cuentas', st: 'Deslizamiento y comisiones', stSub: 'En {n} operaci{s} con el P&L real', tot: 'Deslizamiento', avg: 'Promedio por operación', avgR: 'Promedio en R', worst: 'Peor', feesT: 'Comisiones (todas)', none: 'Introduce el P&L de tu plataforma en una operación (formulario o revisión) para medir tu deslizamiento.', hint: 'Comisiones incluidas, como en tu cuenta.' } };
  const tx = (k) => (TXT[L] || TXT.en)[k];
  const $m = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));
  const toC = (v) => { const s = String(v == null ? '' : v).replace(/[\s\u00a0$]/g, '').replace(',', '.'); if (s === '' || s === '-' || !isFinite(+s)) return null; return Math.round(+s * 100); };
  const calcOf = (d) => { try { return typeof calcPnl === 'function' ? calcPnl(d.direction, d.entry, d.exit, d.contracts, d.instrument || 'NQ') : null; } catch (e) { return null; } };
  const acctOf = (id) => (typeof S !== 'undefined' && S.accounts || []).find((a) => a.id === id);

  /* every saved trade: fees from the account, P&L from the prices, real P&L as the truth */
  /** contracts bought and sold: one round trip each — an add counts (2 contracts, out 1, back in 1, out 2 = 3), like the CSV import and the sync */
  const turnsOf = (ex, n) => { ex = Array.isArray(ex) ? ex : []; if (!ex.length) return n; const side = ex[0].side, q = ex.reduce((a, x) => a + (x.side === side ? +x.qty || 0 : 0), 0); return q > 0 ? q : n; };
  function shape(d) {
    if (!d || d.demo) return d;
    const a = acctOf(d.account_id);
    const isNew = !(typeof getDoc === 'function' && getDoc('trades', d.id));   // older trades keep their fees as they are
    if (isNew && d.fees_c == null && a && a.fee_rt_c > 0 && d.contracts > 0) { d.fees_c = Math.round(a.fee_rt_c * turnsOf(d.executions, d.contracts)); d.fees_auto = true; }
    const c = calcOf(d); if (c != null) d.pnl_calc_c = c;
    if (typeof d.real_pnl_c === 'number' && isFinite(d.real_pnl_c)) { d.pnl_c = d.real_pnl_c + (d.fees_c || 0); d.pnl_manual = true; d.pnl_real = true; }
    else if (d.pnl_real) { delete d.pnl_real; d.pnl_manual = false; if (c != null) d.pnl_c = c; }
    return d;
  }
  /* copy trading (brief 02 part 4): a copy on another account takes that account's size (copy_pct, % of the original's
     contracts, 100 by default, at least 1 contract), its P&L for that size and that account's commission; the source's
     platform numbers (real P&L, import key, synced source) never travel with it. Every way of copying goes through here:
     the trade page's « Copy to accounts », the add form, the screenshot forms. */
  const sizeFor = (accId, n0) => { const a = acctOf(accId), p = a && +a.copy_pct > 0 ? +a.copy_pct : 100; return Math.max(1, Math.round((+n0 || 1) * p / 100)); };
  function scaleExecs(ex, f, n) {
    if (!Array.isArray(ex) || !ex.length || f === 1) return ex;
    const s = ex.map((x) => Object.assign({}, x, { qty: (+x.qty || 0) * f }));
    if (s.every((x) => Math.abs(x.qty - Math.round(x.qty)) < 1e-9)) return s.map((x) => Object.assign(x, { qty: Math.round(x.qty) }));
    // a size that does not divide the fills: one entry and one exit at their average prices (same P&L, whole contracts)
    const side = ex[0].side, ins = ex.filter((x) => x.side === side), outs = ex.filter((x) => x.side !== side), q = (l) => l.reduce((a, x) => a + (+x.qty || 0), 0);
    if (!ins.length || !outs.length || Math.abs(q(ins) - q(outs)) > 1e-9) return s.map((x) => Object.assign(x, { qty: Math.max(1, Math.round(x.qty)) }));
    const avg = (l) => l.reduce((a, x) => a + (+x.price) * (+x.qty || 0), 0) / q(l);
    return [Object.assign({}, ins[0], { qty: n, price: avg(ins) }), Object.assign({}, outs[outs.length - 1], { qty: n, price: avg(outs) })];
  }
  const known = (d) => !d.pnl_manual && typeof instOf === 'function' && !instOf(d.instrument || 'NQ').unknown;
  function feesFor(d, n, srcFees, f) {
    const a = acctOf(d.account_id);
    if (a && a.fee_rt_c > 0) { d.fees_c = Math.round(a.fee_rt_c * turnsOf(d.executions, n)); d.fees_auto = true; }
    else if (srcFees != null) { d.fees_c = Math.round(srcFees * f); }
  }
  function makeCopy(src, accId, group, k) {
    const d = JSON.parse(JSON.stringify(src));
    ['real_pnl_c', 'pnl_real', 'import_key'].forEach((x) => delete d[x]);
    if (d.source && d.source !== 'screenshot') delete d.source;   // a copy made in Sweep is not the platform's trade
    d.id = typeof uid === 'function' ? uid() : 't' + Math.random().toString(36).slice(2); d.account_id = accId; d.copy_group = group;
    d.copy_src = src.id;   // a copy made by Sweep: a synced trade of that account takes its place, whatever its size (sync_match)
    // the original stays the earliest created: a group is counted as its original (Stats, Journal, My money, the coach, the server)
    d.created_at = new Date(Math.max(Date.now(), Date.parse(src.created_at || '') || 0) + 1 + (k || 0)).toISOString();
    const n0 = +src.contracts || 1, n = sizeFor(accId, n0), f = n / n0;
    d.contracts = n;
    if (f !== 1) {
      d.executions = scaleExecs(src.executions, f, n);
      d.pnl_c = Math.round((+src.pnl_c || 0) * f);
      if (src.risk_c != null) d.risk_c = Math.round(src.risk_c * f);
    }
    feesFor(d, n, src.fees_c, f);
    return d;
  }
  /** a copy after its original was edited in the add form: same prices and times, its own size, its P&L for that size */
  function follow(b, c) {
    const n = +b.contracts || 1, f = n / (+c.contracts || 1);
    b.instrument = c.instrument;
    b.executions = scaleExecs(JSON.parse(JSON.stringify(c.executions || [])), f, n);
    const pos = known(c) && Array.isArray(b.executions) && b.executions.length && typeof positionOf === 'function' ? positionOf(b.executions, c.instrument || 'NQ') : null;
    if (pos && pos.closed) b.pnl_c = pos.realized_c; else if (c.pnl_c != null) b.pnl_c = Math.round(c.pnl_c * f);
    if (b.fees_auto) feesFor(b, n, null, 1);
    return b;
  }
  window.SweepCopy = { make: makeCopy, follow, sizeFor };

  (function wrapPut(n) {
    if (typeof window.put !== 'function') { if (n < 60) setTimeout(() => wrapPut(n + 1), 100); return; }
    if (window.put.__real) return;
    const orig = window.put;
    const w = function (col, doc) {
      if (col === 'trades' && doc && typeof doc === 'object') {
        // the add / edit form: its « Real P&L » field applies to the trade it saves
        const tk = document.querySelector('#tkSlide.open'), f = tk && tk.querySelector('[data-real]');
        if (f && typeof TK !== 'undefined' && TK && doc.account_id === TK.account) { const v = toC(f.value); if (v == null) delete doc.real_pnl_c; else doc.real_pnl_c = v; }
        shape(doc);
      }
      return orig.apply(this, arguments);
    };
    w.__real = true; window.put = w;
  })(0);

  /* the form: « Real P&L (platform) » under the exit, with the gap to the prices */
  const realMem = {};
  function formField() {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || typeof TK === 'undefined' || !TK) return;
    const key = TK.id || 'new';
    let box = tk.querySelector('.nav-real');
    const ax = tk.querySelector('.nav-ax'), at = tk.querySelector('[data-act="tk-exitat"]'), rk = tk.querySelector('#tkRisk');
    const row = ax || rk || (at && at.closest('.row'));   // after the risk box (the exit time now sits next to the entry time): the last thing to fill
    if (!row) { if (box) box.remove(); return; }
    if (!box) {
      if (realMem[key] == null && TK.id) { const t = typeof getDoc === 'function' && getDoc('trades', TK.id); if (t && typeof t.real_pnl_c === 'number') realMem[key] = (t.real_pnl_c / 100).toFixed(2); }
      box = document.createElement('label'); box.className = 'tk-f nav-real'; box.setAttribute('data-noi18n', '');
      box.innerHTML = `<span>${tx('real')}</span><div class="tk-in"><input data-real inputmode="decimal" autocomplete="off" placeholder="${tx('realPh')}" value="${realMem[key] || ''}"></div><small class="nav-real-gap"></small>`;
      row.after(box);
      box.querySelector('input').addEventListener('input', (e) => { realMem[key] = e.target.value; gapLine(box); });
    } else if (box.previousElementSibling !== row) row.after(box);
    gapLine(box);
  }
  function gapLine(box) {
    const out = box.querySelector('.nav-real-gap'), v = toC(box.querySelector('input').value);
    let calc = null; try { const s = typeof tkState === 'function' ? tkState() : null; calc = s && s.pos && typeof s.pos.realized_c === 'number' && s.pos.closed ? s.pos.realized_c : null; } catch (e) { /* form not ready */ }
    const set = (html) => { if (out.innerHTML !== html) out.innerHTML = html; };   // unchanged = untouched (no endless redraw)
    if (v == null || calc == null) { set(tx('hint')); return; }
    const a = acctOf(TK.account), fee = a && a.fee_rt_c > 0 ? Math.round(a.fee_rt_c * turnsOf(typeof tkExecs === 'function' ? tkExecs() : [], TK.qty || 1)) : 0;
    const slip = v + fee - calc;
    set(`${tx('calc')} : <b>${$m(calc)}</b> · ${tx('gap')} : <b class="${slip < 0 ? 'neg' : 'pos'}">${$m(slip)}</b>${fee ? ` · ${tx('fees')} : <b>${$m(-fee)}</b>` : ''}`);
  }
  // put back in the same frame the form is redrawn (before paint): the form never jumps
  new window.SweepMO((recs) => {
    if (!document.querySelector('#tkSlide.open')) return;
    if (recs.every((r) => r.target.closest && r.target.closest('.nav-real'))) return;   // our own line: nothing to do
    try { formField(); } catch (e) { /* never blocks */ }
  }).observe(document.body, { childList: true, subtree: true });

  /* the trade review page: real P&L next to the fees, with the slippage */
  function tradeField() {
    const m = /^#trade\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), t = typeof getDoc === 'function' && getDoc('trades', id); if (!t) return;
    const feeIn = document.querySelector('#main [data-bind$="|fees_c"]'), feeLab = feeIn && feeIn.closest('label, .f'); if (!feeLab) return;
    let box = document.querySelector('#main .nav-real-tr');
    if (!box) {
      box = document.createElement('label'); box.className = 'f nav-real-tr'; box.setAttribute('data-noi18n', '');
      box.innerHTML = `<span>${tx('real')}</span><input inputmode="decimal" data-real-tr placeholder="${tx('realPh')}" value="${typeof t.real_pnl_c === 'number' ? (t.real_pnl_c / 100).toFixed(2) : ''}"><small class="help nav-real-gap"></small>`;
      feeLab.after(box);
      box.querySelector('input').addEventListener('change', (e) => {
        const v = toC(e.target.value);
        editDoc('trades', id, (d) => { if (v == null) delete d.real_pnl_c; else d.real_pnl_c = v; shape(d); });
        setTimeout(() => { if (typeof render === 'function') render(); }, 60);
      });
    }
    const g = box.querySelector('.nav-real-gap');
    if (typeof t.real_pnl_c === 'number' && typeof t.pnl_calc_c === 'number') {
      const slip = t.pnl_c - t.pnl_calc_c;
      g.innerHTML = `${tx('calc')} : ${$m(t.pnl_calc_c)} · ${tx('gap')} : <b class="${slip < 0 ? 'neg' : 'pos'}">${$m(slip)}</b>${t.fees_c ? ` · ${tx('fees')} : ${$m(-t.fees_c)}` : ''}`;
    } else g.textContent = tx('hint');
  }

  /* the account page: commission per contract */
  function accountFee() {
    const m = /^#account\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), a = acctOf(id); if (!a) return;
    const inp = document.querySelector('#main [data-bind$="|rules.consistency_pct"], #main [data-bind$="|rules.min_days"]');
    const grid = inp && inp.closest('.fgrid'); if (!grid || grid.querySelector('.nav-fee')) return;
    const box = document.createElement('label'); box.className = 'f nav-fee'; box.setAttribute('data-noi18n', '');
    box.innerHTML = `<span>${tx('feeAcc')}</span><input inputmode="decimal" placeholder="$" value="${a.fee_rt_c > 0 ? (a.fee_rt_c / 100).toFixed(2) : ''}"><small class="help">${tx('feeHelp')}</small>`;
    grid.append(box);
    box.querySelector('input').addEventListener('change', (e) => { const v = toC(e.target.value); editDoc('accounts', id, (d) => { if (v == null || v <= 0) delete d.fee_rt_c; else d.fee_rt_c = Math.abs(v); }); });
    // copy trading (brief 02 part 4): the size a copy of a trade takes on this account
    const cp = document.createElement('label'); cp.className = 'f nav-cpct'; cp.setAttribute('data-noi18n', '');
    cp.innerHTML = `<span>${tx('cpct')}</span><input inputmode="numeric" placeholder="100" value="${a.copy_pct > 0 && a.copy_pct !== 100 ? a.copy_pct : ''}"><small class="help">${tx('cpctHelp')}</small>`;
    grid.append(cp);
    cp.querySelector('input').addEventListener('change', (e) => { const v = Math.round(parseFloat(String(e.target.value).replace(',', '.').replace('%', ''))); editDoc('accounts', id, (d) => { if (!(v > 0) || v === 100) delete d.copy_pct; else d.copy_pct = Math.min(1000, v); }); });
    const all = a.group_id && typeof copyGroups === 'function' ? copyGroups().get(a.group_id) : null;
    if (all) {   // the accounts it is traded with (« Copy to my group » on a trade's page)
      const gb = document.createElement('div'); gb.className = 'f full nav-grp'; gb.setAttribute('data-noi18n', '');
      const nm = typeof groupName === 'function' ? groupName(all) : '', n = all.length === 1 ? tx('acc1') : tx('accN').replace('{k}', all.length);
      gb.innerHTML = `<span>${esc(tx('grpLine').replace('{x}', nm ? `${nm} (${n})` : n))}</span><small class="help">${all.map((x) => esc(typeof acctLabel === 'function' ? acctLabel(x.id) : x.name)).join(' · ')}</small><button type="button" class="link" data-grp-leave="${esc(id)}">${tx('grpLeave')}</button>`;
      grid.append(gb);
    }
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-grp-leave]'); if (!b) return;
    const a = acctOf(b.dataset.grpLeave), g = a && a.group_id; if (!g) return;
    editDoc('accounts', a.id, (d) => { delete d.group_id; });
    const rest = (S.accounts || []).filter((x) => x.group_id === g);
    if (rest.length === 1) editDoc('accounts', rest[0].id, (d) => { delete d.group_id; });   // a group of one is no group
    if (typeof render === 'function') render();
  });

  /* Stats: slippage and fees */
  function statsCard() {
    if (!/^#analytics/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-slip')) return;
    const tr = (typeof ft === 'function' ? ft() : (S.trades || [])).filter((t) => !t.demo);   // the page's trades: its filters, a copy once (brief 02 part 6)
    const real = tr.filter((t) => typeof t.real_pnl_c === 'number' && typeof t.pnl_calc_c === 'number');
    const fees = tr.reduce((s, t) => s + (t.fees_c || 0), 0);
    const sec = document.createElement('section'); sec.className = 'surface nav-slip'; sec.setAttribute('data-noi18n', '');
    if (!real.length) {
      sec.innerHTML = `<div class="nav-ch"><h2>${tx('st')}</h2></div><p class="muted">${tx('none')}</p>${fees ? `<div class="nav-slip-k"><div><span>${tx('feesT')}</span><b class="neg">${$m(-fees)}</b></div></div>` : ''}`;
    } else {
      const slips = real.map((t) => ({ t, s: t.pnl_c - t.pnl_calc_c }));
      const tot = slips.reduce((a, x) => a + x.s, 0), avg = Math.round(tot / slips.length);
      const rs = slips.map((x) => { const r = typeof tRisk === 'function' ? tRisk(x.t) : null; return r ? x.s / r : null; }).filter((v) => v != null);
      const avgR = rs.length ? rs.reduce((a, v) => a + v, 0) / rs.length : null;
      const worst = slips.slice().sort((a, b) => a.s - b.s)[0];
      sec.innerHTML = `<div class="nav-ch"><h2>${tx('st')}</h2><span class="muted">${tx('stSub').replace('{n}', real.length).replace('{s}', L === 'es' ? (real.length > 1 ? 'ones' : 'ón') : (real.length > 1 ? 's' : ''))}</span></div>
        <div class="nav-slip-k"><div><span>${tx('tot')}</span><b class="${tot < 0 ? 'neg' : 'pos'}">${$m(tot)}</b></div>
        <div><span>${tx('avg')}</span><b class="${avg < 0 ? 'neg' : 'pos'}">${$m(avg)}</b></div>
        <div><span>${tx('avgR')}</span><b class="${avgR < 0 ? 'neg' : 'pos'}">${avgR == null ? '—' : avgR.toFixed(2) + ' R'}</b></div>
        <div><span>${tx('worst')}</span><a href="#trade/${encodeURIComponent(worst.t.id)}"><b class="${worst.s < 0 ? 'neg' : 'pos'}">${$m(worst.s)}</b></a></div>
        <div><span>${tx('feesT')}</span><b class="neg">${$m(-fees)}</b></div></div>`;
    }
    const anchor = main.querySelector('.ikpis, .kpis, .igrid');
    if (anchor) anchor.after(sec); else main.append(sec);
  }

  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__real) {
    const w = function () { const out = appRender.apply(this, arguments); [tradeField, accountFee, statsCard].forEach((f) => { try { f(); } catch (e) { /* never blocks */ } }); return out; };
    w.__real = true; window.render = w;
  }
})();

/* ───────────── add a trade from everywhere; dollar amounts in the form; a short Journal recap ───────────── */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { add: 'Add a trade', addDay: 'Add a trade on this day', usdExit: 'Or the result in $', usdExitPh: 'e.g. -350', usdRisk: 'Or risk in $', usdGain: 'Or target in $', usdNeed: 'Pick Buy / Sell and the entry price first.', unit: 'Enter as', px: 'Price', usd: '$ amount', rRisk: 'Stop loss ($)', rGain: 'Take profit ($)', sl: 'Stop loss (SL)', tp: 'Take profit (TP)', rRes: 'Result ($)', eq: '= {v}', multi: '+ Several entries or exits', recap: 'Recap', plan: 'Plan', exec: 'In your plan', review: 'Review', lesson: 'Lesson', none: '—', done: 'Done', todo: 'To do', pre: 'Pre-market', post: 'Post-market', fill: 'To fill in', open: 'Open', close: 'Close', bias: { bullish: 'Long', bearish: 'Short', neutral: 'Neutral', no_trade: 'No trading' }, followed: { yes: 'Plan followed', partly: 'Plan partly followed', no: 'Plan not followed' } },
    fr: { add: 'Ajouter un trade', addDay: 'Ajouter un trade ce jour-là', usdExit: 'Ou le résultat en $', usdExitPh: 'ex. -350', usdRisk: 'Ou le risque en $', usdGain: 'Ou l’objectif en $', usdNeed: 'Choisis Achat / Vente et le prix d’entrée d’abord.', unit: 'Saisir en', px: 'Prix', usd: 'Montant $', rRisk: 'Stop loss ($)', rGain: 'Take profit ($)', sl: 'Stop loss (SL)', tp: 'Take profit (TP)', rRes: 'Résultat ($)', eq: '= {v}', multi: '+ Plusieurs entrées ou sorties', recap: 'Récap', plan: 'Plan', exec: 'Dans ton plan', review: 'Revue', lesson: 'Leçon', none: '—', done: 'Faite', todo: 'À faire', pre: 'Pré-marché', post: 'Post-marché', fill: 'À compléter', open: 'Ouvrir', close: 'Fermer', bias: { bullish: 'Long', bearish: 'Short', neutral: 'Neutre', no_trade: 'Pas de trading' }, followed: { yes: 'Plan suivi', partly: 'Plan suivi en partie', no: 'Plan non suivi' } },
    es: { add: 'Añadir una operación', addDay: 'Añadir una operación ese día', usdExit: 'O el resultado en $', usdExitPh: 'ej. -350', usdRisk: 'O el riesgo en $', usdGain: 'O el objetivo en $', usdNeed: 'Elige Compra / Venta y el precio de entrada primero.', unit: 'Introducir en', px: 'Precio', usd: 'Importe $', rRisk: 'Stop loss ($)', rGain: 'Take profit ($)', sl: 'Stop loss (SL)', tp: 'Take profit (TP)', rRes: 'Resultado ($)', eq: '= {v}', multi: '+ Varias entradas o salidas', recap: 'Resumen', plan: 'Plan', exec: 'En tu plan', review: 'Revisión', lesson: 'Lección', none: '—', done: 'Hecha', todo: 'Pendiente', pre: 'Pre-mercado', post: 'Post-mercado', fill: 'Por completar', open: 'Abrir', close: 'Cerrar', bias: { bullish: 'Long', bearish: 'Short', neutral: 'Neutral', no_trade: 'No operar' }, followed: { yes: 'Plan seguido', partly: 'Plan seguido en parte', no: 'Plan no seguido' } } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const PLUS = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/></svg>';

  /* 1. « Add a trade » in the title row of Trades, Calendar and Journal (the Journal day: on that day); never on Today */
  function addButton() {
    const top = document.querySelector('.main-wrap .top'); if (!top) return;
    const v = (location.hash.slice(1).split('/')[0] || 'dashboard');
    let b = top.querySelector('.nav-addtop');
    const want = ['trades', 'calendar', 'journal'].includes(v);   // (31 Oct., A3) not on Today: the rail's « + » (N) and the Execution step are enough
    if (!want) { if (b) b.hidden = true; return; }
    const m = /^#journal\/(\d{4}-\d{2}-\d{2})/.exec(location.hash);
    const day = m ? m[1] : (v === 'journal' ? (document.querySelector('#main [data-act="add-trade"][data-date]') || {}).dataset?.date : '');
    if (!b) { b = document.createElement('button'); b.type = 'button'; b.className = 'nav-addtop'; b.setAttribute('data-noi18n', ''); b.setAttribute('data-act', 'add-trade'); top.append(b); }
    b.hidden = false;
    if (day) b.dataset.date = day; else delete b.dataset.date;
    const label = day && day !== (typeof todayStr === 'function' ? todayStr() : '') ? t('addDay') : t('add');
    const html = `${PLUS}<span>${label}</span>`; if (b.innerHTML !== html) b.innerHTML = html;
    b.setAttribute('aria-label', label);
    // the Journal's own small link becomes a real button too
    const lk = document.querySelector('#main .sec-h [data-act="add-trade"][data-date]');
    if (lk && !lk.classList.contains('nav-addday')) { lk.classList.remove('link'); lk.classList.add('btn', 'sm', 'nav-addday'); /* a neutral button: the page's one primary action is elsewhere (5, 15.1) */ lk.innerHTML = `${PLUS}<span>${t('addDay')}</span>`; lk.setAttribute('data-noi18n', ''); }
  }

  // (2 Nov., audit « transfuge » G2) no « + Add a trade » row on top of the trades list any more: the title row's button is enough

  /* 2. the form: « several entries or exits » right under the entry price; amounts in $ that fill the prices */
  const mem = {};
  const inst = () => { try { return instOf(TK.inst); } catch (e) { return null; } };
  const perPoint = () => { const i = inst(); return i ? i.tickC / 100 / i.tick : null; };   // $ per point per contract
  const roundTick = (p) => { const i = inst(); return i ? Math.round(p / i.tick) * i.tick : p; };
  const num = (v) => { const s = String(v == null ? '' : v).replace(/[\s\u00a0$]/g, '').replace(',', '.'); return s === '' || s === '-' || !isFinite(+s) ? null : +s; };
  function setTk(k, val) {
    const el = document.querySelector(`#tkSlide [data-tk="${k}"]`); if (!el || el.value === String(val)) return;   // unchanged: nothing to redraw
    el.value = String(val); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function posBase() {
    // several executions: the average entry and the size of the whole position, like the platforms
    if (TK && TK.multi && typeof positionOf === 'function') { try { const p = positionOf(tkExecs(), TK.inst); if (p && p.avgEntry) return { e: p.avgEntry, q: p.maxQty || Math.abs(p.open || 0) || 1, dir: p.dir || TK.dir }; } catch (x) { /* form not ready */ } }
    return { e: num(TK && TK.entry), q: num(TK && TK.qty) || 1, dir: TK && TK.dir };
  }
  function usdApply(kind, raw) {
    const base = posBase(), v = num(raw), e = base.e, q = base.q, pp = perPoint(), dir = base.dir;
    if (v == null || e == null || !pp || !dir) return false;
    const sign = dir === 'short' ? -1 : 1, pts = Math.abs(v) / (pp * q);
    if (kind === 'exit') setTk('exit', roundTick(e + sign * (v / (pp * q))).toFixed(2));
    if (kind === 'stop') setTk('stop', roundTick(e - sign * pts).toFixed(2));
    if (kind === 'target') setTk('target', roundTick(e + sign * pts).toFixed(2));
    return true;
  }
  const unitMode = { st: 'px', ex: 'px' };
  function usdRow(kinds, grp) {
    const row = document.createElement('div'); row.className = 'nav-usd ' + grp; row.setAttribute('data-noi18n', '');
    const lab = (k) => t(k === 'exit' ? 'rRes' : k === 'stop' ? 'rRisk' : 'rGain');
    row.innerHTML = kinds.map((k) => `<label class="tk-f"><span>${lab(k)}</span><div class="tk-in"><input inputmode="decimal" autocomplete="off" data-usd="${k}" placeholder="${k === 'exit' ? t('usdExitPh') : '$'}" value="${esc2(mem[k] || '')}"></div><small class="nav-usd-eq" data-eq="${k}"></small></label>`).join('') + `<small class="nav-usd-need" hidden>${t('usdNeed')}</small>`;
    row.addEventListener('input', (ev) => {
      const i = ev.target.closest('[data-usd]'); if (!i) return;
      mem[i.dataset.usd] = i.value;
      const ok = i.value.trim() === '' || usdApply(i.dataset.usd, i.value);
      row.querySelector('.nav-usd-need').hidden = ok;
      eqLines(row);
    });
    return row;
  }
  function eqLines(row) {
    row.querySelectorAll('[data-eq]').forEach((el) => { const k = el.dataset.eq, v = TK && TK[k]; const txt = mem[k] && v !== '' && v != null ? t('eq').replace('{v}', (+v).toFixed(2)) : ''; if (el.textContent !== txt) el.textContent = txt; });
  }
  function unitSwitch(grp) {
    const sw = document.createElement('div'); sw.className = 'nav-unit ' + grp; sw.setAttribute('data-noi18n', ''); sw.setAttribute('role', 'tablist');
    sw.innerHTML = `<span>${t('unit')}</span><div class="seg"><button type="button" role="tab" data-unit="px" data-grp="${grp}">${t('px')}</button><button type="button" role="tab" data-unit="usd" data-grp="${grp}">${t('usd')}</button></div>`;
    return sw;
  }
  function applyUnit(tk, grp) {
    const sw = tk.querySelector('.nav-unit'), row = tk.querySelector('.nav-usd.' + grp);
    const priceRow = grp === 'st' ? (tk.querySelector('[data-tk="stop"]') || {}).closest?.('.tk-row2') : (tk.querySelector('[data-tk="exit"]') || {}).closest?.('.tk-row2');
    const usd = unitMode[grp] === 'usd';
    if (sw) sw.querySelectorAll('[data-unit]').forEach((b) => { const on = b.dataset.unit === unitMode[grp]; b.classList.toggle('on', on); b.setAttribute('aria-selected', String(on)); });
    if (row) row.hidden = !usd;
    // the exit row also holds the exit time: in $ mode only its price box steps aside
    if (priceRow) { if (grp === 'st') priceRow.classList.toggle('nav-hide', usd); else { const pf = priceRow.querySelector('[data-tk="exit"]'); const lab = pf && pf.closest('.tk-f'); if (lab) lab.classList.toggle('nav-hide', usd); } }
    if (row) eqLines(row);
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.nav-unit [data-unit]'); if (!b) return;
    unitMode.st = unitMode.ex = b.dataset.unit;
    const tk = document.querySelector('#tkSlide.open'); if (!tk) return;
    applyUnit(tk, 'st'); applyUnit(tk, 'ex');
    const first = tk.querySelector(b.dataset.unit === 'usd' ? '.nav-usd:not([hidden]) input' : '[data-tk="exit"], [data-tk="stop"]');
    if (first) first.focus();
  });
  function formExtras() {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || typeof TK === 'undefined' || !TK) return;
    const stop = tk.querySelector('[data-tk="stop"]'), sRow = stop && stop.closest('.tk-row2');
    let anchor = sRow;
    if (!TK.multi) {
      // entry and exit side by side, then the initial take profit and stop loss below
      const entry = tk.querySelector('[data-tk="entry"]'), eLab = entry && entry.closest('.tk-f');
      const exit = tk.querySelector('[data-tk="exit"]'), xLab = exit && exit.closest('.tk-f');
      if (eLab && xLab) {
        let row = tk.querySelector('.nav-ee');
        if (!row) { row = document.createElement('div'); row.className = 'tk-row2 nav-ee'; eLab.before(row); }
        if (eLab.parentElement !== row) row.prepend(eLab);
        if (xLab.parentElement !== row) { if (row.firstElementChild === eLab) eLab.after(xLab); else row.append(xLab); }
        if (!row.querySelector('.nav-usd.ex')) row.append(usdRow(['exit'], 'ex'));
        if (!tk.querySelector('.nav-multi')) { const a = document.createElement('button'); a.type = 'button'; a.className = 'link nav-multi'; a.setAttribute('data-noi18n', ''); a.setAttribute('data-act', 'tk-multi'); a.textContent = t('multi'); row.after(a); }
        // the « exit at target / exit at stop » shortcuts sit right under the exit price
        const at = tk.querySelector('[data-act="tk-exitat"]'), atRow = at && at.closest('.row');
        if (atRow && row.nextElementSibling !== atRow) { atRow.classList.add('nav-exitat'); row.after(atRow); }
        anchor = row;
      }
    }
    [['stop', 'sl'], ['target', 'tp']].forEach(([k, lab]) => { const sp = tk.querySelector(`.tk-f:has([data-tk="${k}"]) > span`); if (sp && sp.textContent !== t(lab)) { sp.textContent = t(lab); sp.setAttribute('data-noi18n', ''); } });
    if (unitMode.st === 'usd') ['stop', 'target'].forEach((k) => { if (mem[k]) usdApply(k, mem[k]); });   // executions or size changed: same $ amounts, new prices
    if (sRow && !tk.querySelector('.nav-usd.st')) sRow.after(usdRow(['stop', 'target'], 'st'));
    // one « Price | $ amount » switch, right above the prices it changes
    if (anchor) { let sw = tk.querySelector('.nav-unit'); if (!sw) { sw = unitSwitch('all'); anchor.before(sw); } else if (sw.nextElementSibling !== anchor) anchor.before(sw); }
    if (sRow) applyUnit(tk, 'st');
    if (!TK.multi) applyUnit(tk, 'ex');
  }
  new window.SweepMO((recs) => {
    if (!document.querySelector('#tkSlide.open')) { for (const k in mem) delete mem[k]; unitMode.st = unitMode.ex = 'px'; return; }
    if (recs.every((r) => r.target.closest && r.target.closest('.nav-usd, .nav-multi, .nav-unit'))) return;
    try { formExtras(); } catch (e) { /* never blocks */ }
  }).observe(document.body, { childList: true, subtree: true });

  /* 3. Journal day: a recap at the top; pre- and post-market folded into one line each until opened */
  const opened = new Set();
  /* (31 Oct., B4) « In your plan » counted once, by the server (game_days.compliant_count), as Today's Execution step says it */
  const GD = {};
  function gameDay(day, k) {
    const st = window.SweepGame && SweepGame.state && SweepGame.state();
    for (const k of ['today', 'yesterday']) { const d = st && st[k]; if (d && d.day === day) return { n: +d.trades || 0, c: d.plan_valid ? +d.compliant || 0 : 0 }; }
    if (day in GD && (!GD[day] || GD[day].k === k)) return GD[day];   // read again when the day's trades change
    GD[day] = null;
    if (typeof apiJSON === 'function') apiJSON(`api/game/history?from=${day}&to=${day}`).then((r) => { const d = (r && r.days || [])[0]; GD[day] = Object.assign(d ? { n: +d.trades_count || 0, c: +d.plan_valid ? +d.compliant_count || 0 : 0 } : { n: 0, c: 0 }, { k }); journalRecap(); }).catch(() => {});
    return null;
  }
  function journalRecap() {
    const m = /^#journal\/(\d{4}-\d{2}-\d{2})$/.exec(location.hash) || (/^#journal$/.test(location.hash) || location.hash === '#journal/' ? [null, (document.querySelector('#main [data-act="add-trade"][data-date]') || {}).dataset?.date] : null);
    if (!m || !m[1]) return;
    const day = m[1], main = document.getElementById('main');
    const stat = main.querySelector('.statline'); if (!stat) return;
    const j = (typeof getDoc === 'function' && getDoc('journals', day)) || {}, pre = j.pre || {}, post = j.post || {};
    const trades = (S.trades || []).filter((x) => x.date === day && !x.demo);
    const g = window.SweepGame && SweepGame.summary ? null : null;
    const biasTxt = pre.bias ? ((t('bias')[pre.bias] || pre.bias) + (Array.isArray(pre.setups) && pre.setups.length ? ' · ' + pre.setups.slice(0, 2).join(', ') : '')) : t('fill');
    const reviewed = !!(post.reviewed_at || (post.well || '').trim() || (post.tomorrow || '').trim() || (post.lesson || '').trim() || (post.wrong || '').trim());
    const lesson = (post.lesson || post.tomorrow || post.well || '').trim();
    const gd = trades.length ? gameDay(day, trades.length) : null;
    const inPlan = !trades.length ? t('none') : gd ? `${gd.c} / ${gd.n || trades.length}` : '…';
    const html = `<div class="nav-recap" data-noi18n><h3>${t('recap')}</h3><div class="nav-recap-g">
      <div><span>${t('plan')}</span><b>${esc2(biasTxt)}</b></div>
      <div><span>${t('exec')}</span><b>${inPlan}</b></div>
      <div><span>${t('review')}</span><b class="${reviewed ? 'pos' : ''}">${reviewed ? '✓ ' + t('done') : t('todo')}</b></div>
      <div class="w"><span>${t('lesson')}</span><b>${lesson ? esc2(lesson.length > 140 ? lesson.slice(0, 140) + '…' : lesson) : t('none')}</b></div></div></div>`;
    let rc = main.querySelector('.nav-recap');
    if (!rc) { stat.insertAdjacentHTML('afterend', html); }
    else if (rc.outerHTML.replace(/\s+/g, '') !== html.replace(/\s+/g, '')) rc.outerHTML = html;
    // fold the two long forms
    main.querySelectorAll('.cols.even > section').forEach((sec, i) => {
      const key = day + '|' + i, h = sec.querySelector('.sec-h'), body = sec.querySelector('.surface'); if (!h || !body) return;
      const filled = i === 0 ? !!(pre.bias || (pre.levels || '').trim() || (pre.scenario || '').trim() || (pre.plan || '').trim()) : reviewed || !!post.followed;
      const sum = i === 0 ? (pre.bias ? biasTxt + ((pre.levels || '').trim() ? ' · ' + (pre.levels || '').trim().slice(0, 40) : '') : t('fill'))
        : (post.followed ? t('followed')[post.followed] : '') + (lesson ? (post.followed ? ' · ' : '') + lesson.slice(0, 60) : '') || t('fill');
      sec.classList.add('nav-fold'); const open = opened.has(key);
      sec.classList.toggle('open', open);
      let bar = h.querySelector('.nav-fold-t');
      const barHtml = `<span class="nav-fold-s ${filled ? '' : 'todo'}">${esc2(sum)}</span><span class="nav-fold-c">${open ? t('close') : t('open')}</span>`;
      if (!bar) { bar = document.createElement('button'); bar.type = 'button'; bar.className = 'nav-fold-t'; bar.setAttribute('data-noi18n', ''); bar.dataset.key = key; h.append(bar); h.classList.add('nav-fold-h'); }
      if (bar.innerHTML !== barHtml) bar.innerHTML = barHtml;
      bar.setAttribute('aria-expanded', String(open));
    });
  }
  document.addEventListener('click', (e) => {
    const h = e.target.closest && e.target.closest('.nav-fold-h'); if (!h) return;
    const bar = h.querySelector('.nav-fold-t'), key = bar && bar.dataset.key; if (!key) return;
    opened.has(key) ? opened.delete(key) : opened.add(key);
    try { journalRecap(); } catch (x) { /* never blocks */ }
  });

  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__addj) {
    const w = function () { const out = appRender.apply(this, arguments); [addButton, journalRecap].forEach((f) => { try { f(); } catch (e) { /* never blocks */ } }); return out; };
    w.__addj = true; window.render = w;
  }
})();

/* ───────────── several executions: add to the position, partial exits, live average like the platforms ───────────── */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { add: '+ Add to the position', partial: '+ Partial exit', rest: 'Exit the rest', avg: 'Average entry', size: 'Contracts', open: 'Still open', avgx: 'Average exit', real: 'Realized', tagIn: 'Entry', tagAdd: 'Add', tagPart: 'Partial exit', tagOut: 'Exit', closed: 'Position closed', axP: 'Exit price', axT: 'Exit time (ET)', axH: 'Closes what is still open.' },
    fr: { add: '+ Ajouter à la position', partial: '+ Sortie partielle', rest: 'Sortir le reste', avg: 'Prix moyen d’entrée', size: 'Contrats', open: 'Encore ouverts', avgx: 'Prix moyen de sortie', real: 'Réalisé', tagIn: 'Entrée', tagAdd: 'Ajout', tagPart: 'Sortie partielle', tagOut: 'Sortie', closed: 'Position fermée', axP: 'Prix de sortie', axT: 'Heure de sortie (ET)', axH: 'Ferme ce qui reste ouvert.' },
    es: { add: '+ Añadir a la posición', partial: '+ Salida parcial', rest: 'Cerrar el resto', avg: 'Entrada media', size: 'Contratos', open: 'Aún abiertos', avgx: 'Salida media', real: 'Realizado', tagIn: 'Entrada', tagAdd: 'Añadido', tagPart: 'Salida parcial', tagOut: 'Salida', closed: 'Posición cerrada', axP: 'Precio de salida', axT: 'Hora de salida (ET)', axH: 'Cierra lo que sigue abierto.' } };
  const t = (k) => (T[L] || T.en)[k];
  const $m = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));
  const fx = (n) => (n == null || !isFinite(n) ? '—' : (Math.round(n * 100) / 100).toLocaleString(L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));

  /* the exit price stays in the form with several executions: it becomes a final exit line (hidden in the list),
     always last and sized on what is still open — the trader can type it before or after adding to the position */
  const AX = { tk: null, price: '', time: '' };
  const axFor = () => { if (AX.tk !== TK) { AX.tk = TK; AX.price = ''; AX.time = ''; } return AX; };
  const numx = (v) => { const s = String(v == null ? '' : v).replace(/[\s\u00a0]/g, '').replace(',', '.'); return s === '' || !isFinite(+s) ? null : +s; };
  function wantAuto() {
    const ax = axFor(), p = numx(ax.price); if (p == null) return null;
    const manual = TK.execs.filter((x) => !x.auto), saved = TK.execs; TK.execs = manual;
    let pos; try { pos = positionOf(tkExecs(), TK.inst); } finally { TK.execs = saved; }
    const open = Math.abs(pos.open || 0); if (!open || !pos.dir) return null;
    const last = manual[manual.length - 1], tm = (ax.time && typeof hms === 'function' && hms(ax.time)) || (last && last.t ? last.t.slice(11, 19) : '09:30:00');
    return { id: 'ax', side: pos.dir === 'short' ? 'buy' : 'sell', qty: open, price: String(p), t: `${TK.date} ${tm}`, auto: true };
  }
  function ensureAuto() {   // true when the final exit line changed
    if (!TK || !TK.multi) return false;
    const cur = TK.execs.find((x) => x.auto), want = wantAuto();
    const same = (!cur && !want) || (cur && want && cur.qty === want.qty && cur.price === want.price && cur.side === want.side && cur.t === want.t && TK.execs[TK.execs.length - 1] === cur);
    if (same) return false;
    TK.execs = TK.execs.filter((x) => !x.auto); if (want) TK.execs.push(want);
    return true;
  }
  function pushRow(kind) {
    if (typeof TK === 'undefined' || !TK) return;
    if (!TK.multi) {
      // an exit already typed in the simple form is kept as the final exit
      const ax = axFor(); if (numx(TK.exit) != null) { ax.price = String(TK.exit); ax.time = TK.exitTime || ''; }
      const ex = TK.exit; TK.exit = ''; TK.execs = tkExecs(); TK.exit = ex; TK.multi = true;
    }
    if (kind === 'rest') axFor().price = '';   // « exit the rest » by hand replaces the final exit
    TK.execs = TK.execs.filter((x) => !x.auto);
    const pos = positionOf(tkExecs(), TK.inst), last = TK.execs.at(-1);
    const dir = pos.dir || TK.dir || 'long', inSide = dir === 'short' ? 'sell' : 'buy', outSide = dir === 'short' ? 'buy' : 'sell';
    const open = Math.abs(pos.open || 0) || (+TK.qty || 1);
    const row = { id: typeof uid === 'function' ? uid() : String(Date.now()), side: kind === 'add' ? inSide : outSide, qty: kind === 'rest' ? open : 1, price: last ? last.price : (TK.entry || ''), t: last ? last.t : `${TK.date} ${(typeof hms === 'function' && hms(TK.entryTime)) || '09:30:00'}` };
    TK.execs.push(row);
    ensureAuto();
    tkRefresh({ panel: true });
    // put the cursor on the new price
    setTimeout(() => {
      const rows = document.querySelectorAll('#tkSlide .tk-ex'), r = rows[rows.length - 1]; if (!r) return;
      r.classList.add('nav-new'); setTimeout(() => r.classList.remove('nav-new'), 1600);
      r.scrollIntoView({ block: 'center', behavior: 'smooth' });
      const i = r.querySelector('[data-tkx="price"]'); if (i) { i.focus({ preventScroll: true }); i.select && i.select(); }
    }, 60);
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-px]'); if (!b) return;
    e.preventDefault(); pushRow(b.dataset.px);
  });

  /* the live position, and a tag on each execution (entry, add, partial exit, exit) */
  function panel() {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || typeof TK === 'undefined' || !TK) return;
    // simple form: the two shortcuts sit right under the entry price (they replace « several entries or exits »)
    if (!TK.multi) {
      const m = tk.querySelector('.nav-multi'); if (m && !m.dataset.px2) { m.dataset.px2 = '1'; m.outerHTML = `<div class="nav-px nav-multi" data-noi18n data-px2="1"><button type="button" class="link" data-px="add">${t('add')}</button><button type="button" class="link" data-px="partial">${t('partial')}</button></div>`; }
      return;
    }
    const list = tk.querySelector('.tk-exs'); if (!list) return;
    if (ensureAuto()) { tkRefresh({ panel: true }); return; }
    const execF = list.closest('.tk-f'), avgF = (tk.querySelector('#tkAvg') || {}).closest?.('.tk-f');
    // the exit fields, right under the executions
    const ax = axFor(); let axBox = tk.querySelector('.nav-ax');
    if (!axBox && execF) { axBox = document.createElement('div'); axBox.className = 'tk-row2 nav-ax'; axBox.setAttribute('data-noi18n', '');
      axBox.innerHTML = `<label class="tk-f"><span>${t('axP')}</span><div class="tk-in"><input data-ax="price" inputmode="decimal" autocomplete="off" value="${String(ax.price).replace(/"/g, '')}"></div></label><label class="tk-f"><span>${t('axT')}</span><div class="tk-in"><input data-ax="time" data-wheel="time" placeholder="hh:mm:ss" value="${String(ax.time).replace(/"/g, '')}"></div></label><small class="nav-ax-h">${t('axH')}</small>`; }
    if (axBox && execF && execF.nextElementSibling !== axBox) execF.after(axBox);
    if (execF && avgF && avgF.nextElementSibling !== execF) avgF.after(execF);   // same place as the entry price: the eye does not search
    let st; try { st = positionOf(tkExecs(), TK.inst); } catch (e) { return; }
    // tags
    const rows = [...list.querySelectorAll('.tk-ex')];
    let running = 0, firstDone = false; const dir = st.dir;
    rows.forEach((r, i) => {
      const ex = TK.execs[i]; if (!ex) return;
      r.classList.toggle('nav-auto', !!ex.auto); if (ex.auto) return;   // the final exit is typed in « Exit price »
      const q = Math.abs(+ex.qty || 0), isIn = dir ? (ex.side === (dir === 'short' ? 'sell' : 'buy')) : true;
      let tag;
      if (isIn) { tag = firstDone ? t('tagAdd') : t('tagIn'); firstDone = true; running += q; }
      else { running -= q; tag = running > 0 ? t('tagPart') : t('tagOut'); }
      let el = r.querySelector('.nav-extag'); if (!el) { el = document.createElement('span'); el.className = 'nav-extag'; el.setAttribute('data-noi18n', ''); r.prepend(el); }
      if (el.textContent !== tag) el.textContent = tag;
      el.className = 'nav-extag ' + (isIn ? 'in' : 'out');
    });
    // summary
    const html = `<div class="nav-pos-g"><div><span>${t('avg')}</span><b>${fx(st.avgEntry)}</b></div><div><span>${t('size')}</span><b>${st.maxQty || 0}</b></div><div><span>${st.closed ? t('closed') : t('open')}</span><b class="${st.closed ? 'pos' : ''}">${st.closed ? '✓' : Math.abs(st.open || 0)}</b></div>${st.avgExit != null ? `<div><span>${t('avgx')}</span><b>${fx(st.avgExit)}</b></div><div><span>${t('real')}</span><b class="${st.realized_c < 0 ? 'neg' : 'pos'}">${$m(st.realized_c || 0)}</b></div>` : ''}</div>
      <div class="nav-px" data-noi18n><button type="button" class="btn sm" data-px="add">${t('add')}</button><button type="button" class="btn sm" data-px="partial">${t('partial')}</button>${!st.closed && Math.abs(st.open || 0) > 0 && st.avgExit != null ? `<button type="button" class="btn sm" data-px="rest">${t('rest')}</button>` : ''}</div>`;
    let box = tk.querySelector('.nav-pos');
    if (!box) { box = document.createElement('div'); box.className = 'nav-pos'; box.setAttribute('data-noi18n', ''); list.before(box); }
    if (box._h !== html) { box.innerHTML = html; box._h = html; }
    const old = tk.querySelector('[data-act="tk-exadd"]'); if (old) old.hidden = true;   // replaced by the two clear buttons
  }
  new window.SweepMO((recs) => {
    if (!document.querySelector('#tkSlide.open')) return;
    if (recs.every((r) => r.target.closest && r.target.closest('.nav-pos, .nav-extag, .nav-px'))) return;
    try { panel(); } catch (e) { /* never blocks */ }
  }).observe(document.body, { childList: true, subtree: true });
  // typing a price or a quantity updates the position at once
  document.addEventListener('input', (e) => {
    const a = e.target.closest && e.target.closest('#tkSlide [data-ax]');
    if (a) { axFor()[a.dataset.ax] = a.value; if (ensureAuto()) tkRefresh(); setTimeout(() => { try { panel(); } catch (x) { /* never blocks */ } }, 0); return; }
    if (e.target.closest && e.target.closest('#tkSlide .tk-ex')) setTimeout(() => { try { if (ensureAuto()) tkRefresh(); panel(); } catch (x) { /* never blocks */ } }, 0);
  });
})();


/* ───────────── Ask Sweep follows you: the floating button on every page, with questions about the page you are on ───────────── */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const Q = {
    en: { trade: (d) => [`Analyse my ${d} trade`, 'What could I have done better on this trade?', 'Does this setup work for me?'], journal: ['Debrief my day', 'What keeps coming back in my mistakes?', 'How was my discipline this week?'], stats: ['What costs me the most?', 'When do I trade best?', 'Which setup makes me the most money?'], cal: ['What is on the economic calendar today?', 'How did I do this month?', 'Which day of the week is my best?'], acc: ['How much room before my drawdown?', 'When can I ask for a payout?', 'Which account is doing best?'], trades: ['How did I do this week?', 'What is my win rate on longs vs shorts?', 'Which setup makes me the most money?'] },
    fr: { trade: (d) => [`Analyse mon trade ${d}`, 'Qu’est-ce que j’aurais pu mieux faire sur ce trade ?', 'Ce setup fonctionne-t-il pour moi ?'], journal: ['Débriefe ma journée', 'Qu’est-ce qui revient dans mes erreurs ?', 'Comment était ma discipline cette semaine ?'], stats: ['Qu’est-ce qui me coûte le plus ?', 'À quel moment je trade le mieux ?', 'Quel setup me rapporte le plus ?'], cal: ['Qu’y a-t-il au calendrier économique aujourd’hui ?', 'Comment s’est passé mon mois ?', 'Quel jour de la semaine est mon meilleur ?'], acc: ['Combien de marge avant mon drawdown ?', 'Quand pourrai-je demander un payout ?', 'Quel compte performe le mieux ?'], trades: ['Comment s’est passée ma semaine ?', 'Mon taux de réussite en long vs en short ?', 'Quel setup me rapporte le plus ?'] },
    es: { trade: (d) => [`Analiza mi operación ${d}`, '¿Qué pude hacer mejor en esta operación?', '¿Este setup funciona para mí?'], journal: ['Resume mi día', '¿Qué se repite en mis errores?', '¿Cómo fue mi disciplina esta semana?'], stats: ['¿Qué me cuesta más?', '¿Cuándo opero mejor?', '¿Qué setup me da más dinero?'], cal: ['¿Qué hay hoy en el calendario económico?', '¿Cómo me fue este mes?', '¿Qué día de la semana es el mejor?'], acc: ['¿Cuánto margen antes de mi drawdown?', '¿Cuándo podré pedir un payout?', '¿Qué cuenta va mejor?'], trades: ['¿Cómo me fue esta semana?', '¿Mi tasa de acierto en largos vs cortos?', '¿Qué setup me da más dinero?'] } };
  const q = Q[L] || Q.en;
  let base = null;
  function pageStarters() {
    const h = location.hash || '#dashboard', v = h.slice(1).split('/')[0];
    if (v === 'trade') {
      const id = decodeURIComponent(h.split('/')[1] || ''), t = typeof getDoc === 'function' && getDoc('trades', id);
      if (t) { const dd = new Date(t.date + 'T12:00:00').toLocaleDateString(L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA', { day: 'numeric', month: 'short' }); return q.trade(`${t.instrument || 'NQ'} ${t.direction === 'short' ? 'Short' : 'Long'} ${dd} ${(t.entry_time || '').slice(0, 5)}`.trim()); }
    }
    if (v === 'journal') return q.journal;
    if (v === 'analytics') return q.stats;
    if (v === 'calendar' || v === 'news') return q.cal;
    if (v === 'accounts' || v === 'account' || v === 'payouts') return q.acc;
    if (v === 'trades') return q.trades;
    return null;   // Today and the rest: the usual starters
  }
  (function wrap(n) {
    if (typeof window.askRender !== 'function' || typeof ASKL === 'undefined') { if (n < 60) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.askRender.__ctx) return;
    const orig = window.askRender;
    const w = function () {
      const dict = ASKL[L] || ASKL.en;
      if (!base) base = dict.starters.slice();
      dict.starters = pageStarters() || base;
      return orig.apply(this, arguments);
    };
    w.__ctx = true; window.askRender = w;
  })(0);
})();

/* ───────────── account: recalibrate the balance on the platform's real one ─────────────
 * When some trades were logged without their real P&L (slippage, fees), the account drifts from the platform.
 * The trader types the balance the platform shows; Sweep records the difference as a dated adjustment on the
 * account. Adjustments count in the balance, the account P&L and the drawdown margin — not in the trade statistics.
 *   account.adjustments = [{ id, at: 'YYYY-MM-DD', amount_c, note }] */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { t: 'Recalibrate on your platform', sub: 'Some trades were logged without their real P&L? Enter the balance your platform shows: Sweep adds the difference as an adjustment.', sweep: 'Balance in Sweep', real: 'Real balance (platform)', go: 'Recalibrate', none: 'Already matching.', hist: 'Adjustments', note: 'Recalibrated on the platform balance', undo: 'Remove', done: 'Balance recalibrated: {v}', added: 'Adjustment added: {v}', manual: 'Or add an adjustment in $', add: 'Add', manualNote: 'Manual P&L adjustment', total: 'Total adjustments' },
    fr: { t: 'Recalibrer sur ta plateforme', sub: 'Des trades enregistrés sans leur P&L réel ? Entre le solde affiché par ta plateforme : Sweep ajoute la différence comme ajustement.', sweep: 'Solde dans Sweep', real: 'Solde réel (plateforme)', go: 'Recalibrer', none: 'Déjà aligné.', hist: 'Ajustements', note: 'Recalibré sur le solde de la plateforme', undo: 'Retirer', done: 'Solde recalibré : {v}', added: 'Ajustement ajouté : {v}', manual: 'Ou ajoute un ajustement en $', add: 'Ajouter', manualNote: 'Ajustement manuel du P&L', total: 'Total des ajustements' },
    es: { t: 'Recalibrar con tu plataforma', sub: '¿Operaciones guardadas sin su P&L real? Introduce el saldo que muestra tu plataforma: Sweep añade la diferencia como ajuste.', sweep: 'Saldo en Sweep', real: 'Saldo real (plataforma)', go: 'Recalibrar', none: 'Ya coincide.', hist: 'Ajustes', note: 'Recalibrado con el saldo de la plataforma', undo: 'Quitar', done: 'Saldo recalibrado: {v}', added: 'Ajuste añadido: {v}', manual: 'O añade un ajuste en $', add: 'Añadir', manualNote: 'Ajuste manual del P&L', total: 'Total de ajustes' } };
  const t = (k) => (T[L] || T.en)[k];
  const $m = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));
  const toC = (v) => { const s = String(v == null ? '' : v).replace(/[\s\u00a0$]/g, '').replace(/,(?=\d{3}(\D|$))/g, '').replace(',', '.'); return s === '' || s === '-' || !isFinite(+s) ? null : Math.round(+s * 100); };
  const adjOf = (a) => (a && Array.isArray(a.adjustments) ? a.adjustments.reduce((s, x) => s + (+x.amount_c || 0), 0) : 0);
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

  // the balance, the account P&L and the drawdown margin include the adjustments
  (function wrap(n) {
    if (typeof window.acctState !== 'function') { if (n < 60) setTimeout(() => wrap(n + 1), 100); return; }
    if (window.acctState.__adj) return;
    const orig = window.acctState;
    const w = function (acc) {
      const r = orig.apply(this, arguments), adj = adjOf(acc);
      if (r && adj) { r.bal += adj; r.net += adj; if (r.buffer != null) r.buffer += adj; if (r.thr != null && r.bal <= r.thr) r.breached = true; r.adj = adj; }
      // (an account added « already running »: its adjustments are in acctState's drawdown path since 12 Oct., stop at the start
      // included — the old hwm_c override here ignored that stop and never followed later trades)
      return r;
    };
    w.__adj = true; window.acctState = w;
  })(0);
  (function wrapBal(n) {   // the accounts table and the totals use this one
    if (typeof window.acctBalance !== 'function') { if (n < 60) setTimeout(() => wrapBal(n + 1), 100); return; }
    if (window.acctBalance.__adj) return;
    const orig = window.acctBalance;
    const w = function (acc) { return orig.apply(this, arguments) + adjOf(acc); };
    w.__adj = true; window.acctBalance = w;
  })(0);

  /* ── (27 Oct., brief « pertes oubliées », step 2) a gap between the platform's balance and the journal, said in one tap:
   *  trades  → a « Trades not detailed » line on that day and account (a trade: in the P&L, the calendar and the firm's rules;
   *            no instrument, setup or checklist). « Add the detail »: each trade then logged on that account and day leaves the line.
   *  fees    → an adjustment (the recalibration) and the same amount as an expense in My money
   *  payout  → My money's payout form, filled in
   * The review sheet (« Close my day ») and « Recalibrate » both use it: window.SweepGap. */
  const GT = {
    en: { gapNeg: '{v} missing between your platform and your journal. What was it?', gapPos: '{v} more on your platform than in your journal. What was it?', trades: 'Trades I didn’t log', fees: 'Fees', payout: 'A payout', line: 'Trades not detailed', feesNote: 'Fees (platform balance)', lineAdded: 'Added: Trades not detailed {v}', feesAdded: 'Fees added: {v}', detail: 'Add the detail', lineWhat: 'The gap between your platform and your journal on {d}. It counts in your P&L and your firm’s rules. Add the detail: each trade you log on this account that day leaves this line.', lineLeft: 'Left to detail: {v}', del: 'Remove this line', note: '{v} not detailed: your win rate and your edge and leak don’t count them.', coach: 'Your journal said you had {a} left before your max loss. Your platform says {b}. That’s why every trade counts: I can only protect you from what I see.' },
    fr: { gapNeg: 'Il manque {v} entre ta plateforme et ton journal. C’était quoi ?', gapPos: 'Il y a {v} de plus sur ta plateforme que dans ton journal. C’était quoi ?', trades: 'Des trades pas notés', fees: 'Des frais', payout: 'Un payout', line: 'Trades non détaillés', feesNote: 'Frais (solde de la plateforme)', lineAdded: 'Ajouté : Trades non détaillés {v}', feesAdded: 'Frais ajoutés : {v}', detail: 'Ajouter le détail', lineWhat: 'L’écart entre ta plateforme et ton journal le {d}. Il compte dans ton P&L et les règles de ta firme. Ajoute le détail : chaque trade que tu notes sur ce compte ce jour-là sort de cette ligne.', lineLeft: 'Reste à détailler : {v}', del: 'Retirer cette ligne', note: '{v} non détaillés : ton taux de réussite et ta force/fuite ne les comptent pas.', coach: 'Ton journal disait qu’il te restait {a} avant ta perte max. Ta plateforme dit {b}. C’est pour ça que chaque trade compte : je ne peux te protéger que de ce que je vois.' },
    es: { gapNeg: 'Faltan {v} entre tu plataforma y tu diario. ¿Qué fue?', gapPos: 'Hay {v} más en tu plataforma que en tu diario. ¿Qué fue?', trades: 'Operaciones sin anotar', fees: 'Comisiones', payout: 'Un payout', line: 'Operaciones sin detallar', feesNote: 'Comisiones (saldo de la plataforma)', lineAdded: 'Añadido: Operaciones sin detallar {v}', feesAdded: 'Comisiones añadidas: {v}', detail: 'Añadir el detalle', lineWhat: 'La diferencia entre tu plataforma y tu diario el {d}. Cuenta en tu P&L y en las reglas de tu firma. Añade el detalle: cada operación que anotes en esta cuenta ese día sale de esta línea.', lineLeft: 'Queda por detallar: {v}', del: 'Quitar esta línea', note: '{v} sin detallar: tu tasa de acierto y tu fuerza/fuga no los cuentan.', coach: 'Tu diario decía que te quedaban {a} antes de tu pérdida máx. Tu plataforma dice {b}. Por eso cuenta cada operación: solo puedo protegerte de lo que veo.' } };
  const g = (k) => (GT[L] || GT.en)[k];
  const lineOf = (aid, day) => (S.trades || []).find((x) => x.untracked && x.account_id === aid && x.date === day);
  const gapKinds = (gap) => (gap < 0 ? ['trades', 'fees', 'payout'] : ['trades', 'fees']);   // more on the platform: never a payout
  const gapMsg = (gap) => g(gap < 0 ? 'gapNeg' : 'gapPos').replace('{v}', $m(gap));
  const gapChips = (gap, on, attr) => gapKinds(gap).map((k) => `<button type="button" class="chip ${on === k ? 'on' : ''}" ${attr}="${k}">${g(k)}</button>`).join('');
  function gapApply(aid, day, gap, kind) {
    const a = getDoc('accounts', aid); if (!a || !gap) return;
    if (kind === 'trades') {
      const r0 = !(S.settings && S.settings.gap_coach) && window.SweepCoach && SweepCoach.riskNow ? SweepCoach.riskNow(day) : null;   // (step 3) what the journal said was left
      const ln = lineOf(aid, day);
      if (ln) { editDoc('trades', ln.id, (d) => { d.pnl_c = (+d.pnl_c || 0) + gap; d.untracked = Object.assign({ gap_c: 0, detailed_c: 0 }, d.untracked, { gap_c: ((d.untracked || {}).gap_c || 0) + gap }); }); }
      else put('trades', { id: 'ut' + uid(), account_id: aid, date: day, session_date: true, instrument: '', direction: '', contracts: 0, entry: null, exit: null, entry_time: '', exit_time: '',
        pnl_c: gap, fees_c: 0, pnl_manual: true, untracked: { gap_c: gap, detailed_c: 0 }, discipline: {}, emo: {}, review: {}, shots: [], setup: '', tags: [], notes: '' });
      if (typeof toast === 'function') toast(g('lineAdded').replace('{v}', $m(gap)));
      // the first gap a trader's platform shows: the coach says, once, what the journal hid (S.settings.gap_coach, kept on every device)
      if (r0) { const r1 = SweepCoach.riskNow(day); if (r1 && r1.left !== r0.left) put('settings', Object.assign(structuredClone(S.settings), { gap_coach: { day, before_c: r0.left, after_c: r1.left } })); }
    } else if (kind === 'fees') {
      const adj = { id: 'adj' + Date.now().toString(36), at: day, amount_c: gap, note: g('feesNote'), kind: 'fees' };
      editDoc('accounts', aid, (d) => { d.adjustments = [...(d.adjustments || []), adj]; });
      if (typeof billCan !== 'function' || billCan('payouts')) put('expenses', { id: uid(), date: day, firm_id: a.firm_id || '', account_id: aid, category: 'platform', amount_c: -gap, notes: g('feesNote'), adj_id: adj.id });   // (My money is a paid feature: on Free, the adjustment only)
      if (typeof toast === 'function') toast(g('feesAdded').replace('{v}', $m(gap)));
    } else if (kind === 'payout') {
      U.addP = true; U.editP = null; U.addPre = { account_id: aid, gross_c: -gap, amount_c: -gap, payment_date: day, prefill: true };
      U.mview = 'entries'; location.hash = '#payouts';
    }
  }
  // « Add the detail »: the next trades logged on that account and day (a form, a screenshot, an import) leave the line
  let detailing = null;   // { id, aid, day, until }
  const appPut = window.put;
  if (typeof appPut === 'function' && !appPut.__gap) {
    const w = function (col, doc) {
      const fresh = col === 'trades' && doc && !doc.untracked && !doc.demo && !(S.trades || []).some((x) => x.id === doc.id);
      const out = appPut.apply(this, arguments);
      try {
        const d = detailing;
        if (fresh && d && Date.now() < d.until && doc.account_id === d.aid && doc.date === d.day) {
          const ln = getDoc('trades', d.id), n = (+doc.pnl_c || 0) - (+doc.fees_c || 0);
          if (ln) {
            const left = (+ln.pnl_c || 0) - n;
            if (Math.abs(left) < 1) { remove('trades', ln.id); detailing = null; }
            else editDoc('trades', ln.id, (x) => { x.pnl_c = left; x.untracked = Object.assign({ gap_c: 0, detailed_c: 0 }, x.untracked); x.untracked.detailed_c = (x.untracked.detailed_c || 0) + n; });
          }
        }
      } catch (e) { /* never blocks a save */ }
      return out;
    };
    w.__gap = true; window.put = w;
  }
  function detail(id) {
    const ln = getDoc('trades', id); if (!ln) return;
    detailing = { id, aid: ln.account_id, day: ln.date, until: Date.now() + 3600e3 };
    if (typeof lsSet === 'function') lsSet('tj.last', Object.assign({}, lsGet('tj.last', {}), { account: ln.account_id, copyTo: [] }));   // the form opens on that account
    if (typeof openTicket === 'function') openTicket(null, { date: ln.date });
  }
  // (step 3) while a gap stays « not detailed »: a grey line on Stats and on the account page — information, not a fault (never gold)
  function noteHtml(lines) {
    const left = lines.reduce((s, x) => s + (+x.pnl_c || 0), 0); if (!lines.length || !left) return '';
    const last = lines.slice().sort((a, b) => String(b.date).localeCompare(String(a.date)))[0];
    return `<p class="ut-note" data-noi18n>${esc2(g('note').replace('{v}', typeof money === 'function' ? money(Math.abs(left), { sign: false, dec: 0 }) : $m(Math.abs(left))))} <button type="button" class="link" data-ut-go="${esc2(last.id)}">${esc2(g('detail'))} ›</button></p>`;
  }
  function paintNote() {
    const main = document.getElementById('main'); if (!main) return;
    const h = location.hash || '', m = /^#account\/([^/]+)/.exec(h), stats = /^#analytics/.test(h);
    let lines = [], host = null;
    if (m) { const id = decodeURIComponent(m[1]); lines = (S.trades || []).filter((x) => x.untracked && x.account_id === id); host = main.querySelector('.acard'); }
    else if (stats) { lines = (typeof ft === 'function' ? ft() : S.trades || []).filter((x) => x.untracked); host = main.querySelector('.fx') || main.firstElementChild; }
    const html = host ? noteHtml(lines) : '';
    let el = main.querySelector('.ut-note');
    if (!html) { if (el) el.remove(); return; }
    if (!el) { const w = document.createElement('div'); w.innerHTML = html; el = w.firstElementChild; host.after(el); }
    else if (el.outerHTML !== html) { const w = document.createElement('div'); w.innerHTML = html; el.replaceWith(w.firstElementChild); }
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-ut-go]'); if (b) detail(b.dataset.utGo); });
  const rnd = window.render;
  if (typeof rnd === 'function' && !rnd.__utNote) {
    const w = function () { const out = rnd.apply(this, arguments); try { paintNote(); } catch (e) { /* never blocks */ } return out; };
    w.__utNote = true; window.render = w;
  }
  /** the coach's sentence, the day of the first gap (null otherwise) */
  const u0 = (c) => (typeof money === 'function' ? money(c, { sign: false, dec: 0 }) : '$' + Math.round(c / 100));
  const coachGap = (day) => { const c = S.settings && S.settings.gap_coach; return c && c.day === day ? g('coach').replace('{a}', u0(c.before_c)).replace('{b}', u0(c.after_c)) : null; };
  window.SweepGap = { msg: gapMsg, chips: gapChips, kinds: gapKinds, apply: gapApply, lineOf, detail, word: g, coach: coachGap };

  function card() {
    const m = /^#account\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), a = typeof getDoc === 'function' && getDoc('accounts', id); if (!a) return;
    const main = document.getElementById('main'); if (!main) return;
    const st = acctState(a), list = (a.adjustments || []).slice().reverse();
    const html = `<div class="nav-recal-h"><h3>${t('t')}</h3><p>${t('sub')}</p></div>
      <div class="nav-recal-row"><div><span>${t('sweep')}</span><b>${typeof money === 'function' ? money(st.bal, { sign: false, dec: 2 }) : '$' + (st.bal / 100).toFixed(2)}</b></div>
        <label><span>${t('real')}</span><input inputmode="decimal" data-recal="bal" placeholder="$"></label>
        <button type="button" class="btn primary sm" data-recal-go="bal">${t('go')}</button></div>
      <div class="nav-recal-row sm"><label><span>${t('manual')}</span><input inputmode="decimal" data-recal="amt" placeholder="-150"></label><button type="button" class="btn sm" data-recal-go="amt">${t('add')}</button></div>
      <p class="nav-recal-msg" aria-live="polite"></p>
      ${list.length ? `<div class="nav-recal-hist"><div class="nav-recal-hh"><span>${t('hist')}</span><b class="${adjOf(a) < 0 ? 'neg' : 'pos'}">${t('total')} : ${$m(adjOf(a))}</b></div>${list.map((x) => `<div class="nav-recal-it"><span>${esc2(x.at)} · ${esc2(x.note || '')}</span><b class="${x.amount_c < 0 ? 'neg' : 'pos'}">${$m(x.amount_c)}</b><button type="button" class="link" data-recal-rm="${esc2(x.id)}">${t('undo')}</button></div>`).join('')}</div>` : ''}`;
    let box = main.querySelector('.nav-recal');
    if (!box) {
      const h = [...main.querySelectorAll('.sec-h h2')].find((e) => /^(Status|Statut|Estado)$/i.test(e.textContent.trim()));
      const sec = h && h.closest('section, .sec'); const host = sec || main.querySelector('.surface');
      if (!host) return;
      box = document.createElement('section'); box.className = 'surface nav-recal'; box.setAttribute('data-noi18n', ''); box.dataset.acc = id;
      if (sec) sec.append(box); else host.after(box);
    }
    if (box._h !== html) { const keep = [...box.querySelectorAll('[data-recal]')].map((i) => i.value); box.innerHTML = html; box._h = html; box.querySelectorAll('[data-recal]').forEach((i, k) => { if (keep[k]) i.value = keep[k]; }); }
  }
  document.addEventListener('click', (e) => {
    const go = e.target.closest && e.target.closest('[data-recal-go]'), rm = e.target.closest && e.target.closest('[data-recal-rm]'), k = e.target.closest && e.target.closest('[data-recal-k]');
    if (!go && !rm && !k) return;
    const box = e.target.closest('.nav-recal'), id = box && box.dataset.acc; if (!id) return;
    const a = getDoc('accounts', id); if (!a) return;
    const msg = box.querySelector('.nav-recal-msg');
    // (brief « pertes oubliées », step 2) the platform's balance: the gap, then what it was, as at « Close my day »
    if (k) { const gap = +box.dataset.gap || 0; if (!gap) return; gapApply(id, typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10), gap, k.dataset.recalK); box.dataset.gap = ''; msg.innerHTML = ''; box.querySelectorAll('[data-recal]').forEach((i) => { i.value = ''; }); setTimeout(() => render(), 80); return; }
    if (rm) { editDoc('accounts', id, (d) => { d.adjustments = (d.adjustments || []).filter((x) => x.id !== rm.dataset.recalRm); }); setTimeout(() => render(), 80); return; }
    const kind = go.dataset.recalGo, v = toC(box.querySelector(`[data-recal="${kind}"]`).value); if (v == null) return;
    const amt = kind === 'bal' ? v - acctState(a).bal : v;
    if (!amt) { msg.textContent = t('none'); return; }
    if (kind === 'bal') { box.dataset.gap = String(amt); msg.innerHTML = `<span>${esc2(gapMsg(amt))}</span><span class="g-chips-row wrap">${gapChips(amt, null, 'data-recal-k')}</span>`; return; }
    const entry = { id: 'adj' + Date.now().toString(36), at: typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10), amount_c: amt, note: kind === 'bal' ? t('note') : t('manualNote') };
    editDoc('accounts', id, (d) => { d.adjustments = [...(d.adjustments || []), entry]; });
    if (typeof toast === 'function') toast(t(kind === 'bal' ? 'done' : 'added').replace('{v}', $m(amt)));
    box.querySelectorAll('[data-recal]').forEach((i) => { i.value = ''; });
    setTimeout(() => render(), 80);
  });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__recal) {
    const w = function () { const out = appRender.apply(this, arguments); try { card(); } catch (e) { /* never blocks */ } return out; };
    w.__recal = true; window.render = w;
  }
})();

/* ───────────── account page: rename the account right in its title (pencil) ───────────── */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: ['Rename', 'Account name', 'Renamed'], fr: ['Renommer', 'Nom du compte', 'Compte renommé'], es: ['Renombrar', 'Nombre de la cuenta', 'Cuenta renombrada'] }[L] || ['Rename', 'Account name', 'Renamed'];
  const PEN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z M14 6l4 4" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round" stroke-linecap="round"/></svg>';
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  let editing = null;
  function crumb() {
    const m = /^#account\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), a = typeof getDoc === 'function' && getDoc('accounts', id); if (!a) return;
    const back = document.querySelector('#main > .row > a[href="#accounts"]'), span = back && back.parentElement.querySelector('span.muted'); if (!span) return;
    if (editing === id && span.querySelector('input')) return;
    const f = typeof firm === 'function' ? firm(a.firm_id) : null;
    const html = `${f ? esc2(f.name) + ' — ' : ''}<button type="button" class="nav-accname" data-ren="${esc2(id)}" title="${T[0]}" aria-label="${T[0]} : ${esc2(a.name)}"><span>${esc2(a.name)}</span>${PEN}</button>`;
    if (span._h !== html) { span.innerHTML = html; span._h = html; span.setAttribute('data-noi18n', ''); }
  }
  function startEdit(btn) {
    const id = btn.dataset.ren, a = getDoc('accounts', id); if (!a) return;
    editing = id;
    const span = btn.parentElement; span._h = null;
    btn.outerHTML = `<input class="nav-accname-in" data-ren-in="${esc2(id)}" value="${esc2(a.name)}" maxlength="60" aria-label="${T[1]}" enterkeyhint="done">`;
    const i = span.querySelector('input'); i.focus(); i.select();
  }
  function save(i, keep) {
    const id = i.dataset.renIn, v = i.value.trim(), a = getDoc('accounts', id);
    editing = null;
    if (keep && v && a && v !== a.name) { editDoc('accounts', id, (d) => { d.name = v; }); if (typeof toast === 'function') toast(T[2]); }
    setTimeout(() => { if (typeof render === 'function') render(); }, 60);
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-ren]'); if (b) { e.preventDefault(); startEdit(b); } });
  document.addEventListener('keydown', (e) => { const i = e.target.closest && e.target.closest('[data-ren-in]'); if (!i) return; if (e.key === 'Enter') { e.preventDefault(); i.blur(); } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); i.dataset.cancel = '1'; i.blur(); } }, true);   // first, before the app's own Escape
  document.addEventListener('focusout', (e) => { const i = e.target.closest && e.target.closest('[data-ren-in]'); if (i) save(i, !i.dataset.cancel); });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__ren) {
    const w = function () { const out = appRender.apply(this, arguments); try { crumb(); } catch (e) { /* never blocks */ } return out; };
    w.__ren = true; window.render = w;
  }
})();


/* ───────────── pre-market: a live chart and screenshots, in the plan and on the Journal day ─────────────
 * The chart is TradingView's free embed (the continuous contract of the trader's usual instrument).
 * Screenshots go through the app's own upload (same storage as trade screenshots), kept on the day's journal:
 *   journals[day].pre.shots = [{ id, name }] */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { t: 'Chart and screenshots', chart: 'Live chart', shots: 'Pre-market screenshots', add: '+ Add a screenshot', up: 'Uploading…', done: 'Screenshot added', fail: 'Upload failed', rm: 'Remove', open: 'Show the chart', hide: 'Hide the chart', note: 'TradingView chart · CME futures may be delayed on the free version.' },
    fr: { t: 'Graphique et captures', chart: 'Graphique en direct', shots: 'Captures du pré-marché', add: '+ Ajouter une capture', up: 'Téléversement…', done: 'Capture ajoutée', fail: 'Échec du téléversement', rm: 'Retirer', open: 'Afficher le graphique', hide: 'Masquer le graphique', note: 'Graphique TradingView · les futures CME peuvent être en différé dans la version gratuite.' },
    es: { t: 'Gráfico y capturas', chart: 'Gráfico en vivo', shots: 'Capturas del pre-mercado', add: '+ Añadir una captura', up: 'Subiendo…', done: 'Captura añadida', fail: 'Error al subir', rm: 'Quitar', open: 'Mostrar el gráfico', hide: 'Ocultar el gráfico', note: 'Gráfico de TradingView · los futuros CME pueden ir con retraso en la versión gratuita.' } };
  const t = (k) => (T[L] || T.en)[k];
  const SYM = { NQ: 'CME_MINI:NQ1!', MNQ: 'CME_MINI:MNQ1!', ES: 'CME_MINI:ES1!', MES: 'CME_MINI:MES1!', RTY: 'CME_MINI:RTY1!', M2K: 'CME_MINI:M2K1!', YM: 'CBOT_MINI:YM1!', MYM: 'CBOT_MINI:MYM1!', GC: 'COMEX:GC1!', MGC: 'COMEX:MGC1!', SI: 'COMEX:SI1!', CL: 'NYMEX:CL1!', MCL: 'NYMEX:MCL1!', '6E': 'CME:6E1!' };
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  let inst = null, tf = '5', chartOn = false;
  /** in the pre-market sheet, the chart shows the sheet's instrument (picked there) */
  const sheetInst = () => { const sh = document.querySelector('#gSheet.g-pm'), r = sh && String(sh.dataset.inst || ''); return r && SYM[r] && sh.querySelector('.pm-chart-slot') ? r : null; };
  function usual() {
    const si = sheetInst(); if (si) return si;
    if (inst) return inst;
    const c = {}; (S.trades || []).filter((x) => !x.demo).slice(-60).forEach((x) => { c[x.instrument] = (c[x.instrument] || 0) + 1; });
    const top = Object.entries(c).sort((a, b) => b[1] - a[1])[0];
    return (inst = top && SYM[top[0]] ? top[0] : 'NQ');
  }
  function frame() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark' || (document.documentElement.getAttribute('data-theme') !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
    const q = new URLSearchParams({ symbol: SYM[usual()] || SYM.NQ, interval: tf, theme: dark ? 'dark' : 'light', style: '1', timezone: 'America/New_York', hide_side_toolbar: '1', allow_symbol_change: '1', saveimage: '0', withdateranges: '0', locale: L === 'en' ? 'en' : L });
    return `<iframe class="nav-tv" loading="lazy" title="${esc2(t('chart'))}" src="https://s.tradingview.com/widgetembed/?${q}" referrerpolicy="origin" allow="fullscreen"></iframe>`;
  }
  function shotsOf(day) { const j = typeof getDoc === 'function' && getDoc('journals', day); return (j && j.pre && Array.isArray(j.pre.shots)) ? j.pre.shots : []; }
  /** parts: 'chart' (the pre-market levels, where they are read), 'shots' (the end of the pre-market), both (the Journal day) */
  function block(day, parts) {
    const shots = shotsOf(day), src = (id) => (typeof blobSrc === 'function' ? blobSrc(id) : 'uploads/' + encodeURIComponent(id)), c = parts !== 'shots', p = parts !== 'chart';
    return `<div class="nav-pre${parts ? ' nav-pre-' + parts : ''}" data-noi18n data-day="${esc2(day)}">
      ${c ? `<div class="nav-pre-h"><b>${t('chart')}</b>
        <div class="nav-pre-tools">${chartOn ? `${parts === 'chart' ? '' : `<div class="seg sm2">${Object.keys(SYM).filter((k) => ['NQ', 'ES', 'MNQ', 'MES', 'GC', 'MGC', 'CL', 'YM', 'RTY'].includes(k) || k === usual()).map((k) => `<button type="button" class="${k === usual() ? 'on' : ''}" data-pre-inst="${k}">${k}</button>`).join('')}</div>`}<div class="seg sm2">${['1', '5', '15', '60'].map((k) => `<button type="button" class="${k === tf ? 'on' : ''}" data-pre-tf="${k}">${k === '60' ? '1h' : k + 'm'}</button>`).join('')}</div>` : ''}
        <button type="button" class="link" data-pre-chart>${chartOn ? t('hide') : t('open')}</button></div></div>
      ${chartOn ? `<div class="nav-tv-wrap">${frame()}</div><small class="nav-pre-note">${t('note')}</small>` : ''}` : ''}
      ${p ? `<div class="nav-pre-h"><b>${t('shots')}</b><label class="link nav-pre-add">${t('add')}<input type="file" accept="image/png,image/jpeg,image/gif,image/webp" multiple hidden data-pre-up></label></div>
      ${shots.length ? `<div class="nav-pre-shots">${shots.map((x) => `<figure><a href="${src(x.id)}" target="_blank" rel="noopener"><img src="${src(x.id)}" alt="${esc2(x.name || '')}" loading="lazy"></a><button type="button" class="nav-pre-rm" data-pre-rm="${esc2(x.id)}" aria-label="${t('rm')}">×</button></figure>`).join('')}</div>` : ''}` : ''}
    </div>`;
  }
  function paint(host, day, parts) {
    let b = host.querySelector(':scope > .nav-pre');
    const html = block(day, parts);
    if (!b) { host.insertAdjacentHTML('beforeend', html); return; }
    if (b._h !== html) { b.outerHTML = html; host.querySelector(':scope > .nav-pre')._h = html; }
  }
  // the Journal day: inside the pre-market section
  function journal() {
    const m = /^#journal\/(\d{4}-\d{2}-\d{2})$/.exec(location.hash) || [null, (document.querySelector('#main [data-act="add-trade"][data-date]') || {}).dataset?.date];
    if (!/^#journal/.test(location.hash || '') || !m[1]) return;
    const sec = document.querySelector('#main .cols.even > section'); const body = sec && sec.querySelector('.surface'); if (!body) return;
    paint(body, m[1]);
  }
  // the plan sheet: before its save button. The pre-market: the chart on the screen of the levels, the screenshots at the end
  function plan() {
    const sh = document.getElementById('gSheet'); if (!sh || !sh.classList.contains('g-plan') || !sh.dataset.day) return;
    const pm = sh.classList.contains('g-pm'), slot = pm && sh.querySelector('.pm-chart-slot');
    if (slot) paint(slot, sh.dataset.day, 'chart');
    const save = sh.querySelector('[data-g="save-plan"]'); if (!save) return;
    let host = sh.querySelector('.nav-pre-host');
    if (!host) { host = document.createElement('div'); host.className = 'nav-pre-host'; (save.closest('.pm-nav') || save).before(host); }
    paint(host, sh.dataset.day, pm ? 'shots' : null);
  }
  const refresh = () => { try { journal(); plan(); } catch (e) { /* never blocks */ } };
  document.addEventListener('click', (e) => {
    const c = e.target.closest && e.target.closest('[data-pre-chart],[data-pre-inst],[data-pre-tf],[data-pre-rm]'); if (!c) return;
    e.preventDefault();
    if (c.dataset.preChart !== undefined && c.hasAttribute('data-pre-chart')) chartOn = !chartOn;
    if (c.dataset.preInst) inst = c.dataset.preInst;
    if (c.dataset.preTf) tf = c.dataset.preTf;
    if (c.dataset.preRm) {
      const day = c.closest('.nav-pre').dataset.day, id = c.dataset.preRm;
      editDoc('journals', day, (d) => { d.id = d.id || day; d.date = d.date || day; d.pre = d.pre || {}; d.pre.shots = (d.pre.shots || []).filter((x) => x.id !== id); });
      try { if (typeof ASSETS !== 'undefined' && ASSETS && ASSETS.delete) ASSETS.delete(id); } catch (x) { /* keep going */ }
    }
    setTimeout(refresh, 30);
  });
  document.addEventListener('change', async (e) => {
    const inp = e.target.closest && e.target.closest('[data-pre-up]'); if (!inp) return;
    const day = inp.closest('.nav-pre').dataset.day, files = [...inp.files]; inp.value = '';
    if (!files.length || typeof ASSETS === 'undefined' || !ASSETS) return;
    for (const f of files) {
      try {
        if (typeof toast === 'function') toast(t('up'), { ms: 20000 });
        const o = await ASSETS.upload(f);
        const exists = typeof getDoc === 'function' && getDoc('journals', day);
        if (exists) editDoc('journals', day, (d) => { d.pre = d.pre || {}; d.pre.shots = [...(d.pre.shots || []), { id: o.id, name: f.name }]; });
        else put('journals', { id: day, date: day, pre: { shots: [{ id: o.id, name: f.name }] }, post: {} });
      } catch (x) { if (typeof toast === 'function') toast(t('fail') + ' : ' + (x.message || '')); return; }
    }
    if (typeof toast === 'function') toast(t('done'));
    setTimeout(refresh, 60);
  });
  new window.SweepMO((recs) => {
    if (recs.every((r) => r.target.closest && r.target.closest('.nav-pre'))) return;
    const sh = document.getElementById('gSheet');
    if ((sh && sh.classList.contains('g-plan') && (!sh.querySelector('.nav-pre') || (sh.querySelector('.pm-chart-slot') && !sh.querySelector('.pm-chart-slot > .nav-pre')))) || (/^#journal/.test(location.hash || '') && !document.querySelector('#main .nav-pre'))) refresh();
  }).observe(document.body, { childList: true, subtree: true });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__pre) {
    const w = function () { const out = appRender.apply(this, arguments); refresh(); return out; };
    w.__pre = true; window.render = w;
  }
})();

/* ───────────── exact P&L on average prices ─────────────
 * Prices were rounded to the tick before computing the P&L. Platforms report average fills that are often between
 * ticks (MGC short 10 @ 4171.86 → 4160.90): rounding 4171.86 to 4171.9 gave $1,100 instead of $1,096 (Lucid: 1,096 − 16 fees = 1,080).
 * Now: P&L = price difference × $ per point × contracts, rounded to the cent only at the end. */
(function () {
  'use strict';
  const perPointC = (inst) => { try { const i = instOf(inst || 'NQ'); return i.tickC / i.tick; } catch (e) { return null; } };   // cents per point per contract
  (function wrapCalc(n) {
    if (typeof window.calcPnl !== 'function' || typeof window.positionOf !== 'function') { if (n < 60) setTimeout(() => wrapCalc(n + 1), 100); return; }
    if (window.calcPnl.__exact) return;
    const oc = window.calcPnl;
    const c = function (dir, entry, exit, qty, inst) {
      if (entry === '' || exit === '' || entry == null || exit == null || !qty) return null;
      const a = Number(entry), b = Number(exit), pp = perPointC(inst);
      if (!isFinite(a) || !isFinite(b) || !pp) return oc.apply(this, arguments);
      return Math.round((b - a) * (dir === 'short' ? -1 : 1) * Math.round(Number(qty)) * pp);
    };
    c.__exact = true; window.calcPnl = c;
    const op = window.positionOf;
    const p = function (execs, inst) {
      const r = op.apply(this, arguments);
      // a flat position: the exact P&L is what was sold minus what was bought
      try {
        const pp = perPointC(inst);
        if (r && r.closed && pp && Array.isArray(execs)) {
          let cash = 0; for (const x of execs) { const q = Math.abs(+x.qty || 0), px = +x.price; if (!q || !isFinite(px)) continue; cash += (x.side === 'sell' ? 1 : -1) * px * q; }
          r.realized_c = Math.round(cash * pp);
        }
      } catch (e) { /* keep the original */ }
      return r;
    };
    p.__exact = true; window.positionOf = p;
  })(0);

  // trades already saved with the rounded formula: corrected once (only when the stored P&L is exactly the rounded one)
  let swept = false;
  (function sweep(n) {
    if (swept) return;
    if (typeof S === 'undefined' || !Array.isArray(S.trades) || !S.trades.length || typeof editDoc !== 'function' || typeof instOf !== 'function') { if (n < 60) setTimeout(() => sweep(n + 1), 600); return; }
    swept = true;
    const fix = [];
    for (const t of S.trades) {
      if (t.demo || t.pnl_manual || t.pnl_real || typeof t.pnl_c !== 'number' || t.entry == null || t.exit == null || !t.contracts) continue;
      const i = instOf(t.instrument || 'NQ'); if (!i || !i.tick) continue;
      const sign = t.direction === 'short' ? -1 : 1, q = Math.round(+t.contracts);
      const old = (Math.round(+t.exit / i.tick) - Math.round(+t.entry / i.tick)) * sign * q * i.tickC;
      const exact = Math.round((+t.exit - +t.entry) * sign * q * i.tickC / i.tick);
      if (t.pnl_c === old && exact !== old) fix.push([t.id, exact]);
    }
    fix.slice(0, 500).forEach(([id, v]) => editDoc('trades', id, (d) => { d.pnl_c = v; if (typeof d.pnl_calc_c === 'number') d.pnl_calc_c = v; }));
  })(0);

  // the risk box shows the plan (to the stop, to the take profit), not the result: say it
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const LB = { en: ['Risk to SL', 'Reward to TP'], fr: ['Risque au SL', 'Gain visé au TP'], es: ['Riesgo al SL', 'Ganancia al TP'] }[L] || ['Risk to SL', 'Reward to TP'];
  new window.SweepMO(() => {
    const box = document.querySelector('#tkSlide.open #tkRisk'); if (!box) return;
    const sp = box.querySelectorAll(':scope > div > span:first-child');
    if (sp[0] && sp[0].textContent !== LB[0]) { sp[0].textContent = LB[0]; sp[0].setAttribute('data-noi18n', ''); }
    if (sp[1] && sp[1].textContent !== LB[1]) { sp[1].textContent = LB[1]; sp[1].setAttribute('data-noi18n', ''); }
  }).observe(document.body, { childList: true, subtree: true });
})();

/* ───────────── how the trader likes to add a trade: by screenshot or by hand ─────────────
 * Asked once (the first « Add a trade », for new and existing traders), kept in settings.add_mode ('shot' | 'manual'),
 * changeable in Settings and switchable for one trade with a small link in both forms.
 *  - by hand: the detailed form, then the trade page for setup, checklist, psychology and review (as before)
 *  - by screenshot: one screen — the screenshot (read by Sweep AI when it is on), the few key fields,
 *    then the discipline checklist and the psychology questions right below. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { dup: 'This trade looks like the one at {t}. Add it anyway?', dupOk: 'Add anyway', shot: 'With a screenshot', man: 'By hand', title: 'New trade', sub: 'from a sentence or a screenshot', subNo: 'your platform’s P&L', noShot: 'No screenshot? Enter your P&L ›', cancel: 'Cancel', byHand: 'Enter by hand', fromShot: 'From a screenshot', impFile: 'Import CSV', toMan: 'Enter by hand ›', toShot: 'From a screenshot ›', drop: 'Paste or drop your screenshot (Ctrl+V)', dropT: 'Choose a screenshot', noShotP: 'Without a screenshot ›', reading: 'Reading the screenshot…', read: 'Filled in from the screenshot: check and complete.', noAi: 'Fill in the key fields.', aiFail: 'Could not read it: fill in the key fields.', acc: 'Account', sym: 'Symbol', dir: 'Direction', long: 'Long', short: 'Short', date: 'Date', time: 'Entry time (ET)', qty: 'Contracts', entry: 'Entry price', exit: 'Exit price', pnl: 'Result ($)', pnlH: 'Calculated from the prices when both are there.', disc: 'Discipline', psy: 'Psychology', emo: 'How did you feel before the trade?', conf: 'Confidence', exec: 'Execution', yes: 'Yes', no: 'No', na: 'N/A', save: 'Save the trade', saved: 'Trade saved', need: 'The account and the net P&L (or the prices) are needed.', set: 'Adding a trade', setS: 'What « Add a trade » opens first.', more: '+ More', addEmo: '+ Add yours', addEmoQ: 'Your emotion (one or two words)', moreQ: '+ {n} more questions', addQ: '+ Add a question', addQQ: 'Your question (e.g. « Did I wait for my level? »)', also: 'Also on (copy trading)', alsoS: 'Also on', net: 'Net P&L (as on your platform)', risk: 'Risk ($)', rHint: 'Enter the net P&L shown by your platform.', rAdd: 'Add the risk to see the R.', verify: 'Check the trade details ›', alsoH: 'Same trade saved on each account you pick.', needDir: 'Long or Short? Tap one to save the trade.', shotQuota: '3 screenshots a day with Free: fill in the key fields, or read without limit with Pro.', dupDay: 'This trade looks like one already saved that day. Add it anyway?' },
    fr: { dup: 'Ce trade ressemble à celui de {t}. L’ajouter quand même ?', dupOk: 'Ajouter quand même', shot: 'Avec une capture d’écran', man: 'Manuellement', title: 'Nouveau trade', sub: 'par une phrase ou une capture', subNo: 'le P&L de ta plateforme', noShot: 'Pas de capture ? Entre ton P&L ›', cancel: 'Annuler', byHand: 'Saisir à la main', fromShot: 'Par capture d’écran', impFile: 'Importer un CSV', toMan: 'Saisir manuellement ›', toShot: 'Par capture d’écran ›', drop: 'Colle ou dépose ta capture (Ctrl+V)', dropT: 'Choisir une capture', noShotP: 'Sans capture ›', reading: 'Lecture de la capture…', read: 'Rempli à partir de la capture : vérifie et complète.', noAi: 'Remplis les infos principales.', aiFail: 'Lecture impossible : remplis les infos principales.', acc: 'Compte', sym: 'Symbole', dir: 'Sens', long: 'Long', short: 'Short', date: 'Date', time: 'Heure d’entrée (ET)', qty: 'Contrats', entry: 'Prix d’entrée', exit: 'Prix de sortie', pnl: 'Résultat ($)', pnlH: 'Calculé à partir des prix quand les deux sont là.', disc: 'Discipline', psy: 'Psychologie', emo: 'Comment te sentais-tu avant le trade ?', conf: 'Confiance', exec: 'Exécution', yes: 'Oui', no: 'Non', na: 'N/A', save: 'Enregistrer le trade', saved: 'Trade enregistré', need: 'Il faut le compte et le P&L net (ou les prix).', set: 'Ajout d’un trade', setS: 'Ce que « Ajouter un trade » ouvre en premier.', more: '+ Voir plus', addEmo: '+ Ajouter la tienne', addEmoQ: 'Ton émotion (un ou deux mots)', moreQ: '+ {n} autres questions', addQ: '+ Ajouter une question', addQQ: 'Ta question (ex. « Ai-je attendu mon niveau ? »)', also: 'Aussi sur (copy trading)', alsoS: 'Aussi sur', net: 'P&L net (comme sur ta plateforme)', risk: 'Risque ($)', rHint: 'Entre le P&L net affiché par ta plateforme.', rAdd: 'Ajoute le risque pour voir le R.', verify: 'Vérifier le trade ›', alsoH: 'Le même trade est enregistré sur chaque compte choisi.', needDir: 'Long ou Short ? Touche un des deux pour enregistrer le trade.', shotQuota: '3 captures par jour avec Free : remplis les infos principales, ou lis-les sans limite avec Pro.', dupDay: 'Ce trade ressemble à un trade déjà enregistré ce jour-là. L’ajouter quand même ?' },
    es: { dup: 'Esta operación se parece a la de las {t}. ¿Añadirla de todos modos?', dupOk: 'Añadir de todos modos', shot: 'Con una captura', man: 'Manualmente', title: 'Nueva operación', sub: 'con una frase o una captura', subNo: 'el P&L de tu plataforma', noShot: '¿Sin captura? Escribe tu P&L ›', cancel: 'Cancelar', byHand: 'Introducir a mano', fromShot: 'Desde una captura', impFile: 'Importar CSV', toMan: 'Introducir manualmente ›', toShot: 'Con una captura ›', drop: 'Pega o suelta tu captura (Ctrl+V)', dropT: 'Elegir una captura', noShotP: 'Sin captura ›', reading: 'Leyendo la captura…', read: 'Rellenado desde la captura: revisa y completa.', noAi: 'Rellena los datos principales.', aiFail: 'No se pudo leer: rellena los datos principales.', acc: 'Cuenta', sym: 'Símbolo', dir: 'Sentido', long: 'Long', short: 'Short', date: 'Fecha', time: 'Hora de entrada (ET)', qty: 'Contratos', entry: 'Precio de entrada', exit: 'Precio de salida', pnl: 'Resultado ($)', pnlH: 'Calculado con los precios cuando están los dos.', disc: 'Disciplina', psy: 'Psicología', emo: '¿Cómo te sentías antes de la operación?', conf: 'Confianza', exec: 'Ejecución', yes: 'Sí', no: 'No', na: 'N/A', save: 'Guardar la operación', saved: 'Operación guardada', need: 'Hacen falta la cuenta y el P&L neto (o los precios).', set: 'Añadir una operación', setS: 'Lo que « Añadir una operación » abre primero.', more: '+ Ver más', addEmo: '+ Añadir la tuya', addEmoQ: 'Tu emoción (una o dos palabras)', moreQ: '+ {n} preguntas más', addQ: '+ Añadir una pregunta', addQQ: 'Tu pregunta (ej. « ¿Esperé mi nivel? »)', also: 'También en (copy trading)', alsoS: 'También en', net: 'P&L neto (como en tu plataforma)', risk: 'Riesgo ($)', rHint: 'Introduce el P&L neto de tu plataforma.', rAdd: 'Añade el riesgo para ver la R.', verify: 'Revisar la operación ›', alsoH: 'La misma operación se guarda en cada cuenta elegida.', needDir: '¿Long o Short? Toca uno para guardar la operación.', shotQuota: '3 capturas al día con Free: rellena los datos principales, o léelas sin límite con Pro.', dupDay: 'Esta operación se parece a una ya guardada ese día. ¿Añadirla de todos modos?' } };
  const t = (k) => (T[L] || T.en)[k];
  /* (brief avance, step 3) one field for a sentence or a screenshot: « long NQ 2 contracts +$400 » fills the sheet (api/ai/entry:
     a plain sentence is read without AI, else Sweep AI with a strict JSON answer and a confidence per field); the low ones are
     highlighted, the account is asked when several are possible; nothing is saved before « Save » */
  const AI = {
    en: { ph: 'Describe your trade or drop a screenshot', ex: 'e.g. « long NQ 2 contracts +$400 »', go: 'Fill in', reading: 'Reading your trade…', read: 'Filled in from your sentence: check the highlighted fields.', readOk: 'Filled in from your sentence: check and save.', fail: 'Sweep AI could not read this sentence: fill in the main fields.', quota: 'Your {n} AI entries this month are used: fill in the main fields.', sub: 'from your sentence', accAsk: 'Which account?', chk: 'Check', needAcc: 'Pick the account of this trade.', shotAcc: 'Read from the screenshot: pick the account of this trade.' },
    fr: { ph: 'Décris ton trade ou dépose une capture', ex: 'ex. « long NQ 2 contrats +400 $ »', go: 'Remplir', reading: 'Lecture de ton trade…', read: 'Rempli à partir de ta phrase\u00a0: vérifie les champs en évidence.', readOk: 'Rempli à partir de ta phrase\u00a0: vérifie et enregistre.', fail: 'Sweep AI n’a pas pu lire cette phrase\u00a0: remplis les infos principales.', quota: 'Tes {n} saisies IA du mois sont utilisées\u00a0: remplis les infos principales.', sub: 'à partir de ta phrase', accAsk: 'Quel compte\u00a0?', chk: 'À vérifier', needAcc: 'Choisis le compte de ce trade.', shotAcc: 'Lu sur la capture\u00a0: choisis le compte de ce trade.' },
    es: { ph: 'Describe tu operación o suelta una captura', ex: 'p. ej. « long NQ 2 contratos +400 $ »', go: 'Rellenar', reading: 'Leyendo tu operación…', read: 'Rellenado a partir de tu frase: revisa los campos resaltados.', readOk: 'Rellenado a partir de tu frase: revisa y guarda.', fail: 'Sweep AI no pudo leer esta frase: rellena los datos principales.', quota: 'Usaste tus {n} entradas con IA del mes: rellena los datos principales.', sub: 'a partir de tu frase', accAsk: '¿Qué cuenta?', chk: 'Revisar', needAcc: 'Elige la cuenta de esta operación.', shotAcc: 'Leído en la captura: elige la cuenta de esta operación.' } };
  const ta = (k) => (AI[L] || AI.en)[k];
  // the sheet's fields → the names of the entry's answer (its confidence per field)
  const AK = { account: 'account_id', inst: 'instrument', dir: 'direction', qty: 'contracts', net: 'pnl_c', time: 'time', date: 'date', entry: 'entry', exit: 'exit' };
  const lowC = (k) => (SH.aiLow && SH.aiLow.has(k) ? ' ai-low' : '');
  const chk = (k) => (SH.aiLow && SH.aiLow.has(k) ? ` <em class="nav-ai-chk">${ta('chk')}</em>` : '');
  const ICGO = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg>';
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const num = (v) => { const s = String(v == null ? '' : v).replace(/[\s\u00a0$]/g, '').replace(',', '.'); return s === '' || s === '-' || !isFinite(+s) ? null : +s; };
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  /* the day a new trade goes to: today's session, or, while the market is closed (17:00–18:00 ET, Friday 17:00 to Sunday
     18:00), the last session that ended (a Friday evening's trade is Friday's, never Saturday's): app.js marketClosedET, as the form */
  const sheetDay = () => (typeof marketClosedET === 'function' && marketClosedET() ? lastSessionET() : today());
  let origTicket = null;

  /* the overlay (same family as the other sheets: back button and Escape close it) */
  function layer(cls, html) {
    close();
    const scrim = document.createElement('div'); scrim.className = 'evp-scrim nav-am-scrim'; scrim.addEventListener('click', close);
    const el = document.createElement('aside'); el.className = 'evp nav-am ' + cls; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true');   // translated by the app like the trade page (questions, emotions)
    el.innerHTML = `<div class="evp-in nav-am-in">${html}</div>`;
    document.body.append(scrim, el);
    requestAnimationFrame(() => { el.classList.add('open'); scrim.classList.add('open'); });
    if (window.SW_MQ6.matches) document.body.classList.add('evp-lock');
    // swipe down to close, like the app's other sheets (phone)
    if (typeof swipeDismiss === 'function') swipeDismiss(el, { scroller: () => (el.scrollTop > 0 ? el : el.querySelector('.nav-am-in')), onClose: close, ignore: '.nav-am-opts, .nav-am-drop, input, textarea' });
    return el;
  }
  function close() {
    document.querySelectorAll('.nav-am, .nav-am-scrim').forEach((x) => { x.classList.remove('open'); setTimeout(() => x.remove(), 260); });
    document.body.classList.remove('evp-lock');
  }
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.querySelector('.nav-am.open')) { e.stopPropagation(); close(); } }, true);

  const ICS = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="12" cy="12" r="3.2"/><path d="M8 5l1.5-2h5L16 5"/></svg>';

  /* 2. the screenshot form */
  const SH = { file: null, shot: null, src: '', dir: '', emo: new Set(), conf: 0, exec: 0, disc: {}, status: '', busy: false, f: {} };
  function shotForm(opts) {
    Object.assign(SH, { aiText: (opts && opts.aiText) || '', aiDone: false, aiBusy: false, aiLow: new Set(), aiAsk: false, noShot: false, ctxOpen: false, dupOk: false, quotaShown: false, batch: [], open: false, setup: '', copy: new Set(), allEmo: false, allQ: false, file: null, shot: null, src: '', dir: '', emo: new Set(), conf: 0, exec: 0, disc: {}, status: '', busy: false, f: { date: (opts && opts.date) || sheetDay(), qty: '1' } });
    const accs = ((l) => (l.some((a) => !a.demo) ? l.filter((a) => !a.demo) : l))((S.accounts || []).filter((a) => a.status !== 'archived'));
    SH.f.account = (accs[0] || {}).id || '';
    { const a0 = getDoc('accounts', SH.f.account); if (a0 && a0.group_id) (window.SweepCopy && SweepCopy.targets ? SweepCopy.targets(a0.id) : (S.accounts || []).filter((x) => x.group_id === a0.group_id && x.id !== a0.id && x.status !== 'archived').map((x) => x.id)).forEach((x) => SH.copy.add(x)); }
    const usual = (() => { const c = {}; (S.trades || []).filter((x) => !x.demo).slice(-40).forEach((x) => { c[x.instrument] = (c[x.instrument] || 0) + 1; }); const top = Object.entries(c).sort((a, b) => b[1] - a[1])[0]; return top ? top[0] : 'NQ'; })();
    SH.f.inst = typeof rookieInst === 'function' ? rookieInst(usual) : usual;   // (27 Oct.) starting out: the micro of the usual contract
    layer('nav-am-shot', '');
    paint();
    if (opts && opts.aiText) aiRun(opts.aiText);   // typed on Today
    else if (opts && opts.files && opts.files.length) takeFiles([...opts.files]);   // a screenshot dropped or chosen on Today
  }
  /** copy groups (« ou le groupe de copie », built separately): when they exist, offer each group here as one more option of
   *  the account asked (picking one = its lead account in SH.f.account, the others in SH.copy). Today: the accounts only. */
  // (brief avance, steps 2 and 3) « which account? »: a copy group's master says its copies — picking it fills the group (SH.copy)
  const AIG = { en: '{a} + its {n} copies', fr: '{a} + ses {n} copies', es: '{a} + sus {n} copias' };
  function aiAccountOptions(accs) {
    return accs.map((a) => {
      const l = typeof acctLabel === 'function' ? acctLabel(a.id) : a.name, G = window.SweepCopy && SweepCopy.leadOf ? SweepCopy.leadOf(a.id) : null, n = G && G.lead.id === a.id ? SweepCopy.targets(a.id).length : 0;
      return [a.id, n ? (AIG[typeof LANG === 'string' ? LANG : 'en'] || AIG.en).replace('{a}', l).replace('{n}', n) : l];
    });
  }
  const accList = () => ((l) => (l.some((a) => !a.demo) ? l.filter((a) => !a.demo) : l))((S.accounts || []).filter((a) => a.status !== 'archived'));
  /** several accounts and none known for this trade: the sheet asks (empty, highlighted, « Save » says so) */
  function askAccount() { if (accList().length > 1 && !SH.f.accountPicked) { SH.f.account = ''; SH.copy = new Set(); SH.aiAsk = true; SH.aiLow.add('account_id'); } }
  /* the sentence → the sheet filled in (never saved here) */
  async function aiRun(text) {
    text = String(text || '').trim(); if (!text || SH.aiBusy) return;
    SH.aiText = text; SH.aiBusy = SH.busy = true; SH.status = ta('reading'); paint();
    let res = null, j = {};
    try {
      res = await fetch('api/ai/entry', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ text, lang: L }) });
      j = await res.json().catch(() => ({}));
    } catch (e) { res = null; }
    if (!document.querySelector('.nav-am-shot')) return;   // the sheet was closed meanwhile
    SH.aiBusy = SH.busy = false; SH.aiDone = true; SH.aiLow = new Set(); SH.aiAsk = false;
    if (res && res.status === 402) {   // the month's AI entries used: the plans' window, the sheet to fill by hand
      SH.status = ta('quota').replace('{n}', j.limit || 10); paint();
      if (window.SweepBilling && SweepBilling.handleApiError) SweepBilling.handleApiError(j);
      return;
    }
    if (!res || !res.ok || !j.trade) { SH.status = ta('fail'); paint(); return; }
    const tr = j.trade, accs = accList(), insts = typeof INSTR !== 'undefined' ? Object.keys(INSTR) : [];
    (j.low || []).forEach((k) => SH.aiLow.add(k));
    if (tr.account_id && accs.some((a) => a.id === tr.account_id)) { SH.f.account = tr.account_id; SH.f.accountPicked = true; SH.copy.delete(tr.account_id); }
    else if (accs.length === 1) SH.f.account = accs[0].id;
    else askAccount();
    if (tr.instrument && (!insts.length || insts.includes(tr.instrument))) SH.f.inst = tr.instrument; else SH.aiLow.add('instrument');   // not said (or unknown): the usual one, to check
    if (tr.direction) SH.dir = tr.direction; else SH.aiLow.add('direction');
    if (tr.contracts) { SH.f.qty = String(tr.contracts); delete SH.f.turns; }
    if (tr.entry != null) SH.f.entry = String(tr.entry);
    if (tr.exit != null) SH.f.exit = String(tr.exit);
    if (tr.pnl_c != null) SH.f.net = (tr.pnl_c / 100).toFixed(2); else if (tr.entry == null || tr.exit == null) SH.aiLow.add('pnl_c');
    if (tr.time) SH.f.time = tr.time;
    if (tr.date) SH.f.date = tr.date;
    if (['instrument', 'contracts', 'time', 'date', 'entry', 'exit'].some((k) => SH.aiLow.has(k))) SH.open = true;   // « Check the trade » open on what to check
    SH.status = SH.aiLow.size ? ta('read') : ta('readOk');
    paint();
  }
  function aiBox() {
    const ph = !!(window.SW_MQ6 && SW_MQ6.matches) || (window.matchMedia && matchMedia('(pointer: coarse)').matches);
    return `<div class="nav-ai-box" data-ai-box>
      <div class="nav-ai-in"><textarea data-ai-text rows="2" enterkeyhint="go" autocomplete="off" placeholder="${esc2(ta('ph'))}" aria-label="${esc2(ta('ph'))}" ${SH.aiBusy ? 'disabled' : ''}>${esc2(SH.aiText)}</textarea>
        <button type="button" class="nav-ai-go" data-am="ai-go" aria-label="${esc2(ta('go'))}" ${SH.aiText.trim() && !SH.aiBusy ? '' : 'hidden'}>${ICGO}</button></div>
      <label class="nav-am-drop nav-ai-pick"><span class="nav-am-ic">${ICS}</span><b>${t(ph ? 'dropT' : 'drop')}</b><input type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden multiple data-am-file></label>
      ${SH.status ? `<p class="nav-am-st ${SH.busy ? 'busy' : ''}">${SH.status}</p>` : `<small class="nav-ai-ex muted">${esc2(ta('ex'))}</small>`}</div>`;
  }
  // the coach before this trade (brief 03 step 3, src/coach.js): one trade only (not a batch of screenshots)
  const coachBefore = () => (!SH.batch.length && window.SweepCoach && SweepCoach.before ? SweepCoach.before({ form: 'shot', account: SH.f.account, date: SH.f.date, qty: +SH.f.qty || 0, time: String(SH.f.time || '').slice(0, 5), setup: SH.setup, dir: SH.dir, inst: SH.f.inst }) : '');
  const coachPaint = () => { const w = document.querySelector('.nav-am-shot .nav-am-co'); if (w) w.innerHTML = coachBefore(); };
  document.addEventListener('sweep:qs', () => { if (document.querySelector('.nav-am-shot')) setTimeout(repaintKeep, 120); });   // a criterion added on the form
  function repaintKeep() {
    const r = document.querySelector('.nav-am-shot .nav-sp-row'), x = r ? r.scrollLeft : 0, a = document.querySelector('.nav-am-shot'), b = a && a.querySelector('.nav-am-in'), ya = a ? a.scrollTop : 0, yb = b ? b.scrollTop : 0;
    paint();
    const r2 = document.querySelector('.nav-am-shot .nav-sp-row'); if (r2) r2.scrollLeft = x;
    if (a) a.scrollTop = ya; const b2 = a && a.querySelector('.nav-am-in'); if (b2) b2.scrollTop = yb;
  }
  function paint() {
    const el = document.querySelector('.nav-am-shot .nav-am-in'); if (!el) return;
    const accs = ((l) => (l.some((a) => !a.demo) ? l.filter((a) => !a.demo) : l))((S.accounts || []).filter((a) => a.status !== 'archived'));
    const insts = typeof INSTR !== 'undefined' ? Object.keys(INSTR) : ['NQ', 'MNQ', 'ES', 'MES', 'GC', 'MGC', 'CL'];
    const QO = window.SweepQs ? SweepQs.order(SH.setup) : { list: ((S.settings && S.settings.questions) || []).filter((q) => q.active), shown: 3 };   // edge T7: the setup's criteria, the question that separates, the acquired ones
    const qs = QO.list, qn = QO.shown, qLab = (q) => (window.SweepQs ? SweepQs.label(q) : esc2(q.text));
    const emos = typeof EMO !== 'undefined' ? EMO : ['Calm', 'Confident', 'Patient', 'Focused', 'FOMO', 'Fearful', 'Frustrated', 'Greedy', 'Hesitant', 'Impulsive'];
    // (31 Oct., C1) on a phone: « Choose a screenshot », one « Without a screenshot › » (the full form is inside it), never Ctrl+V,
    // and the screenshot area does not come back once in the P&L entry
    const ph = !!(window.SW_MQ6 && SW_MQ6.matches);
    const pnl = autoPnl(), has = !!(SH.batch.length || SH.src || SH.noShot || SH.aiDone);   // the screenshot is there (or « No screenshot? », or a sentence read): the rest of the sheet shows
    el.closest('.nav-am').classList.toggle('nav-am-min', !has);   // before it: a short sheet, its height its content (phone)
    // (2 Nov., analyse débutant C6) a trader of the 90-day gameplan: the instrument in sight (the last one used, a tap to change it), not
    // folded under « Check the trade »; a line says what the risk is and what the R is
    const gp = typeof gpTrader === 'function' && gpTrader();
    const instBox = `<div class="tk-f nav-am-wide${lowC('instrument')}"><span>${t('sym')}${chk('instrument')}</span>${pickBox('inst', insts.map((k) => [k, k + (typeof INSTR !== 'undefined' && INSTR[k] && INSTR[k].name ? ' — ' + INSTR[k].name : '')]), SH.f.inst)}${typeof rookieRule === 'function' ? rookieRule(SH.f.inst) : ''}</div>`;
    const fld = (k, label, attrs = '') => `<label class="tk-f${lowC(AK[k])}"><span>${label}${chk(AK[k])}</span><div class="tk-in"><input data-am-f="${k}" value="${esc2(SH.f[k] ?? '')}" ${attrs}></div></label>`;
    const seg = (key, vals, cur) => `<div class="seg yn">${vals.map(([v, l]) => `<button type="button" class="${String(cur) === String(v) ? 'on' : ''}" data-am-seg="${key}" data-v="${v}">${l}</button>`).join('')}</div>`;
    // same header as the manual form: title, subtitle, the other way, « Cancel » on the right
    el.innerHTML = `<div class="tk-head nav-am-head"><div><h2>${t('title')}</h2><span class="muted">${SH.aiDone && !SH.src ? ta('sub') : t(SH.noShot && !SH.src ? 'subNo' : 'sub')}</span>${has ? `<button type="button" class="link nav-am-sw" data-am="to-manual">${t('toMan')}</button>` : ''}</div><button type="button" class="link" data-am="close">${t('cancel')}</button></div>
      ${SH.batch.length ? batchTop() : !has ? aiBox() : SH.aiDone && !SH.src ? `${ph ? '' : `<label class="nav-am-drop slim"><span class="nav-am-ic">${ICS}</span><b>${t('drop')}</b><input type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden multiple data-am-file></label>`}<p class="nav-ai-said" data-noi18n>« ${esc2(SH.aiText)} »</p>${SH.status ? `<p class="nav-am-st">${SH.status}</p>` : ''}` : ph && SH.noShot && !SH.src ? '' : `<label class="nav-am-drop ${SH.src ? 'has' : SH.noShot ? 'slim' : ''}">${SH.src ? `<img src="${SH.src}" alt="">` : `<span class="nav-am-ic">${ICS}</span><b>${t(ph || (window.matchMedia && matchMedia('(pointer: coarse)').matches) ? 'dropT' : 'drop')}</b>`}<input type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden multiple data-am-file></label>
      ${SH.status ? `<p class="nav-am-st ${SH.busy ? 'busy' : ''}">${SH.status}</p>` : ''}`}
      ${has || ph ? '' : `<button type="button" class="link nav-am-noshot" data-am="no-shot">${t('noShot')}</button>`}
      ${/* (SWEEP.md step 2) the same quick sheet without an image: account, net P&L, Long / Short, setup… — no prices to type */ ''}
      ${/* (3 Nov., Mateo's iPhone) on a phone « Without a screenshot » and « Import CSV » side by side, two equal buttons (a centred link over a half-width button looked off) */ ''}
      ${has ? '' : `<div class="nav-am-alt">${ph ? `<button type="button" class="btn" data-am="no-shot">${t('noShotP').replace(/\s*›$/, '')}</button>` : `<button type="button" class="btn" data-am="to-manual">${t('byHand')}</button>`}<button type="button" class="btn" data-am-imp>${t('impFile')}</button></div>`}
      ${/* nothing else until the screenshot is there (18 Oct., Mateo: a minimal first screen) */ ''}${has ? `
      <div class="nav-am-co">${coachBefore()}</div>
      <div class="nav-am-grid">
        <div class="tk-f nav-am-wide${lowC('account_id')}"><span>${t('acc')}${chk('account_id')}</span>${pickBox('account', aiAccountOptions(accs), SH.f.account, SH.aiAsk ? ta('accAsk') : '')}</div>
        ${accs.length > 1 && SH.f.account ? `<div class="tk-copies nav-am-wide nav-am-copy"><span class="help">${t('alsoS')}</span>${accs.filter((a) => a.id !== SH.f.account).map((a) => `<button type="button" class="chip ${SH.copy.has(a.id) ? 'on' : ''}" data-am-copy="${esc2(a.id)}">${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</button>`).join('')}</div>` : ''}
        ${SH.batch.length ? batchList() : `<label class="tk-f nav-am-net${lowC('pnl_c')}"><span>${t('net')}${chk('pnl_c')}</span><div class="tk-in"><input data-am-f="net" inputmode="decimal" value="${esc2(SH.f.net ?? '')}" placeholder="${pnl != null ? ((pnl - (SH.f.fees || 0)) / 100).toFixed(2) : '+250'}"></div></label>
        <div class="tk-f nav-am-dir${lowC('direction')}"><span>${t('dir')}${chk('direction')}</span>${seg('dir', [['long', t('long')], ['short', t('short')]], SH.dir)}</div>
        ${window.SweepSetupPick ? `<div class="nav-am-wide">${SweepSetupPick.html(SH.f.date, SH.setup)}</div>` : ''}
        ${gp ? instBox : ''}<label class="tk-f nav-am-risk"><span>${t('risk')}</span><div class="tk-in"><input data-am-f="risk" inputmode="decimal" value="${esc2(SH.f.risk ?? '')}" placeholder="$"></div>${gp ? `<small class="muted nav-am-riskh">${esc2(RISKH[L] || RISKH.en)}</small>` : ''}</label>
        <div class="nav-am-r nav-am-wide">${rLine()}</div>
        <details class="nav-am-more-d nav-am-wide" ${SH.open ? 'open' : ''}><summary>${t('verify')}<small>${verifyLine()}</small></summary><div class="nav-am-grid">
        ${gp ? '' : instBox}
        ${fld('qty', t('qty'), 'inputmode="numeric"')}
        ${fld('date', t('date'), 'type="date"')}${fld('time', t('time'), 'placeholder="hh:mm"')}
        ${fld('entry', t('entry'), 'inputmode="decimal"')}${fld('exit', t('exit'), 'inputmode="decimal"')}
        </div></details>`}
      </div>
      ${/* brief 03 step 5: 3 questions (the trader's first three), emotions in one tap; the rest, confidence and execution under « More » */ ''}
      <div class="nav-am-ctxw ${ctxFold() ? 'fold' : ''}"><button type="button" class="chip nav-am-ctxb" data-am="ctx-open">${CTX[0]}</button>
      ${qs.length ? `<section class="nav-am-sec"><h3>${t('disc')}</h3>${(SH.allQ ? qs : qs.filter((q, i) => i < qn || SH.disc[q.id])).map((q) => `<div class="nav-am-q"><span>${qLab(q)}</span>${seg('d:' + q.id, [['y', t('yes')], ['n', t('no')], ['na', t('na')]], SH.disc[q.id] || '')}</div>`).join('')}
        <div class="nav-am-qmore">${!SH.allQ && qs.length > qn ? `<button type="button" class="chip nav-am-more" data-am="q-more">${t('moreQ').replace('{n}', qs.filter((q, i) => i >= qn && !SH.disc[q.id]).length)}</button>` : ''}<button type="button" class="chip nav-am-more" data-am="q-add">${t('addQ')}</button>${window.SweepQs ? SweepQs.addLink(SH.setup) : ''}</div></section>` : ''}
      <section class="nav-am-sec"><h3>${t('psy')}</h3><p class="muted">${t('emo')}</p>
        <div class="chips nav-am-emo">${(() => {
          const own = ((S.settings && S.settings.custom_emotions) || []).filter((k) => !emos.includes(k));
          const first = ['Calm', 'Confident', 'FOMO', 'Frustrated', 'Hesitant'].filter((k) => emos.includes(k));
          const rest = [...emos.filter((k) => !first.includes(k)), ...own];
          const shown = SH.allEmo ? [...first, ...rest] : [...first, ...rest.filter((k) => SH.emo.has(k))];
          return shown.map((k) => `<button type="button" class="chip ${SH.emo.has(k) ? 'on' : ''}" data-am-emo="${esc2(k)}">${esc2(k)}</button>`).join('')
            + (SH.allEmo ? '' : `<button type="button" class="chip nav-am-more" data-am="emo-more">${t('more')}</button>`)
            + `<button type="button" class="chip nav-am-more" data-am="emo-add">${t('addEmo')}</button>`;
        })()}</div>
        ${SH.allEmo || SH.conf || SH.exec ? `<div class="nav-am-scores"><div><span>${t('conf')}</span>${seg('conf', [1, 2, 3, 4, 5].map((n) => [n, n]), SH.conf || '')}</div><div><span>${t('exec')}</span>${seg('exec', [1, 2, 3, 4, 5].map((n) => [n, n]), SH.exec || '')}</div></div>` : ''}</section>
      </div>
      <p class="err nav-am-err"></p>
      <button type="button" class="btn primary nav-am-save" data-am="save" ${SH.busy ? 'disabled' : ''}>${t('save')}</button>` : ''}`;
  }
  // (brief « pertes oubliées », step 4) a loss typed: the checklist and the emotions fold under « + Add context (optional) » —
  // noting a loss costs no more taps than a win
  const RISKH = { en: 'What you lose if your stop is hit. It gives your R (your result divided by your risk).', fr: 'Ce que tu perds si ton stop est touché. Il sert à calculer ton R (ton résultat divisé par ton risque).', es: 'Lo que pierdes si tocan tu stop. Sirve para calcular tu R (tu resultado dividido por tu riesgo).' };
  const CTX = ({ en: ['+ Add context'], fr: ['+ Ajouter le contexte'], es: ['+ Añadir el contexto'] })[L] || ['+ Add context'];   // (2 Nov., analyse débutant C6) no « (optional) » next to a field
  function ctxFold() { const v = num(SH.f.net); return !SH.batch.length && !SH.ctxOpen && v != null && v < 0; }
  function ctxPaint() { const w = document.querySelector('.nav-am .nav-am-ctxw'); if (w) w.classList.toggle('fold', ctxFold()); }
  function pickBox(k, opts, cur, ph) {
    const hit = opts.find((o) => o[0] === cur), lab = hit ? hit[1] : ph || (opts[0] || ['', ''])[1];   // ph: nothing chosen yet (« Which account? »)
    return `<div class="nav-am-sel ${SH.openPick === k ? 'open' : ''}" data-noi18n><button type="button" class="nav-am-selb${!hit && ph ? ' ph' : ''}" data-am-sel="${k}" aria-expanded="${SH.openPick === k}"><span>${esc2(lab)}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>${SH.openPick === k ? `<div class="nav-am-opts" role="listbox">${opts.map((o) => `<button type="button" role="option" class="${o[0] === cur ? 'on' : ''}" data-am-pickf="${k}" data-v="${esc2(o[0])}">${esc2(o[1])}</button>`).join('')}</div>` : ''}</div>`;
  }
  /* several screenshots: one trade each, same account, discipline and psychology for all */
  function batchTop() {
    return `<div class="nav-am-thumbs">${SH.batch.map((b) => `<div class="nav-am-th ${b.st}"><img src="${b.src}" alt=""><button type="button" class="nav-am-thx" data-am-rm="${b.id}" aria-label="×">×</button>${b.st === 'reading' ? '<i class="nav-am-spin"></i>' : ''}</div>`).join('')}<label class="nav-am-th add"><span>+</span><input type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden multiple data-am-file></label></div>`;
  }
  function batchList() {
    const total = SH.batch.reduce((a, b) => a + (num(b.f.net) != null ? Math.round(num(b.f.net) * 100) : 0), 0);
    return `<div class="nav-am-wide nav-am-batch"><div class="nav-am-bh"><b>${SH.batch.length} trades</b><span class="${total < 0 ? 'neg' : 'pos'}">${typeof money === 'function' ? money(total) : (total / 100).toFixed(2)}</span></div>
      ${SH.batch.map((b, i) => `<div class="nav-am-bi"><img src="${b.src}" alt=""><div class="nav-am-bm"><b>${esc2([b.f.inst, b.f.dir ? t(b.f.dir) : '', b.f.qty ? b.f.qty + ' ×' : ''].filter(Boolean).join(' · ') || '#' + (i + 1))}</b><small class="muted">${b.st === 'reading' ? t('reading') : esc2([b.f.time, b.f.entry && b.f.exit ? b.f.entry + ' → ' + b.f.exit : ''].filter(Boolean).join(' · '))}</small></div><input data-am-bnet="${b.id}" inputmode="decimal" placeholder="${t('net')}" value="${esc2(b.f.net ?? '')}"></div>`).join('')}</div>`;
  }
  /** the screenshot as a data URL; a very big one is resized (longest side 3200 px, sharp JPEG) so it is never refused */
  async function shotData(file) {
    const raw = await new Promise((ok, ko) => { const r = new FileReader(); r.onload = () => ok(String(r.result)); r.onerror = ko; r.readAsDataURL(file); });
    try {
      const img = await new Promise((ok, ko) => { const i = new Image(); i.onload = () => ok(i); i.onerror = ko; i.src = raw; });
      const big = Math.max(img.naturalWidth, img.naturalHeight);
      if (file.size < 3.5e6 && big <= 4000) return raw;
      const k = Math.min(1, 3200 / big), c = document.createElement('canvas'); c.width = Math.round(img.naturalWidth * k); c.height = Math.round(img.naturalHeight * k);
      const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(img, 0, 0, c.width, c.height);
      return c.toDataURL('image/jpeg', 0.92);
    } catch (e) { return raw; }
  }
  async function readOne(b) {
    try {
      if (typeof ASSETS !== 'undefined' && ASSETS) { const o = await ASSETS.upload(b.file); b.shot = { id: o.id, phase: 'after', name: b.file.name }; }
    } catch (e) { /* the trade can still be saved */ }
    if (!document.body.classList.contains('ai-on')) { b.st = 'ok'; return; }
    try {
      const b64 = await shotData(b.file);
      const res = await fetch('api/ai/import', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ image: b64, mime: (b64.match(/^data:([^;]+)/) || [])[1] || b.file.type, mode: 'shot', local_tz: (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (x) { return ''; } })() }) });
      const j = await res.json().catch(() => ({})); const trs = res.ok && Array.isArray(j.trades) ? j.trades : [];
      if (res.status === 402 && !SH.quotaShown) { SH.quotaShown = true; SH.status = t('shotQuota'); if (window.SweepBilling && SweepBilling.handleApiError) SweepBilling.handleApiError(j); }   // Free: 3 a day, once per batch
      b.res = res.ok ? j : null; const d = trs[0];
      if (d) Object.assign(b.f, { inst: d.instrument || b.f.inst, dir: d.direction || '', qty: d.contracts ? String(d.contracts) : '1', turns: d.turns || null, date: d.date || b.f.date, time: String(d.entry_time || '').slice(0, 5), entry: d.entry != null ? String(d.entry) : '', exit: d.exit != null ? String(d.exit) : '', net: d.pnl_c != null ? ((d.pnl_c - (d.fees_c || 0)) / 100).toFixed(2) : '', fees: d.fees_c || 0, exitTime: d.exit_time || '' });
      if (j.account_suggest && !SH.f.accountPicked) SH.f.account = j.account_suggest;
      b.st = d ? 'ok' : 'fail';
    } catch (e) { b.st = 'fail'; }
  }

  /* ───── several trades read on screenshots: « X trades found », checked by the trader, saved in one go ───── */
  const MX = { en: { raw: 'What Sweep AI read on the screenshot', wTime: 'time not read', wSide: 'side not read', wPnl: 'P&L differs from the prices', wRead: 'hard to read', wOpen: 'still open', fixed: 'side taken from the prices and the P&L', feesP: 'fees = shown P&L difference', found: '{n} trades found', acc: 'Account', all: 'Check all', none: 'Uncheck all', save: 'Save {n} trades', net: 'Net of the batch', wl: '{w} won · {l} lost', check: 'To check', open: 'Open — to complete', dup: 'Already in Sweep',
      shown: 'Shown {a} · computed {b}', tz: 'Times on this screenshot', tzQ: 'In which time zone are the times on this screenshot?', disc: 'Discipline for the batch', each: 'Answer trade by trade', yes: 'Yes', no: 'No', na: 'N/A', added: '{n} trades added · {p}', undone: 'Batch removed',
      fail: 'Could not save the batch. Nothing was added.', copy: 'Also on', edit: 'Edit', done: 'Done', inst: 'Symbol', dir: 'Side', qty: 'Qty', entry: 'Entry', exit: 'Exit', tin: 'Entry time', tout: 'Exit time', pnl: 'P&L ($)', long: 'Long', short: 'Short', gross: 'gross {a} · fees {b}', unknown: 'Not read (symbol unknown to Sweep): {s}' },
    fr: { raw: 'Ce que Sweep AI a lu sur la capture', wTime: 'heure non lue', wSide: 'sens non lu', wPnl: 'P&L différent des prix', wRead: 'lecture incertaine', wOpen: 'encore ouvert', fixed: 'sens déduit des prix et du P&L', feesP: 'frais = écart avec le P&L affiché', found: '{n} trades trouvés', acc: 'Compte', all: 'Tout cocher', none: 'Tout décocher', save: 'Enregistrer {n} trades', net: 'Net du lot', wl: '{w} gagnants · {l} perdants', check: 'À vérifier', open: 'Ouvert — à compléter', dup: 'Déjà dans Sweep',
      shown: 'Affiché {a} · calculé {b}', tz: 'Heures de cette capture', tzQ: 'Dans quel fuseau sont les heures de cette capture ?', disc: 'Discipline pour le lot', each: 'Répondre trade par trade', yes: 'Oui', no: 'Non', na: 'N/A', added: '{n} trades ajoutés · {p}', undone: 'Lot retiré',
      fail: 'Le lot n’a pas pu être enregistré. Rien n’a été ajouté.', copy: 'Aussi sur', edit: 'Modifier', done: 'OK', inst: 'Symbole', dir: 'Sens', qty: 'Qté', entry: 'Entrée', exit: 'Sortie', tin: 'Heure d’entrée', tout: 'Heure de sortie', pnl: 'P&L ($)', long: 'Long', short: 'Short', gross: 'brut {a} · frais {b}', unknown: 'Non lus (symbole inconnu de Sweep) : {s}' },
    es: { raw: 'Lo que Sweep AI leyó en la captura', wTime: 'hora no leída', wSide: 'lado no leído', wPnl: 'P&L distinto de los precios', wRead: 'lectura dudosa', wOpen: 'aún abierta', fixed: 'lado deducido de los precios y el P&L', feesP: 'comisiones = diferencia con el P&L mostrado', found: '{n} operaciones encontradas', acc: 'Cuenta', all: 'Marcar todo', none: 'Desmarcar todo', save: 'Guardar {n} operaciones', net: 'Neto del lote', wl: '{w} ganadoras · {l} perdedoras', check: 'Por revisar', open: 'Abierta — por completar', dup: 'Ya está en Sweep',
      shown: 'Mostrado {a} · calculado {b}', tz: 'Horas de esta captura', tzQ: '¿En qué zona horaria están las horas de esta captura?', disc: 'Disciplina para el lote', each: 'Responder operación por operación', yes: 'Sí', no: 'No', na: 'N/A', added: '{n} operaciones añadidas · {p}', undone: 'Lote eliminado',
      fail: 'No se pudo guardar el lote. No se añadió nada.', copy: 'También en', edit: 'Editar', done: 'OK', inst: 'Símbolo', dir: 'Lado', qty: 'Cant.', entry: 'Entrada', exit: 'Salida', tin: 'Hora de entrada', tout: 'Hora de salida', pnl: 'P&L ($)', long: 'Long', short: 'Short', gross: 'bruto {a} · comisiones {b}', unknown: 'No leídas (símbolo desconocido para Sweep): {s}' } };
  const mx = (k, p) => { let v = (MX[L] || MX.en)[k] || MX.en[k]; if (p) Object.keys(p).forEach((q) => { v = v.replace('{' + q + '}', p[q]); }); return v; };
  const SHM = { res: [], trades: [], acc: '', tz: '', needsTz: false, shots: [], each: false, disc: {}, copy: new Set(), edit: null };
  const mU2 = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));
  const pvOf = (inst) => (typeof PV === 'function' ? PV(inst) : 2000);   // cents per point
  function recompute(tr) {   // the P&L follows every change, unless the trader typed it
    if (tr._pnlTyped) return;
    // average prices × contracts bought and sold (turns, from the fills); contracts shown = the largest position
    const q = tr.turns || tr.contracts;
    if (tr.entry != null && tr.exit != null && q) tr.pnl_c = Math.round((tr.exit - tr.entry) * (tr.direction === 'long' ? 1 : -1) * q * pvOf(tr.instrument));
  }
  /** the trade already in Sweep that looks the same: same account, instrument, side, contracts, session, entry within a minute
   *  (when both trades have a time), same prices when known, the same P&L when there are no prices. « Already in Sweep » here; « looks like the one at 10:32 » on the form and the single screenshot */
  function dupTrade(tr, acc) {
    const m = (x) => +String(x || '').slice(0, 2) * 60 + +String(x || '').slice(3, 5);
    return (S.trades || []).find((x) => x.account_id === acc && x.instrument === tr.instrument && x.direction === tr.direction && +x.contracts === +tr.contracts && x.date === tr.date
      && (!x.entry_time || !tr.entry_time || Math.abs(m(x.entry_time) - m(tr.entry_time)) <= 1) && (tr.entry == null || +x.entry === +tr.entry) && (tr.exit == null || +x.exit === +tr.exit)
      && (tr.entry != null || tr.exit != null || (tr.pnl_c != null && +x.pnl_c === +tr.pnl_c))) || null;
  }
  function dupOf(tr) { return !!dupTrade(tr, SHM.acc); }
  window.SweepDupOf = dupTrade;
  function flag() { SHM.trades.forEach((tr) => { const d = dupOf(tr); if (d && !tr._dupSeen) { tr.sel = false; tr._dupSeen = true; } tr.dup = d; }); }
  function multiHtml() {
    const sel = SHM.trades.filter((x) => x.sel), net = sel.reduce((a, x) => a + (x.pnl_c || 0) - (x.fees_c || 0), 0);
    const w = sel.filter((x) => (x.pnl_c || 0) - (x.fees_c || 0) > 0).length, l = sel.filter((x) => (x.pnl_c || 0) - (x.fees_c || 0) < 0).length;
    const accs = (S.accounts || []).filter((a) => a.status !== 'archived');
    const qs = ((S.settings && S.settings.questions) || []).filter((q) => q.active).slice(0, 8);
    const disc = (ans, key) => qs.map((q) => `<div class="nav-shm-q"><span>${esc2(typeof tr === 'function' ? tr(q.text) : q.text)}</span><div class="seg">${[['y', mx('yes')], ['n', mx('no')], ['na', mx('na')]].map(([v, lab]) => `<button type="button" class="${(ans || {})[q.id] === v ? 'on' : ''}" data-shm-q="${esc2(q.id)}" data-shm-v="${v}" data-shm-k="${key}">${lab}</button>`).join('')}</div></div>`).join('');
    const card = (tr, i) => {
      const n1 = (tr.pnl_c || 0) - (tr.fees_c || 0), badges = [tr.check ? `<span class="nav-shm-b ck">${mx('check')}</span>` : '', tr.open ? `<span class="nav-shm-b op">${mx('open')}</span>` : '', tr.dup ? `<span class="nav-shm-b dp">${mx('dup')}</span>` : ''].join('');
      const ed = SHM.edit === i ? `<div class="nav-shm-ed" data-noi18n>
        <div class="fgrid">${[['inst', 'instrument', tr.instrument], ['qty', 'contracts', tr.contracts], ['entry', 'entry', tr.entry ?? ''], ['exit', 'exit', tr.exit ?? ''], ['tin', 'entry_time', tr.entry_time || ''], ['tout', 'exit_time', tr.exit_time || ''], ['pnl', 'pnl', ((tr.pnl_c || 0) / 100).toFixed(2)]].map(([k, f, v]) => `<label class="f"><span>${mx(k)}</span><input data-shm-f="${f}" data-i="${i}" value="${esc2(v)}" ${['entry_time', 'exit_time'].includes(f) ? 'placeholder="HH:MM"' : 'inputmode="decimal"'}></label>`).join('')}</div>
        <div class="seg"><button type="button" class="${tr.direction === 'long' ? 'on' : ''}" data-shm-dir="long" data-i="${i}">${mx('long')}</button><button type="button" class="${tr.direction === 'short' ? 'on' : ''}" data-shm-dir="short" data-i="${i}">${mx('short')}</button></div>
        ${SHM.each ? `<div class="nav-shm-disc">${disc(tr._disc, 't' + i)}</div>` : ''}
        <button type="button" class="btn sm" data-shm-done>${mx('done')}</button></div>` : '';
      return `<div class="nav-shm-c ${tr.sel ? 'sel' : ''} ${SHM.edit === i ? 'ed' : ''}"><label class="nav-shm-ck"><input type="checkbox" data-shm-sel="${i}" ${tr.sel ? 'checked' : ''} aria-label="${esc2(tr.instrument + ' ' + (tr.entry_time || ''))}"></label>
        <button type="button" class="nav-shm-m" data-shm-edit="${i}"><span class="t">${esc2(tr.entry_time || '—')}</span><b>${esc2(tr.instrument)} · ${tr.direction === 'long' ? mx('long') : mx('short')} · ${tr.contracts}</b>
          <small>${tr.entry != null ? esc2(String(tr.entry)) : '—'} → ${tr.exit != null ? esc2(String(tr.exit)) : '—'}${tr.fees_c ? ' · ' + mx('gross', { a: mU2(tr.pnl_c || 0), b: mU2(tr.fees_c) }) : ''}${tr.check && tr.pnl_calc_c != null && tr.pnl_shown_c != null ? ' · ' + mx('shown', { a: mU2(tr.pnl_shown_c), b: mU2(tr.pnl_calc_c) }) : ''}</small>${(() => { const w = (tr.why || []).map((k) => mx({ time: 'wTime', side: 'wSide', pnl: 'wPnl', read: 'wRead', open: 'wOpen' }[k] || 'wRead')); if (tr.side_fixed) w.push(mx('fixed')); if (tr.fees_from_pnl) w.push(mx('feesP')); return w.length ? `<small class="nav-shm-why">${esc2(w.join(' · '))}</small>` : ''; })()}${badges ? `<span class="nav-shm-bs">${badges}</span>` : ''}</button>
        <span class="nav-shm-p ${n1 > 0 ? 'pos' : n1 < 0 ? 'neg' : ''}">${mU2(n1)}</span>${ed}</div>`;
    };
    const unk = [...new Set(SHM.res.flatMap((r) => r.unknown || []))];
    return `<div class="nav-shm" data-noi18n>
      <div class="nav-am-h"><b class="nav-shm-title">${mx('found', { n: SHM.trades.length })}</b></div>
      <div class="nav-shm-top">${SHM.shots.map((x) => `<button type="button" class="nav-shm-img" data-shm-img="${esc2(x.src)}" aria-label="${esc2(x.name || 'screenshot')}"><img src="${esc2(x.src)}" alt=""></button>`).join('')}
        <div class="nav-shm-sum"><label class="f"><span>${mx('acc')}</span><select data-shm-acc>${accs.map((a) => `<option value="${esc2(a.id)}" ${a.id === SHM.acc ? 'selected' : ''}>${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</option>`).join('')}</select></label>
        <div class="nav-shm-tot"><small>${mx('net')}</small><b class="${net > 0 ? 'pos' : net < 0 ? 'neg' : ''}">${mU2(net)}</b><small>${mx('wl', { w, l })}</small></div></div></div>
      ${SHM.needsTz ? `<label class="f nav-shm-tz"><span>${mx('tzQ')}</span><select data-shm-tz><option value="America/New_York" ${SHM.tz === 'America/New_York' ? 'selected' : ''}>New York (ET)</option><option value="America/Chicago" ${SHM.tz === 'America/Chicago' ? 'selected' : ''}>Chicago (CT)</option><option value="UTC" ${SHM.tz === 'UTC' ? 'selected' : ''}>UTC</option></select></label>` : ''}
      ${unk.length ? `<p class="nav-shm-note">${esc2(mx('unknown', { s: unk.join(', ') }))}</p>` : ''}
      ${SHM.res.some((r) => (r.table || []).length) ? `<details class="nav-shm-raw"><summary>${mx('raw')}</summary><div class="scroll-x">${SHM.res.filter((r) => (r.table || []).length).map((r) => `<table class="tbl"><thead><tr>${(r.columns || []).map((c) => `<th>${esc2(c)}</th>`).join('')}</tr></thead><tbody>${r.table.map((row) => `<tr>${(row || []).map((c) => `<td>${esc2(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`).join('')}</div></details>` : ''}
      <div class="nav-shm-tools"><button type="button" class="link" data-shm-all="1">${mx('all')}</button><button type="button" class="link" data-shm-all="0">${mx('none')}</button></div>
      <div class="nav-shm-list">${SHM.trades.map(card).join('')}</div>
      ${accs.length > 1 ? `<div class="nav-shm-copy"><span>${mx('copy')}</span><div class="nav-shm-chips">${accs.filter((a) => a.id !== SHM.acc).map((a) => `<button type="button" class="chip ${SHM.copy.has(a.id) ? 'on' : ''}" data-shm-copy="${esc2(a.id)}">${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</button>`).join('')}</div></div>` : ''}
      ${qs.length ? `<div class="nav-shm-discw"><div class="nav-shm-dh"><b>${mx('disc')}</b><label class="nav-shm-each"><input type="checkbox" data-shm-each ${SHM.each ? 'checked' : ''}> ${mx('each')}</label></div>${SHM.each ? '' : disc(SHM.disc, 'lot')}</div>` : ''}
      <button type="button" class="btn primary nav-am-save nav-shm-save" data-shm-save ${sel.length ? '' : 'disabled'}>${mx('save', { n: sel.length })}</button></div>`;
  }
  function paintMulti() { const el = document.querySelector('.nav-am.nav-shm-l .nav-am-in'); if (el) { const st = el.scrollTop; el.innerHTML = multiHtml(); el.scrollTop = st; } }
  function openMulti(results, shots) {
    SHM.res = results; SHM.shots = shots; SHM.each = false; SHM.disc = {}; SHM.copy = new Set(); SHM.edit = null;
    const r0 = results[0] || {};
    SHM.acc = (SH.f && SH.f.accountPicked && SH.f.account) || r0.account_suggest || (SH.f && SH.f.account) || ((S.accounts || []).find((a) => a.status !== 'archived') || {}).id || '';
    SHM.tz = r0.tz || 'America/New_York'; SHM.needsTz = results.some((r) => r.needs_tz);
    SHM.trades = results.flatMap((r, k) => (r.trades || []).map((x) => Object.assign({}, x, { sel: !x.open, _shot: (shots[k] || {}).shot || null })));
    flag();
    const el = layer('nav-shm-l', multiHtml()); el.setAttribute('data-noi18n', '');
  }
  async function rebuild() {   // another account or time zone: the same rows, built again by the server (no AI credit)
    try {
      const out = [];
      for (const r of SHM.res) {
        const res = await fetch('api/ai/shot-build', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ rows: r.rows, columns: r.columns, table: r.table, pnl_colors: r.pnl_colors, date_shown: r.date_shown, symbol_shown: r.symbol_shown, source_type: r.source_type, timezone_shown: r.timezone_shown, account_label: r.account_label, account_id: SHM.acc, tz: SHM.tz }) });
        out.push(res.ok ? await res.json() : r);
      }
      SHM.res = out;
      SHM.trades = out.flatMap((r, k) => (r.trades || []).map((x) => Object.assign({}, x, { sel: !x.open, _shot: (SHM.shots[k] || {}).shot || null })));
      flag(); paintMulti();
    } catch (e) { paintMulti(); }
  }
  async function saveMulti() {
    const pick = SHM.trades.filter((x) => x.sel); if (!pick.length) return;
    const batch = 'ib' + (typeof uid === 'function' ? uid() : Date.now().toString(36));
    const acc = SHM.acc, now = new Date().toISOString(), docs = [];
    pick.forEach((x) => {
      const d = { id: typeof uid === 'function' ? uid() : 't' + Math.random().toString(36).slice(2), account_id: acc, instrument: x.instrument, date: x.date, session_date: true, entry_time: x.entry_time || '', exit_time: x.exit_time || '',
        session: typeof sessionFor === 'function' ? sessionFor(x.entry_time || '09:30') : '', direction: x.direction, contracts: x.contracts, entry: x.entry, exit: x.exit, pnl_c: x.pnl_c || 0, pnl_manual: !!(x.pnl_manual || x._pnlTyped), fees_c: x.fees_c || 0,
        executions: x.executions || [], import_batch_id: batch, source: 'screenshot', discipline: Object.assign({}, SHM.each ? x._disc || {} : SHM.disc), emo: {}, review: {}, tags: [], shots: x._shot ? [x._shot] : [], setup: '', notes: '', created_at: now };
      if (x.check) d.pnl_check = true;
      if (x.fees_auto) d.fees_auto = true;
      docs.push(d);
      if (SHM.copy.size) { d.copy_group = 'g' + d.id; let k = 0; SHM.copy.forEach((aid) => docs.push(window.SweepCopy ? SweepCopy.make(d, aid, d.copy_group, k++) : Object.assign(JSON.parse(JSON.stringify(d)), { id: (typeof uid === 'function' ? uid() : 't' + Math.random().toString(36).slice(2)), account_id: aid }))); }
    });
    const btn = document.querySelector('[data-shm-save]'); if (btn) btn.disabled = true;
    try {
      const r = await fetch('api/docs/batch', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ col: 'trades', put: docs }) });
      if (!r.ok) throw new Error(String(r.status));
    } catch (e) { if (typeof toast === 'function') toast(mx('fail')); if (btn) btn.disabled = false; return; }
    docs.forEach((d) => { d.user_id = S.uid; d.updated_at = now; S.trades.push(d); });
    // the trader's account remembers the zone of its platform (asked only once)
    if (SHM.needsTz && SHM.tz && typeof editDoc === 'function') editDoc('accounts', acc, (a) => { a.platform_tz = SHM.tz; });
    close(); if (typeof render === 'function') render();
    const net = pick.reduce((a, x) => a + (x.pnl_c || 0) - (x.fees_c || 0), 0), ids = docs.map((d) => d.id);
    const msg = mx('added', { n: pick.length, p: mU2(net) });
    const undo = async () => {
      try { await fetch('api/docs/batch', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ col: 'trades', del: ids }) }); } catch (e) { /* removed locally anyway */ }
      S.trades = S.trades.filter((x) => !ids.includes(x.id)); if (typeof render === 'function') render();
    };
    if (window.SweepUndo && SweepUndo.toast) SweepUndo.toast(msg, undo, () => {}); else if (typeof toast === 'function') toast(msg);
    if (window.SweepGame && SweepGame.refresh) setTimeout(() => SweepGame.refresh(), 800);
  }
  document.addEventListener('click', (e) => {
    const sh = e.target.closest && e.target.closest('.nav-shm'); if (!sh) return;
    const g = (a) => e.target.closest('[' + a + ']');
    let b;
    if ((b = g('data-shm-all'))) { SHM.trades.forEach((x) => { x.sel = b.dataset.shmAll === '1'; }); paintMulti(); }
    else if ((b = g('data-shm-edit'))) { const i = +b.dataset.shmEdit; SHM.edit = SHM.edit === i ? null : i; paintMulti(); }
    else if (g('data-shm-done')) { SHM.edit = null; paintMulti(); }
    else if ((b = g('data-shm-dir'))) { const tr = SHM.trades[+b.dataset.i]; tr.direction = b.dataset.shmDir; recompute(tr); paintMulti(); }
    else if ((b = g('data-shm-q'))) { const k = b.dataset.shmK, v = b.dataset.shmV, q = b.dataset.shmQ; const tgt = k === 'lot' ? SHM.disc : (SHM.trades[+k.slice(1)]._disc = SHM.trades[+k.slice(1)]._disc || {}); tgt[q] = tgt[q] === v ? undefined : v; paintMulti(); }
    else if ((b = g('data-shm-copy'))) { const a = b.dataset.shmCopy; SHM.copy.has(a) ? SHM.copy.delete(a) : SHM.copy.add(a); paintMulti(); }
    else if ((b = g('data-shm-img'))) { const lb = document.createElement('div'); lb.className = 'lightbox'; lb.innerHTML = `<img src="${esc2(b.dataset.shmImg)}" alt="">`; lb.onclick = () => lb.remove(); document.body.append(lb); }
    else if (g('data-shm-save')) saveMulti();
  });
  document.addEventListener('change', (e) => {
    const t0 = e.target; if (!t0.closest || !t0.closest('.nav-shm')) return;
    if (t0.matches('[data-shm-sel]')) { SHM.trades[+t0.dataset.shmSel].sel = t0.checked; paintMulti(); }
    else if (t0.matches('[data-shm-acc]')) { SHM.acc = t0.value; SHM.trades.forEach((x) => { x._dupSeen = false; }); rebuild(); }
    else if (t0.matches('[data-shm-tz]')) { SHM.tz = t0.value; rebuild(); }
    else if (t0.matches('[data-shm-each]')) { SHM.each = t0.checked; paintMulti(); }
    else if (t0.matches('[data-shm-f]')) {
      const tr = SHM.trades[+t0.dataset.i], f = t0.dataset.shmF, v = t0.value.trim();
      if (f === 'instrument') tr.instrument = v.toUpperCase();
      else if (f === 'entry_time' || f === 'exit_time') { tr[f] = /^\d{1,2}:\d{2}$/.test(v) ? v.padStart(5, '0') : tr[f]; if (f === 'entry_time') tr.date = sessOf(tr.executions && tr.executions[0] ? tr.executions[0].t.slice(0, 10) : tr.date, tr.entry_time); }
      else if (f === 'pnl') { const n2 = num(v); if (n2 != null) { tr.pnl_c = Math.round(n2 * 100); tr._pnlTyped = true; } }
      else { const n2 = num(v); tr[f] = f === 'contracts' ? Math.max(1, Math.round(n2 || 1)) : n2; if (f === 'contracts') delete tr.turns; }   // contracts typed by the trader: a simple trade of that size
      if (f !== 'pnl') recompute(tr);
      flag(); paintMulti();
    }
  });
  window.SweepShotMulti = { open: openMulti, state: SHM };
  async function takeFiles(files) {
    files = files.filter((f) => f && /^image\//.test(f.type)); if (!files.length) return;
    if (files.length === 1 && !SH.batch.length && !SH.file) return takeFile(files[0]);
    if (SH.file && !SH.batch.length) SH.batch.push({ id: 'b0', file: SH.file, src: SH.src, shot: SH.shot, st: 'ok', f: { inst: SH.f.inst, dir: SH.dir, qty: SH.f.qty, turns: SH.f.turns, date: SH.f.date, time: SH.f.time, exitTime: SH.f.exitTime, entry: SH.f.entry, exit: SH.f.exit, fees: SH.f.fees, net: SH.f.net } });
    const added = files.map((file, i) => ({ id: 'b' + Date.now().toString(36) + i, file, src: URL.createObjectURL(file), st: 'reading', f: { inst: SH.f.inst, qty: '1', date: SH.f.date } }));
    SH.batch.push(...added); paint();
    for (const b of added) { await readOne(b); paint(); }
    // one of the screenshots shows several trades: every trade of every screenshot goes to « X trades found »
    if (SH.batch.some((b) => b.res && (b.res.trades || []).length > 1)) openMulti(SH.batch.filter((b) => b.res).map((b) => b.res), SH.batch.filter((b) => b.res).map((b) => ({ src: b.src, shot: b.shot, name: b.file && b.file.name })));
  }
  function netC() {   // the net P&L as the platform shows it (fees included)
    const v = num(SH.f.net); if (v != null) return Math.round(v * 100);
    const g = autoPnl(); return g == null ? null : g - (SH.f.fees || 0);
  }
  function rLine() {
    const n = netC(), r = num(SH.f.risk);
    if (n == null) return `<small class="muted">${t('rHint')}</small>`;
    const m = typeof money === 'function' ? money(n) : (n / 100).toFixed(2);
    return r ? `<b class="${n < 0 ? 'neg' : 'pos'}">${m}</b><span class="nav-am-rr">${(n / 100 / Math.abs(r) >= 0 ? '+' : '') + (n / 100 / Math.abs(r)).toFixed(2)} R</span>${window.SweepTerm ? SweepTerm('r') : ''}` : `<b class="${n < 0 ? 'neg' : 'pos'}">${m}</b><small class="muted">${t('rAdd')}</small>${window.SweepTerm ? SweepTerm('r') : ''}`;
  }
  function verifyLine() {
    const bits = [SH.f.inst, SH.dir ? t(SH.dir) : '', SH.f.qty ? SH.f.qty + ' ×' : '', SH.f.entry && SH.f.exit ? `${SH.f.entry} → ${SH.f.exit}` : '', SH.f.time || ''].filter(Boolean);
    return esc2(bits.join(' · '));
  }
  function autoPnl() {
    const e = num(SH.f.entry), x = num(SH.f.exit), q = SH.f.turns || num(SH.f.qty) || 1;   // average prices × contracts bought and sold
    if (e == null || x == null || !SH.dir || typeof calcPnl !== 'function') return null;
    return calcPnl(SH.dir, e, x, q, SH.f.inst);
  }
  async function takeFile(file) {
    if (!file || !/^image\//.test(file.type)) return;
    SH.file = file; SH.src = URL.createObjectURL(file);
    const ai = document.body.classList.contains('ai-on');
    SH.status = ai ? t('reading') : t('noAi'); SH.busy = ai; paint();
    // the screenshot is stored like trade screenshots
    try { if (typeof ASSETS !== 'undefined' && ASSETS) { const o = await ASSETS.upload(file); SH.shot = { id: o.id, phase: 'after', name: file.name }; } } catch (e) { /* the trade can still be saved */ }
    if (!ai) return;
    try {
      const b64 = await shotData(file);   // big screenshots are resized (kept sharp enough to read a table)
      const res = await fetch('api/ai/import', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ image: b64, mime: (b64.match(/^data:([^;]+)/) || [])[1] || file.type, mode: 'shot', account_id: SH.f && SH.f.accountPicked ? SH.f.account : '', local_tz: (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (x) { return ''; } })() }) });
      const j = await res.json().catch(() => ({}));
      if (res.status === 402) { SH.status = t('shotQuota'); SH.busy = false; paint(); if (window.SweepBilling && SweepBilling.handleApiError) SweepBilling.handleApiError(j); return; }   // Free: 3 a day (18 Oct.)
      const trs = res.ok && Array.isArray(j.trades) ? j.trades : [];
      if (trs.length >= 2) { SH.busy = false; openMulti([j], [{ src: SH.src, shot: SH.shot, name: file.name }]); return; }   // several trades: « X trades found »
      const d = trs[0];
      if (d) {   // one trade: the screen as before
        if (j.account_suggest && !SH.f.accountPicked) SH.f.account = j.account_suggest;
        else askAccount();   // (brief avance, step 3) several accounts, none on the screenshot: the sheet asks
        if (d.instrument) SH.f.inst = d.instrument;
        if (d.direction) SH.dir = d.direction;
        if (d.contracts) SH.f.qty = String(d.contracts);
        SH.f.turns = d.turns || null;   // contracts bought and sold (scale-ins): the P&L of the prices uses them
        if (d.date) SH.f.date = d.date;   // already the session (the server applies the 18:00 rule)
        if (d.entry_time) SH.f.time = String(d.entry_time).slice(0, 5);
        if (d.entry != null) SH.f.entry = String(d.entry);
        if (d.exit != null) SH.f.exit = String(d.exit);
        if (d.pnl_c != null) SH.f.net = ((d.pnl_c - (d.fees_c || 0)) / 100).toFixed(2);
        SH.f.exitTime = d.exit_time || ''; SH.f.fees = d.fees_c || 0;
        SH.status = SH.aiAsk ? ta('shotAcc') : t('read');
      } else {
        // say why: the server's message, a symbol Sweep does not know, or no trade table on the image
        const W = { en: ['No trade table found on this screenshot.', 'Symbol not known by Sweep: {s}.', 'Sweep AI could not read it ({e}).'], fr: ['Aucun tableau de trades trouvé sur cette capture.', 'Symbole inconnu de Sweep : {s}.', 'Sweep AI n’a pas pu la lire ({e}).'], es: ['No se encontró una tabla de operaciones en esta captura.', 'Símbolo desconocido para Sweep: {s}.', 'Sweep AI no pudo leerla ({e}).'] }[L] || null;
        const w3 = W || ['No trade table found on this screenshot.', 'Symbol not known by Sweep: {s}.', 'Sweep AI could not read it ({e}).'];
        SH.status = !res.ok ? w3[2].replace('{e}', j.message || j.error || res.status) : (j.unknown || []).filter(Boolean).length ? w3[1].replace('{s}', j.unknown.filter(Boolean).join(', ')) : j.no_symbol ? ({ fr: 'Aucun symbole lu sur la capture : choisis-le dans le détail du trade.', es: 'No se leyó ningún símbolo en la captura: elígelo en el detalle de la operación.' })[L] || 'No symbol read on the screenshot: pick it in the trade details.' : !(j.table || []).length && !(j.rows || []).length ? w3[0] : t('aiFail');
      }
    } catch (e) { SH.status = t('aiFail'); }
    SH.busy = false; paint();
  }
  function save() {
    const err = document.querySelector('.nav-am-err');
    if (SH.batch.length) {
      const missing = SH.batch.filter((b) => num(b.f.net) == null && !(num(b.f.entry) != null && num(b.f.exit) != null && b.f.dir));
      if (!SH.f.account || missing.length) { if (err) err.textContent = t('need'); return; }
      const keep = { file: SH.file, src: SH.src, shot: SH.shot, f: Object.assign({}, SH.f), dir: SH.dir }, list = SH.batch.slice();
      SH.batch = [];
      list.forEach((b) => { Object.assign(SH, { file: b.file, src: b.src, shot: b.shot, dir: b.f.dir || '' }); SH.f = Object.assign({}, keep.f, b.f, { account: keep.f.account }); saveOne(true); });
      Object.assign(SH, keep);
      close(); if (typeof toast === 'function') toast(t('saved') + ' · ' + list.length);
      setTimeout(() => { if (typeof render === 'function') render(); }, 80);
      return;
    }
    saveOne(false);
  }
  /** calendar day + clock time read on a screenshot → the session (18:00 ET or later = next day) */
  function sessOf(day, time) { const hm = String(time || '').slice(0, 5); return hm >= '18:00' && typeof sessionOfTs === 'function' ? sessionOfTs(day + ' ' + hm) : day; }
  function saveOne(quiet) {
    const err = document.querySelector('.nav-am-err');
    const e = num(SH.f.entry), x = num(SH.f.exit), q = Math.max(1, Math.round(num(SH.f.qty) || 1));
    const typed = num(SH.f.net) != null ? Math.round(num(SH.f.net) * 100) : null;
    if (!SH.dir && e != null && x != null && typed != null) SH.dir = (x > e) === (typed > 0) ? 'long' : 'short';   // read from the prices
    if (!SH.dir && quiet) SH.dir = 'long';   // several screenshots: the side read on each (as before)
    const net = typed != null ? typed : netC();
    if (!SH.f.account || net == null) { if (err) err.textContent = !SH.f.account && SH.aiAsk ? ta('needAcc') : t('need'); if (!SH.f.account && SH.aiAsk) { const b = document.querySelector('.nav-am-shot .nav-am-selb[data-am-sel=account]'); if (b) b.focus(); } return; }
    if (!SH.dir) { if (err) err.textContent = t('needDir'); return; }   // never guessed on the quick sheet
    const pnl = net + (SH.f.fees || 0);
    // no entry time on today's session: the New York time of the save (todayStr() is already the session: 18:00 ET or later = next day)
    const tm = /^\d{1,2}:\d{2}/.test(SH.f.time || '') ? (SH.f.time.length === 4 ? '0' + SH.f.time : SH.f.time).slice(0, 5) + ':00'
      : !quiet && (SH.f.date || today()) === today() ? new Intl.DateTimeFormat('en-GB', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).format(new Date()) : '';
    const emo = { before: [...SH.emo] }; if (SH.conf) emo.confidence = SH.conf; if (SH.exec) emo.execution = SH.exec;
    const doc = { id: typeof uid === 'function' ? uid() : 't' + Date.now(), account_id: SH.f.account, instrument: SH.f.inst, date: SH.f.date || today(), session_date: true, entry_time: tm, exit_time: SH.f.exitTime ? String(SH.f.exitTime).slice(0, 8) : '', direction: SH.dir, contracts: q,
      entry: e, exit: x, pnl_c: pnl, pnl_manual: true, real_pnl_c: net, risk_c: num(SH.f.risk) ? Math.round(Math.abs(num(SH.f.risk)) * 100) : null, stop: null, target: null, fees_c: SH.f.fees || null,
      discipline: Object.assign({}, SH.disc), emo, review: {}, shots: SH.shot ? [SH.shot] : [], tags: [], setup: SH.setup || '', notes: '', source: SH.shot || SH.src ? 'screenshot' : 'manual' };
    const same = !quiet && !SH.dupOk && dupTrade(doc, doc.account_id);   // the same trade saved twice: asked once
    if (same) {
      const hm = String(same.entry_time || '').slice(0, 5), at = LANG === 'fr' ? `${+hm.slice(0, 2)} h ${hm.slice(3, 5)}` : hm;
      if (err) err.innerHTML = `${esc2(hm ? t('dup').replace('{t}', at) : t('dupDay'))} <button type="button" class="btn sm" data-am="dupok">${esc2(t('dupOk'))}</button>`;
      return;
    }
    const copies = [...SH.copy].filter((id) => id !== doc.account_id && typeof acct === 'function' && acct(id));
    if (copies.length) doc.copy_group = typeof uid === 'function' ? uid() : 'g' + Date.now();
    if (window.SweepFiche && SweepFiche.markTrade) SweepFiche.markTrade(doc);   // a day with a pre-market sheet: off-plan until linked
    if (typeof put === 'function') {
      put('trades', doc);
      copies.forEach((id, k) => put('trades', window.SweepCopy ? SweepCopy.make(doc, id, doc.copy_group, k) : Object.assign(JSON.parse(JSON.stringify(doc)), { id: typeof uid === 'function' ? uid() : 't' + Math.random().toString(36).slice(2), account_id: id })));
    }
    if (SH.setup && window.SweepSetupPick) SweepSetupPick.keep(SH.setup);
    if (quiet) return;
    close();
    if (typeof toast === 'function') toast(t('saved'), typeof seeTradeLink === 'function' ? { link: seeTradeLink(doc.id) } : undefined);   // (27 Oct.) no sheet « which scenario? » after the save: the chips of the form
    setTimeout(() => { if (typeof render === 'function') render(); }, 80);
  }

  /* events */
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('[data-am],[data-am-pickf],[data-am-sel],[data-am-copy],[data-am-seg],[data-am-emo],[data-am-rm],[data-sp]'); if (!a) return;
    const box = a.closest('.nav-am'); if (!box) return;
    if (a.dataset.sp != null) { SH.setup = window.SweepSetupPick ? SweepSetupPick.tap(a, SH.setup) : ''; repaintKeep(); return; }   // the coach (edge T3) and the questions (edge T7) follow the setup; the row keeps its scroll
    if (a.dataset.amRm) { SH.batch = SH.batch.filter((b) => b.id !== a.dataset.amRm); if (SH.batch.length === 1) { const b = SH.batch[0]; SH.batch = []; Object.assign(SH, { file: b.file, src: b.src, shot: b.shot, dir: b.f.dir || SH.dir }); Object.assign(SH.f, b.f); } paint(); return; }
    if (a.dataset.amSel) { SH.openPick = SH.openPick === a.dataset.amSel ? null : a.dataset.amSel; paint(); return; }
    if (a.dataset.amPickf) { SH.f[a.dataset.amPickf] = a.dataset.v; SH.aiLow.delete(AK[a.dataset.amPickf]); if (a.dataset.amPickf === 'account') { SH.f.accountPicked = true; SH.aiAsk = false; } SH.openPick = null; if (a.dataset.amPickf === 'account') { SH.copy.delete(a.dataset.v); if (window.SweepCopy && SweepCopy.leadOf && SweepCopy.leadOf(a.dataset.v)) SH.copy = new Set(SweepCopy.targets(a.dataset.v)); } paint(); return; }
    if (a.dataset.amCopy) { const k = a.dataset.amCopy; SH.copy.has(k) ? SH.copy.delete(k) : SH.copy.add(k); a.classList.toggle('on'); return; }
    if (a.dataset.amSeg) { const k = a.dataset.amSeg, v = a.dataset.v; if (k === 'dir') { SH.dir = v; SH.aiLow.delete('direction'); } else if (k === 'conf') SH.conf = +v; else if (k === 'exec') SH.exec = +v; else if (k.startsWith('d:')) SH.disc[k.slice(2)] = v; paint(); return; }
    if (a.dataset.amEmo) { const k = a.dataset.amEmo; SH.emo.has(k) ? SH.emo.delete(k) : SH.emo.add(k); a.classList.toggle('on'); return; }
    const act = a.dataset.am;
    if (act === 'emo-more') { SH.allEmo = true; paint(); return; }
    if (act === 'q-more') { SH.allQ = true; paint(); return; }
    if (act === 'q-add') {
      const v = (prompt(t('addQQ')) || '').trim().slice(0, 120); if (!v) return;
      const id = 'q' + Date.now().toString(36);
      if (typeof editDoc === 'function') editDoc('settings', 'settings', (r) => { r.questions = [...(r.questions || []), { id, text: v, active: true }]; });
      SH.allQ = true; setTimeout(paint, 120); return;
    }
    if (act === 'emo-add') {
      const v = (prompt(t('addEmoQ')) || '').trim().slice(0, 30); if (!v) return;
      SH.emo.add(v); SH.allEmo = true;
      if (typeof editDoc === 'function') editDoc('settings', 'settings', (r) => { const l = r.custom_emotions || []; if (!l.includes(v)) r.custom_emotions = [...l, v]; });
      paint(); return;
    }
    if (act === 'close') close();
    if (act === 'ai-go') { const x = document.querySelector('.nav-am-shot [data-ai-text]'); aiRun(x ? x.value : SH.aiText); return; }
    if (act === 'ctx-open') { SH.ctxOpen = true; ctxPaint(); return; }
    if (act === 'save') save();
    if (act === 'dupok') { SH.dupOk = true; save(); }
    if (act === 'no-shot') { SH.noShot = true; paint(); const n = document.querySelector('.nav-am-shot [data-am-f=net]'); if (n) n.focus({ preventScroll: true }); return; }   // focused in the tap itself: the iPhone opens its keyboard only then
    if (act === 'to-manual') { const d = SH.f.date; close(); setTimeout(() => origTicket && origTicket(null, { date: d }), 280); }
  });
  document.addEventListener('toggle', (e) => { if (e.target.classList && e.target.classList.contains('nav-am-more-d')) SH.open = e.target.open; }, true);
  document.addEventListener('input', (e) => {
    const bn = e.target.closest && e.target.closest('.nav-am [data-am-bnet]'); if (bn) { const b = SH.batch.find((x) => x.id === bn.dataset.amBnet); if (b) b.f.net = bn.value; return; }
    const tx = e.target.closest && e.target.closest('.nav-am [data-ai-text]');
    if (tx) { SH.aiText = tx.value; const g = document.querySelector('.nav-am-shot .nav-ai-go'); if (g) g.hidden = !tx.value.trim(); return; }
    const f = e.target.closest && e.target.closest('.nav-am [data-am-f]'); if (!f) return;
    { const ak = AK[f.dataset.amF]; if (ak && SH.aiLow.delete(ak)) { const w = f.closest('.tk-f'); if (w) { w.classList.remove('ai-low'); const c = w.querySelector('.nav-ai-chk'); if (c) c.remove(); } } }   // corrected by the trader: no longer highlighted
    SH.f[f.dataset.amF] = f.value; if (f.dataset.amF === 'qty') delete SH.f.turns;   // contracts typed by the trader: a simple trade of that size
    const v = autoPnl(), p = document.querySelector('.nav-am-net input'); if (p) p.placeholder = v != null ? ((v - (SH.f.fees || 0)) / 100).toFixed(2) : '+250';
    const r = document.querySelector('.nav-am-r'); if (r) r.innerHTML = rLine();
    const sm = document.querySelector('.nav-am-more-d summary small'); if (sm) sm.innerHTML = verifyLine();
    coachPaint(); ctxPaint();
  });
  document.addEventListener('change', (e) => {
    const f = e.target.closest && e.target.closest('.nav-am [data-am-file]'); if (f && f.files.length) { takeFiles([...f.files]); return; }
    const s = e.target.closest && e.target.closest('.nav-am select[data-am-f]'); if (s) SH.f[s.dataset.amF] = s.value;
  });
  // the sentence sent with Enter (Shift+Enter: a new line); a screenshot dropped on the field (here and on Today)
  document.addEventListener('keydown', (e) => {
    const x = e.target.closest && e.target.closest('.nav-am [data-ai-text]');
    if (x && e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); aiRun(x.value); }
  });
  document.addEventListener('dragover', (e) => { if (e.target.closest && e.target.closest('.nav-ai-box, .nav-ai-today')) e.preventDefault(); });
  document.addEventListener('drop', (e) => {
    const box = e.target.closest && e.target.closest('.nav-ai-box, .nav-ai-today'); if (!box) return;
    const fs = [...((e.dataTransfer && e.dataTransfer.files) || [])].filter((f) => /^image\//.test(f.type)); if (!fs.length) return;
    e.preventDefault();
    if (box.classList.contains('nav-ai-today')) { if (typeof openTicket === 'function') openTicket(null, { files: fs }); } else takeFiles(fs);
  });
  /* Today: the same field, one line under the day's card; it opens the sheet with the sentence read, or the screenshot */
  const ICAI = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg>';
  window.SweepAiToday = function (host) {
    if (!host || !accList().length) { const o = host && host.querySelector('.nav-ai-today'); if (o) o.remove(); return; }
    let el = host.querySelector(':scope > .nav-ai-today');
    if (!el) {
      el = document.createElement('form'); el.className = 'nav-ai-today'; el.setAttribute('data-noi18n', ''); el.setAttribute('autocomplete', 'off');
      el.innerHTML = `<span class="nav-ai-ic">${ICAI}</span><input type="text" data-ai-today enterkeyhint="go" placeholder="${esc2(ta('ph'))}" aria-label="${esc2(ta('ph'))}"><label class="nav-ai-cam" aria-label="${esc2(t('dropT'))}">${ICS}<input type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden multiple data-ai-today-file></label><button type="submit" class="nav-ai-go" aria-label="${esc2(ta('go'))}" hidden>${ICGO}</button>`;
      el.addEventListener('submit', (e) => { e.preventDefault(); const i = el.querySelector('[data-ai-today]'), v = i.value.trim(); if (!v) return; i.value = ''; el.querySelector('.nav-ai-go').hidden = true; i.blur(); if (typeof openTicket === 'function') openTicket(null, { aiText: v }); });
      el.addEventListener('input', (e) => { if (e.target.matches('[data-ai-today]')) el.querySelector('.nav-ai-go').hidden = !e.target.value.trim(); });
      el.addEventListener('change', (e) => { const f = e.target.closest('[data-ai-today-file]'); if (f && f.files.length) { const fs = [...f.files]; f.value = ''; if (typeof openTicket === 'function') openTicket(null, { files: fs }); } });
    }
    const card = host.querySelector(':scope > .nav-rt');
    if (card && el.previousElementSibling !== card) card.after(el); else if (!card && !el.parentNode) host.prepend(el);
  };

  /* (the default is no longer switched to « by hand » after a manual trade: screenshot stays first) */
  document.addEventListener('click', (e) => { const a = e.target.closest && e.target.closest('[data-am-imp]'); if (a) { e.preventDefault(); close(); setTimeout(impSheet, 280); } });   // the CSV in a sheet too (19 Oct.)
  document.addEventListener('paste', (e) => {
    if (!document.querySelector('.nav-am-shot.open')) return;
    const its = [...(e.clipboardData && e.clipboardData.items || [])].filter((i) => i.type.startsWith('image/'));
    if (its.length) { e.preventDefault(); takeFiles(its.map((i) => i.getAsFile())); }
  });

  /* « Add a trade » goes through here: the question once, then the trader's way */
  function go(v, opts) {
    if (v === 'shot') { if (window.SweepGame && SweepGame.planFirst && SweepGame.planFirst(() => shotForm(opts))) return; shotForm(opts); }
    else origTicket && origTicket(null, opts || {});
  }
  (function wrap(n) {
    if (typeof window.openTicket !== 'function') { if (n < 80) setTimeout(() => wrap(n + 1), 100); return; }
    if (window.__amWrapped) return; window.__amWrapped = true;   // once, whatever wraps around it later (the plan-first gate works either way)
    origTicket = window.openTicket;
    const w = function (id, opts) {
      if (id || !(S.accounts || []).some((a) => a.status !== 'archived') || (opts && opts.manual)) return origTicket.apply(this, arguments);
      if (!(S.accounts || []).filter((a) => a.status !== 'archived').length && !(opts && opts.edit)) {   // (sample accounts count: the sample trades belong to them)   // no account yet: the account comes first
        if (typeof toast === 'function') toast(({ en: 'Add your account first: every trade belongs to one.', fr: 'Ajoute d’abord ton compte : chaque trade lui appartient.', es: 'Añade primero tu cuenta: cada operación pertenece a una.' })[(typeof LANG !== 'undefined' && LANG) || 'en']);
        if (!/^#?(dashboard)?$/.test((location.hash || '').replace(/^#/, ''))) location.hash = '#dashboard';
        setTimeout(() => { const f = document.querySelector('#main .onb form[data-form="account"]'); if (f) f.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 400);
        return;
      }
      go('shot', opts);   // always the screenshot first, never asked (18 Oct., Mateo); « Enter by hand » and « Import CSV » are on it
    };
    w.__mode = true; window.openTicket = w;
  })(0);

  /* 3. Import a CSV in a sheet, like the screenshot and the manual form (19 Oct., Mateo: « que ça ne nous sorte pas de
   *    l'univers »): the account, the file, what it holds (new trades, P&L, those already in Sweep), « Import ». The file is
   *    read and saved by the import page's own code (impFile, impGo: formats, fees, duplicates); a file with several
   *    accounts goes on to the import page, where they are matched. */
  const IT = ({
    en: { t: 'Import a CSV', sub: 'Tradovate, Rithmic R|Trader Pro, TopstepX, TradingView', acc: 'Account', drop: 'Tap to choose your CSV file', dropD: 'Drop your CSV file here, or click to choose it', reading: 'Reading the file…',
      found: '{n} new trades · {p}', found1: '1 new trade · {p}', dups: '{n} already in Sweep', none: 'No new trade in this file for this account.', go: 'Import {n} trades', go1: 'Import 1 trade', multi: 'This file holds several accounts: match each one to a Sweep account on the import page.', page: 'Continue on the import page', help: 'How to export it from my platform', other: 'Another file' },
    fr: { t: 'Importer un CSV', sub: 'Tradovate, Rithmic R|Trader Pro, TopstepX, TradingView', acc: 'Compte', drop: 'Touche pour choisir ton fichier CSV', dropD: 'Dépose ton fichier CSV ici, ou clique pour le choisir', reading: 'Lecture du fichier…',
      found: '{n} nouveaux trades · {p}', found1: '1 nouveau trade · {p}', dups: '{n} déjà dans Sweep', none: 'Aucun nouveau trade pour ce compte dans ce fichier.', go: 'Importer {n} trades', go1: 'Importer 1 trade', multi: 'Ce fichier contient plusieurs comptes : associe chacun à un compte Sweep sur la page d’import.', page: 'Continuer sur la page d’import', help: 'Comment l’exporter de ma plateforme', other: 'Un autre fichier' },
    es: { t: 'Importar un CSV', sub: 'Tradovate, Rithmic R|Trader Pro, TopstepX, TradingView', acc: 'Cuenta', drop: 'Toca para elegir tu archivo CSV', dropD: 'Suelta tu archivo CSV aquí, o haz clic para elegirlo', reading: 'Leyendo el archivo…',
      found: '{n} operaciones nuevas · {p}', found1: '1 operación nueva · {p}', dups: '{n} ya en Sweep', none: 'Ninguna operación nueva para esta cuenta en este archivo.', go: 'Importar {n} operaciones', go1: 'Importar 1 operación', multi: 'Este archivo tiene varias cuentas: asocia cada una a una cuenta de Sweep en la página de importación.', page: 'Seguir en la página de importación', help: 'Cómo exportarlo de mi plataforma', other: 'Otro archivo' } })[L] || null;
  const it = (k, v) => String(((IT || {})[k]) || k).replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ''));
  const IS = { busy: false };
  function impSheet() {
    if (typeof IMP === 'undefined' || typeof impFile !== 'function') { location.hash = '#import'; return; }
    IMP.rows = null; IMP.file = ''; IMP.err = ''; IS.busy = false;
    layer('nav-imp-sheet', ''); paintImp();
  }
  function paintImp() {
    const el = document.querySelector('.nav-imp-sheet .nav-am-in'); if (!el) return;
    const accs = ((l) => (l.some((a) => !a.demo) ? l.filter((a) => !a.demo) : l))((S.accounts || []).filter((a) => a.status !== 'archived' && a.status !== 'closed'));
    if (!IMP.account || !accs.some((a) => a.id === IMP.account)) IMP.account = (accs[0] || {}).id || '';
    const rows = IMP.rows || [], multi = !!(window.SweepImport && SweepImport.fileAccts && SweepImport.fileAccts().length > 1);
    const have = new Set((S.trades || []).filter((x) => x.account_id === IMP.account && x.import_key).map((x) => x.import_key));
    const fresh = rows.filter((r) => !have.has(r.key)), dups = rows.length - fresh.length, sum = fresh.reduce((a, r) => a + (r.pnl_c || 0), 0);
    const coarse = window.matchMedia && matchMedia('(pointer: coarse)').matches;
    let res = '';
    if (IS.busy) res = `<p class="nav-am-st busy">${it('reading')}</p>`;
    else if (IMP.err) res = `<p class="nav-am-st nav-imps-err">${esc2(IMP.err)}</p>`;
    else if (rows.length && multi) res = `<p class="nav-am-st">${it('multi')}</p><button type="button" class="btn primary nav-am-save" data-imps="page">${it('page')}</button>`;
    else if (rows.length) res = `<div class="nav-imps-sum"><b class="${sum > 0 ? 'pos' : sum < 0 ? 'neg' : ''}">${fresh.length ? esc2(it(fresh.length === 1 ? 'found1' : 'found', { n: fresh.length, p: typeof money === 'function' ? money(sum) : (sum / 100).toFixed(2) })) : it('none')}</b>${dups ? `<small class="muted">${it('dups', { n: dups })}</small>` : ''}</div>
      ${fresh.length ? `<button type="button" class="btn primary nav-am-save" data-imps="go">${it(fresh.length === 1 ? 'go1' : 'go', { n: fresh.length })}</button>` : ''}`;
    el.innerHTML = `<div class="tk-head nav-am-head"><div><h2>${it('t')}</h2><span class="muted">${it('sub')}</span></div><button type="button" class="link" data-imps="close">${t('cancel')}</button></div>
      <label class="tk-f"><span>${it('acc')}</span><select data-imps="acc">${accs.map((a) => `<option value="${esc2(a.id)}" ${a.id === IMP.account ? 'selected' : ''}>${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</option>`).join('')}</select></label>
      <label class="nav-am-drop nav-imps-drop ${IMP.file ? 'has' : ''}"><span class="nav-am-ic"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5"/><path d="M5 19h14"/></svg></span><b>${IMP.file ? esc2(IMP.file) : it(coarse ? 'drop' : 'dropD')}</b>${IMP.file ? `<small class="muted">${it('other')}</small>` : ''}<input type="file" accept=".csv,text/csv,.txt,text/plain" hidden data-imps="file"></label>
      ${res}
      <button type="button" class="link nav-imps-help" data-imp-help>${it('help')}</button>`;
  }
  async function readImp(file) {
    if (!file) return;
    IS.busy = true; paintImp();
    try { await impFile(file); } catch (e) { IMP.err = String(e && e.message || e); }
    IS.busy = false; paintImp();
  }
  document.addEventListener('change', (e) => {
    const x = e.target.closest && e.target.closest('.nav-imp-sheet [data-imps]'); if (!x) return;
    if (x.dataset.imps === 'acc') { IMP.account = x.value; paintImp(); }
    else if (x.dataset.imps === 'file' && x.files && x.files[0]) { const f = x.files[0]; x.value = ''; readImp(f); }
  });
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('.nav-imp-sheet [data-imps]'); if (!b || b.tagName === 'SELECT' || b.tagName === 'INPUT') return;
    const k = b.dataset.imps;
    if (k === 'close') close();
    else if (k === 'page') { close(); setTimeout(() => { location.hash = '#import'; }, 250); }   // (IMP keeps the file: the page shows it)
    else if (k === 'go') { b.disabled = true; try { await impGo(); } finally { close(); } }
  });
  document.addEventListener('dragover', (e) => { if (e.target.closest && e.target.closest('.nav-imps-drop')) e.preventDefault(); });
  document.addEventListener('drop', (e) => { const d = e.target.closest && e.target.closest('.nav-imps-drop'); if (!d) return; e.preventDefault(); const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]; if (f) readImp(f); });
  window.SweepImportSheet = { open: impSheet };

  // (28 Oct., activation F, C4) the manual form opens on its fields only: « From a screenshot », the CSV import and « Log with AI »
  // are in the « + » sheet (they were two buttons and a banner right under the title)

  /* Settings: no « Adding a trade » choice any more (18 Oct., Mateo: always the screenshot first, never asked) */
  function settingsRow() { const r = document.querySelector('#main .nav-am-set'); if (r) r.remove(); }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__am) {
    const w = function () { const out = appRender.apply(this, arguments); try { settingsRow(); } catch (e) { /* never blocks */ } return out; };
    w.__am = true; window.render = w;
  }
  window.SweepAddMode = { open: (opts) => shotForm(opts) };
})();

/* ───────────── trade page: copy trading in plain sight ─────────────
 * The « Copy to accounts » action lived in the « ⋯ » menu. Now a line under the trade says where it is,
 * and offers to copy it to the other accounts (the trader may have forgotten when logging it). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: { only: 'Only on {a}.', also: 'Also on {l}.', ask: 'Did you take it on other accounts too?', btn: 'Copy to other accounts', grp: 'Copy to my {g} group ({n})', grp0: 'Copy to my group ({n})', done: 'Copied to {n}', acc: ['1 account', '{k} accounts'] },
    fr: { only: 'Seulement sur {a}.', also: 'Aussi sur {l}.', ask: 'Tu l’as pris sur d’autres comptes aussi ?', btn: 'Copier sur d’autres comptes', grp: 'Copier sur mon groupe {g} ({n})', grp0: 'Copier sur mon groupe ({n})', done: 'Copié sur {n}', acc: ['1 compte', '{k} comptes'] },
    es: { only: 'Solo en {a}.', also: 'También en {l}.', ask: '¿La tomaste también en otras cuentas?', btn: 'Copiar a otras cuentas', grp: 'Copiar a mi grupo {g} ({n})', grp0: 'Copiar a mi grupo ({n})', done: 'Copiado en {n}', acc: ['1 cuenta', '{k} cuentas'] } }[L] || null;
  const tx = T || { only: 'Only on {a}.', also: 'Also on {l}.', ask: 'Did you take it on other accounts too?', btn: 'Copy to other accounts', grp: 'Copy to my {g} group ({n})', grp0: 'Copy to my group ({n})', done: 'Copied to {n}', acc: ['1 account', '{k} accounts'] };
  const accN = (k) => tx.acc[k === 1 ? 0 : 1].replace('{k}', k);
  /** the trader's group of this trade's account: the accounts that do not have this trade yet */
  function groupOf(t, on) {
    const a = typeof getDoc === 'function' && getDoc('accounts', t.account_id), all = a && a.group_id && typeof copyGroups === 'function' ? copyGroups(t).get(a.group_id) : null;
    return all ? { g: a.group_id, name: typeof groupName === 'function' ? groupName(all) : '', left: all.filter((x) => x.id !== t.account_id && !on.has(x.id)) } : null;
  }
  /* « Copy to my Apex group (4 accounts) »: one tap, each copy at its account's size (SweepCopy), « Undo » for 5 s */
  function copyToGroup(id, gid) {
    const t = getDoc('trades', id); if (!t || !window.SweepCopy) return;
    const on = new Set((typeof copiesOf === 'function' ? copiesOf(t) : [t]).map((x) => x.account_id)), G = groupOf(t, on);
    if (!G || G.g !== gid || !G.left.length) return;
    const had = t.copy_group, g = had || (typeof uid === 'function' ? uid() : 'g' + Date.now());
    if (!had) editDoc('trades', t.id, (d) => { d.copy_group = g; });
    const src = JSON.parse(JSON.stringify(getDoc('trades', t.id))), made = G.left.map((a, k) => { const d = SweepCopy.make(src, a.id, g, k); put('trades', d); return d.id; });
    if (typeof render === 'function') render();
    const label = tx.done.replace('{n}', accN(made.length));
    if (window.SweepUndo) SweepUndo.toast(label, () => { made.forEach((x) => remove('trades', x)); if (!had) editDoc('trades', t.id, (d) => { delete d.copy_group; }); });
    else if (typeof toast === 'function') toast(label);
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-copy-grp]'); if (!b) return; e.preventDefault(); copyToGroup(b.dataset.id, b.dataset.copyGrp); });
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2.5"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>';
  function line() {
    const m = /^#trade\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), t = typeof getDoc === 'function' && getDoc('trades', id);
    if (!t || t.untracked) return;   // (a « Trades not detailed » line: a gap of that account, never copied)
    const main = document.getElementById('main'); if (!main) return;
    const group = typeof copiesOf === 'function' ? copiesOf(t) : [t];
    const on = new Set(group.map((x) => x.account_id));
    // an account that can take a copy: active, not paused by the plan, real (sample accounts only for a sample trade)
    const usable = (a) => a.status !== 'archived' && a.status !== 'closed' && (!a.demo || t.demo) && !(typeof billFrozen === 'function' && billFrozen(a.id));
    const free0 = (S.accounts || []).filter((a) => usable(a) && !on.has(a.id));
    // B14 / brief 02 part 4: ask only when another active account has a trade in the same session (likely copy trading; the
    // sample data's trades never count for a real one); otherwise « Copy to accounts » stays in the « ⋯ » menu, without a banner
    const free = free0.filter((a) => (S.trades || []).some((x) => x.account_id === a.id && x.date === t.date && (!x.demo || t.demo)));
    const name = (aid) => (typeof acctLabel === 'function' ? acctLabel(aid) : aid);
    const others = group.filter((x) => x.id !== t.id).map((x) => name(x.account_id));
    const panelOpen = typeof CP !== 'undefined' && CP && CP.id === t.id;
    const G = groupOf(t, on);
    let html = '';
    // (2 Nov., audit « transfuge » G1) the accounts it is already on: only in the folded line under the result (« Also on 4 accounts
    // · total … »), never here too; this banner stays only to offer the copy
    if (G && G.left.length && !panelOpen) html = `<div class="nav-copy" data-noi18n><span class="nav-copy-ic">${ICON}</span><span class="nav-copy-t">${others.length ? `<b>${tx.ask}</b>` : tx.only.replace('{a}', esc2(name(t.account_id)))}</span><button type="button" class="btn sm primary" data-copy-grp="${esc2(G.g)}" data-id="${esc2(t.id)}">${esc2((G.name ? tx.grp.replace('{g}', G.name) : tx.grp0).replace('{n}', accN(G.left.length)))}</button></div>`;
    else if (free.length && !panelOpen) html = `<div class="nav-copy" data-noi18n><span class="nav-copy-ic">${ICON}</span><span class="nav-copy-t">${others.length ? '' : tx.only.replace('{a}', esc2(name(t.account_id))) + ' '}<b>${tx.ask}</b></span><button type="button" class="btn sm primary" data-act="copy-open" data-id="${esc2(t.id)}">${tx.btn}</button></div>`;
    let el = main.querySelector('.nav-copy');
    if (!html) { if (el) el.remove(); return; }
    if (!el) {
      const edit = main.querySelector('[data-act="edit-trade"]'); const head = edit && (edit.closest('.row') || edit.parentElement);
      const host = head || main.firstElementChild; if (!host) return;
      host.insertAdjacentHTML('afterend', html);
    } else if (el.outerHTML !== html) el.outerHTML = html;
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__copy) {
    const w = function () { const out = appRender.apply(this, arguments); try { line(); } catch (e) { /* never blocks */ } return out; };
    w.__copy = true; window.render = w;
  }
})();

/* ───────────── payouts: the firm's real conditions, counted since the last payout request ─────────────
 * rules.payout_win_days / payout_win_min_c   N winning days of at least $X (Topstep 5 × $150, Apex 5 × $100–350…)
 * rules.payout_min_bal_c                     balance to keep (Apex safety net, TPT buffer, MFFU buffer)
 * rules.payout_min_c / payout_max_c / payout_max_pct / payout_ladder_c   request size
 * rules.payout_cycle_pos / payout_cycle_min_c  profitable since the last payout
 * rules.payout_first_min_c                  profit since the start before the first payout (Alpha Direct: withdrawal target)
 * rules.consistency_pct                      best day ≤ X % of the cycle's profit
 * rules.payout_max_n                         the firm's number of payouts on the account (Apex 6) */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { sumD: '{d} winning days', sumM: 'min {m}', sum0: 'not set yet', t: 'Payout', rules: 'Payout rules', ready: 'Ready for a payout', notyet: 'Not yet', avail: 'You can request up to {v}', since: 'Counted since your last request ({d}).', first: 'Counted since the start of the account.', win: 'Winning days of {m}+', winAny: 'Profitable days', tdays: 'Traded days', cons: 'Best day ≤ {p} of the profit', pos: 'Profitable since the last payout', cmin: 'Profit since the last payout', fmin: 'Profit before the first payout', bal: 'Balance to keep', amt: 'Amount available (min {m})', maxn: 'Payouts made', req: 'Record my request',
      n_win: ['1 more winning day of {m}+', '{k} more winning days of {m}+'], n_any: ['1 more profitable day', '{k} more profitable days'], n_td: ['1 more traded day', '{k} more traded days'],
      n_pos: '{v} more profit to be positive since the last payout', n_fmin: '{v} more profit before the first payout', n_cmin: '{v} more profit since the last payout',
      n_cons: ['Bring your best day under {p}: about {v} more profit, on at least 1 more day', 'Bring your best day under {p}: about {v} more profit, spread over at least {k} days'],
      n_bal: '{v} more above the balance to keep', n_amt: '{v} more profit to request the minimum of {m}', n_maxn: 'You made the {n} payouts this account allows', n_brk: 'This account went past its max loss: no payout', none: 'Add your firm’s payout rules to see when you can request one.', f_days: 'Winning days required', f_wmin: 'Minimum profit per day ($)', f_min: 'Minimum payout ($)', f_max: 'Maximum per payout ($)', f_pct: 'Max % of the profit', f_bal: 'Balance to keep ($)', hint: 'Filled in by the preset of your firm when there is one. Check them on your firm’s site.' },
    fr: { sumD: '{d} jours gagnants', sumM: 'min {m}', sum0: 'pas encore réglées', t: 'Payout', rules: 'Règles de payout', ready: 'Prêt pour un payout', notyet: 'Pas encore', avail: 'Tu peux demander jusqu’à {v}', since: 'Compté depuis ta dernière demande ({d}).', first: 'Compté depuis le début du compte.', win: 'Jours gagnants de {m} et +', winAny: 'Jours profitables', tdays: 'Jours tradés', cons: 'Meilleur jour ≤ {p} du profit', pos: 'Profitable depuis le dernier payout', cmin: 'Profit depuis le dernier payout', fmin: 'Profit avant le premier payout', bal: 'Solde à garder', amt: 'Montant disponible (min {m})', maxn: 'Payouts faits', req: 'Enregistrer ma demande',
      n_win: ['Encore 1 jour gagnant de {m} et +', 'Encore {k} jours gagnants de {m} et +'], n_any: ['Encore 1 jour profitable', 'Encore {k} jours profitables'], n_td: ['Encore 1 jour tradé', 'Encore {k} jours tradés'],
      n_pos: 'Encore {v} de profit pour repasser en positif depuis le dernier payout', n_fmin: 'Encore {v} de profit avant le premier payout', n_cmin: 'Encore {v} de profit depuis le dernier payout',
      n_cons: ['Baisse ton meilleur jour sous {p} : environ {v} de profit en plus, sur au moins 1 jour', 'Baisse ton meilleur jour sous {p} : environ {v} de profit en plus, réparti sur au moins {k} jours'],
      n_bal: 'Encore {v} au-dessus du solde à garder', n_amt: 'Encore {v} de profit pour demander le minimum de {m}', n_maxn: 'Tu as fait les {n} payouts que ce compte permet', n_brk: 'Ce compte a dépassé sa perte max : pas de payout', none: 'Ajoute les règles de payout de ta firme pour voir quand tu pourras en demander un.', f_days: 'Jours gagnants requis', f_wmin: 'Profit minimum par jour ($)', f_min: 'Payout minimum ($)', f_max: 'Maximum par payout ($)', f_pct: 'Max % du profit', f_bal: 'Solde à garder ($)', hint: 'Remplies par le préréglage de ta firme quand il y en a un. Vérifie-les sur le site de ta firme.' },
    es: { sumD: '{d} días ganadores', sumM: 'mín {m}', sum0: 'aún sin definir', t: 'Payout', rules: 'Reglas de payout', ready: 'Listo para un payout', notyet: 'Aún no', avail: 'Puedes pedir hasta {v}', since: 'Contado desde tu última solicitud ({d}).', first: 'Contado desde el inicio de la cuenta.', win: 'Días ganadores de {m} o más', winAny: 'Días rentables', tdays: 'Días operados', cons: 'Mejor día ≤ {p} del beneficio', pos: 'Rentable desde el último payout', cmin: 'Beneficio desde el último payout', fmin: 'Beneficio antes del primer payout', bal: 'Saldo a mantener', amt: 'Importe disponible (mín. {m})', maxn: 'Payouts hechos', req: 'Registrar mi solicitud',
      n_win: ['Falta 1 día ganador de {m} o más', 'Faltan {k} días ganadores de {m} o más'], n_any: ['Falta 1 día rentable', 'Faltan {k} días rentables'], n_td: ['Falta 1 día operado', 'Faltan {k} días operados'],
      n_pos: 'Faltan {v} de beneficio para volver a positivo desde el último payout', n_fmin: 'Faltan {v} de beneficio antes del primer payout', n_cmin: 'Faltan {v} de beneficio desde el último payout',
      n_cons: ['Baja tu mejor día bajo el {p}: unos {v} más de beneficio, en al menos 1 día más', 'Baja tu mejor día bajo el {p}: unos {v} más de beneficio, repartidos en al menos {k} días'],
      n_bal: 'Faltan {v} por encima del saldo a mantener', n_amt: 'Faltan {v} de beneficio para pedir el mínimo de {m}', n_maxn: 'Hiciste los {n} payouts que permite esta cuenta', n_brk: 'Esta cuenta superó su pérdida máxima: sin payout', none: 'Añade las reglas de payout de tu firma para ver cuándo puedes pedir uno.', f_days: 'Días ganadores requeridos', f_wmin: 'Beneficio mínimo por día ($)', f_min: 'Payout mínimo ($)', f_max: 'Máximo por payout ($)', f_pct: 'Máx. % del beneficio', f_bal: 'Saldo a mantener ($)', hint: 'Rellenadas por el preajuste de tu firma cuando existe. Compruébalas en el sitio de tu firma.' } };
  const t = (k) => (T[L] || T.en)[k];
  const $u = (c) => (typeof moneyU === 'function' ? moneyU(Math.round(c)) : '$' + (Math.round(c) / 100).toFixed(2));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const net1 = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0));
  const pc = (n) => n + (L === 'en' ? '%' : '\u202f%');   // a percent never leaves its number (« 50% », « 50 % » with a narrow space)
  const up = (c) => $u(Math.ceil(Math.max(0, c) / 100) * 100);   // what is missing, in whole dollars, rounded up
  const fill = (k, n, o) => { const v = t(k), s = Array.isArray(v) ? v[(L === 'fr' ? n > 1 : n !== 1) ? 1 : 0] : v; return s.replace(/\{(\w+)\}/g, (x, y) => (o[y] != null ? o[y] : x)); };

  function status(acc) {
    if (!acc) return null;
    const r = acc.rules || {};
    const has = r.payout_win_days || r.payout_trade_days || r.payout_min_bal_c || r.payout_min_c || r.payout_max_c || r.payout_cycle_pos || r.payout_first_min_c;
    if (!has) return null;
    // the payouts that count: requested, approved or paid (a planned one is not asked yet, a rejected one never happened);
    // each one restarts the cycle and is one step of the firm's ladder (brief 02 part 3)
    const pays = (S.payouts || []).filter((p) => p.account_id === acc.id && p.status !== 'rejected' && p.status !== 'planned');
    const dateOf = (p) => p.request_date || p.approval_date || p.payment_date || (p.created_at || '').slice(0, 10);
    const last = pays.map(dateOf).filter(Boolean).sort().pop() || null;
    const tr = (S.trades || []).filter((x) => x.account_id === acc.id && (!last || x.date > last));
    const days = {}; tr.forEach((x) => { days[x.date] = (days[x.date] || 0) + net1(x); });
    const vals = Object.values(days), cycle = vals.reduce((a, v) => a + v, 0);
    let st = null; try { st = acctState(acc); } catch (e) { /* no state */ }
    const bal = st ? st.bal : (acc.starting_balance_c || 0), start = acc.starting_balance_c || 0;
    const conds = [];
    if (r.payout_win_days) {
      const m = r.payout_win_min_c || 0, n = vals.filter((v) => (m ? v >= m : v > 0)).length;
      conds.push({ k: 'win', label: m ? t('win').replace('{m}', $u(m)) : t('winAny'), ok: n >= r.payout_win_days, have: `${Math.min(n, r.payout_win_days)} / ${r.payout_win_days}`, frac: Math.min(1, n / r.payout_win_days) });
    }
    if (r.payout_trade_days) {   // days with at least one trade, whatever the result (Topstep Consistency, Apex Legacy)
      const n = vals.length;
      conds.push({ k: 'tdays', label: t('tdays'), ok: n >= r.payout_trade_days, have: `${Math.min(n, r.payout_trade_days)} / ${r.payout_trade_days}`, frac: Math.min(1, n / r.payout_trade_days) });
    }
    if (r.payout_cycle_pos && last) conds.push({ k: 'pos', label: t('pos'), ok: cycle > 0, have: $u(cycle), frac: cycle > 0 ? 1 : 0 });
    if (r.payout_first_min_c && !last) conds.push({ k: 'fmin', label: t('fmin'), ok: cycle >= r.payout_first_min_c, have: `${$u(Math.max(0, cycle))} / ${$u(r.payout_first_min_c)}`, frac: Math.max(0, Math.min(1, cycle / r.payout_first_min_c)) });
    if (r.payout_cycle_min_c && last) conds.push({ k: 'cmin', label: t('cmin'), ok: cycle >= r.payout_cycle_min_c, have: `${$u(Math.max(0, cycle))} / ${$u(r.payout_cycle_min_c)}`, frac: Math.max(0, Math.min(1, cycle / r.payout_cycle_min_c)) });
    if (r.consistency_pct && !r.target_c) {
      // one consistency for the whole app (consPct, app.js; brief 00, Q4): ÷ the total net profit, or the winning days if the catalogue says so
      const pos = vals.filter((v) => v > 0), best = pos.length ? Math.max(...pos) : 0, sum = (r.consistency_base === 'win' ? pos : vals).reduce((a, v) => a + v, 0);
      const pct = typeof consPct === 'function' ? consPct(vals, r.consistency_base) : (sum > 0 ? (best / sum) * 100 : null), okc = pct != null && pct <= r.consistency_pct;
      conds.push({ k: 'cons', label: t('cons').replace('{p}', pc(r.consistency_pct)), ok: okc, have: pct != null ? pc(Math.round(pct)) : '—', frac: okc ? 1 : 0, best, sum });
    }
    const minReq = r.payout_min_c || 0;
    if (r.payout_min_bal_c) conds.push({ k: 'bal', label: t('bal'), ok: bal >= r.payout_min_bal_c + minReq, have: `${$u(bal)} / ${$u(r.payout_min_bal_c + minReq)}`, frac: Math.max(0, Math.min(1, (bal - start) / Math.max(1, r.payout_min_bal_c + minReq - start))) });
    // what can be asked for
    let avail = r.payout_min_bal_c ? bal - r.payout_min_bal_c : bal - start;
    if (r.payout_max_pct) avail = Math.min(avail, Math.floor((bal - start) * r.payout_max_pct / 100));
    const done = pays.length;   // the next payout is n° done + 1 of the ladder (a requested one counts: the firm caps the next request)
    const cap = Array.isArray(r.payout_ladder_c) && r.payout_ladder_c.length ? r.payout_ladder_c[Math.min(done, r.payout_ladder_c.length - 1)] : r.payout_max_c;
    if (cap) avail = Math.min(avail, cap);
    avail = Math.max(0, avail);
    conds.push({ k: 'amt', label: t('amt').replace('{m}', $u(minReq)), ok: avail >= Math.max(1, minReq), have: $u(avail), frac: minReq ? Math.max(0, Math.min(1, avail / minReq)) : (avail > 0 ? 1 : 0) });
    // the firm's number of payouts on this account (Apex 6, LucidFlex 5…): none left → no new request
    if (r.payout_max_n) conds.push({ k: 'maxn', label: t('maxn'), ok: done < r.payout_max_n, have: `${Math.min(done, r.payout_max_n)} / ${r.payout_max_n}`, frac: done < r.payout_max_n ? 1 : 0 });
    const breached = st && st.breached;
    const ready = !breached && conds.every((c) => c.ok);
    // not ready: what is missing, exactly, one line per condition (« 2 more winning days of $250+ », « about $600 more profit… »)
    const todo = [];
    if (!ready) {
      const bad = (k) => conds.find((c) => c.k === k && !c.ok), m = r.payout_win_min_c || 0;
      if (breached) todo.push({ k: 'brk', text: t('n_brk') });
      if (bad('win')) { const k = r.payout_win_days - vals.filter((v) => (m ? v >= m : v > 0)).length; todo.push({ k: 'win', text: fill(m ? 'n_win' : 'n_any', k, { k, m: $u(m) }) }); }
      if (bad('tdays')) { const k = r.payout_trade_days - vals.length; todo.push({ k: 'tdays', text: fill('n_td', k, { k }) }); }
      if (bad('pos')) todo.push({ k: 'pos', text: fill('n_pos', 0, { v: up(1 - cycle) }) });
      if (bad('fmin')) todo.push({ k: 'fmin', text: fill('n_fmin', 0, { v: up(r.payout_first_min_c - cycle) }) });
      if (bad('cmin')) todo.push({ k: 'cmin', text: fill('n_cmin', 0, { v: up(r.payout_cycle_min_c - cycle) }) });
      const cb = bad('cons');
      if (cb && cb.sum > 0) {   // the best day must weigh ≤ X %: the profit has to grow to best × 100 / X, on days each no bigger than the best one
        const more = Math.ceil(cb.best * 100 / r.consistency_pct) - cb.sum, k = Math.max(1, Math.ceil(more / cb.best));
        todo.push({ k: 'cons', text: fill('n_cons', k, { k, p: pc(r.consistency_pct), v: up(more) }) });
      }
      const bb = bad('bal'); if (bb) todo.push({ k: 'bal', text: fill('n_bal', 0, { v: up(r.payout_min_bal_c + minReq - bal) }) });
      if (bad('amt') && minReq) {   // the request's minimum: enough above the safety net, and enough profit when only a part of it can be asked for
        const x = Math.max(r.payout_min_bal_c ? r.payout_min_bal_c + minReq - bal : minReq - (bal - start), r.payout_max_pct ? Math.ceil(minReq * 100 / r.payout_max_pct) - (bal - start) : 0);
        if (x > 0 && !(bb && x <= r.payout_min_bal_c + minReq - bal)) todo.push({ k: 'amt', text: fill('n_amt', 0, { v: up(x), m: $u(minReq) }) });
      }
      if (bad('maxn')) todo.splice(0, todo.length, ...todo.filter((x) => x.k === 'brk'), { k: 'maxn', text: fill('n_maxn', 0, { n: r.payout_max_n }) });   // no payout left: that is the one thing to say (« 5 more winning days » would promise one)
    }
    return { ready, conds, avail, last, done, max_n: r.payout_max_n || null, todo, pct: ready ? 100 : Math.min(99, Math.round(Math.min(...conds.map((c) => c.frac)) * 100)) };   // (the server: GameV2::payoutStatus)
  }
  /* « Record my request »: My money's payout form, open, for this account, « requested », with the most that can be asked for
     (brief 02 part 3; the Today « Ready for payout » pill too) */
  function request(id) {
    const a = typeof getDoc === 'function' && getDoc('accounts', id), s = a && status(a);
    try { sessionStorage.setItem('sw.openPayout', JSON.stringify({ acc: id, gross_c: s && s.ready ? s.avail : 0, status: 'requested' })); } catch (x) { /* private mode */ }
    location.hash = '#payouts';
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-po-req]'); if (b) { e.preventDefault(); request(b.dataset.poReq); } });
  window.SweepPayout = { status, request };

  /* the account page: conditions one by one, and the rules to edit */
  function card() {
    const m = /^#account\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), a = typeof getDoc === 'function' && getDoc('accounts', id); if (!a) return;
    const main = document.getElementById('main'); if (!main) return;
    const r = a.rules || {}, s = status(a);
    // (27 Oct., brief « nouveau trader » N4) an evaluation: the payout rules folded (they serve once funded), still one tap away
    const funded = ['funded', 'live'].includes(a.phase) || ['funded', 'live'].includes(a.money_type);
    const val = (k) => (r[k] == null ? '' : k.endsWith('_c') ? (r[k] / 100) : r[k]);
    // (10 Nov., brief « produit final » step 4) the rules stay folded, their summary on the line: opened with a tap
    const poSum = (x) => { const p = []; if (x.payout_win_days) p.push(t('sumD').replace('{d}', x.payout_win_days)); if (x.payout_min_c) p.push(t('sumM').replace('{m}', $u(x.payout_min_c))); return p.join(' · ') || t('sum0'); };
    const fld = (k, lab, ph) => `<label class="f"><span>${lab}</span><input inputmode="decimal" data-po="${k}" value="${esc2(val(k))}" placeholder="${ph || ''}"></label>`;
    const head = s ? `<div class="nav-po-h ${s.ready ? 'ok' : ''}"><b>${s.ready ? '✓ ' + t('ready') : t('notyet')}</b>${s.ready ? `<span>${t('avail').replace('{v}', $u(s.avail))}</span><button type="button" class="btn primary sm nav-po-req" data-po-req="${esc2(id)}">${t('req')}</button>` : ''}${!s.ready && s.todo.length ? `<ul class="nav-po-todo">${s.todo.map((x) => `<li data-k="${x.k}">${esc2(x.text)}</li>`).join('')}</ul>` : ''}</div>
      <ul class="nav-po-c">${s.conds.map((c) => `<li class="${c.ok ? 'ok' : ''}"><i>${c.ok ? '✓' : ''}</i><span>${esc2(c.label)}</span><b>${esc2(c.have)}</b><s style="--w:${Math.round(c.frac * 100)}%"></s></li>`).join('')}</ul>
      <small class="muted">${s.last ? t('since').replace('{d}', s.last) : t('first')}</small>` : `<p class="muted nav-po-none">${t('none')}</p>`;
    const html = `<h3>${t('t')}</h3>${head}
      <details class="nav-po-rules"><summary>${t('rules')}<small>${esc2(poSum(r))}</small></summary><div class="fgrid">${fld('payout_win_days', t('f_days'), '5')}${fld('payout_win_min_c', t('f_wmin'), '150')}${fld('payout_min_c', t('f_min'), '500')}${fld('payout_max_c', t('f_max'))}${fld('payout_max_pct', t('f_pct'), '50')}${fld('payout_min_bal_c', t('f_bal'))}</div><small class="muted">${t('hint')}</small></details>`;
    let box = main.querySelector('.nav-po');
    if (!box) {
      const recal = main.querySelector('.nav-recal');
      box = document.createElement('section'); box.className = 'surface nav-po'; box.setAttribute('data-noi18n', ''); box.dataset.acc = id;
      if (recal) recal.before(box); else { const h = [...main.querySelectorAll('.sec-h h2')].find((e) => /^(Status|Statut|Estado)$/i.test(e.textContent.trim())); const sec = h && h.closest('section, .sec, div'); if (!sec) return; sec.append(box); }
    }
    if (box._h !== html && !box.contains(document.activeElement)) { const open = box.querySelector('.nav-po-rules') && box.querySelector('.nav-po-rules').open; box.innerHTML = html; box._h = html; if (open) box.querySelector('.nav-po-rules').open = true; }
  }
  document.addEventListener('change', (e) => {
    const i = e.target.closest && e.target.closest('[data-po]'); if (!i) return;
    const box = i.closest('.nav-po'), id = box && box.dataset.acc; if (!id) return;
    const k = i.dataset.po, raw = String(i.value).replace(/[\s$]/g, '').replace(',', '.'), n = raw === '' ? null : +raw;
    editDoc('accounts', id, (d) => { d.rules = d.rules || {}; if (n == null || !isFinite(n)) delete d.rules[k]; else d.rules[k] = k.endsWith('_c') ? Math.round(n * 100) : Math.round(n); if (k === 'payout_win_days' && n && d.rules.payout_win_min_c == null) d.rules.payout_win_min_c = 0; });
    setTimeout(() => { box._h = ''; try { card(); } catch (x) { /* never blocks */ } }, 60);
  });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__po) {
    const w = function () { const out = appRender.apply(this, arguments); try { card(); } catch (e) { /* never blocks */ } return out; };
    w.__po = true; window.render = w;
  }
})();

/* ───────────── evaluation passed → funded ─────────────
 * An evaluation account (phase « eval », or a profit target without phase) that reaches its objectives
 * (target, minimum days, consistency, never breached) gets a « You passed » window once:
 * « Move to funded » archives the evaluation (kept with its trades, marked passed) and creates the funded account
 * with the same firm and size and the firm's funded rules (from its preset when there is one).
 * « Not yet » asks again the next day. A button on the account page does the same at any time. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { t: 'You passed {n}!', s: 'Profit target reached{d}, without going past your drawdown.{m} Did your firm confirm the pass?', low: ' Your room went down to {v} on {w}.', wait: 'waiting for your firm', go: 'Yes, move it to funded', later: 'Not yet', note: 'The evaluation stays in your history (archived, marked passed). A new funded account starts with the same firm and size{r}.', rules: ' and its funded rules', done: 'Funded account created', btn: 'Move to funded', btnS: 'Passed the evaluation? Create the funded account.', badge: 'Objectives reached', fund: 'Funded' },
    fr: { t: 'Tu as réussi {n} !', s: 'Objectif de profit atteint{d}, sans dépasser ton drawdown.{m} Ta firme a confirmé la réussite\u00a0?', low: ' Ta marge est descendue à {v} le {w}.', wait: 'en attente de ta firme', go: 'Oui, passer en financé', later: 'Pas encore', note: 'L’évaluation reste dans ton historique (archivée, marquée réussie). Un nouveau compte financé démarre avec la même firme et la même taille{r}.', rules: ' et ses règles de compte financé', done: 'Compte financé créé', btn: 'Passer en financé', btnS: 'Évaluation réussie ? Crée le compte financé.', badge: 'Objectifs atteints', fund: 'Financé' },
    es: { t: '¡Aprobaste {n}!', s: 'Objetivo de beneficio alcanzado{d}, sin superar tu drawdown.{m} ¿Tu firma confirmó la aprobación?', low: ' Tu margen bajó a {v} el {w}.', wait: 'esperando a tu firma', go: 'Sí, pasar a financiada', later: 'Todavía no', note: 'La evaluación queda en tu historial (archivada, marcada aprobada). Una nueva cuenta financiada empieza con la misma firma y tamaño{r}.', rules: ' y sus reglas de cuenta financiada', done: 'Cuenta financiada creada', btn: 'Pasar a financiada', btnS: '¿Evaluación aprobada? Crea la cuenta financiada.', badge: 'Objetivos alcanzados', fund: 'Financiada' } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const isEval = (a) => a && a.status !== 'archived' && a.status !== 'closed' && !a.demo && (a.phase === 'eval' || (!a.phase && a.rules && a.rules.target_c > 0));
  function passed(a) {
    if (!isEval(a)) return false;
    let st; try { st = acctState(a); } catch (e) { return false; }
    return !!(st && st.passed);   // target + consistency + minimum days, all met (acctState)
  }
  function fundedRules(a, choice) {
    const pv = a.preset && String(a.preset).split('|');
    if (pv && pv.length >= 4 && window.SweepPresets) { pv[3] = 'funded'; let v = pv.join('|');
      if (choice && SweepPresets.withChoice) { const [g, id] = String(choice).split(':'); v = SweepPresets.withChoice(v, g, id); }   // Topstep: Standard / Consistency, chosen now
      const p = SweepPresets.rulesOf(v); if (p) return { rules: p.rules, preset: v, from: true, ver: SweepPresets.version && SweepPresets.version() }; }
    const r = Object.assign({}, a.rules || {}); r.target_c = null; r.min_days = null;   // no preset: same limits, no target
    return { rules: r, preset: null, from: false };
  }
  /* brief 02 part 2: the funded account is named the way its firm names it (« Topstep XFA 50K »), « #2 » kept from the evaluation */
  const FUNDED = [[/topstep/i, 'XFA'], [/apex/i, 'PA'], [/take ?profit|^tpt\b/i, 'PRO']];
  function fundedName(a) {
    const f = (S.firms || []).find((x) => x.id === a.firm_id), fn = (f && f.name) || '';
    const key = `${String(a.preset || '').split('|')[0]} ${fn}`.trim(), code = (FUNDED.find((x) => x[0].test(key)) || [])[1] || t('fund');
    const k = Math.round((+a.starting_balance_c || 0) / 100000), n = (/\s(#\d+)$/.exec(a.name || '') || [])[1];
    return fn ? [fn, code, k ? k + 'K' : '', n || ''].filter(Boolean).join(' ') : a.name;
  }
  function toFunded(id, choice, quiet) {
    const a = getDoc('accounts', id); if (!a) return;
    const fr = fundedRules(a, choice);
    const nid = typeof uid === 'function' ? uid() : 'a' + Date.now();
    put('accounts', { id: nid, firm_id: a.firm_id, name: fundedName(a), starting_balance_c: a.starting_balance_c, status: 'active', created_on: today(), phase: 'funded', money_type: 'funded', rules: fr.rules, preset: fr.preset, preset_ver: fr.ver || null, from_eval: a.id, ...(a.demo ? { demo: true } : {}) });
    try {   // the activation fee of the funded account, when the catalogue has one (editable in My money)
      const pr = fr.preset && window.SweepPresets && SweepPresets.priceOf ? SweepPresets.priceOf(fr.preset) : null;
      if (pr && pr.activation > 0) {
        put('expenses', { id: 'act-' + nid, account_id: nid, firm_id: a.firm_id || '', amount_c: Math.round(pr.activation * 100), date: today(), category: 'activation', notes: '' });
        if (typeof toast === 'function' && !quiet) toast(({ en: 'Activation fee added to your expenses', fr: 'Frais d’activation ajoutés à tes dépenses', es: 'Cuota de activación añadida a tus gastos' })[LANG] || 'Activation fee added to your expenses');
      }
    } catch (x) { /* the trader can add it in My money */ }
    editDoc('accounts', id, (d) => { d.status = 'archived'; d.result = 'passed'; d.passed_on = today(); d.phase = 'eval'; d.funded_id = nid; });
    if (quiet) return nid;   // several at once (Accounts): the list stays, one message for all
    if (typeof toast === 'function') toast(t('done'));
    setTimeout(() => { location.hash = '#account/' + nid; }, 300);
    return nid;
  }
  /* the window */
  function ask(a) {
    document.querySelectorAll('.nav-pass').forEach((x) => x.remove());
    let st = {}; try { st = acctState(a); } catch (e) { /* no state */ }
    const fr = fundedRules(a);
    // its own small window (not one of the app's side sheets, which the app closes on its own)
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-pass';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-pass'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
    const d = st.days ? ` · ${st.days} ${L === 'en' ? 'days' : L === 'es' ? 'días' : 'jours'}` : '';
    el.innerHTML = `<div class="nav-dlg-in"><div class="nav-pass-ic" aria-hidden="true">🏁</div><h2>${esc2(t('t').replace('{n}', a.name))}</h2>
      <p class="nav-pass-s">${t('s').replace('{d}', esc2(d)).replace('{m}', esc2(lowRoom(st)))}</p>
      <p class="muted nav-pass-n">${t('note').replace('{r}', fr.from ? t('rules') : '')}</p>
      ${choicesHtml(a) || `<button type="button" class="btn primary nav-am-save" data-pass-go="${esc2(a.id)}">${t('go')}</button>`}
      <button type="button" class="btn nav-pass-later" data-pass-later="${esc2(a.id)}">${t('later')}</button></div>`;
    document.body.append(scrim, el);
    requestAnimationFrame(() => { el.classList.add('open'); scrim.classList.add('open'); });
    scrim.addEventListener('click', () => later(a.id));
  }
  /** (1 Nov., brief dans le temps A2) the room went under half of the drawdown on the way: said, with the day (« without touching
   *  the drawdown » was said to a trader whose room had gone down to $950 of $2,000) */
  function lowRoom(st) {
    if (!st || st.lowRoom == null || !st.dd || st.lowRoom >= st.dd / 2 || !st.lowDay) return '';
    const w = new Date(st.lowDay + 'T12:00:00').toLocaleDateString(L === 'en' ? 'en-US' : L === 'fr' ? 'fr-CA' : 'es-ES', { day: 'numeric', month: 'short' });
    return t('low').replace('{v}', typeof money === 'function' ? money(Math.max(0, st.lowRoom), { sign: false, dec: 0 }) : '$' + Math.round(st.lowRoom / 100)).replace('{w}', w);
  }
  /** the firm asks for a choice when the account becomes funded (Topstep: Standard or Consistency): one button per option */
  function choicesHtml(a) {
    if (window.SweepPresets && SweepPresets.ready && !SweepPresets.ready()) SweepPresets.load();
    const g = a.preset && window.SweepPresets && SweepPresets.fundedChoices ? SweepPresets.fundedChoices(a.preset) : [];
    if (!g.length) return '';
    const o = g[0];
    return `<p class="nav-pass-q"><b>${esc2(o.label)}</b></p><div class="nav-pass-ch">${o.choices.map((c) => `<button type="button" class="btn ${c.def ? 'primary' : ''} nav-am-save" data-pass-go="${esc2(a.id)}" data-pass-choice="${esc2(o.id + ':' + c.id)}"><b>${esc2(c.label)}</b>${c.sub ? `<small>${esc2(c.sub)}</small>` : ''}</button>`).join('')}</div>`;
  }
  function closeAsk() { document.querySelectorAll('.nav-pass').forEach((x) => { x.classList.remove('open'); setTimeout(() => x.remove(), 250); }); }
  function later(id) { editDoc('accounts', id, (d) => { d.pass_asked = today(); }); closeAsk(); }
  document.addEventListener('click', (e) => {
    const g = e.target.closest && e.target.closest('[data-pass-go]'), l = e.target.closest && e.target.closest('[data-pass-later]'), b = e.target.closest && e.target.closest('[data-pass-btn]');
    if (g) { closeAsk(); toFunded(g.dataset.passGo, g.dataset.passChoice || null); }
    else if (l) later(l.dataset.passLater);
    else if (b) { const a = getDoc('accounts', b.dataset.passBtn); if (a) ask(a); }
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.querySelector('.nav-pass.open')) { e.stopPropagation(); const b = document.querySelector('[data-pass-later]'); if (b) later(b.dataset.passLater); } }, true);
  /* when to ask: an evaluation just passed, once, never on top of another window. (1 Nov., brief dans le temps C2) never between the
     day's first trade and its review (SweepQuiet: it waits for the review or the next morning); after « Not yet » never again as a
     window: the account's card says « Objectives reached · waiting for your firm » and its page keeps the button */
  let asking = false;
  function check() {
    if (asking || document.querySelector('.nav-pass, #gSheet.open, #tkSlide.open, .nav-am.open, #gOb, .evp.open, .g-sweep, .nav-inst') || (window.SweepQuiet && SweepQuiet())) return;
    const a = (S.accounts || []).find((x) => passed(x) && !x.pass_asked);
    if (!a) return;
    if (a.preset && window.SweepPresets && SweepPresets.ready && !SweepPresets.ready()) SweepPresets.load();   // its choices (Topstep Standard / Consistency) are in the catalogue
    asking = true; setTimeout(() => { asking = false; if (passed(getDoc('accounts', a.id) || a) && !document.querySelector('.nav-pass, .g-sweep, .nav-inst, #gSheet.open') && !(window.SweepQuiet && SweepQuiet())) ask(a); }, 900);
  }
  /* the account page: a clear button on a passed evaluation (and a small one on any evaluation) */
  function pageButton() {
    const m = /^#account\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), a = getDoc('accounts', id); const main = document.getElementById('main'); if (!main) return;
    let el = main.querySelector('.nav-pass-row');
    if (!isEval(a)) { if (el) el.remove(); return; }
    const ok = passed(a);
    let st = null; try { st = acctState(a); } catch (e) { st = null; }
    // « Move to funded » only once the evaluation is really passed; target reached but something missing → say what
    // (10 Nov., brief « produit final » step 4) « Move to funded » is in the page's « ⋯ » menu (its window still opens once, by itself)
    const pop = main.querySelector('details.menu > .menu-pop'); let mi = pop && pop.querySelector('.nav-pass-m');
    if (ok && pop && !mi) pop.insertAdjacentHTML('afterbegin', `<button type="button" class="nav-pass-m" data-noi18n data-pass-btn="${esc2(id)}">🏁 ${t('btn')}</button>`);
    else if (!ok && mi) mi.remove();
    const html = ok ? ''
      : st && st.reached && !st.breached && st.missing && st.missing.length ? `<div class="nav-pass-row nav-pass-miss" data-noi18n><span>${esc2(evalMissLabel(st.missing))}</span></div>` : '';
    if (!html) { if (el) el.remove(); return; }
    if (!el) { const back = main.querySelector(':scope > .row'); if (!back) return; back.insertAdjacentHTML('afterend', html); }
    else if (el.outerHTML !== html) el.outerHTML = html;
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__pass) {
    const w = function () { const out = appRender.apply(this, arguments); try { pageButton(); } catch (e) { /* never blocks */ } setTimeout(() => { try { check(); } catch (e) { /* never blocks */ } }, 50); return out; };
    w.__pass = true; window.render = w;
  }
  window.SweepPass = { passed, toFunded, ask, wait: () => t('wait'), choicesOf: (a) => (a && a.preset && window.SweepPresets && SweepPresets.fundedChoices ? SweepPresets.fundedChoices(a.preset) : []) };
})();

/* ───────────── live accounts, put forward ─────────────
 * A « LIVE » badge on live accounts (Today, account page), and on a funded account a line to move it to live
 * when the firm promotes it (Topstep Live, Lucid Live…): the funded account is archived (marked « went live »)
 * and the live account is created with the firm's live rules. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T0 = { s: 'Promoted to a live account?', sub: 'Sweep creates the live account with your firm’s live rules and archives this one, its trades and payouts kept.', b: 'Move to live', done: 'Live account created' };
  const T = { en: T0, fr: { s: 'Promu en compte live ?', sub: 'Sweep crée le compte live avec les règles live de ta firme et archive celui-ci, avec ses trades et ses payouts.', b: 'Passer en live', done: 'Compte live créé' }, es: { s: '¿Ascendido a cuenta live?', sub: 'Sweep crea la cuenta live con las reglas live de tu firma y archiva esta, con sus operaciones y pagos.', b: 'Pasar a live', done: 'Cuenta live creada' } }[L] || T0;
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const BADGE = '<span class="nav-live" aria-label="Live">LIVE</span>';
  function badges() {
    // Today's accounts card
    document.querySelectorAll('#main .nav-acc[href^="#account/"]').forEach((el) => {
      const a = getDoc('accounts', decodeURIComponent(el.getAttribute('href').slice(9))); const b = el.querySelector('.nav-acc-t b');
      if (!b) return; const has = b.querySelector('.nav-live');
      if (a && a.phase === 'live' && !has) b.insertAdjacentHTML('beforeend', BADGE); else if ((!a || a.phase !== 'live') && has) has.remove();
    });
    const m = /^#account\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), a = getDoc('accounts', id), main = document.getElementById('main'); if (!a || !main) return;
    const name = main.querySelector('.nav-accname span'); if (name && a.phase === 'live' && !name.parentElement.querySelector('.nav-live')) name.insertAdjacentHTML('afterend', BADGE);
    // a funded account: « moved to live? »
    // (10 Nov., brief « produit final » step 4) « Move to live » is in the page's « ⋯ » menu, and asked once in a window when the
    // moment comes: the funded account's first payout paid (firms promote to live after payouts)
    const show = a.phase === 'funded' && a.status !== 'archived';
    const pop = main.querySelector('details.menu > .menu-pop'); let mi = pop && pop.querySelector('.nav-live-m');
    if (!show) { if (mi) mi.remove(); return; }
    if (pop && !mi) pop.insertAdjacentHTML('afterbegin', `<button type="button" class="nav-live-m" data-noi18n data-live-go="${esc2(id)}">${T.b}</button>`);
    offer(a);
  }
  function offer(a) {
    let seen = []; try { seen = JSON.parse(localStorage.getItem('sw.liveAsk') || '[]'); } catch (e) { seen = []; }
    if (seen.includes(a.id) || a.demo || !window.SweepAsk) return;
    if (!(S.payouts || []).some((p) => p.account_id === a.id && p.status === 'paid')) return;
    if (document.querySelector('.nav-pass, .nav-ask, #gSheet.open, #tkSlide.open, .evp.open, .g-sweep, #gOb') || (window.SweepQuiet && SweepQuiet())) return;
    seen.push(a.id); try { localStorage.setItem('sw.liveAsk', JSON.stringify(seen.slice(-50))); } catch (e) { /* private mode */ }
    SweepAsk(T.s, T.sub, T.b, false).then((go) => { if (go) toLive(a.id); });
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-live-go]'); if (!b) return;
    toLive(b.dataset.liveGo);
  });
  function toLive(id, quiet) {
    const a = getDoc('accounts', id); if (!a) return;
    let rules = Object.assign({}, a.rules || {}), preset = null, start = a.starting_balance_c;
    const pv = a.preset && String(a.preset).split('|');
    if (pv && pv.length >= 4 && window.SweepPresets) { pv[3] = 'live'; const p = SweepPresets.rulesOf(pv.join('|')); if (p) { rules = p.rules; preset = pv.join('|'); if (p.start) start = Math.round(p.start * 100); } }
    else { rules.payout_max_c = null; rules.payout_ladder_c = null; }   // live: no sim payout caps
    const nid = typeof uid === 'function' ? uid() : 'a' + Date.now();
    const today = typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10);
    if (rules.dd_floor_c != null) rules.dd_c = Math.max(0, start - rules.dd_floor_c);   // live: a fixed balance floor (Topstep: $1,000)
    put('accounts', { id: nid, firm_id: a.firm_id, name: a.name, starting_balance_c: start, status: 'active', created_on: today, phase: 'live', money_type: 'live', rules, preset, from_funded: a.id, ...(a.demo ? { demo: true } : {}) });
    editDoc('accounts', a.id, (d) => { d.status = 'archived'; d.result = 'live'; d.live_on = today; d.live_id = nid; });
    if (quiet) return nid;
    if (typeof toast === 'function') toast(T.done);
    setTimeout(() => { location.hash = '#account/' + nid; }, 300);
    return nid;
  }
  window.SweepLive = { toLive };
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__live) {
    const w = function () { const out = appRender.apply(this, arguments); try { badges(); } catch (e) { /* never blocks */ } return out; };
    w.__live = true; window.render = w;
  }
})();

/* ───────────── share payouts: by period (day, week, month, lifetime), received or requested ─────────────
 * The share window had « net after fees » only. Now, from the payouts page, the trader picks what to share:
 * net after fees, or the total of the payouts of the day / week / month / since the start — received (paid)
 * or requested (every request that was not rejected). Same card design as the app's other share cards. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { what: 'Share', net: 'Net after fees', day: 'Today', week: 'This week', month: 'This month', all: 'Lifetime', paid: 'Received', req: 'Requested', label: 'Payouts', labelReq: 'Payouts requested', n: '{n} payout{s}', biggest: 'Biggest', accounts: 'Accounts', firms: 'Firms', btn: 'Share my payouts', cap: (v, p) => `${p}: ${v} in payouts 💸 Tracked with Sweep`, capReq: (v, p) => `${p}: ${v} in payouts requested. Tracked with Sweep`, none: 'No payout in this period yet.' },
    fr: { what: 'Partager', net: 'Net après frais', day: 'Aujourd’hui', week: 'Cette semaine', month: 'Ce mois-ci', all: 'Depuis le début', paid: 'Reçus', req: 'Demandés', label: 'Payouts', labelReq: 'Payouts demandés', n: '{n} payout{s}', biggest: 'Le plus gros', accounts: 'Comptes', firms: 'Firmes', btn: 'Partager mes payouts', cap: (v, p) => `${p} : ${v} en payouts 💸 Suivi avec Sweep`, capReq: (v, p) => `${p} : ${v} de payouts demandés. Suivi avec Sweep`, none: 'Aucun payout sur cette période pour l’instant.' },
    es: { what: 'Compartir', net: 'Neto tras comisiones', day: 'Hoy', week: 'Esta semana', month: 'Este mes', all: 'Desde el inicio', paid: 'Recibidos', req: 'Solicitados', label: 'Payouts', labelReq: 'Payouts solicitados', n: '{n} payout{s}', biggest: 'El mayor', accounts: 'Cuentas', firms: 'Firmas', btn: 'Compartir mis payouts', cap: (v, p) => `${p}: ${v} en payouts 💸 Registrado con Sweep`, capReq: (v, p) => `${p}: ${v} en payouts solicitados. Registrado con Sweep`, none: 'Aún no hay payouts en este periodo.' } };
  const t = (k) => (T[L] || T.en)[k];
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const st = { mode: 'paid' };
  function range(per) {
    const d = today();
    if (per === 'day') return [d, d];
    if (per === 'week') { const w = typeof weekStart === 'function' ? weekStart(d) : d; return [w, typeof addDays === 'function' ? addDays(w, 6) : d]; }
    if (per === 'month') return [d.slice(0, 8) + '01', d.slice(0, 8) + '31'];
    return ['0000-00-00', '9999-12-31'];
  }
  function list(per, mode) {
    const [a, b] = range(per);
    return (S.payouts || []).filter((p) => (mode === 'paid' ? p.status === 'paid' : p.status !== 'rejected'))
      .map((p) => ({ p, d: mode === 'paid' ? (p.payment_date || p.approval_date || p.request_date || '') : (p.request_date || p.payment_date || '') }))
      .filter((x) => x.d && x.d >= a && x.d <= b).sort((x, y) => x.d.localeCompare(y.d));
  }
  // the card data: same shape as the app's own cards
  (function wrap(n) {
    if (typeof window.shData !== 'function') { if (n < 60) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.shData.__po) return;
    const orig = window.shData;
    const w = function (kind, per) {
      if (kind !== 'payouts') return orig.apply(this, arguments);
      const a = SL(), showAmt = SH.amounts, rows = list(per, st.mode);
      const total = rows.reduce((s, x) => s + (x.p.amount_c || 0), 0), big = rows.reduce((m, x) => Math.max(m, x.p.amount_c || 0), 0);
      const accs = new Set(rows.map((x) => x.p.account_id)), firms = new Set(rows.map((x) => (acct(x.p.account_id) || {}).firm_id || x.p.firm_id).filter(Boolean));
      const plabel = t(per), cnt = t('n').replace('{n}', rows.length).replace('{s}', rows.length > 1 ? 's' : '');
      return {
        label: st.mode === 'paid' ? t('label') : t('labelReq'),
        eyebrow: [plabel, cnt].join(' · '),
        big: rows.length ? (showAmt ? moneyU(total) : '✓ ' + cnt) : '—',
        tone: 'pos',
        sub: rows.length ? null : t('none'),
        stats: [[a.payouts || t('label'), String(rows.length)], ...(showAmt && rows.length > 1 ? [[t('biggest'), moneyU(big)]] : []), ...(firms.size > 1 ? [[t('firms'), String(firms.size)]] : accs.size > 1 ? [[t('accounts'), String(accs.size)]] : [])].slice(0, 3),
        demo: rows.some((x) => x.p.demo),
        chart: null,
        bars: rows.length > 1 ? rows.slice(-12).map((x) => [x.p.amount_c || 0, false]) : null,
        mark: false,
        cap: (st.mode === 'paid' ? t('cap') : t('capReq'))(showAmt ? moneyU(total) : cnt, plabel),
      };
    };
    w.__po = true; window.shData = w;
  })(0);
  // the choice, in the share window, for payouts and net
  (function wrapR(n) {
    if (typeof window.shRender !== 'function') { if (n < 60) setTimeout(() => wrapR(n + 1), 150); return; }
    if (window.shRender.__po) return;
    const orig = window.shRender;
    const w = async function () {
      const out = await orig.apply(this, arguments);
      try {
        if (SH.kind === 'net' || SH.kind === 'payouts') {
          const head = document.querySelector('#shPanel .sh-head'); if (!head) return out;
          const cur = SH.kind === 'net' ? 'net' : SH.id;
          head.insertAdjacentHTML('afterend', `<div class="nav-shpo" data-noi18n><div class="nav-shpo-k">${['net', 'day', 'week', 'month', 'all'].map((k) => `<button type="button" class="chip ${cur === k ? 'on' : ''}" data-shpo="${k}">${t(k)}</button>`).join('')}</div>
            ${SH.kind === 'payouts' ? `<div class="seg nav-shpo-m">${['paid', 'req'].map((m) => `<button type="button" class="${(st.mode === 'paid') === (m === 'paid') ? 'on' : ''}" data-shpo-m="${m === 'paid' ? 'paid' : 'requested'}">${t(m)}</button>`).join('')}</div>` : ''}</div>`);
          const k = document.querySelector('#shPanel .nav-shpo-k'), on = k && k.querySelector('.chip.on'); if (on) k.scrollLeft = on.offsetLeft - (k.clientWidth - on.offsetWidth) / 2;   // the chosen period stays in view
        }
      } catch (e) { /* never blocks */ }
      return out;
    };
    w.__po = true; window.shRender = w;
  })(0);
  document.addEventListener('click', (e) => {
    const k = e.target.closest && e.target.closest('[data-shpo]'), m = e.target.closest && e.target.closest('[data-shpo-m]');
    if (!k && !m) return;
    if (k) { if (k.dataset.shpo === 'net') { SH.kind = 'net'; SH.id = 'all'; } else { SH.kind = 'payouts'; SH.id = k.dataset.shpo; } }
    if (m) st.mode = m.dataset.shpoM;
    SH.blob = null; shRender();
  });
  // the payouts page: the button says what it does now
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__shpo) {
    const w = function () {
      const out = appRender.apply(this, arguments);
      try { const b = document.querySelector('#main .sh-row [data-act="share"][data-k="net"]'); if (b && !b.dataset.po) { b.dataset.po = '1'; const sp = [...b.childNodes].filter((x) => x.nodeType === 3 && x.textContent.trim()).pop(); if (sp) sp.textContent = ' ' + t('btn'); else b.append(' ' + t('btn')); b.setAttribute('data-noi18n', ''); } } catch (e) { /* never blocks */ }
      return out;
    };
    w.__shpo = true; window.render = w;
  }
})();


/* manual form: the exit time sits next to the entry time (Date · Entry time · Exit time) */
(function () {
  'use strict';
  function place() {
    const tk = document.querySelector('#tkSlide.open'); if (!tk) return;
    const et = tk.querySelector('[data-tk="exitTime"]'), d = tk.querySelector('[data-tk="date"]');
    const lab = et && et.closest('label, .tk-f'), row = d && d.closest('.tk-row2');
    if (!lab || !row || lab.parentElement === row) return;
    const old = lab.parentElement; row.append(lab); row.classList.add('nav-dt');
    if (old && !old.querySelector('input, select, button')) old.hidden = true;
  }
  new window.SweepMO(() => { try { place(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();


  // what a link needs: a light preview image (JPEG, 1200 px wide) and, for the Stats page, the page gzipped
  window.SweepLinkPayload = {
    async image(blob) {
      if (!blob) return '';
      const bmp = await createImageBitmap(blob); const k = Math.min(1, 1200 / bmp.width);
      const c = document.createElement('canvas'); c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k);
      c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
      return c.toDataURL('image/jpeg', 0.86);
    },
    // the link's preview on Discord, X and iMessage (brief 02 part 12): the same card, wide (1200 × 675), whatever format is shared
    async preview() {
      if (SH.fmt === 'wide' || typeof shDraw !== 'function') return '';   // the card is already wide
      const keep = SH.fmt; SH.fmt = 'wide';
      try { const cv = await shDraw(shData(SH.kind, SH.id)); const b = await new Promise((r) => cv.toBlob(r, 'image/png')); return await this.image(b); }
      catch (e) { return ''; } finally { SH.fmt = keep; }
    },
    async gz(text) {
      if (typeof CompressionStream === 'undefined') return null;
      const st = new Blob([text]).stream().pipeThrough(new CompressionStream('gzip'));
      const buf = await new Response(st).arrayBuffer(); let bin = ''; const u = new Uint8Array(buf);
      for (let i = 0; i < u.length; i += 32768) bin += String.fromCharCode.apply(null, u.subarray(i, i + 32768));
      return btoa(bin);
    },
  };

/* ───────────── share the Stats page, as an image or as a link ─────────────
 * « Share my stats » on the Stats page opens the share window with a card of the period shown (net P&L,
 * win rate, profit factor, trades, the P&L curve). In the share window, « Create a link » publishes a snapshot
 * of the card at app.makeitsweep.com/s/… (image + numbers, nothing else of the account; amounts hidden stay hidden),
 * to paste anywhere; the link can be deleted from the same place. Works for the other cards too (payouts, week…). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { btn: 'Share my stats', label: 'My trading stats', wr: 'Win rate', pf: 'Profit factor', trades: 'Trades', avgR: 'Avg R', days: 'Green days', cap: (v, p) => `My trading stats ${p}${v ? ': ' + v : ''}. Tracked with Sweep`, link: 'Create a link', linking: 'Creating the link…', copy: 'Copy', copied: 'Link copied', del: 'Delete the link', deleted: 'Link deleted', linkHint: 'Anyone with the link sees this card only, nothing else of your account.', err: 'Could not create the link. Try again.' },
    fr: { btn: 'Partager mes stats', label: 'Mes stats de trading', wr: 'Taux de réussite', pf: 'Profit factor', trades: 'Trades', avgR: 'R moyen', days: 'Jours verts', cap: (v, p) => `Mes stats de trading ${p}${v ? ' : ' + v : ''}. Suivi avec Sweep`, link: 'Créer un lien', linking: 'Création du lien…', copy: 'Copier', copied: 'Lien copié', del: 'Supprimer le lien', deleted: 'Lien supprimé', linkHint: 'Le lien montre seulement cette carte, rien d’autre de ton compte.', err: 'Impossible de créer le lien. Réessaie.' },
    es: { btn: 'Compartir mis stats', label: 'Mis stats de trading', wr: 'Tasa de acierto', pf: 'Profit factor', trades: 'Operaciones', avgR: 'R medio', days: 'Días verdes', cap: (v, p) => `Mis stats de trading ${p}${v ? ': ' + v : ''}. Registrado con Sweep`, link: 'Crear un enlace', linking: 'Creando el enlace…', copy: 'Copiar', copied: 'Enlace copiado', del: 'Eliminar el enlace', deleted: 'Enlace eliminado', linkHint: 'El enlace muestra solo esta tarjeta, nada más de tu cuenta.', err: 'No se pudo crear el enlace. Inténtalo de nuevo.' } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  let lastLink = null;   // {id, url, kind}

  // the stats card
  (function wrap(n) {
    if (typeof window.shData !== 'function' || !window.shData.__po) { if (n < 80) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.shData.__stats) return;
    const orig = window.shData;
    const w = function (kind) {
      if (kind !== 'stats') return orig.apply(this, arguments);
      const tr = typeof ft === 'function' ? ft() : (S.trades || []);
      const list = typeof mergeCopies === 'function' && typeof sorted === 'function' ? mergeCopies(sorted(tr)) : tr;
      const st = typeof stats === 'function' ? stats(list) : {};
      const net = list.reduce((a, x) => a + (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0)), 0);
      const PL = { fr: { 'today': 'aujourd’hui', 'yesterday': 'hier', 'this week': 'cette semaine', 'last week': 'la semaine dernière', 'this month': 'ce mois-ci', 'last month': 'le mois dernier', 'this year': 'cette année', 'all time': 'depuis le début', 'last 7 days': 'les 7 derniers jours', 'last 30 days': 'les 30 derniers jours', 'last 90 days': 'les 90 derniers jours' },
        es: { 'today': 'hoy', 'yesterday': 'ayer', 'this week': 'esta semana', 'last week': 'la semana pasada', 'this month': 'este mes', 'last month': 'el mes pasado', 'this year': 'este año', 'all time': 'desde el inicio', 'last 7 days': 'los últimos 7 días', 'last 30 days': 'los últimos 30 días', 'last 90 days': 'los últimos 90 días' } };
      const raw = typeof periodLabel === 'function' ? String(periodLabel()) : '', per = ((PL[L] || {})[raw.toLowerCase()] || raw);
      // under 5 trades, no ratio that means nothing; no infinite profit factor (brief 02 part 6, like the Stats page)
      const FV = { en: 'From 5 trades', fr: 'Dès 5 trades', es: 'Desde 5 operaciones' }[L] || 'From 5 trades', NL = { en: 'No loss yet', fr: 'Pas encore de perte', es: 'Aún sin pérdidas' }[L] || 'No loss yet';
      const few = list.length < 5, amt = SH.amounts, wr = few ? FV : st.wr != null ? Math.round(st.wr * (st.wr <= 1 ? 100 : 1)) + (L === 'en' ? '%' : '\u202f%') : '—';
      const pf = few ? FV : st.pf === Infinity ? NL : st.pf ? (L === 'en' ? st.pf.toFixed(2) : st.pf.toFixed(2).replace('.', ',')) : '—';
      let c = 0; const curve = list.slice().sort((a, b) => ((a.date || '') + (a.entry_time || '')).localeCompare((b.date || '') + (b.entry_time || ''))).map((x) => (c += (typeof tNet === 'function' ? tNet(x) : 0)));
      return {
        label: t('label'), eyebrow: [per, list.length + ' trades'].filter(Boolean).join(' · '),
        big: list.length ? (amt ? money(net) : wr) : '—', tone: net >= 0 ? 'pos' : 'neg', sub: null,
        stats: [[t('wr'), wr], [t('pf'), pf], amt ? [t('trades'), String(list.length)] : [t('avgR'), !few && st.avgR != null ? (st.avgR >= 0 ? '+' : '') + st.avgR.toFixed(2) + 'R' : '—']],
        demo: list.some((x) => x.demo), chart: amt && curve.length > 1 ? curve : null, bars: null, mark: false,
        cap: t('cap')(amt ? money(net) : wr, per),
      };
    };
    w.__stats = true; w.__po = true; window.shData = w;
  })(0);

  // « Create a link » in the share window (every card)
  (function wrapR(n) {
    if (typeof window.shRender !== 'function' || !window.shRender.__po) { if (n < 80) setTimeout(() => wrapR(n + 1), 150); return; }
    if (window.shRender.__link) return;
    const orig = window.shRender;
    const w = async function () {
      const out = await orig.apply(this, arguments);
      try {
        const acts = document.querySelector('#shPanel .sh-acts'); if (!acts || document.querySelector('#shPanel .nav-shl')) return out;
        const mine = lastLink && lastLink.kind === SH.kind + '|' + SH.id ? lastLink : null;
        acts.insertAdjacentHTML('afterend', `<div class="nav-shl" data-noi18n>${mine ? linkBox(mine) : `<button type="button" class="btn nav-shl-go" data-shl="create"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>${t('link')}</button>`}<small class="muted">${t('linkHint')}</small></div>`);
      } catch (e) { /* never blocks */ }
      return out;
    };
    w.__link = true; w.__po = true; window.shRender = w;
  })(0);
  const fullUrl = (u) => location.origin + u;
  const linkBox = (l) => `<div class="nav-shl-row"><input readonly value="${esc2(fullUrl(l.url))}" aria-label="Link"><button type="button" class="btn sm primary" data-shl="copy">${t('copy')}</button></div><button type="button" class="link nav-shl-del" data-shl="delete">${t('del')}</button>`;
  async function create(btn) {
    if (!SH.blob) return;
    btn.disabled = true; btn.textContent = t('linking');
    try {
      const img = await SweepLinkPayload.image(SH.blob), preview = await SweepLinkPayload.preview();
      const card = shData(SH.kind, SH.id) || {};
      const res = await fetch('api/share/create', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ kind: SH.kind === 'payouts' ? 'payouts' : SH.kind, lang: L, image: img, preview, card: { label: card.label, eyebrow: card.eyebrow, big: String(card.big || '').replace(/<[^>]*>/g, ''), stats: card.stats, cap: card.cap } }) });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.url) throw new Error('fail');
      lastLink = { id: j.id, url: j.url, kind: SH.kind + '|' + SH.id };
      const box = btn.closest('.nav-shl'); box.innerHTML = linkBox(lastLink) + `<small class="muted">${t('linkHint')}</small>`;
      try { await navigator.clipboard.writeText(fullUrl(j.url)); if (typeof toast === 'function') toast(t('copied')); } catch (e) { /* copy by hand */ }
    } catch (e) { btn.disabled = false; btn.textContent = t('link'); if (typeof toast === 'function') toast(t('err')); }
  }
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('[data-shl]'); if (!b) return;
    const k = b.dataset.shl;
    if (k === 'create') return create(b);
    if (k === 'copy' && lastLink) {
      const u = fullUrl(lastLink.url);
      if (navigator.share && window.SW_MQ.matches) { try { await navigator.share({ url: u, title: 'Sweep' }); return; } catch (x) { /* fall back to copy */ } }
      try { await navigator.clipboard.writeText(u); if (typeof toast === 'function') toast(t('copied')); } catch (x) { const i = b.parentElement.querySelector('input'); i.select(); }
    }
    if (k === 'delete' && lastLink) {
      await fetch('api/share/delete', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ id: lastLink.id }) }).catch(() => {});
      lastLink = null; if (typeof toast === 'function') toast(t('deleted'));
      const box = b.closest('.nav-shl'); if (box) box.remove(); shRender();
    }
  });
  // a new card in the share window = a new link
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-shpo], [data-shpo-m], [data-sh-fmt]')) lastLink = null; }, true);
  document.addEventListener('change', (e) => { if (e.target.closest && e.target.closest('#shPanel [data-sh]')) lastLink = null; }, true);

  // the button on the Stats page (title row)
  function statsButton() {
    const top = document.querySelector('.main-wrap .top'); if (!top) return;
    let b = top.querySelector('.nav-shstats');
    const on = /^#analytics/.test(location.hash || '');
    if (!on) { if (b) b.remove(); return; }
    if (b) return;
    b = document.createElement('button'); b.type = 'button'; b.className = 'btn sm sh-btn nav-shstats'; b.setAttribute('data-noi18n', '');
    b.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>${t('btn')}`;
    b.addEventListener('click', () => { lastLink = null; openShare('stats', 'view'); });
    (top.querySelector('.nav-titleacts') || top).append(b);
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__shst) {
    const w = function () { const out = appRender.apply(this, arguments); try { statsButton(); } catch (e) { /* never blocks */ } return out; };
    w.__shst = true; window.render = w;
  }
  addEventListener('sw:page', () => { try { statsButton(); } catch (e) { /* never blocks */ } });   // (1 Nov.) in the page's first image: the instant pages showed it a frame early
  window.addEventListener('hashchange', () => setTimeout(() => { try { statsButton(); } catch (e) { /* never blocks */ } }, 50));
})();

/* ───────────── the trader's full name: profile, sign-up, share cards ─────────────
 * Full name asked at sign-up (step 2) and editable in Settings. Share cards show it under the big number
 * (« Show my name », on by default; asked in the share window when it is missing). Payout cards draw an
 * equity line that goes up and down and finishes up, big — « all the way up ». */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: { name: 'Full name', nameS: 'Shown on the cards you share.', save: 'Save', saved: 'Name saved', show: 'Show my name', add: 'Your name on the card', ph: 'First and last name' },
    fr: { name: 'Nom complet', nameS: 'Affiché sur les cartes que tu partages.', save: 'Enregistrer', saved: 'Nom enregistré', show: 'Afficher mon nom', add: 'Ton nom sur la carte', ph: 'Prénom et nom' },
    es: { name: 'Nombre completo', nameS: 'Aparece en las tarjetas que compartes.', save: 'Guardar', saved: 'Nombre guardado', show: 'Mostrar mi nombre', add: 'Tu nombre en la tarjeta', ph: 'Nombre y apellido' } }[L] || null;
  const t = (k) => (T || { name: 'Full name' })[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const fullName = () => (S.me && S.me.full_name) || '';
  const firstName = () => (S.me && S.me.first_name) || fullName().split(' ')[0] || '';   // the discipline cards: the first name only
  let showName = true;
  try { showName = localStorage.getItem('sw.shName') !== '0'; } catch (e) { /* private mode */ }
  async function saveName(v) {
    const r = await fetch('api/me/name', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ full_name: v }) });
    if (r.ok) { S.me = Object.assign({}, S.me || {}, { full_name: v.trim() }); if (typeof toast === 'function') toast(t('saved')); return true; }
    return false;
  }
  window.SweepName = { get: fullName, first: firstName, shown: () => showName, save: saveName };

  // an equity line, up and down, that finishes up big
  function upLine(trades, seed) {
    let c = 0; const pts = [0];
    trades.slice().sort((a, b) => ((a.date || '') + (a.entry_time || '')).localeCompare((b.date || '') + (b.entry_time || ''))).forEach((x) => { c += (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0)); pts.push(c); });
    let s = pts;
    if (s.length < 8 || Math.max(...s) <= 0) {   // not enough history: a drawn line with the same spirit
      s = []; let v = 0, r = seed || 7;
      for (let i = 0; i < 28; i++) { r = (r * 9301 + 49297) % 233280; v += (r / 233280 - 0.38) * 10; s.push(v + i * 1.6); }
    }
    if (s.length > 60) { const k = s.length / 60; s = Array.from({ length: 60 }, (_, i) => s[Math.floor(i * k)]).concat([s[s.length - 1]]); }
    const hi = Math.max(...s), lo = Math.min(...s), span = (hi - lo) || 1;
    s.push(Math.max(s[s.length - 1], hi) + span * 0.18, Math.max(s[s.length - 1], hi) + span * 0.42);   // the last leg: all the way up
    return s;
  }
  (function wrap(n) {
    if (typeof window.shData !== 'function' || !window.shData.__stats) { if (n < 100) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.shData.__name) return;
    const orig = window.shData;
    const w = function (kind, id) {
      const d = orig.apply(this, arguments); if (!d) return d;
      if (kind === 'payout' || kind === 'payouts') {
        let trades = S.trades || [];
        if (kind === 'payout') { const p = getDoc('payouts', id); if (p) { const end = p.payment_date || p.request_date || '9999'; trades = trades.filter((x) => x.account_id === p.account_id && (!x.date || x.date <= end)); } }
        else { const ids = new Set((S.payouts || []).map((p) => p.account_id)); trades = trades.filter((x) => ids.has(x.account_id)); }
        trades = typeof mergeCopies === 'function' ? mergeCopies(trades) : trades;
        d.chart = upLine(trades, (id || '').length + 7); d.bars = null; d.mark = false; d.tone = 'pos';
      }
      const nm = fullName();
      if (nm && showName) { d.who = nm; d.whoAt = ['payout', 'payouts', 'net'].includes(kind) ? 'stats' : 'eyebrow'; }   // drawn by the wrapper of shDraw below
      return d;
    };
    w.__name = true; w.__stats = true; w.__po = true; window.shData = w;
  })(0);
  // the share window: « Show my name », or the name to add when it is missing
  (function wrapR(n) {
    if (typeof window.shRender !== 'function' || !window.shRender.__link) { if (n < 100) setTimeout(() => wrapR(n + 1), 150); return; }
    if (window.shRender.__name) return;
    const orig = window.shRender;
    const w = async function () {
      const out = await orig.apply(this, arguments);
      try {
        const tg = document.querySelector('#shPanel .sh-tg'); if (!tg || tg.querySelector('[data-shname]')) return out;
        tg.insertAdjacentHTML('afterbegin', (['discipline', 'swept'].includes(SH.kind) ? firstName() : fullName())
          ? `<label data-noi18n><span>${t('show')}</span><span class="sw"><input type="checkbox" data-shname ${showName ? 'checked' : ''}><i></i></span></label>`
          : `<div class="nav-shname" data-noi18n data-shname><span>${t('add')}</span><div><input type="text" maxlength="80" placeholder="${t('ph')}" autocomplete="name"><button type="button" class="btn sm primary" data-shname-save>${t('save')}</button></div></div>`);
      } catch (e) { /* never blocks */ }
      return out;
    };
    w.__name = true; w.__link = true; w.__po = true; window.shRender = w;
  })(0);
  document.addEventListener('change', (e) => {
    const c = e.target.closest && e.target.closest('input[data-shname]'); if (!c) return;
    showName = c.checked; try { localStorage.setItem('sw.shName', showName ? '1' : '0'); } catch (x) { /* private mode */ }
    SH.blob = null; shRender();
  });
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('[data-shname-save]'); if (!b) return;
    const v = b.parentElement.querySelector('input').value.trim(); if (v.split(/\s+/).length < 2) { b.parentElement.querySelector('input').focus(); return; }
    if (await saveName(v)) { SH.blob = null; shRender(); }
  });
  // Settings: the full name, next to the email
  function settingsName() {
    if (!/^#settings/.test(location.hash || '')) return;
    return;   // replaced by the « Profile » section (first name, last name, username)
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-fullname')) return;
    const email = main.querySelector('input[type=email], [name=email]'); const host = (email && (email.closest('.surface') || email.closest('section'))) || main.querySelector('.surface'); if (!host) return;
    const box = document.createElement('div'); box.className = 'nav-fullname'; box.setAttribute('data-noi18n', '');
    box.innerHTML = `<label class="f"><span>${t('name')}</span><input type="text" maxlength="80" autocomplete="name" value="${esc2(fullName())}" placeholder="${t('ph')}"></label><button type="button" class="btn sm" data-fullname-save>${t('save')}</button><small class="muted">${t('nameS')}</small>`;
    host.prepend(box);
  }
  document.addEventListener('click', async (e) => { const b = e.target.closest && e.target.closest('[data-fullname-save]'); if (!b) return; await saveName(b.parentElement.querySelector('input').value); });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__fn) {
    const w = function () { const out = appRender.apply(this, arguments); try { settingsName(); } catch (e) { /* never blocks */ } return out; };
    w.__fn = true; window.render = w;
  }
})();

/* ───────────── the Stats link = the whole Stats page, as the trader sees it ─────────────
 * In the share window of « Share my stats », the link part offers: the period (default: the one on screen
 * when he tapped Share) and the parts of the page to include (default: all). The link shows a snapshot of
 * those parts, with his name, read-only, at app.makeitsweep.com/s/… */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { title: 'Link to my Stats page', per: 'Period', parts: 'What to show', all: 'All', go: 'Create the link of my Stats page', making: 'Preparing your page…', P: { today: 'Today', week: 'This week', month: 'This month', all: 'All time', custom: 'Custom dates' },
      S: { kpis: 'Key numbers', slip: 'Slippage and fees', perf: 'Performance', risk: 'Drawdown and durations', split: 'P&L split and trends', cal: 'Calendar', deep: 'Detailed analysis' }, err: 'Could not create the link. Try again.' },
    fr: { title: 'Lien vers ma page Stats', per: 'Période', parts: 'Ce que tu montres', all: 'Tout', go: 'Créer le lien de ma page Stats', making: 'Préparation de ta page…', P: { today: 'Aujourd’hui', week: 'Cette semaine', month: 'Ce mois-ci', all: 'Depuis le début', custom: 'Dates choisies' },
      S: { kpis: 'Chiffres clés', slip: 'Glissement et frais', perf: 'Performance', risk: 'Drawdown et durées', split: 'Répartition et tendances', cal: 'Calendrier', deep: 'Analyse détaillée' }, err: 'Impossible de créer le lien. Réessaie.' },
    es: { title: 'Enlace a mi página de Stats', per: 'Periodo', parts: 'Qué mostrar', all: 'Todo', go: 'Crear el enlace de mi página de Stats', making: 'Preparando tu página…', P: { today: 'Hoy', week: 'Esta semana', month: 'Este mes', all: 'Desde el inicio', custom: 'Fechas elegidas' },
      S: { kpis: 'Cifras clave', slip: 'Deslizamiento y comisiones', perf: 'Rendimiento', risk: 'Drawdown y duraciones', split: 'Reparto y tendencias', cal: 'Calendario', deep: 'Análisis detallado' }, err: 'No se pudo crear el enlace. Inténtalo de nuevo.' } };
  const t = (k) => (T[L] || T.en)[k];
  const PARTS = [['kpis', '.ikpis'], ['perf', '.g-top'], ['risk', '.g-ins'], ['split', '.g-two'], ['cal', 'section.ic'], ['deep', 'section.deep']];
  const st = { per: null, parts: new Set(PARTS.map((p) => p[0])), from: '', to: '' };
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  // opening the share window from Stats: the period on screen becomes the default
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('.nav-shstats')) { st.per = (typeof F !== 'undefined' && F.period) || 'month'; st.from = F.from || ''; st.to = F.to || ''; st.parts = new Set(PARTS.map((p) => p[0])); } }, true);
  function box() {
    const pers = ['today', 'week', 'month', 'all'].concat(st.per === 'custom' ? ['custom'] : []);
    return `<div class="nav-stl" data-noi18n><b>${t('title')}</b>
      <span class="nav-stl-k">${t('per')}</span><div class="nav-stl-c">${pers.map((k) => `<button type="button" class="chip ${st.per === k ? 'on' : ''}" data-stl-per="${k}">${t('P')[k]}</button>`).join('')}</div>
      <span class="nav-stl-k">${t('parts')}</span><div class="nav-stl-c"><button type="button" class="chip ${st.parts.size === PARTS.length ? 'on' : ''}" data-stl-all>${t('all')}</button>${PARTS.map(([k]) => `<button type="button" class="chip ${st.parts.has(k) ? 'on' : ''}" data-stl-part="${k}">${t('S')[k]}</button>`).join('')}</div>
      <button type="button" class="btn primary nav-stl-go" data-stl-go>${t('go')}</button></div>`;
  }
  (function wrapR(n) {
    if (typeof window.shRender !== 'function' || !window.shRender.__name) { if (n < 120) setTimeout(() => wrapR(n + 1), 150); return; }
    if (window.shRender.__stl) return;
    const orig = window.shRender;
    const w = async function () {
      const out = await orig.apply(this, arguments);
      try {
        if (SH.kind !== 'stats') return out;
        const l = document.querySelector('#shPanel .nav-shl'); if (!l || l.querySelector('input')) return out;   // a link already made stays shown
        const go = l.querySelector('[data-shl=create]'); if (go) go.remove();
        if (!st.per) st.per = (typeof F !== 'undefined' && F.period) || 'month';
        l.insertAdjacentHTML('afterbegin', box());
        const hint = l.querySelector('small'); if (hint) hint.textContent = ({ en: 'The link shows your Stats page, read-only, with what you picked. Nothing else of your account.', fr: 'Le lien montre ta page Stats en lecture seule, avec ce que tu as choisi. Rien d’autre de ton compte.', es: 'El enlace muestra tu página de Stats en solo lectura, con lo que elegiste. Nada más de tu cuenta.' })[L] || '';
      } catch (e) { /* never blocks */ }
      return out;
    };
    w.__stl = true; w.__name = true; w.__link = true; w.__po = true; window.shRender = w;
  })(0);
  const redraw = () => { const b = document.querySelector('#shPanel .nav-stl'); if (b) b.outerHTML = box(); };
  async function snapshot() {
    const prev = { p: F.period, f: F.from, t: F.to }, changed = st.per !== F.period;
    if (changed) { F.period = st.per; if (st.per === 'custom') { F.from = st.from; F.to = st.to; } render(); await new Promise((r) => setTimeout(r, 1200)); }
    const main = document.getElementById('main'), root = main && main.lastElementChild;
    let html = '', per = '';
    try {
      per = typeof periodLabel === 'function' ? String(periodLabel()) : '';
      const c = root.cloneNode(true);
      PARTS.forEach(([k, sel]) => { if (!st.parts.has(k)) c.querySelectorAll(sel).forEach((x) => x.remove()); });
      c.querySelectorAll('script, iframe, input, select, textarea, .nav-shstats, .filter-bar, .fbars, [data-act=filters]').forEach((x) => x.remove());
      c.querySelectorAll('canvas').forEach((cv, i) => { const o = root.querySelectorAll('canvas')[i]; const im = document.createElement('img'); try { im.src = o.toDataURL('image/png'); } catch (e) { /* tainted */ } im.style.width = '100%'; cv.replaceWith(im); });
      c.querySelectorAll('*').forEach((x) => { [...x.attributes].forEach((a) => { if (/^on/i.test(a.name) || (a.name === 'href' && !/^#/.test(a.value))) x.removeAttribute(a.name); }); });
      html = c.outerHTML;
    } finally {
      if (changed) { F.period = prev.p; F.from = prev.f; F.to = prev.t; render(); }
    }
    return { html, per };
  }
  async function create(btn) {
    btn.disabled = true; btn.textContent = t('making');
    try {
      const snap = await snapshot();
      const img = await SweepLinkPayload.image(SH.blob);
      const gz = await SweepLinkPayload.gz(snap.html.replace(/>\s+</g, '><'));
      const card = shData('stats', 'view') || {};
      const name = (window.SweepName && SweepName.get()) || '';
      const res = await fetch('api/share/create', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' },
        body: JSON.stringify({ kind: 'stats_page', lang: L, image: img, html: gz ? '' : snap.html, html_gz: gz || '', period: t('P')[st.per] || snap.per, name, card: { label: card.label, eyebrow: card.eyebrow, big: String(card.big || ''), stats: card.stats, cap: card.cap } }) });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.url) throw new Error(j.error || ('HTTP ' + res.status));
      const u = location.origin + j.url;
      const l = btn.closest('.nav-shl');
      l.innerHTML = `<div class="nav-shl-row"><input readonly value="${esc2(u)}" aria-label="Link"><button type="button" class="btn sm primary" data-stl-copy>${({ en: 'Copy', fr: 'Copier', es: 'Copiar' })[L] || 'Copy'}</button></div><div class="nav-stl-acts"><a class="link" href="${esc2(u)}" target="_blank" rel="noopener">${({ en: 'Open the page ›', fr: 'Ouvrir la page ›', es: 'Abrir la página ›' })[L] || 'Open ›'}</a><button type="button" class="link nav-shl-del" data-stl-del>${({ en: 'Delete the link', fr: 'Supprimer le lien', es: 'Eliminar el enlace' })[L]}</button></div>`;
      l.dataset.id = j.id;
      try { await navigator.clipboard.writeText(u); if (typeof toast === 'function') toast(({ en: 'Link copied', fr: 'Lien copié', es: 'Enlace copiado' })[L]); } catch (x) { /* copy by hand */ }
    } catch (e) { btn.disabled = false; btn.textContent = t('go'); if (typeof toast === 'function') toast(t('err') + (e && e.message && e.message !== 'fail' ? ' (' + e.message + ')' : '')); }
  }
  document.addEventListener('click', async (e) => {
    const p = e.target.closest && e.target.closest('[data-stl-per]'), pt = e.target.closest && e.target.closest('[data-stl-part]'), al = e.target.closest && e.target.closest('[data-stl-all]'), g = e.target.closest && e.target.closest('[data-stl-go]'), cp = e.target.closest && e.target.closest('[data-stl-copy]');
    if (p) { st.per = p.dataset.stlPer; redraw(); }
    else if (pt) { const k = pt.dataset.stlPart; if (st.parts.has(k) && st.parts.size > 1) st.parts.delete(k); else st.parts.add(k); redraw(); }
    else if (al) { st.parts = new Set(PARTS.map((x) => x[0])); redraw(); }
    else if (g) create(g);
    else if (e.target.closest && e.target.closest('[data-stl-del]')) {
      const l = e.target.closest('.nav-shl'); const id = l && l.dataset.id; if (!id) return;
      await fetch('api/share/delete', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ id }) }).catch(() => {});
      if (typeof toast === 'function') toast(({ en: 'Link deleted', fr: 'Lien supprimé', es: 'Enlace eliminado' })[L]);
      l.remove(); SH.blob = null; shRender();
    }
    else if (cp) { const i = cp.parentElement.querySelector('input'); if (navigator.share && window.SW_MQ.matches) { try { await navigator.share({ url: i.value, title: 'Sweep' }); return; } catch (x) { /* copy */ } } try { await navigator.clipboard.writeText(i.value); if (typeof toast === 'function') toast(({ en: 'Link copied', fr: 'Lien copié', es: 'Enlace copiado' })[L]); } catch (x) { i.select(); } }
  });
})();


/* ───────────── the profile: completed in the app before the first account, and in Settings ─────────────
 * Sign-up asks only the email and the password; the trader is in right away. The first-account page asks his first name
 * and, optional, how long he has been trading (where he found Sweep: under « More options »), saved with the account:
 * one screen (brief 03 step 1; before, a « Complete your profile » window, then the experience question on its own).
 * Settings gets a « Profile » section (first name, last name — optional — and username) and the support address. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { fn: 'First name', ln: 'Last name', un: 'Username', unH: 'The name you sign in with.', fv: 'Where did you find Sweep?', need: 'Enter your first name.', me: 'Your first name', prof: 'Profile', save: 'Save', saved: 'Profile saved', friend: 'A friend', google: 'Google', other: 'Other' },
    fr: { fn: 'Prénom', ln: 'Nom', un: 'Nom d’utilisateur', unH: 'Le nom avec lequel tu te connectes.', fv: 'Où as-tu trouvé Sweep ?', need: 'Entre ton prénom.', me: 'Ton prénom', prof: 'Profil', save: 'Enregistrer', saved: 'Profil enregistré', friend: 'Un ami', google: 'Google', other: 'Autre' },
    es: { fn: 'Nombre', ln: 'Apellido', un: 'Nombre de usuario', unH: 'El nombre con el que inicias sesión.', fv: '¿Dónde encontraste Sweep?', need: 'Escribe tu nombre.', me: 'Tu nombre', prof: 'Perfil', save: 'Guardar', saved: 'Perfil guardado', friend: 'Un amigo', google: 'Google', other: 'Otro' } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const SUPPORT = 'hello@makeitsweep.com';
  const SRC = [['tiktok', 'TikTok'], ['instagram', 'Instagram'], ['youtube', 'YouTube'], ['discord', 'Discord'], ['x', 'X'], ['friend', 'friend'], ['google', 'google'], ['other', 'other']];
  const fields = (m, wide) => `<div class="nav-prof-g ${wide ? 'wide' : ''}">
      <label class="f"><span>${t('fn')}</span><input data-pf="first_name" autocomplete="given-name" maxlength="40" value="${esc2(m.first_name || '')}"></label>
      <label class="f"><span>${t('ln')}</span><input data-pf="last_name" autocomplete="family-name" maxlength="40" value="${esc2(m.last_name || '')}"></label>
      <label class="f nav-prof-w"><span>${t('un')}</span><input data-pf="username" autocomplete="username" maxlength="32" value="${esc2(m.username || '')}"><small class="muted">${t('unH')}</small></label></div>`;
  async function save(root) {
    const b = {}; root.querySelectorAll('[data-pf]').forEach((i) => { b[i.dataset.pf] = i.value.trim(); });
    const err = root.querySelector('.nav-prof-err');
    if (!b.first_name) { if (err) err.textContent = t('need'); return false; }
    const r = await fetch('api/me/profile', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify(b) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { if (err) err.textContent = j.error || '—'; return false; }
    S.me = Object.assign({}, S.me || {}, { first_name: j.first_name, last_name: j.last_name, full_name: j.full_name, username: j.username });
    return true;
  }
  /* 1. the first-account page: the first name and the experience on top, saved with the account */
  function onbName() {
    if (!S.me || S.me.first_name) return;
    const f = document.querySelector('#main form[data-form="account"][data-onb]'); if (!f) return;
    const had = f.querySelector('.nav-onb-me'); if (had) { if (f.firstElementChild !== had) f.prepend(had); srcInOptions(f); return; }   // above the guided picker, which is put on top of the form too
    const box = document.createElement('div'); box.className = 'nav-onb-me'; box.setAttribute('data-noi18n', '');
    const X = EXP[L] || EXP.en;
    box.innerHTML = `<label class="f"><span>${t('me')}</span><input data-onb-fn autocomplete="given-name" maxlength="40" enterkeyhint="next"></label>
      <div class="nav-prof-src nav-onb-exp"><span>${X.q}</span><div class="nav-prof-chips">${[['new', X.a], ['lt1', X.b], ['gt1', X.c]].map(([v, l]) => `<button type="button" class="chip" data-exp="${v}">${l}</button>`).join('')}</div></div>
      <p class="err nav-prof-err"></p>`;
    f.prepend(box);
    srcInOptions(f);
  }
  // where he found Sweep: under the form's « More options » (brief 03 step 1), once that line exists
  function srcInOptions(f) {
    const more = f.querySelector('.nav-acc-opt'); if (!more || more.querySelector('[data-src]')) return;
    more.querySelector('summary').insertAdjacentHTML('afterend', `<div class="nav-prof-src nav-onb-src" data-noi18n><span>${t('fv')}</span><div class="nav-prof-chips">${SRC.map(([v, l]) => `<button type="button" class="chip" data-src="${v}">${T[L] && T[L][l] ? T[L][l] : l}</button>`).join('')}</div></div>`);
  }
  // the experience sets the coach's starting tone (brief 03); the source is for Sweep: both optional, one tap, tapped again = undone
  // « less than 6 months » (value « new »): the 90-day gameplan is offered right under it, started with the account (20 Oct.)
  const EXP = { en: { q: 'How long have you been trading?', a: 'Less than 6 months', b: '6 months to a year', c: 'More than a year',
      gp: 'Your 90-day gameplan is included: one mission a day to learn, with Sweep. It starts today.', gpL: 'The 90-day gameplan comes with Pro: one mission a day to learn, with Sweep.' },
    fr: { q: 'Tu trades depuis combien de temps ?', a: 'Moins de 6 mois', b: '6 mois à 1 an', c: 'Plus d’un an',
      gp: 'Ton parcours de 90 jours est inclus : une mission par jour pour apprendre, avec Sweep. Il commence aujourd’hui.', gpL: 'Le parcours de 90 jours vient avec Pro : une mission par jour pour apprendre, avec Sweep.' },
    es: { q: '¿Desde cuándo operas?', a: 'Menos de 6 meses', b: '6 meses a 1 año', c: 'Más de un año',
      gp: 'Tu recorrido de 90 días está incluido: una misión al día para aprender, con Sweep. Empieza hoy.', gpL: 'El recorrido de 90 días viene con Pro: una misión al día para aprender, con Sweep.' } };
  let GPA = null;   // can this trader have the gameplan (Pro, the trial, billing not live)? asked once, when « less than 6 months » is tapped
  async function gpOffer(f, on) {
    let box = f.querySelector('.nav-onb-gp');
    if (!on) { if (box) box.remove(); return; }
    const X = EXP[L] || EXP.en;
    if (GPA == null) { try { GPA = !!(await apiJSON('api/game/gameplan')).access; } catch (e) { GPA = false; } }
    if (!f.querySelector('[data-exp="new"].on')) return;
    if (!box) { box = document.createElement('div'); box.className = 'nav-onb-gp'; box.setAttribute('data-noi18n', ''); f.querySelector('.nav-onb-exp').after(box); }
    box.innerHTML = GPA ? `<p>✦ ${X.gp}</p>` : `<p>${X.gpL}</p>`;   // its track (sim or an evaluation) comes from the account chosen below: one question, not two
  }
  document.addEventListener('click', (e) => {
    const c = e.target.closest && e.target.closest('form[data-onb] [data-src], form[data-onb] [data-exp]'); if (!c) return;
    const k = c.dataset.src != null ? 'data-src' : 'data-exp', was = c.classList.contains('on');
    c.closest('.nav-prof-chips').querySelectorAll(`[${k}]`).forEach((x) => { x.classList.remove('on'); x.setAttribute('aria-pressed', 'false'); });
    if (!was) { c.classList.add('on'); c.setAttribute('aria-pressed', 'true'); }
    if (k === 'data-exp') gpOffer(c.closest('form'), !was && c.dataset.exp === 'new');
  });
  // « Create account » without a first name: asked there, nothing else runs; with one: saved, then the app creates the account
  document.addEventListener('submit', (e) => {
    const f = e.target; const box = f && f.matches && f.matches('form[data-form="account"]') && f.querySelector('.nav-onb-me'); if (!box) return;
    const fn = (box.querySelector('[data-onb-fn]').value || '').trim(), err = box.querySelector('.nav-prof-err');
    if (!fn) { e.preventDefault(); e.stopImmediatePropagation(); if (err) err.textContent = t('need'); const i = box.querySelector('[data-onb-fn]'); i.focus(); i.scrollIntoView({ block: 'center', behavior: 'smooth' }); return; }
    const src = (f.querySelector('[data-src].on') || {}).dataset, xp = (f.querySelector('[data-exp].on') || {}).dataset;
    const b = { first_name: fn }; if (src && src.src) b.found_via = src.src; if (xp && xp.exp) b.experience = xp.exp;
    // less than 6 months, with access: the 90-day gameplan starts today (its first mission is this very account; Sweep ticks it);
    // track A for a simulation account, B for an evaluation, a funded or a live one
    const tr = xp && xp.exp === 'new' && GPA ? { gpTrack: f.dataset.uxPhase === 'simulation' || f.dataset.acctMtype === 'simulation' ? 'A' : 'B' } : null;
    if (tr) apiJSON('api/game/gameplan/start', { method: 'POST', body: { track: tr.gpTrack } }).then((st) => { if (window.SweepGPCheck) window.SweepGPCheck(st); }).catch(() => { /* Settings can start it */ });
    // (27 Oct.) the experience at once too: the coach's tone for a trader starting out (no setup asked) from the first plan, not the next load
    S.me = Object.assign({}, S.me || {}, { first_name: fn }, b.experience ? { experience: b.experience } : {});
    fetch('api/me/profile', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify(b) })
      .then((r) => r.json()).then((j) => { if (j && j.first_name) S.me = Object.assign({}, S.me, { first_name: j.first_name, last_name: j.last_name, full_name: j.full_name }); }).catch(() => { /* kept in this view; Settings can set it again */ });
  }, true);
  /* 2. Settings: Profile first, and help & support */
  function settings() {
    if (!/^#settings/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-set-prof')) return;
    const first = main.querySelector('details.nav-sgd[data-i="0"] .surface') || main.querySelector('.surface'); if (!first) return;   // in « Account », wherever its group stands
    const sec = document.createElement('section'); sec.className = 'surface nav-set-prof'; sec.setAttribute('data-noi18n', '');
    sec.innerHTML = `<h2>${t('prof')}</h2>${fields(S.me || {}, true)}<p class="err nav-prof-err"></p><button type="button" class="btn primary" data-prof-save>${t('save')}</button>`;
    first.before(sec);
    // (10 Nov., brief « produit final » step 6) the support email, the referral and the feedback are in « About Sweep » (no Help block)
    const about = main.querySelector('section.about .surface'), legal = about && about.querySelector('.legal');
    const RF = { en: ['Referral', 'Give feedback'], fr: ['Parrainage', 'Donner mon avis'], es: ['Referidos', 'Dar mi opinión'] }[LANG] || ['Referral', 'Give feedback'];   // (31 Oct., fluidity 14) out of the profile menu
    if (legal && !about.querySelector('.nav-set-rows')) legal.insertAdjacentHTML('afterend', `<div class="nav-set-rows nav-about-rows" data-noi18n><a href="mailto:${SUPPORT}">${SUPPORT}</a><a href="#referral">${RF[0]} ›</a><a href="#feedback">${RF[1]} ›</a></div>`);
  }
  document.addEventListener('click', async (e) => { const b = e.target.closest && e.target.closest('[data-prof-save]'); if (!b) return; b.disabled = true; const ok = await save(b.closest('.nav-set-prof')); b.disabled = false; if (ok && typeof toast === 'function') toast(t('saved')); });
  // the trader has started filling in the first account: a refresh that would draw the same page (still no account, same
  // address) is skipped, otherwise it sends the guided picker back to its first question and empties the first name
  // (the app draws from its cache, then again when the server answers, which can be seconds later on a phone)
  const onbBusy = () => { const f = document.querySelector('#main form[data-form="account"][data-onb][data-touched]'); return !!f && f.dataset.touched === location.hash && !(S.accounts || []).length; };
  const touch = (e) => { const f = e.target.closest && e.target.closest('#main form[data-form="account"][data-onb]'); if (f && !f.dataset.touched) f.dataset.touched = location.hash; };
  document.addEventListener('click', touch, true); document.addEventListener('input', touch, true);
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__prof) {
    const w = function () { if (onbBusy()) return undefined; const out = appRender.apply(this, arguments); try { settings(); onbName(); } catch (e) { /* never blocks */ } return out; };
    w.__prof = true; window.render = w;
  }
  new window.SweepMO(() => { try { onbName(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();


/* the name on share cards: right-aligned on the period line (stats, week, day, trade), or just above the boxes
 * of numbers (payout, payouts, net after fees) */
(function () {
  'use strict';
  (function wrap(n) {
    if (typeof window.shDraw !== 'function') { if (n < 100) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.shDraw.__who) return;
    const orig = window.shDraw;
    const w = async function (e) {
      const cv = await orig.apply(this, arguments);
      try {
        if (!e || !e.who || !cv || !cv.getContext) return cv;
        const s = cv.getContext('2d'), t = cv.width, a = cv.height, m = SH.fmt === 'wide', v = SH.fmt === 'story', b = m ? 64 : 84;
        const font = 'Geist, -apple-system, "SF Pro Display", system-ui, sans-serif';
        s.save(); s.textBaseline = 'alphabetic';
        if (e.whoAt === 'stats' && (e.stats || []).length) {
          const me = m ? 96 : 120, pe = m ? 120 : 150, top = m ? a - me - pe - 36 : v ? a - me - pe - 120 : a - me - pe - 60;
          s.font = `600 ${m ? 30 : 36}px ${font}`; s.fillStyle = '#F2F2F3'; s.textAlign = 'left';
          s.fillText(e.who, b, top - (m ? 20 : 26));
        } else {
          const J = m ? 190 : v ? 520 : 330;
          s.font = `600 ${m ? 30 : 36}px ${font}`; s.fillStyle = '#F2F2F3'; s.textAlign = 'right';
          const eyebrowW = (() => { s.font = `500 ${m ? 30 : 36}px ${font}`; const x = s.measureText(e.eyebrow || '').width; s.font = `600 ${m ? 30 : 36}px ${font}`; return x; })();
          if (b + eyebrowW + 40 + s.measureText(e.who).width <= t - b) s.fillText(e.who, t - b, J);
          else { s.textAlign = 'left'; s.font = `600 ${m ? 26 : 30}px ${font}`; s.fillText(e.who, b, J - (m ? 40 : 48)); }   // a long period line: the name goes just above it
        }
        s.restore();
      } catch (x) { /* never blocks */ }
      return cv;
    };
    w.__who = true; window.shDraw = w;
  })(0);
})();

/* ───────────── October 7 notes ─────────────
 * 1. Stats: « Slippage and fees » hidden.
 * 2. Plan: setups optional (folded behind « + My setups »).
 * 3. Import: a visible « Import » button + a ⓘ « how to export from your platform » next to it (Trades and both
 *    « New trade » forms; not on the Calendar nor the Journal since B17: no one imports from there).
 * 4. Payout cards: « Congrats {name} ! » where the period line was, the period line above the boxes; and the boxes
 *    can show discipline (win rate, average R:R, discipline) instead of dollars — discipline by default.
 * 5. Accounts: « How many » (several identical accounts at once) and « Account cost » (added to expenses).
 * 6. Payouts and expenses: « Also for » other accounts (one payout / expense per account at once). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { opts: 'More options', setups: '+ My setups', imp: 'Import CSV', impH: 'How to export your trades from your platform', congrats: 'Congrats', show: 'Boxes', disc: 'Discipline', dol: 'Dollars', wr: 'Win rate', rr: 'Avg R:R', dsc: 'Discipline', qty: 'How many accounts', qtyH: 'Same firm, size and rules. Named #1, #2…', cost: 'Account cost ($)', costH: 'Added to your expenses.', also: 'Also for', alsoH: 'Same entry for each account you pick.', added: (n) => `${n} added` },
    fr: { opts: 'Plus d’options', setups: '+ Mes setups', imp: 'Importer un CSV', impH: 'Comment exporter tes trades de ta plateforme', congrats: 'Congrats', show: 'Cases', disc: 'Discipline', dol: 'Dollars', wr: 'Taux de réussite', rr: 'R:R moyen', dsc: 'Discipline', qty: 'Nombre de comptes', qtyH: 'Même firme, taille et règles. Nommés #1, #2…', cost: 'Coût du compte ($)', costH: 'Ajouté à tes dépenses.', also: 'Aussi pour', alsoH: 'La même entrée pour chaque compte choisi.', added: (n) => `${n} ajoutés` },
    es: { opts: 'Más opciones', setups: '+ Mis setups', imp: 'Importar CSV', impH: 'Cómo exportar tus operaciones de tu plataforma', congrats: 'Congrats', show: 'Casillas', disc: 'Disciplina', dol: 'Dólares', wr: 'Tasa de acierto', rr: 'R:R medio', dsc: 'Disciplina', qty: 'Número de cuentas', qtyH: 'Misma firma, tamaño y reglas. Nombradas #1, #2…', cost: 'Coste de la cuenta ($)', costH: 'Se añade a tus gastos.', also: 'También para', alsoH: 'La misma entrada para cada cuenta elegida.', added: (n) => `${n} añadidos` } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const nid = () => (typeof uid === 'function' ? uid() : 'x' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6));
  const ICON_IMP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5"/><path d="M5 19h14"/></svg>';
  const impHtml = (cls) => `<span class="nav-imp ${cls || ''}" data-noi18n><a class="btn sm nav-imp-b" href="#import" title="${esc2(t('impH'))}">${ICON_IMP}<span class="l">${t('imp')}</span><span class="s">CSV</span></a></span>`;   // the import page shows the instructions
  document.addEventListener('click', (e) => {
    if (e.target.closest && e.target.closest('[data-imp-help]')) { e.preventDefault(); if (window.SweepGuide) SweepGuide.open('import'); return; }
    const a = e.target.closest && e.target.closest('.nav-imp-b');
    if (a && (a.closest('#tkSlide') || a.closest('.nav-am'))) { e.preventDefault(); if (typeof closeTicket === 'function' && a.closest('#tkSlide')) closeTicket(); document.querySelectorAll('.nav-am [data-am=close]').forEach((b) => b.click()); setTimeout(() => { if (window.SweepImportSheet) SweepImportSheet.open(); else location.hash = '#import'; }, 280); }
  });

  function pass() {
    const h = location.hash || '';
    // 3. import, in the title row of the pages where trades come in, and in both forms
    const top = document.querySelector('.main-wrap .top');
    if (top) {
      const want = /^#trades/.test(h);   // B17: the CSV button only in Trades (not Calendar or Journal)
      let b = top.querySelector('.nav-imp');
      if (want && !b) { const add = top.querySelector('.nav-addtop'); if (add) add.insertAdjacentHTML('beforebegin', impHtml('top')); b = top.querySelector('.nav-imp'); }
      else if (!want && b) b.remove();
      // « Import CSV » stays the direct neighbour of « Add a trade » (placed by CSS, nothing is moved)
      const add2 = top.querySelector('.nav-addtop'); if (want && b && add2 && b.nextElementSibling !== add2) add2.before(b);
    }
    const tk = document.querySelector('#tkSlide.open .tk-head');
    /* (manual form: « Import a file » is one of the two buttons under the title) */
    /* (screenshot form: « By hand » and « Import a file » live under the drop zone only) */
    // 2. plan: setups folded
    const sh = document.getElementById('gSheet');
    if (sh) sh.querySelectorAll('.g-setups:not([data-fold])').forEach((g) => {
      g.dataset.fold = '1';
      const has = g.querySelector('.chip.on, [aria-pressed=true]');
      if (has) return;   // the trader already uses setups: leave them open
      g.hidden = true;
      const b = document.createElement('button'); b.type = 'button'; b.className = 'link nav-setups-open'; b.setAttribute('data-noi18n', ''); b.textContent = t('setups');
      b.addEventListener('click', () => { g.hidden = false; b.remove(); });
      g.before(b);
    });
    // 5. account form: how many, account cost
    const af = document.querySelector('form[data-form="account"]');
    if (af && !af.querySelector('.nav-acc-x')) {
      const sub = af.querySelector('[type="submit"]'); const host = sub && (sub.closest('.row, .acts, div') || sub);   // next to the button: visible with or without a preset
      // under « More options » (brief 03 step 1): the cost, the count and « new or already running » are inserted in it
      if (host) host.insertAdjacentHTML('beforebegin', `<details class="nav-acc-opt" data-noi18n><summary><span>${t('opts')}</span><small class="muted nav-acc-opt-s"></small></summary><div class="nav-acc-xs"><label class="f nav-acc-x" data-noi18n><span>${t('cost')}</span><input name="nav_cost" inputmode="decimal" placeholder="$"><small class="muted">${t('costH')}</small></label><label class="f nav-acc-x" data-noi18n><span>${t('qty')}</span><input name="nav_qty" type="number" min="1" max="20" value="1" inputmode="numeric"><small class="muted">${t('qtyH')}</small></label></div></details>`);
    }
    // (31 Oct., C2) one « More options » in the account step: the firm's choices open and close with it
    if (af && !af.dataset.optOne) {
      af.dataset.optOne = '1';
      af.addEventListener('toggle', (e) => { if (e.target.matches && e.target.matches('.nav-acc-opt')) af.querySelectorAll('.ux-st-more').forEach((x) => { if (x.open !== e.target.open) x.open = e.target.open; }); }, true);
    }
    // 6. payout and expense forms: also for other accounts
    document.querySelectorAll('form[data-form="payout"], form[data-form="expense"]').forEach((f) => {
      if (f.querySelector('.nav-also') || f.dataset.id) return;   // only when adding
      const sel = f.querySelector('[name="account"]'); if (!sel) return;
      const accs = (S.accounts || []).filter((a) => a.status !== 'archived');
      if (accs.length < 2) return;
      const host = sel.closest('label, .f, div');
      host.insertAdjacentHTML('afterend', `<div class="nav-also" data-noi18n><span>${t('also')}</span><div class="nav-also-c">${accs.map((a) => `<button type="button" class="chip" data-also="${esc2(a.id)}">${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</button>`).join('')}</div><small class="muted">${t('alsoH')}</small></div>`);
      const sync = () => f.querySelectorAll('[data-also]').forEach((c) => { c.hidden = c.dataset.also === sel.value; if (c.hidden) c.classList.remove('on'); });
      sel.addEventListener('change', sync); sync();
    });
  }
  document.addEventListener('click', (e) => { const c = e.target.closest && e.target.closest('[data-also]'); if (c) { c.classList.toggle('on'); } });
  new window.SweepMO(() => { try { pass(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
  addEventListener('sw:page', () => { try { pass(); } catch (e) { /* never blocks */ } });   // (1 Nov.) in the page's first image: the instant pages showed it a frame early
  window.addEventListener('hashchange', () => setTimeout(() => { try { pass(); } catch (e) { /* never blocks */ } }, 60));
  { const ar = window.render; if (typeof ar === 'function' && !ar.__imp) { const w = function () { const o = ar.apply(this, arguments); try { pass(); } catch (e) { /* never blocks */ } return o; }; w.__imp = true; window.render = w; } }

  // 5 + 6: after the app saves the form, the extra accounts / entries
  document.addEventListener('submit', (e) => {
    const f = e.target;
    if (f.matches && f.matches('form[data-form="account"]')) {
      const qty = Math.max(1, Math.min(20, parseInt((f.querySelector('[name=nav_qty]') || {}).value || '1', 10) || 1));
      const pv0 = f.dataset.uxPreset || '', pr0 = pv0 && window.SweepPresets && SweepPresets.priceOf ? SweepPresets.priceOf(pv0) : null;   // a monthly evaluation (Topstep Combine) is a subscription
      const feeOn = f.querySelector('[name=nav_fee_on]'), feeV = parseFloat(String((f.querySelector('[name=nav_fee]') || {}).value || '').replace(/[$\s]/g, '').replace(',', '.')) || 0;
      const cost = feeOn ? (feeOn.checked ? feeV : 0) : (parseFloat(String((f.querySelector('[name=nav_cost]') || {}).value || '').replace(/[$\s]/g, '').replace(',', '.')) || 0);   // the catalogue fee when shown, else the free field
      const num2 = (n) => { const v = parseFloat(String((f.querySelector(`[name=${n}]`) || {}).value || '').replace(/[$\s,]/g, '')); return isFinite(v) && v > 0 ? Math.round(v * 100) : null; };
      const running = (f.querySelector('[data-acst].on') || {}).dataset?.acst === 'run', cur = running ? num2('nav_cur') : null, peak = running ? num2('nav_peak') : null;
      if (qty === 1 && !cost && cur == null) return;
      const before = new Set((S.accounts || []).map((a) => a.id));
      setTimeout(() => {
        const first = (S.accounts || []).find((a) => !before.has(a.id)); if (!first) return;
        const made = [first];
        const gid = qty > 1 ? 'grp-' + nid() : null;
        if (gid) editDoc('accounts', first.id, (d) => { d.group_id = gid; });   // made together = traded together (copy trading)
        if (qty > 1) {
          const base = first.name.replace(/\s*#\d+$/, '');
          editDoc('accounts', first.id, (d) => { d.name = base + ' #1'; });
          for (let i = 2; i <= qty; i++) { const id = nid(); put('accounts', Object.assign(JSON.parse(JSON.stringify(first)), { id, name: base + ' #' + i, created_at: undefined, group_id: gid })); made.push({ id }); }
        }
        // an account already running: its current balance (and its highest balance, for a drawdown that trails it), as the recalibration does
        if (cur != null) {
          const yday = (() => { const d = new Date(today() + 'T12:00:00'); d.setDate(d.getDate() - 1); return d.toISOString().slice(0, 10); })();
          made.forEach((a) => editDoc('accounts', a.id, (d) => {
            const start = d.starting_balance_c || 0, adj = [];
            if (peak != null && peak > start && peak >= cur) adj.push({ id: nid(), at: yday, amount_c: peak - start, note: ({ en: 'Highest balance', fr: 'Plus haut solde', es: 'Saldo más alto' })[(typeof LANG !== 'undefined' && LANG) || 'en'] });
            const base = adj.length ? peak : start;
            if (cur !== base) adj.push({ id: nid(), at: today(), amount_c: cur - base, note: ({ en: 'Balance when added to Sweep', fr: 'Solde à l’ajout dans Sweep', es: 'Saldo al añadir a Sweep' })[(typeof LANG !== 'undefined' && LANG) || 'en'] });
            d.adjustments = (d.adjustments || []).concat(adj);
            d.hwm_c = Math.max(start, peak != null ? peak : cur);   // the highest balance already reached
          }));
        }
        if (cost > 0) made.forEach((a) => { const acc = getDoc('accounts', a.id) || first; put('expenses', { id: nid(), account_id: a.id, firm_id: acc.firm_id || '', amount_c: Math.round(cost * 100), date: today(), category: acc.phase === 'eval' ? (pr0 && pr0.eval_period === 'month' ? 'subscription' : 'evaluation') : 'activation', ...(acc.phase === 'eval' && pr0 && pr0.eval_period === 'month' ? { recurring: 'monthly' } : {}), notes: '' }); });
        if (typeof toast === 'function' && qty > 1) toast(t('added')(qty));
        if (typeof render === 'function') render();
      }, 900);
      return;
    }
    if (f.matches && f.matches('form[data-form="payout"], form[data-form="expense"]')) {
      const extra = [...f.querySelectorAll('[data-also].on')].map((c) => c.dataset.also); if (!extra.length || f.dataset.id) return;
      const kind = f.dataset.form, fd = new FormData(f), g = (k) => fd.get(k) || '';
      const amt = typeof parseMoney === 'function' ? parseMoney(g('amount')) : Math.round(parseFloat(g('amount')) * 100);
      if (!amt || amt <= 0) return;
      setTimeout(() => {
        extra.forEach((aid) => {
          const acc = getDoc('accounts', aid) || {};
          if (kind === 'payout') put('payouts', { id: nid(), account_id: aid, firm_id: acc.firm_id || '', amount_c: amt, status: g('status') || 'paid', request_date: g('request_date'), approval_date: g('approval_date'), payment_date: g('payment_date'), notes: String(g('notes')).trim() });
          else put('expenses', { id: nid(), account_id: aid, firm_id: acc.firm_id || g('firm') || '', amount_c: amt, date: g('date') || today(), category: g('category') || 'evaluation', notes: String(g('notes')).trim() });
        });
        if (typeof toast === 'function') toast(t('added')(extra.length + 1));
        if (typeof render === 'function') render();
      }, 700);
    }
  }, true);

  // 4. payout cards: Congrats + the period line above the boxes; discipline boxes (default) or dollars
  let focus = 'disc';
  try { focus = localStorage.getItem('sw.shFocus') || 'disc'; } catch (e) { /* private mode */ }
  (function wrap(n) {
    if (typeof window.shData !== 'function' || !window.shData.__name) { if (n < 120) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.shData.__congrats) return;
    const orig = window.shData;
    const w = function (kind, id) {
      const d = orig.apply(this, arguments); if (!d) return d;
      if (!['payout', 'payouts', 'net'].includes(kind)) return d;
      if (d.who) { d.whoLine = d.eyebrow; d.eyebrow = `${t('congrats')} ${d.who} !`; }
      if (focus === 'disc') {
        let tr = S.trades || [];
        if (kind === 'payout') { const p = getDoc('payouts', id); if (p) tr = tr.filter((x) => x.account_id === p.account_id && (!x.date || x.date <= (p.payment_date || p.request_date || '9999'))); }
        else { const ids = new Set((S.payouts || []).map((p) => p.account_id)); tr = tr.filter((x) => ids.has(x.account_id)); }
        tr = typeof mergeCopies === 'function' ? mergeCopies(tr) : tr;
        const st = typeof stats === 'function' ? stats(tr) : {};
        const n1 = (x) => (typeof tNet === 'function' ? tNet(x) : x.pnl_c || 0);
        const W = tr.filter((x) => n1(x) > 0), Lo = tr.filter((x) => n1(x) < 0);
        const wr = W.length + Lo.length ? Math.round(W.length / (W.length + Lo.length) * 100) + (L === 'en' ? '%' : '\u202f%') : '—';
        const aw = W.length ? W.reduce((a, x) => a + n1(x), 0) / W.length : 0, al = Lo.length ? Math.abs(Lo.reduce((a, x) => a + n1(x), 0) / Lo.length) : 0;
        const rr = aw && al ? '1 : ' + (aw / al).toFixed(1) : '—';
        const ds = typeof tDisc === 'function' ? tr.map(tDisc).filter((x) => x != null) : [];
        const disc = ds.length ? Math.round(ds.reduce((a, x) => a + x, 0) / ds.length * (ds[0] <= 1 ? 100 : 1)) + (L === 'en' ? '%' : '\u202f%') : (st.disc != null ? Math.round(st.disc) + (L === 'en' ? '%' : '\u202f%') : '—');
        d.stats = [[t('wr'), wr], [t('rr'), rr], [t('dsc'), disc]];
      }
      return d;
    };
    w.__congrats = true; w.__name = true; w.__stats = true; w.__po = true; window.shData = w;
  })(0);
  // the share window: Discipline | Dollars for payout cards
  (function wrapR(n) {
    if (typeof window.shRender !== 'function' || !window.shRender.__stl) { if (n < 120) setTimeout(() => wrapR(n + 1), 150); return; }
    if (window.shRender.__focus) return;
    const orig = window.shRender;
    const w = async function () {
      const out = await orig.apply(this, arguments);
      try {
        if (!['payout', 'payouts', 'net'].includes(SH.kind)) return out;
        const tg = document.querySelector('#shPanel .sh-tg'); if (!tg || tg.querySelector('.nav-focus')) return out;
        tg.insertAdjacentHTML('beforebegin', `<div class="nav-focus" data-noi18n><span>${t('show')}</span><div class="seg">${[['disc', t('disc')], ['dol', t('dol')]].map(([k, l]) => `<button type="button" class="${focus === k ? 'on' : ''}" data-focus="${k}">${l}</button>`).join('')}</div></div>`);
      } catch (e) { /* never blocks */ }
      return out;
    };
    w.__focus = true; w.__stl = true; w.__name = true; w.__link = true; w.__po = true; window.shRender = w;
  })(0);
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-focus]'); if (!b) return; focus = b.dataset.focus; try { localStorage.setItem('sw.shFocus', focus); } catch (x) { /* private mode */ } SH.blob = null; shRender(); });
  // the canvas: the period line (whoLine) above the boxes instead of the name
  (function wrapD(n) {
    if (typeof window.shDraw !== 'function' || !window.shDraw.__who) { if (n < 120) setTimeout(() => wrapD(n + 1), 150); return; }
    if (window.shDraw.__cg) return;
    const orig = window.shDraw;
    const w = async function (e) {
      if (e && e.whoLine) {
        const keep = e.who, eb = e.eyebrow; e.who = e.whoLine; e.eyebrow = '';
        const cv = await orig.call(this, e); e.who = keep; e.eyebrow = eb;
        try {   // « Congrats {name} ! » in white, bold, where the period line was
          const c = cv.getContext('2d'), m = SH.fmt === 'wide', v = SH.fmt === 'story', b = m ? 64 : 84, J = m ? 190 : v ? 520 : 330;
          c.save(); c.textBaseline = 'alphabetic'; c.textAlign = 'left'; c.font = `600 ${m ? 34 : 42}px Geist, -apple-system, system-ui, sans-serif`; c.fillStyle = '#F2F2F3';
          c.fillText(eb, b, J); c.restore();
        } catch (x) { /* never blocks */ }
        return cv;
      }
      return orig.apply(this, arguments);
    };
    w.__cg = true; w.__who = true; window.shDraw = w;
  })(0);
})();

/* ───────────── Journal · Week: a complete weekly view ─────────────
 * Above the weekly questions: the week's numbers (net, trades, win rate, R:R, discipline, plan days),
 * the five days side by side (P&L, trades, plan / review done, the day's lesson), best and worst trade,
 * setups and emotions of the week, and the lessons written. The questions below get the full width. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { net: 'Net P&L', trades: 'Trades', wr: 'Win rate', rr: 'Avg R:R', disc: 'Discipline', plan: 'Days with a plan', days: 'The week, day by day', none: 'No trade', planOk: 'Plan', revOk: 'Review', best: 'Best trade', worst: 'Worst trade', setups: 'Setups', emos: 'Before the trade', lessons: 'Lessons of the week', noLesson: 'Write your lessons in each day’s review: they gather here.', review: 'Your weekly review', empty: 'No trade this week yet. Your plans and reviews still count.' },
    fr: { net: 'P&L net', trades: 'Trades', wr: 'Taux de réussite', rr: 'R:R moyen', disc: 'Discipline', plan: 'Jours avec un plan', days: 'La semaine, jour par jour', none: 'Aucun trade', planOk: 'Plan', revOk: 'Revue', best: 'Meilleur trade', worst: 'Pire trade', setups: 'Setups', emos: 'Avant le trade', lessons: 'Leçons de la semaine', noLesson: 'Écris tes leçons dans la revue de chaque jour : elles se rassemblent ici.', review: 'Ta revue de la semaine', empty: 'Aucun trade cette semaine pour l’instant. Tes plans et tes revues comptent quand même.' },
    es: { net: 'P&L neto', trades: 'Operaciones', wr: 'Tasa de acierto', rr: 'R:R medio', disc: 'Disciplina', plan: 'Días con plan', days: 'La semana, día a día', none: 'Sin operaciones', planOk: 'Plan', revOk: 'Revisión', best: 'Mejor operación', worst: 'Peor operación', setups: 'Setups', emos: 'Antes de operar', lessons: 'Lecciones de la semana', noLesson: 'Escribe tus lecciones en la revisión de cada día: se reúnen aquí.', review: 'Tu revisión semanal', empty: 'Aún no hay operaciones esta semana. Tus planes y revisiones cuentan igual.' } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const n1 = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0));
  const m$ = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));
  const loc = L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA';
  function weekOf() {
    const h = (location.hash || '').replace(/^#journal\/?/, '');
    if (h === 'weekly') return weekStart(todayStr());
    if (/^w\d{4}-\d{2}-\d{2}$/.test(h)) return weekStart(h.slice(1));
    return null;
  }
  function build(ws) {
    const we = addDays(ws, 4), sun = addDays(ws, -1);
    const all = (S.trades || []).filter((x) => (typeof acctOK !== 'function' || acctOK(x)) && x.date >= sun && x.date <= addDays(ws, 6));
    const tr = typeof mergeCopies === 'function' ? mergeCopies(typeof sorted === 'function' ? sorted(all) : all) : all;
    const net = tr.reduce((a, x) => a + n1(x), 0);
    const W = tr.filter((x) => n1(x) > 0), Lo = tr.filter((x) => n1(x) < 0);
    const wr = W.length + Lo.length ? Math.round(W.length / (W.length + Lo.length) * 100) + (L === 'en' ? '%' : '\u202f%') : '—';
    const aw = W.length ? W.reduce((a, x) => a + n1(x), 0) / W.length : 0, al = Lo.length ? Math.abs(Lo.reduce((a, x) => a + n1(x), 0) / Lo.length) : 0;
    const rr = aw && al ? '1 : ' + (aw / al).toFixed(1) : W.length ? '∞' : '—';
    const ds = typeof tDisc === 'function' ? tr.map(tDisc).filter((x) => x != null) : [];
    const disc = ds.length ? Math.round(ds.reduce((a, x) => a + x, 0) / ds.length * (ds[0] <= 1 ? 100 : 1)) + (L === 'en' ? '%' : '\u202f%') : '—';
    const J = (d) => (typeof getDoc === 'function' && getDoc('journals', d)) || {};
    const days = [0, 1, 2, 3, 4].map((i) => addDays(ws, i));
    const planDays = days.filter((d) => J(d).pre && (J(d).pre.bias || J(d).pre.max_loss)).length;
    const kp = [[t('net'), m$(net), net >= 0 ? 'pos' : 'neg'], [t('trades'), String(tr.length)], [t('wr'), wr], [t('rr'), rr], [t('disc'), disc], [t('plan'), planDays + ' / 5']];
    const dayCards = days.map((d) => {
      const dt = tr.filter((x) => x.date === d || (x.date === sun && d === ws)), dn = dt.reduce((a, x) => a + n1(x), 0), j = J(d);
      const lesson = (j.post && (j.post.lesson || j.post.well)) || (dt.find((x) => x.review && x.review.lesson) || {}).review?.lesson || '';
      const lab = new Date(d + 'T12:00:00').toLocaleDateString(loc, { weekday: 'short', day: 'numeric' });
      return `<a class="nav-wk-d ${dt.length ? (dn >= 0 ? 'p' : 'n') : 'z'} ${d > todayStr() ? 'fut' : ''}" href="#journal/${d}"><small>${esc2(lab)}</small><b>${dt.length ? m$(dn) : '—'}</b><span class="muted">${dt.length ? dt.length + ' trade' + (dt.length > 1 ? 's' : '') : t('none')}</span>
        <span class="nav-wk-flags"><i class="${j.pre && (j.pre.bias || j.pre.max_loss) ? 'on' : ''}">${t('planOk')}</i><i class="${j.post && Object.values(j.post).some((v) => v) ? 'on' : ''}">${t('revOk')}</i></span>${lesson ? `<em>${esc2(String(lesson).slice(0, 90))}</em>` : ''}</a>`;
    }).join('');
    const sortedT = tr.slice().sort((a, b) => n1(b) - n1(a)), best = sortedT[0], worst = sortedT[sortedT.length - 1];
    const tline = (x) => x ? `<a class="nav-wk-t" href="#trade/${esc2(x.id)}"><b class="${n1(x) >= 0 ? 'pos' : 'neg'}">${m$(n1(x))}</b><span>${esc2(x.instrument || '')} · ${x.direction === 'short' ? 'Short' : 'Long'} · ${esc2(x.setup || '—')}</span><small class="muted">${esc2(new Date(x.date + 'T12:00:00').toLocaleDateString(loc, { weekday: 'long', day: 'numeric', month: 'short' }))} · ${esc2((x.entry_time || '').slice(0, 5))}</small></a>` : '<p class="muted">—</p>';
    const grp = (key) => { const m = new Map(); tr.forEach((x) => { const ks = key(x); (Array.isArray(ks) ? ks : [ks]).filter(Boolean).forEach((k) => { const g = m.get(k) || { n: 0, net: 0, w: 0 }; g.n++; g.net += n1(x); if (n1(x) > 0) g.w++; m.set(k, g); }); }); return [...m].sort((a, b) => b[1].n - a[1].n).slice(0, 5); };
    const bars = (rows) => rows.length ? rows.map(([k, g]) => `<div class="nav-wk-bar"><span>${esc2(k)}</span><small class="muted">${g.n} · ${Math.round(g.w / g.n * 100)} %</small><b class="${g.net >= 0 ? 'pos' : 'neg'}">${m$(g.net)}</b></div>`).join('') : '<p class="muted">—</p>';
    const lessons = days.map((d) => { const j = J(d); return j.post && (j.post.lesson || j.post.tomorrow) ? [d, j.post.lesson || j.post.tomorrow] : null; }).filter(Boolean)
      .concat(tr.filter((x) => x.review && x.review.lesson).map((x) => [x.date, x.review.lesson])).slice(0, 8);
    const uniq = [...new Map(lessons.map(([d, l]) => [String(l).trim().toLowerCase(), [d, l]])).values()];
    return `<section class="nav-wk" data-noi18n>
      <div class="nav-wk-k">${kp.map(([l, v, c]) => `<div><span>${l}</span><b class="${c || ''}">${esc2(v)}</b></div>`).join('')}</div>
      ${tr.length ? '' : `<p class="muted nav-wk-empty">${t('empty')}</p>`}
      <h3>${t('days')}</h3><div class="nav-wk-days">${dayCards}</div>
      <div class="nav-wk-g">
        <div class="surface"><h3>${t('best')}</h3>${tline(best)}<h3>${t('worst')}</h3>${tline(worst !== best ? worst : null)}</div>
        <div class="surface"><h3>${t('setups')}</h3>${bars(grp((x) => x.setup))}</div>
        <div class="surface"><h3>${t('emos')}</h3>${bars(grp((x) => ((x.emo && x.emo.before) || []).map((k) => { try { const v = window.SweepGame && SweepGame.t('emo.' + k); return v && v !== 'emo.' + k ? v : k; } catch (e) { return k; } })))}</div>
      </div>
      <div class="surface nav-wk-l"><h3>${t('lessons')}</h3>${uniq.length ? `<ul>${uniq.map(([d, l]) => `<li><small class="muted">${esc2(new Date(d + 'T12:00:00').toLocaleDateString(loc, { weekday: 'short' }))}</small> ${esc2(l)}</li>`).join('')}</ul>` : `<p class="muted">${t('noLesson')}</p>`}</div>
      <h3 class="nav-wk-rv">${t('review')}</h3></section>`;
  }
  function place() {
    const ws = weekOf(); document.body.classList.toggle('nav-wk-on', !!ws);
    if (!ws) return;
    const main = document.getElementById('main'); if (!main) return;
    const nav = [...main.children].find((e) => e.classList.contains('row') && e.querySelector('a[href^="#journal/w"]')); if (!nav) return;
    const html = build(ws), old = main.querySelector('.nav-wk');
    if (old && old.dataset.ws === ws && old._h === html) return;
    if (old) old.remove();
    nav.insertAdjacentHTML('afterend', html);
    const el = main.querySelector('.nav-wk'); el.dataset.ws = ws; el._h = html;
    // the app's own week summary (« No trades this week » or its table) is said above: hidden, the questions stay
    let nx = el.nextElementSibling; while (nx && !(nx.classList.contains('surface') && nx.classList.contains('pad'))) { if (nx.classList.contains('surface') || nx.classList.contains('empty')) nx.hidden = true; nx = nx.nextElementSibling; }
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__wk) {
    const w = function () { const out = appRender.apply(this, arguments); try { place(); } catch (e) { /* never blocks */ } return out; };
    w.__wk = true; window.render = w;
  }
  addEventListener('sw:page', () => { try { place(); } catch (e) { /* never blocks */ } });   // (1 Nov.) in the page's first image: the instant pages showed it a frame early
  window.addEventListener('hashchange', () => setTimeout(() => { try { place(); } catch (e) { /* never blocks */ } }, 80));
})();


/* ───────────── Today · « Your routine » (first section, redesigned) ─────────────
 * Traders did not understand three nested rings. The section now says it plainly: three steps of the day,
 * side by side — 1. Plan before your first trade · 2. Trade your plan · 3. Review your day — each with where it
 * stands and the one button to do it. Above them: « 2 of 3 done » and a « How it works » link; on the right:
 * streak and level. Yesterday still open shows as a clear line. The game's own block stays (hidden) and keeps
 * every action: the buttons here trigger the same ones. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { title: 'Your routine today', how: 'How it works', of: '{n} of 3 done', swept: 'Day complete', closed: 'Markets are closed today. Rest is part of the process.', dayoffT: 'Day off', dayoff: 'No trading today: your streak is safe.',
      s1: 'Plan', s1d: 'Make your plan', s2: 'Execution', s2d: 'Trade your plan', s3: 'Review', s3d: 'Do your review',
      todo: 'To do', done: 'Done', late: 'Done after your first trade', noTrade: 'No trade yet', inPlan: '{c} of {n} trades in your plan', inPlan1: '{c} of 1 trade in your plan', noPlanN: '{n} trades · no plan', noPlan1: '1 trade · no plan', reviewTodo: 'To do after your session', reviewDone: 'Done',
      b1: 'Make my plan', b1v: 'See my plan', off: 'Not trading today', b2: 'Add a trade', fin: 'I’m done for today', b3: 'Do my review', b3v: 'See my review', streak: 'day streak', streak1: 'day streak', level: 'Level', yday: 'Yesterday is not finished: {t} left', ydayB: 'Finish yesterday', ydayP: 'Yesterday: {t} left', b1s: 'Plan it', b2s: 'Add', b3s: 'Review', see: 'See',
      help: 'Each day, three steps: plan before you trade, trade what you planned, review your day. All three = « day complete »: your streak goes on. Profit never counts, only the process.' },
    fr: { title: 'Ta routine du jour', how: 'Comment ça marche', of: '{n} sur 3 faites', swept: 'Journée complète', closed: 'Les marchés sont fermés aujourd’hui. Le repos fait partie du processus.', dayoffT: 'Journée off', dayoff: 'Pas de trading aujourd’hui : ta série est protégée.',
      s1: 'Plan', s1d: 'Fais ton plan', s2: 'Exécution', s2d: 'Respecte ton plan', s3: 'Revue', s3d: 'Fais ta revue',
      todo: 'À faire', done: 'Fait', late: 'Fait après ton premier trade', noTrade: 'Aucun trade pour l’instant', inPlan: '{c} sur {n} trades dans ton plan', inPlan1: '{c} sur 1 trade dans ton plan', noPlanN: '{n} trades · pas de plan', noPlan1: '1 trade · pas de plan', reviewTodo: 'À faire après ta séance', reviewDone: 'Faite',
      b1: 'Faire mon plan', b1v: 'Voir mon plan', off: 'Pas de trading aujourd’hui', b2: 'Ajouter un trade', fin: 'J’ai fini pour aujourd’hui', b3: 'Faire ma revue', b3v: 'Voir ma revue', streak: 'jours de suite', streak1: 'jour de suite', level: 'Niveau', yday: 'Hier n’est pas terminé : encore {t}', ydayB: 'Terminer hier', ydayP: 'Hier : encore {t}', b1s: 'Planifier', b2s: 'Ajouter', b3s: 'Réviser', see: 'Voir',
      help: 'Chaque jour, trois étapes : planifie avant de trader, trade ce que tu as prévu, fais ta revue. Les trois = « journée complète » : ta série continue. Le profit ne compte jamais, seulement le processus.' },
    es: { title: 'Tu rutina de hoy', how: 'Cómo funciona', of: '{n} de 3 hechas', swept: 'Día completado', closed: 'Los mercados están cerrados hoy. El descanso es parte del proceso.', dayoffT: 'Día libre', dayoff: 'Sin operar hoy: tu racha está protegida.',
      s1: 'Plan', s1d: 'Haz tu plan', s2: 'Ejecución', s2d: 'Respeta tu plan', s3: 'Revisión', s3d: 'Haz tu revisión',
      todo: 'Pendiente', done: 'Hecho', late: 'Hecho después de tu primera operación', noTrade: 'Aún sin operaciones', inPlan: '{c} de {n} operaciones en tu plan', inPlan1: '{c} de 1 operación en tu plan', noPlanN: '{n} operaciones · sin plan', noPlan1: '1 operación · sin plan', reviewTodo: 'Pendiente tras tu sesión', reviewDone: 'Hecha',
      b1: 'Hacer mi plan', b1v: 'Ver mi plan', off: 'Hoy no opero', b2: 'Añadir una operación', fin: 'He terminado por hoy', b3: 'Hacer mi revisión', b3v: 'Ver mi revisión', streak: 'días seguidos', streak1: 'día seguido', level: 'Nivel', yday: 'Ayer no está terminado: quedan {t}', ydayB: 'Terminar ayer', ydayP: 'Ayer: quedan {t}', b1s: 'Planificar', b2s: 'Añadir', b3s: 'Revisar', see: 'Ver',
      help: 'Cada día, tres pasos: planifica antes de operar, opera lo que planeaste, revisa tu día. Los tres = « día completado »: tu racha sigue. El beneficio nunca cuenta, solo el proceso.' } };
  const t = (k, v) => String((T[L] || T.en)[k]).replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ''));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const IC = {
    plan: '<path d="M8 4h8M9 2h6v4H9z"/><rect x="5" y="4" width="14" height="17" rx="2.5"/><path d="M9 11h6M9 15h4"/>',
    trade: '<path d="M4 17l5-5 4 4 7-7"/><path d="M15 9h5v5"/>',
    review: '<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/>',
    check: '<path d="M5 12.5l4.2 4.2L19 7"/>', fire: '<path d="M12 3c1 3 4 4.5 4 8.5a4 4 0 0 1-8 0c0-2 1-3 1-3s.5 1.5 2 1.5c0-3 1-5 1-7z"/>', help: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.1-2.4 3.6M12 17h.01"/>' };
  const svg = (k) => `<svg viewBox="0 0 24 24" aria-hidden="true">${IC[k]}</svg>`;
  // the routine opens every session (the next step stands out); the trader can fold it, until the session ends (1.1)
  const rtDay = () => { const st = window.SweepGame && SweepGame.state && SweepGame.state(); return (st && st.today && st.today.day) || ''; };
  const rtClosed = () => { try { const d = localStorage.getItem('sw.rtClosedDay'); return !!d && d === rtDay(); } catch (x) { return false; } };
  const FOLD = { en: ['Fold the routine', 'Unfold the routine'], fr: ['Replier la routine', 'Déplier la routine'], es: ['Plegar la rutina', 'Desplegar la rutina'] };
  const foldBtn = () => { const c = rtClosed(), f = FOLD[L] || FOLD.en; return `<button type="button" class="nav-rt-fold" data-rt="toggle" aria-expanded="${!c}" aria-label="${c ? f[1] : f[0]}"><svg class="nav-rt-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button>`; };
  const left = (dl) => { if (!dl) return ''; const s = Math.max(0, dl - Date.now() / 1000), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60); return h ? `${h} h ${String(m).padStart(2, '0')}` : `${m} min`; };
  /** the review is offered when the session is done (brief 02 part 5): at the 17:00 ET close (the CME closes at 17:00, reopens at 18:00), or earlier once a trade is
   *  logged and the day's last announcement is past (a logged trade is a closed one: Sweep sees no open position) */
  function reviewTime(d) {
    const now = Math.floor(Date.now() / 1000), et = typeof etStr === 'function' ? etStr(now) : ''; if (!et) return true;
    const date = et.slice(0, 10), hm = et.slice(11, 16);
    if (date > d.day || (date === d.day && hm >= '17:00')) return true;
    if (date < d.day || !d.trades) return false;   // the evening before the session (from 18:00 ET), or nothing traded yet
    const ev = typeof ECON !== 'undefined' && ECON.days && ECON.days[d.day];
    return !!(ev && ev.length && now > ev[ev.length - 1].ts);
  }
  /* « Now » (SWEEP.md step 3): one line on top of the routine, the figure that counts at this moment of the New York day —
     before the first trade the risk allowed today (and the next big release with its no-trade window), during the session what
     is left, past a stop the day over; the numbers are the coach's own (SweepCoach.riskNow). Nothing once the day is reviewed. */
  const NW3 = {
    en: { now: 'Now', ruleEnd: 'Done for today: that was your rule.', closeDay: 'Close my day', risk: 'Your risk allowed today', left: 'Left today', count: 'trade {n} of {m}', end: 'Day over by your plan', plan: 'your plan’s max loss', last: 'your last plan’s max loss', dll: 'the daily limit of {a}', dd: 'your drawdown room on {a}', news: '{t} · {e}: no trade from {a} to {b}', Lplan: 'before your max loss', Llast: 'before your last plan’s max loss', Ldll: 'before the daily limit of {a}', Ldd: 'of drawdown room on {a}',
      set: 'your daily max loss', Lset: 'before your daily max loss', pl: '{p} today', cnt: '{p} today · {n}/{m} trades · {v} left', cnt1: '{p} today · {n} trade · {v} left', cntN: '{p} today · {n} trades · {v} left',
      limit: 'Your limit today', caution: 'half your last max loss', Lcaution: 'before half your last max loss', czRoom: 'Room at {m}: risk cut in half today ({r})', czLoss: 'After a day past your max loss: risk cut in half today ({r})', rule: 'Your rule today' },
    fr: { now: 'Maintenant', ruleEnd: 'Fini pour aujourd’hui, c’était ta règle.', closeDay: 'Fermer ma journée', risk: 'Ton risque permis aujourd’hui', left: 'Il te reste', count: 'trade {n} sur {m}', end: 'Journée terminée selon ton plan', plan: 'la perte max de ton plan', last: 'la perte max de ton dernier plan', dll: 'la limite du jour de {a}', dd: 'ta marge de drawdown sur {a}', news: '{t} · {e} : pas de trade de {a} à {b}', Lplan: 'avant ta perte max', Llast: 'avant la perte max de ton dernier plan', Ldll: 'avant la limite du jour de {a}', Ldd: 'de marge de drawdown sur {a}',
      set: 'ta perte max par jour', Lset: 'avant ta perte max par jour', pl: '{p} aujourd’hui', cnt: '{p} aujourd’hui · {n}/{m} trades · {v} restants', cnt1: '{p} aujourd’hui · {n} trade · {v} restants', cntN: '{p} aujourd’hui · {n} trades · {v} restants',
      limit: 'Ta limite aujourd’hui', caution: 'la moitié de ta dernière perte max', Lcaution: 'avant la moitié de ta dernière perte max', czRoom: 'Marge à {m}\u00a0: risque réduit de moitié aujourd’hui ({r})', czLoss: 'Après une journée au-delà de ta perte max\u00a0: risque réduit de moitié aujourd’hui ({r})', rule: 'Ta règle d’aujourd’hui' },
    es: { now: 'Ahora', ruleEnd: 'Terminado por hoy: era tu regla.', closeDay: 'Cerrar mi día', risk: 'Tu riesgo permitido hoy', left: 'Te quedan', count: 'operación {n} de {m}', end: 'Día terminado según tu plan', plan: 'la pérdida máx. de tu plan', last: 'la pérdida máx. de tu último plan', dll: 'el límite diario de {a}', dd: 'tu margen de drawdown en {a}', news: '{t} · {e}: sin operar de {a} a {b}', Lplan: 'antes de tu pérdida máx.', Llast: 'antes de la pérdida máx. de tu último plan', Ldll: 'antes del límite diario de {a}', Ldd: 'de margen de drawdown en {a}',
      set: 'tu pérdida máx. por día', Lset: 'antes de tu pérdida máx. por día', pl: '{p} hoy', cnt: '{p} hoy · {n}/{m} operaciones · {v} restantes', cnt1: '{p} hoy · {n} operación · {v} restantes', cntN: '{p} hoy · {n} operaciones · {v} restantes',
      limit: 'Tu límite hoy', caution: 'la mitad de tu última pérdida máx.', Lcaution: 'antes de la mitad de tu última pérdida máx.', czRoom: 'Margen en {m}: riesgo reducido a la mitad hoy ({r})', czLoss: 'Tras un día más allá de tu pérdida máx.: riesgo reducido a la mitad hoy ({r})', rule: 'Tu regla de hoy' },
  };
  const nw = (k, v) => String((NW3[L] || NW3.en)[k]).replace(/\{(\w)\}/g, (m0, x) => (v && v[x] != null ? v[x] : ''));
  const usd0 = (c) => (typeof money === 'function' ? money(Math.abs(Math.round(c)), { sign: false, dec: 0 }) : '$' + Math.round(Math.abs(c) / 100));   // as the coach writes it (no sign)
  const newsAsked = {};
  function newsLine(day) {   // the next high-impact release of the session, while its window is still ahead
    const ev = typeof ECON !== 'undefined' && ECON.days && ECON.days[day];
    if (!ev && !newsAsked[day] && typeof loadEcon === 'function') {   // (27 Oct.) not loaded yet: asked once, « Now » redrawn when they come
      newsAsked[day] = 1; Promise.resolve(loadEcon(day, day)).then(() => window.SweepNowRefresh && SweepNowRefresh()).catch(() => { /* no line */ });
    }
    if (!ev || !ev.length) return '';
    const s0 = S.settings || {}, bf = s0.pm_news_before != null && s0.pm_news_before !== '' ? +s0.pm_news_before : 5, af = s0.pm_news_after != null && s0.pm_news_after !== '' ? +s0.pm_news_after : 15;
    const now = Date.now() / 1000, e = ev.filter((x) => x.impact === 'high' && x.ts + af * 60 > now).sort((x, y) => x.ts - y.ts)[0]; if (!e) return '';
    const hm = (ts) => (typeof etStr === 'function' ? etStr(ts).slice(11, 16) : '');
    return `<p class="nav-now-news">${esc2(nw('news', { t: hm(e.ts), e: typeof tr === 'function' ? tr(e.event) : e.event, a: hm(e.ts - bf * 60), b: hm(e.ts + af * 60) }))}</p>`;
  }
  const nowPnl = (c) => `<span class="nav-now-v nav-now-p ${c > 0 ? 'pos' : c < 0 ? 'neg' : ''}">${esc2(typeof money === 'function' ? money(c || 0) : String(c))}</span>`;   // (2 Nov., C1)
  let NOWEND = false, NOWSTOP = false;   // « Now » holds the only blue button (« Close my day »); « Now » says stop
  function nowHtml(d, r) {
    NOWEND = NOWSTOP = false;
    if (!d || !d.market || d.day_off || (r && r.review >= 100) || !window.SweepCoach || !SweepCoach.riskNow) return '';
    let x = null; try { x = SweepCoach.riskNow(d.day); } catch (e) { return ''; }
    if (!x) return '';
    NOWSTOP = !!x.end;
    let big, val = '', sub = '';
    // (1 Nov., brief dans le temps A4) the drawdown room is shown as a limit, never as a « risk allowed »
    if (!x.n) { big = nw(x.k === 'dd' ? 'limit' : 'risk'); val = usd0(x.allowed); sub = nw(x.k, { a: x.a }); }
    else if (x.end && x.rule) { big = nw('ruleEnd'); sub = ''; NOWEND = true; }   // a trader starting out: his rule, and closing the day right here
    else if (x.end) { big = nw('end'); sub = x.text; }
    // (1 Nov., brief avance 4) in the session, one discreet counter « 2/3 trades · $180 left today » (was « Left today $180 · trade 3 of 3 »)
    // (2 Nov., audit « transfuge » C1) the day's P&L first, as in the header of every platform: « +$821.60 today · 2/3 trades · $1,422 left »
    else { big = esc2(nw(x.m ? 'cnt' : x.n === 1 ? 'cnt1' : 'cntN', { n: x.n, m: x.m, v: '\u0001', p: '\u0002' })).replace('\u0002', nowPnl(x.pnl)).replace('\u0001', `<span class="nav-now-v">${esc2(usd0(x.left))}</span>`); sub = [nw('L' + x.k, { a: x.a }), x.pause ? x.text : ''].filter(Boolean).join(' · '); }
    // (D1) the caution mode, the morning after a hard day: one line; (D4) the rule the trader wrote last night for this session
    const cz = !x.n && x.caution ? `<p class="nav-now-cz">${esc2(nw(x.caution.why === 'room' && x.caution.room != null ? 'czRoom' : 'czLoss', { m: usd0(x.caution.room || 0), r: usd0(x.caution.cap) }))}</p>` : '';
    const pr = (getDoc('journals', d.day) || {}).pre || {}, r0 = !x.n && x.rule0 && !pr.rule ? `<p class="nav-now-rule"><b>${esc2(nw('rule'))}</b> · ${esc2(/^\p{Lu}\p{Ll}/u.test(x.rule0) ? x.rule0.charAt(0).toLowerCase() + x.rule0.slice(1) : x.rule0)}</p>` : '';
    return `<div class="nav-now ${x.end ? 'is-end' : ''}" data-now="${!x.n ? 'before' : x.end ? 'end' : 'during'}"><small>${esc2(nw('now'))}</small><p class="nav-now-l${x.n && !x.end ? ' nav-now-cnt' : ''}"><b>${x.n && !x.end ? big : esc2(big)}</b>${val ? `<span class="nav-now-v">${esc2(val)}</span>` : ''}</p>${x.n && x.end ? `<p class="nav-now-s nav-now-pl">${esc2(nw('pl', { p: '\u0002' })).replace('\u0002', nowPnl(x.pnl))}</p>` : ''}${sub ? `<p class="nav-now-s">${esc2(sub)}</p>` : ''}${cz}${r0}${!x.n ? newsLine(d.day) : ''}${NOWEND ? `<div class="nav-now-a"><button type="button" class="btn sm primary" data-rt="fin">${esc2(nw('closeDay'))}</button></div>` : ''}${!x.n && window.SweepStart ? SweepStart.tradedLink() : ''}</div>`;
  }
  /* (27 Oct., brief activation step E) the next day's appointment: right after a first plan, on a phone, once — « Shall I remind you
     tomorrow at 8:45 for your plan? », on in one tap (Settings › Notifications' own way, SweepNotify.push.on). On an iPhone outside the
     Home Screen, the three gestures instead of a refusal. It takes the place of the « reminders » suggestion of the 2nd day. */
  const RM_T = {
    en: { q: 'Shall I remind you tomorrow at {t} for your plan?', yes: 'Yes, remind me', no: 'No thanks', on: 'Reminder on: tomorrow at {t}.', off: 'Notifications are blocked on this phone: Settings › Notifications.',
      iosQ: 'Your reminders on iPhone: add Sweep to your Home Screen.', i1: 'Tap Share in Safari', i2: '« Add to Home Screen »', i3: 'Open Sweep from its icon, then turn on the reminders', ok: 'Got it' },
    fr: { q: 'Je te rappelle demain à {t} pour ton plan ?', yes: 'Oui, rappelle-moi', no: 'Non merci', on: 'Rappel activé : demain à {t}.', off: 'Les notifications sont bloquées sur ce téléphone : Réglages › Notifications.',
      iosQ: 'Tes rappels sur iPhone : ajoute Sweep à ton écran d’accueil.', i1: 'Touche Partager dans Safari', i2: '« Sur l’écran d’accueil »', i3: 'Ouvre Sweep depuis son icône, puis active les rappels', ok: 'Compris' },
    es: { q: '¿Te recuerdo mañana a las {t} tu plan?', yes: 'Sí, recuérdamelo', no: 'No, gracias', on: 'Recordatorio activado: mañana a las {t}.', off: 'Las notificaciones están bloqueadas en este teléfono: Ajustes › Notificaciones.',
      iosQ: 'Tus recordatorios en iPhone: añade Sweep a tu pantalla de inicio.', i1: 'Toca Compartir en Safari', i2: '« Añadir a pantalla de inicio »', i3: 'Abre Sweep desde su icono y activa los recordatorios', ok: 'Entendido' } };
  const rmt = (k, v) => String((RM_T[L] || RM_T.en)[k]).replace('{t}', v || '');
  const RM = { st: null, asked: false };
  const rmDone = () => { try { return localStorage.getItem('sw.remind1') === '1'; } catch (e) { return true; } };
  const rmClose = () => { try { localStorage.setItem('sw.remind1', '1'); const g = JSON.parse(localStorage.getItem('sw.sugg') || '{}') || {}; g.push = Object.assign({}, g.push, { done: true }); localStorage.setItem('sw.sugg', JSON.stringify(g)); } catch (e) { /* private mode */ } };
  function remindRow() {
    if (rmDone() || !(matchMedia('(pointer: coarse)').matches && innerWidth < 900) || !window.SweepNotify || !SweepNotify.push) return '';
    const planned = (S.journals || []).some((j) => !j.demo && j.pre && j.pre.bias); if (!planned) return '';
    if (!RM.st) { if (!RM.asked) { RM.asked = true; SweepNotify.push.state().then((x) => { RM.st = x; if (window.SweepNowRefresh) SweepNowRefresh(); }).catch(() => { /* no row */ }); } return ''; }
    const x = RM.st; if (!x.available || x.on) return '';
    if (x.ios) return `<div class="nav-remind"><p><b>${esc2(rmt('iosQ'))}</b></p><ol><li>${esc2(rmt('i1'))}</li><li>${esc2(rmt('i2'))}</li><li>${esc2(rmt('i3'))}</li></ol><div class="nav-remind-a"><button type="button" class="btn sm" data-rt="remind-no">${esc2(rmt('ok'))}</button></div></div>`;
    if (!x.can) return '';
    return `<div class="nav-remind"><p><b>${esc2(rmt('q', x.planAt))}</b></p><div class="nav-remind-a"><button type="button" class="btn sm" data-rt="remind-yes">${esc2(rmt('yes'))}</button><button type="button" class="link" data-rt="remind-no">${esc2(rmt('no'))}</button></div></div>`;
  }
  /* (5 Nov., brief notifications) on a computer, once a trade is journaled: « Sweep on your phone » with the QR code (the phone then
     shows how to install, /?i=qr); never blue. « Later »: 7 days; « Done »: never again. Not when a phone already gets notifications. */
  const QR_T = {
    en: { t: 'Sweep on your phone', s: 'Scan this code: your alerts and reminders follow you, even when Sweep is closed.', later: 'Later', done: 'Done' },
    fr: { t: 'Sweep sur ton téléphone', s: 'Scanne ce code : tes alertes et tes rappels te suivent, même quand Sweep est fermé.', later: 'Plus tard', done: 'C’est fait' },
    es: { t: 'Sweep en tu teléfono', s: 'Escanea este código: tus alertas y recordatorios te siguen, incluso con Sweep cerrado.', later: 'Más tarde', done: 'Listo' } };
  const qrt = (k) => (QR_T[L] || QR_T.en)[k];
  const QR = { st: null, asked: false };
  function qrRow() {
    let off = false; try { off = localStorage.getItem('sw.qr1') === '1' || +(localStorage.getItem('sw.qrLater') || 0) > Date.now(); } catch (e) { off = true; }
    if (off || !matchMedia('(pointer: fine)').matches || matchMedia('(pointer: coarse)').matches || !window.SweepNotify || !SweepNotify.push) return '';
    if (!(S.trades || []).some((x) => !x.demo)) return '';
    if (!QR.st) { if (!QR.asked) { QR.asked = true; SweepNotify.push.state().then((x) => { QR.st = x; if (window.SweepNowRefresh) SweepNowRefresh(); }).catch(() => { /* no row */ }); } return ''; }
    if (!QR.st.available || QR.st.devices > 0) return '';
    return `<div class="nav-remind nav-qr"><img src="img/qr-app.svg" alt="" width="84" height="84"><div><p><b>${esc2(qrt('t'))}</b></p><p class="muted">${esc2(qrt('s'))}</p>
      <div class="nav-remind-a"><button type="button" class="btn sm" data-rt="qr-done">${esc2(qrt('done'))}</button><button type="button" class="link" data-rt="qr-later">${esc2(qrt('later'))}</button></div></div></div>`;
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-rt="qr-done"], [data-rt="qr-later"]'); if (!b) return;
    try { if (b.dataset.rt === 'qr-done') localStorage.setItem('sw.qr1', '1'); else localStorage.setItem('sw.qrLater', String(Date.now() + 7 * 864e5)); } catch (x) { /* private mode */ }
    if (window.SweepNowRefresh) SweepNowRefresh();
  });
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('[data-rt="remind-yes"], [data-rt="remind-no"]'); if (!b) return;
    rmClose();
    if (b.dataset.rt === 'remind-yes') {
      b.disabled = true;
      const r = await SweepNotify.push.on().catch(() => null);
      if (typeof toast === 'function') toast(r && r.on ? rmt('on', r.planAt) : rmt('off'));
    }
    if (window.SweepNowRefresh) SweepNowRefresh();
  });
  /* (1 Nov., brief avance 4) « Day closed »: the day's limit reached (max loss or max trades: SweepCoach.dayLock, the same as the
     server's record), the routine's steps give way to a calm screen until 18:00 ET — the time to the next session, a sentence of the
     coach that protects without guilt, two actions (grade the day's trades, close the day). Never a sheet over the app: the + and the
     trades stay where they are, entry and grading are never blocked, and nothing lifts it before 18:00. */
  const LK = {
    en: { pill: 'Day closed', loss: 'Your max loss of {m} is reached.', trades: 'Your {n} trades of the day are taken.', trades1: 'Your trade of the day is taken.', losses: '{n} losing trades in a row: your stop rule.', next: 'Next session in', at: '6:00 PM, New York time', atSun: 'Sunday, 6:00 PM, New York time', d: '{d} d {h} h',
      coL: 'Stopping here is what protects your account: the day is over, not you. Next session, cut your size after a first loss.', coT: 'Your number is reached: stopping now is keeping your word. Next session, keep your trades for your best setups.',
      grade: 'Grade my trades', close: 'Close my day', seeRv: 'See my review' },
    fr: { pill: 'Journée fermée', loss: 'Ta perte max de {m} est atteinte.', trades: 'Tes {n} trades du jour sont pris.', trades1: 'Ton trade du jour est pris.', losses: '{n} trades perdants à la suite\u00a0: ta règle d’arrêt.', next: 'Prochaine séance dans', at: '18\u00a0h, heure de New York', atSun: 'Dimanche, 18\u00a0h, heure de New York', d: '{d}\u00a0j {h}\u00a0h',
      coL: 'T’arrêter ici, c’est ce qui protège ton compte\u00a0: la journée est finie, pas toi. À la prochaine séance, réduis ta taille après une première perte.', coT: 'Ton nombre est atteint\u00a0: t’arrêter maintenant, c’est tenir parole. À la prochaine séance, garde tes trades pour tes meilleurs setups.',
      grade: 'Noter mes trades', close: 'Fermer ma journée', seeRv: 'Voir ma revue' },
    es: { pill: 'Día cerrado', loss: 'Alcanzaste tu pérdida máx. de {m}.', trades: 'Tus {n} operaciones del día están hechas.', trades1: 'Tu operación del día está hecha.', losses: '{n} operaciones perdedoras seguidas: tu regla de stop.', next: 'Próxima sesión en', at: '18:00, hora de Nueva York', atSun: 'Domingo, 18:00, hora de Nueva York', d: '{d} d {h} h',
      coL: 'Parar aquí es lo que protege tu cuenta: el día terminó, tú no. En la próxima sesión, reduce tu tamaño después de una primera pérdida.', coT: 'Llegaste a tu número: parar ahora es cumplir tu palabra. En la próxima sesión, guarda tus operaciones para tus mejores setups.',
      grade: 'Calificar mis operaciones', close: 'Cerrar mi día', seeRv: 'Ver mi revisión' } };
  const lt = (k, v) => String((LK[L] || LK.en)[k]).replace(/\{(\w)\}/g, (m0, x) => (v && v[x] != null ? v[x] : ''));
  // (lifted at 18:00 ET by the page's own clock too: the app left open past 18:00 opens the next session even before the game answers)
  const lockOf = (d) => { try { return window.SweepCoach && SweepCoach.dayLock && !(typeof todayStr === 'function' && todayStr() > d.day) ? SweepCoach.dayLock(d.day) : null; } catch (e) { return null; } };
  /** the next session opens at 18:00 ET the evening before the next weekday (Friday → Sunday 18:00) */
  function reopen(day) {
    const n = new Date(day + 'T12:00:00'); do n.setDate(n.getDate() + 1); while (n.getDay() === 0 || n.getDay() === 6);
    n.setDate(n.getDate() - 1);
    const ymd = `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}-${String(n.getDate()).padStart(2, '0')}`;
    return { ts: typeof etEpoch === 'function' ? etEpoch(ymd + ' 18:00') : 0, sun: n.getDay() === 0 };
  }
  const cdown = (ts) => { const s = Math.max(0, ts - Date.now() / 1000), dd = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60); return dd ? lt('d', { d: dd, h }) : h ? `${h}\u00a0h\u00a0${String(m).padStart(2, '0')}` : `${m}\u00a0min`; };
  /** the day's trades, a copy once, in their order (the « Trades not detailed » line is not a trade) */
  const lockTrades = (day) => { const seen = new Set(); return (S.trades || []).filter((x) => x.date === day && !x.demo && !x.untracked).sort((a, b) => String(a.entry_time || '').localeCompare(String(b.entry_time || '')) || String(a.created_at || '').localeCompare(String(b.created_at || ''))).filter((x) => { if (!x.copy_group) return true; if (seen.has(x.copy_group)) return false; seen.add(x.copy_group); return true; }); };
  /** graded = journaled, as the server counts it (GameEngine::journaled): a setup, the emotion before, the checklist answered */
  const graded = (x) => !!String(x.setup || '').trim() && !!(x.emo && x.emo.before && x.emo.before.length) && (['yes', 'partial', 'no'].includes(x.rules_followed) || Object.values(x.discipline || {}).some((v) => v === 'y' || v === 'n'));
  function lockHtml(d, r, lk) {
    const ro = reopen(d.day), rv = r && r.review >= 100;
    const what = lk.why === 'loss' ? lt('loss', { m: usd0(lk.loss_c) }) : lk.why === 'losses' ? lt('losses', { n: lk.losses || 2 }) : lt(+lk.trades === 1 ? 'trades1' : 'trades', { n: lk.trades });   // (3 Nov.) losing trades in a row: the guardian's stop rule
    return `<div class="nav-lock" data-lock="${lk.why === 'loss' || lk.why === 'losses' ? lk.why : 'trades'}"><span class="nav-lock-ic" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></span>
      <p class="nav-lock-w">${esc2(what)}</p>
      <p class="nav-lock-cd"><small>${esc2(lt('next'))}</small><b class="nav-lock-n">${esc2(cdown(ro.ts))}</b><small>${esc2(lt(ro.sun ? 'atSun' : 'at'))}</small></p>
      <p class="nav-lock-co">${esc2(lt(lk.why === 'trades' ? 'coT' : 'coL'))}</p>
      <div class="nav-lock-a"><button type="button" class="btn" data-rt="lock-grade">${esc2(lt('grade'))}</button>${rv ? `<button type="button" class="btn" data-rt="review">${esc2(lt('seeRv'))}</button>` : `<button type="button" class="btn primary" data-rt="fin">${esc2(lt('close'))}</button>`}</div></div>`;
  }
  function card() {
    const st = window.SweepGame && SweepGame.state && SweepGame.state(); let d = st && st.today;
    // (31 Oct., C4) sample data only: the routine counts the sample trades listed under it (the server never sees them)
    if (d && !d.trades && sampleOnly()) { const n = (S.trades || []).filter((x) => x.demo && x.date === d.day).length; if (n) d = Object.assign({}, d, { trades: n }); }
    // the 90-day gameplan's mission of the day (SWEEP.md step 3: its card became this line; gameplan.js draws it, the last one kept in the browser)
    const gpLine = () => (() => { try { return window.SweepGP && SweepGP.line ? SweepGP.line() : localStorage.getItem('sw.gpLine') || ''; } catch (e) { return ''; } })() || (window.SweepDisc ? SweepDisc.line() : '');   // (SWEEP.md step 5) the gameplan's mission, else the discovery mission
    // (1 Nov.) the loading card has the card's size: the mission line kept in the browser, and steps with the real texts, hidden
    // (a 70 px line and steps 28 px taller arrived with the game's answer on a slow server: the accounts card was pushed down 100 px)
    const skStep = (a, b, c, d2, x) => `<div class="nav-rt-s sk"><div class="nav-rt-si"><span class="nav-rt-n">1</span></div><div class="nav-rt-sb"><b>${t(a)}</b><small>${t(b)}</small><span class="nav-rt-st">${t(d2)}</span></div><div class="nav-rt-sa"><button type="button" class="btn sm" tabindex="-1"><span class="l">${t(c)}</span><span class="s">${t(c + 's')}</span></button>${x ? `<span class="link nav-rt-off">${t('off')}</span>` : ''}</div></div>`;
    // and the height the real card had last time at this width (kept in the browser: rows the loading card cannot know, as « Yesterday is not finished »;
    // 10 Nov.: exactly that height, the one line under the title may be « Now » instead of the mission kept in the browser)
    const rtH = (() => { try { const k = JSON.parse(localStorage.getItem('sw.rtH') || 'null'); return k && k.w === innerWidth && k.h > 0 ? k.h : 0; } catch (e) { return 0; } })();
    if (!d) return `<section class="surface nav-rt ph" data-noi18n aria-busy="true"${rtH ? ` style="height:${rtH}px;overflow:hidden"` : ''}><div class="nav-rt-h"><div><h2>${t('title')}</h2></div><div class="nav-rt-me"><span class="nav-rt-disc nav-rt-disc-ph" aria-hidden="true"></span><span class="nav-rt-sk w"></span><span class="nav-rt-sk"></span></div></div>${gpLine()}<div class="nav-rt-steps">${skStep('s1', 's1d', 'b1', 'todo', !(S.trades || []).some((x) => typeof todayStr === 'function' && x.date === todayStr()))}${skStep('s2', 's2d', 'b2', 'noTrade')}${skStep('s3', 's3d', 'b3', 'reviewTodo')}</div></section>`;
    const p = st.profile || {}, y = st.yesterday && st.yesterday.market && !st.yesterday.valid && (st.yesterday.trades > 0 || st.yesterday.plan_valid) ? st.yesterday : null;   // only a day that was started is « not finished »
    const r = d.rings || {};
    // before the first trade (27 Oct. tour): no « Discipline — », no streak « 0 », no level — they mean nothing yet; they come with it
    const first = (S.trades || []).some((x) => !x.demo) || (S.trades || []).length > 0 && !(S.accounts || []).some((a) => !a.demo);
    // (10 Nov., brief « produit final » step 1) no level any more: « Level n › » became « n swept days › » (My progress), from the first trade
    const SUM = { en: ['{n} swept day', '{n} swept days'], fr: ['{n} journée balayée', '{n} journées balayées'], es: ['{n} día barrido', '{n} días barridos'] }[L] || ['{n} swept day', '{n} swept days'];
    const swd = +p.swept_days || 0;
    const sumLine = first ? `<button type="button" class="nav-rt-sum" data-rt="hub">${SUM[swd === 1 || (swd === 0 && L === 'fr') ? 0 : 1].replace('{n}', swd)} ›</button>` : '';
    // (10 Nov.) the « ? » in the title's row when there is no line under it (an empty row before the first complete day)
    const helpB = `<button type="button" class="nav-rt-help" data-rt="help" aria-label="${t('how')}">${svg('help')}</button>`;
    const head = (extra, still) => `<div class="nav-rt-h"><div class="nav-rt-tg"><h2>${t('title')}</h2>${d.market && !still ? foldBtn() : ''}${extra || ''}${sumLine ? '' : helpB}</div></div>${sumLine ? `<div class="nav-rt-sub">${sumLine}${helpB}</div>` : ''}`;
    // the week's recap is ready (brief 01 step 5): it takes the place of the next step, with the only primary button
    const wk = st.weekly, wkReady = !!(wk && wk.open && !wk.seen);
    const wkt = ({ en: ['Your week is ready', 'Open the weekly recap'], fr: ['Ta semaine est prête', 'Ouvrir le bilan de la semaine'], es: ['Tu semana está lista', 'Abrir el resumen semanal'] })[L]   // (SWEEP.md step 6) one name: « Bilan de la semaine » || ['Your week is ready', 'See my week'];
    const wkRow = wkReady ? `<div class="nav-rt-wk"><b>${wkt[0]}</b><button type="button" class="btn primary" data-rt="week">${wkt[1]}</button></div>` : '';
    // the intention written in last week's recap, shown all this week (SWEEP.md step 1, D5: it lived only in the game's hidden card)
    const intT = ({ en: 'Your intention this week', fr: 'Ton intention cette semaine', es: 'Tu intención esta semana' })[L] || 'Your intention this week';
    const intRow = !wkReady && wk && wk.intention ? `<p class="nav-rt-int"><b>${intT}</b> · ${esc2(wk.intention)}</p>` : '';
    const nowRow = nowHtml(d, r);
    const rmRow = remindRow() || qrRow();
    const gpRow = gpLine();
    // (10 Nov., brief « produit final » step 2) « Now » first (the session's block, on every market day), then one line at most,
    // the most useful, in the brief's order: the week's recap ready, the mission of the day, then the rest (a one-time offer: the
    // reminder after a first plan, Sweep on the phone; the week's intention); « Yesterday » stays in the title; the recap and the
    // mission are never hidden by « Now », they are the loop
    const one = nowRow + (wkRow || gpRow || rmRow || intRow);
    // the « ? » of the header opens the same help on every card (market closed, day off: it threw on a missing help text, Admin › Errors, 12 Oct.)
    const helpT = `<div class="nav-rt-help-t" hidden>${t('help')}</div>`;
    if (!d.market) return `<section class="surface nav-rt closed" data-noi18n>${head()}${wkRow || gpRow || rmRow || intRow}<p class="nav-rt-msg">${t('closed')}</p>${helpT}</section>`;
    if (d.day_off) return `<section class="surface nav-rt off" data-noi18n>${head(`<span class="nav-rt-pill ok">${svg('check')}${t('dayoffT')}</span>`)}${wkRow || gpRow || intRow}<p class="nav-rt-msg">${t('dayoff')}</p>${helpT}</section>`;
    // (1 Nov., brief avance 4) the day's limit reached: « Day closed » in place of « Now » and the 3 steps, until 18:00 ET (no fold: it is the day)
    const lk = lockOf(d);
    if (lk) return `<section class="surface nav-rt nav-lockd" data-noi18n>${head(`<span class="nav-rt-pill lk">${esc2(lt('pill'))}</span>`, true)}${lockHtml(d, r, lk)}${helpT}</section>`;
    const s1 = r.plan >= 100 ? 'done' : r.plan > 0 ? 'late' : 'todo';
    const s2 = !d.trades ? 'wait' : r.execution >= 100 ? 'done' : 'part';
    const s3 = r.review >= 100 ? 'done' : 'todo';
    const n = [s1 !== 'todo', s2 === 'done', s3 === 'done'].filter(Boolean).length;
    const nextI = wkReady || NOWEND ? 0 : s1 === 'todo' ? 1 : s3 === 'done' ? 0 : reviewTime(d) ? 3 : 2;   // (« Now » with « Close my day »: the only blue button)   // only the next step is highlighted (none when the week's recap is ready)
    const pill = d.swept ? `<span class="nav-rt-pill ok">${svg('check')}${t('swept')}</span>` : `<span class="nav-rt-pill">${t('of', { n })}</span>`;
    const step = (i, key, ic, title, sub, state, stateTxt, btn, act, extra, short) => `<div class="nav-rt-s ${state}${i === nextI ? ' next' : ''}"${i === nextI ? ' aria-current="step"' : ''}>
        <div class="nav-rt-si"><span class="nav-rt-n">${state === 'done' ? svg('check') : i}</span><span class="nav-rt-ic">${svg(ic)}</span></div>
        <div class="nav-rt-sb"><b>${title}</b><small>${sub}</small><span class="nav-rt-st">${stateTxt}</span></div>
        <div class="nav-rt-sa"><button type="button" class="btn sm ${i === nextI ? 'primary' : ''}" data-rt="${act}"><span class="l">${btn}</span><span class="s">${short}</span></button>${extra || ''}</div>
        <i class="nav-rt-bar"><i style="width:${key}%"></i></i></div>`;
    const execPct = d.trades && d.plan_valid ? Math.round((d.compliant || 0) / d.trades * 100) : 0;
    // without a valid plan no trade is « in your plan » (audit of 16 Oct.; the server counts 0 too: game.php compliant_count)
    // (27 Oct., brief « daily loop » step 3) under the steps from the first trade: « I'm done for today » opens the review at once
    const execLine = !d.trades ? t('noTrade') : !d.plan_valid ? (d.trades === 1 ? t('noPlan1') : t('noPlanN', { n: d.trades })) : t(d.trades === 1 ? 'inPlan1' : 'inPlan', { c: d.compliant || 0, n: d.trades });
    // (2 Nov., analyse débutant C4) « Yesterday: 15 h 19 left › »: « Finish yesterday › 15 h 19 » read the time left as a clock time
    const ych = y ? `<button type="button" class="nav-rt-y" data-rt="yday" title="${esc2(t('yday', { t: left(y.deadline) }))}"><b>${esc2(t('ydayP', { t: left(y.deadline) }))} ›</b></button>` : '';
    return `<section class="surface nav-rt" data-noi18n>${head(pill + ych)}${one}
      <div class="nav-rt-steps" data-next="${nextI}">
        ${step(1, r.plan || 0, 'plan', t('s1'), t('s1d'), s1, s1 === 'done' ? t('done') : s1 === 'late' ? t('late') : t('todo'), s1 === 'todo' ? t('b1') : t('b1v'), 'plan', s1 === 'todo' && !d.trades ? `<button type="button" class="link nav-rt-off" data-rt="dayoff">${t('off')}</button>` : '', s1 === 'todo' ? t('b1s') : t('see'))}
        ${step(2, d.trades ? execPct : 0, 'trade', t('s2'), t('s2d'), s2, execLine, t('b2'), 'trade', '', t('b2s'))}
        ${step(3, r.review || 0, 'review', t('s3'), t('s3d'), s3, s3 === 'done' ? t('reviewDone') : t('reviewTodo'), s3 === 'done' ? t('b3v') : t('b3'), 'review', '', s3 === 'done' ? t('see') : t('b3s'))}
      </div>
      ${NOWSTOP && s3 !== 'done' ? `<p class="nav-rt-finl"><button type="button" class="link nav-rt-fin" data-rt="fin">${t('fin')} ›</button></p>` : ''}
      ${helpT}</section>`;
  }
  window.SweepNowRefresh = () => { try { place(); } catch (e) { /* never blocks */ } };
  function place() {
    if (!/^#?(dashboard)?$/.test((location.hash || '').replace(/^#/, ''))) return;
    const host = document.querySelector('#main .d-today'); if (!host) return;
    if (window.SweepAiToday) SweepAiToday(host);   // (brief avance, step 3) « Describe your trade or drop a screenshot », under the card
    const cl = rtClosed(); const cur = host.querySelector('.nav-rt'); if (cur) cur.classList.toggle('closed-rt', cl && !cur.classList.contains('nav-lockd'));   // (the closed day never folds)
    const html = card(); if (!html) return;
    let el = host.querySelector('.nav-rt');
    const ht = el && el.querySelector('.nav-rt-help-t'); const open = !!(ht && !ht.hidden);   // the loading card has no help text
    if (el && el._h === html) return;
    const co = el && el.querySelector(':scope > .co-today');   // the coach lives in the card: it moves to the new one, no flash
    if (el) el.remove();
    host.insertAdjacentHTML('afterbegin', html);
    el = host.querySelector('.nav-rt'); el._h = html; if (open && el.querySelector('.nav-rt-help-t')) el.querySelector('.nav-rt-help-t').hidden = false;
    if (co) { const st = el.querySelector(':scope > .nav-rt-steps'), hp = el.querySelector(':scope > .nav-rt-help-t'); st ? st.before(co) : hp ? hp.before(co) : el.append(co); }
    else if (window.SweepCoach && SweepCoach.paintToday) SweepCoach.paintToday();   // (1 Nov.) the coach in the same image as its card: it pushed the 3 steps down one frame later
    el.classList.toggle('closed-rt', rtClosed() && !el.classList.contains('nav-lockd'));
    document.body.classList.add('nav-rt-on');
    if (!el.classList.contains('ph')) requestAnimationFrame(() => { try { if (el.isConnected) localStorage.setItem('sw.rtH', JSON.stringify({ w: innerWidth, h: Math.round(el.getBoundingClientRect().height) })); } catch (e) { /* private mode */ } });
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-rt]'); if (!b) return;
    const k = b.dataset.rt, g = document.querySelector('#main .g-today');
    if (k === 'plan') { if (window.SweepGame && SweepGame.openPlan) { const nx = window.SweepNextSession && SweepNextSession(); nx ? SweepGame.openPlan(nx) : SweepGame.openPlan(); } }
    else if (k === 'review' || k === 'fin') { if (window.SweepGame && SweepGame.openReview) SweepGame.openReview(); }   // « I'm done for today »: the same review, at once
    else if (k === 'week') { if (window.SweepGame && SweepGame.open) SweepGame.open('weekly'); }
    else if (k === 'trade') { if (typeof openTicket === 'function') openTicket(); }
    else if (k === 'lock-grade') {   // (1 Nov., brief avance 4) the next trade of the day not graded yet, else the day's trades (Journal)
      const day = rtDay() || (typeof todayStr === 'function' ? todayStr() : ''), nx = lockTrades(day).find((x) => !graded(x));
      location.hash = nx ? '#trade/' + encodeURIComponent(nx.id) : '#journal/' + day;
    }
    else if (k === 'dayoff') { const o = g && g.querySelector('[data-g=dayoff]'); if (o) o.click(); }
    else if (k === 'yday') { const o = document.querySelector('#main [data-g=yday]'); if (o) o.click(); }
    else if (k === 'hub') {
      if (window.SweepGame) SweepGame.open('hub');
      // keyboard users: when My progress closes, the focus comes back to the button that opened it
      const back = () => { if (document.querySelector('#gSheet')) { setTimeout(back, 120); return; } const r = document.querySelector('#main .nav-rt-sum'); if (r) r.focus(); };
      setTimeout(back, 300);
    }
    else if (k === 'help') { const h = b.closest('.nav-rt') && b.closest('.nav-rt').querySelector('.nav-rt-help-t'); if (h) h.hidden = !h.hidden; }
    else if (k === 'toggle') {   // folded until the session ends; the next session opens it again
      const card = b.closest('.nav-rt'), c = !card.classList.contains('closed-rt'), f = FOLD[L] || FOLD.en;
      try { if (c) localStorage.setItem('sw.rtClosedDay', rtDay()); else localStorage.removeItem('sw.rtClosedDay'); } catch (x) { /* private mode: for this view only */ }
      card.classList.toggle('closed-rt', c); b.setAttribute('aria-expanded', String(!c)); b.setAttribute('aria-label', c ? f[1] : f[0]);
    }
  });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__rt) {
    const w = function () { const out = appRender.apply(this, arguments); try { place(); } catch (e) { /* never blocks */ } return out; };
    w.__rt = true; window.render = w;
  }
  new window.SweepMO(() => { try { place(); } catch (e) { if (!place.w) { place.w = 1; console.warn('Sweep routine: ' + (e && e.message)); } } }).observe(document.body, { childList: true, subtree: true });
  setInterval(() => { try { place(); } catch (e) { /* next minute */ } }, 60000);   // the review's moment comes with the clock, not with a change on the page
})();


/* (1 Nov., brief avance 4) Settings › My routine › Risk rules: the trader's own daily limits — max loss per day and max trades per
 * day — that close the day on Today (SweepCoach.dayLimits: with the day's plan and the account's daily limit, the tightest wins).
 * A change applies from the next session: settings.day_lock = { loss_c, trades, from, was } (the values in force until `from`), so
 * a limit is never lifted in the middle of the day it guards. Blank: none of his own (the plan and the firm's limit still count). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { loss: 'Max loss per day', trades: 'Max trades per day', none: 'None', help: 'Once one is reached, Today closes your day until 6:00 PM New York time. A change applies from your next session.', firm: 'Blank: your plan and your account’s daily limit ({a}).',
      wait: 'From {d}: these limits. Today: {o}.', off: 'no limit of your own', tr: '{n} trades', tr1: '1 trade', saved: 'Saved: it applies from your next session.', stop: 'My stop rule: close my day after losing trades in a row', losses: 'Losing trades in a row', lossesH: 'Once your stop rule or one of these limits is reached, the account guardian tells you to stop and offers to close your day. Sweep advises; your platform still takes your orders.', ls: '{n} losses in a row' },
    fr: { loss: 'Perte max par jour', trades: 'Trades max par jour', none: 'Aucun', help: 'Une fois une limite atteinte, Aujourd’hui ferme ta journée jusqu’à 18\u00a0h, heure de New York. Un changement s’applique à ta prochaine séance.', firm: 'Vide\u00a0: ton plan et la limite du jour de ton compte ({a}).',
      wait: 'À partir du {d}\u00a0: ces limites. Pour aujourd’hui\u00a0: {o}.', off: 'aucune limite à toi', tr: '{n} trades', tr1: '1 trade', saved: 'Enregistré\u00a0: ça s’applique à ta prochaine séance.', stop: 'Ma règle d’arrêt\u00a0: fermer ma journée après des trades perdants à la suite', losses: 'Trades perdants à la suite', lossesH: 'Une fois ta règle d’arrêt ou une de ces limites atteinte, le Gardien de compte te dit de t’arrêter et te propose de fermer ta journée. Sweep conseille\u00a0; ta plateforme prend toujours tes ordres.', ls: '{n} pertes à la suite' },
    es: { loss: 'Pérdida máx. por día', trades: 'Operaciones máx. por día', none: 'Ninguno', help: 'Al alcanzar un límite, Hoy cierra tu día hasta las 18:00, hora de Nueva York. Un cambio se aplica desde tu próxima sesión.', firm: 'Vacío: tu plan y el límite diario de tu cuenta ({a}).',
      wait: 'Desde el {d}: estos límites. Para hoy: {o}.', off: 'ningún límite propio', tr: '{n} operaciones', tr1: '1 operación', saved: 'Guardado: se aplica desde tu próxima sesión.', stop: 'Mi regla de stop: cerrar mi día tras operaciones perdedoras seguidas', losses: 'Operaciones perdedoras seguidas', lossesH: 'Al alcanzar tu regla de stop o uno de estos límites, el guardián de cuenta te dice que pares y te propone cerrar tu día. Sweep aconseja; tu plataforma sigue aceptando tus órdenes.', ls: '{n} pérdidas seguidas' } };
  const t = (k, v) => String((T[L] || T.en)[k]).replace(/\{(\w)\}/g, (m0, x) => (v && v[x] != null ? v[x] : ''));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const usd = (c) => (typeof money === 'function' ? money(c, { sign: false, dec: 0 }) : '$' + Math.round(c / 100));
  const day0 = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const now = (day) => (window.SweepCoach && SweepCoach.standing ? SweepCoach.standing(day) : { loss: 0, trades: 0 });
  const say = (x) => [x.loss ? usd(x.loss) : '', x.trades ? t(x.trades === 1 ? 'tr1' : 'tr', { n: x.trades }) : '', x.stop && x.losses ? t('ls', { n: x.losses }) : ''].filter(Boolean).join(' · ') || t('off');
  const stopOn = () => typeof billCan !== 'function' || billCan('guard_stop');   // (3 Nov.) the stop rule: Pro and Elite
  function fields() {
    const x = (S.settings && S.settings.day_lock) || {}, d = day0(), lim = (S.accounts || []).filter((a) => !a.demo && a.status !== 'archived' && a.status !== 'closed' && a.rules && a.rules.dll_c > 0).sort((a, b) => a.rules.dll_c - b.rules.dll_c)[0];
    const lv = +x.loss_c > 0 ? String(Math.round(x.loss_c / 100)) : '', tv = +x.trades > 0 ? String(x.trades) : '';
    const wait = x.from && d < x.from ? t('wait', { d: new Date(x.from + 'T12:00:00').toLocaleDateString(L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA', { weekday: 'long', day: 'numeric', month: 'long' }), o: say(now(d)) }) : '';
    return `<label class="f" data-noi18n><span>${esc2(t('loss'))}</span><input type="text" inputmode="decimal" data-daylock="loss" value="${esc2(lv)}" placeholder="${esc2(lim ? usd(lim.rules.dll_c) : '$')}"></label>
    <label class="f" data-noi18n><span>${esc2(t('trades'))}</span><input type="text" inputmode="numeric" data-daylock="trades" value="${esc2(tv)}" placeholder="${esc2(t('none'))}"></label>
    ${stopOn() ? `<label class="chk nav-dl-stop" data-noi18n><input type="checkbox" data-daylock="stop"${x.stop ? ' checked' : ''}><span>${esc2(t('stop'))}</span></label>
    <label class="f" data-noi18n><span>${esc2(t('losses'))}</span><input type="text" inputmode="numeric" data-daylock="losses" value="${esc2(x.losses == null || x.losses === '' ? '2' : String(x.losses))}" placeholder="2"></label><p class="help nav-dl-stoph" data-noi18n>${esc2(t('lossesH'))}</p>` : ''}
    <p class="help nav-dl-help" data-noi18n>${esc2(t('help'))}${lim ? ' ' + esc2(t('firm', { a: usd(lim.rules.dll_c) + ' · ' + (lim.name || '') })) : ''}${wait ? `<b class="nav-dl-wait">${esc2(wait)}</b>` : ''}</p>`;
  }
  document.addEventListener('change', (e) => {
    const el = e.target; if (!el.matches || !el.matches('input[data-daylock]')) return;
    const box = el.closest('.fgrid') || document, num = (k) => { const v = parseFloat(String((box.querySelector(`input[data-daylock="${k}"]`) || {}).value || '').replace(/[^0-9.]/g, '')); return isFinite(v) && v > 0 ? v : 0; };
    const d = day0(), x = (S.settings && S.settings.day_lock) || {};
    const next = new Date(d + 'T12:00:00'); next.setDate(next.getDate() + 1);
    const from = `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}-${String(next.getDate()).padStart(2, '0')}`;
    const cur = now(d), was = x.from && d < x.from ? x.was || { loss_c: 0, trades: 0 } : { loss_c: cur.loss, trades: cur.trades };   // a change already waiting keeps what today had
    const lsIn = box.querySelector('input[data-daylock="losses"]'), stIn = box.querySelector('input[data-daylock="stop"]');
    const lsV = lsIn ? parseInt(String(lsIn.value).replace(/[^0-9]/g, ''), 10) : NaN, losses = lsIn ? (isFinite(lsV) && lsV > 0 ? Math.min(20, lsV) : 2) : x.losses, stop = stIn ? stIn.checked : !!x.stop;   // blank: 2
    const keep = (o) => Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined));
    const dl = keep({ loss_c: Math.round(num('loss') * 100), trades: Math.min(99, Math.floor(num('trades'))), stop, losses, from, was: keep(Object.assign({}, was, x.from && d < x.from ? {} : { stop: !!x.stop, losses: x.losses })) });
    if (dl.loss_c === (+x.loss_c || 0) && dl.trades === (+x.trades || 0) && dl.stop === !!x.stop && String(dl.losses) === String(x.losses == null ? (lsIn ? 2 : undefined) : x.losses)) return;
    if (typeof editDoc === 'function') editDoc('settings', 'settings', (s) => { s.day_lock = dl; });
    if (typeof toast === 'function') toast(t('saved'));
  });
  window.SweepDayLock = { fields };
})();

/* left menu (computer): search and notifications get their label when the menu opens, like the other links */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const LB = { en: ['Search', 'Notifications'], fr: ['Rechercher', 'Notifications'], es: ['Buscar', 'Notificaciones'] }[L] || ['Search', 'Notifications'];
  function labels() {
    const side = document.querySelector('aside.side'); if (!side) return;
    [['.nav-search', LB[0]], ['.nt-bell', LB[1]]].forEach(([sel, txt]) => {
      const b = side.querySelector(sel); if (!b || b.querySelector('.nav-side-l')) return;
      const sp = document.createElement('span'); sp.className = 'nav-side-l'; sp.setAttribute('data-noi18n', ''); sp.textContent = txt;
      const svg = b.querySelector('svg'); if (svg) svg.after(sp); else b.append(sp);
    });
    // Sweep AI sits here on a computer, above search (audit of 18 Oct.: floating, it covered the cards on the right)
    const se = side.querySelector('.nav-search');
    if (se && !side.querySelector('.nav-ask-side')) {
      const nm = (typeof AL === 'function' && AL().name) || 'Sweep AI';
      const b = document.createElement('button'); b.type = 'button'; b.className = se.className.replace('nav-search', 'nav-ask-side'); b.setAttribute('aria-label', nm); b.setAttribute('data-noi18n', '');
      b.innerHTML = `${typeof ASK_MARK === 'string' ? ASK_MARK : ''}<span class="nav-side-l">${nm.replace(/[<>&]/g, '')}</span>`;
      b.addEventListener('click', () => { if (typeof askToggle === 'function') askToggle(true); });
      se.before(b);
    }
  }
  new window.SweepMO(() => { try { labels(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();


/* Payouts: « Share my payouts » above the numbers */
(function () {
  'use strict';
  function pass() {
    if (/^#payouts/.test(location.hash || '')) {
      const row = document.querySelector('#main .sh-row'), k = row && row.previousElementSibling;
      if (row && k && k.classList.contains('kpis')) { k.before(row); row.classList.add('nav-sh-top'); }
      // on the filters' line, at the right: symmetric with « All prop firms · All accounts »
      const fb = document.querySelector('#main > .fbars') || document.querySelector('#main > .mfb'), sr = document.querySelector('#main .sh-row.nav-sh-top');
      const fbt = fb && (fb.querySelector(':scope > .mfb-row') || fb);   // phone: next to « Filters » in its row
      if (fbt && sr && sr.parentElement !== fbt) { fbt.append(sr); sr.classList.add('nav-sh-fb'); }
    }
  }
  new window.SweepMO(() => { try { pass(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();

/* first account screen: welcome by first name, not by the generated username */
(function () {
  'use strict';
  new window.SweepMO(() => {
    const el = document.querySelector('#main .onb-eyebrow'); const fn = S && S.me && S.me.first_name;
    if (!el || !fn || el.dataset.fn === fn) return;
    const L = (typeof LANG !== 'undefined' && LANG) || 'en';
    el.textContent = ({ en: `Welcome ${fn},`, fr: `Bienvenue ${fn},`, es: `Bienvenido ${fn},` })[L] || `Welcome ${fn},`; el.dataset.fn = fn; el.setAttribute('data-noi18n', '');
  }).observe(document.body, { childList: true, subtree: true });
})();

/* ───────────── Delivery 1 · the first two minutes ─────────────
 * 2. The first-account page: « Three steps and you're trading » (account, plan, first trade), brief 03 step 1.
 * 3a. Firms as a grid of initials badges · 3b. « New or already running? » (current balance, highest balance).
 * 5. Manual form at first glance: account, symbol, direction, contracts, entry/exit or net P&L; the rest under « More details ».
 * 7. After the first trade, once: « Add Sweep to your home screen ». (6, the rings tip: replaced by « Your coach », brief 03 step 2.) */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { pushAT: 'Get this alert on your phone', pushAS: 'Even when Sweep is closed: your account guardian and your day closed, the moment they happen.', pushAGo: 'Turn on', later: 'Later', instGo: 'Install', pushT: 'Turn on your reminders', pushS: 'Your plan before the open, your review after the session, your Friday recap: Sweep reminds you on this phone.', pushGo: 'Turn on', planT: 'Your plan before your next trade', planS: 'Your last 3 sessions were traded without a plan. 30 seconds before the open: your bias and your max loss.', planGo: 'Make my plan', onbT: 'Three steps and you’re trading.', onbS: 'Your account, your plan for the day, your first trade: about two minutes.', st1: 'Your account', st2: 'Your plan', st3: 'Your first trade', wel: 'Welcome', feeN: '${a} of fees added to your expenses', state: 'New or already running?', nw: 'New', run: 'Already running', cur: 'Current balance ($)', peak: 'Highest balance reached ($)', peakH: 'Only for a drawdown that trails your highest balance.', more: 'More details', less: 'Fewer details', netH: 'or your net P&L', instT: 'Add Sweep to your home screen', instS: 'Open it like an app, full screen, in one tap.', ios: 'iPhone', and: 'Android', i1: 'In Safari, tap Share', i2: 'Choose « Add to Home Screen »', i3: 'Tap « Add »', a1: 'In Chrome, tap the ⋮ menu', a2: 'Choose « Install app » or « Add to Home screen »', a3: 'Confirm', ok: 'Got it' },
    fr: { pushAT: 'Reçois cette alerte sur ton téléphone', pushAS: 'Même quand Sweep est fermé : ton Gardien de compte et ta journée fermée, au moment où ça arrive.', pushAGo: 'Activer', later: 'Plus tard', instGo: 'Installer', pushT: 'Active tes rappels', pushS: 'Ton plan avant l’ouverture, ta revue après la séance, ton bilan du vendredi : Sweep te les rappelle sur ce téléphone.', pushGo: 'Activer', planT: 'Ton plan avant ton prochain trade', planS: 'Tes 3 dernières séances se sont faites sans plan. 30 secondes avant l’ouverture : ton biais et ta perte max.', planGo: 'Faire mon plan', onbT: 'Trois étapes et tu trades.', onbS: 'Ton compte, ton plan du jour, ton premier trade : environ deux minutes.', st1: 'Ton compte', st2: 'Ton plan', st3: 'Ton premier trade', wel: 'Bienvenue', feeN: '{a} $ de frais ajoutés à tes dépenses', state: 'Neuf ou déjà en cours ?', nw: 'Neuf', run: 'Déjà en cours', cur: 'Solde actuel ($)', peak: 'Plus haut solde atteint ($)', peakH: 'Seulement pour un drawdown qui suit ton plus haut solde.', more: 'Plus de détails', less: 'Moins de détails', netH: 'ou ton P&L net', instT: 'Ajoute Sweep à ton écran d’accueil', instS: 'Ouvre-le comme une app, plein écran, en un toucher.', ios: 'iPhone', and: 'Android', i1: 'Dans Safari, touche Partager', i2: 'Choisis « Sur l’écran d’accueil »', i3: 'Touche « Ajouter »', a1: 'Dans Chrome, touche le menu ⋮', a2: 'Choisis « Installer l’application » ou « Ajouter à l’écran d’accueil »', a3: 'Confirme', ok: 'Compris' },
    es: { pushAT: 'Recibe esta alerta en tu teléfono', pushAS: 'Incluso con Sweep cerrado: tu guardián de cuenta y tu día cerrado, en el momento en que ocurren.', pushAGo: 'Activar', later: 'Más tarde', instGo: 'Instalar', pushT: 'Activa tus recordatorios', pushS: 'Tu plan antes de la apertura, tu revisión tras la sesión, tu resumen del viernes: Sweep te lo recuerda en este teléfono.', pushGo: 'Activar', planT: 'Tu plan antes de tu próxima operación', planS: 'Tus 3 últimas sesiones se operaron sin plan. 30 segundos antes de la apertura: tu sesgo y tu pérdida máxima.', planGo: 'Hacer mi plan', onbT: 'Tres pasos y operas.', onbS: 'Tu cuenta, tu plan del día, tu primera operación: unos dos minutos.', st1: 'Tu cuenta', st2: 'Tu plan', st3: 'Tu primera operación', wel: 'Bienvenido', feeN: '{a} $ de comisiones añadidas a tus gastos', state: '¿Nueva o ya en curso?', nw: 'Nueva', run: 'Ya en curso', cur: 'Saldo actual ($)', peak: 'Saldo más alto alcanzado ($)', peakH: 'Solo para un drawdown que sigue tu saldo más alto.', more: 'Más detalles', less: 'Menos detalles', netH: 'o tu P&L neto', instT: 'Añade Sweep a tu pantalla de inicio', instS: 'Ábrelo como una app, a pantalla completa, con un toque.', ios: 'iPhone', and: 'Android', i1: 'En Safari, toca Compartir', i2: 'Elige « Añadir a pantalla de inicio »', i3: 'Toca « Añadir »', a1: 'En Chrome, toca el menú ⋮', a2: 'Elige « Instalar aplicación » o « Añadir a pantalla de inicio »', a3: 'Confirma', ok: 'Entendido' } };
  const t = (k, v) => String((T[L] || T.en)[k]).replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ''));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const LS = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } return null; };

  function pass() {
    // 2. before the first account: a simple screen; the app's form appears on tap
    const onb = document.querySelector('#main .onb');
    if (onb && !onb.dataset.simple) {
      onb.dataset.simple = '1'; onb.classList.add('nav-onb-direct');
      const ttl = onb.querySelector('h1, h2'); if (ttl) { ttl.textContent = t('onbT'); ttl.setAttribute('data-noi18n', ''); }
      const sub = onb.querySelector('.onb-sub'); if (sub) { sub.textContent = t('onbS'); sub.setAttribute('data-noi18n', ''); }
      const ol = onb.querySelector('.onb-steps'); if (ol) { ol.setAttribute('data-noi18n', ''); ol.innerHTML = ['st1', 'st2', 'st3'].map((k, i) => `<li class="${i ? '' : 'on'}"><span>${i + 1}</span>${t(k)}</li>`).join(''); }
      if (window.SweepStart && SweepStart.paint) SweepStart.paint();   // (activation D) the ending of this trader's case
    }
    if (onb) ['title', 'mtitle'].forEach((id) => { const el = document.getElementById(id); if (el && el.textContent !== t('wel')) el.textContent = t('wel'); });   // the page title and its collapsed copy on a phone
    // 3a. firms: initials badges
    document.querySelectorAll('.ux-st-tile[data-st-firm]:not([data-ini])').forEach((b) => {
      b.dataset.ini = '1'; const nm = (b.querySelector('b') || b).textContent.trim();
      const ini = nm.split(/\s+/).filter((w) => /^[A-Za-z]/.test(w)).slice(0, 2).map((w) => w[0].toUpperCase()).join('') || nm.slice(0, 2).toUpperCase();
      let h = 0; for (const c of nm) h = (h * 31 + c.charCodeAt(0)) % 360;
      b.insertAdjacentHTML('afterbegin', `<span class="nav-firm-ini" style="--h:${h}" aria-hidden="true">${esc2(ini)}</span>`);
    });
    // 3d. the firm's fees, when the catalogue knows them (otherwise the free « Account cost » field stays)
    const af2 = document.querySelector('form[data-form="account"]');
    if (af2) {
      const pv = af2.dataset.uxPreset || '', ph = pv.split('|')[3] || '';
      const pr = pv && window.SweepPresets && SweepPresets.priceOf ? SweepPresets.priceOf(pv) : null;
      const amt = pr ? (ph === 'eval' ? pr.eval : (ph === 'funded' ? pr.activation : null)) : null;
      let box = af2.querySelector('.nav-fee');
      if (amt == null) { if (box) box.remove(); const c = af2.querySelector('.nav-acc-x [name=nav_cost]'); if (c) c.closest('.nav-acc-x').hidden = false; }
      else if (!box || box.dataset.pv !== pv) {
        if (box) box.remove();
        const firmName = ((typeof CAT !== 'undefined' && CAT) ? '' : '') || ((af2.querySelector('.ux-st-crumbs button, .ux-st-crumb') || {}).textContent || '').trim();
        const label = ({ en: `Add the fees of ${pv.split('|')[0] === 'topstep' ? 'Topstep' : firmName} to my expenses`, fr: `Ajouter les frais de ${pv.split('|')[0] === 'topstep' ? 'Topstep' : firmName} à mes dépenses`, es: `Añadir las comisiones de ${pv.split('|')[0] === 'topstep' ? 'Topstep' : firmName} a mis gastos` })[L] || '';
        const what = ph === 'eval' ? ({ en: 'evaluation, first month', fr: 'évaluation, premier mois', es: 'evaluación, primer mes' })[L] : ({ en: 'activation', fr: 'activation', es: 'activación' })[L];
        const xs2 = af2.querySelector('.nav-acc-xs');
        if (xs2) {
          xs2.insertAdjacentHTML('beforebegin', `<label class="nav-fee" data-pv="${esc2(pv)}" data-noi18n><input type="checkbox" name="nav_fee_on" checked><span><b>${esc2(label)}</b><small class="muted">${esc2(what)} · ${({ en: 'catalogue price, editable', fr: 'prix du catalogue, modifiable', es: 'precio del catálogo, editable' })[L]}</small></span><span class="nav-fee-amt">$<input name="nav_fee" inputmode="decimal" value="${amt}"></span></label>`);
          const c = af2.querySelector('.nav-acc-x [name=nav_cost]'); if (c) c.closest('.nav-acc-x').hidden = true;   // one cost field, not two
        }
      }
      optNote(af2);
    }
    // 3b. new or already running (in the add-account form, next to the cost and count)
    const xs = document.querySelector('form[data-form="account"] .nav-acc-xs');
    if (xs && !xs.closest('form').querySelector('.nav-acst')) {
      xs.insertAdjacentHTML('beforebegin', `<div class="nav-acst" data-noi18n><span>${t('state')}</span><div class="seg"><button type="button" class="on" data-acst="new">${t('nw')}</button><button type="button" data-acst="run">${t('run')}</button></div>
        <div class="nav-acst-run" hidden><label class="f"><span>${t('cur')}</span><input name="nav_cur" inputmode="decimal" placeholder="$"></label><label class="f"><span>${t('peak')}</span><input name="nav_peak" inputmode="decimal" placeholder="$"><small class="muted">${t('peakH')}</small></label></div></div>`);
    }
    // a funded (or live) account chosen in the guided steps is often one already running: the question comes out of « More
    // options », right above it (audit of 16 Oct., R14); an evaluation keeps it there
    if (xs) {
      const f0 = xs.closest('form'), st = f0.querySelector('.nav-acst'), w = f0.querySelector('.ux-st'), opt = f0.querySelector('details.nav-acc-opt');
      const out = !!(st && w && opt && f0.classList.contains('ux-st-final') && /^(funded|live)$/.test(w.dataset.phase || ''));
      if (st && out && st.nextElementSibling !== opt) opt.before(st);
      else if (st && !out && st.parentElement !== xs.parentElement) xs.before(st);
    }
    // 5. manual form: the essentials first
    const tk = document.querySelector('#tkSlide.open');
    if (tk) {
      const editing = typeof TK !== 'undefined' && TK && TK.id;
      const min = !editing && LS('sw.tkMore') !== '1';
      tk.classList.toggle('nav-tk-min', min);
      const tag = (el) => el && el.classList.add('nav-more-x');
      const stop = tk.querySelector('[data-tk="stop"]'); tag(stop && stop.closest('.tk-row2'));
      tk.querySelectorAll('.nav-units, .nav-unit, #tkRisk, .nav-multi, .nav-exitat, .tk-copies, [data-act="tk-multi"], .tk-chart, #tkChart, .nav-ee + .nav-units').forEach(tag);
      const ris = tk.querySelector('#tkRisk'); if (ris) tag(ris.closest('.tk-risk, .tk-box') || ris);
      const ch = tk.querySelector('.ch-wrap, .tk-ch, [class*="chart"]'); if (ch && !ch.closest('.nav-more-x')) tag(ch);
      const real = tk.querySelector('.nav-real'); if (real && !real.dataset.min) { real.dataset.min = '1'; const lab = real.querySelector('span, label'); if (lab) lab.insertAdjacentHTML('beforeend', ` <em class="nav-netH">· ${t('netH')}</em>`); }
      const ee = tk.querySelector('.nav-ee') || (tk.querySelector('[data-tk="exit"]') || {}).closest?.('.tk-row2');
      if (!editing && ee && !tk.querySelector('.nav-more-b')) {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'link nav-more-b'; b.setAttribute('data-noi18n', '');
        const after = real || ee; after.after(b);
      }
      const realBox = tk.querySelector('.nav-real');
      if (realBox && !editing && !tk.querySelector('.nav-real-l')) {
        const l = document.createElement('button'); l.type = 'button'; l.className = 'link nav-real-l'; l.setAttribute('data-noi18n', '');
        l.textContent = ({ en: 'I have my platform’s P&L', fr: 'J’ai le P&L de ma plateforme', es: 'Tengo el P&L de mi plataforma' })[L] || 'I have my platform’s P&L';
        l.addEventListener('click', () => { tk.classList.add('nav-real-on'); l.remove(); const i = realBox.querySelector('input'); if (i) i.focus(); });
        realBox.before(l);
      }
      if (realBox && (editing || (realBox.querySelector('input') || {}).value)) tk.classList.add('nav-real-on');
      const mb = tk.querySelector('.nav-more-b'); if (mb) { mb.textContent = (tk.classList.contains('nav-tk-min') ? t('more') + ' ▾' : t('less') + ' ▴'); }
    }
  }
  // the folded « More options » line says when the firm's fees go to the expenses (nothing added without the trader seeing it)
  function optNote(f) {
    const s = f.querySelector('.nav-acc-opt-s'); if (!s) return;
    const on = f.querySelector('[name=nav_fee_on]'), amt = f.querySelector('[name=nav_fee]');
    const v = on && on.checked && amt ? Number(String(amt.value).replace(/[^0-9.]/g, '')) : 0;
    const txt = v > 0 ? t('feeN', { a: v.toLocaleString(L === 'en' ? 'en-US' : L + '-CA') }) : '';
    if (s.textContent !== txt) s.textContent = txt;
  }
  document.addEventListener('input', (e) => { const f = e.target.closest && e.target.closest('form[data-form="account"]'); if (f && /^nav_fee/.test(e.target.name || '')) optNote(f); });
  document.addEventListener('change', (e) => { const f = e.target.closest && e.target.closest('form[data-form="account"]'); if (f && /^nav_fee/.test(e.target.name || '')) optNote(f); });
  document.addEventListener('click', (e) => {
    const s = e.target.closest && e.target.closest('[data-acst]');
    if (s) {
      const box = s.closest('.nav-acst'); box.querySelectorAll('[data-acst]').forEach((x) => x.classList.toggle('on', x === s)); box.querySelector('.nav-acst-run').hidden = s.dataset.acst !== 'run';
      // already running: its activation fee was paid long ago — unticked (ticked again for a new one); the trader can still tick it
      const f = s.closest('form'), fee = f && f.querySelector('[name=nav_fee_on]');
      if (fee) { fee.checked = s.dataset.acst !== 'run'; optNote(f); }
      if (s.dataset.acst === 'run') { const c = box.querySelector('[name=nav_cur]'); if (c) c.focus({ preventScroll: true }); }
      return;
    }
    const m = e.target.closest && e.target.closest('.nav-more-b');
    if (m) { const tk = m.closest('#tkSlide'); const on = tk.classList.toggle('nav-tk-min'); LS('sw.tkMore', on ? '0' : '1'); m.textContent = on ? t('more') + ' ▾' : t('less') + ' ▴'; }
  });
  new window.SweepMO(() => { try { pass(); install(); moment(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });


  // 7. suggestions « do it now » (16 Oct., step 2 of the announcements): something useful not done yet, offered with the button
  // that does it — one at a time, the session's one window, only on a phone and from the 2nd day of use (the sign-up day and
  // this device's first day both before today; audit of 16 Oct.: never over the coach after the very first trade). In order:
  // Sweep on the home screen (Android / Chrome: « Install » installs it; iPhone: the 3 gestures, Apple lets no page do it), the
  // reminders on this phone, a plan before the next session after 3 sessions without one. « Later »: not before 7 days; each
  // one 3 times at most on this device. Checked once a few seconds after the app opens, and after each new trade.
  const standalone = () => (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  const nyDay = (ms) => new Date(ms).toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
  const nowDay = () => (typeof todayStr === 'function' ? todayStr() : nyDay(Date.now()));
  function secondDay() {
    const now = nowDay();
    let first = LS('sw.day0'); if (!first) { first = now; LS('sw.day0', now); }
    const c = S.me && S.me.created_at;
    const ms = c == null || c === '' ? NaN : /^\d+$/.test(String(c)) ? +c * 1000 : Date.parse(String(c).replace(' ', 'T') + (/[zZ]$|[+-]\d\d:?\d\d$/.test(String(c)) ? '' : 'Z'));
    return first < now && (!isFinite(ms) || nyDay(ms + 216e5) < now);   // the session of the sign-up (18:00 ET or later = the next day, as todayStr)
  }
  const phone = () => !!(window.matchMedia && matchMedia('(pointer: coarse)').matches) && innerWidth < 900;
  let bip = null;   // Chrome's own install prompt, kept for the « Install » button
  addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); bip = e; });
  addEventListener('appinstalled', () => { bip = null; LS('sw.installShown', '1'); });
  const SG = () => { try { return JSON.parse(LS('sw.sugg') || '{}') || {}; } catch (e) { return {}; } };
  const sgSet = (id, f) => { const all = SG(), r = all[id] || {}; f(r); all[id] = r; LS('sw.sugg', JSON.stringify(all)); };
  // (1 Nov., brief dans le temps C2) « Later » means 7 days on every device: kept in Settings too (the browser's copy was lost with a
  // new session, and the same window came back the next day)
  const sgOk = (id) => { const r = SG()[id] || {}, u = (S.settings && S.settings.sugg_later && +S.settings.sugg_later[id]) || 0; return !r.done && (r.n || 0) < 3 && !(r.until && r.until > Date.now()) && !(u > Date.now()); };
  const laterSet = (id) => { const until = Date.now() + 7 * 864e5; sgSet(id, (r) => { r.until = until; }); if (typeof editDoc === 'function' && S.settings) editDoc('settings', 'settings', (x) => { x.sugg_later = Object.assign({}, x.sugg_later, { [id]: until }); }); };
  const planOk = (j) => !!(j && j.pre && j.pre.bias && (j.pre.bias === 'no_trade' || parseFloat(String(j.pre.max_loss || '').replace(/[^0-9.]/g, '')) > 0));
  function noPlanRun() {   // the last 3 sessions with trades had no plan, and none yet for today
    const now = nowDay(), days = [...new Set((S.trades || []).filter((x) => !x.demo && x.date < now).map((x) => x.date))].sort().slice(-3);
    const jr = (d) => (typeof getDoc === 'function' ? getDoc('journals', d) : null);
    return days.length === 3 && days.every((d) => !planOk(jr(d))) && !planOk(jr(now));
  }
  async function pick(force) {
    if (force) return 'install';
    if (sgOk('install') && LS('sw.installShown') !== '1' && !standalone()) return 'install';
    if (sgOk('push') && window.SweepNotify && SweepNotify.push) { const p = await SweepNotify.push.state().catch(() => null); if (p && p.available && p.can && !p.on) return 'push'; }
    if (sgOk('plan') && noPlanRun()) return 'plan';
    return '';
  }
  let seenTrades = null, forced = false, loadT = 0, busy = false, held = false;
  function install() {   // called on every change of the page: cheap unless there is something new
    if (typeof S === 'undefined' || !Array.isArray(S.trades)) return;
    const n = S.trades.filter((x) => !x.demo).length;
    if (held && !(window.SweepQuiet && SweepQuiet())) { held = false; seenTrades = n; suggest(false); return; }   // the review done (or the next morning): now
    if (seenTrades === null) { seenTrades = n; if (!LS('sw.day0')) LS('sw.day0', nowDay()); if (!loadT) loadT = setTimeout(() => suggest(false), 5000); return; }
    if (n <= seenTrades && !forced) { seenTrades = n; return; }
    seenTrades = n; suggest(forced); forced = false;
  }
  async function suggest(force) {
    if (busy || document.querySelector('.nav-inst')) return;
    if (!force && (!phone() || !secondDay() || !S.me)) return;
    if (!force && window.SweepQuiet && SweepQuiet()) { held = true; return; }   // (C2) nothing over the app between the first trade and the review
    try { if (!force && sessionStorage.getItem('sw.modal') === '1') return; } catch (x) { /* private mode */ }
    busy = true; let id = ''; try { id = await pick(force); } finally { busy = false; }
    if (!id || document.querySelector('.nav-inst, .nav-pass, #gSheet.open, .nav-am.open, #tkSlide.open')) return;   // (never two windows at once: the evaluation's too)
    if (!force && window.SweepQuiet && SweepQuiet()) { held = true; return; }
    try { if (!force && sessionStorage.getItem('sw.modal') === '1') return; sessionStorage.setItem('sw.modal', '1'); } catch (x) { /* private mode */ }
    sgSet(id, (r) => { r.n = (r.n || 0) + 1; });
    show(id);
  }
  const SH_I = '<svg viewBox="0 0 24 24"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>';
  const ADD_I = '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8v8M8 12h8"/></svg>';
  const DOT_I = '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>';
  const OK_I = '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.2 4.2L19 7"/></svg>';
  const BELL_I = '<svg viewBox="0 0 24 24"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg>';
  const PLAN_I = '<svg viewBox="0 0 24 24"><path d="M6 21V4M6 4h11l-2 4 2 4H6"/></svg>';
  function show(id) {
    const ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const step = (n2, ic, txt) => `<li><span class="nav-inst-n">${n2}</span><span class="nav-inst-ic">${ic}</span><span>${txt}</span></li>`;
    LS('sw.suggAt', String(Date.now()));   // (5 Nov.) the last offer, whatever it was (the moments below wait a week after it)
    const head = id === 'install' ? `<div class="nav-inst-app" aria-hidden="true"><img src="icons/icon-192.png?v=2" alt="" onerror="this.remove()"></div><h2>${t('instT')}</h2><p class="muted">${t('instS')}</p>`
      : `<div class="nav-inst-app nav-inst-sg" aria-hidden="true">${id === 'push' || id === 'pushA' ? BELL_I : PLAN_I}</div><h2>${t(id + 'T')}</h2><p class="muted">${t(id + 'S')}</p>`;
    const body = id !== 'install' || bip ? '' : `<div class="seg nav-inst-seg"><button type="button" class="${ios ? 'on' : ''}" data-inst="ios">${t('ios')}</button><button type="button" class="${ios ? '' : 'on'}" data-inst="and">${t('and')}</button></div>
      <ol class="nav-inst-l" data-for="ios" ${ios ? '' : 'hidden'}>${step(1, SH_I, t('i1'))}${step(2, ADD_I, t('i2'))}${step(3, OK_I, t('i3'))}</ol>
      <ol class="nav-inst-l" data-for="and" ${ios ? 'hidden' : ''}>${step(1, DOT_I, t('a1'))}${step(2, ADD_I, t('a2'))}${step(3, OK_I, t('a3'))}</ol>`;
    const go = id === 'install' ? (bip ? t('instGo') : t('ok')) : t(id + 'Go');
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-inst open';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-inst open'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', ''); el.dataset.sg = id;
    el.innerHTML = `<div class="nav-dlg-in nav-inst-in">${head}${body}<button type="button" class="btn primary nav-am-save" data-inst-ok>${go}</button><button type="button" class="link nav-inst-later" data-inst-later>${t('later')}</button></div>`;
    document.body.append(scrim, el);
    const close = () => document.querySelectorAll('.nav-inst').forEach((x) => x.remove());
    const later = () => { laterSet(id); close(); };
    scrim.addEventListener('click', later); el.querySelector('[data-inst-later]').addEventListener('click', later);
    el.querySelector('[data-inst-ok]').addEventListener('click', async () => {
      close();
      if (id === 'install') {
        if (!bip) { sgSet(id, (r) => { r.done = true; }); return; }   // the gestures read: not asked again on this device
        const e = bip; bip = null;
        try { e.prompt(); const c = await e.userChoice; if (c && c.outcome === 'accepted') { LS('sw.installShown', '1'); sgSet(id, (r) => { r.done = true; }); } else laterSet(id); } catch (x) { /* the browser said no */ }
      } else if (id === 'push' || id === 'pushA') {
        const r = window.SweepNotify && SweepNotify.push ? await SweepNotify.push.on().catch(() => null) : null;
        if (r && r.on) sgSet(id, (x) => { x.done = true; }); else location.hash = '#settings';   // refused: Settings says why
      } else if (id === 'plan') { sgSet(id, (x) => { x.done = true; }); if (window.SweepGame && SweepGame.openPlan) SweepGame.openPlan(); }
    });
    el.querySelectorAll('[data-inst]').forEach((b) => b.addEventListener('click', () => { el.querySelectorAll('[data-inst]').forEach((x) => x.classList.toggle('on', x === b)); el.querySelectorAll('.nav-inst-l').forEach((l) => { l.hidden = l.dataset.for !== b.dataset.inst; }); }));
  }
  /* (5 Nov., brief notifications) the right moments on the phone: the first account guardian alert seen in the app (« watch » or
     « danger ») and the first day closed → « Get this alert on your phone, even when Sweep is closed » (on an iPhone in Safari: Sweep
     on the home screen first, notifications live there). Once each on this device; never between the first trade and the review
     (offered after it), never within 7 days of another offer, never two windows at once. */
  let mBusy = false;
  async function moment() {
    if (mBusy || typeof S === 'undefined' || !S.me || !phone()) return;
    const seen = document.querySelector('#main .nav-guard.lv-watch, #main .nav-guard.lv-danger') ? 'guard' : document.querySelector('#main .nav-lock') ? 'lock' : '';
    if (seen && !(SG()['m_' + seen] || {}).done && !LS('sw.momentDue')) LS('sw.momentDue', seen);
    const due = LS('sw.momentDue'); if (!due) return;
    if ((window.SweepQuiet && SweepQuiet()) || document.querySelector('.nav-inst, .nav-pass, #gSheet.open, .nav-am.open, #tkSlide.open, .nt-modal')) return;
    if (+(LS('sw.suggAt') || 0) > Date.now() - 7 * 864e5) return;
    mBusy = true;
    try {
      const p = window.SweepNotify && SweepNotify.push ? await SweepNotify.push.state().catch(() => null) : null;
      const done = () => { sgSet('m_' + due, (r) => { r.done = true; }); try { localStorage.removeItem('sw.momentDue'); } catch (e) { /* private */ } };
      if (!p || !p.available || p.on || (!p.can && !p.ios)) { done(); return; }   // nothing to offer (already on, blocked, or no push here)
      try { if (sessionStorage.getItem('sw.modal') === '1') return; sessionStorage.setItem('sw.modal', '1'); } catch (x) { /* private mode */ }
      done(); show(p.ios ? 'install' : 'pushA');
    } finally { mBusy = false; }
  }
  /* (5 Nov.) the QR code shown on a computer opens /?i=qr on the phone: there, once signed in, « Sweep on your home screen » (its own
     address cleaned, so a reload does not show it again); already installed, or on a computer: nothing */
  try {
    if (new URLSearchParams(location.search).get('i') === 'qr') {
      history.replaceState(null, '', location.pathname + location.hash);
      const qrGo = () => { if (typeof S === 'undefined' || !S.me) { setTimeout(qrGo, 400); return; } if (phone() && !standalone() && window.SweepInstall) SweepInstall.show(); };
      setTimeout(qrGo, 800);
    }
  } catch (e) { /* never blocks */ }
  window.SweepInstall = { show: () => { forced = true; LS('sw.installShown', '0'); try { sessionStorage.removeItem('sw.modal'); } catch (e) { /* private */ } suggest(true); },
    suggest: () => suggest(false), state: SG };
})();

/* ───────────── Delivery 2 · expected gestures and clarity ─────────────
 * 9 « Ready for payout » → record the payout · 10 trade rows: swipe (phone) / ⋯ (computer) · 11 delete = « Deleted · Undo » 5 s
 * 12 pull to refresh · 13 « Mark as failed » + « Archived » · 14 account filter pill · 15 « per your platform »
 * 16 discipline score featured + explained · 17 « Discipline » share card first · 19 end of Pro trial card (day 50) · + the line when
 * screenshot reading is not in the trader's plan. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { delAll: 'Deleted on {n} accounts', shotDel: 'Screenshot removed', qDel: 'Question removed', demoDel: 'Sample data removed', accDelT: 'Delete your Sweep account?', accDelS: 'Your account and all your data (trades, journals, accounts, payouts, expenses, screenshots) are deleted for good. This cannot be undone.', accDelGo: 'Delete for good', cancel: 'Cancel', edit: 'Edit', del: 'Delete', deleted: 'Deleted', undo: 'Undo', refresh: 'Release to refresh', refreshing: 'Refreshing…', failed: 'Mark as failed', failedT: 'Account marked as failed', failedL: 'Failed', passedL: 'Passed', liveL: 'Went live', archived: 'Archived', allAcc: 'All accounts', platform: 'per your platform', disc: 'Discipline', discT: 'Your discipline score', ckT: 'The checklist of this trade', ckH: 'Your « yes » answers to the checklist of this trade. Your discipline score (on Today) is something else: the share of your trades without a mistake over 30 days, by your coach\'s rules.', discH: 'The share of your trades without a mistake over the last 30 days, by the same rules as your coach: your checklist (a « no » counts), your stop, your bias, your max loss and number of trades, your setups, no trade within 10 minutes of a loss.', discI: 'To raise it: answer your checklist on every trade, define your stop before entering, stay under your max loss and your number of trades, and trade the setups of your plan.', discLast: 'last 30 days', ok: 'Got it', dCard: 'My discipline', streak: 'Streak', swept: 'Days swept', score: 'Discipline', capD: (s, n) => `${s}-day streak, ${n} % discipline. The process, every day. Tracked with Sweep`, kDisc: 'Discipline', kStats: 'Stats', kAlt: { stats: 'Stats', payout: 'Payout', payouts: 'Payouts', net: 'My money', week: 'Week', day: 'Day', trade: 'Trade' }, trialH: 'Your Pro trial ends in {n} days', trialH1: 'Your Pro trial ends tomorrow', trialU: 'What you use of Pro:', trialK: 'On Free, everything stays saved: nothing is deleted.', trialB: 'See the plans', noAi: 'Screenshot reading is part of Pro: enter your trade by hand.',
      u: { acc: ['account', 'accounts'], act: ['active', 'active'], po: ['payout', 'payouts'], ex: ['expense', 'expenses'], tr: ['trade', 'trades'], accounts: '{n} (Free keeps {f})', money: 'My money ({x})', shots: 'Screenshot reading ({n})', history: 'Your full history ({n} older than {d} days)', ai: 'Sweep AI beyond the Free limit' } },
    fr: { delAll: 'Supprimé sur {n} comptes', shotDel: 'Capture retirée', qDel: 'Question retirée', demoDel: 'Données d’exemple retirées', accDelT: 'Supprimer ton compte Sweep ?', accDelS: 'Ton compte et toutes tes données (trades, journaux, comptes, payouts, dépenses, captures) sont supprimés pour de bon. C’est irréversible.', accDelGo: 'Supprimer pour de bon', cancel: 'Annuler', edit: 'Modifier', del: 'Supprimer', deleted: 'Supprimé', undo: 'Annuler', refresh: 'Relâche pour actualiser', refreshing: 'Actualisation…', failed: 'Marquer comme échoué', failedT: 'Compte marqué comme échoué', failedL: 'Échoué', passedL: 'Réussi', liveL: 'Passé en live', archived: 'Archivés', allAcc: 'Tous les comptes', platform: 'selon ta plateforme', disc: 'Discipline', discT: 'Ton score de discipline', ckT: 'La checklist de ce trade', ckH: 'Tes réponses « oui » à la checklist de ce trade. Ton score de discipline (sur Aujourd’hui) est autre chose : la part de tes trades sans erreur sur 30 jours, avec les règles de ton coach.', discH: 'La part de tes trades sans erreur sur les 30 derniers jours, avec les mêmes règles que ton coach : ta checklist (un « non » compte), ton stop, ton biais, ta perte max et ton nombre de trades, tes setups, pas de trade dans les 10 minutes après une perte.', discI: 'Pour le monter : réponds à ta checklist sur chaque trade, définis ton stop avant d’entrer, reste sous ta perte max et ton nombre de trades, et trade les setups de ton plan.', discLast: '30 derniers jours', ok: 'Compris', dCard: 'Ma discipline', streak: 'Série', swept: 'Journées balayées', score: 'Discipline', capD: (s, n) => `${s} jours de suite, ${n} % de discipline. Le processus, chaque jour. Suivi avec Sweep`, kDisc: 'Discipline', kStats: 'Stats', kAlt: { stats: 'Stats', payout: 'Payout', payouts: 'Payouts', net: 'Mon argent', week: 'Semaine', day: 'Journée', trade: 'Trade' }, trialH: 'Ton essai Pro se termine dans {n} jours', trialH1: 'Ton essai Pro se termine demain', trialU: 'Ce que tu utilises de Pro :', trialK: 'Sur Free, tout reste enregistré : rien n’est supprimé.', trialB: 'Voir les forfaits', noAi: 'La lecture des captures fait partie de Pro : saisis ton trade à la main.',
      u: { acc: ['compte', 'comptes'], act: ['actif', 'actifs'], po: ['payout', 'payouts'], ex: ['dépense', 'dépenses'], tr: ['trade', 'trades'], accounts: '{n} (Free en garde {f})', money: 'Mon argent ({x})', shots: 'La lecture des captures ({n})', history: 'Ton historique complet ({n} de plus de {d} jours)', ai: 'Sweep AI au-delà de la limite de Free' } },
    es: { delAll: 'Eliminado en {n} cuentas', shotDel: 'Captura quitada', qDel: 'Pregunta quitada', demoDel: 'Datos de ejemplo quitados', accDelT: '¿Eliminar tu cuenta de Sweep?', accDelS: 'Tu cuenta y todos tus datos (operaciones, diarios, cuentas, payouts, gastos, capturas) se eliminan para siempre. No se puede deshacer.', accDelGo: 'Eliminar para siempre', cancel: 'Cancelar', edit: 'Editar', del: 'Eliminar', deleted: 'Eliminado', undo: 'Deshacer', refresh: 'Suelta para actualizar', refreshing: 'Actualizando…', failed: 'Marcar como fallida', failedT: 'Cuenta marcada como fallida', failedL: 'Fallida', passedL: 'Aprobada', liveL: 'Pasó a live', archived: 'Archivadas', allAcc: 'Todas las cuentas', platform: 'según tu plataforma', disc: 'Disciplina', discT: 'Tu puntuación de disciplina', ckT: 'La checklist de esta operación', ckH: 'Tus respuestas « sí » a la checklist de esta operación. Tu puntuación de disciplina (en Hoy) es otra cosa: la parte de tus operaciones sin error en 30 días, con las reglas de tu coach.', discH: 'La parte de tus operaciones sin error en los últimos 30 días, con las mismas reglas que tu coach: tu checklist (un « no » cuenta), tu stop, tu sesgo, tu pérdida máx. y tu número de operaciones, tus setups, ninguna operación en los 10 minutos tras una pérdida.', discI: 'Para subirla: responde tu checklist en cada operación, define tu stop antes de entrar, quédate bajo tu pérdida máx. y tu número de operaciones, y opera los setups de tu plan.', discLast: 'últimos 30 días', ok: 'Entendido', dCard: 'Mi disciplina', streak: 'Racha', swept: 'Días barridos', score: 'Disciplina', capD: (s, n) => `${s} días seguidos, ${n} % de disciplina. El proceso, cada día. Registrado con Sweep`, kDisc: 'Disciplina', kStats: 'Stats', kAlt: { stats: 'Stats', payout: 'Payout', payouts: 'Payouts', net: 'Mi dinero', week: 'Semana', day: 'Día', trade: 'Operación' }, trialH: 'Tu prueba Pro termina en {n} días', trialH1: 'Tu prueba Pro termina mañana', trialU: 'Lo que usas de Pro:', trialK: 'En Free, todo queda guardado: no se borra nada.', trialB: 'Ver los planes', noAi: 'La lectura de capturas es parte de Pro: introduce tu operación a mano.',
      u: { acc: ['cuenta', 'cuentas'], act: ['activa', 'activas'], po: ['payout', 'payouts'], ex: ['gasto', 'gastos'], tr: ['operación', 'operaciones'], accounts: '{n} (Free mantiene {f})', money: 'Mi dinero ({x})', shots: 'La lectura de capturas ({n})', history: 'Tu historial completo ({n} de más de {d} días)', ai: 'Sweep AI más allá del límite de Free' } } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const LS = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } return null; };
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const isPhone = () => window.SW_MQ.matches;

  /* 11. deletes with « Undo » (5 s) */
  function undoToast(label, restore, after) {
    document.querySelectorAll('.nav-undo').forEach((x) => x.remove());
    const el = document.createElement('div'); el.className = 'nav-undo'; el.setAttribute('role', 'status'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<span>${esc2(label)}</span><button type="button">${t('undo')}</button><i></i>`;
    document.body.append(el); requestAnimationFrame(() => el.classList.add('on'));
    let undone = false;
    const end = setTimeout(() => { el.classList.remove('on'); setTimeout(() => el.remove(), 300); if (!undone && after) after(); }, 5000);
    el.querySelector('button').addEventListener('click', () => { undone = true; clearTimeout(end); restore(); el.classList.remove('on'); setTimeout(() => el.remove(), 300); if (typeof render === 'function') render(); });
  }
  function softDelete(coll, id, then, one) {
    const doc = getDoc(coll, id); if (!doc) return;
    // a trade logged on several accounts (brief « avance concurrentielle », step 2): on all of them, or this one only? asked
    if (coll === 'trades' && !one && typeof siblings === 'function' && siblings(id).length && window.SweepCopyGroup) {
      SweepCopyGroup.askDelete(id).then((k) => { if (k === 'all') deleteAllCopies(id); else if (k === 'one') softDelete(coll, id, then, true); });
      return;
    }
    const snap = JSON.parse(JSON.stringify(doc));
    const solo = coll !== 'trades' || !(typeof siblings === 'function' && siblings(id).length);
    remove(coll, id);
    if (then) then();
    if (typeof render === 'function') render();
    undoToast(t('deleted'), () => put(coll, snap), () => { if (coll === 'trades' && solo) (snap.shots || []).forEach((r) => { try { ASSETS && ASSETS.delete(r.id).catch(() => {}); } catch (e) { /* asset kept */ } }); });
  }
  window.SweepUndo = { del: softDelete, toast: (text, undo, after) => undoToast(text, undo, after) };
  /** « Delete all N » on a copied trade: every copy goes, one « Deleted on N accounts · Undo » brings them all back (same copy_group, checklist, notes) */
  function deleteAllCopies(id) {
    const doc = getDoc('trades', id); if (!doc) return;
    const group = typeof copiesOf === 'function' ? copiesOf(doc) : [doc];
    const snaps = group.map((x) => JSON.parse(JSON.stringify(x)));
    group.forEach((x) => remove('trades', x.id));
    if (/^#trade\//.test(location.hash || '')) location.hash = '#trades';   // from a row of a list: the list stays
    if (typeof render === 'function') render();
    undoToast(t('delAll').replace('{n}', group.length), () => snaps.forEach((x) => put('trades', x)), () => {
      const shots = new Set(); snaps.forEach((x) => (x.shots || []).forEach((r) => shots.add(r.id)));   // the files go only once nobody undid
      shots.forEach((sid) => { try { ASSETS && ASSETS.delete(sid).catch(() => {}); } catch (e) { /* asset kept */ } });
    });
  }
  /** a screenshot of a trade (and of its copies): back with « Undo », the file is deleted after 5 s */
  function deleteShot(id, sid) {
    const doc = getDoc('trades', id); if (!doc) return;
    const before = JSON.parse(JSON.stringify(doc.shots || []));
    editDoc('trades', id, (d) => { d.shots = (d.shots || []).filter((o) => o.id !== sid); });
    if (typeof syncTrade === 'function') syncTrade(id, ['shots']);
    if (typeof render === 'function') render();
    undoToast(t('shotDel'), () => { editDoc('trades', id, (d) => { d.shots = before; }); if (typeof syncTrade === 'function') syncTrade(id, ['shots']); },
      () => { try { ASSETS && ASSETS.delete(sid).catch(() => {}); } catch (e) { /* asset kept */ } });
  }
  /** a question of the checklist (Settings) */
  function deleteQuestion(i) {
    const set = getDoc('settings', 'settings'); if (!set || !Array.isArray(set.questions)) return;
    const before = JSON.parse(JSON.stringify(set.questions));
    editDoc('settings', 'settings', (d) => { d.questions.splice(Number(i), 1); });
    if (typeof render === 'function') render();
    undoToast(t('qDel'), () => editDoc('settings', 'settings', (d) => { d.questions = before; }));
  }
  /** all the sample data: removed at once, back with « Undo » */
  async function deleteDemo() {
    const cols = typeof COLS !== 'undefined' ? COLS : ['firms', 'accounts', 'trades', 'journals', 'weekly', 'payouts', 'expenses', 'meta'];
    const snap = {}; cols.forEach((c) => { snap[c] = (S[c] || []).filter((x) => x.demo).map((x) => JSON.parse(JSON.stringify(x))); });
    try { for (const c of cols) if (snap[c].length) await bulkDel(c, snap[c].map((x) => x.id)); } catch (err) { if (typeof toast === 'function') toast(typeof saveErr === 'function' ? saveErr(err) : String(err)); }
    if (typeof F !== 'undefined' && (String(F.account).startsWith('demo') || String(F.firm).startsWith('demo'))) { F.account = 'all'; F.firm = 'all'; if (typeof saveF === 'function') saveF(); }
    if (typeof render === 'function') render();
    undoToast(t('demoDel'), async () => { for (const c of cols) if (snap[c].length) { try { await bulkPut(c, snap[c]); } catch (err) { /* next */ } } if (typeof render === 'function') render(); });
  }
  /** a choice in the app's own window (never the browser's): resolves true / false */
  function askApp(title, text, go, danger = true) {
    return new Promise((done) => {
      const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-ask';
      const el = document.createElement('aside'); el.className = 'nav-dlg nav-ask'; el.setAttribute('role', 'alertdialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
      el.innerHTML = `<div class="nav-dlg-in"><h2>${esc2(title)}</h2><p class="nav-pass-s">${esc2(text)}</p><button type="button" class="btn primary ${danger ? 'danger' : ''} nav-am-save" data-ask="1">${esc2(go)}</button><button type="button" class="btn nav-pass-later" data-ask="0">${esc2(t('cancel'))}</button></div>`;
      document.body.append(scrim, el); requestAnimationFrame(() => { el.classList.add('open'); scrim.classList.add('open'); });
      const close = (v) => { [el, scrim].forEach((x) => { x.classList.remove('open'); setTimeout(() => x.remove(), 250); }); done(v); };
      el.addEventListener('click', (e) => { const b = e.target.closest('[data-ask]'); if (b) close(b.dataset.ask === '1'); });
      scrim.addEventListener('click', () => close(false));
      setTimeout(() => { const b = el.querySelector('[data-ask="0"]'); if (b) b.focus(); }, 50);
    });
  }
  window.SweepAsk = askApp;   // (the 90-day gameplan's « Stop » asks with it too)
  // deleting the Sweep account itself is final (server side): no « Undo » possible, so the app's own window asks, not the browser
  if (typeof deleteAccount === 'function') {
    deleteAccount = async function (form) {
      const pw = form && form.elements && form.elements.password ? form.elements.password.value : '';
      if (!pw) { if (typeof toast === 'function') toast('Enter your password to confirm.'); return; }
      if (!(await askApp(t('accDelT'), t('accDelS'), t('accDelGo')))) return;
      try { await apiJSON('api/account?_method=DELETE', { method: 'POST', body: { password: pw } }); location.href = location.pathname; } catch (err) { if (typeof toast === 'function') toast(err.message); }
    };
  }
  window.SweepUndo.ask = askApp;
  /* B16: sample data — the app's window with the exact number of trades it will add */
  window.SweepUndo.demo = (n, a) => {
    const D = { en: ['Add sample data?', 'Adds {n} sample trades in {a} sample accounts. You can remove them anytime in Settings; your own data is not touched.', 'Add {n} trades'],
      fr: ['Ajouter des données d’exemple ?', 'Ajoute {n} trades d’exemple dans {a} comptes d’exemple. Tu peux les retirer quand tu veux dans les Réglages ; tes données ne sont pas touchées.', 'Ajouter {n} trades'],
      es: ['¿Añadir datos de ejemplo?', 'Añade {n} operaciones de ejemplo en {a} cuentas de ejemplo. Puedes quitarlas cuando quieras en Ajustes; tus datos no se tocan.', 'Añadir {n} operaciones'] }[LANG] || null;
    const x = (D || ['Add sample data?', 'Adds {n} sample trades in {a} sample accounts.', 'Add {n} trades']).map((v) => v.replace('{n}', n).replace('{a}', a));
    return askApp(x[0], x[1], x[2], false);
  };
  document.addEventListener('click', (e) => {
    const x = e.target.closest && e.target.closest('[data-act="del-trade-all"], [data-act="del-shot"], [data-act="q-del"], [data-act="demo-del"]'); if (!x) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const k = x.dataset.act, m = x.closest('details[open]'); if (m) m.open = false;
    if (k === 'del-trade-all' && x.dataset.id) deleteAllCopies(x.dataset.id);
    else if (k === 'del-shot' && x.dataset.id) deleteShot(x.dataset.id, x.dataset.v);
    else if (k === 'q-del') deleteQuestion(x.dataset.i);
    else if (k === 'demo-del') deleteDemo();
  }, true);
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-act="del-trade"], [data-act="del-payout"], [data-act="del-expense"], [data-act="del-account"]'); if (!b || !b.dataset.id) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const k = b.dataset.act;
    if (k === 'del-trade') softDelete('trades', b.dataset.id, () => { if (/^#trade\//.test(location.hash)) history.length > 1 ? history.back() : (location.hash = '#trades'); });
    else if (k === 'del-payout') softDelete('payouts', b.dataset.id, () => { if (typeof U !== 'undefined') U.editP = null; });
    else if (k === 'del-expense') softDelete('expenses', b.dataset.id, () => { if (typeof U !== 'undefined') U.editE = null; });
    else softDelete('accounts', b.dataset.id, () => { location.hash = '#accounts'; });
  }, true);

  /* 9. « Ready for payout » → record the payout for that account */
  document.addEventListener('click', (e) => {
    const r = e.target.closest && e.target.closest('.nav-acc .nav-ready'); if (!r) return;
    const a = r.closest('.nav-acc'); const id = a && decodeURIComponent((a.getAttribute('href') || '').replace('#account/', '')); if (!id) return;
    if (/Objectifs|Objectives|Objetivos/.test(r.textContent)) return;   // an evaluation: no payout
    e.preventDefault(); e.stopPropagation();
    if (window.SweepPayout && SweepPayout.request) SweepPayout.request(id);
  }, true);

  /* 10. trade rows: ⋯ (computer), swipe left (phone) */
  const rowId = (r) => { const h = r.getAttribute('href') || r.dataset.href || ''; const m = /#trade\/([^/?#]+)/.exec(h); return m ? decodeURIComponent(m[1]) : null; };
  function rows() {
    document.querySelectorAll('#main a.trow, #main tr[data-href^="#trade/"], #main a.nav-tr').forEach((r) => {
      if (r.dataset.rowActs) return; const id = rowId(r); if (!id) return; r.dataset.rowActs = '1';
      const IE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/></svg>', ID = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>';
      const acts = `<span class="nav-ra" data-noi18n><button type="button" class="del" data-ra="del" data-id="${esc2(id)}" title="${t('del')}" aria-label="${t('del')}">${ID}<span>${t('del')}</span></button></span>`;   // editing happens on the trade page (one way only)
      const tr0 = getDoc('trades', id); if (tr0 && tr0.real_pnl_c != null) { const pl = r.querySelector('.trow-pnl') || [...r.children].find((c) => /^[+−-]?\$[\d,]/.test(c.textContent.trim())); if (pl && !pl.querySelector('.nav-plat-r')) pl.insertAdjacentHTML('beforeend', `<small class="nav-plat-r" data-noi18n>${t('platform')}</small>`); }
      if (r.tagName === 'TR') { r.classList.add('nav-ra-tr'); const td = r.lastElementChild; if (td) { td.classList.add('nav-ra-td'); td.insertAdjacentHTML('beforeend', `<span class="nav-dots" data-noi18n>${acts}</span>`); } }
      else { r.classList.add('nav-ra-row'); r.insertAdjacentHTML('beforeend', `<span class="nav-dots" data-noi18n>${acts}</span>`); }
    });
  }
  document.addEventListener('click', (e) => {
    const d = e.target.closest && e.target.closest('.nav-dots-b');
    if (d) { e.preventDefault(); e.stopPropagation(); const box = d.parentElement; const open = box.classList.toggle('open'); document.querySelectorAll('.nav-dots.open').forEach((x) => { if (x !== box) x.classList.remove('open'); }); return; }
    const a = e.target.closest && e.target.closest('button[data-ra]');
    if (a) { e.preventDefault(); e.stopPropagation(); const id = a.dataset.id; document.querySelectorAll('.nav-dots.open, .nav-ra-row.nav-sw').forEach((x) => x.classList.remove('open', 'nav-sw'));
      if (a.dataset.ra === 'edit') { if (typeof openTicket === 'function') openTicket(id); } else softDelete('trades', id); return; }
    if (!e.target.closest('.nav-dots')) document.querySelectorAll('.nav-dots.open').forEach((x) => x.classList.remove('open'));
  }, true);
  let sx = 0, sy = 0, srow = null, moved = false;
  document.addEventListener('touchstart', (e) => { const r = e.target.closest && e.target.closest('.nav-ra-row'); if (!r || !isPhone()) { srow = null; return; } srow = r; sx = e.touches[0].clientX; sy = e.touches[0].clientY; moved = false; }, { passive: true });
  document.addEventListener('touchmove', (e) => {
    if (!srow) return; const dx = e.touches[0].clientX - sx, dy = e.touches[0].clientY - sy;
    if (!moved && Math.abs(dx) > 12 && Math.abs(dx) > Math.abs(dy)) moved = true;
    if (!moved) return;
    const base = srow.classList.contains('nav-sw') ? -96 : 0, x = Math.min(0, dx + base), w = srow.offsetWidth;
    srow.classList.add('dragging'); srow.classList.toggle('nav-full', -x > w * 0.55);
    const d = srow.querySelector('.nav-dots'); if (d) d.style.width = Math.max(0, -x) + 'px';
    srow._x = x;
  }, { passive: true });
  document.addEventListener('touchend', () => {
    if (!srow) return; const r = srow; srow = null; const x = r._x || 0, w = r.offsetWidth, d = r.querySelector('.nav-dots');
    r.classList.remove('dragging'); r._x = 0; if (d) d.style.width = '';
    if (!moved) return;
    if (-x > w * 0.55) { const id = rowId(r); r.classList.remove('nav-sw', 'nav-full'); if (id) softDelete('trades', id); return; }   // long swipe: delete (Undo for 5 s)
    r.classList.remove('nav-full'); r.classList.toggle('nav-sw', x < -48);
    document.querySelectorAll('.nav-ra-row.nav-sw').forEach((o) => { if (o !== r) o.classList.remove('nav-sw'); });
  });
  document.addEventListener('click', (e) => { const r = e.target.closest && e.target.closest('.nav-ra-row.nav-sw'); if (r && !e.target.closest('[data-ra]')) { e.preventDefault(); r.classList.remove('nav-sw'); } }, true);

  /* 12. pull to refresh (phone: Today, Trades, Stats) */
  /* the small tap of the Mail app when the pull reaches the refresh: navigator.vibrate where it exists; on the iPhone, which has
     none, the switch trick of Safari 18 (toggling an <input switch> plays the system haptic) */
  function ptrTick() {
    try {
      if (navigator.vibrate) { navigator.vibrate(10); return; }
      let l = document.getElementById('navPtrTick');
      if (!l) { l = document.createElement('label'); l.id = 'navPtrTick'; l.setAttribute('aria-hidden', 'true'); l.innerHTML = '<input type="checkbox" switch tabindex="-1">'; document.body.append(l); }
      l.click();
    } catch (e) { /* no haptic: fine */ }
  }
  let py = null, pdist = 0, pel = null;
  const ptrPage = () => true;
  /* the installed app (html.pwa, 19 Oct.): iOS's own bounce is off (what it showed above the page did not match its
     background: a dark line), the app moves the header and the page itself, the indicator in the gap */
  const ptrMove = (y, back) => {
    const h = document.documentElement; if (!h.classList.contains('pwa')) return;
    h.classList.toggle('ptr-back', !!back); h.style.setProperty('--ptr-y', y + 'px'); h.classList.add('ptr-on');
    if (back && !y) setTimeout(() => { if (h.style.getPropertyValue('--ptr-y') === '0px') h.classList.remove('ptr-on', 'ptr-back'); }, 450);
  };   // every page (the app's first pull to refresh, now removed, worked everywhere)
  document.addEventListener('touchstart', (e) => { if (!isPhone() || !ptrPage() || scrollY > 0 || e.target.closest('.evp, .nav-am, .nav-dlg, #gSheet, #shPanel, .nav-fstrip, .nav-ra-row')) { py = null; return; } py = e.touches[0].clientY; pdist = 0; }, { passive: true });
  document.addEventListener('touchmove', (e) => { if (py == null) return; pdist = Math.max(0, e.touches[0].clientY - py); if (pdist < 8) return; if (!pel) { pel = document.createElement('div'); pel.className = 'nav-ptr'; pel.setAttribute('data-noi18n', ''); pel.innerHTML = '<i></i><span></span>'; document.body.append(pel); pel._armed = false; } const p = Math.min(1, pdist / 90); pel.style.setProperty('--p', p); ptrMove(Math.round(130 * (1 - Math.exp(-pdist / 190))));   /* a rubber band: follows the finger, harder the further it goes */ pel.querySelector('span').textContent = p >= 1 ? t('refresh') : ''; if (p >= 1 && !pel._armed) { pel._armed = true; pel.classList.add('armed'); ptrTick(); } else if (p < 1 && pel._armed) { pel._armed = false; pel.classList.remove('armed'); } }, { passive: true });
  document.addEventListener('touchend', async () => {
    if (py == null) return; py = null; if (!pel) { ptrMove(0, true); return; } const go = pdist >= 90; const el = pel; pel = null;
    if (!go) { el.remove(); ptrMove(0, true); return; }
    ptrMove(56, true);   // the page waits a little lower while it spins
    el.classList.add('busy'); el.querySelector('span').textContent = t('refreshing'); const t0 = Date.now();
    try { if (typeof syncNow === 'function') await syncNow({ manual: true }); if (window.SweepGame && SweepGame.refresh) await SweepGame.refresh(); } catch (e) { /* keeps what is shown */ }
    await new Promise((r) => setTimeout(r, Math.max(0, 700 - (Date.now() - t0))));   // it spins long enough to be seen, like Mail
    if (typeof syncNow !== 'function') { location.reload(); return; }   // only if the app's sync is missing
    if (typeof render === 'function') render(); ptrMove(0, true); setTimeout(() => el.remove(), 300);
  });

  /* 13. accounts: « Mark as failed » and the archived list */
  function accountsExtras() {
    const m = /^#account\/([^/]+)/.exec(location.hash || ''); const main = document.getElementById('main'); if (!main) return;
    if (m) {
      const a = getDoc('accounts', decodeURIComponent(m[1]));
      // B12: one back link only (the breadcrumb « Comptes »)
      const backs = [...main.querySelectorAll('a[href="#accounts"]')]; backs.slice(1).forEach((x) => { if (x.closest('.nav-arch')) return; x.hidden = true; const sl = x.nextElementSibling; if (sl && sl.matches('.faint') && sl.textContent.trim() === '/') sl.hidden = true; });   // and the « / » that followed it
      if (main.querySelector('.acc-menu')) return;   // « Mark as failed » lives in the « ⋯ » menu
      if (a && a.status !== 'archived' && !main.querySelector('.nav-fail')) {
        const close = [...main.querySelectorAll('button, a')].find((b) => /Fermer le compte|Close account|Cerrar la cuenta/i.test(b.textContent));
        const host = close ? close.parentElement : main.querySelector('.row'); if (host) host.insertAdjacentHTML('beforeend', `<button type="button" class="btn sm nav-fail" data-fail="${esc2(a.id)}" data-noi18n>${t('failed')}</button>`);
      }
      return;
    }
    if (!/^#accounts$/.test(location.hash || '')) return;
    if (main.querySelector('.nav-arch')) return;
    const arch = (S.accounts || []).filter((a) => a.status === 'archived'); if (!arch.length) return;
    const lab = (a) => a.result === 'failed' ? t('failedL') : a.result === 'passed' ? t('passedL') : a.result === 'live' ? t('liveL') : a.result === 'won' ? (({ en: 'Closed in profit', fr: 'Fermé en gain', es: 'Cerrada con ganancia' })[LANG] || 'Closed in profit') : t('archived');
    const when = (a) => a.failed_on || a.passed_on || a.live_on || a.won_on || '';
    const html = `<details class="surface nav-arch" data-noi18n><summary>${t('archived')} · ${arch.length}</summary><div>${arch.map((a) => `<a class="nav-arch-r" href="#account/${esc2(a.id)}"><b>${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</b><span class="nav-arch-t ${a.result || ''}">${lab(a)}</span><small class="muted">${esc2(when(a))}</small></a>`).join('')}</div></details>`;
    const add = main.querySelector('[data-act="acct-add"]'); const host = (add && add.closest('.surface')) || main.lastElementChild; if (host) host.insertAdjacentHTML('afterend', html);
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-fail]'); if (!b) return;
    // brief 02 part 2: no confirm() window — marked at once, « Undo » for 5 s puts the account back as it was
    const id = b.dataset.fail, was = getDoc('accounts', id); if (!was) return;
    const keep = { status: was.status, result: was.result, failed_on: was.failed_on };
    editDoc('accounts', id, (d) => { d.status = 'archived'; d.result = 'failed'; d.failed_on = today(); });
    location.hash = '#accounts';
    undoToast(t('failedT'), () => editDoc('accounts', id, (d) => { for (const k in keep) { if (keep[k] === undefined) delete d[k]; else d[k] = keep[k]; } }));
  });

  /* 14. the account filter, visible on Today and Stats */
  function filterPill() {
    const top = document.querySelector('.main-wrap > .top'); const on = /^#?(dashboard|analytics)?$/.test((location.hash || '').replace(/^#/, '')) && typeof F !== 'undefined' && F.account && F.account !== 'all';
    let p = document.querySelector('.nav-fpill');
    if (!on) { if (p) p.remove(); return; }
    const name = typeof acctLabel === 'function' ? acctLabel(F.account) : F.account;
    if (p && p.dataset.v === String(F.account)) return;
    const html = `<button type="button" class="nav-fpill" data-fpill data-noi18n data-v="${esc2(F.account)}"><span>${esc2(name)}</span><b aria-label="${t('allAcc')}">✕</b></button>`;
    if (p) p.remove();
    const main = document.getElementById('main'); if (main) main.insertAdjacentHTML('afterbegin', html);
  }
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-fpill]')) { F.account = 'all'; if (typeof saveF === 'function') saveF(); if (typeof render === 'function') render(); } });

  /* 15. one P&L: the platform's when it is there, said discreetly */
  function platformMark() {
    const m = /^#trade\/([^/]+)/.exec(location.hash || ''); if (!m) return;
    const tr = getDoc('trades', decodeURIComponent(m[1])); const main = document.getElementById('main'); if (!tr || !main || tr.real_pnl_c == null || main.querySelector('.nav-plat')) return;
    const big = [...main.querySelectorAll('.big, .pnl, b, strong')].find((x) => /^[+−-]?\$[\d,]+/.test(x.textContent.trim())); if (big) big.insertAdjacentHTML('afterend', `<small class="nav-plat" data-noi18n>${t('platform')}</small>`);
  }

  /* 16. discipline: the featured score on Today (and explained everywhere it shows) */
  // the share of the last 30 days' trades without a mistake, by the coach's own rules (src/coach.js: the checklist — a « no »
  // counts —, the stop, the bias, the max loss and number of trades, the setups, a trade within 10 min of a loss…), copies once.
  // Audit of 16 Oct. (R10): it read the checklist only, so a day of tilt traded without it stayed at 100 %. Without the coach:
  // the checklist average as before.
  let dCache = { k: '', v: null };
  function discScore() {
    const from = (() => { const d = new Date(today() + 'T12:00:00'); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10); })();
    const last = (a) => (a || []).reduce((m, x) => (x.updated_at > m ? x.updated_at : m), '');
    const key = [from, (S.trades || []).length, last(S.trades), (S.journals || []).length, last(S.journals), JSON.stringify((S.settings || {}).max_contracts || '')].join('|');
    if (dCache.k === key) return dCache.v;
    let tr = (S.trades || []).filter((x) => !x.demo && x.date >= from); if (!tr.length) tr = (S.trades || []).filter((x) => x.date >= from);
    // (29 Oct., tour T4) while no checklist at all is filled, « — » (never a 0 % that reads like a mark); once one is, every trade
    // counts, the way the coach counts (R10, 16 Oct.: a mistake without a checklist still counts)
    if (typeof tDisc === 'function' && !tr.some((x) => tDisc(x) != null)) tr = [];
    tr = typeof mergeCopies === 'function' ? mergeCopies(tr) : tr;
    let v = null;
    if (window.SweepCoach && SweepCoach.trade) {
      const notes = tr.map((x) => { try { return SweepCoach.trade(x); } catch (e) { return null; } }).filter(Boolean);
      v = notes.length ? Math.round(notes.filter((c) => !c.fix).length / notes.length * 100) : null;
    } else {
      const ds = typeof tDisc === 'function' ? tr.map(tDisc).filter((x) => x != null) : [];
      v = ds.length ? Math.round(ds.reduce((a, x) => a + x, 0) / ds.length * (ds[0] <= 1 ? 100 : 1)) : null;
    }
    dCache = { k: key, v }; return v;
  }
  function discChip() {
    const me = document.querySelector('#main .nav-rt .nav-rt-me'); if (!me || !me.querySelector('.nav-rt-streak')) return;   // before the first trade the routine shows no figures (27 Oct.)
    const v = discScore(), key = String(v); let c = me.querySelector('.nav-rt-disc:not(.nav-rt-disc-ph)');
    if (c && c.dataset.v === key) return;   // unchanged: touch nothing (a DOM change here would wake every watcher again)
    const html = `<button type="button" class="nav-rt-disc" data-disc-why data-noi18n data-v="${key}"><small>${t('disc')}</small><b>${v == null ? '—' : v + (L === 'en' ? '%' : '\u202f%')}</b></button>`;
    if (c) c.remove(); const ph = me.querySelector('.nav-rt-disc-ph'); if (ph) ph.remove(); me.insertAdjacentHTML('afterbegin', html);   // takes the placeholder's place: same size, nothing moves
  }
  function discWhy(kind) {
    let v = discScore();
    if (kind === 'trade') { const m = /^#trade\/([^/]+)/.exec(location.hash || ''); const tr = m && getDoc('trades', decodeURIComponent(m[1])); const d = tr && typeof tDisc === 'function' ? tDisc(tr) : null; v = d == null ? null : Math.round(d * (d <= 1 ? 100 : 1)); }
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-dwhy open';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-dwhy open'; el.setAttribute('role', 'dialog'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in nav-dwhy-in"><div class="nav-dwhy-v"><b>${v == null ? '—' : v + (L === 'en' ? '%' : '\u202f%')}</b><small>${kind === 'trade' ? ({ en: 'this trade', fr: 'ce trade', es: 'esta operación' })[L] : t('discLast')}</small></div><h2>${kind === 'trade' ? t('ckT') : t('discT')}</h2><p>${kind === 'trade' ? t('ckH') : t('discH')}</p>${kind === 'trade' ? '' : `<p class="muted">${t('discI')}</p>`}<button type="button" class="btn primary nav-am-save" data-dwhy-ok>${t('ok')}</button></div>`;
    document.body.append(scrim, el);
    const done = () => document.querySelectorAll('.nav-dwhy').forEach((x) => x.remove());
    scrim.addEventListener('click', done); el.querySelector('[data-dwhy-ok]').addEventListener('click', done);
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-disc-why]'); if (b) { e.preventDefault(); discWhy(b.dataset.discWhy); } });

  /* 17. « Discipline » share card, first in the share window opened from Stats */
  let swept = null;
  async function loadSwept() {
    try { const d = today(), from = d.slice(0, 8) + '01'; const r = await fetch(`api/game/history?from=${from}&to=${d}`, { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } }); const j = await r.json(); const arr = Array.isArray(j) ? j : (j.days || j.history || j.items || []); swept = arr.filter((x) => x && (x.swept || x.is_swept || (x.rings && x.rings.plan >= 100 && x.rings.execution >= 100 && x.rings.review >= 100))).length; } catch (e) { swept = null; }
  }
  (function wrap(n) {
    if (typeof window.shData !== 'function' || !window.shData.__congrats) { if (n < 150) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.shData.__disc) return;
    const orig = window.shData;
    const w = function (kind) {
      if (kind !== 'discipline') return orig.apply(this, arguments);
      const st = window.SweepGame && SweepGame.state && SweepGame.state(); const p = (st && st.profile) || {};
      const s = (p.streak && p.streak.current) || 0, v = discScore(), nm = window.SweepName && SweepName.shown() && SweepName.first();
      return { label: t('dCard'), eyebrow: new Date().toLocaleDateString(L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA', { month: 'long', year: 'numeric' }), big: v == null ? '—' : v + (L === 'en' ? '%' : '\u202f%'), tone: 'pos', sub: null,
        stats: [[t('streak'), String(s)], [t('score'), v == null ? '—' : v + (L === 'en' ? '%' : '\u202f%')], [t('swept'), swept == null ? '—' : String(swept)]], demo: false, chart: null, bars: null, mark: true, who: nm || null, whoAt: 'eyebrow', cap: t('capD')(s, v == null ? 0 : v) };
    };
    w.__disc = true; w.__congrats = true; w.__name = true; w.__stats = true; w.__po = true; window.shData = w;
  })(0);
  (function wrapR(n) {
    if (typeof window.shRender !== 'function' || !window.shRender.__focus) { if (n < 150) setTimeout(() => wrapR(n + 1), 150); return; }
    if (window.shRender.__disc) return;
    const orig = window.shRender;
    const w = async function () {
      const out = await orig.apply(this, arguments);
      try {
        if (SH.kind === 'discipline' || SH.kind === 'swept') document.querySelectorAll('#shPanel .sh-tg [data-sh]').forEach((i) => { const l = i.closest('label'); if (l) l.remove(); });   // no amount, no firm on these cards: no switch for them
        const alt = SH.alt ? SH.alt[0] : 'stats';   // the card asked for (or Stats, from the Stats page)
        if (!SH.alt && SH.kind !== 'discipline' && SH.kind !== 'stats') return out;
        const head = document.querySelector('#shPanel .sh-head'); if (!head || document.querySelector('#shPanel .nav-dk')) return out;
        head.insertAdjacentHTML('afterend', `<div class="seg nav-dk" data-noi18n><button type="button" class="${SH.kind === 'discipline' ? 'on' : ''}" data-dk="discipline">${t('kDisc')}</button><button type="button" class="${SH.kind !== 'discipline' ? 'on' : ''}" data-dk="${alt}">${esc(t('kAlt')[alt] || t('kStats'))}</button></div>`);
      } catch (e) { /* never blocks */ }
      return out;
    };
    w.__disc = true; w.__focus = true; w.__stl = true; w.__name = true; w.__link = true; w.__po = true; window.shRender = w;
  })(0);
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-dk]'); if (!b) return; const k = b.dataset.dk; SH.kind = k; SH.id = k !== 'discipline' && SH.alt ? SH.alt[1] : 'view'; SH.blob = null; shRender(); });
  // brief 02 part 12: the Discipline card first, everywhere (payout, payouts, week, day, trade…): the card asked for is one tap away
  (function wrapO(n) {
    if (typeof window.openShare !== 'function') { if (n < 150) setTimeout(() => wrapO(n + 1), 150); return; }
    if (window.openShare.__disc) return;
    const orig = window.openShare;
    const w = async function (kind, id) {
      if (kind === 'discipline' || kind === 'swept') { SH.alt = null; return orig.apply(this, arguments); }
      SH.alt = [kind, id];
      await loadSwept();
      const out = await orig.call(this, 'discipline', 'view');
      return out;
    };
    w.__disc = true; window.openShare = w;
  })(0);
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('.nav-shstats')) { e.stopImmediatePropagation(); loadSwept().then(() => openShare('discipline', 'view')); } }, true);   // discipline first

  /* 19. end of the Pro trial: from day 50 (10 days left) until dismissed, the paid features the trader really uses
     (api/billing/me pro_used: the same list as the reminders, billing-core.php sb_pro_used); nothing used → no card */
  const trialKey = (tr) => 'sw.trialCard.' + String(tr.ends_at).slice(0, 10);
  function trialHtml() {
    const st = typeof BILL !== 'undefined' && BILL.on && BILL.st, tr = st && st.trial;
    if (!tr || tr.days_left > 10 || tr.days_left <= 0 || st.subscription || !(st.pro_used || []).length || LS(trialKey(tr)) === '1') return '';
    const U = t('u'), pl = (n, w) => n + ' ' + U[w][(L === 'fr' ? n > 1 : n !== 1) ? 1 : 0];
    const line = (i) => i.k === 'accounts' ? U.accounts.replace('{n}', pl(i.n, 'acc')).replace('{f}', pl(i.free, 'act'))
      : i.k === 'money' ? U.money.replace('{x}', [i.payouts ? pl(i.payouts, 'po') : '', i.expenses ? pl(i.expenses, 'ex') : ''].filter(Boolean).join(', '))
      : i.k === 'shots' ? U.shots.replace('{n}', pl(i.n, 'tr'))
      : i.k === 'history' ? U.history.replace('{n}', pl(i.n, 'tr')).replace('{d}', i.days)
      : i.k === 'ai' ? U.ai : '';
    const head = tr.days_left === 1 ? t('trialH1') : t('trialH').replace('{n}', tr.days_left);
    return `<section class="surface nav-trial" data-noi18n data-ends="${esc2(String(tr.ends_at).slice(0, 10))}"><div class="nav-trial-t"><b>${esc2(head)}</b><span>${esc2(t('trialU'))}</span>`
      + `<ul>${st.pro_used.map((i) => `<li data-k="${esc2(i.k)}">${esc2(line(i))}</li>`).join('')}</ul><small>${esc2(t('trialK'))}</small></div>`
      + `<a class="btn primary sm" href="#plan" data-trial-ok>${esc2(t('trialB'))}</a><button type="button" class="nav-trial-x" data-trial-x aria-label="✕">✕</button></section>`;
  }
  window.SweepTrialCard = trialHtml;   // drawn with the dashboard (composeToday): nothing lands above the page afterwards
  function trialCard() {   // (the plan state arrived after the dashboard was drawn: put it in place once)
    const main = document.getElementById('main'), host = main && main.querySelector('.nav-dash .d-today');
    if (!host || main.querySelector('.nav-trial')) return;
    const html = trialHtml(); if (html) host.insertAdjacentHTML('afterend', html);
  }
  document.addEventListener('click', (e) => {
    const x = e.target.closest && e.target.closest('[data-trial-x]'); if (!x) return;
    const card = x.closest('.nav-trial'), tr = typeof BILL !== 'undefined' && BILL.st && BILL.st.trial;
    if (tr) LS(trialKey(tr), '1'); if (card) card.remove();
  });

  let grpFor = null;
  function copiesFromGroup() {
    if (typeof TK === 'undefined' || !TK || TK.id || !document.querySelector('#tkSlide.open') || !TK.copyTo) return;
    if (grpFor === TK.account) return; grpFor = TK.account;
    const a = getDoc('accounts', TK.account); if (!a || !a.group_id) return;
    // a group with a master account (brief « avance concurrentielle », step 2): its followers only, from the master only
    const lead = window.SweepCopy && SweepCopy.leadOf ? SweepCopy.leadOf(a.id) : null;
    if (lead) { TK.copyTo = new Set(SweepCopy.targets(a.id)); if (typeof tkRefresh === 'function') tkRefresh({ panel: true }); return; }
    const sib = (S.accounts || []).filter((x) => x.group_id === a.group_id && x.id !== a.id && x.status !== 'archived'); if (!sib.length) return;
    sib.forEach((x) => TK.copyTo.add(x.id)); if (typeof tkRefresh === 'function') tkRefresh({ panel: true });
  }
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-act="tk-cancel"], #tkSlide .tk-x')) grpFor = null; }, true);

  /* (Delivery 1, point 4) without Sweep AI in the plan: say it in one line on the manual form */
  function noAiLine() {
    const tk = document.querySelector('#tkSlide.open .nav-tk-alt'); if (!tk || document.body.classList.contains('ai-on') || tk.querySelector('.nav-noai') || (typeof TK !== 'undefined' && TK && TK.id)) return;   // under the two buttons, not in the header
    tk.insertAdjacentHTML('beforeend', `<small class="nav-noai" data-noi18n>${t('noAi')}</small>`);
  }

  new window.SweepMO(() => { [rows, accountsExtras, filterPill, platformMark, discChip, trialCard, noAiLine, copiesFromGroup].forEach((f) => { try { f(); } catch (e) { if (!f.__warned) { f.__warned = true; console.warn('Sweep:', f.name, e && e.message); } } }); /* each on its own: one failing never stops the others */ }).observe(document.body, { childList: true, subtree: true });
})();

/* routine: the whole step is the button (the small action inside stays as the visible cue) */
document.addEventListener('click', (e) => {
  const st = e.target.closest && e.target.closest('#main .nav-rt-s'); if (!st || e.target.closest('button, a')) return;
  const b = st.querySelector('.nav-rt-sa [data-rt]'); if (b) b.click();
});

/* ───────────── no « reload » look: a background sync redraws the page only if the data really changed ─────────────
 * The app re-fetches its data every minute and when you come back to it (phone). It redrew the whole page whenever
 * its quick fingerprint differed — and that fingerprint differed after any local save (dates set by the server),
 * so the page was often redrawn with the same content: charts, lists and cards flashed as if reloading.
 * Now the content itself is compared (server-only date fields ignored): same content, no redraw. */
(function () {
  'use strict';
  (function wrap(n) {
    if (typeof window.syncNow !== 'function' || typeof window.render !== 'function') { if (n < 100) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.syncNow.__quiet) return;
    const orig = window.syncNow;
    const skip = new Set(['updated_at', 'created_at', 'synced_at', '_v', 'v']);
    const fp = () => { try { return JSON.stringify((typeof COLS !== 'undefined' ? COLS : ['trades', 'accounts', 'firms', 'payouts', 'expenses', 'journals']).map((c) => S[c] || []).concat([S.settings || {}]), (k, v) => (skip.has(k) ? undefined : v)); } catch (e) { return String(Math.random()); } };
    let quiet = false;
    const appRender = window.render;
    const r = function () { if (quiet) return; return appRender.apply(this, arguments); };
    Object.keys(appRender).forEach((k) => { r[k] = appRender[k]; });
    window.render = r;
    const w = async function (opts) {
      const before = fp(); quiet = true;
      let out;
      try { out = await orig.apply(this, arguments); } finally { quiet = false; }
      if ((opts && opts.manual) || fp() !== before) window.render();   // only a real change is drawn
      return out;
    };
    w.__quiet = true; window.syncNow = w;
  })(0);
})();

/* ───────────── Accounts: your own order, « Add account » on top ─────────────
 * Computer: drag a row up or down (a grip shows on hover). Phone: « Reorder » shows a handle on the left of each
 * row to slide it up or down, « Done » to finish. The order is saved on the accounts and used everywhere
 * (Today, lists, forms). « Add account » moves to the top of the list, in blue, like « Add a trade ». */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: ['Reorder', 'Done', 'Drag to reorder'], fr: ['Modifier l’ordre', 'Terminé', 'Glisser pour réordonner'], es: ['Cambiar el orden', 'Listo', 'Arrastra para ordenar'] }[L] || ['Reorder', 'Done', 'Drag to reorder'];
  const GRIP = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="6" r="1.5"/><circle cx="15" cy="6" r="1.5"/><circle cx="9" cy="12" r="1.5"/><circle cx="15" cy="12" r="1.5"/><circle cx="9" cy="18" r="1.5"/><circle cx="15" cy="18" r="1.5"/></svg>';
  // the saved order applies everywhere
  function sortAccounts() {
    if (typeof S === 'undefined' || !Array.isArray(S.accounts) || !S.accounts.some((a) => a.sort != null)) return;
    const idx = new Map(S.accounts.map((a, i) => [a, i]));
    S.accounts.sort((a, b) => ((a.sort ?? 1e6) - (b.sort ?? 1e6)) || (idx.get(a) - idx.get(b)));
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__accsort) {
    const w = function () { try { sortAccounts(); } catch (e) { /* never blocks */ } const out = appRender.apply(this, arguments); try { decorate(); } catch (e) { /* never blocks */ } return out; };
    Object.keys(appRender).forEach((k) => { w[k] = appRender[k]; });
    w.__accsort = true; window.render = w;
  }
  const idOf = (tr) => decodeURIComponent((tr.dataset.href || '').replace('#account/', ''));
  function save(tbody) {   // every group of the page, in the order shown (Live, Funded, Evaluations, Personal): one order for all
    const page = (tbody && tbody.closest('.surface')) || document.getElementById('main');
    const ids = [...page.querySelectorAll('table.acct-tbl tbody tr[data-href^="#account/"]')].map(idOf);
    ids.forEach((id, i) => { const a = getDoc('accounts', id); if (a && a.sort !== i) editDoc('accounts', id, (d) => { d.sort = i; }); });
    sortAccounts();
  }
  let editing = false;
  function decorate() {
    if (!/^#accounts$/.test(location.hash || '')) { editing = false; return; }
    const main = document.getElementById('main'); if (!main) return;
    const tb = main.querySelector('table.acct-tbl tbody'); if (!tb) return;
    const surf = tb.closest('.surface');
    const bodies = [...((surf || main).querySelectorAll('table.acct-tbl tbody'))];   // each group has its own table (10: not only the first one)
    // « Add account » on top, in blue
    const add = surf && (surf.querySelector(':scope > [data-act="acct-add"][data-v="1"]') || null);   // (once moved into the top row it is no longer a direct child)
    const sx = surf && surf.querySelector(':scope > .scroll-x');
    if (add && sx && add.nextElementSibling !== sx) { sx.before(add); add.classList.add('nav-addrow'); }
    // the add-account form (it replaces the « + » row) opens at the top, above the list
    const af0 = surf && surf.querySelector('form[data-form="account"]');
    if (af0 && sx) { let blk = af0; while (blk.parentElement && blk.parentElement !== surf) blk = blk.parentElement; if (blk.parentElement === surf && (blk.compareDocumentPosition(sx) & 4) === 0) { sx.before(blk); blk.classList.add('nav-acc-form'); } }
    if (af0 && !af0.closest('.onb') && !af0.querySelector('.nav-cancel')) af0.insertAdjacentHTML('afterbegin', `<button type="button" class="nav-cancel" data-act="acct-add" data-v="0" data-noi18n aria-label="✕">${({ en: 'Cancel', fr: 'Annuler', es: 'Cancelar' })[(typeof LANG !== 'undefined' && LANG) || 'en']} ✕</button>`);
    // the reorder control (phone) and the grips
    if (surf && !surf.querySelector('.nav-ord-b')) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'link nav-ord-b'; b.setAttribute('data-noi18n', ''); b.textContent = T[0];
      b.addEventListener('click', () => { editing = !editing; b.textContent = editing ? T[1] : T[0]; surf.classList.toggle('nav-ord-on', editing); });
      const addr = surf.querySelector(':scope > .nav-addrow');
      if (addr) { const row = document.createElement('div'); row.className = 'nav-acc-top'; addr.before(row); row.append(addr, b); } else surf.firstElementChild.after(b);
    }
    if (surf) surf.classList.toggle('nav-ord-on', editing);
    const top = surf && surf.querySelector(':scope > .nav-acc-top'), af = main.querySelector('form[data-form="account"]');
    if (top && af && !af.closest('.nav-dlg, .onb')) { const blk = af.closest('#main > *') === surf ? af : (af.closest('.surface') || af); if (blk !== surf && top.nextElementSibling !== blk) { top.after(blk); blk.classList.add('nav-acc-form'); blk.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } }
    bodies.forEach((one) => one.querySelectorAll('tr[data-href^="#account/"]').forEach((tr) => {
      if (tr.dataset.ord) return; tr.dataset.ord = '1';
      const td = tr.firstElementChild; if (!td) return;
      td.insertAdjacentHTML('afterbegin', `<span class="nav-grip" aria-label="${T[2]}" title="${T[2]}" data-noi18n>${GRIP}</span>`);
      if (!window.SW_MQ.matches) tr.draggable = true;
    }));
  }
  // whatever redraws the list (a render, a quiet sync), the top row and the grips are in place before the browser paints:
  // a native observer runs right after the change, so the list never shows a frame without them and then jumps (CLS)
  { const m0 = document.getElementById('main');
    if (m0) new MutationObserver(() => { if (/^#accounts$/.test(location.hash || '')) { const s0 = m0.querySelector('table.acct-tbl tbody'); const sf = s0 && s0.closest('.surface'); if (sf && (!sf.querySelector('.nav-acc-top') || sf.querySelector('tr[data-href^="#account/"]:not([data-ord])'))) { try { decorate(); } catch (e) { /* never blocks */ } } } }).observe(m0, { childList: true, subtree: true }); }
  // computer: drag and drop
  let dragRow = null;
  document.addEventListener('dragstart', (e) => { const tr = e.target.closest && e.target.closest('#main table.acct-tbl tr[data-href^="#account/"]'); if (!tr) return; dragRow = tr; tr.classList.add('nav-drag'); e.dataTransfer.effectAllowed = 'move'; try { e.dataTransfer.setData('text/plain', idOf(tr)); } catch (x) { /* some browsers */ } });
  document.addEventListener('dragover', (e) => {
    if (!dragRow) return; const over = e.target.closest && e.target.closest('#main table.acct-tbl tr[data-href^="#account/"]'); if (!over || over === dragRow || over.parentElement !== dragRow.parentElement) return;   // within its own group only
    e.preventDefault(); const r = over.getBoundingClientRect(); const after = e.clientY > r.top + r.height / 2;
    if (after) over.after(dragRow); else over.before(dragRow);
  });
  document.addEventListener('drop', (e) => { if (dragRow) e.preventDefault(); });
  document.addEventListener('dragend', () => { if (!dragRow) return; const tb = dragRow.parentElement; dragRow.classList.remove('nav-drag'); dragRow = null; save(tb); });
  // phone: slide a row with its handle
  let tRow = null;
  document.addEventListener('touchstart', (e) => { const g = e.target.closest && e.target.closest('.nav-ord-on .nav-grip'); if (!g) return; tRow = g.closest('tr'); tRow.classList.add('nav-drag'); }, { passive: true });
  document.addEventListener('touchmove', (e) => {
    if (!tRow) return; e.preventDefault();
    const y = e.touches[0].clientY, rows = [...tRow.parentElement.querySelectorAll('tr[data-href^="#account/"]')];
    for (const r of rows) { if (r === tRow) continue; const b = r.getBoundingClientRect(); if (y > b.top && y < b.bottom) { if (y > b.top + b.height / 2) r.after(tRow); else r.before(tRow); break; } }
  }, { passive: false });
  document.addEventListener('touchend', () => { if (!tRow) return; const tb = tRow.parentElement; tRow.classList.remove('nav-drag'); tRow = null; save(tb); });
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('.nav-grip')) { e.preventDefault(); e.stopPropagation(); } }, true);
})();

/* ───────────── « Day swept » share card: show it, and invite the people who see it ─────────────
 * The Share button of the « Day swept » moment opens a card made to spread: « I completed my discipline today »,
 * 3/3, « Have you completed yours? », streak · discipline · days swept this month, the trader's name, makeitsweep.com.
 * No dollars. The caption carries the same invitation. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { label: 'Day complete', eb: 'I completed my discipline today', sub: 'Have you completed yours?', streak: 'Streak', disc: 'Discipline', swept: 'Days swept', cap: (s) => `I completed my discipline today: plan, execution, review ✅${s ? ` ${s}-day streak.` : ''} Have you completed yours? makeitsweep.com` },
    fr: { label: 'Journée complète', eb: 'J’ai complété ma discipline aujourd’hui', sub: 'Et toi, as-tu complété la tienne ?', streak: 'Série', disc: 'Discipline', swept: 'Journées balayées', cap: (s) => `J’ai complété ma discipline aujourd’hui : plan, exécution, revue ✅${s ? ` ${s} jours de suite.` : ''} Et toi, as-tu complété la tienne ? makeitsweep.com` },
    es: { label: 'Día completado', eb: 'Hoy completé mi disciplina', sub: '¿Y tú, completaste la tuya?', streak: 'Racha', disc: 'Disciplina', swept: 'Días barridos', cap: (s) => `Hoy completé mi disciplina: plan, ejecución, revisión ✅${s ? ` ${s} días seguidos.` : ''} ¿Y tú, completaste la tuya? makeitsweep.com` } };
  const t = (k) => (T[L] || T.en)[k];
  let swept = null, disc = null;
  async function load() {
    try {
      const d = typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10);
      const r = await fetch(`api/game/history?from=${d.slice(0, 8)}01&to=${d}`, { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } });
      const j = await r.json(); const arr = Array.isArray(j) ? j : (j.days || j.history || j.items || []);
      swept = Math.max(1, arr.filter((x) => x && (x.swept || x.is_swept)).length);
    } catch (e) { swept = null; }
    try { const dd = window.shData && shData('discipline', 'view'); const s = dd && (dd.stats || []).find((x) => x[0] === (dd.stats[1] || [])[0]); disc = dd ? dd.big : null; } catch (e) { disc = null; }
  }
  (function wrap(n) {
    if (typeof window.shData !== 'function' || !window.shData.__disc) { if (n < 150) setTimeout(() => wrap(n + 1), 150); return; }
    if (window.shData.__swept) return;
    const orig = window.shData;
    const w = function (kind) {
      if (kind !== 'swept') return orig.apply(this, arguments);
      const st = window.SweepGame && SweepGame.state && SweepGame.state(); const p = (st && st.profile) || {};
      const s = (p.streak && p.streak.current) || 0, nm = window.SweepName && SweepName.shown() && SweepName.first();
      return { label: t('label'), eyebrow: t('eb'), big: '3/3 ✓', tone: 'pos', sub: t('sub'),
        stats: [[t('streak'), String(s)], [t('disc'), disc || '—'], [t('swept'), swept == null ? '—' : String(swept)]],
        demo: false, chart: null, bars: null, mark: true, who: nm || null, whoAt: 'eyebrow', cap: t('cap')(s) };
    };
    w.__swept = true; w.__disc = true; w.__congrats = true; w.__name = true; w.__stats = true; w.__po = true; window.shData = w;
  })(0);
  // the « Day swept » moment: its Share button opens this card
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.g-sweep [data-g="share"][data-k="sweep"]'); if (!b) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const close = b.closest('.g-sweep').querySelector('[data-g="sw-close"]');
    load().then(() => { if (close) close.click(); setTimeout(() => openShare('swept', 'today'), 320); });
  }, true);
  window.SweepSweptShare = () => load().then(() => openShare('swept', 'today'));
})();

/* ───────────── Payouts & expenses: « + Add payout » / « + Add expense » like « Add a trade » ─────────────
 * The add forms stay folded behind a small blue « + » row; one tap opens the section (Paid / Requested and the
 * details). Saving folds it back. Editing an existing entry shows it open. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: ['Add payout', 'Add expense'], fr: ['Ajouter un payout', 'Ajouter une dépense'], es: ['Añadir un payout', 'Añadir un gasto'] }[L] || ['Add payout', 'Add expense'];
  const open = new Set();
  function pass() {
    if (!/^#payouts/.test(location.hash || '')) { open.clear(); return; }
    document.querySelectorAll('#main form[data-form="payout"], #main form[data-form="expense"]').forEach((f) => {
      const box = f.closest('.pz-add'); if (!box) return;
      if (f.closest('.mny')) {   // « My money » opens its forms itself (« + Add »): only the round ✕ to close them
        if (!f.dataset.id && !f.querySelector('.nav-cancel')) f.insertAdjacentHTML('afterbegin', `<button type="button" class="nav-cancel" data-mny="cancel" data-noi18n aria-label="${({ en: 'Cancel', fr: 'Annuler', es: 'Cancelar' })[L]}">${({ en: 'Cancel', fr: 'Annuler', es: 'Cancelar' })[L]}</button>`);
        return;
      }
      const k = f.dataset.form, editing = !!f.dataset.id;
      let b = box.previousElementSibling && box.previousElementSibling.classList.contains('nav-pz-b') ? box.previousElementSibling : null;
      if (!b) { b = document.createElement('button'); b.type = 'button'; b.className = 'add-row nav-addrow nav-pz-b'; b.setAttribute('data-noi18n', ''); b.dataset.k = k; b.innerHTML = `<span class="add-ic">+</span>${k === 'payout' ? T[0] : T[1]}`; box.before(b); }
      // when there is a list under it, the row and the form go inside that list's card, on top
      const list = (() => { let n = box.nextElementSibling; while (n && (n.classList.contains('nav-pz-b') || n.tagName === 'SCRIPT')) n = n.nextElementSibling; return n && n.classList.contains('surface') && !n.classList.contains('pz-add') ? n : null; })();
      if (list && b.parentElement !== list) { list.prepend(box); list.prepend(b); list.classList.add('nav-pz-list'); }
      if (!list && !box.parentElement.classList.contains('nav-pz-list')) b.classList.add('nav-pz-solo');
      const show = editing || open.has(k);
      if (!editing && !f.querySelector('.nav-cancel')) f.insertAdjacentHTML('afterbegin', `<button type="button" class="nav-cancel" data-pz-cancel="${k}" data-noi18n>${({ en: 'Cancel', fr: 'Annuler', es: 'Cancelar' })[L] || 'Cancel'} ✕</button>`);
      box.classList.toggle('nav-pz-hidden', !show); b.hidden = show;
    });
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.nav-pz-b'); if (!b) return;
    open.add(b.dataset.k); pass();
    const box = b.nextElementSibling; if (box) { box.classList.add('nav-pz-in'); setTimeout(() => { const i = box.querySelector('input[name="amount"], input'); if (i) i.focus(); }, 60); }
  });
  document.addEventListener('click', (e) => { const c = e.target.closest && e.target.closest('[data-pz-cancel]'); if (c) { e.preventDefault(); open.delete(c.dataset.pzCancel); pass(); } });
  document.addEventListener('submit', (e) => { const f = e.target; if (f.matches && f.matches('form[data-form="payout"], form[data-form="expense"]') && !f.dataset.id) setTimeout(() => { open.delete(f.dataset.form); pass(); }, 400); });
  new window.SweepMO(() => { try { pass(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();


/* avatar and menu header: the trader's initial and full name (not the generated username);
   Stats: no rank card on top (it lives in Progression), « From 5 trades » instead of « ∞ » under 5 trades; Trends message translated */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const TREND = { fr: 'Pas encore assez de données. Les stats apparaissent dès 5 trades dans chaque groupe comparé.', es: 'Aún no hay suficientes datos. Las estadísticas aparecen con al menos 5 operaciones en cada grupo comparado.' }[L];
  function pass() {
    const me = (typeof S !== 'undefined' && S.me) || {}; const full = [me.first_name, me.last_name].filter(Boolean).join(' ');
    if (full) {
      const ini = (me.first_name || full)[0].toUpperCase();
      document.querySelectorAll('aside.side .who, .mhdr .who, .nav-av, [data-act="menu"] .av, .who.nav-dot').forEach((w) => { const t = w.querySelector('b, span, i') || w; if (t.children.length === 0 && t.textContent.trim().length <= 2 && t.textContent.trim() !== ini) t.textContent = ini; });
      document.querySelectorAll('#navMenu .nav-m-name, .menu-pop .mp-name, .menu-pop header b').forEach((n) => { if (n.textContent !== full) n.textContent = full; });
    }
    if (/^#analytics/.test(location.hash || '')) {
      const ins = document.querySelector('#main #gIns'); if (ins && !ins.hidden) ins.hidden = true;
    }
    // only Stats shows that message
    if (TREND && /^#analytics/.test(location.hash || '')) document.querySelectorAll('#main p, #main .muted, #main div').forEach((p) => { if (p.children.length === 0 && /^Not enough data yet\./.test(p.textContent.trim())) p.textContent = TREND; });
  }
  new window.SweepMO(() => { try { pass(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();

(function () {
  'use strict';
  new window.SweepMO(() => {
    const few = /^#(trades|journal|calendar)/.test(location.hash || '#') && typeof S !== 'undefined' && (S.trades || []).filter((t) => !t.demo).length < 10;
    document.body.classList.toggle('nav-few-trades', !!few);
  }).observe(document.body, { childList: true, subtree: true });
})();

/* C12 · before the first account, the bottom « + » says why the account comes first */
document.addEventListener('click', (e) => {
  const b = e.target.closest && e.target.closest('.bottomnav .plus, aside.side .new'); if (!b) return;
  if (typeof S === 'undefined' || (S.accounts || []).some((a) => a.status !== 'archived')) return;
  setTimeout(() => { if (typeof toast === 'function') toast(({ en: 'Add your account first: every trade belongs to one.', fr: 'Ajoute d’abord ton compte : chaque trade lui appartient.', es: 'Añade primero tu cuenta: cada operación pertenece a una.' })[(typeof LANG !== 'undefined' && LANG) || 'en']); }, 250);
}, true);

/* B9 · after the 17:00 ET close (or on a day without a session), the Plan step prepares the next session */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const HOUR_ET = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: '2-digit', hourCycle: 'h23' });   // one formatter, not one per call
  /** the session the Plan prepares: from 17:00 (the close) to 18:00 (the reopening) the day is over → the next one; from 18:00 the new day has started
   *  (todayStr is already that day); weekends → Monday. null when it is simply today's plan, already done or not. */
  window.SweepNextSession = function () {
    const st = window.SweepGame && SweepGame.state && SweepGame.state(); const d = st && st.today;
    const h = +HOUR_ET.format(new Date()) % 24, today = typeof todayStr === 'function' ? todayStr() : null; if (!today) return null;
    const n = new Date(today + 'T12:00:00');
    if (h >= 17 && h < 18) n.setDate(n.getDate() + 1);
    while (n.getDay() === 0 || n.getDay() === 6) n.setDate(n.getDate() + 1);
    const target = `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}-${String(n.getDate()).padStart(2, '0')}`;
    if (d && d.rings && d.rings.plan >= 100 && target === (d.day || today)) return null;   // already planned
    return h >= 17 || target !== today || !d || !d.market ? target : null;
  };
  function tagNext() {
    // never on the loading card: its steps have no title, so the tag landed next to the step, as a 4th cell of the grid (layout shift)
    const nx = window.SweepNextSession(); const s1 = document.querySelector('#main .nav-rt-s:first-child'); if (!s1 || s1.classList.contains('sk')) return;
    let tag = s1.querySelector('.nav-next-ses');
    if (!nx) { if (tag) tag.remove(); return; }
    const txt = ({ en: 'For the next session', fr: 'Pour la prochaine séance', es: 'Para la próxima sesión' })[L];
    if (!tag) { tag = document.createElement('small'); tag.className = 'nav-next-ses'; tag.setAttribute('data-noi18n', ''); const h = s1.querySelector('h3, b'); (h || s1).after(tag); }
    if (tag.textContent !== txt) tag.textContent = txt;
  }
  new window.SweepMO(tagNext).observe(document.body, { childList: true, subtree: true });
  // (28 Oct., the CI) also in the same pass as the page's render, before it is painted: added after, it pushed « Now » down 25 px
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__nextSes) {
    const w = function () { const out = appRender.apply(this, arguments); try { tagNext(); } catch (e) { /* never blocks */ } return out; };
    w.__nextSes = true; window.render = w;
  }
})();

/* D15 · the discipline checklist on the manual form, right above « Save »: 3 questions, « See more » for the rest */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const W = ({ en: ['Yes', 'No', 'N/A', 'See more', 'Checklist', 'Fees and review are on the next page.'], fr: ['Oui', 'Non', 'N/A', 'Voir plus', 'Checklist', 'Les frais et le bilan sont sur la page suivante.'],
    es: ['Sí', 'No', 'N/A', 'Ver más', 'Checklist', 'Las comisiones y la revisión están en la página siguiente.'] })[L];
  let ans = {}, pending = null;   // pending: the answers of the trade being saved (and its copies)
  function qs() { return ((typeof S !== 'undefined' && S.settings && S.settings.questions) || []).filter((q) => q.active !== false); }
  // edge T7: the setup's criteria first (they replace the 3 questions), the question that separates winners from losers, the acquired ones under « See more »
  const order = () => (window.SweepQs ? SweepQs.order(typeof TK !== 'undefined' && TK ? TK.setup : '') : { list: qs(), shown: 3 });
  function ckFill(box) {
    const O = order(), list = O.list, setup = typeof TK !== 'undefined' && TK ? TK.setup : '';
    box.classList.remove('all');
    box.innerHTML = `<b class="nav-ck-t" data-noi18n>${W[4]}</b>` + list.map((q, i) => `<div class="nav-ck-q ${i >= O.shown && !ans[q.id] ? 'more' : ''}" data-q="${q.id}"><span data-noi18n>${window.SweepQs ? SweepQs.label(q) : (q.text || q.q || q.label || q.id).replace(/[<>&]/g, '')}</span><div class="nav-ck-b" data-noi18n>${['y', 'n', 'na'].map((v, k) => `<button type="button" data-v="${v}" class="${ans[q.id] === v ? 'on' : ''}">${W[k]}</button>`).join('')}</div></div>`).join('')
      + (list.length > O.shown ? `<button type="button" class="link nav-ck-more" data-noi18n>${W[3]} ›</button>` : '') + (window.SweepQs ? `<div class="nav-ck-add" data-noi18n>${SweepQs.addLink(setup)}</div>` : '');
  }
  window.SweepCkFill = () => { const b = document.querySelector('#tkSlide.open .nav-ck'); if (b) ckFill(b); };
  document.addEventListener('sweep:qs', () => setTimeout(() => window.SweepCkFill(), 120));
  new window.SweepMO(() => {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || (typeof TK !== 'undefined' && TK && TK.id)) { if (!tk) { ans = {}; pending = null; } return; }
    if (tk.querySelector('.nav-ck')) return;
    const save = tk.querySelector('[data-act="tk-save"]'); const list = order().list; if (!save || !list.length) return;
    const box = document.createElement('div'); box.className = 'nav-ck';
    ckFill(box);
    (save.closest('.tk-foot, .tk-actions') || save).before(box);
    const hint = tk.querySelector('#tkErr') && tk.querySelector('#tkErr').previousElementSibling;   // « …checklist… on the next page »: it is here now
    if (hint && hint.classList.contains('help')) { hint.textContent = W[5]; hint.setAttribute('data-noi18n', ''); }
  }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.nav-ck-b button');
    if (b) { const q = b.closest('.nav-ck-q'); q.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b)); ans[q.dataset.q] = b.dataset.v; return; }
    const m = e.target.closest && e.target.closest('.nav-ck-more'); if (m) { m.closest('.nav-ck').classList.add('all'); m.remove(); return; }
    if (e.target.closest && e.target.closest('#tkSlide [data-act="tk-save"]') && !(typeof TK !== 'undefined' && TK && TK.id)) pending = Object.keys(ans).length ? Object.assign({}, ans) : null;
  }, true);
  document.addEventListener('keydown', (e) => {   // ⌘/Ctrl + Enter saves too
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && document.querySelector('#tkSlide.open') && !(typeof TK !== 'undefined' && TK && TK.id)) pending = Object.keys(ans).length ? Object.assign({}, ans) : null;
  }, true);
  // the answers go into the trade as it is saved, copies included (before: applied 900 ms later, and lost after a refused save,
  // e.g. « Add the entry price »: the score stayed empty); « Step 2 » shows them at once. Kept until the form closes.
  (function wrap(n) {
    if (typeof window.put !== 'function') { if (n < 60) setTimeout(() => wrap(n + 1), 100); return; }
    const orig = window.put;
    const w = function (col, doc) {
      if (col === 'trades' && pending && doc && typeof doc === 'object' && !doc.demo && document.querySelector('#tkSlide.open') && !(typeof getDoc === 'function' && getDoc('trades', doc.id)))
        doc.discipline = Object.assign({}, doc.discipline || {}, pending);
      return orig.apply(this, arguments);
    };
    Object.keys(orig).forEach((k) => { w[k] = orig[k]; });
    window.put = w;
  })(0);
})();

/* Edge T1 · the setup in one tap, on the quick sheet and the manual form: the day's plan setups first,
 * then the trader's own (Settings, then the most used on their trades); common setups while they have fewer than 3 */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const W = ['Setup'];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const low = (s) => String(s || '').trim().toLowerCase();
  function list(day) {
    const out = [], seen = new Set();
    const add = (s) => { const v = String(s || '').trim().slice(0, 40); if (v && !seen.has(low(v))) { seen.add(low(v)); out.push(v); } };
    const j = typeof getDoc === 'function' ? getDoc('journals', day) : null;
    ((j && j.pre && j.pre.setups) || []).forEach(add);
    ((typeof S !== 'undefined' && S.settings && S.settings.setups) || []).forEach(add);
    const n = {}; ((typeof S !== 'undefined' && S.trades) || []).filter((t) => !t.demo && t.setup).slice(-80).forEach((t) => { n[t.setup] = (n[t.setup] || 0) + 1; });
    Object.entries(n).sort((a, b) => b[1] - a[1]).forEach((x) => add(x[0]));
    if (out.length < 3) ((window.SweepGame && SweepGame.suggestedSetups) || []).forEach(add);
    return out.slice(0, 12);
  }
  // (2 Nov., analyse débutant C6) a trader of the 90-day gameplan, before mission 8 (« Read the setup »): the one setup it teaches, the
  // Sweep Setup, and « + Other » for the rest — not « Liquidity sweep », « Break & retest »… on his first days
  const OTHER = { en: '+ Other', fr: '+ Autre', es: '+ Otro' };
  const gpEarly = () => { try { const st = window.SweepGP && SweepGP.state && SweepGP.state(); return !!(st && st.started && st.access && !(st.done && st.done[8])); } catch (e) { return false; } };
  function html(day, cur, all) {
    const few = !all && gpEarly();
    const l = few ? ['Sweep Setup'] : list(day); if (cur && !l.some((x) => low(x) === low(cur))) l.unshift(cur);
    // (27 Oct.) its « i », and each name's meaning (a long press, or the title on a computer): the names stay the traders' English
    const what = (x) => (window.SweepSetupWhat ? SweepSetupWhat(x) : '');
    return `<div class="tk-f nav-sp" data-noi18n data-day="${esc2(day || '')}" data-cur="${esc2(cur || '')}"><span>${W[0]}${window.SweepTerm ? SweepTerm('setup') : ''}</span><div class="nav-sp-row">${l.map((x) => `<button type="button" class="chip ${low(x) === low(cur) ? 'on' : ''}" data-sp="${esc2(x)}"${what(x) ? ` title="${esc2(what(x))}"` : ''}>${esc2(x)}</button>`).join('')}${few ? `<button type="button" class="chip nav-more nav-sp-other" data-sp-other>${esc2(OTHER[L] || OTHER.en)}</button>` : ''}</div></div>`;
  }
  /** a tap: one setup at most, a second tap clears it; returns the new value */
  function tap(b, cur) {
    const v = low(b.dataset.sp) === low(cur) ? '' : b.dataset.sp;
    b.closest('.nav-sp-row').querySelectorAll('[data-sp]').forEach((x) => x.classList.toggle('on', !!v && x === b));
    const w = b.closest('.nav-sp'); if (w) w.dataset.cur = v;
    return v;
  }
  /** a setup used on a trade joins the trader's list (as when it is picked in the plan) */
  function keep(v) {
    v = String(v || '').trim().slice(0, 40); if (!v || typeof editDoc !== 'function') return;
    if (((S.settings && S.settings.setups) || []).some((x) => low(x) === low(v))) return;
    editDoc('settings', 'settings', (r) => { r.setups = r.setups || []; if (!r.setups.some((x) => low(x) === low(v))) r.setups.push(v); });
  }
  document.addEventListener('click', (e) => {   // « + Other »: the whole list, in place
    const b = e.target.closest && e.target.closest('[data-sp-other]'); if (!b) return;
    const w = b.closest('.nav-sp'); if (!w) return;
    const t = document.createElement('div'); t.innerHTML = html(w.dataset.day, w.dataset.cur, true); w.replaceWith(t.firstElementChild);
  });
  window.SweepSetupPick = { list, html, tap, keep };
  // the manual form (a new trade): the row above the notes
  new window.SweepMO(() => {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || typeof TK === 'undefined' || !TK || TK.id || tk.querySelector('.nav-sp')) return;
    const notes = tk.querySelector('[data-tk="notes"]'), at = notes && notes.closest('.tk-f'); if (!at) return;
    at.insertAdjacentHTML('beforebegin', html(TK.date, TK.setup));
  }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('#tkSlide [data-sp]'); if (!b || typeof TK === 'undefined' || !TK) return;
    TK.setup = tap(b, TK.setup);
    const al = document.getElementById('tkAlerts'); if (al && typeof tkAlerts === 'function' && typeof tkState === 'function') al.innerHTML = tkAlerts(tkState());   // the coach follows the setup (edge T3)
    if (window.SweepCkFill) SweepCkFill();   // and the checklist: the setup's criteria (edge T7)
  });
})();

/* Edge T7 · questions that adapt (computed, never saved: nothing changes in the trader's settings without them)
 *  - a setup's own entry criteria (settings.setup_rules = { setup: [{ id, text }] }, 3 at most, Settings › Setups or on the form):
 *    the setup picked on a form, its criteria replace the 3 generic questions (these stay under « See more »); answers in discipline.*;
 *  - the question that separates winners from losers (average result of « yes » against « no », 5 trades of each at least,
 *    8 weeks) comes first, with its mention;
 *  - an « acquired » question (« yes » on 95 % of the trades of the last 4 weeks, 10 answers at least, no « no » in the last
 *    7 days) goes under « See more », marked; it comes back with a « no » */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const W = ({ en: { sep: 'This question separates your winners from your losers', acq: 'acquired', crit: 'Criteria of {s}', add: '+ Add a criterion for {s}', addQ: 'An entry criterion of {s} (e.g. « Break of the 15-minute range »)', rules: 'Entry criteria', rulesH: 'Up to 3 per setup. On the trade forms, they replace the first questions of the checklist when the setup is picked.', ph: 'Criterion {n}' },
    fr: { sep: 'Cette question sépare tes gagnants de tes perdants', acq: 'acquise', crit: 'Critères de {s}', add: '+ Ajouter un critère pour {s}', addQ: 'Un critère d’entrée de {s} (ex. « Cassure du range des 15 premières minutes »)', rules: 'Critères d’entrée', rulesH: 'Jusqu’à 3 par setup. Sur les formulaires de trade, ils remplacent les premières questions de la checklist quand le setup est choisi.', ph: 'Critère {n}' },
    es: { sep: 'Esta pregunta separa tus ganadoras de tus perdedoras', acq: 'adquirida', crit: 'Criterios de {s}', add: '+ Añadir un criterio para {s}', addQ: 'Un criterio de entrada de {s} (ej. « Ruptura del rango de los 15 primeros minutos »)', rules: 'Criterios de entrada', rulesH: 'Hasta 3 por setup. En los formularios de operación, reemplazan las primeras preguntas de la checklist cuando eliges el setup.', ph: 'Criterio {n}' } })[L] || null;
  const T = W || { sep: 'This question separates your winners from your losers', acq: 'acquired', crit: 'Criteria of {s}', add: '+ Add a criterion for {s}', addQ: 'An entry criterion of {s}', rules: 'Entry criteria', rulesH: '', ph: 'Criterion {n}' };
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const fill = (s, v) => String(s).replace(/\{(\w+)\}/g, (_, k) => (v[k] != null ? v[k] : ''));
  const low = (s) => String(s || '').trim().toLowerCase();
  const day0 = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const addD = (d, k) => { const x = new Date(d + 'T12:00:00Z'); x.setUTCDate(x.getUTCDate() + k); return x.toISOString().slice(0, 10); };
  const net = (t) => (t.pnl_c || 0) - (t.fees_c || 0);
  const active = () => ((typeof S !== 'undefined' && S.settings && S.settings.questions) || []).filter((q) => q.active !== false && q.active !== 0);
  /** the setup's own criteria, as questions (id « sr_… ») */
  function criteria(setup) {
    const r = (typeof S !== 'undefined' && S.settings && S.settings.setup_rules) || {}, k = Object.keys(r).find((x) => low(x) === low(setup));
    return k && setup ? (r[k] || []).filter((c) => c && String(c.text || '').trim()).slice(0, 3).map((c) => ({ id: c.id, text: c.text, crit: true })) : [];
  }
  let memo = { k: '', v: null };
  function stats() {
    const tr = (typeof S !== 'undefined' && S.trades) || [], k = tr.length + '|' + tr.reduce((m, t) => (t.updated_at > m ? t.updated_at : m), '') + '|' + day0();
    if (memo.k === k) return memo.v;
    const d = day0(), from = addD(d, -55), m4 = addD(d, -27), w1 = addD(d, -6), seen = new Set();
    const list = tr.filter((t) => !t.demo && t.date >= from && t.date <= d && (!t.copy_group || (!seen.has(t.copy_group) && seen.add(t.copy_group))));
    const out = {};
    active().forEach((q) => {
      const y = [], n = []; let ry = 0, rn = 0, late = false;
      list.forEach((t) => {
        const a = (t.discipline || {})[q.id]; if (a !== 'y' && a !== 'n') return;
        const v = net(t) / Math.max(1, Math.round(+t.contracts || 1)); (a === 'y' ? y : n).push(v);
        if (t.date >= m4) { a === 'y' ? ry++ : rn++; if (a === 'n' && t.date >= w1) late = true; }
      });
      const avg = (l) => l.reduce((s, x) => s + x, 0) / l.length;
      out[q.id] = { gap: y.length >= 5 && n.length >= 5 ? avg(y) - avg(n) : null, acq: ry + rn >= 10 && ry / (ry + rn) >= 0.95 && !late };
    });
    memo = { k, v: out }; return out;
  }
  /** the questions of a form, in their order, and how many are shown before « See more » */
  function order(setup) {
    const qs = active(), st = stats(), crit = criteria(setup);
    const sepQ = qs.filter((q) => st[q.id] && st[q.id].gap > 0).sort((a, b) => st[b.id].gap - st[a.id].gap)[0] || null;
    const gen = qs.map((q) => Object.assign({}, q, { sep: !!sepQ && q.id === sepQ.id, acq: !!(st[q.id] && st[q.id].acq) && !(sepQ && q.id === sepQ.id) }));
    const ord = [...gen.filter((q) => q.sep), ...gen.filter((q) => !q.sep && !q.acq), ...gen.filter((q) => q.acq)];
    if (crit.length) return { list: [...crit, ...ord], shown: crit.length, crit: true };
    return { list: ord, shown: Math.min(3, ord.filter((q) => !q.acq).length), crit: false };
  }
  /** a question's words, with its mention */
  // (27 Oct.) in the trader's language: the default questions are saved in English (tr: the app's dictionary, a trader's own text stays as it is)
  const label = (q) => `${esc2(((t) => (typeof tr === 'function' ? tr(t) : t))(q.text || q.q || q.label || q.id))}${q.sep ? `<small class="nav-q-sep">${esc2(T.sep)}</small>` : ''}${q.acq ? ` <small class="nav-q-acq">· ${esc2(T.acq)}</small>` : ''}`;
  function saveRules(setup, texts) {
    if (typeof editDoc !== 'function') return;
    editDoc('settings', 'settings', (r) => {
      const all = Object.assign({}, r.setup_rules || {}), k = Object.keys(all).find((x) => low(x) === low(setup)) || String(setup).trim(), old = all[k] || [];
      const list = texts.map((x) => String(x || '').trim().slice(0, 120)).map((x, i) => (x ? { id: (old[i] && old[i].id) || 'sr_' + Date.now().toString(36) + i, text: x } : null)).filter(Boolean).slice(0, 3);
      if (list.length) all[k] = list; else delete all[k];
      r.setup_rules = all;
    });
  }
  /** a criterion added on the form (the setup picked) */
  function addOne(setup) {
    const v = (prompt(fill(T.addQ, { s: setup })) || '').trim(); if (!v) return false;
    saveRules(setup, [...criteria(setup).map((c) => c.text), v]); return true;
  }
  const addLink = (setup) => (setup && criteria(setup).length < 3 ? `<button type="button" class="chip nav-am-more nav-sr-add" data-sr-add="${esc2(setup)}">${esc2(fill(T.add, { s: setup }))}</button>` : '');
  /** Settings › Setups: the entry criteria of each setup */
  function rulesHtml() {
    const l = (typeof S !== 'undefined' && S.settings && S.settings.setups) || []; if (!l.length) return '';
    return `<div class="nav-sr" data-noi18n><b>${esc2(T.rules)}</b><p class="help">${esc2(T.rulesH)}</p>${l.map((s) => { const c = criteria(s); return `<details class="nav-sr-s"${c.length ? '' : ''}><summary>${esc2(s)} <small class="muted">${c.length}/3</small></summary><div class="nav-sr-in">${[0, 1, 2].map((i) => `<input data-sr="${esc2(s)}" data-i="${i}" maxlength="120" value="${esc2((c[i] || {}).text || '')}" placeholder="${esc2(fill(T.ph, { n: i + 1 }))}">`).join('')}</div></details>`; }).join('')}</div>`;
  }
  document.addEventListener('change', (e) => {
    const i = e.target.closest && e.target.closest('input[data-sr]'); if (!i) return;
    const box = i.closest('.nav-sr-in'); saveRules(i.dataset.sr, [...box.querySelectorAll('input[data-sr]')].map((x) => x.value));
  });
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-sr-add]'); if (!b) return;
    if (addOne(b.dataset.srAdd)) document.dispatchEvent(new CustomEvent('sweep:qs'));
  });
  window.SweepQs = { order, criteria, label, addOne, addLink, rulesHtml, stats, T };
  // the checklist questions of Settings grow with their text (where field-sizing is not there yet)
  const fit = (t) => { t.style.height = 'auto'; t.style.height = t.scrollHeight + 'px'; };
  document.addEventListener('input', (e) => { if (e.target.matches && e.target.matches('textarea.q-ta')) fit(e.target); });
  new window.SweepMO(() => { document.querySelectorAll('#main textarea.q-ta:not([data-fit])').forEach((t) => { t.setAttribute('data-fit', ''); requestAnimationFrame(() => fit(t)); }); }).observe(document.body, { childList: true, subtree: true });
})();

/* D16 · « This trade looks like the one at 10:32. Add it anyway? » on the manual form (brief 02, part 1): the same rule as the
   screenshots (window.SweepDupOf), asked once, before « Save » or ⌘/Ctrl + Enter */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const W = ({ en: ['This trade looks like the one at {t}.', 'Add it anyway?', 'Add anyway', 'This trade looks like one already saved that day.'], fr: ['Ce trade ressemble à celui de {t}.', 'L’ajouter quand même ?', 'Ajouter quand même', 'Ce trade ressemble à un trade déjà enregistré ce jour-là.'],
    es: ['Esta operación se parece a la de las {t}.', '¿Añadirla de todos modos?', 'Añadir de todos modos', 'Esta operación se parece a una ya guardada ese día.'] })[L];
  let okFor = null;   // the values the trader confirmed
  const at = (x) => { const v = String(x || '').slice(0, 5); return L === 'fr' ? `${+v.slice(0, 2)} h ${v.slice(3, 5)}` : v; };
  function cand() {
    if (typeof TK === 'undefined' || !TK || TK.id || !TK.account || typeof tkState !== 'function') return null;
    const s = tkState(), ex = s.ex || []; if (!ex.length) return null;
    const p = s.pos || {}, r2 = (v) => (v == null ? null : Math.round(v * 100) / 100), t0 = String(ex[0].t || '');
    return { instrument: TK.inst, direction: s.dir, contracts: p.maxQty, date: typeof sessionOfTs === 'function' ? sessionOfTs(t0) : t0.slice(0, 10), entry_time: t0.slice(11, 16), entry: r2(p.avgEntry), exit: p.closed ? r2(p.avgExit) : null };
  }
  function check(e) {
    const c = cand(); if (!c || typeof window.SweepDupOf !== 'function') return;
    const key = JSON.stringify([TK.account, c]); if (okFor === key) return;
    const d = window.SweepDupOf(c, TK.account); if (!d) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const tk = document.querySelector('#tkSlide.open'), save = tk && tk.querySelector('[data-act="tk-save"]'); if (!save) return;
    let box = tk.querySelector('.nav-dup');
    if (!box) { box = document.createElement('div'); box.className = 'nav-dup'; box.setAttribute('role', 'alert'); (save.closest('.tk-foot, .tk-actions') || save).before(box); }
    box.dataset.key = key;
    box.innerHTML = `<p><b>${d.entry_time ? W[0].replace('{t}', at(d.entry_time)) : W[3]}</b> ${W[1]}</p><button type="button" class="btn sm" data-dup-ok>${W[2]}</button>`;
  }
  document.addEventListener('click', (e) => {
    const ok = e.target.closest && e.target.closest('#tkSlide [data-dup-ok]');
    if (ok) { const box = ok.closest('.nav-dup'); okFor = box.dataset.key; box.remove(); const s = document.querySelector('#tkSlide.open [data-act="tk-save"]'); if (s) s.click(); return; }
    if (e.target.closest && e.target.closest('#tkSlide [data-act="tk-save"]')) check(e);
  }, true);
  document.addEventListener('keydown', (e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && document.querySelector('#tkSlide.open')) check(e); }, true);
  document.addEventListener('input', (e) => { const b = e.target.closest && e.target.closest('#tkSlide') && document.querySelector('#tkSlide .nav-dup'); if (b) b.remove(); }, true);   // other values: asked again
})();

/* D17 · « Same as last » on the manual form (brief 02, part 1): the account, instrument, side and contracts of the previous trade
   in one tap (the account and the instrument are pre-selected already; the side never was) */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const W = ({ en: ['Same as last', 'Buy', 'Sell'], fr: ['Comme le dernier', 'Achat', 'Vente'], es: ['Como la última', 'Compra', 'Venta'] })[L];
  const last = () => (S.trades || []).filter((x) => !x.demo && x.account_id && x.instrument && x.direction)
    .sort((a, b) => ((b.date || '') + (b.entry_time || '')).localeCompare((a.date || '') + (a.entry_time || '')))[0] || null;
  const usable = (t) => t && typeof acct === 'function' && acct(t.account_id) && acct(t.account_id).status !== 'archived';
  new window.SweepMO(() => {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || typeof TK === 'undefined' || !TK || TK.id || TK.multi || TK.likeDone) return;
    if (tk.querySelector('.nav-like')) return;
    const head = tk.querySelector('#tkPanel .tk-head'), t = last(); if (!head || !usable(t)) return;
    const b = document.createElement('button'); b.type = 'button'; b.className = 'chip nav-like'; b.setAttribute('data-like', ''); b.setAttribute('data-noi18n', '');
    b.innerHTML = `<span>${W[0]}</span><b>${String(t.instrument).replace(/[<>&]/g, '')} · ${t.direction === 'short' ? W[2] : W[1]} · ${Math.max(1, +t.contracts || 1)}</b>`;
    head.after(b);
  }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('#tkSlide [data-like]'); if (!b) return;
    const t = last(); if (!usable(t) || typeof TK === 'undefined' || !TK) return;
    Object.assign(TK, { account: t.account_id, inst: t.instrument, dir: t.direction === 'short' ? 'short' : 'long', qty: Math.max(1, +t.contracts || 1), likeDone: true });
    if (typeof tkRefresh === 'function') tkRefresh({ panel: true });
  });
})();

/* a trade copied on several accounts shows « 2 × 5 » contracts (per account × accounts), never the sum */
(function () {
  'use strict';
  function fix(row, id) {
    const t = getDoc('trades', id); if (!t || !t.copy_group || row.dataset.qty) return;
    const n = (S.trades || []).filter((x) => x.copy_group === t.copy_group).length; if (n < 2) return;
    const per = t.contracts || 0, sum = String(per * n), lab = `${per} × ${n}`;
    row.dataset.qty = '1';
    if (row.tagName === 'TR') { [...row.children].forEach((td) => { if (td.children.length === 0 && td.textContent.trim() === sum) td.textContent = lab; }); return; }
    row.querySelectorAll('b, span, small').forEach((el) => { if (el.children.length === 0) { const tx = el.textContent; const r = tx.replace(new RegExp('(·\\s*)' + sum + '(\\b)'), '$1' + lab + '$2'); if (r !== tx) el.textContent = r; } });
  }
  new window.SweepMO(() => {
    document.querySelectorAll('#main tr[data-href^="#trade/"], #main a.trow, #main a.nav-tr').forEach((r) => { const m = /#trade\/([^/?#]+)/.exec(r.getAttribute('href') || r.dataset.href || ''); if (m) try { fix(r, decodeURIComponent(m[1])); } catch (e) { /* never blocks */ } });
  }).observe(document.body, { childList: true, subtree: true });
})();

new window.SweepMO(() => {
  let want = null; try { want = sessionStorage.getItem('sw.openPayout'); } catch (x) { /* private */ }   // '1', or a pre-filled request (JSON)
  if (!want || !/^#payouts/.test(location.hash || '')) return;
  const b = document.querySelector('#main .nav-pz-b[data-k="payout"]');
  if (!b) { const tab = document.querySelector('#main [data-mny-view="entries"]:not(.on)'); if (tab) tab.click(); return; }   // « My money » shown on « Analysis »: the add buttons are on « My entries »
  try { sessionStorage.removeItem('sw.openPayout'); } catch (x) { /* private */ }
  b.click(); setTimeout(() => {
    const f = document.querySelector('#main form[data-form="payout"]'); if (!f) return;
    let o = null; try { o = want[0] === '{' ? JSON.parse(want) : null; } catch (x) { /* a plain « open » */ }
    if (o) {   // « Record my request » (the account's payout counter): this account, « requested », the most that can be asked for
      const sel = f.elements.account; if (sel && o.acc) { sel.value = o.acc; sel.dispatchEvent(new Event('change', { bubbles: true })); }
      const rq = f.querySelector('input[name="status"][value="requested"]'); if (rq && !rq.checked) rq.click();
      if (o.gross_c > 0) { f.elements.gross.value = String(o.gross_c / 100); f.elements.gross.dispatchEvent(new Event('input', { bubbles: true })); }
      f.classList.add('nav-flash'); setTimeout(() => f.classList.remove('nav-flash'), 1400);
    }
    f.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, 150);
}).observe(document.body, { childList: true, subtree: true });

/* Today · « Accounts » card: drag to reorder (computer: drag; phone: press and hold, then slide). Same saved order as the Accounts page. */
(function () {
  'use strict';
  const idOf = (a) => decodeURIComponent((a.getAttribute('href') || '').replace('#account/', ''));
  function save(box) {
    [...box.querySelectorAll('a.nav-acc')].map(idOf).forEach((id, i) => { const a = getDoc('accounts', id); if (a && a.sort !== i) editDoc('accounts', id, (d) => { d.sort = i; }); });
  }
  let drag = null, moved = false;
  document.addEventListener('dragstart', (e) => { const a = e.target.closest && e.target.closest('#main .d-acc a.nav-acc'); if (!a) return; drag = a; moved = false; a.classList.add('nav-acc-drag'); try { e.dataTransfer.setData('text/plain', ''); e.dataTransfer.effectAllowed = 'move'; } catch (x) { /* some browsers */ } });
  document.addEventListener('dragover', (e) => { if (!drag) return; const o = e.target.closest && e.target.closest('#main .d-acc a.nav-acc'); if (!o || o === drag) return; e.preventDefault(); const r = o.getBoundingClientRect(); (e.clientY > r.top + r.height / 2 ? o.after(drag) : o.before(drag)); moved = true; });
  document.addEventListener('drop', (e) => { if (drag) e.preventDefault(); });
  document.addEventListener('dragend', () => { if (!drag) return; const box = drag.parentElement; drag.classList.remove('nav-acc-drag'); drag = null; if (moved) save(box); });
  // phone: hold 450 ms, then slide
  let t = null, held = null;
  document.addEventListener('touchstart', (e) => { const a = e.target.closest && e.target.closest('#main .d-acc a.nav-acc'); if (!a) return; t = setTimeout(() => { held = a; a.classList.add('nav-acc-drag'); if (navigator.vibrate) navigator.vibrate(10); }, 450); }, { passive: true });
  document.addEventListener('touchmove', (e) => {
    if (!held) { clearTimeout(t); return; } e.preventDefault();
    const y = e.touches[0].clientY; for (const o of held.parentElement.querySelectorAll('a.nav-acc')) { if (o === held) continue; const r = o.getBoundingClientRect(); if (y > r.top && y < r.bottom) { (y > r.top + r.height / 2 ? o.after(held) : o.before(held)); break; } }
  }, { passive: false });
  document.addEventListener('touchend', () => { clearTimeout(t); if (!held) return; const box = held.parentElement; held.classList.remove('nav-acc-drag'); const h = held; held = null; save(box); h.dataset.noNav = '1'; setTimeout(() => { delete h.dataset.noNav; }, 400); });
  document.addEventListener('click', (e) => { const a = e.target.closest && e.target.closest('a.nav-acc[data-no-nav]'); if (a) { e.preventDefault(); e.stopPropagation(); } }, true);
})();

/* Live account: a simple, premium form — no presets (live rules differ too much between platforms).
   Broker or firm, account name, starting balance, creation date. A simulation account (20 Oct., Mateo) takes the same form. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = ({ en: ['Live account', 'Live rules differ from one platform to another: enter just the essentials. You can add your rules later on the account page.', '‹ Back', 'Broker or prop firm'], fr: ['Compte live', 'Les règles live varient d’une plateforme à l’autre : entre seulement l’essentiel. Tu pourras ajouter tes règles plus tard sur la page du compte.', '‹ Retour', 'Broker ou prop firm'], es: ['Cuenta live', 'Las reglas live cambian de una plataforma a otra: introduce solo lo esencial. Podrás añadir tus reglas más tarde en la página de la cuenta.', '‹ Volver', 'Bróker o prop firm'] })[L];
  const TS = ({ en: ['Simulation account', 'Your practice account: its platform, its name and its starting balance. No firm rules.', '‹ Back', 'Platform (NinjaTrader, Tradovate…)', 'Platform', 'Simulation', 'e.g. Sim 50K'],
    fr: ['Compte de simulation', 'Ton compte de pratique : sa plateforme, son nom et son solde de départ. Aucune règle de firme.', '‹ Retour', 'Plateforme (NinjaTrader, Tradovate…)', 'Plateforme', 'Simulation', 'p. ex. Simulation 50K'],
    es: ['Cuenta de simulación', 'Tu cuenta de práctica: su plataforma, su nombre y su saldo inicial. Sin reglas de firma.', '‹ Volver', 'Plataforma (NinjaTrader, Tradovate…)', 'Plataforma', 'Simulación', 'p. ej. Simulación 50K'] })[L] || [];
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('form[data-form="account"] [data-st-ph0="live"], form[data-form="account"] [data-st-ph0="simulation"]'); if (!b) return;
    const f = b.closest('form'), sim = b.dataset.stPh0 === 'simulation', H = sim ? TS : T;
    setTimeout(() => {
      f.classList.remove('ux-st-on', 'ux-st-final'); f.classList.add('nav-live'); f.dataset.uxPreset = '';
      const w = f.querySelector('.ux-st, .ux-pk'); if (w) w.hidden = true;
      if (!f.querySelector('.nav-live-h')) f.insertAdjacentHTML('afterbegin', `<div class="nav-live-h" data-noi18n><button type="button" class="link nav-live-back">${H[2]}</button><h3>${H[0]}</h3><p>${H[1]}</p></div>`);
      if (sim) {   // a practice account: its platform (not a prop firm), no firm chips
        f.dataset.acctMtype = 'simulation'; f.classList.add('nav-sim');
        const fn0 = f.querySelector('[name="firmName"]'), lab = fn0 && fn0.closest('label'), sp = lab && lab.querySelector('span');
        if (fn0) { fn0.placeholder = H[3]; if (!fn0.value) fn0.value = H[5]; }
        if (sp) { sp.dataset.was = sp.textContent; sp.textContent = H[4]; }
        const nm0 = f.querySelector('[name="name"]'); if (nm0) { nm0.dataset.ph = nm0.placeholder; nm0.placeholder = H[6]; setTimeout(() => nm0.focus(), 80); }
        return;
      }
      // real money, two kinds: the firm's live account, or a personal brokerage account (« Other firm or personal account »)
      const KD = { en: ['Firm live account', 'Personal account (broker)'], fr: ['Compte live de la firme', 'Compte perso (courtier)'], es: ['Cuenta live de la firma', 'Cuenta personal (bróker)'] }[L] || ['Firm live account', 'Personal account (broker)'];
      if (!f.querySelector('.nav-live-kind')) { f.dataset.acctMtype = f.dataset.acctMtype || 'live'; f.querySelector('.nav-live-h').insertAdjacentHTML('beforeend', `<div class="seg nav-live-kind" role="group">${[['live', KD[0]], ['personal', KD[1]]].map(([v, l]) => `<button type="button" data-lkind="${v}" class="${f.dataset.acctMtype === v ? 'on' : ''}">${l}</button>`).join('')}</div>`); }
      const fn = f.querySelector('[name="firmName"]'); if (fn) fn.placeholder = T[3];
      const nm = f.querySelector('[name="name"]'); if (nm) setTimeout(() => nm.focus(), 80);
    }, 60);
  }, true);
  document.addEventListener('click', (e) => {
    const k = e.target.closest && e.target.closest('[data-lkind]'); if (!k) return;
    const f = k.closest('form'); f.dataset.acctMtype = k.dataset.lkind; k.parentElement.querySelectorAll('button').forEach((y) => y.classList.toggle('on', y === k));
  });
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.nav-live-back'); if (!b) return;
    const f = b.closest('form'); delete f.dataset.acctMtype; f.classList.remove('nav-live');
    if (f.classList.contains('nav-sim')) { f.classList.remove('nav-sim'); const sp = f.querySelector('[name="firmName"]') && f.querySelector('[name="firmName"]').closest('label').querySelector('span'); if (sp && sp.dataset.was) sp.textContent = sp.dataset.was; const nm = f.querySelector('[name="name"]'); if (nm && nm.dataset.ph) nm.placeholder = nm.dataset.ph; const fn = f.querySelector('[name="firmName"]'); if (fn && fn.value === TS[5]) fn.value = ''; } f.classList.add('ux-st-on'); const w = f.querySelector('.ux-st, .ux-pk'); if (w) w.hidden = false; b.closest('.nav-live-h').remove();
    const back = f.querySelector('[data-st-go="phase"], [data-st-go="firm"]'); if (back) back.click();
  });
})();

/* News: releases without a number (minutes, speeches, press conferences, Beige Book, statements) say so, so an empty
   Actual / Forecast / Previous never looks like a bug. A small pill on the event, and a note in its detail. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const RX = /\b(minutes|speech|speaks|testimony|press conference|beige book|statement|remarks)\b/i;
  const T = ({ en: ['No number', 'No figure expected · AI impact at +1 min and +30 min'],
    fr: ['Sans chiffre', 'Pas de chiffre attendu · impact IA à +1 min et +30 min'],
    es: ['Sin cifra', 'Sin cifra esperada · impacto IA a +1 min y +30 min'] })[L];
  function pass() {
    const rows = document.querySelectorAll('#main [data-act="ev-open"], #main .ff-row, #main .evm, #main .ev, #main .nctx, #main .cev, .evp .evp-top, .evp .nctx, #gSheet [data-act="ev-open"], .sheet-panel [data-act="ev-open"], .drawer .nctx');   // release rows only, not every element of the page
    const els = []; rows.forEach((r) => { for (const e of r.getElementsByTagName('*')) els.push(e); });
    els.forEach((el) => {
      if (el.children.length || el.dataset.noNum || el.closest('.nav-nonum, .nav-nonum-note')) return;
      const ownRow = el.closest('.nav-ev, .nav-fev'); if (ownRow && ownRow.querySelector('.nav-nonum-r')) { el.dataset.noNum = '1'; return; }
      const tx = el.textContent.trim(); if (tx.length < 6 || tx.length > 80 || !RX.test(tx)) return;
      el.dataset.noNum = '1';
      el.insertAdjacentHTML('afterend', `<span class="nav-nonum" data-noi18n title="${T[1].replace(/"/g, '&quot;')}">${T[0]}</span>`);
      // list row: no « Fcst — / Prev. — »
      const row = el.closest('.nav-ev, .nav-fev, [data-act="ev-open"], tr, li');   // that event's own row only
      if (row && !row.closest('.evp, .sheet-panel, #gSheet, .drawer')) row.querySelectorAll('*').forEach((x) => { if (x.children.length === 0 && /^(Fcst|Prev|Prév|Préc|Prévu|Prevision|Previsión|Ant)\.?\b/i.test(x.textContent.trim())) x.style.display = 'none'; });
      // detail: the Actual / Forecast / Previous / Surprise tiles give way to one clear note
      const box = el.closest('.evp, .sheet-panel, #gSheet, .drawer');
      if (box) {
        const pill = el.nextElementSibling && el.nextElementSibling.classList.contains('nav-nonum') ? el.nextElementSibling : null;
        const when = [...box.querySelectorAll('*')].find((x) => x.children.length === 0 && /\d{1,2}:\d{2}/.test(x.textContent) && x.textContent.length < 60);
        if (pill && when && !when.parentElement.querySelector(':scope > .nav-nonum')) { when.parentElement.classList.add('nav-nonum-line'); when.parentElement.append(pill); }
      }
      if (box && !box.querySelector('.nav-nonum-note')) {
        const lab = [...box.querySelectorAll('*')].find((x) => x.children.length === 0 && /^(Actual|Réel|Real)$/i.test(x.textContent.trim()));
        const grid = lab && lab.parentElement && lab.parentElement.parentElement;
        if (grid) { grid.style.display = 'none'; grid.insertAdjacentHTML('beforebegin', `<p class="nav-nonum-note" data-noi18n>${T[1]}</p>`); }
        box.querySelectorAll('*').forEach((x) => { if (x.children.length === 0 && /^(Awaiting release|En attente de publication|En attente|Esperando publicación)$/i.test(x.textContent.trim())) x.style.display = 'none'; });
      }
    });
  }
  new window.SweepMO(() => { try { pass(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();

/* Economic calendar: a page flag so its cards clip their inner rows (no inner box poking out of the rounded corners) */
new window.SweepMO(() => { document.body.classList.toggle('nav-news-page', /^#news/.test(location.hash || '')); }).observe(document.body, { childList: true, subtree: true });
window.addEventListener('hashchange', () => document.body.classList.toggle('nav-news-page', /^#news/.test(location.hash || '')));

/* Economic calendar: the long footer legend becomes one small pill */
new window.SweepMO(() => {
  if (!/^#news/.test(location.hash || '')) return;
  document.querySelectorAll('#main p, #main .muted, #main small, #main div').forEach((p) => {
    if (p.dataset.short || p.children.length > 2) return;
    const tx = p.textContent.trim();
    if (/^(Click an event|Clique sur une annonce|Toca un evento|Haz clic)/i.test(tx) && tx.length > 60) {
      p.dataset.short = '1';
      p.innerHTML = `<span class="nav-legend" data-noi18n><b>est.</b> ${({ en: 'estimated date', fr: 'date estimée', es: 'fecha estimada' })[(typeof LANG !== 'undefined' && LANG) || 'en']}</span>`;
    }
  });
}).observe(document.body, { childList: true, subtree: true });


/* B10: key figures (P&L, balances, KPIs) are never cut by « … »: a figure that does not fit gets a smaller font instead */
(function () {
  'use strict';
  // the shortened forms too: « −4,8 k $ », « 1,23 M $ », « $4.8k », « $1.23M » (21 Oct.: in French and Spanish a figure shortened once was no
  // longer taken for a figure, so never fitted again — it stayed cut when its tile got narrower or its font loaded late)
  const MONEY = /^[−+\-]?\$?[\d,.\s]+(\s?[kM])?(\s?\$|%)?$|^[−+\-]?\$[\d,.]+[kM]?$/;
  let q = 0;
  const LG = (typeof LANG !== 'undefined' && LANG) || 'en';
  /** the amount (cents) of a dollar figure as the app writes it in the trader's language; null for anything else */
  function centsOf(tx) {
    if (!/\$/.test(tx) || /%|k\b/.test(tx)) return null;
    let n = tx.replace(/[^\d,.]/g, '');
    if (LG === 'en') n = n.replace(/,/g, ''); else { if (LG === 'es') n = n.replace(/\./g, ''); n = n.replace(/,/g, '.'); }
    const v = parseFloat(n); if (!isFinite(v)) return null;
    return Math.round(v * 100) * (/^[−\-]/.test(tx.trim()) ? -1 : 1);
  }
  /** the same amount, shorter each time: rounded to the dollar, then « 12,3 k », « 123 k », « 1,23 M » */
  function shorter(c, tx) {
    const sign = /^[−\-]/.test(tx.trim()) ? '−' : /^\+/.test(tx.trim()) ? '+' : '', a = Math.abs(c) / 100;
    const loc = LG === 'en' ? 'en-US' : LG === 'es' ? 'es-ES' : 'fr-CA';
    const num = (v, d) => v.toLocaleString(loc, { maximumFractionDigits: d, minimumFractionDigits: 0, useGrouping: 'auto' });   // grouped as everywhere else (« −1 769 $ », not « −1769 $ »; Spanish keeps « 1769 »)
    const cur = (body, unit) => (LG === 'en' ? `${sign}$${body}${unit}` : `${sign}${body}${unit ? '\u202f' + unit : ''}\u00a0$`);
    const out = [cur(num(Math.round(a), 0), '')];
    if (a >= 1000) out.push(a < 99950 ? cur(num(a / 1000, 1), 'k') : a < 999500 ? cur(num(a / 1000, 0), 'k') : cur(num(a / 1e6, a < 9995000 ? 2 : 1), 'M'));   // never « 1000 k »
    return out;
  }
  /** whether a figure is one to fit (no layout read) */
  function isFig(el) {
    if (el.children.length) return false;
    const tx = (el.textContent || '').trim();
    return !!tx && tx.length <= 18 && /\d/.test(tx) && MONEY.test(tx);
  }
  /** writes only: a new text, or a figure shrunk before, is measured again at its own size (20 Oct.: shrunk from an already
      smaller size, while a tile was still narrow, amounts ended at 8 px and never grew back) */
  function reset(el) {
    const tx = el.textContent.trim();
    if (el.dataset.fitTx !== tx) { if (el.style.fontSize) el.style.removeProperty('font-size'); el.dataset.fitTx = tx; }
    else if (el.dataset.fitShrunk) el.style.removeProperty('font-size');
  }
  /** reads only: false when the figure fits, else what is needed to shrink it */
  function measure(el) {
    const box = el.clientWidth ? el : el.parentElement; if (!box) return null;
    const over = el.scrollWidth - el.clientWidth > 1 || (box !== el && el.scrollWidth - box.clientWidth > 1);
    if (!over) return false;
    return { room: Math.max(1, (box === el ? el.clientWidth : box.clientWidth)), sw: el.scrollWidth, fs: parseFloat(getComputedStyle(el).fontSize) || 16 };
  }
  /** writes: a key figure tile (Net P&L, balances…) is rounded, then abbreviated, before the font gets smaller (the exact
      amount stays in its label; each try is measured, a handful of tiles); any other figure gets a smaller font */
  function shrink(el, m) {
    const tx = el.textContent.trim();
    if (!el.dataset.fitFull && el.closest('.nav-kpi-g, .d-perf')) {
      const c = centsOf(tx);
      if (c != null) {
        el.dataset.fitFull = tx; el.title = tx; el.setAttribute('aria-label', tx);
        for (const v of shorter(c, tx)) { el.textContent = v; if (el.scrollWidth <= m.room + 1) break; }
        el.dataset.fitTx = el.textContent.trim();
        if (el.scrollWidth <= m.room + 1) return;
        m.sw = el.scrollWidth;
      }
    }
    const min = m.fs * 0.55; let fs = Math.max(min, Math.floor(m.fs * m.room / m.sw * 10) / 10);
    el.style.setProperty('font-size', fs + 'px', 'important'); el.dataset.fitShrunk = '1';   // « important »: the page's own sizes are !important too
    el.style.setProperty('text-overflow', 'clip'); el.style.setProperty('overflow', 'visible');
    // a text's width does not follow its font size exactly (21 Oct., the CI's Linux fonts: « −1,6 k $ » at 17.9 px still 2 px too
    // wide, then never measured again): checked, half a pixel smaller until it fits — a few reads, only for a figure shrunk
    for (let i = 0; i < 8 && fs > min && el.scrollWidth > m.room + 1; i++) { fs = Math.max(min, fs - 0.5); el.style.setProperty('font-size', fs + 'px', 'important'); }
  }
  /** the figure's text, the width it has and (not shrunk) the width its text takes: when they are the same as at its last fit,
      there is nothing to do (21 Oct.: without the text's own width, a figure drawn before its font had loaded kept overflowing) */
  const keyOf = (el) => el.textContent.trim() + '|' + (el.clientWidth || (el.parentElement ? el.parentElement.clientWidth : 0)) + (el.dataset.fitShrunk ? '' : '|' + el.scrollWidth);
  /** figures, never cut by « … »: all the reads, then all the writes, then the reads, then the writes (20 Oct.: one figure at a time, a
      write then a read, made the browser lay the page out again for every figure — 600 ms when Today opened on a phone) */
  function fitAll(list) {
    list = list.filter((el) => isFig(el) && el.getClientRects().length);   // a hidden figure keeps its size until it is shown
    const keys = list.map(keyOf);
    const todo = [], w = [];
    list.forEach((el, i) => { if (el.__fitKey !== keys[i]) { todo.push(el); w.push('|' + keys[i].split('|')[1]); } });   // (a count-up elsewhere in the page redrew every figure at each frame)
    todo.forEach(reset);
    const ms = todo.map(measure);
    todo.forEach((el, i) => {
      if (ms[i] === false) delete el.dataset.fitShrunk; else if (ms[i]) shrink(el, ms[i]);
      el.__fitKey = ms[i] === false ? keys[i] : el.textContent.trim() + w[i];   // (nothing read again: one more layout of the page; a figure that fit keeps the key read before, a shrunk one its text and width)
    });
  }
  function fit() {
    q = 0;
    const main = document.getElementById('main'); if (!main) return;
    fitAll([...main.querySelectorAll('.neg, .pos, .big, .nav-acc-bal, .nav-now-v, .ik b > span, .v, .num, b, strong')]);   // (7 Nov.: « Now »'s figure, at Apple's display size, and Stats' tiles, whose figure is a span in the b: 7 digits went past the tile)
  }
  // the key figure tiles (a handful of elements) are fitted right after each redraw, before the browser paints:
  // a page redrawn by a sync never shows its P&L cut for a frame (the rest of the page keeps the per-frame pass).
  // Only when a change touches the tiles (20 Oct.: every change in the page measured them again, 70 times while Today opened)
  { const m0 = document.getElementById('main'), K = '.nav-kpi-g, .d-perf';
    const touches = (rs) => rs.some((r) => (r.target.closest && r.target.closest(K)) || [...r.addedNodes].some((n) => n.nodeType === 1 && (n.matches(K) || n.querySelector(K))));
    if (m0) new MutationObserver((rs) => { if (!touches(rs)) return; const k = m0.querySelectorAll('.nav-kpi-g b, .d-perf b'); if (k.length) fitAll([...k]); }).observe(m0, { childList: true, subtree: true }); }
  const soon = () => { if (!q) q = requestAnimationFrame(fit); };
  if (window.SweepMO) new window.SweepMO(soon).observe(document.getElementById('main') || document.body, { childList: true, subtree: true });
  else new MutationObserver(soon).observe(document.body, { childList: true, subtree: true });
  addEventListener('resize', soon);
  // a font that loads after the figures were fitted makes their text wider without any change in the page (21 Oct., seen on the CI):
  // a figure that fit sees it in its key (its text's width); a shrunk one keeps its text and its width, so its key is cleared and
  // it is measured again at its own size — only when a font has loaded, so nothing goes back and forth
  const fontsIn = () => { document.querySelectorAll('[data-fit-shrunk]').forEach((el) => { el.__fitKey = ''; }); soon(); };
  if (document.fonts) { try { document.fonts.addEventListener('loadingdone', fontsIn); document.fonts.ready.then(fontsIn); } catch (e) { /* old browser */ } }
})();

/* B11: computer, Today — the two columns stay balanced (height gap ≤ 20 %): cards move from the taller column to the shorter.
   Stable: a card moves at most once per page, never back, and only when the gap gets smaller; the balance runs when the
   page is drawn and once more when late content has arrived — never while scrolling (it used to swap a card back and
   forth, and the page jumped). */
(function () {
  'use strict';
  function balance(last) {
    if (!window.SW_MQ || window.SW_MQ.matches) return;
    const dash = document.querySelector('#main .nav-dash'); if (!dash) return;
    dash.__bal = (dash.__bal || 0) + 1;   // no limit needed: a card moves at most once, so the columns cannot swap back and forth
    const a = dash.querySelector('.d-col-a'), b = dash.querySelector('.d-col-b'); if (!a || !b) return;
    const h = (c) => [...c.children].reduce((s, x) => s + (x.getClientRects().length ? x.getBoundingClientRect().height + 16 : 0), 0);
    const tried = new Set();
    for (let i = 0; i < 6; i++) {
      const ha = h(a), hb = h(b), big = ha > hb ? a : b, small = big === a ? b : a, hi = Math.max(ha, hb), lo = Math.min(ha, hb);
      if (!hi || (hi - lo) / hi <= 0.2) return;
      let movable = [...big.children].filter((x) => x.getClientRects().length && !x.dataset.balMoved && !tried.has(x) && !x.matches('.d-today, .nav-rt, .d-perf, .nav-merge, .d-news, .nav-trial, .nav-guard'));   // « What to watch » never moves: it stays under the day, whatever the filter
      if (!movable.length) { const mg = big.querySelector(':scope > .nav-merge'); const kids = mg ? [...mg.children].filter((x) => x.matches('.d-pay, .d-cal') && !x.dataset.balMoved && !tried.has(x) && x.getClientRects().length) : []; if (kids.length) movable = [kids[kids.length - 1]]; }
      const c = movable[movable.length - 1]; if (!c) return;
      if (c.parentElement && c.parentElement.classList.contains('nav-merge')) c.dataset.balFrom = 'merge';
      const ch = c.getBoundingClientRect().height + 16;
      if (Math.abs((hi - ch) - (lo + ch)) >= hi - lo) { tried.add(c); continue; }   // moving it would not help: try the next card
      small.append(c); c.dataset.balMoved = '1';
      const after = Math.abs(h(a) - h(b));
      if (after >= hi - lo) { (c.dataset.balFrom === 'merge' ? (big.querySelector(':scope > .nav-merge') || big) : big).append(c); continue; }   // its new size made it worse: back where it was (never tried again), try the next card
      const key = [...c.classList].find((k) => /^d-/.test(k)); if (key) { remembered.set(key, small === a ? 'a' : 'b'); keep(); }
    }
    if (last === true && remembered.size) { const ha = h(a), hb = h(b), hi = Math.max(ha, hb); if (hi && Math.abs(ha - hb) / hi > 0.2) { remembered.clear(); keep(); } }   // (last pass) the places kept no longer fit (other cards, other sizes): found again next time
  }
  // the page is redrawn now and then (sync, edits): the cards already moved go straight to their place, before the
  // page is painted — so a redraw never shows them in the other column for a moment (that was the jump)
  // kept on this device too (24 Oct.: coming back to Today, a card moved 53 px after the first paint on a slow computer —
  // the places were only in memory): the next visit puts the cards in their column before the page is painted
  const remembered = new Map((() => { try { return Object.entries(JSON.parse(localStorage.getItem('sw.bal') || '{}')); } catch (e) { return []; } })());
  const keep = () => { try { remembered.size ? localStorage.setItem('sw.bal', JSON.stringify(Object.fromEntries(remembered))) : localStorage.removeItem('sw.bal'); } catch (e) { /* private mode */ } };
  function replay(dash) {
    if (!remembered.size || !window.SW_MQ || window.SW_MQ.matches) return;
    const cols = { a: dash.querySelector('.d-col-a'), b: dash.querySelector('.d-col-b') }; if (!cols.a || !cols.b) return;
    remembered.forEach((to, key) => { const el = dash.querySelector('.' + key); if (el && el.parentElement !== cols[to]) { cols[to].append(el); el.dataset.balMoved = '1'; } });
  }
  new MutationObserver(() => { const d = document.querySelector('#main .nav-dash'); if (d && !d.__replayed) { d.__replayed = true; replay(d); } }).observe(document.getElementById('main') || document.body, { childList: true, subtree: true });
  let seen = null;
  const check = () => {
    const dash = document.querySelector('#main .nav-dash');
    if (!dash || dash === seen) return;   // only a newly drawn Today page
    seen = dash;
    requestAnimationFrame(() => requestAnimationFrame(balance));
    setTimeout(balance, 700); setTimeout(balance, 1600); setTimeout(() => balance(true), 3200);   // again as the accounts, the news and the routine arrive (a card still moves only once)
  };
  if (window.SweepMO) new window.SweepMO(check).observe(document.getElementById('main') || document.body, { childList: true });
  addEventListener('resize', () => { const d = document.querySelector('#main .nav-dash'); if (d) { d.__bal = 0; balance(); } });
  window.SweepBalance = balance;
})();

/* B12 / B17: words — « Worst drawdown », « Exceeded » (« Exceeded (n/m) »: a pattern of I18N_PAT, app.js)
   Brief 02 part 2: the firm's rule (« Max drawdown allowed ») no longer has the same name as the account's own worst drawdown
   Brief 02 part 7: what stayed in English (the Journal's « Max trades », two rules of the default checklist, the week's view,
   the economic releases' names: the acronyms traders use stay, CPI, PPI, PCE, NFP, FOMC, ISM)
   Brief 02 part 14: the buttons of the app's own window that replaced the browser's confirm()
   16 Oct.: the one line of filters (the dates of « Custom », « Copies » in the Filters sheet); one word in French for the
   consistency rule, « Consistance » (the account's rule and the score said « Constance », the forms « Consistance ») */
(function () {
  'use strict';
  // (27 Oct., brief « nouveau trader » N7) the Stats words a French or Spanish trader still read in English, with their « i »
  // (29 Oct., SWEEP.md step 6, D7b) the average of a trade's checklist is « Checklist » (the coach's score alone says « Discipline »)
  const D7 = { fr: { 'Any checklist': 'Toute checklist', 'Average checklist score of today’s trades': 'Score moyen de checklist des trades du jour', 'Checklist not done': 'Checklist non remplie' },
    es: { 'Any checklist': 'Cualquier checklist', 'Average checklist score of today’s trades': 'Puntuación media de checklist de las operaciones de hoy', 'Checklist not done': 'Checklist sin completar' } };
  try { if (window.I18N_FR) Object.assign(window.I18N_FR, D7.fr); if (window.I18N_ES) Object.assign(window.I18N_ES, D7.es); } catch (e) { /* the dictionaries load first */ }
  // (2 Nov., audit « transfuge » G2) one name for the action in Spanish too (the dictionary said « Añadir operación »)
  try { if (window.I18N_ES) Object.assign(window.I18N_ES, { 'Add a trade': 'Añadir una operación' }); } catch (e) { /* as it was */ }
  const add = { fr: { 'Profit factor': 'Facteur de profit', 'Session': 'Séance', 'Gross profit ÷ gross loss. Above 1.0 is profitable.': 'Total des gains ÷ total des pertes. Au-dessus de 1, tu gagnes plus que tu ne perds.', 'Clear': 'Effacer', 'Add an account first': 'Ajoute d’abord un compte', 'Trades belong to an account.': 'Chaque trade appartient à un compte.', 'Consistency': 'Consistance', 'Consistency rule': 'Règle de consistance', 'From': 'Du', 'To': 'Au', 'Copies': 'Copies', 'Counted once': 'Comptées une fois', 'Per contract': 'Par contrat', 'Disable': 'Désactiver', 'Replace': 'Remplacer', 'Delete this trade? This cannot be undone.': 'Supprimer ce trade ? C’est définitif.', 'My money': 'Mon argent', 'Worst drawdown': 'Pire recul', 'Max drawdown allowed': 'Drawdown permis', 'Exceeded': 'Dépassé', 'Avg win / loss': 'Gain / perte moy.', 'See its stats': 'Voir ses stats',
      'Max trades': 'Trades max', 'Entered without confirmation': 'Entrée sans confirmation', 'Broke daily loss limit': 'Limite de perte du jour dépassée', 'None recorded': 'Aucune', 'Show all accounts': 'Voir tous les comptes', 'schedule file': 'calendrier livré avec l’app', 'manual entry': 'saisie manuelle', 'ADP Non-Farm Employment Change': 'Emploi privé ADP', 'Average Hourly Earnings m/m': 'Salaire horaire moyen m/m', 'CB Consumer Confidence': 'Confiance des consommateurs (CB)', 'Core CPI m/m': 'CPI de base m/m', 'Core PCE Price Index m/m': 'Indice PCE de base m/m', 'Core PPI m/m': 'PPI de base m/m', 'FOMC Meeting Minutes': 'Procès-verbal du FOMC', 'FOMC Press Conference': 'Conférence de presse du FOMC', 'FOMC Rate Decision': 'Décision de taux du FOMC', 'GDP q/q (Advance)': 'PIB t/t (première estimation)', 'GDP q/q (Second Estimate)': 'PIB t/t (deuxième estimation)', 'GDP q/q (Third Estimate)': 'PIB t/t (troisième estimation)', 'ISM Manufacturing PMI': 'PMI manufacturier ISM', 'ISM Services PMI': 'PMI des services ISM', 'Initial Jobless Claims': 'Inscriptions au chômage', 'JOLTS Job Openings': 'Offres d’emploi JOLTS', 'Nonfarm Payrolls': 'Emplois non agricoles (NFP)', 'PCE Price Index m/m': 'Indice PCE m/m', 'Retail Sales m/m': 'Ventes au détail m/m', 'Unemployment Rate': 'Taux de chômage' },
    es: { 'Profit factor': 'Factor de beneficio', 'Gross profit ÷ gross loss. Above 1.0 is profitable.': 'Total de ganancias ÷ total de pérdidas. Por encima de 1, ganas más de lo que pierdes.', 'Clear': 'Borrar', 'Add an account first': 'Primero añade una cuenta', 'Trades belong to an account.': 'Cada operación pertenece a una cuenta.', 'From': 'Desde', 'To': 'Hasta', 'Copies': 'Copias', 'Counted once': 'Contadas una vez', 'Per contract': 'Por contrato', 'Disable': 'Desactivar', 'Replace': 'Reemplazar', 'OK': 'OK', 'Delete this trade? This cannot be undone.': '¿Eliminar esta operación? No se puede deshacer.', 'My money': 'Mi dinero', 'Worst drawdown': 'Peor retroceso', 'Max drawdown allowed': 'Drawdown permitido', 'Exceeded': 'Superado', 'Avg win / loss': 'Ganancia / pérdida', 'See its stats': 'Ver sus estadísticas',
      'Max trades': 'Operaciones máx.', 'Entered without confirmation': 'Entrada sin confirmación', 'Broke daily loss limit': 'Límite de pérdida diaria superado', 'None recorded': 'Ninguna', 'Show all accounts': 'Ver todas las cuentas', 'schedule file': 'calendario incluido en la app', 'manual entry': 'entrada manual', 'ADP Non-Farm Employment Change': 'Empleo privado ADP', 'Average Hourly Earnings m/m': 'Ingresos medios por hora m/m', 'CB Consumer Confidence': 'Confianza del consumidor (CB)', 'Core CPI m/m': 'CPI subyacente m/m', 'Core PCE Price Index m/m': 'Índice PCE subyacente m/m', 'Core PPI m/m': 'PPI subyacente m/m', 'FOMC Meeting Minutes': 'Actas del FOMC', 'FOMC Press Conference': 'Rueda de prensa del FOMC', 'FOMC Rate Decision': 'Decisión de tipos del FOMC', 'GDP q/q (Advance)': 'PIB t/t (avance)', 'GDP q/q (Second Estimate)': 'PIB t/t (segunda estimación)', 'GDP q/q (Third Estimate)': 'PIB t/t (tercera estimación)', 'ISM Manufacturing PMI': 'PMI manufacturero ISM', 'ISM Services PMI': 'PMI de servicios ISM', 'Initial Jobless Claims': 'Solicitudes de subsidio por desempleo', 'JOLTS Job Openings': 'Ofertas de empleo JOLTS', 'Nonfarm Payrolls': 'Nóminas no agrícolas (NFP)', 'PCE Price Index m/m': 'Índice PCE m/m', 'Retail Sales m/m': 'Ventas minoristas m/m', 'Unemployment Rate': 'Tasa de desempleo' } };
  try { if (window.I18N_FR) Object.assign(window.I18N_FR, add.fr); if (window.I18N_ES) Object.assign(window.I18N_ES, add.es); } catch (e) { /* the app stays in English */ }
  // French typography (audit of 16 Oct., R24): the translation file's straight apostrophes become ’ (« aujourd’hui », « l’app »)
  try { const D = window.I18N_FR; if (D) for (const k in D) if (typeof D[k] === 'string' && D[k].indexOf("'") >= 0) D[k] = D[k].replace(/([A-Za-zÀ-ÿ])'(?=[A-Za-zÀ-ÿ])/g, '$1’'); } catch (e) { /* as it was */ }
})();

/* brief 00, 1.2-k (16 Oct.), Q5 recommendation A: once the first real trade is there, the sample data is hidden everywhere
   (Trades, Journal, Calendar, Stats, My money, Accounts…), never deleted: it is set aside in S.__demo at each render (a sync
   may bring it back), a sample account holding a real trade stays; one line on Today and Trades offers « Remove them »
   (removeDemo: the app's window, with Cancel). Before: only Today hid it, and Trades showed two P&L for the same day. */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  const COLS_D = ['trades', 'accounts', 'payouts', 'expenses', 'journals', 'firms'];
  const T = { en: ['Sample data hidden', 'Remove them'], fr: ['Données d’exemple masquées', 'Les retirer'], es: ['Datos de ejemplo ocultos', 'Quitarlos'] };
  function setAside() {
    if (typeof S === 'undefined' || !Array.isArray(S.trades) || !Array.isArray(S.accounts)) return;
    const accIds = new Set(S.accounts.concat((S.__demo && S.__demo.accounts) || []).map((a) => a.id)), real = S.trades.filter((t) => !t.demo && accIds.has(t.account_id));   // a real trade on an account that exists
    if (!real.length) {   // no real trade any more (the only one deleted): the sample data comes back
      if (S.__demo) { COLS_D.forEach((c) => { const l = S.__demo[c]; if (l && l.length && Array.isArray(S[c])) { const have = new Set(S[c].map((d) => d.id)); S[c] = S[c].concat(l.filter((d) => !have.has(d.id))); } }); S.__demo = null; }
      return;
    }
    const keepAcc = new Set(real.map((t) => t.account_id));
    const keepFirm = new Set((S.accounts || []).filter((a) => !a.demo || keepAcc.has(a.id)).map((a) => a.firm_id));
    COLS_D.forEach((c) => {
      if (!Array.isArray(S[c])) return;
      const out = S[c].filter((d) => d.demo && !(c === 'accounts' && keepAcc.has(d.id)) && !(c === 'firms' && keepFirm.has(d.id)));
      if (!out.length || (c === 'accounts' && out.length === S[c].length)) return;   // never no account left
      S.__demo = S.__demo || {}; const ids = new Set(out.map((d) => d.id));
      S.__demo[c] = (S.__demo[c] || []).filter((d) => !ids.has(d.id)).concat(out);
      S[c] = S[c].filter((d) => !ids.has(d.id));
    });
    if (typeof F !== 'undefined' && ((F.account || '').startsWith('demo') || (F.firm || '').startsWith('demo'))) { F.account = 'all'; F.firm = 'all'; if (typeof saveF === 'function') saveF(); }
  }
  function line() {
    const main = document.getElementById('main'); if (!main) return;
    const want = !!(S.__demo && Object.values(S.__demo).some((l) => l.length)) && /^#(dashboard|trades)?$/.test(location.hash || '');   // Today and Trades
    let el = main.querySelector('.nav-demo-hid');
    if (!want) { if (el) el.remove(); return; }
    if (el) return;
    const t = T[(typeof LANG !== 'undefined' && LANG) || 'en'] || T.en;
    el = document.createElement('p'); el.className = 'nav-demo-hid'; el.setAttribute('data-noi18n', '');
    el.innerHTML = `<span>${t[0]}</span> · <button type="button" class="link" data-act="demo-remove">${t[1]}</button>`;
    main.prepend(el);
  }
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-act="demo-remove"]') && typeof removeDemo === 'function') removeDemo(); });
  const r0 = render;
  window.render = render = function () { try { setAside(); } catch (e) { /* never blocks */ } const o = r0.apply(this, arguments); try { line(); } catch (e) { /* never blocks */ } return o; };
})();

/* brief 00, 1.2-b and 1.2-c (16 Oct.), Q3 recommendation B: two margins were wrong (a payout with no trade after it; the evening
   trades' order in the real-time drawdown). A trader whose account changes is told once, the room now and before; a mark in
   his settings (margin_fix) keeps it from coming back, on every device. Nothing changes in his data. */
(function () {
  'use strict';
  if (typeof render !== 'function' || typeof acctStateV1 !== 'function') return;
  const T = { en: { h: 'We fixed how your room is calculated', s: 'A payout with no trade after it, or an evening trade, was counted wrong. Your accounts are right now:', room: '{a}: room {n} (not {o})', brk: '{a}: drawdown exceeded — the old calculation missed it', ok: 'Got it' },
    fr: { h: 'On a corrigé le calcul de ta marge', s: 'Un payout sans trade après lui, ou un trade du soir, était mal compté. Tes comptes sont maintenant justes :', room: '{a} : marge {n} (et non {o})', brk: '{a} : drawdown dépassé, l’ancien calcul ne le montrait pas', ok: 'Compris' },
    es: { h: 'Corregimos el cálculo de tu margen', s: 'Un payout sin operación después, o una operación de la noche, se contaba mal. Tus cuentas ya son correctas:', room: '{a}: margen {n} (no {o})', brk: '{a}: drawdown superado, el cálculo anterior no lo mostraba', ok: 'Entendido' } };
  const t = () => T[(typeof LANG !== 'undefined' && LANG) || 'en'] || T.en;
  const usd = (c) => (typeof money === 'function' ? money(Math.round(c), { sign: false, dec: 0 }) : '$' + Math.round(c / 100));
  const esc2 = (x) => String(x == null ? '' : x).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  let done = false;
  function check() {
    if (done || !S || !S.settings || !Array.isArray(S.accounts)) return;
    if (S.settings.margin_fix) { done = true; return; }
    const accs = S.accounts.filter((a) => !a.demo && a.status !== 'archived' && a.rules && a.rules.dd_c);
    if (!accs.length) return;   // nothing to compare yet (a new trader): asked again when he has accounts
    done = true;
    const lines = [];
    accs.forEach((a) => {
      let n = null, o = null; try { n = acctState(a); o = acctStateV1(a); } catch (e) { return; }
      if (!n || !o) return;
      if (n.breached && !o.breached) lines.push(t().brk.replace('{a}', a.name || ''));
      else if (n.buffer != null && o.buffer != null && Math.abs(n.buffer - o.buffer) >= 100) lines.push(t().room.replace('{a}', a.name || '').replace('{n}', usd(Math.max(0, n.buffer))).replace('{o}', usd(Math.max(0, o.buffer))));
    });
    try { editDoc('settings', 'settings', (d) => { d.margin_fix = typeof todayStr === 'function' ? todayStr() : '1'; }); } catch (e) { /* asked again next time */ }
    if (!lines.length) return;
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-mfix';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-mfix'; el.setAttribute('role', 'alertdialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in"><h2>${esc2(t().h)}</h2><p class="nav-pass-s">${esc2(t().s)}</p><ul class="nav-mfix-l">${lines.map((x) => `<li>${esc2(x)}</li>`).join('')}</ul><button type="button" class="btn primary nav-am-save" data-mfix="1">${esc2(t().ok)}</button></div>`;
    document.body.append(scrim, el); requestAnimationFrame(() => { el.classList.add('open'); scrim.classList.add('open'); });
    const close = () => [el, scrim].forEach((x) => { x.classList.remove('open'); setTimeout(() => x.remove(), 250); });
    el.addEventListener('click', (e) => { if (e.target.closest('[data-mfix]')) close(); }); scrim.addEventListener('click', close);
    setTimeout(() => { const b = el.querySelector('[data-mfix]'); if (b) b.focus(); }, 50);
  }
  const r0 = render;
  window.render = render = function () { const o = r0.apply(this, arguments); try { setTimeout(check, 1200); } catch (e) { /* never blocks */ } return o; };
})();

/* brief 00, 1.2-i (16 Oct.): one action on the first screen — no « + » in the bars while the first-run page is shown (it
   opened « Add an account first »); it comes back with the first account */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  const r0 = render;
  window.render = render = function () { const o = r0.apply(this, arguments); try { document.body.classList.toggle('sw-onb', !!document.querySelector('#main .onb')); } catch (e) { /* never blocks */ } return o; };
})();

/* B17: an unknown page address leads to Today (the address is corrected too) */
(function () {
  'use strict';
  const fix = () => {
    try {
      const v = decodeURIComponent((location.hash || '').slice(1)).split('/')[0];
      if (v && typeof TITLES !== 'undefined' && !TITLES[v] && !/^(import|account|trade|journal|news|admin|plan|progress)$/.test(v)) history.replaceState(null, '', location.pathname + location.search + '#dashboard');
    } catch (e) { /* stays */ }
  };
  fix(); addEventListener('hashchange', fix);
})();

/* B18: every field has a name — a field shown with only a placeholder (or nothing) gets one, in the trader's language */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const N = { en: { date: 'Date', q: 'Checklist question {n}', v: 'Label when not respected ({n})', firm: 'Prop firm name', thr: 'Valid-day threshold (%)', search: 'Search', num: 'Amount' },
    fr: { date: 'Date', q: 'Question {n} de la checklist', v: 'Libellé si non respectée ({n})', firm: 'Nom de la prop firm', thr: 'Seuil de jour valide (%)', search: 'Rechercher', num: 'Montant' },
    es: { date: 'Fecha', q: 'Pregunta {n} de la checklist', v: 'Etiqueta si no se cumple ({n})', firm: 'Nombre de la prop firm', thr: 'Umbral de día válido (%)', search: 'Buscar', num: 'Importe' } }[L] || null;
  if (!N) return;
  let q = 0;
  function name() {
    q = 0;
    document.querySelectorAll('input:not([type=hidden]):not([aria-label]), select:not([aria-label]), textarea:not([aria-label])').forEach((e) => {
      if ((e.labels && e.labels.length && [...e.labels].some((l) => l.textContent.trim())) || e.getAttribute('aria-labelledby')) return;
      const b = e.dataset.bind || '', m = /questions\.(\d+)\.(text|viol)$/.exec(b);
      let n = e.placeholder || '';
      if (m) n = N[m[2] === 'text' ? 'q' : 'v'].replace('{n}', +m[1] + 1);
      else if (/^firms\|.*\|name$/.test(b)) n = N.firm;
      else if (/threshold$/.test(b)) n = N.thr;
      else if (!n && e.type === 'date') n = N.date;
      else if (!n && e.type === 'search') n = N.search;
      else if (!n) { const lab = e.closest('label, .f, td, .row'); const tx = lab && [...lab.childNodes].filter((x) => x.nodeType === 3 || (x.nodeType === 1 && !x.matches('input,select,textarea,button'))).map((x) => x.textContent).join(' ').trim(); n = tx || (e.type === 'number' ? N.num : ''); }
      if (!n) { const pv = e.previousElementSibling || (e.parentElement && e.parentElement.previousElementSibling); if (pv && !pv.matches('input,select,textarea,button')) n = (pv.textContent || '').trim(); }   // the title just above (trade review)
      if (n) e.setAttribute('aria-label', n.slice(0, 80));
    });
  }
  const soon = () => { if (!q) q = requestAnimationFrame(name); };
  if (window.SweepMO) new window.SweepMO(soon).observe(document.body, { childList: true, subtree: true });
  soon();
})();

/* B15: « Log out » stays the last thing of Settings (help and legal cards are added later by other parts) */
(function () {
  'use strict';
  const keep = () => { const m = document.getElementById('main'); const o = m && m.querySelector(':scope > .nav-logout'); if (o && o !== m.lastElementChild) m.append(o); };
  if (window.SweepMO) new window.SweepMO(keep).observe(document.getElementById('main') || document.body, { childList: true });
})();

/* C19: the chart module is loaded on demand — when a trade, the trade form, the calendar or Stats is opened, and
   otherwise once the page is idle — instead of with the first page. Its calendar setting lives here (no jump). */
(function () {
  'use strict';
  if (typeof calDays === 'function') calDays = function () { return 5; };   // Monday to Friday (was in chart.js)
  const src = window.SWEEP_LAZY && window.SWEEP_LAZY.chart; if (!src) return;
  let p = null;
  function load() {
    if (window.SweepChart || p) return p || Promise.resolve();
    p = new Promise((done) => {
      const e = document.createElement('script'); e.src = src; e.async = true;
      e.onload = () => {
        try { if (typeof render === 'function') render(); } catch (x) { /* the next render does it */ }
        // a trade form already open: let the module see it (it watches the page for the form)
        try { const t = document.createElement('i'); t.hidden = true; document.body.appendChild(t); setTimeout(() => t.remove(), 30); } catch (x) { /* nothing open */ }
        done();
      };
      e.onerror = () => { p = null; done(); };
      document.body.appendChild(e);
    });
    return p;
  }
  window.SweepLoadChart = load;
  const need = () => /^#(trade|calendar|analytics|import)/.test(location.hash || '') || document.getElementById('tkPanel');
  addEventListener('hashchange', () => { if (need()) load(); });
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-act^="add-trade"], [data-act="new-trade"], .nav-addtop, [data-act="tk-open"], [data-act="demo"]')) load(); }, true);
  if (typeof openTicket === 'function') { const o = openTicket; openTicket = function () { load(); return o.apply(this, arguments); }; }
  if (need()) load();
  else (window.requestIdleCallback || ((f) => setTimeout(f, 2500)))(() => load(), { timeout: 4000 });
})();

/* accounts: the add-account box opens only when asked (its open state was kept in the saved UI state and came back
   on the next visit); it closes when the trader leaves the page */
(function () {
  'use strict';
  const shut = () => { try { if (typeof U !== 'undefined' && U.addAcct) { U.addAcct = false; if (typeof saveU === 'function') saveU(); return true; } } catch (e) { /* nothing open */ } return false; };
  if (shut() && typeof render === 'function') render();
  let last = location.hash;
  addEventListener('hashchange', () => { if (/^#accounts/.test(last) && !/^#accounts$/.test(location.hash)) shut(); last = location.hash; });
})();

/* The plan (Today → 1. Plan) and the journal's Pre-market are the same day sheet (journals/<day>.pre): bias, setups,
   max loss, max trades, key levels. The journal shows the planned setups and « No trade » too, and changing them in
   the journal changes the plan. */
(function () {
  'use strict';
  const esc3 = (x) => String(x == null ? '' : x).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  window.journalSetupsHtml = function (day, chosen) {
    const own = (typeof S !== 'undefined' && S.settings && S.settings.setups) || [];
    const all = [...new Set([...own, ...(chosen || [])])];
    if (!all.length) { const E = { en: 'No setups yet: add them in your plan (Today → Plan) or in Settings.', fr: 'Aucun setup pour l’instant : ajoute-les dans ton plan (Aujourd’hui → Plan) ou dans les Réglages.', es: 'Aún no hay setups: añádelos en tu plan (Hoy → Plan) o en Ajustes.' }; return `<p class="muted" data-noi18n>${E[LANG] || E.en}</p>`; }
    return `<div class="seg nav-jsetups" role="group" data-noi18n>${all.map((x) => `<button type="button" class="${(chosen || []).includes(x) ? 'on' : ''}" data-jsetup="${esc3(x)}" data-day="${esc3(day)}" aria-pressed="${(chosen || []).includes(x)}">${esc3(x)}</button>`).join('')}</div>`;
  };
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-jsetup]'); if (!b) return;
    e.preventDefault();
    const day = b.dataset.day, v = b.dataset.jsetup;
    const edit = (d) => { d.id = d.id || day; d.date = d.date || day; d.pre = d.pre || {}; const cur = new Set(d.pre.setups || []); cur.has(v) ? cur.delete(v) : cur.add(v); d.pre.setups = [...cur]; };
    if (typeof getDoc === 'function' && getDoc('journals', day)) editDoc('journals', day, edit);
    else { const d = { id: day, date: day, pre: {} }; edit(d); put('journals', d); }
    if (typeof render === 'function') render();
  });
})();

/* Journal without a date, after the day is over (17:00–18:00 ET) or on a weekend: if the plan was made for the next
   session, the journal opens on that day — where the plan is (otherwise it would show today's empty sheet). */
(function () {
  'use strict';
  const go = () => {
    try {
      if ((location.hash || '') !== '#journal') return;
      const nx = window.SweepNextSession && SweepNextSession(); if (!nx || nx === (typeof todayStr === 'function' ? todayStr() : nx)) return;
      const j = typeof getDoc === 'function' && getDoc('journals', nx);
      if (j && j.pre && (j.pre.bias || (j.pre.setups || []).length || j.pre.levels)) history.replaceState(history.state, '', '#journal/' + nx);
    } catch (e) { /* stays on today */ }
  };
  addEventListener('hashchange', go, true); go();
})();

/* Account page, computer: two independent columns (Status · Payout · Equity | Firm rules · Recalibrate · Details), so a
   short card never leaves an empty hole under it (the rows of the two-column grid used to wait for the taller card) */
(function () {
  'use strict';
  function lay() {
    if (!/^#account\//.test(location.hash || '') || !window.SW_MQ || window.SW_MQ.matches) return;
    const main = document.getElementById('main'); if (!main || main.querySelector(':scope > .acc-mas')) return;
    const cols = [...main.querySelectorAll(':scope > section.cols')].slice(0, 2); if (!cols.length) return;
    const wrap = document.createElement('div'); wrap.className = 'acc-mas';
    const L = document.createElement('div'), R = document.createElement('div'); wrap.append(L, R);
    cols.forEach((c) => [...c.children].forEach((k, i) => (i % 2 ? R : L).append(k)));
    cols[0].replaceWith(wrap); cols.slice(1).forEach((c) => c.remove());
  }
  if (typeof render === 'function') { const r0 = render; render = function () { const o = r0.apply(this, arguments); try { lay(); } catch (e) { /* stays a grid */ } return o; }; }
  // (not while an account is being added: the redraw would send the guided picker back to its first question; CSS adapts the page meanwhile)
  if (window.SW_MQ && window.SW_MQ.addEventListener) window.SW_MQ.addEventListener('change', () => { if (typeof render === 'function' && !document.querySelector('#main .onb, #main .acct-add')) render(); });
})();

/* A screenshot can belong to several trades (several trades read from one screenshot): its file is deleted only when no
   trade or journal uses it any more — whatever the deletion path (one trade, all copies, undo expiry). */
(function guardShots(n) {
  'use strict';
  try {
    if (typeof ASSETS !== 'undefined' && ASSETS && ASSETS.delete && !ASSETS.__guard) {
      const del0 = ASSETS.delete.bind(ASSETS);
      ASSETS.delete = (id) => new Promise((res) => setTimeout(() => {   // after the caller removed its own trade
        const used = (S.trades || []).some((t) => (t.shots || []).some((x) => x && x.id === id)) || (S.journals || []).some((j) => JSON.stringify(j).includes(id));
        if (used) { res({ kept: true }); return; }
        Promise.resolve(del0(id)).then(res, res);
      }, 80));
      ASSETS.__guard = true; return;
    }
  } catch (e) { /* the app deletes as before */ }
  if (n < 60) setTimeout(() => guardShots(n + 1), 500);
})(0);

/* ───────────── Accounts: act on one account or on several (15 Oct.) ─────────────
 * Computer: two small icons at the right of each active row (« Move up »: evaluation → funded, funded → live; « Remove »:
 * failed or passed, never removed without a result) and a box to select several rows. Phone: « Select » (or a long press),
 * then a tap selects. Selected accounts get one bar of actions: Mark as failed (one Undo for all), Move to funded, Move to
 * live, Closed in profit (live / personal). An account only leaves the list with its result; a true delete stays on the page
 * of an account without trades. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { sel: 'Select', done: 'Done', n1: '1 account selected', n: '{n} accounts selected', clear: 'Clear', fail: 'Mark as failed', funded: 'Move to funded', live: 'Move to live', won: 'Closed in profit',
      up: 'Move up', upF: 'Move to funded', upL: 'Move to live', out: 'Remove', ck: 'Select {a}',
      outT: 'Remove {a}?', outTn: 'Remove {n} accounts?', outS: 'An account leaves your list with its result: it stays in your history and your stats.', okF: 'Passed → funded', okL: 'Passed → live', cancel: 'Cancel',
      failedT: '{n} accounts marked as failed', failed1: 'Account marked as failed', wonT: '{n} accounts closed in profit', won1: 'Account closed in profit',
      upT: 'Move {n} evaluations to funded?', upT1: 'Move {a} to funded?', upTL1: 'Move {a} to live?', upS: 'A funded account is created for each, with the same firm and size; each evaluation stays in your history, marked passed.', upTL: 'Move {n} funded accounts to live?', upSL: 'A live account is created for each, with the firm’s live rules; each funded account stays in your history.',
      choice: '{f}: {c} (the firm’s usual choice)', go: 'Confirm', doneF: '{n} funded accounts created', doneL: '{n} live accounts created', doneF1: 'Funded account created', doneL1: 'Live account created', skip: ' · {n} skipped (not eligible)', skip1: ' · 1 skipped (not eligible)' },
    fr: { sel: 'Sélectionner', done: 'Terminé', n1: '1 compte sélectionné', n: '{n} comptes sélectionnés', clear: 'Effacer', fail: 'Marquer échoué', funded: 'Passer financé', live: 'Passer live', won: 'Fermé en gain',
      up: 'Monter', upF: 'Passer en financé', upL: 'Passer en live', out: 'Retirer', ck: 'Sélectionner {a}',
      outT: 'Retirer {a} ?', outTn: 'Retirer {n} comptes ?', outS: 'Un compte quitte ta liste avec son résultat : il reste dans ton historique et tes stats.', okF: 'Réussi → financé', okL: 'Réussi → live', cancel: 'Annuler',
      failedT: '{n} comptes marqués échoués', failed1: 'Compte marqué échoué', wonT: '{n} comptes fermés en gain', won1: 'Compte fermé en gain',
      upT: 'Passer {n} évaluations en financé ?', upT1: 'Passer {a} en financé ?', upTL1: 'Passer {a} en live ?', upS: 'Un compte financé est créé pour chacune, avec la même firme et la même taille ; chaque évaluation reste dans ton historique, marquée réussie.', upTL: 'Passer {n} comptes financés en live ?', upSL: 'Un compte live est créé pour chacun, avec les règles live de la firme ; chaque compte financé reste dans ton historique.',
      choice: '{f} : {c} (le choix habituel de la firme)', go: 'Confirmer', doneF: '{n} comptes financés créés', doneL: '{n} comptes live créés', doneF1: 'Compte financé créé', doneL1: 'Compte live créé', skip: ' · {n} ignorés (pas concernés)', skip1: ' · 1 ignoré (pas concerné)' },
    es: { sel: 'Seleccionar', done: 'Listo', n1: '1 cuenta seleccionada', n: '{n} cuentas seleccionadas', clear: 'Borrar', fail: 'Marcar fallida', funded: 'Pasar a financiada', live: 'Pasar a live', won: 'Cerrada con ganancia',
      up: 'Subir', upF: 'Pasar a financiada', upL: 'Pasar a live', out: 'Retirar', ck: 'Seleccionar {a}',
      outT: '¿Retirar {a}?', outTn: '¿Retirar {n} cuentas?', outS: 'Una cuenta sale de tu lista con su resultado: queda en tu historial y en tus stats.', okF: 'Aprobada → financiada', okL: 'Aprobada → live', cancel: 'Cancelar',
      failedT: '{n} cuentas marcadas fallidas', failed1: 'Cuenta marcada fallida', wonT: '{n} cuentas cerradas con ganancia', won1: 'Cuenta cerrada con ganancia',
      upT: '¿Pasar {n} evaluaciones a financiada?', upT1: '¿Pasar {a} a financiada?', upTL1: '¿Pasar {a} a live?', upS: 'Se crea una cuenta financiada para cada una, con la misma firma y tamaño; cada evaluación queda en tu historial, marcada aprobada.', upTL: '¿Pasar {n} cuentas financiadas a live?', upSL: 'Se crea una cuenta live para cada una, con las reglas live de la firma; cada cuenta financiada queda en tu historial.',
      choice: '{f}: {c} (la opción habitual de la firma)', go: 'Confirmar', doneF: '{n} cuentas financiadas creadas', doneL: '{n} cuentas live creadas', doneF1: 'Cuenta financiada creada', doneL1: 'Cuenta live creada', skip: ' · {n} omitidas (no aplican)', skip1: ' · 1 omitida (no aplica)' }
  };
  const t = (k, v) => String((T[L] || T.en)[k]).replace(/\{(\w+)\}/g, (m, x) => (v && v[x] != null ? v[x] : m));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const name = (a) => (typeof acctLabel === 'function' ? acctLabel(a.id) : a.name) || a.name || '';
  const kind = (a) => { const m = window.SweepMoney && SweepMoney.moneyTypeOf ? SweepMoney.moneyTypeOf(a) : ''; return a.phase === 'eval' || m === 'eval' ? 'eval' : a.phase === 'funded' || m === 'funded' ? 'funded' : m === 'live' || a.phase === 'live' ? 'live' : m === 'personal' ? 'personal' : m === 'simulation' || a.phase === 'simulation' ? 'simulation' : 'none'; };
  const active = (a) => a && a.status !== 'archived' && a.status !== 'closed';
  const next = (a) => (kind(a) === 'eval' ? 'funded' : kind(a) === 'funded' ? 'live' : '');
  const SEL = new Set(); let mode = false;   // phone: select mode
  const onPage = () => /^#accounts$/.test(location.hash || '');
  const idOf = (tr) => decodeURIComponent((tr.dataset.href || '').replace('#account/', ''));
  const IC_UP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"/></svg>';
  const IC_OUT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>';

  /* the rows: a box, and the two icons (active accounts only) */
  function decorate() {
    if (!onPage()) { if (SEL.size || mode) { SEL.clear(); mode = false; } bar(); return; }
    const main = document.getElementById('main'); if (!main) return;
    const tb = main.querySelector('table.acct-tbl tbody'); const surf = tb && tb.closest('.surface'); if (!surf) return;
    const top = surf.querySelector(':scope > .nav-acc-top');
    if (top && !top.querySelector('.acc-selb')) { const b = document.createElement('button'); b.type = 'button'; b.className = 'link acc-selb'; b.setAttribute('data-noi18n', ''); b.textContent = mode ? t('done') : t('sel'); top.append(b); }
    surf.classList.toggle('acc-sel-on', mode); surf.classList.toggle('acc-sel-any', SEL.size > 0);
    surf.querySelectorAll('table.acct-tbl tbody tr[data-href^="#account/"]').forEach((tr) => {
      const id = idOf(tr), a = getDoc('accounts', id); if (!active(a)) return;
      const td = tr.firstElementChild, last = tr.lastElementChild; if (!td || !last) return;
      if (!td.querySelector('.acc-ck')) td.insertAdjacentHTML('afterbegin', `<label class="acc-ck" data-noi18n><input type="checkbox" data-acc-ck="${esc2(id)}" aria-label="${esc2(t('ck', { a: name(a) }))}"><i aria-hidden="true"></i></label>`);
      const ck = td.querySelector('[data-acc-ck]'); if (ck.checked !== SEL.has(id)) ck.checked = SEL.has(id);
      tr.classList.toggle('acc-on', SEL.has(id));
      if (!last.querySelector('.acc-acts')) {
        last.classList.add('acc-last');
        const n = next(a);
        last.insertAdjacentHTML('beforeend', `<span class="acc-acts" data-noi18n>${n ? `<button type="button" class="acc-ic" data-acc-up="${esc2(id)}" title="${esc2(n === 'funded' ? t('upF') : t('upL'))}" aria-label="${esc2((n === 'funded' ? t('upF') : t('upL')) + ' · ' + name(a))}">${IC_UP}</button>` : ''}<button type="button" class="acc-ic" data-acc-out="${esc2(id)}" title="${esc2(t('out'))}" aria-label="${esc2(t('out') + ' · ' + name(a))}">${IC_OUT}</button></span>`);
      }
    });
    bar();
  }
  /* the bar of actions, under the list (above the bottom bar on a phone) */
  function bar() {
    let el = document.getElementById('accBar');
    const ids = [...SEL].filter((id) => active(getDoc('accounts', id)));
    document.body.classList.toggle('acc-bar-on', onPage() && ids.length > 0);   // (Sweep AI's button steps aside while the bar is there)
    if (!onPage() || !ids.length) { if (el) el.remove(); return; }
    const ks = ids.map((id) => kind(getDoc('accounts', id)));
    const html = `<div class="acc-bar-h"><span class="acc-bar-n">${ids.length === 1 ? t('n1') : t('n', { n: ids.length })}</span><button type="button" class="link acc-bar-x" data-accb="clear">${t('clear')}</button></div><div class="acc-bar-a"><button type="button" class="btn sm" data-accb="fail">${t('fail')}</button>${ks.includes('eval') ? `<button type="button" class="btn sm" data-accb="funded">${t('funded')}</button>` : ''}${ks.includes('funded') ? `<button type="button" class="btn sm" data-accb="live">${t('live')}</button>` : ''}${ks.some((k) => k === 'live' || k === 'personal') ? `<button type="button" class="btn sm" data-accb="won">${t('won')}</button>` : ''}</div>`;
    if (!el) { el = document.createElement('div'); el.id = 'accBar'; el.className = 'acc-bar'; el.setAttribute('role', 'toolbar'); el.setAttribute('data-noi18n', ''); document.body.append(el); }
    if (el._h !== html) { el.innerHTML = html; el._h = html; }
  }
  const refresh = () => { if (typeof render === 'function') render(); else decorate(); };
  /* the actions */
  function fail(ids) {
    const keep = ids.map((id) => { const a = getDoc('accounts', id); return [id, { status: a.status, result: a.result, failed_on: a.failed_on }]; });
    ids.forEach((id) => editDoc('accounts', id, (d) => { d.status = 'archived'; d.result = 'failed'; d.failed_on = today(); }));
    SEL.clear(); refresh();
    window.SweepUndo.toast(ids.length === 1 ? t('failed1') : t('failedT', { n: ids.length }), () => keep.forEach(([id, k]) => editDoc('accounts', id, (d) => { for (const x in k) { if (k[x] === undefined) delete d[x]; else d[x] = k[x]; } })));
  }
  function won(ids) {
    const keep = ids.map((id) => { const a = getDoc('accounts', id); return [id, { status: a.status, result: a.result, won_on: a.won_on }]; });
    ids.forEach((id) => editDoc('accounts', id, (d) => { d.status = 'archived'; d.result = 'won'; d.won_on = today(); }));
    SEL.clear(); refresh();
    window.SweepUndo.toast(ids.length === 1 ? t('won1') : t('wonT', { n: ids.length }), () => keep.forEach(([id, k]) => editDoc('accounts', id, (d) => { for (const x in k) { if (k[x] === undefined) delete d[x]; else d[x] = k[x]; } })));
  }
  /* a small window of the app (never the browser's): its buttons resolve the promise with their value, or null */
  function dlg(title, text, buttons, extra) {
    return new Promise((done) => {
      document.querySelectorAll('.acc-dlg').forEach((x) => x.remove());
      const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim acc-dlg';
      const el = document.createElement('aside'); el.className = 'nav-dlg acc-dlg'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
      el.innerHTML = `<div class="nav-dlg-in"><h2>${esc2(title)}</h2><p class="nav-pass-s">${esc2(text)}</p>${extra || ''}<div class="acc-dlg-b">${buttons.map((b) => `<button type="button" class="btn ${b.primary ? 'primary ' : ''}nav-am-save" data-v="${esc2(b.v)}">${esc2(b.label)}</button>`).join('')}<button type="button" class="btn nav-pass-later" data-v="">${t('cancel')}</button></div></div>`;
      document.body.append(scrim, el);
      requestAnimationFrame(() => { el.classList.add('open'); scrim.classList.add('open'); const f = el.querySelector('[data-v]'); if (f) f.focus(); });
      const close = (v) => { document.removeEventListener('keydown', key, true); [el, scrim].forEach((x) => { x.classList.remove('open'); setTimeout(() => x.remove(), 250); }); done(v || null); };
      const key = (e) => { if (e.key === 'Escape') { e.stopPropagation(); close(null); } };
      document.addEventListener('keydown', key, true);
      scrim.addEventListener('click', () => close(null));
      el.addEventListener('click', (e) => { const b = e.target.closest('[data-v]'); if (b) close(b.dataset.v); });
    });
  }
  async function upgrade(ids, to) {
    const list = ids.map((id) => getDoc('accounts', id)).filter((a) => active(a) && next(a) === to), skip = ids.length - list.length;
    if (!list.length) return;
    if (to === 'funded' && list.length === 1 && window.SweepPass && SweepPass.passed(list[0])) { SEL.clear(); window.SweepPass.ask(list[0]); bar(); return; }   // one evaluation Sweep sees passed: its own window (and the firm's choice)
    const ch = to === 'funded' ? list.map((a) => { const g = window.SweepPass && SweepPass.choicesOf ? SweepPass.choicesOf(a) : []; const o = g[0]; const c = o && (o.choices.find((x) => x.def) || o.choices[0]); return c ? { a, choice: o.id + ':' + c.id, line: t('choice', { f: name(a), c: c.label }) } : { a, choice: null }; }) : list.map((a) => ({ a, choice: null }));
    const lines = ch.filter((x) => x.line).map((x) => `<p class="muted acc-dlg-l">${esc2(x.line)}</p>`).join('');
    const one = list.length === 1 ? name(list[0]) : null;
    const v = await dlg(to === 'funded' ? (one ? t('upT1', { a: one }) : t('upT', { n: list.length })) : (one ? t('upTL1', { a: one }) : t('upTL', { n: list.length })), to === 'funded' ? t('upS') : t('upSL'), [{ v: 'go', label: t('go'), primary: true }], lines);
    if (v !== 'go') return;
    ch.forEach((x) => { if (to === 'funded') window.SweepPass.toFunded(x.a.id, x.choice, true); else window.SweepLive.toLive(x.a.id, true); });
    SEL.clear(); refresh();
    if (typeof toast === 'function') toast((to === 'funded' ? (one ? t('doneF1') : t('doneF', { n: list.length })) : (one ? t('doneL1') : t('doneL', { n: list.length }))) + (skip ? (skip === 1 ? t('skip1') : t('skip', { n: skip })) : ''));
  }
  async function out(ids) {
    const list = ids.map((id) => getDoc('accounts', id)).filter(active); if (!list.length) return;
    const ks = new Set(list.map(kind));
    const btn = [{ v: 'fail', label: t('fail') }];
    if (ks.size === 1 && ks.has('eval')) btn.push({ v: 'funded', label: t('okF') });
    if (ks.size === 1 && ks.has('funded')) btn.push({ v: 'live', label: t('okL') });
    if ([...ks].every((k) => k === 'live' || k === 'personal' || k === 'none')) btn.push({ v: 'won', label: t('won') });
    const v = await dlg(list.length === 1 ? t('outT', { a: name(list[0]) }) : t('outTn', { n: list.length }), t('outS'), btn);
    const x = list.map((a) => a.id);
    if (v === 'fail') { fail(x); if (/^#account\//.test(location.hash)) location.hash = '#accounts'; }
    else if (v === 'won') { won(x); if (/^#account\//.test(location.hash)) location.hash = '#accounts'; }
    else if (v === 'funded' || v === 'live') upgrade(x, v);
  }
  /* clicks: before the row's own link */
  document.addEventListener('click', (e) => {
    const tg = e.target; if (!tg.closest) return;
    const o = tg.closest('[data-acc-out]'), u = tg.closest('[data-acc-up]'), c = tg.closest('.acc-ck'), b = tg.closest('[data-accb]'), sb = tg.closest('.acc-selb');
    if (o) { e.preventDefault(); e.stopPropagation(); const dm = o.closest('details.menu'); if (dm) dm.open = false; out([o.dataset.accOut]); return; }
    if (u) { e.preventDefault(); e.stopPropagation(); const a = getDoc('accounts', u.dataset.accUp); if (a) upgrade([a.id], next(a)); return; }
    if (c) { e.stopPropagation(); if (tg.matches('input')) { const id = tg.dataset.accCk; tg.checked ? SEL.add(id) : SEL.delete(id); decorate(); } return; }
    if (b) { const k = b.dataset.accb, ids = [...SEL]; if (k === 'clear') { SEL.clear(); mode = false; decorate(); return; } if (k === 'fail') fail(ids); else if (k === 'won') won(ids); else upgrade(ids, k); return; }
    if (sb) { mode = !mode; if (!mode) SEL.clear(); sb.textContent = mode ? t('done') : t('sel'); decorate(); return; }
    if (mode && onPage()) {   // phone, select mode: a tap selects the row instead of opening it
      const tr = tg.closest('#main table.acct-tbl tbody tr[data-href^="#account/"]'); if (!tr) return;
      const id = idOf(tr); if (!active(getDoc('accounts', id))) return;
      e.preventDefault(); e.stopPropagation(); SEL.has(id) ? SEL.delete(id) : SEL.add(id); decorate();
    }
  }, true);
  // phone: a long press on a row starts the selection with it
  let lp = null, lpXY = null;
  document.addEventListener('touchstart', (e) => {
    if (!onPage() || e.touches.length !== 1) return; const tr = e.target.closest && e.target.closest('#main table.acct-tbl tbody tr[data-href^="#account/"]'); if (!tr || e.target.closest('.nav-grip, .nav-ord-on')) return;
    lpXY = [e.touches[0].clientX, e.touches[0].clientY];
    lp = setTimeout(() => { lp = null; const id = idOf(tr); if (!active(getDoc('accounts', id))) return; mode = true; SEL.add(id); const sb = document.querySelector('#main .acc-selb'); if (sb) sb.textContent = t('done'); decorate(); try { navigator.vibrate && navigator.vibrate(10); } catch (x) { /* no vibration */ }
      const stop = (ev) => { ev.preventDefault(); ev.stopPropagation(); document.removeEventListener('click', stop, true); }; document.addEventListener('click', stop, true); setTimeout(() => document.removeEventListener('click', stop, true), 600); }, 450);
  }, { passive: true });
  document.addEventListener('touchmove', (e) => { if (lp && lpXY && Math.hypot(e.touches[0].clientX - lpXY[0], e.touches[0].clientY - lpXY[1]) > 8) { clearTimeout(lp); lp = null; } }, { passive: true });
  document.addEventListener('touchend', () => { if (lp) { clearTimeout(lp); lp = null; } }, { passive: true });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__accsel) {
    const w = function () { const out = appRender.apply(this, arguments); try { decorate(); } catch (e) { /* never blocks */ } return out; };
    Object.keys(appRender).forEach((k) => { w[k] = appRender[k]; });
    w.__accsel = true; window.render = w;
  }
  addEventListener('sw:page', () => { try { decorate(); } catch (e) { /* never blocks */ } });   // (1 Nov.) in the page's first image: the instant pages showed it a frame early
  window.addEventListener('hashchange', () => setTimeout(() => { try { decorate(); } catch (e) { /* never blocks */ } }, 30));
  // a quiet sync redraws the list without render(): the boxes and icons are back before the browser paints (no jump)
  { const m0 = document.getElementById('main');
    if (m0) new MutationObserver(() => { if (!onPage()) return; const tr = [...m0.querySelectorAll('table.acct-tbl tbody tr[data-href^="#account/"]')].find((x) => !x.querySelector('.acc-ck') && active(getDoc('accounts', idOf(x)))); if (tr) { try { decorate(); } catch (e) { /* never blocks */ } } }).observe(m0, { childList: true, subtree: true }); }
  window.SweepAccSel = { out, upgrade, fail, won, selected: () => [...SEL] };
})();

/* ───────────── One line of filters (16 Oct.): the pills' choices ─────────────
 * A pill (Period ▾, Account type ▾, My money's period ▾) opens its choices: a small menu under it on a computer, a sheet
 * from the bottom on a phone. A choice applies at once and closes it; « Dates » keeps it open with its two dates.
 * The choices come from window.SweepFxOpts[kind]() = { title, cur, opts: [[value, label]], attr, pick(v), keep(v), dates }. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const tr2 = (s) => (typeof tr === 'function' ? tr(s) : s);
  window.SweepFxOpts = Object.assign(window.SweepFxOpts || {}, {
    per: () => ({ title: ({ fr: 'Période', es: 'Período' })[L] || 'Period', cur: F.period || 'all',
      opts: [['today', tr2('Today')], ['week', tr2('This week')], ['month', tr2('This month')], ['all', tr2('All time')], ['custom', tr2('Custom')]], attr: 'data-per',
      dates: F.period === 'custom' ? `<label class="f"><span>${esc2(tr2('From'))}</span><input type="date" data-filter="from" value="${esc2(F.from || '')}"></label><label class="f"><span>${esc2(tr2('To'))}</span><input type="date" data-filter="to" value="${esc2(F.to || '')}"></label>` : '',
      pick: (v) => { F.period = v; if (v === 'custom' && !F.from) { F.from = monthStart(todayStr()); F.to = todayStr(); } saveF(); render(); }, keep: (v) => v === 'custom' })
  });
  const phone = () => (window.SW_MQ ? window.SW_MQ.matches : matchMedia('(max-width:860px)').matches);
  let open = null;   // { kind, chip }
  function close(back) {
    const m = document.getElementById('fxMenu'), sc = document.getElementById('fxScrim');
    if (m) { m.classList.remove('open'); setTimeout(() => m.remove(), 220); }
    if (sc) { sc.classList.remove('open'); setTimeout(() => sc.remove(), 220); }
    const c = open && open.chip; open = null;
    if (back && c && document.contains(c)) c.focus();
  }
  function paint(kind) {
    const fn = window.SweepFxOpts[kind]; if (!fn) return;
    const o = fn();
    let m = document.getElementById('fxMenu');
    if (!m) {
      m = document.createElement('div'); m.id = 'fxMenu'; m.setAttribute('role', 'dialog'); m.setAttribute('aria-modal', phone() ? 'true' : 'false'); m.setAttribute('data-noi18n', '');
      document.body.append(m);
      if (phone()) { const sc = document.createElement('div'); sc.id = 'fxScrim'; sc.className = 'fxm-scrim'; sc.addEventListener('click', () => close(true)); document.body.append(sc); requestAnimationFrame(() => sc.classList.add('open')); }
    }
    m.className = 'fxm' + (phone() ? ' fxm-sheet' : '') + (m.classList.contains('open') ? ' open' : '');
    m.setAttribute('aria-label', o.title);
    m.innerHTML = `${phone() ? '<i class="fxm-grab" aria-hidden="true"></i>' : ''}<p class="fxm-t">${esc2(o.title)}</p><div class="fxm-l" role="menu">${o.opts.map(([v, l]) => `<button type="button" role="menuitemradio" aria-checked="${String(v) === String(o.cur)}" class="fxm-o ${String(v) === String(o.cur) ? 'on' : ''}" data-fxv="${esc2(v)}" ${o.attr ? `${o.attr}="${esc2(v)}"` : ''}><span>${esc2(l)}</span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8.4l2.8 2.8 6.2-6.4"/></svg></button>`).join('')}</div>${o.dates ? `<div class="fxm-d">${o.dates}</div>` : ''}`;
    if (!phone() && open && open.chip) {   // under its pill, kept on screen
      const r = open.chip.getBoundingClientRect(), w = Math.max(220, r.width);
      m.style.left = Math.max(12, Math.min(r.left, innerWidth - w - 12)) + 'px'; m.style.top = (r.bottom + 6) + 'px'; m.style.minWidth = w + 'px';
      const h = m.offsetHeight; if (r.bottom + 6 + h > innerHeight - 12 && r.top - 6 - h >= 12) m.style.top = (r.top - 6 - h) + 'px';   // no room below: above its pill (19 Oct.: low in the window, its last choices were off screen)
    }
    requestAnimationFrame(() => m.classList.add('open'));
  }
  function show(kind, chip) {
    if (open && open.kind === kind) { close(true); return; }
    close(false); open = { kind, chip };
    paint(kind);
    requestAnimationFrame(() => { const f = document.querySelector('#fxMenu .fxm-o.on') || document.querySelector('#fxMenu .fxm-o'); if (f) f.focus(); });
  }
  document.addEventListener('click', (e) => {
    const t = e.target; if (!t.closest) return;
    const chip = t.closest('[data-fx]');
    if (chip) { e.preventDefault(); show(chip.dataset.fx, chip); return; }
    const o = t.closest('#fxMenu .fxm-o');
    if (o && open) {
      const kind = open.kind, fn = window.SweepFxOpts[kind], v = o.dataset.fxv, d = fn && fn();
      if (!d) return;
      d.pick(v);
      if (d.keep && d.keep(v)) { const c = document.querySelector(`#main [data-fx="${kind}"]`); if (c) open.chip = c; paint(kind); const i = document.querySelector('#fxMenu .fxm-d input'); if (i) i.focus(); }
      else close(true);
      return;
    }
    if (open && !t.closest('#fxMenu')) close(false);
  });
  // a date typed in the window: the pill follows (the app redraws the page; the window stays)
  document.addEventListener('change', (e) => { if (!open || !e.target.closest || !e.target.closest('#fxMenu')) return; setTimeout(() => { if (!open) return; const c = document.querySelector(`#main [data-fx="${open.kind}"]`); if (c) open.chip = c; paint(open.kind); }, 80); });
  document.addEventListener('keydown', (e) => {
    if (!open) return;
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(true); return; }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { const l = [...document.querySelectorAll('#fxMenu .fxm-o')], i = l.indexOf(document.activeElement); if (!l.length) return; e.preventDefault(); l[(i + (e.key === 'ArrowDown' ? 1 : l.length - 1)) % l.length].focus(); }
  }, true);
  window.addEventListener('hashchange', () => close(false));
  window.addEventListener('resize', () => { if (open && !phone()) close(false); });
  if (typeof swipeDismiss === 'function') {   // phone: the sheet closes by sliding it down, like the others
    new MutationObserver(() => { const m = document.getElementById('fxMenu'); if (m && m.classList.contains('fxm-sheet') && !m._sw) { m._sw = true; try { swipeDismiss(m, { scroller: () => m, onClose: () => close(true), ignore: 'input' }); } catch (x) { /* a tap closes it anyway */ } } }).observe(document.body, { childList: true });
  }
})();

/* ───────────── Settings › « Your devices » (17 Oct., the code by email on a new browser: auth/twofa.php) ─────────────
 * Each browser remembered for 30 days, this one marked; « Sign out » ends its sessions and forgets it (the next log-in there asks
 * for a code again). Shown only when the second step is on. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = ({ en: { h: 'Your devices', s: 'A new browser asks for a code sent to your email; this list is the browsers Sweep remembers (30 days).', me: 'This browser', seen: 'Last used {d}', out: 'Sign out', outQ: 'Sign out this device?', outS: 'Its sessions end; the next log-in there asks for a code.', none: 'No remembered browser yet.' },
    fr: { h: 'Tes appareils', s: 'Un nouveau navigateur demande un code envoyé par courriel ; voici les navigateurs que Sweep reconnaît (30 jours).', me: 'Ce navigateur', seen: 'Utilisé le {d}', out: 'Déconnecter', outQ: 'Déconnecter cet appareil ?', outS: 'Ses sessions se terminent ; la prochaine connexion y demandera un code.', none: 'Aucun navigateur reconnu pour l’instant.' },
    es: { h: 'Tus dispositivos', s: 'Un navegador nuevo pide un código enviado a tu correo; estos son los navegadores que Sweep recuerda (30 días).', me: 'Este navegador', seen: 'Usado el {d}', out: 'Cerrar sesión', outQ: '¿Cerrar sesión en este dispositivo?', outS: 'Sus sesiones terminan; el próximo inicio de sesión allí pedirá un código.', none: 'Ningún navegador recordado por ahora.' } })[L];
  const esc = (x) => String(x == null ? '' : x).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  let st = null, busy = false;
  const day = (s) => new Date(s * 1000).toLocaleDateString(L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA', { day: 'numeric', month: 'long' });
  function html() {
    if (!st || !st.on) return '';
    const rows = st.devices.map((d) => `<li class="nav-dev"><span><b>${esc(d.label)}</b><small>${d.this ? T.me + ' · ' : ''}${T.seen.replace('{d}', day(d.seen))}</small></span>${d.this ? '' : `<button type="button" class="btn sm" data-dev-out="${esc(d.id)}">${T.out}</button>`}</li>`).join('');
    return `<div class="nav-devs" data-noi18n><h3>${T.h}</h3><p class="help">${T.s}</p>${rows ? `<ul>${rows}</ul>` : `<p class="muted">${T.none}</p>`}</div>`;
  }
  function paint() {
    if (!/^#settings/.test(location.hash || '')) return;
    const form = document.querySelector('#main form[data-form="email"]'), box = form && form.closest('.surface'); if (!box) return;
    let el = box.querySelector('.nav-devs-w');
    if (!st) { if (!busy) { busy = true; apiJSON('api/me/devices').then((r) => { st = r; busy = false; paint(); }).catch(() => { busy = false; }); } return; }
    const h = html(); if (el && el._h === h) return;
    if (!el) { el = document.createElement('div'); el.className = 'nav-devs-w'; box.append(el); }
    el._h = h; el.innerHTML = h;
  }
  addEventListener('hashchange', () => { if (/^#settings/.test(location.hash || '')) { st = null; paint(); } });
  new window.SweepMO(() => { try { paint(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('[data-dev-out]'); if (!b) return;
    const ok = window.SweepUndo && SweepUndo.ask ? await SweepUndo.ask(T.outQ, T.outS, T.out, true) : true; if (!ok) return;
    try { await apiJSON('api/me/devices/forget', { method: 'POST', body: { id: b.dataset.devOut } }); } catch (x) { /* shown again as it is */ }
    st = null; paint();
  });
})();

/* ───────────── Face ID in the app added to the Home Screen (17 Oct., auth/passkey.php) ─────────────
 * Offered once in the installed app (« Later »: not before 7 days); then, after 12 hours without the app, the server answers
 * « locked » (423) and this screen covers the app: « Unlock with Face ID », or « Use my password » (signed out, log in again).
 * Never in a browser tab: there the code by email (auth/twofa.php) is the second step. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const BIO = ios ? 'Face ID' : ({ en: 'your fingerprint or face', fr: 'ton empreinte ou ton visage', es: 'tu huella o tu cara' })[L];
  const T = ({ en: { askT: 'Unlock Sweep with {b}', askS: 'After 12 hours without the app, {b} unlocks it. Your face never leaves your phone: Sweep keeps no picture of it.', on: 'Turn on {b}', later: 'Later', done: '{b} is on for Sweep', fail: 'It could not be turned on. Try again from Settings.', lockT: 'Sweep is locked', lockS: 'It has been a while: confirm it’s you.', unlock: 'Unlock with {b}', unlockG: 'Unlock', pw: 'Use my password', bad: '{b} did not unlock Sweep. Try again, or use your password.', set: '{b} on this phone', setOn: 'On', setOff: 'Turn off', setAdd: 'Turn on' },
    fr: { askT: 'Déverrouiller Sweep avec {b}', askS: 'Après 12 heures sans ouvrir l’app, {b} la déverrouille. Ton visage ne quitte jamais ton téléphone : Sweep n’en garde aucune image.', on: 'Activer {b}', later: 'Plus tard', done: '{b} est activé pour Sweep', fail: 'L’activation n’a pas marché. Réessaie depuis les Réglages.', lockT: 'Sweep est verrouillé', lockS: 'Ça fait un moment : confirme que c’est toi.', unlock: 'Déverrouiller avec {b}', unlockG: 'Déverrouiller', pw: 'Utiliser mon mot de passe', bad: '{b} n’a pas déverrouillé Sweep. Réessaie, ou utilise ton mot de passe.', set: '{b} sur ce téléphone', setOn: 'Activé', setOff: 'Désactiver', setAdd: 'Activer' },
    es: { askT: 'Desbloquear Sweep con {b}', askS: 'Tras 12 horas sin abrir la app, {b} la desbloquea. Tu cara nunca sale de tu teléfono: Sweep no guarda ninguna imagen.', on: 'Activar {b}', later: 'Más tarde', done: '{b} está activado para Sweep', fail: 'No se pudo activar. Inténtalo desde Ajustes.', lockT: 'Sweep está bloqueado', lockS: 'Ha pasado un rato: confirma que eres tú.', unlock: 'Desbloquear con {b}', unlockG: 'Desbloquear', pw: 'Usar mi contraseña', bad: '{b} no desbloqueó Sweep. Inténtalo de nuevo, o usa tu contraseña.', set: '{b} en este teléfono', setOn: 'Activado', setOff: 'Desactivar', setAdd: 'Activar' } })[L];
  const t = (k) => T[k].replace('{b}', BIO);
  const standalone = () => (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  const can = async () => { try { return !!(window.PublicKeyCredential && (await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable())); } catch (e) { return false; } };
  const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const unb = (s) => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)), (c) => c.charCodeAt(0));
  const post = (u, b) => fetch(u, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify(b || {}) }).then(async (r) => ({ ok: r.ok, status: r.status, d: await r.json().catch(() => ({})) }));
  const LS = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { /* private mode */ } return null; };
  const ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3H5a2 2 0 0 0-2 2v2M17 3h2a2 2 0 0 1 2 2v2M7 21H5a2 2 0 0 1-2-2v-2M17 21h2a2 2 0 0 0 2-2v-2"/><path d="M9 9v1M15 9v1M12 9v4h-1M9 16c1.6 1.2 4.4 1.2 6 0"/></svg>';

  /* turning it on (from the offer or from Settings) */
  async function register() {
    const o = await post('api/me/passkey/options'); if (!o.ok) throw new Error('options');
    const c = await navigator.credentials.create({ publicKey: { challenge: unb(o.d.challenge), rp: o.d.rp, user: { id: unb(o.d.user.id), name: o.d.user.name, displayName: o.d.user.displayName },
      pubKeyCredParams: [{ type: 'public-key', alg: -7 }], authenticatorSelection: { authenticatorAttachment: 'platform', userVerification: 'required', residentKey: 'discouraged' }, attestation: 'none', timeout: 60000 } });
    const r = await post('api/me/passkey/register', { id: c.id, clientDataJSON: b64u(c.response.clientDataJSON), attestationObject: b64u(c.response.attestationObject) });
    if (!r.ok) throw new Error('register ' + r.status);
  }
  // a failure is noted in Admin › Errors (its reason: the phone's or the server's), the trader only sees « try again »
  const report = (e) => { if (e && e.name === 'NotAllowedError') return; try { post('api/client-error', { msg: 'Face ID: ' + String((e && (e.name + ': ' + e.message)) || e).slice(0, 400), page: location.hash || '#', src: 'nav.js faceid' }).catch(() => {}); } catch (x) { /* offline */ } };
  function dialog(html, cls) {
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-fid open ' + (cls || '');
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-fid open ' + (cls || ''); el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in nav-fid-in"><div class="nav-fid-ic">${ICON}</div>${html}</div>`;
    document.body.append(scrim, el); return el;
  }
  const close = () => document.querySelectorAll('.nav-fid:not(.nav-lock)').forEach((x) => x.remove());
  async function offer() {
    if (!standalone() || document.querySelector('.nav-fid, .nav-inst, #gSheet.open')) return;
    const at = +(LS('sw.fidLater') || 0); if (at && at > Date.now()) return;
    try { if (sessionStorage.getItem('sw.modal') === '1') return; } catch (e) { /* private mode */ }
    if (!(await can())) return;
    let st = null; try { st = await apiJSON('api/me/passkey'); } catch (e) { return; }
    if (!st || !st.on || st.has || document.querySelector('.nav-fid')) return;
    try { sessionStorage.setItem('sw.modal', '1'); } catch (e) { /* private mode */ }
    const el = dialog(`<h2>${t('askT')}</h2><p class="muted">${t('askS')}</p><button type="button" class="btn primary nav-am-save" data-fid-on>${t('on')}</button><button type="button" class="link nav-inst-later" data-fid-later>${t('later')}</button>`);
    el.querySelector('[data-fid-later]').addEventListener('click', () => { LS('sw.fidLater', String(Date.now() + 7 * 864e5)); close(); });
    el.querySelector('[data-fid-on]').addEventListener('click', async () => {
      try { await register(); close(); if (typeof toast === 'function') toast(t('done')); } catch (e) { report(e); close(); if (typeof toast === 'function') toast(t('fail')); }
    });
  }
  /* the lock: any request answered 423 */
  let locked = false;
  function lock() {
    if (locked) return; locked = true;
    const el = dialog(`<h2>${t('lockT')}</h2><p class="muted">${t('lockS')}</p><p class="err nav-fid-err"></p><button type="button" class="btn primary nav-am-save" data-fid-unlock>${ios ? t('unlock') : T.unlockG}</button><button type="button" class="link nav-inst-later" data-fid-pw>${t('pw')}</button>`, 'nav-lock');
    const err = el.querySelector('.nav-fid-err');
    el.querySelector('[data-fid-pw]').addEventListener('click', async () => { await post('api/auth/logout').catch(() => {}); location.href = '/'; });
    el.querySelector('[data-fid-unlock]').addEventListener('click', async (e) => {
      const b = e.currentTarget; b.disabled = true; err.textContent = '';
      try {
        const o = await post('api/auth/unlock/options'); if (!o.ok) throw new Error('options');
        const a = await navigator.credentials.get({ publicKey: { challenge: unb(o.d.challenge), rpId: o.d.rpId, allowCredentials: o.d.allow.map((x) => ({ type: 'public-key', id: unb(x.id) })), userVerification: 'required', timeout: 60000 } });
        const r = await post('api/auth/unlock', { id: a.id, clientDataJSON: b64u(a.response.clientDataJSON), authenticatorData: b64u(a.response.authenticatorData), signature: b64u(a.response.signature) });
        if (!r.ok) throw new Error('unlock');
        location.reload();
      } catch (x) { err.textContent = t('bad'); b.disabled = false; }
    });
  }
  const orig = window.fetch.bind(window);
  window.fetch = async function (...args) { const r = await orig(...args); if (r.status === 423) { try { const j = await r.clone().json(); if (j && j.locked) lock(); } catch (e) { /* not ours */ } } return r; };
  // the app's first requests leave before this file is read: ask once now whether this session is locked
  if (document.querySelector('meta[name="sweep-build"]')) orig('api/me/passkey', { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } }).then((r) => { if (r.status === 423) lock(); }).catch(() => {});
  // offered a few seconds after the app opens (after « What's new » and the suggestions have had their turn)
  setTimeout(() => { offer().catch(() => {}); }, 6500);
  /* Settings › « Your devices »: Face ID on this phone (installed app only) */
  async function settingsLine() {
    const box = document.querySelector('#main .nav-devs'); if (!box || box.querySelector('.nav-fid-set') || !standalone() || !(await can())) return;
    let st = null; try { st = await apiJSON('api/me/passkey'); } catch (e) { return; }
    if (!st || !st.on || box.querySelector('.nav-fid-set')) return;
    const row = document.createElement('div'); row.className = 'nav-dev nav-fid-set';
    row.innerHTML = `<span><b>${t('set')}</b><small>${st.has ? T.setOn : ''}</small></span><button type="button" class="btn sm" data-fid-set="${st.has ? 'off' : 'on'}">${st.has ? T.setOff : T.setAdd}</button>`;
    box.insertBefore(row, box.querySelector('ul, p.muted'));
    row.querySelector('[data-fid-set]').addEventListener('click', async (e) => {
      const off = e.currentTarget.dataset.fidSet === 'off';
      try { if (off) await post('api/me/passkey/remove'); else await register(); if (typeof toast === 'function' && !off) toast(t('done')); } catch (x) { report(x); if (typeof toast === 'function') toast(t('fail')); }
      row.remove(); settingsLine();
    });
  }
  new window.SweepMO(() => { if (/^#settings/.test(location.hash || '')) settingsLine().catch(() => {}); }).observe(document.body, { childList: true, subtree: true });
  window.SweepFaceID = { offer, lock, register };
})();

/* The page of an account (audit of 18 Oct., lot 2): what the account is doing first — its status, its payout, its capital,
 * its trades and payouts — and its settings together, folded, at the bottom: « Account settings » holds the firm's rules,
 * « Recalibrate on your platform » and the details. Open by itself while the account has no rules yet (they come first
 * then); kept open or closed per account while the tab lives. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = ({ en: ['Account settings', 'Firm rules · recalibrate · details'], fr: ['Réglages du compte', 'Règles de la firme · recalibrer · détails'], es: ['Ajustes de la cuenta', 'Reglas de la firma · recalibrar · detalles'] })[L] || ['Account settings', 'Firm rules · recalibrate · details'];
  const open = new Map();   // account id → open
  let last = null;   // the box drawn before (a redraw replaces it before its « toggle » event: its state is read from it)
  const col = (main, re) => { const h = [...main.querySelectorAll('.sec-h h2')].find((e) => re.test(e.textContent.trim())); return h ? h.closest('.sec-h').parentElement : null; };
  function group() {
    const m = /^#account\/(.+)$/.exec(location.hash || ''); if (!m) return;
    const main = document.getElementById('main'); if (!main) return;
    const id = decodeURIComponent(m[1]), a = typeof getDoc === 'function' ? getDoc('accounts', id) : null; if (!a) return;
    const parts = [col(main, /^(Firm rules|Règles de la firme|Reglas de la firma)$/i), main.querySelector('.nav-recal'), col(main, /^(Details|Détails|Detalles)$/i)].filter(Boolean);
    let box = main.querySelector('.nav-accset');
    if (!parts.length || (box && parts.every((p) => box.contains(p)))) return;
    if (!box) {
      const noRules = !(a.rules && Object.keys(a.rules).some((k) => +a.rules[k] > 0));
      box = document.createElement('details'); box.className = 'nav-accset';
      box.innerHTML = `<summary data-noi18n><span><b>${T[0]}</b><small>${T[1]}</small></span></summary><div class="nav-accset-in"></div>`;
      if (last && last.dataset.acc === id) open.set(id, last.open);
      box.dataset.acc = id; box.open = open.has(id) ? open.get(id) : noRules; last = box;
      box.addEventListener('toggle', () => open.set(id, box.open));
      main.append(box);
    }
    const inner = box.querySelector('.nav-accset-in');
    parts.forEach((p) => { if (p.parentElement !== inner) inner.append(p); });
    // computer: the right column of the page held these settings; the payout goes there, next to the status
    const mas = main.querySelector(':scope > .acc-mas'), R = mas && mas.children[1], po = main.querySelector('.nav-po');
    if (R && po && po.parentElement !== R && ![...R.children].some((x) => x !== po)) R.append(po);
  }
  new window.SweepMO(() => { try { group(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();

/* My money (audit of 18 Oct., lot 3): « My entries / Analysis » first in the filters' line (one row less: the page had
 * « Accounts / My money », the filters, then this switch, three rows of controls) */
(function () {
  'use strict';
  function move() {
    const main = document.getElementById('main'); if (!main) return;
    const v = main.querySelector('.mny > .mny-view'), row = main.querySelector('.fx .fx-row'); if (!v || !row) return;
    v.classList.add('mny-view-fx'); v.dataset.fx = 'view'; row.prepend(v);
  }
  new window.SweepMO(() => { try { move(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();

/* Accounts on a phone (19 Oct., Mateo): one « Edit » on the line of « Add an account » in place of « Select » and
 * « Reorder »: it turns both on (a tap selects an account, the handle on the left moves it), « Done » turns both off.
 * The two buttons stay in the page, hidden: they keep doing the work. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = ({ en: ['Edit', 'Done'], fr: ['Modifier', 'Terminé'], es: ['Editar', 'Listo'] })[L] || ['Edit', 'Done'];
  const on = (surf) => surf.classList.contains('acc-sel-on') || surf.classList.contains('nav-ord-on');
  let edited = false;   // « Edit » turned both on: when the selection ends (« Clear » on the bar), the order ends with it
  function place() {
    if (!/^#accounts$/.test(location.hash || '') || !window.SW_MQ || !window.SW_MQ.matches) return;
    const top = document.querySelector('#main .nav-acc-top'); if (!top) return;
    const surf = top.closest('.surface'); if (!surf || !top.querySelector('.acc-selb') || !top.querySelector('.nav-ord-b')) return;
    if (edited && !surf.classList.contains('acc-sel-on')) { edited = false; if (surf.classList.contains('nav-ord-on')) top.querySelector('.nav-ord-b').click(); }
    let b = top.querySelector('.acc-editb');
    if (!b) { b = document.createElement('button'); b.type = 'button'; b.className = 'link acc-editb'; b.setAttribute('data-noi18n', ''); top.append(b); }
    const want = on(surf) ? T[1] : T[0]; if (b.textContent !== want) b.textContent = want;
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('#main .acc-editb'); if (!b) return;
    const top = b.closest('.nav-acc-top'), surf = top.closest('.surface'), sel = top.querySelector('.acc-selb'), ord = top.querySelector('.nav-ord-b');
    if (on(surf)) { edited = false; if (surf.classList.contains('acc-sel-on')) sel.click(); if (surf.classList.contains('nav-ord-on')) ord.click(); }
    else { edited = true; sel.click(); const t2 = document.querySelector('#main .nav-acc-top .nav-ord-b'); if (t2 && !t2.closest('.surface').classList.contains('nav-ord-on')) t2.click(); }
    setTimeout(place, 0);
  });
  new window.SweepMO(() => { try { place(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
})();

/* Accounts: the closed ones folded, like the archived ones (19 Oct., Mateo: « visuellement fermés »): « Closed accounts · 3 »,
 * opened with a tap, kept open or closed while the tab lives */
(function () {
  'use strict';
  let open = false, last = null;
  function fold() {
    if (!/^#accounts$/.test(location.hash || '')) return;
    const h = [...document.querySelectorAll('#main .sec > .sec-h > h2')].find((x) => /^(Closed accounts|Comptes fermés|Cuentas cerradas)$/.test(x.textContent.trim())); if (!h) return;
    const sec = h.closest('.sec'); if (sec.querySelector(':scope > details.nav-closed')) return;
    const body = sec.querySelector(':scope > .surface'); if (!body) return;
    const n = body.querySelectorAll('tbody tr[data-href^="#account/"]').length;
    if (last) open = last.open;   // (a redraw replaces it before its « toggle » event)
    const d = document.createElement('details'); d.className = 'nav-closed'; d.open = open; last = d;
    d.addEventListener('toggle', () => { open = d.open; });
    const s = document.createElement('summary'); s.setAttribute('data-noi18n', '');
    s.innerHTML = `<span><b></b><small></small></span>`; s.querySelector('b').textContent = h.textContent.trim() + (n ? ' · ' + n : '');
    const help = sec.querySelector(':scope > .sec-h .help'); s.querySelector('small').textContent = help ? help.textContent.trim() : '';
    d.append(s); body.before(d); d.append(body);
    sec.querySelector(':scope > .sec-h').hidden = true;
  }
  new window.SweepMO(() => { try { fold(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();

/* « Explore with sample data first » (20 Oct., Mateo: it looked like nothing happened): the button shows at once that it
   is preparing (a ring, its words), until the « Add the sample data? » window opens or the data is there. */
(function () {
  'use strict';
  const W = ({ en: 'Preparing the sample data…', fr: 'Préparation des données d’exemple…', es: 'Preparando los datos de ejemplo…' })[(typeof LANG !== 'undefined' && LANG) || 'en'] || 'Preparing the sample data…';
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-act="demo"]'); if (!b) return;
    if (b.classList.contains('is-busy')) { e.preventDefault(); e.stopImmediatePropagation(); return; }
    // a status line in its place, next to it (a redraw of the button's text cannot take it away); the button back at the end
    b.classList.add('is-busy'); b.setAttribute('aria-busy', 'true'); b.hidden = true;
    const st = document.createElement('span'); st.className = 'nav-busy-l'; st.setAttribute('role', 'status'); st.setAttribute('data-noi18n', ''); st.innerHTML = `<i aria-hidden="true"></i>${W}`; b.after(st);
    const t0 = Date.now();
    const done = () => document.querySelector('aside.nav-ask.open') || (typeof S !== 'undefined' && (S.trades || []).some((t) => t.demo)) || Date.now() - t0 > 45000 || !document.body.contains(b);
    (function wait() { if (!done()) { setTimeout(wait, 150); return; } b.classList.remove('is-busy'); b.removeAttribute('aria-busy'); b.hidden = false; st.remove(); })();
  }, true);
})();

/* ───────────── the trade page, iOS 27.2 (28 Oct., brief « design iOS 27.2 », V4 and V5; tour C3) ─────────────
 * V4: Geist Mono for the numbers only — a value in words (a setup, a session, « the 16th at 19:14 ») reads in Geist.
 * C3: « Economic context » only when there is an announcement (a trade without news: nothing to read there). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const WORD = /[A-Za-zÀ-ÿ]{3,}/;
  function paint() {
    if (!/^#trade\//.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main) return;
    main.querySelectorAll('.facts > div > span:last-child, .facts > div > b').forEach((v) => { const w = WORD.test(v.textContent || ''); if (v.classList.contains('fx-tx') !== w) v.classList.toggle('fx-tx', w); });
    const m = /^#trade\/([^/]+)/.exec(location.hash), t = typeof getDoc === 'function' && getDoc('trades', decodeURIComponent(m[1]));
    const box = main.querySelector('#newsCtx'), none = !!(t && Array.isArray(t.news) && !t.news.length);
    if (box) { const h = box.previousElementSibling; box.classList.toggle('fx-none', none); if (h && h.classList.contains('sec-h')) h.classList.toggle('fx-none', none); }
    // (activation F, C3) the setup is chosen in one place, « Setup & costs »: not again in the facts; the fees, the platform's
    // P&L and the tags under « More details »
    main.querySelectorAll('.facts > div').forEach((r) => { const l = r.firstElementChild; const k = !!l && /^Setup$/i.test(l.textContent.trim()); if (k !== r.classList.contains('fx-setup')) r.classList.toggle('fx-setup', k); });
    // a phone: the gross P&L (the header's net + the fees) and the fees (in « More details ») are not repeated in the facts
    main.querySelectorAll('.facts > div').forEach((r) => { const l = r.firstElementChild; const k = l && /^(Gross P&L|P&L brut|P&L bruto|Fees|Frais|Comisiones)$/i.test(l.textContent.trim()); if (k !== r.classList.contains('fx-dup')) r.classList.toggle('fx-dup', !!k); });
    // an empty value (« — ») says nothing: not a row of its own (the notes too)
    main.querySelectorAll('.facts > div, .facts > .ux-notes').forEach((r) => { const v = r.lastElementChild; const empty = !!v && r.children.length > 1 && /^[—–-]?$/.test((v.textContent || '').trim()); if (empty !== r.classList.contains('fx-empty')) r.classList.toggle('fx-empty', empty); });
    const fg = main.querySelector('.tr-side .fgrid.one');
    if (fg && !fg.querySelector('.tr-more')) {
      const rest = [...fg.children].filter((c, i) => i > 0 && !(c.matches && c.matches('datalist, .nav-sp, [class*=setup]')) && c.tagName === 'LABEL');
      if (rest.length) {
        // (10 Nov.) only its title is kept from the translation pass: the fields moved in were left in English (« Fees & commissions »)
        const d = document.createElement('details'); d.className = 'tr-more';
        d.innerHTML = `<summary data-noi18n>${({ en: 'More details', fr: 'Plus de détails', es: 'Más detalles' })[L] || 'More details'}</summary><div class="fgrid one"></div>`;
        const inner = d.lastElementChild; rest[0].before(d); rest.forEach((c) => inner.append(c));
        // the hint line under the platform's P&L follows its field
        [...fg.children].filter((c) => c !== d && c.previousElementSibling === d && c.tagName !== 'LABEL' && c.tagName !== 'DETAILS').forEach((c) => inner.append(c));
      }
    }
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__trFace) {
    const w = function () { const out = appRender.apply(this, arguments); try { paint(); } catch (e) { /* never blocks */ } return out; };
    w.__trFace = true; window.render = w;
  }
})();

/* ───────────── the first visit fits the moment (28 Oct., brief « activation », step D) ─────────────
 * One start, three endings after « Create account »:
 *   open    the market is open (it closes at 17:00 ET and reopens at 18:00; the weekend: Friday 17:00 → Sunday 18:00, 1 Nov.):
 *           the short plan (risk allowed), then the first trade (as before)
 *   closed  17:00 → 18:00 on a weekday, and the weekend: « Prepare tomorrow's session »: the plan of the next session and its risk allowed, then Today
 *           (the reminder of step E) — never an empty trade form; « I traded today: add my trade » stays, discreet, in « Now »
 *   active  « More than a year », or an account added « already running »: after the plan, « Bring your history » (the
 *           NinjaTrader 8 / Quantower sync or the CSV import, in one screen); « Later » leads to the case of the moment
 * The welcome page announces the right ending. window.__swNow (tests only) pins the clock. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { open: ['Your account', 'Your plan', 'Your first trade'], closed: ['Your account', 'Your plan for tomorrow'], mon: ['Your account', 'Your plan for Monday'], active: ['Your account', 'Your plan', 'Your history'],
      tOpen: 'Three steps and you’re trading.', sOpen: 'Your account, your plan for the day, your first trade: about two minutes.',
      tClosed: 'Prepare tomorrow’s session.', tMon: 'Prepare Monday’s session.', sClosed: 'Your account, then your plan for the next session and your risk allowed: about a minute.',
      tActive: 'Three steps and your journal is full.', sActive: 'Your account, your plan, then your history: Today, Stats and « Your edge » filled in from today.',
      hT: 'Bring your history', hS: 'Sync NinjaTrader 8 or Quantower, or import a CSV of your platform: Today, Stats and « Your edge » fill up from your first visit.', csv: 'Import a CSV', later: 'Later', traded: 'I traded today: add my trade' },
    fr: { open: ['Ton compte', 'Ton plan', 'Ton premier trade'], closed: ['Ton compte', 'Ton plan de demain'], mon: ['Ton compte', 'Ton plan de lundi'], active: ['Ton compte', 'Ton plan', 'Ton historique'],
      tOpen: 'Trois étapes et tu trades.', sOpen: 'Ton compte, ton plan du jour, ton premier trade : environ deux minutes.',
      tClosed: 'Prépare ta séance de demain.', tMon: 'Prépare ta séance de lundi.', sClosed: 'Ton compte, puis ton plan de la prochaine séance et ton risque permis : environ une minute.',
      tActive: 'Trois étapes et ton journal est rempli.', sActive: 'Ton compte, ton plan, puis ton historique : Aujourd’hui, Stats et « Ton edge » remplis dès aujourd’hui.',
      hT: 'Ramène ton historique', hS: 'Synchronise NinjaTrader 8 ou Quantower, ou importe un CSV de ta plateforme : Aujourd’hui, Stats et « Ton edge » se remplissent dès ta première visite.', csv: 'Importer un CSV', later: 'Plus tard', traded: 'J’ai tradé aujourd’hui : ajouter mon trade' },
    es: { open: ['Tu cuenta', 'Tu plan', 'Tu primera operación'], closed: ['Tu cuenta', 'Tu plan de mañana'], mon: ['Tu cuenta', 'Tu plan del lunes'], active: ['Tu cuenta', 'Tu plan', 'Tu historial'],
      tOpen: 'Tres pasos y operas.', sOpen: 'Tu cuenta, tu plan del día, tu primera operación: unos dos minutos.',
      tClosed: 'Prepara tu sesión de mañana.', tMon: 'Prepara tu sesión del lunes.', sClosed: 'Tu cuenta, luego tu plan de la próxima sesión y tu riesgo permitido: un minuto.',
      tActive: 'Tres pasos y tu diario está lleno.', sActive: 'Tu cuenta, tu plan y luego tu historial: Hoy, Estadísticas y « Tu ventaja » llenos desde hoy.',
      hT: 'Trae tu historial', hS: 'Sincroniza NinjaTrader 8 o Quantower, o importa un CSV de tu plataforma: Hoy, Estadísticas y « Tu ventaja » se llenan desde tu primera visita.', csv: 'Importar un CSV', later: 'Más tarde', traded: 'Operé hoy: añadir mi operación' } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const NYF = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
  function nyNow() { const p = {}; NYF.formatToParts(window.__swNow ? new Date(window.__swNow) : new Date()).forEach((x) => { p[x.type] = x.value; }); return { wk: !['Sat', 'Sun'].includes(p.weekday), wd: p.weekday, m: (+p.hour % 24) * 60 + +p.minute }; }
  function moment() { const n = nyNow(); return n.wd === 'Sat' || (n.wd === 'Fri' && n.m >= 1020) || (n.wd === 'Sun' && n.m < 1080) || (n.m >= 1020 && n.m < 1080) ? 'closed' : 'open'; }
  /** (30 Oct., tour W2) Friday after the close and Saturday: the next session is Monday's, « tomorrow » only when it is */
  const toMonday = () => { const n = nyNow(); return n.wd === 'Sat' || (n.wd === 'Fri' && n.m >= 1020); };
  const running = () => (S.accounts || []).some((a) => !a.demo && Array.isArray(a.adjustments) && a.adjustments.some((x) => +x.amount_c));
  function kind(xp) { return xp === 'gt1' || running() ? 'active' : moment(); }
  function history(later) {
    document.querySelectorAll('.nav-hist').forEach((x) => x.remove());
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-hist open';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-hist open'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in nav-hist-in"><h2>${esc2(t('hT'))}</h2><p class="muted">${esc2(t('hS'))}</p>
      <div class="nav-hist-b"><button type="button" class="btn" data-sy="connect" data-p="ninjatrader">NinjaTrader 8</button><button type="button" class="btn" data-sy="connect" data-p="quantower">Quantower</button><button type="button" class="btn" data-am-imp>${esc2(t('csv'))}</button></div>
      <button type="button" class="link nav-inst-later" data-hist-later>${esc2(t('later'))}</button></div>`;
    document.body.append(scrim, el);
    const close = () => document.querySelectorAll('.nav-hist').forEach((x) => x.remove());
    el.querySelectorAll('[data-sy], [data-am-imp]').forEach((b) => b.addEventListener('click', () => setTimeout(close, 0)));   // the sync or the import takes over
    const no = () => { close(); if (typeof later === 'function') later(); };
    scrim.addEventListener('click', no); el.querySelector('[data-hist-later]').addEventListener('click', no);
  }
  /** after « Create account »: the plan, then the ending of this trader's case */
  function after(xp) {
    const G = window.SweepGame, d = (window.SweepNextSession && SweepNextSession()) || (G && G.state && G.state() && G.state().today && G.state().today.day);
    const byMoment = () => { if (moment() === 'open' && typeof openTicket === 'function') openTicket(null); else if (typeof render === 'function') render(); };
    const end = () => { if (kind(xp) === 'active') history(byMoment); else byMoment(); };
    if (G && G.openPlan && d) G.openPlan(d, { then: end }); else end();
  }
  const SHORT = { en: { 'Your account': 'Account', 'Your plan': 'Plan', 'Your first trade': '1st trade', 'Your history': 'History', 'Your plan for tomorrow': 'Tomorrow’s plan', 'Your plan for Monday': 'Monday’s plan' },
    fr: { 'Ton compte': 'Compte', 'Ton plan': 'Plan', 'Ton premier trade': '1er trade', 'Ton historique': 'Historique', 'Ton plan de demain': 'Plan de demain', 'Ton plan de lundi': 'Plan de lundi' },
    es: { 'Tu cuenta': 'Cuenta', 'Tu plan': 'Plan', 'Tu primera operación': '1.ª operación', 'Tu historial': 'Historial', 'Tu plan de mañana': 'Plan de mañana', 'Tu plan del lunes': 'Plan del lunes' } };
  /** the welcome page: the right ending announced (the experience tapped changes it) */
  function paintWelcome(f) {
    const onb = document.querySelector('#main .onb'); if (!onb) return;
    const xp = ((f || onb).querySelector('[data-exp].on') || {}).dataset; const k = kind(xp && xp.exp);
    const ol = onb.querySelector('.onb-steps'), ttl = onb.querySelector('h1, h2'), sub = onb.querySelector('.onb-sub');
    const key = k === 'closed' ? (toMonday() ? 'Mon' : 'Closed') : k === 'active' ? 'Active' : 'Open';
    if (ttl && ttl.textContent !== t('t' + key)) ttl.textContent = t('t' + key);
    const sk = key === 'Mon' ? 'sClosed' : 's' + key;
    if (sub && sub.textContent !== t(sk)) sub.textContent = t(sk);
    // (2 Nov., tour visuel 11) a phone: the short words, the 3 steps on one line (« 3 Your first trade » fell on a 2nd line)
    const sh = (x) => ((SHORT[L] || SHORT.en)[x] || x);
    const html = t(key === 'Mon' ? 'mon' : k).map((x, i) => `<li class="${i ? '' : 'on'}"><span>${i + 1}</span><em class="onb-l">${esc2(x)}</em><em class="onb-s">${esc2(sh(x))}</em></li>`).join('');
    if (ol && ol.innerHTML !== html) { ol.setAttribute('data-noi18n', ''); ol.innerHTML = html; }
    onb.dataset.start = k;
  }
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('form[data-onb] [data-exp]')) setTimeout(() => paintWelcome(e.target.closest('form')), 0); });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__start) {
    const w = function () { const out = appRender.apply(this, arguments); try { paintWelcome(); } catch (e) { /* never blocks */ } return out; };
    w.__start = true; window.render = w;
  }
  /** « Now », a trader whose market is closed, before any trade: the discreet way to the trade form */
  function tradedLink() {
    if (moment() !== 'closed' || (S.trades || []).some((x) => !x.demo)) return '';
    return `<p class="nav-now-traded"><button type="button" class="link" data-rt="trade">${esc2(t('traded'))} ›</button></p>`;
  }
  window.SweepStart = { moment, kind, after, history, tradedLink, paint: () => paintWelcome() };
})();


/* ───────────── the discovery missions (29 Oct., SWEEP.md step 5): the mission of the day in the routine, « Do it now », and the
 * functions not yet discovered hidden (the server says which: GameDiscovery, game/discovery.php) ───────────── */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const M = {
    en: { kick: 'Mission {n} of {of}', go: 'Do it now', all: 'Show everything', allS: 'Every mission done and every function shown, now.',
      1: ['Add your account', 'Its firm rules fill in: your margin and your target are right from day one.'], 2: ['Your risk allowed', '30 seconds before the open: the most you can lose today, on screen.'], 3: ['Your first trade', 'A screenshot or your P&L: the journal starts.'], 4: ['Close your day', 'One tap at the end of the session: the day counts.'],
      5: ['A trade in your plan', 'In the way of your bias, under your max loss and your max trades.'], 6: ['Your setup in one tap', 'Its checklist adapts: your stats will say which setup pays.'], 7: ['Answer your coach', 'One sentence, your lesson: the coach learns from it.'], 8: ['Your trades on their own', 'NinjaTrader 8, Quantower or a CSV: no more typing.'],
      9: ['Stay within your margin', 'A day closed whose loss stayed under your risk allowed.'], 10: ['Sweep on your home screen', 'Install it, turn on your reminders: your plan before the open.'], 11: ['Your weekly recap', 'Friday: your week, your rule for the next one.'], 12: ['Your real net', 'My money: payouts minus fees, what trading really made you.'],
      13: ['Trade your edge', 'What works for you, in Stats: a plan that takes its rule.'], 14: ['The guided plan', 'Levels, scenarios, a locked sheet: the plan of serious days.'], 15: ['Three days in a row', 'Three complete days: « My progress » opens.'] },
    fr: { kick: 'Mission {n} sur {of}', go: 'Faire maintenant', all: 'Tout montrer', allS: 'Toutes les missions faites et toutes les fonctions montrées, tout de suite.',
      1: ['Ajoute ton compte', 'Les règles de ta firme se remplissent : ta marge et ton objectif sont justes dès le premier jour.'], 2: ['Ton risque permis', '30 secondes avant l’ouverture : ce que tu peux perdre aujourd’hui, à l’écran.'], 3: ['Ton premier trade', 'Une capture ou ton P&L : le journal commence.'], 4: ['Ferme ta journée', 'Un toucher à la fin de la séance : la journée compte.'],
      5: ['Un trade dans ton plan', 'Dans le sens de ton biais, sous ta perte max et ton nombre max de trades.'], 6: ['Ton setup en un toucher', 'Sa checklist s’adapte : tes stats diront quel setup paie.'], 7: ['Réponds au coach', 'Une phrase, ta leçon : le coach apprend d’elle.'], 8: ['Tes trades arrivent seuls', 'NinjaTrader 8, Quantower ou un CSV : plus rien à taper.'],
      9: ['Reste dans ta marge', 'Une journée fermée dont la perte est restée sous ton risque permis.'], 10: ['Sweep sur ton écran d’accueil', 'Installe-le, active tes rappels : ton plan avant l’ouverture.'], 11: ['Ton bilan de la semaine', 'Vendredi : ta semaine, ta règle pour la suivante.'], 12: ['Ton vrai net', 'Mon argent : les payouts moins les frais, ce que le trading te rapporte vraiment.'],
      13: ['Trade ton edge', 'Ce qui marche pour toi, dans Stats : un plan qui reprend sa règle.'], 14: ['Le plan guidé', 'Niveaux, scénarios, fiche verrouillée : le plan des jours sérieux.'], 15: ['Trois journées de suite', 'Trois journées complètes : « Ma progression » s’ouvre.'] },
    es: { kick: 'Misión {n} de {of}', go: 'Hacerlo ahora', all: 'Mostrar todo', allS: 'Todas las misiones hechas y todas las funciones visibles, ahora.',
      1: ['Añade tu cuenta', 'Las reglas de tu firma se completan: tu margen y tu objetivo son correctos desde el primer día.'], 2: ['Tu riesgo permitido', '30 segundos antes de la apertura: lo que puedes perder hoy, en pantalla.'], 3: ['Tu primera operación', 'Una captura o tu P&L: el diario empieza.'], 4: ['Cierra tu día', 'Un toque al final de la sesión: el día cuenta.'],
      5: ['Una operación en tu plan', 'En el sentido de tu sesgo, bajo tu pérdida máx. y tu número máx. de operaciones.'], 6: ['Tu setup en un toque', 'Su checklist se adapta: tus stats dirán qué setup paga.'], 7: ['Responde a tu coach', 'Una frase, tu lección: el coach aprende de ella.'], 8: ['Tus operaciones llegan solas', 'NinjaTrader 8, Quantower o un CSV: nada más que escribir.'],
      9: ['Quédate en tu margen', 'Un día cerrado cuya pérdida quedó bajo tu riesgo permitido.'], 10: ['Sweep en tu pantalla de inicio', 'Instálalo, activa tus recordatorios: tu plan antes de la apertura.'], 11: ['Tu resumen semanal', 'Viernes: tu semana, tu regla para la siguiente.'], 12: ['Tu neto real', 'Mi dinero: los payouts menos las comisiones, lo que el trading te deja de verdad.'],
      13: ['Opera tu ventaja', 'Lo que te funciona, en Estadísticas: un plan que retoma su regla.'], 14: ['El plan guiado', 'Niveles, escenarios, ficha bloqueada: el plan de los días serios.'], 15: ['Tres días seguidos', 'Tres días completos: « Mi progreso » se abre.'] } };
  const x = M[L] || M.en;
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const st = () => (window.SweepGame && SweepGame.state && SweepGame.state().discovery) || null;
  /** « Do it now »: the page or the sheet of the mission (opening it ticks nothing) */
  function go(n) {
    const G = window.SweepGame, last = (S.trades || []).filter((t) => !t.demo && !t.untracked).slice(-1)[0], acc = (S.accounts || []).find((a) => !a.demo);
    const A = { 1: () => { location.hash = '#accounts'; }, 2: () => G && G.openPlan && G.openPlan(), 3: () => typeof openTicket === 'function' && openTicket(null), 4: () => G && G.openReview && G.openReview(),
      5: () => typeof openTicket === 'function' && openTicket(null), 6: () => typeof openTicket === 'function' && openTicket(null), 7: () => { location.hash = last ? '#trade/' + last.id : '#trades'; }, 8: () => { location.hash = '#settings'; },
      9: () => { location.hash = acc ? '#account/' + acc.id : '#accounts'; }, 10: () => window.SweepInstall && SweepInstall.show(), 11: () => G && G.open && G.open('weekly'), 12: () => { location.hash = '#payouts'; },
      13: () => { location.hash = '#analytics'; }, 14: () => window.SweepFiche && SweepFiche.open ? SweepFiche.open() : G && G.openPlan && G.openPlan(), 15: () => G && G.openReview && G.openReview() };
    (A[n] || (() => {}))();
  }
  function line() {
    const d = st(); if (!d || d.all || !d.current || sampleOnly()) return '';   // (31 Oct., C4) not beside the sample's 5 accounts
    const n = d.current, m = x[n] || ['', ''];
    return `<div class="nav-disc" data-disc="${n}"><small>${esc2(x.kick.replace('{n}', n).replace('{of}', d.of || 15))}</small><p><b>${esc2(m[0])}</b><span>${esc2(m[1])}</span></p><button type="button" class="btn sm" data-disc-go="${n}">${esc2(x.go)} ›</button></div>`;
  }
  /** what is not discovered yet is not shown */
  function apply() {
    const d = st(), sh = (d && d.shown) || { money: true, guided: true, game: true, ai: true }, b = document.body; if (!b) return;
    [['money', 'disc-no-money'], ['guided', 'disc-no-guided'], ['game', 'disc-no-game'], ['ai', 'disc-no-ai']].forEach(([k, c]) => { const on = !sh[k]; if (b.classList.contains(c) !== on) b.classList.toggle(c, on); });
    // mission 10, said by this device: installed, or the reminders on
    if (d && !d.all && !(d.done || []).includes(10) && S.settings && !(S.settings.discovery || {}).device) {
      const inst = (navigator.standalone === true) || (window.matchMedia && matchMedia('(display-mode: standalone)').matches);
      const push = (typeof Notification !== 'undefined' && Notification.permission === 'granted');
      if (inst || push) put('settings', Object.assign(structuredClone(S.settings), { discovery: Object.assign({}, S.settings.discovery, { device: true }) }));
    }
    // Settings › My routine: « Show everything »
    if (d && !d.all && route().v === 'settings') {
      const grp = [...document.querySelectorAll('#main details.nav-sgd')].find((g) => g.dataset.i === '1');
      if (grp && !grp.querySelector('.nav-disc-all')) grp.insertAdjacentHTML('beforeend', `<section class="surface pad nav-disc-all" data-noi18n><p class="muted">${esc2(x.allS)}</p><button type="button" class="btn" data-disc-all>${esc2(x.all)}</button></section>`);
    }
  }
  document.addEventListener('click', (e) => {
    const g = e.target.closest && e.target.closest('[data-disc-go]'); if (g) { go(+g.dataset.discGo); return; }
    const a = e.target.closest && e.target.closest('[data-disc-all]');
    if (a) { a.disabled = true; apiJSON('api/game/discovery/all', { method: 'POST', body: {} }).then(() => window.SweepGame && SweepGame.refresh && SweepGame.refresh()).then(() => setTimeout(() => { apply(); render(); }, 400)).catch(() => { a.disabled = false; }); }
  });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__disc) {
    const w = function () { const out = appRender.apply(this, arguments); try { apply(); } catch (e) { /* never blocks */ } return out; };
    w.__disc = true; window.render = w;
  }
  // « My progress » before mission 15: the streak only, and when the badges open (10 Nov.: drawn by the sheet itself, game.js progressHtml)
  const HUB = { en: 'Your badges open with mission 15: three days in a row.', fr: 'Tes badges s’ouvrent avec la mission 15 : trois journées de suite.',
    es: 'Tus insignias se abren con la misión 15: tres días seguidos.' };
  window.SweepDisc = { line, go, apply, hubNote: () => HUB[L] || HUB.en };
})();

/* ───────────── (31 Oct., brief « fluidité iOS 27 », lot 1) moving between pages like iOS ─────────────
 * 1 a tab change and a back are instant: no entry animation (only what appears in a page already shown animates);
 * 2 each tab keeps its scroll and its open sub-page; the active tab tapped: to the top, tapped again: to its root;
 * 3 back and forward put the scroll back exactly (history.scrollRestoration manual, the scroll kept per address);
 * 4 a sub-page (a trade, an account, Settings, What's new, My progress, Stats' detailed analysis) slides in from the right,
 *   the page under it leaves 30 % to the left, dimmed; back does the opposite (startViewTransition, else no animation);
 * 5 the installed app: a swipe from the left edge follows the finger and goes back past a third or when fast;
 * 6 phone: the tab bar shrinks to the active tab and the « + » while scrolling down, and comes back scrolling up. */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  try { history.scrollRestoration = 'manual'; } catch (e) { /* old browser */ }
  const view = (h) => (decodeURIComponent(String(h || '').replace(/^#/, '')) || 'dashboard').split('/')[0];
  const ROOT = { dashboard: 'dashboard', today: 'dashboard', trades: 'trades', calendar: 'trades', journal: 'trades', analytics: 'analytics', accounts: 'accounts', payouts: 'accounts' };
  const SUB = ['trade', 'account', 'settings', 'news', 'progress'];   // the brief's sub-pages (the others open as before)
  const depth = (h) => (SUB.includes(view(h)) || /^#analytics\/./.test(h || '') ? 1 : 0);   // (#analytics/deep and its tabs: Stats' detailed analysis)
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const pos = {}, mem = {};
  let shown = location.hash || '#dashboard', idx = 0, tab = ROOT[view(shown)] || 'dashboard', want = null, noVT = false;
  try { if (history.state && history.state.swI != null) idx = history.state.swI; else history.replaceState(Object.assign({}, history.state, { swI: 0 }), ''); } catch (e) { /* sandboxed */ }
  mem[tab] = shown;
  addEventListener('scroll', () => { if (!want) pos[shown] = scrollY; }, { passive: true });
  // the scroll a page opens at: kept for back, forward and a tab coming back; the top for a new page
  function place(y) {
    want = { y, t: Date.now() };
    const go = () => { if (!want) return; const max = document.documentElement.scrollHeight - innerHeight; scrollTo(0, Math.min(want.y, Math.max(0, max))); };
    go(); requestAnimationFrame(go); setTimeout(go, 120);
    setTimeout(() => { go(); want = null; pos[shown] = scrollY; }, 320);   // the cards that fill in after the first image
  }
  ['wheel', 'touchstart', 'keydown'].forEach((k) => addEventListener(k, () => { want = null; }, { passive: true }));   // the trader scrolls: his scroll wins
  let restoreTab = false;
  const r0 = window.render;
  const w = function () {
    const to = location.hash || '#dashboard';
    if (to === shown) return r0.apply(this, arguments);
    const st = history.state; let back = false;
    if (st && st.swI != null) { back = st.swI < idx; idx = st.swI; }
    else { idx += 1; try { history.replaceState(Object.assign({}, st, { swI: idx }), ''); } catch (e) { /* sandboxed */ } }
    const keep = back || (st && st.swI != null && !back) || restoreTab;   // back, forward, or a tab coming back to where it was
    const y = keep && pos[to] != null ? pos[to] : 0;
    const dir = depth(to) > depth(shown) ? 'push' : depth(to) < depth(shown) ? 'pop' : '';
    const from = shown; shown = to; restoreTab = false;
    if (ROOT[view(to)]) tab = ROOT[view(to)];
    mem[tab] = to;
    const args = arguments, self = this;
    const draw = () => { const out = r0.apply(self, args); try { dispatchEvent(new Event('sw:page')); window.SweepMO.flushAll(); queueMicrotask(() => { try { window.SweepMO.flushAll(); } catch (e) { /* never blocks */ } }); } catch (e) { /* never blocks */ } place(y); return out; };   // the page's own decorations in the same image, and once every wrapper of render has drawn (still before the image)   // the page's own decorations, in the same image
    if (dir && !noVT && document.startViewTransition && !document.hidden) {
      document.documentElement.dataset.vt = back && dir === 'push' ? 'pop' : dir;
      try { const vt = document.startViewTransition(draw); vt.ready.catch(() => {}); vt.updateCallbackDone.catch(() => {}); vt.finished.catch(() => {}).finally(() => { delete document.documentElement.dataset.vt; }); return; }   // (a transition skipped by the next one: never an error)
      catch (e) { delete document.documentElement.dataset.vt; }
    }
    noVT = false; pos[from] = pos[from] ?? 0;
    return draw();
  };
  w.__swnav = true; window.render = w;
  // 2 the tabs (phone bar and computer rail)
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('#bottomnav a[data-v], aside.side .nav a[data-v]'); if (!a || e.metaKey || e.ctrlKey) return;
    const t = ROOT[a.dataset.v]; if (!t) return;
    e.preventDefault();
    if (t === tab) {
      if (scrollY > 4) { scrollTo({ top: 0, behavior: reduced() ? 'auto' : 'smooth' }); return; }
      if (location.hash !== '#' + a.dataset.v) location.hash = '#' + a.dataset.v;
      return;
    }
    const h = mem[t] || '#' + a.dataset.v; restoreTab = true; noVT = true;
    if (location.hash === h) { restoreTab = false; noVT = false; return; }
    location.hash = h;
  }, true);
  // 5 the installed app: back from the left edge
  if (document.documentElement.classList.contains('pwa') || matchMedia('(display-mode: standalone)').matches) {
    let sx = null, sy = 0, st0 = 0, dx = 0, on = false;
    const pane = () => document.querySelector('.main-wrap');
    const busy = () => document.querySelector('.nav-am.open, #gSheet.open, .evp.open, .nav-dlg.open, #tkSlide.open, .sheet:not([hidden]), #navMenu.open');
    addEventListener('touchstart', (e) => { const t = e.touches[0]; sx = t.clientX < 20 && depth(shown) && !busy() ? t.clientX : null; sy = t.clientY; st0 = Date.now(); dx = 0; on = false; }, { passive: true });
    addEventListener('touchmove', (e) => {
      if (sx == null) return; const t = e.touches[0]; dx = Math.max(0, t.clientX - sx);
      if (!on && Math.abs(t.clientY - sy) > dx) { sx = null; return; }
      on = true; const p = pane(); if (p) { p.style.transition = 'none'; p.style.transform = `translateX(${dx}px)`; }
    }, { passive: true });
    addEventListener('touchend', () => {
      if (sx == null || !on) { sx = null; return; } sx = null;
      const p = pane(); if (!p) return; const fast = dx / Math.max(1, Date.now() - st0) > 0.5;
      p.style.transition = reduced() ? 'none' : 'transform .3s var(--spring)';
      if (dx > innerWidth / 3 || fast) { p.style.transform = 'translateX(100%)'; noVT = true; setTimeout(() => { history.back(); setTimeout(() => { p.style.transition = 'none'; p.style.transform = ''; }, 60); }, reduced() ? 0 : 260); }
      else { p.style.transform = ''; }
    });
  }
})();

/* ───────────── (31 Oct., fluidity 10) every touch target has a 44 × 44 area, its drawing unchanged ─────────────
 * A kind of target smaller than 44 px (its tag and classes) gets an invisible area around it, in a style sheet of its own
 * (its free ::after, else its ::before). The page's elements are never touched: the pages that redraw when their HTML differs
 * keep their nodes (a class added to them made them redraw, and a tapped answer lost its place). Measured after the first image,
 * so nothing it adds moves the page: an invisible area only, never a height. */
(function () {
  'use strict';
  const SEL = '#main a[href], #main button, #main [role=button], #main summary, #main [data-act], .main-wrap .top a, .main-wrap .top button';
  const STATE = /^(on|sel|active|open|is-|has-|nav-sw|pos|neg|z|p|n|fut|today|past|done|todo|wait|part|late|next)$/;
  const seen = new WeakSet(), rules = new Map();
  let sheet = null, t = 0;
  const free = (e, ps) => { const c = getComputedStyle(e, ps).content; return !c || c === 'none' || c === 'normal'; };
  // inside a box that scrolls: an area past its edge would give it a scrollbar (one that takes room on Linux and Windows)
  const inScroller = (e) => { for (let p = e.parentElement; p && p.id !== 'main' && p !== document.body; p = p.parentElement) { const c = getComputedStyle(p); if (/auto|scroll/.test(c.overflowX + c.overflowY)) return true; } return false; };
  const later = (fn) => (window.requestIdleCallback ? requestIdleCallback(fn, { timeout: 400 }) : setTimeout(fn, 120));
  const kind = (e) => {
    const at = e.closest('#main') ? '#main ' : '.main-wrap .top ';   // where it was measured only (never a sheet's link over its buttons)
    const cl = [...e.classList].filter((c) => !STATE.test(c) && /^[a-z][\w-]*$/i.test(c));
    if (cl.length) return at + e.tagName.toLowerCase() + '.' + cl.join('.');
    const p = e.parentElement, pc = p && [...p.classList].filter((c) => !STATE.test(c) && /^[a-z][\w-]*$/i.test(c))[0];
    return pc ? at + '.' + pc + ' > ' + e.tagName.toLowerCase() : '';
  };
  function pass() {
    let added = false; const fresh = [];
    document.querySelectorAll(SEL).forEach((e) => {
      if (seen.has(e) || !e.getClientRects().length) return;
      const r = e.getBoundingClientRect(); if (r.width < 1) return;
      seen.add(e);
      if (r.width >= 44 && r.height >= 44) return;
      if (e.parentElement && e.parentElement.closest('a[href], button, [role=button], summary')) return;
      const k = kind(e); if (!k || rules.has(k) || inScroller(e)) return;
      const ps = free(e, '::after') ? '::after' : free(e, '::before') ? '::before' : '';
      if (!ps) return;   // (a summary drawing both: its 44 px in nav.css, from the first image — never a height added later)
      // a static element whose children are placed against something above it: a position of its own would move them
      if (getComputedStyle(e).position === 'static' && [...e.querySelectorAll('*')].some((c) => /absolute|fixed/.test(getComputedStyle(c).position))) return;
      rules.set(k, rule(k, ps)); added = true; fresh.push(k);
    });
    // a new kind's area must leave every element of that kind exactly where and as big as it was (never in the flow)
    const box = (x) => { const r = x.getBoundingClientRect(); return Math.round(r.top) + ',' + Math.round(r.left) + ',' + Math.round(r.width) + ',' + Math.round(r.height); };
    const before = new Map(); fresh.forEach((k) => document.querySelectorAll(k).forEach((x) => before.set(x, box(x))));
    if (added) write();
    fresh.forEach((k) => { const v = rules.get(k) || '', ps = v.includes('::after{') ? '::after' : '::before';
      if ([...document.querySelectorAll(k)].some((x) => before.get(x) !== box(x) || getComputedStyle(x, ps).position !== 'absolute')) { rules.delete(k); write(); } });
    // a kind whose pseudo-element another page rule draws somewhere (a « › » on the routine's buttons): the other one, or none
    for (const [k, v] of [...rules]) {
      const ps = v.includes('::after{') ? '::after' : v.includes('::before{') ? '::before' : ''; if (!ps) continue;
      const els = [...document.querySelectorAll(k)].filter((e) => e.getClientRects().length);
      if (els.some(inScroller)) { rules.delete(k); write(); continue; }   // the same kind inside a scrolling box elsewhere: none
      if (els.every((e) => getComputedStyle(e, ps).content === '""')) continue;
      const other = ps === '::after' ? '::before' : '';
      rules.delete(k); write();
      if (other && els.every((e) => free(e, other))) { rules.set(k, rule(k, other)); write(); }
    }
  }
  // its area around itself: relative when nothing else positions it (:where, no weight: an element placed by the page keeps its place)
  const rule = (k, ps) => `:where(html body ${k}){position:relative}html body ${k}${ps}{content:"";position:absolute;left:50%;top:50%;width:max(100%,44px);height:max(100%,44px);transform:translate(-50%,-50%);background:transparent;pointer-events:auto}`;
  function write() { if (!sheet) { sheet = document.createElement('style'); sheet.id = 'sw-hit'; document.head.append(sheet); } sheet.textContent = [...rules.values()].join('\n'); }
  const soon = () => { if (!t) t = later(() => { t = 0; pass(); }); };
  new window.SweepMO(soon).observe(document.body, { childList: true, subtree: true });
  addEventListener('load', soon); addEventListener('hashchange', soon); document.addEventListener('toggle', soon, true);
})();

/* ───────────── (31 Oct., fluidity 12) Stats on a phone in about two screens ─────────────
 * Stats: the 4 figures, the score and the curve, « Patterns to watch » and the calendar, then « Detailed analysis › ». The rest
 * (drawdown, P&L breakdown and the « Deep dive » with its 10 tabs, durations among them: 10 Nov.) is one level down: #analytics/deep
 * (or a tab: #analytics/time…), a sub-page that slides in. Nothing removed: the same blocks, shown on one page or the other. */
(function () {
  'use strict';
  const T = { en: ['Detailed analysis ›', '‹ Stats', 'Show {n} more'], fr: ['Analyse détaillée ›', '‹ Stats', 'Voir les {n} autres'], es: ['Análisis detallado ›', '‹ Stats', 'Ver {n} más'] };
  const t = () => T[(typeof LANG !== 'undefined' && LANG) || 'en'] || T.en;
  function split() {
    const main = document.getElementById('main'); if (!main) return;
    const on = /^#analytics/.test(location.hash || '') && window.SW_MQ && SW_MQ.matches;
    if (!on) { main.classList.remove('st-main', 'st-deep'); return; }
    const box = main.querySelector('.g-top') && main.querySelector('.g-top').parentElement; if (!box) return;
    const two = box.querySelector(':scope > .g-two');
    [box.querySelector(':scope > .g-ins'), box.querySelector(':scope > .deep')].forEach((x) => { if (x && !x.classList.contains('st-detail')) x.classList.add('st-detail'); });
    [box.querySelector(':scope > .ikpis'), box.querySelector(':scope > .g-top'), two, [...box.querySelectorAll(':scope > section.ic')].pop()].forEach((x) => { if (x && !x.classList.contains('st-keep')) x.classList.add('st-keep'); });
    const deep = /^#analytics\/./.test(location.hash || '');
    main.classList.toggle('st-deep', deep); main.classList.toggle('st-main', !deep);
    if (!box.querySelector(':scope > .st-more')) box.insertAdjacentHTML('beforeend', `<a class="st-more" href="#analytics/deep" data-noi18n>${t()[0]}</a>`);
    // « Patterns to watch »: its first 3, the others open in place with one tap
    const ul = two && two.querySelector('ul.ins'), n = ul ? ul.children.length - 3 : 0;
    if (ul && n > 0 && !ul.nextElementSibling?.classList.contains('st-ins-more') && !ul.classList.contains('st-all')) ul.insertAdjacentHTML('afterend', `<button type="button" class="link st-ins-more" data-noi18n>${t()[2].replace('{n}', n)}</button>`);
    if (!main.querySelector(':scope > .st-back')) main.insertAdjacentHTML('afterbegin', `<a class="nav-back st-back" href="#analytics" data-noi18n>${t()[1]}</a>`);
  }
  new window.SweepMO(() => { try { split(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
  addEventListener('hashchange', () => { try { split(); } catch (e) { /* never blocks */ } });
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('.st-ins-more'); if (!b) return; const ul = b.previousElementSibling; if (ul) ul.classList.add('st-all'); b.remove(); });
})();

/* ───────────── Copy groups: a master account and its followers (brief « avance concurrentielle », step 2, 2 Nov.) ─────────────
 * Prop traders copy one master account on several accounts; typing the same trade five times kills the journal habit.
 * Built on the reusable groups of brief 02 part 4 (accounts' group_id, SweepCopy.make): the master is the account with
 * copy_lead, the followers are the other accounts of its group, each with a contract multiplier (copy_pct ÷ 100, ×1 by default).
 *  - Accounts › « Copy trading »: the groups, « Create a copy group » / « Edit » → one sheet (master, followers, ×);
 *  - a trade saved on the master: its followers are chosen in the form, in sight (SweepCopy.targets), never a follower synced
 *    itself (its own synced trade wins: no double); a synced master trade is copied by the server (sync/sync-store.php);
 *  - editing the trade (prices, times, size) or deleting it asks: the whole group, or this account only (askEdit, askDelete);
 *    the setup, grade, emotions and notes stay shared as before;
 *  - the Journal, Trades: one row « ×5 accounts » that unfolds (tradeRows, tradeTable in app.js).
 * Pro and Elite (limit copy_groups); Free sees the card and the plans sheet. */
(function () {
  'use strict';
  const NB = ' ';
  const TX = {
    en: { title: 'Copy trading', card: 'Log a trade once on a master account: Sweep puts it on its followers, sized by their multiplier.', create: 'Create a copy group', edit: 'Edit',
      sheet: 'Copy group', leadL: 'Master account', folL: 'Followers · contract multiplier', help: 'Each trade logged or synced on the master is copied to every follower, its P&L × the multiplier. Setup, grade, emotions and notes are shared.',
      synced: 'Synced: its own trades count, never a copy', save: 'Save the group', saved: 'Copy group saved', remove: 'Remove the group', removed: 'Copy group removed',
      fol1: '1 follower', folN: '{n} followers', lead: 'master', close: 'Close', less: 'Smaller', more: 'Larger',
      editT: 'Apply to the group?', editS: 'This trade is on {n} accounts. Make the same change on the other {k}? Setup, grade, emotions and notes are already shared.', editAll: 'Apply to all {n} accounts', editOne: 'Only this account',
      delT: 'Delete this trade?', delS: 'It is logged on {n} accounts.', delAll: 'Delete on all {n} accounts', delOne: 'Only on {a}', cancel: 'Cancel',
      roleLead: 'Master of a copy group: {f}', roleFol: 'Follows {m} · ×{x}' },
    fr: { title: 'Copy trading', card: `Saisis un trade une fois sur un compte maître${NB}: Sweep le reporte sur ses suiveurs, à la taille de leur multiplicateur.`, create: 'Créer un groupe de copie', edit: 'Modifier',
      sheet: 'Groupe de copie', leadL: 'Compte maître', folL: 'Suiveurs · multiplicateur de contrats', help: 'Chaque trade saisi ou synchronisé sur le maître est copié sur chaque suiveur, son P&L × le multiplicateur. Le setup, le grade, l’émotion et les notes sont partagés.',
      synced: `Synchronisé${NB}: ses propres trades comptent, jamais une copie`, save: 'Enregistrer le groupe', saved: 'Groupe de copie enregistré', remove: 'Retirer le groupe', removed: 'Groupe de copie retiré',
      fol1: '1 suiveur', folN: '{n} suiveurs', lead: 'maître', close: 'Fermer', less: 'Plus petit', more: 'Plus grand',
      editT: `Appliquer au groupe${NB}?`, editS: `Ce trade est sur {n} comptes. Faire la même modification sur les {k} autres${NB}? Le setup, le grade, l’émotion et les notes sont déjà partagés.`, editAll: 'Appliquer aux {n} comptes', editOne: 'Ce compte seulement',
      delT: `Supprimer ce trade${NB}?`, delS: 'Il est enregistré sur {n} comptes.', delAll: 'Supprimer sur les {n} comptes', delOne: 'Seulement sur {a}', cancel: 'Annuler',
      roleLead: `Maître d’un groupe de copie${NB}: {f}`, roleFol: 'Suit {m} · ×{x}' },
    es: { title: 'Copy trading', card: 'Registra una operación una vez en una cuenta maestra: Sweep la lleva a sus seguidoras, según su multiplicador.', create: 'Crear un grupo de copia', edit: 'Editar',
      sheet: 'Grupo de copia', leadL: 'Cuenta maestra', folL: 'Seguidoras · multiplicador de contratos', help: 'Cada operación registrada o sincronizada en la maestra se copia en cada seguidora, su P&L × el multiplicador. El setup, la calificación, la emoción y las notas se comparten.',
      synced: 'Sincronizada: cuentan sus propias operaciones, nunca una copia', save: 'Guardar el grupo', saved: 'Grupo de copia guardado', remove: 'Quitar el grupo', removed: 'Grupo de copia quitado',
      fol1: '1 seguidora', folN: '{n} seguidoras', lead: 'maestra', close: 'Cerrar', less: 'Más pequeño', more: 'Más grande',
      editT: '¿Aplicar al grupo?', editS: 'Esta operación está en {n} cuentas. ¿Hacer el mismo cambio en las otras {k}? El setup, la calificación, la emoción y las notas ya se comparten.', editAll: 'Aplicar a las {n} cuentas', editOne: 'Solo esta cuenta',
      delT: '¿Eliminar esta operación?', delS: 'Está registrada en {n} cuentas.', delAll: 'Eliminar en las {n} cuentas', delOne: 'Solo en {a}', cancel: 'Cancelar',
      roleLead: 'Maestra de un grupo de copia: {f}', roleFol: 'Sigue a {m} · ×{x}' } };
  const L = () => (typeof LANG !== 'undefined' && TX[LANG] ? LANG : 'en');
  const t = (k, o) => String(TX[L()][k] != null ? TX[L()][k] : TX.en[k]).replace(/\{(\w+)\}/g, (x, y) => (o && o[y] != null ? o[y] : x));
  const h = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const accs = () => (typeof S !== 'undefined' && S.accounts) || [];
  const usable = (a) => !!a && !a.demo && a.status !== 'archived' && a.status !== 'closed';
  const frozen = (id) => typeof billFrozen === 'function' && billFrozen(id);
  const can = () => (typeof billCan === 'function' ? billCan('copy_groups') : true);
  const nameOf = (id) => (typeof acctLabel === 'function' ? acctLabel(id) : ((accs().find((a) => a.id === id) || {}).name || ''));
  const mult = (a) => (a && +a.copy_pct > 0 ? +a.copy_pct : 100) / 100;
  const fx = (m) => { const s = String(Math.round(m * 100) / 100); return L() === 'en' ? s : s.replace('.', ','); };
  const STEPS = [0.5, 1, 2, 3, 4, 5, 6, 8, 10];   // contracts: half size (micro-style), then whole multiples
  /** the accounts synced with their platform (Settings › Connections): their own trades arrive, a copy would be a double */
  const linked = () => { try { const st = window.SweepSync && SweepSync.state(); return new Set(((st && st.accounts) || []).filter((x) => x.state === 'linked' && x.account_id).map((x) => x.account_id)); } catch (e) { return new Set(); } };

  /** the groups that have a master: [{ g, lead, followers }] */
  function leadGroups() {
    const out = [];
    for (const m of accs()) {
      if (!m.copy_lead || !m.group_id || !usable(m) || out.some((x) => x.g === m.group_id)) continue;
      const f = accs().filter((a) => a.group_id === m.group_id && a.id !== m.id && usable(a));
      if (f.length) out.push({ g: m.group_id, lead: m, followers: f });
    }
    return out;
  }
  /** the group with a master an account is in (master or follower), while the plan includes it */
  const leadOf = (id) => (can() ? leadGroups().find((x) => x.lead.id === id || x.followers.some((a) => a.id === id)) || null : null);
  /** where a new trade of this account is copied: from a master, its followers (not a synced one, not one paused by the plan);
   *  from a follower, nowhere; a group without a master (brief 02 part 4): every account of it, as before */
  function targets(id) {
    const a = accs().find((x) => x.id === id); if (!a || !a.group_id) return [];
    const G = leadOf(id);
    if (G) { if (G.lead.id !== id) return []; const ln = linked(); return G.followers.filter((x) => !ln.has(x.id) && !frozen(x.id)).map((x) => x.id); }
    return accs().filter((x) => x.group_id === a.group_id && x.id !== a.id && x.status !== 'archived').map((x) => x.id);
  }
  if (window.SweepCopy) Object.assign(window.SweepCopy, { targets, leadOf });

  /* ── the app's own window: two choices (never the browser's) ── */
  function ask(title, text, a, b, { danger = false, cancel = true, dflt = null } = {}) {
    return new Promise((done) => {
      const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-ask cg-ask-scrim';
      const el = document.createElement('aside'); el.className = 'nav-dlg nav-ask cg-ask'; el.setAttribute('role', 'alertdialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
      el.innerHTML = `<div class="nav-dlg-in"><h2>${h(title)}</h2><p class="nav-pass-s">${h(text)}</p><button type="button" class="btn primary ${danger ? 'danger' : ''} cg-ask-b" data-cg-ask="a">${h(a)}</button><button type="button" class="btn cg-ask-b" data-cg-ask="b">${h(b)}</button>${cancel ? `<button type="button" class="btn nav-pass-later cg-ask-b" data-cg-ask="0">${h(t('cancel'))}</button>` : ''}</div>`;
      document.body.append(scrim, el); requestAnimationFrame(() => { el.classList.add('open'); scrim.classList.add('open'); });
      const close = (v) => { [el, scrim].forEach((x) => { x.classList.remove('open'); setTimeout(() => x.remove(), 250); }); done(v); };
      el.addEventListener('click', (e) => { const x = e.target.closest('[data-cg-ask]'); if (x) close(x.dataset.cgAsk === '0' ? null : x.dataset.cgAsk); });
      scrim.addEventListener('click', () => close(dflt));
      setTimeout(() => { const x = el.querySelector('[data-cg-ask="b"]'); if (x) x.focus(); }, 50);
    });
  }
  /** an edited trade with copies: true = the same change on every account */
  const askEdit = (id, n) => ask(t('editT'), t('editS', { n, k: n - 1 }), t('editAll', { n }), t('editOne'), { cancel: false, dflt: 'b' }).then((v) => v === 'a');
  /** a trade with copies to delete: 'all', 'one' or null */
  function askDelete(id) {
    const d = typeof getDoc === 'function' && getDoc('trades', id); if (!d) return Promise.resolve(null);
    const n = (typeof siblings === 'function' ? siblings(id).length : 0) + 1;
    return ask(t('delT'), t('delS', { n }), t('delAll', { n }), t('delOne', { a: nameOf(d.account_id) }), { danger: true }).then((v) => (v === 'a' ? 'all' : v === 'b' ? 'one' : null));
  }

  /* ── Accounts › « Copy trading » ── */
  function lineOf(G) { return `→ ${G.followers.map((a) => `${h(nameOf(a.id))} <span class="cg-x">×${fx(mult(a))}</span>`).join(' · ')}`; }
  function cardHtml() {
    const G = leadGroups(), ok = can(), taken = new Set(G.flatMap((x) => [x.lead.id, ...x.followers.map((a) => a.id)])), room = accs().filter((a) => usable(a) && !taken.has(a.id)).length >= 2;
    const rows = ok ? G.map((x) => `<button type="button" class="cg-grp" data-cg-edit="${h(x.g)}"><span class="cg-grp-t"><b>${h(nameOf(x.lead.id))}</b><small>${h(t('lead'))} · ${h(x.followers.length === 1 ? t('fol1') : t('folN', { n: x.followers.length }))}</small><span class="cg-grp-l">${lineOf(x)}</span></span><span class="cg-grp-e">${h(t('edit'))}</span></button>`).join('') : '';
    return `<div class="sec-h"><h2>${h(t('title'))}</h2></div><div class="surface pad cg-box">${rows || `<p class="cg-pitch">${h(t('card'))}</p>`}${rows && !room ? '' : `<button type="button" class="btn sm cg-new" data-cg-new>${h(t('create'))}${ok ? '' : ' <em class="cg-pro">Pro</em>'}</button>`}</div>`;
  }
  function card() {
    if (!/^#accounts$/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main) return;
    const tbl = main.querySelector('table.acct-tbl'), sec = tbl && tbl.closest('section'); if (!sec) return;
    const show = accs().filter(usable).length >= 2;   // copy trading shows from the 2nd account (SWEEP.md, missions: « au 2ᵉ compte »)
    let el = main.querySelector('.cg-card');
    if (!show) { if (el) el.remove(); return; }
    const html = cardHtml();
    if (!el) { el = document.createElement('section'); el.className = 'sec cg-card'; el.setAttribute('data-noi18n', ''); sec.after(el); }
    else if (el.previousElementSibling !== sec) sec.after(el);
    if (el.__h !== html) { el.innerHTML = html; el.__h = html; }
  }
  /* the account page: its role in the group, and « Edit » (the line « Copy group: … » of brief 02 part 4) */
  function accountLine() {
    const m = /^#account\/([^/]+)/.exec(location.hash || ''); if (!m) return;
    const main = document.getElementById('main'), gb = main && main.querySelector('.nav-grp'); if (!gb || gb.querySelector('.cg-role')) return;
    const id = decodeURIComponent(m[1]), G = leadOf(id); if (!G) return;
    const me = accs().find((a) => a.id === id);
    const txt = G.lead.id === id ? t('roleLead', { f: G.followers.length === 1 ? t('fol1') : t('folN', { n: G.followers.length }) }) : t('roleFol', { m: nameOf(G.lead.id), x: fx(mult(me)) });
    gb.insertAdjacentHTML('beforeend', `<small class="help cg-role" data-noi18n>${h(txt)} · <button type="button" class="link" data-cg-edit="${h(G.g)}">${h(t('edit'))}</button></small>`);
  }

  /* ── the sheet ── */
  const CG = { g: null, lead: null, sel: new Map() };
  function sheet() {
    let el = document.getElementById('cgSheet'); if (el) return el;
    el = document.createElement('aside'); el.id = 'cgSheet'; el.className = 'evp sysh cgsh';
    el.setAttribute('data-noi18n', ''); el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true');
    el.innerHTML = '<div class="evp-in sy-in cg-in"></div>'; document.body.append(el);
    const sc = document.createElement('div'); sc.id = 'cgScrim'; sc.className = 'evp-scrim'; sc.addEventListener('click', close); document.body.append(sc);
    if (typeof swipeDismiss === 'function') swipeDismiss(el, { scroller: () => el.querySelector('.evp-in'), onClose: close, ignore: '.cg-chips, .cg-step' });
    return el;
  }
  const X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  function viewHtml() {
    const list = accs().filter(usable), ln = linked();
    const others = list.filter((a) => a.id !== CG.lead);
    return `<div class="sy-head"><h2>${h(t('sheet'))}</h2><button type="button" class="sy-x" data-cg="close" aria-label="${h(t('close'))}">${X}</button></div>
      <p class="sy-note">${h(t('help'))}</p>
      <p class="sy-q">${h(t('leadL'))}</p>
      <div class="cg-chips" role="radiogroup">${list.map((a) => `<button type="button" class="chip${a.id === CG.lead ? ' on' : ''}" role="radio" aria-checked="${a.id === CG.lead}" data-cg-lead="${h(a.id)}">${h(nameOf(a.id))}</button>`).join('')}</div>
      <p class="sy-q">${h(t('folL'))}</p>
      <div class="sy-opts cg-fol">${others.map((a) => { const on = CG.sel.has(a.id), m = CG.sel.get(a.id) || mult(a), i = STEPS.indexOf(m);
        return `<div class="cg-f${on ? ' on' : ''}"><button type="button" class="sy-opt cg-pick${on ? ' on' : ''}" role="checkbox" aria-checked="${on}" data-cg-pick="${h(a.id)}"><i></i><span>${h(nameOf(a.id))}${ln.has(a.id) ? `<small>${h(t('synced'))}</small>` : ''}</span></button>${on ? `<span class="cg-step"><button type="button" data-cg-m="-1" data-id="${h(a.id)}" aria-label="${h(t('less'))}"${i === 0 ? ' disabled' : ''}>−</button><b>×${fx(m)}</b><button type="button" data-cg-m="1" data-id="${h(a.id)}" aria-label="${h(t('more'))}"${i === STEPS.length - 1 ? ' disabled' : ''}>+</button></span>` : ''}</div>`; }).join('')}</div>
      <button type="button" class="btn primary sy-main" data-cg="save"${CG.sel.size ? '' : ' disabled'}>${h(t('save'))}</button>${CG.g ? `<button type="button" class="btn danger sy-wide" data-cg="remove">${h(t('remove'))}</button>` : ''}`;
  }
  function paint() { const el = document.getElementById('cgSheet'); if (el) el.querySelector('.cg-in').innerHTML = viewHtml(); }
  function open(g) {
    if (!can()) { if (window.SweepBilling && SweepBilling.paywall) SweepBilling.paywall('copy_groups'); return; }
    const list = accs().filter(usable); if (list.length < 2) return;
    const G = g ? leadGroups().find((x) => x.g === g) : null;
    if (G) { CG.g = G.g; CG.lead = G.lead.id; CG.sel = new Map(G.followers.map((a) => [a.id, snap(mult(a))])); }
    else {
      const taken = new Set(leadGroups().flatMap((x) => [x.lead.id, ...x.followers.map((a) => a.id)]));
      const free = list.filter((a) => !taken.has(a.id)), lead = free[0] || list[0];
      CG.g = null; CG.lead = lead.id; CG.sel = new Map(free.filter((a) => a.id !== lead.id).map((a) => [a.id, snap(mult(a))]));
    }
    const el = sheet(); paint(); el.setAttribute('aria-label', t('sheet'));
    requestAnimationFrame(() => { el.classList.add('open'); document.getElementById('cgScrim').classList.add('open'); document.body.classList.add('evp-lock'); });
  }
  const snap = (m) => STEPS.reduce((b, s) => (Math.abs(s - m) < Math.abs(b - m) ? s : b), 1);
  function close() {
    const el = document.getElementById('cgSheet'); if (!el) return;
    el.classList.remove('open'); const sc = document.getElementById('cgScrim'); if (sc) sc.classList.remove('open');
    if (!document.querySelector('.evp.open')) document.body.classList.remove('evp-lock');
  }
  /** a group left with one account is no group */
  function tidy(ids) { ids.forEach((g) => { const rest = accs().filter((a) => a.group_id === g); if (rest.length === 1) editDoc('accounts', rest[0].id, (d) => { delete d.group_id; delete d.copy_lead; }); }); }
  function save() {
    if (!CG.sel.size || !CG.lead) return;
    const g = CG.g || 'grp-' + (typeof uid === 'function' ? uid() : Date.now().toString(36));
    const keep = new Set([CG.lead, ...CG.sel.keys()]), left = new Set();
    accs().filter((a) => a.group_id === g && !keep.has(a.id)).forEach((a) => editDoc('accounts', a.id, (d) => { delete d.group_id; delete d.copy_lead; }));
    for (const id of keep) {
      const a = accs().find((x) => x.id === id); if (a && a.group_id && a.group_id !== g) left.add(a.group_id);
      editDoc('accounts', id, (d) => {
        d.group_id = g;
        if (id === CG.lead) d.copy_lead = true;
        else { delete d.copy_lead; const m = CG.sel.get(id) || 1; if (m === 1) delete d.copy_pct; else d.copy_pct = Math.round(m * 100); }
      });
    }
    tidy(left);
    close(); if (typeof toast === 'function') toast(t('saved')); if (typeof render === 'function') render();
  }
  function remove() {
    const g = CG.g; if (!g) return;
    const was = accs().filter((a) => a.group_id === g).map((a) => ({ id: a.id, g: a.group_id, lead: !!a.copy_lead }));
    was.forEach((x) => editDoc('accounts', x.id, (d) => { delete d.group_id; delete d.copy_lead; }));   // the trades stay as they are
    close(); if (typeof render === 'function') render();
    const undo = () => { was.forEach((x) => editDoc('accounts', x.id, (d) => { d.group_id = x.g; if (x.lead) d.copy_lead = true; })); if (typeof render === 'function') render(); };
    if (window.SweepUndo && SweepUndo.toast) SweepUndo.toast(t('removed'), undo); else if (typeof toast === 'function') toast(t('removed'));
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-cg-new], [data-cg-edit], #cgSheet [data-cg], #cgSheet [data-cg-lead], #cgSheet [data-cg-pick], #cgSheet [data-cg-m]'); if (!b) return;
    e.preventDefault();
    if (b.hasAttribute('data-cg-new')) return open(null);
    if (b.dataset.cgEdit) return open(b.dataset.cgEdit);
    if (b.dataset.cgLead) { const was = CG.lead; CG.lead = b.dataset.cgLead; CG.sel.delete(CG.lead); if (was && was !== CG.lead) CG.sel.set(was, 1); return paint(); }
    if (b.dataset.cgPick) { const id = b.dataset.cgPick; if (CG.sel.has(id)) CG.sel.delete(id); else CG.sel.set(id, snap(mult(accs().find((a) => a.id === id)))); return paint(); }
    if (b.dataset.cgM) { const id = b.dataset.id, i = STEPS.indexOf(CG.sel.get(id) || 1), j = Math.min(STEPS.length - 1, Math.max(0, i + +b.dataset.cgM)); CG.sel.set(id, STEPS[j]); return paint(); }
    const k = b.dataset.cg;
    if (k === 'close') close(); else if (k === 'save') save(); else if (k === 'remove') remove();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.querySelector('#cgSheet.open')) { e.stopPropagation(); close(); } }, true);

  window.SweepCopyGroup = { leadGroups, leadOf, targets, askEdit, askDelete, open, close };
  new window.SweepMO(() => { [card, accountLine].forEach((f) => { try { f(); } catch (e) { if (!f.__warned) { f.__warned = true; console.warn('Sweep:', f.name, e && e.message); } } }); }).observe(document.body, { childList: true, subtree: true });
})();

/* (2 Nov., tour visuel 14) the numbers of the chart axes at the app's small text size, 11 px in Geist Mono: a chart is drawn on a fixed
   width (its viewBox) and shrunk into its card, and its 11 units read about 6 px — the size is set again from the chart's real scale */
(function () {
  'use strict';
  let raf = 0;
  function fit() {
    raf = 0;
    document.querySelectorAll('#main svg.chart').forEach((s) => {
      const vb = s.viewBox && s.viewBox.baseVal, w = s.getBoundingClientRect().width; if (!vb || !vb.width || !w) return;
      // (3 Nov.) the amounts on the left, at 11 px, went past the chart's edge (« 0 k $ » for « −20 k $ »): the view opens to the left
      // of 0 by what the widest needs, its height in proportion — the drawing narrows a little inside a box of the same size (nothing
      // moves on the page, e2e_page_shift); worked out from the drawn width (W0) and from the characters (Geist Mono, 0.6 em each:
      // the same before and after the font loads), so the same on every pass
      if (!s.dataset.vb0) s.dataset.vb0 = [vb.x, vb.y, vb.width, vb.height].join(' ');
      const [, , W0, H0] = s.dataset.vb0.split(' ').map(Number), tx = [...s.querySelectorAll(':scope > text')], y = Math.max(...tx.map((t) => +t.getAttribute('y') || 0));
      let pu = 0;
      tx.filter((t) => +t.getAttribute('y') !== y && t.getAttribute('text-anchor') === 'end').forEach((t) => { const ax = +t.getAttribute('x') || 0, px = t.textContent.length * 6.6 + 2; if (px < w) pu = Math.max(pu, Math.ceil((px * W0 / w - ax) / (1 - px / w))); });
      const vw = W0 + pu, vh = H0 * vw / W0, want = [-pu, -(vh - H0) / 2, vw, vh].map((n) => +n.toFixed(1)).join(' ');
      if (s.getAttribute('viewBox') !== want) s.setAttribute('viewBox', want);
      const fs = (11 * vw / w).toFixed(1); if (s.dataset.fs !== fs) { s.dataset.fs = fs; s.style.setProperty('--ax-fs', fs + 'px'); }
      // the dates under the chart at that size: one that would touch the one before it skips (« 12 oct.15 oct. » at the end, 3 Nov.)
      let right = -Infinity;
      tx.filter((t) => +t.getAttribute('y') === y).sort((a, b) => +a.getAttribute('x') - +b.getAttribute('x')).forEach((t) => {
        t.style.display = ''; const r = t.getBBox();
        if (r.x < right + fs * 0.6) t.style.display = 'none'; else right = r.x + r.width;
      });
    });
  }
  const soon = () => { if (!raf) raf = requestAnimationFrame(fit); };
  addEventListener('sw:page', soon); addEventListener('resize', soon); document.addEventListener('toggle', soon, true);   // (a chart in a folded card: sized when it opens)
  const go = () => { const m = document.getElementById('main'); if (!m) { setTimeout(go, 300); return; } new MutationObserver(soon).observe(m, { childList: true, subtree: true }); soon(); };
  go();
})();

/* (2 Nov., tour visuel 19) Stats › durations in Spanish: its two choices without « Por », side by side in their card (8 px cut) */
if (window.I18N_ES) { window.I18N_ES['By % of trades'] = '% de operaciones'; window.I18N_ES['By win rate'] = 'Tasa de acierto'; }

/* ───────────── The account guardian (brief « Gardien de compte », 3 Nov., SWEEP.md section 8) ─────────────
 * On top of Today: how much the account most at risk can still lose today (« Risk left today ») with its room as a bar — blue
 * while calm, gold from « watch » —, one calm sentence, the other accounts as pills (a tap shows one; Free: one account, the
 * others locked with a link to the plans). A tap on the card opens its sheet: the two floors, the room, the consistency, the
 * target, and what the firm's rules do not say. Every number comes from the server (guard/guard.php, api/guardian). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { title: 'Account guardian', risk: 'Risk left today', calm: 'You have room. Trade your plan.', watch: 'Half your room is used. Slow down, A+ setups only.',
      danger: 'One more loss could cost this account. Protect it.', stoppedT: 'Session done. That’s discipline.', stoppedS: 'You hit your stop rule. Closing now keeps tomorrow’s account alive.',
      breached: 'This account crossed its limit. Your history stays safe in Sweep.', close: 'Close my day', update: 'Update', estimate: 'Estimate', missing: 'Not set in this firm’s rules',
      ddFloor: 'Drawdown floor', ddFloorS: 'The balance this account must stay above.', dayFloor: 'Daily floor', dayFloorS: 'Today’s lowest balance allowed: the start of the day minus the daily loss limit.',
      room: 'Room', roomS: 'Your balance minus the higher floor: {a} at the start of the day.', bal: 'Balance now', pnl: 'Today', plan: 'Planned risk', planS: 'Your plan’s max loss for the day.',
      cons: 'Consistency', consS: 'Your best day’s share of your profit: {p} of {l} allowed.', consNone: 'No profit yet: it counts from your first winning days.', consMax: 'Up to {m} more today keeps it.',
      goal: 'Profit target', goalS: '{m} left to reach {t}.', days: 'Trading days', daysS: '{n} more of {m}.', notSet: 'Not available', estS: 'Trailing trade by trade: Sweep sees your closed trades, not the highs of an open trade. Synced accounts are exact.',
      types: { static: 'static', eod: 'trailing at the end of the day', trade: 'trailing trade by trade', live: 'live: your balance' },
      keys: { dd: 'Drawdown floor', dll: 'Daily loss limit', consistency: 'Consistency rule', target: 'Profit target', min_days: 'Minimum trading days' },
      more: 'Every account with Pro', locked: 'With Pro, the guardian watches every account.', levels: { calm: 'Calm', watch: 'Watch', danger: 'Danger', stopped: 'Stopped', breached: 'Limit crossed' },
      upT: 'Balance now', upS: 'The balance {p} shows right now. Sweep uses it until your next trade is saved, then proposes it when you close your day.', upSave: 'Save', upBad: 'Enter the balance your platform shows.', upDone: 'Updated', stTrades: 'Trades today', stPnl: 'Today’s P&L' },
    fr: { title: 'Gardien de compte', risk: 'Risque restant aujourd’hui', calm: 'Tu as de la marge. Suis ton plan.', watch: 'La moitié de ta marge est utilisée. Ralentis, seulement tes meilleurs setups.',
      danger: 'Encore une perte pourrait coûter ce compte. Protège-le.', stoppedT: 'Séance terminée. C’est ça, la discipline.', stoppedS: 'Tu as atteint ta règle d’arrêt. Fermer maintenant garde ton compte en vie pour demain.',
      breached: 'Ce compte a dépassé sa limite. Ton historique reste en sécurité dans Sweep.', close: 'Fermer ma journée', update: 'Mettre à jour', estimate: 'Estimation', missing: 'Non défini dans les règles de cette firme',
      ddFloor: 'Plancher de drawdown', ddFloorS: 'Le solde au-dessus duquel ce compte doit rester.', dayFloor: 'Plancher du jour', dayFloorS: 'Le plus bas solde permis aujourd’hui : le début de la journée moins la perte journalière max.',
      room: 'Marge', roomS: 'Ton solde moins le plus haut des planchers : {a} au début de la journée.', bal: 'Solde actuel', pnl: 'Aujourd’hui', plan: 'Risque prévu', planS: 'La perte max de ton plan du jour.',
      cons: 'Consistance', consS: 'La part de ton meilleur jour dans ton profit : {p} sur {l} permis.', consNone: 'Pas encore de profit : elle compte dès tes premiers jours gagnants.', consMax: 'Jusqu’à {m} de plus aujourd’hui la garde.',
      goal: 'Objectif de profit', goalS: 'Encore {m} pour atteindre {t}.', days: 'Jours de trading', daysS: 'Encore {n} sur {m}.', notSet: 'Non disponible', estS: 'Suiveur trade par trade : Sweep voit tes trades fermés, pas les hauts d’un trade ouvert. Les comptes synchronisés sont exacts.',
      types: { static: 'statique', eod: 'suiveur en fin de journée', trade: 'suiveur trade par trade', live: 'live : ton solde' },
      keys: { dd: 'Plancher de drawdown', dll: 'Perte journalière max', consistency: 'Règle de consistance', target: 'Objectif de profit', min_days: 'Jours de trading minimums' },
      more: 'Tous les comptes avec Pro', locked: 'Avec Pro, le Gardien veille sur tous tes comptes.', levels: { calm: 'Calme', watch: 'Attention', danger: 'Danger', stopped: 'Arrêt', breached: 'Limite dépassée' },
      upT: 'Solde actuel', upS: 'Le solde affiché par {p} en ce moment. Sweep l’utilise jusqu’à ton prochain trade enregistré, puis te le propose quand tu fermes ta journée.', upSave: 'Enregistrer', upBad: 'Entre le solde affiché par ta plateforme.', upDone: 'Mis à jour', stTrades: 'Trades du jour', stPnl: 'P&L du jour' },
    es: { title: 'Guardián de cuenta', risk: 'Riesgo restante hoy', calm: 'Tienes margen. Sigue tu plan.', watch: 'Usaste la mitad de tu margen. Baja el ritmo, solo tus mejores setups.',
      danger: 'Una pérdida más podría costarte esta cuenta. Protégela.', stoppedT: 'Sesión terminada. Eso es disciplina.', stoppedS: 'Alcanzaste tu regla de stop. Cerrar ahora mantiene viva tu cuenta para mañana.',
      breached: 'Esta cuenta superó su límite. Tu historial sigue a salvo en Sweep.', close: 'Cerrar mi día', update: 'Actualizar', estimate: 'Estimación', missing: 'No definido en las reglas de esta firma',
      ddFloor: 'Piso de drawdown', ddFloorS: 'El saldo por encima del cual debe quedarse esta cuenta.', dayFloor: 'Piso del día', dayFloorS: 'El saldo más bajo permitido hoy: el inicio del día menos la pérdida diaria máx.',
      room: 'Margen', roomS: 'Tu saldo menos el piso más alto: {a} al inicio del día.', bal: 'Saldo actual', pnl: 'Hoy', plan: 'Riesgo previsto', planS: 'La pérdida máx. de tu plan del día.',
      cons: 'Consistencia', consS: 'La parte de tu mejor día en tu beneficio: {p} de {l} permitido.', consNone: 'Aún sin beneficio: cuenta desde tus primeros días ganadores.', consMax: 'Hasta {m} más hoy la mantiene.',
      goal: 'Objetivo de beneficio', goalS: 'Faltan {m} para llegar a {t}.', days: 'Días de trading', daysS: 'Faltan {n} de {m}.', notSet: 'No disponible', estS: 'Dinámico operación por operación: Sweep ve tus operaciones cerradas, no los máximos de una operación abierta. Las cuentas sincronizadas son exactas.',
      types: { static: 'estático', eod: 'dinámico al cierre del día', trade: 'dinámico operación por operación', live: 'live: tu saldo' },
      keys: { dd: 'Piso de drawdown', dll: 'Pérdida diaria máx.', consistency: 'Regla de consistencia', target: 'Objetivo de beneficio', min_days: 'Días de trading mínimos' },
      more: 'Todas las cuentas con Pro', locked: 'Con Pro, el guardián vigila todas tus cuentas.', levels: { calm: 'Calma', watch: 'Atención', danger: 'Peligro', stopped: 'Parada', breached: 'Límite superado' },
      upT: 'Saldo actual', upS: 'El saldo que muestra {p} ahora mismo. Sweep lo usa hasta tu próxima operación guardada, y te lo propone al cerrar tu día.', upSave: 'Guardar', upBad: 'Introduce el saldo que muestra tu plataforma.', upDone: 'Actualizado', stTrades: 'Operaciones de hoy', stPnl: 'P&L de hoy' },
  };
  const X = T[L] || T.en;
  const t = (k, v) => String(X[k]).replace(/\{(\w)\}/g, (m0, x) => (v && v[x] != null ? v[x] : ''));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const usd = (c, sign) => (typeof money === 'function' ? money(c, { sign: !!sign, dec: 0 }) : '$' + Math.round(c / 100));
  const pct = (v) => (L === 'en' ? v + '%' : String(v).replace('.', ',') + ' %');
  const LOCK = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 7V5a3 3 0 0 1 6 0v2h.5A1.5 1.5 0 0 1 13 8.5v5a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 3 13.5v-5A1.5 1.5 0 0 1 4.5 7H5Zm1.5 0h3V5a1.5 1.5 0 0 0-3 0v2Z"/></svg>';
  const G = { st: null, at: 0, busy: false, pick: null };
  try { G.pick = sessionStorage.getItem('sw.guardPick'); } catch (e) { /* private mode */ }
  const onToday = () => /^#?(dashboard)?$/.test((location.hash || '').replace(/^#/, ''));
  const tone = (lv) => (lv === 'calm' ? 'ok' : 'warn');
  const shown = () => { const a = (G.st && G.st.accounts) || []; return a.find((x) => x.id === G.pick && !x.locked) || a[0] || null; };
  const line = (g) => (g.level === 'stopped' ? t('stoppedT') : t(g.level));

  async function load(force) {
    if ((typeof S === 'undefined' || S.mode !== 'server') || typeof apiJSON !== 'function') return;
    if (G.busy) { if (force) G.again = true; return; }   // a save during a load: once more after it
    if (!force && G.st && Date.now() - G.at < 30000) return;
    G.busy = true; G.again = false;
    try { G.st = await apiJSON('api/guardian'); G.at = Date.now(); try { localStorage.setItem('sw.guard', JSON.stringify({ uid: S.uid, st: G.st })); } catch (x) { /* private mode */ } } catch (e) { /* the guardian never blocks Today */ }
    G.busy = false; place(); paintSheet(); stopSheet();
    if (G.again) load(true);
  }
  let soonT = 0; const soon = (ms) => { clearTimeout(soonT); soonT = setTimeout(() => load(true), ms || 800); };

  /* the last numbers seen on this device (the same trader, the same session): the card is there at Today's first image, nothing
     pushed down when the server answers (e2e_page_shift) */
  function cached() {
    if (G.st || G.noCache || typeof S === 'undefined' || !S.uid) return; G.noCache = true;
    try { const c = JSON.parse(localStorage.getItem('sw.guard') || 'null'); if (c && c.uid === S.uid && c.st && c.st.day === (typeof todayStr === 'function' ? todayStr() : '')) G.st = c.st; } catch (e) { /* private mode */ }
  }
  function cardHtml() {
    cached();
    const g = shown(); if (!g) return '';
    const all = G.st.accounts, w = g.room_pct == null ? 0 : Math.max(0, Math.min(100, g.room_pct));
    const big = g.level === 'breached' ? 0 : g.left_c;
    const pills = all.length > 1 ? `<div class="nav-guard-pills" role="group" aria-label="${esc2(t('title'))}">${all.map((a) => a.locked
      ? `<a class="nav-guard-pill is-locked" href="#plan" title="${esc2(t('locked'))}">${LOCK}<span>${esc2(a.name)}</span></a>`
      : `<button type="button" class="nav-guard-pill${a.id === g.id ? ' on' : ''}" data-guard-pick="${esc2(a.id)}" aria-pressed="${a.id === g.id}"><i class="nav-guard-dot ${tone(a.level)}" aria-hidden="true"></i><span>${esc2(a.name)}</span></button>`).join('')}</div>` : '';
    return `<section class="surface nav-guard lv-${g.level} ${tone(g.level)}" data-noi18n data-guard="${esc2(g.id)}">
      <div class="nav-guard-main" role="button" tabindex="0" data-guard-open aria-label="${esc2(t('title') + ' · ' + g.name)}">
        <div class="nav-guard-h"><small>${esc2(t('title'))}</small><b class="nav-guard-acc">${esc2(g.name)}</b>${g.estimate ? `<span class="nav-guard-est">${esc2(t('estimate'))}</span>` : ''}</div>
        <div class="nav-guard-v"><span>${esc2(t('risk'))}</span><b class="nav-guard-n">${big == null ? '—' : esc2(usd(big))}</b></div>
        ${g.room_c == null ? '' : `<i class="nav-guard-bar" aria-hidden="true"><i style="width:${w.toFixed(1)}%"></i></i>`}
        <p class="nav-guard-msg">${esc2(line(g))}</p>
      </div>${g.synced ? '' : `<button type="button" class="link nav-guard-up" data-guard-up="${esc2(g.id)}">${esc2(t('update'))}</button>`}${pills}</section>`;
  }
  function place() {
    if (!onToday()) return;
    const col = document.querySelector('#main .nav-dash .d-col-a'); if (!col) return;
    let el = col.querySelector(':scope > .nav-guard');
    const html = cardHtml();
    if (!html) { if (el) el.remove(); return; }
    if (el && !el._h && el.outerHTML.replace(/\s+/g, ' ') === html.trim().replace(/\s+/g, ' ')) el._h = html;   // the one drawn with Today
    if (el && el._h === html) { if (col.firstElementChild !== el) col.prepend(el); return; }
    const tmp = document.createElement('div'); tmp.innerHTML = html; const nx = tmp.firstElementChild; nx._h = html;
    const sx = el && el.querySelector('.nav-guard-pills') ? el.querySelector('.nav-guard-pills').scrollLeft : 0;
    if (el) el.replaceWith(nx); else col.prepend(nx);
    const pl = nx.querySelector('.nav-guard-pills'); if (pl && sx) pl.scrollLeft = sx;
  }

  /* step 5: the stop rule reached (Pro and Elite; the day's lock recorded by the server, game/game.php): once a day, a calm sheet —
     full screen on a phone — with the day in two numbers and « Close my day » (the review, in one tap). Nothing is blocked: the +
     and the trades stay; Sweep cannot stop orders on the trading platform and never says so. Seen: journals/{day}.guard.stop_seen. */
  function stopSheet() {
    const st = G.st, lk = st && st.stop_rule && st.stop; if (!lk || !onToday() || !window.SweepGame || !SweepGame.ui || !SweepGame.openReview) return;
    const j = typeof getDoc === 'function' ? getDoc('journals', st.day) : null;
    if ((j && j.guard && j.guard.stop_seen) || (j && j.post && j.post.reviewed_at) || G.stopShown === st.day) return;
    if (document.querySelector('#gSheet, .evp.open, .sb-layer, .nt-modal')) { setTimeout(stopSheet, 2500); return; }   // never over another sheet: a bit later
    G.stopShown = st.day;
    editDoc('journals', st.day, (d) => { d.guard = Object.assign({}, d.guard, { stop_seen: new Date().toISOString() }); });
    SweepGame.ui.sheet(`${SweepGame.ui.head('', '')}<div class="nav-guard-stopin">
      <span class="nav-lock-ic" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></span>
      <h2>${esc2(t('stoppedT'))}</h2><p class="nav-guard-stopt">${esc2(t('stoppedS'))}</p>
      <div class="nav-guard-stopn"><div><small>${esc2(t('stPnl'))}</small><b class="${lk.net_c > 0 ? 'pos' : lk.net_c < 0 ? 'neg' : ''}">${esc2(usd(lk.net_c, true))}</b></div><div><small>${esc2(t('stTrades'))}</small><b>${esc2(String(lk.n))}</b></div></div>
      <button type="button" class="btn primary g-big" data-guard-close>${esc2(t('close'))}</button></div>`, { cls: 'nav-guard-stop' });
  }

  /* the sheet: every number of the account shown */
  const row = (k, v, sub, cls) => `<div class="nav-guard-r${cls ? ' ' + cls : ''}"><div><b>${esc2(k)}</b>${sub ? `<small>${esc2(sub)}</small>` : ''}</div><span class="nav-guard-rv">${v}</span></div>`;
  function sheetHtml(g) {
    const f = g.floors || {}, r = [];
    if (f.drawdown_c != null) r.push(row(t('ddFloor'), esc2(usd(f.drawdown_c)), t('ddFloorS') + (f.type ? ' (' + (X.types[f.type] || f.type) + ')' : '')));
    if (f.daily_c != null) r.push(row(t('dayFloor'), esc2(usd(f.daily_c)), t('dayFloorS')));
    if (g.room_c != null) r.push(row(t('room'), esc2(usd(Math.max(0, g.room_c))), g.room_start_c != null ? t('roomS', { a: usd(Math.max(0, g.room_start_c)) }) : ''));
    r.push(row(t('bal'), esc2(usd(g.balance_c)), ''));
    r.push(row(t('pnl'), `<span class="${g.pnl_c > 0 ? 'pos' : g.pnl_c < 0 ? 'neg' : ''}">${esc2(usd(g.pnl_c, true))}</span>`, ''));
    if (g.plan_c) r.push(row(t('plan'), esc2(usd(g.plan_c)), t('planS')));
    const c = g.consistency;
    if (c) r.push(row(t('cons'), c.pct == null ? '—' : `<span class="${c.ok ? '' : 'neg'}">${esc2(pct(c.pct))}</span>`, c.pct == null ? t('consNone') : t('consS', { p: pct(c.pct), l: pct(c.limit) }) + (c.max_today_c != null ? ' ' + t('consMax', { m: usd(c.max_today_c) }) : '')));
    const o = g.goal || {};
    if (o.target_c) r.push(row(t('goal'), esc2(usd(o.left_c)), t('goalS', { m: usd(o.left_c), t: usd(o.target_c) })));
    if (o.min_days) r.push(row(t('days'), esc2(String(o.days_left)), t('daysS', { n: o.days_left, m: o.min_days })));
    const miss = (g.missing || []).map((k) => row(X.keys[k] || k, `<span class="faint">—</span>`, t('missing'), 'is-miss')).join('');
    const head = window.SweepGame && SweepGame.ui ? SweepGame.ui.head(esc2(g.name), esc2(t('title'))) : `<h2>${esc2(g.name)}</h2>`;
    return `${head}<div class="nav-guard-sh lv-${g.level} ${tone(g.level)}" data-guard-sheet="${esc2(g.id)}">
      <div class="nav-guard-v"><span>${esc2(t('risk'))}</span><b class="nav-guard-n">${esc2(usd(g.level === 'breached' ? 0 : (g.left_c || 0)))}</b></div>
      ${g.room_c == null ? '' : `<i class="nav-guard-bar" aria-hidden="true"><i style="width:${Math.max(0, Math.min(100, g.room_pct || 0)).toFixed(1)}%"></i></i>`}
      <p class="nav-guard-msg">${esc2(line(g))}</p>
      ${g.estimate ? `<p class="nav-guard-estl"><span class="nav-guard-est">${esc2(t('estimate'))}</span> ${esc2(t('estS'))}</p>` : ''}
      <div class="nav-guard-rows">${r.join('')}</div>
      ${miss ? `<h3 class="nav-guard-h3">${esc2(t('notSet'))}</h3><div class="nav-guard-rows">${miss}</div>` : ''}</div>`;
  }
  function openSheet(id) {
    const g = ((G.st && G.st.accounts) || []).find((x) => x.id === id && !x.locked); if (!g || !window.SweepGame || !SweepGame.ui) return;
    SweepGame.ui.sheet(sheetHtml(g), { cls: 'nav-guard-sheet' });
  }
  function paintSheet() {   // the sheet open follows the new numbers
    const sh = document.querySelector('#gSheet.nav-guard-sheet [data-guard-sheet]'); if (!sh) return;
    const g = ((G.st && G.st.accounts) || []).find((x) => x.id === sh.dataset.guardSheet && !x.locked); if (!g) return;
    const inner = sh.closest('.g-in'); if (inner) inner.innerHTML = sheetHtml(g);
  }
  /* step 4: « Update » — one field, the balance the platform shows now (an account without sync): a value of the day kept in
     journals/{day}.guard.live, used until the next trade saved, proposed by « Close my day » as the platform's balance */
  const balC = (v) => { let x = String(v == null ? '' : v).replace(/[\s\u00a0\u202f$]/g, '');
    if (x.includes(',') && x.includes('.')) x = x.lastIndexOf(',') < x.lastIndexOf('.') ? x.replace(/,/g, '') : x.replace(/\./g, '').replace(',', '.');
    else x = x.replace(/,(?=\d{3}(\D|$))/g, '').replace(',', '.');
    if ((x.match(/\./g) || []).length > 1) { const k = x.lastIndexOf('.'); x = /^\d{1,2}$/.test(x.slice(k + 1)) ? x.slice(0, k).replace(/\./g, '') + '.' + x.slice(k + 1) : x.replace(/\./g, ''); }   // (as the review's, game.js)
    return x === '' || x === '-' || !isFinite(+x) ? null : Math.round(+x * 100); };
  const balIn = (c) => { const s = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(c / 100);
    return L === 'fr' || L === 'es' ? s.replace(/[,.]/g, (m) => (m === ',' ? '\0' : ',')).replace(/\0/g, L === 'fr' ? '\u202f' : '.') : s; };
  function openUpdate(id) {
    const g = ((G.st && G.st.accounts) || []).find((x) => x.id === id && !x.locked); if (!g || !window.SweepGame || !SweepGame.ui) return;
    const a = typeof getDoc === 'function' ? getDoc('accounts', id) : null, f = a && a.firm_id && typeof firm === 'function' ? firm(a.firm_id) : null;
    const where = (f && f.name) || ({ en: 'your platform', fr: 'ta plateforme', es: 'tu plataforma' })[L] || 'your platform';
    SweepGame.ui.sheet(`${SweepGame.ui.head(esc2(t('upT')), esc2(g.name))}<div class="nav-guard-upf">
      <label class="g-f"><span>${esc2(t('upS', { p: where }))}</span><input inputmode="decimal" autocomplete="off" data-guard-bal value="${esc2(balIn(g.balance_c))}" aria-label="${esc2(t('upT') + ' · ' + g.name)}"></label>
      <p class="g-err nav-guard-uperr" role="alert"></p>
      <button type="button" class="btn primary g-big" data-guard-save="${esc2(id)}">${esc2(t('upSave'))}</button></div>`, { cls: 'nav-guard-upsheet' });
    const i = document.querySelector('#gSheet [data-guard-bal]'); if (i && !matchMedia('(pointer: coarse)').matches) { i.focus(); i.select(); }
  }
  async function saveUpdate(id, btn) {
    const i = document.querySelector('#gSheet [data-guard-bal]'), err = document.querySelector('#gSheet .nav-guard-uperr'), v = i ? balC(i.value) : null;
    if (v == null || v < 0) { if (err) err.textContent = t('upBad'); if (i) i.focus(); return; }
    btn.disabled = true;
    const day = (G.st && G.st.day) || (typeof todayStr === 'function' ? todayStr() : '');
    editDoc('journals', day, (j) => { j.guard = Object.assign({}, j.guard); j.guard.live = Object.assign({}, j.guard.live, { [id]: { bal_c: v, at: new Date().toISOString() } }); });
    // the card follows at once (the server's numbers come right after)
    const g = G.st.accounts.find((x) => x.id === id);
    if (g && g.room_c != null) { const d = v - g.balance_c; g.balance_c = v; g.pnl_c += d; g.room_c += d; if (g.left_c != null) g.left_c = Math.max(0, g.left_c + d); place(); }
    if (window.SweepGame && SweepGame.ui) SweepGame.ui.close();
    if (typeof toast === 'function') toast(t('upDone'));
    try { if (typeof chains !== 'undefined') await chains['journals/' + day]; } catch (e) { /* the save says its own error */ }
    load(true);
  }
  document.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.matches && e.target.matches('#gSheet [data-guard-bal]')) { e.preventDefault(); const b = document.querySelector('#gSheet [data-guard-save]'); if (b) b.click(); } });
  document.addEventListener('click', (e) => {
    if (e.target.closest && e.target.closest('[data-guard-close]')) { SweepGame.ui.close(true); setTimeout(() => SweepGame.openReview(), 60); return; }
    const up = e.target.closest && e.target.closest('[data-guard-up]');
    if (up) { openUpdate(up.dataset.guardUp); return; }
    const sv = e.target.closest && e.target.closest('[data-guard-save]');
    if (sv) { saveUpdate(sv.dataset.guardSave, sv); return; }
    const p = e.target.closest && e.target.closest('[data-guard-pick]');
    if (p) { G.pick = p.dataset.guardPick; try { sessionStorage.setItem('sw.guardPick', G.pick); } catch (x) { /* private mode */ } place(); return; }
    const o = e.target.closest && e.target.closest('[data-guard-open]');
    if (o) { const c = o.closest('.nav-guard'); if (c) openSheet(c.dataset.guard); }
  });
  document.addEventListener('keydown', (e) => { if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('[data-guard-open]')) { e.preventDefault(); e.target.click(); } });
  // a trade, a plan, an account or a payout saved on the server: the numbers again
  if (typeof srvSend === 'function') {
    const orig = srvSend;
    srvSend = async function (col) { const out = await orig.apply(this, arguments); if (['trades', 'journals', 'accounts', 'payouts', 'meta', 'settings'].includes(col)) soon(); return out; };
  }
  new window.SweepMO(() => { if (onToday()) { place(); load(false); } }).observe(document.body, { childList: true, subtree: true });   // (#main is drawn again by the app: its own node can change)
  setInterval(() => { if (onToday() && document.visibilityState === 'visible') load(true); }, 60000);
  // the bell's words for the alerts (guard/guard.php guard_alerts: once per account, level and day)
  const NB = {
    en: { 'g_guard_watch.title': '{account}: half your room is used', 'g_guard_watch.body': 'Slow down, A+ setups only.', 'g_guard_danger.title': '{account}: one more loss could cost this account', 'g_guard_danger.body': 'Protect it: see what you can still lose today.' },
    fr: { 'g_guard_watch.title': '{account} : la moitié de ta marge est utilisée', 'g_guard_watch.body': 'Ralentis, seulement tes meilleurs setups.', 'g_guard_danger.title': '{account} : encore une perte pourrait coûter ce compte', 'g_guard_danger.body': 'Protège-le : vois ce que tu peux encore perdre aujourd’hui.' },
    es: { 'g_guard_watch.title': '{account}: usaste la mitad de tu margen', 'g_guard_watch.body': 'Baja el ritmo, solo tus mejores setups.', 'g_guard_danger.title': '{account}: una pérdida más podría costar esta cuenta', 'g_guard_danger.body': 'Protégela: mira lo que aún puedes perder hoy.' } };
  (function reg(n) { if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings(NB); } catch (e) { /* older module */ } } else if (n < 40) setTimeout(() => reg(n + 1), 150); })(0);
  window.SweepGuard = { load, state: () => G.st, shown, t, open: openSheet, update: openUpdate };
  window.SweepGuardCard = () => { try { return cardHtml(); } catch (e) { return ''; } };   // drawn with Today itself (composeToday): there at its first image
})();
