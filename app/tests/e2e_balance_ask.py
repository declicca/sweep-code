"""
Sweep — « Close my day » asks the platform's balance only when it is needed (brief « l'app dans le temps », D3, 1 Nov.), Playwright:
  python3 tests/e2e_balance_ask.py http://127.0.0.1:8095
A trader of its own, three Topstep accounts traded today; phone 390 (fr, dark, touch), computer 1300 (en, light), phone 390 (es, light).
 A  its trade of the day came from a screenshot, no gap at the last check: « C'est le même » chosen in advance
 B  a trade typed by hand today: the balance is asked (nothing chosen)
 C  a screenshot trade, but the last check of that account (yesterday) found a gap: asked
Then « C'est le même » on B and C closes the day in one tap each, the three balances kept (journal.post.bal). No page error,
nothing wider than the window.
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
SAME = {'fr': 'C’est le même', 'en': 'It matches', 'es': 'Es el mismo'}
ACC = "([id, name]) => put('accounts', { id, name, firm_id: 'ba-f', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dd_type: 'eod', dll_c: 100000, target_c: 300000, consistency_pct: 50 } })"
TRADE = "([id, acc, d, c, shot]) => put('trades', Object.assign({ id, account_id: acc, instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: c, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:05', discipline: { plan: 'y' } }, shot ? { source: 'shot', shots: ['ba-' + id + '.png'] } : {}))"
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, scheme in (('fr', True, 'dark'), ('en', False, 'light'), ('es', True, 'light')):
    w = 390 if phone else 1300; tag = f'{w}-{lang}-{scheme}'
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'ba%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    tap = lambda l: l.tap() if phone else l.click()
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('firms', { id: 'ba-f', name: 'Topstep' })")
    for a, n in (('ba-a', 'Topstep A'), ('ba-b', 'Topstep B'), ('ba-c', 'Topstep C')): pg.evaluate(ACC, [a, n])
    day = pg.evaluate("todayStr()"); yday = pg.evaluate("(d) => ymdAdd(d, -1)", day)
    pg.evaluate("([d, y]) => { put('journals', { id: d, pre: { bias: 'bullish', max_loss: '500', max_trades: '5', saved_at: Math.floor(Date.now() / 1000) - 3600 } }); put('journals', { id: y, post: { reviewed_at: Math.floor(Date.now() / 1000) - 86400, bal: [{ acc: 'ba-c', plat_c: 4996600, sweep_c: 5000000, gap_c: -3400 }] } }) }", [day, yday])
    pg.evaluate(TRADE, ['ba-t1', 'ba-a', day, 10000, True]); pg.evaluate(TRADE, ['ba-t2', 'ba-b', day, 5000, False]); pg.evaluate(TRADE, ['ba-t3', 'ba-c', day, 7000, True])
    pg.evaluate("Promise.all(Object.values(chains)).then(() => true)"); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
    pg.evaluate("(d) => SweepGame.openReview(d)", day); pg.wait_for_selector('#gSheet [data-g=save-review]', timeout=8000); pg.wait_for_timeout(500)
    pg.evaluate("document.querySelectorAll('#gSheet .g-rv-more').forEach((d) => { d.open = true })")
    for k in ('r-followed', 'r-score', 'r-grade'):
      if not pg.locator(f'#gSheet [data-g={k}].on').count(): tap(pg.locator(f'#gSheet [data-g={k}]').first); pg.wait_for_timeout(150)
    st = pg.evaluate("Object.fromEntries([...document.querySelectorAll('#gSheet .g-bal')].map((e) => [e.dataset.bal, [e.querySelector('[data-bal-same]').classList.contains('on'), e.querySelector('[data-bal-same]').textContent.trim()]]))")
    ok(st.get('ba-a') == [True, SAME[lang]], f'{tag} A: a screenshot trade, no gap last time: « {SAME[lang]} » chosen in advance ({st.get("ba-a")})')
    ok(st.get('ba-b') == [False, SAME[lang]], f'{tag} B: a trade typed by hand: the balance asked ({st.get("ba-b")})')
    ok(st.get('ba-c') == [False, SAME[lang]], f'{tag} C: a gap at the last check: the balance asked ({st.get("ba-c")})')
    for a in ('ba-b', 'ba-c'): tap(pg.locator(f'#gSheet [data-bal-same="{a}"]')); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())")
    tap(pg.locator('#gSheet [data-g=save-review]')); pg.wait_for_timeout(1200)
    j = pg.evaluate("(d) => ((getDoc('journals', d) || {}).post || {}).bal || []", day)
    ok(not pg.evaluate("!!document.querySelector('#gSheet.open')") and sorted(b['acc'] for b in j) == ['ba-a', 'ba-b', 'ba-c'] and all(b.get('gap_c') == 0 for b in j), f'{tag}: one tap on each asked account and the day closes, the three balances kept ({j})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
