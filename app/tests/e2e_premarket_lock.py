"""
Sweep — locking the pre-market sheet (brief « Plan pre-market adaptatif », step 4), phone 390 and computer 1300:
  python3 tests/e2e_premarket_lock.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the sheet says when it locks by itself (09:25 New York); « Lock my plan » locks it now
 2  a locked sheet opens read-only (no field, no « Back »); the app refuses a change of plan, lets the checklist move
 3  the server too: a level sent anyway stays as it was; a status follows
 4  by the clock: a sheet whose lock time is past is locked without « Lock »; a sheet under 2R never locks
 5  Settings: the lock time, saved in the trader's settings (plan_lock_hm)
The test days are removed at the end.
"""
import sys
from playwright.sync_api import sync_playwright
from pm_helper import premarket
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
H = "{'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}"
SRV = "async (d) => { const r = await fetch('api/data', {headers: {'X-Requested-With': 'fetch'}}); const x = await r.json(); const j = (x.journals || []).find((y) => y.id === d); return j && j.fiche }"
PUT = "async ([d, f]) => { const j = structuredClone(getDoc('journals', d) || {id: d}); j.fiche = f; const r = await fetch('api/docs/journals/' + d, {method: 'PUT', headers: " + H + ", body: JSON.stringify(j)}); return r.status }"

with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone, day in [(390, True, '2027-03-10'), (1300, False, '2027-03-11')]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepGame && window.SweepFiche && SweepFiche.open && window.S && S.journals'); pg.wait_for_timeout(800)
    # 1. « Lock my plan »
    premarket(pg, day=day, save=False)
    hint = pg.locator('#gSheet .pm-locks').inner_text()
    ok('09:25' in hint and pg.locator('#gSheet [data-pm=lock]').count() == 1, f'1 {w}: the sheet says it locks by itself at 09:25 and offers « Verrouiller mon plan » ({hint!r})')
    pg.click('#gSheet [data-pm=lock]'); pg.wait_for_timeout(900)
    f = pg.evaluate("(d) => SweepFiche.get(d)", day)
    ok(f and isinstance(f.get('locked_at'), int), f'1 {w}: locked now ({f and f.get("locked_at")})')
    # 2. read-only, the checklist still moves
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, "document.querySelector('#gSheet.g-pm-locked')"); pg.wait_for_timeout(400)
    ok(pg.locator('#gSheet input').count() == 0 and pg.locator('#gSheet [data-pm=back]').count() == 0 and 'Verrouillée à' in pg.locator('#gSheet .g-head').inner_text(),
       f'2 {w}: it opens read-only, « Verrouillée à … »')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(400)
    r = pg.evaluate("(d) => { const f = SweepFiche.get(d); f.levels.london_high = 5900; const a = SweepFiche.save(f); const g = SweepFiche.get(d); g.scenarios[0].status = 'confirmed'; g.scenarios[0].done = [g.scenarios[0].conditions[0]]; const b = SweepFiche.save(g); const h = SweepFiche.get(d); return [a, h.levels.london_high, b, h.scenarios[0].status, h.scenarios[0].done.length === 1 && h.scenarios[0].done[0] === h.scenarios[0].conditions[0]] }", day)
    ok(r == [False, 5820, True, 'confirmed', True], f'2 {w}: the app keeps the plan, the checklist moves ({r})')
    # 3. the server
    pg.wait_for_timeout(1200)
    f = pg.evaluate("(d) => SweepFiche.get(d)", day); f['levels']['london_high'] = 5950; f['scenarios'][0]['status'] = 'taken'
    st = pg.evaluate(PUT, [day, f]); srv = pg.evaluate(SRV, day)
    ok(st == 200 and srv and srv['levels']['london_high'] == 5820 and srv['scenarios'][0]['status'] == 'taken', f"3 {w}: the server keeps the level, takes the status ({srv and [srv['levels']['london_high'], srv['scenarios'][0]['status']]})")
    # 4. by the clock: a past day; under 2R
    past = '2025-06-02'   # (a Monday long ago, with no journal: removed at the end)
    f2 = pg.evaluate("(d) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; f.levels.london_high = 5820; f.levels.london_low = 5800; f.scenarios = [{ id: 'A', direction: 'long', type: 'breakout', level: 5820, stop_estimate: 5814, target: 5850 }]; return f }", past)
    pg.evaluate(PUT, [past, f2]); pg.wait_for_timeout(300)
    f2['levels']['london_high'] = 5999; pg.evaluate(PUT, [past, f2]); srv2 = pg.evaluate(SRV, past)
    lockedClock = pg.evaluate("(d) => { const f = SweepFiche.normalize({ trading_day: d }, d); return SweepFiche.locked(Object.assign(f, { trading_day: d })) }", past)
    ok(lockedClock and srv2 and srv2['levels']['london_high'] == 5820 and srv2['locked_at'] is None, f'4 {w}: lock time past: locked without « Lock » (the app and the server) ({srv2 and srv2["levels"]["london_high"]})')
    bad = pg.evaluate("(d) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; f.scenarios = [{ id: 'A', direction: 'long', type: 'breakout', level: 5820, stop_estimate: 5814, target: 5825 }]; f.locked_at = Math.floor(Date.now() / 1000); return f }", '2027-03-12')
    pg.evaluate(PUT, ['2027-03-12', bad]); srv3 = pg.evaluate(SRV, '2027-03-12')
    ok(srv3 and srv3['locked_at'] is None and srv3['scenarios'][0]['r_estimate'] == 0.8, f'4 {w}: under 2R (0.8R), the server does not lock it ({srv3 and srv3["locked_at"]})')
    for d in (day, '2027-03-12', past): (pg.wait_for_timeout(1500), pg.evaluate("(d) => remove('journals', d)", d), pg.wait_for_timeout(1500))
    # 5. Settings
    pg.evaluate("location.hash = '#settings'"); pg.wait_for_timeout(1500); pg.evaluate("document.querySelectorAll('details').forEach((d) => d.open = true)"); pg.wait_for_timeout(300)
    inp = pg.locator('#main [data-bind="settings|settings|plan_lock_hm"]')
    lab = pg.evaluate("(() => { const i = document.querySelector('#main [data-bind=\"settings|settings|plan_lock_hm\"]'); return i ? i.closest('label').textContent.trim() : '' })()")
    ok(inp.count() == 1 and inp.input_value() == '09:25' and 'Verrouillage de la fiche pre-market' in lab, f'5 {w}: Settings shows the lock time, 09:25 by default ({lab!r})')
    inp.fill('09:15'); inp.dispatch_event('change'); pg.wait_for_timeout(1200)
    v = pg.evaluate("[S.settings.plan_lock_hm, SweepFiche.lockHm()]")
    ok(v == ['09:15', '09:15'], f'5 {w}: saved and used ({v})')
    inp.fill('09:25'); inp.dispatch_event('change'); pg.wait_for_timeout(800)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
