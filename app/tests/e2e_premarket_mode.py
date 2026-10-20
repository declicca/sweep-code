"""
Sweep — the pre-market, guided or express at any time (the trader's choice is kept), phone 390 and computer 1300, the browser's
clock at 08:00 New York (before the lock time):
  python3 tests/e2e_premarket_mode.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the guided plan opens; « Plan express (30 s) » switches to the express version (no « Later » before the lock time) and keeps the choice
 2  express saved before the lock time: mode express, not locked; reopened, it stays the express version, on its sheet
 3  the next day, the plan opens on the express version by itself
 4  « Plan guidé » goes back to the guided plan and keeps that choice for the next day
The test days are removed at the end and the trader's choice is put back.
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
SCREEN = "(document.querySelector('#gSheet.g-pm [data-pm-screen]') || {dataset: {}}).dataset.pmScreen || ''"
TAP = "(s) => { const b = document.querySelector(s); if (b) b.click(); return !!b }"
NY = ZoneInfo('America/New_York')
def open_plan(pg, day):
  pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, SCREEN); pg.wait_for_timeout(400)
  return pg.evaluate(SCREEN)
def close(pg):
  pg.evaluate(TAP, '#gSheet [data-g=close]'); pg.wait_for_timeout(400)
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone, d1, d2, d3 in [(390, True, '2027-04-05', '2027-04-06', '2027-04-07'), (1300, False, '2027-04-12', '2027-04-13', '2027-04-14')]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    y, m, d = map(int, d1.split('-'))
    pg.clock.install(time=dt.datetime(y, m, d, 8, 0, tzinfo=NY))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepFiche && window.SweepGame && window.S && S.journals && S.settings'); pg.wait_for_timeout(1500)
    was = pg.evaluate("S.settings.pm_mode || null")
    if was: pg.evaluate("(() => { const s = structuredClone(S.settings); delete s.pm_mode; put('settings', s) })()"); pg.wait_for_timeout(500)
    # 1. guided first, then express one tap away
    ok(open_plan(pg, d1) == 'base' and pg.locator('#gSheet [data-pm="mode"][data-v="express"]').count() == 1, f'1 {w}: the guided plan opens, « Plan express (30 s) » on its first screen')
    pg.evaluate(TAP, '#gSheet [data-pm="mode"][data-v="express"]'); pg.wait_for_timeout(400)
    txt = pg.locator('#gSheet').inner_text()
    ok(pg.evaluate(SCREEN) == 'express' and 'verrouillage' not in txt and pg.locator('#gSheet [data-pm="later"]').count() == 0 and pg.locator('#gSheet [data-pm="mode"][data-v="full"]').count() == 1,
       f'1 {w}: the express version, without « Plus tard » nor the lock-time hint, « Plan guidé » to go back')
    ok(pg.evaluate("S.settings.pm_mode") == 'express', f'1 {w}: the choice is kept (settings.pm_mode = express)')
    # 2. saved before the lock time
    pg.evaluate(TAP, '#gSheet [data-q="X_dir"][data-v="long"]'); pg.wait_for_timeout(150)
    pg.click('#gSheet [data-pm="inst-pick"][data-v="MES"]'); pg.wait_for_timeout(150)
    pg.fill('#gSheet [data-pmf="X_level"]', '5820'); pg.fill('#gSheet [data-pmf="C3_A"]', '5850')
    if not pg.input_value('#gSheet [data-pmf="max_loss"]'): pg.fill('#gSheet [data-pmf="max_loss"]', '500')
    pg.evaluate(TAP, '#gSheet [data-pm="next"]'); pg.wait_for_timeout(300)
    ok(pg.evaluate(SCREEN) == 'sheet' and '(5R)' in pg.locator('#gSheet .pm-sheet').inner_text(), f'2 {w}: 5R, the sheet')
    pg.evaluate(TAP, '#gSheet [data-pm="save"]'); pg.wait_for_timeout(900)
    f = pg.evaluate("(d) => SweepFiche.get(d)", d1)
    ok(f and f['mode'] == 'express' and not pg.evaluate("(d) => SweepFiche.locked(SweepFiche.get(d))", d1), f'2 {w}: saved: mode express, not locked before 09:25')
    ok(open_plan(pg, d1) == 'sheet' and '2 sur 2' in pg.locator('#gSheet').inner_text(), f'2 {w}: reopened: the express sheet (2 of 2), not the guided screens')
    pg.evaluate(TAP, '#gSheet [data-pm="back"]'); pg.wait_for_timeout(300)
    ok(pg.evaluate(SCREEN) == 'express' and pg.input_value('#gSheet [data-pmf="X_level"]') == '5820', f'2 {w}: « Retour »: its answers are there')
    close(pg)
    # 3. the next day: express by itself
    ok(open_plan(pg, d2) == 'express', f'3 {w}: the next day, the express version opens by itself')
    # 4. back to the guided plan, kept
    pg.evaluate(TAP, '#gSheet [data-pm="mode"][data-v="full"]'); pg.wait_for_timeout(400)
    ok(pg.evaluate(SCREEN) == 'base' and pg.evaluate("S.settings.pm_mode") == 'full', f'4 {w}: « Plan guidé »: the guided plan, the choice kept')
    close(pg)
    ok(open_plan(pg, d3) == 'base', f'4 {w}: the day after, the guided plan again')
    close(pg)
    for x in (d1, d2, d3): pg.evaluate("(d) => { if (S.journals.some((j) => j.id === d)) remove('journals', d) }", x)
    pg.evaluate("(v) => { const s = structuredClone(S.settings); if (v) s.pm_mode = v; else delete s.pm_mode; put('settings', s) }", was)
    pg.wait_for_timeout(1500)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
