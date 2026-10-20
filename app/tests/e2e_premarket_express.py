"""
Sweep — the pre-market missed (brief « Plan pre-market adaptatif », step 6), phone 390 and computer 1300, the browser's clock
after 09:25 New York:
  python3 tests/e2e_premarket_express.py http://127.0.0.1:8095 /tmp/show_state.json
 1  a trader who makes sheets opens the app after the lock time without one: the express version opens by itself, once
 2  bias, key levels, the expected and the alternative scenario (and the day's max loss; 20 Oct.: no prices to set); saved: mode express, locked, the session view, the journal's Pre-market
 3  « Later »: no sheet; the day's new trades are off-plan (nothing to link)
The test days are removed at the end.
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
PREV = """(d) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; Object.assign(f.levels, { london_high: 5820, london_low: 5800, price: 5810 });
  f.scenarios = [{ id: 'A', direction: 'long', type: 'breakout', level: 5820, stop_estimate: 5814, target: 5850 }]; return SweepFiche.save(f) }"""
NY = ZoneInfo('America/New_York')
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone, prev, day, later in [(390, True, '2027-03-15', '2027-03-17', '2027-03-18'), (1300, False, '2027-03-22', '2027-03-24', '2027-03-25')]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    y, m, d = map(int, day.split('-'))
    pg.clock.install(time=dt.datetime(y, m, d, 10, 0, tzinfo=NY))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepFiche && SweepFiche.maybeExpress && window.S && S.journals'); pg.wait_for_timeout(2500)
    ok(pg.locator('#gSheet [data-pm-screen=express]').count() == 0, f'1 {w}: no sheet ever made: nothing opens by itself')
    pg.evaluate(PREV, prev); pg.wait_for_timeout(800)
    pg.reload(); until(pg, 'window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(500); pg.clock.run_for(3000); until(pg, "document.querySelector('#gSheet [data-pm-screen=express]')", 15000)
    ok(pg.locator('#gSheet [data-pm-screen=express]').count() == 1 and 'Plan express' in pg.locator('#gSheet').inner_text(), f'1 {w}: after the lock time, without a sheet: the express version opens by itself')
    # 2. bias, key levels, the two scenarios
    pg.click('#gSheet [data-pm="inst-pick"][data-v="MES"]'); pg.wait_for_timeout(150)   # (the instrument: one chip)
    ok(pg.locator('#gSheet [data-pmf="X_level"], #gSheet [data-pmf="X_stop"]').count() == 0 and pg.locator('#gSheet [data-q="X_bias"]').count() == 3, f'2 {w}: no entry / stop / target to set: the bias (3 choices)')
    pg.click('#gSheet [data-pm="next"]'); pg.wait_for_timeout(250)
    ok(pg.locator('#gSheet [data-pm-screen=express]').count() == 1 and 'Choisis ton biais et écris ton scénario attendu.' in pg.locator('#gSheet .pm-err').inner_text(), f'2 {w}: without bias nor scenario: it says so and stays')
    pg.click('#gSheet [data-q="X_bias"][data-v="bullish"]'); pg.wait_for_timeout(150)
    pg.fill('#gSheet [data-pmf="X_levels"]', 'PDH 5850 · London high 5820'); pg.fill('#gSheet [data-pmf="X_plan"]', 'Cassure du London high qui tient au retest : achat vers le PDH.'); pg.fill('#gSheet [data-pmf="X_alt"]', 'Retour sous 5800 : pas de trade.')
    if not pg.input_value('#gSheet [data-pmf="max_loss"]'): pg.fill('#gSheet [data-pmf="max_loss"]', '500')   # (the day's max loss, as the plan always had)
    pg.click('#gSheet [data-pm="next"]'); pg.wait_for_timeout(300)
    t = pg.locator('#gSheet .pm-sheet').inner_text().replace('\xa0', ' ')
    ok(pg.locator('#gSheet [data-pm-screen=sheet]').count() == 1 and 'Biais · Haussier' in t and 'Niveaux clés · PDH 5850 · London high 5820' in t and 'Scénario attendu · Cassure du London high' in t and 'Scénario alternatif · Retour sous 5800' in t, f'2 {w}: the sheet: bias, key levels, the two scenarios ({t[:120]!r})')
    pg.click('#gSheet [data-pm="save"]'); pg.wait_for_timeout(900)
    f = pg.evaluate("(d) => SweepFiche.get(d)", day); pre = pg.evaluate("(d) => (getDoc('journals', d) || {}).pre || {}", day)
    ok(f and f['mode'] == 'express' and len(f['scenarios']) == 0 and pg.evaluate("(d) => SweepFiche.locked(SweepFiche.get(d))", day) and pre.get('bias') == 'bullish' and pre.get('levels') == 'PDH 5850 · London high 5820' and pre.get('scenario', '').startswith('Cassure') and pre.get('alt', '').startswith('Retour'),
       f"2 {w}: saved: mode express, locked (its lock time is past); the journal's Pre-market has the bias, the key levels and both scenarios")
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, "document.querySelector('#gSheet.g-pm-locked')")
    pg.wait_for_timeout(300); lt = pg.locator('#gSheet.g-pm-locked').inner_text().replace('\xa0', ' ')
    ok('Scénario attendu · Cassure du London high' in lt, f'2 {w}: the plan opens on the session view, with the scenarios ({lt[:200]!r})')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(300)
    # 3. « Later » the next day
    y, m, d = map(int, later.split('-'))
    pg.close(); c.clock.set_fixed_time(dt.datetime(y, m, d, 10, 0, tzinfo=NY)); pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160])); pg.goto(B + '/#dashboard');   # (19 Oct., GitHub: the page closed first; still open, it offered the next day itself, once, before the reload)
    until(pg, 'window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(2500)
    until(pg, "document.querySelector('#gSheet [data-pm-screen=express]')", 15000)   # (19 Oct., GitHub: 6 s after the reload were not always enough)
    why = ''
    if not pg.locator('#gSheet [data-pm-screen=express]').count():   # (why, when it fails on GitHub only)
      why = str(pg.evaluate("(d) => { const g = document.getElementById('gSheet'); return { day: SweepFiche.dayOf(), now: etStr(Math.floor(Date.now() / 1000)), lock: SweepFiche.lockAt(d), sheet: g && g.className + ' ' + g.innerText.slice(0, 60), mine: !!SweepFiche.get(d), before: (S.journals || []).filter((j) => j.fiche).map((j) => j.id), later: lsGet('pm.later.' + d, 0), shown: lsGet('pm.xshown.' + d, 0), hash: location.hash } }", later))
    ok(pg.locator('#gSheet [data-pm-screen=express]').count() == 1, f'3 {w}: the next day, after the lock time: the express version again {why}')
    pg.click('#gSheet [data-pm="later"]'); pg.wait_for_timeout(400)
    doc = pg.evaluate("(d) => SweepFiche.markTrade({ id: 'x', date: d, instrument: 'MES' })", later)
    ok(pg.locator('#gSheet').count() == 0 and doc.get('off_plan') is True, f'3 {w}: « Plus tard »: closed; a trade of the day is off-plan ({doc.get("off_plan")})')
    pg.reload(); until(pg, 'window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(2500)
    ok(pg.locator('#gSheet [data-pm-screen=express]').count() == 0, f'3 {w}: not offered again that day')
    for x in (prev, day): pg.evaluate("(d) => remove('journals', d)", x); pg.wait_for_timeout(800)
    pg.wait_for_timeout(1200)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
