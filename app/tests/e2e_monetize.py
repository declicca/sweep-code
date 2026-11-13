"""
Sweep — monetization at 100 traders (brief of 5 Nov., steps 3 and 4) in the app, Playwright:
  python3 tests/e2e_monetize.py http://127.0.0.1:8095      (SWEEP_TEST_DB: the dev server's SQLite file)
A second copy of the local server runs next to the first one (port + 1, same database) with billing on (tools/billing-config.local.php
plus the founding offer: coupon, deadline, every trader) and a stand-in Stripe (SWEEP_STRIPE_MOCK: each call written to a file,
nothing leaves the machine; refused with a live key). Webhooks are signed with the test secret, like e2e_billing.
 A. the plans page of a trader on trial: « Founding offer … spots left: N of 100 » (N = 100 − founders) with the countdown, the
    founding price on Pro; on a phone 390 (touch) and a computer 1300, light and dark, in EN, FR and ES;
 B. a paying trader: « Manage billing » opens « Taking a break from trading? » first — « Pause for 1 month » and « Card, plan or
    cancellation » — (EN, FR, ES; the window fits the screen, ✕ by tapping outside); « Pause » asks Stripe (pause_collection, 30
    days): Free, « On pause until … », « Resume now », no buy button, the banner on the dashboard; « Resume now » asks Stripe to
    clear it: Pro again, and no pause offered for 6 months (« Manage billing » goes straight to Stripe).
Checks: no page error, nothing wider than the window, the buttons inside the window.
"""
import hashlib, hmac, json, os, re, signal, sqlite3, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APPDIR = os.path.dirname(os.path.dirname(DB))   # the served copy (its data/ holds the database)
P1 = int(B.rsplit(':', 1)[1]) + 1; B1 = f'http://127.0.0.1:{P1}'
SECRET = 'whsec_local_test_only'   # tools/billing-config.local.php
MOCK = os.path.join(APPDIR, 'data', 'stripe-mock-monetize.jsonl')
CFG = os.path.join(APPDIR, 'data', 'billing-config.monetize.php')
SHOTS = os.environ.get('SWEEP_SHOTS', '')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
D = 86400
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

def billing_server():
  for f in (MOCK, MOCK + '.subs.json'):
    if os.path.exists(f): os.remove(f)
  # the local test settings plus the founding offer (a made-up coupon: the stand-in Stripe never checks it)
  open(CFG, 'w').write("<?php return array_merge(require %r, ['founding_for' => 'everyone', 'founding_cap' => 100, 'founding_percent_off' => 50,\n"
                       "  'founding_deadline' => gmdate('c', time() + 20 * 86400), 'stripe_founding_coupon' => 'FOUNDING50_LOCAL', 'display_prices' => ['pro' => ['month' => 19, 'year' => 159], 'elite' => ['month' => 39, 'year' => 329]]]);\n"
                       % (APPDIR + '/tools/billing-config.local.php'))
  env = dict(os.environ, SWEEP_BILLING_CONFIG=CFG, SWEEP_STRIPE_MOCK=MOCK, PHP_CLI_SERVER_WORKERS='4')
  p = subprocess.Popen(['php', '-S', f'127.0.0.1:{P1}', 'router.php'], cwd=APPDIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
  for _ in range(50):
    try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=2); return p
    except Exception: time.sleep(0.2)
  raise RuntimeError('billing server did not start')
def stop(p):
  try: os.killpg(p.pid, signal.SIGTERM)
  except ProcessLookupError: pass
  p.wait()
def sql(q, args=()):
  d = sqlite3.connect(DB, timeout=10); c = d.execute(q, args); r = c.fetchall(); d.commit(); d.close(); return r
def unthrottle():
  try: sql('DELETE FROM attempts')
  except Exception: pass
def uid_of(email): return sql('SELECT id FROM users WHERE email_lc = ?', (email.lower(),))[0][0]
def mock_calls(path): return [c for c in (json.loads(l) for l in open(MOCK).read().splitlines()) if c['path'] == path] if os.path.exists(MOCK) else []
def hook(req, ev):
  body = json.dumps(ev); t = int(time.time())
  sig = 't=%d,v1=%s' % (t, hmac.new(SECRET.encode(), ('%d.%s' % (t, body)).encode(), hashlib.sha256).hexdigest())
  r = req.post(B1 + '/api/billing/webhook', data=body, headers={'Content-Type': 'application/json', 'Stripe-Signature': sig})
  return r.status, (r.json() if r.status < 500 else {})
SUBS = {}
def subscribe(req, uid):
  s = {'id': 'sub_mz_' + uid, 'object': 'subscription', 'customer': 'cus_mz_' + uid, 'status': 'active', 'cancel_at_period_end': False, 'current_period_end': int(time.time()) + 30 * D,
       'metadata': {'uid': uid, 'founding': '0'}, 'items': {'data': [{'price': {'id': 'price_local_pro_m'}, 'current_period_end': int(time.time()) + 30 * D}]}, 'pause_collection': None}
  SUBS[s['id']] = s; open(MOCK + '.subs.json', 'w').write(json.dumps(SUBS))
  sql("UPDATE billing_grants SET ends_at = ? WHERE uid = ?", (int(time.time()) - 60, uid))   # the trial is over: he pays
  return hook(req, {'id': 'evt_mz_' + uid, 'object': 'event', 'type': 'customer.subscription.created', 'data': {'object': s}})
def register(ctx, tag, lang='fr'):
  unthrottle()
  email = 'mz%s%d@t.dev' % (tag, int(time.time() * 1000))
  r = ctx.request.post(B1 + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000, 'lang': lang}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:200]))
  ctx.request.post(B1 + '/api/me/profile', data=json.dumps({'first_name': 'Noé', 'experience': 'gt1'}), headers=H)
  ctx.request.put(B1 + '/api/docs/accounts/mza1', data=json.dumps({'id': 'mza1', 'name': 'Topstep 50K', 'starting_balance_c': 5000000, 'status': 'active'}), headers=H)
  ctx.request.get(B1 + '/api/billing/me')   # the trial is given at the first contact
  return email, uid_of(email)
def context(br, lang, phone, dark, state=None):
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme='dark' if dark else 'light',
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], storage_state=state)
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  return ctx
WIDE = "() => document.documentElement.scrollWidth - innerWidth"
# every visible button of the window (or of the page's plan card) inside the screen, none over another
FIT = """(sel) => { const bs = [...document.querySelectorAll(sel)].filter((b) => b.offsetParent); const r = bs.map((b) => b.getBoundingClientRect());
  const out = r.filter((x) => x.left < 0 || x.right > innerWidth + 0.5 || x.width < 40 || x.height < 30).length;
  let over = 0; for (let i = 0; i < r.length; i++) for (let j = i + 1; j < r.length; j++) if (r[i].left < r[j].right - 1 && r[j].left < r[i].right - 1 && r[i].top < r[j].bottom - 1 && r[j].top < r[i].bottom - 1) over++;
  return { n: bs.length, out, over } }"""
X = {
  'fr': {'found': 'Offre fondateur : 50 % de rabais à vie · places restantes : {n} sur 100. Se termine dans', 'pz_t': 'Tu fais une pause de trading ?', 'pz_s': 'Garde tout, sans payer ce mois-ci.',
         'go': 'Mettre en pause 1 mois', 'manage': 'Carte, forfait ou annulation', 'status': 'En pause jusqu’au', 'resume': 'Reprendre maintenant', 'banner': 'Pro est en pause jusqu’au'},
  'en': {'found': 'Founding offer: 50% off for life · spots left: {n} of 100. Ends in', 'pz_t': 'Taking a break from trading?', 'pz_s': 'Keep everything, without paying this month.',
         'go': 'Pause for 1 month', 'manage': 'Card, plan or cancellation', 'status': 'On pause until', 'resume': 'Resume now', 'banner': 'Pro is on pause until'},
  'es': {'found': 'Oferta fundador: 50 % de descuento de por vida · plazas restantes: {n} de 100. Termina en', 'pz_t': '¿Te tomas un descanso del trading?', 'pz_s': 'Conserva todo, sin pagar este mes.',
         'go': 'Pausar 1 mes', 'manage': 'Tarjeta, plan o cancelación', 'status': 'En pausa hasta el', 'resume': 'Reanudar ahora', 'banner': 'Pro está en pausa hasta el'},
}
def norm(s): return [norm(x) for x in s] if isinstance(s, list) else s if isinstance(s, int) else re.sub('[\u00a0\u202f]', ' ', s or '')
def plans(pg):
  pg.evaluate("location.hash = '#plan'"); pg.wait_for_selector('#main .sb-plans', timeout=15000); pg.wait_for_timeout(500)
def shot(pg, name):
  if SHOTS: os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, name + '.png'))

srv = billing_server()
try:
  with sync_playwright() as p:
    br = p.chromium.launch()
    # A. the founding offer on the plans page of a trader on trial
    tctx = br.new_context(); temail, tuid = register(tctx, 'trial'); tstate = tctx.storage_state(); tctx.close()
    founders = sql("SELECT COUNT(DISTINCT uid) FROM billing_subs WHERE founding = 1 AND status NOT IN ('incomplete', 'incomplete_expired')")[0][0]
    for lang, phone, dark in [('fr', True, False), ('fr', False, True), ('en', False, False), ('en', True, True), ('es', True, False), ('es', False, True)]:
      tag = f"A {lang} {'390' if phone else '1300'} {'dark' if dark else 'light'}"
      ctx = context(br, lang, phone, dark, tstate); pg = ctx.new_page(); errs = []
      pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
      pg.goto(B1 + '/'); pg.wait_for_selector('#main', timeout=20000); plans(pg)
      f = norm(pg.evaluate("(document.querySelector('#main .sb-founding') || {}).textContent || ''"))
      ok(f.startswith(norm(X[lang]['found'].format(n=100 - founders))), f'{tag}: « {f} »')
      price = norm(pg.evaluate("[...document.querySelectorAll('#main .sb-plans s')].map((s) => s.parentElement.textContent).join(' | ')"))
      ok('19' in price or '13,25' in price or '13.25' in price, f'{tag}: the full price struck out next to the founding price ({price[:80]})')
      ok(pg.evaluate(WIDE) <= 0, f'{tag}: nothing wider than the window')
      shot(pg, f"monetize-founding-{lang}-{'390' if phone else '1300'}-{'dark' if dark else 'light'}")
      ok(not errs, f'{tag}: no page error ' + '; '.join(errs[:2]))
      ctx.close()

    # B. « Pause 1 month » before « Cancel », for a trader who pays
    pctx = br.new_context(); pemail, puid = register(pctx, 'pause')
    st, r = subscribe(pctx.request, puid)
    ok(st == 200 and 'synced active' in r.get('result', ''), f'B the subscription arrives by its webhook ({st} {r})')
    pstate = pctx.storage_state(); pctx.close()
    # the window, in each language (closed by tapping outside)
    for lang, phone, dark in [('es', True, False), ('en', False, True)]:
      tag = f"B {lang} {'390' if phone else '1300'} {'dark' if dark else 'light'}"
      ctx = context(br, lang, phone, dark, pstate); pg = ctx.new_page(); errs = []
      pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
      pg.goto(B1 + '/'); pg.wait_for_selector('#main', timeout=20000); plans(pg)
      pg.click('#main .sb-manage'); pg.wait_for_selector('.sb-pz.open', timeout=5000); pg.wait_for_timeout(400)
      t = pg.evaluate("[document.querySelector('.sb-pz h2').textContent, document.querySelector('.sb-pz p').textContent, ...[...document.querySelectorAll('.sb-pz [data-pz]')].map((b) => b.textContent)]")
      ok(t[0] == X[lang]['pz_t'] and t[1].startswith(X[lang]['pz_s']) and t[2:] == [X[lang]['go'], X[lang]['manage']], f'{tag}: « {t[0]} » — {t[2:]}')
      fit = pg.evaluate(FIT, '.sb-pz [data-pz]')
      ok(fit['n'] == 2 and fit['out'] == 0 and fit['over'] == 0, f'{tag}: both buttons inside the window, none over the other {fit}')
      shot(pg, f"monetize-pause-ask-{lang}-{'390' if phone else '1300'}-{'dark' if dark else 'light'}")
      pg.mouse.click(5, 5); pg.wait_for_timeout(500)
      ok(pg.locator('.sb-pz').count() == 0 and not mock_calls('subscriptions/sub_mz_' + puid), f'{tag}: tapping outside closes it, nothing asked to Stripe')
      ok(not errs, f'{tag}: no page error ' + '; '.join(errs[:2]))
      ctx.close()
    # the pause itself (FR, phone, dark), then the banner on the dashboard and « Resume now » (FR, computer, light)
    ctx = context(br, 'fr', True, True, pstate); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B1 + '/'); pg.wait_for_selector('#main', timeout=20000); plans(pg)
    pg.click('#main .sb-manage'); pg.wait_for_selector('.sb-pz.open', timeout=5000); pg.wait_for_timeout(300)
    pg.click('.sb-pz [data-pz="go"]'); pg.wait_for_function("() => !document.querySelector('.sb-pz') && document.querySelector('#main .sb-resume')", timeout=10000); pg.wait_for_timeout(400)
    c = (mock_calls('subscriptions/sub_mz_' + puid) or [{}])[-1].get('p', {})
    pc = c.get('pause_collection') or {}
    ok(pc.get('behavior') == 'void' and abs(int(pc.get('resumes_at', 0)) - (time.time() + 30 * D)) < 120, f'B Stripe asked to hold the payments 30 days ({pc})')
    s = norm(pg.evaluate("[document.querySelector('#main .sb-big').textContent, document.querySelector('#main .sb-status').textContent, document.querySelector('#main .sb-resume').textContent, document.querySelectorAll('#main [data-buy]').length, (document.querySelector('#main .sb-founding') || {}).textContent || '']"))
    ok(s[0] == 'Free' and s[1].startswith(X['fr']['status']) and s[2] == X['fr']['resume'] and s[3] == 0 and s[4] == '', f'B paused: {s[:4]} — no buy button, no founding offer')
    fit = pg.evaluate(FIT, '#main .sb-card button')
    ok(fit['out'] == 0 and fit['over'] == 0 and pg.evaluate(WIDE) <= 0, f'B 390 dark: « Resume now » inside the card, nothing wider than the window {fit}')
    shot(pg, 'monetize-paused-fr-390-dark')
    ok(not errs, 'B 390 dark: no page error ' + '; '.join(errs[:2]))
    ctx.close()
    ok(sql('SELECT paused_until FROM billing_subs WHERE id = ?', ('sub_mz_' + puid,))[0][0] > time.time() + 29 * D, 'B the database knows until when')
    ctx = context(br, 'fr', False, False, pstate); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B1 + '/#dashboard'); pg.wait_for_selector('#main', timeout=20000); pg.wait_for_timeout(1500)
    bn = norm(pg.evaluate("[...document.querySelectorAll('.sb-banner')].map((b) => b.textContent).join(' | ')"))
    ok(X['fr']['banner'] in bn and X['fr']['resume'] in bn and pg.locator('.sb-fw').count() == 0, f'B the banner says it, no « back on Free » window: « {bn} »')
    plans(pg)
    pg.click('#main .sb-resume'); pg.wait_for_function("() => document.querySelector('#main .sb-manage') && !document.querySelector('#main .sb-resume')", timeout=10000); pg.wait_for_timeout(400)
    c = (mock_calls('subscriptions/sub_mz_' + puid) or [{}])[-1].get('p', {})
    ok(c.get('pause_collection', 'x') == '' and norm(pg.evaluate("document.querySelector('#main .sb-big').textContent")) == 'Pro', f'B « Resume now »: Stripe asked to clear the pause, Pro again ({c})')
    pg.route('**/api/billing/portal', lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps({'url': B1 + '/#plan'})))
    pg.click('#main .sb-manage'); pg.wait_for_timeout(800)
    ok(pg.locator('.sb-pz').count() == 0, 'B one pause per 6 months: « Manage billing » goes straight to Stripe')
    shot(pg, 'monetize-resumed-fr-1300-light')
    ok(not errs, 'B 1300 light: no page error ' + '; '.join(errs[:2]))
    ctx.close()
    # C. (13 Nov.) the plan's limits hold on the batch route too (before: trades only — a batch created the accounts and the
    #    payouts that Free refuses one at a time). Free: 2 accounts, no payouts
    fctx = br.new_context(); femail, fuid = register(fctx, 'free')
    sql("UPDATE billing_grants SET ends_at = ? WHERE uid = ?", (int(time.time()) - 60, fuid))   # the trial is over: Free
    acc = lambda i: {'id': 'mzb%d' % i, 'name': 'Apex %d' % i, 'starting_balance_c': 5000000, 'status': 'active'}
    one = fctx.request.put(B1 + '/api/docs/accounts/mzb9', data=json.dumps(acc(9)), headers=H)   # his 2nd account: allowed
    third = fctx.request.put(B1 + '/api/docs/accounts/mzb8', data=json.dumps(acc(8)), headers=H)
    ok(one.status < 300 and third.status == 402, f'C Free, one at a time: the 2nd account is saved, the 3rd refused ({one.status}, {third.status})')
    b = fctx.request.post(B1 + '/api/docs/batch', data=json.dumps({'col': 'accounts', 'put': [acc(1), acc(2)]}), headers=H)
    n = sql("SELECT COUNT(*) FROM documents WHERE user_id = ? AND collection = 'accounts'", (fuid,))[0][0]
    ok(b.status == 402 and n == 2, f'C Free, a batch of 2 more accounts: refused, still 2 accounts ({b.status}, {n})')
    b = fctx.request.post(B1 + '/api/docs/batch', data=json.dumps({'col': 'accounts', 'put': [dict(acc(9), name='Apex renamed')]}), headers=H)
    ok(b.status < 300, f'C Free, a batch that changes an account he has: saved ({b.status})')
    b = fctx.request.post(B1 + '/api/docs/batch', data=json.dumps({'col': 'payouts', 'put': [{'id': 'mzp1', 'account_id': 'mza1', 'amount_c': 100000, 'date': '2026-11-10'}]}), headers=H)
    n = sql("SELECT COUNT(*) FROM documents WHERE user_id = ? AND collection = 'payouts'", (fuid,))[0][0]
    ok(b.status == 402 and n == 0, f'C Free, a payout in a batch: refused like the single write ({b.status}, {n})')
    b = fctx.request.post(B1 + '/api/docs/batch', data=json.dumps({'col': 'trades', 'put': [{'id': 'mzt1', 'account_id': 'mza1', 'date': '2026-11-10', 'instrument': 'NQ', 'direction': 'long', 'contracts': 1, 'pnl_c': 1000}]}), headers=H)
    ok(b.status < 300, f'C Free, a batch of trades on an active account: saved ({b.status})')
    fctx.close()
    br.close()
finally:
  stop(srv)
  for f in (CFG, MOCK, MOCK + '.subs.json'):
    if os.path.exists(f): os.remove(f)
print('\n' + ('all passed' if not fails else f'{fails} failed'))
sys.exit(1 if fails else 0)
