"""
Sweep — the second step at log-in (17 Oct., step 1: a code by email on a new browser), Playwright:
  python3 tests/e2e_twofa.py http://127.0.0.1:8095
The dev copy writes its emails to data/outbox.jsonl (never sent). A trader signs up on browser A (remembered). Then:
 1  browser B, new: the right password → « Check it's you », the code sent to the masked email; a wrong code: refused;
    the right one: in; the code email says it is valid 10 minutes;
 2  B again (logged out, logged in): the password only, no code;
 3  browser C: 5 wrong codes → the code has expired, a new log-in is needed; « Send a new code » right away: wait a little;
 4  Settings › « Your devices » on B: A and B listed, B marked « This browser »; « Sign out » A → A is signed out;
Phone 390 (fr) and computer 1300 (en). No page error, nothing wider than the window.
"""
import json, os, random, re, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
BOX = os.path.join(os.path.dirname(os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')), 'outbox.jsonl')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
PW = 'Testpass123!'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def mails(to):
  try: return [json.loads(l) for l in open(BOX, encoding='utf-8').read().splitlines() if l.strip() and json.loads(l).get('to') == to]
  except FileNotFoundError: return []
def code_of(m): return re.search(r'\b(\d{6})\b', m['subject']).group(1)
X = {'fr': {'t': 'Vérifie que c’est toi', 'wrong': 'Code incorrect', 'exp': 'Ce code a expiré', 'wait': 'Attends un peu', 'h': 'Tes appareils', 'me': 'Ce navigateur', 'out': 'Déconnecter', 'valid': '10 minutes'},
     'en': {'t': 'Check it’s you', 'wrong': 'Wrong code', 'exp': 'This code has expired', 'wait': 'Wait a little', 'h': 'Your devices', 'me': 'This browser', 'out': 'Sign out', 'valid': '10 minutes'}}
with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    mk = lambda: br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    email = 'tf%06d@t.dev' % random.randint(0, 999999)
    A = mk(); A.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = A.request.post(B + '/api/auth/register', data=json.dumps({'password': PW, 'email': email, 'consent': True, 'elapsed': 6000, 'lang': lang}), headers=H)
    ok(r.status == 201 and any(c['name'] == 'tj_dev' for c in A.cookies()), f'{tag} signing up: in, this browser remembered')
    A.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Tia', 'experience': 'gt1'}), headers=H)
    def login_page(ctx):
      pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
      pg.goto(B + '/'); pg.wait_for_selector('#username', timeout=15000); pg.wait_for_timeout(500)
      if pg.locator('[data-m=login]').first.is_visible(): pg.locator('[data-m=login]').first.click(); pg.wait_for_timeout(400)
      pg.fill('#username', email); pg.fill('#password', PW); pg.click('#go'); pg.wait_for_timeout(1500)
      return pg, errs
    # 1. browser B, new
    Bc = mk(); Bc.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    n0 = len(mails(email))
    pg, errs = login_page(Bc)
    h = pg.evaluate("(document.getElementById('h') || {}).textContent || ''"); sub = pg.evaluate("(document.getElementById('sub') || {}).textContent || ''")
    ms = mails(email)
    ok(h == x['t'] and '•' in sub and email.split('@')[1] in sub and pg.locator('#otp').is_visible() and len(ms) == n0 + 1, f'{tag} 1 a new browser: « {h} », « {sub[:80]} », one email')
    ok(x['valid'] in ms[-1]['text'] and code_of(ms[-1]) in ms[-1]['text'], f'{tag} 1 the email: the code, valid 10 minutes')
    if phone: pg.screenshot(path='/tmp/twofa_390.png')
    else: pg.screenshot(path='/tmp/twofa_1300.png')
    good = code_of(ms[-1]); bad = '000000' if good != '000000' else '111111'
    pg.fill('#otp', bad); pg.wait_for_timeout(1500)
    er = pg.evaluate("(document.getElementById('err') || {}).textContent || ''")
    ok(x['wrong'] in er and pg.locator('#otp').is_visible(), f'{tag} 1 a wrong code: « {er} »')
    pg.fill('#otp', good); pg.wait_for_timeout(3000)
    inside = pg.evaluate("!!document.querySelector('#main') && !document.getElementById('username')")
    ok(inside, f'{tag} 1 the right code: in the app')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    allerr += errs
    # 2. B again: the password only
    Bc.request.post(B + '/api/auth/logout', headers=H); pg.close()
    n1 = len(mails(email))
    r = Bc.request.post(B + '/api/auth/login', data=json.dumps({'username': email, 'password': PW}), headers=H)
    ok(r.ok and not r.json().get('code') and len(mails(email)) == n1, f'{tag} 2 the same browser again: the password only, no code ({r.json()})')
    # 3. browser C: 5 wrong codes, then a new code too soon
    Cc = mk()
    r = Cc.request.post(B + '/api/auth/login', data=json.dumps({'username': email, 'password': PW}), headers=H)
    ok(r.ok and r.json().get('code'), f'{tag} 3 another new browser: a code asked')
    good = code_of(mails(email)[-1]); bad = '000000' if good != '000000' else '111111'
    st = [Cc.request.post(B + '/api/auth/code', data=json.dumps({'code': bad}), headers=H).status for _ in range(5)]
    r = Cc.request.post(B + '/api/auth/code', data=json.dumps({'code': good}), headers=H)
    ok(st == [401] * 4 + [410] and r.status == 410, f'{tag} 3 five wrong codes: the 5th says to log in again, even the right one is refused now ({st}, {r.status})')
    Cc.request.post(B + '/api/auth/login', data=json.dumps({'username': email, 'password': PW}), headers=H)
    r = Cc.request.post(B + '/api/auth/code/resend', headers=H)
    ok(r.status == 429, f'{tag} 3 « Send a new code » right away: wait a little ({r.status})')
    Cc.close()
    # 4. Settings › Your devices on B: sign out A
    pg = Bc.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#settings'); pg.wait_for_selector('#main .nav-devs', timeout=15000); pg.wait_for_timeout(600)
    txt = pg.evaluate("document.querySelector('#main .nav-devs').textContent")
    ok(x['h'] in txt and x['me'] in txt and pg.locator('#main [data-dev-out]').count() >= 1, f'{tag} 4 « {x["h"]} »: this browser marked, the other one can be signed out')
    pg.locator('#main [data-dev-out]').first.click(); pg.wait_for_timeout(600)
    dlg = pg.locator('.nav-dlg.open button', has_text=x['out'])
    if dlg.count(): dlg.last.click()
    pg.wait_for_timeout(1500)
    ra = A.request.get(B + '/api/data', headers=H)
    ok(ra.status == 401, f'{tag} 4 « {x["out"]} » the other browser: it is signed out ({ra.status})')
    allerr += errs; A.close(); Bc.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
