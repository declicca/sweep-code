"""
Sweep — creator program (brief « avance concurrentielle », step 5), Playwright:
  python3 tests/e2e_creator.py http://127.0.0.1:8095 /tmp/show_state.json      (SWEEP_TEST_DB: the dev server's SQLite file)
A second copy of the local server runs next to the first one (port + 1, same database) with billing on
(SWEEP_BILLING_CONFIG=tools/billing-config.local.php) and a stand-in Stripe (SWEEP_STRIPE_MOCK: each call written to a file,
nothing leaves the machine; refused with a live key). Webhooks are signed with the test secret, like e2e_billing.
 A. Admin › Creators (1300, FR): Stripe refuses a code → no status, the reason is shown; then the status is given: the coupon
    (20 % for 3 months) and the promotion code (the creator's code) asked to Stripe;
 B. two visitors arrive with /?ref=CODE (the click is counted, then sign-up), sign up and pay (signed webhooks): 30 % of
    each payment, a refund takes it back, a payment of last month;
 C. the creator sees the Creator section of the Referrals tab with his numbers — clicks, sign-ups, paying subscribers,
    earned this month, to be paid — on a phone 390 (touch) and a computer 1300, light and dark, in EN, FR and ES;
 D. Admin marks last month paid (« to be paid » goes down) and exports the statement (CSV download);
 E. a normal trader sees the Referrals tab unchanged (the gift, the steps, the terms), and cannot reach Admin › Creators.
Checks: no page error, nothing wider than the window.
"""
import hashlib, hmac, json, os, re, signal, sqlite3, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APPDIR = os.path.dirname(os.path.dirname(DB))   # the served copy (its data/ holds the database)
P1 = int(B.rsplit(':', 1)[1]) + 1; B1 = f'http://127.0.0.1:{P1}'
SECRET = 'whsec_local_test_only'   # tools/billing-config.local.php
MOCK = os.path.join(APPDIR, 'data', 'stripe-mock.jsonl')
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
  env = dict(os.environ, SWEEP_BILLING_CONFIG=APPDIR + '/tools/billing-config.local.php', SWEEP_STRIPE_MOCK=MOCK, PHP_CLI_SERVER_WORKERS='4')
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
def sub(uid):
  s = {'id': 'sub_cr_' + uid, 'object': 'subscription', 'customer': 'cus_cr_' + uid, 'status': 'active', 'cancel_at_period_end': False, 'current_period_end': int(time.time()) + 30 * D,
       'metadata': {'uid': uid, 'founding': '0'}, 'items': {'data': [{'price': {'id': 'price_local_pro_m'}, 'current_period_end': int(time.time()) + 30 * D}]}}
  SUBS[s['id']] = s; open(MOCK + '.subs.json', 'w').write(json.dumps(SUBS)); return s
def pay(req, uid, inv, cents, paid_at):
  sub(uid)
  return hook(req, {'id': 'evt_cr_' + inv, 'object': 'event', 'type': 'invoice.paid', 'data': {'object': {'id': inv, 'object': 'invoice', 'customer': 'cus_cr_' + uid, 'subscription': 'sub_cr_' + uid,
    'amount_paid': cents, 'currency': 'usd', 'charge': 'ch_' + inv, 'payment_intent': 'pi_' + inv, 'status_transitions': {'paid_at': int(paid_at)}}}})
def register(ctx, tag, lang='fr'):
  unthrottle()
  email = 'cr%s%d@t.dev' % (tag, int(time.time() * 1000))
  r = ctx.request.post(B1 + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000, 'lang': lang}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:200]))
  ctx.request.post(B1 + '/api/me/profile', data=json.dumps({'first_name': 'Noé', 'experience': 'gt1'}), headers=H)
  ctx.request.put(B1 + '/api/docs/accounts/cra1', data=json.dumps({'id': 'cra1', 'name': 'Topstep 50K', 'starting_balance_c': 5000000, 'status': 'active'}), headers=H)
  return email, uid_of(email)
def context(p, br, lang, phone, dark, state=None):
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme='dark' if dark else 'light',
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], storage_state=state)
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  return ctx
WIDE = "() => document.documentElement.scrollWidth - innerWidth"
TILES = "() => Object.fromEntries([...document.querySelectorAll('#main .rf-cr-t')].map((t) => [t.dataset.cr, [t.querySelector('small').textContent, t.querySelector('b').textContent.replace(/\\s+/g, ' ').trim(), t.querySelector('b').className]]))"
def digits(s): return re.sub(r'[^0-9]', '', s)
X = {
  'fr': {'h': 'Ton programme Creator', 'labels': ['Clics', 'Inscriptions', 'Abonnés payants', 'Gains du mois', 'Gains à verser'], 'lead': '30\u202f%', 'dec': ','},
  'en': {'h': 'Your Creator program', 'labels': ['Clicks', 'Sign-ups', 'Paying subscribers', 'Earned this month', 'To be paid'], 'lead': '30%', 'dec': '.'},
  'es': {'h': 'Tu programa Creator', 'labels': ['Clics', 'Registros', 'Suscriptores de pago', 'Ganado este mes', 'Por pagar'], 'lead': '30\u202f%', 'dec': ','},
}

def admin_page(p, br, lang, phone, dark):
  ctx = context(p, br, lang, phone, dark, STATE); pg = ctx.new_page(); errs = []
  pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B1 + '/#admin'); pg.wait_for_selector('#main .cr-adm form[data-form="cr-make"]', timeout=20000); pg.wait_for_timeout(800)
  return ctx, pg, errs

def creator_view(p, br, state, lang, phone, dark, want):
  tag = f"{'390' if phone else '1300'}-{lang}-{'dark' if dark else 'light'}"; x = X[lang]
  ctx = context(p, br, lang, phone, dark, state); pg = ctx.new_page(); errs = []
  pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B1 + '/#referral'); pg.wait_for_selector('#main .rf-cr .rf-cr-tiles', timeout=20000); pg.wait_for_timeout(700)
  ok(pg.evaluate("document.querySelector('#main .rf-cr h2').textContent") == x['h'], f"{tag}: the Creator section « {x['h']} »")
  ok(x['lead'] in pg.evaluate("document.querySelector('#main .rf-cr p').textContent"), f"{tag}: 30 % of payments, written the language's way")
  t = pg.evaluate(TILES)
  ok([t[k][0] for k in ('clicks', 'signups', 'paying', 'month', 'toPay')] == x['labels'], f'{tag}: the 5 numbers ' + json.dumps({k: v[0] for k, v in t.items()}, ensure_ascii=False))
  ok(t['clicks'][1] == str(want['clicks']) and t['signups'][1] == str(want['signups']) and t['paying'][1] == str(want['paying']), f"{tag}: clicks {t['clicks'][1]}, sign-ups {t['signups'][1]}, paying {t['paying'][1]}")
  ok(digits(t['month'][1]) == digits('%.2f' % (want['month'] / 100)) and digits(t['toPay'][1]) == digits('%.2f' % (want['to_pay'] / 100)) and x['dec'] in t['toPay'][1] and 'pos' in t['toPay'][2] and 'pos' in t['month'][2],
     f"{tag}: this month {t['month'][1]}, to be paid {t['toPay'][1]} (blue)")
  col = pg.evaluate("() => [getComputedStyle(document.querySelector('#main .rf-cr-t[data-cr=toPay] b')).color, getComputedStyle(document.documentElement).getPropertyValue('--pos')]")
  ok('rgb' in col[0], f'{tag}: gains in the blue of gains ({col[0]})')
  link = pg.evaluate("document.querySelector('#main .rf-cr .rf-link span').textContent")
  ok(link == 'makeitsweep.com/?ref=' + want['code'], f'{tag}: the link {link}')
  ok(pg.locator('#main .rf-gift').count() == 0 and pg.locator('#main .rf-steps').count() == 0 and pg.locator('#main .rf-list .rf-item').count() == want['signups'], f'{tag}: no free-month gift or steps, his invitations listed')
  ok(pg.evaluate(WIDE) <= 1 and pg.evaluate("() => [...document.querySelectorAll('#main .rf-cr *')].every((e) => { const r = e.getBoundingClientRect(); return r.right <= innerWidth + 1 && r.left >= -1 })"), f'{tag}: nothing wider than the window')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'creator-{tag}.png'), full_page=True)
  ok(not errs, f'{tag}: no page error ' + '; '.join(errs[:2]))
  ctx.close()

srv = billing_server()
try:
  with sync_playwright() as p:
    br = p.chromium.launch()
    # the creator and a normal trader
    cctx = br.new_context(); cemail, cuid = register(cctx, 'creator')
    cstate = cctx.storage_state()
    nctx = br.new_context(); nemail, nuid = register(nctx, 'normal')
    code = 'CR' + str(int(time.time()))[-6:]

    # A. Admin gives the status (1300, FR light), Stripe refusing first
    actx, apg, aerrs = admin_page(p, br, 'fr', False, False)
    apg.fill('#main form[data-form="cr-make"] [name=user]', nemail); apg.fill('#main form[data-form="cr-make"] [name=code]', 'FAIL' + code[2:])
    apg.click('#main form[data-form="cr-make"] button[type=submit]'); apg.wait_for_selector('#main .cr-adm-err', timeout=10000)
    err = apg.evaluate("document.querySelector('#main .cr-adm-err').textContent")
    ok('Stripe refused' in err and 'not allowed' in err and not sql('SELECT 1 FROM creators WHERE uid = ?', (nuid,)), f'A Stripe refuses → no status, the reason shown: « {err} »')
    apg.fill('#main form[data-form="cr-make"] [name=user]', cemail); apg.fill('#main form[data-form="cr-make"] [name=code]', code.lower())
    apg.click('#main form[data-form="cr-make"] button[type=submit]'); apg.wait_for_selector(f'#main .cr-adm-tbl [data-cr-row="{cuid}"]', timeout=10000)
    co = [c for c in mock_calls('coupons')]; pc = [c for c in mock_calls('promotion_codes') if c['p'].get('code') == code]
    ok(sql('SELECT code, rate_bp, months FROM creators WHERE uid = ?', (cuid,)) == [(code, 3000, 12)], f'A the status is given: code {code}, 30 %, 12 months')
    ok(len(co) >= 1 and str(co[-1]['p'].get('percent_off')) == '20' and co[-1]['p'].get('duration') == 'repeating' and str(co[-1]['p'].get('duration_in_months')) == '3', 'A Stripe coupon asked: 20 % for 3 months ' + json.dumps(co[-1]['p'] if co else None))
    ok(len(pc) == 1 and pc[0]['p'].get('restrictions', {}).get('first_time_transaction') == 'true', 'A Stripe promotion code asked with the creator\'s code, first payment only')
    ok(not aerrs and apg.evaluate(WIDE) <= 1, 'A admin 1300: no page error, nothing wider than the window ' + '; '.join(aerrs[:2]))
    actx.close()

    # B. visitors with /?ref=CODE: the click, the sign-up, the payments
    sql('DELETE FROM referrals WHERE created_at > ?', (int(time.time()) - D,))   # earlier runs today (3 a day per connection)
    vis = []
    for i in range(2):
      v = br.new_context(); r = v.request.get(B1 + '/?ref=' + code + '&utm_source=ig', max_redirects=0)
      ok(r.status == 302 and r.headers.get('location', '').startswith('/?signup=1') and 'utm_source=ig' in r.headers.get('location', '') and 'ref=' not in r.headers.get('location', ''), f'B visitor {i + 1}: /?ref=CODE → sign-up, the other parameters kept ({r.headers.get("location")})')
      e, u = register(v, 'fan%d' % i); vis.append((v, u))
    ok([r[0] for r in sql('SELECT referrer_id FROM referrals WHERE referee_id IN (?, ?)', (vis[0][1], vis[1][1]))] == [cuid, cuid], 'B both visitors are linked to the creator')
    req = cctx.request; now = time.time()
    last = time.localtime(now - 35 * D); last_month = time.strftime('%Y-%m', last)
    c1 = pay(req, vis[0][1], 'in_cr1_%d' % int(now), 1900, now - 35 * D)
    c2 = pay(req, vis[0][1], 'in_cr2_%d' % int(now), 1900, now)
    inv3 = 'in_cr3_%d' % int(now); c3 = pay(req, vis[1][1], inv3, 3900, now)
    ok(all(c[0] == 200 for c in (c1, c2, c3)) and 'commission 570' in c1[1].get('result', '') and 'commission 1170' in c3[1].get('result', ''), 'B payments: 30 % of 19.00 and of 39.00 ' + json.dumps([c1[1], c3[1]]))
    c4 = hook(req, {'id': 'evt_cr_rf_' + inv3, 'object': 'event', 'type': 'charge.refunded', 'data': {'object': {'id': 'ch_' + inv3, 'object': 'charge', 'invoice': inv3, 'amount': 3900, 'amount_refunded': 3900}}})
    ok(c4[0] == 200 and c4[1].get('result') == 'refund: reversed -1170', 'B a refund takes its commission back ' + json.dumps(c4[1]))
    clicks = sql('SELECT COUNT(*) FROM referral_clicks WHERE referrer_id = ?', (cuid,))[0][0]
    want = {'clicks': clicks, 'signups': 2, 'paying': 2, 'month': 570, 'to_pay': 1140, 'code': code}
    ok(clicks == 2, f'B 2 clicks counted ({clicks})')

    # C. the creator's Referrals tab: phone and computer, light and dark, EN / FR / ES
    for lang, phone, dark in (('fr', True, True), ('es', True, False), ('en', False, False), ('fr', False, True), ('en', True, False), ('es', False, True)):
      creator_view(p, br, cstate, lang, phone, dark, want)

    # D. Admin marks last month paid, exports the statement (390 EN dark, then the download)
    actx, apg, aerrs = admin_page(p, br, 'en', True, True)
    btn = apg.locator(f'#main [data-cr-month-row="{cuid}:{last_month}"] [data-act="cr-paid"]')
    ok(btn.count() == 1 and apg.locator(f'#main [data-cr-month-row="{cuid}:{time.strftime("%Y-%m")}"] [data-act="cr-paid"]').count() == 0, 'D last month can be marked paid, not the month in progress')
    btn.click(); apg.wait_for_selector('aside.nav-ask.open [data-ask="1"]', timeout=5000)
    ok('5.70' in apg.evaluate("document.querySelector('aside.nav-ask.open').textContent"), 'D the app\'s own window asks, with the amount')
    apg.click('aside.nav-ask.open [data-ask="1"]'); apg.wait_for_selector(f'#main [data-cr-month-row="{cuid}:{last_month}"]:not(:has([data-act="cr-paid"]))', timeout=10000)
    ok(sql('SELECT amount_c FROM creator_payouts WHERE creator_id = ? AND month = ?', (cuid, last_month)) == [(570,)], 'D last month marked paid: 5.70')
    row = apg.evaluate(f"[...document.querySelectorAll('#main [data-cr-row=\"{cuid}\"] td')].map((t) => t.textContent)")
    ok(digits(row[-1]) == '570' and row[1] == '2' and row[2] == '2' and row[3] == '2', 'D Admin: clicks, sign-ups, paying, to be paid now 5.70 ' + json.dumps(row))
    ok(apg.evaluate(WIDE) <= 1, 'D admin 390: nothing wider than the window')
    apg.select_option('#main [data-cr-month]', last_month); apg.wait_for_timeout(300)
    with apg.expect_download() as dl:
      apg.click('#main [data-cr-export]')
    csv = open(dl.value.path(), encoding='utf-8').read()
    lines = [l for l in csv.splitlines() if code in l]
    ok(dl.value.suggested_filename == f'sweep-creators-{last_month}.csv' and any(',payment,' in l and ',19.00,5.70,' in l for l in lines) and any(',total,' in l and 'paid ' in l for l in lines), 'D the statement exported (CSV): the payment, the total, paid ' + json.dumps(lines[:3]))
    ok(not aerrs, 'D admin 390: no page error ' + '; '.join(aerrs[:2]))
    if SHOTS: apg.screenshot(path=os.path.join(SHOTS, 'creator-admin-390-en-dark.png'), full_page=True)
    actx.close()
    want['to_pay'] = 570
    creator_view(p, br, cstate, 'fr', True, False, want)

    # E. a normal trader: the Referrals tab unchanged, no Admin › Creators
    nstate = nctx.storage_state()
    for lang, phone in (('fr', True), ('en', False)):
      ctx = context(p, br, lang, phone, False, nstate); pg = ctx.new_page(); errs = []
      pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
      pg.goto(B1 + '/#referral'); pg.wait_for_selector('#main .rf-hero', timeout=20000); pg.wait_for_timeout(600)
      ok(pg.locator('#main .rf-cr').count() == 0 and pg.locator('#main .rf-gift').count() == 1 and pg.locator('#main .rf-steps li').count() == 3 and pg.locator('#main [data-act="ref-terms"]').count() == 1 and pg.locator('#main .rf-candles').count() == 1,
         f'E {lang} {"390" if phone else "1300"}: the Referrals tab as before (gift, 3 steps, the months, the terms), no Creator section')
      ok(pg.evaluate(WIDE) <= 1 and not errs, f'E {lang}: nothing wider, no page error ' + '; '.join(errs[:2]))
      ctx.close()
    r = nctx.request.get(B1 + '/api/admin/creators', headers=H)
    ok(r.status == 403, f'E a trader cannot reach Admin › Creators ({r.status})')
    r = nctx.request.get(B1 + '/api/referral', headers=H).json()
    ok(r.get('creator') is None and r.get('link', '').endswith('/r/' + r.get('code', '?')), 'E his referral link is the usual /r/CODE')
    br.close()
finally:
  stop(srv)
print(('FAIL ' if fails else 'ok   ') + f'{fails} failed')
sys.exit(1 if fails else 0)
