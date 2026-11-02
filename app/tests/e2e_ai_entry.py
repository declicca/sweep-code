"""
Sweep — a trade from one sentence or a screenshot, in one field (brief avance, step 3; ai/ai-entry.php, shotForm in src/nav.js).
Playwright:
  python3 tests/e2e_ai_entry.py http://127.0.0.1:8095 [state]        (SWEEP_TEST_DB: the dev server's SQLite file)
Sweep AI is the test stand-in (SWEEP_AI_ENTRY_MOCK, SWEEP_AI_MOCK: tools/run.sh), never Google.
A trader of its own with two accounts, on a phone 390 (touch) and a computer 1300, light and dark, in EN, FR and ES:
 1  Today: « Describe your trade or drop a screenshot »; a plain sentence (« short ES 1 lot stopped -$250 at 9:42 »…) + Enter
    → the add-trade sheet, filled in: side, symbol, contracts, P&L, time; the sentence shown; nothing saved;
 2  two accounts and none named: « Which account? », highlighted; « Save » asks for it, still nothing saved; the account
    picked → no longer highlighted → « Save »: the trade as read;
 3  in the « + » sheet, a sentence Sweep AI reads with low confidences (contracts, time): those fields highlighted
    (« Check »), « Check the trade » open; closed without saving: nothing added;
 4  a screenshot in the same field still works (read by the screenshot reader, the sheet filled in);
 5  Free with its 10 AI entries of the month used (billing on, a second server on port + 1): the plans' window
    (« You've used this month's 10 AI entries ») and the sheet to fill by hand.
No page error, nothing wider than the window.
"""
import json, os, random, signal, sqlite3, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APPDIR = os.path.dirname(os.path.dirname(DB))   # the served copy (its data/ holds the database)
P1 = int(B.rsplit(':', 1)[1]) + 1; B1 = f'http://127.0.0.1:{P1}'
SHOTS = os.environ.get('SWEEP_SHOTS', '')
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples', 'shot-topstepx-one-trade.png')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def sql(q, args=()):
  d = sqlite3.connect(DB, timeout=10); c = d.execute(q, args); r = c.fetchall(); d.commit(); d.close(); return r

X = {
  'en': {'ph': 'Describe your trade or drop a screenshot', 'say': 'short ES 1 lot stopped -$250 at 9:42', 'dir': 'short', 'inst': 'ES', 'qty': '1', 'net': '-250.00', 'time': '09:42',
         'ask': 'Which account?', 'need': 'Pick the account of this trade.', 'chk': 'Check', 'ai': 'took a long on nasdaq this morning, made 400 with two', 'quota': 'You’ve used this month’s 10 AI entries', 'saved': 'Trade saved'},
  'fr': {'ph': 'Décris ton trade ou dépose une capture', 'say': 'achat NQ 2 contrats +400 $ à 9h42', 'dir': 'long', 'inst': 'NQ', 'qty': '2', 'net': '400.00', 'time': '09:42',
         'ask': 'Quel compte ?', 'need': 'Choisis le compte de ce trade.', 'chk': 'À vérifier', 'ai': 'long nasdaq ce matin, +400 avec deux', 'quota': 'Tu as utilisé tes 10 saisies IA du mois', 'saved': 'Trade enregistré'},
  'es': {'ph': 'Describe tu operación o suelta una captura', 'say': 'venta ES 1 contrato -250$ a las 10:05', 'dir': 'short', 'inst': 'ES', 'qty': '1', 'net': '-250.00', 'time': '10:05',
         'ask': '¿Qué cuenta?', 'need': 'Elige la cuenta de esta operación.', 'chk': 'Revisar', 'ai': 'long en nasdaq esta mañana, +400 con dos', 'quota': 'Usaste tus 10 entradas con IA del mes', 'saved': 'Operación guardada'},
}
WIDE = "document.documentElement.scrollWidth - innerWidth"
REAL = "S.trades.filter((t) => !t.demo).length"
FORM = """() => { const q = (s) => document.querySelector('.nav-am-shot.open ' + s), v = (s) => (q(s) || {}).value;
  return { dir: (q('[data-am-seg=dir].on') || {dataset: {}}).dataset.v || '', inst: ((q('.nav-am-selb[data-am-sel=inst] span') || {}).textContent || '').split(' ')[0],
    qty: v('[data-am-f=qty]'), net: v('[data-am-f=net]'), time: v('[data-am-f=time]'), acc: ((q('.nav-am-selb[data-am-sel=account] span') || {}).textContent || ''),
    accPh: !!q('.nav-am-selb[data-am-sel=account].ph'), said: ((q('.nav-ai-said') || {}).textContent || ''),
    low: [...document.querySelectorAll('.nav-am-shot.open .tk-f.ai-low')].map((e) => (e.querySelector('[data-am-f]') || {dataset: {}}).dataset.amF || (e.querySelector('[data-am-sel]') || {dataset: {}}).dataset.amSel || (e.querySelector('[data-am-seg]') || {dataset: {}}).dataset.amSeg || '?'),
    chk: ((q('.nav-ai-chk') || {}).textContent || ''), open: !!q('details.nav-am-more-d[open]') } }"""

def billing_server():
  env = dict(os.environ, SWEEP_BILLING_CONFIG=APPDIR + '/tools/billing-config.local.php', PHP_CLI_SERVER_WORKERS='4')
  pr = subprocess.Popen(['php', '-S', f'127.0.0.1:{P1}', 'router.php'], cwd=APPDIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
  for _ in range(50):
    try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=2); return pr
    except Exception: time.sleep(0.2)
  raise RuntimeError('billing server did not start')

def shot(pg, name):
  if SHOTS: os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, name + '.png'))

srv = billing_server()
try:
  with sync_playwright() as p:
    br = p.chromium.launch()
    for lang, w, phone, scheme, quota in (('fr', 390, True, 'light', True), ('en', 1300, False, 'dark', True), ('es', 390, True, 'dark', False), ('en', 390, True, 'light', False), ('es', 1300, False, 'light', False)):
      tag = f'{w}-{lang}-{scheme}'; x = X[lang]
      try: sql('DELETE FROM attempts')
      except Exception: pass
      ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
      ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
      email = 'aie%06d@t.dev' % random.randint(0, 999999)
      r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000}), headers=H)
      if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
      ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Ari', 'experience': 'gt1'}), headers=H)
      pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
      pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
      pg.evaluate("put('accounts', { id: 'ai-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } })")
      pg.evaluate("put('accounts', { id: 'ai-b', name: 'Apex 2', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-02', rules: { dd_c: 200000, dll_c: 100000 } })")
      pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_timeout(1800)
      act = (lambda s: pg.locator(s).first.tap()) if phone else (lambda s: pg.locator(s).first.click())

      # 1. Today's field → the sheet filled in
      pg.wait_for_selector('#main .nav-ai-today input[data-ai-today]', timeout=10000)
      fld = pg.locator('#main .nav-ai-today input[data-ai-today]')
      box = pg.locator('#main .nav-ai-today').bounding_box()
      after = pg.evaluate("(() => { const f = document.querySelector('#main .nav-ai-today'); return !!(f && f.previousElementSibling && f.previousElementSibling.matches('.nav-rt')) })()")
      ok(fld.get_attribute('placeholder') == x['ph'] and box and box['height'] >= 44 and after, f'{tag} 1 Today: « {fld.get_attribute("placeholder")} », right under the day’s card ({box and round(box["height"])} px)')
      shot(pg, f'ai-entry-{tag}-today')
      act('#main .nav-ai-today input[data-ai-today]'); pg.keyboard.type(x['say']); pg.keyboard.press('Enter')
      pg.wait_for_selector('.nav-am-shot.open .nav-ai-said', timeout=10000); pg.wait_for_timeout(500)
      f = pg.evaluate(FORM)
      ok(f['dir'] == x['dir'] and f['inst'] == x['inst'] and f['qty'] == x['qty'] and f['net'] == x['net'] and f['time'] == x['time'] and x['say'] in f['said'],
         f'{tag} 1 the sentence fills the sheet: {f["dir"]}, {f["inst"]}, {f["qty"]}, {f["net"]}, {f["time"]}')
      # 2. the account asked
      ok(f['accPh'] and f['acc'] == x['ask'] and 'account' in f['low'] and f['chk'] == x['chk'], f'{tag} 2 two accounts, none named: « {f["acc"]} », highlighted « {f["chk"]} » ({f["low"]})')
      ok(pg.evaluate(REAL) == 0, f'{tag} 1 nothing saved before « Save »')
      shot(pg, f'ai-entry-{tag}-sheet')
      pg.evaluate("document.querySelector('.nav-am-shot.open [data-am=save]').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(200)
      act('.nav-am-shot.open [data-am=save]'); pg.wait_for_timeout(500)
      err = pg.evaluate("(document.querySelector('.nav-am-shot.open .nav-am-err') || {}).textContent || ''")
      ok(err == x['need'] and pg.evaluate(REAL) == 0, f'{tag} 2 « Save » without the account: « {err} », nothing saved')
      pg.evaluate("document.querySelector('.nav-am-shot.open [data-am-sel=account]').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(200)
      act('.nav-am-shot.open [data-am-sel=account]'); pg.wait_for_timeout(300)
      act('.nav-am-shot.open [data-am-pickf=account][data-v=ai-b]'); pg.wait_for_timeout(400)
      f = pg.evaluate(FORM)
      ok(not f['accPh'] and 'Apex 2' in f['acc'] and 'account' not in f['low'], f'{tag} 2 « Apex 2 » picked: no longer highlighted')
      pg.evaluate("document.querySelector('.nav-am-shot.open [data-am=save]').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(200)
      act('.nav-am-shot.open [data-am=save]'); pg.wait_for_timeout(2000)
      t = pg.evaluate("S.trades.filter((t) => !t.demo)[0] || null")
      want = round(float(x['net']) * 100)
      ok(t and t['account_id'] == 'ai-b' and t['direction'] == x['dir'] and t['instrument'] == x['inst'] and t['contracts'] == int(x['qty']) and (t['pnl_c'] - (t.get('fees_c') or 0)) == want and t['entry_time'][:5] == x['time'] and not pg.locator('.nav-am-shot.open').count(),
         f'{tag} 2 « Save »: the trade as read ({t and [t["account_id"], t["direction"], t["instrument"], t["contracts"], t["pnl_c"], t["entry_time"]]})')

      # 3. in the « + » sheet: Sweep AI, low confidences highlighted, closed without saving
      pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am-shot.open [data-ai-text]', timeout=8000); pg.wait_for_timeout(400)
      ta = pg.locator('.nav-am-shot.open [data-ai-text]')
      ok(ta.get_attribute('placeholder') == x['ph'] and pg.locator('.nav-am-shot.open .nav-ai-box input[data-am-file]').count() == 1, f'{tag} 3 the « + » sheet: one field for a sentence or a screenshot')
      shot(pg, f'ai-entry-{tag}-plus')
      act('.nav-am-shot.open [data-ai-text]'); pg.keyboard.type(x['ai'])
      act('.nav-am-shot.open .nav-ai-go'); pg.wait_for_selector('.nav-am-shot.open .nav-ai-said', timeout=10000); pg.wait_for_timeout(500)
      f = pg.evaluate(FORM)
      ok(f['dir'] == 'long' and f['inst'] == 'NQ' and f['qty'] == '2' and f['net'] == '400.00' and f['time'] == '09:35', f'{tag} 3 Sweep AI read it: long NQ 2 +400 09:35 ({f})')
      ok('qty' in f['low'] and 'time' in f['low'] and 'net' not in f['low'] and f['open'], f'{tag} 3 the low confidences highlighted (contracts, time), « Check the trade » open ({f["low"]})')
      shot(pg, f'ai-entry-{tag}-low')
      pg.evaluate("document.querySelector('.nav-am-shot.open [data-am=close]').click()"); pg.wait_for_timeout(600)
      ok(pg.evaluate(REAL) == 1, f'{tag} 3 closed without « Save »: nothing added')

      # 4. a screenshot in the same field still works
      pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am-shot.open .nav-ai-box', timeout=8000); pg.wait_for_timeout(300)
      pg.locator('.nav-am-shot.open .nav-ai-box input[data-am-file]').set_input_files(IMG); pg.wait_for_timeout(3500)
      sh = pg.evaluate("({ img: !!document.querySelector('.nav-am-shot.open .nav-am-drop.has img'), net: (document.querySelector('.nav-am-shot.open [data-am-f=net]') || {}).value || '', st: (document.querySelector('.nav-am-shot.open .nav-am-st') || {}).textContent || '' })")
      ok(sh['img'] and sh['net'] not in ('', None), f'{tag} 4 a screenshot: read, the sheet filled in ({sh})')
      pg.evaluate("document.querySelector('.nav-am-shot.open [data-am=close]').click()"); pg.wait_for_timeout(600)
      ok(pg.evaluate(REAL) == 1, f'{tag} 4 nothing saved without « Save »')
      ok(pg.evaluate(WIDE) <= 0, f'{tag} nothing wider than the window')

      # 5. Free, the month's 10 AI entries used: the plans' window
      if quota:
        uid = sql('SELECT id FROM users WHERE email_lc = ?', (email.lower(),))[0][0]
        pg.goto(B1 + '/#dashboard'); pg.wait_for_timeout(2500)   # the first contact with billing on gives the trial: ended now
        sql("UPDATE billing_grants SET ends_at = ? WHERE uid = ?", (int(time.time()) - 60, uid))
        period = pg.evaluate("new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit' }).format(new Date())")
        sql("INSERT OR REPLACE INTO billing_usage (uid, metric, period, count) VALUES (?, 'ai_entry', ?, 10)", (uid, period))
        pg.reload(); pg.wait_for_timeout(3000)
        for _ in range(3):   # a « back on Free » window may open first
          if pg.locator('.sb-layer').count(): pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
        pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am-shot.open [data-ai-text]', timeout=8000); pg.wait_for_timeout(300)
        act('.nav-am-shot.open [data-ai-text]'); pg.keyboard.type(x['ai']); pg.keyboard.press('Enter')
        pg.wait_for_selector('.sb-layer .sb-h', timeout=10000); pg.wait_for_timeout(600)
        h = pg.locator('.sb-layer .sb-h').first.inner_text()
        ok(h == x['quota'], f'{tag} 5 Free, 10 AI entries used: « {h} »')
        shot(pg, f'ai-entry-{tag}-quota')
        pg.locator('.sb-layer .sb-later').first.click(); pg.wait_for_timeout(600)   # « Not now »
        ok(pg.locator('.nav-am-shot.open [data-am-f=net]').count() == 1 and pg.evaluate(REAL) == 1, f'{tag} 5 the sheet stays, to fill by hand; nothing saved')
        ok(pg.evaluate(WIDE) <= 0, f'{tag} 5 nothing wider than the window')
      ok(not errs, f'{tag} no page error ({errs[:2]})')
      ctx.close()
    br.close()
finally:
  try: os.killpg(srv.pid, signal.SIGTERM)
  except ProcessLookupError: pass
  srv.wait()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
