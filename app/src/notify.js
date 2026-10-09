/*
 * Sweep — notification center (Feature 0).
 * Loaded right after app.js and uses its globals: S, LANG, LOC, apiJSON, esc, swipeDismiss, haptic, toast, render.
 * Everything here is self-contained: its own EN / FR / ES strings (roots carry data-noi18n so the app's
 * automatic translator leaves them alone), its own sheet, modal and settings section.
 */
(function () {
  'use strict';
  if (typeof S === 'undefined' || typeof apiJSON !== 'function') return;

  /* ───────────── strings ───────────── */
  const D = {
    en: {
      'Notifications': 'Notifications',
      'Mark all as read': 'Mark all as read',
      'Close': 'Close',
      'Today': 'Today',
      'This week': 'This week',
      'Earlier': 'Earlier',
      'empty.title': "You're all caught up",
      'empty.body': 'Milestones, product updates and account alerts will show up here.',
      'View': 'View',
      'Not now': 'Not now',
      'Got it': 'Got it',
      'unread': '{n} unread',
      'now': 'Just now',
      'prefs.help': 'Choose what Sweep tells you about. Everything stays inside the app.',
      'cat.product_updates': 'Product updates',
      'cat.product_updates.d': 'New features and answers to your feedback',
      'cat.achievements': 'Achievements',
      'cat.achievements.d': 'Milestones worth celebrating',
      'cat.prop_alerts': 'Prop firm alerts',
      'cat.prop_alerts.d': 'Drawdown room, daily limit and profit target',
      'cat.streaks': 'Streaks',
      'cat.streaks.d': 'Your discipline streak',
      'cat.system': 'Account and data',
      'cat.system.d': 'Exports ready and account notices',
      'test.h': 'Test (administrator)',
      'test.normal': 'Send a notification',
      'test.celebration': 'Send a celebration',
      'test.sent': 'Sent. Open the bell.',
      'test.cel_sent': 'Sent. Reload the app to see the celebration.',
      'test.skipped': 'Skipped: daily limit or category turned off.',
      'saved': 'Saved',
      'error': 'Could not save. Try again.',
      'welcome.title': 'Your notifications live here',
      'welcome.body': 'Milestones, product updates and account alerts will show up right here, so you never miss a thing.',
      'test_normal.title': 'Test notification',
      'test_normal.body': 'If you can read this, notifications are working.',
      'test_celebration.title': 'Test celebration',
      'test_celebration.body': 'This is how your milestones will look.'
    },
    fr: {
      'Notifications': 'Notifications',
      'Mark all as read': 'Tout marquer comme lu',
      'Close': 'Fermer',
      'Today': "Aujourd'hui",
      'This week': 'Cette semaine',
      'Earlier': 'Plus tôt',
      'empty.title': 'Tout est à jour',
      'empty.body': 'Tes étapes importantes, les nouveautés et les alertes de tes comptes vont apparaître ici.',
      'View': 'Voir',
      'Not now': 'Plus tard',
      'Got it': 'OK',
      'unread': '{n} non lues',
      'now': "À l'instant",
      'prefs.help': "Choisis ce dont Sweep te parle. Tout reste dans l'app.",
      'cat.product_updates': 'Nouveautés',
      'cat.product_updates.d': 'Nouvelles fonctions et suivi de tes suggestions',
      'cat.achievements': 'Accomplissements',
      'cat.achievements.d': 'Les étapes qui méritent d’être soulignées',
      'cat.prop_alerts': 'Alertes prop firm',
      'cat.prop_alerts.d': 'Marge de drawdown, limite quotidienne et objectif de profit',
      'cat.streaks': 'Séries',
      'cat.streaks.d': 'Ta série de discipline',
      'cat.system': 'Compte et données',
      'cat.system.d': 'Exports prêts et avis sur ton compte',
      'test.h': 'Test (administrateur)',
      'test.normal': 'Envoyer une notification',
      'test.celebration': 'Envoyer une célébration',
      'test.sent': 'Envoyée. Ouvre la cloche.',
      'test.cel_sent': "Envoyée. Recharge l'app pour voir la célébration.",
      'test.skipped': 'Pas envoyée : limite quotidienne ou catégorie désactivée.',
      'saved': 'Enregistré',
      'error': "Impossible d'enregistrer. Réessaie.",
      'welcome.title': 'Tes notifications sont ici',
      'welcome.body': 'Tes étapes importantes, les nouveautés et les alertes de tes comptes vont apparaître ici. Tu ne manqueras rien.',
      'test_normal.title': 'Notification de test',
      'test_normal.body': 'Si tu lis ceci, les notifications fonctionnent.',
      'test_celebration.title': 'Célébration de test',
      'test_celebration.body': 'Voici de quoi auront l’air tes étapes importantes.'
    },
    es: {
      'Notifications': 'Notificaciones',
      'Mark all as read': 'Marcar todo como leído',
      'Close': 'Cerrar',
      'Today': 'Hoy',
      'This week': 'Esta semana',
      'Earlier': 'Antes',
      'empty.title': 'Estás al día',
      'empty.body': 'Tus logros, las novedades y las alertas de tus cuentas aparecerán aquí.',
      'View': 'Ver',
      'Not now': 'Ahora no',
      'Got it': 'Entendido',
      'unread': '{n} sin leer',
      'now': 'Ahora',
      'prefs.help': 'Elige de qué te avisa Sweep. Todo se queda dentro de la app.',
      'cat.product_updates': 'Novedades',
      'cat.product_updates.d': 'Nuevas funciones y respuestas a tus sugerencias',
      'cat.achievements': 'Logros',
      'cat.achievements.d': 'Hitos que vale la pena celebrar',
      'cat.prop_alerts': 'Alertas de prop firm',
      'cat.prop_alerts.d': 'Margen de drawdown, límite diario y objetivo de ganancia',
      'cat.streaks': 'Rachas',
      'cat.streaks.d': 'Tu racha de disciplina',
      'cat.system': 'Cuenta y datos',
      'cat.system.d': 'Exportaciones listas y avisos de tu cuenta',
      'test.h': 'Prueba (administrador)',
      'test.normal': 'Enviar una notificación',
      'test.celebration': 'Enviar una celebración',
      'test.sent': 'Enviada. Abre la campana.',
      'test.cel_sent': 'Enviada. Recarga la app para ver la celebración.',
      'test.skipped': 'No enviada: límite diario o categoría desactivada.',
      'saved': 'Guardado',
      'error': 'No se pudo guardar. Inténtalo de nuevo.',
      'welcome.title': 'Tus notificaciones están aquí',
      'welcome.body': 'Tus logros, las novedades y las alertas de tus cuentas aparecerán justo aquí, para que no te pierdas nada.',
      'test_normal.title': 'Notificación de prueba',
      'test_normal.body': 'Si puedes leer esto, las notificaciones funcionan.',
      'test_celebration.title': 'Celebración de prueba',
      'test_celebration.body': 'Así se verán tus logros.'
    }
  };
  const lang = () => (LANG === 'fr' || LANG === 'es' ? LANG : 'en');
  /** Translate a key. {name} placeholders come from params; a param "name_fr" wins over "name" in French. */
  function t(key, p) {
    const d = D[lang()];
    let s = d[key] != null ? d[key] : D.en[key] != null ? D.en[key] : key;
    if (p) s = s.replace(/\{(\w+)\}/g, (m, n) => {
      const v = p[n + '_' + lang()] != null && p[n + '_' + lang()] !== '' ? p[n + '_' + lang()] : p[n];
      return v != null ? String(v) : m;
    });
    return s;
  }
  /** Extend the dictionary (later features call SweepNotify.strings({...}) with their own keys). */
  function strings(more) {
    for (const l of ['en', 'fr', 'es']) Object.assign(D[l], (more && more[l]) || {});
  }

  /* ───────────── icons (SVG only; Geist has no ✓ glyph) ───────────── */
  const P = {
    bell: '<path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
    trophy: '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5v1.5A3.5 3.5 0 0 0 8.5 11M16 6h3v1.5a3.5 3.5 0 0 1-3.5 3.5M12 13v4M8.5 20h7M10 17h4"/>',
    check: '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.6"/>',
    flag: '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
    shield: '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/>',
    flame: '<path d="M12 21c3.9 0 6.5-2.6 6.5-6.2 0-3.6-2.6-5.6-3.9-8.8-.5 2.2-1.7 3.4-3 3.9.3-2.6-.6-5.2-3.2-6.9.2 3.4-2.9 5.6-2.9 10.1C5.5 18.4 8.1 21 12 21z"/>',
    gift: '<rect x="3.5" y="8" width="17" height="5" rx="1"/><path d="M5 13v7h14v-7M12 8v12M12 8c-1.8-3.6-5.5-3.6-5.5-1.3S9.3 8 12 8zm0 0c1.8-3.6 5.5-3.6 5.5-1.3S14.7 8 12 8z"/>',
    download: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    sparkle: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16l.7 1.8 1.8.7-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7z"/>',
    dollar: '<path d="M12 3v18M16.5 7.5c0-1.9-2-3-4.5-3s-4.5 1.1-4.5 3 2 2.7 4.5 3.2 4.5 1.4 4.5 3.3-2 3-4.5 3-4.5-1.1-4.5-3"/>'
  };
  const icon = (n, cls) => `<svg class="${cls || ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[n] || P.bell}</svg>`;

  /* ───────────── state + server ───────────── */
  const NT = { items: null, unread: 0, modal: null, modalDone: false, busy: false, at: 0, prefs: null, open: false };
  const on = () => S.mode === 'server' && !!S.me;

  async function load(force) {
    if (!on() || NT.busy || (!force && Date.now() - NT.at < 15000)) return;
    NT.busy = true;
    try {
      const r = await apiJSON('api/notifications');
      NT.items = r.items || [];
      NT.unread = r.unread || 0;
      NT.modal = r.modal || null;
      NT.at = Date.now();
      paintBadge();
      if (NT.open) paintSheet();
      maybeModal();
    } catch (e) {
      if (NT.items == null) NT.items = [];
    } finally {
      NT.busy = false;
    }
  }
  const post = (url, body) => apiJSON(url, { method: 'POST', body: body || {} });

  /* ───────────── bell ───────────── */
  function paintBadge() {
    document.querySelectorAll('[data-nt="bell"]').forEach((b) => {
      b.hidden = !on();
      b.setAttribute('aria-label', t('Notifications') + (NT.unread ? ' · ' + t('unread', { n: NT.unread }) : ''));
      const badge = b.querySelector('.nt-badge');
      if (badge) {
        badge.textContent = NT.unread > 9 ? '9+' : String(NT.unread || '');
        badge.hidden = !NT.unread;
      }
    });
  }

  /* ───────────── time ───────────── */
  const dayKey = (d) => d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
  function groupOf(iso) {
    const d = new Date(iso), now = new Date();
    if (dayKey(d) === dayKey(now)) return 'Today';
    return now - d < 7 * 86400000 ? 'This week' : 'Earlier';
  }
  function ago(iso) {
    const d = new Date(iso), s = (Date.now() - d) / 1000;
    if (s < 60) return t('now');
    try {
      const rtf = new Intl.RelativeTimeFormat(LOC(), { numeric: 'auto', style: 'short' });
      if (s < 3600) return rtf.format(-Math.round(s / 60), 'minute');
      if (s < 86400) return rtf.format(-Math.round(s / 3600), 'hour');
      if (s < 7 * 86400) return rtf.format(-Math.round(s / 86400), 'day');
    } catch (e) { /* older browsers: fall through to a date */ }
    return d.toLocaleDateString(LOC(), { month: 'short', day: 'numeric' });
  }

  /* ───────────── sheet ───────────── */
  function itemHtml(n) {
    const tone = n.priority === 'celebration' ? 'cel' : (n.params && n.params.tone === 'caution' ? 'caution' : '');
    return `<li><button type="button" class="nt-item${n.read ? '' : ' unread'}" data-nt="open" data-id="${n.id}">
      <span class="nt-ic ${tone}">${icon(n.icon)}</span>
      <span class="nt-txt"><b>${esc(t(n.title_key, n.params))}</b>${n.body_key ? `<span>${esc(t(n.body_key, n.params))}</span>` : ''}<small>${esc(ago(n.created_at))}</small></span>
      <i class="nt-dot" aria-hidden="true"></i></button></li>`;
  }
  function sheetHtml() {
    const items = NT.items || [];
    let body;
    if (NT.items == null) body = '<div class="nt-skel"><div class="skel"></div><div class="skel"></div><div class="skel"></div></div>';
    else if (!items.length) {
      body = `<div class="nt-empty">${icon('check', 'nt-empty-ic')}<b>${esc(t('empty.title'))}</b><p>${esc(t('empty.body'))}</p></div>`;
    } else {
      const groups = { 'Today': [], 'This week': [], 'Earlier': [] };
      items.forEach((n) => groups[groupOf(n.created_at)].push(n));
      body = Object.keys(groups).filter((g) => groups[g].length).map((g) =>
        `<section class="nt-grp"><h3>${esc(t(g))}</h3><ul>${groups[g].map(itemHtml).join('')}</ul></section>`).join('');
    }
    return `<div class="nt-head"><h2>${esc(t('Notifications'))}</h2>
      ${NT.unread ? `<button type="button" class="link nt-all" data-nt="all">${esc(t('Mark all as read'))}</button>` : ''}
      <button type="button" class="nt-x" data-nt="close" aria-label="${esc(t('Close'))}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
      <div class="nt-body">${body}</div>`;
  }
  function sheetEl() {
    let el = document.getElementById('ntSheet');
    if (el) return el;
    el = document.createElement('aside');
    el.id = 'ntSheet';
    el.className = 'evp ntsh';
    el.setAttribute('data-noi18n', '');
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.innerHTML = '<div class="evp-in nt-in"></div>';
    document.body.append(el);
    const scrim = document.createElement('div');
    scrim.id = 'ntScrim';
    scrim.className = 'evp-scrim';
    scrim.addEventListener('click', closeSheet);
    document.body.append(scrim);
    if (typeof swipeDismiss === 'function') swipeDismiss(el, { scroller: () => el.querySelector('.evp-in'), onClose: closeSheet });
    return el;
  }
  function paintSheet() {
    const el = sheetEl();
    el.setAttribute('aria-label', t('Notifications'));
    el.querySelector('.nt-in').innerHTML = sheetHtml();
  }
  function openSheet() {
    if (!on()) return;
    NT.open = true;
    paintSheet();
    load(true);
    requestAnimationFrame(() => {
      document.getElementById('ntSheet').classList.add('open');
      document.getElementById('ntScrim').classList.add('open');
      document.body.classList.add('evp-lock');
      const x = document.querySelector('#ntSheet [data-nt="close"]');
      if (x && !matchMedia('(pointer: coarse)').matches) x.focus({ preventScroll: true });
    });
  }
  function closeSheet() {
    NT.open = false;
    const el = document.getElementById('ntSheet');
    if (!el) return;
    el.classList.remove('open');
    document.getElementById('ntScrim').classList.remove('open');
    document.body.classList.remove('evp-lock');
  }
  function go(url) {
    if (!url) return;
    if (url[0] === '#') { if (location.hash !== url) location.hash = url; }
    else if (url[0] === '/') location.href = url;
  }
  function openItem(id) {
    const n = (NT.items || []).find((x) => x.id === id);
    if (!n) return;
    if (!n.read) {
      n.read = true;
      NT.unread = Math.max(0, NT.unread - 1);
      paintBadge();
      post(`api/notifications/${id}/read`).catch(() => {});
    }
    if (n.action_url) { closeSheet(); go(n.action_url); } else paintSheet();
  }
  function markAll() {
    (NT.items || []).forEach((n) => { n.read = true; });
    NT.unread = 0;
    paintBadge();
    paintSheet();
    post('api/notifications/read-all').catch(() => load(true));
  }

  /* ───────────── celebration modal (once per app open) ───────────── */
  function maybeModal() {
    const n = NT.modal;
    if (!n || NT.modalDone || !on() || document.visibilityState !== 'visible') return;
    if (document.body.classList.contains('evp-lock') || document.querySelector('.drawer.on, .nt-modal, .sb-layer, .sai-open')) return;   // never on top of another sheet
    NT.modalDone = true;
    post(`api/notifications/${n.id}/shown`).catch(() => {});
    // one automatic modal per session belongs to the game (onboarding, rank); notification celebrations are a short toast
    if (typeof toast === 'function') toast(t(n.title_key, n.params));
  }
  function closeModal(follow) {
    const m = document.querySelector('.nt-modal');
    if (!m) return;
    const n = m._n;
    if (n) {
      const it = (NT.items || []).find((x) => x.id === n.id);
      if (it && !it.read) { it.read = true; NT.unread = Math.max(0, NT.unread - 1); paintBadge(); }
      post(`api/notifications/${n.id}/read`).catch(() => {});
    }
    NT.modal = null;
    m.classList.remove('in');
    setTimeout(() => m.remove(), matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 220);
    if (follow && n) go(n.action_url);
  }

  /* ───────────── Settings → Notifications ───────────── */
  const CATS = ['product_updates', 'achievements', 'prop_alerts', 'streaks', 'system'];
  function prefsHtml() {
    const p = NT.prefs;
    const rows = CATS.map((c) => `<label class="nt-prow"><span><b>${esc(t('cat.' + c))}</b><small>${esc(t('cat.' + c + '.d'))}</small></span>
      <span class="sw"><input type="checkbox" data-nt-pref="${c}" ${!p || p[c] !== false ? 'checked' : ''} ${p ? '' : 'disabled'} aria-label="${esc(t('cat.' + c))}"><i></i></span></label>`).join('');
    const admin = S.me && S.me.is_admin ? `<div class="nt-test"><span class="muted">${esc(t('test.h'))}</span>
      <button type="button" class="btn sm" data-nt="test" data-k="normal">${esc(t('test.normal'))}</button>
      <button type="button" class="btn sm" data-nt="test" data-k="celebration">${esc(t('test.celebration'))}</button></div>` : '';
    return `<div class="sec-h"><h2>${esc(t('Notifications'))}</h2><span class="help">${esc(t('prefs.help'))}</span></div>
      <div class="surface nt-plist">${rows}</div>${admin}`;
  }
  function paintPrefs() {
    if (!on() || !/^#settings/.test(location.hash)) return;
    const main = document.getElementById('main');
    if (!main) return;
    let sec = document.getElementById('ntPrefs');
    if (!sec) {
      sec = document.createElement('section');
      sec.id = 'ntPrefs';
      sec.className = 'sec';
      sec.setAttribute('data-noi18n', '');
      const theme = main.querySelector('[data-act="theme"]');
      const anchor = theme && theme.closest('section');
      anchor ? anchor.before(sec) : main.append(sec);
    }
    sec.innerHTML = prefsHtml();
    if (!NT.prefs) {
      apiJSON('api/notifications/prefs').then((r) => { NT.prefs = r.prefs || {}; const s = document.getElementById('ntPrefs'); if (s) s.innerHTML = prefsHtml(); }).catch(() => {});
    }
  }
  async function setPref(input) {
    const c = input.dataset.ntPref, val = input.checked;
    try {
      const r = await post('api/notifications/prefs', { category: c, enabled: val });
      NT.prefs = r.prefs;
      if (typeof haptic === 'function') haptic(6);
    } catch (e) {
      input.checked = !val;
      toast(t('error'));
    }
  }
  async function sendTest(kind, btn) {
    btn.disabled = true;
    try {
      const r = await post('api/notifications/test', { kind });
      toast(r.ok ? t(kind === 'celebration' ? 'test.cel_sent' : 'test.sent') : t('test.skipped'));
      load(true);
    } catch (e) {
      toast(e.message || t('error'));
    } finally {
      btn.disabled = false;
    }
  }

  /* ───────────── wiring ───────────── */
  document.addEventListener('click', (e) => {
    const el = e.target.closest && e.target.closest('[data-nt]');
    if (!el) return;
    const a = el.dataset.nt;
    if (a === 'bell') { e.preventDefault(); openSheet(); }
    else if (a === 'close') closeSheet();
    else if (a === 'all') markAll();
    else if (a === 'open') openItem(+el.dataset.id);
    else if (a === 'mclose') closeModal(false);
    else if (a === 'mgo') closeModal(true);
    else if (a === 'test') sendTest(el.dataset.k, el);
  });
  document.addEventListener('change', (e) => {
    const i = e.target.closest && e.target.closest('input[data-nt-pref]');
    if (i) setPref(i);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (document.querySelector('.nt-modal')) { e.stopPropagation(); closeModal(false); }
    else if (NT.open) { e.stopPropagation(); closeSheet(); }
  }, true);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') load(); });
  setInterval(() => { if (document.visibilityState === 'visible') load(); }, 60000);

  // Run after every app render: show the bell once signed in, keep Settings → Notifications in place.
  if (typeof render === 'function') {
    const appRender = render;
    render = function () {
      const out = appRender.apply(this, arguments);
      try { afterRender(); } catch (e) { console.error('[Sweep notify]', e); }
      return out;
    };
  }
  function afterRender() {
    paintBadge();
    if (on() && NT.items == null && !NT.busy) load(true);
    paintPrefs();
  }
  afterRender();

  // Public hooks for later features (feedback loop, wow moments, streaks…)
  window.SweepNotify = { refresh: () => load(true), open: openSheet, strings, t };
})();
