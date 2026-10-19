"""
Sweep — the pre-market questionnaire and its sheet (brief « Plan pre-market adaptatif », steps 2 and 3), phone 390 and computer 1300:
  python3 tests/e2e_premarket.py http://127.0.0.1:8095 /tmp/show_state.json
 1  a day without news, the price inside the range: at most 6 screens of questions, then the sheet
 2  A1 is pre-selected from the levels and the price; A2 only inside the range; A3 only outside; A4 only near PDH/PDL
 3  scenarios: A from block A, B its mirror; stop = level ± buffer, the next opposite level as target, R estimated
 4  under 2R: « not viable », the screen cannot be left; another target makes it viable; B can be removed
 5  news before the open: B2 shows, the news condition comes first in every checklist, the blocked window is −5 / +15 min
 6  the sheet is written with the day's plan (bias, max trades, max loss, levels), French and no page error
The test days (March 2027) are removed at the end.
"""
import sys
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
def screen(pg): return pg.evaluate("(document.querySelector('#gSheet [data-pm-screen]') || {}).dataset ? document.querySelector('#gSheet [data-pm-screen]').dataset.pmScreen : null")
def fill(pg, k, v): pg.fill(f'#gSheet [data-pmf="{k}"]', str(v))
def ans(pg, q, v): pg.click(f'#gSheet [data-pm="ans"][data-q="{q}"][data-v="{v}"]'); pg.wait_for_timeout(150)
def nxt(pg): pg.click('#gSheet [data-pm="next"]'); pg.wait_for_timeout(250)
def on(pg, q): return pg.evaluate(f"(document.querySelector('#gSheet [data-q=\"{q}\"].on') || {{}}).dataset ? document.querySelector('#gSheet [data-q=\"{q}\"].on').dataset.v : null")

with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone, day, nday in [(390, True, '2027-03-02', '2027-03-03'), (1300, False, '2027-03-04', '2027-03-05')]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepGame && window.SweepFiche && SweepFiche.open && window.S && S.journals'); pg.wait_for_timeout(800)
    # ---- 1 to 4, 6: a quiet day, the price in the range
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, "document.querySelector('#gSheet.g-pm [data-pm-screen]')")
    seen = []
    ok(screen(pg) == 'base' and pg.locator('#gSheet .g-head span').inner_text().endswith('sur 7'), f'1 {w}: the first screen is the base data, 7 screens in all (6 of questions + the sheet)')
    fill(pg, 'instrument', 'MES'); fill(pg, 'lv.london_high', '5820'); fill(pg, 'lv.london_low', '5800'); fill(pg, 'lv.pdh', '5850'); fill(pg, 'lv.pdl', '5770'); fill(pg, 'lv.price', '5810')
    seen.append(screen(pg)); nxt(pg); seen.append(screen(pg))
    ok(on(pg, 'A1') == 'in' and pg.locator('#gSheet [data-q="A2"]').count() == 3 and pg.locator('#gSheet [data-q="A3"]').count() == 0 and pg.locator('#gSheet [data-q="A4"]').count() == 0,
       f'2 {w}: A1 pre-selected « Dans le range », A2 asked, not A3, no A4 (PDH/PDL far)')
    ans(pg, 'A2', 'high'); nxt(pg); seen.append(screen(pg))
    ok(on(pg, 'B1') == 'no', f'1 {w}: no news in the calendar: « Non » pre-selected')
    nxt(pg); seen.append(screen(pg))
    sc = pg.evaluate("Array.from(document.querySelectorAll('#gSheet [data-pm-r]')).map((x) => x.dataset.pmR + ' ' + x.textContent)")
    ok(len(sc) == 2 and '5R' in sc[0] and '5R' in sc[1], f'3 {w}: A long breakout at 5 820 (stop 5 814, target PDH 5 850) and B short breakdown at 5 800 (target PDL 5 770), 5R each ({sc})')
    fill(pg, 'C3_A', '5825'); pg.wait_for_timeout(150)
    r = pg.locator('#gSheet [data-pm-r="A"]').inner_text()
    nxt(pg)
    ok(screen(pg) == 'scen' and 'Non viable' in r and pg.locator('#gSheet .pm-err').count() == 1, f'4 {w}: target 5 825 → under 2R, not viable, the screen stays ({r!r})')
    fill(pg, 'C3_A', '5850'); ans(pg, 'C2', 'remove'); ans(pg, 'C2', 'keep'); nxt(pg); seen.append(screen(pg))
    ok(pg.evaluate("['two_invalidations', 'time_limit'].every((v) => document.querySelector(`#gSheet [data-pm=nt][data-v=${v}]`).classList.contains('on'))"), f'1 {w}: no-trade: 2 invalidations and the time limit pre-checked')
    nxt(pg); seen.append(screen(pg))
    if not pg.input_value('#gSheet [data-pmf="max_loss"]'): fill(pg, 'max_loss', '500')
    fill(pg, 'lim.max_trades', '2'); nxt(pg); seen.append(screen(pg))
    qs = [x for x in seen if x != 'sheet']
    ok(len(qs) <= 6 and seen[-1] == 'sheet', f'1 {w}: {len(qs)} screens of questions, then the sheet ({seen})')
    txt = pg.locator('#gSheet .pm-sheet').inner_text().replace('\xa0', ' ').replace('\u202f', ' ')
    ok('Scénario A — Long' in txt and '5 850' in txt and '(5R)' in txt and 'Scénario B — Short' in txt and 'Risque 0,5 %' in txt and '2 trades' in txt and 'après 11:30' in txt,
       f'3 {w}: the sheet reads like the brief ({txt[:160]!r})')
    pg.click('#gSheet [data-pm="save"]'); pg.wait_for_timeout(900)
    j = pg.evaluate("(d) => getDoc('journals', d)", day)
    f = j and j.get('fiche')
    ok(f and len(f['scenarios']) == 2 and f['scenarios'][0]['r_estimate'] == 5 and f['scenarios'][0]['stop_estimate'] == 5814 and f['scenarios'][1]['target'] == 5770
       and f['scenarios'][0]['conditions'] == ['close_15m', 'retest_5m', 'trigger_5m', 'risk_checked'] and f['limits']['max_trades'] == 2,
       f'6 {w}: the sheet is saved (scenarios, stops, targets, R, checklist, limits)')
    ok(j and j['pre']['bias'] == 'bullish' and j['pre']['max_trades'] == '2' and float(j['pre']['max_loss']) > 0 and 'LH 5' in j['pre']['levels'], f"6 {w}: and the day's plan with it ({ {k: j['pre'].get(k) for k in ('bias', 'max_trades', 'max_loss', 'levels')} })")
    # ---- 2, 5: above the range, a news before the open
    pg.evaluate("(d) => SweepGame.openPlan(d)", nday); until(pg, "document.querySelector('#gSheet.g-pm [data-pm-screen]')")
    fill(pg, 'instrument', 'MES'); fill(pg, 'lv.london_high', '5820'); fill(pg, 'lv.london_low', '5800'); fill(pg, 'lv.pdh', '5826'); fill(pg, 'lv.pdl', '5770'); fill(pg, 'lv.price', '5823'); nxt(pg)
    ok(on(pg, 'A1') == 'above' and pg.locator('#gSheet [data-q="A3"]').count() == 2 and pg.locator('#gSheet [data-q="A2"]').count() == 0, f'2 {w}: above the high: A3 asked, not A2')
    ans(pg, 'A3', 'yes')
    ok(pg.locator('#gSheet [data-q="A4"]').count() == 3, f'2 {w}: PDH 6 points from the London high: A4 asked')
    ans(pg, 'A4', 'ignore'); nxt(pg)
    ans(pg, 'B1', 'yes'); pg.fill('#gSheet [data-pmf="B1_time"]', '08:30'); pg.dispatch_event('#gSheet [data-pmf="B1_time"]', 'change'); pg.wait_for_timeout(200)
    ok(pg.locator('#gSheet [data-q="B2"]').count() == 2, f'5 {w}: a news at 08:30, before the open: B2 asked')
    nxt(pg)
    sc = pg.evaluate("Array.from(document.querySelectorAll('#gSheet .pm-sc-h b')).map((x) => x.textContent)")
    ok(len(sc) == 2 and 'continuation' in sc[0] and 'rejet' in sc[1], f'3 {w}: closed above: A long continuation, B short rejection ({sc})')
    ans(pg, 'C2', 'remove'); fill(pg, 'C3_A', '5850'); nxt(pg); nxt(pg)
    if pg.locator('#gSheet [data-pmf="max_loss"]').count() and not pg.input_value('#gSheet [data-pmf="max_loss"]'): fill(pg, 'max_loss', '500')
    nxt(pg); pg.click('#gSheet [data-pm="save"]'); pg.wait_for_timeout(900)
    f = pg.evaluate("(d) => (getDoc('journals', d) || {}).fiche", nday)
    ok(f and len(f['scenarios']) == 1 and f['scenarios'][0]['conditions'][0] == 'news_15m' and f['news_windows'][0]['start'] == '08:25' and f['news_windows'][0]['end'] == '08:45',
       f"5 {w}: B removed; the news condition first, window 08:25–08:45 ({f and f['news_windows']})")
    for d in (day, nday): (pg.wait_for_timeout(1500), pg.evaluate("(d) => remove('journals', d)", d), pg.wait_for_timeout(1500))
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
