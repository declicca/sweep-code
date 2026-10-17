"""
Sweep — Face ID in the installed app (17 Oct., step 2 of the second step at log-in), Playwright:
  python3 tests/e2e_faceid.py http://127.0.0.1:8095        (SWEEP_TEST_DB: the dev server's SQLite file)
Chromium's virtual authenticator plays the phone's Face ID (WebAuthn, user verified); the page is opened on localhost (a
WebAuthn RP id cannot be an IP address). A trader of its own. Phone 390 (fr) and computer 1300 (en):
 1  turning it on: a passkey of this phone (the server keeps its public key);
 2  12 hours without the app: every data request answers « locked » (423), the lock screen covers the app;
 3  « Unlock with Face ID »: the phone signs, the server checks the signature, the app opens;
 4  a forged answer is refused; « Use my password »: signed out, the log-in page.
No page error, nothing wider than the window.
"""
import json, os, random, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095').replace('127.0.0.1', 'localhost')
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def idle(uid, hours):
  d = sqlite3.connect(DB); d.execute('UPDATE sessions SET active_at = ? WHERE user_id = ?', (int(time.time()) - hours * 3600, uid)); d.commit(); d.close()
X = {'fr': {'t': 'Sweep est verrouillé', 'u': 'Déverrouiller', 'pw': 'Utiliser mon mot de passe'}, 'en': {'t': 'Sweep is locked', 'u': 'Unlock', 'pw': 'Use my password'}}
with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'fi%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000, 'lang': lang}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Fay', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    cdp = ctx.new_cdp_session(pg); cdp.send('WebAuthn.enable')
    cdp.send('WebAuthn.addVirtualAuthenticator', {'options': {'protocol': 'ctap2', 'transport': 'internal', 'hasResidentKey': True, 'hasUserVerification': True, 'isUserVerified': True, 'automaticPresenceSimulation': True}})
    pg.goto(B + '/#dashboard'); pg.wait_for_function("typeof S !== 'undefined' && S.me && window.SweepFaceID", timeout=20000); pg.wait_for_timeout(800)
    uid = pg.evaluate("S.me.id")
    # 1. turn it on
    res = pg.evaluate("SweepFaceID.register().then(() => 'ok', (e) => String(e))")
    st = pg.evaluate("apiJSON('api/me/passkey')")
    ok(res == 'ok' and st.get('has') is True, f'{tag} 1 Face ID on: a passkey of this phone ({res}, {st})')
    ok(pg.evaluate("fetch('api/data', { headers: { 'X-Requested-With': 'fetch' } }).then((r) => r.status)") == 200, f'{tag} 1 used now: not locked')
    # 2. 12 hours later
    idle(uid, 13)
    s2 = pg.evaluate("fetch('api/data', { headers: { 'X-Requested-With': 'fetch' } }).then((r) => r.status)")
    pg.reload(); pg.wait_for_timeout(3500)
    lk = pg.evaluate("(() => { const e = document.querySelector('aside.nav-lock.open'); return e ? e.textContent : '' })()")
    ok(s2 == 423 and x['t'] in lk and x['u'] in lk, f'{tag} 2 13 hours later: locked (423) and the lock screen ({s2}, {lk[:60]!r})')
    if phone: pg.screenshot(path='/tmp/faceid_lock_390.png')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    # 4a. a forged answer
    bad = pg.evaluate("""(async () => { await fetch('api/auth/unlock/options', { method: 'POST', headers: { 'X-Requested-With': 'fetch', 'Content-Type': 'application/json' }, body: '{}' });
      const r = await fetch('api/auth/unlock', { method: 'POST', headers: { 'X-Requested-With': 'fetch', 'Content-Type': 'application/json' }, body: JSON.stringify({ id: 'x', clientDataJSON: 'e30', authenticatorData: 'AA', signature: 'AA' }) }); return r.status })()""")
    ok(bad == 401, f'{tag} 4 a forged answer: refused ({bad})')
    # 3. unlock
    pg.locator('aside.nav-lock [data-fid-unlock]').click(); pg.wait_for_timeout(4000)
    s3 = pg.evaluate("fetch('api/data', { headers: { 'X-Requested-With': 'fetch' } }).then((r) => r.status)")
    ok(s3 == 200 and pg.locator('aside.nav-lock.open').count() == 0 and pg.evaluate("typeof S !== 'undefined' && Array.isArray(S.trades)"), f'{tag} 3 « {x["u"]} »: the phone signs, the app opens ({s3})')
    # 4b. use my password
    idle(uid, 13); pg.reload(); pg.wait_for_timeout(3500)
    pg.locator('aside.nav-lock [data-fid-pw]').click(); pg.wait_for_timeout(3000)
    ok(pg.locator('#username').count() == 1, f'{tag} 4 « {x["pw"]} »: signed out, the log-in page')
    allerr += errs; ctx.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
