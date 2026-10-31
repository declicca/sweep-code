"""
Sweep — the journey's step 1, the defects (SWEEP.md, section 3), Playwright:
  python3 tests/e2e_parcours_defauts.py http://127.0.0.1:8095
A trader of its own. Phone 390 (fr) and computer 1300 (en):
 D5   the intention written in last week's recap is on the routine card all this week (it lived only in the game's hidden card);
 D7a  the trade page: the box of a trade's checklist says « Checklist », and its window explains that very number (before:
      « Discipline », with the text of the 30-day discipline score, another number).
No page error, nothing wider than the window.
"""
import json, os, random, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'int': 'Ton intention cette semaine', 'ck': 'Checklist', 'ckT': 'La checklist de ce trade', 'discT': 'Ton score de discipline'},
     'en': {'int': 'Your intention this week', 'ck': 'Checklist', 'ckT': 'The checklist of this trade', 'discT': 'Your discipline score'}}
WIDE = "document.documentElement.scrollWidth - innerWidth"
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'pd%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Ari', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'pd-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000 } })")
    pg.evaluate("put('trades', { id: 'pd-t', account_id: 'pd-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 21000, exit: 21010, pnl_c: 20000, pnl_manual: true, date: todayStr(), entry_time: '10:00', exit_time: '10:05', discipline: { plan: 'y', risk: 'y', stop: 'n' } })")
    pg.wait_for_timeout(2500)
    # D5: last week's recap with an intention (written straight to the test database, as the recap would)
    uid = pg.evaluate("fetch('api/data',{headers:{'X-Requested-With':'fetch'},credentials:'same-origin'}).then(r=>r.json()).then(j=>j.user&&j.user.id)")
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()")
    mon = pg.evaluate("(d) => { const x = new Date(d + 'T12:00:00'); x.setDate(x.getDate() - ((x.getDay() + 6) % 7) - 7); return x.toISOString().slice(0, 10) }", day)
    d = sqlite3.connect(DB); d.execute('INSERT OR REPLACE INTO weekly_reviews (user_id, week_start, data_json, completed_at) VALUES (?, ?, ?, ?)', (uid, mon, json.dumps({'intention': 'Attendre la clôture 5 min'}), int(time.time()))); d.commit(); d.close()
    pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(1500)
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-rt', timeout=8000); pg.wait_for_timeout(1000)
    wk = pg.evaluate("(SweepGame.state() && SweepGame.state().weekly) || {}")
    it = pg.locator('#main .nav-rt .nav-rt-int')
    if wk.get('open') and not wk.get('seen'):
      ok(it.count() == 0, f'{tag} D5 the week\'s recap is ready: its row comes first, no intention line')
    else:
      ok(it.count() == 1 and it.is_visible() and x['int'] in it.inner_text() and 'Attendre la clôture 5 min' in it.inner_text(), f'{tag} D5 the intention of last week\'s recap on the routine card ({it.inner_text() if it.count() else None!r})')
    # D7a: the trade page, the checklist box and its window
    pg.evaluate("location.hash = '#trade/pd-t'"); pg.wait_for_selector('#main .nav-tdisc', timeout=8000); pg.wait_for_timeout(800)
    lbl = pg.locator('#main .nav-tdisc .lbl').inner_text().strip()
    ok(lbl == x['ck'], f'{tag} D7a the trade\'s box says « {x["ck"]} » ({lbl!r})')
    pg.locator('#main .nav-tdisc').click(); pg.wait_for_selector('aside.nav-dwhy.open', timeout=4000)
    h2 = pg.locator('aside.nav-dwhy.open h2').inner_text().strip(); tip = pg.locator('aside.nav-dwhy.open p.muted').count()
    ok(h2 == x['ckT'] and tip == 0, f'{tag} D7a its window explains this trade\'s checklist (« {h2} »), without the tips to raise the 30-day score')
    pg.locator('aside.nav-dwhy.open [data-dwhy-ok]').click(); pg.wait_for_timeout(300)
    # (31 Oct., C5) the routine has no discipline chip any more: one line « Level … · … › » under its title
    pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_selector('#main .nav-rt .nav-rt-sum', timeout=8000); pg.wait_for_timeout(600)
    ok(pg.locator('#main .nav-rt [data-disc-why]').count() == 0, f'{tag} D7a the routine: no discipline chip, its one line instead (31 Oct., C5)')
    ok(pg.evaluate(WIDE) <= 0, f'{tag} nothing wider than the window')
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
