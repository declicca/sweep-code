"""
Sweep — a trade copied on 3 accounts counts once on Today (audit of 16 Oct., step 4), Playwright:
  python3 tests/e2e_copy_once.py http://127.0.0.1:8095
A trader of its own, 3 accounts; on the last weekday D: a trade copied on the 3 accounts (+$450 on each) and a trade on one
account (−$100). The decided rule: a copy counts once (the main copy's P&L, n = 1, the « +2 » badge kept). Everywhere on
Today the day is +$350 · 2 trades — before: « +$450 · 1 trade » in the performance, « $1.4k · 3 trades » in the month card,
« +$1,350 » in the day row. Since SWEEP.md step 3 the month card is on Trades › Calendar only: checked there. Phone 390 (fr: the strip of days, the day's numbers and rows) and computer 1300 (en: the month
card, the performance, the rows). No page error, nothing wider than the window.
"""
import json, random, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
SEED = """() => {
  const d0 = new Date(todayStr() + 'T12:00:00'); while (d0.getDay() === 0 || d0.getDay() === 6) d0.setDate(d0.getDate() - 1);
  const D = `${d0.getFullYear()}-${String(d0.getMonth() + 1).padStart(2, '0')}-${String(d0.getDate()).padStart(2, '0')}`;
  put('firms', { id: 'cof', name: 'Apex Trader Funding' });
  ['coa', 'cob', 'coc'].forEach((id, k) => put('accounts', { id, firm_id: 'cof', name: 'Apex ' + (k + 1), starting_balance_c: 5000000, status: 'active', phase: 'funded', created_on: '2026-09-01', rules: { dd_c: 250000 } }));
  ['coa', 'cob', 'coc'].forEach((a, k) => put('trades', { id: 'co' + k, account_id: a, copy_group: 'cog', instrument: 'ES', direction: 'long', contracts: 2, entry: 5800, exit: 5804.5, pnl_c: 45000, pnl_manual: true, date: D, session_date: true, entry_time: '10:00', exit_time: '10:20', created_at: '2026-10-01T10:00:0' + k }));
  put('trades', { id: 'co9', account_id: 'coa', instrument: 'NQ', direction: 'short', contracts: 1, entry: 21000, exit: 21005, pnl_c: -10000, pnl_manual: true, date: D, session_date: true, entry_time: '11:00', exit_time: '11:10' });
  return D; }"""
READ = """(D) => {
  const N = (x) => String(x).replace(/[\\s\\u00a0\\u202f]+/g, ' ').trim();
  const T = (q) => { const e = document.querySelector(q); return e ? N(e.textContent) : null; };
  const kpi = [...document.querySelectorAll('#main .d-perf .nav-kpi-g > div')].map((d) => T2(d));
  function T2(d) { return d.querySelector('b') ? N(d.querySelector('b').textContent) : ''; }
  const rows = [...document.querySelectorAll('#main .d-perf .nav-tr')].map((r) => [(r.querySelector('.nav-tr-copy') || {}).textContent || '', N(r.querySelector('.nav-tr-p').textContent)]);
  return { cal: T(`#main .nav-cd[data-day="${D}"] .nav-cd-p`), calN: T(`#main .nav-cd[data-day="${D}"] .nav-cd-n`), strip: T(`#main .nav-sd[data-day="${D}"] span`),
    feed: T(`#main .nav-fd[data-fd="${D}"] .nav-fd-p`), kpi, rows, want: [moneyShort(35000), money(35000), money(45000), money(-10000)].map(N) }; }"""

with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.kpiTab', 'week'); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cn%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ok(r.ok, f'{tag} a trader of its own ({r.status})')
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Sam', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    D = pg.evaluate(SEED); pg.wait_for_timeout(1500)
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-dash .d-perf', timeout=10000); pg.wait_for_timeout(1200)
    if phone:   # the strip of days: the day D, its numbers and rows
      pg.locator(f'#main .nav-fd[data-fd="{D}"]').scroll_into_view_if_needed(); pg.locator(f'#main .nav-fd[data-fd="{D}"]').click(); pg.wait_for_timeout(900)
      if pg.locator('#main .d-perf [data-kt=day]').count(): pg.locator('#main .d-perf [data-kt=day]').click(); pg.wait_for_timeout(700)
    v = pg.evaluate(READ, D); short, net, copy, single = v['want']
    if phone: ok(v['feed'] == short, f'{tag} the strip of days: {v["feed"]} (want {short})')
    for k in ('cal', 'strip'):
      if v[k] is not None: ok(v[k] == short, f'{tag} the month card ({k}): {v[k]} (want {short})')
    if v['calN'] is not None: ok(v['calN'] == '2 trades', f'{tag} the month card: « {v["calN"]} » (want « 2 trades »)')
    ok(len(v['kpi']) >= 2 and v['kpi'][0] == net and v['kpi'][1] == '2', f'{tag} the performance: {v["kpi"][:2]} (want {net} · 2)')
    ok(sorted(v['rows']) == sorted([['+2', copy], ['', single]]), f'{tag} the day rows: the copied trade once with « +2 » and its own P&L ({v["rows"]})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    # (SWEEP.md step 3) the month card left Today: the same day on Trades › Calendar
    pg.evaluate("location.hash = '#calendar'"); pg.wait_for_timeout(1500)
    cl = pg.evaluate("(D) => { const N = (x) => String(x).replace(/[\\s\\u00a0\\u202f]+/g, ' ').trim(); const a = document.querySelector(`#main a.d[href='#journal/${D}']`); return a ? [N((a.querySelector('.p .short') || {}).textContent || ''), N((a.querySelector('.m') || {}).textContent || '')] : null }", D)
    dg = lambda x: ''.join(ch for ch in (x or '') if ch.isdigit())   # (the calendar cell is short: « +350 »)
    ok(cl is not None and dg(cl[0]) == dg(short) and cl[1] in ('2 trades', '2 trade'), f'{tag} Trades › Calendar: the day {cl} (want {short} · 2 trades)')
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
