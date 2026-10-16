"""
Sweep — sample data once the first real trade is there (brief 00, phase 1.2-k; Q5, recommendation A), Playwright:
  python3 tests/e2e_demo_hidden.py http://127.0.0.1:8095 [storage_state, unused: it signs up its own trader]
A new trader explores with the sample data, then logs a real trade: from then on the sample trades, accounts and payouts are
hidden everywhere — Trades, Journal, Calendar, Stats, My money, Accounts — not deleted; one line says so and offers
« Remove them » (the app's window, with Cancel). Cancel keeps them; Remove deletes them on the server. His own trade and
account are never touched; his only real trade deleted, the sample data comes back. Before 16 Oct.: only Today hid them; Trades and Stats showed two P&L for the same day.
"""
import json, os, random, sqlite3, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
L = {'fr': ('Données d’exemple masquées', 'Les retirer'), 'en': ('Sample data hidden', 'Remove them'), 'es': ('Datos de ejemplo ocultos', 'Quitarlos')}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
DATA = "fetch('api/data',{headers:{'X-Requested-With':'fetch'},credentials:'same-origin'}).then(r=>r.json()).then(j=>Object.fromEntries(['trades','accounts','payouts'].map(c=>[c,(j[c]||[]).filter(d=>d.demo).length])))"

with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False), ('es', 390, True)):
    tag = f'{w} {lang}'
    try: d = sqlite3.connect(os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    c = br.new_context(viewport={'width': w, 'height': 844}, is_mobile=phone, has_touch=phone)
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'dh%07d@t.dev' % random.randint(0, 9999999), 'consent': True, 'elapsed': 6000}), headers=H)
    c.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Dana', 'last_name': 'Test'}), headers=H)
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160])); pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts',{id:'dh-a',name:'Mon compte',status:'active',phase:'eval',starting_balance_c:5000000,rules:{}})"); pg.wait_for_timeout(1000)
    pg.evaluate("void loadDemo()")
    for _ in range(40):
      pg.wait_for_timeout(500)
      if pg.evaluate("!!document.querySelector('aside.nav-ask.open')"): break
    pg.locator('aside.nav-ask.open [data-ask="1"]').click()
    for _ in range(40):
      pg.wait_for_timeout(500)
      if pg.evaluate("S.trades.filter(t=>t.demo).length > 10"): break
    n0 = -1
    for _ in range(60):   # the sample data is saved in batches: wait until the server has all of it (under load it takes a while)
      pg.wait_for_timeout(500); mem = pg.evaluate("S.trades.filter(t=>t.demo).length")
      if mem > 10 and pg.evaluate(DATA)['trades'] == mem: n0 = mem; break
    pg.evaluate("location.hash='#trades'"); pg.wait_for_timeout(1800)
    ok(n0 > 10 and pg.evaluate("document.querySelectorAll('#main [data-href^=\"#trade/demo\"], #main a[href^=\"#trade/demo\"]').length") > 0, f'{tag} exploring: {n0} sample trades shown')
    # the first real trade
    pg.evaluate("put('trades',{id:'dh-t1',account_id:'dh-a',instrument:'NQ',direction:'long',contracts:1,entry:21000,exit:21010,pnl_c:20000,pnl_manual:true,date:todayStr(),session_date:true,entry_time:'10:00',exit_time:'10:05'})"); pg.wait_for_timeout(1500)
    for h in ('#trades', '#journal', '#calendar', '#analytics', '#payouts', '#accounts'):
      pg.evaluate(f"location.hash='{h}'"); pg.wait_for_timeout(1700)
      shown = pg.evaluate("document.querySelectorAll('#main [data-href*=\"demo-\"], #main a[href*=\"demo-\"], #main [data-id^=\"demo-\"], #main [data-acc^=\"demo-\"]').length")
      ok(shown == 0, f'{tag} {h}: no sample data shown ({shown})')
    pg.evaluate("location.hash='#trades'"); pg.wait_for_timeout(1700)
    k = pg.evaluate("[...document.querySelectorAll('#main .ikpis .ik b, #main .kpis b')].map(b=>b.textContent.trim())")
    line = pg.evaluate("(document.querySelector('#main .nav-demo-hid')||{}).innerText||''")
    ok(L[lang][0] in line and L[lang][1] in line, f'{tag} one line: « {L[lang][0]} · {L[lang][1]} » ({line[:80]!r})')
    srv = pg.evaluate(DATA)
    ok(srv['trades'] == n0, f'{tag} hidden, not deleted: still {srv["trades"]} on the server')
    pg.evaluate("remove('trades','dh-t1')"); pg.wait_for_timeout(1200)
    back = pg.evaluate("[S.trades.filter(t=>t.demo).length, !!document.querySelector('#main .nav-demo-hid')]")
    ok(back == [n0, False], f'{tag} his only real trade deleted: the sample data comes back ({back})')
    pg.evaluate("put('trades',{id:'dh-t1',account_id:'dh-a',instrument:'NQ',direction:'long',contracts:1,entry:21000,exit:21010,pnl_c:20000,pnl_manual:true,date:todayStr(),session_date:true,entry_time:'10:00',exit_time:'10:05'}); location.hash='#dashboard'"); pg.wait_for_timeout(800)
    pg.evaluate("location.hash='#trades'"); pg.wait_for_timeout(1700)
    # Cancel keeps them; Remove deletes them
    pg.locator('#main .nav-demo-hid [data-act="demo-remove"]').click(); pg.wait_for_timeout(700)
    pg.locator('aside.nav-ask.open [data-ask="0"]').click(); pg.wait_for_timeout(1200)
    ok(pg.evaluate(DATA)['trades'] == n0, f'{tag} Cancel: kept')
    pg.locator('#main .nav-demo-hid [data-act="demo-remove"]').click(); pg.wait_for_timeout(700)
    pg.locator('aside.nav-ask.open [data-ask="1"]').click(); pg.wait_for_timeout(4000)
    srv = pg.evaluate(DATA)
    ok(srv == {'trades': 0, 'accounts': 0, 'payouts': 0}, f'{tag} Remove: gone from the server ({srv})')
    ok(pg.evaluate("!!getDoc('trades','dh-t1') && !!getDoc('accounts','dh-a') && !document.querySelector('#main .nav-demo-hid')"), f'{tag} his own trade and account untouched, the line gone')
    ok(not errs and pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} no page error, nothing wider than the window ({errs[:1]})')
    c.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
