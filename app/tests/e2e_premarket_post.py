"""
Sweep — after the session (brief « Plan pre-market adaptatif », step 7), phone 390 and computer 1300:
  python3 tests/e2e_premarket_post.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the day's review on a day with a sheet: « As-tu suivi ta fiche ? »; « Quelle règle ? » only after « En partie » / « Non »,
    the rules the app saw pre-checked (a trade off the sheet, more trades than the limit); a note for tomorrow
 2  saved in the day's journal (post.rules_broken, in the brief's order); a day without a sheet keeps the review as it was
 3  the next session's pre-market: the note at the top, the D2 question of the first rule broken, its answer as the sheet's
    reminder (at the top of the sheet)
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
SHEET = """(d) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; Object.assign(f.levels, { london_high: 5820, london_low: 5800, price: 5810 });
  f.scenarios = [{ id: 'A', direction: 'long', type: 'breakout', level: 5820, stop_estimate: 5814, target: 5850 }]; f.limits.max_trades = 1; return SweepFiche.save(f) }"""
TR = """([id, d, off, acc]) => put('trades', { id, account_id: acc, instrument: 'MES', direction: 'long', contracts: 1, entry: 5821, exit: 5830, pnl_c: 4500, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:10', session_date: true, off_plan: off })"""
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone, day, nx, plain in [(390, True, '2027-04-06', '2027-04-07', '2027-04-08'), (1300, False, '2027-04-13', '2027-04-14', '2027-04-15')]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepGame && window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(800)
    acc = pg.evaluate("((S.accounts || []).find((x) => x.status !== 'archived' && x.status !== 'closed') || {}).id")
    pg.evaluate(SHEET, day); pg.evaluate(TR, ['pp1' + str(w), day, False, acc]); pg.evaluate(TR, ['pp2' + str(w), day, True, acc]); pg.wait_for_timeout(800)
    # 1. the review
    pg.evaluate("(d) => SweepGame.openReview(d)", day); until(pg, "document.querySelector('#gSheet.g-rv')"); pg.wait_for_timeout(300)
    lab = pg.evaluate("[...document.querySelectorAll('#gSheet .g-f > span')].map((x) => x.textContent.trim())")
    ok(lab[0] == 'As-tu suivi ta fiche ?' and pg.locator('#gSheet .rv-rules').is_hidden() and any('Une note pour demain' in x for x in lab), f'1 {w}: « As-tu suivi ta fiche ? », no rule asked yet, a note for tomorrow ({lab})')
    pg.click('#gSheet [data-g=r-followed][data-v=partly]'); pg.wait_for_timeout(200)
    pre = pg.evaluate("[...document.querySelectorAll('#gSheet [data-rv-rule].on')].map((b) => b.dataset.rvRule)")
    ok(pg.locator('#gSheet .rv-rules').is_visible() and pre == ['off_plan', 'max_trades'], f'1 {w}: « En partie »: « Quelle règle ? », off-plan and too many trades pre-checked ({pre})')
    pg.click('#gSheet [data-rv-rule=no_retest]'); pg.click('#gSheet [data-g=r-score][data-v="3"]'); pg.click('#gSheet [data-g=r-grade][data-v=C]')
    pg.fill('#gSheet [data-gr=tomorrow]', 'Attendre la clôture 15m.'); pg.click('#gSheet [data-g=save-review]'); pg.wait_for_timeout(900)
    post = pg.evaluate("(d) => (getDoc('journals', d) || {}).post", day)
    ok(post and post.get('rules_broken') == ['no_retest', 'off_plan', 'max_trades'] and post.get('followed') == 'partly', f"2 {w}: saved in the day's journal ({post and post.get('rules_broken')})")
    # 2. a day without a sheet: as before
    pg.evaluate("(d) => SweepGame.openReview(d)", plain); until(pg, "document.querySelector('#gSheet.g-rv')"); pg.wait_for_timeout(300)
    lab2 = pg.evaluate("[...document.querySelectorAll('#gSheet .g-f > span')].map((x) => x.textContent.trim())")
    ok(lab2[0] == 'As-tu suivi ton plan ?' and pg.locator('#gSheet .rv-rules').count() == 0, f'2 {w}: a day without a sheet: the review as it was ({lab2[0]})')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(300)
    # 3. the next pre-market
    pg.evaluate("(d) => SweepGame.openPlan(d)", nx); until(pg, "document.querySelector('#gSheet.g-pm [data-pm-screen]')"); pg.wait_for_timeout(300)
    note = pg.evaluate("(document.querySelector('#gSheet .pm-rem') || {}).textContent || ''")
    ok('Attendre la clôture 15m.' in note, f'3 {w}: the note for tomorrow at the top of the pre-market ({note!r})')
    premarket(pg, stop_at='d2')
    q = pg.evaluate("(document.querySelector('#gSheet [data-pm-screen=d2] .pm-q') || {}).textContent || ''")
    ok(q == 'Hier tu es entré sans attendre le retest en 5 min. Qu’est-ce qui t’aidera à attendre aujourd’hui ?', f'3 {w}: the D2 question of the first rule broken ({q!r})')
    pg.fill('#gSheet [data-pmf=D2]', 'Je pose une alerte, je regarde, je ne clique pas avant le retest.'); premarket(pg)
    f = pg.evaluate("(d) => SweepFiche.get(d)", nx)
    ok(f and f['reminder'] == 'Je pose une alerte, je regarde, je ne clique pas avant le retest.', f"3 {w}: D2's answer is the sheet's reminder")
    for x in (day, nx, plain): pg.evaluate("(d) => remove('journals', d)", x)
    for x in ('pp1' + str(w), 'pp2' + str(w)): pg.evaluate("(id) => remove('trades', id)", x)
    pg.wait_for_timeout(1500)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
