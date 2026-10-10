/* Viewport tests without forcing a layout: media queries are cached by the browser (reading innerWidth after a DOM change
 * recalculated the whole page each time). */
window.SW_MQ = window.SW_MQ || matchMedia('(max-width: 860px)');
window.SW_MQ6 = window.SW_MQ6 || matchMedia('(max-width: 600px)');
/* Performance: every DOM watcher of this file is batched to one call per frame (they used to run on every
 * single DOM change: 13 watchers × hundreds of changes when a page renders). The callback still runs before the
 * next paint, so nothing flashes. */
window.SweepMO = window.SweepMO || class {
  constructor(cb) {
    let q = [], pending = false;
    this.o = new MutationObserver((recs) => {
      for (const r of recs) q.push(r);
      if (pending) return; pending = true;
      requestAnimationFrame(() => { pending = false; const b = q; q = []; try { cb(b, this); } catch (e) { /* never blocks */ } });
    });
  }
  observe(t, o) { this.o.observe(t, o); }
  disconnect() { this.o.disconnect(); }
  takeRecords() { return this.o.takeRecords(); }
};
/*
 * Sweep — navigation (one place for it).
 * Structure: Today · Trades (List · Calendar · Journal) · Stats · Accounts (Accounts · Payouts & expenses) · Progression.
 * Avatar menu (phone and desktop): Progression, Settings, Subscription, Referral, Give feedback, Help, [Traders], Log out.
 * Hashes stay the official addresses (old links keep working); aliases: #today, #stats, #subscription, #progress.
 * Every sub-page has a back chevron to its parent; Android back / iOS swipe closes an open sheet first.
 */
(function () {
  'use strict';
  if (typeof render !== 'function' || typeof route !== 'function') return;
  const T = {
    en: { list: 'List', cal: 'Calendar', jour: 'Journal', acc: 'Accounts', pay: 'My money', today: 'Today', trades: 'Trades', stats: 'Stats',
      prog: 'Progression', settings: 'Settings', sub: 'Subscription', ref: 'Referral', fb: 'Give feedback', help: 'Help', admin: 'Traders', out: 'Log out', back: 'Back', menu: 'Menu', search: 'Search' },
    fr: { list: 'Liste', cal: 'Calendrier', jour: 'Journal', acc: 'Comptes', pay: 'Mon argent', today: 'Aujourd’hui', trades: 'Trades', stats: 'Stats',
      prog: 'Progression', settings: 'Réglages', sub: 'Abonnement', ref: 'Parrainage', fb: 'Donner mon avis', help: 'Aide', admin: 'Traders', out: 'Déconnexion', back: 'Retour', menu: 'Menu', search: 'Rechercher' },
    es: { list: 'Lista', cal: 'Calendario', jour: 'Diario', acc: 'Cuentas', pay: 'Mi dinero', today: 'Hoy', trades: 'Operaciones', stats: 'Stats',
      prog: 'Progreso', settings: 'Ajustes', sub: 'Suscripción', ref: 'Referidos', fb: 'Dar mi opinión', help: 'Ayuda', admin: 'Traders', out: 'Cerrar sesión', back: 'Atrás', menu: 'Menú', search: 'Buscar' },
  };
  const t = () => T[LANG] || T.en;
  const SEG = {
    trades: [['trades', 'list'], ['calendar', 'cal'], ['journal', 'jour']],
    accounts: [['accounts', 'acc'], ['payouts', 'pay']],
  };
  const GROUP = { trades: 'trades', calendar: 'trades', journal: 'trades', accounts: 'accounts', payouts: 'accounts' };
  // parent of each sub-page (the back chevron)
  const PARENT = { trade: ['#trades', 'trades'], import: ['#trades', 'trades'], account: ['#accounts', 'acc'], news: ['#dashboard', 'today'],
    settings: ['#dashboard', 'today'], plan: ['#dashboard', 'today'], referral: ['#dashboard', 'today'], feedback: ['#dashboard', 'today'], admin: ['#dashboard', 'today'] };
  const IC = {
    back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>',
    prog: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.6"/></svg>',
    settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
    sub: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="M3 10h18M7 15h4"/></svg>',
    ref: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="8" width="17" height="12" rx="2"/><path d="M12 8v12M3.5 12h17M12 8c-1.5-3-5-3.5-5-1.2C7 8 9.5 8 12 8zm0 0c1.5-3 5-3.5 5-1.2C17 8 14.5 8 12 8z"/></svg>',
    fb: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 0 1-11.8 7L4 20l1-4.2A8 8 0 1 1 20 12z"/></svg>',
    help: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.2-2.4 3.6M12 17h.01"/></svg>',
    admin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20c-.5-2.6-2-4.3-4-5"/></svg>',
    out: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l5-5-5-5M15 12H4"/></svg>',
  };

  const OVERLAYS = '#gSheet.open, .evp.open, #navMenu.open, .gd-help-ov.open, #tkSlide.open, #cmd:not([hidden]), .wr, .sheet:not([hidden])';

  /* ───────────── segmented controls + back chevron (drawn with each page) ───────────── */
  function chrome() {
    const v = route().v, main = document.getElementById('main'); if (!main) return;
    const g = GROUP[v];
    if (g && !main.querySelector('.nav-seg')) {
      const el = document.createElement('div'); el.className = 'seg nav-seg'; el.setAttribute('role', 'tablist'); el.setAttribute('data-noi18n', '');
      el.innerHTML = SEG[g].map(([r, k]) => `<a href="#${r}" role="tab" class="${r === v ? 'on' : ''}" aria-selected="${r === v}">${t()[k]}</a>`).join('');
      main.prepend(el);
    }
    const NT = { en: 'Add a trade (N)', fr: 'Ajouter un trade (N)', es: 'Añadir una operación (N)' };
    document.querySelectorAll('aside.side .new, #bottomnav .plus').forEach((b) => { b.title = NT[LANG] || NT.en; b.setAttribute('aria-keyshortcuts', 'N'); });
    // the reward dot pulses once per visit, then stays still (the avatar is redrawn on every render)
    const dot = rewardWaiting(); document.querySelectorAll('aside.side .who').forEach((w) => { w.classList.toggle('nav-dot', dot); w.classList.toggle('nav-dot-still', dot && dotPulsed); });
    if (dot && !dotPulsed) setTimeout(() => { dotPulsed = true; }, 3800);
    const p = PARENT[v];
    if (p && !main.querySelector('.nav-back') && !main.querySelector('.crumbs, .bc, .back-link')) {
      const has = [...main.querySelectorAll('a')].slice(0, 6).some((a) => /^\s*[‹<]/.test(a.textContent) || a.classList.contains('crumb'));
      if (!has) {
        const a = document.createElement('a'); a.className = 'nav-back'; a.href = p[0]; a.setAttribute('data-noi18n', '');
        a.innerHTML = `${IC.back}<span>${t()[p[1]]}</span>`; main.prepend(a);
      }
    }
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
      ${S.me ? `<button type="button" class="nav-menu-who" data-navm="plan"><span class="av">${esc(S.me.username.slice(0, 1).toUpperCase())}</span><span class="nm"><b>${esc(S.me.username)}</b>${planLine()}</span></button>` : ''}
      <div class="nav-mg">${item('prog', IC.prog, x.prog)}</div>
      <div class="nav-mg">${item('settings', IC.settings, x.settings)}${item('plan', IC.sub, x.sub)}</div>
      <div class="nav-mg">${item('referral', IC.ref, x.ref)}${item('feedback', IC.fb, x.fb)}${item('help', IC.help, x.help)}</div>
      ${admin ? `<div class="nav-mg">${item('admin', IC.admin, x.admin)}</div>` : ''}
      <div class="nav-mg"><button type="button" role="menuitem" class="out" data-act="logout">${IC.out}<span>${x.out}</span></button></div></div>`;
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
      else if (k !== 'close') location.hash = '#' + k;
      return;
    }
    if (e.target.closest && e.target.closest('#navMenu [data-act="logout"]')) closeMenu(true);
  });
  let lastTrigger = null, trapped = null, kbdUser = false, dotPulsed = false;
  addEventListener('keydown', (e) => { if (e.key === 'Tab' || e.key === 'Enter' || e.key === ' ' || e.key.startsWith('Arrow')) kbdUser = true; }, true);
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
    { l: { en: 'Progression', fr: 'Progression', es: 'Progreso' }, k: 'progression progress progreso rang rank rango streak racha xp niveau level nivel', go: () => SweepGame.open('hub') },
    { l: { en: 'Weekly missions', fr: 'Missions hebdomadaires', es: 'Misiones semanales' }, k: 'missions misiones mission boss jefe', go: () => SweepGame.open('missions') },
    { l: { en: 'Season pass', fr: 'Pass de saison', es: 'Pase de temporada' }, k: 'season saison temporada palier tier nivel chapitre chapter capitulo parcours journey', go: () => SweepGame.open('season') },
    { l: { en: 'Weekly league', fr: 'Ligue hebdomadaire', es: 'Liga semanal' }, k: 'league ligue liga classement ranking clasificacion', go: () => SweepGame.open('league') },
    { l: { en: 'Crew & buddy', fr: 'Crew et buddy', es: 'Crew y buddy' }, k: 'crew buddy equipe equipo ami amigo friend', go: () => SweepGame.open('social') },
    { l: { en: 'Weekly recap', fr: 'Bilan de la semaine', es: 'Resumen semanal' }, k: 'weekly recap bilan semaine resumen semanal coffre chest cofre edge reveal', go: () => SweepGame.open('weekly') },
    { l: { en: 'Plan of the day', fr: 'Plan du jour', es: 'Plan del día' }, k: 'plan du jour plan of the day plan del dia biais bias sesgo', go: () => SweepGame.open('plan') },
    { l: { en: 'Daily review', fr: 'Revue du jour', es: 'Revisión del día' }, k: 'daily review revue du jour revision del dia', go: () => SweepGame.open('review') },
    { l: { en: 'Badges & ring themes', fr: 'Badges et thèmes d’anneaux', es: 'Insignias y temas' }, k: 'badge badges insignia insignias themes theme themes temas tema collection coleccion anneaux rings anillos', go: () => SweepGame.open('hub') },
    { l: { en: 'Subscription', fr: 'Abonnement', es: 'Suscripción' }, k: 'subscription abonnement suscripcion forfait billing facturation facturacion pro elite upgrade', go: '#plan' },
    { l: { en: 'Export all my data (ZIP)', fr: 'Exporter toutes mes données (ZIP)', es: 'Exportar todos mis datos (ZIP)' }, k: 'export exporter exportar zip donnees data datos sauvegarde backup', go: '#settings' },
    { l: { en: 'Import trades (Tradovate, Rithmic, TopstepX)', fr: 'Importer des trades (Tradovate, Rithmic, TopstepX)', es: 'Importar operaciones (Tradovate, Rithmic, TopstepX)' }, k: 'import importer importar csv tradovate rithmic topstepx topstep', go: '#import' },
    { l: { en: 'My money', fr: 'Mon argent', es: 'Mi dinero' }, k: 'argent money dinero payout payouts depenses expenses gastos retrait withdrawal retiro frais fees', go: '#payouts' },
    { l: { en: 'Accounts', fr: 'Comptes', es: 'Cuentas' }, k: 'accounts comptes cuentas compte account cuenta prop drawdown regles rules reglas', go: '#accounts' },
    { l: { en: 'Economic news', fr: 'Nouvelles économiques', es: 'Noticias económicas' }, k: 'news nouvelles noticias calendrier economique economic calendar calendario economico cpi nfp fomc', go: '#news' },
    { l: { en: 'Stats', fr: 'Stats', es: 'Stats' }, k: 'stats statistiques statistics estadisticas analyses analytics insights analisis', go: '#analytics' },
    { l: { en: 'Calendar', fr: 'Calendrier', es: 'Calendario' }, k: 'calendar calendrier calendario', go: '#calendar' },
    { l: { en: 'Journal', fr: 'Journal', es: 'Diario' }, k: 'journal diario notes notas', go: '#journal' },
    { l: { en: 'Referral', fr: 'Parrainage', es: 'Referidos' }, k: 'referral parrainage referidos inviter invite invitar', go: '#referral' },
    { l: { en: 'Give feedback', fr: 'Donner mon avis', es: 'Dar mi opinión' }, k: 'feedback avis opinion idee idea bug probleme problem', go: '#feedback' },
    { l: { en: 'Settings', fr: 'Réglages', es: 'Ajustes' }, k: 'settings reglages ajustes parametres preferences', go: '#settings' },
    { l: { en: 'Notifications', fr: 'Notifications', es: 'Notificaciones' }, k: 'notifications notificaciones rappels reminders recordatorios', go: '#settings' },
    { l: { en: 'Help', fr: 'Aide', es: 'Ayuda' }, k: 'help aide ayuda guide guia comment how como', go: () => window.SweepGuide && SweepGuide.open() },
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
  if (typeof cmdItems === 'function') {
    const orig = cmdItems;
    cmdItems = function (q) {
      const base = orig.apply(this, arguments), s = norm(q).trim();
      if (!s) return base;
      const g = { en: 'Features', fr: 'Fonctions', es: 'Funciones' }[LANG] || 'Features';
      const hits = FIND.filter((f) => norm(f.l[LANG] || f.l.en).includes(s) || norm(f.k).split(' ').some((w) => w.startsWith(s) || (s.length > 3 && w.includes(s))))
        .map((f) => ({ g, t: f.l[LANG] || f.l.en, run: typeof f.go === 'string' ? () => { location.hash = f.go; } : f.go }));
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
    if (SELDAY) { const [a, b] = span(tab); const tr = pool.filter((x) => x.date >= a && x.date <= b); const n1 = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0)); const gs = byDecision(tr), w = gs.filter((g) => g.net > 0).length, l = gs.filter((g) => g.net < 0).length; return { net: tr.reduce((a2, x) => a2 + n1(x), 0), n: gs.length, win: w + l ? Math.round(w / (w + l) * 100) : null }; }   // sample trades only when there is nothing else; active account filter respected
    const now = new Date(etToday() + 'T12:00:00');   // the current session
    const mon = new Date(now); mon.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    const from = tab === 'week' ? ymd(mon) : ymd(now);
    const tr = pool.filter((x) => x.date >= from && x.date <= ymd(now));
    const net1 = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0));
    const net = tr.reduce((a, x) => a + net1(x), 0), wins = tr.filter((x) => net1(x) > 0).length, losses = tr.filter((x) => net1(x) < 0).length;   // a $0 trade is neither
    const gs = byDecision(tr), gw = gs.filter((g) => g.net > 0).length, gl = gs.filter((g) => g.net < 0).length;
    return { net, n: gs.length, win: gw + gl ? Math.round(gw / (gw + gl) * 100) : null };
  }
  /* performance of the period, by account type (« of which Eval +600 · Funded +400 · Live +100 »): a copied trade counts once */
  const MT = { en: { of: 'of which', eval: 'Eval', funded: 'Funded', live: 'Live', personal: 'Personal', perf: 'Performance', sim: 'Simulated', real: 'Real' },
    fr: { of: 'dont', eval: 'Éval', funded: 'Financé', live: 'Live', personal: 'Perso', perf: 'Performance', sim: 'Simulé', real: 'Réel' },
    es: { of: 'de lo cual', eval: 'Eval', funded: 'Financiada', live: 'Live', personal: 'Personal', perf: 'Rendimiento', sim: 'Simulado', real: 'Real' } };
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
    const parts = ['eval', 'funded', 'live', 'personal'].filter((k) => pf.byType[k]).map((k) => `<span class="nav-split-${k}">${y[k]} <b>${fm(pf.byType[k])}</b></span>`);
    return parts.length > 1 || (parts.length === 1 && (pf.byType.live || pf.byType.personal)) ? `<p class="nav-split" data-noi18n>${y.of} ${parts.join(' · ')}</p>` : '';
  }
  function kpiHtml(tab) {
    const x = KT[LANG] || KT.en, k = kpis(tab);
    const pf = perfOf(tab); if (pf) k.net = pf.total;   // the same performance as Stats: a copied trade counts once
    const fmt = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));   // same formatter as Stats and Trades
    return `<div class="nav-kpi-g"><div><small>${x.net} ${window.SweepTypeTag ? SweepTypeTag() : ''}</small><b class="${k.net > 0 ? 'pos' : k.net < 0 ? 'neg' : ''}">${fmt(k.net)}</b></div><div><small>${x.trades}</small><b>${k.n}</b></div><div><small>${x.win}</small><b>${k.win == null ? '—' : k.win + ' %'}</b></div></div>${splitHtml(pf)}`;
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
    const rows = groups.slice(0, max).map((g) => {
      const t = g.t, net = g.net, unj = !t.notes && !(t.discipline && Object.keys(t.discipline).length);
      // an evening trade says its session AND the clock time it was entered (« session of Oct 8 · entered on the 7th at 23:36 »)
      const eve = typeof isEveTrade === 'function' && isEveTrade(t);
      const when = eve ? tradeWhen(t) : tab === 'week' ? `${typeof fdate === 'function' ? fdate(t.date, { weekday: 'short' }) : t.date} · ${(t.entry_time || '').slice(0, 5)}` : (t.entry_time || '').slice(0, 5);
      return `<a class="nav-tr" href="#trade/${esc(t.id)}"><span class="nav-tr-d ${t.direction === 'short' ? 's' : 'l'}">${t.direction === 'short' ? 'S' : 'L'}</span>
        <span class="nav-tr-m"><b>${esc(t.instrument || '')} · ${esc(String(t.contracts || ''))}${g.n > 1 ? ` <em class="nav-tr-copy" title="${(COPY[LANG] || COPY.en).replace('{n}', g.n)}" aria-label="${(COPY[LANG] || COPY.en).replace('{n}', g.n)}">+${g.n - 1}</em>` : ''}</b><small>${esc(when)}${t.setup ? ' · ' + esc(t.setup) : ''}</small></span>
        ${unj ? `<span class="nav-tolog">${x.tolog}</span>` : ''}<span class="nav-tr-p ${net > 0 ? 'pos' : net < 0 ? 'neg' : ''}">${typeof money === 'function' ? money(net) : net}</span></a>`;
    }).join('');
    return `<div class="nav-trs">${rows}</div>${groups.length > max ? `<a class="nav-more" href="#trades">+${groups.length - max} · ${x.all}</a>` : ''}`;
  }
  let DESK_TAB = 'day';   // computer: the tab shown by the performance card (the news card follows it)
  function kpiCard() {
    const x = KT[LANG] || KT.en; let tab = 'day'; try { tab = localStorage.getItem('sw.kpiTab') === 'week' ? 'week' : 'day'; } catch (e) { /* private mode */ }
    if (tab === 'day' && kpis('day').n === 0 && !window.SW_MQ.matches) tab = 'week';   // computer: nothing today → the week (the phone shows the day with its news)
    if (window.SW_MQ.matches) return feedCard(tab);
    DESK_TAB = tab;
    return `<section class="surface nav-kpi nav-card d-perf" data-noi18n>${window.SweepTypeSeg ? `<div class="nav-ktype">${SweepTypeSeg()}</div>` : ''}<div class="nav-kpi-h"><div class="seg nav-kseg" role="tablist"><button type="button" role="tab" aria-selected="${tab === 'day'}" data-kt="day" class="${tab === 'day' ? 'on' : ''}">${x.day}</button><button type="button" role="tab" aria-selected="${tab === 'week'}" data-kt="week" class="${tab === 'week' ? 'on' : ''}">${x.week}</button></div><a class="nav-all" href="#trades">${(TL[LANG] || TL.en).all}</a></div><div class="nav-kpi-b">${kpiHtml(tab)}</div><div class="nav-kpi-t">${tradesHtml(tab)}</div></section>`;
  }
  /* ───── phone: one card for the day — scroll the days (P&L, news dot), see the day's numbers, releases and trades ───── */
  const FD = { en: { news: 'Releases', none: 'No important US release.', loading: 'Loading the releases…', fc: 'Fcst', act: 'Act', cal: 'Calendar ›', jr: 'Journal ›', all: 'All ›' }, fr: { news: 'Annonces', none: 'Aucune annonce américaine importante.', loading: 'Chargement des annonces…', fc: 'Prév.', act: 'Réel', cal: 'Calendrier ›', jr: 'Journal ›', all: 'Tout voir ›' }, es: { news: 'Publicaciones', none: 'Sin publicaciones importantes de EE. UU.', loading: 'Cargando publicaciones…', fc: 'Prev.', act: 'Real', cal: 'Calendario ›', jr: 'Diario ›', all: 'Ver todo ›' } };
  function stripDays() {
    const today = etToday(), out = [], t0 = new Date(today + 'T12:00:00');
    for (let i = -21; i <= 7; i++) { const d = new Date(t0); d.setDate(t0.getDate() + i); if (d.getDay() === 0 || d.getDay() === 6) continue; out.push(ymd(d)); }
    return out;
  }
  function feedStrip() {
    const days = stripDays(), today = etToday(), sel = SELDAY || today;
    econFor(days[0], days[days.length - 1]);
    const tr = pool(), byDay = typeof dayMap === 'function' ? dayMap(tr.filter((t) => t.date >= days[0])) : new Map();
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
      return `<button type="button" class="nav-fev ${e.impact}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-fev-t">${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-fev-n">${esc(e.event)}</span>${(/\b(minutes|speech|speaks|testimony|press conference|beige book|statement|remarks)\b/i.test(e.event || '')) ? `<span class="nav-nonum nav-nonum-r" data-noi18n>${({ en: 'No number', fr: 'Sans chiffre', es: 'Sin cifra' })[LANG] || 'No number'}</span>` : `<span class="nav-fev-v nav-ev-v3"><span><small>${x.act || ({ fr: 'Réel', es: 'Real' })[LANG] || 'Act.'}</small><b>${e.actual != null && e.actual !== '' ? esc(String(e.actual)) : '—'}</b></span><span><small>${x.fc || ({ fr: 'Prév.', es: 'Prev.' })[LANG] || 'Fcst'}</small><b>${esc(String(e.forecast || '—'))}</b></span><span><small>${x.prev || ({ fr: 'Préc.', es: 'Ant.' })[LANG] || 'Prev.'}</small><b>${esc(String(e.previous || '—'))}</b></span></span>`}</button>`; }).join('')}</div>`;
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
        rows.push(`<button type="button" class="nav-fev ${e.impact} ${e.ts < now - 60 ? 'nav-fev-past' : ''}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-fev-t"><small class="nav-fev-d">${esc(wd)}</small> ${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-fev-n">${esc(e.event)}</span>${(/\b(minutes|speech|speaks|testimony|press conference|beige book|statement|remarks)\b/i.test(e.event || '')) ? `<span class="nav-nonum nav-nonum-r" data-noi18n>${({ en: 'No number', fr: 'Sans chiffre', es: 'Sin cifra' })[LANG] || 'No number'}</span>` : `<span class="nav-fev-v nav-ev-v3"><span><small>${({ en: 'Act.', fr: 'Réel', es: 'Real' })[LANG] || 'Act.'}</small><b>${e.actual != null && e.actual !== '' ? esc(String(e.actual)) : '—'}</b></span><span><small>${({ en: 'Fcst', fr: 'Prév.', es: 'Prev.' })[LANG] || 'Fcst'}</small><b>${esc(String(e.forecast || '—'))}</b></span><span><small>${({ en: 'Prev.', fr: 'Préc.', es: 'Ant.' })[LANG] || 'Prev.'}</small><b>${esc(String(e.previous || '—'))}</b></span></span>`}</button>`);
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
    return `<section class="surface nav-kpi nav-card d-perf nav-feed" data-noi18n>${window.SweepTypeSeg ? `<div class="nav-ktype">${SweepTypeSeg()}</div>` : ''}<div class="nav-kpi-h"><div class="seg nav-kseg" role="tablist"><button type="button" role="tab" aria-selected="${tab === 'day'}" data-kt="day" class="${tab === 'day' ? 'on' : ''}">${x.day}</button><button type="button" role="tab" aria-selected="${tab === 'week'}" data-kt="week" class="${tab === 'week' ? 'on' : ''}">${x.week}</button></div><a class="nav-all" href="#calendar">${(FD[LANG] || FD.en).cal}</a></div>
      <div class="nav-fstrip" role="list">${feedStrip()}</div>
      <div class="nav-fdate">${feedDate()}</div>
      <div class="nav-kpi-b">${kpiHtml(tab)}</div><div class="nav-fn">${tab === 'day' ? feedNews() : feedWeekNews()}</div><div class="nav-kpi-t">${tradesHtml(tab)}</div></section>`;
  }
  function feedRefresh(card, keepScroll) {
    const tab = (card.querySelector('[data-kt].on') || {}).dataset?.kt || 'day';
    const st = card.querySelector('.nav-fstrip'), sl = st ? st.scrollLeft : 0;
    if (st) { st.innerHTML = feedStrip(); if (keepScroll) st.scrollLeft = sl; }
    const fdt = card.querySelector('.nav-fdate'); if (fdt) fdt.innerHTML = feedDate();
    card.querySelector('.nav-kpi-b').innerHTML = kpiHtml(tab);
    card.querySelector('.nav-fn').innerHTML = tab === 'day' ? feedNews() : feedWeekNews();
    card.querySelector('.nav-kpi-t').innerHTML = tradesHtml(tab);
  }
  function centerSel(card, smooth) {
    const st = card && card.querySelector('.nav-fstrip'), el = st && st.querySelector('.nav-fd.sel'); if (!el) return;
    const left = el.offsetLeft - (st.clientWidth - el.offsetWidth) / 2;
    st.scrollTo({ left: Math.max(0, left), behavior: smooth ? 'smooth' : 'auto' });
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-fd]'); if (!b) return;
    const card = b.closest('.nav-feed'); SELDAY = b.dataset.fd === etToday() ? null : b.dataset.fd;
    feedRefresh(card, true); centerSel(card, true);
  });
  // the releases arrive after the card: refresh it in place (and once, put today in the middle)
  let feedT = 0;
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
  const progSeen = () => { try { return localStorage.getItem('sw.progSeen') || ''; } catch (e) { return ''; } };
  function rewardWaiting() { const n = window.SweepGame && SweepGame.next && SweepGame.next(); return !!(n && n.dot && n.sig !== progSeen()); }
  function markProgSeen() {
    const n = window.SweepGame && SweepGame.next && SweepGame.next();
    try { if (n && n.sig) localStorage.setItem('sw.progSeen', n.sig); } catch (e) { /* private mode */ }
    document.querySelectorAll('.nav-dot').forEach((e) => e.classList.remove('nav-dot'));
  }
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-nav="progress"], [data-navm="prog"], [data-g="hub"]')) markProgSeen(); }, true);
  function rankCard() {
    const p = window.SweepGame && SweepGame.summary && SweepGame.summary(); if (!p) return '';
    const nx = SweepGame.next && SweepGame.next();
    const SL = { en: 'Streak {n} days · best {b}', fr: 'Streak {n} jours · record {b}', es: 'Racha {n} días · récord {b}' };
    const line = nx && nx.text ? nx.text : (SL[LANG] || SL.en).replace('{n}', p.streak).replace('{b}', p.best);
    return `<button type="button" class="surface nav-rank ${rewardWaiting() ? 'nav-dot' + (dotPulsed ? ' nav-dot-still' : '') : ''}" data-nav="progress" data-noi18n><span class="nav-rank-ic">${IC.prog}</span><span class="nav-rank-t"><b>${esc(p.rank)} · ${esc(SweepGame.t ? SweepGame.t('lvl', { n: p.level }) : 'Lv ' + p.level)}</b><small>${esc(line)}</small></span>${IC.back.replace('M15 6l-6 6 6 6', 'M9 6l6 6-6 6')}</button>`;
  }
  const report = (msg) => { try { fetch('api/client-error', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ msg, page: '#dashboard', src: 'nav.js' }) }).catch(() => {}); } catch (e) { /* offline */ } };
  let reported = false;
  /* ───────────── computer: the rank sits in the day card; its old place becomes « Quick access » ───────────── */
  const QK = {
    en: ['Quick access', 'Ask Sweep AI', 'Plan of the day', 'Daily review', 'Import trades', 'Economic calendar', 'Add a payout', 'Share my week'],
    fr: ['Accès rapide', 'Demander à Sweep AI', 'Plan du jour', 'Revue du jour', 'Importer des trades', 'Calendrier économique', 'Ajouter un payout', 'Partager ma semaine'],
    es: ['Acceso rápido', 'Preguntar a Sweep AI', 'Plan del día', 'Revisión del día', 'Importar operaciones', 'Calendario económico', 'Añadir un payout', 'Compartir mi semana'] };
  const QI = {
    ai: '<path d="M12 3l1.8 4.7L18.5 9.5 13.8 11.3 12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>',
    plan: '<path d="M5 4v16M5 5h10l-2 3 2 3H5"/>', review: '<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/>',
    import: '<path d="M12 4v11M7 10l5 5 5-5"/><path d="M5 19h14"/>', news: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 9h16M9 3v4M15 3v4"/>',
    payout: '<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>', share: '<path d="M12 15V4M7 9l5-5 5 5"/><path d="M5 13v6a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-6"/>' };
  function quickCard() {
    const x = QK[LANG] || QK.en, ic = (k) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${QI[k]}</svg>`;
    const d = new Date(etToday() + 'T12:00:00'), mon = new Date(d); mon.setDate(d.getDate() - ((d.getDay() + 6) % 7));   // week of the current session
    const wk = `${mon.getFullYear()}-${String(mon.getMonth() + 1).padStart(2, '0')}-${String(mon.getDate()).padStart(2, '0')}`;
    const b = (k, label, extra) => `<button type="button" class="nav-q" ${extra}>${ic(k)}<span>${label}</span></button>`;
    return `<section class="surface nav-card d-quick" data-noi18n><div class="nav-ch"><h2>${x[0]}</h2></div><div class="nav-qgrid">
      ${b('import', x[4], 'data-q="#import"')}${b('payout', x[6], 'data-q="#payouts"')}
      ${b('news', x[5], 'data-q="#news"')}${b('share', ({ en: 'Share', fr: 'Partager', es: 'Compartir' })[LANG] || 'Share', 'data-q-share')}</div></section>`;
  }
  document.addEventListener('click', (e) => {
    const q = e.target.closest && e.target.closest('.nav-q[data-q]'); if (!q) return;
    const v = q.dataset.q;
    if (v === 'ai') { if (typeof askToggle === 'function') askToggle(true); return; }
    if (v[0] === '#') location.hash = v; else if (window.SweepGame) SweepGame.open(v);
  });
  const AIQ = {
    en: { t: 'Ask Sweep AI', s: 'Answers from your own journal.', ph: 'Ask anything about your trading…', q: ['How did I do this week?', 'Which setup makes me the most money?', 'What costs me the most?'] },
    fr: { t: 'Demande à Sweep AI', s: 'Les réponses viennent de ton propre journal.', ph: 'Pose une question sur ton trading…', q: ['Comment s’est passée ma semaine ?', 'Quel setup me rapporte le plus ?', 'Qu’est-ce qui me coûte le plus ?'] },
    es: { t: 'Pregunta a Sweep AI', s: 'Las respuestas salen de tu propio diario.', ph: 'Pregunta lo que sea sobre tu trading…', q: ['¿Cómo me fue esta semana?', '¿Qué setup me da más dinero?', '¿Qué me cuesta más?'] } };
  function aiCard(dash) {
    const on = document.body.classList.contains('ai-on') && typeof askToggle === 'function';
    const old = dash.querySelector('.d-ai'); if (!on) { if (old) old.remove(); return; }
    if (old) return;
    const x = AIQ[LANG] || AIQ.en;
    dash.querySelector('.d-col-b').insertAdjacentHTML('afterbegin', `<section class="surface nav-card d-ai" data-noi18n>
      <div class="nav-ch"><h2><span class="d-ai-sp" aria-hidden="true">✦</span> ${x.t}</h2></div><p class="d-ai-sub">${x.s}</p>
      <div class="d-ai-q">${x.q.map((q) => `<button type="button" data-ai-q="${esc(q)}">${esc(q)}</button>`).join('')}</div>
      <form class="d-ai-in" data-ai-form><input type="text" maxlength="400" placeholder="${esc(x.ph)}" enterkeyhint="send" aria-label="${esc(x.t)}"><button type="submit" aria-label="${esc(x.t)}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg></button></form></section>`);
  }
  const askNow = (q) => { q = String(q || '').trim(); if (!q || typeof askToggle !== 'function') return; askToggle(true); setTimeout(() => { if (typeof askSend === 'function') askSend(q); }, 60); };
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-ai-q]'); if (b) { e.preventDefault(); askNow(b.dataset.aiQ); } });
  document.addEventListener('submit', (e) => { const f = e.target.closest && e.target.closest('[data-ai-form]'); if (!f) return; e.preventDefault(); const i = f.querySelector('input'); askNow(i.value); i.value = ''; });
  // a suggested question is sent as soon as it is tapped (no « Ask » needed); keeping the focus avoids the keyboard closing and moving the button under the finger
  document.addEventListener('pointerdown', (e) => { if (e.target.closest && e.target.closest('#askPanel [data-ask-q], .sai .sai-chip[data-act="ask-ex"], [data-ai-q]')) e.preventDefault(); }, true);
  function newsUnderDay(dash) {
    if (!dash || window.SW_MQ.matches) return;
    const col = dash.querySelector('.d-col-a'); if (!col) return;
    const parts = ['.d-perf', '.d-news', '.d-cal', '.d-pay'].map((q) => dash.querySelector(q)).filter((el) => el && !el.dataset.balMoved); if (!parts.length) return;   // a card the balance moved stays where it went (pulling it back made the page jump)
    let box = col.querySelector(':scope > .nav-merge');
    if (!box) { box = document.createElement('section'); box.className = 'surface nav-card nav-merge'; const today = col.querySelector(':scope > .d-today'); today ? today.after(box) : col.prepend(box); }
    parts.forEach((el, i) => { if (el.parentElement !== box || box.children[i] !== el) box.insertBefore(el, box.children[i] || null); });
  }
  new window.SweepMO(() => { try { newsUnderDay(document.querySelector('#main .nav-dash')); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
  function deskToday(dash) {
    if (dash && window.SW_MQ.matches && !dash.querySelector('.d-quick')) { const acc = dash.querySelector('.d-acc'); (acc ? acc.parentElement : dash).insertAdjacentHTML('beforeend', quickCard()); }   // phone: Quick access at the end too
    if (!dash || window.SW_MQ.matches) return;
    const rank = dash.querySelector('.d-col-b > .d-rank'), today = dash.querySelector('.d-today');
    if (rank && today) { today.append(rank); dash.classList.add('rank-in'); }
    if (!dash.querySelector('.d-quick')) dash.querySelector('.d-col-b').insertAdjacentHTML('beforeend', quickCard());
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
      curve: 'Equity curve', recent: 'Recent trades', trends: 'Trends', news: 'Economic news', tolog: 'Checklist to do', swept: 'Swept', moretr: 'Trends appear after a few more trades.' },
    fr: { all: 'Tout voir ›', acc: 'Comptes', pay: 'Payouts et dépenses', recv: 'Reçus', exp: 'Dépenses', net: 'Net (ROI prop)', last: 'Dernier payout : {a} · {d}', nopay: 'Aucun payout ni dépense pour l’instant.', addpay: 'En noter un',
      dd: 'Marge de drawdown', ready: 'Prêt pour le payout', cal: 'Ce mois-ci', nocal: 'Ton mois s’allumera ici dès tes premiers trades.', notrade: 'Rien à afficher pour l’instant : journalise ton premier trade.', log: 'Ajouter un trade',
      curve: 'Courbe de capital', recent: 'Trades récents', trends: 'Tendances', news: 'Nouvelles économiques', tolog: 'Checklist à faire', swept: 'Balayée', moretr: 'Les tendances apparaissent après quelques trades de plus.' },
    es: { all: 'Ver todo ›', acc: 'Cuentas', pay: 'Payouts y gastos', recv: 'Recibidos', exp: 'Gastos', net: 'Neto (ROI prop)', last: 'Último payout: {a} · {d}', nopay: 'Aún no hay payouts ni gastos.', addpay: 'Registrar uno',
      dd: 'Margen de drawdown', ready: 'Listo para el payout', cal: 'Este mes', nocal: 'Tu mes se iluminará aquí con tus primeras operaciones.', notrade: 'Nada que mostrar aún: registra tu primera operación.', log: 'Añadir una operación',
      curve: 'Curva de capital', recent: 'Operaciones recientes', trends: 'Tendencias', news: 'Noticias económicas', tolog: 'Checklist pendiente', swept: 'Barrido', moretr: 'Las tendencias aparecen tras algunas operaciones más.' },
  };
  const dt = () => DT[LANG] || DT.en;
  const head = (title, href, extra = '') => `<div class="nav-ch" role="link" tabindex="0" data-href="${href}"><h2>${esc(title)}${extra ? `<span class="nav-ch-sub">${extra}</span>` : ''}</h2><span class="nav-all">${dt().all}</span></div>`;
  const fmtM = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));
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
        ${room != null ? `<span class="nav-acc-dd"><small>${x.dd} · ${fmtU(st.breached ? 0 : Math.max(0, st.buffer))}</small><i><s class="${room < 0.25 ? 'neg' : 'pos'}" style="width:${(room * 100).toFixed(0)}%"></s></i></span>` : ''}
        ${ready ? `<span class="nav-ready">${(a.phase === 'eval' || (!a.phase && !ps && a.rules && a.rules.target_c)) ? ({ en: 'Objectives reached', fr: 'Objectifs atteints', es: 'Objetivos alcanzados' }[LANG] || 'Objectives reached') : x.ready}</span>` : ''}</a>`;   // an evaluation is « passed », not « ready for payout »
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
    if (!window.SweepMoney) return `<section class="surface nav-card d-pay">${head(x.pay, '#payouts')}</section>`;
    const [a, b] = SweepMoney.periodOf('month'), m = SweepMoney.moneyOf({ from: a, to: b });
    const fm = (c) => (typeof money === 'function' ? money(c, { dec: 0 }) : (c / 100).toFixed(0));
    return `<section class="surface nav-card d-pay d-money" data-noi18n>${head(z.t, '#payouts')}
      <div class="nav-mny-l">${z.net} <span class="mny-tag real">${z.real}</span></div><div class="nav-mny-big ${m.real.net >= 0 ? 'pos' : 'neg'}">${fm(m.real.net)}</div>
      <div class="nav-kpi-g nav-mny-g"><div><small>${z.wd} <span class="mny-tag sim">${z.sim}</span></small><b class="mny-dim">${fmtU(m.withdrawable)}</b></div><div><small>${z.exp}</small><b>${fm(-m.real.expenses)}</b></div><div><small>${z.pend}</small><b>${fmtU(m.real.pending)}</b></div></div>${window.SweepRealNet ? SweepRealNet.invite() : ''}</section>`;
  }
  const NW = {
    en: { title: 'What to watch', today: 'Today', next: 'Next session', none: 'No major U.S. release today.', nextOne: 'Next big one: {e} · {d} {t}', in: 'in {m}', now: 'now', act: 'Act.', fc: 'Fcst', prev: 'Prev.' },
    fr: { title: 'À surveiller', today: 'Aujourd’hui', next: 'Prochaine séance', none: 'Aucune annonce américaine importante aujourd’hui.', nextOne: 'Prochaine importante : {e} · {d} {t}', in: 'dans {m}', now: 'maintenant', act: 'Réel', fc: 'Prév.', prev: 'Préc.' },
    es: { title: 'Para vigilar', today: 'Hoy', next: 'Próxima sesión', none: 'No hay publicaciones importantes de EE. UU. hoy.', nextOne: 'Próxima importante: {e} · {d} {t}', in: 'en {m}', now: 'ahora', act: 'Real', fc: 'Prev.', prev: 'Ant.' } };
  const etNowStr = () => new Date().toLocaleString('sv-SE', { timeZone: 'America/New_York' }).replace(' ', 'T');
  function sessionDay() {   // after 16:00 ET (and on weekends) the next session is what you prepare
    const n = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/New_York' }));
    if (n.getHours() >= 16) n.setDate(n.getDate() + 1);
    while (n.getDay() === 0 || n.getDay() === 6) n.setDate(n.getDate() + 1);
    return ymd(n);
  }
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
    return (/\b(minutes|speech|speaks|testimony|press conference|beige book|statement|remarks)\b/i.test(e.event || '')) ? `<span class="nav-nonum nav-nonum-r" data-noi18n>${({ en: 'No number', fr: 'Sans chiffre', es: 'Sin cifra' })[LANG] || 'No number'}</span>` : `<span class="nav-ev-v nav-ev-v3"><span><small>${x.act || 'Act.'}</small><b class="${hasAct && diff ? diff.direction : ''}">${hasAct ? esc(String(e.actual)) : '—'}</b></span><span><small>${x.fc}</small><b>${esc(String(e.forecast || '—'))}</b></span><span><small>${x.prev}</small><b>${esc(String(e.previous || '—'))}</b></span></span>`;
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
        return `<button type="button" class="nav-ev ${e.impact} ${past ? 'past' : ''} ${e === nextUp ? 'next' : ''}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-ev-t">${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-ev-n">${esc(e.event)}${cd}</span>${right}</button>`;
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
        rows.push(`<button type="button" class="nav-ev ${e.impact} ${past ? 'past nav-ev-wpast' : 'nav-ev-wnext'}" data-act="ev-open" data-id="${esc(e.id)}"><span class="nav-ev-t"><small class="nav-ev-d">${esc(wd)}</small>${hm}</span><span class="imp ${e.impact}"><i></i></span><span class="nav-ev-n">${esc(e.event)}</span>${evNums(e, x, now)}</button>`);
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
    const byDay = typeof dayMap === 'function' ? dayMap(tr) : new Map();
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
      const tip = [k, net != null ? `${typeof money === 'function' ? money(net) : net} · ${n} trade${n > 1 ? 's' : ''}` : '', ...evs.map((e) => `${etStr(e.ts).slice(11, 16)} ${e.event}`)].filter(Boolean).join('\n');
      cells.push(`<a class="nav-cd ${net == null ? '' : net > 0 ? 'p' : net < 0 ? 'n' : 'z'} ${histDays[k] ? 'nav-sw' : ''} ${k === ymd(now) ? 'today' : ''} ${k < ymd(now) ? 'past' : ''}" href="#journal/${k}" data-day="${k}" title="${esc(tip)}">
        <b>${d}</b>${net != null ? `<span class="nav-cd-p">${short(net)}</span><span class="nav-cd-n">${n} trade${n > 1 ? 's' : ''}</span>` : ''}
        ${evs.length ? `<span class="nav-cd-e"><i></i>${esc(evs[0].event.replace(/\s*\(.*?\)/g, '').split(' ').slice(0, 2).join(' '))}${evs.length > 1 ? ` +${evs.length - 1}` : ''}</span>` : ''}</a>`);
      strip.push(`<a class="nav-sd ${net == null ? '' : net > 0 ? 'p' : net < 0 ? 'n' : 'z'} ${histDays[k] ? 'nav-sw' : ''} ${k === ymd(now) ? 'today' : ''} ${k < ymd(now) ? 'past' : ''}" href="#journal/${k}" data-day="${k}" title="${esc(tip)}"><small>${WD[wd]}</small><b>${d}</b><span>${net != null ? short(net) : evs.length ? '<i></i>' : '·'}</span></a>`);
    }
    const wk = LANG === 'en' ? ['M', 'T', 'W', 'T', 'F'] : LANG === 'es' ? ['L', 'M', 'X', 'J', 'V'] : ['L', 'M', 'M', 'J', 'V'];
    return `<section class="surface nav-card d-cal" data-noi18n>${head(x.cal, '#calendar')}<div class="nav-strip" role="list">${strip.join('')}</div><div class="nav-cal"><div class="nav-cw">${wk.map((w) => `<span>${w}</span>`).join('')}</div><div class="nav-cg">${cells.join('')}</div></div></section>`;
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
  let dashEnteredAt = '', navCount = 0;
  addEventListener('hashchange', () => { navCount++; });
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
    if (dashEnteredAt !== location.hash + '|' + navCount) { dashEnteredAt = location.hash + '|' + navCount; dash.classList.add('nav-dash-in'); }
    // two columns on a computer, each card at its natural height (no stretched empty cards); one list on a phone (CSS order)
    const rk = rankCard() ? `<div class="d-rank">${rankCard()}</div>` : '<div class="d-rank"><div class="surface nav-rank ph" aria-hidden="true"><span class="skel" style="display:block;height:38px;width:100%;border-radius:12px"></span></div></div>';
    dash.innerHTML = `<div class="d-col d-col-a"><div class="d-today"></div>${kpiCard()}${calCard()}</div><div class="d-col d-col-b">${newsCard()}${accountsCard()}${payoutsCard()}${rk}</div>`;
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
    if (trends && pool().length && !trends.querySelector('.empty')) {
      asCard(trends, 'd-trends', x.trends, '#analytics', null);
      dash.querySelector('.d-col-a').append(trends); dash.classList.add('has-trends');
    } else if (trends) trends.classList.add('nav-old');
    // the old economic section, equity curve and recent trades are replaced (news card, performance card with its trades)
    [econ, curve, recent].forEach((sec) => sec && sec.classList.add('nav-old'));

    if (dash.querySelector('.nav-rank.ph')) setTimeout(() => fillRank(0), 400);
    headDay();
    deskToday(dash);
    { const old = dash.querySelector('.d-ai'); if (old) old.remove(); }   // Sweep AI = the floating button, on every page
    const sp = dash.querySelector('.nav-strip'), td = sp && sp.querySelector('.today');
    if (sp && td) sp.scrollLeft = Math.max(0, td.offsetLeft - sp.clientWidth / 2 + td.offsetWidth / 2);
  }

  /* ───────────── Settings in 4 groups: Account · Discipline · Notifications · Data ───────────── */
  const SG = {
    en: ['Account', 'Discipline', 'Notifications', 'Data'], fr: ['Compte', 'Discipline', 'Notifications', 'Données'], es: ['Cuenta', 'Disciplina', 'Notificaciones', 'Datos'],
  };
  // which section goes where (matched on the section title in any language)
  const SMAP = [
    [0, /^(your account|ton compte|tu cuenta|appearance|apparence|apariencia|keyboard shortcuts|raccourcis clavier|atajos de teclado)/i],
    [1, /^(discipline checklist|checklist de discipline|checklist de disciplina|setups|prop firms|risk rules|règles de risque|reglas de riesgo|copied trades|trades copiés|operaciones copiadas)/i],
    [2, /^(notifications|notificaciones)/i],
    [3, /^(data|données|datos)/i],
  ];
  function groupSettings() {
    if (route().v !== 'settings') return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-sgrp')) return;
    const secs = [...main.querySelectorAll(':scope > section')];
    const buckets = [[], [], [], []], rest = [];
    for (const sec of secs) {
      const h = ((sec.querySelector('h2, h3') || {}).textContent || '').trim();
      const m = SMAP.find(([, re]) => re.test(h));
      (m ? buckets[m[0]] : rest).push(sec);
    }
    const names = SG[LANG] || SG.en;
    const anchor = main.querySelector('.nav-back');
    let at = anchor || null;
    // B15: four foldable groups (Account, Discipline, Notifications, Data); the open ones stay open while you navigate
    let openSet; try { openSet = new Set(JSON.parse(sessionStorage.getItem('sw.sgd') || '[0]')); } catch (e) { openSet = new Set([0]); }
    buckets.forEach((list, i) => {
      if (!list.length) return;
      const d = document.createElement('details'); d.className = 'nav-sgd'; d.dataset.i = i; d.open = openSet.has(i);
      d.innerHTML = `<summary class="nav-sgrp" data-noi18n><h2>${names[i]}</h2></summary>`;
      d.addEventListener('toggle', () => { d.open ? openSet.add(i) : openSet.delete(i); try { sessionStorage.setItem('sw.sgd', JSON.stringify([...openSet])); } catch (e) { /* private mode */ } });
      at ? at.after(d) : main.prepend(d); at = d;
      for (const sec of list) d.append(sec);
    });
    for (const sec of rest) main.append(sec);   // « About » and legal notes stay at the end
    const VL = { fr: 'Libellé si non respectée', es: 'Etiqueta si no se cumple' }[LANG];
    if (VL) main.querySelectorAll('.q-tbl td[data-l]').forEach((td) => { td.dataset.l = VL; });
    if (matchMedia('(pointer:coarse)').matches) main.querySelectorAll(':scope > section').forEach((sec) => { if (/^(keyboard shortcuts|raccourcis clavier|atajos de teclado)/i.test(((sec.querySelector('h2,h3') || {}).textContent || '').trim())) sec.hidden = true; });
    main.querySelectorAll('.nav-sgrp').forEach((g) => { const n = g.nextElementSibling, h = n && (n.querySelector('h2,h3') || {}).textContent; const next2 = n && n.nextElementSibling; if (h && h.trim().toLowerCase() === g.textContent.trim().toLowerCase() && (!next2 || next2.classList.contains('nav-sgrp') || next2.tagName !== 'SECTION')) { const hh = n.querySelector('h2,h3'); if (hh) hh.hidden = true; } });   // one section with the group's name: its own title goes, the group stays foldable
    const legal = main.querySelector(':scope > .sc-legal'); if (legal) main.append(legal);
    // B15: « Log out » at the very bottom, on its own
    const out = main.querySelector('[data-act="logout"]');
    if (out) { const w = document.createElement('div'); w.className = 'nav-logout'; out.style.marginLeft = ''; w.append(out); main.append(w); }
  }

  /* ───────────── Trade review: sticky mini-navigation (Chart · Details · Review · Setup) ───────────── */
  const TN = { en: ['Chart', 'Details', 'Review', 'Setup'], fr: ['Graphique', 'Détails', 'Bilan', 'Setup'], es: ['Gráfico', 'Detalles', 'Revisión', 'Setup'] };
  function tradeNav() {
    if (route().v !== 'trade') return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-tnav')) return;
    const chart = main.querySelector('.sc-wrap, .tchart, .sc-chart');
    const facts = main.querySelector('.facts');
    const review = main.querySelector('.rprog');
    const setup = [...main.querySelectorAll('h2, h3, .sec-h')].find((h) => /^(setup)/i.test(h.textContent.trim()));
    const targets = [chart, facts, review, setup];
    if (targets.filter(Boolean).length < 2) return;
    const el = document.createElement('div'); el.className = 'seg nav-tnav'; el.setAttribute('data-noi18n', '');
    el.setAttribute('role', 'tablist');
    el.innerHTML = (TN[LANG] || TN.en).map((l, i) => targets[i] ? `<button type="button" role="tab" aria-selected="false" data-tn="${i}">${l}</button>` : '').join('');
    const top = main.querySelector('.tr-top'); top ? top.after(el) : main.prepend(el);
    el.addEventListener('click', (e) => {
      const b = e.target.closest('[data-tn]'); if (!b) return;
      const tgt = targets[+b.dataset.tn]; if (!tgt) return;
      el.querySelectorAll('button').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-selected', x === b); });
      const y = tgt.getBoundingClientRect().top + scrollY - (el.offsetHeight + (window.SW_MQ.matches ? 70 : 20));
      scrollTo({ top: Math.max(0, y), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    });
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
    document.querySelectorAll('#main .nav-seg, #main .nav-tnav').forEach((seg) => {
      if (seg.querySelector('.nav-thumb')) return;
      const on = seg.querySelector('.on'); if (!on) return;
      seg.classList.add('has-thumb');   // positioned first: the thumb is measured inside the control, never against the page
      const th = document.createElement('i'); th.className = 'nav-thumb'; th.setAttribute('aria-hidden', 'true'); seg.prepend(th);
      const key = seg.classList.contains('nav-tnav') ? 'tnav' : [...seg.querySelectorAll('a')].map((a) => a.getAttribute('href')).join();
      const place = (el, anim) => { th.style.transition = anim ? '' : 'none'; const r = el.getBoundingClientRect(), b = seg.getBoundingClientRect(); th.style.width = r.width + 'px'; th.style.transform = `translateX(${r.left - b.left - seg.clientLeft}px)`; };
      const prev = segPrev[key]; const from = prev != null && seg.children[prev + 1];
      if (from && from !== on) { place(from, false); requestAnimationFrame(() => requestAnimationFrame(() => place(on, true))); } else place(on, false);
      segPrev[key] = [...seg.children].indexOf(on) - 1;
      seg.classList.add('has-thumb');
      seg.addEventListener('click', (e) => { const b = e.target.closest('a, button'); if (b && b.parentElement === seg) { segPrev[key] = [...seg.children].indexOf(b) - 1; place(b, true); } });
    });
  }

  /* ───────────── Today: the rank card has a placeholder until the game data is in ───────────── */
  function fillRank(n = 0) {
    const ph = document.querySelector('#main .nav-rank.ph'); if (!ph) return;
    const html = rankCard();
    if (html) { ph.outerHTML = html; return; }
    if (n >= 4) { ph.remove(); return; }                       // no game data: the card is simply left out
    setTimeout(() => fillRank(n + 1), 400 * Math.pow(2, n));    // 0.4 s, 0.8, 1.6, 3.2, 6.4
  }


  /* ───────────── jump report (trade review page, phones) ─────────────
   * After a tap, any block ABOVE what you are looking at that changes height for a moment makes the page jump on iOS
   * (Safari has no scroll anchoring). This samples the blocks for 0.7 s after each tap and, if one changes, sends a short
   * report to the admin dashboard (Errors): which block, how many pixels, for how long. At most 5 reports per visit. */
  let jumpReports = 0;
  addEventListener('pointerdown', (e) => {
    if (jumpReports >= 5 || route().v !== 'trade' || !window.SW_MQ.matches) return;
    const main = document.getElementById('main'); if (!main || !main.contains(e.target)) return;
    const blocks = () => [...main.children].map((c, i) => { const r = c.getBoundingClientRect(); return { k: (c.className || c.tagName).toString().split(' ').slice(0, 2).join('.') || ('#' + i), h: Math.round(r.height), top: Math.round(r.top) }; });
    const base = blocks(), t0 = performance.now(), seen = {}, key = (e.target.closest('[data-v],[data-act],[data-path]') || e.target);
    const y0 = key.getBoundingClientRect().top; let worst = 0, worstAt = 0;
    const find = () => { if (document.contains(key)) return key; const k = ['data-act', 'data-path', 'data-v', 'data-id'].filter((a) => key.hasAttribute && key.hasAttribute(a)).map((a) => `[${a}="${CSS.escape(key.getAttribute(a))}"]`).join(''); return k ? main.querySelector(k) : null; };
    const tick = () => {
      const ms = Math.round(performance.now() - t0), el = find();
      if (el) { const d = Math.round(el.getBoundingClientRect().top - y0); if (Math.abs(d) > Math.abs(worst)) { worst = d; worstAt = ms; } }
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
    document.querySelectorAll('#main .nav-seg, #main .nav-tnav').forEach((b) => {
      const top = parseFloat(getComputedStyle(b).top) || 0;
      b.classList.toggle('is-stuck', scrollY > 0 && Math.abs(b.getBoundingClientRect().top - top) < 1.5);
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
    about.append(p);
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
    const b = e.target.closest && e.target.closest('[data-act="toggle"][data-path][data-v], [data-g="j-emo"][data-v]'); if (!b || toggleReports >= 3) return;
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
    fr: ['Ajouter une question, ex. Ai-je attendu mon niveau ?', 'Ajouter', 'Ajoutée à ce trade et à tous les suivants.', 'Non : '],
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
    [chrome, greetOff, composeToday, groupSettings, tradeNav, measureHeader, animateSeg, markStuck, versionLine, iconLabels, questionAdd, headDay, hideWeekends].forEach((f) => { try { f(); } catch (e) { /* never blocks */ } });
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
    en: { real: 'Real P&L (platform)', realPh: 'As shown by your platform', calc: 'From your prices', gap: 'Slippage', fees: 'Fees', feeAcc: 'Commission per contract (round trip)', feeHelp: 'Deducted from every new trade on this account.', st: 'Slippage and fees', stSub: 'On {n} trade{s} with the real P&L entered', tot: 'Slippage', avg: 'Average per trade', avgR: 'Average in R', worst: 'Worst', feesT: 'Fees (all trades)', none: 'Enter the platform\'s P&L on a trade (form or trade review) to measure your slippage.', hint: 'Fees included, as in your account.' },
    fr: { real: 'P&L réel (plateforme)', realPh: 'Comme affiché par ta plateforme', calc: 'Selon tes prix', gap: 'Glissement', fees: 'Frais', feeAcc: 'Commission par contrat (aller-retour)', feeHelp: 'Déduite de chaque nouveau trade sur ce compte.', st: 'Glissement et frais', stSub: 'Sur {n} trade{s} avec le P&L réel entré', tot: 'Glissement', avg: 'Moyenne par trade', avgR: 'Moyenne en R', worst: 'Pire', feesT: 'Frais (tous les trades)', none: 'Entre le P&L de ta plateforme sur un trade (formulaire ou bilan) pour mesurer ton glissement.', hint: 'Frais inclus, comme dans ton compte.' },
    es: { real: 'P&L real (plataforma)', realPh: 'Como lo muestra tu plataforma', calc: 'Según tus precios', gap: 'Deslizamiento', fees: 'Comisiones', feeAcc: 'Comisión por contrato (ida y vuelta)', feeHelp: 'Se descuenta de cada nueva operación en esta cuenta.', st: 'Deslizamiento y comisiones', stSub: 'En {n} operaci{s} con el P&L real', tot: 'Deslizamiento', avg: 'Promedio por operación', avgR: 'Promedio en R', worst: 'Peor', feesT: 'Comisiones (todas)', none: 'Introduce el P&L de tu plataforma en una operación (formulario o revisión) para medir tu deslizamiento.', hint: 'Comisiones incluidas, como en tu cuenta.' } };
  const tx = (k) => (TXT[L] || TXT.en)[k];
  const $m = (c) => (typeof money === 'function' ? money(c) : (c / 100).toFixed(2));
  const toC = (v) => { const s = String(v == null ? '' : v).replace(/[\s\u00a0$]/g, '').replace(',', '.'); if (s === '' || s === '-' || !isFinite(+s)) return null; return Math.round(+s * 100); };
  const calcOf = (d) => { try { return typeof calcPnl === 'function' ? calcPnl(d.direction, d.entry, d.exit, d.contracts, d.instrument || 'NQ') : null; } catch (e) { return null; } };
  const acctOf = (id) => (typeof S !== 'undefined' && S.accounts || []).find((a) => a.id === id);

  /* every saved trade: fees from the account, P&L from the prices, real P&L as the truth */
  function shape(d) {
    if (!d || d.demo) return d;
    const a = acctOf(d.account_id);
    const isNew = !(typeof getDoc === 'function' && getDoc('trades', d.id));   // older trades keep their fees as they are
    if (isNew && d.fees_c == null && a && a.fee_rt_c > 0 && d.contracts > 0) { d.fees_c = Math.round(a.fee_rt_c * d.contracts); d.fees_auto = true; }
    const c = calcOf(d); if (c != null) d.pnl_calc_c = c;
    if (typeof d.real_pnl_c === 'number' && isFinite(d.real_pnl_c)) { d.pnl_c = d.real_pnl_c + (d.fees_c || 0); d.pnl_manual = true; d.pnl_real = true; }
    else if (d.pnl_real) { delete d.pnl_real; d.pnl_manual = false; if (c != null) d.pnl_c = c; }
    return d;
  }
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
    const a = acctOf(TK.account), fee = a && a.fee_rt_c > 0 ? Math.round(a.fee_rt_c * (TK.qty || 1)) : 0;
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
  }

  /* Stats: slippage and fees */
  function statsCard() {
    if (!/^#analytics/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-slip')) return;
    const tr = (S.trades || []).filter((t) => !t.demo);
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
    en: { add: 'Add a trade', addDay: 'Add a trade on this day', usdExit: 'Or the result in $', usdExitPh: 'e.g. -350', usdRisk: 'Or risk in $', usdGain: 'Or target in $', usdNeed: 'Pick Buy / Sell and the entry price first.', unit: 'Enter as', px: 'Price', usd: '$ amount', rRisk: 'Stop loss ($)', rGain: 'Take profit ($)', sl: 'Stop loss (SL)', tp: 'Take profit (TP)', rRes: 'Result ($)', eq: '= {v}', multi: '+ Several entries or exits', recap: 'Recap', plan: 'Plan', exec: 'In your plan', review: 'Review', lesson: 'Lesson', none: '—', done: 'Done', todo: 'To do', pre: 'Pre-market', post: 'Post-market', fill: 'To fill in', open: 'Open', close: 'Close', bias: { bullish: 'Bullish', bearish: 'Bearish', neutral: 'Neutral', no_trade: 'No trading' }, followed: { yes: 'Plan followed', partly: 'Plan partly followed', no: 'Plan not followed' } },
    fr: { add: 'Ajouter un trade', addDay: 'Ajouter un trade ce jour-là', usdExit: 'Ou le résultat en $', usdExitPh: 'ex. -350', usdRisk: 'Ou le risque en $', usdGain: 'Ou l’objectif en $', usdNeed: 'Choisis Achat / Vente et le prix d’entrée d’abord.', unit: 'Saisir en', px: 'Prix', usd: 'Montant $', rRisk: 'Stop loss ($)', rGain: 'Take profit ($)', sl: 'Stop loss (SL)', tp: 'Take profit (TP)', rRes: 'Résultat ($)', eq: '= {v}', multi: '+ Plusieurs entrées ou sorties', recap: 'Récap', plan: 'Plan', exec: 'Dans ton plan', review: 'Revue', lesson: 'Leçon', none: '—', done: 'Faite', todo: 'À faire', pre: 'Pré-marché', post: 'Post-marché', fill: 'À compléter', open: 'Ouvrir', close: 'Fermer', bias: { bullish: 'Haussier', bearish: 'Baissier', neutral: 'Neutre', no_trade: 'Pas de trading' }, followed: { yes: 'Plan suivi', partly: 'Plan suivi en partie', no: 'Plan non suivi' } },
    es: { add: 'Añadir una operación', addDay: 'Añadir una operación ese día', usdExit: 'O el resultado en $', usdExitPh: 'ej. -350', usdRisk: 'O el riesgo en $', usdGain: 'O el objetivo en $', usdNeed: 'Elige Compra / Venta y el precio de entrada primero.', unit: 'Introducir en', px: 'Precio', usd: 'Importe $', rRisk: 'Stop loss ($)', rGain: 'Take profit ($)', sl: 'Stop loss (SL)', tp: 'Take profit (TP)', rRes: 'Resultado ($)', eq: '= {v}', multi: '+ Varias entradas o salidas', recap: 'Resumen', plan: 'Plan', exec: 'En tu plan', review: 'Revisión', lesson: 'Lección', none: '—', done: 'Hecha', todo: 'Pendiente', pre: 'Pre-mercado', post: 'Post-mercado', fill: 'Por completar', open: 'Abrir', close: 'Cerrar', bias: { bullish: 'Alcista', bearish: 'Bajista', neutral: 'Neutral', no_trade: 'No operar' }, followed: { yes: 'Plan seguido', partly: 'Plan seguido en parte', no: 'Plan no seguido' } } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const PLUS = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/></svg>';

  /* 1. « Add a trade » in the title row of Trades, Calendar and Journal (the Journal day: on that day) */
  function addButton() {
    const top = document.querySelector('.main-wrap .top'); if (!top) return;
    const v = (location.hash.slice(1).split('/')[0] || 'dashboard');
    let b = top.querySelector('.nav-addtop');
    const want = ['trades', 'calendar', 'journal'].includes(v) || ((v === 'dashboard' || v === 'today') && !window.SW_MQ.matches);
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

  function tradesAddRow() {
    if (!/^#trades(\/list)?$|^#trades$/.test(location.hash || '') && location.hash !== '' && !/^#trades\b/.test(location.hash)) return;
    if (!/^#trades/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-addrow')) return;
    const list = main.querySelector('.tlist, .tbl'); if (!list) return;
    const host = list.closest('.surface') || list.parentElement;
    if (!host || host.closest('.jlayout')) return;
    const b = document.createElement('button'); b.type = 'button'; b.className = 'add-row nav-addrow'; b.setAttribute('data-act', 'add-trade'); b.setAttribute('data-noi18n', '');
    b.innerHTML = `<span class="add-ic">+</span>${t('add')}`;
    host.prepend(b);
  }

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
    const inPlan = trades.length ? `${trades.filter((x) => (x.stop != null && x.stop !== '') && x.rules_followed !== 'no' && x.rules_followed !== 'partial').length} / ${trades.length}` : t('none');
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
    const w = function () { const out = appRender.apply(this, arguments); [addButton, journalRecap, tradesAddRow].forEach((f) => { try { f(); } catch (e) { /* never blocks */ } }); return out; };
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
    fr: { trade: (d) => [`Analyse mon trade ${d}`, 'Qu’est-ce que j’aurais pu mieux faire sur ce trade ?', 'Ce setup fonctionne-t-il pour moi ?'], journal: ['Débriefe ma journée', 'Qu’est-ce qui revient dans mes erreurs ?', 'Comment était ma discipline cette semaine ?'], stats: ['Qu’est-ce qui me coûte le plus ?', 'À quel moment je trade le mieux ?', 'Quel setup me rapporte le plus ?'], cal: ['Qu’y a-t-il au calendrier économique aujourd’hui ?', 'Comment s’est passé mon mois ?', 'Quel jour de la semaine est mon meilleur ?'], acc: ['Combien de marge avant mon drawdown ?', 'Quand pourrai-je demander un payout ?', 'Quel compte performe le mieux ?'], trades: ['Comment s’est passée ma semaine ?', 'Mon taux de réussite en long vs en short ?', 'Quel setup me rapporte le plus ?'] },
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
      // an account added « already running »: a trailing drawdown counts from the highest balance it had reached
      const ru = acc && acc.rules; if (r && acc && acc.hwm_c && ru && ru.dd_c && ru.dd_type !== 'static' && r.thr != null) { const f = acc.hwm_c - ru.dd_c; if (f > r.thr) { r.thr = f; r.buffer = r.bal - f; r.breached = r.bal <= f; } }
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
    const go = e.target.closest && e.target.closest('[data-recal-go]'), rm = e.target.closest && e.target.closest('[data-recal-rm]');
    if (!go && !rm) return;
    const box = e.target.closest('.nav-recal'), id = box && box.dataset.acc; if (!id) return;
    const a = getDoc('accounts', id); if (!a) return;
    const msg = box.querySelector('.nav-recal-msg');
    if (rm) { editDoc('accounts', id, (d) => { d.adjustments = (d.adjustments || []).filter((x) => x.id !== rm.dataset.recalRm); }); setTimeout(() => render(), 80); return; }
    const kind = go.dataset.recalGo, v = toC(box.querySelector(`[data-recal="${kind}"]`).value); if (v == null) return;
    const amt = kind === 'bal' ? v - acctState(a).bal : v;
    if (!amt) { msg.textContent = t('none'); return; }
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
  function usual() {
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
  function block(day) {
    const shots = shotsOf(day), src = (id) => (typeof blobSrc === 'function' ? blobSrc(id) : 'uploads/' + encodeURIComponent(id));
    return `<div class="nav-pre" data-noi18n data-day="${esc2(day)}">
      <div class="nav-pre-h"><b>${t('chart')}</b>
        <div class="nav-pre-tools">${chartOn ? `<div class="seg sm2">${Object.keys(SYM).filter((k) => ['NQ', 'ES', 'MNQ', 'MES', 'GC', 'MGC', 'CL', 'YM', 'RTY'].includes(k) || k === usual()).map((k) => `<button type="button" class="${k === usual() ? 'on' : ''}" data-pre-inst="${k}">${k}</button>`).join('')}</div><div class="seg sm2">${['1', '5', '15', '60'].map((k) => `<button type="button" class="${k === tf ? 'on' : ''}" data-pre-tf="${k}">${k === '60' ? '1h' : k + 'm'}</button>`).join('')}</div>` : ''}
        <button type="button" class="link" data-pre-chart>${chartOn ? t('hide') : t('open')}</button></div></div>
      ${chartOn ? `<div class="nav-tv-wrap">${frame()}</div><small class="nav-pre-note">${t('note')}</small>` : ''}
      <div class="nav-pre-h"><b>${t('shots')}</b><label class="link nav-pre-add">${t('add')}<input type="file" accept="image/png,image/jpeg,image/gif,image/webp" multiple hidden data-pre-up></label></div>
      ${shots.length ? `<div class="nav-pre-shots">${shots.map((x) => `<figure><a href="${src(x.id)}" target="_blank" rel="noopener"><img src="${src(x.id)}" alt="${esc2(x.name || '')}" loading="lazy"></a><button type="button" class="nav-pre-rm" data-pre-rm="${esc2(x.id)}" aria-label="${t('rm')}">×</button></figure>`).join('')}</div>` : ''}
    </div>`;
  }
  function paint(host, day) {
    let b = host.querySelector(':scope > .nav-pre');
    const html = block(day);
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
  // the plan sheet: before its save button
  function plan() {
    const sh = document.getElementById('gSheet'); if (!sh || !sh.classList.contains('g-plan')) return;
    const save = sh.querySelector('[data-g="save-plan"]'); if (!save || !sh.dataset.day) return;
    let host = sh.querySelector('.nav-pre-host');
    if (!host) { host = document.createElement('div'); host.className = 'nav-pre-host'; save.before(host); }
    paint(host, sh.dataset.day);
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
    if ((sh && sh.classList.contains('g-plan') && !sh.querySelector('.nav-pre')) || (/^#journal/.test(location.hash || '') && !document.querySelector('#main .nav-pre'))) refresh();
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
    en: { q: 'How do you like to log a trade?', qs: 'You can change it any time in Settings.', shot: 'With a screenshot', shotS: 'Drop the screenshot of your platform or chart. Sweep fills in the trade, you answer the discipline and psychology questions on the same screen.', man: 'By hand', manS: 'Entry, exit, stop, executions: every detail, then the review on the next page.', title: 'New trade', sub: 'from a screenshot', cancel: 'Cancel', byHand: 'Enter by hand', fromShot: 'From a screenshot', impFile: 'Import CSV', toMan: 'Enter by hand ›', toShot: 'From a screenshot ›', drop: 'Paste or drop your screenshot (Ctrl+V)', reading: 'Reading the screenshot…', read: 'Filled in from the screenshot: check and complete.', noAi: 'Fill in the key fields.', aiFail: 'Could not read it: fill in the key fields.', acc: 'Account', sym: 'Symbol', dir: 'Direction', long: 'Long', short: 'Short', date: 'Date', time: 'Entry time (ET)', qty: 'Contracts', entry: 'Entry price', exit: 'Exit price', pnl: 'Result ($)', pnlH: 'Calculated from the prices when both are there.', disc: 'Discipline', psy: 'Psychology', emo: 'How did you feel before the trade?', conf: 'Confidence', exec: 'Execution', yes: 'Yes', no: 'No', na: 'N/A', save: 'Save the trade', saved: 'Trade saved', need: 'The account and the net P&L (or the prices) are needed.', set: 'Adding a trade', setS: 'What « Add a trade » opens first.', pref: 'Saved as your default way', more: '+ More', addEmo: '+ Add yours', addEmoQ: 'Your emotion (one or two words)', moreQ: '+ {n} more questions', addQ: '+ Add a question', addQQ: 'Your question (e.g. « Did I wait for my level? »)', also: 'Also on (copy trading)', alsoS: 'Also on', net: 'Net P&L (as on your platform)', risk: 'Risk ($), optional', rHint: 'Enter the net P&L shown by your platform.', rAdd: 'Add the risk to see the R.', verify: 'Check the trade details ›', alsoH: 'Same trade saved on each account you pick.' },
    fr: { q: 'Comment préfères-tu ajouter un trade ?', qs: 'Tu pourras changer ça en tout temps dans Réglages.', shot: 'Avec une capture d’écran', shotS: 'Dépose la capture de ta plateforme ou de ton graphique. Sweep remplit le trade, et tu réponds à la discipline et à la psychologie sur le même écran.', man: 'Manuellement', manS: 'Entrée, sortie, stop, exécutions : chaque détail, puis le bilan sur la page suivante.', title: 'Nouveau trade', sub: 'par capture d’écran', cancel: 'Annuler', byHand: 'Saisir à la main', fromShot: 'Par capture d’écran', impFile: 'Importer un CSV', toMan: 'Saisir manuellement ›', toShot: 'Par capture d’écran ›', drop: 'Colle ou dépose ta capture (Ctrl+V)', reading: 'Lecture de la capture…', read: 'Rempli à partir de la capture : vérifie et complète.', noAi: 'Remplis les infos principales.', aiFail: 'Lecture impossible : remplis les infos principales.', acc: 'Compte', sym: 'Symbole', dir: 'Sens', long: 'Long', short: 'Short', date: 'Date', time: 'Heure d’entrée (ET)', qty: 'Contrats', entry: 'Prix d’entrée', exit: 'Prix de sortie', pnl: 'Résultat ($)', pnlH: 'Calculé à partir des prix quand les deux sont là.', disc: 'Discipline', psy: 'Psychologie', emo: 'Comment te sentais-tu avant le trade ?', conf: 'Confiance', exec: 'Exécution', yes: 'Oui', no: 'Non', na: 'N/A', save: 'Enregistrer le trade', saved: 'Trade enregistré', need: 'Il faut le compte et le P&L net (ou les prix).', set: 'Ajout d’un trade', setS: 'Ce que « Ajouter un trade » ouvre en premier.', pref: 'Enregistré comme ta façon par défaut', more: '+ Voir plus', addEmo: '+ Ajouter la tienne', addEmoQ: 'Ton émotion (un ou deux mots)', moreQ: '+ {n} autres questions', addQ: '+ Ajouter une question', addQQ: 'Ta question (ex. « Ai-je attendu mon niveau ? »)', also: 'Aussi sur (copy trading)', alsoS: 'Aussi sur', net: 'P&L net (comme sur ta plateforme)', risk: 'Risque ($), facultatif', rHint: 'Entre le P&L net affiché par ta plateforme.', rAdd: 'Ajoute le risque pour voir le R.', verify: 'Vérifier le trade ›', alsoH: 'Le même trade est enregistré sur chaque compte choisi.' },
    es: { q: '¿Cómo prefieres añadir una operación?', qs: 'Puedes cambiarlo cuando quieras en Ajustes.', shot: 'Con una captura', shotS: 'Sube la captura de tu plataforma o gráfico. Sweep rellena la operación y respondes disciplina y psicología en la misma pantalla.', man: 'Manualmente', manS: 'Entrada, salida, stop, ejecuciones: cada detalle, y la revisión en la página siguiente.', title: 'Nueva operación', sub: 'por captura', cancel: 'Cancelar', byHand: 'Introducir a mano', fromShot: 'Desde una captura', impFile: 'Importar CSV', toMan: 'Introducir manualmente ›', toShot: 'Con una captura ›', drop: 'Pega o suelta tu captura (Ctrl+V)', reading: 'Leyendo la captura…', read: 'Rellenado desde la captura: revisa y completa.', noAi: 'Rellena los datos principales.', aiFail: 'No se pudo leer: rellena los datos principales.', acc: 'Cuenta', sym: 'Símbolo', dir: 'Sentido', long: 'Long', short: 'Short', date: 'Fecha', time: 'Hora de entrada (ET)', qty: 'Contratos', entry: 'Precio de entrada', exit: 'Precio de salida', pnl: 'Resultado ($)', pnlH: 'Calculado con los precios cuando están los dos.', disc: 'Disciplina', psy: 'Psicología', emo: '¿Cómo te sentías antes de la operación?', conf: 'Confianza', exec: 'Ejecución', yes: 'Sí', no: 'No', na: 'N/A', save: 'Guardar la operación', saved: 'Operación guardada', need: 'Hacen falta la cuenta y el P&L neto (o los precios).', set: 'Añadir una operación', setS: 'Lo que « Añadir una operación » abre primero.', pref: 'Guardado como tu forma por defecto', more: '+ Ver más', addEmo: '+ Añadir la tuya', addEmoQ: 'Tu emoción (una o dos palabras)', moreQ: '+ {n} preguntas más', addQ: '+ Añadir una pregunta', addQQ: 'Tu pregunta (ej. « ¿Esperé mi nivel? »)', also: 'También en (copy trading)', alsoS: 'También en', net: 'P&L neto (como en tu plataforma)', risk: 'Riesgo ($), opcional', rHint: 'Introduce el P&L neto de tu plataforma.', rAdd: 'Añade el riesgo para ver la R.', verify: 'Revisar la operación ›', alsoH: 'La misma operación se guarda en cada cuenta elegida.' } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const num = (v) => { const s = String(v == null ? '' : v).replace(/[\s\u00a0$]/g, '').replace(',', '.'); return s === '' || s === '-' || !isFinite(+s) ? null : +s; };
  const emoLabel = (k) => { try { const v = window.SweepGame && SweepGame.t('emo.' + k); return v && v !== 'emo.' + k ? v : k; } catch (e) { return k; } };
  const mode = () => (typeof S !== 'undefined' && S.settings && S.settings.add_mode_pref) || 'shot';   // screenshot first, unless the trader chose « by hand » in Settings
  const setMode = (v) => { if (typeof editDoc === 'function') editDoc('settings', 'settings', (r) => { r.add_mode = v; r.add_mode_pref = v; }); };
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
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

  /* 1. the question, asked once */
  function chooser(opts) {
    const el = layer('nav-am-ask', `<button type="button" class="nav-am-x" data-am="close" aria-label="×">×</button>
      <h2>${t('q')}</h2><p class="muted">${t('qs')}</p>
      <div class="nav-am-choices">
        <button type="button" class="nav-am-c" data-am-pick="shot"><span class="nav-am-ic">${ICS}</span><b>${t('shot')}</b><small>${t('shotS')}</small></button>
        <button type="button" class="nav-am-c" data-am-pick="manual"><span class="nav-am-ic">${ICM}</span><b>${t('man')}</b><small>${t('manS')}</small></button>
      </div>`);
    el._opts = opts || {};
  }
  const ICS = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="12" cy="12" r="3.2"/><path d="M8 5l1.5-2h5L16 5"/></svg>';
  const ICM = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z M14 6l4 4"/></svg>';

  /* 2. the screenshot form */
  const SH = { file: null, shot: null, src: '', dir: '', emo: new Set(), conf: 0, exec: 0, disc: {}, status: '', busy: false, f: {} };
  function shotForm(opts) {
    Object.assign(SH, { batch: [], open: false, copy: new Set(), allEmo: false, allQ: false, file: null, shot: null, src: '', dir: '', emo: new Set(), conf: 0, exec: 0, disc: {}, status: '', busy: false, f: { date: (opts && opts.date) || today(), qty: '1' } });
    const accs = ((l) => (l.some((a) => !a.demo) ? l.filter((a) => !a.demo) : l))((S.accounts || []).filter((a) => a.status !== 'archived'));
    SH.f.account = (accs[0] || {}).id || '';
    { const a0 = getDoc('accounts', SH.f.account); if (a0 && a0.group_id) (S.accounts || []).filter((x) => x.group_id === a0.group_id && x.id !== a0.id && x.status !== 'archived').forEach((x) => SH.copy.add(x.id)); }
    const usual = (() => { const c = {}; (S.trades || []).filter((x) => !x.demo).slice(-40).forEach((x) => { c[x.instrument] = (c[x.instrument] || 0) + 1; }); const top = Object.entries(c).sort((a, b) => b[1] - a[1])[0]; return top ? top[0] : 'NQ'; })();
    SH.f.inst = usual;
    layer('nav-am-shot', '');
    paint();
  }
  function paint() {
    const el = document.querySelector('.nav-am-shot .nav-am-in'); if (!el) return;
    const accs = ((l) => (l.some((a) => !a.demo) ? l.filter((a) => !a.demo) : l))((S.accounts || []).filter((a) => a.status !== 'archived'));
    const insts = typeof INSTR !== 'undefined' ? Object.keys(INSTR) : ['NQ', 'MNQ', 'ES', 'MES', 'GC', 'MGC', 'CL'];
    const qs = ((S.settings && S.settings.questions) || []).filter((q) => q.active);
    const emos = typeof EMO !== 'undefined' ? EMO : ['Calm', 'Confident', 'Patient', 'Focused', 'FOMO', 'Fearful', 'Frustrated', 'Greedy', 'Hesitant', 'Impulsive'];
    const pnl = autoPnl();
    const fld = (k, label, attrs = '') => `<label class="tk-f"><span>${label}</span><div class="tk-in"><input data-am-f="${k}" value="${esc2(SH.f[k] ?? '')}" ${attrs}></div></label>`;
    const seg = (key, vals, cur) => `<div class="seg yn">${vals.map(([v, l]) => `<button type="button" class="${String(cur) === String(v) ? 'on' : ''}" data-am-seg="${key}" data-v="${v}">${l}</button>`).join('')}</div>`;
    // same header as the manual form: title, subtitle, the other way, « Cancel » on the right
    el.innerHTML = `<div class="tk-head nav-am-head"><div><h2>${t('title')}</h2><span class="muted">${t('sub')}</span><button type="button" class="link nav-am-sw" data-am="to-manual">${t('toMan')}</button></div><button type="button" class="link" data-am="close">${t('cancel')}</button></div>
      ${SH.batch.length ? batchTop() : `<label class="nav-am-drop ${SH.src ? 'has' : ''}">${SH.src ? `<img src="${SH.src}" alt="">` : `<span class="nav-am-ic">${ICS}</span><b>${t('drop')}</b>`}<input type="file" accept="image/png,image/jpeg,image/gif,image/webp" hidden multiple data-am-file></label>
      ${SH.status ? `<p class="nav-am-st ${SH.busy ? 'busy' : ''}">${SH.status}</p>` : ''}`}
      ${SH.batch.length || SH.src ? '' : `<div class="nav-am-alt"><button type="button" class="btn" data-am="to-manual">${t('byHand')}</button><a class="btn" href="#import" data-am-imp>${t('impFile')}</a></div>`}
      <div class="nav-am-grid">
        <div class="tk-f nav-am-wide"><span>${t('acc')}</span>${pickBox('account', accs.map((a) => [a.id, typeof acctLabel === 'function' ? acctLabel(a.id) : a.name]), SH.f.account)}</div>
        ${accs.length > 1 ? `<div class="tk-copies nav-am-wide nav-am-copy"><span class="help">${t('alsoS')}</span>${accs.filter((a) => a.id !== SH.f.account).map((a) => `<button type="button" class="chip ${SH.copy.has(a.id) ? 'on' : ''}" data-am-copy="${esc2(a.id)}">${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</button>`).join('')}</div>` : ''}
        ${SH.batch.length ? batchList() : `<label class="tk-f nav-am-net"><span>${t('net')}</span><div class="tk-in"><input data-am-f="net" inputmode="decimal" value="${esc2(SH.f.net ?? '')}" placeholder="${pnl != null ? ((pnl - (SH.f.fees || 0)) / 100).toFixed(2) : '+250'}"></div></label>
        <label class="tk-f nav-am-risk"><span>${t('risk')}</span><div class="tk-in"><input data-am-f="risk" inputmode="decimal" value="${esc2(SH.f.risk ?? '')}" placeholder="$"></div></label>
        <div class="nav-am-r nav-am-wide">${rLine()}</div>
        <details class="nav-am-more-d nav-am-wide" ${SH.open ? 'open' : ''}><summary>${t('verify')}<small>${verifyLine()}</small></summary><div class="nav-am-grid">
        <div class="tk-f nav-am-wide"><span>${t('sym')}</span>${pickBox('inst', insts.map((k) => [k, k + (typeof INSTR !== 'undefined' && INSTR[k] && INSTR[k].name ? ' — ' + INSTR[k].name : '')]), SH.f.inst)}</div>
        <div class="tk-f nav-am-dir"><span>${t('dir')}</span>${seg('dir', [['long', t('long')], ['short', t('short')]], SH.dir)}</div>
        ${fld('qty', t('qty'), 'inputmode="numeric"')}
        ${fld('date', t('date'), 'type="date"')}${fld('time', t('time'), 'placeholder="hh:mm"')}
        ${fld('entry', t('entry'), 'inputmode="decimal"')}${fld('exit', t('exit'), 'inputmode="decimal"')}
        </div></details>`}
      </div>
      ${qs.length ? `<section class="nav-am-sec"><h3>${t('disc')}</h3>${(SH.allQ ? qs : qs.filter((q, i) => i < 5 || SH.disc[q.id])).map((q) => `<div class="nav-am-q"><span>${esc2(q.text)}</span>${seg('d:' + q.id, [['y', t('yes')], ['n', t('no')], ['na', t('na')]], SH.disc[q.id] || '')}</div>`).join('')}
        <div class="nav-am-qmore">${!SH.allQ && qs.length > 5 ? `<button type="button" class="chip nav-am-more" data-am="q-more">${t('moreQ').replace('{n}', qs.filter((q, i) => i >= 5 && !SH.disc[q.id]).length)}</button>` : ''}<button type="button" class="chip nav-am-more" data-am="q-add">${t('addQ')}</button></div></section>` : ''}
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
        <div class="nav-am-scores"><div><span>${t('conf')}</span>${seg('conf', [1, 2, 3, 4, 5].map((n) => [n, n]), SH.conf || '')}</div><div><span>${t('exec')}</span>${seg('exec', [1, 2, 3, 4, 5].map((n) => [n, n]), SH.exec || '')}</div></div></section>
      <p class="err nav-am-err"></p>
      <button type="button" class="btn primary nav-am-save" data-am="save" ${SH.busy ? 'disabled' : ''}>${t('save')}</button>`;
  }
  function pickBox(k, opts, cur) {
    const lab = (opts.find((o) => o[0] === cur) || opts[0] || ['', ''])[1];
    return `<div class="nav-am-sel ${SH.openPick === k ? 'open' : ''}" data-noi18n><button type="button" class="nav-am-selb" data-am-sel="${k}" aria-expanded="${SH.openPick === k}"><span>${esc2(lab)}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>${SH.openPick === k ? `<div class="nav-am-opts" role="listbox">${opts.map((o) => `<button type="button" role="option" class="${o[0] === cur ? 'on' : ''}" data-am-pickf="${k}" data-v="${esc2(o[0])}">${esc2(o[1])}</button>`).join('')}</div>` : ''}</div>`;
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
      b.res = res.ok ? j : null; const d = trs[0];
      if (d) Object.assign(b.f, { inst: d.instrument || b.f.inst, dir: d.direction || '', qty: d.contracts ? String(d.contracts) : '1', date: d.date || b.f.date, time: String(d.entry_time || '').slice(0, 5), entry: d.entry != null ? String(d.entry) : '', exit: d.exit != null ? String(d.exit) : '', net: d.pnl_c != null ? ((d.pnl_c - (d.fees_c || 0)) / 100).toFixed(2) : '', fees: d.fees_c || 0, exitTime: d.exit_time || '' });
      if (j.account_suggest && !SH.f.accountPicked) SH.f.account = j.account_suggest;
      b.st = d ? 'ok' : 'fail';
    } catch (e) { b.st = 'fail'; }
  }

  /* ───── several trades read on screenshots: « X trades found », checked by the trader, saved in one go ───── */
  const MX = { en: { raw: 'What Sweep AI read on the screenshot', wTime: 'time not read', wSide: 'side not read', wPnl: 'P&L differs from the prices', wRead: 'hard to read', wOpen: 'still open', fixed: 'side taken from the prices and the P&L', feesP: 'fees = shown P&L difference', found: '{n} trades found', acc: 'Account', all: 'Check all', none: 'Uncheck all', save: 'Save {n} trades', net: 'Net of the batch', wl: '{w} won · {l} lost', check: 'To check', open: 'Open — to complete', dup: 'Already in Sweep',
      shown: 'Shown {a} · computed {b}', tz: 'Times on this screenshot', tzQ: 'In which time zone are the times on this screenshot?', disc: 'Discipline for the batch', each: 'Answer trade by trade', yes: 'Yes', no: 'No', na: 'N/A', added: '{n} trades added · {p}', undone: 'Batch removed',
      fail: 'Could not save the batch. Nothing was added.', copy: 'Also on', edit: 'Edit', done: 'Done', inst: 'Symbol', dir: 'Side', qty: 'Qty', entry: 'Entry', exit: 'Exit', tin: 'Entry time', tout: 'Exit time', pnl: 'P&L ($)', long: 'Long', short: 'Short', gross: 'gross {a} · fees {b}', unknown: 'Not read (symbol unknown to Sweep): {s}' },
    fr: { raw: 'Ce que Sweep AI a lu sur la capture', wTime: 'heure non lue', wSide: 'sens non lu', wPnl: 'P&L différent des prix', wRead: 'lecture incertaine', wOpen: 'encore ouvert', fixed: 'sens déduit des prix et du P&L', feesP: 'frais = écart avec le P&L affiché', found: '{n} trades trouvés', acc: 'Compte', all: 'Tout cocher', none: 'Tout décocher', save: 'Enregistrer {n} trades', net: 'Net du lot', wl: '{w} gagnants · {l} perdants', check: 'À vérifier', open: 'Ouvert — à compléter', dup: 'Déjà dans Sweep',
      shown: 'Affiché {a} · calculé {b}', tz: 'Heures de cette capture', tzQ: 'Dans quel fuseau sont les heures de cette capture ?', disc: 'Discipline pour le lot', each: 'Répondre trade par trade', yes: 'Oui', no: 'Non', na: 'N/A', added: '{n} trades ajoutés · {p}', undone: 'Lot retiré',
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
    if (tr.entry != null && tr.exit != null && tr.contracts) tr.pnl_c = Math.round((tr.exit - tr.entry) * (tr.direction === 'long' ? 1 : -1) * tr.contracts * pvOf(tr.instrument));
  }
  function dupOf(tr) {
    const m = (x) => +String(x || '').slice(0, 2) * 60 + +String(x || '').slice(3, 5);
    return (S.trades || []).some((x) => x.account_id === SHM.acc && x.instrument === tr.instrument && x.direction === tr.direction && +x.contracts === +tr.contracts && x.date === tr.date
      && Math.abs(m(x.entry_time) - m(tr.entry_time)) <= 1 && (tr.entry == null || +x.entry === +tr.entry) && (tr.exit == null || +x.exit === +tr.exit));
  }
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
      if (SHM.copy.size) { d.copy_group = 'g' + d.id; SHM.copy.forEach((aid) => docs.push(Object.assign(JSON.parse(JSON.stringify(d)), { id: (typeof uid === 'function' ? uid() : 't' + Math.random().toString(36).slice(2)), account_id: aid }))); }
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
      else { const n2 = num(v); tr[f] = f === 'contracts' ? Math.max(1, Math.round(n2 || 1)) : n2; }
      if (f !== 'pnl') recompute(tr);
      flag(); paintMulti();
    }
  });
  window.SweepShotMulti = { open: openMulti, state: SHM };
  async function takeFiles(files) {
    files = files.filter((f) => f && /^image\//.test(f.type)); if (!files.length) return;
    if (files.length === 1 && !SH.batch.length && !SH.file) return takeFile(files[0]);
    if (SH.file && !SH.batch.length) SH.batch.push({ id: 'b0', file: SH.file, src: SH.src, shot: SH.shot, st: 'ok', f: { inst: SH.f.inst, dir: SH.dir, qty: SH.f.qty, date: SH.f.date, time: SH.f.time, exitTime: SH.f.exitTime, entry: SH.f.entry, exit: SH.f.exit, fees: SH.f.fees, net: SH.f.net } });
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
    return r ? `<b class="${n < 0 ? 'neg' : 'pos'}">${m}</b><span class="nav-am-rr">${(n / 100 / Math.abs(r) >= 0 ? '+' : '') + (n / 100 / Math.abs(r)).toFixed(2)} R</span>` : `<b class="${n < 0 ? 'neg' : 'pos'}">${m}</b><small class="muted">${t('rAdd')}</small>`;
  }
  function verifyLine() {
    const bits = [SH.f.inst, SH.dir ? t(SH.dir) : '', SH.f.qty ? SH.f.qty + ' ×' : '', SH.f.entry && SH.f.exit ? `${SH.f.entry} → ${SH.f.exit}` : '', SH.f.time || ''].filter(Boolean);
    return esc2(bits.join(' · '));
  }
  function autoPnl() {
    const e = num(SH.f.entry), x = num(SH.f.exit), q = num(SH.f.qty) || 1;
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
      const trs = res.ok && Array.isArray(j.trades) ? j.trades : [];
      if (trs.length >= 2) { SH.busy = false; openMulti([j], [{ src: SH.src, shot: SH.shot, name: file.name }]); return; }   // several trades: « X trades found »
      const d = trs[0];
      if (d) {   // one trade: the screen as before
        if (j.account_suggest && !SH.f.accountPicked) SH.f.account = j.account_suggest;
        if (d.instrument) SH.f.inst = d.instrument;
        if (d.direction) SH.dir = d.direction;
        if (d.contracts) SH.f.qty = String(d.contracts);
        if (d.date) SH.f.date = d.date;   // already the session (the server applies the 18:00 rule)
        if (d.entry_time) SH.f.time = String(d.entry_time).slice(0, 5);
        if (d.entry != null) SH.f.entry = String(d.entry);
        if (d.exit != null) SH.f.exit = String(d.exit);
        if (d.pnl_c != null) SH.f.net = ((d.pnl_c - (d.fees_c || 0)) / 100).toFixed(2);
        SH.f.exitTime = d.exit_time || ''; SH.f.fees = d.fees_c || 0;
        SH.status = t('read');
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
    if (!SH.dir) SH.dir = e != null && x != null && typed != null ? ((x > e) === (typed > 0) ? 'long' : 'short') : 'long';   // not needed to log a screenshot
    const net = typed != null ? typed : netC();
    if (!SH.f.account || net == null) { if (err) err.textContent = t('need'); return; }
    const pnl = net + (SH.f.fees || 0);
    const tm = /^\d{1,2}:\d{2}/.test(SH.f.time || '') ? (SH.f.time.length === 4 ? '0' + SH.f.time : SH.f.time).slice(0, 5) + ':00' : '';
    const emo = { before: [...SH.emo] }; if (SH.conf) emo.confidence = SH.conf; if (SH.exec) emo.execution = SH.exec;
    const doc = { id: typeof uid === 'function' ? uid() : 't' + Date.now(), account_id: SH.f.account, instrument: SH.f.inst, date: SH.f.date || today(), session_date: true, entry_time: tm, exit_time: SH.f.exitTime ? String(SH.f.exitTime).slice(0, 8) : '', direction: SH.dir, contracts: q,
      entry: e, exit: x, pnl_c: pnl, pnl_manual: true, real_pnl_c: net, risk_c: num(SH.f.risk) ? Math.round(Math.abs(num(SH.f.risk)) * 100) : null, stop: null, target: null, fees_c: SH.f.fees || null,
      discipline: Object.assign({}, SH.disc), emo, review: {}, shots: SH.shot ? [SH.shot] : [], tags: [], setup: '', notes: '', source: 'screenshot' };
    const copies = [...SH.copy].filter((id) => id !== doc.account_id && typeof acct === 'function' && acct(id));
    if (copies.length) doc.copy_group = typeof uid === 'function' ? uid() : 'g' + Date.now();
    if (typeof put === 'function') {
      put('trades', doc);
      copies.forEach((id) => put('trades', Object.assign(JSON.parse(JSON.stringify(doc)), { id: typeof uid === 'function' ? uid() : 't' + Math.random().toString(36).slice(2), account_id: id })));
    }
    if (quiet) return;
    close();
    if (typeof toast === 'function') toast(t('saved'));
    setTimeout(() => { if (typeof render === 'function') render(); }, 80);
  }

  /* events */
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('[data-am],[data-am-pick],[data-am-pickf],[data-am-sel],[data-am-copy],[data-am-seg],[data-am-emo],[data-am-rm]'); if (!a) return;
    const box = a.closest('.nav-am'); if (!box) return;
    if (a.dataset.amPick) { const v = a.dataset.amPick, opts = box._opts || {}; setMode(v); close(); if (typeof toast === 'function') toast(t('pref')); setTimeout(() => go(v, opts), 280); return; }
    if (a.dataset.amRm) { SH.batch = SH.batch.filter((b) => b.id !== a.dataset.amRm); if (SH.batch.length === 1) { const b = SH.batch[0]; SH.batch = []; Object.assign(SH, { file: b.file, src: b.src, shot: b.shot, dir: b.f.dir || SH.dir }); Object.assign(SH.f, b.f); } paint(); return; }
    if (a.dataset.amSel) { SH.openPick = SH.openPick === a.dataset.amSel ? null : a.dataset.amSel; paint(); return; }
    if (a.dataset.amPickf) { SH.f[a.dataset.amPickf] = a.dataset.v; if (a.dataset.amPickf === 'account') SH.f.accountPicked = true; SH.openPick = null; if (a.dataset.amPickf === 'account') SH.copy.delete(a.dataset.v); paint(); return; }
    if (a.dataset.amCopy) { const k = a.dataset.amCopy; SH.copy.has(k) ? SH.copy.delete(k) : SH.copy.add(k); a.classList.toggle('on'); return; }
    if (a.dataset.amSeg) { const k = a.dataset.amSeg, v = a.dataset.v; if (k === 'dir') SH.dir = v; else if (k === 'conf') SH.conf = +v; else if (k === 'exec') SH.exec = +v; else if (k.startsWith('d:')) SH.disc[k.slice(2)] = v; paint(); return; }
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
    if (act === 'save') save();
    if (act === 'to-manual') { const d = SH.f.date; close(); setTimeout(() => origTicket && origTicket(null, { date: d }), 280); }
  });
  document.addEventListener('toggle', (e) => { if (e.target.classList && e.target.classList.contains('nav-am-more-d')) SH.open = e.target.open; }, true);
  document.addEventListener('input', (e) => {
    const bn = e.target.closest && e.target.closest('.nav-am [data-am-bnet]'); if (bn) { const b = SH.batch.find((x) => x.id === bn.dataset.amBnet); if (b) b.f.net = bn.value; return; }
    const f = e.target.closest && e.target.closest('.nav-am [data-am-f]'); if (!f) return;
    SH.f[f.dataset.amF] = f.value;
    const v = autoPnl(), p = document.querySelector('.nav-am-net input'); if (p) p.placeholder = v != null ? ((v - (SH.f.fees || 0)) / 100).toFixed(2) : '+250';
    const r = document.querySelector('.nav-am-r'); if (r) r.innerHTML = rLine();
    const sm = document.querySelector('.nav-am-more-d summary small'); if (sm) sm.innerHTML = verifyLine();
  });
  document.addEventListener('change', (e) => {
    const f = e.target.closest && e.target.closest('.nav-am [data-am-file]'); if (f && f.files.length) { takeFiles([...f.files]); return; }
    const s = e.target.closest && e.target.closest('.nav-am select[data-am-f]'); if (s) SH.f[s.dataset.amF] = s.value;
  });
  /* (the default is no longer switched to « by hand » after a manual trade: screenshot stays first) */
  document.addEventListener('click', (e) => { const a = e.target.closest && e.target.closest('[data-am-imp]'); if (a) { e.preventDefault(); close(); setTimeout(() => { location.hash = '#import'; }, 250); } });
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
      const m = mode();
      if (!m) { go(document.body.classList.contains('ai-on') ? 'shot' : 'manual', opts); return; }   // one entry screen, no question
      go(m, opts);
    };
    w.__mode = true; window.openTicket = w;
  })(0);

  /* the manual form: the same two quiet buttons as the screenshot screen, right under the title —
   « From a screenshot » and « Import a file (Rithmic, TopstepX) » (no link in the header any more) */
  new window.SweepMO(() => {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || (typeof TK !== 'undefined' && TK && TK.id)) return;
    if (tk.querySelector('.nav-am-alt')) return;
    const head = tk.querySelector('.tk-head'); if (!head) return;
    const box = document.createElement('div'); box.className = 'nav-am-alt nav-tk-alt'; box.setAttribute('data-noi18n', '');
    box.innerHTML = `<button type="button" class="btn" data-tk-alt="shot">${t('fromShot')}</button><button type="button" class="btn" data-tk-alt="imp">${t('impFile')}</button>`;
    head.after(box);
    box.querySelector('[data-tk-alt=shot]').addEventListener('click', () => { const d = typeof TK !== 'undefined' && TK ? TK.date : null; if (typeof closeTicket === 'function') closeTicket(); setTimeout(() => shotForm({ date: d }), 300); });
    box.querySelector('[data-tk-alt=imp]').addEventListener('click', () => { if (typeof closeTicket === 'function') closeTicket(); setTimeout(() => { location.hash = '#import'; }, 250); });
  }).observe(document.body, { childList: true, subtree: true });

  /* Settings: the default way */
  function settingsRow() {
    if (!/^#settings/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main) return;
    const m = mode() || 'manual';
    const html = `<div class="nav-am-set" data-noi18n><div><b>${t('set')}</b><small class="muted">${t('setS')}</small></div><div class="seg"><button type="button" class="${m === 'shot' ? 'on' : ''}" data-am-set="shot">${t('shot')}</button><button type="button" class="${m === 'manual' ? 'on' : ''}" data-am-set="manual">${t('man')}</button></div></div>`;
    let row = main.querySelector('.nav-am-set');
    if (!row) { const first = main.querySelector('.surface'); if (!first) return; first.insertAdjacentHTML('beforeend', html); return; }
    if (row.outerHTML !== html.replace(/^\s+/, '')) row.outerHTML = html;
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-am-set]'); if (!b) return; setMode(b.dataset.amSet); setTimeout(() => { try { settingsRow(); } catch (x) { /* never blocks */ } }, 60); });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__am) {
    const w = function () { const out = appRender.apply(this, arguments); try { settingsRow(); } catch (e) { /* never blocks */ } return out; };
    w.__am = true; window.render = w;
  }
  window.SweepAddMode = { open: (opts) => shotForm(opts), ask: (opts) => chooser(opts) };
})();

/* ───────────── trade page: copy trading in plain sight ─────────────
 * The « Copy to accounts » action lived in the « ⋯ » menu. Now a line under the trade says where it is,
 * and offers to copy it to the other accounts (the trader may have forgotten when logging it). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: { only: 'Only on {a}.', also: 'Also on {l}.', ask: 'Did you take it on other accounts too?', btn: 'Copy to other accounts' },
    fr: { only: 'Seulement sur {a}.', also: 'Aussi sur {l}.', ask: 'Tu l’as pris sur d’autres comptes aussi ?', btn: 'Copier sur d’autres comptes' },
    es: { only: 'Solo en {a}.', also: 'También en {l}.', ask: '¿La tomaste también en otras cuentas?', btn: 'Copiar a otras cuentas' } }[L] || null;
  const tx = T || { only: 'Only on {a}.', also: 'Also on {l}.', ask: 'Did you take it on other accounts too?', btn: 'Copy to other accounts' };
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2.5"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>';
  function line() {
    const m = /^#trade\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), t = typeof getDoc === 'function' && getDoc('trades', id); if (!t || t.demo && !(S.accounts || []).some((a) => !a.demo)) { /* sample data: still show it */ }
    if (!t) return;
    const main = document.getElementById('main'); if (!main) return;
    const group = typeof copiesOf === 'function' ? copiesOf(t) : [t];
    const on = new Set(group.map((x) => x.account_id));
    const free0 = (S.accounts || []).filter((a) => a.status !== 'archived' && !on.has(a.id));
    // B14: ask only when another active account traded in the same session (likely copy trading); otherwise the
    // « Copy to accounts » action stays in the « ⋯ » menu, without a banner
    const free = free0.filter((a) => (S.trades || []).some((x) => x.account_id === a.id && x.date === t.date));
    const name = (aid) => (typeof acctLabel === 'function' ? acctLabel(aid) : aid);
    const others = group.filter((x) => x.id !== t.id).map((x) => name(x.account_id));
    const panelOpen = typeof CP !== 'undefined' && CP && CP.id === t.id;
    let html = '';
    if (free.length && !panelOpen) html = `<div class="nav-copy" data-noi18n><span class="nav-copy-ic">${ICON}</span><span class="nav-copy-t">${others.length ? tx.also.replace('{l}', esc2(others.join(', '))) : tx.only.replace('{a}', esc2(name(t.account_id)))} <b>${tx.ask}</b></span><button type="button" class="btn sm primary" data-act="copy-open" data-id="${esc2(t.id)}">${tx.btn}</button></div>`;
    else if (others.length && !panelOpen) html = `<div class="nav-copy done" data-noi18n><span class="nav-copy-ic">${ICON}</span><span class="nav-copy-t">${tx.also.replace('{l}', esc2(others.join(', ')))}</span></div>`;
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
 * rules.consistency_pct                      best day ≤ X % of the cycle's profit */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { t: 'Payout', rules: 'Payout rules', ready: 'Ready for a payout', notyet: 'Not yet', avail: 'You can request up to {v}', since: 'Counted since your last request ({d}).', first: 'Counted since the start of the account.', win: 'Winning days of {m}+', winAny: 'Profitable days', tdays: 'Traded days', cons: 'Best day ≤ {p} % of the profit', pos: 'Profitable since the last payout', cmin: 'Profit since the last payout', bal: 'Balance to keep', amt: 'Amount available (min {m})', none: 'Add your firm’s payout rules to see when you can request one.', f_days: 'Winning days required', f_wmin: 'Minimum profit per day ($)', f_min: 'Minimum payout ($)', f_max: 'Maximum per payout ($)', f_pct: 'Max % of the profit', f_bal: 'Balance to keep ($)', hint: 'Filled in by the preset of your firm when there is one. Check them on your firm’s site.' },
    fr: { t: 'Payout', rules: 'Règles de payout', ready: 'Prêt pour un payout', notyet: 'Pas encore', avail: 'Tu peux demander jusqu’à {v}', since: 'Compté depuis ta dernière demande ({d}).', first: 'Compté depuis le début du compte.', win: 'Jours gagnants de {m} et +', winAny: 'Jours profitables', tdays: 'Jours tradés', cons: 'Meilleur jour ≤ {p} % du profit', pos: 'Profitable depuis le dernier payout', cmin: 'Profit depuis le dernier payout', bal: 'Solde à garder', amt: 'Montant disponible (min {m})', none: 'Ajoute les règles de payout de ta firme pour voir quand tu pourras en demander un.', f_days: 'Jours gagnants requis', f_wmin: 'Profit minimum par jour ($)', f_min: 'Payout minimum ($)', f_max: 'Maximum par payout ($)', f_pct: 'Max % du profit', f_bal: 'Solde à garder ($)', hint: 'Remplies par le préréglage de ta firme quand il y en a un. Vérifie-les sur le site de ta firme.' },
    es: { t: 'Payout', rules: 'Reglas de payout', ready: 'Listo para un payout', notyet: 'Aún no', avail: 'Puedes pedir hasta {v}', since: 'Contado desde tu última solicitud ({d}).', first: 'Contado desde el inicio de la cuenta.', win: 'Días ganadores de {m} o más', winAny: 'Días rentables', tdays: 'Días operados', cons: 'Mejor día ≤ {p} % del beneficio', pos: 'Rentable desde el último payout', cmin: 'Beneficio desde el último payout', bal: 'Saldo a mantener', amt: 'Importe disponible (mín. {m})', none: 'Añade las reglas de payout de tu firma para ver cuándo puedes pedir uno.', f_days: 'Días ganadores requeridos', f_wmin: 'Beneficio mínimo por día ($)', f_min: 'Payout mínimo ($)', f_max: 'Máximo por payout ($)', f_pct: 'Máx. % del beneficio', f_bal: 'Saldo a mantener ($)', hint: 'Rellenadas por el preajuste de tu firma cuando existe. Compruébalas en el sitio de tu firma.' } };
  const t = (k) => (T[L] || T.en)[k];
  const $u = (c) => (typeof moneyU === 'function' ? moneyU(Math.round(c)) : '$' + (Math.round(c) / 100).toFixed(2));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const net1 = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0));

  function status(acc) {
    if (!acc) return null;
    const r = acc.rules || {};
    const has = r.payout_win_days || r.payout_trade_days || r.payout_min_bal_c || r.payout_min_c || r.payout_max_c || r.payout_cycle_pos;
    if (!has) return null;
    const pays = (S.payouts || []).filter((p) => p.account_id === acc.id && p.status !== 'rejected');
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
    if (r.payout_cycle_min_c && last) conds.push({ k: 'cmin', label: t('cmin'), ok: cycle >= r.payout_cycle_min_c, have: `${$u(Math.max(0, cycle))} / ${$u(r.payout_cycle_min_c)}`, frac: Math.max(0, Math.min(1, cycle / r.payout_cycle_min_c)) });
    if (r.consistency_pct && !r.target_c) {
      const pos = vals.filter((v) => v > 0), sum = pos.reduce((a, v) => a + v, 0), best = pos.length ? Math.max(...pos) : 0;
      const pct = sum > 0 ? (best / sum) * 100 : 0;
      conds.push({ k: 'cons', label: t('cons').replace('{p}', r.consistency_pct), ok: sum > 0 && pct <= r.consistency_pct, have: sum > 0 ? Math.round(pct) + ' %' : '—', frac: sum > 0 && pct <= r.consistency_pct ? 1 : 0 });
    }
    const minReq = r.payout_min_c || 0;
    if (r.payout_min_bal_c) conds.push({ k: 'bal', label: t('bal'), ok: bal >= r.payout_min_bal_c + minReq, have: `${$u(bal)} / ${$u(r.payout_min_bal_c + minReq)}`, frac: Math.max(0, Math.min(1, (bal - start) / Math.max(1, r.payout_min_bal_c + minReq - start))) });
    // what can be asked for
    let avail = r.payout_min_bal_c ? bal - r.payout_min_bal_c : bal - start;
    if (r.payout_max_pct) avail = Math.min(avail, Math.floor((bal - start) * r.payout_max_pct / 100));
    const nPaid = pays.filter((p) => p.status === 'paid' || p.status === 'approved').length;
    const cap = Array.isArray(r.payout_ladder_c) && r.payout_ladder_c.length ? r.payout_ladder_c[Math.min(nPaid, r.payout_ladder_c.length - 1)] : r.payout_max_c;
    if (cap) avail = Math.min(avail, cap);
    avail = Math.max(0, avail);
    conds.push({ k: 'amt', label: t('amt').replace('{m}', $u(minReq)), ok: avail >= Math.max(1, minReq), have: $u(avail), frac: minReq ? Math.max(0, Math.min(1, avail / minReq)) : (avail > 0 ? 1 : 0) });
    const breached = st && st.breached;
    const ready = !breached && conds.every((c) => c.ok);
    return { ready, conds, avail, last, pct: Math.round(Math.min(...conds.map((c) => c.frac)) * 100) };
  }
  window.SweepPayout = { status };

  /* the account page: conditions one by one, and the rules to edit */
  function card() {
    const m = /^#account\/([^/]+)/.exec(location.hash); if (!m) return;
    const id = decodeURIComponent(m[1]), a = typeof getDoc === 'function' && getDoc('accounts', id); if (!a) return;
    const main = document.getElementById('main'); if (!main) return;
    const r = a.rules || {}, s = status(a);
    const val = (k) => (r[k] == null ? '' : k.endsWith('_c') ? (r[k] / 100) : r[k]);
    const fld = (k, lab, ph) => `<label class="f"><span>${lab}</span><input inputmode="decimal" data-po="${k}" value="${esc2(val(k))}" placeholder="${ph || ''}"></label>`;
    const head = s ? `<div class="nav-po-h ${s.ready ? 'ok' : ''}"><b>${s.ready ? '✓ ' + t('ready') : t('notyet')}</b>${s.ready ? `<span>${t('avail').replace('{v}', $u(s.avail))}</span>` : ''}</div>
      <ul class="nav-po-c">${s.conds.map((c) => `<li class="${c.ok ? 'ok' : ''}"><i>${c.ok ? '✓' : ''}</i><span>${esc2(c.label)}</span><b>${esc2(c.have)}</b><s style="--w:${Math.round(c.frac * 100)}%"></s></li>`).join('')}</ul>
      <small class="muted">${s.last ? t('since').replace('{d}', s.last) : t('first')}</small>` : `<p class="muted nav-po-none">${t('none')}</p>`;
    const html = `<h3>${t('t')}</h3>${head}
      <details class="nav-po-rules" ${s ? '' : 'open'}><summary>${t('rules')}</summary><div class="fgrid">${fld('payout_win_days', t('f_days'), '5')}${fld('payout_win_min_c', t('f_wmin'), '150')}${fld('payout_min_c', t('f_min'), '500')}${fld('payout_max_c', t('f_max'))}${fld('payout_max_pct', t('f_pct'), '50')}${fld('payout_min_bal_c', t('f_bal'))}</div><small class="muted">${t('hint')}</small></details>`;
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
    en: { t: 'You passed {n}!', s: 'Profit target reached{d}, without breaking the drawdown. Did your firm confirm the pass?', go: 'Yes, move it to funded', later: 'Not yet', note: 'The evaluation stays in your history (archived, marked passed). A new funded account starts with the same firm and size{r}.', rules: ' and its funded rules', done: 'Funded account created', btn: 'Move to funded', btnS: 'Passed the evaluation? Create the funded account.', badge: 'Objectives reached', fund: 'Funded' },
    fr: { t: 'Tu as réussi {n} !', s: 'Objectif de profit atteint{d}, sans toucher au drawdown. Ta firme a confirmé la réussite ?', go: 'Oui, passer en financé', later: 'Pas encore', note: 'L’évaluation reste dans ton historique (archivée, marquée réussie). Un nouveau compte financé démarre avec la même firme et la même taille{r}.', rules: ' et ses règles de compte financé', done: 'Compte financé créé', btn: 'Passer en financé', btnS: 'Évaluation réussie ? Crée le compte financé.', badge: 'Objectifs atteints', fund: 'Financé' },
    es: { t: '¡Aprobaste {n}!', s: 'Objetivo de beneficio alcanzado{d}, sin tocar el drawdown. ¿Tu firma confirmó la aprobación?', go: 'Sí, pasar a financiada', later: 'Todavía no', note: 'La evaluación queda en tu historial (archivada, marcada aprobada). Una nueva cuenta financiada empieza con la misma firma y tamaño{r}.', rules: ' y sus reglas de cuenta financiada', done: 'Cuenta financiada creada', btn: 'Pasar a financiada', btnS: '¿Evaluación aprobada? Crea la cuenta financiada.', badge: 'Objetivos alcanzados', fund: 'Financiada' } };
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
  function toFunded(id, choice) {
    const a = getDoc('accounts', id); if (!a) return;
    const fr = fundedRules(a, choice);
    const nid = typeof uid === 'function' ? uid() : 'a' + Date.now();
    put('accounts', { id: nid, firm_id: a.firm_id, name: a.name, starting_balance_c: a.starting_balance_c, status: 'active', created_on: today(), phase: 'funded', money_type: 'funded', rules: fr.rules, preset: fr.preset, preset_ver: fr.ver || null, from_eval: a.id });
    try {   // the activation fee of the funded account, when the catalogue has one (editable in My money)
      const pr = fr.preset && window.SweepPresets && SweepPresets.priceOf ? SweepPresets.priceOf(fr.preset) : null;
      if (pr && pr.activation > 0) {
        put('expenses', { id: 'act-' + nid, account_id: nid, firm_id: a.firm_id || '', amount_c: Math.round(pr.activation * 100), date: today(), category: 'activation', notes: '' });
        if (typeof toast === 'function') toast(({ en: 'Activation fee added to your expenses', fr: 'Frais d’activation ajoutés à tes dépenses', es: 'Cuota de activación añadida a tus gastos' })[LANG] || 'Activation fee added to your expenses');
      }
    } catch (x) { /* the trader can add it in My money */ }
    editDoc('accounts', id, (d) => { d.status = 'archived'; d.result = 'passed'; d.passed_on = today(); d.phase = 'eval'; d.funded_id = nid; });
    if (typeof toast === 'function') toast(t('done'));
    setTimeout(() => { location.hash = '#account/' + nid; }, 300);
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
      <p class="nav-pass-s">${t('s').replace('{d}', esc2(d))}</p>
      <p class="muted nav-pass-n">${t('note').replace('{r}', fr.from ? t('rules') : '')}</p>
      ${choicesHtml(a) || `<button type="button" class="btn primary nav-am-save" data-pass-go="${esc2(a.id)}">${t('go')}</button>`}
      <button type="button" class="btn nav-pass-later" data-pass-later="${esc2(a.id)}">${t('later')}</button></div>`;
    document.body.append(scrim, el);
    requestAnimationFrame(() => { el.classList.add('open'); scrim.classList.add('open'); });
    scrim.addEventListener('click', () => later(a.id));
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
  /* when to ask: an evaluation just passed, once a day at most, never on top of another window */
  let asking = false;
  function check() {
    if (asking || document.querySelector('.nav-pass, #gSheet.open, #tkSlide.open, .nav-am.open, #gOb, .evp.open')) return;
    const a = (S.accounts || []).find((x) => passed(x) && x.pass_asked !== today());
    if (!a) return;
    if (a.preset && window.SweepPresets && SweepPresets.ready && !SweepPresets.ready()) SweepPresets.load();   // its choices (Topstep Standard / Consistency) are in the catalogue
    asking = true; setTimeout(() => { asking = false; if (passed(getDoc('accounts', a.id) || a) && !document.querySelector('.nav-pass')) ask(a); }, 900);
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
    const html = ok ? `<div class="nav-pass-row ok" data-noi18n><span>🏁 <b>${t('badge')}</b> · ${t('btnS')}</span><button type="button" class="btn sm primary" data-pass-btn="${esc2(id)}">${t('btn')}</button></div>`
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
  window.SweepPass = { passed, toFunded, ask };
})();

/* ───────────── live accounts, put forward ─────────────
 * A « LIVE » badge on live accounts (Today, account page), and on a funded account a line to move it to live
 * when the firm promotes it (Topstep Live, Lucid Live…): the funded account is archived (marked « went live »)
 * and the live account is created with the firm's live rules. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: { s: 'Promoted to a live account?', b: 'Move to live', done: 'Live account created' }, fr: { s: 'Promu en compte live ?', b: 'Passer en live', done: 'Compte live créé' }, es: { s: '¿Ascendido a cuenta live?', b: 'Pasar a live', done: 'Cuenta live creada' } }[L] || { s: 'Promoted to a live account?', b: 'Move to live', done: 'Live account created' };
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
    let row = main.querySelector('.nav-live-row');
    const show = a.phase === 'funded' && a.status !== 'archived';
    if (!show) { if (row) row.remove(); return; }
    if (!row) { const back = main.querySelector(':scope > .row'); if (!back) return; back.insertAdjacentHTML('afterend', `<div class="nav-pass-row nav-live-row" data-noi18n><span>${BADGE} ${T.s}</span><button type="button" class="btn sm" data-live-go="${esc2(id)}">${T.b}</button></div>`); }
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-live-go]'); if (!b) return;
    const a = getDoc('accounts', b.dataset.liveGo); if (!a) return;
    let rules = Object.assign({}, a.rules || {}), preset = null, start = a.starting_balance_c;
    const pv = a.preset && String(a.preset).split('|');
    if (pv && pv.length >= 4 && window.SweepPresets) { pv[3] = 'live'; const p = SweepPresets.rulesOf(pv.join('|')); if (p) { rules = p.rules; preset = pv.join('|'); if (p.start) start = Math.round(p.start * 100); } }
    else { rules.payout_max_c = null; rules.payout_ladder_c = null; }   // live: no sim payout caps
    const nid = typeof uid === 'function' ? uid() : 'a' + Date.now();
    const today = typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10);
    if (rules.dd_floor_c != null) rules.dd_c = Math.max(0, start - rules.dd_floor_c);   // live: a fixed balance floor (Topstep: $1,000)
    put('accounts', { id: nid, firm_id: a.firm_id, name: a.name, starting_balance_c: start, status: 'active', created_on: today, phase: 'live', money_type: 'live', rules, preset, from_funded: a.id });
    editDoc('accounts', a.id, (d) => { d.status = 'archived'; d.result = 'live'; d.live_on = today; d.live_id = nid; });
    if (typeof toast === 'function') toast(T.done);
    setTimeout(() => { location.hash = '#account/' + nid; }, 300);
  });
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
      const amt = SH.amounts, wr = st.wr != null ? Math.round(st.wr * (st.wr <= 1 ? 100 : 1)) + ' %' : '—';
      const pf = st.pf === Infinity ? '∞' : st.pf ? st.pf.toFixed(2) : '—';
      let c = 0; const curve = list.slice().sort((a, b) => ((a.date || '') + (a.entry_time || '')).localeCompare((b.date || '') + (b.entry_time || ''))).map((x) => (c += (typeof tNet === 'function' ? tNet(x) : 0)));
      return {
        label: t('label'), eyebrow: [per, list.length + ' trades'].filter(Boolean).join(' · '),
        big: list.length ? (amt ? money(net) : wr) : '—', tone: net >= 0 ? 'pos' : 'neg', sub: null,
        stats: [[t('wr'), wr], [t('pf'), pf], amt ? [t('trades'), String(list.length)] : [t('avgR'), st.avgR != null ? (st.avgR >= 0 ? '+' : '') + st.avgR.toFixed(2) + 'R' : '—']],
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
      const img = await SweepLinkPayload.image(SH.blob);
      const card = shData(SH.kind, SH.id) || {};
      const res = await fetch('api/share/create', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ kind: SH.kind === 'payouts' ? 'payouts' : SH.kind, lang: L, image: img, card: { label: card.label, eyebrow: card.eyebrow, big: String(card.big || '').replace(/<[^>]*>/g, ''), stats: card.stats, cap: card.cap } }) });
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
  let showName = true;
  try { showName = localStorage.getItem('sw.shName') !== '0'; } catch (e) { /* private mode */ }
  async function saveName(v) {
    const r = await fetch('api/me/name', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ full_name: v }) });
    if (r.ok) { S.me = Object.assign({}, S.me || {}, { full_name: v.trim() }); if (typeof toast === 'function') toast(t('saved')); return true; }
    return false;
  }
  window.SweepName = { get: fullName, save: saveName };

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
        tg.insertAdjacentHTML('afterbegin', fullName()
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
 * Sign-up asks only the email and the password; the trader is in right away. Before he adds his first account,
 * « Complete your profile » asks first name, last name, username, where he found Sweep and his accounts.
 * Settings gets a « Profile » section (first name and last name as two fields) and the support address. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { t: 'Complete your profile', s: 'Two more details and your journal is ready.', fn: 'First name', ln: 'Last name', un: 'Username', unH: 'Your public name in leagues and shared links.', fv: 'Where did you find Sweep?', choose: 'Choose…', vid: 'Which video?', acc: 'How many accounts do you trade, and with which firm(s)?', accPh: 'e.g. 3 × Apex 50K, 1 Topstep 150K', go: 'Continue', need: 'Enter your first and last name.', prof: 'Profile', save: 'Save', saved: 'Profile saved', help: 'Help & support', helpS: 'A question, an idea, a bug? Write to us, we answer every message.', friend: 'A friend', google: 'Google', other: 'Other', email: 'Email' },
    fr: { t: 'Complète ton profil', s: 'Deux petites infos et ton journal est prêt.', fn: 'Prénom', ln: 'Nom', un: 'Nom d’utilisateur', unH: 'Ton nom public dans les ligues et les liens partagés.', fv: 'Où as-tu trouvé Sweep ?', choose: 'Choisir…', vid: 'Quelle vidéo ?', acc: 'Combien de comptes trades-tu, et avec quelle(s) firme(s) ?', accPh: 'ex. 3 × Apex 50K, 1 Topstep 150K', go: 'Continuer', need: 'Entre ton prénom et ton nom.', prof: 'Profil', save: 'Enregistrer', saved: 'Profil enregistré', help: 'Aide et support', helpS: 'Une question, une idée, un bug ? Écris-nous, on répond à chaque message.', friend: 'Un ami', google: 'Google', other: 'Autre', email: 'Email' },
    es: { t: 'Completa tu perfil', s: 'Dos datos más y tu diario está listo.', fn: 'Nombre', ln: 'Apellido', un: 'Nombre de usuario', unH: 'Tu nombre público en ligas y enlaces compartidos.', fv: '¿Dónde encontraste Sweep?', choose: 'Elegir…', vid: '¿Qué video?', acc: '¿Cuántas cuentas operas y con qué firma(s)?', accPh: 'ej. 3 × Apex 50K, 1 Topstep 150K', go: 'Continuar', need: 'Escribe tu nombre y apellido.', prof: 'Perfil', save: 'Guardar', saved: 'Perfil guardado', help: 'Ayuda y soporte', helpS: '¿Una pregunta, una idea, un error? Escríbenos, respondemos cada mensaje.', friend: 'Un amigo', google: 'Google', other: 'Otro', email: 'Email' } };
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
    if (!b.first_name || !b.last_name) { if (err) err.textContent = t('need'); return false; }
    const r = await fetch('api/me/profile', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify(b) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { if (err) err.textContent = j.error || '—'; return false; }
    S.me = Object.assign({}, S.me || {}, { first_name: j.first_name, last_name: j.last_name, full_name: j.full_name, username: j.username });
    return true;
  }
  /* 1. before the first account */
  function ask() {
    if (!S.me || S.me.first_name || document.querySelector('.nav-prof')) return;
    if ((S.accounts || []).some((a) => !a.demo)) return;   // traders who already have accounts set it in Settings (or when sharing)
    if (!/^#?(dashboard)?$/.test((location.hash || '').replace(/^#/, '')) && !/^#dashboard/.test(location.hash)) return;
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-prof open';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-prof open'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in nav-prof-in"><h2>${t('t')}</h2><p class="muted">${t('s')}</p>
      <div class="nav-prof-g"><label class="f"><span>${t('fn')}</span><input data-pf="first_name" autocomplete="given-name" maxlength="40"></label><label class="f"><span>${t('ln')}</span><input data-pf="last_name" autocomplete="family-name" maxlength="40"></label></div>
      <div class="nav-prof-src"><span>${t('fv')} <em>${({ en: 'optional', fr: 'facultatif', es: 'opcional' })[L] || ''}</em></span><div class="nav-prof-chips">${SRC.map(([v, l]) => `<button type="button" class="chip" data-src="${v}">${T[L] && T[L][l] ? T[L][l] : l}</button>`).join('')}</div><input type="hidden" data-pf="found_via" value=""></div>
      <p class="err nav-prof-err"></p><button type="button" class="btn primary nav-am-save" data-prof-go>${t('go')}</button></div>`;
    document.body.append(scrim, el);
    setTimeout(() => { const i = el.querySelector('[data-pf=first_name]'); if (i) i.focus(); }, 80);
  }
  document.addEventListener('click', (e) => { const c = e.target.closest && e.target.closest('.nav-prof [data-src]'); if (!c) return; const box = c.closest('.nav-prof-in'); const was = c.classList.contains('on'); box.querySelectorAll('[data-src]').forEach((x) => x.classList.remove('on')); if (!was) c.classList.add('on'); box.querySelector('[data-pf=found_via]').value = was ? '' : c.dataset.src; });
  document.addEventListener('click', async (e) => {
    const g = e.target.closest && e.target.closest('[data-prof-go]'); if (!g) return;
    g.disabled = true; const ok = await save(g.closest('.nav-prof-in')); g.disabled = false;
    if (!ok) return;
    // then one question, one tap: how long he has been trading (kept for the default rules later on)
    const box = g.closest('.nav-prof-in'), X = EXP[L] || EXP.en;
    box.innerHTML = `<h2>${X.q}</h2><p class="muted">${X.s}</p><div class="nav-exp">${[['new', X.a], ['lt1', X.b], ['gt1', X.c]].map(([v, l]) => `<button type="button" class="nav-exp-o" data-exp="${v}">${l}</button>`).join('')}</div>
      <button type="button" class="link nav-exp-skip" data-exp="">${X.skip}</button>`;
    const f = box.querySelector('[data-exp]'); if (f) f.focus();
  });
  const EXP = { en: { q: 'How long have you been trading?', s: 'Sweep adapts its first settings to you.', a: 'I’m starting out', b: 'Less than a year', c: 'More than a year', skip: 'Skip' },
    fr: { q: 'Tu trades depuis combien de temps ?', s: 'Sweep adapte ses premiers réglages à toi.', a: 'Je commence', b: 'Moins d’un an', c: 'Plus d’un an', skip: 'Passer' },
    es: { q: '¿Desde cuándo operas?', s: 'Sweep adapta sus primeros ajustes a ti.', a: 'Estoy empezando', b: 'Menos de un año', c: 'Más de un año', skip: 'Omitir' } };
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('.nav-prof [data-exp]'); if (!b) return;
    const v = b.dataset.exp;
    b.closest('.nav-prof-in').querySelectorAll('[data-exp]').forEach((x) => { x.disabled = true; });
    if (v) {
      try {
        const r = await fetch('api/me/profile', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify({ first_name: S.me.first_name, last_name: S.me.last_name, experience: v }) });
        if (r.ok) S.me = Object.assign({}, S.me, { experience: v });
      } catch (x) { /* the answer is optional: never blocks the start */ }
    }
    document.querySelectorAll('.nav-prof').forEach((x) => x.remove()); if (typeof render === 'function') render();
  });
  /* 2. Settings: Profile first, and help & support */
  function settings() {
    if (!/^#settings/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-set-prof')) return;
    const first = main.querySelector('.surface'); if (!first) return;
    const sec = document.createElement('section'); sec.className = 'surface nav-set-prof'; sec.setAttribute('data-noi18n', '');
    sec.innerHTML = `<h2>${t('prof')}</h2>${fields(S.me || {}, true)}<p class="err nav-prof-err"></p><button type="button" class="btn primary" data-prof-save>${t('save')}</button>`;
    first.before(sec);
    const help = document.createElement('section'); help.className = 'surface nav-set-help'; help.setAttribute('data-noi18n', '');
    help.innerHTML = `<h2>${t('help')}</h2><p class="muted">${t('helpS')}</p><a class="btn" href="mailto:${SUPPORT}">${SUPPORT}</a>`;
    main.append(help);
  }
  document.addEventListener('click', async (e) => { const b = e.target.closest && e.target.closest('[data-prof-save]'); if (!b) return; b.disabled = true; const ok = await save(b.closest('.nav-set-prof')); b.disabled = false; if (ok && typeof toast === 'function') toast(t('saved')); });
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__prof) {
    const w = function () { const out = appRender.apply(this, arguments); try { settings(); setTimeout(ask, 400); } catch (e) { /* never blocks */ } return out; };
    w.__prof = true; window.render = w;
  }
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

/* computer, Today: the level becomes a small ring in the first section (no separate « Apprentice · Lv » row,
 * which overlapped the mission line); tapping it opens Progression like the row did */
(function () {
  'use strict';
  function merge() {
    if (window.SW_MQ.matches) return;
    const dash = document.querySelector('#main .nav-dash'); if (!dash) return;
    const rank = dash.querySelector('.d-rank .nav-rank'), mid = dash.querySelector('.g-today .gc-mid');
    if (!rank || !mid) return;
    const chip = [...mid.querySelectorAll('button, span, div')].find((x) => /^Lv\s?\d+/i.test((x.textContent || '').trim()) && x.children.length <= 3 && !x.closest('.nav-lvring'));
    document.body.classList.add('nav-lvr');
    if (!chip || chip.dataset.lvRing) return;
    const bar = [...chip.querySelectorAll('*')].find((x) => /width\s*:\s*[\d.]+%/.test(x.getAttribute('style') || ''));
    const pct = bar ? Math.max(0, Math.min(100, parseFloat((bar.getAttribute('style').match(/width\s*:\s*([\d.]+)%/) || [0, 0])[1]))) : 0;
    const lv = ((chip.textContent || '').match(/Lv\s?(\d+)/i) || [0, ''])[1];
    const r = 9, C = 2 * Math.PI * r;
    const ring = document.createElement('button'); ring.type = 'button'; ring.className = 'nav-lvring' + (rank.classList.contains('nav-dot') ? ' dot' : '');
    ring.title = (rank.innerText || '').replace(/\s+/g, ' ').trim();
    ring.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="${r}" class="bg"/><circle cx="12" cy="12" r="${r}" class="fg" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - pct / 100)}"/></svg><b>Lv ${lv}</b>`;
    ring.addEventListener('click', () => {
      rank.click();
      // keyboard users: when Progression closes, the focus comes back to the ring (the old row is hidden)
      const back = () => { if (document.querySelector('#gSheet')) { setTimeout(back, 120); return; } const r = document.querySelector('.nav-lvring'); if (r && (document.activeElement === document.body || !document.activeElement || document.activeElement.offsetParent === null)) r.focus(); };
      setTimeout(back, 300);
    });
    ring.dataset.pct = String(Math.round(pct)); ring.dataset.lv = lv;
    chip.dataset.lvRing = '1'; chip.replaceWith(ring);
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__lvr) {
    const w = function () { const out = appRender.apply(this, arguments); try { merge(); } catch (e) { /* never blocks */ } return out; };
    w.__lvr = true; window.render = w;
  }
  new window.SweepMO(() => { try { merge(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();

/* ───────────── October 7 notes ─────────────
 * 1. Stats: « Slippage and fees » hidden.
 * 2. Plan: setups optional (folded behind « + My setups (optional) »).
 * 3. Import: a visible « Import » button + a ⓘ « how to export from your platform » next to it (Trades, Calendar,
 *    Journal, both « New trade » forms).
 * 4. Payout cards: « Congrats {name} ! » where the period line was, the period line above the boxes; and the boxes
 *    can show discipline (win rate, average R:R, discipline) instead of dollars — discipline by default.
 * 5. Accounts: « How many » (several identical accounts at once) and « Account cost » (added to expenses).
 * 6. Payouts and expenses: « Also for » other accounts (one payout / expense per account at once). */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { setups: '+ My setups (optional)', imp: 'Import CSV', impH: 'How to export your trades from your platform', congrats: 'Congrats', show: 'Boxes', disc: 'Discipline', dol: 'Dollars', wr: 'Win rate', rr: 'Avg R:R', dsc: 'Discipline', qty: 'How many accounts', qtyH: 'Same firm, size and rules. Named #1, #2…', cost: 'Account cost ($)', costH: 'Optional: added to your expenses.', also: 'Also for', alsoH: 'Same entry for each account you pick.', added: (n) => `${n} added` },
    fr: { setups: '+ Mes setups (facultatif)', imp: 'Importer un CSV', impH: 'Comment exporter tes trades de ta plateforme', congrats: 'Congrats', show: 'Cases', disc: 'Discipline', dol: 'Dollars', wr: 'Taux de réussite', rr: 'R:R moyen', dsc: 'Discipline', qty: 'Nombre de comptes', qtyH: 'Même firme, taille et règles. Nommés #1, #2…', cost: 'Coût du compte ($)', costH: 'Facultatif : ajouté à tes dépenses.', also: 'Aussi pour', alsoH: 'La même entrée pour chaque compte choisi.', added: (n) => `${n} ajoutés` },
    es: { setups: '+ Mis setups (opcional)', imp: 'Importar CSV', impH: 'Cómo exportar tus operaciones de tu plataforma', congrats: 'Congrats', show: 'Casillas', disc: 'Disciplina', dol: 'Dólares', wr: 'Tasa de acierto', rr: 'R:R medio', dsc: 'Disciplina', qty: 'Número de cuentas', qtyH: 'Misma firma, tamaño y reglas. Nombradas #1, #2…', cost: 'Coste de la cuenta ($)', costH: 'Opcional: se añade a tus gastos.', also: 'También para', alsoH: 'La misma entrada para cada cuenta elegida.', added: (n) => `${n} añadidos` } };
  const t = (k) => (T[L] || T.en)[k];
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const nid = () => (typeof uid === 'function' ? uid() : 'x' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6));
  const ICON_I = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>';
  const ICON_IMP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5"/><path d="M5 19h14"/></svg>';
  const impHtml = (cls) => `<span class="nav-imp ${cls || ''}" data-noi18n><a class="btn sm nav-imp-b" href="#import" title="${esc2(t('impH'))}">${ICON_IMP}<span class="l">${t('imp')}</span><span class="s">CSV</span></a></span>`;   // the import page shows the instructions
  document.addEventListener('click', (e) => {
    if (e.target.closest && e.target.closest('[data-imp-help]')) { e.preventDefault(); if (window.SweepGuide) SweepGuide.open('import'); return; }
    const a = e.target.closest && e.target.closest('.nav-imp-b');
    if (a && (a.closest('#tkSlide') || a.closest('.nav-am'))) { e.preventDefault(); if (typeof closeTicket === 'function' && a.closest('#tkSlide')) closeTicket(); document.querySelectorAll('.nav-am [data-am=close]').forEach((b) => b.click()); setTimeout(() => { location.hash = '#import'; }, 250); }
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
      if (host) host.insertAdjacentHTML('beforebegin', `<div class="nav-acc-xs"><label class="f nav-acc-x" data-noi18n><span>${t('cost')}</span><input name="nav_cost" inputmode="decimal" placeholder="$"><small class="muted">${t('costH')}</small></label><label class="f nav-acc-x" data-noi18n><span>${t('qty')}</span><input name="nav_qty" type="number" min="1" max="20" value="1" inputmode="numeric"><small class="muted">${t('qtyH')}</small></label></div>`);
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
        const wr = W.length + Lo.length ? Math.round(W.length / (W.length + Lo.length) * 100) + ' %' : '—';
        const aw = W.length ? W.reduce((a, x) => a + n1(x), 0) / W.length : 0, al = Lo.length ? Math.abs(Lo.reduce((a, x) => a + n1(x), 0) / Lo.length) : 0;
        const rr = aw && al ? '1 : ' + (aw / al).toFixed(1) : '—';
        const ds = typeof tDisc === 'function' ? tr.map(tDisc).filter((x) => x != null) : [];
        const disc = ds.length ? Math.round(ds.reduce((a, x) => a + x, 0) / ds.length * (ds[0] <= 1 ? 100 : 1)) + ' %' : (st.disc != null ? Math.round(st.disc) + ' %' : '—');
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
    const wr = W.length + Lo.length ? Math.round(W.length / (W.length + Lo.length) * 100) + ' %' : '—';
    const aw = W.length ? W.reduce((a, x) => a + n1(x), 0) / W.length : 0, al = Lo.length ? Math.abs(Lo.reduce((a, x) => a + n1(x), 0) / Lo.length) : 0;
    const rr = aw && al ? '1 : ' + (aw / al).toFixed(1) : W.length ? '∞' : '—';
    const ds = typeof tDisc === 'function' ? tr.map(tDisc).filter((x) => x != null) : [];
    const disc = ds.length ? Math.round(ds.reduce((a, x) => a + x, 0) / ds.length * (ds[0] <= 1 ? 100 : 1)) + ' %' : '—';
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
    en: { title: 'Your routine today', how: 'How it works', of: '{n} of 3 done', swept: 'Day swept', closed: 'Markets are closed today. Rest is part of the process.', dayoffT: 'Day off', dayoff: 'No trading today: your streak is safe.',
      s1: 'Plan', s1d: 'Make your plan', s2: 'Execution', s2d: 'Trade your plan', s3: 'Review', s3d: 'Do your review',
      todo: 'To do', done: 'Done', late: 'Done after your first trade', noTrade: 'No trade yet', inPlan: '{c} of {n} trades in your plan', reviewTodo: 'To do after your session', reviewDone: 'Done',
      b1: 'Make my plan', b1v: 'See my plan', off: 'Not trading today', b2: 'Add a trade', b3: 'Do my review', b3v: 'See my review', streak: 'day streak', streak1: 'day streak', level: 'Level', yday: 'Yesterday is not finished: {t} left', ydayB: 'Finish yesterday', b1s: 'Plan it', b2s: '+ Trade', b3s: 'Review', see: 'See',
      help: 'Each day, three steps: plan before you trade, trade what you planned, review your day. All three = « day swept »: your streak goes on and you earn XP. Profit never counts, only the process.' },
    fr: { title: 'Ta routine du jour', how: 'Comment ça marche', of: '{n} sur 3 faites', swept: 'Journée réussie', closed: 'Les marchés sont fermés aujourd’hui. Le repos fait partie du processus.', dayoffT: 'Journée off', dayoff: 'Pas de trading aujourd’hui : ta série est protégée.',
      s1: 'Plan', s1d: 'Fais ton plan', s2: 'Exécution', s2d: 'Respecte ton plan', s3: 'Revue', s3d: 'Fais ta revue',
      todo: 'À faire', done: 'Fait', late: 'Fait après ton premier trade', noTrade: 'Aucun trade pour l’instant', inPlan: '{c} sur {n} trades dans ton plan', reviewTodo: 'À faire après ta séance', reviewDone: 'Faite',
      b1: 'Faire mon plan', b1v: 'Voir mon plan', off: 'Pas de trading aujourd’hui', b2: 'Ajouter un trade', b3: 'Faire ma revue', b3v: 'Voir ma revue', streak: 'jours de suite', streak1: 'jour de suite', level: 'Niveau', yday: 'Hier n’est pas terminé : encore {t}', ydayB: 'Terminer hier', b1s: 'Planifier', b2s: '+ Trade', b3s: 'Réviser', see: 'Voir',
      help: 'Chaque jour, trois étapes : planifie avant de trader, trade ce que tu as prévu, fais ta revue. Les trois = « journée réussie » : ta série continue et tu gagnes de l’XP. Le profit ne compte jamais, seulement le processus.' },
    es: { title: 'Tu rutina de hoy', how: 'Cómo funciona', of: '{n} de 3 hechas', swept: 'Día completado', closed: 'Los mercados están cerrados hoy. El descanso es parte del proceso.', dayoffT: 'Día libre', dayoff: 'Sin operar hoy: tu racha está protegida.',
      s1: 'Plan', s1d: 'Haz tu plan', s2: 'Ejecución', s2d: 'Respeta tu plan', s3: 'Revisión', s3d: 'Haz tu revisión',
      todo: 'Pendiente', done: 'Hecho', late: 'Hecho después de tu primera operación', noTrade: 'Aún sin operaciones', inPlan: '{c} de {n} operaciones en tu plan', reviewTodo: 'Pendiente tras tu sesión', reviewDone: 'Hecha',
      b1: 'Hacer mi plan', b1v: 'Ver mi plan', off: 'Hoy no opero', b2: 'Añadir una operación', b3: 'Hacer mi revisión', b3v: 'Ver mi revisión', streak: 'días seguidos', streak1: 'día seguido', level: 'Nivel', yday: 'Ayer no está terminado: quedan {t}', ydayB: 'Terminar ayer', b1s: 'Planificar', b2s: '+ Operación', b3s: 'Revisar', see: 'Ver',
      help: 'Cada día, tres pasos: planifica antes de operar, opera lo que planeaste, revisa tu día. Los tres = « día completado »: tu racha sigue y ganas XP. El beneficio nunca cuenta, solo el proceso.' } };
  const t = (k, v) => String((T[L] || T.en)[k]).replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ''));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const IC = {
    plan: '<path d="M8 4h8M9 2h6v4H9z"/><rect x="5" y="4" width="14" height="17" rx="2.5"/><path d="M9 11h6M9 15h4"/>',
    trade: '<path d="M4 17l5-5 4 4 7-7"/><path d="M15 9h5v5"/>',
    review: '<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/>',
    check: '<path d="M5 12.5l4.2 4.2L19 7"/>', fire: '<path d="M12 3c1 3 4 4.5 4 8.5a4 4 0 0 1-8 0c0-2 1-3 1-3s.5 1.5 2 1.5c0-3 1-5 1-7z"/>', help: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.1-2.4 3.6M12 17h.01"/>' };
  const svg = (k) => `<svg viewBox="0 0 24 24" aria-hidden="true">${IC[k]}</svg>`;
  // computer: the routine opens and closes (closed by default; the numbers stay visible). Phone: always open.
  // the routine opens every session (the next step stands out); the trader can fold it, until the session ends (1.1)
  const rtDay = () => { const st = window.SweepGame && SweepGame.state && SweepGame.state(); return (st && st.today && st.today.day) || ''; };
  const rtClosed = () => { try { const d = localStorage.getItem('sw.rtClosedDay'); return !!d && d === rtDay(); } catch (x) { return false; } };
  const FOLD = { en: ['Fold the routine', 'Unfold the routine'], fr: ['Replier la routine', 'Déplier la routine'], es: ['Plegar la rutina', 'Desplegar la rutina'] };
  const foldBtn = () => { const c = rtClosed(), f = FOLD[L] || FOLD.en; return `<button type="button" class="nav-rt-fold" data-rt="toggle" aria-expanded="${!c}" aria-label="${c ? f[1] : f[0]}"><svg class="nav-rt-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button>`; };
  const left = (dl) => { if (!dl) return ''; const s = Math.max(0, dl - Date.now() / 1000), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60); return h ? `${h} h ${String(m).padStart(2, '0')}` : `${m} min`; };
  function card() {
    const st = window.SweepGame && SweepGame.state && SweepGame.state(); const d = st && st.today;
    if (!d) return `<section class="surface nav-rt ph" data-noi18n aria-busy="true"><div class="nav-rt-h"><div><h2>${t('title')}</h2></div><div class="nav-rt-me"><span class="nav-rt-disc nav-rt-disc-ph" aria-hidden="true"></span><span class="nav-rt-sk w"></span><span class="nav-rt-sk"></span></div></div><div class="nav-rt-steps">${'<div class="nav-rt-s sk"></div>'.repeat(3)}</div></section>`;
    const p = st.profile || {}, y = st.yesterday && st.yesterday.market && !st.yesterday.valid && (st.yesterday.trades > 0 || st.yesterday.plan_valid) ? st.yesterday : null;   // only a day that was started is « not finished »
    const r = d.rings || {}, ring = document.querySelector('.nav-lvring');
    // level progress: from the game's own level bar (or the ring made from it)
    let pct = ring ? +ring.dataset.pct || 0 : 0;
    if (!pct) { const g = document.querySelector('#main .g-today'); const chip = g && [...g.querySelectorAll('*')].find((x) => /^Lv\s?\d+/i.test((x.textContent || '').trim()) && x.children.length <= 3); const bar = chip && [...chip.querySelectorAll('*')].find((x) => /width\s*:\s*[\d.]+%/.test(x.getAttribute('style') || '')); if (bar) pct = parseFloat(bar.getAttribute('style').match(/width\s*:\s*([\d.]+)%/)[1]) || 0; }
    const lv = (ring && ring.dataset.lv) || p.level || '';
    const streak = (p.streak && p.streak.current) || 0;
    const head = (extra) => `<div class="nav-rt-h"><div class="nav-rt-tg"><h2>${t('title')}</h2>${d.market ? foldBtn() : ''}${extra || ''}</div><div class="nav-rt-me"><span class="nav-rt-disc nav-rt-disc-ph" aria-hidden="true"></span>
        <button type="button" class="nav-rt-streak" data-rt="hub" title="${esc2(streak + ' ' + t(streak === 1 ? 'streak1' : 'streak'))}">${svg('fire')}<b>${streak}</b><span>${t(streak === 1 ? 'streak1' : 'streak')}</span></button>
        <button type="button" class="nav-rt-lv ${pct ? '' : 'nopct'}" data-rt="hub">${pct ? `<svg viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15" class="bg"/><circle cx="18" cy="18" r="15" class="fg" stroke-dasharray="94.25" stroke-dashoffset="${94.25 * (1 - pct / 100)}"/></svg>` : ''}<span><small>${t('level')}</small><b>${esc2(lv)}</b></span></button>
        <button type="button" class="nav-rt-help" data-rt="help" aria-label="${t('how')}">${svg('help')}</button></div></div>`;
    if (!d.market) return `<section class="surface nav-rt closed" data-noi18n>${head()}<p class="nav-rt-msg">${t('closed')}</p></section>`;
    if (d.day_off) return `<section class="surface nav-rt off" data-noi18n>${head(`<span class="nav-rt-pill ok">${svg('check')}${t('dayoffT')}</span>`)}<p class="nav-rt-msg">${t('dayoff')}</p></section>`;
    const s1 = r.plan >= 100 ? 'done' : r.plan > 0 ? 'late' : 'todo';
    const s2 = !d.trades ? 'wait' : r.execution >= 100 ? 'done' : 'part';
    const s3 = r.review >= 100 ? 'done' : 'todo';
    const n = [s1 !== 'todo', s2 === 'done', s3 === 'done'].filter(Boolean).length;
    const nextI = s1 === 'todo' ? 1 : !d.trades ? 2 : s3 !== 'done' ? 3 : 0;   // only the next step is highlighted
    const pill = d.swept ? `<span class="nav-rt-pill ok">${svg('check')}${t('swept')}</span>` : `<span class="nav-rt-pill">${t('of', { n })}</span>`;
    const step = (i, key, ic, title, sub, state, stateTxt, btn, act, extra, short) => `<div class="nav-rt-s ${state}${i === nextI ? ' next' : ''}"${i === nextI ? ' aria-current="step"' : ''}>
        <div class="nav-rt-si"><span class="nav-rt-n">${state === 'done' ? svg('check') : i}</span><span class="nav-rt-ic">${svg(ic)}</span></div>
        <div class="nav-rt-sb"><b>${title}</b><small>${sub}</small><span class="nav-rt-st">${stateTxt}</span></div>
        <div class="nav-rt-sa"><button type="button" class="btn sm ${i === nextI ? 'primary' : ''}" data-rt="${act}"><span class="l">${btn}</span><span class="s">${short}</span></button>${extra || ''}</div>
        <i class="nav-rt-bar"><i style="width:${key}%"></i></i></div>`;
    const execPct = d.trades ? Math.round((d.compliant || 0) / d.trades * 100) : 0;
    const ych = y ? `<button type="button" class="nav-rt-y" data-rt="yday" title="${esc2(t('yday', { t: left(y.deadline) }))}"><b>${t('ydayB')} ›</b><span>${esc2(left(y.deadline))}</span></button>` : '';
    return `<section class="surface nav-rt" data-noi18n>${head(pill + ych)}
      <div class="nav-rt-steps" data-next="${nextI}">
        ${step(1, r.plan || 0, 'plan', t('s1'), t('s1d'), s1, s1 === 'done' ? t('done') : s1 === 'late' ? t('late') : t('todo'), s1 === 'todo' ? t('b1') : t('b1v'), 'plan', s1 === 'todo' && !d.trades ? `<button type="button" class="link nav-rt-off" data-rt="dayoff">${t('off')}</button>` : '', s1 === 'todo' ? t('b1s') : t('see'))}
        ${step(2, d.trades ? execPct : 0, 'trade', t('s2'), t('s2d'), s2, d.trades ? t('inPlan', { c: d.compliant || 0, n: d.trades }) : t('noTrade'), t('b2'), 'trade', '', t('b2s'))}
        ${step(3, r.review || 0, 'review', t('s3'), t('s3d'), s3, s3 === 'done' ? t('reviewDone') : t('reviewTodo'), s3 === 'done' ? t('b3v') : t('b3'), 'review', '', s3 === 'done' ? t('see') : t('b3s'))}
      </div>
      <div class="nav-rt-help-t" hidden>${t('help')}</div></section>`;
  }
  function place() {
    if (!/^#?(dashboard)?$/.test((location.hash || '').replace(/^#/, ''))) return;
    const host = document.querySelector('#main .d-today'); if (!host) return;
    const cl = rtClosed(); const cur = host.querySelector('.nav-rt'); if (cur) cur.classList.toggle('closed-rt', cl);
    const html = card(); if (!html) return;
    let el = host.querySelector('.nav-rt');
    const ht = el && el.querySelector('.nav-rt-help-t'); const open = !!(ht && !ht.hidden);   // the loading card has no help text
    if (el && el._h === html) return;
    if (el) el.remove();
    host.insertAdjacentHTML('afterbegin', html);
    el = host.querySelector('.nav-rt'); el._h = html; if (open && el.querySelector('.nav-rt-help-t')) el.querySelector('.nav-rt-help-t').hidden = false;
    el.classList.toggle('closed-rt', rtClosed());
    document.body.classList.add('nav-rt-on');
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-rt]'); if (!b) return;
    const k = b.dataset.rt, g = document.querySelector('#main .g-today');
    if (k === 'plan') { if (window.SweepGame && SweepGame.openPlan) { const nx = window.SweepNextSession && SweepNextSession(); nx ? SweepGame.openPlan(nx) : SweepGame.openPlan(); } }
    else if (k === 'review') { if (window.SweepGame && SweepGame.openReview) SweepGame.openReview(); }
    else if (k === 'trade') { if (typeof openTicket === 'function') openTicket(); }
    else if (k === 'dayoff') { const o = g && g.querySelector('[data-g=dayoff]'); if (o) o.click(); }
    else if (k === 'yday') { const o = document.querySelector('#main [data-g=yday]'); if (o) o.click(); }
    else if (k === 'hub') {
      const cls = b.classList.contains('nav-rt-lv') ? '.nav-rt-lv' : '.nav-rt-streak';
      const o = document.querySelector('#main .nav-rank') || document.querySelector('.nav-lvring'); if (o) o.click(); else if (window.SweepGame) SweepGame.open('hub');
      // keyboard users: when Progression closes, the focus comes back to the button that opened it
      const back = () => { if (document.querySelector('#gSheet')) { setTimeout(back, 120); return; } const r = document.querySelector('#main .nav-rt ' + cls); if (r) r.focus(); };
      setTimeout(back, 300);
    }
    else if (k === 'help') { const h = b.closest('.nav-rt').querySelector('.nav-rt-help-t'); h.hidden = !h.hidden; }
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
  }
  new window.SweepMO(() => { try { labels(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });
})();


/* Stats: the rank opens Progression (what's done, what's next, missions); Payouts: « Share my payouts » above the numbers */
(function () {
  'use strict';
  document.addEventListener('click', (e) => {
    const r = e.target.closest && e.target.closest('#main #gIns .gm-ins-rank');
    if (r && !e.target.closest('button:not(.gm-ins-rank), a')) { if (window.SweepGame && SweepGame.open) SweepGame.open('hub'); }
  });
  function pass() {
    const rk = document.querySelector('#main #gIns .gm-ins-rank');
    if (rk && !rk.querySelector('.nav-rank-more')) { const m = document.createElement('span'); m.className = 'nav-rank-more'; m.setAttribute('data-noi18n', ''); m.textContent = ({ en: 'What’s next ›', fr: 'Voir la suite ›', es: 'Ver lo siguiente ›' })[(typeof LANG !== 'undefined' && LANG) || 'en'] || 'What’s next ›'; rk.append(m); }
    if (rk && !rk.dataset.go) { rk.dataset.go = '1'; rk.setAttribute('role', 'button'); rk.tabIndex = 0; rk.classList.add('nav-rank-go'); rk.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); rk.click(); } }); }
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
 * 2. Before the first account: « Hi {first name} », one sentence, one big button. The app's own setup form opens on tap.
 * 3a. Firms as a grid of initials badges · 3b. « New or already running? » (current balance, highest balance).
 * 5. Manual form at first glance: account, symbol, direction, contracts, entry/exit or net P&L; the rest under « More details ».
 * 6. First ring filled: one sentence, once. · 7. After the first trade, once: « Add Sweep to your home screen ». */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { hi: 'Hi {n}', one: 'Add your prop firm account: Sweep tracks its rules for you.', add: 'Add my account', state: 'New or already running?', nw: 'New', run: 'Already running', cur: 'Current balance ($)', peak: 'Highest balance reached ($)', peakH: 'Only for a drawdown that trails your highest balance.', more: 'More details', less: 'Fewer details', netH: 'or your net P&L', ring: 'Close the 3 rings = day swept. That’s your discipline.', instT: 'Add Sweep to your home screen', instS: 'Open it like an app, full screen, in one tap.', ios: 'iPhone', and: 'Android', i1: 'In Safari, tap Share', i2: 'Choose « Add to Home Screen »', i3: 'Tap « Add »', a1: 'In Chrome, tap the ⋮ menu', a2: 'Choose « Install app » or « Add to Home screen »', a3: 'Confirm', ok: 'Got it' },
    fr: { hi: 'Bonjour {n}', one: 'Ajoute ton compte de prop firm : Sweep suit ses règles pour toi.', add: 'Ajouter mon compte', state: 'Neuf ou déjà en cours ?', nw: 'Neuf', run: 'Déjà en cours', cur: 'Solde actuel ($)', peak: 'Plus haut solde atteint ($)', peakH: 'Seulement pour un drawdown qui suit ton plus haut solde.', more: 'Plus de détails', less: 'Moins de détails', netH: 'ou ton P&L net', ring: 'Ferme les 3 anneaux = journée balayée. C’est ta discipline.', instT: 'Ajoute Sweep à ton écran d’accueil', instS: 'Ouvre-le comme une app, plein écran, en un toucher.', ios: 'iPhone', and: 'Android', i1: 'Dans Safari, touche Partager', i2: 'Choisis « Sur l’écran d’accueil »', i3: 'Touche « Ajouter »', a1: 'Dans Chrome, touche le menu ⋮', a2: 'Choisis « Installer l’application » ou « Ajouter à l’écran d’accueil »', a3: 'Confirme', ok: 'Compris' },
    es: { hi: 'Hola {n}', one: 'Añade tu cuenta de prop firm: Sweep sigue sus reglas por ti.', add: 'Añadir mi cuenta', state: '¿Nueva o ya en curso?', nw: 'Nueva', run: 'Ya en curso', cur: 'Saldo actual ($)', peak: 'Saldo más alto alcanzado ($)', peakH: 'Solo para un drawdown que sigue tu saldo más alto.', more: 'Más detalles', less: 'Menos detalles', netH: 'o tu P&L neto', ring: 'Cierra los 3 anillos = día completado. Esa es tu disciplina.', instT: 'Añade Sweep a tu pantalla de inicio', instS: 'Ábrelo como una app, a pantalla completa, con un toque.', ios: 'iPhone', and: 'Android', i1: 'En Safari, toca Compartir', i2: 'Elige « Añadir a pantalla de inicio »', i3: 'Toca « Añadir »', a1: 'En Chrome, toca el menú ⋮', a2: 'Elige « Instalar aplicación » o « Añadir a pantalla de inicio »', a3: 'Confirma', ok: 'Entendido' } };
  const t = (k, v) => String((T[L] || T.en)[k]).replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ''));
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const LS = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } return null; };

  function pass() {
    // 2. before the first account: a simple screen; the app's form appears on tap
    const onb = document.querySelector('#main .onb');
    if (onb && !onb.dataset.simple) {
      onb.dataset.simple = '1'; onb.classList.add('nav-onb-direct');
      const ttl = onb.querySelector('h1, h2'); if (ttl) { ttl.textContent = ({ en: 'Your first account', fr: 'Ton premier compte', es: 'Tu primera cuenta' })[L] || 'Your first account'; ttl.setAttribute('data-noi18n', ''); }
    }
    if (false) {
      const fn = (S.me && (S.me.first_name || '')) || '';
      onb.insertAdjacentHTML('beforebegin', `<section class="nav-hello" data-noi18n><div class="nav-hello-ic" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="13" rx="3"/><path d="M3 10h18M8 15h4"/></svg></div><h1>${esc2(t('hi', { n: fn }).trim())}</h1><p>${t('one')}</p><button type="button" class="btn primary nav-hello-go" data-hello-go>${t('add')}</button></section>`);
    }
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
    }
    // 3b. new or already running (in the add-account form, next to the cost and count)
    const xs = document.querySelector('form[data-form="account"] .nav-acc-xs');
    if (xs && !xs.parentElement.querySelector('.nav-acst')) {
      xs.insertAdjacentHTML('beforebegin', `<div class="nav-acst" data-noi18n><span>${t('state')}</span><div class="seg"><button type="button" class="on" data-acst="new">${t('nw')}</button><button type="button" data-acst="run">${t('run')}</button></div>
        <div class="nav-acst-run" hidden><label class="f"><span>${t('cur')}</span><input name="nav_cur" inputmode="decimal" placeholder="$"></label><label class="f"><span>${t('peak')}</span><input name="nav_peak" inputmode="decimal" placeholder="$"><small class="muted">${t('peakH')}</small></label></div></div>`);
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
  document.addEventListener('click', (e) => {
    const g = e.target.closest && e.target.closest('[data-hello-go]');
    if (g) { const onb = document.querySelector('#main .onb'); const hello = g.closest('.nav-hello'); if (onb) { onb.classList.remove('nav-onb-hidden'); onb.classList.add('nav-onb-open'); } if (hello) hello.remove(); const f = onb && onb.querySelector('form[data-form="account"]'); if (f) f.scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
    const s = e.target.closest && e.target.closest('[data-acst]');
    if (s) { const box = s.closest('.nav-acst'); box.querySelectorAll('[data-acst]').forEach((x) => x.classList.toggle('on', x === s)); box.querySelector('.nav-acst-run').hidden = s.dataset.acst !== 'run'; return; }
    const m = e.target.closest && e.target.closest('.nav-more-b');
    if (m) { const tk = m.closest('#tkSlide'); const on = tk.classList.toggle('nav-tk-min'); LS('sw.tkMore', on ? '0' : '1'); m.textContent = on ? t('more') + ' ▾' : t('less') + ' ▴'; }
  });
  new window.SweepMO(() => { try { pass(); ring(); install(); } catch (e) { /* never blocks */ } }).observe(document.body, { childList: true, subtree: true });

  // 6. the first ring: one sentence under the routine, once, gone on tap
  function ring() {
    const card = document.querySelector('#main .nav-rt:not(.ph)'); if (!card || LS('sw.ringTip') === '1' || card.querySelector('.nav-ring-tip')) return;
    const st = window.SweepGame && SweepGame.state && SweepGame.state(); const r = st && st.today && st.today.rings; if (!r) return;
    if (!(r.plan > 0 || r.execution > 0 || r.review > 0)) return;
    const steps = card.querySelector('.nav-rt-steps'); if (!steps) return;
    steps.insertAdjacentHTML('afterend', `<button type="button" class="nav-ring-tip" data-noi18n>${t('ring')}</button>`);
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('.nav-ring-tip'); if (b) { LS('sw.ringTip', '1'); b.remove(); } });

  // 7. after the first trade, once (and only if not installed): add to home screen — the session's one window
  const standalone = () => (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  let seenTrades = null;
  function install() {
    if (typeof S === 'undefined' || !Array.isArray(S.trades)) return;
    const n = S.trades.filter((x) => !x.demo).length;
    if (seenTrades === null) { seenTrades = n; return; }
    if (n <= seenTrades) { seenTrades = n; return; }
    seenTrades = n;
    if (LS('sw.installShown') === '1' || standalone() || document.querySelector('.nav-inst')) return;
    try { if (sessionStorage.getItem('sw.modal') === '1') return; sessionStorage.setItem('sw.modal', '1'); } catch (x) { /* private mode */ }
    LS('sw.installShown', '1');
    const ios = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const step = (n2, ic, txt) => `<li><span class="nav-inst-n">${n2}</span><span class="nav-inst-ic">${ic}</span><span>${txt}</span></li>`;
    const SH_I = '<svg viewBox="0 0 24 24"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>';
    const ADD_I = '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8v8M8 12h8"/></svg>';
    const DOT_I = '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>';
    const OK_I = '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.2 4.2L19 7"/></svg>';
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-inst open';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-inst open'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in nav-inst-in"><div class="nav-inst-app" aria-hidden="true"><img src="icons/icon-192.png" alt="" onerror="this.remove()"></div><h2>${t('instT')}</h2><p class="muted">${t('instS')}</p>
      <div class="seg nav-inst-seg"><button type="button" class="${ios ? 'on' : ''}" data-inst="ios">${t('ios')}</button><button type="button" class="${ios ? '' : 'on'}" data-inst="and">${t('and')}</button></div>
      <ol class="nav-inst-l" data-for="ios" ${ios ? '' : 'hidden'}>${step(1, SH_I, t('i1'))}${step(2, ADD_I, t('i2'))}${step(3, OK_I, t('i3'))}</ol>
      <ol class="nav-inst-l" data-for="and" ${ios ? 'hidden' : ''}>${step(1, DOT_I, t('a1'))}${step(2, ADD_I, t('a2'))}${step(3, OK_I, t('a3'))}</ol>
      <button type="button" class="btn primary nav-am-save" data-inst-ok>${t('ok')}</button></div>`;
    document.body.append(scrim, el);
    const done = () => document.querySelectorAll('.nav-inst').forEach((x) => x.remove());
    scrim.addEventListener('click', done); el.querySelector('[data-inst-ok]').addEventListener('click', done);
    el.querySelectorAll('[data-inst]').forEach((b) => b.addEventListener('click', () => { el.querySelectorAll('[data-inst]').forEach((x) => x.classList.toggle('on', x === b)); el.querySelectorAll('.nav-inst-l').forEach((l) => { l.hidden = l.dataset.for !== b.dataset.inst; }); }));
  }
  window.SweepInstall = { show: () => { seenTrades = -1; LS('sw.installShown', '0'); try { sessionStorage.removeItem('sw.modal'); } catch (e) { /* private */ } install(); } };
})();

/* ───────────── Delivery 2 · expected gestures and clarity ─────────────
 * 9 « Ready for payout » → record the payout · 10 trade rows: swipe (phone) / ⋯ (computer) · 11 delete = « Deleted · Undo » 5 s
 * 12 pull to refresh · 13 « Mark as failed » + « Archived » · 14 account filter pill · 15 « per your platform »
 * 16 discipline score featured + explained · 17 « Discipline » share card first · 19 end of Pro trial card · + the line when
 * screenshot reading is not in the trader's plan. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = {
    en: { delAll: 'Deleted on {n} accounts', shotDel: 'Screenshot removed', qDel: 'Question removed', demoDel: 'Sample data removed', accDelT: 'Delete your Sweep account?', accDelS: 'Your account and all your data (trades, journals, accounts, payouts, expenses, screenshots) are deleted for good. This cannot be undone.', accDelGo: 'Delete for good', cancel: 'Cancel', edit: 'Edit', del: 'Delete', deleted: 'Deleted', undo: 'Undo', refresh: 'Release to refresh', refreshing: 'Refreshing…', failed: 'Mark as failed', failedQ: 'Mark this account as failed? It is archived; its trades and stats stay.', failedL: 'Failed', passedL: 'Passed', liveL: 'Went live', archived: 'Archived', allAcc: 'All accounts', platform: 'per your platform', disc: 'Discipline', discT: 'Your discipline score', discH: 'For each trade, the share of your checklist answered « yes » (stop respected, size, max loss, setup in your plan…). Your score is the average of your trades over the last 30 days.', discI: 'To raise it: answer your checklist on every trade, define your stop before entering, stay under your max loss and your number of trades, and trade the setups of your plan.', discLast: 'last 30 days', ok: 'Got it', dCard: 'My discipline', streak: 'Streak', swept: 'Days swept', score: 'Discipline', capD: (s, n) => `${s}-day streak, ${n} % discipline. The process, every day. Tracked with Sweep`, kDisc: 'Discipline', kStats: 'Stats', trial: 'In {n} days, your Pro trial ends. You use {f}.', trialB: 'See the plans', noAi: 'Screenshot reading is part of Pro: enter your trade by hand.', f: { shot: 'screenshot reading', copy: 'copy trading', link: 'shared Stats links', payout: 'payout conditions', ai: 'Sweep AI' } },
    fr: { delAll: 'Supprimé sur {n} comptes', shotDel: 'Capture retirée', qDel: 'Question retirée', demoDel: 'Données d’exemple retirées', accDelT: 'Supprimer ton compte Sweep ?', accDelS: 'Ton compte et toutes tes données (trades, journaux, comptes, payouts, dépenses, captures) sont supprimés pour de bon. C’est irréversible.', accDelGo: 'Supprimer pour de bon', cancel: 'Annuler', edit: 'Modifier', del: 'Supprimer', deleted: 'Supprimé', undo: 'Annuler', refresh: 'Relâche pour actualiser', refreshing: 'Actualisation…', failed: 'Marquer comme échoué', failedQ: 'Marquer ce compte comme échoué ? Il est archivé ; ses trades et ses stats restent.', failedL: 'Échoué', passedL: 'Réussi', liveL: 'Passé en live', archived: 'Archivés', allAcc: 'Tous les comptes', platform: 'selon ta plateforme', disc: 'Discipline', discT: 'Ton score de discipline', discH: 'Pour chaque trade, la part de ta checklist répondue « oui » (stop respecté, taille, perte max, setup dans ton plan…). Ton score est la moyenne de tes trades des 30 derniers jours.', discI: 'Pour le monter : réponds à ta checklist sur chaque trade, définis ton stop avant d’entrer, reste sous ta perte max et ton nombre de trades, et trade les setups de ton plan.', discLast: '30 derniers jours', ok: 'Compris', dCard: 'Ma discipline', streak: 'Série', swept: 'Jours réussis', score: 'Discipline', capD: (s, n) => `${s} jours de suite, ${n} % de discipline. Le processus, chaque jour. Suivi avec Sweep`, kDisc: 'Discipline', kStats: 'Stats', trial: 'Dans {n} jours, ton essai Pro se termine. Tu utilises {f}.', trialB: 'Voir les forfaits', noAi: 'La lecture des captures fait partie de Pro : saisis ton trade à la main.', f: { shot: 'la lecture des captures', copy: 'le copy trading', link: 'les liens de ta page Stats', payout: 'les conditions de payout', ai: 'Sweep AI' } },
    es: { delAll: 'Eliminado en {n} cuentas', shotDel: 'Captura quitada', qDel: 'Pregunta quitada', demoDel: 'Datos de ejemplo quitados', accDelT: '¿Eliminar tu cuenta de Sweep?', accDelS: 'Tu cuenta y todos tus datos (operaciones, diarios, cuentas, payouts, gastos, capturas) se eliminan para siempre. No se puede deshacer.', accDelGo: 'Eliminar para siempre', cancel: 'Cancelar', edit: 'Editar', del: 'Eliminar', deleted: 'Eliminado', undo: 'Deshacer', refresh: 'Suelta para actualizar', refreshing: 'Actualizando…', failed: 'Marcar como fallida', failedQ: '¿Marcar esta cuenta como fallida? Se archiva; sus operaciones y estadísticas se conservan.', failedL: 'Fallida', passedL: 'Aprobada', liveL: 'Pasó a live', archived: 'Archivadas', allAcc: 'Todas las cuentas', platform: 'según tu plataforma', disc: 'Disciplina', discT: 'Tu puntuación de disciplina', discH: 'Para cada operación, la parte de tu checklist respondida « sí » (stop respetado, tamaño, pérdida máx., setup de tu plan…). Tu puntuación es la media de tus operaciones de los últimos 30 días.', discI: 'Para subirla: responde tu checklist en cada operación, define tu stop antes de entrar, quédate bajo tu pérdida máx. y tu número de operaciones, y opera los setups de tu plan.', discLast: 'últimos 30 días', ok: 'Entendido', dCard: 'Mi disciplina', streak: 'Racha', swept: 'Días completados', score: 'Disciplina', capD: (s, n) => `${s} días seguidos, ${n} % de disciplina. El proceso, cada día. Registrado con Sweep`, kDisc: 'Disciplina', kStats: 'Stats', trial: 'En {n} días termina tu prueba Pro. Usas {f}.', trialB: 'Ver los planes', noAi: 'La lectura de capturas es parte de Pro: introduce tu operación a mano.', f: { shot: 'la lectura de capturas', copy: 'el copy trading', link: 'los enlaces de Stats', payout: 'las condiciones de payout', ai: 'Sweep AI' } } };
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
  function softDelete(coll, id, then) {
    const doc = getDoc(coll, id); if (!doc) return;
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
    location.hash = '#trades';
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
      fr: ['Ajouter des données d’exemple ?', 'Ajoute {n} trades d’exemple dans {a} comptes d’exemple. Tu peux les retirer quand tu veux dans les Réglages ; tes données ne sont pas touchées.', 'Ajouter {n} trades'],
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
    location.hash = '#payouts';
    let n = 0; (function fill() {
      const f = document.querySelector('form[data-form="payout"]');
      if (!f) { if (n++ < 30) setTimeout(fill, 100); return; }
      const sel = f.querySelector('[name="account"]'); if (sel) { sel.value = id; sel.dispatchEvent(new Event('change', { bubbles: true })); }
      f.scrollIntoView({ behavior: 'smooth', block: 'center' }); setTimeout(() => { const i = f.querySelector('[name="amount"]'); if (i) i.focus(); }, 350);
      f.classList.add('nav-flash'); setTimeout(() => f.classList.remove('nav-flash'), 1400);
    })();
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
  let py = null, pdist = 0, pel = null;
  const ptrPage = () => /^#?(dashboard|trades|analytics)?$/.test((location.hash || '').replace(/^#/, '').split('/')[0]);
  document.addEventListener('touchstart', (e) => { if (!isPhone() || !ptrPage() || scrollY > 0 || e.target.closest('.evp, .nav-am, .nav-dlg, #gSheet, #shPanel, .nav-fstrip, .nav-ra-row')) { py = null; return; } py = e.touches[0].clientY; pdist = 0; }, { passive: true });
  document.addEventListener('touchmove', (e) => { if (py == null) return; pdist = Math.max(0, e.touches[0].clientY - py); if (pdist < 8) return; if (!pel) { pel = document.createElement('div'); pel.className = 'nav-ptr'; pel.setAttribute('data-noi18n', ''); pel.innerHTML = '<i></i><span></span>'; document.body.append(pel); } const p = Math.min(1, pdist / 90); pel.style.setProperty('--p', p); pel.querySelector('span').textContent = p >= 1 ? t('refresh') : ''; }, { passive: true });
  document.addEventListener('touchend', async () => {
    if (py == null) return; py = null; if (!pel) return; const go = pdist >= 90; const el = pel; pel = null;
    if (!go) { el.remove(); return; }
    el.classList.add('busy'); el.querySelector('span').textContent = t('refreshing');
    try { if (typeof syncNow === 'function') await syncNow({ manual: true }); if (window.SweepGame && SweepGame.refresh) await SweepGame.refresh(); } catch (e) { /* keeps what is shown */ }
    if (typeof syncNow !== 'function') { location.reload(); return; }   // only if the app's sync is missing
    if (typeof render === 'function') render(); setTimeout(() => el.remove(), 300);
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
    const lab = (a) => a.result === 'failed' ? t('failedL') : a.result === 'passed' ? t('passedL') : a.result === 'live' ? t('liveL') : t('archived');
    const when = (a) => a.failed_on || a.passed_on || a.live_on || '';
    const html = `<details class="surface nav-arch" data-noi18n><summary>${t('archived')} · ${arch.length}</summary><div>${arch.map((a) => `<a class="nav-arch-r" href="#account/${esc2(a.id)}"><b>${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</b><span class="nav-arch-t ${a.result || ''}">${lab(a)}</span><small class="muted">${esc2(when(a))}</small></a>`).join('')}</div></details>`;
    const add = main.querySelector('[data-act="acct-add"]'); const host = (add && add.closest('.surface')) || main.lastElementChild; if (host) host.insertAdjacentHTML('afterend', html);
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-fail]'); if (!b) return;
    if (!confirm(t('failedQ'))) return;
    editDoc('accounts', b.dataset.fail, (d) => { d.status = 'archived'; d.result = 'failed'; d.failed_on = today(); });
    location.hash = '#accounts';
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
  function discScore() {
    const from = (() => { const d = new Date(today() + 'T12:00:00'); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10); })();
    let tr = (S.trades || []).filter((x) => !x.demo && x.date >= from); if (!tr.length) tr = (S.trades || []).filter((x) => x.date >= from);
    tr = typeof mergeCopies === 'function' ? mergeCopies(tr) : tr;
    const ds = typeof tDisc === 'function' ? tr.map(tDisc).filter((x) => x != null) : [];
    return ds.length ? Math.round(ds.reduce((a, x) => a + x, 0) / ds.length * (ds[0] <= 1 ? 100 : 1)) : null;
  }
  function discChip() {
    const me = document.querySelector('#main .nav-rt .nav-rt-me'); if (!me) return;
    const v = discScore(), key = String(v); let c = me.querySelector('.nav-rt-disc:not(.nav-rt-disc-ph)');
    if (c && c.dataset.v === key) return;   // unchanged: touch nothing (a DOM change here would wake every watcher again)
    const html = `<button type="button" class="nav-rt-disc" data-disc-why data-noi18n data-v="${key}"><small>${t('disc')}</small><b>${v == null ? '—' : v + '\u202f%'}</b></button>`;
    if (c) c.remove(); const ph = me.querySelector('.nav-rt-disc-ph'); if (ph) ph.remove(); me.insertAdjacentHTML('afterbegin', html);   // takes the placeholder's place: same size, nothing moves
  }
  function tradeDisc() {
    const m = /^#trade\/([^/]+)/.exec(location.hash || ''); if (!m) return;
    const main = document.getElementById('main'); if (!main || main.querySelector('.nav-tdisc')) return;
    const lab = [...main.querySelectorAll('span, small, div')].find((x) => x.children.length === 0 && /^(Discipline|Disciplina)$/i.test(x.textContent.trim()));
    const box = lab && lab.parentElement; if (!box) return;
    box.classList.add('nav-tdisc'); box.setAttribute('data-disc-why', 'trade'); box.setAttribute('role', 'button'); box.tabIndex = 0;
  }
  function discWhy(kind) {
    let v = discScore();
    if (kind === 'trade') { const m = /^#trade\/([^/]+)/.exec(location.hash || ''); const tr = m && getDoc('trades', decodeURIComponent(m[1])); const d = tr && typeof tDisc === 'function' ? tDisc(tr) : null; v = d == null ? null : Math.round(d * (d <= 1 ? 100 : 1)); }
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim nav-dwhy open';
    const el = document.createElement('aside'); el.className = 'nav-dlg nav-dwhy open'; el.setAttribute('role', 'dialog'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in nav-dwhy-in"><div class="nav-dwhy-v"><b>${v == null ? '—' : v + ' %'}</b><small>${kind === 'trade' ? ({ en: 'this trade', fr: 'ce trade', es: 'esta operación' })[L] : t('discLast')}</small></div><h2>${t('discT')}</h2><p>${t('discH')}</p><p class="muted">${t('discI')}</p><button type="button" class="btn primary nav-am-save" data-dwhy-ok>${t('ok')}</button></div>`;
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
      const s = (p.streak && p.streak.current) || 0, v = discScore(), nm = window.SweepName && SweepName.get();
      return { label: t('dCard'), eyebrow: new Date().toLocaleDateString(L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA', { month: 'long', year: 'numeric' }), big: v == null ? '—' : v + ' %', tone: 'pos', sub: null,
        stats: [[t('streak'), String(s)], [t('score'), v == null ? '—' : v + ' %'], [t('swept'), swept == null ? '—' : String(swept)]], demo: false, chart: null, bars: null, mark: true, who: nm || null, whoAt: 'eyebrow', cap: t('capD')(s, v == null ? 0 : v) };
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
        if (SH.kind !== 'discipline' && SH.kind !== 'stats') return out;
        const head = document.querySelector('#shPanel .sh-head'); if (!head || document.querySelector('#shPanel .nav-dk')) return out;
        head.insertAdjacentHTML('afterend', `<div class="seg nav-dk" data-noi18n><button type="button" class="${SH.kind === 'discipline' ? 'on' : ''}" data-dk="discipline">${t('kDisc')}</button><button type="button" class="${SH.kind === 'stats' ? 'on' : ''}" data-dk="stats">${t('kStats')}</button></div>`);
      } catch (e) { /* never blocks */ }
      return out;
    };
    w.__disc = true; w.__focus = true; w.__stl = true; w.__name = true; w.__link = true; w.__po = true; window.shRender = w;
  })(0);
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('[data-dk]'); if (!b) return; SH.kind = b.dataset.dk; SH.id = 'view'; SH.blob = null; shRender(); });
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('.nav-shstats')) { e.stopImmediatePropagation(); loadSwept().then(() => openShare('discipline', 'view')); } }, true);   // discipline first

  /* 19. end of the Pro trial: once, 10 days before */
  function trialCard() {
    const tr = typeof BILL !== 'undefined' && BILL.st && BILL.st.trial; const main = document.getElementById('main');
    const lead = tr && tr.kind === 'trial' ? 3 : 10;   // a 14-day trial: 3 days before the end · a long early access: 10 days before
    if (!tr || !main || !/^#?(dashboard)?$/.test((location.hash || '').replace(/^#/, '')) || tr.days_left > lead || tr.days_left <= 0) return;
    const key = 'sw.trialCard.' + String(tr.ends_at).slice(0, 10); if (LS(key) === '1' || main.querySelector('.nav-trial')) return;
    const all = (S.trades || []).filter((x) => !x.demo), used = [];
    if (all.some((x) => x.source === 'screenshot')) used.push(t('f').shot);
    if (all.some((x) => x.copy_group)) used.push(t('f').copy);
    if ((S.accounts || []).some((a) => a.rules && (a.rules.payout_win_days || a.rules.payout_min_bal_c))) used.push(t('f').payout);
    if (document.body.classList.contains('ai-on')) used.push(t('f').ai);
    if (!used.length) return;
    const list = used.length > 1 ? used.slice(0, -1).join(', ') + (L === 'en' ? ' and ' : L === 'es' ? ' y ' : ' et ') + used[used.length - 1] : used[0];
    const host = main.querySelector('.d-today') || main.firstElementChild; if (!host) return;
    host.insertAdjacentHTML('afterend', `<section class="surface nav-trial" data-noi18n><p>${esc2(t('trial').replace('{n}', tr.days_left).replace('{f}', list))}</p><a class="btn primary sm" href="#subscription" data-trial-ok>${t('trialB')}</a><button type="button" class="nav-trial-x" data-trial-x aria-label="✕">✕</button></section>`);
    LS(key, '1');
  }
  document.addEventListener('click', (e) => { const x = e.target.closest && e.target.closest('[data-trial-x]'); if (x) x.closest('.nav-trial').remove(); });

  let grpFor = null;
  function copiesFromGroup() {
    if (typeof TK === 'undefined' || !TK || TK.id || !document.querySelector('#tkSlide.open') || !TK.copyTo) return;
    if (grpFor === TK.account) return; grpFor = TK.account;
    const a = getDoc('accounts', TK.account); if (!a || !a.group_id) return;
    const sib = (S.accounts || []).filter((x) => x.group_id === a.group_id && x.id !== a.id && x.status !== 'archived'); if (!sib.length) return;
    sib.forEach((x) => TK.copyTo.add(x.id)); if (typeof tkRefresh === 'function') tkRefresh({ panel: true });
  }
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-act="tk-cancel"], #tkSlide .tk-x')) grpFor = null; }, true);

  /* (Delivery 1, point 4) without Sweep AI in the plan: say it in one line on the manual form */
  function noAiLine() {
    const tk = document.querySelector('#tkSlide.open .nav-tk-alt'); if (!tk || document.body.classList.contains('ai-on') || tk.querySelector('.nav-noai') || (typeof TK !== 'undefined' && TK && TK.id)) return;   // under the two buttons, not in the header
    tk.insertAdjacentHTML('beforeend', `<small class="nav-noai" data-noi18n>${t('noAi')}</small>`);
  }

  new window.SweepMO(() => { [rows, accountsExtras, filterPill, platformMark, discChip, tradeDisc, trialCard, noAiLine, copiesFromGroup].forEach((f) => { try { f(); } catch (e) { if (!f.__warned) { f.__warned = true; console.warn('Sweep:', f.name, e && e.message); } } }); /* each on its own: one failing never stops the others */ }).observe(document.body, { childList: true, subtree: true });
})();

/* motion: blocks rise into place when a page opens — only the blocks of that first draw. A later redraw of the same
 * page (data arriving, a sync) shows its content directly: it never fades in a second time. */
(function () {
  'use strict';
  let last = null, pending = false;
  window.addEventListener('hashchange', () => { const page = (location.hash || '#dashboard').split('/')[0]; if (page !== last) { last = page; pending = true; mark(); } });
  window.addEventListener('load', () => { last = (location.hash || '#dashboard').split('/')[0]; pending = true; setTimeout(mark, 30); });
  function mark() {
    if (!pending) return;
    const main = document.getElementById('main'); if (!main || !main.children.length) return;
    pending = false;
    const els = [...main.querySelectorAll(':scope > *:not(.nav-dash), :scope > .nav-dash > .d-today, :scope > .nav-dash > * > *')].filter((e) => !e.classList.contains('d-today') || e.parentElement.classList.contains('nav-dash'));
    els.slice(0, 12).forEach((e, i) => { e.classList.remove('sw-in'); e.style.animationDelay = Math.min(i, 4) * (window.SW_MQ && SW_MQ.matches ? 30 : 40) + 'ms'; e.classList.add('sw-in'); });
    clearTimeout(mark.t); mark.t = setTimeout(() => els.forEach((e) => { e.classList.remove('sw-in'); e.style.animationDelay = ''; }), 900);
  }
  const appRender = window.render;
  if (typeof appRender === 'function' && !appRender.__swin) {
    const w = function () { const out = appRender.apply(this, arguments); try { mark(); } catch (e) { /* never blocks */ } return out; };
    w.__swin = true; window.render = w;
  }
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
    en: { label: 'Day swept', eb: 'I completed my discipline today', sub: 'Have you completed yours?', streak: 'Streak', disc: 'Discipline', swept: 'Days swept', cap: (s) => `I completed my discipline today: plan, execution, review ✅${s ? ` ${s}-day streak.` : ''} Have you completed yours? makeitsweep.com` },
    fr: { label: 'Journée réussie', eb: 'J’ai complété ma discipline aujourd’hui', sub: 'Et toi, as-tu complété la tienne ?', streak: 'Série', disc: 'Discipline', swept: 'Jours réussis', cap: (s) => `J’ai complété ma discipline aujourd’hui : plan, exécution, revue ✅${s ? ` ${s} jours de suite.` : ''} Et toi, as-tu complété la tienne ? makeitsweep.com` },
    es: { label: 'Día completado', eb: 'Hoy completé mi disciplina', sub: '¿Y tú, completaste la tuya?', streak: 'Racha', disc: 'Disciplina', swept: 'Días completados', cap: (s) => `Hoy completé mi disciplina: plan, ejecución, revisión ✅${s ? ` ${s} días seguidos.` : ''} ¿Y tú, completaste la tuya? makeitsweep.com` } };
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
      const s = (p.streak && p.streak.current) || 0, nm = window.SweepName && SweepName.get();
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

document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('[data-q-share]')) { e.preventDefault(); if (window.SweepSweptShare && false) return; if (typeof openShare === 'function') openShare('discipline', 'view'); } });

/* avatar and menu header: the trader's initial and full name (not the generated username);
   Stats: no rank card on top (it lives in Progression), « From 5 trades » instead of « ∞ » under 5 trades; Trends message translated */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const FIVE = { en: 'From 5 trades', fr: 'Dès 5 trades', es: 'Desde 5 operaciones' }[L];
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
      const n = (S.trades || []).filter((x) => !x.demo || (S.trades || []).every((y) => y.demo)).length;
      if (n < 5) document.querySelectorAll('#main b, #main .big, #main strong').forEach((b) => { if (b.children.length === 0 && b.textContent.trim() === '∞') { b.textContent = FIVE; b.classList.add('nav-five'); } });
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

/* A4 · « Get started » lives at the top of the routine card while unfinished (no separate checklist at the bottom) */
(function () {
  'use strict';
  new window.SweepMO(() => {
    const st = document.querySelector('#main .gd-start'), rt = document.querySelector('#main .nav-rt:not(.ph)'); if (!st || !rt) return;
    const head = rt.querySelector('.nav-rt-h'); if (!head) return;
    if (st.parentElement !== rt) { head.after(st); st.classList.add('nav-start-in'); }
  }).observe(document.body, { childList: true, subtree: true });
})();

/* C12 · before the first account, the bottom « + » says why the account comes first */
document.addEventListener('click', (e) => {
  const b = e.target.closest && e.target.closest('.bottomnav .plus, aside.side .new'); if (!b) return;
  if (typeof S === 'undefined' || (S.accounts || []).some((a) => a.status !== 'archived')) return;
  setTimeout(() => { if (typeof toast === 'function') toast(({ en: 'Add your account first: every trade belongs to one.', fr: 'Ajoute d’abord ton compte : chaque trade lui appartient.', es: 'Añade primero tu cuenta: cada operación pertenece a una.' })[(typeof LANG !== 'undefined' && LANG) || 'en']); }, 250);
}, true);

/* B9 · after the 16:00 ET close (or on a day without a session), the Plan step prepares the next session */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const HOUR_ET = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: '2-digit', hourCycle: 'h23' });   // one formatter, not one per call
  /** the session the Plan prepares: from 16:00 to 18:00 the day is over → the next one; from 18:00 the new day has started
   *  (todayStr is already that day); weekends → Monday. null when it is simply today's plan, already done or not. */
  window.SweepNextSession = function () {
    const st = window.SweepGame && SweepGame.state && SweepGame.state(); const d = st && st.today;
    const h = +HOUR_ET.format(new Date()) % 24, today = typeof todayStr === 'function' ? todayStr() : null; if (!today) return null;
    const n = new Date(today + 'T12:00:00');
    if (h >= 16 && h < 18) n.setDate(n.getDate() + 1);
    while (n.getDay() === 0 || n.getDay() === 6) n.setDate(n.getDate() + 1);
    const target = `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}-${String(n.getDate()).padStart(2, '0')}`;
    if (d && d.rings && d.rings.plan >= 100 && target === (d.day || today)) return null;   // already planned
    return h >= 16 || target !== today || !d || !d.market ? target : null;
  };
  new window.SweepMO(() => {
    // never on the loading card: its steps have no title, so the tag landed next to the step, as a 4th cell of the grid (layout shift)
    const nx = window.SweepNextSession(); const s1 = document.querySelector('#main .nav-rt-s:first-child'); if (!s1 || s1.classList.contains('sk')) return;
    let tag = s1.querySelector('.nav-next-ses');
    if (!nx) { if (tag) tag.remove(); return; }
    const txt = ({ en: 'For the next session', fr: 'Pour la prochaine séance', es: 'Para la próxima sesión' })[L];
    if (!tag) { tag = document.createElement('small'); tag.className = 'nav-next-ses'; tag.setAttribute('data-noi18n', ''); const h = s1.querySelector('h3, b'); (h || s1).after(tag); }
    if (tag.textContent !== txt) tag.textContent = txt;
  }).observe(document.body, { childList: true, subtree: true });
})();

/* D15 · the discipline checklist on the manual form, right above « Save »: 3 questions, « See more » for the rest */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const W = ({ en: ['Yes', 'No', 'N/A', 'See more', 'Checklist'], fr: ['Oui', 'Non', 'N/A', 'Voir plus', 'Checklist'], es: ['Sí', 'No', 'N/A', 'Ver más', 'Checklist'] })[L];
  let ans = {}, before = null;
  function qs() { return ((typeof S !== 'undefined' && S.settings && S.settings.questions) || []).filter((q) => q.active !== false); }
  new window.SweepMO(() => {
    const tk = document.querySelector('#tkSlide.open'); if (!tk || (typeof TK !== 'undefined' && TK && TK.id)) { if (!tk) ans = {}; return; }
    if (tk.querySelector('.nav-ck')) return;
    const save = tk.querySelector('[data-act="tk-save"]'); const list = qs(); if (!save || !list.length) return;
    const box = document.createElement('div'); box.className = 'nav-ck';
    box.innerHTML = `<b class="nav-ck-t" data-noi18n>${W[4]}</b>` + list.map((q, i) => `<div class="nav-ck-q ${i > 2 ? 'more' : ''}" data-q="${q.id}"><span>${(q.text || q.q || q.label || q.id).replace(/[<>&]/g, '')}</span><div class="nav-ck-b" data-noi18n>${['y', 'n', 'na'].map((v, k) => `<button type="button" data-v="${v}">${W[k]}</button>`).join('')}</div></div>`).join('') + (list.length > 3 ? `<button type="button" class="link nav-ck-more" data-noi18n>${W[3]} ›</button>` : '');
    (save.closest('.tk-foot, .tk-actions') || save).before(box);
  }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.nav-ck-b button');
    if (b) { const q = b.closest('.nav-ck-q'); q.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b)); ans[q.dataset.q] = b.dataset.v; return; }
    const m = e.target.closest && e.target.closest('.nav-ck-more'); if (m) { m.closest('.nav-ck').classList.add('all'); m.remove(); return; }
    if (e.target.closest && e.target.closest('#tkSlide [data-act="tk-save"]') && !(typeof TK !== 'undefined' && TK && TK.id)) {
      before = new Set((S.trades || []).map((t) => t.id)); const a = Object.assign({}, ans);
      setTimeout(() => { if (!Object.keys(a).length) return; (S.trades || []).filter((t) => !before.has(t.id)).forEach((t) => editDoc('trades', t.id, (d) => { d.discipline = Object.assign({}, d.discipline || {}, a); })); ans = {}; }, 900);
    }
  }, true);
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

document.addEventListener('click', (e) => { const q = e.target.closest && e.target.closest('.d-quick [data-q="#payouts"]'); if (q) { try { sessionStorage.setItem('sw.openPayout', '1'); } catch (x) { /* private */ } } }, true);
new window.SweepMO(() => {
  let want = false; try { want = sessionStorage.getItem('sw.openPayout') === '1'; } catch (x) { /* private */ }
  if (!want || !/^#payouts/.test(location.hash || '')) return;
  const b = document.querySelector('#main .nav-pz-b[data-k="payout"]');
  if (!b) { const tab = document.querySelector('#main [data-mny-view="entries"]:not(.on)'); if (tab) tab.click(); return; }   // « My money » shown on « Analysis »: the add buttons are on « My entries »
  try { sessionStorage.removeItem('sw.openPayout'); } catch (x) { /* private */ }
  b.click(); setTimeout(() => { const f = document.querySelector('#main form[data-form="payout"]'); if (f) f.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150);
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
   Broker or firm, account name, starting balance, creation date. */
(function () {
  'use strict';
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = ({ en: ['Live account', 'Live rules differ from one platform to another: enter just the essentials. You can add your rules later on the account page.', '‹ Back', 'Broker or prop firm'], fr: ['Compte live', 'Les règles live varient d’une plateforme à l’autre : entre seulement l’essentiel. Tu pourras ajouter tes règles plus tard sur la page du compte.', '‹ Retour', 'Broker ou prop firm'], es: ['Cuenta live', 'Las reglas live cambian de una plataforma a otra: introduce solo lo esencial. Podrás añadir tus reglas más tarde en la página de la cuenta.', '‹ Volver', 'Bróker o prop firm'] })[L];
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('form[data-form="account"] [data-st-ph0="live"]'); if (!b) return;
    const f = b.closest('form');
    setTimeout(() => {
      f.classList.remove('ux-st-on', 'ux-st-final'); f.classList.add('nav-live'); f.dataset.uxPreset = '';
      const w = f.querySelector('.ux-st, .ux-pk'); if (w) w.hidden = true;
      if (!f.querySelector('.nav-live-h')) f.insertAdjacentHTML('afterbegin', `<div class="nav-live-h" data-noi18n><button type="button" class="link nav-live-back">${T[2]}</button><h3>${T[0]}</h3><p>${T[1]}</p></div>`);
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
    const f = b.closest('form'); delete f.dataset.acctMtype; f.classList.remove('nav-live'); f.classList.add('ux-st-on'); const w = f.querySelector('.ux-st, .ux-pk'); if (w) w.hidden = false; b.closest('.nav-live-h').remove();
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
  const MONEY = /^[−+\-]?\$?[\d,.\s]+(\s?\$|k|%)?$|^[−+\-]?\$[\d,.]+k?$/;
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
    const num = (v, d) => v.toLocaleString(loc, { maximumFractionDigits: d, minimumFractionDigits: 0, useGrouping: v >= 10000 });
    const cur = (body, unit) => (LG === 'en' ? `${sign}$${body}${unit}` : `${sign}${body}${unit ? '\u202f' + unit : ''}\u00a0$`);
    const out = [cur(num(Math.round(a), 0), '')];
    if (a >= 1000) out.push(a < 99950 ? cur(num(a / 1000, 1), 'k') : a < 999500 ? cur(num(a / 1000, 0), 'k') : cur(num(a / 1e6, a < 9995000 ? 2 : 1), 'M'));   // never « 1000 k »
    return out;
  }
  /** one figure: rounded / abbreviated (key figure tiles) then a smaller font, never cut by « … » */
  function fitOne(el) {
      if (el.children.length || !el.getClientRects().length) return;
      const tx = (el.textContent || '').trim(); if (!tx || tx.length > 18 || !/\d/.test(tx) || !MONEY.test(tx)) return;
      if (el.dataset.fitTx !== tx) { el.style.removeProperty('font-size'); el.dataset.fitTx = tx; }
      const box = el.clientWidth ? el : el.parentElement; if (!box) return;
      const over = el.scrollWidth - el.clientWidth > 1 || (box !== el && el.scrollWidth - box.clientWidth > 1);
      if (!over) return;
      const room = Math.max(1, (box === el ? el.clientWidth : box.clientWidth));
      // 11 · a key figure tile (Net P&L, balances…): rounded, then abbreviated, before the font gets smaller; the exact amount stays in its label
      if (!el.dataset.fitFull && el.closest('.nav-kpi-g, .d-perf')) {
        const c = centsOf(tx);
        if (c != null) {
          el.dataset.fitFull = tx; el.title = tx; el.setAttribute('aria-label', tx);
          for (const v of shorter(c, tx)) { el.textContent = v; if (el.scrollWidth <= room + 1) break; }
          el.dataset.fitTx = el.textContent.trim();
          if (el.scrollWidth <= room + 1) return;
        }
      }
      const fs = parseFloat(getComputedStyle(el).fontSize) || 16;
      el.style.setProperty('font-size', Math.max(fs * 0.55, Math.floor(fs * room / el.scrollWidth * 10) / 10) + 'px', 'important');   // « important »: the page's own sizes are !important too
      el.style.setProperty('text-overflow', 'clip'); el.style.setProperty('overflow', 'visible');
  }
  function fit() {
    q = 0;
    const main = document.getElementById('main'); if (!main) return;
    main.querySelectorAll('.neg, .pos, .big, .nav-acc-bal, .v, .num, b, strong').forEach(fitOne);
  }
  // the key figure tiles (a handful of elements) are fitted right after each redraw, before the browser paints:
  // a page redrawn by a sync never shows its P&L cut for a frame (the rest of the page keeps the per-frame pass)
  { const m0 = document.getElementById('main');
    if (m0) new MutationObserver(() => { const k = m0.querySelectorAll('.nav-kpi-g b, .d-perf b'); if (k.length) k.forEach(fitOne); }).observe(m0, { childList: true, subtree: true }); }
  const soon = () => { if (!q) q = requestAnimationFrame(fit); };
  if (window.SweepMO) new window.SweepMO(soon).observe(document.getElementById('main') || document.body, { childList: true, subtree: true });
  else new MutationObserver(soon).observe(document.body, { childList: true, subtree: true });
  addEventListener('resize', soon);
})();

/* B11: computer, Today — the two columns stay balanced (height gap ≤ 20 %): cards move from the taller column to the shorter.
   Stable: a card moves at most once per page, never back, and only when the gap gets smaller; the balance runs when the
   page is drawn and once more when late content has arrived — never while scrolling (it used to swap a card back and
   forth, and the page jumped). */
(function () {
  'use strict';
  function balance() {
    if (!window.SW_MQ || window.SW_MQ.matches) return;
    const dash = document.querySelector('#main .nav-dash'); if (!dash) return;
    dash.__bal = (dash.__bal || 0) + 1;   // no limit needed: a card moves at most once, so the columns cannot swap back and forth
    const a = dash.querySelector('.d-col-a'), b = dash.querySelector('.d-col-b'); if (!a || !b) return;
    const h = (c) => [...c.children].reduce((s, x) => s + (x.getClientRects().length ? x.getBoundingClientRect().height + 16 : 0), 0);
    const tried = new Set();
    for (let i = 0; i < 6; i++) {
      const ha = h(a), hb = h(b), big = ha > hb ? a : b, small = big === a ? b : a, hi = Math.max(ha, hb), lo = Math.min(ha, hb);
      if (!hi || (hi - lo) / hi <= 0.2) return;
      let movable = [...big.children].filter((x) => x.getClientRects().length && !x.dataset.balMoved && !tried.has(x) && !x.matches('.d-today, .nav-rt, .d-perf, .nav-merge, .d-news'));   // « What to watch » never moves: it stays under the day, whatever the filter
      if (!movable.length) { const mg = big.querySelector(':scope > .nav-merge'); const kids = mg ? [...mg.children].filter((x) => x.matches('.d-pay, .d-cal') && !x.dataset.balMoved && !tried.has(x) && x.getClientRects().length) : []; if (kids.length) movable = [kids[kids.length - 1]]; }
      const c = movable[movable.length - 1]; if (!c) return;
      if (c.parentElement && c.parentElement.classList.contains('nav-merge')) c.dataset.balFrom = 'merge';
      const ch = c.getBoundingClientRect().height + 16;
      if (Math.abs((hi - ch) - (lo + ch)) >= hi - lo) { tried.add(c); continue; }   // moving it would not help: try the next card
      small.append(c); c.dataset.balMoved = '1';
      const after = Math.abs(h(a) - h(b));
      if (after >= hi - lo) { (c.dataset.balFrom === 'merge' ? (big.querySelector(':scope > .nav-merge') || big) : big).append(c); continue; }   // its new size made it worse: back where it was (never tried again), try the next card
      const key = [...c.classList].find((k) => /^d-/.test(k)); if (key) remembered.set(key, small === a ? 'a' : 'b');
    }
  }
  // the page is redrawn now and then (sync, edits): the cards already moved go straight to their place, before the
  // page is painted — so a redraw never shows them in the other column for a moment (that was the jump)
  const remembered = new Map();
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
    setTimeout(balance, 700); setTimeout(balance, 1600); setTimeout(balance, 3200);   // again as the accounts, the news and the routine arrive (a card still moves only once)
  };
  if (window.SweepMO) new window.SweepMO(check).observe(document.getElementById('main') || document.body, { childList: true });
  addEventListener('resize', () => { const d = document.querySelector('#main .nav-dash'); if (d) { d.__bal = 0; balance(); } });
  window.SweepBalance = balance;
})();

/* B12 / B17: words — « Worst drawdown », « Exceeded », the regex for « Exceeded (n/m) » */
(function () {
  'use strict';
  const add = { fr: { 'My money': 'Mon argent', 'Worst drawdown': 'Pire recul', 'Exceeded': 'Dépassé', 'Avg win / loss': 'Gain / perte moy.', 'See its stats': 'Voir ses stats' },
    es: { 'My money': 'Mi dinero', 'Worst drawdown': 'Peor retroceso', 'Exceeded': 'Superado', 'Avg win / loss': 'Ganancia / pérdida media', 'See its stats': 'Ver sus estadísticas' } };
  try { if (window.I18N_FR) Object.assign(window.I18N_FR, add.fr); if (window.I18N_ES) Object.assign(window.I18N_ES, add.es); } catch (e) { /* the app stays in English */ }
  // « Exceeded (12/10) » → « Dépassé (12/10) »
  const L = (typeof LANG !== 'undefined' && LANG) || 'en'; if (L === 'en') return;
  const W = { fr: 'Dépassé', es: 'Superado' }[L];
  const fix = () => document.querySelectorAll('#main span.neg').forEach((x) => { if (!x.children.length && /^Exceeded( \(.*\))?$/.test(x.textContent.trim())) x.textContent = x.textContent.replace('Exceeded', W); });
  if (window.SweepMO) new window.SweepMO(fix).observe(document.getElementById('main') || document.body, { childList: true, subtree: true });
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

/* Journal without a date, after the day is over (16:00–18:00 ET) or on a weekend: if the plan was made for the next
   session, the journal opens on that day — where the plan is (otherwise it would show today's empty sheet). */
(function () {
  'use strict';
  const go = () => {
    try {
      if ((location.hash || '') !== '#journal') return;
      const nx = window.SweepNextSession && SweepNextSession(); if (!nx || nx === (typeof todayStr === 'function' ? todayStr() : nx)) return;
      const j = typeof getDoc === 'function' && getDoc('journals', nx);
      if (j && j.pre && (j.pre.bias || (j.pre.setups || []).length || j.pre.levels)) history.replaceState(null, '', '#journal/' + nx);
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
  if (window.SW_MQ && window.SW_MQ.addEventListener) window.SW_MQ.addEventListener('change', () => { if (typeof render === 'function') render(); });
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
