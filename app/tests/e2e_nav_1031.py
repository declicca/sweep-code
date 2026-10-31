"""
Sweep — the 31 Oct. tour: navigation, understanding, use (briefs/brief-app-navigation-2026-10-31.md), Playwright:
  python3 tests/e2e_nav_1031.py http://127.0.0.1:8095
A trader of its own; phone 390 (fr, touch, dark), computer 1300 (en, light), phone 390 (es, light).
 A1 no tab bar with a single tab: on Accounts while « My money » is hidden; on My money both tabs
 A3 Today (computer): no « Add a trade » in the title row
 A4 an account's page: its 5 last trades, then « See its 7 trades › »; each line: date, time, setup
 B2 no « Performance » pill beside « Net P&L »
 B4 one trade in the bias, one against: « 1 of 2 » on Today and « 1 / 2 » in the Journal
 B5 « Checklist to do » once, grey
 C1 the phone's new-trade sheet: « Choose a screenshot » (no Ctrl+V), one « Without a screenshot › », no « Enter by hand »;
    in the P&L entry the screenshot area does not come back
 C5 the routine: one line « Level … · … › » under its title, no pills; no « I'm done for today » before « Now » says stop
No page error, nothing wider than the window.
"""
import json, random, sqlite3, os, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'one': '1 sur 2 trades dans ton plan', 'drop': 'Choisir une capture', 'no': 'Sans capture ›', 'all': 'Voir ses 7 trades ›', 'tolog': 'Checklist à faire', 'lv': 'Niveau'},
     'en': {'one': '1 of 2 trades in your plan', 'drop': 'Choose a screenshot', 'no': 'Without a screenshot ›', 'all': 'See its 7 trades ›', 'tolog': 'Checklist to do', 'lv': 'Level'},
     'es': {'one': '1 de 2 operaciones en tu plan', 'drop': 'Elegir una captura', 'no': 'Sin captura ›', 'all': 'Ver sus 7 operaciones ›', 'tolog': 'Checklist pendiente', 'lv': 'Nivel'}}
FLUSH = "Promise.all(Object.values(chains)).then(() => true)"
SWC = "document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())"
VIS = "(s) => [...document.querySelectorAll(s)].filter((e) => e.getClientRects().length).length"
try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
except Exception: pass
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, scheme in (('fr', True, 'dark'), ('en', False, 'light'), ('es', True, 'light')):
    w = 390 if phone else 1300; tag = f'{w}-{lang}-{scheme}'; x = X[lang]
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-MX'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'nv%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    day = pg.evaluate("todayStr()")
    pg.evaluate("put('accounts', { id: 'nv-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } })")
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '1500', max_trades: '5', saved_at: Math.floor(Date.now() / 1000) - 7200 } })", day)
    # B4: one long (in the bias), one short (against it), both with a stop; 5 older trades for A4
    T = "([id, d, dir, t, pnl]) => put('trades', { id, account_id: 'nv-a', instrument: 'MNQ', direction: dir, contracts: 1, entry: 1, exit: 2, stop: 0.5, pnl_c: pnl, pnl_manual: true, date: d, session_date: true, entry_time: t, exit_time: t, setup: 'Liquidity sweep' })"
    pg.evaluate(T, ['nv-1', day, 'long', '09:45:00', 12000]); pg.evaluate(T, ['nv-2', day, 'short', '10:20:00', -8000])
    for k in range(5): pg.evaluate(T, [f'nv-o{k}', pg.evaluate("(k) => ymdAdd(todayStr(), -7 - k)", k), 'long', '10:00:00', 5000])
    pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500); pg.evaluate("render()"); pg.wait_for_timeout(1500); pg.evaluate(SWC)
    rt = pg.evaluate("(document.querySelector('#main .nav-rt') || {}).innerText || ''")
    ok(x['one'] in rt, f'B4 {tag}: Today « {x["one"]} »')
    # C5
    ok(pg.evaluate(VIS, '#main .nav-rt .nav-rt-disc, #main .nav-rt .nav-rt-streak, #main .nav-rt .nav-rt-lv') == 0 and x['lv'] in pg.evaluate("(document.querySelector('#main .nav-rt-sum') || {}).textContent || ''"), f'C5 {tag}: one line « {x["lv"]} … › », no pills')
    ok(pg.evaluate(VIS, '#main .nav-rt [data-rt=fin]') == 0, f'C5 {tag}: no « done for today » link before « Now » says stop')
    # B2, B5
    ok(pg.evaluate(VIS, '#main .mny-tag.perf') == 0, f'B2 {tag}: no « Performance » pill')
    tl = pg.evaluate("[...document.querySelectorAll('#main .nav-tolog')].filter((e) => e.getClientRects().length).map((e) => getComputedStyle(e).color === getComputedStyle(document.querySelector('#main .nav-tr-p.neg') || document.body).color)")
    ok(tl == [False], f'B5 {tag}: « {x["tolog"]} » once, not in the loss colour ({tl})')
    # A3
    if not phone: ok(pg.evaluate(VIS, '.main-wrap .top .nav-addtop') == 0, f'A3 {tag}: no « Add a trade » in Today\'s title row')
    # B4 the Journal
    pg.evaluate("(d) => { location.hash = '#journal/' + d }", day); pg.wait_for_timeout(2500)
    jr = pg.evaluate("(document.querySelector('#main .nav-recap') || {}).innerText || ''")
    ok('1 / 2' in jr, f'B4 {tag}: the Journal « 1 / 2 » ({jr[:90]!r})')
    # A4
    pg.evaluate("location.hash = '#account/nv-a'"); pg.wait_for_timeout(2500)
    rows = pg.evaluate("[...document.querySelectorAll('#main .trow, #main tr[data-href^=\"#trade/\"]')].filter((e) => e.getClientRects().length).length")
    more = pg.evaluate("(document.querySelector('#main .acct-all-tr') || {}).textContent || ''")
    ok(rows == 5 and more == x['all'], f'A4 {tag}: 5 trades, then « {more} » ({rows})')
    if phone:
      line = pg.evaluate("(document.querySelector('#main .trow small') || {}).textContent || ''")
      ok(line.endswith('10:20 · Liquidity sweep'), f'A4 {tag}: the line: date, time, setup ({line!r})')
    pg.locator('#main .acct-all-tr').click(); pg.wait_for_timeout(1500)
    ok(pg.evaluate("location.hash") == '#trades' and pg.evaluate("F.account") == 'nv-a', f'A4 {tag}: it opens Trades on this account')
    pg.evaluate("F.account = 'all'; saveF()")
    # A1
    pg.evaluate("location.hash = '#accounts'"); pg.wait_for_timeout(1500)
    pg.evaluate("document.body.classList.add('disc-no-money')"); pg.wait_for_timeout(100)
    one = pg.evaluate("[...document.querySelectorAll('#main .nav-seg')].filter((e) => e.getClientRects().length).map((e) => [...e.querySelectorAll('a')].filter((a) => a.getClientRects().length).length)")
    ok(not one, f'A1 {tag}: Accounts without « My money »: no tab bar ({one})')
    pg.evaluate("location.hash = '#payouts'"); pg.wait_for_timeout(1500)
    pg.evaluate("document.body.classList.add('disc-no-money')"); pg.wait_for_timeout(100)
    two = pg.evaluate("[...document.querySelectorAll('#main .nav-seg')].filter((e) => e.getClientRects().length).map((e) => [...e.querySelectorAll('a')].filter((a) => a.getClientRects().length).length)")
    ok(two == [2], f'A1 {tag}: on My money both tabs ({two})')
    # C1
    if phone:
      pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(1200)
      pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am.open [data-am=no-shot]', timeout=8000); pg.wait_for_timeout(400)
      drop = pg.evaluate("(document.querySelector('.nav-am.open .nav-am-drop b') || {}).textContent || ''")
      ok(drop == x['drop'] and pg.evaluate(VIS, '.nav-am.open [data-am=no-shot]') == 1 and pg.evaluate(VIS, '.nav-am.open [data-am=to-manual]') == 0 and pg.locator('.nav-am.open [data-am=no-shot]').inner_text() == x['no'],
         f'C1 {tag}: « {drop} », one « {x["no"]} », no « Enter by hand »')
      pg.locator('.nav-am.open [data-am=no-shot]').click(); pg.wait_for_timeout(500)
      ok(pg.evaluate(VIS, '.nav-am.open .nav-am-drop') == 0 and pg.evaluate(VIS, '.nav-am.open [data-am-f=net]') == 1, f'C1 {tag}: in the P&L entry the screenshot area does not come back')
      pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    pg.evaluate(FLUSH)
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
