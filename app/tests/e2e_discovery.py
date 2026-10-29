"""
Sweep — the discovery missions (SWEEP.md step 5, 29 Oct.), Playwright:
  python3 tests/e2e_discovery.py http://127.0.0.1:8095
A trader of its own, marked to follow the missions (users.discovery_done = 2: the tests' accounts see everything otherwise,
SWEEP_DISC_ALL); phone 390 (fr, touch) and computer 1300 (en).
 1  day 1: My money and Sweep AI are not shown; the routine shows « Mission 1 of 15 »
 2  each mission ticks by its behaviour: the account, the plan, the first trade, the day closed — never by opening its page
    (« Do it now » opens the plan: still mission 2); 20 XP once each (disc:N)
 3  one mission a trading day: the 4 of day 1 done, nothing more today (mission 5 waits for day 2)
 4  « Show everything » (Settings › My routine): every function shown, at once
 5  an account from before the missions sees everything (nothing lost)
No page error, nothing wider than the window.
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
X = {'fr': {'kick': 'Mission 1 sur 15', 'm2': 'Ton risque permis', 'all': 'Tout montrer'}, 'en': {'kick': 'Mission 1 of 15', 'm2': 'Your risk allowed', 'all': 'Show everything'}}
FLUSH = "Promise.all(Object.values(chains)).then(() => true)"
DISC = "(SweepGame.state() && SweepGame.state().discovery) || null"
def mark(uid, v):
  d = sqlite3.connect(DB); d.execute('UPDATE users SET discovery_done = ? WHERE id = ?', (v, uid)); d.commit(); d.close()
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone in (('fr', True), ('en', False)):
    w = 390 if phone else 1300; tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'ds%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'lt1'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    SWC = "document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())"   # (a day swept: its celebration, whenever it comes)
    def tap(l):
      pg.evaluate(SWC); pg.wait_for_timeout(200); l.tap() if phone else l.click()
    pg.goto(B + '/'); pg.wait_for_timeout(2500)
    uid = pg.evaluate("S.uid"); mark(uid, 2)
    def refresh():
      pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2200); pg.evaluate("render()"); pg.wait_for_timeout(600)
      return pg.evaluate(DISC)
    # 1. day 1 (the account put in directly: the first-account page is the step before)
    pg.evaluate("put('accounts', { id: 'ds-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000, target_c: 300000 } })")
    pg.evaluate("location.hash = '#dashboard'"); d = refresh()
    cls = pg.evaluate("[...document.body.classList].filter((c) => c.startsWith('disc-'))")
    ok(d and not d['all'] and 'disc-no-money' in cls and 'disc-no-ai' in cls, f'1 {tag}: day 1, My money and Sweep AI not shown ({d and d.get("current")}, {cls})')
    ok(pg.evaluate("!document.querySelector('#main .d-pay') || !document.querySelector('#main .d-pay').getClientRects().length"), f'1 {tag}: no « My money » card on Today')
    # 2. the account done (mission 1): mission 2 in the routine, « Do it now » opens the plan and ticks nothing
    ok(d['done'] and 1 in d['done'] and d['current'] == 2, f'2 {tag}: the account ticks mission 1 ({d["done"]}, current {d["current"]})')
    line = pg.evaluate("(document.querySelector('#main .nav-disc') || {}).textContent || ''")
    ok(x['m2'] in line, f'2 {tag}: the routine shows mission 2, « {x["m2"]} » ({line[:60]!r})')
    tap(pg.locator('#main .nav-disc [data-disc-go]')); pg.wait_for_timeout(1200)
    opened = pg.evaluate("!!document.querySelector('#gSheet [data-gp=max_loss], #gSheet [data-pmf=max_loss], #gSheet .g-plan, #gSheet.g-pm')")
    pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(500)
    d = refresh()
    ok(opened and d['current'] == 2, f'2 {tag}: « Do it now » opens the plan, opening it ticks nothing ({opened}, current {d["current"]})')
    day = pg.evaluate("todayStr()")
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '500', max_trades: '3', saved_at: Math.floor(Date.now() / 1000) } })", day); d = refresh()
    ok(2 in d['done'] and d['current'] == 3, f'2 {tag}: the plan ticks mission 2 ({d["current"]})')
    pg.evaluate("(d) => put('trades', { id: 'ds-t1', account_id: 'ds-a', instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 8000, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:05' })", day); d = refresh()
    ok(3 in d['done'] and d['current'] == 4, f'2 {tag}: the first trade ticks mission 3 ({d["current"]})')
    pg.evaluate("(d) => editDoc('journals', d, (j) => { j.post = { followed: 'yes', discipline: 4, grade: 'A', reviewed_at: new Date().toISOString(), bal: [{ acc: 'ds-a', gap_c: 0 }] }; })", day); d = refresh()
    ok(4 in d['done'], f'2 {tag}: the day closed ticks mission 4 ({d["done"]})')
    xp = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM xp_events WHERE user_id = ? AND event_key LIKE 'disc:%'", (uid,)).fetchone()[0]
    ok(xp == len(d['done']), f'2 {tag}: 20 XP once for each mission done ({xp} for {len(d["done"])})')
    # 3. one mission a trading day
    ok(d['current'] is None and pg.locator('#main .nav-disc').count() == 0, f'3 {tag}: the 4 of day 1 done, nothing more today (next: {d["next"]})')
    # 4. « Show everything »
    pg.evaluate("location.hash = '#settings'"); pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelectorAll('#main details.nav-sgd').forEach((g) => { if (g.dataset.i === '1') g.open = true })"); pg.wait_for_timeout(400)
    b = pg.locator('#main [data-disc-all]')
    ok(b.count() == 1 and b.text_content() == x['all'], f'4 {tag}: « {x["all"]} » in « My routine »')
    if b.count(): tap(b); pg.wait_for_timeout(2500)
    d = pg.evaluate(DISC); cls = pg.evaluate("[...document.body.classList].filter((c) => c.startsWith('disc-'))")
    ok(d and d['all'] and not cls, f'4 {tag}: every function shown ({cls})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    pg.evaluate(FLUSH)
    ctx.close()
  # 5. an account from before (the tests' accounts: SWEEP_DISC_ALL) sees everything
  ctx = br.new_context(viewport={'width': 1300, 'height': 850}); ctx.add_init_script("sessionStorage.setItem('sw.modal', '1')")
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
  ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'dso%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
  pg = ctx.new_page(); pg.goto(B + '/'); pg.wait_for_timeout(2500)
  pg.evaluate("put('accounts', { id: 'dso-a', name: 'Apex 50K', status: 'active', starting_balance_c: 5000000, created_on: '2026-09-01' })"); pg.evaluate("location.hash = '#dashboard'")
  pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500); pg.evaluate("render()"); pg.wait_for_timeout(500)
  d = pg.evaluate(DISC); cls = pg.evaluate("[...document.body.classList].filter((c) => c.startsWith('disc-'))")
  ok(d and d['all'] and not cls and pg.locator('#main .nav-disc').count() == 0, f'5 an account from before: everything shown, no mission ({cls})')
  ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
