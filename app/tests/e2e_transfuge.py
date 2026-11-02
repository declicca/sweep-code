"""
Sweep — audit « le transfuge » (2 Nov. 2026, docs/parcours/AUDIT-TRANSFUGE-2026-11-02.md): the 16 reflexes of a trader who
comes from Tradovate / TopstepX and Tradezella / TraderSync, each one checked, Playwright:
  python3 tests/e2e_transfuge.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
A new trader with 5 Topstep accounts, two trades today on « Combine 150K » copied on the others (a long and a short, both
winners), a loss the day before, his plan (max loss, 3 trades) and his own setups. Six runs spread over the combinations:
390 × 844 (touch) and 1300 × 850, light and dark, EN / FR / ES.
 R1 ⌘K opens the search (« / » puts the cursor in « Search trades »; the phone: the header's search button)
 R2 « N » opens « Add a trade », Escape closes it (the phone: the « + » of the tab bar)
 R3 a day of the calendar opens that day's journal
 R4 the period filter is on Trades and on Stats, the same
 R5 Import: Tradovate, Rithmic, TopstepX and TradingView detected, « How to export »
 C1 « Now »: the day's P&L first (« +821,60 $ aujourd'hui · 2/3 trades · … restants »), visible without scrolling
 C2 Long / Short (and the L / S pills) in neutral ink, never in the colours of a gain or a loss
 C3 the symbol: 3rd column of the computer table (after date and time), on each phone row
 C4 the whole table at 1300 px: no side scroll, no « Session » column, the account by its short name (full name on hover)
 C5 sorting by a header keeps it in the trader's language, arrow included
 C6 the duration « 8 min », never « 08:00 »
 G1 the trade page opens on « NQ · Long · 1 » and this account's P&L; the other accounts folded in one line « Also on 4 accounts ·
    total … », no « Also on » banner
 G2 one name for the action: « Add a trade » (rail, title row, routine, tab bar), no « + Add a trade » row in the table
 G3 one name for the measure: « Discipline » (table, trade page)
 G4 Stats: no second calendar, a « Calendar › » link to Trades › Calendar
 G5 setups: the trader's own first; the common ones in his language, without doubles, behind « + Other »
Also: the phone's Sweep AI button covers nothing once the page is still; « Drawdown room » in full (never « Marge DD »); no English
in French or Spanish (the approach of e2e_no_english_in_fr_es); no page error; nothing wider than the window.
"""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try:
    import sqlite3; d = sqlite3.connect(DB, timeout=10); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
N = lambda s: re.sub(r'\s+', ' ', str(s).replace(' ', ' ').replace(' ', ' ')).strip()

X = {
  'en': {'now': '+$821.60 today · 2/3 trades', 'sym': 'Symbol', 'acc': 'Account', 'disc': 'Discipline', 'add': 'Add a trade', 'dur': '8 min',
         'also': 'Also on 4 accounts · total', 'cal': 'Calendar ›', 'other': '+ Other', 'dd': 'Drawdown room', 'ddOld': 'DD room', 'cat': 'Liquidity Sweep',
         'catNo': ['Opening Range Breakout', 'Break & Retest', 'Fair Value Gap'], 'catEn': [], 'none': 'No trades match these filters.'},
  'fr': {'now': '+821,60 $ aujourd’hui · 2/3 trades', 'sym': 'Symbole', 'acc': 'Compte', 'disc': 'Discipline', 'add': 'Ajouter un trade', 'dur': '8 min',
         'also': 'Aussi sur 4 comptes · total', 'cal': 'Calendrier ›', 'other': '+ Autre', 'dd': 'Marge de drawdown', 'ddOld': 'Marge DD', 'cat': 'Prise de liquidité',
         'catNo': ['Cassure du range d’ouverture', 'Opening Range Breakout', 'Break & Retest', 'Fair Value Gap'], 'catEn': ['Liquidity Sweep', 'VWAP Bounce', 'Gap Fill'], 'none': 'Aucun trade ne correspond à ces filtres.'},
  'es': {'now': '+821,60 $ hoy · 2/3 operaciones', 'sym': 'Símbolo', 'acc': 'Cuenta', 'disc': 'Disciplina', 'add': 'Añadir una operación', 'dur': '8 min',
         'also': 'También en 4 cuentas · total', 'cal': 'Calendario ›', 'other': '+ Otro', 'dd': 'Margen de drawdown', 'ddOld': 'Margen DD', 'cat': 'Barrido de liquidez',
         'catNo': ['Ruptura del rango de apertura', 'Opening Range Breakout', 'Break & Retest', 'Fair Value Gap'], 'catEn': ['Liquidity Sweep', 'VWAP Bounce', 'Gap Fill'], 'none': 'Ninguna operación coincide con estos filtros.'},
}
# the trader: 5 Topstep accounts; today 10:22 a long (8 min) on Combine 150K copied on the 4 others, 09:41 a short copied on 3;
# yesterday a losing short; his plan (max loss $2,000, 3 trades) and his own setups (in French, as the audit's trader)
SEED = """() => {
  const day = todayStr(), y = ymdAdd(day, -1), now = Date.now();
  put('firms', { id: 'tp', name: 'Topstep' });
  const A = (id, name, extra) => put('accounts', Object.assign({ id, name, firm_id: 'tp', starting_balance_c: 5000000, status: 'active', phase: 'funded', money_type: 'funded', created_on: ymdAdd(day, -30), rules: { dd_c: 200000, dd_type: 'eod' } }, extra || {}));
  A('C', 'Combine 150K', { starting_balance_c: 15000000, phase: 'eval', money_type: 'eval', rules: { dd_c: 450000, dd_type: 'eod' } }); A('X', 'XFA 50K'); A('F', 'Flex 50K'); A('P', 'PA 50K'); A('L', 'Live 50K');
  const T = (id, acc, o) => put('trades', Object.assign({ id, account_id: acc, date: day, instrument: 'NQ', contracts: 1, session: 'ny_am', fees_c: 420, setup: 'Retest de FVG', created_at: new Date(now).toISOString() }, o));
  const L1 = { direction: 'long', entry: 24413, exit: 24425, entry_time: '10:22', exit_time: '10:30', copy_group: 'g1' };
  T('t1', 'C', Object.assign({ pnl_c: 24000 }, L1)); T('t1x', 'X', Object.assign({ pnl_c: 9524 }, L1)); T('t1f', 'F', Object.assign({ pnl_c: 9524 }, L1)); T('t1p', 'P', Object.assign({ pnl_c: 9524 }, L1)); T('t1l', 'L', Object.assign({ pnl_c: 4972 }, L1));
  const S1 = { direction: 'short', entry: 24398.75, exit: 24369.25, entry_time: '09:41', exit_time: '09:50', copy_group: 'g2', setup: 'Cassure et retest' };
  T('t2', 'C', Object.assign({ pnl_c: 59000, created_at: new Date(now - 60000).toISOString() }, S1)); T('t2x', 'X', Object.assign({ pnl_c: 20000 }, S1)); T('t2f', 'F', Object.assign({ pnl_c: 20000 }, S1)); T('t2p', 'P', Object.assign({ pnl_c: 20000 }, S1));
  T('t0', 'C', { date: y, direction: 'short', entry: 24300, exit: 24315, entry_time: '10:05', exit_time: '10:50', pnl_c: -30000, setup: 'Opening range' });
  put('journals', { id: day, pre: { bias: 'bullish', max_loss: '2000', max_trades: 3 } });
  put('settings', Object.assign(structuredClone(S.settings), { setups: ['Retest de FVG', 'Cassure et retest', 'Opening range'] }));
  render(); return day; }"""
TXT = "(sel) => [...document.querySelectorAll(sel)].filter((e) => e.getClientRects().length).map((e) => e.textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim())"
# (from e2e_weekly_share) elements and text that run past the window, scrolling rows apart
WIDE = """(()=>{ const W = document.documentElement.clientWidth, out = [];
  const name = (e) => e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\\s+/).slice(0, 2).join('.');
  const inside = (e) => { for (let x = e; x; x = x.parentElement) { const c = getComputedStyle(x); if (x === document.body) break; if (c.position === 'fixed' || (x !== e && c.overflowX !== 'visible' && x.getBoundingClientRect().right <= W + .5)) return true; } return false; };
  document.querySelectorAll('body *').forEach((e) => { const r = e.getBoundingClientRect(); if (!r.width || inside(e)) return; if (r.right > W + .5) out.push(name(e) + ' ' + Math.round(r.right) + 'px'); });
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = tw.nextNode(); n; n = tw.nextNode()) { if (!n.textContent.trim() || inside(n.parentElement)) continue; const g = document.createRange(); g.selectNodeContents(n); const r = g.getBoundingClientRect();
    if (r.right > W + .5) out.push('text « ' + n.textContent.trim().slice(0, 30) + ' » in ' + name(n.parentElement) + ' ' + Math.round(r.right) + 'px'); }
  return out.slice(-8); })()"""
# C2: the colour of every Long / Short / L / S on the page against the colours of a gain and a loss
DIRS = """(() => { const probe = (c) => { const e = document.createElement('span'); e.className = c; document.getElementById('main').append(e); const v = getComputedStyle(e).color; e.remove(); return v; };
  const pos = probe('pos'), neg = probe('neg'), out = [];
  document.querySelectorAll('#main .tag-l, #main .tag-s, #main .trow-dir, #main .nav-tr-d, #main .trow-main b').forEach((e) => {
    if (!e.getClientRects().length) return; const c = getComputedStyle(e).color, bg = getComputedStyle(e).backgroundColor;
    if (c === pos || c === neg || bg.includes(pos.slice(4, -1)) || bg.includes(neg.slice(4, -1))) out.push(e.className + ' « ' + e.textContent.trim().slice(0, 20) + ' » ' + c + ' / ' + bg); });
  return { n: document.querySelectorAll('#main .tag-l, #main .tag-s, #main .trow-dir, #main .nav-tr-d').length, bad: out, pos, neg }; })()"""
# the phone's Sweep AI button, at rest: shown only over empty space
FAB = """(() => { const f = document.querySelector('.ask-fab'); if (!f || !document.body.classList.contains('ask-on')) return { shown: false, under: [] };
  const cs = getComputedStyle(f), shown = cs.display !== 'none' && +cs.opacity > 0.5 && !document.body.classList.contains('ux-fab-away');
  const r = f.getBoundingClientRect(), hit = (q) => q.width > 0 && q.height > 0 && q.left < r.right && q.right > r.left && q.top < r.bottom && q.bottom > r.top, under = [];
  if (shown) { const main = document.getElementById('main');
    main.querySelectorAll('a, button, input, select, img, svg').forEach((e) => { if (hit(e.getBoundingClientRect()) && getComputedStyle(e).visibility !== 'hidden') under.push(e.tagName + ' ' + (e.textContent || '').trim().slice(0, 20)); });
    const tw = document.createTreeWalker(main, NodeFilter.SHOW_TEXT), g = document.createRange();
    for (let n = tw.nextNode(); n; n = tw.nextNode()) { if (!n.textContent.trim()) continue; g.selectNodeContents(n); for (const q of g.getClientRects()) if (hit(q)) { under.push('« ' + n.textContent.trim().slice(0, 20) + ' »'); break; } } }
  return { shown, under: under.slice(0, 4) }; })()"""
# no English in French or Spanish (tests/e2e_no_english_in_fr_es.py): the phrases known to slip through and English-only words
PHRASES = (r"Not enough data|See all|Add a trade|New trade|Your routine|Trades in your plan|Win rate|No trades match|Net P&L|Logged on|Also on|Search trades|This week|This month|"
           r"Copy to|Copy this trade|stay in sync|Share trade card|Edit trade|Show \d+ more|not shown|Symbol|Account|Session|Duration|DD room|Marge DD|Margen DD|Calendar")
WORDS = r"the|your|you|with|without|this|these|those|have|been|were|will|would|should|could|which|what|why|already|never|always|none"
EN = re.compile(r"(?<![\w’'-])(" + PHRASES + r"|" + WORDS + r")(?![\w’'-])", re.I)
PAGETXT = """(() => { const root = document.querySelector('.main-wrap') || document.body, c = root.cloneNode(true);
  const own = new Set([...(S.trades || []).flatMap((t) => [t.setup, t.notes]), ...(S.accounts || []).flatMap((a) => [a.name, a.notes])].filter(Boolean));
  const w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT), out = [];
  while (w.nextNode()) { let v = w.currentNode.textContent; for (const o of own) if (o && v.includes(o)) v = v.split(o).join(' '); out.push(v); }
  return out.join('\\n'); })()"""

def run(p, lang, phone, dark):
  tag = f"{'390' if phone else '1300'}-{lang}-{'dark' if dark else 'light'}"; x = X[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], color_scheme='dark' if dark else 'light')
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tf%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Alex', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  day = pg.evaluate(SEED); pg.wait_for_timeout(2500)
  pg.reload(); pg.wait_for_selector('#main', timeout=20000); pg.wait_for_timeout(1500)
  english = []
  def look(where):   # no English in French / Spanish, nothing wider than the window
    if lang != 'en':
      for line in pg.evaluate(PAGETXT).split('\n'):
        for m in EN.finditer(line): english.append(f'{where}: « {m.group(1)} » in « {N(line)[:80]} »')
    w = pg.evaluate(WIDE); ok(not w, f'{tag} {where}: nothing wider than the window {w}')
  def go(h, sel='#main', t=1200):
    pg.evaluate(f"location.hash = '{h}'"); pg.wait_for_selector(sel, timeout=10000); pg.wait_for_timeout(t)
  tap = lambda sel: pg.locator(sel).first.tap() if phone else pg.locator(sel).first.click()

  # ── Today: C1, C2, G2 (routine), the button of Sweep AI
  go('#dashboard', '#main .nav-now')
  now = N(pg.evaluate("(document.querySelector('#main .nav-now-l') || {}).textContent || ''"))
  r1 = pg.evaluate("(() => { const e = document.querySelector('#main .nav-now-p'); if (!e) return null; const r = e.getBoundingClientRect(); return { b: r.bottom, h: innerHeight, cls: e.className, y: scrollY }; })()")
  ok(now.startswith(x['now']) and r1 and 'pos' in r1['cls'], f"{tag} C1 « Now » starts with the day's P&L « {x['now']} … » ({now})")
  ok(r1 and r1['y'] == 0 and 0 < r1['b'] <= r1['h'], f"{tag} C1 the day's P&L visible without scrolling ({r1})")
  d = pg.evaluate(DIRS); ok(d['n'] > 0 and not d['bad'], f"{tag} C2 Today: L / S in neutral ink ({d['n']} marks, {d['bad'][:2]})")
  b2 = pg.evaluate(TXT, '#main .nav-rt-s [data-rt="trade"] .l, #main .nav-rt-s [data-rt="trade"] .s')
  ok(b2 and all(v == x['add'] for v in b2), f"{tag} G2 the routine says « {x['add']} » (long and short label: {b2})")
  look('Today')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'tf-today-{tag}.png'))
  if phone:
    for h in ['#dashboard', '#accounts']:
      go(h, '#main', 900)
      for yy in [0, 300, 700]:
        pg.evaluate(f'scrollTo(0, {yy})'); pg.wait_for_timeout(500)
        f = pg.evaluate(FAB); ok(not f['shown'] or not f['under'], f"{tag} the Sweep AI button covers nothing at rest ({h}, {yy} px: {f})")
      pg.evaluate('scrollTo(0, 0)')
    acc = ' '.join(pg.evaluate(TXT, '#main .acc-line'))
    ok(x['dd'] in acc and x['ddOld'] not in acc, f"{tag} Accounts: « {x['dd']} » in full ({acc[:90]})")
    ok(pg.evaluate("document.querySelector('#bottomnav .plus').getAttribute('aria-label')") == x['add'], f"{tag} G2 the tab bar's « + »: « {x['add']} »")
    look('Accounts')
  else:
    ok(N(pg.evaluate("document.querySelector('aside.side .new .lbl').textContent")) == x['add'], f"{tag} G2 the rail's button: « {x['add']} »")

  # ── Trades: C2, C3, C4, C5, G2, G3, R1 « / »
  go('#trades', '#main .tlist, #main table.tbl')
  ok(pg.locator('#main .nav-addrow').count() == 0, f'{tag} G2 no « + {x["add"]} » row in the list')
  d = pg.evaluate(DIRS); ok(d['n'] > 0 and not d['bad'], f"{tag} C2 Trades: Long / Short in neutral ink ({d['n']}, {d['bad'][:2]})")
  if phone:
    rows = pg.evaluate(TXT, '#main .trow:not(.trow-ut) .trow-main b')
    ok(rows and all(v.startswith('NQ ') for v in rows), f'{tag} C3 each row starts with its symbol ({rows[:2]})')
  else:
    ok(N(pg.evaluate("document.querySelector('aside.side .new .lbl').textContent")) == x['add'] and N(pg.evaluate("(document.querySelector('.nav-addtop') || {}).textContent || ''")) == x['add'], f"{tag} G2 the title row's button: « {x['add']} »")
    th = pg.evaluate(TXT, '#main table.tbl thead th')
    first = pg.evaluate(TXT, '#main table.tbl tbody tr:not(.cg-sub) td')
    ok(len(th) == 12 and th[2] == x['sym'] and first[2] == 'NQ', f"{tag} C3 « {x['sym']} » is the 3rd column, « NQ » ({th})")
    ok(not any(re.search(r'Session|Séance|Sesión', h) for h in th) and x['disc'] in th and 'Checklist' not in th, f"{tag} C4 / G3 no « Session » column, « {x['disc']} » ({th})")
    fit = pg.evaluate("(() => { const s = document.querySelector('#main .scroll-x'); return [s.scrollWidth, s.clientWidth]; })()")
    ok(fit[0] <= fit[1], f'{tag} C4 the whole table fits, no side scroll, not even 1 px ({fit})')   # (2 Nov., reste: 1019 in 1016 on Alex's data, the « ×5 accounts » pill)
    pill = pg.evaluate("(() => { const b = document.querySelector('#main table.tbl .cg-pill'); return b ? [b.textContent.trim(), b.getAttribute('aria-label')] : null })()")
    ok(bool(pill) and re.match(r'^×\d+$', pill[0]) and len(pill[1]) > len(pill[0]), f'{tag} C4 in the table the copies pill is « ×5 », its words on hover ({pill})')
    acc = pg.evaluate("(() => { const td = document.querySelector('#main table.tbl tbody tr:not(.cg-sub) td.tt-acc'); return [td.firstChild.textContent.trim(), td.title]; })()")
    ok(acc == ['Combine 150K', 'Topstep — Combine 150K'], f'{tag} C4 the account by its short name, the full one on hover ({acc})')
    pg.locator('#main th[data-sort="account"]').click(); pg.wait_for_timeout(700)
    h = N(pg.evaluate("document.querySelector('#main th[data-sort=\"account\"]').textContent"))
    ok(h in (x['acc'] + ' ↑', x['acc'] + ' ↓'), f"{tag} C5 sorted, the header stays « {h} »")
    pg.locator('#main th[data-sort="date"]').click(); pg.wait_for_timeout(500)
    if pg.locator('#main th[data-sort="date"]').inner_text().strip().endswith('↑'): pg.locator('#main th[data-sort="date"]').click(); pg.wait_for_timeout(500)
    pg.keyboard.press('/'); pg.wait_for_timeout(500)
    ok(pg.evaluate("document.activeElement && document.activeElement.id") == 'search', f'{tag} R1 « / » puts the cursor in the search of trades')
    pg.evaluate("document.activeElement.blur()")
  look('Trades')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'tf-trades-{tag}.png'))
  ok(N(pg.evaluate(f"(() => {{ const d = document.createElement('div'); d.innerHTML = tradeTable([]); return d.textContent; }})()")) == x['none'], f"{tag} an empty list: « {x['none']} »")

  # ── R1 ⌘K / the search, R2 « N » and Escape / the « + »
  if phone:
    tap('.nav-search:visible, [data-act="cmd"]:visible'); pg.wait_for_timeout(700)
    ok(pg.locator('#cmd:not([hidden]) #cmdq').count() == 1, f'{tag} R1 the search button opens the search')
    pg.evaluate("closeCmd()"); pg.wait_for_timeout(400)
    tap('#bottomnav .plus'); pg.wait_for_timeout(900)
    ok(pg.locator('.nav-am.open, #tkSlide.open').count() >= 1, f"{tag} R2 the « + » opens « {x['add']} »")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(700)
  else:
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(600)
    ok(pg.locator('#cmd:not([hidden]) #cmdq').count() == 1, f'{tag} R1 ⌘K opens the search')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    foc = pg.evaluate("document.activeElement ? document.activeElement.tagName + '#' + document.activeElement.id : ''")
    pg.evaluate("document.activeElement && document.activeElement.blur()")   # (the search of trades may keep the cursor: « N » would be typed there)
    pg.keyboard.press('n'); pg.wait_for_timeout(900)
    opened = pg.locator('.nav-am.open, #tkSlide.open').count() >= 1
    pg.keyboard.press('Escape'); pg.wait_for_timeout(900)
    ok(opened and pg.locator('.nav-am.open, #tkSlide.open').count() == 0, f'{tag} R2 « N » opens « {x["add"]} », Escape closes it (focus was {foc})')

  # ── R3 a day of the calendar
  go('#calendar', f'#main a[href="#journal/{day}"]')
  tap(f'#main a.d[href="#journal/{day}"]'); pg.wait_for_timeout(1000)
  ok(pg.evaluate('location.hash') == f'#journal/{day}', f'{tag} R3 a day of the calendar opens that day ({pg.evaluate("location.hash")})')
  d = pg.evaluate(DIRS); ok(not d['bad'], f"{tag} C2 the Journal: Long / Short in neutral ink ({d['bad'][:2]})")
  look('Journal')

  # ── the trade page: G1, C6, G3, G5, C2
  go('#trade/t1', '#main .th-head')
  head = pg.evaluate("(() => { const h = document.querySelector('#main .th-head'), l = h.querySelector('.lbl'), b = h.querySelector('.big'); return [l.textContent.replace(/\\s+/g, ' ').trim(), b.textContent.replace(/[\\u00a0\\u202f]/g, ' ').trim(), b.className]; })()")
  ok(head[0] == 'NQ · ' + ('Largo' if lang == 'es' else 'Long') + ' · 1' and head[1].replace(' ', '') in ('+$235.80', '+235,80$') and 'pos' in head[2], f'{tag} G1 the trade opens on « NQ · Long · 1 » and its P&L ({head})')
  cp = pg.evaluate("(() => { const d = document.querySelector('#main .tr-copies'), h = document.querySelector('#main .th-head'); return d ? [d.open, d.querySelector('summary').textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim(), !!(h.compareDocumentPosition(d) & Node.DOCUMENT_POSITION_FOLLOWING)] : null; })()")
  ok(cp and cp[0] is False and cp[1].startswith(x['also']) and cp[1].replace(' ', '').endswith(('+$554.44›', '+554,44$›')) and cp[2], f"{tag} G1 one folded line under the result « {x['also']} … » ({cp})")
  banner = ' '.join(pg.evaluate(TXT, '#main .nav-copy'))
  ok(not re.search(r'Also on|Aussi sur|También en', banner), f'{tag} G1 no « Also on » banner ({banner[:80]})')
  tap('#main .tr-copies summary'); pg.wait_for_timeout(500)
  ok(len(pg.evaluate(TXT, '#main .tr-copies .cg-r')) == 4, f'{tag} G1 open: the 4 other accounts, each with its P&L')
  facts = pg.evaluate("[...document.querySelectorAll('#main .facts > div')].map((d) => [...d.children].map((c) => c.textContent.replace(/[\\u00a0\\u202f]/g, ' ').trim()))")
  dur = [f[1] for f in facts if len(f) > 1 and f[0] in ('Duration', 'Durée', 'Duración')]
  ok(dur == [x['dur']], f"{tag} C6 the duration « {x['dur']} » ({dur})")
  ok(N(pg.evaluate("(document.querySelector('#main .nav-tdisc .lbl') || {}).textContent || ''")) == x['disc'], f"{tag} G3 the trade's « {x['disc']} »")
  d = pg.evaluate(DIRS); ok(not d['bad'], f"{tag} C2 the trade page: Long in neutral ink ({d['bad'][:2]})")
  pg.evaluate("document.querySelectorAll('#main details:not(.tr-copies):not([open])').forEach((d) => { d.open = true; })"); pg.wait_for_timeout(500)
  sh = pg.evaluate("(() => { const r = document.querySelector('#main .ux-setups'); if (!r) return null; const b = [...r.querySelectorAll('.ux-setup')]; return { vis: b.filter((x) => !x.hidden).map((x) => x.textContent.trim()), hid: b.filter((x) => x.hidden).map((x) => x.textContent.trim()) }; })()")
  ok(sh and sh['vis'][:3] == ['Retest de FVG', 'Cassure et retest', 'Opening range'] and sh['vis'][-1] == x['other'] and len(sh['vis']) == 4, f"{tag} G5 his own setups first, then « {x['other']} » ({sh and sh['vis']})")
  ok(sh and x['cat'] in sh['hid'] and not any(c in sh['hid'] for c in x['catNo'] + x['catEn']), f"{tag} G5 the common ones behind « {x['other']} », in his language, without doubles ({sh and sh['hid']})")
  pg.locator('#main [data-ux-other]').first.scroll_into_view_if_needed(); tap('#main [data-ux-other]'); pg.wait_for_timeout(500)
  ok(pg.locator(f'#main .ux-setup-cat:visible').count() == len(sh['hid']) if sh else False, f"{tag} G5 « {x['other']} » shows them")
  if phone:
    pg.evaluate('scrollTo(0, 0)'); pg.wait_for_timeout(600)
    f = pg.evaluate(FAB); ok(not f['shown'] or not f['under'], f"{tag} the Sweep AI button covers nothing at rest (the trade page: {f})")
  look('a trade')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'tf-trade-{tag}.png'))

  # ── Stats: G4, R4
  go('#analytics', '#main .st-cal-link, #main .st-soon')
  ok(pg.locator('#main .cal').count() == 0 and N(pg.evaluate("(document.querySelector('#main .st-cal-link a') || {}).textContent || ''")) == x['cal'], f"{tag} G4 Stats: no second calendar, « {x['cal']} »")
  per_s = pg.evaluate(TXT, '#main .fx-per')[:1]
  tap('#main .st-cal-link a'); pg.wait_for_timeout(900)
  ok(pg.evaluate('location.hash') == '#calendar', f'{tag} G4 the link opens Trades › Calendar')
  go('#trades', '#main')
  per_t = pg.evaluate(TXT, '#main .fx-per')[:1]
  ok(per_s and per_s == per_t, f'{tag} R4 the same period filter on Trades and Stats ({per_t} / {per_s})')

  # ── R5 Import
  go('#import', '#main')
  imp = N(pg.evaluate("document.getElementById('main').innerText"))
  ok(all(k in imp for k in ['Tradovate', 'Rithmic', 'TopstepX', 'TradingView']), f'{tag} R5 Import: Tradovate, Rithmic, TopstepX and TradingView')

  english = sorted(set(english))
  ok(not english, f'{tag} no English in {lang.upper()} ({english[:4]})')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

with sync_playwright() as p:
  run(p, 'fr', True, False)
  run(p, 'fr', False, True)
  run(p, 'en', True, True)
  run(p, 'en', False, False)
  run(p, 'es', True, False)
  run(p, 'es', False, True)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
