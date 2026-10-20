"""
Sweep — what the pre-market learns (brief « Plan pre-market adaptatif », step 8), phone 390 and computer 1300:
  python3 tests/e2e_premarket_learn.py http://127.0.0.1:8095 /tmp/show_state.json
After 10 sheets (MES each time; 3 trades on 6 of them, 2 on 4; 11:00 on 7; a short breakdown kept as B, never taken):
 1  the instrument is no longer asked (shown, « Modifier » brings the field back)
 2  the limits start from the most frequent values: 3 trades, 11:00
 3  under the alternative scenario: « Ce scénario n'a pas été pris depuis 10 séances. Le garder ? »
 4  with 2 sheets only: the instrument asked, no note, the limits already theirs (3 trades, 11:00)
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
SEED = """(days) => days.forEach((d, i) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; Object.assign(f.levels, { london_high: 5820, london_low: 5800, price: 5810 });
  f.scenarios = [{ id: 'A', direction: 'long', type: 'breakout', level: 5820, stop_estimate: 5814, target: 5850, status: 'taken' }, { id: 'B', direction: 'short', type: 'breakdown', level: 5800, stop_estimate: 5806, target: 5770 }];
  f.limits.max_trades = i < 6 ? 3 : 2; f.limits.time_limit = i < 7 ? '11:00' : '11:30'; SweepFiche.save(f) })"""
DAYS = ['2027-05-13', '2027-05-14', '2027-05-17', '2027-05-18', '2027-05-19', '2027-05-20', '2027-05-21', '2027-05-24', '2027-05-25', '2027-05-26']
D = '2027-05-27'
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone in [(390, True), (1300, False)]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepGame && window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(800)
    # 4. first, with 2 sheets only
    pg.evaluate(SEED, DAYS[-2:]); pg.wait_for_timeout(600)
    pg.evaluate("(d) => SweepGame.openPlan(d)", D); until(pg, "document.querySelector('#gSheet.g-pm [data-pm-screen]')"); pg.wait_for_timeout(300)
    ok(pg.locator('#gSheet [data-pm=inst-pick]').count() > 1, f'4 {w}: 2 sheets: the instrument is asked (its chips)')
    premarket(pg, stop_at='scen')
    ok(pg.locator('#gSheet .pm-never').count() == 0, f'4 {w}: 2 sheets: no note under B')
    premarket(pg, stop_at='limits')
    lim = [pg.input_value('#gSheet [data-pmf="lim.max_trades"]'), pg.input_value('#gSheet [data-pmf="lim.time_limit"]')]
    ok(lim == ['3', '11:00'], f'4 {w}: 2 sheets (3 trades, 11:00): already their values ({lim})')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(300)
    pg.evaluate("localStorage.removeItem('pm.draft')")   # (the sheet closed without saving is kept as a draft: this part starts afresh)
    # 1 to 3: 10 sheets
    pg.evaluate(SEED, DAYS); pg.wait_for_timeout(1200)
    pg.evaluate("(d) => SweepGame.openPlan(d)", D); until(pg, "document.querySelector('#gSheet.g-pm [data-pm-screen]')"); pg.wait_for_timeout(300)
    inst = pg.evaluate("(document.querySelector('#gSheet .pm-inst') || {}).textContent || ''")
    ok(pg.locator('#gSheet [data-pm=inst-pick]').count() == 0 and 'MES' in inst and 'Micro S&P 500' in inst, f'1 {w}: the same instrument for 5 sheets: not asked, its name with it ({inst.strip()!r})')
    pg.click('#gSheet [data-pm=inst]'); pg.wait_for_timeout(200)
    on = pg.evaluate("(document.querySelector('#gSheet [data-pm=inst-pick].on') || {}).textContent || ''")
    ok(pg.locator('#gSheet [data-pm=inst-pick]').count() > 1 and on == 'MES', f'1 {w}: « Modifier » brings the chips back, MES chosen ({on!r})')
    premarket(pg, stop_at='scen')
    note = pg.evaluate("(document.querySelector('#gSheet .pm-never') || {}).textContent || ''")
    ok(note == 'Ce scénario n’a pas été pris depuis 10 séances. Le garder ?', f'3 {w}: under B, the note ({note!r})')
    premarket(pg, stop_at='limits')
    lim = [pg.input_value('#gSheet [data-pmf="lim.max_trades"]'), pg.input_value('#gSheet [data-pmf="lim.time_limit"]')]
    ok(lim == ['3', '11:00'], f'2 {w}: the limits from the last 10 sheets ({lim})')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(300)
    pg.evaluate("localStorage.removeItem('pm.draft')")
    for d in DAYS: pg.evaluate("(d) => remove('journals', d)", d)
    pg.wait_for_timeout(1800)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
