"""
Sweep — the pre-market missed (brief « Plan pre-market adaptatif », step 6), phone 390 and computer 1300, the browser's clock
after 09:25 New York:
  python3 tests/e2e_premarket_express.py http://127.0.0.1:8095 /tmp/show_state.json
 1  a trader who makes sheets opens the app after the lock time without one: the express version opens by itself, once
 2  main level, direction, target (and the day's max loss): the R is computed (under 2R it cannot go on); saved: mode express, locked, the session view
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
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); window.__closes = []; Object.defineProperty(window, '__gSheetClosed', { configurable: true, get() { return this.__gsc || 0 }, set(v) { this.__gsc = v; const g = document.getElementById('gSheet'); window.__closes.push([(g && g.className || '').slice(0, 40), (new Error().stack || '').split('\\n').slice(2, 6).map((l) => l.trim().replace(/https?:[^ )]*\\//, '')).join(' < ')]) } })")   # (who closes a sheet: the diagnostic below)
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160])); con = []; pg.on('console', lambda m: con.append(m.text[:100]))
    y, m, d = map(int, day.split('-'))
    pg.clock.install(time=dt.datetime(y, m, d, 10, 0, tzinfo=NY))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepFiche && SweepFiche.maybeExpress && window.S && S.journals'); pg.wait_for_timeout(2500)
    ok(pg.locator('#gSheet [data-pm-screen=express]').count() == 0, f'1 {w}: no sheet ever made: nothing opens by itself')
    pg.evaluate(PREV, prev); pg.wait_for_timeout(800)
    pg.reload(); until(pg, 'window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(500); pg.clock.run_for(3000); until(pg, "document.querySelector('#gSheet [data-pm-screen=express]')", 15000)
    ok(pg.locator('#gSheet [data-pm-screen=express]').count() == 1 and 'Plan express' in pg.locator('#gSheet').inner_text(), f'1 {w}: after the lock time, without a sheet: the express version opens by itself')
    # 2. level, direction, target
    pg.click('#gSheet [data-q="X_dir"][data-v="long"]'); pg.wait_for_timeout(150)
    pg.fill('#gSheet [data-pmf="instrument"]', 'MES'); pg.fill('#gSheet [data-pmf="X_level"]', '5820'); pg.fill('#gSheet [data-pmf="C3_A"]', '5825'); pg.wait_for_timeout(150)
    r = pg.locator('#gSheet [data-pm-r="A"]').inner_text()
    pg.click('#gSheet [data-pm="next"]'); pg.wait_for_timeout(250)
    ok('Non viable' in r and pg.locator('#gSheet [data-pm-screen=express]').count() == 1, f'2 {w}: 5 825 → under 2R, not viable: it stays ({r!r})')
    if not pg.input_value('#gSheet [data-pmf="max_loss"]'): pg.fill('#gSheet [data-pmf="max_loss"]', '500')   # (the day's max loss, as the plan always had)
    pg.fill('#gSheet [data-pmf="C3_A"]', '5850'); pg.wait_for_timeout(150); pg.click('#gSheet [data-pm="next"]'); pg.wait_for_timeout(300)
    ok(pg.locator('#gSheet [data-pm-screen=sheet]').count() == 1 and '(5R)' in pg.locator('#gSheet .pm-sheet').inner_text(), f'2 {w}: 5 850 → 5R, the sheet')
    pg.click('#gSheet [data-pm="save"]'); pg.wait_for_timeout(900)
    f = pg.evaluate("(d) => SweepFiche.get(d)", day)
    ok(f and f['mode'] == 'express' and len(f['scenarios']) == 1 and f['scenarios'][0]['stop_estimate'] == 5814 and pg.evaluate("(d) => SweepFiche.locked(SweepFiche.get(d))", day),
       f"2 {w}: saved: mode express, stop 5 814, locked (its lock time is past)")
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, "document.querySelector('#gSheet.g-pm-locked')")
    ok(pg.locator('#gSheet.g-pm-locked [data-sc=A]').count() == 1, f'2 {w}: the plan opens on the session view')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(300)
    # 3. « Later » the next day
    y, m, d = map(int, later.split('-'))
    pg.clock.set_fixed_time(dt.datetime(y, m, d, 10, 0, tzinfo=NY)); pg.reload(); until(pg, 'window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(2500)
    until(pg, "document.querySelector('#gSheet [data-pm-screen=express]')", 15000)   # (19 Oct., GitHub: 6 s after the reload were not always enough)
    why = ''
    if not pg.locator('#gSheet [data-pm-screen=express]').count():   # (why, when it fails on GitHub only)
      why = str(pg.evaluate("(d) => { const g = document.getElementById('gSheet'); return { day: SweepFiche.dayOf(), now: etStr(Math.floor(Date.now() / 1000)), lock: SweepFiche.lockAt(d), sheet: g && g.className + ' ' + g.innerText.slice(0, 60), mine: !!SweepFiche.get(d), before: (S.journals || []).filter((j) => j.fiche).map((j) => j.id), later: lsGet('pm.later.' + d, 0), shown: lsGet('pm.xshown.' + d, 0), hash: location.hash } }", later))
      why += f" · errors {errs[-3:]} · console {con[-5:]} · closed {pg.evaluate('window.__closes')}"
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
