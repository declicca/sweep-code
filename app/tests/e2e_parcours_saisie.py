"""
Sweep — the journey's step 2 (SWEEP.md): a trade without a screenshot, and the express plan for a new trader. Playwright:
  python3 tests/e2e_parcours_saisie.py http://127.0.0.1:8095
A trader of its own. Phone 390 (fr, touch) and computer 1300 (en):
 1  « + » → the sheet: under the drop zone, « Pas de capture ? Entre ton P&L ›»; one tap: the same sheet without an image —
    account, net P&L (focused), Long / Short… —, the subtitle « le P&L de ta plateforme »; no price to type;
 2  net P&L + Long + « Save »: « Trade saved · <the coach> », the trade kept as typed (net, long, no screenshot, source manual,
    New York time), 4 taps from « + »; the drop zone still there to add a screenshot after all;
 3  the plan: a trader who never chose opens the express pre-market; « Plan guidé » switches and keeps the choice (pm_mode = full),
    the next plan opens on it.
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
X = {'fr': {'no': 'Pas de capture ? Entre ton P&L', 'sub': 'le P&L de ta plateforme', 'saved': 'Trade enregistré'},
     'en': {'no': 'No screenshot? Enter your P&L', 'sub': 'your platform’s P&L', 'saved': 'Trade saved'}}
SCREEN = "(document.querySelector('#gSheet.g-pm [data-pm-screen]') || {dataset: {}}).dataset.pmScreen || ''"
WIDE = "document.documentElement.scrollWidth - innerWidth"
NEXT = "(d) => { const n = new Date(d + 'T12:00:00'); do n.setDate(n.getDate() + 1); while (n.getDay() === 0 || n.getDay() === 6); return n.toISOString().slice(0, 10) }"
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'ps%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Ari', 'experience': 'new'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'ps-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } })")
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_timeout(1500)
    act = (lambda s: pg.locator(s).first.tap()) if phone else (lambda s: pg.locator(s).first.click())
    # 1. the sheet and its line
    taps = 0
    act('[data-act=add-trade]:visible'); taps += 1; pg.wait_for_selector('.nav-am.open [data-am=no-shot]', timeout=8000); pg.wait_for_timeout(400)
    ln = pg.locator('.nav-am.open [data-am=no-shot]')
    ok(ln.is_visible() and x['no'] in ln.inner_text() and pg.locator('.nav-am.open [data-am-f=net]').count() == 0, f'{tag} 1 under the drop zone: « {x["no"]} », no field yet')
    box = ln.bounding_box(); ok(box and box['height'] >= 44, f'{tag} 1 the line is a 44 px target ({box and box["height"]})')
    act('.nav-am.open [data-am=no-shot]'); taps += 1; pg.wait_for_timeout(300)
    foc = pg.evaluate("!!(document.activeElement && document.activeElement.dataset && document.activeElement.dataset.amF === 'net')")
    sub = pg.locator('.nav-am.open .nav-am-head .muted').first.inner_text()
    ok(foc and pg.locator('.nav-am.open [data-am-f=net]').is_visible() and pg.locator('.nav-am.open [data-am-seg=dir]').count() == 2, f'{tag} 1 one tap: the net P&L focused, Long / Short there')
    ok(sub == x['sub'] and pg.locator('.nav-am.open label.nav-am-drop').count() == 1 and not pg.locator('.nav-am.open [data-am-f=entry]').is_visible(), f'{tag} 1 « {sub} », the drop zone kept, no price asked')
    # 2. saved
    pg.evaluate("window.__toasts = []; new MutationObserver(() => { const t = document.getElementById('toast'); if (t && t.textContent && !window.__toasts.includes(t.textContent)) window.__toasts.push(t.textContent) }).observe(document.getElementById('toast'), { childList: true, characterData: true, subtree: true })")
    pg.keyboard.type('250')
    act('.nav-am.open [data-am-seg=dir][data-v=long]'); taps += 1
    act('.nav-am.open [data-am=save]'); taps += 1
    pg.wait_for_timeout(2500)
    msg = next((m for m in pg.evaluate("window.__toasts") if m.startswith(x['saved'])), '')
    t = pg.evaluate("(S.trades.filter(t => !t.demo)[0]) || null")
    ok(bool(msg), f'{tag} 2 « {x["saved"]} » with the coach ({msg[:90]!r})')
    ok(t and t.get('direction') == 'long' and abs((t.get('pnl_c') or 0) - (t.get('fees_c') or 0) - 25000) <= 1 and not t.get('shots') and t.get('source') == 'manual' and bool(t.get('entry_time')),
       f'{tag} 2 kept as typed: net $250, long, no screenshot, source manual, a New York time ({t and [t.get("pnl_c"), t.get("fees_c"), t.get("direction"), t.get("source"), t.get("entry_time")]})')
    ok(taps == 4, f'{tag} 2 4 taps from « + » to the saved trade ({taps})')
    # 3. the express plan for a trader who never chose, « Plan guidé » kept
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()"); nx = pg.evaluate(NEXT, day)
    ok(pg.evaluate("(S.settings || {}).pm_mode || null") is None, f'{tag} 3 no choice made yet')
    pg.evaluate("(d) => SweepGame.openPlan(d)", nx)
    for _ in range(40):
      if pg.evaluate(SCREEN): break
      pg.wait_for_timeout(150)
    ok(pg.evaluate(SCREEN) == 'express' and pg.locator('#gSheet [data-pm="mode"][data-v="full"]').count() == 1, f'{tag} 3 the plan opens on the express version, « Plan guidé » one tap away ({pg.evaluate(SCREEN)})')
    pg.evaluate("document.querySelector('#gSheet [data-pm=\"mode\"][data-v=\"full\"]').click()"); pg.wait_for_timeout(600)
    ok(pg.evaluate(SCREEN) == 'base' and pg.evaluate("S.settings.pm_mode") == 'full', f'{tag} 3 « Plan guidé »: the guided plan, the choice kept (pm_mode = full)')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    if pg.locator('#gSheet').count(): pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(500)
    pg.evaluate("localStorage.removeItem('pm.draft')")
    pg.evaluate("(d) => SweepGame.openPlan(d)", pg.evaluate(NEXT, nx))
    for _ in range(40):
      if pg.evaluate(SCREEN): break
      pg.wait_for_timeout(150)
    ok(pg.evaluate(SCREEN) == 'base', f'{tag} 3 the next plan opens on the guided version ({pg.evaluate(SCREEN)})')
    ok(pg.evaluate(WIDE) <= 0, f'{tag} nothing wider than the window')
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
