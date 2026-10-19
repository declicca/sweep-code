"""
Sweep — the session view of the pre-market sheet (brief « Plan pre-market adaptatif », step 5), phone 390 and computer 1300,
the browser's clock at 10:30 New York on the sheet's day (locked by the clock at 09:25):
  python3 tests/e2e_premarket_session.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the plan opens on the session view: each scenario's checklist in its order, a banner during the news window (10:25–10:45),
    the trades against the limit
 2  a box only after the one before it (the next ones are not tappable); the last one can be undone; all checked → confirmed
 3  the max of trades reached, or 2 invalidations (« Invalidate » stops a scenario) → « Journée terminée selon ton plan »
 4  a trade saved with the full form on that day: « which scenario? »; linked to A → A taken, the trade not off-plan;
    another one left « Hors fiche » → off-plan
The test day is removed at the end.
"""
import datetime as dt, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def until(pg, expr, ms=15000):
  for _ in range(ms // 150):
    if pg.evaluate(f'!!({expr})'): return True
    pg.wait_for_timeout(150)
  return False
SHEET = """(d) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; Object.assign(f.levels, { london_high: 5820, london_low: 5800, pdh: 5850, pdl: 5770, price: 5810 });
  f.scenarios = [{ id: 'A', direction: 'long', type: 'breakout', level: 5820, stop_estimate: 5814, target: 5850 }, { id: 'B', direction: 'short', type: 'breakdown', level: 5800, stop_estimate: 5806, target: 5770 }];
  f.news_windows = [{ start: '10:25', end: '10:45', event: 'Test' }]; f.no_trade_conditions = ['two_invalidations', 'time_limit']; f.limits.time_limit = '11:30'; f.limits.max_trades = 2;
  return SweepFiche.save(f) }"""
DAY = '2027-03-16'   # a Tuesday
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone in [(390, True), (1300, False)]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.clock.install(time=dt.datetime(2027, 3, 16, 10, 30, tzinfo=ZoneInfo('America/New_York')))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepGame && window.SweepFiche && SweepFiche.offerLink && window.S && S.journals'); pg.wait_for_timeout(800)
    ok(pg.evaluate("SweepFiche.dayOf()") == DAY, f'0 {w}: the browser\'s clock is on {DAY}, 10:30 NY')
    pg.evaluate(SHEET, DAY); pg.wait_for_timeout(500)
    # 1. the session view
    pg.evaluate("(d) => SweepGame.openPlan(d)", DAY); until(pg, "document.querySelector('#gSheet.g-pm-locked')"); pg.wait_for_timeout(300)
    txt = pg.locator('#gSheet').inner_text().replace('\xa0', ' ').replace(' ', ' ')
    ok('Ta séance' in txt and 'Fenêtre de news : pas de trade avant 10:45.' in txt and 'Trades : 0 sur 2' in txt and pg.locator('#gSheet [data-sc]').count() == 2,
       f'1 {w}: the session view, the news banner (10:25–10:45), « Trades : 0 sur 2 », 2 scenarios')
    labels = pg.evaluate("[...document.querySelectorAll('#gSheet [data-sc=A] .pm-chk')].map((b) => b.dataset.c)")
    ok(labels == ['close_15m', 'retest_5m', 'trigger_5m', 'risk_checked'], f'1 {w}: the checklist in its order ({labels})')
    # 2. the order of the boxes
    dis = pg.evaluate("[...document.querySelectorAll('#gSheet [data-sc=A] .pm-chk')].map((b) => b.disabled)")
    ok(dis == [False, True, True, True], f'2 {w}: only the first box can be ticked ({dis})')
    pg.click('#gSheet [data-sc=A] [data-c=close_15m]'); pg.wait_for_timeout(250)
    dis = pg.evaluate("[...document.querySelectorAll('#gSheet [data-sc=A] .pm-chk')].map((b) => b.disabled)")
    ok(dis == [False, False, True, True], f'2 {w}: ticked, the next one opens ({dis})')
    pg.click('#gSheet [data-sc=A] [data-c=close_15m]'); pg.wait_for_timeout(250)
    ok(pg.evaluate("(d) => SweepFiche.get(d).scenarios[0].done", DAY) == [], f'2 {w}: the last box can be undone')
    for cnd in ['close_15m', 'retest_5m', 'trigger_5m', 'risk_checked']: pg.click(f'#gSheet [data-sc=A] [data-c={cnd}]'); pg.wait_for_timeout(200)
    a = pg.evaluate("(d) => SweepFiche.get(d).scenarios[0]", DAY)
    ok(a['done'] == ['close_15m', 'retest_5m', 'trigger_5m', 'risk_checked'] and a['status'] == 'confirmed', f"2 {w}: all ticked → confirmed ({a['status']})")
    # 4. a trade with the full form, linked to A
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(400)
    acc = pg.evaluate("((S.accounts || []).find((x) => x.status !== 'archived' && x.status !== 'closed') || {}).id")
    pg.evaluate("openTicket(null, {manual: true})"); pg.wait_for_timeout(700)
    pg.evaluate("([d, a]) => { Object.assign(TK, { account: a, inst: 'MES', dir: 'long', qty: 1, entry: 5821, exit: 5850, date: d, entryTime: '10:32' }); tkRefresh(); tkSave() }", [DAY, acc]); pg.wait_for_timeout(1200)
    until(pg, "document.querySelector('#gSheet.g-pm-link')", 5000)
    q = pg.locator('#gSheet.g-pm-link').inner_text() if pg.locator('#gSheet.g-pm-link').count() else ''
    ok('quel scénario' in q and pg.locator('#gSheet.g-pm-link [data-pm=link]').count() == 3, f'4 {w}: after the save: « quel scénario de ta fiche ? » with A, B and « Hors fiche »')
    tid = pg.evaluate("(d) => (S.trades.filter((t) => t.date === d && !t.demo).sort((x, y) => (y.created_at || '').localeCompare(x.created_at || ''))[0] || {}).id", DAY)
    ok(pg.evaluate("(id) => getDoc('trades', id).off_plan === true", tid), f'4 {w}: until linked, the trade is off-plan')
    pg.click('#gSheet.g-pm-link [data-pm=link][data-s=A]'); pg.wait_for_timeout(700)
    t1 = pg.evaluate("(id) => { const t = getDoc('trades', id); return [t.plan_scenario, t.off_plan] }", tid)
    ok(t1 == ['A', False] and pg.evaluate("(d) => SweepFiche.get(d).scenarios[0].status", DAY) == 'taken', f'4 {w}: linked to A: the trade in the plan, A taken ({t1})')
    pg.evaluate("openTicket(null, {manual: true})"); pg.wait_for_timeout(700)
    pg.evaluate("([d, a]) => { Object.assign(TK, { account: a, inst: 'MES', dir: 'short', qty: 1, entry: 5815, exit: 5812, date: d, entryTime: '10:50' }); tkRefresh(); tkSave() }", [DAY, acc]); pg.wait_for_timeout(1200)
    until(pg, "document.querySelector('#gSheet.g-pm-link')", 5000)
    tid2 = pg.evaluate("(d) => (S.trades.filter((t) => t.date === d && !t.demo && !t.plan_scenario).sort((x, y) => (y.created_at || '').localeCompare(x.created_at || ''))[0] || {}).id", DAY)
    pg.click('#gSheet.g-pm-link [data-pm=link][data-s=""]'); pg.wait_for_timeout(600)
    ok(pg.evaluate("(id) => getDoc('trades', id).off_plan === true && !getDoc('trades', id).plan_scenario", tid2), f'4 {w}: « Hors fiche »: off-plan')
    # 3. invalidations → day over
    pg.evaluate("(d) => SweepGame.openPlan(d)", DAY); until(pg, "document.querySelector('#gSheet.g-pm-locked')"); pg.wait_for_timeout(300)
    ok('Trades : 2 sur 2' in pg.locator('#gSheet .pm-count').inner_text().replace('\xa0', ' '), f'1 {w}: the counter follows the trades (2 of 2)')
    ok('Journée terminée selon ton plan.' in pg.locator('#gSheet').inner_text() and pg.evaluate("(d) => SweepFiche.over(d)", DAY) == 'max_trades',
       f'3 {w}: 2 trades of 2: « Journée terminée selon ton plan. » (the max of trades)')
    st_b = pg.evaluate("(document.querySelector('#gSheet [data-sc=B] .pm-st') || {}).textContent")
    ok(st_b == 'Expiré' and pg.locator('#gSheet [data-pm=inval]').count() == 0, f'3 {w}: what was left waiting expires, nothing to invalidate any more ({st_b})')
    # 2 invalidations, on a fresh day, without trades
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(300)
    for t in pg.evaluate("(d) => S.trades.filter((t) => t.date === d && !t.demo).map((t) => t.id)", DAY): pg.evaluate("(id) => remove('trades', id)", t)
    pg.wait_for_timeout(1500); pg.evaluate("(d) => remove('journals', d)", DAY); pg.wait_for_timeout(1500)
    pg.evaluate(SHEET, DAY); pg.wait_for_timeout(500)
    pg.evaluate("(d) => SweepGame.openPlan(d)", DAY); until(pg, "document.querySelector('#gSheet.g-pm-locked')"); pg.wait_for_timeout(300)
    ok('Journée terminée' not in pg.locator('#gSheet').inner_text(), f'3 {w}: no trade, no invalidation: the day goes on')
    pg.click('#gSheet [data-sc=A] [data-pm=inval]'); pg.wait_for_timeout(300); pg.click('#gSheet [data-sc=B] [data-pm=inval]'); pg.wait_for_timeout(400)
    ok('Journée terminée selon ton plan.' in pg.locator('#gSheet').inner_text() and pg.evaluate("(d) => SweepFiche.over(d)", DAY) == 'two_invalidations', f'3 {w}: 2 invalidations: « Journée terminée selon ton plan. »')
    pg.wait_for_timeout(1500); pg.evaluate("(d) => remove('journals', d)", DAY); pg.wait_for_timeout(1500)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
