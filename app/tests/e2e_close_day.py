"""
Sweep — closing the day in one tap (brief « daily loop », step 3, 27 Oct.), Playwright:
  python3 tests/e2e_close_day.py http://127.0.0.1:8095
A trader of its own for each day, one account, the day's trades put in; then the Review step (or « J'ai fini pour aujourd'hui » when « Now » says stop,
31 Oct.) opens the review filled in from the day, « C'est le même » for the platform's balance (brief « pertes
oubliées », step 2) and « Fermer ma journée » closes it: 3 taps.
 1  a clean day (a plan, 2 trades in it, every rule respected): followed « yes », discipline 5, grade A
 2  a tilt day (a bullish plan, 4 shorts, every rule broken): « no », 1, F
 3  a day without a plan (2 trades, half the rules respected): « no », 2, D
 4  an answer changes with one tap before closing; the day is reviewed (the routine's review step done)
Phone 390 (fr, touch) for the three days, computer 1300 (en) for the clean one. No page error.
"""
import json, os, random, sqlite3, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'fin': 'J’ai fini pour aujourd’hui', 'close': 'Fermer ma journée'}, 'en': {'fin': 'I’m done for today', 'close': 'Close my day'}}
DISC = {'all': "{ plan: 'y', confirm: 'y', entry: 'y', size: 'y', risk: 'y' }", 'none': "{ plan: 'n', confirm: 'n', entry: 'n', size: 'n', risk: 'n' }", 'half': "{ plan: 'y', confirm: 'n', entry: 'y', size: 'n' }"}
DAYS = [   # name, plan, trades (direction, discipline), expected (followed, discipline, grade)
  ('clean', "{ bias: 'bullish', max_loss: '500', max_trades: '3' }", [('long', 'all'), ('long', 'all')], ('yes', 5, 'A')),
  ('tilt', "{ bias: 'bullish', max_loss: '500', max_trades: '2' }", [('short', 'none')] * 4, ('no', 1, 'F')),
  ('noplan', None, [('long', 'half'), ('long', 'half')], ('no', 2, 'D')),
]
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for (name, plan, trades, want), phone in [(d, True) for d in DAYS] + [(DAYS[0], False)]:
    lang = 'fr' if phone else 'en'; w = 390 if phone else 1300; tag = f'{w}-{lang} {name}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if phone else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cd%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Cy', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    market = pg.evaluate("!!(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.market)")
    if not market: print(f'skip {tag}: the market is closed today (the game\'s clock)'); ctx.close(); continue
    pg.evaluate("put('accounts', { id: 'cd-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } })")
    day = pg.evaluate("SweepGame.state().today.day")
    if plan: pg.evaluate("(d) => put('journals', { id: d, pre: Object.assign(%s, { saved_at: Math.floor(Date.now() / 1000) - 3600 }) })" % plan, day)
    for i, (dr, ds) in enumerate(trades):
      pg.evaluate("([d, i, dr]) => put('trades', { id: 'cd-t' + i, account_id: 'cd-a', instrument: 'NQ', direction: dr, contracts: 1, entry: 1, exit: 2, pnl_c: dr === 'long' ? 9000 : -12000, pnl_manual: true, date: d, entry_time: '1' + i + ':00', exit_time: '1' + i + ':05', discipline: %s })" % DISC[ds], [day, i, dr])
    pg.wait_for_timeout(1500); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-rt', timeout=10000); pg.wait_for_timeout(1500)
    # (31 Oct., C5) one way to the review: the Review step; « I'm done for today » only at the stop « Now » announces
    fin, end = pg.locator('#main .nav-rt .nav-rt-fin'), pg.locator('#main .nav-now.is-end').count() > 0
    ok(fin.count() == (1 if end else 0) and (not end or fin.first.inner_text().replace('›', '').strip() == x['fin']), f'{tag}: « {x["fin"]} » only when « Now » says stop ({fin.count()}, stop: {end})')
    go = fin.first if end else pg.locator('#main .nav-rt [data-rt=review]').first
    taps = 0
    (go.tap() if phone else go.click()); taps += 1
    pg.wait_for_selector('#gSheet [data-g=save-review]', timeout=8000); pg.wait_for_timeout(500)
    got = pg.evaluate("""(() => { const v = (k) => ((document.querySelector('#gSheet [data-g=' + k + '].on') || {}).dataset || {}).v;
      return [v('r-followed'), +v('r-score') || null, v('r-grade'), (document.querySelector('#gSheet [data-g=save-review]') || {}).textContent] })()""")
    ok(got[:3] == list(want), f'{tag}: filled in from the day: {got[:3]} (want {list(want)})')
    ok((got[3] or '').strip() == x['close'], f'{tag}: one button « {x["close"]} » ({got[3]!r})')
    if name == 'tilt':   # 4. an answer changes with one tap
      pg.evaluate("document.querySelectorAll('#gSheet .g-rv-more').forEach((d) => { d.open = true })")   # (tour T2) the grade under « + Details »
      b = pg.locator('#gSheet [data-g=r-grade][data-v=D]'); (b.tap() if phone else b.click()); pg.wait_for_timeout(200)
      ok(pg.evaluate("(document.querySelector('#gSheet [data-g=r-grade].on') || {dataset: {}}).dataset.v") == 'D', f'{tag}: the grade changed with one tap (F → D)')
      want = (want[0], want[1], 'D')
    for b in pg.locator('#gSheet [data-bal-same]').all(): (b.tap() if phone else b.click()); taps += 1; pg.wait_for_timeout(150)   # « Ton solde sur … ? »
    s = pg.locator('#gSheet [data-g=save-review]'); (s.tap() if phone else s.click()); taps += 1 if name != 'tilt' else 2
    pg.wait_for_timeout(1500)
    post = pg.evaluate("(d) => { const j = getDoc('journals', d) || {}; return j.post ? [j.post.followed, j.post.discipline, j.post.grade, !!j.post.reviewed_at] : null }", day)
    ok(post == [want[0], want[1], want[2], True], f'{tag}: the day closed in {taps} taps, the answers saved ({post})')
    if name != 'tilt': ok(taps == 3, f'{tag}: 3 taps (open, the same balance, close)')
    pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2000); pg.evaluate("render()"); pg.wait_for_timeout(800)
    ok(pg.locator('#main .nav-rt .nav-rt-fin').count() == 0, f'{tag}: reviewed: no « {x["fin"]} » any more')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
