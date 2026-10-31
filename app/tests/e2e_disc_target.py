"""
Sweep — the Discipline tile counts like the coach (R10) and an evaluation shows its target on Today (R11), audit of 16 Oct.:
  python3 tests/e2e_disc_target.py http://127.0.0.1:8095
A trader of its own, an evaluation (target $3,000, $2,000 drawdown), a plan each day. Yesterday: 2 clean trades (+$1,000 each,
checklist « yes »). Today: a short against the bullish bias (−$400), then a trade 3 minutes after that loss (−$300), both
logged without the checklist (a day of tilt).
 R10  (31 Oct., C5) no Discipline tile on Today any more: one line under the routine's title; (was: the tile, 2 of 4 = 50 %; its window
      says it counts like the coach;
 R11  the Accounts card of Today: « Target $1,300 / $3,000 · room $3,300 » for the evaluation (before: the room only).
Phone 390 (fr) and computer 1300 (en). No page error, nothing wider than the window.
"""
import json, random, re, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'why': 'sans erreur', 'obj': 'Objectif {a} / {b} · marge {m}'}, 'en': {'why': 'without a mistake', 'obj': 'Target {a} / {b} · room {m}'}}
SEED = """() => {
  const day = (SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr(), y = ymdAdd(day, -1);
  put('firms', { id: 'dtf', name: 'Topstep' });
  put('accounts', { id: 'dta', firm_id: 'dtf', name: 'Combine 50K', starting_balance_c: 5000000, status: 'active', phase: 'eval', created_on: '2026-09-01', rules: { target_c: 300000, dd_c: 200000, dd_type: 'static' } });
  [day, y].forEach((d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '1000', saved_at: 1 } }));
  const T = (id, d, tm, dir, pnl, disc) => put('trades', { id, account_id: 'dta', instrument: 'NQ', direction: dir, contracts: 1, entry: 1, exit: 2, pnl_c: pnl, pnl_manual: true, date: d, session_date: true, entry_time: tm, exit_time: tm.slice(0, 3) + '02', discipline: disc || {} });
  T('dt1', y, '10:00', 'long', 100000, { plan: 'y', size: 'y', risk: 'y' }); T('dt2', y, '11:00', 'long', 100000, { plan: 'y', size: 'y', risk: 'y' });
  T('dt3', day, '10:00', 'short', -40000); T('dt4', day, '10:05', 'long', -30000);
  return day; }"""
with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'dt%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Dee', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(3000)
    pg.evaluate(SEED); pg.wait_for_timeout(1800)
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-rt-sum', timeout=10000); pg.wait_for_timeout(1500)
    # (31 Oct., C5) the Discipline tile left Today: the routine has one line « Level … · … complete days › » instead of its pills
    ok(pg.locator('#main .nav-rt-disc').count() == 0 and pg.locator('#main .nav-rt-sum').count() == 1, f'{tag} R10 no Discipline tile on Today, one line under the routine\'s title (tour of 31 Oct., C5)')
    want = pg.evaluate("(o) => o.replace('{a}', moneyU(130000)).replace('{b}', moneyU(300000)).replace('{m}', moneyU(330000))", x['obj'])
    got = pg.evaluate("(document.querySelector('#main .d-acc .nav-acc-dd small') || {}).textContent || ''")
    ok(got == want, f'{tag} R11 the Accounts card: « {got} » (want « {want} »)')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    pg.screenshot(path=f'/tmp/disc_target_{w}.png', full_page=True)
    allerr += errs; ctx.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
