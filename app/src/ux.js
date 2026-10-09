/*
 * Sweep — experience layer (mobile ergonomics). Loaded after app.js.
 * Safe by design: it never cancels a click and never touches data or app logic.
 *  1. Top-bar hairline once content scrolls under it
 *  2. Tab bar hidden while typing (the keyboard would push it over the field)
 *  3. Direction hint for the page entrance animation (CSS only)
 *  4. Tap the active tab again → smooth scroll to top
 */
(function () {
  'use strict';
  const body = document.body;
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const phone = () => innerWidth <= 860;

  /* 1 */
  let ticking = false;
  const onScroll = () => { ticking = false; body.classList.toggle('ux-scrolled', scrollY > 4); };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });

  /* 2 */
  const isField = (el) => el && el.matches && el.matches('input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=file]):not([type=button]):not([type=submit]),textarea,select,[contenteditable="true"]');
  let typingT = 0;
  document.addEventListener('focusin', (e) => {
    if (!phone() || !isField(e.target)) return;
    clearTimeout(typingT);
    body.classList.add('ux-typing');
  });
  document.addEventListener('focusout', () => {
    clearTimeout(typingT);
    typingT = setTimeout(() => { if (!isField(document.activeElement)) body.classList.remove('ux-typing'); }, 150);
  });
  addEventListener('hashchange', () => { if (!isField(document.activeElement)) body.classList.remove('ux-typing'); });

  /* 3 + 4 */
  const ORDER = ['dashboard', 'trades', 'trade', 'calendar', 'journal', 'news', 'analytics', 'accounts', 'account', 'payouts', 'referral', 'feedback', 'plan', 'import', 'admin', 'settings'];
  const viewOf = (h) => (decodeURIComponent(String(h || '').replace(/^#/, '')) || 'dashboard').split('/')[0];
  const rank = (v) => { const i = ORDER.indexOf(v); return i < 0 ? ORDER.length : i; };
  let dirT = 0;
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('a[href^="#"][data-v]');
    if (!a || !a.closest('#bottomnav, .side, #moreSheet')) return;
    const to = a.getAttribute('href'), from = location.hash || '#dashboard';
    if (to === from) {
      if (a.closest('#bottomnav') && scrollY > 0 && !e.defaultPrevented) {
        e.preventDefault();
        scrollTo({ top: 0, behavior: reduced() ? 'auto' : 'smooth' });
      }
      return;
    }
    document.documentElement.dataset.uxDir = rank(viewOf(to)) >= rank(viewOf(from)) ? 'fwd' : 'back';
    clearTimeout(dirT);
    dirT = setTimeout(() => { delete document.documentElement.dataset.uxDir; }, 1600);
  });

  onScroll();
})();

/* ───────────── 5. Payouts & expenses: fewer fields, fewer taps ─────────────
 * Payouts: only "Paid" or "Requested", one date, note hidden behind a link.
 * Expenses: evaluation, activation, reset or other; no note field.
 * Existing data is never changed: older statuses (approved, rejected…) and older categories still display. */
(function () {
  'use strict';
  if (typeof S === 'undefined' || typeof payoutForm !== 'function') return;

  const T = {
    fr: { 'Mark as paid': 'Marquer payé', 'Add a note': 'Ajouter une note', 'Note': 'Note', 'Payouts paid': 'Payouts payés',
      'Pending payouts': 'Payouts en attente', 'No payouts yet.': 'Aucun payout pour l’instant.', 'No expenses yet.': 'Aucune dépense pour l’instant.',
      'Save payout': 'Enregistrer le payout', 'Save expense': 'Enregistrer la dépense', 'Payout added': 'Payout ajouté', 'Payout saved': 'Payout enregistré',
      'Marked as paid': 'Marqué payé', 'Expense added': 'Dépense ajoutée', 'Expense saved': 'Dépense enregistrée',
      'Finish editing the payout above to add a new one.': 'Termine la modification du payout ci-dessus pour en ajouter un nouveau.',
      'Finish editing the expense above to add a new one.': 'Termine la modification de la dépense ci-dessus pour en ajouter une nouvelle.',
      'Evaluation': 'Évaluation', 'Activation': 'Activation', 'Reset': 'Reset' },
    es: { 'Mark as paid': 'Marcar pagado', 'Add a note': 'Añadir una nota', 'Note': 'Nota', 'Payouts paid': 'Payouts recibidos',
      'Pending payouts': 'Payouts pendientes', 'No payouts yet.': 'Aún no hay payouts.', 'No expenses yet.': 'Aún no hay gastos.',
      'Save payout': 'Guardar payout', 'Save expense': 'Guardar gasto', 'Payout added': 'Payout añadido', 'Payout saved': 'Payout guardado',
      'Marked as paid': 'Marcado como pagado', 'Expense added': 'Gasto añadido', 'Expense saved': 'Gasto guardado',
      'Finish editing the payout above to add a new one.': 'Termina de editar el payout de arriba para añadir uno nuevo.',
      'Finish editing the expense above to add a new one.': 'Termina de editar el gasto de arriba para añadir uno nuevo.',
      'Evaluation': 'Evaluación', 'Activation': 'Activación', 'Reset': 'Reset' }
  };
  if (window.I18N_FR) Object.assign(window.I18N_FR, T.fr);
  if (window.I18N_ES) Object.assign(window.I18N_ES, T.es);
  const t = (k) => (typeof tr === 'function' ? tr(k) : k);

  const ECATS = [['evaluation', 'Evaluation'], ['activation', 'Activation'], ['reset', 'Reset'], ['other', 'Other']];
  const isPaid = (p) => p.status === 'paid';
  const pDate = (p) => (isPaid(p) ? p.payment_date || p.approval_date || p.request_date : p.request_date) || '';
  const lastAcct = () => { try { return localStorage.getItem('tj.payacct') || ''; } catch (e) { return ''; } };
  const pill = (st) => {
    const lab = (PST.find((x) => x[0] === st) || [st, st])[1];
    return `<span class="pz-pill ${esc(st)}">${esc(lab)}</span>`;
  };

  /* Form */
  payoutForm = function (e = {}) {
    const active = S.accounts.filter((a) => a.status !== 'archived' || a.id === e.account_id);
    const st = e.id ? (isPaid(e) ? 'paid' : 'requested') : 'paid';
    const def = e.account_id || (F.account !== 'all' ? F.account : '') || (active.some((a) => a.id === lastAcct()) ? lastAcct() : '') || (active[0] || {}).id;
    return `<form class="pz-form" data-form="payout" data-id="${e.id || ''}" data-orig="${esc(e.status || '')}" autocomplete="off">
      <div class="seg pz-st" role="radiogroup">${[['paid', 'Paid'], ['requested', 'Requested']].map(([v, l]) =>
        `<label class="${st === v ? 'on' : ''}"><input type="radio" name="status" value="${v}" ${st === v ? 'checked' : ''}>${l}</label>`).join('')}</div>
      <div class="pz-fields">
        <label class="f pz-amt"><span>Amount</span><input name="amount" inputmode="decimal" required value="${e.amount_c != null ? e.amount_c / 100 : ''}" placeholder="$"></label>
        <label class="f"><span>Account</span><select name="account" required>${opts(active.map((a) => [a.id, acctLabel(a.id)]), def)}</select></label>
        <label class="f"><span>Date</span><input type="date" name="date" value="${pDate(e) || todayStr()}"></label>
      </div>
      <details class="pz-note" ${e.notes ? 'open' : ''}><summary>Add a note</summary><input name="notes" value="${esc(e.notes || '')}" placeholder="Note"></details>
      <div class="row pz-acts"><button class="btn primary" type="submit">${e.id ? 'Save payout' : 'Add payout'}</button>${e.id ? `<button class="btn" type="button" data-act="cancel-edit">Cancel</button><button class="btn danger" type="button" data-act="del-payout" data-id="${e.id}">Delete</button>` : ''}</div>
    </form>`;
  };

  submitPayout = function (form) {
    if (!billGate('payouts', 'payouts', { payoutTotal: billPayoutTotal() })) return;
    const d = new FormData(form), id = form.dataset.id || uid(), a = acct(d.get('account')), amt = parseMoney(d.get('amount'));
    if (!a) { toast(t('Choose an account.')); return; }
    if (amt == null || amt <= 0) { toast(t('Enter a payout amount.')); return; }
    const prev = getDoc('payouts', id) || {};
    const date = d.get('date') || todayStr();
    let status = d.get('status') === 'requested' ? 'requested' : 'paid';
    // an older status (approved, planned…) is kept unless the trader switched it to Paid
    if (status === 'requested' && form.dataset.orig && !['paid', 'requested'].includes(form.dataset.orig)) status = form.dataset.orig;
    const doc = { ...prev, id, account_id: a.id, firm_id: a.firm_id, amount_c: amt, status, notes: String(d.get('notes') || '').trim() };
    if (status === 'paid') {
      doc.payment_date = date;
      doc.request_date = prev.request_date || date;
      doc.approval_date = prev.approval_date || date;
    } else {
      doc.request_date = date;
      if (prev.status === 'paid') doc.payment_date = '';
    }
    put('payouts', doc);
    try { localStorage.setItem('tj.payacct', a.id); } catch (e) { /* private mode */ }
    toast(t(form.dataset.id ? 'Payout saved' : 'Payout added'));
    U.editP = null;
    render();
    if (status === 'paid' && prev.status !== 'paid') setTimeout(() => openShare('payout', id), 400);
  };

  /* List (also used on each account page) */
  payoutTable = function (rows) {
    const list = rows.slice().sort((x, y) => pDate(y).localeCompare(pDate(x)));
    return `<ul class="pz-list">${list.map((p) => U.editP === p.id ? `<li class="pz-edit">${payoutForm(p)}</li>` : `
      <li class="pz-row pz-open ${isPaid(p) ? 'is-paid' : ''}" data-act="edit-payout" data-id="${p.id}" role="button" tabindex="0" aria-label="${esc(acctLabel(p.account_id) + ' · ' + moneyU(p.amount_c))}">
        <div class="pz-main"><b>${esc(acctLabel(p.account_id))}</b><small>${fdate(pDate(p))}${p.notes ? ' · ' + esc(p.notes) : ''}</small></div>
        <div class="pz-right"><span class="pz-amt-v ${isPaid(p) ? 'pos' : ''}">${moneyU(p.amount_c)}</span>${pill(p.status)}</div>
        <div class="pz-acts2">${isPaid(p) ? shareBtn('payout', p.id, 'Share', 'link sh-link') : `<button class="link pz-paid" data-pz-paid="${p.id}">Mark as paid</button>`}</div>
      </li>`).join('')}</ul>`;
  };

  document.addEventListener('click', (ev) => {
    const b = ev.target.closest && ev.target.closest('[data-pz-paid]');
    if (!b) return;
    ev.stopImmediatePropagation(); ev.preventDefault();
    const id = b.dataset.pzPaid, p = getDoc('payouts', id);
    if (!p) return;
    const today = todayStr();
    put('payouts', { ...p, status: 'paid', payment_date: today, approval_date: p.approval_date || today, request_date: p.request_date || today });
    if (typeof haptic === 'function') haptic(10);
    toast(t('Marked as paid'));
    render();
    setTimeout(() => openShare('payout', id), 400);
  }, true);   // capture: before the row's own « open » action
  document.addEventListener('change', (ev) => {
    const r = ev.target.closest && ev.target.closest('.pz-st input[type=radio]');
    if (!r) return;
    r.closest('.pz-st').querySelectorAll('label').forEach((l) => l.classList.toggle('on', l.contains(r)));
  });

  /* Expenses */
  expenseForm = function (e = {}) {
    const cat = e.category || 'evaluation';
    const cats = ECATS.some((c) => c[0] === cat) ? ECATS : [...ECATS, [cat, (ECAT.find((c) => c[0] === cat) || [cat, cat])[1]]];
    return `<form class="pz-form" data-form="expense" data-id="${e.id || ''}" autocomplete="off">
      <div class="seg pz-st pz-cats" role="radiogroup">${cats.map(([v, l]) =>
        `<label class="${cat === v ? 'on' : ''}"><input type="radio" name="category" value="${esc(v)}" ${cat === v ? 'checked' : ''}>${esc(l)}</label>`).join('')}</div>
      <div class="pz-fields four">
        <label class="f pz-amt"><span>Amount</span><input name="amount" inputmode="decimal" required value="${e.amount_c != null ? e.amount_c / 100 : ''}" placeholder="$"></label>
        <label class="f"><span>Prop firm</span><select name="firm">${opts([['', '\u2014'], ...S.firms.map((f) => [f.id, f.name])], e.firm_id || '')}</select></label>
        <label class="f"><span>Account (optional)</span><select name="account">${opts([['', '\u2014'], ...S.accounts.map((a) => [a.id, acctLabel(a.id)])], e.account_id || '')}</select></label>
        <label class="f"><span>Date</span><input type="date" name="date" value="${e.date || todayStr()}" required></label>
      </div>
      <div class="row pz-acts"><button class="btn primary" type="submit">${e.id ? 'Save expense' : 'Add expense'}</button>${e.id ? `<button class="btn" type="button" data-act="cancel-edit">Cancel</button><button class="btn danger" type="button" data-act="del-expense" data-id="${e.id}">Delete</button>` : ''}</div>
    </form>`;
  };
  document.addEventListener('change', (ev) => {
    const r = ev.target.closest && ev.target.closest('.pz-cats input[type=radio]');
    if (r) r.closest('.pz-cats').querySelectorAll('label').forEach((l) => l.classList.toggle('on', l.contains(r)));
  });

  submitExpense = function (form) {
    if (!billGate('payouts', 'payouts', { payoutTotal: billPayoutTotal() })) return;
    const d = new FormData(form), id = form.dataset.id || uid(), amt = parseMoney(d.get('amount'));
    if (amt == null || amt <= 0) { toast(t('Enter an expense amount.')); return; }
    const acc = d.get('account') || '', fid = d.get('firm') || (acc ? (acct(acc) || {}).firm_id : '') || '', prev = getDoc('expenses', id) || {};
    put('expenses', { ...prev, id, date: d.get('date') || todayStr(), firm_id: fid, account_id: acc, category: d.get('category') || 'other', amount_c: amt });
    toast(t(form.dataset.id ? 'Expense saved' : 'Expense added'));
    U.editE = null;
    render();
  };

  /* Page */
  vPayouts = function () {
    if (!S.accounts.length) return onboarding();
    const keep = (h) => !(F.account !== 'all' && h.account_id !== F.account || F.firm !== 'all' && (h.firm_id || (acct(h.account_id) || {}).firm_id) !== F.firm);
    const P = S.payouts.filter(keep), E = S.expenses.filter(keep);
    const sum = (arr, f = () => true) => arr.filter(f).reduce((x, y) => x + (y.amount_c || 0), 0);
    const pnl = S.trades.filter(acctOK).reduce((x, y) => x + tNet(y), 0);
    const paid = sum(P, isPaid), pending = sum(P, (p) => ['requested', 'approved', 'planned'].includes(p.status)), exp = sum(E);
    const nPaid = P.filter(isPaid).length;
    const catLabel = (c) => (ECATS.find((x) => x[0] === c) || ECAT.find((x) => x[0] === c) || [0, 'Other'])[1];
    const expRows = E.slice().sort((x, y) => (y.date || '').localeCompare(x.date || '')).map((h) => U.editE === h.id ? `<li class="pz-edit">${expenseForm(h)}</li>` : `
      <li class="pz-row pz-open" data-act="edit-expense" data-id="${h.id}" role="button" tabindex="0" aria-label="${esc(catLabel(h.category) + ' · ' + moneyU(h.amount_c || 0))}"><div class="pz-main"><b>${esc(catLabel(h.category))}${(firm(h.firm_id) || {}).name ? ' · ' + esc(firm(h.firm_id).name) : ''}</b><small>${fdate(h.date)}${h.account_id ? ' · ' + esc(acctName(h.account_id)) : ''}${h.notes ? ' · ' + esc(h.notes) : ''}</small></div>
      <div class="pz-right"><span class="pz-amt-v neg">${money(-(h.amount_c || 0))}</span></div>
</li>`).join('');
    return `${filterBar({ period: false, session: false, dir: false })}<div data-lock="payouts" data-feature="payouts" class="bill-lock">
      <div class="kpis k4"><div><div class="lbl">${tip('Trading P&amp;L', 'Net P&L from all logged trades. Not money in your bank account.')}</div><div class="val ${cls(pnl)}">${money(pnl, { dec: 0 })}</div></div><div><div class="lbl">Payouts received</div><div class="val">${moneyU(paid)}</div></div><div><div class="lbl">Trading expenses</div><div class="val ${exp ? 'neg' : ''}">${exp ? money(-exp, { dec: 0 }) : '$0'}</div></div><div><div class="lbl">${tip('Net realized income', 'Payouts received \u2212 trading expenses. The money trading actually made you.')}</div><div class="val ${cls(paid - exp)}">${money(paid - exp, { dec: 0 })}</div></div></div>
      ${paid || S.expenses.length ? `<div class="sh-row">${shareBtn('net', 'all', 'Share net after fees')}</div>` : ''}
      ${pending ? `<div class="metrics surface pz-metrics"><div><span>Pending payouts</span><span class="dc">${moneyU(pending)}</span></div><div><span>Payouts paid</span><span>${nPaid}</span></div></div>` : ''}
      <section class="sec"><div class="sec-h"><h2>Payouts</h2></div>
        <div class="surface pad pz-add">${U.editP ? '<span class="muted">Finish editing the payout above to add a new one.</span>' : payoutForm()}</div>
        ${P.length ? `<div class="surface pz-wrap">${payoutTable(P)}</div>` : '<div class="pz-empty muted">No payouts yet.</div>'}</section>
      <section class="sec"><div class="sec-h"><h2>Expenses</h2>${aiBtn('ai-scan', 'Scan a receipt')}</div>
        <div class="surface pad pz-add">${U.editE ? '<span class="muted">Finish editing the expense above to add a new one.</span>' : expenseForm()}</div>
        ${E.length ? `<div class="surface pz-wrap"><ul class="pz-list">${expRows}</ul></div>` : '<div class="pz-empty muted">No expenses yet.</div>'}</section></div>`;
  };
})();

/* i18n: "8 trades · this week" under Net P&L */
(function () {
  if (typeof I18N_PAT === 'undefined' || typeof tr !== 'function') return;
  I18N_PAT.unshift([/^(\d+) trades? · (today|this week|this month|all time|the selected range)$/, (m) => `${tr(m[1] + (m[1] === '1' ? ' trade' : ' trades'))} · ${tr(m[2])}`]);
  if (window.I18N_FR) window.I18N_FR['the selected range'] = window.I18N_FR['the selected range'] || 'la période choisie';
  if (window.I18N_ES) window.I18N_ES['the selected range'] = window.I18N_ES['the selected range'] || 'el período elegido';
})();

/* ───────────── 6. Discipline checklist: 5 essential questions by default ─────────────
 * Once per account: the default checklist keeps plan, risk, stop, size and daily loss limit active.
 * The other default questions are only deactivated (Settings can turn them back on); custom questions are untouched. */
(function () {
  'use strict';
  const KEEP = ['plan', 'risk', 'stop', 'size', 'dll'];
  const DEF = ['plan', 'confirm', 'entry', 'size', 'risk', 'stop', 'widen', 'addloser', 'revenge', 'chase', 'dll', 'emotion', 'exit'];
  function migrate() {
    try {
      if (S.mode !== 'server' || !S.settings || S.settings.qs5 || !Array.isArray(S.settings.questions)) return false;
      const s = JSON.parse(JSON.stringify(S.settings));
      s.questions.forEach((q) => { if (DEF.includes(q.id)) q.active = KEEP.includes(q.id); });
      s.qs5 = true;
      put('settings', s);
      return true;
    } catch (e) { return false; }
  }
  const iv = setInterval(() => { if (S.mode === 'server' && S.settings) { clearInterval(iv); migrate(); } }, 800);
  setTimeout(() => clearInterval(iv), 60000);
})();

/* ───────────── 7. Journal pre-market: today's news with your expectation for each ─────────────
 * Replaces the free "Economic events" box with the day's high/medium U.S. events from the economic calendar,
 * one short "what I expect" note per event (saved in the journal as pre.news). No events that day: no section. */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  const T = {
    en: { title: 'News of the day', ph: 'What I expect / how I will react', prev: 'Prev', fcst: 'Fcst' },
    fr: { title: 'Nouvelles du jour', ph: 'Mon attente / comment je vais réagir', prev: 'Préc.', fcst: 'Prév.' },
    es: { title: 'Noticias del día', ph: 'Lo que espero / cómo reaccionaré', prev: 'Ant.', fcst: 'Prev.' },
  };
  const tt = (k) => (T[LANG] || T.en)[k];
  const loading = {};
  function enhance() {
    if (typeof route !== 'function' || route().v !== 'journal') return;
    const ta = document.querySelector('#main textarea[data-bind$="|pre.events"]');
    if (!ta || ta.dataset.uxNews) return;
    const day = ta.dataset.bind.split('|')[1];
    const box = ta.closest('.prompt') || ta.parentElement;
    if (typeof ECON === 'undefined' || !ECON.days) return;
    const evs = ECON.days[day];
    if (!evs) { if (!loading[day] && typeof loadEcon === 'function') { loading[day] = true; loadEcon(day, day).then(() => { loading[day] = false; enhance(); }).catch(() => {}); } return; }
    ta.dataset.uxNews = '1';
    const legacy = ta.value.trim();
    if (!evs.length) { if (!legacy) box.style.display = 'none'; return; }
    const j = (typeof getDoc === 'function' ? getDoc('journals', day) : null) || {};
    const notes = ((j.pre || {}).news) || {};
    const lab = box.querySelector('label'); if (lab) { lab.textContent = tt('title'); lab.setAttribute('data-noi18n', ''); }
    if (!legacy) ta.style.display = 'none';
    const wrap = document.createElement('div');
    wrap.className = 'ux-news'; wrap.setAttribute('data-noi18n', '');
    wrap.innerHTML = evs.map((e) => `<div class="ux-ev"><div class="ux-ev-h"><span class="ux-ev-t">${etStr(e.ts).slice(11, 16)}</span><span class="imp ${e.impact}"><i></i></span><b>${esc(e.event)}</b>
      <small>${e.forecast ? tt('fcst') + ' ' + esc(e.forecast) : ''}${e.forecast && e.previous ? ' · ' : ''}${e.previous ? tt('prev') + ' ' + esc(e.previous) : ''}</small></div>
      <input data-ux-news="${esc(e.id)}" value="${esc(notes[e.id] || '')}" placeholder="${esc(tt('ph'))}" maxlength="240"></div>`).join('');
    box.append(wrap);
  }
  document.addEventListener('input', (e) => {
    const i = e.target.closest && e.target.closest('[data-ux-news]');
    if (!i) return;
    const ta = document.querySelector('#main textarea[data-bind$="|pre.events"]'); if (!ta) return;
    const day = ta.dataset.bind.split('|')[1], id = i.dataset.uxNews, v = i.value;
    editDoc('journals', day, (d) => { d.pre = d.pre || {}; d.pre.news = Object.assign({}, d.pre.news || {}, { [id]: v }); }, { delay: 600, init: () => ({ id: day }) });
  });
  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { enhance(); } catch (e) { /* never blocks */ } return out; };
})();

/* ───────────── 8. Checklist shows only the active questions (5 by default) ─────────────
 * Older trades keep their answers in the data; on screen, an inactive question only appears
 * when an automatic check flagged it (stop, size, daily limit, added to a loser). */
(function () {
  'use strict';
  if (typeof checklist !== 'function') return;
  const AUTO = ['addloser', 'dll', 'stop', 'size'];
  const orig = checklist;
  checklist = function (col, trade) {
    try {
      const qs = (S.settings && S.settings.questions) || [];
      const act = new Set(qs.filter((q) => q.active).map((q) => q.id));
      if (!act.size) return orig.apply(this, arguments);
      const d = trade.discipline || {}, keep = {};
      for (const k in d) if (act.has(k) || (d[k] === 'n' && AUTO.includes(k))) keep[k] = d[k];
      return orig.call(this, col, Object.assign({}, trade, { discipline: keep }));
    } catch (e) { return orig.apply(this, arguments); }
  };
})();

/* ───────────── 9. Missing translations spotted in the design pass ───────────── */
(function () {
  const fr = { 'No trades today. ': "Aucun trade aujourd'hui. ", 'No trades today.': "Aucun trade aujourd'hui.", 'No trades on this day.': 'Aucun trade ce jour-là.' };
  const es = { 'No trades today. ': 'Ninguna operación hoy. ', 'No trades today.': 'Ninguna operación hoy.', 'No trades on this day.': 'Ninguna operación este día.' };
  if (window.I18N_FR) for (const k in fr) window.I18N_FR[k] = window.I18N_FR[k] || fr[k];
  if (window.I18N_ES) for (const k in es) window.I18N_ES[k] = window.I18N_ES[k] || es[k];
})();

/* ───────────── 10. Feedback page: « what happens next » card + loop notifications text ───────────── */
(function () {
  'use strict';
  const T = {
    en: { h: 'What happens next', s: ['We read every message within 48 h.', 'You see its status here: planned, in progress, shipped.', 'When it ships, you get « You asked, we built it ».'],
      n: { 'fb_planned.title': 'Your idea is planned', 'fb_planned.body': '{reply}', 'fb_in_progress.title': "We're building what you asked for", 'fb_in_progress.body': '{reply}',
        'fb_shipped.title': 'You asked, we built it.', 'fb_shipped.body': '{reply}', 'fb_declined.title': 'An answer to your feedback', 'fb_declined.body': '{reply}' } },
    fr: { h: 'Ce qui se passe ensuite', s: ['On lit chaque message sous 48 h.', 'Tu suis son statut ici : planifié, en cours, livré.', 'Quand c’est livré, tu reçois « Tu l’as demandé, on l’a construit ».'],
      n: { 'fb_planned.title': 'Ton idée est planifiée', 'fb_planned.body': '{reply}', 'fb_in_progress.title': 'On construit ce que tu as demandé', 'fb_in_progress.body': '{reply}',
        'fb_shipped.title': 'Tu l’as demandé, on l’a construit.', 'fb_shipped.body': '{reply}', 'fb_declined.title': 'Une réponse à ton retour', 'fb_declined.body': '{reply}' } },
    es: { h: 'Qué pasa después', s: ['Leemos cada mensaje en menos de 48 h.', 'Ves su estado aquí: planificado, en curso, lanzado.', 'Cuando se lanza, recibes « Lo pediste, lo construimos ».'],
      n: { 'fb_planned.title': 'Tu idea está planificada', 'fb_planned.body': '{reply}', 'fb_in_progress.title': 'Estamos construyendo lo que pediste', 'fb_in_progress.body': '{reply}',
        'fb_shipped.title': 'Lo pediste, lo construimos.', 'fb_shipped.body': '{reply}', 'fb_declined.title': 'Una respuesta a tu comentario', 'fb_declined.body': '{reply}' } },
  };
  const t = () => T[LANG] || T.en;
  const reg = () => { if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings({ en: T.en.n, fr: T.fr.n, es: T.es.n }); } catch (e) { /* older module */ } return true; } return false; };
  if (!reg()) setTimeout(reg, 1500);
  if (typeof render !== 'function') return;
  const appRender = render;
  render = function () {
    const out = appRender.apply(this, arguments);
    try {
      if (route().v === 'feedback') {
        const fb = document.querySelector('#main .fb');
        if (fb && !fb.querySelector('.fb-next')) {
          const c = document.createElement('section'); c.className = 'surface fb-next'; c.setAttribute('data-noi18n', '');
          c.innerHTML = `<h3>${t().h}</h3><ol>${t().s.map((x, i) => `<li><span>${i + 1}</span>${x}</li>`).join('')}</ol>`;
          const form = fb.querySelector('.fb-form'); if (form) form.after(c); else fb.append(c);
        }
      }
    } catch (e) { /* never blocks */ }
    return out;
  };
})();

/* ───────────── 11. Complete export button + prop firm presets ───────────── */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  const T = {
    en: { zip: 'Export everything (ZIP)', zip_d: 'Backup, spreadsheets and screenshots in one file.', preset: 'Prop firm preset (optional)', none: 'No preset', apply: 'Apply a preset', applied: 'Rules filled from the preset',
      warn: 'Evaluation rules prefilled as a starting point. Firms change their rules: check them on the firm’s site.' },
    fr: { zip: 'Tout exporter (ZIP)', zip_d: 'Sauvegarde, tableurs et captures en un seul fichier.', preset: 'Préréglage de prop firm (facultatif)', none: 'Aucun préréglage', apply: 'Appliquer un préréglage', applied: 'Règles remplies depuis le préréglage',
      warn: 'Règles d’évaluation préremplies pour démarrer. Les firmes changent leurs règles : vérifie-les sur le site de la firme.' },
    es: { zip: 'Exportar todo (ZIP)', zip_d: 'Copia, hojas de cálculo y capturas en un solo archivo.', preset: 'Preajuste de prop firm (opcional)', none: 'Sin preajuste', apply: 'Aplicar un preajuste', applied: 'Reglas completadas desde el preajuste',
      warn: 'Reglas de evaluación precargadas como punto de partida. Las firmas cambian sus reglas: verifícalas en su sitio.' },
  };
  const t = (k) => (T[LANG] || T.en)[k];
  /* ───── prop firm presets: firm → account type → size → phase, from api/presets (checked every week) ───── */
  const PT = {
    en: { types: '{n} account types', q0: 'Evaluation, funded or live account?', liveStart: 'Starting balance', floor: 'Balance to stay above', liveNote: 'Your live starting balance comes from your funded accounts: change it below if yours is different.', live: 'Live', liveT: 'Live account', real: 'Real money', liveSub: 'Your firm’s live account (Topstep Live, Apex, Lucid Live…) or your own brokerage account.', evalSub: 'You are trying to pass: profit target, drawdown, rules.', fundedSub: 'Already passed: payouts, safety net, payout rules.', foldSub: 'Pick the account type and size: the rules below are filled in for you{f}.', q1: 'Which prop firm?', q2: 'Which account type?', q3: 'Which size?', other: 'Other firm or personal account', otherSub: 'Enter it yourself', back: '← Choose from the list', ready: 'Your account', nameL: 'Account name', withDll: 'I took the daily loss limit option', noDll: 'none (option not taken)', firm: 'Prop firm', type: 'Account type', size: 'Size', phase: 'Phase', eval: 'Evaluation', funded: 'Funded', pick: 'Choose…', applyBtn: 'Apply these rules',
      seed: 'Starting rules of {d}, compiled from public sources. The weekly check confirms them on the firm’s own pages.', checked: 'Rules checked on {d} from the firm’s own pages.', tgt: 'Target', mll: 'Max loss', dll: 'Daily limit', cons: 'Consistency', days: 'Min. days', minis: 'Max', eod: 'end of day', trade: 'real time', static: 'static', none: 'none', direct: 'funded directly' },
    fr: { types: '{n} types de compte', q0: 'Évaluation, financé ou compte live ?', liveStart: 'Solde de départ', floor: 'Solde à garder au-dessus de', liveNote: 'Ton solde live de départ vient de tes comptes financés : modifie-le plus bas s’il est différent.', live: 'Live', liveT: 'Compte live', real: 'Argent réel', liveSub: 'Le compte live de ta firme (Topstep Live, Apex, Lucid Live…) ou ton compte de courtage perso.', evalSub: 'Tu essaies de passer : objectif de profit, drawdown, règles.', fundedSub: 'Déjà passé : payouts, coussin, règles de payout.', foldSub: 'Choisis le type de compte et la taille : les règles ci-dessous se remplissent{f}.', q1: 'Quelle prop firm ?', q2: 'Quel type de compte ?', q3: 'Quelle taille ?', other: 'Autre firme ou compte perso', otherSub: 'Je le saisis moi-même', back: '← Choisir dans la liste', ready: 'Ton compte', nameL: 'Nom du compte', withDll: 'J’ai pris l’option de limite journalière', noDll: 'aucune (option non prise)', firm: 'Prop firm', type: 'Type de compte', size: 'Taille', phase: 'Phase', eval: 'Évaluation', funded: 'Financé', pick: 'Choisir…', applyBtn: 'Appliquer ces règles',
      seed: 'Règles de départ du {d}, compilées de sources publiques. La vérification hebdomadaire les confirme sur les pages de la firme.', checked: 'Règles vérifiées le {d} sur les pages de la firme.', tgt: 'Objectif', mll: 'Perte max', dll: 'Limite jour', cons: 'Consistance', days: 'Jours min.', minis: 'Max', eod: 'fin de journée', trade: 'temps réel', static: 'fixe', none: 'aucune', direct: 'financé directement' },
    es: { types: '{n} tipos de cuenta', q0: '¿Evaluación, financiada o cuenta live?', liveStart: 'Saldo inicial', floor: 'Saldo mínimo', liveNote: 'Tu saldo live inicial viene de tus cuentas financiadas: cámbialo abajo si es diferente.', live: 'Live', liveT: 'Cuenta live', real: 'Dinero real', liveSub: 'La cuenta live de tu firma (Topstep Live, Apex, Lucid Live…) o tu cuenta de bróker propia.', evalSub: 'Intentas pasar: objetivo de beneficio, drawdown, reglas.', fundedSub: 'Ya aprobada: payouts, colchón, reglas de payout.', foldSub: 'Elige el tipo de cuenta y el tamaño: las reglas de abajo se rellenan{f}.', q1: '¿Qué prop firm?', q2: '¿Qué tipo de cuenta?', q3: '¿Qué tamaño?', other: 'Otra firma o cuenta personal', otherSub: 'La escribo yo', back: '← Elegir de la lista', ready: 'Tu cuenta', nameL: 'Nombre de la cuenta', withDll: 'Tomé la opción de límite diario', noDll: 'ninguno (opción no tomada)', firm: 'Prop firm', type: 'Tipo de cuenta', size: 'Tamaño', phase: 'Fase', eval: 'Evaluación', funded: 'Financiada', pick: 'Elegir…', applyBtn: 'Aplicar estas reglas',
      seed: 'Reglas iniciales del {d}, recopiladas de fuentes públicas. La verificación semanal las confirma en las páginas de la firma.', checked: 'Reglas verificadas el {d} en las páginas de la firma.', tgt: 'Objetivo', mll: 'Pérdida máx.', dll: 'Límite diario', cons: 'Consistencia', days: 'Días mín.', minis: 'Máx.', eod: 'al cierre', trade: 'tiempo real', static: 'fija', none: 'ninguna', direct: 'financiada directamente' } };
  const pt = (k) => (PT[LANG] || PT.en)[k];
  let CAT = null, catBusy = false;
  function loadCat() {
    if (CAT || catBusy || typeof apiJSON !== 'function') return; catBusy = true;
    apiJSON('api/presets').then((d) => { CAT = d && Array.isArray(d.firms) ? d : { firms: [] }; catBusy = false; document.querySelectorAll('.ux-st').forEach((w) => stDraw(w)); try { enhance(); } catch (x) { /* never blocks */ } }).catch(() => { catBusy = false; });
  }
  const usd = (v) => (typeof moneyU === 'function' ? moneyU(Math.round(Number(v) * 100)) : '$' + Number(v).toLocaleString('en-US'));
  const find = (fid, pid, size) => { const f = CAT && CAT.firms.find((x) => x.id === fid); const p = f && f.programs.find((x) => x.id === pid); const s = p && p.sizes.find((x) => String(x.size) === String(size)); return { f, p, s }; };
  /** options chosen at purchase are « + »-joined in the 5th part of the value: dll (daily loss limit taken), or a variant (Topstep « consistency ») */
  const optsOf = (o) => String(o || '').split('+').filter(Boolean);
  const merge = (base, over) => { const r = Object.assign({}, base); Object.keys(over || {}).forEach((k) => { if (over[k] === null) delete r[k]; else r[k] = over[k]; }); return r; };
  const phaseRules = (s, phase, opt) => {
    if (phase === 'live') return s.live || (s.funded && Object.assign({}, s.funded, { payout: s.funded.payout_live || (s.funded.payout ? Object.assign({}, s.funded.payout, { max: null, max_dll: null, ladder: null, max_payouts: null }) : null) }));
    let r = s[phase]; if (!r) return r;
    optsOf(opt).forEach((o) => { const v = s.variants && s.variants[o] && s.variants[o][phase]; if (v) r = merge(r, v); });
    return r;
  };
  /** the choices a program offers at purchase for this phase (Topstep: Standard / Consistency for the funded account) */
  const choicesFor = (p, phase) => ((p && p.options) || []).filter((o) => o.phase === phase || o.phase === 'all');
  const L3 = (o) => (o ? (o[LANG] || o.en || '') : '');
  /** funded accounts: the firm's payout conditions (winning days, minimum day, safety net, min / max per request) */
  function payoutRules(po, opt) {
    const c = (x) => (x == null ? null : Math.round(x * 100));
    if (!po) return { payout_split_pct: null, payout_win_days: null, payout_win_min_c: null, payout_trade_days: null, payout_min_c: null, payout_max_c: null, payout_max_pct: null, payout_min_bal_c: null, payout_cycle_pos: null, payout_cycle_min_c: null, payout_ladder_c: null, payout_max_n: null };
    return { payout_win_days: po.win_days || null, payout_win_min_c: po.win_days ? c(po.win_min || 0) : null, payout_trade_days: po.trade_days || null, payout_max_n: po.max_payouts || null, payout_split_pct: po.split_pct || null, payout_min_c: c(po.min), payout_max_c: c(optsOf(opt).includes('dll') && po.max_dll ? po.max_dll : po.max),
      payout_max_pct: po.max_pct || null, payout_min_bal_c: c(po.min_bal), payout_cycle_pos: po.cycle_pos ? true : null, payout_cycle_min_c: c(po.cycle_min), payout_ladder_c: Array.isArray(po.ladder) ? po.ladder.map(c) : null };
  }
  window.SweepPresets = { rulesOf: (v) => rulesOf(v), priceOf: (v) => { const [fid, pid, size] = String(v || '').split('|'); const { s } = find(fid, pid, size); return (s && s.price) || null; },
    /** the choices to make when an evaluation becomes funded (Topstep: Standard or Consistency) */
    fundedChoices: (v) => { const [fid, pid] = String(v || '').split('|'); const { p } = find(fid, pid, ''); return choicesFor(p, 'funded').map((o) => ({ id: o.id, label: L3(o.label), choices: o.choices.map((c) => ({ id: c.id, label: L3(c.label), sub: L3(c.sub), def: c.id === o.default })) })); },
    /** a preset value with one option set (other options kept) */
    withChoice: (v, group, id) => { const pv = String(v || '').split('|'); while (pv.length < 5) pv.push(''); const { p } = find(pv[0], pv[1], ''); const g = p && (p.options || []).find((o) => o.id === group); if (!g) return pv.join('|'); const keep = optsOf(pv[4]).filter((o) => !g.choices.some((c) => c.id === o)); if (id && id !== g.default) keep.push(id); pv[4] = keep.join('+'); return pv.join('|'); },
    version: () => (CAT && CAT.version) || null, ready: () => !!CAT, load: () => loadCat() };   // used to move a passed evaluation to its funded rules
  /** value « firm|program|size|phase » → account fields + rules (amounts in cents, as the app stores them) */
  const rulesOf = (v) => {
    const [fid, pid, size, phase, opt] = String(v || '').split('|'); const { f, p, s } = find(fid, pid, size); if (!s) return null;
    const r = phaseRules(s, phase, opt) || s.eval || s.funded; if (!r) return null;
    const price = s.price || null; const hasDll = optsOf(opt).includes('dll');   // the firm's fee for this account, when the catalogue knows it
    // a live account with its own rules (Topstep Live): it starts with a part of the size, and must stay above a fixed floor
    const liveStart = phase === 'live' && r.start_pct ? Math.round(s.size * r.start_pct / 100) : null;
    const liveDd = liveStart != null && r.floor != null ? liveStart - r.floor : null;
    const c = (x) => (x == null ? null : Math.round(x * 100));
    return { start: liveStart != null ? liveStart : s.size, name: phase === 'live' ? `${f.name} Live ${s.size / 1000}K` : `${p.name} ${s.size / 1000}K`, firm: f.name, aliases: [f.name, ...(f.aliases || [])], rules: { target_c: phase === 'eval' ? c(r.target) : null, dd_c: liveDd != null ? c(liveDd) : c(r.dd), dd_floor_c: phase === 'live' && r.floor != null ? c(r.floor) : null, dd_type: r.dd_type || 'eod', dd_lock: true, dd_lock_offset_c: r.dd_lock_offset ? c(r.dd_lock_offset) : null, dll_c: r.dll_optional && !hasDll ? null : c(r.dll), consistency_pct: r.consistency || null, min_days: phase === 'eval' ? (r.min_days || null) : null, ...payoutRules(phase === 'eval' ? null : r.payout, opt) } };
  };
  function summary(fid, pid, size, phase, opt) {
    const { s, p } = find(fid, pid, size); const r = s && (phaseRules(s, phase, opt) || s.eval || s.funded); if (!r) return ''; const hasDll = optsOf(opt).includes('dll');
    const bits = [];
    if (phase === 'live' && r.start_pct) { bits.push(`${pt('liveStart')} <b>${usd(Math.round(s.size * r.start_pct / 100))}</b> (${r.start_pct} %)`); if (r.floor != null) bits.push(`${pt('floor')} <b>${usd(r.floor)}</b>`); if (r.dll) bits.push(`${pt('dll')} <b>${usd(r.dll)}</b>`); return bits.join(' · ') + `<small class="ux-st-note">${pt('liveNote')}</small>`; }
    if (phase === 'eval' && r.target) bits.push(`${pt('tgt')} <b>${usd(r.target)}</b>`);
    bits.push(`${pt('mll')} <b>${usd(r.dd)}</b> (${pt(r.dd_type || 'eod')})`);
    bits.push(`${pt('dll')} <b>${r.dll && (!r.dll_optional || hasDll) ? usd(r.dll) : (r.dll_optional ? pt('noDll') : pt('none'))}</b>`);
    if (r.consistency) bits.push(`${pt('cons')} <b>${r.consistency} %</b>`);
    if (phase === 'eval' && r.min_days) bits.push(`${pt('days')} <b>${r.min_days}</b>`);
    if (r.max_minis) bits.push(`${pt('minis')} <b>${r.max_minis}</b> minis`);
    const po = phase !== 'eval' && r.payout;
    if (po) {
      const PW = ({ en: ['Payout', '{n} winning days of {m}+', '{n} traded days', 'max {v} per request', 'min {v}', 'up to {n} payouts'], fr: ['Payout', '{n} jours gagnants de {m} et +', '{n} jours tradés', 'max {v} par demande', 'min {v}', 'jusqu’à {n} payouts'], es: ['Payout', '{n} días ganadores de {m} o más', '{n} días operados', 'máx. {v} por solicitud', 'mín. {v}', 'hasta {n} payouts'] })[LANG] || ['Payout', '{n} winning days of {m}+', '{n} traded days', 'max {v} per request', 'min {v}', 'up to {n} payouts'];
      const pb = [];
      if (po.trade_days) pb.push(PW[2].replace('{n}', po.trade_days));
      if (po.win_days) pb.push(PW[1].replace('{n}', po.win_days).replace('{m}', usd(po.win_min || 0)));
      const mx = hasDll && po.max_dll ? po.max_dll : po.max; if (mx) pb.push(PW[3].replace('{v}', usd(mx)));
      if (po.min) pb.push(PW[4].replace('{v}', usd(po.min)));
      if (po.max_payouts) pb.push(PW[5].replace('{n}', po.max_payouts));
      if (pb.length) bits.push(`${PW[0]} : <b>${pb.join(', ')}</b>`);
    }
    const note = p && p.note ? (p.note[LANG] || p.note.en || '') : '';
    const when = CAT && CAT.checked_at ? new Date(CAT.checked_at).toLocaleDateString(LANG === 'en' ? 'en-US' : LANG + '-CA', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
    // three lines in plain words (goal · max loss · daily loss), everything else under « See all the rules »
    const W = ({ en: ['Goal', 'Max loss', 'Daily loss', 'none', 'See all the rules', 'Starting balance'], fr: ['Objectif', 'Perte max', 'Perte du jour', 'aucune', 'Voir toutes les règles', 'Solde de départ'], es: ['Objetivo', 'Pérdida máx.', 'Pérdida diaria', 'ninguna', 'Ver todas las reglas', 'Saldo inicial'] })[LANG] || ['Goal', 'Max loss', 'Daily loss', 'none', 'See all the rules', 'Starting balance'];
    const lines = [];
    if (phase === 'eval' && r.target) lines.push([W[0], usd(r.target)]); else if (phase === 'live' && r.start_pct) lines.push([W[5], usd(Math.round(s.size * r.start_pct / 100))]);
    lines.push([W[1], usd(r.dd)]);
    lines.push([W[2], r.dll && (!r.dll_optional || hasDll) ? usd(r.dll) : W[3]]);
    return `<ul class="ux-sum3">${lines.map(([k, v]) => `<li><span>${k}</span><b>${v}</b></li>`).join('')}</ul>
      <details class="ux-sum-more"><summary>${W[4]}</summary><p class="ux-pk-rules">${bits.join(' · ')}</p>${note ? `<p class="ux-pk-note">${esc(note)}</p>` : ''}${when ? `<p class="ux-pk-when">${pt(CAT.origin === 'seed' ? 'seed' : 'checked').replace('{d}', when)}</p>` : ''}</details>`;
  }
  /** guided steps: firm → account type → size, then phase / options and the summary. One question at a time, big tiles. */
  function stValue(w) {
    const d = w.dataset; if (!d.firm || !d.type || !d.size) return '';
    const { s } = find(d.firm, d.type, d.size); if (!s) return '';
    const { p } = find(d.firm, d.type, d.size);
    const phase = phaseRules(s, d.phase) ? d.phase : (s.eval ? 'eval' : 'funded');
    const r = s[phase], toks = [];
    if (r && r.dll_optional && d.dll === '1') toks.push('dll');
    // a choice made for the funded account (Topstep Standard / Consistency): kept from the evaluation on, used when it becomes funded
    ((p && p.options) || []).forEach((o) => { const v = d['opt_' + o.id]; if (v && v !== o.default && (o.phase === 'all' || o.phase === phase || phase === 'eval')) toks.push(v); });
    return [d.firm, d.type, d.size, phase, toks.join('+')].join('|');
  }
  function stDraw(w) {
    if (!CAT) { w.innerHTML = '<div class="skel" style="height:120px;border-radius:14px"></div>'; return; }
    const d = w.dataset, mode = d.mode;
    if (mode === 'apply' && d.open !== '1') {
      const fm = CAT.firms.find((x) => x.id === d.firm);
      w.classList.add('folded');
      w.innerHTML = `<button type="button" class="ux-st-fold" data-st-open><span><b>${t('apply')}</b><small>${pt('foldSub').replace('{f}', fm ? ' · ' + esc(fm.name) : '')}</small></span><i aria-hidden="true">›</i></button>`;
      return;
    }
    w.classList.remove('folded');
    const f = CAT.firms.find((x) => x.id === d.firm), p = f && f.programs.find((x) => x.id === d.type), s = p && p.sizes.find((x) => String(x.size) === d.size);
    const phCrumb = mode === 'create' && d.phaseSet === '1' ? `<button type="button" data-st-go="phase">${pt(d.phase)}</button><span>›</span>` : '';
    const crumbs = f ? `<div class="ux-st-crumbs">${phCrumb}<button type="button" data-st-go="firm">${esc(f.name)}</button>${p ? `<span>›</span><button type="button" data-st-go="type">${esc(p.name)}</button>` : ''}${s ? `<span>›</span><button type="button" data-st-go="size">${s.size / 1000}K</button>` : ''}</div>` : '';
    let body = '';
    if (mode === 'create' && d.phaseSet !== '1') {
      body = `<p class="ux-st-q">${pt('q0')}</p><div class="ux-st-tiles ux-st-ph"><button type="button" class="ux-st-tile" data-st-ph0="eval"><b>${pt('eval')}</b><small>${pt('evalSub')}</small></button><button type="button" class="ux-st-tile" data-st-ph0="funded"><b>${pt('funded')}</b><small>${pt('fundedSub')}</small></button><button type="button" class="ux-st-tile ux-st-live" data-st-ph0="live"><b>${pt('liveT')} <em>${pt('real')}</em></b><small>${pt('liveSub')}</small></button></div>`;
    } else if (!f) {
      body = `<p class="ux-st-q">${pt('q1')}</p><div class="ux-st-tiles">${CAT.firms.map((x) => `<button type="button" class="ux-st-tile" data-st-firm="${esc(x.id)}"><b>${esc(x.name)}</b><small>${((n) => (n === 1 ? esc(x.programs.find((y) => !y.legacy).name) : pt('types').replace('{n}', n)))(x.programs.filter((y) => !y.legacy).length || x.programs.length)}</small></button>`).join('')}
        ${mode === 'create' ? `<button type="button" class="ux-st-tile ghost" data-st-manual><b>${pt('other')}</b><small>${pt('otherSub')}</small></button>` : ''}</div>`;
    } else if (!p) {
      const row = (x) => `<button type="button" class="ux-st-row${x.legacy ? ' ux-st-legacy' : ''}" data-st-type="${esc(x.id)}"><b>${esc(x.legacy && x.label ? L3(x.label) : x.name)}${x.direct ? ` <em>${pt('direct')}</em>` : ''}</b><small>${esc(x.note ? (x.note[LANG] || x.note.en || '') : '')}</small><i aria-hidden="true">›</i></button>`;
      const cur = f.programs.filter((x) => !x.legacy), old = f.programs.filter((x) => x.legacy);
      const OLD = ({ en: 'Account bought before the firm’s last rule change', fr: 'Compte acheté avant le dernier changement de règles', es: 'Cuenta comprada antes del último cambio de reglas' })[LANG] || 'Account bought before the firm’s last rule change';
      body = `<p class="ux-st-q">${pt('q2')}</p><div class="ux-st-list">${cur.map(row).join('')}</div>${old.length ? `<p class="ux-st-sub">${OLD}</p><div class="ux-st-list">${old.map(row).join('')}</div>` : ''}`;
    } else if (!s) {
      body = `<p class="ux-st-q">${pt('q3')}</p><div class="ux-st-sizes">${p.sizes.map((x) => `<button type="button" class="ux-st-size" data-st-size="${x.size}">${x.size / 1000}K</button>`).join('')}</div>`;
    } else {
      const phases = ['eval', 'funded'].filter((k) => s[k]);
      if (d.phase === 'live' && phaseRules(s, 'live')) phases.push('live');
      if (!phaseRules(s, d.phase)) d.phase = phases[0];
      if (mode === 'create' && d.phaseSet === '1' && phases.includes(d.phase)) phases.splice(0, phases.length, d.phase);   // already answered first
      const r = s[d.phase];
      body = `${phases.length > 1 ? `<div class="seg ux-st-phase" role="tablist">${phases.map((k) => `<button type="button" role="tab" aria-selected="${k === d.phase}" class="${k === d.phase ? 'on' : ''}" data-st-phase="${k}">${pt(k)}</button>`).join('')}</div>` : ''}
        ${choicesFor(p, d.phase === 'eval' ? 'funded' : d.phase).map((o) => { const cur = d['opt_' + o.id] || o.default; return `<div class="ux-st-choice"><p class="ux-st-cl">${esc(L3(o.label))}${d.phase === 'eval' ? ` <small>${({ en: '(you can choose it later, when the account is funded)', fr: '(tu peux le choisir plus tard, au passage en financé)', es: '(puedes elegirla más tarde, al pasar a financiada)' })[LANG] || ''}</small>` : ''}</p><div class="seg ux-st-phase" role="tablist">${o.choices.map((c) => `<button type="button" role="tab" aria-selected="${c.id === cur}" class="${c.id === cur ? 'on' : ''}" data-st-opt="${esc(o.id)}" data-st-val="${esc(c.id)}">${esc(L3(c.label))}</button>`).join('')}</div>${((c) => (c && c.sub ? `<small class="ux-st-note">${esc(L3(c.sub))}</small>` : ''))(o.choices.find((c) => c.id === cur))}</div>`; }).join('')}
        ${r && r.dll && r.dll_optional ? `<label class="ux-st-opt"><span>${pt('withDll')} · ${usd(r.dll)}</span><span class="sw"><input type="checkbox" data-st-dll ${d.dll === '1' ? 'checked' : ''}><i></i></span></label>` : ''}
        <div class="ux-st-sum">${summary(d.firm, d.type, d.size, d.phase, (stValue(w) || '').split('|')[4] || '')}</div>
        ${mode === 'apply' ? `<button type="button" class="btn primary" data-pk-apply="${esc(d.acct)}">${pt('applyBtn')}</button>` : ''}`;
    }
    w.innerHTML = `<p class="ux-pk-title">${mode === 'apply' ? t('apply') : pt('ready')}</p>${crumbs}${body}`;
    w.dataset.value = s ? stValue(w) : '';
    const form = w.closest('form[data-form="account"]');
    if (form) { form.classList.toggle('ux-st-final', !!s); if (s) fillForm(form, w.dataset.value); }
  }
  /** the app's own fields are filled from the choice (firm, name, starting balance) */
  function fillForm(f, val) {
    f.dataset.uxPreset = val || '';
    const p = rulesOf(val); if (!p) return;
    const firmSel = f.querySelector('[name="firm"]');
    const names = p.aliases.map((n) => n.toLowerCase());   // « Lucid » already in the journal = « Lucid Trading » of the catalogue
    const known = (S.firms || []).find((x) => names.includes((x.name || '').toLowerCase()));
    if (firmSel && firmSel.tagName === 'SELECT') {
      const opts = [...firmSel.options];
      if (known && opts.some((o) => o.value === known.id)) firmSel.value = known.id; else if (opts.some((o) => o.value === '__new')) firmSel.value = '__new';
      firmSel.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (firmSel) firmSel.value = known ? known.id : '__new';
    const fn = f.querySelector('[name="firmName"]');
    if (fn && (!known || !firmSel || firmSel.value === '__new' || firmSel.tagName !== 'SELECT')) { fn.value = p.firm; fn.dispatchEvent(new Event('input', { bubbles: true })); }
    const nm = f.querySelector('[name="name"]'); if (nm && (!nm.value.trim() || nm.dataset.uxAuto === '1')) { nm.value = p.name; nm.dataset.uxAuto = '1'; }
    const st = f.querySelector('[name="start"]'); if (st) st.value = String(p.start);
  }
  const stHtml = (mode, acct) => { const w = document.createElement('div'); w.className = 'ux-pk ux-st'; w.setAttribute('data-noi18n', ''); w.dataset.mode = mode; if (acct) w.dataset.acct = acct; w.dataset.phase = 'eval'; return w; };
  // taps in the steps
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.ux-st button, .ux-st-manualback'); if (!b) return;
    if (b.matches('.ux-st-manualback')) { const f = b.closest('form'); f.classList.add('ux-st-on'); b.remove(); const w = f.querySelector('.ux-st'); w.hidden = false; stDraw(w); return; }
    const w = b.closest('.ux-st'), d = w.dataset;
    if (b.hasAttribute('data-st-open')) { d.open = '1'; stDraw(w); return; }
    if (b.dataset.stPh0) { d.phase = b.dataset.stPh0; d.phaseSet = '1'; const f = w.closest('form'); if (f) f.dataset.uxPhase = d.phase; }
    else if (b.dataset.stFirm) { d.firm = b.dataset.stFirm; delete d.type; delete d.size; const f = CAT.firms.find((x) => x.id === d.firm); if (f && f.programs.length === 1) { d.type = f.programs[0].id; if (f.programs[0].sizes.length === 1) d.size = String(f.programs[0].sizes[0].size); } }
    else if (b.dataset.stType) { d.type = b.dataset.stType; delete d.size; const f = CAT.firms.find((x) => x.id === d.firm), p = f && f.programs.find((x) => x.id === d.type); if (p && p.sizes.length === 1) d.size = String(p.sizes[0].size); }
    else if (b.dataset.stSize) d.size = b.dataset.stSize;
    else if (b.dataset.stPhase) d.phase = b.dataset.stPhase;
    else if (b.dataset.stOpt) d['opt_' + b.dataset.stOpt] = b.dataset.stVal;
    else if (b.dataset.stGo === 'phase') { d.phaseSet = ''; delete d.firm; delete d.type; delete d.size; }
    else if (b.dataset.stGo) { const k = b.dataset.stGo; if (k === 'firm') { delete d.firm; delete d.type; delete d.size; } else if (k === 'type') { delete d.type; delete d.size; } else delete d.size; const f = w.closest('form'); if (f) { f.dataset.uxPreset = ''; } }
    else if (b.hasAttribute('data-st-manual')) {
      const f = w.closest('form'); f.classList.remove('ux-st-on', 'ux-st-final'); w.hidden = true; f.dataset.uxPreset = '';
      const back = document.createElement('button'); back.type = 'button'; back.className = 'link ux-st-manualback'; back.textContent = pt('back'); w.after(back);
      const first = f.querySelector('input:not([type=hidden]), select'); if (first) first.focus();
      return;
    } else return;
    stDraw(w);
    const q = w.querySelector('.ux-st-q, .ux-st-sum'); if (q && innerWidth <= 860) w.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  });
  document.addEventListener('change', (e) => { const x = e.target; if (x.matches && x.matches('[data-st-dll]')) { const w = x.closest('.ux-st'); w.dataset.dll = x.checked ? '1' : ''; stDraw(w); } });

  function enhance() {
    const v = route().v, main = document.getElementById('main'); if (!main) return;
    // Settings: the ZIP export next to the JSON one
    const ex = main.querySelector('[data-act="export"]');
    if (ex && !main.querySelector('.ux-zip')) {
      const a = document.createElement('a'); a.className = 'btn primary ux-zip'; a.href = 'api/export/full'; a.setAttribute('data-noi18n', ''); a.textContent = t('zip'); a.title = t('zip_d');
      ex.before(a);
    }
    // account creation: firm → account type → size → phase
    document.querySelectorAll('form[data-form="account"]').forEach((f) => {
      if (f.querySelector('.ux-pk')) return;
      const w = stHtml('create'); f.prepend(w); f.classList.add('ux-st-on');
      loadCat(); stDraw(w);
    });
    // account page: apply the rules of a firm's account type
    if (v === 'account') {
      const mm = /^#account\/([^/]+)/.exec(location.hash);
      if (mm) { loadCat(); if (CAT) rulesBanner(main, decodeURIComponent(mm[1])); }
      const inp = main.querySelector('[data-bind$="|rules.consistency_pct"], [data-bind$="|rules.min_days"]');
      if (inp && !main.querySelector('.ux-pk')) {
        const id = inp.dataset.bind.split('|')[1];
        const acc = (S.accounts || []).find((a) => a.id === id), fn = acc && typeof firm === 'function' && firm(acc.firm_id);
        const box = stHtml('apply', id); box.classList.add('ux-preset-apply');
        const host = inp.closest('.fgrid') || inp.closest('section') || inp.parentElement; host.before(box);
        loadCat(); stDraw(box);
        // start at the account's own firm when its name matches the catalogue
        const tryHint = () => { if (!CAT || !fn) return; const m = CAT.firms.find((x) => [x.name, ...(x.aliases || [])].some((n) => n.toLowerCase() === String(fn.name || '').toLowerCase())); if (m && !box.dataset.firm) { box.dataset.firm = m.id; stDraw(box); } };
        if (CAT) tryHint(); else setTimeout(tryHint, 800);
      }
    }
  }
  /* ───── a firm changed its rules: the account keeps its own until the trader applies the new ones ───── */
  const RU = { en: { t: '{f} changed its rules', s: 'What changes for this account:', apply: 'Apply the new rules', keep: 'Keep my rules', done: 'New rules applied', kept: 'Your rules are kept' },
    fr: { t: '{f} a changé ses règles', s: 'Ce qui change pour ce compte :', apply: 'Appliquer les nouvelles règles', keep: 'Garder mes règles', done: 'Nouvelles règles appliquées', kept: 'Tes règles sont gardées' },
    es: { t: '{f} cambió sus reglas', s: 'Lo que cambia para esta cuenta:', apply: 'Aplicar las nuevas reglas', keep: 'Mantener mis reglas', done: 'Nuevas reglas aplicadas', kept: 'Se mantienen tus reglas' } };
  const ru = (k) => (RU[LANG] || RU.en)[k];
  const RL = { en: { dd_lock_offset_c: 'Threshold stops at start +', target_c: 'Profit target', dd_c: 'Max loss', dd_type: 'Drawdown type', dll_c: 'Daily loss limit', consistency_pct: 'Consistency', min_days: 'Minimum days', payout_win_days: 'Winning days for a payout', payout_win_min_c: 'Minimum per winning day', payout_trade_days: 'Trading days for a payout', payout_min_c: 'Minimum payout', payout_max_c: 'Maximum per payout', payout_max_pct: 'Max % of the profit', payout_min_bal_c: 'Balance to keep', payout_cycle_min_c: 'Profit since the last payout', payout_ladder_c: 'Payout caps', payout_max_n: 'Max number of payouts', payout_cycle_pos: 'Profitable since the last payout' },
    fr: { dd_lock_offset_c: 'Seuil bloqué à départ +', target_c: 'Objectif de profit', dd_c: 'Perte max', dd_type: 'Type de drawdown', dll_c: 'Limite de perte du jour', consistency_pct: 'Consistance', min_days: 'Jours minimum', payout_win_days: 'Jours gagnants pour un payout', payout_win_min_c: 'Minimum par jour gagnant', payout_trade_days: 'Jours tradés pour un payout', payout_min_c: 'Payout minimum', payout_max_c: 'Maximum par payout', payout_max_pct: 'Max % du profit', payout_min_bal_c: 'Solde à garder', payout_cycle_min_c: 'Profit depuis le dernier payout', payout_ladder_c: 'Plafonds de payout', payout_max_n: 'Nombre max de payouts', payout_cycle_pos: 'Profitable depuis le dernier payout' },
    es: { dd_lock_offset_c: 'Umbral fijo en inicio +', target_c: 'Objetivo de beneficio', dd_c: 'Pérdida máx.', dd_type: 'Tipo de drawdown', dll_c: 'Límite de pérdida diaria', consistency_pct: 'Consistencia', min_days: 'Días mínimos', payout_win_days: 'Días ganadores para un payout', payout_win_min_c: 'Mínimo por día ganador', payout_trade_days: 'Días operados para un payout', payout_min_c: 'Payout mínimo', payout_max_c: 'Máximo por payout', payout_max_pct: 'Máx. % del beneficio', payout_min_bal_c: 'Saldo a mantener', payout_cycle_min_c: 'Beneficio desde el último payout', payout_ladder_c: 'Topes de payout', payout_max_n: 'Número máx. de payouts', payout_cycle_pos: 'Rentable desde el último payout' } };
  const fmtR = (k, v) => { if (v == null || v === false) return pt('none'); if (v === true) return '✓'; if (Array.isArray(v)) return v.map((x) => (x == null ? '∞' : usd(x / 100))).join(' / '); if (/_c$/.test(k)) return usd(v / 100); if (k === 'consistency_pct' || k === 'payout_max_pct') return v + ' %'; if (k === 'dd_type') return pt(v); return String(v); };
  /** [key, now, new] for every rule of the preset that differs from the account's (live accounts: the max loss follows the floor) */
  function rulesDiff(acc) {
    if (!acc || !acc.preset || !CAT) return [];
    const p = rulesOf(acc.preset); if (!p) return [];
    const cur = acc.rules || {}, out = [];
    Object.keys(p.rules).forEach((k) => {
      if (!(RL.en[k])) return; if (k === 'dd_c' && p.rules.dd_floor_c != null) return;
      const a = cur[k] == null ? null : cur[k], b = p.rules[k] == null ? null : p.rules[k];
      if (JSON.stringify(a) !== JSON.stringify(b)) out.push([k, a, b]);
    });
    return out;
  }
  function rulesBanner(main, id) {
    const acc = (S.accounts || []).find((a) => a.id === id); let el = main.querySelector('.ux-newrules');
    const diff = acc && acc.status !== 'archived' && acc.status !== 'closed' && CAT && CAT.version && acc.preset_ver !== CAT.version && acc.preset_skip !== CAT.version ? rulesDiff(acc) : [];
    if (!diff.length) { if (el) el.remove(); return; }
    const fm = CAT.firms.find((x) => x.id === String(acc.preset).split('|')[0]);
    const L = RL[LANG] || RL.en;
    const html = `<section class="surface ux-newrules" data-noi18n data-acc="${esc(id)}"><b>${esc(ru('t').replace('{f}', fm ? fm.name : ''))}</b><p class="muted">${ru('s')}</p>
      <ul>${diff.slice(0, 8).map(([k, a, b]) => `<li><span>${esc(L[k])}</span><s>${esc(fmtR(k, a))}</s><b>${esc(fmtR(k, b))}</b></li>`).join('')}</ul>
      <div class="ux-newrules-a"><button type="button" class="btn primary" data-nr-apply="${esc(id)}">${ru('apply')}</button><button type="button" class="btn" data-nr-keep="${esc(id)}">${ru('keep')}</button></div></section>`;
    if (el && el._h === html) return;
    if (!el) { el = document.createElement('div'); const back = main.querySelector(':scope > .row'); if (back) back.after(el); else main.prepend(el); }
    el.outerHTML = html; const n = main.querySelector('.ux-newrules'); if (n) n._h = html;
  }
  document.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('[data-nr-apply]'), k = e.target.closest && e.target.closest('[data-nr-keep]');
    if (!a && !k) return;
    const id = (a || k).dataset.nrApply || (a || k).dataset.nrKeep, acc = (S.accounts || []).find((x) => x.id === id); if (!acc) return;
    if (a) {
      const p = rulesOf(acc.preset); if (!p) return;
      editDoc('accounts', id, (d) => { const live = p.rules.dd_floor_c != null; const keepDd = d.rules && d.rules.dd_c; d.rules = Object.assign({}, d.rules || {}, p.rules); if (live && keepDd != null) d.rules.dd_c = Math.max(0, (d.starting_balance_c || 0) - d.rules.dd_floor_c); d.preset_ver = CAT.version; delete d.preset_skip; });
      toast(ru('done'));
    } else { editDoc('accounts', id, (d) => { d.preset_skip = CAT.version; }); toast(ru('kept')); }
    setTimeout(() => render(), 80);
  });
  window.SweepPresets.rulesDiff = (id) => rulesDiff((S.accounts || []).find((a) => a.id === id));
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-pk-apply]'); if (!b) return;
    const p = rulesOf(b.closest('.ux-pk').dataset.value); if (!p) return;
    const pv = b.closest('.ux-pk').dataset.value;
    editDoc('accounts', b.dataset.pkApply, (d) => { d.rules = Object.assign({}, d.rules || {}, p.rules); d.phase = pv.split('|')[3] || d.phase; d.preset = pv; d.preset_ver = CAT && CAT.version; delete d.preset_skip; });
    const st = b.closest('.ux-st'); if (st) { st.dataset.open = ''; }
    toast(t('applied')); setTimeout(() => render(), 100);
  });
  // after the account is created, give it the preset rules
  if (typeof submitAccount === 'function') {
    const orig = submitAccount;
    submitAccount = function (form) {
      const pv = form && form.dataset && form.dataset.uxPreset, before = new Set((S.accounts || []).map((a) => a.id));
      const out = orig.apply(this, arguments);
      try {
        const p = pv && rulesOf(pv), ph = (pv && pv.split('|')[3]) || (form && form.dataset && form.dataset.uxPhase) || null;
        const added = (S.accounts || []).find((a) => !before.has(a.id));
        if (added) editDoc('accounts', added.id, (d) => { if (p) d.rules = Object.assign({}, d.rules || {}, p.rules); if (ph) d.phase = ph; { const mt = (form && form.dataset && form.dataset.acctMtype) || (['eval', 'funded', 'live', 'personal'].includes(ph) ? ph : ''); if (mt) d.money_type = mt; } if (p && pv) { d.preset = pv; d.preset_ver = CAT && CAT.version; } if (d.rules && d.rules.dd_floor_c != null) d.rules.dd_c = Math.max(0, (d.starting_balance_c || 0) - d.rules.dd_floor_c); });
      } catch (x) { /* never blocks */ }
      return out;
    };
  }
  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { enhance(); } catch (x) { /* never blocks */ } return out; };
  document.addEventListener('click', () => setTimeout(() => { try { enhance(); } catch (x) { /* drawers */ } }, 60), true);
})();

/* ───────────── 12. « Wow » moments: notification text ───────────── */
(function () {
  const N = {
    en: { 'wow_journal.title': '{n} trades journaled.', 'wow_journal.body': 'This is what consistency looks like. Keep going.', 'wow_plans.title': '{n} plans made.', 'wow_plans.body': 'You show up prepared. That is an edge.',
      'wow_reviews.title': '{n} reviews done.', 'wow_reviews.body': 'Every review makes the next day sharper.', 'wow_days.title': '{n} days with Sweep.', 'wow_days.body': 'Thank you for building the habit with us.',
      'wow_clean_week.title': 'A full week inside your plan.', 'wow_clean_week.body': 'Not one trade outside your plan last week. That is discipline.',
      'wow_best_month.title': 'Your best month of discipline.', 'wow_best_month.body': '{pct} % valid days in {month}. Your record.',
      'rules_changed.title': '{firm} changed its rules', 'rules_changed.body': 'For {account}: {changes}. Your account keeps its rules until you apply the new ones.' },
    fr: { 'wow_journal.title': '{n} trades journalisés.', 'wow_journal.body': 'La régularité, c’est exactement ça. Continue.', 'wow_plans.title': '{n} plans faits.', 'wow_plans.body': 'Tu te présentes préparé. C’est un edge.',
      'wow_reviews.title': '{n} revues faites.', 'wow_reviews.body': 'Chaque revue rend le jour suivant plus clair.', 'wow_days.title': '{n} jours avec Sweep.', 'wow_days.body': 'Merci de bâtir l’habitude avec nous.',
      'wow_clean_week.title': 'Une semaine entière dans ton plan.', 'wow_clean_week.body': 'Pas un seul trade hors plan la semaine dernière. C’est ça, la discipline.',
      'wow_best_month.title': 'Ton meilleur mois de discipline.', 'wow_best_month.body': '{pct} % de jours valides en {month}. Ton record.',
      'rules_changed.title': '{firm} a changé ses règles', 'rules_changed.body': 'Pour {account} : {changes}. Ton compte garde ses règles tant que tu n’appliques pas les nouvelles.' },
    es: { 'wow_journal.title': '{n} trades registrados.', 'wow_journal.body': 'Así se ve la constancia. Sigue.', 'wow_plans.title': '{n} planes hechos.', 'wow_plans.body': 'Llegas preparado. Eso es una ventaja.',
      'wow_reviews.title': '{n} revisiones hechas.', 'wow_reviews.body': 'Cada revisión hace el día siguiente más claro.', 'wow_days.title': '{n} días con Sweep.', 'wow_days.body': 'Gracias por construir el hábito con nosotros.',
      'wow_clean_week.title': 'Una semana entera dentro de tu plan.', 'wow_clean_week.body': 'Ni un trade fuera de tu plan la semana pasada. Eso es disciplina.',
      'wow_best_month.title': 'Tu mejor mes de disciplina.', 'wow_best_month.body': '{pct} % de días válidos en {month}. Tu récord.',
      'rules_changed.title': '{firm} cambió sus reglas', 'rules_changed.body': 'Para {account}: {changes}. Tu cuenta mantiene sus reglas hasta que apliques las nuevas.' },
  };
  const reg = () => { if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings(N); } catch (e) { /* older module */ } return true; } return false; };
  if (!reg()) setTimeout(reg, 1500);
})();

/* ───────────── 13. Two dynamic sentences the dictionary cannot catch ───────────── */
(function () {
  if (typeof render !== 'function') return;
  const P = { fr: { 'this month': 'ce mois-ci', 'this week': 'cette semaine', today: "aujourd'hui", 'this year': 'cette année', 'in this range': 'sur cette période', overall: 'au total', 'all time': 'au total' },
              es: { 'this month': 'este mes', 'this week': 'esta semana', today: 'hoy', 'this year': 'este año', 'in this range': 'en este periodo', overall: 'en total', 'all time': 'en total' } };
  const RULES = [
    [/^No trades (.+)\. Change the period or add trades to see your (?:insights|stats)\.$/, (m, L) => L === 'fr' ? `Aucun trade ${P.fr[m[1]] || m[1]}. Change la période ou ajoute des trades pour voir tes analyses.` : `Ninguna operación ${P.es[m[1]] || m[1]}. Cambia el periodo o añade operaciones para ver tus análisis.`],
    [/^Not enough data yet\. Complete the discipline checklist on at least (\d+) trades \((\d+) so far\)\.$/, (m, L) => L === 'fr' ? `Pas encore assez de données. Remplis la checklist de discipline sur au moins ${m[1]} trades (${m[2]} pour l'instant).` : `Aún no hay suficientes datos. Completa la checklist de disciplina en al menos ${m[1]} operaciones (${m[2]} por ahora).`],
  ];
  function fix() {
    const L = LANG; if (L !== 'fr' && L !== 'es') return;
    const main = document.getElementById('main'); if (!main) return;
    const w = document.createTreeWalker(main, NodeFilter.SHOW_TEXT); let n;
    while ((n = w.nextNode())) { const s = n.textContent.trim(); if (s.length < 20) continue; for (const [re, fn] of RULES) { const m = re.exec(s); if (m) { n.textContent = fn(m, L); break; } } }
  }
  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { fix(); } catch (e) { /* never blocks */ } return out; };
})();

/* ───────────── 14. Empty states: what this screen will become, one action, sample data on demand ───────────── */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  const T = {
    tt: { en: { trades: 'No trades yet', calendar: 'Your month, day by day', analytics: 'Your stats start here', payouts: 'No payouts or expenses yet' },
          fr: { trades: 'Aucun trade pour l’instant', calendar: 'Ton mois, jour par jour', analytics: 'Tes stats commencent ici', payouts: 'Aucun payout ni dépense' },
          es: { trades: 'Aún no hay operaciones', calendar: 'Tu mes, día a día', analytics: 'Tus stats empiezan aquí', payouts: 'Aún no hay payouts ni gastos' } },
    en: { trades: 'Every trade you log lands here, with its chart, its R and its discipline score.', calendar: 'Each market day will light up with its result, your discipline and the day’s news.',
      analytics: 'Here you will see which setups, hours and emotions really pay off for you.', payouts: 'Log every payout and every evaluation fee to see your real result across firms.',
      add: 'Add my first trade', sample: 'Preview with sample data', sample_d: 'Removable in one tap', demo_on: 'You are looking at sample data.', demo_off: 'Remove sample data' },
    fr: { trades: 'Chaque trade journalisé arrive ici, avec son graphique, son R et sa note de discipline.', calendar: 'Chaque jour de marché s’allumera avec son résultat, ta discipline et les nouvelles du jour.',
      analytics: 'Ici, tu verras quels setups, quelles heures et quelles émotions te rapportent vraiment.', payouts: 'Note chaque payout et chaque frais d’évaluation pour voir ton vrai résultat, toutes firmes confondues.',
      add: 'Ajouter mon premier trade', sample: 'Aperçu avec des données d’exemple', sample_d: 'Retirables en un geste', demo_on: 'Tu regardes des données d’exemple.', demo_off: 'Retirer les données d’exemple' },
    es: { trades: 'Cada operación registrada llega aquí, con su gráfico, su R y su nota de disciplina.', calendar: 'Cada día de mercado se iluminará con su resultado, tu disciplina y las noticias del día.',
      analytics: 'Aquí verás qué setups, horas y emociones te rinden de verdad.', payouts: 'Registra cada payout y cada cuota de evaluación para ver tu resultado real.',
      add: 'Añadir mi primera operación', sample: 'Vista previa con datos de ejemplo', sample_d: 'Se quitan con un toque', demo_on: 'Estás viendo datos de ejemplo.', demo_off: 'Quitar los datos de ejemplo' },
  };
  const t = () => T[LANG] || T.en;
  const IC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M12 3v4M12 17v4M8 7h8v10H8z"/></svg>';
  function paint() {
    const v = route().v, main = document.getElementById('main');
    if (!main || !['trades', 'calendar', 'analytics', 'payouts'].includes(v)) return;
    const trades = S.trades || [], real = trades.filter((x) => !x.demo), demo = trades.length - real.length;
    const emptyPay = v === 'payouts' && !(S.payouts || []).length && !(S.expenses || []).length;
    let html = '';
    if (v === 'payouts' ? emptyPay : !real.length) {
      if (demo && v !== 'payouts') html = `<div class="ux-empty demo"><span>${t().demo_on}</span><button type="button" class="link" data-act="demo-del">${t().demo_off}</button></div>`;
      else if (!demo || v === 'payouts') html = `<div class="ux-empty"><span class="ux-e-ic">${IC}</span><h3>${(T.tt[LANG] || T.tt.en)[v]}</h3><p>${t()[v]}</p><div class="ux-e-acts">${v !== 'payouts' ? `<button type="button" class="btn primary" data-act="add-trade">${t().add}</button>` : ''}${!trades.length && v !== 'payouts' ? `<button type="button" class="link" data-act="demo">${t().sample}<small>${t().sample_d}</small></button>` : ''}</div></div>`;
    }
    const old = main.querySelector('.ux-empty');
    if (!html) { if (old) old.remove(); return; }
    if (old && old.dataset.k === v + html.length) return;
    if (old) old.remove();
    const wrap = document.createElement('div'); wrap.innerHTML = html; const el = wrap.firstElementChild; el.dataset.k = v + html.length; el.setAttribute('data-noi18n', '');
    const anchor = main.querySelector('.page-head, h1, .ph');
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(el, anchor.nextSibling); else main.prepend(el);
  }
  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { paint(); } catch (e) { /* never blocks */ } return out; };
})();

/* ───────────── 15. Browser error reports + admin dashboard ───────────── */
(function () {
  'use strict';
  // errors on traders' devices reach the admin dashboard (5 per page load at most)
  let sent = 0;
  const report = (msg, src, line) => {
    if (sent >= 5 || !msg) return; sent++;
    try { fetch('api/client-error', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' },
      body: JSON.stringify({ msg: String(msg).slice(0, 500), src: String(src || '').split('/').pop(), line: line || 0, page: (location.hash || '').split('/')[0], ver: ((document.querySelector('script[src*="assets/app."]') || {}).src || '').split('/').pop() }) }).catch(() => {}); } catch (e) { /* never throws */ }
  };
  addEventListener('error', (e) => { if (e && e.message && !/ResizeObserver|Script error/.test(e.message)) report(e.message, e.filename, e.lineno); });
  addEventListener('unhandledrejection', (e) => { const r = e && e.reason; if (r && !(r.status >= 400 && r.status < 500)) report('Promise: ' + (r.message || r), '', 0); });

  if (typeof render !== 'function') return;
  const T = {
    en: { title: 'Dashboard', north: 'Traders with 3+ swept days (7 d)', active: 'Active traders (7 d)', sign: 'Sign-ups', act: 'Activation: first trade within 24 h', aha: 'First swept day within 7 days', w2: 'Week 2: 3+ swept days', ai: 'AI cost', err: 'Errors (24 h)', mrr: 'Estimated MRR', src: 'Sign-ups by source (30 d)', meth: 'How trades are logged (30 d)', of: 'of {n}', today: 'today', d7: '7 days', js: 'browser', php: 'server', none: 'no data yet' },
    fr: { title: 'Tableau de bord', north: 'Traders avec 3+ journées balayées (7 j)', active: 'Traders actifs (7 j)', sign: 'Inscriptions', act: 'Activation : 1er trade en 24 h', aha: '1re journée balayée en 7 jours', w2: 'Semaine 2 : 3+ journées balayées', ai: 'Coût IA', err: 'Erreurs (24 h)', mrr: 'Revenu mensuel estimé', src: 'Inscriptions par source (30 j)', meth: 'Saisie des trades (30 j)', of: 'sur {n}', today: 'aujourd’hui', d7: '7 jours', js: 'navigateur', php: 'serveur', none: 'pas encore de données' },
    es: { title: 'Panel', north: 'Traders con 3+ días barridos (7 d)', active: 'Traders activos (7 d)', sign: 'Registros', act: 'Activación: 1.ª operación en 24 h', aha: '1.er día barrido en 7 días', w2: 'Semana 2: 3+ días barridos', ai: 'Coste IA', err: 'Errores (24 h)', mrr: 'Ingreso mensual estimado', src: 'Registros por fuente (30 d)', meth: 'Cómo se registran (30 d)', of: 'de {n}', today: 'hoy', d7: '7 días', js: 'navegador', php: 'servidor', none: 'aún sin datos' },
  };
  const t = () => T[LANG] || T.en;
  let data = null, at = 0, busy = false;
  const pct = (o) => (o && o.pct != null ? `${o.pct} %` : '—');
  const card = (label, value, sub, big) => `<div class="ux-m ${big ? 'big' : ''}"><small>${label}</small><b>${value}</b>${sub ? `<span>${sub}</span>` : ''}</div>`;
  function html(d) {
    const x = t(), list = (o) => { const e = Object.entries(o || {}); return e.length ? e.map(([k, v]) => `<li><span>${esc(k)}</span><b>${v}</b></li>`).join('') : `<li class="muted">${x.none}</li>`; };
    return `<div class="sec-h"><h2>${x.title}</h2><small class="muted">${new Date(d.generated_at).toLocaleTimeString()}</small></div>
      <div class="ux-mgrid">${card(x.north, d.north_star, x.active + ' : ' + d.active_7d, true)}${card(x.sign, d.signups.d7 + ' / ' + d.signups.d30, '7 j / 30 j')}
        ${d.first_trade ? card(({ en: 'Sign-up → first trade (median)', fr: 'Inscription → premier trade (médiane)', es: 'Registro → primera operación (mediana)' })[LANG] || 'Sign-up → first trade', d.first_trade.median_min == null ? '—' : (d.first_trade.median_min < 120 ? d.first_trade.median_min + ' min' : Math.round(d.first_trade.median_min / 60) + ' h'), ({ en: 'First trade on day 1: ', fr: 'Premier trade le jour 1 : ', es: 'Primera operación el día 1: ' })[LANG] + d.first_trade.day1_pct + ' %') : ''}        ${card(x.act, pct(d.activation_24h), x.of.replace('{n}', d.activation_24h.of))}${card(x.aha, pct(d.aha_7d), x.of.replace('{n}', d.aha_7d.of))}${card(x.w2, pct(d.retention_w2), x.of.replace('{n}', d.retention_w2.of))}
        ${card(x.ai, '$' + d.ai.today.toFixed(2), x.today + ' · $' + d.ai.d7.toFixed(2) + ' ' + x.d7)}${card(x.err, d.errors.js_24h + d.errors.php_24h, x.js + ' ' + d.errors.js_24h + ' · ' + x.php + ' ' + d.errors.php_24h)}
        ${card(x.mrr, d.revenue.mrr != null ? '$' + d.revenue.mrr : '—', (d.revenue.subs || []).map((s) => `${s.plan} ${s.i || ''} ×${s.n}`).join(' · '))}</div>
      <div class="ux-mlists"><div><h4>${x.src}</h4><ul>${list(d.signups.by_source_30d)}</ul></div><div><h4>${x.meth}</h4><ul>${list(d.trade_methods_30d)}</ul></div><div><h4>${{ en: 'Searches with no result (30 d)', fr: 'Recherches sans résultat (30 j)', es: 'Búsquedas sin resultado (30 d)' }[LANG] || 'Searches with no result (30 d)'}</h4><ul>${list(d.search_misses_30d)}</ul></div>
      ${d.errors.top && d.errors.top.length ? `<div><h4>${x.err}</h4><ul>${d.errors.top.map((e) => `<li><span>${esc(e.msg)}</span><b>${e.n}</b></li>`).join('')}</ul></div>` : ''}</div>`;
  }
  function paint() {
    if (route().v !== 'admin') return;
    const main = document.getElementById('main'); if (!main) return;
    let box = main.querySelector('.ux-metrics');
    if (!box) { box = document.createElement('section'); box.className = 'sec ux-metrics'; box.setAttribute('data-noi18n', ''); const anchor = main.querySelector('.page-head, h1, .ph'); if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(box, anchor.nextSibling); else main.prepend(box); }
    if (data) box.innerHTML = html(data);
    if (!busy && Date.now() - at > 60000) { busy = true; apiJSON('api/admin/metrics').then((d) => { data = d; at = Date.now(); busy = false; const b = document.querySelector('#main .ux-metrics'); if (b) b.innerHTML = html(d); }).catch(() => { busy = false; at = Date.now(); }); }
  }
  /* ───── Admin → Presets: last check, status per firm, alert after 8 days, « Check now » ───── */
  const PT2 = {
    en: { h: 'Presets', last: 'Last full check', never: 'never', by: { cron: 'weekly task', admin: 'Check now' }, ago: '{n} d ago', stale: 'No check for more than {n} days. Traders may be using outdated rules. An email was sent to the support address{m}.', staleNo: 'No check for more than {n} days. Traders may be using outdated rules.', mailed: ' ({d})', st: { unchanged: 'unchanged', updated: 'updated', review: 'to review', error: 'error', never: 'not checked yet' }, btn: 'Check now', run: 'Checking {f}… ({i}/{n})', done: 'Check finished', notified: '{n} trader(s) notified', ver: 'Catalogue', cron: 'Weekly task: 0 5 * * 1 php presets/cron.php' },
    fr: { h: 'Préréglages', last: 'Dernière vérification complète', never: 'jamais', by: { cron: 'tâche hebdomadaire', admin: 'Vérifier maintenant' }, ago: 'il y a {n} j', stale: 'Aucune vérification depuis plus de {n} jours. Les traders utilisent peut-être des règles périmées. Un courriel a été envoyé à l’adresse de support{m}.', staleNo: 'Aucune vérification depuis plus de {n} jours. Les traders utilisent peut-être des règles périmées.', mailed: ' ({d})', st: { unchanged: 'inchangé', updated: 'mis à jour', review: 'à revoir', error: 'erreur', never: 'pas encore vérifié' }, btn: 'Vérifier maintenant', run: 'Vérification de {f}… ({i}/{n})', done: 'Vérification terminée', notified: '{n} trader(s) avisé(s)', ver: 'Catalogue', cron: 'Tâche hebdomadaire : 0 5 * * 1 php presets/cron.php' },
    es: { h: 'Preajustes', last: 'Última verificación completa', never: 'nunca', by: { cron: 'tarea semanal', admin: 'Verificar ahora' }, ago: 'hace {n} d', stale: 'Ninguna verificación desde hace más de {n} días. Los traders quizá usan reglas desactualizadas. Se envió un correo a la dirección de soporte{m}.', staleNo: 'Ninguna verificación desde hace más de {n} días. Los traders quizá usan reglas desactualizadas.', mailed: ' ({d})', st: { unchanged: 'sin cambios', updated: 'actualizado', review: 'a revisar', error: 'error', never: 'aún no verificado' }, btn: 'Verificar ahora', run: 'Verificando {f}… ({i}/{n})', done: 'Verificación terminada', notified: '{n} trader(s) avisado(s)', ver: 'Catálogo', cron: 'Tarea semanal: 0 5 * * 1 php presets/cron.php' } };
  const p2 = () => PT2[LANG] || PT2.en;
  let pr = null, prAt = 0, prBusy = false, prRun = null;
  const when = (iso) => (iso ? new Date(iso).toLocaleString(LANG === 'en' ? 'en-US' : LANG + '-CA', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '');
  function prHtml(d) {
    const x = p2();
    const alert = d.stale ? `<div class="ux-pr-alert" role="alert">${d.alert_mailed_at ? x.stale.replace('{n}', d.stale_days).replace('{m}', x.mailed.replace('{d}', when(d.alert_mailed_at))) : x.staleNo.replace('{n}', d.stale_days)}</div>` : '';
    const rows = d.firms.map((f) => `<li class="ux-pr-${esc(f.status)}"><div><b>${esc(f.name)}</b><span class="ux-pr-chip">${esc(x.st[f.status] || f.status)}</span>${f.checked_at ? `<small>${when(f.checked_at)}</small>` : ''}${f.notified ? `<small>${x.notified.replace('{n}', f.notified)}</small>` : ''}</div>
      ${f.changes.length ? `<details><summary>${f.changes.length} ✎</summary><small>${f.changes.map(esc).join('<br>')}</small></details>` : ''}${f.errors.length ? `<small class="neg">${f.errors.map(esc).join('<br>')}</small>` : ''}</li>`).join('');
    return `<div class="sec-h"><h2>${x.h}</h2><button type="button" class="btn sm primary" data-pr-run ${prRun ? 'disabled' : ''}>${prRun ? esc(prRun) : x.btn}</button></div>${alert}
      <p class="ux-pr-last"><span>${x.last}</span><b>${d.last_run ? when(d.last_run) + ' · ' + x.ago.replace('{n}', d.days_since) + (d.last_run_by ? ' · ' + (x.by[d.last_run_by] || d.last_run_by) : '') : x.never}</b></p>
      <ul class="ux-pr-list">${rows}</ul><small class="muted">${x.ver} v${esc(d.version)} · ${x.cron}</small>`;
  }
  function prPaint() {
    if (route().v !== 'admin') return;
    const main = document.getElementById('main'); if (!main) return;
    let box = main.querySelector('.ux-presets-admin');
    if (!box) { box = document.createElement('section'); box.className = 'sec ux-presets-admin'; box.setAttribute('data-noi18n', ''); const m = main.querySelector('.ux-metrics'); if (m) m.after(box); else main.prepend(box); }
    if (pr) { const h = prHtml(pr); if (box._h !== h) { box.innerHTML = h; box._h = h; } }
    if (!prBusy && !prRun && Date.now() - prAt > 60000) { prBusy = true; apiJSON('api/admin/presets').then((d) => { pr = d; prAt = Date.now(); prBusy = false; prPaint(); }).catch(() => { prBusy = false; prAt = Date.now(); }); }
  }
  const post = (body) => fetch('api/admin/presets/check', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'fetch' }, body: JSON.stringify(body) }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  document.addEventListener('click', async (e) => {
    const b = e.target.closest && e.target.closest('[data-pr-run]'); if (!b || prRun || !pr) return;
    const firms = pr.firms.slice();
    for (let i = 0; i < firms.length; i++) {
      prRun = p2().run.replace('{f}', firms[i].name).replace('{i}', i + 1).replace('{n}', firms.length); prPaint();
      try { const r = await post({ firm: firms[i].id }); const f = pr.firms.find((x) => x.id === firms[i].id); if (f && r.result) Object.assign(f, { status: r.result.status, checked_at: r.result.checked_at, changes: r.result.changes || [], errors: r.result.errors || [], notified: r.result.notified || null }); }
      catch (x) { const f = pr.firms.find((y) => y.id === firms[i].id); if (f) Object.assign(f, { status: 'error', errors: [String(x.message || x)] }); }
    }
    try { pr = await post({ finish: true }); } catch (x) { /* the list above already shows each firm */ }
    prRun = null; prAt = Date.now(); prPaint(); if (typeof toast === 'function') toast(p2().done);
  });
  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { paint(); prPaint(); } catch (e) { /* never blocks */ } return out; };
})();

/* ───────────── 16. Text for « chart ready » and end-of-trial notifications ───────────── */
(function () {
  const N = {
    en: { 'chart_ready.title': 'Your {inst} chart is ready.', 'chart_ready.body': 'Replay your trade on the real candles while it is still fresh.',
      'trial_ending.title': '{days} days of {plan} left', 'trial_ending.body': 'So far: {accounts} accounts, {swept} days swept, {ai} AI analyses. Keep it all with {plan}, or stay on Free: nothing is ever deleted.' },
    fr: { 'chart_ready.title': 'Ton graphique {inst} est prêt.', 'chart_ready.body': 'Revois ton trade sur les vraies bougies pendant que c’est frais.',
      'trial_ending.title': 'Il te reste {days} jours de {plan}', 'trial_ending.body': 'Jusqu’ici : {accounts} comptes, {swept} journées balayées, {ai} analyses IA. Garde tout avec {plan}, ou reste sur Free : rien n’est jamais supprimé.' },
    es: { 'chart_ready.title': 'Tu gráfico de {inst} está listo.', 'chart_ready.body': 'Revisa tu operación en las velas reales mientras está fresca.',
      'trial_ending.title': 'Te quedan {days} días de {plan}', 'trial_ending.body': 'Hasta ahora: {accounts} cuentas, {swept} días barridos, {ai} análisis IA. Consérvalo con {plan}, o quédate en Free: nunca se borra nada.' },
  };
  const reg = () => { if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings(N); } catch (e) { /* older module */ } return true; } return false; };
  if (!reg()) setTimeout(reg, 1500);
})();

/* ───────────── 17. CSV import: Tradovate + Rithmic R|Trader Pro + TopstepX, detected automatically ───────────── */
(function () {
  'use strict';
  if (typeof parseTradovate !== 'function' || typeof parseCSV !== 'function') return;
  const origTv = parseTradovate;
  const PV = { NQ: 20, MNQ: 2, ES: 50, MES: 5, YM: 5, MYM: 0.5, RTY: 50, M2K: 5, CL: 1000, MCL: 100, GC: 100, MGC: 10, SI: 5000, SIL: 1000, '6E': 125000, M6E: 12500, ZN: 1000, ZB: 1000, NG: 10000, HG: 25000, MBT: 0.1, MET: 0.1 };
  const ROOT = /^(MNQ|NQ|MES|ES|MYM|YM|M2K|RTY|MCL|CL|MGC|GC|SIL|SI|M6E|6E|ZN|ZB|NG|HG|MBT|MET)/;
  // a symbol Sweep does not know is never priced as NQ: its root is kept, its P&L comes from the file or is typed by the trader
  const rootOf = (sym) => { const m = String(sym || '').match(ROOT); return m ? { root: m[1], unknown: false } : { root: String(sym || '').replace(/[FGHJKMNQUVXZ]\d{1,2}$/, '') || '?', unknown: true }; };
  const p2 = (n) => String(n).padStart(2, '0');
  const num = (s) => { s = String(s ?? '').replace(/[$,\s]/g, ''); const neg = /^\(.*\)$/.test(s); const v = parseFloat(s.replace(/[()]/g, '')); return isNaN(v) ? NaN : neg ? -Math.abs(v) : v; };
  const nyFmt = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const fromParts = (y, mo, d, h, mi, s) => ({ date: `${y}-${p2(mo)}-${p2(d)}`, time: `${p2(h)}:${p2(mi)}`, key: `${y}${p2(mo)}${p2(d)}${p2(h)}${p2(mi)}${p2(s)}` });
  /** a timestamp with an explicit zone (TopstepX exports UTC) → New York wall clock */
  function utcToNy(raw) {
    let s = String(raw || '').trim(); if (!s) return null;
    let m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})[ T](\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?)\s*(.*)$/);
    if (m) s = `${m[3]}-${p2(m[1])}-${p2(m[2])}T${m[4]}${m[5] ? m[5].replace(/\s+/g, '') : 'Z'}`;
    else { s = s.replace(' ', 'T').replace(/\s+/g, ''); if (!/(Z|[+-]\d{2}:?\d{2})$/.test(s)) s += 'Z'; }
    const d = new Date(s); if (isNaN(d)) return null;
    const q = Object.fromEntries(nyFmt.formatToParts(d).map((x) => [x.type, x.value]));
    return fromParts(q.year, +q.month, +q.day, +q.hour % 24, +q.minute, +q.second);
  }
  /** a local timestamp as shown by the platform (Rithmic): kept as is */
  function localTime(raw) {
    const s = String(raw || '').trim();
    let m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?/); if (m) return fromParts(m[1], +m[2], +m[3], +m[4], +m[5], +(m[6] || 0));
    m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?/); if (m) return fromParts(m[3], +m[1], +m[2], +m[4], +m[5], +(m[6] || 0));
    m = s.match(/^(\d{4})(\d{2})(\d{2})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?/); if (m) return fromParts(m[1], +m[2], +m[3], +m[4], +m[5], +(m[6] || 0));
    return null;
  }
  const keyMs = (k) => new Date(+k.slice(0, 4), +k.slice(4, 6) - 1, +k.slice(6, 8), +k.slice(8, 10), +k.slice(10, 12), +k.slice(12, 14)).getTime();
  const headerAt = (rows, need) => rows.findIndex((r) => { const h = r.map((c) => String(c).trim().toLowerCase()); return need.every((n) => h.includes(n)); });

  /* TopstepX « Trades » export: one row per round trip, times in UTC */
  function parseTopstepX(rows, at) {
    const h = rows[at].map((c) => String(c).trim().toLowerCase()), col = (n) => h.indexOf(n);
    const out = [];
    for (const r of rows.slice(at + 1)) {
      const g = (n) => (col(n) >= 0 ? String(r[col(n)] ?? '').trim() : '');
      const a = utcToNy(g('enteredat')), b = utcToNy(g('exitedat')); if (!a || !b) continue;
      const sym = g('contractname').toUpperCase().replace(/^\/|^CON\.F\.US\./, ''), ro = rootOf(sym), root = ro.root;
      const qty = Math.abs(parseInt(g('size'), 10) || 0); if (!qty) continue;
      const dir = /short|sell/i.test(g('type')) ? 'short' : 'long';
      const pnl = num(g('pnl')), fees = Math.abs(num(g('fees')) || 0) + Math.abs(num(g('commissions')) || 0);
      // TopstepX gives the trading day itself (TradeDay): the session date, used as is
      const td = g('tradeday'), tdm = td.match(/^(\d{4})-(\d{2})-(\d{2})/) || td.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
      const tradeDay = !tdm ? null : tdm[1].length === 4 ? `${tdm[1]}-${tdm[2]}-${tdm[3]}` : `${tdm[3]}-${p2(tdm[1])}-${p2(tdm[2])}`;
      out.push({ key: `tx:${g('id') || sym + ':' + a.key + ':' + qty}`, inst: root, unknown: ro.unknown && isNaN(pnl), sym, dir, date: a.date, tradeDay, entry_time: a.time, exit_time: b.time, entryKey: a.key, exitKey: b.key, qty,
        entry: num(g('entryprice')), exit: num(g('exitprice')), pnl_c: Math.round((isNaN(pnl) ? 0 : pnl) * 100), fees_c: Math.round(fees * 100), duration_s: Math.max(0, Math.round((keyMs(b.key) - keyMs(a.key)) / 1000)) });
    }
    return out;
  }

  /** fills (one account / contract at a time, FIFO) → round trips. prefix makes the import key (no duplicates on a re-import) */
  function pairFills(fills, prefix) {
    fills.sort((a, b) => a.t.key.localeCompare(b.t.key));
    const pos = new Map(), out = [];
    const px = (v) => Math.round(v * 1e6) / 1e6;
    for (const f of fills) {
      const k = f.acct + '|' + f.sym; let st = pos.get(k);
      let left = f.q;
      while (left > 0) {
        if (!st || st.net === 0) { st = { net: 0, dir: f.side, open: f.t, ew: 0, eq: 0, xw: 0, xq: 0, fee: 0, id: f.id }; pos.set(k, st); }
        if (f.side === st.dir) { st.net += left; st.ew += f.px * left; st.eq += left; st.fee += f.fee * (left / f.q); left = 0; break; }
        const close = Math.min(left, st.net);
        st.net -= close; st.xw += f.px * close; st.xq += close; st.fee += f.fee * (close / f.q); left -= close;
        if (st.net === 0) {
          const e = st.ew / st.eq, x = st.xw / st.xq, pv = PV[f.root] || 0;
          out.push({ key: `${prefix}:${f.acct}:${f.sym}:${st.open.key}:${st.id}`, acct: f.acct || '', inst: f.root, sym: f.sym, dir: st.dir > 0 ? 'long' : 'short', date: st.open.date, entry_time: st.open.time, exit_time: f.t.time,
            entryKey: st.open.key, exitKey: f.t.key, qty: st.eq, entry: px(e), exit: px(x),
            unknown: f.unknown, pnl_c: Math.round((x - e) * (st.dir > 0 ? 1 : -1) * st.xq * pv * 100), fees_c: Math.round(st.fee * 100), duration_s: Math.max(0, Math.round((keyMs(f.t.key) - keyMs(st.open.key)) / 1000)) });
        }
      }
    }
    return out;
  }

  /* TradingView « Order History » export (Trading panel → Order History → Export data): one row per order; the filled
     ones are paired into round trips. TradingView writes the times in the time zone set in TradingView (New York by
     default here; the trader can switch to their own or UTC in the preview). */
  const TV = { tz: 'America/New_York', text: '' };
  function tzToNy(p, tz) {
    // p: wall clock parts in tz → the same moment at New York time
    const guess = Date.UTC(+p.date.slice(0, 4), +p.date.slice(5, 7) - 1, +p.date.slice(8, 10), +p.key.slice(8, 10), +p.key.slice(10, 12), +p.key.slice(12, 14));
    const off = (ms) => { const f = new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).formatToParts(new Date(ms)); const q = {}; f.forEach((x) => { q[x.type] = x.value; }); return Date.UTC(+q.year, +q.month - 1, +q.day, +q.hour % 24, +q.minute, +q.second) - ms; };
    const utc = guess - off(guess - off(guess));
    const f = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).formatToParts(new Date(utc));
    const q = {}; f.forEach((x) => { q[x.type] = x.value; });
    return fromParts(q.year, +q.month, +q.day, +q.hour % 24, +q.minute, +q.second);
  }
  function parseTradingView(rows, at) {
    const h = rows[at].map((c) => String(c).trim().toLowerCase()), col = (...ns) => { for (const n of ns) { const i = h.indexOf(n); if (i >= 0) return i; } return -1; };
    const ci = { sym: col('symbol'), side: col('side'), qty: col('filled qty', 'filled quantity', 'qty', 'quantity'), px: col('fill price', 'avg fill price', 'avg price', 'price'), st: col('status'),
      fee: col('commission', 'fees'), t: col('closing time', 'fill time', 'update time', 'time', 'placing time'), id: col('order id', 'id') };
    const fills = [];
    for (const r of rows.slice(at + 1)) {
      const g = (i) => (i >= 0 ? String(r[i] ?? '').trim() : '');
      if (ci.st >= 0 && g(ci.st) && !/fill/i.test(g(ci.st))) continue;   // cancelled, rejected, working: not trades
      const q = Math.abs(parseFloat(g(ci.qty)) || 0), p0 = num(g(ci.px)); if (!q || isNaN(p0)) continue;
      const t0 = localTime(g(ci.t)); if (!t0) continue;
      const t = TV.tz === 'America/New_York' ? t0 : tzToNy(t0, TV.tz);
      const sym = g(ci.sym).toUpperCase().replace(/^[A-Z0-9_]+:/, '').replace(/\d!$/, ''), side = /^b/i.test(g(ci.side)) ? 1 : -1;
      const ro = rootOf(sym);
      fills.push({ acct: '', sym, root: ro.root, unknown: ro.unknown, side, q, px: p0, t, fee: Math.abs(num(g(ci.fee)) || 0), id: g(ci.id) || t.key });
    }
    return pairFills(fills, 'tv').sort((a, b) => (a.date + a.entry_time).localeCompare(b.date + b.entry_time));
  }
  window.SweepImportTV = { get tz() { return TV.tz; }, set tz(v) { TV.tz = v; }, reparse: () => (TV.text ? parseTradovate(TV.text) : null), active: () => !!TV.text };

  /* Rithmic R|Trader Pro « Orders History → Completed Orders »: fills paired into round trips (FIFO, per account and contract) */
  function parseRithmic(rows, at) {
    const h = rows[at].map((c) => String(c).trim().toLowerCase()), col = (n) => h.indexOf(n);
    const fills = [];
    for (const r of rows.slice(at + 1)) {
      const g = (n) => (col(n) >= 0 ? String(r[col(n)] ?? '').trim() : '');
      const q = Math.abs(parseInt(g('qty filled'), 10) || 0), px = num(g('avg fill price'));
      if (!q || isNaN(px) || (g('status') && !/fill/i.test(g('status')))) continue;
      const t = localTime(g('update time') || g('fill time') || g('create time')); if (!t) continue;
      const side = /^b/i.test(g('buy/sell')) ? 1 : -1, sym = g('symbol').toUpperCase();
      fills.push({ acct: g('account'), sym, root: rootOf(sym).root, unknown: rootOf(sym).unknown, side, q, px, t, fee: Math.abs(num(g('commission')) || 0), id: g('order number') });
    }
    const out = pairFills(fills, 'rt');
    return out.sort((a, b) => (a.date + a.entry_time).localeCompare(b.date + b.entry_time));
  }

  /** the trade's date is its session (New York): a trade opened at 18:00 or later belongs to the next day, as for the firms
   *  (daily limit, winning days, consistency, calendar). TopstepX writes that day itself (TradeDay): taken as is. */
  const nextDay = (d) => { const x = new Date(d + 'T12:00:00Z'); x.setUTCDate(x.getUTCDate() + 1); return x.toISOString().slice(0, 10); };
  const toSession = (rows) => rows.map((r) => {
    if (!r || !r.date) return r;
    const day = r.tradeDay || (String(r.entry_time || '') >= '18:00' ? nextDay(r.date) : r.date);
    const o = Object.assign({}, r, { date: day }); delete o.tradeDay; return o;
  });
  parseTradovate = function (text) {
    const rows = parseCSV(text);
    let at = headerAt(rows, ['contractname', 'enteredat', 'exitedat', 'entryprice', 'exitprice']);
    if (at >= 0) { const r = parseTopstepX(rows, at); if (!r.length) throw new Error('No closed trades found in this TopstepX export.'); return toSession(r); }
    TV.text = '';
    at = headerAt(rows, ['buy/sell', 'symbol', 'qty filled', 'avg fill price']);
    if (at >= 0) { const r = parseRithmic(rows, at); if (!r.length) throw new Error('No filled round trip found in this Rithmic export (check the Completed Orders columns).'); return toSession(r); }
    // TradingView Order History (Symbol, Side, Qty, Fill Price, Status, Closing Time…)
    at = rows.findIndex((r) => { const hh = r.map((c) => String(c).trim().toLowerCase()); return hh.includes('symbol') && hh.includes('side') && (hh.includes('fill price') || hh.includes('avg fill price')) && hh.some((x) => /time/.test(x)); });
    if (at >= 0) { TV.text = text; const r = parseTradingView(rows, at); if (!r.length) throw new Error('No filled round trip found in this TradingView export (export « Order History » with the Fill Price, Status and Closing Time columns).'); return toSession(r); }
    let tv; try { tv = origTv(text); } catch (e) {
      throw new Error('This file is not a Tradovate Performance report, a Rithmic R|Trader Pro Completed Orders export, a TopstepX Trades export or a TradingView Order History export.');
    }
    return Array.isArray(tv) ? toSession(tv) : tv;
  };

  /* the import page tells which formats work and how to export each */
  const T = {
    en: { fmt: 'Tradovate, Rithmic R|Trader Pro, TopstepX or TradingView (detected automatically)', tw: ['Trading panel at the bottom of the chart → Order History tab', '⋯ (top right of the tab): show every column (Side, Qty, Fill Price, Status, Commission, Closing Time, Order ID)', 'TradingView menu → Export data → Order History → Export (CSV)', 'Times: pick the time zone set in TradingView in the preview (New York by default)'], how: 'How to export', tv: ['Account Reports → Performance', 'Pick the account and dates', 'Download report (CSV)'],
      rt: ['File → Orders History, pick the account and the day', 'In Completed Orders, right-click the headers: add Account, Status, Buy/Sell, Symbol, Qty Filled, Avg Fill Price, Update Time, Commission', 'Export as CSV (one day per file)'], tx: ['Trades tab at the bottom of TopstepX', 'Click EXPORT (bottom right)', 'Times are in UTC: Sweep converts them to New York time'] },
    fr: { fmt: 'Tradovate, Rithmic R|Trader Pro, TopstepX ou TradingView (détecté automatiquement)', tw: ['Panneau de trading sous le graphique → onglet Order History', '⋯ (en haut à droite de l’onglet) : affiche toutes les colonnes (Side, Qty, Fill Price, Status, Commission, Closing Time, Order ID)', 'Menu TradingView → Export data → Order History → Export (CSV)', 'Heures : choisis dans l’aperçu le fuseau réglé dans TradingView (New York par défaut)'], how: 'Comment exporter', tv: ['Account Reports → Performance', 'Choisis le compte et les dates', 'Download report (CSV)'],
      rt: ['File → Orders History, choisis le compte et la journée', 'Dans Completed Orders, clic droit sur les en-têtes : ajoute Account, Status, Buy/Sell, Symbol, Qty Filled, Avg Fill Price, Update Time, Commission', 'Exporte en CSV (une journée par fichier)'], tx: ['Onglet Trades en bas de TopstepX', 'Clique EXPORT (en bas à droite)', 'Les heures sont en UTC : Sweep les convertit à l’heure de New York'] },
    es: { fmt: 'Tradovate, Rithmic R|Trader Pro, TopstepX o TradingView (detectado automáticamente)', tw: ['Panel de trading bajo el gráfico → pestaña Order History', '⋯ (arriba a la derecha de la pestaña): muestra todas las columnas (Side, Qty, Fill Price, Status, Commission, Closing Time, Order ID)', 'Menú de TradingView → Export data → Order History → Export (CSV)', 'Horas: elige en la vista previa la zona horaria configurada en TradingView (Nueva York por defecto)'], how: 'Cómo exportar', tv: ['Account Reports → Performance', 'Elige la cuenta y las fechas', 'Download report (CSV)'],
      rt: ['File → Orders History, elige la cuenta y el día', 'En Completed Orders, clic derecho en los encabezados: añade Account, Status, Buy/Sell, Symbol, Qty Filled, Avg Fill Price, Update Time, Commission', 'Exporta en CSV (un día por archivo)'], tx: ['Pestaña Trades abajo en TopstepX', 'Haz clic en EXPORT (abajo a la derecha)', 'Las horas están en UTC: Sweep las convierte a la hora de Nueva York'] },
  };
  if (typeof render !== 'function') return;
  const appRender = render;
  render = function () {
    const out = appRender.apply(this, arguments);
    try {
      if (route().v === 'import') {
        const main = document.getElementById('main'), x = T[LANG] || T.en;
        const fmt = [...main.querySelectorAll('.f')].find((f) => /Tradovate/.test(f.textContent) && f.querySelector('div'));
        if (fmt && !fmt.dataset.ux) { fmt.dataset.ux = 1; fmt.querySelector('div').textContent = x.fmt; fmt.setAttribute('data-noi18n', ''); }
        const help = [...main.querySelectorAll('h3')].find((h) => /Tradovate/.test(h.textContent));
        if (help && !help.dataset.ux) {
          help.dataset.ux = 1;
          const box = help.parentElement; box.setAttribute('data-noi18n', '');
          const ol = (a) => `<ol class="muted" style="margin:0 0 14px;padding-left:18px;line-height:1.7">${a.map((s) => `<li>${esc(s)}</li>`).join('')}</ol>`;
          box.innerHTML = `<h3 style="margin-bottom:10px">${x.how}</h3><b>Tradovate</b>${ol(x.tv)}<b>Rithmic R|Trader Pro</b>${ol(x.rt)}<b>TopstepX</b>${ol(x.tx)}<b>TradingView</b>${ol(x.tw)}`;
        }
      }
    } catch (e) { /* never blocks */ }
    return out;
  };
})();

/* ───────────── 18. Import page: the last English labels ───────────── */
(function () {
  if (typeof render !== 'function') return;
  const R = [
    [/^Preview$/, () => ({ fr: 'Aperçu', es: 'Vista previa' })],
    [/^Import (\d+) trades?$/, (m) => ({ fr: `Importer ${m[1]} trade${m[1] === '1' ? '' : 's'}`, es: `Importar ${m[1]} operación${m[1] === '1' ? '' : 'es'}` })],
    [/^(\d+) new · (\d+) already imported ·\s*$/, (m) => ({ fr: `${m[1]} nouveau${m[1] === '1' ? '' : 'x'} · ${m[2]} déjà importé${m[2] === '1' ? '' : 's'} · `, es: `${m[1]} nueva${m[1] === '1' ? '' : 's'} · ${m[2]} ya importada${m[2] === '1' ? '' : 's'} · ` })],
    [/^Already imported$/, () => ({ fr: 'Déjà importé', es: 'Ya importada' })],
    [/^This file is not a Tradovate Performance report/, () => ({ fr: 'Ce fichier n’est ni un rapport Performance de Tradovate, ni un export Completed Orders de Rithmic R|Trader Pro, ni un export Trades de TopstepX, ni un export Order History de TradingView.', es: 'Este archivo no es un informe Performance de Tradovate, ni una exportación Completed Orders de Rithmic R|Trader Pro, ni una exportación Trades de TopstepX, ni una exportación Order History de TradingView.' })],
    [/^No filled round trip found in this TradingView export/, () => ({ fr: 'Aucun aller-retour exécuté dans cet export TradingView (exporte « Order History » avec les colonnes Fill Price, Status et Closing Time).', es: 'Ninguna operación completa en esta exportación de TradingView (exporta « Order History » con las columnas Fill Price, Status y Closing Time).' })],
    [/^No closed trades found in this TopstepX export\.$/, () => ({ fr: 'Aucun trade fermé dans cet export TopstepX.', es: 'Ninguna operación cerrada en esta exportación de TopstepX.' })],
    [/^No filled round trip found in this Rithmic export/, () => ({ fr: 'Aucun aller-retour exécuté dans cet export Rithmic (vérifie les colonnes de Completed Orders).', es: 'Ninguna operación completa en esta exportación de Rithmic (revisa las columnas de Completed Orders).' })],
  ];
  const appRender = render;
  render = function () {
    const out = appRender.apply(this, arguments);
    try {
      if (route().v === 'import' && (LANG === 'fr' || LANG === 'es')) {
        const w = document.createTreeWalker(document.getElementById('main'), NodeFilter.SHOW_TEXT); let n;
        while ((n = w.nextNode())) { const s = n.textContent; for (const [re, fn] of R) { const m = re.exec(s.trim() === s ? s : s.replace(/^\s+/, '')); if (m) { n.textContent = fn(m)[LANG]; break; } } }
      }
    } catch (e) { /* never blocks */ }
    return out;
  };
})();

/* ───────────── 20. Trade page polish: notes, discipline score, compact header on phones ───────────── */
(function () {
  'use strict';
  // compact header (phone, scrolled): the title sits after the logo and never runs under the icons
  function fitTitle() {
    const t = document.querySelector('aside.side .mtitle'); if (!t) return;
    if (!(window.SW_MQ ? window.SW_MQ.matches : innerWidth <= 860)) { t.style.removeProperty('--mt-max'); return; }
    const foot = document.querySelector('aside.side .foot');
    let edge = innerWidth - 12;
    if (foot) for (const e of foot.children) {
      if (e.classList.contains('gd-hbtn') || e.classList.contains('plan-chip') || !e.offsetWidth) continue;
      edge = Math.min(edge, e.getBoundingClientRect().left);
    }
    t.style.setProperty('--mt-max', Math.max(90, edge - 56) + 'px');
  }
  let fitQ = 0; const fitSoon = () => { if (!fitQ) fitQ = requestAnimationFrame(() => { fitQ = 0; fitTitle(); }); };   // once per frame at most
  addEventListener('resize', fitSoon);
  new MutationObserver(() => { if (document.body.classList.contains('tcollapsed')) fitSoon(); }).observe(document.body, { attributes: true, attributeFilter: ['class'] });

  function polish() {
    const main = document.getElementById('main'); if (!main) return;
    // notes: full width, readable text instead of a narrow monospace column
    main.querySelectorAll('.facts > div').forEach((d) => {
      const k = d.firstElementChild;
      if (!k || d.classList.contains('ux-notes') || !/^(Notes|Note|Notas)$/i.test(k.textContent.trim())) return;
      d.classList.add('ux-notes');
    });
    // long text values (setup names, tags) wrap; short values (dates, prices, times) stay on one line
    main.querySelectorAll('.facts > div:not(.ux-notes) > span:last-child').forEach((v) => v.classList.toggle('ux-long', v.textContent.trim().length > 13));
    // discipline score: hide « mark the rest as Yes » when nothing is left to answer
    main.querySelectorAll('.score').forEach((s) => {
      const m = /(\d+)\s*(?:sur|of|de)\s*(\d+)/.exec(s.textContent);
      const b = s.querySelector('[data-act="all-yes"]');
      s.classList.add('ux-score');
      // « Score de discipline » on one line, « 5 sur 5 répondues » on the next (no stray « · »)
      const lab = s.querySelector('.muted');
      if (lab && !lab.dataset.ux) for (const n of [...lab.childNodes]) if (n.nodeType === 3 && /^\s*·\s*/.test(n.textContent)) {
        lab.dataset.ux = 1; const sm = document.createElement('small'); sm.className = 'ux-score-n'; sm.setAttribute('data-noi18n', '');
        let txt = n.textContent.replace(/^\s*·\s*/, ''); const mm = /(\d+)\s+of\s+(\d+)\s+answered/i.exec(txt);
        if (mm && LANG === 'fr') txt = `${mm[1]} sur ${mm[2]} répondues`; else if (mm && LANG === 'es') txt = `${mm[1]} de ${mm[2]} respondidas`;
        sm.textContent = txt; n.replaceWith(sm);
      }
      if (b) b.hidden = !!(m && m[1] === m[2]);
    });
  }
  if (typeof render !== 'function') return;
  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { polish(); fitSoon(); } catch (e) { /* never blocks */ } return out; };
})();

/* ───────────── 21. Setup: one-tap chips (your own setups first, then the 10 most common) ───────────── */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  const POPULAR = ['Opening Range Breakout', 'Liquidity Sweep', 'Fair Value Gap', 'Break & Retest', 'VWAP Bounce', 'Trend Pullback', 'Order Block', 'Break of Structure', 'Key Level Reversal', 'Gap Fill'];
  const NOSHOT = { fr: 'Aucune capture pour l’instant.', es: 'Aún no hay capturas.' };
  function chips(input) {
    const own = (S.settings && S.settings.setups) || [];
    const used = {}; (S.trades || []).forEach((t) => { if (t.setup && !t.demo) used[t.setup] = (used[t.setup] || 0) + 1; });
    const mine = [...new Set([...own, ...Object.keys(used).sort((a, b) => used[b] - used[a]).slice(0, 4)])];
    const low = new Set(mine.map((x) => x.toLowerCase()));
    const list = [...mine.slice(0, 6), ...POPULAR.filter((p) => !low.has(p.toLowerCase()))];
    const cur = (input.value || '').trim().toLowerCase();
    return `<div class="ux-setups" data-noi18n>${list.map((s, i) => `<button type="button" class="ux-setup ${i < Math.min(mine.length, 6) ? 'mine' : ''} ${cur === s.toLowerCase() ? 'on' : ''}" data-ux-setup="${esc(s)}">${esc(s)}</button>`).join('')}</div>`;
  }
  function paint() {
    const main = document.getElementById('main'); if (!main) return;
    main.querySelectorAll('input[data-bind$="|setup"]').forEach((input) => {
      const label = input.closest('label') || input.parentElement;
      let row = label.nextElementSibling && label.nextElementSibling.classList.contains('ux-setups') ? label.nextElementSibling : null;
      const html = chips(input);
      if (row) { if (row.outerHTML !== html) row.outerHTML = html; } else label.insertAdjacentHTML('afterend', html);
    });
    if (NOSHOT[LANG]) {
      const w = document.createTreeWalker(main, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) if (n.textContent.trim() === 'No screenshots yet.') n.textContent = NOSHOT[LANG];
    }
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-ux-setup]'); if (!b) return;
    const row = b.closest('.ux-setups'), label = row && row.previousElementSibling;
    const input = label && (label.querySelector('input[data-bind$="|setup"]') || (label.matches('input') ? label : null)); if (!input) return;
    input.value = b.dataset.uxSetup === input.value ? '' : b.dataset.uxSetup;   // tap again to clear
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
    row.querySelectorAll('.ux-setup').forEach((x) => x.classList.toggle('on', x === b && !!input.value));
    if (typeof haptic === 'function') try { haptic(6); } catch (x) { /* web */ }
  });
  document.addEventListener('input', (e) => {
    if (!e.target.matches || !e.target.matches('input[data-bind$="|setup"]')) return;
    const label = e.target.closest('label') || e.target.parentElement, row = label && label.nextElementSibling;
    if (row && row.classList.contains('ux-setups')) row.querySelectorAll('.ux-setup').forEach((x) => x.classList.toggle('on', x.dataset.uxSetup.toLowerCase() === e.target.value.trim().toLowerCase()));
  });
  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { paint(); } catch (e) { /* never blocks */ } return out; };
})();

/* ───────────── 23. Final details: last English sentences, Ask Sweep steps aside while scrolling ───────────── */
(function () {
  'use strict';
  const D = {
    'Not enough data yet. The score needs at least 10 trades in the selected period.': { fr: 'Pas encore assez de données. Le score a besoin d’au moins 10 trades sur la période choisie.', es: 'Aún no hay suficientes datos. La puntuación necesita al menos 10 operaciones en el periodo elegido.' },
  };
  if (typeof render === 'function') {
    const appRender = render;
    render = function () {
      const out = appRender.apply(this, arguments);
      try {
        if (LANG === 'fr' || LANG === 'es') {
          const w = document.createTreeWalker(document.getElementById('main'), NodeFilter.SHOW_TEXT); let n;
          while ((n = w.nextNode())) { const k = n.textContent.trim(); if (D[k]) n.textContent = D[k][LANG]; }
        }
      } catch (e) { /* never blocks */ }
      return out;
    };
  }

})();

/* ───────────── decimal fields accept a comma (French/Spanish keyboards): « 30182,75 » becomes « 30182.75 » as you type ─────────────
 * Without this the form read « 30182,75 » as an invalid price: the exit (or the entry) did not count and the trade
 * could not be saved (« The position is still open »). Spaces used as thousands separators are removed too. */
(function () {
  'use strict';
  document.addEventListener('input', (e) => {
    const i = e.target;
    if (!i || i.tagName !== 'INPUT' || i.getAttribute('inputmode') !== 'decimal') return;
    const v = i.value; if (!/[,\s\u00a0\u202f]/.test(v)) return;
    let pos = i.selectionStart;
    const before = v.slice(0, pos == null ? v.length : pos);
    const fix = (s) => s.replace(/[\s\u00a0\u202f]/g, '').replace(/,(?=\d{3}(\D|$))(?=.*[.,]\d)/g, '').replace(/,/g, '.');
    const nv = fix(v); if (nv === v) return;
    i.value = nv;
    if (pos != null) { const p = fix(before).length; try { i.setSelectionRange(p, p); } catch (x) { /* some input types */ } }
  }, true);   // capture: the form reads the clean value
})();

/* ───────────── 18. CSV import: several accounts in one file, fees ─────────────
   Rithmic: each account of the file goes to the Sweep account the trader picks (never merged); the same trade taken on
   several accounts (copy trading) becomes one copy group. Fees: from the file, else the account's commission per
   contract, else a clear « fees not included ». Every imported trade carries its session date (session_date: true). */
(function () {
  'use strict';
  if (typeof impGo !== 'function' || typeof IMP === 'undefined') return;
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = ({ en: { map: 'Accounts in this file', to: 'Sweep account', copy: 'The same trade on several accounts becomes one copy group.', nofee: 'Fees not included: this file has none and the account has no commission per contract (account page). P&L is gross.', ing: 'Importing {n} trades…', done: 'Imported {n} trades' },
    fr: { map: 'Comptes dans ce fichier', to: 'Compte Sweep', copy: 'Un même trade pris sur plusieurs comptes devient un groupe de copie.', nofee: 'Frais non inclus : ce fichier n’en contient pas et le compte n’a pas de commission par contrat (page du compte). Le P&L est brut.', ing: 'Import de {n} trades…', done: '{n} trades importés' },
    es: { map: 'Cuentas en este archivo', to: 'Cuenta de Sweep', copy: 'La misma operación en varias cuentas se vuelve un grupo de copia.', nofee: 'Comisiones no incluidas: el archivo no las trae y la cuenta no tiene comisión por contrato (página de la cuenta). El P&L es bruto.', ing: 'Importando {n} operaciones…', done: '{n} operaciones importadas' } })[L];
  const fileAccts = () => [...new Set((IMP.rows || []).map((r) => r.acct).filter(Boolean))];
  const active = () => (S.accounts || []).filter((a) => a.status !== 'archived' && a.status !== 'closed');
  function guess(fa) {
    const low = String(fa).toLowerCase();
    const hit = active().find((a) => (a.name || '').toLowerCase().includes(low) || (a.ext_id || '').toLowerCase() === low || low.includes((a.name || '').toLowerCase()));
    return hit ? hit.id : null;
  }
  function targetOf(r) {
    if (fileAccts().length > 1) { IMP.map = IMP.map || {}; return IMP.map[r.acct] || guess(r.acct) || null; }
    return IMP.account;
  }
  window.SweepImport = { targetOf, fileAccts };
  impGo = async function () {
    const rows = IMP.rows || []; if (!rows.length) return;
    const multi = fileAccts().length > 1;
    const have = new Map();
    (S.trades || []).forEach((t) => { if (t.import_key) { if (!have.has(t.account_id)) have.set(t.account_id, new Set()); have.get(t.account_id).add(t.import_key); } });
    const out = [], bySig = new Map();
    for (const r of rows) {
      const acc = targetOf(r); if (!acc) continue;
      if (have.get(acc) && have.get(acc).has(r.key)) continue;
      const a = typeof acct === 'function' ? acct(acc) : null;
      let fees = r.fees_c || 0, auto = false;
      if (!fees && a && a.fee_rt_c > 0 && r.qty > 0) { fees = Math.round(a.fee_rt_c * r.qty); auto = true; }
      const doc = { id: uid(), account_id: acc, instrument: r.inst, date: r.date, session_date: true, entry_time: r.entry_time, exit_time: r.exit_time,
        session: typeof sessionFor === 'function' ? sessionFor(r.entry_time) : '', direction: r.dir, contracts: r.qty, entry: r.entry, exit: r.exit, pnl_c: r.pnl_c, pnl_manual: true,
        import_key: r.key, duration_s: r.duration_s, discipline: {}, emo: {}, review: {}, tags: [], shots: [] };
      if (fees) { doc.fees_c = fees; if (auto) doc.fees_auto = true; }
      if (r.unknown) doc.pnl_check = true;
      out.push(doc);
      if (multi) { const sig = [String(r.entryKey || '').slice(0, 12), r.inst, r.dir].join('|'); if (!bySig.has(sig)) bySig.set(sig, []); bySig.get(sig).push(doc); }
    }
    if (multi) bySig.forEach((g) => { if (new Set(g.map((d) => d.account_id)).size > 1) { const cg = uid(); g.forEach((d) => { d.copy_group = cg; }); } });
    if (!out.length) return;
    toast(T.ing.replace('{n}', out.length), { ms: 60000 });
    try { await bulkPut('trades', out); toast(T.done.replace('{n}', out.length)); IMP.rows = null; IMP.file = ''; IMP.map = null; location.hash = '#trades'; }
    catch (err) { toast(typeof saveErr === 'function' ? saveErr(err) : String(err)); }
    render();
  };
  function paint() {
    if (!/^#import/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main || !IMP.rows || !IMP.rows.length) return;
    const fas = fileAccts();
    let box = main.querySelector('.ux-imap');
    if (fas.length > 1) {
      IMP.map = IMP.map || {};
      const opts = (sel) => `<option value="">—</option>` + active().map((a) => `<option value="${esc(a.id)}" ${a.id === sel ? 'selected' : ''}>${esc(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</option>`).join('');
      const html = `<div class="surface ux-imap" data-noi18n><b>${T.map}</b><p class="muted">${T.copy}</p>${fas.map((fa) => { const sel = IMP.map[fa] || guess(fa) || ''; IMP.map[fa] = sel; return `<label class="f"><span>${esc(fa)} → ${T.to}</span><select data-imap="${esc(fa)}" aria-label="${esc(fa)} → ${T.to}">${opts(sel)}</select></label>`; }).join('')}</div>`;
      if (!box) { const drop = main.querySelector('#drop'); const host = drop && drop.closest('.surface'); if (host) host.insertAdjacentHTML('afterend', html); }
      else if (box.outerHTML !== html && !box.contains(document.activeElement)) box.outerHTML = html;
    } else if (box) box.remove();
    // fees: none in the file and none on the account → say so above the preview
    let warn = main.querySelector('.ux-inofee');
    const noFee = IMP.rows.some((r) => !r.fees_c && !((acct(targetOf(r)) || {}).fee_rt_c > 0));
    let unk = main.querySelector('.ux-iunk'); const nU = IMP.rows.filter((r) => r.unknown).length;
    const UNK = ({ en: '{n} trade(s) on a symbol Sweep does not know: imported with P&L $0 — type their P&L on each trade.', fr: '{n} trade(s) sur un symbole que Sweep ne connaît pas : importé(s) avec un P&L de 0 $ — saisis leur P&L sur chaque trade.', es: '{n} operación(es) en un símbolo que Sweep no conoce: importada(s) con P&L de 0 $ — escribe su P&L en cada operación.' })[L];
    if (nU && !unk) { const h = [...main.querySelectorAll('.sec-h')].find((x) => x.querySelector('h2')); if (h) h.insertAdjacentHTML('afterend', `<p class="ux-inofee ux-iunk" data-noi18n>${UNK.replace('{n}', nU)}</p>`); } else if (!nU && unk) unk.remove();
    if (noFee && !warn) { const h = [...main.querySelectorAll('.sec-h')].find((x) => x.querySelector('h2')); if (h) h.insertAdjacentHTML('afterend', `<p class="ux-inofee" data-noi18n>${T.nofee}</p>`); }
    else if (!noFee && warn) warn.remove();
  }
  document.addEventListener('change', (e) => { const s2 = e.target.closest && e.target.closest('[data-imap]'); if (!s2) return; IMP.map = IMP.map || {}; IMP.map[s2.dataset.imap] = s2.value; render(); });
  if (typeof render === 'function') { const r0 = render; render = function () { const o = r0.apply(this, arguments); try { paint(); } catch (err) { /* never blocks */ } return o; }; }
})();

/* a trade on a symbol Sweep does not know (no point value): the P&L is typed, never computed as NQ */
(function () {
  'use strict';
  if (typeof render !== 'function' || typeof instOf !== 'function') return;
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const M = { en: 'Sweep does not know this symbol ({s}): its P&L is not computed — type it in the trade.', fr: 'Sweep ne connaît pas ce symbole ({s}) : son P&L n’est pas calculé — saisis-le dans le trade.', es: 'Sweep no conoce este símbolo ({s}): su P&L no se calcula — escríbelo en la operación.' }[L];
  function paint() {
    const m = /^#trade\/([^/]+)/.exec(location.hash || ''); const main = document.getElementById('main'); if (!main) return;
    let el = main.querySelector('.ux-unk');
    const t = m && typeof getDoc === 'function' ? getDoc('trades', decodeURIComponent(m[1])) : null;
    const show = t && (t.pnl_check || (instOf(t.instrument).unknown && !t.pnl_manual));
    if (!show) { if (el) el.remove(); return; }
    if (!el) { const back = main.querySelector(':scope > .row') || main.firstElementChild; if (back) back.insertAdjacentHTML('afterend', `<p class="ux-inofee ux-unk" role="note" data-noi18n>${M.replace('{s}', t.instrument || '?')}</p>`); }
  }
  const r0 = render; render = function () { const o = r0.apply(this, arguments); try { paint(); } catch (e) { /* never blocks */ } return o; };
})();

/* payouts / expenses: a row opens on Enter or Space too (it is a button now, like trades and accounts) */
(function () {
  'use strict';
  document.addEventListener('keydown', (e) => {
    const r = e.target && e.target.matches && e.target.matches('li.pz-open') ? e.target : null;
    if (!r || (e.key !== 'Enter' && e.key !== ' ')) return;
    e.preventDefault(); r.click();
  });
})();

/* TradingView import: the time zone of the file (TradingView writes the times in the zone set in TradingView) */
(function () {
  'use strict';
  if (typeof render !== 'function' || !window.SweepImportTV) return;
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const T = { en: ['Times in this TradingView file', 'New York (ET)', 'My time zone', 'UTC'], fr: ['Heures de ce fichier TradingView', 'New York (HE)', 'Mon fuseau', 'UTC'], es: ['Horas de este archivo de TradingView', 'Nueva York (ET)', 'Mi zona horaria', 'UTC'] }[L] || ['Times in this TradingView file', 'New York (ET)', 'My time zone', 'UTC'];
  const mine = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'; } catch (e) { return 'UTC'; } })();
  function paint() {
    if (!/^#import/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main) return;
    let box = main.querySelector('.ux-itz');
    if (!(window.SweepImportTV.active() && typeof IMP !== 'undefined' && IMP.rows)) { if (box) box.remove(); return; }
    const opts = [['America/New_York', T[1]], ...(mine !== 'America/New_York' && mine !== 'America/Toronto' && mine !== 'UTC' ? [[mine, T[2] + ' (' + mine + ')']] : []), ['UTC', T[3]]];
    const cur = window.SweepImportTV.tz;
    const html = `<label class="f ux-itz" data-noi18n><span>${T[0]}</span><select data-itz aria-label="${T[0]}">${opts.map(([v, l]) => `<option value="${v}" ${v === cur ? 'selected' : ''}>${l}</option>`).join('')}</select></label>`;
    if (!box) { const h = [...main.querySelectorAll('.sec-h')].find((x) => x.querySelector('h2')); if (h) h.insertAdjacentHTML('afterend', html); }
  }
  document.addEventListener('change', (e) => {
    const s2 = e.target.closest && e.target.closest('[data-itz]'); if (!s2) return;
    window.SweepImportTV.tz = s2.value;
    try { const r = window.SweepImportTV.reparse(); if (r) { IMP.rows = r; IMP.err = ''; } } catch (err) { IMP.err = err.message; }
    const b = document.querySelector('#main .ux-itz'); if (b) b.remove();
    render();
  });
  const r0 = render; render = function () { const o = r0.apply(this, arguments); try { paint(); } catch (err) { /* never blocks */ } return o; };
})();

/* ───────────── 24. Money: performance · progress · real money, never mixed ─────────────
 * One shared calculation (moneyOf) used by every screen, so the numbers are the same everywhere.
 *  1. Performance (skill): P&L of the trades, every phase. Not money. A copied trade counts once (its first copy).
 *  2. Progress (prop): evaluation = distance to the target; funded = simulated profit + « withdrawable now ».
 *  3. Real money: net payouts received + realized P&L of Live and Personal accounts − expenses. The only « earned ».
 * money_type: eval / funded (simulated) · live / personal (real). Payouts: gross_c, split_pct, fees_c, net_c, status. */
(function () {
  'use strict';
  if (typeof S === 'undefined') return;
  const TYPES = ['eval', 'funded', 'live', 'personal'];
  const SIMT = { eval: 1, funded: 1 };
  /** the account's money type: stored, else deduced (rules / phase); null = « to classify » */
  function moneyTypeOf(a) {
    if (!a) return null;
    if (TYPES.includes(a.money_type)) return a.money_type;
    if (a.phase === 'eval' || a.phase === 'funded' || a.phase === 'live') return a.phase;
    if (a.phase === 'personal') return 'personal';
    const r = a.rules || {};
    if (r.target_c) return 'eval';
    if (r.payout_win_days || r.payout_min_c || r.payout_max_c || r.payout_min_bal_c || r.payout_trade_days) return 'funded';
    if (!a.firm_id && !a.preset) return 'personal';
    return null;
  }
  const isSim = (t) => !!SIMT[t];
  const pState = (p) => (p.status === 'paid' ? 'paid' : (p.status === 'rejected' || p.status === 'denied') ? 'denied' : 'pending');
  const pGross = (p) => (p.gross_c != null ? p.gross_c : p.amount_c || 0);
  const pNet = (p) => (p.net_c != null ? p.net_c : p.amount_c || 0);
  const pPaidOn = (p) => p.paid_on || p.payment_date || p.approval_date || p.request_date || '';
  const pAskedOn = (p) => p.request_date || p.paid_on || p.payment_date || '';
  const inP = (d, from, to) => !!d && (!from || d >= from) && (!to || d <= to);
  const net = (t) => (t.pnl_c || 0) - (t.fees_c || 0);
  const ended = (a) => a && (a.status === 'archived' || a.status === 'closed' || a.result === 'passed' || a.result === 'failed' || a.outcome === 'passed' || a.outcome === 'failed');
  const passed = (a) => a && (a.result === 'passed' || a.outcome === 'passed' || (S.accounts || []).some((x) => x.from_eval === a.id));
  const failed = (a) => a && !passed(a) && (a.result === 'failed' || a.outcome === 'failed');

  /** trades of the period, a copy group counted once (its first copy: the earliest created) */
  function perfTrades(list) {
    const out = [], seen = new Map();
    for (const t of list) {
      if (!t.copy_group) { out.push(t); continue; }
      const g = seen.get(t.copy_group);
      if (!g) { seen.set(t.copy_group, t); out.push(t); continue; }
      if ((t.created_at || t.id) < (g.created_at || g.id)) { out[out.indexOf(g)] = t; seen.set(t.copy_group, t); }
    }
    return out;
  }

  /**
   * moneyOf({ from, to, firm, account }) — everything the screens show, from the same numbers.
   * Amounts in cents. Periods are inclusive YYYY-MM-DD ('' = no limit).
   */
  function moneyOf(o = {}) {
    const from = o.from || '', to = o.to || '';
    const acc = (id) => (S.accounts || []).find((a) => a.id === id);
    const mt = o.mtype && o.mtype !== 'all' ? o.mtype : '';
    const keepA = (a) => !!a && (!o.account || a.id === o.account) && (!o.firm || a.firm_id === o.firm) && (!mt || moneyTypeOf(a) === mt);
    const typeOfId = (id) => moneyTypeOf(acc(id));
    // 1. performance
    const all0 = (S.trades || []).filter((t) => inP(t.date, from, to) && keepA(acc(t.account_id)));
    // like Today: the sample trades step aside once the trader has real ones
    const trades = o.realOnly && (S.trades || []).some((t) => !t.demo) ? all0.filter((t) => !t.demo) : all0;
    const perf = { total: 0, byType: { eval: 0, funded: 0, live: 0, personal: 0, unknown: 0 }, n: 0 };
    perfTrades(trades).forEach((t) => { const v = net(t); perf.total += v; perf.n++; perf.byType[typeOfId(t.account_id) || 'unknown'] += v; });
    // per account (each copy counts on its own account)
    const perAcct = {};
    trades.forEach((t) => { perAcct[t.account_id] = (perAcct[t.account_id] || 0) + net(t); });
    // 3. real money
    const P = (S.payouts || []).filter((p) => keepA(acc(p.account_id)) || (!mt && !p.account_id && (!o.firm || p.firm_id === o.firm) && !o.account));
    const paid = P.filter((p) => pState(p) === 'paid' && inP(pPaidOn(p), from, to));
    const pending = P.filter((p) => pState(p) === 'pending');
    const E = (S.expenses || []).filter((e) => inP(e.date, from, to) && (!o.account || e.account_id === o.account) && (!o.firm || (e.firm_id || (acc(e.account_id) || {}).firm_id) === o.firm) && (!mt || (e.account_id && moneyTypeOf(acc(e.account_id)) === mt)));
    const realPnl = trades.filter((t) => { const ty = typeOfId(t.account_id); return ty === 'live' || ty === 'personal'; }).reduce((s, t) => s + net(t), 0);
    const payoutsNet = paid.reduce((s, p) => s + pNet(p), 0), expenses = E.reduce((s, e) => s + (e.amount_c || 0), 0);
    const real = { payouts: payoutsNet, live: realPnl, expenses, net: payoutsNet + realPnl - expenses,
      pending: pending.reduce((s, p) => s + pNet(p), 0), nPending: pending.length, nPaid: paid.length };
    const roiProp = expenses > 0 ? (payoutsNet - expenses) / expenses : null;
    // 2. progress, per account
    const accounts = (S.accounts || []).filter(keepA).map((a) => {
      const ty = moneyTypeOf(a); let st = null; try { st = typeof acctState === 'function' ? acctState(a) : null; } catch (e) { st = null; }
      const ps = ty === 'funded' && window.SweepPayout && SweepPayout.status ? SweepPayout.status(a) : null;
      const r = { id: a.id, type: ty, sim: isSim(ty), name: a.name, firm_id: a.firm_id, ended: ended(a), passed: passed(a), failed: failed(a), breached: !!(st && st.breached) };
      if (ty === 'eval') { const tg = (a.rules || {}).target_c || 0, n0 = st ? st.net : 0; r.target = tg; r.net = n0; r.pct = tg ? Math.max(0, Math.min(1, n0 / tg)) : null; }
      if (ty === 'funded') { r.profit = st ? st.net : 0; r.withdrawable = ps && ps.avail != null ? Math.max(0, ps.avail) : 0; r.ready = !!(ps && ps.ready); }
      if (ty === 'live' || ty === 'personal') r.pnl = perAcct[a.id] || 0;
      return r;
    });
    const withdrawable = accounts.filter((x) => x.type === 'funded' && !x.ended).reduce((s, x) => s + (x.withdrawable || 0), 0);
    // indicators
    const evals = (S.accounts || []).filter((a) => keepA(a) && moneyTypeOf(a) === 'eval');
    const nPassed = evals.filter(passed).length, nFailed = evals.filter((a) => failed(a) || (!passed(a) && ended(a) && a.outcome !== 'other')).length;
    const funded = (S.accounts || []).filter((a) => keepA(a) && moneyTypeOf(a) === 'funded');
    const COST = { evaluation: 1, reset: 1, subscription: 1, activation: 1 };
    const costSpend = E.filter((e) => COST[e.category]).reduce((s, e) => s + (e.amount_c || 0), 0);
    const firstPaid = funded.map((f) => {
      const ps = (S.payouts || []).filter((p) => p.account_id === f.id && pState(p) === 'paid').map(pPaidOn).filter(Boolean).sort()[0];
      const src = f.from_eval ? acc(f.from_eval) : null, bought = (src && src.created_on) || f.created_on;
      return ps && bought ? Math.max(0, Math.round((new Date(ps) - new Date(bought)) / 864e5)) : null;
    }).filter((x) => x != null);
    const ind = {
      passRate: nPassed + nFailed ? nPassed / (nPassed + nFailed) : null, nPassed, nFailed,
      costPerFunded: funded.length ? Math.round(costSpend / funded.length) : null, nFunded: funded.length,
      daysToFirstPayout: firstPaid.length ? Math.round(firstPaid.reduce((s, x) => s + x, 0) / firstPaid.length) : null,
      payoutPerFunded: funded.length ? Math.round(payoutsNet / funded.length) : null,
    };
    // by firm (prop: payouts and expenses; live P&L is not part of the prop ROI)
    const firms = {};
    const F0 = (id) => (firms[id || ''] = firms[id || ''] || { firm_id: id || '', spent: 0, received: 0, bought: 0, passed: 0, failed: 0, paid: 0 });
    E.forEach((e) => { F0(e.firm_id || (acc(e.account_id) || {}).firm_id).spent += e.amount_c || 0; });
    paid.forEach((p) => { F0(p.firm_id || (acc(p.account_id) || {}).firm_id).received += pNet(p); });
    evals.forEach((a) => { const f = F0(a.firm_id); f.bought++; if (passed(a)) f.passed++; else if (failed(a)) f.failed++; });
    funded.forEach((a) => { if ((S.payouts || []).some((p) => p.account_id === a.id && pState(p) === 'paid')) F0(a.firm_id).paid++; });
    const byFirm = Object.values(firms).filter((f) => f.spent || f.received || f.bought).map((f) => Object.assign(f, { net: f.received - f.spent, roi: f.spent > 0 ? (f.received - f.spent) / f.spent : null }));
    // by month (real in: payouts + live/personal P&L; out: expenses)
    const months = {};
    const M = (d) => (months[d.slice(0, 7)] = months[d.slice(0, 7)] || { month: d.slice(0, 7), inflow: 0, expenses: 0 });
    paid.forEach((p) => { const d = pPaidOn(p); if (d) M(d).inflow += pNet(p); });
    trades.forEach((t) => { const ty = typeOfId(t.account_id); if (ty === 'live' || ty === 'personal') M(t.date).inflow += net(t); });
    E.forEach((e) => { if (e.date) M(e.date).expenses += e.amount_c || 0; });
    return { from, to, perf, real, roiProp, accounts, withdrawable, ind, byFirm, monthly: Object.values(months).sort((a, b) => a.month.localeCompare(b.month)), payouts: P, expenses: E, trades };
  }
  /** period → [from, to] */
  function periodOf(k, custom) {
    const t = typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10);
    const y = t.slice(0, 4), m = +t.slice(5, 7);
    if (k === 'month') return [t.slice(0, 8) + '01', t];
    if (k === 'quarter') { const q = Math.floor((m - 1) / 3) * 3 + 1; return [`${y}-${String(q).padStart(2, '0')}-01`, t]; }
    if (k === 'year') return [`${y}-01-01`, t];
    if (k === 'custom' && custom) return [custom.from || '', custom.to || ''];
    return ['', ''];
  }
  window.SweepMoney = { moneyOf, moneyTypeOf, periodOf, pNet, pGross, pState, pPaidOn, isSim, perfTrades, TYPES };
  window.moneyOf = moneyOf; window.moneyTypeOf = moneyTypeOf;
})();

/* ───────────── 25. « My money » (replaces Payouts & expenses, same page #payouts) ─────────────
 * Period · net real money (net payouts + live/personal P&L − expenses) · monthly chart · indicators · by firm ·
 * payouts (gross, split, fees, net) · expenses (category, account, monthly) · yearly CSV export. */
(function () {
  'use strict';
  if (typeof S === 'undefined' || !window.SweepMoney) return;
  const M = window.SweepMoney;
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const X = ({
    en: { title: 'My money', real: 'Real', sim: 'Simulated', netReal: 'Net real money', payNet: 'Net payouts received', livePnl: '+ Live and personal P&L (realized)', exp: '− Expenses', eq: '= Net real money',
      roi: 'Prop ROI (net payouts − expenses) / expenses', pend: 'Pending: {a} requested (not counted)', month: 'Month', quarter: 'Quarter', year: 'Year', all: 'All', dates: 'Dates', from: 'From', to: 'To',
      byMonth: 'By month', inflow: 'Real money in', outflow: 'Expenses', ind: 'Indicators', passRate: 'Evaluations passed', passSub: '{a} passed / {b} finished', cost: 'Cost to get a funded account', costSub: '{a} / {b} funded',
      delay: 'Purchase → first payout', days: '{n} d', avg: 'Average', payAvg: 'Average payout per funded account', netRecv: 'net received', byFirm: 'By firm', firm: 'Firm', spent: 'Spent', recv: 'Received', net: 'Net', roiC: 'ROI',
      counts: 'Bought · passed · failed · paid', liveNote: 'Live and personal P&L counts in net real money, not in the prop ROI.', payouts: 'Payouts', expenses: 'Expenses', add: '+ Add', noP: 'No payouts yet.', noE: 'No expenses yet.',
      gross: 'gross {a}', split: 'split {a} %', fees: 'fees {a}', paid: 'Paid', requested: 'Requested', denied: 'Denied', pendingS: 'Pending', export: 'Export (CSV)', monthly: 'monthly', refund: 'refund',
      cats: { evaluation: 'Evaluation', reset: 'Reset', activation: 'Activation', subscription: 'Subscription', data: 'Data', platform: 'Platform', other: 'Other' },
      f: { status: 'Status', account: 'Account', date: 'Date', gross: 'Gross requested ($)', split: 'Split (%)', fees: 'Transfer / processing fees ($)', net: 'Net received ($)', save: 'Save', addP: 'Add payout', addE: 'Add expense', cancel: 'Cancel', del: 'Delete',
        amount: 'Amount ($)', amountH: 'A refund: a negative amount.', firm: 'Prop firm', acc: 'Account (optional)', rec: 'Repeat every month (stops when the account is passed, failed or closed)', cat: 'Category', none: '—', needAcc: 'Choose an account.', needAmt: 'Enter an amount.' },
      csv: ['date', 'type', 'firm', 'account', 'category', 'gross', 'fees', 'net'], payoutT: 'payout', expenseT: 'expense', liveT: 'live P&L' },
    fr: { title: 'Mon argent', real: 'Réel', sim: 'Simulé', netReal: 'Net réel', payNet: 'Payouts nets reçus', livePnl: '+ P&L live et perso (réalisé)', exp: '− Dépenses', eq: '= Net réel',
      roi: 'ROI prop (payouts nets − dépenses) / dépenses', pend: 'En attente : {a} demandés (non comptés)', month: 'Mois', quarter: 'Trimestre', year: 'Année', all: 'Tout', dates: 'Dates', from: 'Du', to: 'Au',
      byMonth: 'Par mois', inflow: 'Entrées réelles', outflow: 'Dépenses', ind: 'Indicateurs', passRate: 'Réussite des évaluations', passSub: '{a} réussie(s) / {b} terminée(s)', cost: 'Coût pour un financé', costSub: '{a} / {b} financé(s)',
      delay: 'Achat → 1er payout', days: '{n} j', avg: 'moyenne', payAvg: 'Payout moyen par financé', netRecv: 'net reçu', byFirm: 'Par firme', firm: 'Firme', spent: 'Dépensé', recv: 'Reçu', net: 'Net', roiC: 'ROI',
      counts: 'Achetés · réussis · échoués · ayant payé', liveNote: 'Le P&L live et perso compte dans le net réel, pas dans le ROI prop.', payouts: 'Payouts', expenses: 'Dépenses', add: '+ Ajouter', noP: 'Aucun payout pour l’instant.', noE: 'Aucune dépense pour l’instant.',
      gross: 'brut {a}', split: 'split {a} %', fees: 'frais {a}', paid: 'Payé', requested: 'Demandé', denied: 'Refusé', pendingS: 'En attente', export: 'Exporter (CSV)', monthly: 'mensuel', refund: 'remboursement',
      cats: { evaluation: 'Évaluation', reset: 'Reset', activation: 'Activation', subscription: 'Abonnement', data: 'Données', platform: 'Plateforme', other: 'Autre' },
      f: { status: 'Statut', account: 'Compte', date: 'Date', gross: 'Brut demandé ($)', split: 'Split (%)', fees: 'Frais de virement / traitement ($)', net: 'Net reçu ($)', save: 'Enregistrer', addP: 'Ajouter le payout', addE: 'Ajouter la dépense', cancel: 'Annuler', del: 'Supprimer',
        amount: 'Montant ($)', amountH: 'Un remboursement : un montant négatif.', firm: 'Prop firm', acc: 'Compte (facultatif)', rec: 'Chaque mois (s’arrête quand le compte est réussi, échoué ou fermé)', cat: 'Catégorie', none: '—', needAcc: 'Choisis un compte.', needAmt: 'Entre un montant.' },
      csv: ['date', 'type', 'firme', 'compte', 'categorie', 'brut', 'frais', 'net'], payoutT: 'payout', expenseT: 'dépense', liveT: 'P&L live' },
    es: { title: 'Mi dinero', real: 'Real', sim: 'Simulado', netReal: 'Neto real', payNet: 'Payouts netos recibidos', livePnl: '+ P&L live y personal (realizado)', exp: '− Gastos', eq: '= Neto real',
      roi: 'ROI prop (payouts netos − gastos) / gastos', pend: 'Pendiente: {a} solicitados (no contados)', month: 'Mes', quarter: 'Trimestre', year: 'Año', all: 'Todo', dates: 'Fechas', from: 'Desde', to: 'Hasta',
      byMonth: 'Por mes', inflow: 'Entradas reales', outflow: 'Gastos', ind: 'Indicadores', passRate: 'Evaluaciones superadas', passSub: '{a} superada(s) / {b} terminada(s)', cost: 'Coste por cuenta financiada', costSub: '{a} / {b} financiada(s)',
      delay: 'Compra → 1er payout', days: '{n} d', avg: 'media', payAvg: 'Payout medio por financiada', netRecv: 'neto recibido', byFirm: 'Por firma', firm: 'Firma', spent: 'Gastado', recv: 'Recibido', net: 'Neto', roiC: 'ROI',
      counts: 'Compradas · superadas · fallidas · con payout', liveNote: 'El P&L live y personal cuenta en el neto real, no en el ROI prop.', payouts: 'Payouts', expenses: 'Gastos', add: '+ Añadir', noP: 'Aún no hay payouts.', noE: 'Aún no hay gastos.',
      gross: 'bruto {a}', split: 'split {a} %', fees: 'comisiones {a}', paid: 'Pagado', requested: 'Solicitado', denied: 'Rechazado', pendingS: 'Pendiente', export: 'Exportar (CSV)', monthly: 'mensual', refund: 'reembolso',
      cats: { evaluation: 'Evaluación', reset: 'Reset', activation: 'Activación', subscription: 'Suscripción', data: 'Datos', platform: 'Plataforma', other: 'Otro' },
      f: { status: 'Estado', account: 'Cuenta', date: 'Fecha', gross: 'Bruto solicitado ($)', split: 'Split (%)', fees: 'Comisiones de transferencia ($)', net: 'Neto recibido ($)', save: 'Guardar', addP: 'Añadir payout', addE: 'Añadir gasto', cancel: 'Cancelar', del: 'Eliminar',
        amount: 'Importe ($)', amountH: 'Un reembolso: un importe negativo.', firm: 'Prop firm', acc: 'Cuenta (opcional)', rec: 'Cada mes (se detiene cuando la cuenta se supera, falla o se cierra)', cat: 'Categoría', none: '—', needAcc: 'Elige una cuenta.', needAmt: 'Escribe un importe.' },
      csv: ['fecha', 'tipo', 'firma', 'cuenta', 'categoria', 'bruto', 'comisiones', 'neto'], payoutT: 'payout', expenseT: 'gasto', liveT: 'P&L live' },
  })[L] || null;
  const x = X || {};
  const esc2 = (v) => String(v == null ? '' : v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const mU = (c) => (typeof moneyU === 'function' ? moneyU(c) : '$' + (c / 100).toFixed(2));
  const mS = (c) => (typeof money === 'function' ? money(c, { dec: Math.abs(c) % 100 ? 2 : 0 }) : mU(c));
  const fd = (d) => (d && typeof fdate === 'function' ? fdate(d) : d || '');
  const firmName = (id) => ((S.firms || []).find((f) => f.id === id) || {}).name || '—';
  const accName = (id) => (typeof acctLabel === 'function' && id ? acctLabel(id) : '');
  const TAG = (k) => `<span class="mny-tag ${k}">${k === 'real' ? x.real : x.sim}</span>`;
  const CATS = ['evaluation', 'reset', 'activation', 'subscription', 'data', 'platform', 'other'];
  const P = () => (U.mper = U.mper || 'month');

  /* ── forms ── */
  const accOpts = (sel, any) => (any ? `<option value="">${x.f.none}</option>` : '') + (S.accounts || []).filter((a) => a.status !== 'archived' || a.id === sel).map((a) => `<option value="${esc2(a.id)}" ${a.id === sel ? 'selected' : ''}>${esc2(accName(a.id))}</option>`).join('');
  const splitOf = (aid) => { const a = (S.accounts || []).find((y) => y.id === aid); const v = a && a.rules && a.rules.payout_split_pct; return v > 0 ? v : 100; };
  payoutForm = function (e = {}) {
    const st = e.id ? M.pState(e) : 'paid', aid = e.account_id || (F.account !== 'all' ? F.account : '') || ((S.accounts || []).find((a) => a.status !== 'archived' && M.moneyTypeOf(a) === 'funded') || (S.accounts || [])[0] || {}).id;
    const gross = M.pGross(e), split = e.split_pct != null ? e.split_pct : splitOf(aid), fees = e.fees_c || 0, net0 = e.id ? M.pNet(e) : '';
    return `<form class="pz-form mny-form" data-form="payout" data-id="${esc2(e.id || '')}" autocomplete="off" data-noi18n>
      <div class="seg pz-st" role="radiogroup" aria-label="${x.f.status}">${[['paid', x.paid], ['requested', x.requested], ['denied', x.denied]].map(([v, l]) => `<label class="${st === v || (v === 'requested' && st === 'pending') ? 'on' : ''}"><input type="radio" name="status" value="${v}" ${st === v || (v === 'requested' && st === 'pending') ? 'checked' : ''}>${l}</label>`).join('')}</div>
      <div class="fgrid mny-g">
        <label class="f"><span>${x.f.account}</span><select name="account" required>${accOpts(aid)}</select></label>
        <label class="f"><span>${x.f.date}</span><input type="date" name="date" value="${esc2((st === 'paid' ? M.pPaidOn(e) : e.request_date) || (typeof todayStr === 'function' ? todayStr() : ''))}"></label>
        <label class="f"><span>${x.f.gross}</span><input name="gross" inputmode="decimal" value="${e.id ? gross / 100 : ''}" placeholder="$" required></label>
        <label class="f"><span>${x.f.split}</span><input name="split" inputmode="decimal" value="${split}"></label>
        <label class="f"><span>${x.f.fees}</span><input name="fees" inputmode="decimal" value="${fees ? fees / 100 : ''}" placeholder="0"></label>
        <label class="f"><span>${x.f.net}</span><input name="net" inputmode="decimal" value="${net0 !== '' ? net0 / 100 : ''}" data-auto="${e.id && e.net_c != null && e.net_c !== Math.round(gross * split / 100) - fees ? '0' : '1'}"></label>
      </div>
      <div class="row pz-acts"><button class="btn primary" type="submit">${e.id ? x.f.save : x.f.addP}</button><button class="btn" type="button" data-mny="cancel">${x.f.cancel}</button>${e.id ? `<button class="btn danger" type="button" data-act="del-payout" data-id="${esc2(e.id)}">${x.f.del}</button>` : ''}</div></form>`;
  };
  // net = gross × split − fees, until the trader types the net themselves
  document.addEventListener('input', (ev) => {
    const f = ev.target.closest && ev.target.closest('form.mny-form[data-form="payout"]'); if (!f) return;
    const n = f.elements.net; if (ev.target === n) { n.dataset.auto = '0'; return; }
    if (n.dataset.auto === '0') return;
    const v = (k) => parseFloat(String(f.elements[k].value).replace(',', '.')) || 0;
    const g = v('gross'), sp = f.elements.split.value === '' ? 100 : v('split'), fe = v('fees');
    n.value = g ? (Math.round((g * sp / 100 - fe) * 100) / 100).toString() : '';
  });
  document.addEventListener('change', (ev) => {
    const s = ev.target.closest && ev.target.closest('form.mny-form[data-form="payout"] select[name=account]'); if (!s) return;
    const f = s.form; f.elements.split.value = splitOf(s.value); f.elements.gross.dispatchEvent(new Event('input', { bubbles: true }));
  });
  submitPayout = function (form) {
    if (typeof billGate === 'function' && typeof billPayoutTotal === 'function' && !billGate('payouts', 'payouts', { payoutTotal: billPayoutTotal() })) return;
    const d = new FormData(form), id = form.dataset.id || uid(), a = (S.accounts || []).find((y) => y.id === d.get('account'));
    const num = (k) => { const s = String(d.get(k) || '').replace(/[$\s]/g, '').replace(',', '.'); return s === '' ? null : parseFloat(s); };
    if (!a) { toast(x.f.needAcc); return; }
    const g = num('gross'); if (g == null || !(g > 0)) { toast(x.f.needAmt); return; }
    const sp = num('split') == null ? 100 : num('split'), fe = num('fees') || 0, n0 = num('net');
    const gross_c = Math.round(g * 100), fees_c = Math.round(fe * 100), net_c = n0 != null ? Math.round(n0 * 100) : Math.round(gross_c * sp / 100) - fees_c;
    const prev = getDoc('payouts', id) || {}, st = d.get('status'), date = d.get('date') || todayStr();
    const doc = { ...prev, id, account_id: a.id, firm_id: a.firm_id, gross_c, split_pct: sp, fees_c, net_c, amount_c: gross_c, status: st === 'denied' ? 'rejected' : st === 'requested' ? (['approved', 'planned'].includes(prev.status) ? prev.status : 'requested') : 'paid' };
    if (doc.status === 'paid') { doc.paid_on = date; doc.payment_date = date; doc.request_date = prev.request_date || date; doc.approval_date = prev.approval_date || date; }
    else { doc.request_date = prev.request_date && prev.status !== 'paid' ? prev.request_date : date; if (prev.status === 'paid') { doc.payment_date = ''; doc.paid_on = ''; } }
    put('payouts', doc);
    U.editP = null; U.addP = false; render();
    if (doc.status === 'paid' && prev.status !== 'paid' && typeof openShare === 'function') setTimeout(() => openShare('payout', id), 400);
  };
  expenseForm = function (e = {}) {
    const cat = e.category || 'evaluation', aid = e.account_id || '';
    return `<form class="pz-form mny-form" data-form="expense" data-id="${esc2(e.id || '')}" autocomplete="off" data-noi18n>
      <div class="seg pz-st pz-cats" role="radiogroup" aria-label="${x.f.cat}">${CATS.map((v) => `<label class="${cat === v ? 'on' : ''}"><input type="radio" name="category" value="${v}" ${cat === v ? 'checked' : ''}>${x.cats[v]}</label>`).join('')}</div>
      <div class="fgrid mny-g">
        <label class="f"><span>${x.f.amount}</span><input name="amount" inputmode="decimal" value="${e.amount_c != null ? e.amount_c / 100 : ''}" placeholder="$" required><small class="muted">${x.f.amountH}</small></label>
        <label class="f"><span>${x.f.firm}</span><select name="firm"><option value="">${x.f.none}</option>${(S.firms || []).map((f) => `<option value="${esc2(f.id)}" ${f.id === e.firm_id ? 'selected' : ''}>${esc2(f.name)}</option>`).join('')}</select></label>
        <label class="f"><span>${x.f.acc}</span><select name="account">${accOpts(aid, true)}</select></label>
        <label class="f"><span>${x.f.date}</span><input type="date" name="date" value="${esc2(e.date || (typeof todayStr === 'function' ? todayStr() : ''))}" required></label>
      </div>
      ${e.recurring_of ? '' : `<label class="mny-rec"><input type="checkbox" name="recurring" ${e.recurring === 'monthly' || (!e.id && cat === 'subscription') ? 'checked' : ''}> ${x.f.rec}</label>`}
      <div class="row pz-acts"><button class="btn primary" type="submit">${e.id ? x.f.save : x.f.addE}</button><button class="btn" type="button" data-mny="cancel">${x.f.cancel}</button>${e.id ? `<button class="btn danger" type="button" data-act="del-expense" data-id="${esc2(e.id)}">${x.f.del}</button>` : ''}</div></form>`;
  };
  document.addEventListener('change', (ev) => {
    const r = ev.target.closest && ev.target.closest('form.mny-form .pz-st input[type=radio]'); if (!r) return;
    r.closest('.pz-st').querySelectorAll('label').forEach((l) => l.classList.toggle('on', l.contains(r)));
    const rec = r.form && r.form.elements.recurring; if (rec && r.name === 'category' && !r.form.dataset.id) rec.checked = r.value === 'subscription';
  });
  submitExpense = function (form) {
    if (typeof billGate === 'function' && typeof billPayoutTotal === 'function' && !billGate('payouts', 'payouts', { payoutTotal: billPayoutTotal() })) return;
    const d = new FormData(form), id = form.dataset.id || uid();
    const s0 = String(d.get('amount') || '').replace(/[$\s]/g, '').replace(',', '.'), v = parseFloat(s0);
    if (!s0 || isNaN(v) || v === 0) { toast(x.f.needAmt); return; }
    const acc = d.get('account') || '', fid = d.get('firm') || (acc ? ((S.accounts || []).find((a) => a.id === acc) || {}).firm_id : '') || '', prev = getDoc('expenses', id) || {};
    const doc = { ...prev, id, date: d.get('date') || todayStr(), firm_id: fid, account_id: acc, category: d.get('category') || 'other', amount_c: Math.round(v * 100) };
    if (!prev.recurring_of) { if (d.get('recurring')) doc.recurring = 'monthly'; else delete doc.recurring; }
    put('expenses', doc);
    U.editE = null; U.addE = false; render();
  };

  /* ── page ── */
  function svgChart(rows) {
    if (!rows.length) return `<p class="muted">—</p>`;
    const mx = Math.max(1, ...rows.map((r) => Math.max(r.inflow, r.expenses, 0)));
    const w = 100 / rows.length;
    const lab = (m) => { const d = new Date(m + '-15T12:00:00'); return d.toLocaleDateString(L === 'en' ? 'en-US' : L === 'es' ? 'es-ES' : 'fr-CA', { month: 'short' }).replace('.', ''); };
    return `<div class="mny-chart" role="img" aria-label="${x.byMonth}">${rows.map((r) => `<div class="mny-m" style="width:${w}%"><div class="mny-bars"><i class="in" style="height:${Math.max(1, Math.max(0, r.inflow) / mx * 100)}%" title="${esc2(x.inflow + ' ' + mU(r.inflow))}"></i><i class="out" style="height:${Math.max(1, Math.max(0, r.expenses) / mx * 100)}%" title="${esc2(x.outflow + ' ' + mU(r.expenses))}"></i></div><small>${lab(r.month)}</small></div>`).join('')}</div>
      <div class="mny-leg"><span><i class="in"></i>${x.inflow}</span><span><i class="out"></i>${x.outflow}</span></div>`;
  }
  const pct = (v) => (v == null ? '—' : Math.round(v * 100) + ' %');
  /** what the page shows: period, account type, firm, account — the CSV uses exactly the same (9, 18.1) */
  const viewOpts = () => { const [from, to] = M.periodOf(P(), U.mcustom); return { from, to, firm: F.firm !== 'all' ? F.firm : '', account: F.account !== 'all' ? F.account : '', mtype: (typeof U !== 'undefined' && U.mtype) || 'all' }; };
  function view() {
    const per = P(), o = viewOpts(), from = o.from, to = o.to;
    const m = M.moneyOf(o);
    const r = m.real, i = m.ind;
    const seg = [['month', x.month], ['quarter', x.quarter], ['year', x.year], ['all', x.all], ['custom', x.dates]].map(([k, l]) => `<button type="button" class="${per === k ? 'on' : ''}" data-mny-per="${k}">${l}</button>`).join('');
    const custom = per === 'custom' ? `<div class="mny-dates"><label class="f"><span>${x.from}</span><input type="date" data-mny-d="from" value="${esc2((U.mcustom || {}).from || '')}"></label><label class="f"><span>${x.to}</span><input type="date" data-mny-d="to" value="${esc2((U.mcustom || {}).to || '')}"></label></div>` : '';
    const payRows = m.payouts.slice().sort((a, b) => (M.pPaidOn(b) || '').localeCompare(M.pPaidOn(a) || '')).map((p) => U.editP === p.id ? `<li class="pz-edit">${payoutForm(p)}</li>` : (() => {
      const st = M.pState(p), lab = st === 'paid' ? x.paid : st === 'denied' ? x.denied : x.requested;
      return `<li class="pz-row pz-open mny-row" data-act="edit-payout" data-id="${esc2(p.id)}" role="button" tabindex="0" aria-label="${esc2(accName(p.account_id) + ' · ' + mU(M.pNet(p)))}">
        <div class="pz-main"><b>${esc2(accName(p.account_id))}</b><small>${fd(M.pPaidOn(p))} · ${x.gross.replace('{a}', mU(M.pGross(p)))} · ${x.split.replace('{a}', p.split_pct != null ? p.split_pct : 100)} · ${x.fees.replace('{a}', mU(p.fees_c || 0))}</small></div>
        <div class="pz-right"><span class="pz-amt-v ${st === 'paid' ? 'pos' : 'mny-dim'}">${st === 'denied' ? '<s>' + mU(M.pNet(p)) + '</s>' : mU(M.pNet(p))}</span><span class="pz-pill ${st}">${lab}</span></div>
        ${st === 'paid' && !p.estimated && typeof shareBtn === 'function' ? `<div class="pz-acts2">${shareBtn('payout', p.id, ({ fr: 'Partager', es: 'Compartir' })[L] || 'Share', 'link sh-link')}</div>` : st === 'pending' ? `<div class="pz-acts2"><button class="link pz-paid" data-pz-paid="${esc2(p.id)}">${({ fr: 'Marquer payé', es: 'Marcar pagado' })[L] || 'Mark as paid'}</button></div>` : ''}</li>`; })()).join('');
    const expRows = m.expenses.slice().sort((a, b) => (b.date || '').localeCompare(a.date || '')).map((e) => U.editE === e.id ? `<li class="pz-edit">${expenseForm(e)}</li>` : `
      <li class="pz-row pz-open mny-row" data-act="edit-expense" data-id="${esc2(e.id)}" role="button" tabindex="0" aria-label="${esc2((x.cats[e.category] || e.category) + ' · ' + mU(e.amount_c || 0))}">
        <div class="pz-main"><b>${esc2(x.cats[e.category] || x.cats.other)}${e.firm_id || (e.account_id && ((S.accounts || []).find((a) => a.id === e.account_id) || {}).firm_id) ? ' · ' + esc2(firmName(e.firm_id || ((S.accounts || []).find((a) => a.id === e.account_id) || {}).firm_id)) : ''}</b><small>${fd(e.date)}${e.account_id ? ' · ' + esc2(accName(e.account_id)) : ''}${e.recurring === 'monthly' || e.recurring_of ? ' · ' + x.monthly : ''}${(e.amount_c || 0) < 0 ? ' · ' + x.refund : ''}</small></div>
        <div class="pz-right"><span class="pz-amt-v ${(e.amount_c || 0) < 0 ? 'pos' : 'neg'}">${mS(-(e.amount_c || 0))}</span></div></li>`).join('');
    const firmRows = m.byFirm.map((f) => `<tr><td>${esc2(firmName(f.firm_id))}</td><td>${mU(f.spent)}</td><td class="${f.received ? 'pos' : ''}">${mU(f.received)}</td><td class="${f.net >= 0 ? 'pos' : 'neg'}">${mS(f.net)}</td><td>${pct(f.roi)}</td><td>${f.bought} · ${f.passed} · ${f.failed} · ${f.paid}</td></tr>`).join('');
    return `<div class="mny" data-noi18n>
      ${window.SweepTypeSeg ? `<div class="mny-typerow">${SweepTypeSeg()}</div>` : ''}
      <div class="mny-top"><div class="mny-tsw"><span class="mny-tsl">${({ fr: 'Période', es: 'Período' })[L] || 'Period'}</span><div class="seg mny-per" role="group">${seg}</div></div><button type="button" class="btn" data-mny="csv">${x.export}</button></div>${custom}
      <section class="surface mny-net"><div class="mny-h"><b>${x.netReal}</b>${TAG('real')}</div>
        <div class="mny-wf"><div><span>${x.payNet}</span><b class="${r.payouts ? 'pos' : ''}">${mS(r.payouts)}</b></div><div><span>${x.livePnl}</span><b class="${r.live >= 0 ? 'pos' : 'neg'}">${mS(r.live)}</b></div><div><span>${x.exp}</span><b class="neg">${mS(-r.expenses)}</b></div><div class="tot ${r.net >= 0 ? 'up' : 'down'}"><span>${x.eq}</span><b class="${r.net >= 0 ? 'pos' : 'neg'}">${mS(r.net)}</b></div></div>
        <p class="mny-note">${x.roi} : <b>${pct(m.roiProp)}</b>${r.nPending ? ' · ' + x.pend.replace('{a}', mU(r.pending)) : ''}</p></section>
      <div class="mny-cols"><div>
        <section class="surface"><div class="mny-h"><b>${x.byMonth}</b></div>${svgChart(m.monthly)}</section>
        <section class="surface"><div class="mny-h"><b>${x.ind}</b></div><div class="mny-ind">
          <div><span>${x.passRate}</span><b>${pct(i.passRate)}</b><small>${x.passSub.replace('{a}', i.nPassed).replace('{b}', i.nPassed + i.nFailed)}</small></div>
          <div><span>${x.cost}</span><b>${i.costPerFunded == null ? '—' : mU(i.costPerFunded)}</b><small>${i.nFunded ? x.costSub.replace('{a}', mU(i.costPerFunded * i.nFunded)).replace('{b}', i.nFunded) : '—'}</small></div>
          <div><span>${x.delay}</span><b>${i.daysToFirstPayout == null ? '—' : x.days.replace('{n}', i.daysToFirstPayout)}</b><small>${x.avg}</small></div>
          <div><span>${x.payAvg}</span><b>${i.payoutPerFunded == null ? '—' : mU(i.payoutPerFunded)}</b><small>${x.netRecv}</small></div></div></section>
      </div><div>
        <section class="surface"><div class="mny-h"><b>${x.byFirm}</b></div>${firmRows ? `<div class="scroll-x"><table class="tbl mny-tbl"><thead><tr><th>${x.firm}</th><th>${x.spent}</th><th>${x.recv}</th><th>${x.net}</th><th>${x.roiC}</th><th>${x.counts}</th></tr></thead><tbody>${firmRows}</tbody></table></div>` : '<p class="muted">—</p>'}
          ${r.live ? `<p class="mny-note">${x.liveNote}</p>` : ''}</section>
        <section class="surface"><div class="mny-h"><b>${x.payouts}</b><button type="button" class="link" data-mny="addP">${x.add}</button></div>
          ${U.addP ? `<div class="pz-add">${payoutForm()}</div>` : ''}${payRows ? `<ul class="pz-list">${payRows}</ul>` : `<p class="muted">${x.noP}</p>`}</section>
        <section class="surface"><div class="mny-h"><b>${x.expenses}</b><button type="button" class="link" data-mny="addE">${x.add}</button></div>
          ${U.addE ? `<div class="pz-add">${expenseForm()}</div>` : ''}${expRows ? `<ul class="pz-list">${expRows}</ul>` : `<p class="muted">${x.noE}</p>`}</section>
      </div></div></div>`;
  }
  vPayouts = function () {
    if (!S.accounts.length) return onboarding();
    return (typeof filterBar === 'function' ? filterBar({ period: false, session: false, dir: false }) : '') + `<div data-lock="payouts" data-feature="payouts" class="bill-lock">${view()}</div>`;
  };
  const EST = () => ({ en: 'estimated', fr: 'estimé', es: 'estimado' })[L] || 'estimated';   // catch-up entries (section 29)
  /** the CSV of what is on screen: the active period and every active filter (account type, firm, account) */
  function csvView() {
    const o = viewOpts(), m = M.moneyOf(o), rows = [x.csv], today = typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10);
    const inP = (d) => !!d && (!o.from || d >= o.from) && (!o.to || d <= o.to);
    const q = (v) => `"${String(v == null ? '' : v).replace(/"/g, '""')}"`, c = (v) => (v / 100).toFixed(2);
    const firmOf = (aid) => ((S.accounts || []).find((a) => a.id === aid) || {}).firm_id;
    m.payouts.filter((p) => M.pState(p) === 'paid' && inP(M.pPaidOn(p))).forEach((p) => rows.push([M.pPaidOn(p), x.payoutT, firmName(p.firm_id), accName(p.account_id), p.estimated ? EST() : '', c(M.pGross(p)), c(p.fees_c || 0), c(M.pNet(p))]));
    m.expenses.forEach((e) => rows.push([e.date, x.expenseT, firmName(e.firm_id || firmOf(e.account_id)), accName(e.account_id), (x.cats[e.category] || e.category) + (e.estimated ? ' (' + EST() + ')' : ''), c(e.amount_c || 0), '0.00', c(-(e.amount_c || 0))]));
    (m.trades || []).filter((t) => ['live', 'personal'].includes(M.moneyTypeOf((S.accounts || []).find((a) => a.id === t.account_id)))).forEach((t) => rows.push([t.date, x.liveT, firmName(firmOf(t.account_id)), accName(t.account_id), '', c(t.pnl_c || 0), c(t.fees_c || 0), c((t.pnl_c || 0) - (t.fees_c || 0))]));
    const head = rows.shift(); rows.sort((a, b) => String(a[0]).localeCompare(String(b[0])));
    const blob = new Blob(['\ufeff' + [head, ...rows].map((r) => r.map(q).join(',')).join('\n')], { type: 'text/csv' });
    const tag = [o.mtype !== 'all' ? o.mtype : '', o.firm ? firmName(o.firm) : '', o.account ? accName(o.account) : ''].filter(Boolean).join('-').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = `sweep-${x.title.toLowerCase().replace(/\s+/g, '-')}-${o.from || 'start'}_${o.to || today}${tag ? '-' + tag : ''}.csv`;
    document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    return rows.length;
  }
  const csvYear = csvView;   // (older name, kept for the tests and the CSV menu)
  window.SweepMoney.csvYear = csvYear;
  document.addEventListener('click', (ev) => {
    const b = ev.target.closest && ev.target.closest('[data-mny-per], [data-mny]'); if (!b) return;
    if (b.dataset.mnyPer) { U.mper = b.dataset.mnyPer; if (typeof saveU === 'function') saveU(); render(); return; }
    const k = b.dataset.mny;
    if (k === 'csv') csvView();
    else if (k === 'addP') { U.addP = !U.addP; U.editP = null; render(); }
    else if (k === 'addE') { U.addE = !U.addE; U.editE = null; render(); }
    else if (k === 'cancel') { U.addP = U.addE = false; U.editP = U.editE = null; render(); }
  });
  document.addEventListener('change', (ev) => { const i = ev.target.closest && ev.target.closest('[data-mny-d]'); if (!i) return; U.mcustom = Object.assign({}, U.mcustom || {}, { [i.dataset.mnyD]: i.value }); if (typeof saveU === 'function') saveU(); render(); });
  // #money → the same page
  const toPay = () => { if (/^#money\b/.test(location.hash || '')) history.replaceState(null, '', '#payouts'); };
  toPay(); addEventListener('hashchange', toPay, true);
})();

/* ───────────── 26. Accounts list grouped by money type (E2): Live · Funded · Evaluations · Personal ─────────────
 * evaluation → progress to the target (never below 0) · funded → simulated profit + withdrawable now ·
 * live / personal → real P&L of the month. No all-accounts total. */
(function () {
  'use strict';
  if (typeof acctTable !== 'function' || !window.SweepMoney) return;
  const M = window.SweepMoney, L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const X = ({ en: { live: 'Live', funded: 'Funded', eval: 'Evaluations', personal: 'Personal', none: 'To classify', real: 'Real', sim: 'Simulated', of: '{a} of {b}', profit: 'Simulated profit', wd: 'withdrawable {a}', month: 'Real P&L this month', passed: 'Passed', failed: 'Failed', acc: 'Account', firm: 'Firm', bal: 'Balance', prog: 'Progress' },
    fr: { live: 'Live', funded: 'Financés', eval: 'Évaluations', personal: 'Perso', none: 'À classer', real: 'Réel', sim: 'Simulé', of: '{a} sur {b}', profit: 'Profit simulé', wd: 'retirable {a}', month: 'P&L réel du mois', passed: 'Réussie', failed: 'Échouée', acc: 'Compte', firm: 'Firme', bal: 'Solde', prog: 'Progression' },
    es: { live: 'Live', funded: 'Financiadas', eval: 'Evaluaciones', personal: 'Personal', none: 'Por clasificar', real: 'Real', sim: 'Simulado', of: '{a} de {b}', profit: 'Beneficio simulado', wd: 'retirable {a}', month: 'P&L real del mes', passed: 'Superada', failed: 'Fallida', acc: 'Cuenta', firm: 'Firma', bal: 'Saldo', prog: 'Progreso' } })[L] || null;
  const x = X || {};
  const orig = acctTable;
  acctTable = function (list, opts) {
    if (!list || !list.length) return orig(list, opts);
    const [a, b] = M.periodOf('month'), mm = M.moneyOf({ from: a, to: b }), info = Object.fromEntries(mm.accounts.map((r) => [r.id, r]));
    const all = M.moneyOf({}), allInfo = Object.fromEntries(all.accounts.map((r) => [r.id, r]));
    const esc2 = (v) => String(v == null ? '' : v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
    const fm = (c) => (typeof money === 'function' ? money(c, { dec: Math.abs(c) % 100 ? 2 : 0 }) : (c / 100).toFixed(2));
    const fu = (c) => (typeof moneyU === 'function' ? moneyU(c) : (c / 100).toFixed(2));
    const groups = [['live', 'real'], ['funded', 'sim'], ['eval', 'sim'], ['personal', 'real'], ['none', '']];
    const sorted = typeof acctSortBreachLast === 'function' ? acctSortBreachLast(list) : list;
    const cell = (acc) => {
      const r = allInfo[acc.id] || {}, ty = M.moneyTypeOf(acc);
      if (ty === 'eval') {
        if (r.passed) return `<span class="pill ok">${x.passed}</span>`;
        if (r.failed) return `<span class="pill ko">${x.failed}</span>`;
        if (!r.target) return '—';
        return `<div class="mny-prog"><span>${x.of.replace('{a}', fu(Math.max(0, r.net))).replace('{b}', fu(r.target))} · <b>${Math.round((r.pct || 0) * 100)} %</b></span><i><s style="width:${Math.round((r.pct || 0) * 100)}%"></s></i></div>`;
      }
      if (ty === 'funded') return `<span class="mny-dim">${fm(r.profit || 0)}</span> <span class="mny-tag sim">${x.sim}</span><small class="mny-sub">${x.wd.replace('{a}', fu(r.withdrawable || 0))}</small>`;
      if (ty === 'live' || ty === 'personal') { const p = (info[acc.id] || {}).pnl || 0; return `<span class="${p >= 0 ? 'pos' : 'neg'}">${fm(p)}</span> <span class="mny-tag real">${x.real}</span><small class="mny-sub">${x.month}</small>`; }
      return '—';
    };
    return `<div class="mny-accs scroll-x" data-noi18n>${groups.map(([g, k]) => {
      const rows = sorted.filter((acc) => (M.moneyTypeOf(acc) || 'none') === g); if (!rows.length) return '';
      return `<div class="mny-grp"><h3>${x[g]}${k ? ` <span class="mny-tag ${k}">${k === 'real' ? x.real : x.sim}</span>` : ''}</h3><div class="scroll-x"><table class="tbl acct-tbl mny-acc-tbl"><thead><tr><th>${x.acc}</th><th>${x.firm}</th><th class="num">${x.bal}</th><th>${x.prog}</th></tr></thead><tbody>${rows.map((acc) => {
        const f = typeof firm === 'function' ? firm(acc.firm_id) : null; let bal = 0; try { bal = typeof acctBalance === 'function' ? acctBalance(acc) : 0; } catch (e) { bal = 0; }
        return `<tr data-href="#account/${esc2(acc.id)}" tabindex="0"><td>${esc2(acc.name)}${typeof billBadge === 'function' ? billBadge(acc.id) : ''}${typeof acctLine === 'function' ? acctLine(acc) : ''}</td><td class="muted">${esc2(f ? f.name : '—')}</td><td class="num">${fu(bal)}</td><td>${cell(acc)}</td></tr>`;
      }).join('')}</tbody></table></div></div>`;
    }).join('')}</div>`;
  };
})();

/* ───────────── 27. Stats by account type (E4) + « Classify your accounts » (R1) ───────────── */
(function () {
  'use strict';
  if (typeof S === 'undefined' || !window.SweepMoney) return;
  const M = window.SweepMoney, L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const X = ({ en: { label: 'Account type', all: 'All', eval: 'Evaluations', funded: 'Funded', live: 'Live', personal: 'Personal', perf: 'Performance', sim: 'Simulated', real: 'Real', note: 'Skill, not money earned: real money is in My money.', split: 'Simulated {a} · Real {b}',
      clsT: 'Classify your accounts', clsS: 'Sweep keeps simulated money (evaluations, funded accounts) apart from real money (live, personal). One tap per account:', clsDone: 'Done', clsLater: 'Later', t_eval: 'Evaluation', t_funded: 'Funded', t_live: 'Live', t_personal: 'Personal' },
    fr: { label: 'Type de compte', all: 'Tout', eval: 'Évaluations', funded: 'Financés', live: 'Live', personal: 'Perso', perf: 'Performance', sim: 'Simulé', real: 'Réel', note: 'Ton habileté, pas de l’argent gagné : l’argent réel est dans Mon argent.', split: 'Simulé {a} · Réel {b}',
      clsT: 'Classe tes comptes', clsS: 'Sweep sépare l’argent simulé (évaluations, financés) de l’argent réel (live, perso). Une touche par compte :', clsDone: 'Terminé', clsLater: 'Plus tard', t_eval: 'Évaluation', t_funded: 'Financé', t_live: 'Live', t_personal: 'Perso' },
    es: { label: 'Tipo de cuenta', all: 'Todo', eval: 'Evaluaciones', funded: 'Financiadas', live: 'Live', personal: 'Personal', perf: 'Rendimiento', sim: 'Simulado', real: 'Real', note: 'Tu habilidad, no dinero ganado: el dinero real está en Mi dinero.', split: 'Simulado {a} · Real {b}',
      clsT: 'Clasifica tus cuentas', clsS: 'Sweep separa el dinero simulado (evaluaciones, financiadas) del dinero real (live, personal). Un toque por cuenta:', clsDone: 'Listo', clsLater: 'Más tarde', t_eval: 'Evaluación', t_funded: 'Financiada', t_live: 'Live', t_personal: 'Personal' } })[L] || null;
  const x = X || {};
  // the account-type filter belongs to Stats only: Trades, Calendar and Journal always show every trade
  /* one account-type filter for the whole journey (Today, Trades, Stats, My money), always shown where it applies */
  // 14 · the Calendar shows the same selector, and follows it (the Journal still shows every trade)
  if (typeof acctOK === 'function') { const ok0 = acctOK; acctOK = function (t) { if (!ok0.apply(this, arguments)) return false; return !/^#calendar/.test(location.hash || '') || !t || !t.account_id || window.mtypeKeep(t); }; }
  window.mtypeKeep = (t) => { const k = typeof U !== 'undefined' && U.mtype; if (!k || k === 'all') return true; return M.moneyTypeOf((S.accounts || []).find((y) => y.id === t.account_id)) === k; };
  window.SweepTypeSeg = () => { const k = (typeof U !== 'undefined' && U.mtype) || 'all'; return `<div class="mny-tsw" data-noi18n><span class="mny-tsl">${x.label}</span><div class="seg mny-tseg" role="group" aria-label="${x.label}">${['all', 'eval', 'funded', 'live', 'personal'].map((v) => `<button type="button" class="${k === v ? 'on' : ''}" data-mtype="${v}" aria-pressed="${k === v}">${x[v]}</button>`).join('')}</div></div>`; };
  window.SweepTypeTag = () => { const k = (typeof U !== 'undefined' && U.mtype) || 'all'; return k === 'all' ? `<span class="mny-tag perf">${x.perf}</span>` : `<span class="mny-tag ${k === 'live' || k === 'personal' ? 'real' : 'sim'}">${k === 'live' || k === 'personal' ? x.real : x.sim}</span>`; };
  // Trades and Stats lists follow it (they show the selector); Calendar and Journal always show every trade
  window.mtypeOK = (t) => { if (!/^#(analytics|progress|trades|calendar)/.test(location.hash || '')) return true; const k = typeof U !== 'undefined' && U.mtype; if (!k || k === 'all') return true; const a = (S.accounts || []).find((y) => y.id === t.account_id); return M.moneyTypeOf(a) === k; };
  function paint() {
    if (!/^#(analytics|progress|trades|calendar)/.test(location.hash || '')) return;
    const main = document.getElementById('main'); if (!main) return;
    const k = (typeof U !== 'undefined' && U.mtype) || 'all';
    let seg = main.querySelector('.mny-tsw');
    const html = window.SweepTypeSeg();
    // copy trading: a group of copies counts once — its first copy, or per contract when the sizes differ between accounts
    const cm = (typeof U !== 'undefined' && U.copyMode) || 'once';
    const CM = { en: ['Copies: once', 'per contract'], fr: ['Copies : une fois', 'par contrat'], es: ['Copias: una vez', 'por contrato'] }[L] || ['Copies: once', 'per contract'];
    const html2 = /^#(trades|calendar)/.test(location.hash || '') ? '' : (S.trades || []).some((t) => t.copy_group) ? `<div class="seg mny-cseg" role="group" data-noi18n><button type="button" class="${cm !== 'contract' ? 'on' : ''}" data-cmode="once">${CM[0]}</button><button type="button" class="${cm === 'contract' ? 'on' : ''}" data-cmode="contract">${CM[1]}</button></div>` : '';
    if (!seg) { const fb = main.querySelector('.fbars, .mfb'); if (fb) fb.insertAdjacentHTML('afterend', html + html2); else main.insertAdjacentHTML('afterbegin', html + html2); }
    // the P&L card says what it is: performance, simulated or real
    const kp = [...main.querySelectorAll('.kpis > div, .ik')].find((d) => /P&L/.test((d.querySelector('.lbl') || {}).textContent || ''));
    if (kp && !kp.querySelector('.mny-ptag')) {
      const lab = kp.querySelector('.lbl'); const tag = k === 'all' ? `<span class="mny-tag perf mny-ptag">${x.perf}</span>` : `<span class="mny-tag ${k === 'live' || k === 'personal' ? 'real' : 'sim'} mny-ptag">${k === 'live' || k === 'personal' ? x.real : x.sim}</span>`;
      if (lab) lab.insertAdjacentHTML('beforeend', ' ' + tag);
      if (k === 'all') {
        const [a, b] = typeof periodRange === 'function' ? periodRange() : ['', ''];
        const pf = M.moneyOf({ from: a, to: b, account: F.account !== 'all' ? F.account : '', firm: F.firm !== 'all' ? F.firm : '' }).perf.byType;
        const fm = (c) => (typeof money === 'function' ? money(c, { dec: 0 }) : (c / 100).toFixed(0));
        kp.insertAdjacentHTML('beforeend', `<small class="mny-psplit" data-noi18n>${x.split.replace('{a}', fm(pf.eval + pf.funded)).replace('{b}', fm(pf.live + pf.personal))}</small>`);
      }
    }
  }
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('.mny-cseg [data-cmode]'); if (!b) return; U.copyMode = b.dataset.cmode; if (typeof saveU === 'function') saveU(); render(); });
  document.addEventListener('click', (e) => { const b = e.target.closest && e.target.closest('.mny-tseg [data-mtype]'); if (b) { e.preventDefault(); e.stopPropagation(); } if (!b) return; U.mtype = b.dataset.mtype; if (typeof saveU === 'function') saveU(); render(); });
  // « Classify your accounts »: once, for the accounts Sweep could not classify
  let asked = false;
  function classify() {
    if (asked || typeof S === 'undefined' || S.mode !== 'server' || !S.settings) return;
    // only accounts that existed before money types (an account made today gets its type when it is created)
    const old = (a) => !a.created_at || Date.now() - new Date(a.created_at).getTime() > 6 * 3600e3;
    const todo = (S.accounts || []).filter((a) => a.status !== 'archived' && !M.moneyTypeOf(a) && old(a));
    if (!todo.length || S.settings.money_classified) return;
    if (document.querySelector('#gSheet.open, .evp.open, .nav-dlg.open:not(.mny-cls), .nt-modal, #tkSlide.open')) { setTimeout(classify, 4000); return; }   // never on top of another window
    asked = true;
    const esc2 = (v) => String(v == null ? '' : v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
    const scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim mny-cls open';
    const el = document.createElement('aside'); el.className = 'nav-dlg mny-cls open'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
    el.innerHTML = `<div class="nav-dlg-in"><h2>${x.clsT}</h2><p class="nav-pass-s">${x.clsS}</p>${todo.map((a) => `<div class="mny-cls-r" data-id="${esc2(a.id)}"><b>${esc2(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name)}</b><div class="seg">${M.TYPES.map((t) => `<button type="button" data-cls="${t}">${x['t_' + t]}</button>`).join('')}</div></div>`).join('')}
      <button type="button" class="btn primary nav-am-save" data-cls-done>${x.clsDone}</button></div>`;
    document.body.append(scrim, el);
    const close = () => { editDoc('settings', 'settings', (d) => { d.money_classified = true; }); el.remove(); scrim.remove(); render(); };
    el.addEventListener('click', (e) => {
      const b = e.target.closest('[data-cls]'); if (b) { const id = b.closest('[data-id]').dataset.id; editDoc('accounts', id, (d) => { d.money_type = b.dataset.cls; }); b.parentElement.querySelectorAll('button').forEach((y) => y.classList.toggle('on', y === b)); return; }
      if (e.target.closest('[data-cls-done]')) close();
    });
    scrim.addEventListener('click', close);
  }
  if (typeof render === 'function') { const r0 = render; render = function () { const o = r0.apply(this, arguments); try { paint(); setTimeout(classify, 1200); } catch (e) { /* never blocks */ } return o; }; }
  window.SweepMoney.classify = classify;
})();

/* « The reality of the month » (money/money.php, the 1st of each month) */
(function () {
  'use strict';
  const N = { en: { 'money_month.title': 'The reality of {month}', 'money_month.body': 'Simulated profit ${sim} · money received ${received} · expenses ${expenses} · net real money ${net}.' },
    fr: { 'money_month.title': 'La réalité de {month}', 'money_month.body': 'Profit simulé {sim} $ · argent reçu {received} $ · dépenses {expenses} $ · net réel {net} $.' },
    es: { 'money_month.title': 'La realidad de {month}', 'money_month.body': 'Beneficio simulado {sim} $ · dinero recibido {received} $ · gastos {expenses} $ · neto real {net} $.' } };
  const reg = () => { if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings(N); } catch (e) { /* older module */ } return true; } return false; };
  if (!reg()) setTimeout(reg, 1500);
})();

/* ───────────── 28. Change an account's type (Evaluation · Funded · Live · Personal), in place ─────────────
 * For accounts created before money types, or simply mis-classified: the account keeps its trades, rules, payouts and
 * stats; only what the money means changes (simulated or real). Becoming funded or live with a NEW account (after a passed
 * evaluation, a funded account moved to live) stays the separate path offered on the account. */
(function () {
  'use strict';
  if (typeof S === 'undefined' || !window.SweepMoney) return;
  const M = window.SweepMoney, L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const X = ({ en: { t: 'Account type', s: 'Change it if this account was classified wrong: its trades, rules and stats stay as they are.', eval: 'Evaluation', funded: 'Funded', live: 'Live', personal: 'Personal', done: 'Type changed: {t}. Trades and stats unchanged.', sim: 'simulated money', real: 'real money' },
    fr: { t: 'Type de compte', s: 'Change-le si ce compte est mal classé : ses trades, ses règles et ses stats restent les mêmes.', eval: 'Évaluation', funded: 'Financé', live: 'Live', personal: 'Perso', done: 'Type changé : {t}. Trades et stats inchangés.', sim: 'argent simulé', real: 'argent réel' },
    es: { t: 'Tipo de cuenta', s: 'Cámbialo si esta cuenta está mal clasificada: sus operaciones, reglas y estadísticas no cambian.', eval: 'Evaluación', funded: 'Financiada', live: 'Live', personal: 'Personal', done: 'Tipo cambiado: {t}. Operaciones y estadísticas sin cambios.', sim: 'dinero simulado', real: 'dinero real' } })[L] || null;
  const x = X || { t: 'Account type', s: '', eval: 'Evaluation', funded: 'Funded', live: 'Live', personal: 'Personal', done: 'Type changed: {t}.', sim: 'simulated money', real: 'real money' };
  const esc2 = (v) => String(v == null ? '' : v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  function paint() {
    const m = /^#account\/([^/?]+)/.exec(location.hash || ''); if (!m) return;
    const id = decodeURIComponent(m[1]), a = (S.accounts || []).find((y) => y.id === id); if (!a) return;
    const main = document.getElementById('main'); if (!main) return;
    const nameIn = main.querySelector(`[data-bind="accounts|${id}|name"]`); const card = nameIn && nameIn.closest('.surface'); if (!card) return;
    const cur = M.moneyTypeOf(a) || '';
    let box = card.querySelector('.acc-type');
    const html = `<div class="acc-type" data-noi18n><span class="lbl">${x.t}</span><div class="seg" role="radiogroup" aria-label="${x.t}">${['eval', 'funded', 'live', 'personal'].map((v) => `<button type="button" role="radio" aria-checked="${cur === v}" class="${cur === v ? 'on' : ''}" data-acc-type="${v}" data-id="${esc2(id)}">${x[v]}</button>`).join('')}</div><small class="muted">${x.s} · ${cur ? (M.isSim(cur) ? x.sim : x.real) : ''}</small></div>`;
    if (box) { if (box.dataset.cur !== cur) { box.outerHTML = html; card.querySelector('.acc-type').dataset.cur = cur; } return; }
    card.insertAdjacentHTML('afterbegin', html); card.querySelector('.acc-type').dataset.cur = cur;
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-acc-type]'); if (!b) return;
    const t = b.dataset.accType, id = b.dataset.id;
    // only the type changes (and the phase that goes with it, so the right card shows: objective or payouts) — never the trades, rules or history
    editDoc('accounts', id, (d) => { d.money_type = t; d.phase = t === 'personal' ? 'live' : t; d.type_changed_on = typeof todayStr === 'function' ? todayStr() : ''; });
    if (typeof toast === 'function') toast(x.done.replace('{t}', x[t]));
    if (typeof render === 'function') render();
  });
  if (typeof render === 'function') { const r0 = render; render = function () { const o = r0.apply(this, arguments); try { paint(); } catch (e) { /* never blocks */ } return o; }; }
})();

/* ───────────── 29. Real net from the start: catch-up of past purchases and payouts, then the real net ─────────────
 * New trader: profile → experience → first account → « Account added » (continue / add another) → catch-up:
 *   1. since when (this month · since January · a date)  2. purchases per firm (+/−, prices from the catalogue, editable)
 *   3. net payouts received  4. the real net (spent, received, net, one sentence), from moneyOf: the same number as My money.
 * « Later » on every screen; Today's « My money » card then offers it until done or hidden. Existing traders: offered one day.
 * The entries are normal My money entries marked estimated: true, one per firm and category (ids est-…, a new catch-up
 * replaces them), dated at the start of the period. Nothing is merged with exact purchases: a reminder offers to adjust.
 * State (synced settings): S.settings.realnet = { state: 'done' | 'later' | 'hidden', shown_on }. */
(function () {
  'use strict';
  if (typeof S === 'undefined' || !window.SweepMoney) return;
  const M = window.SweepMoney;
  const L = (typeof LANG !== 'undefined' && LANG) || 'en';
  const X = ({
    en: { added: 'Account added', addedS: 'Add your other accounts now, or continue.', another: '+ Add another account', cont: 'Continue', later: 'I’ll do it later',
      pT: 'Since when do you want to track your money?', pS: 'Sweep works out your real net: money received minus money spent on prop firms.', month: 'This month', year: 'Since January', date: 'A date',
      bT: 'Your purchases since {d}', bS: 'Just the numbers: prices are editable.', eval: 'Evaluations', evalM: 'Months of subscription', reset: 'Resets', activation: 'Activations', price: 'Price per unit', already: 'Already in My money: {a}', each: 'each',
      rT: 'How much did you receive in payouts since {d}?', rS: 'The net amount that reached your bank. Leave empty if nothing.', rL: 'Net payouts received ($)', see: 'See my real net',
      nT: 'Your real net', spent: 'Spent', recv: 'Received', net: 'Real net', pos: 'You’re up {a} since {p}. Sweep will help you stay there.', neg: 'This is your starting point. From today, every dollar is tracked.', go: 'Let’s go',
      sMonth: 'the start of the month', sYear: 'January', est: 'Estimated', invNew: 'Your real net in 1 minute', invOld: 'Complete your history in 1 minute', invS: 'Your past purchases and payouts, without entering them one by one.', hide: 'Hide',
      remind: 'You have an estimate for {f} over this period: adjust it if needed.', adjust: 'Adjust', estF: 'Estimate · {c}', amount: 'Amount ($)', save: 'Save', del: 'Delete', cancel: 'Cancel', back: '‹ Back', saveErr: 'Not saved: check your connection, then try again.' },
    fr: { added: 'Compte ajouté', addedS: 'Ajoute tes autres comptes maintenant, ou continue.', another: '+ Ajouter un autre compte', cont: 'Continuer', later: 'Je le ferai plus tard',
      pT: 'Depuis quand veux-tu suivre ton argent ?', pS: 'Sweep calcule ton vrai net : l’argent reçu moins l’argent dépensé en prop firms.', month: 'Ce mois-ci', year: 'Depuis janvier', date: 'Une date',
      bT: 'Tes achats depuis le {d}', bS: 'Le nombre suffit : les prix sont modifiables.', eval: 'Évaluations', evalM: 'Mois d’abonnement', reset: 'Resets', activation: 'Activations', price: 'Prix à l’unité', already: 'Déjà dans Mon argent : {a}', each: 'l’unité',
      rT: 'Combien as-tu reçu en payouts depuis le {d} ?', rS: 'Le montant net, arrivé sur ton compte. Laisse vide si rien.', rL: 'Payouts nets reçus ($)', see: 'Voir mon vrai net',
      nT: 'Ton vrai net', spent: 'Dépensé', recv: 'Reçu', net: 'Vrai net', pos: 'Tu es rentable de {a} depuis {p}. Sweep va t’aider à le rester.', neg: 'C’est ton point de départ. À partir d’aujourd’hui, chaque dollar est suivi.', go: 'C’est parti',
      sMonth: 'le début du mois', sYear: 'janvier', est: 'Estimé', invNew: 'Ton vrai net en 1 minute', invOld: 'Complète ton historique en 1 minute', invS: 'Tes achats et payouts passés, sans tout entrer un par un.', hide: 'Masquer',
      remind: 'Tu as une estimation pour {f} sur cette période : ajuste-la si besoin.', adjust: 'Ajuster', estF: 'Estimation · {c}', amount: 'Montant ($)', save: 'Enregistrer', del: 'Supprimer', cancel: 'Annuler', back: '‹ Retour', saveErr: 'Non enregistré : vérifie ta connexion, puis réessaie.' },
    es: { added: 'Cuenta añadida', addedS: 'Añade tus otras cuentas ahora, o continúa.', another: '+ Añadir otra cuenta', cont: 'Continuar', later: 'Lo haré más tarde',
      pT: '¿Desde cuándo quieres seguir tu dinero?', pS: 'Sweep calcula tu neto real: el dinero recibido menos el dinero gastado en prop firms.', month: 'Este mes', year: 'Desde enero', date: 'Una fecha',
      bT: 'Tus compras desde el {d}', bS: 'Basta con el número: los precios se pueden cambiar.', eval: 'Evaluaciones', evalM: 'Meses de suscripción', reset: 'Resets', activation: 'Activaciones', price: 'Precio por unidad', already: 'Ya en Mi dinero: {a}', each: 'c/u',
      rT: '¿Cuánto recibiste en payouts desde el {d}?', rS: 'El importe neto que llegó a tu cuenta. Déjalo vacío si nada.', rL: 'Payouts netos recibidos ($)', see: 'Ver mi neto real',
      nT: 'Tu neto real', spent: 'Gastado', recv: 'Recibido', net: 'Neto real', pos: 'Eres rentable en {a} desde {p}. Sweep te ayudará a seguir así.', neg: 'Este es tu punto de partida. Desde hoy, cada dólar queda registrado.', go: 'Vamos',
      sMonth: 'el inicio del mes', sYear: 'enero', est: 'Estimado', invNew: 'Tu neto real en 1 minuto', invOld: 'Completa tu historial en 1 minuto', invS: 'Tus compras y payouts pasados, sin introducirlos uno por uno.', hide: 'Ocultar',
      remind: 'Tienes una estimación para {f} en este periodo: ajústala si hace falta.', adjust: 'Ajustar', estF: 'Estimación · {c}', amount: 'Importe ($)', save: 'Guardar', del: 'Eliminar', cancel: 'Cancelar', back: '‹ Volver', saveErr: 'No guardado: revisa tu conexión y vuelve a intentarlo.' },
  })[L] || null;
  const x = X || {};
  const CATN = ({ en: { evaluation: 'Evaluation', reset: 'Reset', activation: 'Activation' }, fr: { evaluation: 'Évaluation', reset: 'Reset', activation: 'Activation' }, es: { evaluation: 'Evaluación', reset: 'Reset', activation: 'Activación' } })[L] || {};
  const esc2 = (v) => String(v == null ? '' : v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const today = () => (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10));
  const mU = (c) => (typeof moneyU === 'function' ? moneyU(c) : '$' + (c / 100).toFixed(0));
  const fd = (d) => (typeof fdate === 'function' ? fdate(d) : d);
  const num = (v) => { const s = String(v == null ? '' : v).replace(/[$\s\u202f\u00a0]/g, '').replace(',', '.'); const n = parseFloat(s); return s === '' || !isFinite(n) ? null : n; };
  const realAccts = () => (S.accounts || []).filter((a) => !a.demo);
  const firmName = (id) => ((S.firms || []).find((f) => f.id === id) || {}).name || '';
  const stOf = () => (S.settings && S.settings.realnet) || {};
  function setSt(p) {
    if (typeof put !== 'function' || !S.settings) return;
    const s = JSON.parse(JSON.stringify(S.settings)); s.realnet = Object.assign({}, s.realnet || {}, p); put('settings', s);
  }
  // the session's only automatic window: celebrations and the install prompt wait until the real net is shown
  const holdModals = () => { try { sessionStorage.setItem('sw.modal', '1'); } catch (e) { /* private mode */ } };

  /* ── the sheet (one window, one step at a time) ── */
  let el = null, scrim = null, W = null;   // W: the catch-up being filled
  function shell(html) {
    if (!el) {
      scrim = document.createElement('div'); scrim.className = 'nav-dlg-scrim rn-scrim';
      el = document.createElement('aside'); el.className = 'nav-dlg rn'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('data-noi18n', '');
      document.body.append(scrim, el); requestAnimationFrame(() => { scrim.classList.add('open'); el.classList.add('open'); });
    }
    el.innerHTML = `<div class="nav-dlg-in rn-in">${html}</div>`;
    el.scrollTop = 0;
    const f = el.querySelector('h2'); if (f) { f.setAttribute('tabindex', '-1'); f.focus({ preventScroll: true }); }
  }
  function close() {
    if (!el) return; const a = el, b = scrim; el = scrim = null; W = null;
    a.classList.remove('open'); b.classList.remove('open'); setTimeout(() => { a.remove(); b.remove(); }, 260);
    if (typeof render === 'function') render();
  }
  const laterBtn = () => `<button type="button" class="link rn-later" data-rn="later">${x.later}</button>`;

  /* « Account added »: during the first visit, after each account */
  let flow = false;
  function added() {
    holdModals();
    if (!stOf().state) setSt({ state: 'later' });   // a new trader: if he leaves now, Today offers « Your real net in 1 minute »
    const list = realAccts().slice(-12).map((a) => `<li><b>${esc2(a.name || '')}</b><small>${esc2(firmName(a.firm_id))}</small></li>`).join('');
    shell(`<span class="rn-ok" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.2 4.2L19 7"/></svg></span><h2>${x.added}</h2><p class="muted">${x.addedS}</p>
      <ul class="rn-accs">${list}</ul>
      <button type="button" class="btn primary nav-am-save" data-rn="start">${x.cont}</button>
      <button type="button" class="btn nav-pass-later" data-rn="another">${x.another}</button>`);
  }
  /* 1. the period */
  function start() {
    holdModals(); flow = false;
    W = W || { per: 'year', from: '', q: {}, p: {}, payout: '' };
    shell(`<h2>${x.pT}</h2><p class="muted">${x.pS}</p>
      <div class="rn-opts">${[['month', x.month], ['year', x.year], ['date', x.date]].map(([k, l]) => `<button type="button" class="rn-opt ${W.per === k ? 'on' : ''}" data-rn-per="${k}" aria-pressed="${W.per === k}">${l}</button>`).join('')}</div>
      <label class="f rn-date" ${W.per === 'date' ? '' : 'hidden'}><span>${x.date}</span><input type="date" data-rn-from max="${today()}" value="${esc2(W.from || '')}"></label>
      <button type="button" class="btn primary nav-am-save" data-rn="buys">${x.cont}</button>${laterBtn()}`);
  }
  function fromOf() {
    const t = today();
    if (W.per === 'month') return t.slice(0, 8) + '01';
    if (W.per === 'date' && /^\d{4}-\d{2}-\d{2}$/.test(W.from || '') && W.from <= t) return W.from;
    return t.slice(0, 4) + '-01-01';
  }
  /* 2. purchases per firm (the firms of his accounts), prices from the catalogue when it has them */
  function firmsOf() {
    const ids = []; realAccts().forEach((a) => { if (a.firm_id && !ids.includes(a.firm_id) && M.moneyTypeOf(a) !== 'personal') ids.push(a.firm_id); });
    return ids.map((id) => {
      const a = realAccts().find((y) => y.firm_id === id && y.preset) || null;
      const pr = a && window.SweepPresets && SweepPresets.priceOf ? SweepPresets.priceOf(a.preset) : null;
      return { id, name: firmName(id), monthly: !!(pr && pr.eval_period === 'month'), price: { evaluation: pr && pr.eval, reset: pr && pr.reset, activation: pr && pr.activation } };
    });
  }
  const already = (fid, from) => (S.expenses || []).filter((e) => !e.estimated && !e.demo && e.date >= from && e.date <= today() && (e.firm_id || ((S.accounts || []).find((a) => a.id === e.account_id) || {}).firm_id) === fid).reduce((s, e) => s + (e.amount_c || 0), 0);
  async function buys() {
    const firms = firmsOf();
    if (!firms.length) return payouts();
    if (window.SweepPresets && !SweepPresets.ready()) { SweepPresets.load(); for (let i = 0; i < 20 && !SweepPresets.ready(); i++) await new Promise((r) => setTimeout(r, 100)); }
    const F = firmsOf(), from = fromOf();
    const row = (f, cat) => {
      const k = f.id + '|' + cat, q = W.q[k] || 0, p = W.p[k] != null ? W.p[k] : (f.price[cat] != null ? String(f.price[cat]) : '');
      const lab = cat === 'evaluation' ? (f.monthly ? x.evalM : x.eval) : x[cat];
      return `<div class="rn-row"><span class="rn-lab">${lab}</span>
        <span class="rn-step" role="group" aria-label="${esc2(f.name + ' · ' + lab)}"><button type="button" data-rn-q="${esc2(k)}" data-d="-1" aria-label="−" ${q ? '' : 'disabled'}>−</button><output aria-live="polite">${q}</output><button type="button" data-rn-q="${esc2(k)}" data-d="1" aria-label="+">+</button></span>
        <label class="rn-price">$<input inputmode="decimal" data-rn-p="${esc2(k)}" value="${esc2(p)}" placeholder="0" aria-label="${esc2(lab + ' · ' + x.price)}"><small>${x.each}</small></label></div>`;
    };
    shell(`<h2>${x.bT.replace('{d}', esc2(fd(from)))}</h2><p class="muted">${x.bS}</p>
      ${F.map((f) => { const a = already(f.id, from); return `<section class="rn-firm"><div class="rn-firm-h"><b>${esc2(f.name)}</b>${a ? `<small>${x.already.replace('{a}', mU(a))}</small>` : ''}</div>
        ${['evaluation', 'reset', 'activation'].map((c) => row(f, c)).join('')}</section>`; }).join('')}
      <button type="button" class="btn primary nav-am-save" data-rn="payouts">${x.cont}</button>
      <button type="button" class="link rn-back" data-rn="start">${x.back}</button>${laterBtn()}`);
  }
  /* 3. net payouts received over the period */
  function payouts() {
    const from = fromOf();
    shell(`<h2>${x.rT.replace('{d}', esc2(fd(from)))}</h2><p class="muted">${x.rS}</p>
      <label class="f rn-pay"><span>${x.rL}</span><input inputmode="decimal" data-rn-pay value="${esc2(W.payout || '')}" placeholder="0"></label>
      <button type="button" class="btn primary nav-am-save" data-rn="save">${x.see}</button>
      <button type="button" class="link rn-back" data-rn="${firmsOf().length ? 'buys' : 'start'}">${x.back}</button>${laterBtn()}`);
  }
  /* save: one entry per firm and category, then the real net */
  function save() {
    const from = fromOf(), firms = firmsOf();
    const keep = new Set();
    firms.forEach((f) => ['evaluation', 'reset', 'activation'].forEach((cat) => {
      const k = f.id + '|' + cat, q = W.q[k] || 0, pr = num(W.p[k] != null ? W.p[k] : f.price[cat]), id = `est-${f.id}-${cat}`.replace(/[^A-Za-z0-9_.:@+~-]/g, '-').slice(0, 120);
      if (q > 0 && pr != null && pr > 0) { keep.add(id); put('expenses', { id, date: from, firm_id: f.id, account_id: '', category: cat, amount_c: Math.round(q * pr * 100), estimated: true, est_qty: q, est_unit_c: Math.round(pr * 100), est_monthly: cat === 'evaluation' && f.monthly ? true : undefined }); }
    }));
    // an earlier catch-up: its estimates are replaced (never added twice)
    (S.expenses || []).filter((e) => e.estimated && /^est-/.test(e.id) && !keep.has(e.id)).forEach((e) => remove('expenses', e.id));
    const pay = num(W.payout);
    if (pay != null && pay > 0) { const c = Math.round(pay * 100); put('payouts', { id: 'est-payouts', firm_id: '', account_id: '', gross_c: c, split_pct: 100, fees_c: 0, net_c: c, amount_c: c, status: 'paid', paid_on: from, payment_date: from, request_date: from, approval_date: from, estimated: true }); }
    else if ((S.payouts || []).some((p) => p.id === 'est-payouts')) remove('payouts', 'est-payouts');
    setSt({ state: 'done', at: today() });
    showNet(from, W.per);
  }
  /* 4. the real net: moneyOf over the same period, so it is the number My money shows */
  function showNet(from, per) {
    const m = M.moneyOf({ from, to: today() }), r = m.real;
    const since = per === 'month' ? x.sMonth : per === 'year' ? x.sYear : fd(from);
    const fm = (c) => (typeof money === 'function' ? money(c, { dec: 0 }) : mU(c));
    shell(`<h2>${x.nT}</h2><p class="muted">${esc2(per === 'month' ? x.month : per === 'year' ? x.year : fd(from) + ' → ' + fd(today()))}</p>
      <div class="rn-net"><div><span>${x.spent}</span><b class="neg">${fm(-r.expenses)}</b></div><div><span>${x.recv}</span><b class="pos">${fm(r.payouts + r.live)}</b></div>
        <div class="rn-net-t"><span>${x.net} <span class="mny-tag real">${({ en: 'Real', fr: 'Réel', es: 'Real' })[L] || 'Real'}</span></span><b class="${r.net >= 0 ? 'pos' : 'neg'}">${fm(r.net)}</b></div></div>
      <p class="rn-say">${esc2(r.net > 0 ? x.pos.replace('{a}', mU(r.net)).replace('{p}', since) : x.neg)}</p>
      <button type="button" class="btn primary nav-am-save" data-rn="close">${x.go}</button>`);
  }

  /* ── events ── */
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-rn], [data-rn-per], [data-rn-q]'); if (!b) return;
    if (b.dataset.rnPer) { W.per = b.dataset.rnPer; start(); if (W.per === 'date') { const i = el && el.querySelector('[data-rn-from]'); if (i) i.focus(); } return; }
    if (b.dataset.rnQ) { const k = b.dataset.rnQ, v = Math.max(0, Math.min(99, (W.q[k] || 0) + (+b.dataset.d || 0))); W.q[k] = v; const o = b.parentNode.querySelector('output'); if (o) o.textContent = v; const m = b.parentNode.querySelector('[data-d="-1"]'); if (m) m.disabled = !v; return; }
    const a = b.dataset.rn;
    if (a === 'start') start();
    else if (a === 'another') {   // the Accounts page with its add form open, as its own « + » does
      close(); flow = true; location.hash = '#accounts';
      setTimeout(() => { const all = document.querySelectorAll('#main [data-act="acct-add"]'), btn = all[all.length - 1]; if (btn && !document.querySelector('#main form[data-form="account"]')) btn.click(); }, 400);
    }
    else if (a === 'buys') buys();
    else if (a === 'payouts') payouts();
    else if (a === 'save') { try { save(); } catch (x0) { if (typeof toast === 'function') toast(x.saveErr); } }
    else if (a === 'later') { if (stOf().state !== 'done') setSt({ state: 'later' }); close(); }
    else if (a === 'close') close();
    else if (a === 'open') { W = null; start(); }
    else if (a === 'hide') { setSt({ state: stOf().state === 'done' ? 'done' : 'hidden' }); if (typeof render === 'function') render(); }
  });
  const onField = (e) => {
    const t = e.target; if (!W || !t.closest || !t.closest('.rn')) return;
    if (t.matches('[data-rn-p]')) W.p[t.dataset.rnP] = t.value;
    else if (t.matches('[data-rn-pay]')) W.payout = t.value;
    else if (t.matches('[data-rn-from]')) W.from = t.value;
  };
  document.addEventListener('input', onField); document.addEventListener('change', onField);   // Safari: a date field may only send « change »
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && el) { if (stOf().state !== 'done') setSt({ state: 'later' }); close(); } });

  /* after an account is saved during the first visit: « Account added » instead of the trade window */
  // the app opens the trade window right after an account is saved: during this flow, that one call is skipped.
  // window.openTicket is wrapped at that moment (other modules wrap it later, the outermost one must be held)
  function holdTicket() {
    const cur = window.openTicket; if (typeof cur !== 'function' || cur.__rnHold) return;
    const until = Date.now() + 3000;
    const w = function () { if (Date.now() < until) return undefined; return cur.apply(this, arguments); }; w.__rnHold = true;
    window.openTicket = w; setTimeout(() => { if (window.openTicket === w) window.openTicket = cur; }, 3100);
  }
  if (typeof submitAccount === 'function') {
    const orig = submitAccount;
    submitAccount = function (form) {
      const first = !!(form && form.dataset && form.dataset.onb) && !realAccts().length && !stOf().state && !(typeof billCan === 'function' && !billCan('payouts'));   // (a new trader is on the Pro trial)
      if (first) flow = true;
      if (flow) holdTicket();
      const before = realAccts().length, out = orig.apply(this, arguments);
      if (flow && realAccts().length > before) setTimeout(() => { if (!/^#(dashboard)?$/.test(location.hash || '')) location.hash = '#dashboard'; added(); }, 350);
      return out;
    };
  }

  /* Today's « My money » card: the invitation (new trader who chose « later », or an existing trader, one day) */
  function invite() {
    const s = stOf(); if (flow || el || s.state === 'done' || s.state === 'hidden' || !realAccts().length || S.mode !== 'server') return '';
    if (typeof billCan === 'function' && !billCan('payouts')) return '';   // Free: My money is not in the plan, the server would refuse the entries   // never during the first visit's own flow
    if (!s.state) {   // an existing trader: offered on one day only
      if (s.shown_on && s.shown_on !== today()) return '';
      if (!s.shown_on) setTimeout(() => { if (!stOf().shown_on) setSt({ shown_on: today() }); }, 0);
    }
    return `<div class="rn-inv"><button type="button" class="rn-inv-go" data-rn="open"><b>${s.state === 'later' ? x.invNew : x.invOld}</b><small>${x.invS}</small></button>
      <button type="button" class="rn-inv-x" data-rn="hide" aria-label="${x.hide}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>`;
  }

  /* My money: the « Estimated » tag, a small form for an estimate, and a reminder when an exact purchase enters its period */
  const tag = `<span class="mny-tag rn-est">${x.est}</span>`;
  function estForm(d, coll) {
    const v = coll === 'payouts' ? M.pNet(d) : d.amount_c || 0;
    const what = coll === 'payouts' ? (({ en: 'Payouts', fr: 'Payouts', es: 'Payouts' })[L]) : (CATN[d.category] || d.category) + (firmName(d.firm_id) ? ' · ' + firmName(d.firm_id) : '');
    return `<form class="pz-form mny-form rn-estf" data-rn-est="${coll}" data-id="${esc2(d.id)}" autocomplete="off" data-noi18n><p class="rn-estf-h">${tag} ${esc2(x.estF.replace('{c}', what))}</p>
      <div class="fgrid mny-g"><label class="f"><span>${x.amount}</span><input name="amount" inputmode="decimal" value="${v / 100}"></label>
      <label class="f"><span>${({ en: 'Date', fr: 'Date', es: 'Fecha' })[L]}</span><input type="date" name="date" value="${esc2(coll === 'payouts' ? M.pPaidOn(d) : d.date)}"></label></div>
      <div class="row pz-acts"><button class="btn primary" type="submit">${x.save}</button><button class="btn" type="button" data-mny="cancel">${x.cancel}</button><button class="btn danger" type="button" data-act="${coll === 'payouts' ? 'del-payout' : 'del-expense'}" data-id="${esc2(d.id)}">${x.del}</button></div></form>`;
  }
  if (typeof payoutForm === 'function') { const o = payoutForm; payoutForm = function (e) { return e && e.estimated ? estForm(e, 'payouts') : o.apply(this, arguments); }; }
  if (typeof expenseForm === 'function') { const o = expenseForm; expenseForm = function (e) { return e && e.estimated ? estForm(e, 'expenses') : o.apply(this, arguments); }; }
  document.addEventListener('submit', (e) => {
    const f = e.target; if (!f.matches || !f.matches('form[data-rn-est]')) return;
    e.preventDefault(); e.stopImmediatePropagation();
    const coll = f.dataset.rnEst, d = getDoc(coll, f.dataset.id); if (!d) return;
    const v = num(f.elements.amount.value), date = f.elements.date.value || (coll === 'payouts' ? M.pPaidOn(d) : d.date);
    if (v == null || v === 0) { if (typeof toast === 'function') toast(({ en: 'Enter an amount.', fr: 'Entre un montant.', es: 'Escribe un importe.' })[L]); return; }
    const c = Math.round(v * 100);
    if (coll === 'payouts') put('payouts', Object.assign({}, d, { gross_c: c, net_c: c, amount_c: c, paid_on: date, payment_date: date }));
    else put('expenses', Object.assign({}, d, { amount_c: c, date, est_qty: undefined, est_unit_c: undefined }));
    U.editP = U.editE = null; render();
  }, true);
  // the « Estimated » tag on My money's rows (the yearly CSV says it in its category column, section 25)
  function tagRows() {
    const page = document.querySelector('#main .mny'); if (!page) return;
    page.querySelectorAll('.mny-row[data-id]').forEach((r) => {
      if (r.querySelector('.rn-est')) return;
      const coll = r.dataset.act === 'edit-payout' ? 'payouts' : r.dataset.act === 'edit-expense' ? 'expenses' : ''; if (!coll) return;
      const d = (S[coll] || []).find((y) => y.id === r.dataset.id); if (!d || !d.estimated) return;
      const b = r.querySelector('.pz-main b'); if (!b) return;
      if (coll === 'payouts' && !b.textContent.trim()) b.textContent = ({ en: 'Payouts', fr: 'Payouts', es: 'Payouts' })[L];
      b.insertAdjacentHTML('beforeend', ' ' + tag);
      r.setAttribute('aria-label', (r.getAttribute('aria-label') || '') + ' · ' + x.est);
    });
  }
  // an exact purchase dated inside an estimate's period: a reminder (nothing is merged)
  if (typeof submitExpense === 'function') {
    const o = submitExpense;
    submitExpense = function (form) {
      const before = new Set((S.expenses || []).map((e) => e.id)), out = o.apply(this, arguments);
      try {
        const n = (S.expenses || []).find((e) => !before.has(e.id) && !e.estimated); if (!n) return out;
        const fid = n.firm_id || ((S.accounts || []).find((a) => a.id === n.account_id) || {}).firm_id;
        const est = (S.expenses || []).find((e) => e.estimated && e.firm_id === fid && e.category === n.category && e.date <= n.date);
        if (est) remind(est);
      } catch (x0) { /* a reminder never blocks the save */ }
      return out;
    };
  }
  function remind(est) {
    document.querySelectorAll('.rn-remind').forEach((r) => r.remove());
    const r = document.createElement('div'); r.className = 'nav-undo rn-remind on'; r.setAttribute('role', 'status'); r.setAttribute('data-noi18n', '');
    r.innerHTML = `<span>${esc2(x.remind.replace('{f}', firmName(est.firm_id) || '—'))}</span><button type="button">${x.adjust}</button>`;
    document.body.append(r);
    const end = setTimeout(() => r.remove(), 8000);
    r.querySelector('button').addEventListener('click', () => { clearTimeout(end); r.remove(); U.editE = est.id; U.addE = false; U.mper = 'all'; location.hash = '#payouts'; render(); });
  }

  const appRender = render;
  render = function () { const out = appRender.apply(this, arguments); try { tagRows(); } catch (x0) { /* never blocks */ } return out; };
  window.SweepRealNet = { invite, open: () => { W = null; start(); }, state: stOf, showNet };
})();
