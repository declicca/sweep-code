"""
Sweep — suggestions « do it now » (16 Oct., step 2 of the announcements), Playwright:
  python3 tests/e2e_suggest.py http://127.0.0.1:8095
A trader of its own. Phone 390 (fr):
 1  the day of sign-up: nothing offered;
 2  from the next day: Sweep on the home screen first — iPhone / Android gestures (« Compris », « Plus tard »); with Chrome's
    own prompt: « Installer » installs it in one tap (the prompt is the browser's);
 3  « Plus tard »: not again for 7 days, the next one comes: the reminders on this phone (« Activer »: turned on), then a plan
    after 3 sessions without one (« Faire mon plan »: the plan sheet);
 4  3 times at most each; one window per session.
Computer 1300 (en): never offered. No page error, nothing wider than the window.
"""
import json, random, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
DAY2 = "() => { S.me.created_at = Math.floor(Date.now() / 1000) - 5 * 86400; localStorage.setItem('sw.day0', ymdAdd(todayStr(), -5)); sessionStorage.removeItem('sw.modal'); }"
WIN = "() => { const e = document.querySelector('aside.nav-inst.open'); return e ? { id: e.dataset.sg, h: e.querySelector('h2').textContent, go: e.querySelector('[data-inst-ok]').textContent, later: !!e.querySelector('[data-inst-later]'), steps: e.querySelectorAll('.nav-inst-l:not([hidden]) li').length } : null }"
PUSH = "(on) => { SweepNotify.push.state = async () => ({ available: true, can: true, on: window.__pushOn || false }); SweepNotify.push.on = async () => { window.__pushOn = true; return { available: true, can: true, on: true }; }; }"
def ask(pg):
  pg.evaluate("sessionStorage.removeItem('sw.modal'); SweepInstall.suggest()"); pg.wait_for_timeout(900)
  return pg.evaluate(WIN)

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')) } catch (e) {}" % lang)
    ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'sg%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Sol', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'sg-a', name: 'Apex 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, rules: { dd_c: 250000 } })"); pg.wait_for_timeout(5600)
    ok(pg.evaluate(WIN) is None and ask(pg) is None, f'{tag} the day of sign-up: nothing offered')
    pg.evaluate(DAY2)
    if not phone:
      ok(ask(pg) is None, f'{tag} a computer: never offered')
      allerr += errs; ctx.close(); continue
    # 2. the home screen first, with the gestures
    s = ask(pg)
    ok(s and s['id'] == 'install' and s['steps'] == 3 and s['go'] == 'Compris' and s['later'], f'{tag} from the next day: Sweep on the home screen, the 3 gestures, « Compris » and « Plus tard » ({s})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    pg.screenshot(path='/tmp/suggest_install_390.png')
    ok(ask(pg) is not None and pg.locator('aside.nav-inst.open').count() == 1, f'{tag} one window at a time')
    # 3. « Plus tard » → the next one: the reminders
    pg.locator('aside.nav-inst.open [data-inst-later]').click(); pg.wait_for_timeout(400)
    until = pg.evaluate("(SweepInstall.state().install || {}).until - Date.now()")
    ok(until and 6.9 * 864e5 < until <= 7 * 864e5, f'{tag} « Plus tard »: not again for 7 days ({round((until or 0) / 864e5, 2)} d)')
    pg.evaluate(PUSH)
    s = ask(pg)
    ok(s and s['id'] == 'push' and s['go'] == 'Activer', f'{tag} then the reminders on this phone ({s})')
    pg.screenshot(path='/tmp/suggest_push_390.png')
    pg.locator('aside.nav-inst.open [data-inst-ok]').click(); pg.wait_for_timeout(800)
    ok(pg.evaluate("window.__pushOn === true && (SweepInstall.state().push || {}).done === true"), f'{tag} « Activer »: turned on, not offered again')
    # a plan after 3 sessions without one
    ok(ask(pg) is None, f'{tag} nothing else to offer yet')
    pg.evaluate("() => { for (let k = 1; k <= 3; k++) put('trades', { id: 'sg-t' + k, account_id: 'sg-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 5000, pnl_manual: true, date: ymdAdd(todayStr(), -k), session_date: true, entry_time: '10:00', exit_time: '10:05' }) }"); pg.wait_for_timeout(1200)
    if pg.locator('aside.nav-inst.open').count(): pg.locator('aside.nav-inst.open [data-inst-later]').click(); pg.wait_for_timeout(300)
    pg.evaluate("() => { const r = SweepInstall.state(); delete r.plan; localStorage.setItem('sw.sugg', JSON.stringify(r)); }")
    s = ask(pg)
    ok(s and s['id'] == 'plan' and s['go'] == 'Faire mon plan', f'{tag} 3 sessions without a plan: « Ton plan avant ton prochain trade » ({s})')
    pg.locator('aside.nav-inst.open [data-inst-ok]').click(); pg.wait_for_timeout(1200)
    ok(pg.locator('#gSheet.g-plan, #gSheet [data-g=save-plan]').count() > 0, f'{tag} « Faire mon plan »: the plan sheet opens')
    pg.evaluate("(document.querySelector('#gSheet [data-g=close]') || { click() {} }).click()"); pg.wait_for_timeout(500)
    # 4. 3 times at most
    pg.evaluate("() => localStorage.setItem('sw.sugg', JSON.stringify({ install: { n: 3 }, push: { done: true }, plan: { done: true } }))")
    ok(ask(pg) is None, f'{tag} shown 3 times: not again')
    # Chrome's own prompt: « Installer » in one tap
    pg.evaluate("() => { localStorage.setItem('sw.sugg', '{}'); const e = new Event('beforeinstallprompt'); e.prompt = () => { window.__prompted = 1 }; e.userChoice = Promise.resolve({ outcome: 'accepted' }); dispatchEvent(e); }")
    s = ask(pg)
    ok(s and s['id'] == 'install' and s['go'] == 'Installer' and s['steps'] == 0, f'{tag} Android / Chrome: « Installer », no gestures to read ({s})')
    pg.screenshot(path='/tmp/suggest_android_390.png')
    pg.locator('aside.nav-inst.open [data-inst-ok]').click(); pg.wait_for_timeout(800)
    ok(pg.evaluate("window.__prompted === 1 && localStorage.getItem('sw.installShown') === '1'"), f'{tag} « Installer »: the browser installs it, not offered again')
    allerr += errs; ctx.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
