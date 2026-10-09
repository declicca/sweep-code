/*
 * Sweep — real candle charts, Phase 1 (step 3): SweepChart in the trade recap.
 * TradingView Lightweight Charts v5.2.1 (Apache-2.0), self-hosted and pinned, loaded only when a chart is shown.
 * Data: /api/chart/bars (Databento CME, shared cache, never newer than the licence delay).
 * Times are drawn in New York time; candles up = blue, down = gold; the TradingView attribution logo stays on.
 */
(function () {
  'use strict';
  if (typeof tradeChartMount !== 'function' || typeof apiJSON !== 'function') return;

  const LWC_SRC = 'assets/vendor/lightweight-charts.5.2.1.standalone.production.js';
  const TFS = [['15s', 15], ['30s', 30], ['1m', 60], ['5m', 300], ['15m', 900], ['1h', 3600]];
  const S_ = {
    en: { adv: 'Advanced options', contract_lbl: 'Contract month (optional)', contract_help: 'Only if you traded another month than the main contract (e.g. around a rollover). Sweep then loads that exact contract\'s chart.', contract_bad: 'Format: root + month + year, e.g. NQZ6', snap: 'Snap', hint: 'Tap a candle: {tool}', too_recent_tk: 'The chart for this date will be ready {date}. The form works as usual.', pending: "This trade's chart will be ready {date}. We'll add it to your recap automatically.", unsupported: 'Chart not available yet for this instrument.',
      soon: 'Chart available soon.', far: "This trade's prices are far from the market that day: check the instrument, date or prices.", mismatch: "This price doesn't match that candle. Check the time or price.", save: 'Save image', saved: 'Chart added to your screenshots',
      source: '{contract} · CME data', full: 'Full screen', close: 'Close', entry: 'Entry', exit: 'Exit', stop: 'Stop', target: 'Target', pts: 'pts', recenter: 'Double-tap to recenter',
      legal: 'Charts by TradingView Lightweight Charts™ (Apache 2.0) · tradingview.com' },
    fr: { adv: 'Options avancées', contract_lbl: 'Mois du contrat (facultatif)', contract_help: 'Seulement si tu as tradé un autre mois que le contrat principal (par exemple autour d’un rollover). Sweep charge alors le graphique de ce contrat précis.', contract_bad: 'Format : racine + mois + année, ex. NQZ6', snap: 'Aimanter', hint: 'Touche une bougie : {tool}', too_recent_tk: 'Le graphique de cette date sera disponible {date}. Le formulaire fonctionne normalement.', pending: "Le graphique de ce trade sera disponible {date}. On l'ajoutera automatiquement à ton récap.", unsupported: 'Graphique pas encore disponible pour cet instrument.',
      soon: 'Graphique disponible bientôt.', far: "Les prix de ce trade sont loin du marché ce jour-là : vérifie l'instrument, la date ou les prix.", mismatch: "Le prix ne correspond pas à cette bougie, vérifie l'heure ou le prix.", save: "Enregistrer l'image", saved: 'Graphique ajouté à tes captures',
      source: '{contract} · données CME', full: 'Plein écran', close: 'Fermer', entry: 'Entrée', exit: 'Sortie', stop: 'Stop', target: 'Objectif', pts: 'pts', recenter: 'Double-tap pour recentrer',
      legal: 'Graphiques : TradingView Lightweight Charts™ (Apache 2.0) · tradingview.com' },
    es: { adv: 'Opciones avanzadas', contract_lbl: 'Mes del contrato (opcional)', contract_help: 'Solo si operaste otro mes distinto del contrato principal (por ejemplo, cerca de un rollover). Sweep carga entonces el gráfico de ese contrato exacto.', contract_bad: 'Formato: raíz + mes + año, p. ej. NQZ6', snap: 'Imantar', hint: 'Toca una vela: {tool}', too_recent_tk: 'El gráfico de esta fecha estará listo {date}. El formulario funciona normalmente.', pending: 'El gráfico de este trade estará listo {date}. Lo añadiremos automáticamente a tu resumen.', unsupported: 'Gráfico aún no disponible para este instrumento.',
      soon: 'Gráfico disponible pronto.', far: 'Los precios de este trade están lejos del mercado ese día: revisa el instrumento, la fecha o los precios.', mismatch: 'El precio no coincide con esa vela. Revisa la hora o el precio.', save: 'Guardar imagen', saved: 'Gráfico añadido a tus capturas',
      source: '{contract} · datos CME', full: 'Pantalla completa', close: 'Cerrar', entry: 'Entrada', exit: 'Salida', stop: 'Stop', target: 'Objetivo', pts: 'pts', recenter: 'Doble toque para recentrar',
      legal: 'Gráficos: TradingView Lightweight Charts™ (Apache 2.0) · tradingview.com' },
  };
  const t = (k, p) => { let s = (S_[LANG] || S_.en)[k] || S_.en[k] || k; if (p) s = s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)); return s; };
  const loc = () => (typeof LOC === 'function' ? LOC() : 'en-US');
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ───────────── library (lazy, once) ───────────── */
  let lwcP = null;
  function lwc() {
    if (window.LightweightCharts) return Promise.resolve(window.LightweightCharts);
    return lwcP ||= new Promise((res, rej) => {
      const s = document.createElement('script'); s.src = LWC_SRC; s.async = true;
      s.onload = () => (window.LightweightCharts ? res(window.LightweightCharts) : rej(new Error('lwc')));
      s.onerror = () => { lwcP = null; rej(new Error('lwc')); };
      document.head.append(s);
    });
  }

  /* ───────────── New York wall clock (the chart's time axis) ───────────── */
  const nyFmt = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const offCache = new Map();
  /** UTC seconds → New York wall clock written as UTC seconds (so the axis reads in ET) */
  function ny(ts) {
    const hk = Math.floor(ts / 3600);
    if (!offCache.has(hk)) {
      const p = Object.fromEntries(nyFmt.formatToParts(new Date(hk * 3600000)).map((x) => [x.type, x.value]));
      offCache.set(hk, Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute, +p.second) / 1000 - hk * 3600);
    }
    return ts + offCache.get(hk);
  }
  /** "2026-10-01 10:12:30" (New York) → same wall clock as UTC seconds */
  function wall(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/.exec(String(s || ''));
    return m ? Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0)) / 1000 : null;
  }

  /* ───────────── theme ───────────── */
  function theme() {
    const cs = getComputedStyle(document.documentElement), v = (n, d) => (cs.getPropertyValue(n) || '').trim() || d;
    return { up: v('--pos', '#4C8DFF'), gold: v('--neg', '#D4A24C'), down: v('--neg', '#D4A24C'), text: v('--text', '#F2F2F3'), muted: v('--muted', '#8E8E93'), line: v('--line', 'rgba(255,255,255,.08)'), bg: v('--bg', '#0B0B0C') };
  }
  const alpha = (c, a) => {
    if (/^#([0-9a-f]{6})$/i.test(c)) { const n = parseInt(c.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; }
    if (/^rgb\(/.test(c)) return c.replace('rgb(', 'rgba(').replace(')', `,${a})`);
    return c;
  };

  /** down candles: neutral grey/white from the brand (blue stays for up candles, gold for stops and losses) */
  const candleDown = (th) => alpha(th.text, 0.58);

  /* ───────────── position zone (series primitive: entry→target blue, entry→stop gold, entry time→exit time) ───────────── */
  class PositionZone {
    constructor(z) { this.z = z; this._p = null; const self = this;
      this._view = { zOrder: () => 'bottom', renderer: () => ({ draw: (target) => self.draw(target) }) }; }
    attached(p) { this._p = p; }
    detached() { this._p = null; }
    updateAllViews() {}
    paneViews() { return [this._view]; }
    draw(target) {
      const p = this._p; if (!p) return;
      const ts = p.chart.timeScale(), s = p.series, z = this.z;
      const x1 = ts.timeToCoordinate(z.t1), x2 = ts.timeToCoordinate(z.t2);
      const ye = s.priceToCoordinate(z.entry);
      if (x1 == null || x2 == null || ye == null) return;
      target.useBitmapCoordinateSpace(({ context: c, horizontalPixelRatio: hr, verticalPixelRatio: vr }) => {
        const L = Math.round(Math.min(x1, x2) * hr), W = Math.max(2, Math.round(Math.abs(x2 - x1) * hr) + Math.round(z.bw * hr));
        const box = (price, col) => { const y = s.priceToCoordinate(price); if (y == null) return; const a = Math.round(Math.min(ye, y) * vr), b = Math.round(Math.abs(y - ye) * vr); c.fillStyle = col; c.fillRect(L, a, W, b); };
        if (z.target != null) box(z.target, alpha(z.up, 0.16));
        if (z.stop != null) box(z.stop, alpha(z.down, 0.16));
      });
    }
  }

  /** thin vertical lines at the CME session open (18:00 ET) and the New York open (9:30 ET) */
  class SessionLines {
    constructor(times, color) { this.times = times; this.color = color; this._p = null; const self = this;
      this._view = { zOrder: () => 'bottom', renderer: () => ({ draw: (target) => self.draw(target) }) }; }
    attached(p) { this._p = p; }
    detached() { this._p = null; }
    updateAllViews() {}
    paneViews() { return [this._view]; }
    draw(target) {
      const p = this._p; if (!p) return;
      const ts = p.chart.timeScale();
      target.useBitmapCoordinateSpace(({ context: c, bitmapSize, horizontalPixelRatio: hr }) => {
        c.fillStyle = this.color;
        for (const t0 of this.times) { const x = ts.timeToCoordinate(t0); if (x == null) continue; c.fillRect(Math.round(x * hr), 0, Math.max(1, Math.round(hr)), bitmapSize.height); }
      });
    }
  }
  /** bar times (New York wall clock) where a session starts: crossing 18:00 or 9:30 */
  function sessionTimes(data) {
    const out = [], mod = (t0) => Math.floor((t0 % 86400) / 60);
    for (let i = 1; i < data.length; i++) {
      const a = mod(data[i - 1].time), b = mod(data[i].time), newDay = data[i].time - data[i - 1].time >= 86400 || b < a;
      for (const m of [570, 1080]) if ((a < m && b >= m) || (newDay && b >= m && a < m + 1440 && m === 1080 && a < 1080)) { out.push(data[i].time); break; }
    }
    return out;
  }

  /* ───────────── data ───────────── */
  const cache = new Map();
  async function bars(tradeId, tf) {
    const k = tradeId + '|' + (tf || '');
    if (cache.has(k)) return cache.get(k);
    const r = await apiJSON('api/chart/bars?trade_id=' + encodeURIComponent(tradeId) + (tf ? '&tf=' + tf : ''));
    if (r && r.status === 'ok') cache.set(k, r);
    return r;
  }

  /* ───────────── the recap chart ───────────── */
  let live = null;     // { chart, el, tradeId }
  const origMount = tradeChartMount;
  const pick = {};     // tf chosen per trade

  /** a trade's date is its session: from 18:00 ET the clock time belongs to the evening before (same rule as todayStr) */
  const atSession = (e, t) => (typeof wallOfTrade === 'function' ? wallOfTrade(e, t) : `${e.date} ${t}`);
  function execsOf(e) {
    const ex = (e.executions && e.executions.length ? e.executions : [
      { side: e.direction === 'long' ? 'buy' : 'sell', qty: e.contracts, price: e.entry, t: atSession(e, e.entry_time || '09:30') },
      ...(e.exit != null && e.exit !== '' ? [{ side: e.direction === 'long' ? 'sell' : 'buy', qty: e.contracts, price: e.exit, t: atSession(e, e.exit_time || e.entry_time || '09:31') }] : []),
    ]);
    return ex.map((x) => ({ side: x.side, qty: +x.qty || 0, price: +x.price, t: wall(x.t) })).filter((x) => x.t && isFinite(x.price));
  }

  function shell(e, tf, durOk) {
    const tfs = TFS.filter(([k, s]) => s >= 60 || durOk);
    return `<div class="tk-bar sc-bar" data-noi18n><b>${esc(e.instrument || 'NQ')}</b><span class="muted">· ${fdate(e.date, { weekday: 'short', month: 'short', day: 'numeric' })}</span><span style="flex:1"></span>
      <div class="seg sc-tfs">${tfs.map(([k]) => `<button type="button" data-sc-tf="${k}" class="${k === tf ? 'on' : ''}">${k}</button>`).join('')}</div>
      <button type="button" class="sc-ic" data-sc="full" aria-label="${t('full')}" title="${t('full')}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg></button></div>
      <div class="sc-box"><div class="sc-chart" id="scChart"><div class="sc-skel"></div></div></div>
      <div class="sc-foot" data-noi18n><span class="sc-src"></span><span class="sc-warn"></span><span style="flex:1"></span><button type="button" class="link sc-save" data-sc="save" hidden>${t('save')}</button></div>`;
  }

  const chartSig = (e) => JSON.stringify([e.instrument, e.contract, e.date, e.entry_time, e.exit_time, e.entry, e.exit, e.stop, e.target, e.direction, e.contracts, (e.executions || []).length, pick[e.id] || null]);
  tradeChartMount = async function (e) {
    const holder = document.getElementById('tradeChart') || document.getElementById('scChart');
    const wrap = holder && holder.closest('.tr-chart');
    if (!wrap || !e) return origMount.apply(this, arguments);
    // the page re-renders on every edit (a chip, a note, a checklist answer): when the chart itself would not change,
    // the drawn chart is moved into the new page instead of being rebuilt (no blank flash on each tap)
    const sig = chartSig(e);
    if (live && live.tradeId === e.id && live.sig === sig && live.wrap) {
      if (live.wrap === wrap && document.body.contains(wrap) && wrap.contains(live.el)) return;                 // same chart still on screen: nothing to redraw
      if (live.wrap !== wrap && !document.body.contains(live.wrap)) { wrap.replaceWith(live.wrap); return; }    // page rebuilt: put the drawn chart back
    }
    if (live && !document.body.contains(live.el)) { try { live.chart.remove(); } catch (x) { /* gone */ } live = null; }
    const ex = execsOf(e);
    const dur = ex.length ? Math.max(...ex.map((x) => x.t)) - Math.min(...ex.map((x) => x.t)) : 0;
    const tf = pick[e.id] || null;
    wrap.classList.add('sc-wrap'); wrap.innerHTML = shell(e, tf || '', dur < 7200);
    wrap.dataset.trade = e.id; wrap.dataset.sig = sig;
    let r;
    try { r = await bars(e.id, tf); } catch (x) { r = { status: 'unavailable' }; }
    if (wrap.dataset.trade !== e.id || !document.body.contains(wrap)) return;
    const box = wrap.querySelector('#scChart');
    if (!r || r.status === 'unavailable' || !r.status) {          // no key / Databento down: keep the previous chart, nothing breaks
      // never fall back to the old chart: a calm message and a retry, inside the same chart frame
      const L = (typeof LANG !== 'undefined' && LANG) || 'en';
      const m = ({ en: ['Chart unavailable for a moment.', 'Retry'], fr: ['Graphique indisponible pour le moment.', 'Réessayer'], es: ['Gráfico no disponible por ahora.', 'Reintentar'] })[L] || ['Chart unavailable for a moment.', 'Retry'];
      if (box) box.innerHTML = `<div class="sc-off" data-noi18n><span>${m[0]}</span><button type="button" class="btn sm" data-sc-retry>${m[1]}</button></div>`;
      const rb = wrap.querySelector('[data-sc-retry]'); if (rb) rb.addEventListener('click', () => { live = null; tradeChartMount(e); });
      return;
    }
    if (r.status !== 'ok') {
      const msg = r.status === 'too_recent' ? t('pending', { date: new Date(r.available_at * 1000).toLocaleString(loc(), { weekday: 'long', hour: 'numeric', minute: '2-digit' }) })
        : r.status === 'unsupported' ? t('unsupported') : t('soon');
      box.innerHTML = `<div class="sc-card ${r.status}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M5 19V9M10 19V5M15 19v-7M20 19v-4"/></svg><p>${esc(msg)}</p></div>`;
      wrap.querySelector('.sc-tfs').hidden = true; wrap.querySelector('[data-sc=full]').hidden = true;
      // the message block is kept like a drawn chart: put back as is on every redraw (no blink, no jump)
      live = { chart: { remove() {}, takeScreenshot() { return null; } }, series: null, el: box, tradeId: e.id, wrap, sig, refresh() {} };
      return;
    }
    wrap.querySelectorAll('[data-sc-tf]').forEach((b) => b.classList.toggle('on', b.dataset.scTf === r.tf));
    let L;
    try { L = await lwc(); } catch (x) { box.innerHTML = `<div class="sc-card"><p>${esc(t('soon'))}</p></div>`; return; }
    draw(L, box, wrap, e, r, ex);
  };

  function draw(L, box, wrap, e, r, ex) {
    if (live) { try { live.chart.remove(); } catch (x) { /* gone */ } live = null; }
    box.innerHTML = '';
    const th = theme(), sec = (TFS.find(([k]) => k === r.tf) || [0, 60])[1], dec = r.decimals != null ? r.decimals : 2;
    const data = r.bars.map((b) => ({ time: ny(b[0]), open: b[1], high: b[2], low: b[3], close: b[4] }));
    const lo = Math.min(...data.map((d) => d.low)), hi = Math.max(...data.map((d) => d.high)), span = Math.max(hi - lo, (r.tick_size || 0.25) * 400);
    const levels = [e.entry, e.stop, e.target, e.exit].filter((v) => v != null && v !== '' && isFinite(+v)).map(Number);
    const near = levels.filter((v) => v >= lo - span && v <= hi + span);
    const far = levels.length > 0 && near.length < levels.length;
    const chart = L.createChart(box, {
      autoSize: true,
      layout: { background: { type: 'solid', color: 'transparent' }, textColor: th.muted, fontFamily: 'Geist, -apple-system, system-ui, sans-serif', fontSize: 11, attributionLogo: true },
      grid: { vertLines: { color: alpha(th.text, 0.04) }, horzLines: { color: alpha(th.text, 0.05) } },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.1 } },
      timeScale: { borderVisible: false, timeVisible: true, secondsVisible: sec < 60, rightOffset: 4, barSpacing: 7 },
      crosshair: { mode: L.CrosshairMode.Normal, vertLine: { color: alpha(th.text, 0.25), labelBackgroundColor: th.text }, horzLine: { color: alpha(th.text, 0.25), labelBackgroundColor: th.text } },
      localization: { locale: loc(), priceFormatter: (p) => Number(p).toFixed(dec) },
      handleScale: { pinch: true, mouseWheel: true, axisPressedMouseMove: true }, handleScroll: { vertTouchDrag: false },
    });
    const series = chart.addSeries(L.CandlestickSeries, {
      upColor: th.up, downColor: candleDown(th), borderVisible: false, wickUpColor: th.up, wickDownColor: candleDown(th),
      priceFormat: { type: 'price', precision: dec, minMove: r.tick_size || 0.25 }, priceLineVisible: false, lastValueVisible: false,
      // keep entry, stop and target in view
      // keep entry, stop and target in view, but only when they belong to this market (a typo or a sample trade
      // far from the real prices must never crush the candles into a flat line)
      autoscaleInfoProvider: (orig) => {
        const a = orig(); if (!a || !a.priceRange) return a;
        for (const v of near) { a.priceRange.minValue = Math.min(a.priceRange.minValue, v); a.priceRange.maxValue = Math.max(a.priceRange.maxValue, v); }
        return a;
      },
    });
    series.setData(data);
    const snap = (ts) => Math.floor(ts / sec) * sec;
    const times = new Set(data.map((d) => d.time));
    const nearest = (ts) => { const s0 = snap(ts); if (times.has(s0)) return s0; let best = null; for (const d of data) if (best == null || Math.abs(d.time - s0) < Math.abs(best - s0)) best = d.time; return best; };

    // markers: one arrow per execution; the last exit carries the result (R, or points without a stop)
    const long = e.direction !== 'short';
    const isEntry = (x) => (long ? x.side === 'buy' : x.side === 'sell');
    const net = (e.pnl_c || 0) - (e.fees_c || 0);
    const R = typeof tR === 'function' ? tR(e) : null;
    const pts = e.entry != null && e.exit != null ? (long ? 1 : -1) * (e.exit - e.entry) : null;
    const res = R != null && isFinite(R) ? `${R >= 0 ? '+' : ''}${R.toLocaleString(loc(), { maximumFractionDigits: 1, minimumFractionDigits: 1 })}R` : pts != null ? `${pts >= 0 ? '+' : ''}${pts.toLocaleString(loc(), { maximumFractionDigits: 2 })} ${t('pts')}` : '';
    const exits = ex.filter((x) => !isEntry(x)), lastExit = exits.length ? exits[exits.length - 1] : null;
    const markers = ex.map((x) => {
      const en = isEntry(x), up = x.side === 'buy';
      return { time: nearest(x.t), position: up ? 'belowBar' : 'aboveBar', shape: up ? 'arrowUp' : 'arrowDown',
        color: en ? th.text : net >= 0 ? th.up : th.down, size: 1.2, text: en ? t('entry') : x === lastExit && res ? res : t('exit') };
    }).filter((m) => m.time != null).sort((a, b) => a.time - b.time);
    L.createSeriesMarkers(series, markers);
    series.attachPrimitive(new SessionLines(sessionTimes(data), alpha(th.text, 0.14)));

    // price lines: entry (neutral), stop (gold, dashed), target (blue, dashed)
    const line = (price, color, style, title) => { if (price == null || price === '' || !isFinite(+price)) return; series.createPriceLine({ price: +price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title }); };
    line(e.entry, alpha(th.text, 0.7), L.LineStyle.Solid, t('entry'));
    line(e.stop, th.down, L.LineStyle.Dashed, t('stop'));
    line(e.target, th.up, L.LineStyle.Dashed, t('target'));

    // position zone, from entry time to exit time
    const tIn = ex.length ? Math.min(...ex.map((x) => x.t)) : null, tOut = ex.length ? Math.max(...ex.map((x) => x.t)) : null;
    if (tIn != null && e.entry != null && (e.stop != null || e.target != null)) {
      const a = nearest(tIn), b = nearest(tOut);
      if (a != null && b != null) series.attachPrimitive(new PositionZone({ t1: a, t2: b, entry: +e.entry, stop: e.stop != null && e.stop !== '' ? +e.stop : null, target: e.target != null && e.target !== '' ? +e.target : null, up: th.up, down: th.down, bw: 6 }));
    }

    // a typed price outside its candle → neutral hint
    const tick = r.tick_size || 0.25;
    const off = ex.some((x) => { const tt = nearest(x.t); const d = data.find((q) => q.time === tt); return d && tt === snap(x.t) && (x.price < d.low - tick || x.price > d.high + tick); });
    wrap.querySelector('.sc-warn').textContent = far ? t('far') : off ? t('mismatch') : '';
    wrap.querySelector('.sc-src').textContent = r.contract ? t('source', { contract: r.contract }) : '';
    wrap.querySelector('.sc-save').hidden = typeof ASSETS === 'undefined' || !ASSETS;

    // centre on the trade; double-tap / double-click recentres
    const focus = () => {
      if (tIn == null) { chart.timeScale().fitContent(); return; }
      const pad = Math.max(sec * 25, (tOut - tIn) * 0.6);
      chart.timeScale().setVisibleRange({ from: snap(tIn - pad), to: snap(tOut + pad) });
    };
    try { focus(); } catch (x) { chart.timeScale().fitContent(); }
    if (typeof chart.subscribeDblClick === 'function') chart.subscribeDblClick(focus); else box.addEventListener('dblclick', focus);
    box.title = t('recenter');

    live = { chart, series, el: box, tradeId: e.id, wrap: box.closest('.tr-chart'), sig: (box.closest('.tr-chart') || {}).dataset ? box.closest('.tr-chart').dataset.sig : null, refresh: () => { const n = theme(); chart.applyOptions({ layout: { textColor: n.muted }, grid: { vertLines: { color: alpha(n.text, 0.04) }, horzLines: { color: alpha(n.text, 0.05) } } }); series.applyOptions({ upColor: n.up, downColor: candleDown(n), wickUpColor: n.up, wickDownColor: candleDown(n) }); } };
    if (!reduced()) box.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 280, easing: 'ease-out' });
  }

  /* ───────────── controls ───────────── */
  document.addEventListener('click', async (ev) => {
    const b = ev.target.closest && ev.target.closest('[data-sc-tf],[data-sc]');
    if (!b) return;
    const wrap = b.closest('.sc-wrap'); if (!wrap) return;
    ev.preventDefault(); ev.stopPropagation();
    const id = wrap.dataset.trade, e = typeof getDoc === 'function' ? getDoc('trades', id) : null;
    if (b.dataset.scTf) { pick[id] = b.dataset.scTf; if (e) tradeChartMount(e); return; }
    if (b.dataset.sc === 'full') { wrap.classList.toggle('sc-full'); document.body.classList.toggle('sc-lock', wrap.classList.contains('sc-full')); return; }
    if (b.dataset.sc === 'save' && live && e) {
      try {
        const cv = live.chart.takeScreenshot(), out = document.createElement('canvas'), band = Math.round(cv.height * 0.09) + 24;
        out.width = cv.width; out.height = cv.height + band;
        const c = out.getContext('2d'), th = theme();
        c.fillStyle = th.bg; c.fillRect(0, 0, out.width, out.height); c.drawImage(cv, 0, 0);
        c.fillStyle = th.text; c.font = `600 ${Math.round(band * 0.36)}px Geist, system-ui, sans-serif`; c.textBaseline = 'middle';
        c.fillText(`sweep · ${e.instrument || 'NQ'} · ${e.date}`, 24, cv.height + band / 2);
        c.fillStyle = th.muted; c.textAlign = 'right'; c.fillText('makeitsweep.com', out.width - 24, cv.height + band / 2);
        const blob = await new Promise((res) => out.toBlob(res, 'image/png'));
        const up = await ASSETS.upload(new File([blob], 'chart.png', { type: 'image/png' }));
        editDoc('trades', id, (d) => { d.shots = d.shots || []; d.shots.push({ id: up.id, phase: 'after', name: 'chart.png' }); });
        if (typeof syncTrade === 'function') syncTrade(id, ['shots']);
        toast(t('saved'));
      } catch (x) { toast('Upload failed'); }
    }
  }, true);   // capture: the app's own handlers must not swallow these taps
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') { const w = document.querySelector('.sc-wrap.sc-full'); if (w) { w.classList.remove('sc-full'); document.body.classList.remove('sc-lock'); } } });
  // light/dark follows the app
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => live && live.refresh());
  new MutationObserver(() => live && live.refresh()).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });


  /* ───────────── step 4: chart in the add-trade form ─────────────
   * Tap a candle to fill Entry → Exit → Stop → Target (time + price, rounded to the tick, « Snap » to O/H/L/C within 3 ticks).
   * Stop and Target lines can be dragged. Fields and chart stay in sync both ways; the form always works without the chart. */
  const TOOLS = ['entry', 'exit', 'stop', 'target'];
  const TKC = { tool: 'entry', snap: true, key: '', chart: null, series: null, lines: {}, markers: null, data: [], tick: 0.25, dec: 2, drag: null, L: null };
  const $tk = (k) => document.querySelector(`#tkSlide [data-tk="${k}"]`);
  const val = (k) => { const i = $tk(k); return i && i.value.trim() !== '' && isFinite(+i.value) ? +i.value : null; };
  function setField(k, v) {
    const i = $tk(k); if (!i) return;
    i.value = v; i.dispatchEvent(new Event('input', { bubbles: true }));
  }
  const hms = (ts) => { const d = new Date(ts * 1000); return [d.getUTCHours(), d.getUTCMinutes(), d.getUTCSeconds()].map((n) => String(n).padStart(2, '0')).join(':'); };
  const roundTick = (p) => { const k = TKC.tick; return +(Math.round(p / k) * k).toFixed(TKC.dec); };

  function tkSection() {
    return `<div class="tk-sec sc-tk" data-noi18n>
      <div class="sc-tools">${TOOLS.map((k) => `<button type="button" class="sc-tool ${k} ${TKC.tool === k ? 'on' : ''}" data-sct="${k}">${t(k)}</button>`).join('')}
        <label class="sc-snap"><input type="checkbox" data-sct-snap ${TKC.snap ? 'checked' : ''}><span>${t('snap')}</span></label></div>
      <div class="sc-chart sc-tkchart" id="scTk"><div class="sc-skel"></div></div>
      <div class="sc-foot"><span class="sc-src"></span><span style="flex:1"></span><span class="sc-hint"></span></div>
      <details class="sc-adv" ${TKC.contract ? 'open' : ''}><summary>${t('adv')}</summary>
        <label class="tk-f"><span>${t('contract_lbl')}</span><input data-sc-contract value="${esc(TKC.contract || '')}" placeholder="${esc((($tk('inst') || {}).value || 'NQ') + 'Z6')}" autocomplete="off" autocapitalize="characters" spellcheck="false"></label>
        <small class="sc-chelp">${t('contract_help')}</small><small class="sc-cbad" hidden>${t('contract_bad')}</small></details></div>`;
  }
  function inject() {
    const slide = document.getElementById('tkSlide');
    if (!slide || !slide.classList.contains('open') || typeof TK === 'undefined' || !TK || TK.multi) return;
    if (slide.querySelector('.sc-tk')) return;
    const exitSec = (document.querySelector('#tkSlide #tkResult') || $tk('exit')); const anchor = (exitSec && exitSec.closest('.tk-sec')) || ($tk('inst') && $tk('inst').closest('.tk-sec'));   // the chart goes under the exit: prices first, no scrolling
    if (!anchor) return;
    if (TK.id && TKC.forId !== TK.id) { const d = getDoc('trades', TK.id); TKC.contract = (d && d.contract) || ''; }
    if (!TK.id && TKC.forId !== 'new') TKC.contract = '';
    TKC.forId = TK.id || 'new';
    const k = tkKey();
    if (TKC.host && k && TKC.hostKey === k.key && !document.contains(TKC.host)) { anchor.after(TKC.host); return; }   // same chart: no blink, no jump
    if (TKC.chart) { try { TKC.chart.remove(); } catch (x) { /* gone */ } TKC.chart = null; }
    anchor.insertAdjacentHTML('afterend', tkSection());
    TKC.key = ''; TKC.host = null; loadTk();
  }
  function tkKey() {
    const inst = TKC.contract || ($tk('inst') || {}).value || 'NQ', date = ($tk('date') || {}).value;
    const tm = (($tk('entryTime') || {}).value || '09:30').slice(0, 5);
    if (!date) return null;
    const centre = wall(`${date} ${/^\d{2}:\d{2}$/.test(tm) ? tm : '09:30'}`);
    // the form reads New York wall clock; the API wants real UTC seconds: undo the shift with the offset of that hour
    const utc = centre - (ny(centre) - centre);
    return { inst, date, utc, key: `${inst}|${date}|${Math.floor(utc / 3600)}` };
  }
  async function loadTk() {
    const box = document.getElementById('scTk'); if (!box) return;
    const k0 = tkKey(); if (!k0) return;
    const { inst, date, utc, key } = k0;
    if (key === TKC.key && TKC.chart) return;
    TKC.key = key;
    let r;
    try { r = await apiJSON(`api/chart/bars?symbol=${encodeURIComponent(inst)}&from=${utc - 3 * 3600}&to=${utc + 3 * 3600}&tf=1m`); } catch (x) { r = { status: 'unavailable' }; }
    const host = document.querySelector('#tkSlide .sc-tk'); if (!host || TKC.key !== key) return;
    if (TKC.chart) { try { TKC.chart.remove(); } catch (x) { /* gone */ } TKC.chart = null; }
    if (!r || r.status === 'unavailable' || !r.status) { host.hidden = true; TKC.host = host; TKC.hostKey = key; return; }       // no key / provider down: just the form
    host.hidden = false;
    const tools = host.querySelector('.sc-tools');
    if (r.status !== 'ok' || !r.bars.length) {
      tools.hidden = true;
      const msg = r.status === 'too_recent' ? t('too_recent_tk', { date: new Date(r.available_at * 1000).toLocaleString(loc(), { weekday: 'long', hour: 'numeric', minute: '2-digit' }) }) : r.status === 'unsupported' ? t('unsupported') : t('soon');
      box.innerHTML = `<div class="sc-card ${r.status}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M5 19V9M10 19V5M15 19v-7M20 19v-4"/></svg><p>${esc(msg)}</p></div>`;
      host.querySelector('.sc-src').textContent = '';
      TKC.host = host; TKC.hostKey = key;
      return;
    }
    tools.hidden = false;
    let L; try { L = TKC.L = await lwc(); } catch (x) { host.hidden = true; return; }
    box.innerHTML = '';
    const th = theme();
    TKC.tick = r.tick_size || 0.25; TKC.dec = r.decimals != null ? r.decimals : 2;
    TKC.data = r.bars.map((b) => ({ time: ny(b[0]), open: b[1], high: b[2], low: b[3], close: b[4] }));
    const chart = L.createChart(box, {
      autoSize: true,
      layout: { background: { type: 'solid', color: 'transparent' }, textColor: th.muted, fontFamily: 'Geist, -apple-system, system-ui, sans-serif', fontSize: 11, attributionLogo: true },
      grid: { vertLines: { color: alpha(th.text, 0.04) }, horzLines: { color: alpha(th.text, 0.05) } },
      rightPriceScale: { borderVisible: false }, timeScale: { borderVisible: false, timeVisible: true, rightOffset: 3, barSpacing: 6 },
      crosshair: { mode: L.CrosshairMode.Normal, vertLine: { color: alpha(th.text, 0.3), labelBackgroundColor: th.text }, horzLine: { color: alpha(th.text, 0.3), labelBackgroundColor: th.text } },
      localization: { locale: loc(), priceFormatter: (p) => Number(p).toFixed(TKC.dec) }, handleScroll: { vertTouchDrag: false },
    });
    const series = chart.addSeries(L.CandlestickSeries, { upColor: th.up, downColor: candleDown(th), borderVisible: false, wickUpColor: th.up, wickDownColor: candleDown(th),
      priceFormat: { type: 'price', precision: TKC.dec, minMove: TKC.tick }, priceLineVisible: false, lastValueVisible: false,
      // typed levels stay in view when they belong to this market
      autoscaleInfoProvider: (orig) => {
        const a = orig(); if (!a || !a.priceRange) return a;
        const lo = a.priceRange.minValue, hi = a.priceRange.maxValue, span = Math.max(hi - lo, TKC.tick * 400);
        for (const k of TOOLS) { const v = val(k); if (v != null && v >= lo - span && v <= hi + span) { a.priceRange.minValue = Math.min(a.priceRange.minValue, v); a.priceRange.maxValue = Math.max(a.priceRange.maxValue, v); } }
        return a;
      } });
    series.setData(TKC.data);
    TKC.chart = chart; TKC.series = series; TKC.lines = {}; TKC.markers = L.createSeriesMarkers(series, []);
    series.attachPrimitive(new SessionLines(sessionTimes(TKC.data), alpha(th.text, 0.14)));
    const c = ny(utc); try { chart.timeScale().setVisibleRange({ from: c - 45 * 60, to: c + 45 * 60 }); } catch (x) { chart.timeScale().fitContent(); }
    chart.subscribeClick(onTap);
    host.querySelector('.sc-src').textContent = r.contract ? t('source', { contract: r.contract }) : '';
    TKC.host = host; TKC.hostKey = key;
    redraw(); hint();
  }
  function hint() { const h = document.querySelector('#tkSlide .sc-hint'); if (h) h.textContent = t('hint', { tool: t(TKC.tool) }); }

  /** a tap on the chart: time + price of the touched candle, rounded to the tick, snapped to O/H/L/C within 3 ticks */
  function onTap(p) {
    if (TKC.drag || TKC.justDragged || !p || !p.point || p.time == null) return;
    let price = TKC.series.coordinateToPrice(p.point.y); if (price == null) return;
    const bar = TKC.data.find((d) => d.time === p.time);
    if (TKC.snap && bar) {
      const best = [bar.open, bar.high, bar.low, bar.close].reduce((a, b) => (Math.abs(b - price) < Math.abs(a - price) ? b : a));
      if (Math.abs(best - price) <= TKC.tick * 3) price = best;
    }
    price = roundTick(price);
    const tool = TKC.tool;
    if (tool === 'entry') { setField('entry', price.toFixed(TKC.dec)); setField('entryTime', hms(p.time)); }
    else if (tool === 'exit') { setField('exit', price.toFixed(TKC.dec)); setField('exitTime', hms(p.time)); }
    else setField(tool, price.toFixed(TKC.dec));
    if (typeof haptic === 'function') try { haptic(6); } catch (x) { /* web */ }
    autoDir();
    TKC.tool = TOOLS[(TOOLS.indexOf(tool) + 1) % TOOLS.length];
    document.querySelectorAll('#tkSlide [data-sct]').forEach((b) => b.classList.toggle('on', b.dataset.sct === TKC.tool));
    redraw(); hint();
  }
  /** long when the target (or the exit) sits above the entry, or the stop below; the buttons stay editable */
  function autoDir() {
    const e = val('entry'); if (e == null) return;
    const tg = val('target'), x = val('exit'), st = val('stop');
    const dir = tg != null ? (tg > e ? 'long' : 'short') : st != null ? (st < e ? 'long' : 'short') : x != null ? null : null;
    if (!dir) return;
    const b = document.querySelector(`#tkSlide [data-act="tk-dir"][data-v="${dir}"]`);
    if (b && !b.classList.contains('on') && !b.disabled) b.click();
  }

  /** fields → chart: price lines and entry/exit markers */
  function redraw() {
    const s = TKC.series, L = TKC.L; if (!s || !L) return;
    const th = theme();
    const want = { entry: [val('entry'), alpha(th.text, 0.75), L.LineStyle.Solid], exit: [val('exit'), th.up, L.LineStyle.Dotted],
      stop: [val('stop'), th.gold, L.LineStyle.Dashed], target: [val('target'), th.up, L.LineStyle.Dashed] };
    for (const k of TOOLS) {
      const [p, color, style] = want[k];
      if (p == null) { if (TKC.lines[k]) { s.removePriceLine(TKC.lines[k]); delete TKC.lines[k]; } continue; }
      const opts = { price: p, color, lineWidth: k === 'stop' || k === 'target' ? 2 : 1, lineStyle: style, axisLabelVisible: true, title: t(k) };
      if (TKC.lines[k]) TKC.lines[k].applyOptions(opts); else TKC.lines[k] = s.createPriceLine(opts);
    }
    const mk = [], snap = (ts) => Math.floor(ts / 60) * 60;
    const d = ($tk('date') || {}).value;
    const et = ($tk('entryTime') || {}).value, xt = ($tk('exitTime') || {}).value, long = val('target') != null && val('entry') != null ? val('target') > val('entry') : true;
    if (d && et && val('entry') != null) { const tt = wall(`${d} ${et}`); if (tt) mk.push({ time: snap(tt), position: long ? 'belowBar' : 'aboveBar', shape: long ? 'arrowUp' : 'arrowDown', color: th.text, text: t('entry') }); }
    if (d && xt && val('exit') != null) { const tt = wall(`${d} ${xt}`); if (tt) mk.push({ time: snap(tt), position: long ? 'aboveBar' : 'belowBar', shape: long ? 'arrowDown' : 'arrowUp', color: th.up, text: t('exit') }); }
    const times = new Set(TKC.data.map((q) => q.time));
    TKC.markers.setMarkers(mk.filter((m) => times.has(m.time)).sort((a, b) => a.time - b.time));
  }

  /* drag the Stop / Target lines (the library has no line dragging: pointer events + coordinateToPrice) */
  document.addEventListener('pointerdown', (ev) => {
    const box = ev.target.closest && ev.target.closest('#scTk'); if (!box || !TKC.series) return;
    const y = ev.clientY - box.getBoundingClientRect().top;
    for (const k of ['stop', 'target']) {
      const p = val(k); if (p == null) continue;
      const ly = TKC.series.priceToCoordinate(p);
      if (ly != null && Math.abs(ly - y) < 12) {
        TKC.drag = k; TKC.chart.applyOptions({ handleScroll: false, handleScale: false });
        box.setPointerCapture && box.setPointerCapture(ev.pointerId); ev.preventDefault(); return;
      }
    }
  }, true);
  document.addEventListener('pointermove', (ev) => {
    if (!TKC.drag) return;
    const box = document.getElementById('scTk'); if (!box) return;
    const p = TKC.series.coordinateToPrice(ev.clientY - box.getBoundingClientRect().top); if (p == null) return;
    setField(TKC.drag, roundTick(p).toFixed(TKC.dec)); redraw();
  }, true);
  const endDrag = () => {
    if (!TKC.drag) return;
    TKC.drag = null; TKC.justDragged = true; setTimeout(() => { TKC.justDragged = false; }, 250);
    if (TKC.chart) TKC.chart.applyOptions({ handleScroll: { vertTouchDrag: false, horzTouchDrag: true, mouseWheel: true, pressedMouseMove: true }, handleScale: true });
    autoDir();
  };
  document.addEventListener('pointerup', endDrag, true); document.addEventListener('pointercancel', endDrag, true);

  // toolbar, snap switch
  document.addEventListener('click', (ev) => {
    const b = ev.target.closest && ev.target.closest('#tkSlide [data-sct]'); if (!b) return;
    TKC.tool = b.dataset.sct;
    document.querySelectorAll('#tkSlide [data-sct]').forEach((x) => x.classList.toggle('on', x === b)); hint();
  });
  document.addEventListener('change', (ev) => { if (ev.target.matches && ev.target.matches('#tkSlide [data-sct-snap]')) TKC.snap = ev.target.checked; });
  // exact expiry: "NQZ6" style, saved on the trade (the chart then uses that contract instead of the volume leader)
  let cT = 0;
  document.addEventListener('input', (ev) => {
    if (!ev.target.matches || !ev.target.matches('#tkSlide [data-sc-contract]')) return;
    const v = ev.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''); ev.target.value = v;
    const ok = v === '' || /^[A-Z0-9]{1,4}?[FGHJKMNQUVXZ]\d{1,2}$/.test(v);
    const bad = document.querySelector('#tkSlide .sc-cbad'); if (bad) bad.hidden = ok;
    if (!ok) return;
    TKC.contract = v; clearTimeout(cT); cT = setTimeout(() => { TKC.key = ''; loadTk(); }, 500);
  });
  if (typeof put === 'function') {
    const appPut = put;
    put = function (col, doc) {
      try {
        if (col === 'trades' && doc && typeof TK !== 'undefined' && TK && document.querySelector('#tkSlide.open .sc-tk')) {
          if (TKC.contract) doc.contract = TKC.contract; else delete doc.contract;
        }
      } catch (x) { /* never blocks a save */ }
      return appPut.apply(this, arguments);
    };
  }
  // fields → chart (typing by hand moves the lines); instrument, date or time far away → reload the session
  let rT = 0;
  document.addEventListener('input', (ev) => {
    const k = ev.target.dataset && ev.target.dataset.tk; if (!k || !document.querySelector('#tkSlide .sc-tk')) return;
    if (k === 'inst' || k === 'date' || k === 'entryTime') { clearTimeout(rT); rT = setTimeout(loadTk, 500); }
    redraw();
  });
  document.addEventListener('change', (ev) => { const k = ev.target.dataset && ev.target.dataset.tk; if (k === 'inst' || k === 'date' || k === 'entryTime') { clearTimeout(rT); rT = setTimeout(loadTk, 300); } });
  // the ticket panel is rebuilt by the app at times (account change…): put the chart back
  let tkObs = null;
  function watch() {
    const s = document.getElementById('tkSlide'); if (!s || tkObs) return;
    tkObs = new MutationObserver(() => {
      // put it back in the same frame (a mutation callback runs before the screen is painted): no gap, no blink
      if (s.classList.contains('open') && !s.querySelector('.sc-tk')) inject();
    });
    tkObs.observe(s, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    inject();
  }
  new MutationObserver(watch).observe(document.body, { childList: true });
  window.SweepChart = { form: TKC, reload: () => { TKC.key = ''; return loadTk(); } };
  watch();


  /* ───────────── calendar: Monday to Friday only (CME is closed on weekends) ───────────── */
  if (typeof calDays === 'function') calDays = function () { return 5; };

  /* ───────────── sample data: a short preview built on real CME candles ─────────────
   * About 12 recent market days (never weekends, always older than the licence delay), 1 to 3 NQ trades a day in the
   * New York morning. Entry at the real open of the entry candle; exit at the real close later on, or at the stop/target
   * when the real candles touched them first. Without market data, the previous generator is used. */
  if (typeof loadDemo === 'function') {
    const origDemo = loadDemo;
    const DT = {
      en: { confirm: 'Add a short preview (about 25 trades on real NQ candles, 5 sample accounts)? You can remove it later from Settings.', adding: 'Adding sample data…', added: 'Added {n} sample trades' },
      fr: { confirm: 'Ajouter un aperçu (environ 25 trades sur de vraies bougies NQ, 5 comptes d’exemple) ? Tu pourras le retirer dans les Réglages.', adding: 'Ajout des données d’exemple…', added: '{n} trades d’exemple ajoutés' },
      es: { confirm: '¿Añadir una vista previa (unos 25 trades sobre velas reales de NQ, 5 cuentas de ejemplo)? Podrás quitarla en Ajustes.', adding: 'Añadiendo datos de ejemplo…', added: '{n} trades de ejemplo añadidos' },
    };
    const dt = (k, p) => { let s = (DT[LANG] || DT.en)[k]; if (p) s = s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)); return s; };
    loadDemo = async function () {
      const rnd = (a, b) => a + Math.random() * (b - a), pick = (a) => a[Math.floor(Math.random() * a.length)], chance = (p) => Math.random() < p, q4 = (x) => Math.round(x * 4) / 4;
      const firms = [['demo-f-topstep', 'Topstep'], ['demo-f-lucid', 'Lucid'], ['demo-f-apex', 'Apex']].map(([id, name]) => ({ id, name, demo: true }));
      const accounts = [['demo-a1', 'demo-f-topstep', 'Account 1'], ['demo-a2', 'demo-f-topstep', 'Account 2'], ['demo-a3', 'demo-f-lucid', 'Account 1'], ['demo-a4', 'demo-f-lucid', 'Account 2'], ['demo-a5', 'demo-f-apex', 'Account 1']]
        .map(([id, firm_id, name]) => ({ id, firm_id, name, starting_balance_c: 5e6, status: 'active', created_on: addDays(todayStr(), -40), notes: 'Sample account — sample rule values', demo: true,
          rules: { target_c: 3e5, dd_c: 2e5, dd_type: 'eod', dd_lock: true, dll_c: 1e5, consistency_pct: 50, min_days: 5 } }))
        // sample money types: two evaluations, two funded accounts (they have the sample payouts), one live account
        .map((a) => { const t = { 'demo-a1': 'funded', 'demo-a3': 'funded', 'demo-a5': 'live' }[a.id] || 'eval'; a.money_type = t; a.phase = t; if (t !== 'eval') { a.rules = Object.assign({}, a.rules, { target_c: null, min_days: null }); } return a; });
      const setups = ['Liquidity sweep', 'FVG retest', 'Break of structure', 'Opening range'];
      // recent market days, oldest first
      const days = [];
      for (let h = 2; days.length < 12 && h < 45; h++) { const d = addDays(todayStr(), -h), w = pd(d).getDay(); if (w !== 0 && w !== 6) days.unshift(d); }
      const trades = [], journals = [];
      for (const d of days) {
        const w0 = wall(`${d} 09:30`), utc = w0 - (ny(w0) - w0);
        let r;
        try { r = await apiJSON(`api/chart/bars?symbol=NQ&from=${utc}&to=${utc + 4 * 3600}&tf=1m`); } catch (x) { r = null; }
        if (!r || r.status !== 'ok' || !r.bars || r.bars.length < 60) continue;
        const B = r.bars, n = Math.floor(rnd(1, 3.6)), acct = pick(accounts).id;
        let at = Math.floor(rnd(2, 20)), dayNet = 0, losses = 0;
        for (let k = 0; k < n && at < B.length - 30; k++) {
          const good = chance(0.8), revenge = losses > 0 && chance(0.35);
          const iIn = at, hold = Math.floor(rnd(3, 22)), iOut0 = Math.min(B.length - 1, iIn + hold);
          const entry = B[iIn][1], move = B[iOut0][4] - entry;
          const dir = chance(good ? 0.62 : 0.45) ? (move >= 0 ? 'long' : 'short') : (move >= 0 ? 'short' : 'long');
          const risk = q4(rnd(11, 22)), stop = dir === 'long' ? entry - risk : entry + risk, target = dir === 'long' ? entry + 2 * risk : entry - 2 * risk;
          // walk the real candles: stop or target first, else the close of the last candle
          let iOut = iOut0, exit = B[iOut0][4];
          for (let i = iIn; i <= iOut0; i++) {
            const lo = B[i][3], hi = B[i][2];
            if (dir === 'long' ? lo <= stop : hi >= stop) { iOut = i; exit = stop; break; }
            if (dir === 'long' ? hi >= target : lo <= target) { iOut = i; exit = target; break; }
          }
          const qty = revenge ? Math.min(4, 2 + losses) : pick([1, 1, 2, 2, 3]);
          const tIn = hms(ny(B[iIn][0])), tOut = hms(ny(B[iOut][0] + (exit === B[iOut0][4] ? 45 : 20)));
          const disc = {}; DEFAULT_QS.forEach(([id]) => { disc[id] = 'y'; });
          if (revenge) { disc.revenge = 'n'; disc.emotion = 'n'; } else if (!good) disc[pick(['confirm', 'entry', 'stop', 'plan', 'chase'])] = 'n';
          const t0 = { id: 'demo-t-' + uid(), demo: true, instrument: 'NQ', account_id: acct, date: d, entry_time: tIn, exit_time: tOut, session: sessionFor(tIn.slice(0, 5)),
            direction: dir, contracts: qty, entry, exit, stop, target, pnl_c: calcPnl(dir, entry, exit, qty, 'NQ'), pnl_manual: false, fees_c: qty * 420,
            setup: pick(setups), tags: [], notes: '', review: {}, shots: [], discipline: disc,
            emo: { before: revenge ? ['Frustrated'] : good ? [pick(['Calm', 'Focused', 'Patient', 'Confident'])] : [pick(['FOMO', 'Impulsive', 'Hesitant'])], after: [], confidence: good ? 4 : 2, execution: good ? 4 : 2, quality: good ? 4 : 2 } };
          t0.grade = good ? (tNet(t0) > 0 ? 'A' : 'B') : (tNet(t0) > 0 ? 'C' : 'D');
          trades.push(t0); dayNet += tNet(t0); losses = tNet(t0) < 0 ? losses + 1 : 0;
          at = iOut + Math.floor(rnd(8, 40));
        }
        journals.push({ id: d, date: d, demo: true, pre: { bias: pick(['bullish', 'bearish', 'neutral']), focus: pick(['Do not add to losing positions.', 'Wait for confirmation.', 'Two trades maximum.']), max_loss: '1000', max_trades: '3' },
          post: { grade: dayNet > 0 ? pick(['A', 'B']) : pick(['B', 'C', 'D']), followed: dayNet > 0 ? 'yes' : pick(['partly', 'no']) } });
      }
      if (!trades.length) {      // no market data on this install: the previous generator (weekdays only)
        const c = window.confirm; window.confirm = () => true;
        try { await origDemo(); } finally { window.confirm = c; }
        return;
      }
      const payouts = [
        { id: 'demo-p1', account_id: 'demo-a1', firm_id: 'demo-f-topstep', amount_c: 2e5, status: 'paid', request_date: addDays(todayStr(), -20), approval_date: addDays(todayStr(), -18), payment_date: addDays(todayStr(), -16), demo: true },
        { id: 'demo-p2', account_id: 'demo-a3', firm_id: 'demo-f-lucid', amount_c: 15e4, status: 'requested', request_date: addDays(todayStr(), -4), demo: true },
      ];
      const expenses = [['demo-e1', 'demo-f-topstep', 'demo-a1', 'evaluation', 4900], ['demo-e2', 'demo-f-topstep', 'demo-a2', 'evaluation', 4900], ['demo-e3', 'demo-f-lucid', '', 'evaluation', 8e3], ['demo-e4', 'demo-f-apex', 'demo-a5', 'activation', 8500]]
        .map(([id, firm_id, account_id, category, amount_c], i) => ({ id, firm_id, account_id, category, amount_c, date: addDays(todayStr(), -38 + i * 8), notes: '', demo: true }));
      try {
        await loadEcon(days[0], todayStr());
        for (const x of trades) Object.assign(x, newsContext(etEpoch(x.date + ' ' + x.entry_time), etEpoch(x.date + ' ' + x.exit_time)));
      } catch (x) { /* news context is optional */ }
      // B16: the app's own window (never the browser's), with the exact number of trades it will add
      const ASK = { en: ['Add sample data?', 'Adds {n} sample trades on real NQ candles, in {a} sample accounts. You can remove them anytime in Settings.', 'Add {n} trades'],
        fr: ['Ajouter des données d’exemple ?', 'Ajoute {n} trades d’exemple sur de vraies bougies NQ, dans {a} comptes d’exemple. Tu peux les retirer quand tu veux dans les Réglages.', 'Ajouter {n} trades'],
        es: ['¿Añadir datos de ejemplo?', 'Añade {n} operaciones de ejemplo sobre velas reales de NQ, en {a} cuentas de ejemplo. Puedes quitarlas cuando quieras en Ajustes.', 'Añadir {n} operaciones'] }[LANG] || null;
      const A = (ASK || ['Add sample data?', 'Adds {n} sample trades on real NQ candles, in {a} sample accounts.', 'Add {n} trades']).map((x) => x.replace('{n}', trades.length).replace('{a}', accounts.length));
      if (window.SweepUndo && SweepUndo.demo) { if (!(await SweepUndo.demo(trades.length, accounts.length))) return; } else if (window.SweepUndo && SweepUndo.ask) { if (!(await SweepUndo.ask(A[0], A[1], A[2], false))) return; }
      trades.forEach((x) => { x.session_date = true; });
      toast(dt('adding'), { ms: 60000 });
      try {
        await bulkPut('firms', firms); await bulkPut('accounts', accounts); await bulkPut('trades', trades); await bulkPut('journals', journals);
        await bulkPut('payouts', payouts); await bulkPut('expenses', expenses);
        toast(dt('added', { n: trades.length }));
      } catch (x) { toast(saveErr(x)); }
    };
  }

  /* ───────────── licence mention (Settings, bottom) ───────────── */
  if (typeof render === 'function') {
    const appRender = render;
    render = function () {
      const out = appRender.apply(this, arguments);
      try {
        // trade page re-rendered by an edit: the drawn chart goes back in the same frame (no empty placeholder, no jump)
        if (route().v === 'trade' && live && live.wrap && !document.body.contains(live.wrap)) {
          const nw = document.querySelector('#main .tr-chart'), id = (route().a || [])[0] || (location.hash.split('/')[1] || '');
          const doc = typeof getDoc === 'function' ? getDoc('trades', id) : null;
          if (nw && doc && live.tradeId === doc.id && live.sig === chartSig(doc)) nw.replaceWith(live.wrap);
        }
        if (route().v === 'settings') {
          const main = document.getElementById('main');
          if (main && !main.querySelector('.sc-legal')) { const p = document.createElement('p'); p.className = 'sc-legal'; p.setAttribute('data-noi18n', ''); p.innerHTML = `${esc(t('legal')).replace('tradingview.com', '<a href="https://www.tradingview.com/" target="_blank" rel="noopener">tradingview.com</a>')}`; main.append(p); }
        }
      } catch (x) { /* never blocks */ }
      return out;
    };
  }
})();
