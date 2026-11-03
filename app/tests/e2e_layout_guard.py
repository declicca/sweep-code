"""
Sweep — the layout guard (tour visuel of 2 Nov., docs/parcours/TOUR-VISUEL-2026-11-02.md), Playwright:
  python3 tests/e2e_layout_guard.py http://127.0.0.1:8095 /tmp/show_state.json
Every page, the main sheets (+, P&L, plan, review, search, notifications, My progress), the welcome of a new trader (its account
form, its first plan, its first trade) and a trade's page — phone 390 × 844 touch and computer 1300 × 850, light in EN, FR and ES,
dark in FR. It fails on:
 1 a page wider than the screen
 2 a zone scrolling sideways by 1 to 23 px (a table or a line a hair too wide)
 3 a button, chip, segment or field whose content is wider than itself (cut, or its text spilling out)
 4 a button's or chip's label of 4 words at most on 2 lines
 5 an element sticking out of its card by more than 2 px (lines that scroll on purpose excluded)
 6 siblings of one row (tiles, buttons, chips) of uneven heights (more than 4 px) or not aligned (more than 3 px)
 7 at the end of a page, something to touch left under the tab bar or the Ask Sweep button
 8 a button with neither a visible text nor an icon
 9 a link with two arrows in a row (« › › »)
 10 an English label left on a French or Spanish page (one of the dictionary's labels, shown whole: « Most active »)
Each failure says the screen, the size, the language, the theme and the element; with SHOTS=<folder>, a screenshot with the
element outlined in red. EXCEPTIONS lists what is let through, each with its reason (empty at the start).
"""
import json, os, random, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
SHOTS = os.environ.get('SHOTS')
if SHOTS: os.makedirs(SHOTS, exist_ok=True)
# (screen, kind of failure, element's text or selector part): why it is let through
EXCEPTIONS = {
  ('trade', '3 a segmented control', '15s 30s'): 'the chart\'s timeframes: a line that scrolls on purpose on a phone, its edge fades (tour of 1 Nov., C7)',
}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

# the measure (from docs/parcours/tour-visuel-robot.py, its CHECK, tuned there against false alarms), plus rules 8 and 9
CHECK = r"""(atEnd) => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && +s.opacity > 0.05; };
  const nm = (e) => ((e.innerText || e.value || e.getAttribute('aria-label') || e.placeholder || e.tagName) + '').trim().replace(/\s+/g, ' ').slice(0, 48);
  const where = (e) => { const p = []; let a = e; for (let i = 0; a && i < 4; i++, a = a.parentElement) p.push(a.id ? '#' + a.id : (a.className && typeof a.className === 'string' && a.className.trim() ? '.' + a.className.trim().split(/\s+/)[0] : a.tagName.toLowerCase())); return p.reverse().join(' > '); };
  const clipsInside = (p, e) => { for (let a = p; a && a !== e; a = a.parentElement) { const s = getComputedStyle(a); if (s.overflowX !== 'visible') return true; } return false; };   // text cut on purpose (« … ») inside it
  const textRects = (e, all) => { const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), rs = []; let n; while ((n = w.nextNode())) { if (!n.textContent.trim()) continue; const p = n.parentElement; if (!p || !vis(p) || (!all && clipsInside(p, e))) continue; const rg = document.createRange(); rg.selectNodeContents(n); rs.push(...[...rg.getClientRects()].filter((q) => q.width > 0.5)); } return rs; };
  const rendered = (e) => !(e.innerText === '' && e.textContent.trim() !== '') && !e.closest('details:not([open]) > :not(summary)');   // (a folded block's content keeps a size, not a rendering)
  const clipRect = (e) => { let L = -1e9, T = -1e9, Rr = 1e9, Bb = 1e9; for (let a = e.parentElement; a && a !== document.documentElement; a = a.parentElement) { const s = getComputedStyle(a); if (s.overflowX !== 'visible' || s.overflowY !== 'visible') { const q = a.getBoundingClientRect(); L = Math.max(L, q.left); T = Math.max(T, q.top); Rr = Math.min(Rr, q.right); Bb = Math.min(Bb, q.bottom); } } return { L, T, R: Rr, B: Bb }; };
  const inHScroll = (e, stop) => { for (let a = e.parentElement; a && a !== stop; a = a.parentElement) { const s = getComputedStyle(a); if (/(auto|scroll)/.test(s.overflowX) && a.scrollWidth > a.clientWidth + 1) return true; } return false; };
  const I = [...document.querySelectorAll('button, a[href], [role=button], [role=tab], input:not([type=hidden]), select, textarea, .chip, .pill, .badge, .tag, summary')].filter((e) => vis(e) && rendered(e));
  const out = []; let id = 0; const add = (k, e, x) => { if (e && e.setAttribute) e.setAttribute('data-guard', String(++id)); out.push({ k, name: e ? nm(e) : '', at: e ? where(e) : '', x, id }); };
  const W = innerWidth, H = innerHeight;
  for (const e of I) {
    const r = e.getBoundingClientRect(); if (r.right < 0 || r.left > W) continue;
    const cr = clipRect(e), iw = Math.max(0, Math.min(r.right, cr.R) - Math.max(r.left, cr.L)), ih = Math.max(0, Math.min(r.bottom, cr.B) - Math.max(r.top, cr.T));
    if (iw * ih < 0.5 * r.width * r.height) continue;
    for (let a = e.parentElement; a && a !== document.body; a = a.parentElement) {   // 3. cut by an ancestor that clips (lines of chips that scroll: by design)
      const s = getComputedStyle(a); if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
      const R = a.getBoundingClientRect(), hs = /(auto|scroll)/.test(s.overflowX) && a.scrollWidth > a.clientWidth + 1, vs = /(auto|scroll)/.test(s.overflowY) && a.scrollHeight > a.clientHeight + 1;
      const ox = Math.max(0, R.left - r.left) + Math.max(0, r.right - R.right), oy = Math.max(0, R.top - r.top) + Math.max(0, r.bottom - R.bottom);
      if (!hs && ox > 1.5 && ox < r.width - 1) add('3 cut by its box', e, Math.round(ox) + ' px');
      if (!vs && oy > 1.5 && oy < r.height - 1) add('3 cut by its box', e, Math.round(oy) + ' px (top/bottom)');
      break;
    }
    const card = e.parentElement && e.parentElement.closest('.surface, .card, [class*="-card"], section');   // 5. out of its card
    if (card && card !== e && !inHScroll(e, card)) { const C = card.getBoundingClientRect(); const ox = Math.max(0, C.left - r.left) + Math.max(0, r.right - C.right); if (ox > 2 && C.width < W) add('5 out of its card', e, Math.round(ox) + ' px'); }
    if (/^(BUTTON|A)$/.test(e.tagName) || e.matches('.chip,.pill,.badge,.tag,[role=tab]')) {
      const s = getComputedStyle(e), tr = textRects(e);
      if (tr.length) { const L = Math.min(...tr.map((q) => q.left)), Rr = Math.max(...tr.map((q) => q.right)); const ox = Math.max(0, r.left - L) + Math.max(0, Rr - r.right); if (ox > 1.5) add('3 text wider than its button', e, Math.round(ox) + ' px'); }
      const t = (e.innerText || '').trim();
      if (t && !t.includes('\n') && t.split(/\s+/).length <= 4 && t.length < 34 && tr.length) {   // 4. a short label on 2 lines
        const fs = parseFloat(s.fontSize) || 14, tops = []; for (const q of tr) if (!tops.some((y) => Math.abs(y - q.top) < fs * 0.6)) tops.push(q.top);
        if (tops.length >= 2) add('4 short label on 2 lines', e, t);
      }
      const icon = [...e.querySelectorAll('svg, img, i, [class*=ic]')].some(vis) || e.matches('[class*=ic], .info, .sw-term') || getComputedStyle(e).backgroundImage !== 'none';
      const pseudo = ['::before', '::after'].some((ps) => { const q = getComputedStyle(e, ps), c = q.content; if (!c || ['none', 'normal'].includes(c)) return false; if (c !== '""') return true;
        const mk = q.webkitMaskImage || q.maskImage || 'none', ms = q.webkitMaskSize || q.maskSize || 'auto';   // an icon drawn by a mask shows only with its size set (« auto »: the SVG's own, often outside the box)
        return (mk !== 'none' && ms !== 'auto' && ms !== 'auto auto') || q.backgroundImage !== 'none'; });
      if (/^(BUTTON|A)$/.test(e.tagName) && !textRects(e, true).length && !icon && !pseudo && r.width >= 16 && r.height >= 16 && !e.matches('.g-dots > button, [class*=dot], [class*=swatch], .nav-fd, .cal .d'))   // 8. nothing to read nor to see (its label hidden: « Edit trade » at 44 px)
        add('8 a button with no text and no icon', e, Math.round(r.width) + '×' + Math.round(r.height) + (e.textContent.trim() ? ' — its label « ' + e.textContent.trim().slice(0, 24) + ' » hidden' : ''));
    }
    {   // 9. two arrows in a row: two « › » in its text, or a « › » ending it and a drawn chevron (::after) beside it
      const t = (e.innerText || '').trim(), af = getComputedStyle(e, '::after'), drawn = af.content && !['none', 'normal'].includes(af.content) && (af.content.includes('›') || (parseFloat(af.borderRightWidth) > 0 && af.borderRightStyle !== 'none' && !/rgba\(0, 0, 0, 0\)|transparent/.test(af.borderRightColor)));   // (a chevron drawn by its borders; an invisible ::after is a touch zone)
      if (/›\s*›/.test(t) || (/›$/.test(t) && drawn)) add('9 two arrows', e, t.slice(-14));
    }
    if (r.top >= 0 && r.bottom <= H && r.left >= 0 && r.right <= W) {   // 7. under the tab bar / Ask Sweep, once at the end of the page
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = document.elementFromPoint(cx, cy);
      if (h && h !== e && !e.contains(h) && !h.contains(e)) {
        const bar = h.closest && h.closest('#bottomnav, .ask-fab, #askFab');
        if (bar && atEnd && !(e.closest && e.closest('#bottomnav, .ask-fab, #askFab'))) add('7 under the tab bar or Ask Sweep', e, nm(bar));
      }
    }
  }
  const rows = new Map();   // 6. a row of the same kind: uneven heights or not aligned
  for (const e of I) { const p = e.parentElement; if (!p) continue; const s = getComputedStyle(p); if (!/flex|grid/.test(s.display)) continue; (rows.get(p) || rows.set(p, []).get(p)).push(e); }
  for (const [p, es] of rows) {
    const same = es.filter((e) => e.parentElement === p && e.tagName === es[0].tagName && (e.className || '').split(' ')[0] === (es[0].className || '').split(' ')[0]);
    if (same.length < 2) continue;
    const rs = same.map((e) => e.getBoundingClientRect());
    const byLine = []; rs.forEach((r, i) => { const l = byLine.find((g) => Math.abs(g.c - (r.top + r.height / 2)) < r.height / 2); l ? l.m.push(i) : byLine.push({ c: r.top + r.height / 2, m: [i] }); });
    for (const g of byLine) { if (g.m.length < 2) continue; const hs = g.m.map((i) => rs[i].height), cs = g.m.map((i) => rs[i].top + rs[i].height / 2);
      if (Math.max(...hs) - Math.min(...hs) > 4) add('6 uneven heights in a row', same[g.m[0]], hs.map(Math.round).join(' / ') + ' px');
      else if (Math.max(...cs) - Math.min(...cs) > 3) add('6 not aligned in a row', same[g.m[0]], Math.round(Math.max(...cs) - Math.min(...cs)) + ' px'); }
  }
  for (const g of document.querySelectorAll('.onb-steps, [class*="-steps"]')) {   // 4. a row of 2 or 3 steps on 2 lines (« 3 Your first trade » below)
    if (!vis(g) || !rendered(g)) continue; const k = [...g.children].filter(vis); if (k.length < 2 || k.length > 4) continue;
    const tops = k.map((x) => x.getBoundingClientRect().top), h = Math.min(...k.map((x) => x.getBoundingClientRect().height));
    if (Math.max(...tops) - Math.min(...tops) > h / 2) add('4 a row of steps on 2 lines', g, (g.innerText || '').replace(/\s+/g, ' ').slice(0, 40));
  }
  for (const g of document.querySelectorAll('.seg, [role=tablist], .g-seg3, .g-seg4')) {   // its options past its edges, or hidden behind a scroll (the options themselves: their touch zones may go past on purpose)
    if (!vis(g) || !rendered(g)) continue; const G = g.getBoundingClientRect(), k = [...g.children].filter(vis).map((x) => x.getBoundingClientRect()); if (!k.length) continue;
    const d = Math.max(0, Math.max(...k.map((q) => q.right)) - G.right) + Math.max(0, G.left - Math.min(...k.map((q) => q.left)));
    if (d > 1) add('3 a segmented control wider than its box', g, Math.round(d) + ' px (' + (g.innerText || '').replace(/\s+/g, ' ').slice(0, 30) + ')');
    for (const o of [...g.children].filter(vis)) { const r = document.createRange(); r.selectNodeContents(o); const tw = r.getBoundingClientRect().width;   // an option squeezed to its label, no room left around it (the grade A–F run together as « ABCDF » at 1300, 2 Nov.)
      if (tw > 0 && tw + 6 > o.getBoundingClientRect().width) add('3 an option squeezed to its label', o, Math.round(o.getBoundingClientRect().width) + ' px for ' + Math.round(tw) + ' px (' + (o.innerText || '').trim().slice(0, 20) + ')'); } }
  for (const g of document.querySelectorAll('svg.chart')) {   // 3. the numbers of a chart's axes: cut at its edge, or two dates run together (« 12 oct.15 oct. », « 0 k $ », 3 Nov.)
    if (!vis(g) || !rendered(g)) continue; const G = g.getBoundingClientRect(), open = getComputedStyle(g).overflow === 'visible', tx = [...g.querySelectorAll(':scope > text')].filter((t) => t.style.display !== 'none' && t.getClientRects().length);
    for (const t of tx) { const r = t.getBoundingClientRect(); if (!open && (r.left < G.left - 1 || r.right > G.right + 1)) add('3 a chart number cut at its edge', t, Math.round(Math.max(G.left - r.left, r.right - G.right)) + ' px'); }
    const y = Math.max(...tx.map((t) => +t.getAttribute('y') || 0)), xs = tx.filter((t) => +t.getAttribute('y') === y).map((t) => [t, t.getBoundingClientRect()]).sort((a, b) => a[1].left - b[1].left);
    for (let i = 1; i < xs.length; i++) if (xs[i][1].left < xs[i - 1][1].right + 2) add('3 two dates of a chart run together', xs[i][0], (xs[i - 1][0].textContent + xs[i][0].textContent).slice(0, 30));
  }
  for (const a of document.querySelectorAll('*')) { const s = getComputedStyle(a); if (!/(auto|scroll)/.test(s.overflowX) || !vis(a)) continue; const d = a.scrollWidth - a.clientWidth; if (d > 0 && d < 24) add('2 a thin side scroll', a, d + ' px'); }   // 2
  const ov = document.documentElement.scrollWidth - W; if (ov > 0) out.push({ k: '1 page wider than the screen', name: '', at: '', x: ov + ' px', id: 0 });   // 1
  return out;
}"""
ENG = """(() => {   // 10. an English label left on a French or Spanish page: one of the dictionary's own English labels, shown whole
  if (typeof I18N_D !== 'function' || typeof LANG === 'undefined' || LANG === 'en') return [];
  const d = I18N_D(), keys = new Set(Object.keys(d).filter((k) => d[k] && d[k] !== k && k.length >= 9 && /^[A-Z][a-z]+( [a-z]+)+$/.test(k))), out = new Set();
  for (const e of document.querySelectorAll('#main *, [role=dialog] *, .nav-am.open *, #gSheet *')) {
    if (!e.getClientRects().length || /^(INPUT|TEXTAREA|SELECT|OPTION|SCRIPT|STYLE)$/.test(e.tagName)) continue;
    const t = (e.innerText || '').replace(/\\s+/g, ' ').trim().replace(/ i$/, ''); if (t.length < 9 || t.length > 60) continue;
    if (keys.has(t)) out.add(t);
  }
  return [...out];
})()"""
TOEND = "(() => { const s = [...document.querySelectorAll('[role=dialog], #gSheet .g-sheet, #gSheet, .nav-am.open, #tkSlide.open')].find((e) => e.offsetParent && e.scrollHeight > e.clientHeight + 4); if (s) s.scrollTop = s.scrollHeight; else scrollTo(0, document.documentElement.scrollHeight); })()"
CLOSE = "(() => { document.querySelectorAll('#gSheet [data-g=close], .nav-am.open [data-am=close], aside.open [data-close], .nav-dlg.open [data-close]').forEach((b) => b.click()); if (typeof closeTicket === 'function') try { closeTicket() } catch (e) {} })()"

def check(pg, screen, tag, scroll=True):
  global fails
  seen = set(); found = []
  for at_end in ((False, True) if scroll else (False,)):
    if at_end: pg.evaluate(TOEND); pg.wait_for_timeout(450)
    for x in pg.evaluate(CHECK, at_end):
      key = (x['k'], x['name'], x['at'])
      if key in seen: continue
      seen.add(key)
      if any(screen.startswith(s) and x['k'].startswith(k) and part in (x['name'] + ' ' + x['at']) for (s, k, part) in EXCEPTIONS): continue
      found.append(x)
      if SHOTS and x['id']:
        pg.evaluate("(i) => { const e = document.querySelector(`[data-guard='${i}']`); if (e) { e.style.outline = '3px solid red'; e.style.outlineOffset = '1px'; e.scrollIntoView({ block: 'center', inline: 'nearest' }); } }", x['id'])
        pg.screenshot(path=os.path.join(SHOTS, f"{tag}-{screen}-{len(found)}.png"))
        pg.evaluate("(i) => { const e = document.querySelector(`[data-guard='${i}']`); if (e) e.style.outline = ''; }", x['id'])
  for t in pg.evaluate(ENG): found.append({'k': '10 an English label on a French or Spanish page', 'name': t, 'at': '', 'x': '', 'id': 0})
  ok(not found, f"{tag} {screen}: nothing out of place" + ('' if not found else ' — ' + ' | '.join(f"{x['k']}: « {x['name']} » at {x['at']} ({x['x']})" for x in found[:6])))

def pages(p, phone, lang, theme):
  tag = f"{390 if phone else 1300}-{lang}-{theme}"
  br = p.chromium.launch()
  c = br.new_context(storage_state=STATE, viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone,
                     locale={'fr': 'fr-CA', 'es': 'es-ES', 'en': 'en-US'}[lang], color_scheme=theme)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1') } catch (e) {}" % lang)
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
  pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=20000); pg.wait_for_timeout(2000)
  acc = pg.evaluate("(S.accounts.find((a) => a.status !== 'archived') || {}).id")
  # a trade logged on several accounts (its page has the folded « Also on … » line): one of the sample's, else a copy made for the guard
  tid = pg.evaluate("""(() => { const c = (S.trades || []).find((t) => !t.untracked && t.copy_group && S.trades.filter((x) => x.copy_group === t.copy_group).length > 1); if (c) return c.id;
    const t = (S.trades || []).filter((x) => !x.untracked).slice(-1)[0], b = (S.accounts || []).find((a) => a.status !== 'archived' && a.id !== t.account_id); if (!t || !b) return t && t.id;
    editDoc('trades', t.id, (x) => { x.copy_group = 'lg-guard'; }); put('trades', Object.assign({}, t, { id: 'lg-guard-copy', account_id: b.id, copy_group: 'lg-guard' })); return t.id; })()""")
  t2 = pg.evaluate("(S.trades.filter((t) => !t.untracked && !t.copy_group).sort((a, b) => Math.abs(b.pnl_c || 0) - Math.abs(a.pnl_c || 0))[0] || {}).id")   # and the one with the widest result alone (its amount sets the width of the head: the grade A–F)
  pg.wait_for_timeout(800)
  for h in ('dashboard', 'trades', 'calendar', 'journal', 'analytics', 'accounts', 'payouts', 'news', 'settings', 'progress', 'trade/' + str(tid), 'trade/' + str(t2), 'account/' + str(acc)):
    pg.evaluate("(h) => { location.hash = h }", '#' + h); pg.wait_for_timeout(1500); pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(200)
    check(pg, h.split('/')[0] + ('-copied' if h == 'trade/' + str(tid) else ''), tag)
  tap = (lambda l: l.tap()) if phone else (lambda l: l.click())
  sheets = [('sheet-plus', "openTicket(null)", None), ('sheet-pnl', "openTicket(null)", '.nav-am.open [data-am=no-shot]'),
            ('sheet-plan', "SweepGame.openPlan()", None), ('sheet-review', "SweepGame.openReview()", None),
            ('sheet-progress', "SweepGame.open && SweepGame.open('hub')", None)]
  for name, js, then in sheets:
    pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(1200)
    try:
      pg.evaluate(js); pg.wait_for_timeout(1100)
      if then: tap(pg.locator(then).first); pg.wait_for_timeout(900)
      check(pg, name, tag)
    except Exception as e: ok(False, f'{tag} {name}: could not open ({str(e)[:120]})')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300); pg.evaluate(CLOSE); pg.wait_for_timeout(400)
  for name, sel in (('sheet-notifications', 'button[aria-label*="otificati"], .nt-bell, #ntBell'), ('sheet-search', 'button[aria-label*="earch"], button[aria-label*="echerch"], button[aria-label*="uscar"]')):
    pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(1000)
    l = pg.locator(sel).first
    if l.count() and l.is_visible():
      tap(l); pg.wait_for_timeout(1000); check(pg, name, tag, scroll=False)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300); pg.evaluate(CLOSE); pg.wait_for_timeout(300)
  pg.evaluate("(() => { if (getDoc('trades', 'lg-guard-copy')) { remove('trades', 'lg-guard-copy'); (S.trades || []).filter((t) => t.copy_group === 'lg-guard').forEach((t) => editDoc('trades', t.id, (x) => { delete x.copy_group; })); } })()"); pg.wait_for_timeout(1200)   # (the shared trader as it was)
  ok(not errs, f'{tag}: no page error ({errs[:2]})')
  br.close()

def welcome(p, phone, lang, theme):
  tag = f"{390 if phone else 1300}-{lang}-{theme}"
  br = p.chromium.launch()
  c = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone,
                     locale={'fr': 'fr-CA', 'es': 'es-ES', 'en': 'en-US'}[lang], color_scheme=theme)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1') } catch (e) {}" % lang)
  try: d = sqlite3.connect(os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')); d.execute('DELETE FROM attempts'); d.commit(); d.close()   # (8 sign-ups in a row: not a burst to refuse)
  except Exception: pass
  r = c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'lg%07d@t.dev' % random.randint(0, 9999999), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb]', timeout=20000); pg.wait_for_timeout(900)
  check(pg, 'welcome', tag)
  pg.evaluate("scrollTo(0, 0)")
  for s in ('form[data-form=account] [data-st-ph0=eval]', '[data-st-firm=topstep]'):
    if pg.locator(s).count(): pg.locator(s).first.click(); pg.wait_for_timeout(250)
  if pg.locator('[data-st-size="50000"]').count(): pg.locator('[data-st-size="50000"]').first.click(); pg.wait_for_timeout(250)
  pg.locator('[data-onb-fn]').click(); pg.keyboard.type('Léa'); pg.locator('.nav-onb-me [data-exp="new"]').click(); pg.wait_for_timeout(600)
  pg.evaluate("scrollTo(0, 0)"); check(pg, 'welcome-filled', tag)
  pg.locator('form[data-form=account][data-onb] [type=submit]').click(); pg.wait_for_timeout(2500)
  if pg.locator('#gSheet').count(): check(pg, 'welcome-plan', tag)
  pg.keyboard.press('Escape'); pg.wait_for_timeout(300); pg.evaluate(CLOSE); pg.wait_for_timeout(500)
  try:
    pg.evaluate("openTicket(null)"); pg.wait_for_timeout(1000)
    if pg.locator('.nav-am.open [data-am=no-shot]').count(): (pg.locator('.nav-am.open [data-am=no-shot]').first.tap() if phone else pg.locator('.nav-am.open [data-am=no-shot]').first.click()); pg.wait_for_timeout(900)
    check(pg, 'welcome-first-trade', tag)
  except Exception as e: ok(False, f'{tag} welcome-first-trade: could not open ({str(e)[:120]})')
  ok(not errs, f'{tag} welcome: no page error ({errs[:2]})')
  br.close()

with sync_playwright() as p:
  for phone in (True, False):
    for lang, theme in (('en', 'light'), ('fr', 'light'), ('es', 'light'), ('fr', 'dark')):
      if os.environ.get('GUARD_ONLY') and f"{390 if phone else 1300}-{lang}-{theme}" not in os.environ['GUARD_ONLY'].split(','): continue   # (while fixing: one size, language and theme)
      pages(p, phone, lang, theme)
      welcome(p, phone, lang, theme)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
