"""
Sweep — plans and billing in the app, with billing switched on (brief 02 part 13), Playwright:
  python3 tests/e2e_billing.py http://127.0.0.1:8095 /tmp/show_state.json      (SWEEP_TEST_DB: the dev server's SQLite file)
A second copy of the local server runs next to the first one (port + 1, same database) with billing on
(SWEEP_BILLING_CONFIG=tools/billing-config.local.php: test values, no Stripe key, Stripe is never called). The trial's clock
is moved in the database (the end of the trader's trial), never in the server.
 A. day 50 (FR on a phone, EN on a computer): no « Strong week, go Pro » during the trial (audit of 16 Oct.; again on Free,
    day 61); the dashboard card lists the paid features the trader really uses — 4
    accounts (Free keeps 2), My money, screenshot reading, the full history, Sweep AI — drawn with the dashboard; ✕ hides it;
 B. day 61, back to Free: ONE window opens by itself — what stays, what is paused and kept (the accounts not chosen, My
    money…), the 2 accounts that stay active (picked, saved), how to get it back; not again on the next visit; the banner
    opens it again; a paused account still opens the plan sheet;
 C. a subscription through Stripe's webhook (the real public route, signed with the test secret): a wrong signature is
    refused (400), a replay is ignored; created → Pro, every account open; deleted → Free, the window says « subscription »;
    the same window in Spanish on a phone;
 D. Admin: a referral from the referrer's own connection waits for review; approved → the friend gets 14 days of Elite;
    feedback: a message reaches Admin, an unknown status is refused (400), « planned » is saved and the trader sees it.
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import hashlib, hmac, json, os, signal, sqlite3, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
APPDIR = '/tmp/g'   # the served copy (each shard has its own)
P1 = int(B.rsplit(':', 1)[1]) + 1; B1 = f'http://127.0.0.1:{P1}'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SECRET = 'whsec_local_test_only'   # tools/billing-config.local.php
SHOTS = os.environ.get('SWEEP_SHOTS', '')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
D = 86400
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

def billing_server():
  env = dict(os.environ, SWEEP_BILLING_CONFIG=APPDIR + '/tools/billing-config.local.php', PHP_CLI_SERVER_WORKERS='4')
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
def trial_ends(uid, ts): sql("UPDATE billing_grants SET ends_at = ? WHERE uid = ? AND reason = 'trial'", (int(ts), uid))
def hook(req, ev, secret=SECRET):
  body = json.dumps(ev); t = int(time.time())
  sig = 't=%d,v1=%s' % (t, hmac.new(secret.encode(), ('%d.%s' % (t, body)).encode(), hashlib.sha256).hexdigest())
  r = req.post(B1 + '/api/billing/webhook', data=body, headers={'Content-Type': 'application/json', 'Stripe-Signature': sig})
  return r.status, (r.json() if r.status < 500 else {})
def sub(sid, uid, status, end): return {'id': sid, 'object': 'subscription', 'customer': 'cus_e2e_' + uid, 'status': status, 'cancel_at_period_end': False,
  'current_period_end': end, 'metadata': {'uid': uid, 'founding': '0'}, 'items': {'data': [{'price': {'id': 'price_local_pro_m'}, 'current_period_end': end}]}}

X = {
  'fr': {'card': 'Ton essai Pro se termine dans 10 jours', 'uses': 'Ce que tu utilises de Pro :', 'acc': '4 comptes (Free en garde 2 actifs)', 'money': 'Mon argent (2 payouts, 1 dépense)',
         'shots': 'La lecture des captures (3 trades)', 'hist': 'Ton historique complet (5 trades de plus de 30 jours)', 'ai': 'Sweep AI au-delà de la limite de Free',
         'fw': 'Ton essai Pro est terminé', 'fwsub': 'Ton abonnement Pro est terminé', 'stays': ['Ton journal, tous tes trades et ton coach', '2 comptes actifs', 'Tes stats des 30 derniers jours', 'Sweep AI : 3 messages par jour'],
         'zmoney': 'Mon argent (2 payouts, 1 dépense) : gardé, il revient avec Pro', 'zhist': '5 trades de plus de 30 jours : gardés, hors de tes stats', 'choose': 'Choisis les 2 comptes qui restent actifs',
         'go': 'Revenir à Pro', 'stay': 'Rester sur Free', 'banner': 'Ton essai Pro est terminé. Tes données sont en sécurité.', 'back': 'Retrouver Pro', 'paused': 'Ce compte est en pause'},
  'en': {'card': 'Your Pro trial ends in 10 days', 'uses': 'What you use of Pro:', 'acc': '4 accounts (Free keeps 2 active)', 'money': 'My money (2 payouts, 1 expense)',
         'shots': 'Screenshot reading (3 trades)', 'hist': 'Your full history (5 trades older than 30 days)', 'ai': 'Sweep AI beyond the Free limit',
         'fw': 'Your Pro trial has ended', 'fwsub': 'Your Pro subscription has ended', 'stays': ['Your journal, all your trades and your coach', '2 active accounts', 'Your stats for the last 30 days', 'Sweep AI: 3 messages a day'],
         'zmoney': 'My money (2 payouts, 1 expense): kept, back with Pro', 'zhist': '5 trades older than 30 days: kept, outside your stats', 'choose': 'Choose the 2 accounts that stay active',
         'go': 'Go back to Pro', 'stay': 'Stay on Free', 'banner': 'Your Pro trial ended. Your data is safe.', 'back': 'Get Pro back', 'paused': 'This account is paused'},
  'es': {'fw': 'Tu prueba Pro terminó', 'stays': ['Tu diario, todas tus operaciones y tu coach', '2 cuentas activas', 'Tus stats de los últimos 30 días', 'Sweep AI: 3 mensajes al día'],
         'zmoney': 'Mi dinero (2 payouts, 1 gasto): guardado, vuelve con Pro', 'choose': 'Elige las 2 cuentas que siguen activas', 'go': 'Volver a Pro', 'stay': 'Quedarme en Free'},
}
EN_ONLY = ['What stays', 'Paused, kept', 'Get everything back', 'Stay on Free', 'Go back to', 'has ended', 'active accounts']
SEED = """async (old) => {
  put('firms', { id: 'bf', name: 'Topstep' });
  // one by one, a second apart: the server orders accounts by when it saved them (« the 2 oldest stay active »)
  for (const [i, [id, name]] of [['ba1', 'Topstep 50K'], ['ba2', 'Apex 100K'], ['ba3', 'Tradeify 50K'], ['ba4', 'Lucid 25K']].entries()) {
    put('accounts', { id, firm_id: 'bf', name, starting_balance_c: 5000000, status: 'active', created_on: '2026-09-0' + (i + 1) });
    await new Promise((r) => setTimeout(r, 1100));
  }
  put('payouts', { id: 'bp1', account_id: 'ba1', firm_id: 'bf', amount_c: 150000, net_c: 150000, status: 'paid', request_date: old, payment_date: old });
  put('payouts', { id: 'bp2', account_id: 'ba2', firm_id: 'bf', amount_c: 90000, net_c: 90000, status: 'paid', request_date: old, payment_date: old });
  put('expenses', { id: 'be1', account_id: 'ba3', firm_id: 'bf', category: 'evaluation', amount_c: 15000, date: old });
  for (let i = 1; i <= 5; i++) put('trades', { id: 'bo' + i, account_id: 'ba1', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 10000, pnl_manual: true, date: old, entry_time: '09:4' + i, exit_time: '09:5' + i });
  for (let i = 1; i <= 3; i++) put('trades', { id: 'bs' + i, account_id: 'ba2', instrument: 'NQ', direction: 'short', contracts: 1, entry: 2, exit: 1, pnl_c: 5000, pnl_manual: true, date: todayStr(), entry_time: '10:1' + i, exit_time: '10:2' + i, source: 'screenshot' });
  render(); }"""
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"

def trader(p, lang, phone, tag):
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  email = 'bill%s%d@t.dev' % (tag, int(time.time() * 1000))
  r = ctx.request.post(B1 + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B1 + '/api/me/profile', data=json.dumps({'first_name': 'Noé', 'experience': 'gt1'}), headers=H)
  uid = uid_of(email)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B1 + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  old = time.strftime('%Y-%m-%d', time.localtime(time.time() - 45 * D))
  pg.evaluate(SEED, old); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(2500)   # the puts reach the server
  sql("INSERT OR REPLACE INTO billing_usage (uid, metric, period, count) VALUES (?, 'ai_daily', ?, 5)", (uid, old))
  return br, ctx, pg, errs, uid

def me(ctx): return ctx.request.get(B1 + '/api/billing/me', headers=H).json()
def shot(pg, name):
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, name + '.png'), full_page=False)
def reload(pg, hash_='#dashboard'):   # a real new load (a hash change alone keeps the page and its plan state)
  pg.goto(B1 + '/' + hash_); pg.reload(); pg.wait_for_selector('#main .nav-dash' if hash_ == '#dashboard' else '#main', timeout=15000); pg.wait_for_timeout(1800)

def day50(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  br, ctx, pg, errs, uid = trader(p, lang, phone, tag.replace('-', ''))
  me(ctx); trial_ends(uid, time.time() + 9.5 * D)
  reload(pg)
  # (audit of 16 Oct.) « Strong week, go Pro » never to a trader in his Pro trial
  gw = pg.evaluate("() => { localStorage.removeItem('sb_nudge'); return !!SweepBilling.nudge('green_week') || !!document.querySelector('.sb-nudge') }")
  ok(gw is False, f'{tag} during the trial: no « Strong week, go Pro » banner ({gw})')
  card = pg.locator('#main .nav-dash .nav-trial')
  ok(card.count() == 1, f'{tag} day 50: the card is on the dashboard, drawn with it')
  ok(pg.evaluate(TXT, '#main .nav-trial .nav-trial-t > b') == [x['card']] and pg.evaluate(TXT, '#main .nav-trial .nav-trial-t > span') == [x['uses']], f"{tag} day 50: « {x['card']} »")
  ok(pg.evaluate("() => [...document.querySelectorAll('#main .nav-trial li')].map((l) => l.dataset.k)") == ['accounts', 'money', 'shots', 'history', 'ai'], f'{tag} day 50: the 5 paid features really used, in order')
  ok(pg.evaluate(TXT, '#main .nav-trial li') == [x['acc'], x['money'], x['shots'], x['hist'], x['ai']], f'{tag} day 50: each with its numbers ' + json.dumps(pg.evaluate(TXT, '#main .nav-trial li'), ensure_ascii=False))
  ok(pg.evaluate("() => { const c = document.querySelector('#main .nav-trial'), t = document.querySelector('#main .d-today'); return !!c && !!t && !!(t.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING) && c.parentElement === t.parentElement }"), f'{tag} day 50: under the day card')
  ok(pg.evaluate("() => { const r = document.querySelector('#main .nav-trial').getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth + 1 }") and pg.evaluate(WIDE) <= 1, f'{tag} day 50: nothing wider than the window')
  shot(pg, f'b13-day50-{tag}')
  pg.click('#main .nav-trial [data-trial-x]'); pg.wait_for_timeout(300)
  ok(pg.locator('#main .nav-trial').count() == 0, f'{tag} day 50: ✕ hides it')
  reload(pg)
  ok(pg.locator('#main .nav-trial').count() == 0, f'{tag} day 50: and it stays hidden')
  return br, ctx, pg, errs, uid

def back_to_free(br, ctx, pg, errs, uid, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  trial_ends(uid, time.time() - 3600)
  pg.goto(B1 + '/#dashboard'); pg.reload(); pg.wait_for_selector('.sb-layer .sb-fw', timeout=15000); pg.wait_for_timeout(700)
  ok(pg.evaluate(TXT, '.sb-fw .sb-h') == [x['fw']], f"{tag} day 61: one window opens by itself: « {x['fw']} »")
  ok(pg.locator('.sb-layer').count() == 1, f'{tag} day 61: only that one')
  ok(pg.evaluate(TXT, '.sb-fw .sb-bens li') == x['stays'], f'{tag} day 61: what stays ' + json.dumps(pg.evaluate(TXT, '.sb-fw .sb-bens li'), ensure_ascii=False))
  z = pg.evaluate(TXT, '.sb-fw .sb-fw-z li')
  ok(len(z) == 5 and 'Tradeify 50K' in z[0] and 'Lucid 25K' in z[0] and 'Topstep 50K' not in z[0] and x['zmoney'] in z and x['zhist'] in z, f'{tag} day 61: what is paused and kept ' + json.dumps(z, ensure_ascii=False))
  ok(pg.evaluate(TXT, '.sb-fw .sb-fw-h')[2] == x['choose'] and pg.evaluate("() => [...document.querySelectorAll('.sb-fw [data-acc]')].map((b) => b.dataset.acc + ':' + b.getAttribute('aria-checked') + ':' + b.getAttribute('role'))")
     == ['ba1:true:checkbox', 'ba2:true:checkbox', 'ba3:false:checkbox', 'ba4:false:checkbox'], f'{tag} day 61: the 2 oldest accounts checked, the trader picks 2')
  pg.click('.sb-fw [data-acc="ba4"]'); pg.wait_for_timeout(250)
  ok(pg.evaluate("() => [...document.querySelectorAll('.sb-fw [data-acc][aria-checked=true]')].map((b) => b.dataset.acc)") == ['ba2', 'ba4'] and all(w in pg.evaluate(TXT, '.sb-fw .sb-fw-z li')[0] for w in ('Topstep 50K', 'Tradeify 50K')) and 'Lucid 25K' not in pg.evaluate(TXT, '.sb-fw .sb-fw-z li')[0],
     f'{tag} day 61: a third pick replaces the first one, the paused line follows')
  ok(pg.evaluate(TXT, '.sb-fw .sb-fw-go') == [x['go']] and pg.evaluate(TXT, '.sb-fw .sb-fw-stay') == [x['stay']], f'{tag} day 61: how to get it back, or stay on Free')
  ok(pg.evaluate("() => { const s = document.querySelector('.sb-sheet').getBoundingClientRect(); return s.left >= 0 && s.right <= innerWidth + 1 && document.querySelector('.sb-body').scrollWidth <= document.querySelector('.sb-body').clientWidth + 1 }"), f'{tag} day 61: the window fits the screen')
  shot(pg, f'b13-free-{tag}')
  pg.click('.sb-fw .sb-fw-stay'); pg.wait_for_timeout(900)
  st = me(ctx)
  ok(st['plan'] == 'free' and st['accounts']['active'] == ['ba2', 'ba4'] and st['accounts']['frozen'] == ['ba1', 'ba3'] and st['free_window']['seen'] is True, f'{tag} day 61: « {x["stay"]} » keeps the 2 picked accounts active')
  p2 = ctx.new_page(); p2.on('pageerror', lambda e: errs.append(str(e)[:160]))
  p2.goto(B1 + '/#dashboard'); p2.wait_for_selector('#main .nav-dash', timeout=15000); p2.wait_for_timeout(2500)
  ok(p2.locator('.sb-layer').count() == 0, f'{tag} day 61: not again on the next visit')
  ok(p2.evaluate(TXT, '.sb-banner span') == [x['banner']] and p2.evaluate(TXT, '.sb-banner button') == [x['back']], f"{tag} day 61: the banner « {x['banner']} »")
  p2.click('.sb-banner button'); p2.wait_for_selector('.sb-layer .sb-fw', timeout=5000)
  ok(p2.evaluate(TXT, '.sb-fw .sb-h') == [x['fw']], f'{tag} day 61: the banner opens the same window')
  p2.keyboard.press('Escape'); p2.wait_for_timeout(500)
  p2.goto(B1 + '/#accounts'); p2.wait_for_timeout(1800)
  fz = p2.locator('#main [data-frozen]')
  if fz.count():
    fz.first.click(); p2.wait_for_selector('.sb-layer .sb-pw', timeout=5000)
    ok(p2.evaluate(TXT, '.sb-layer .sb-h') == [x['paused']], f"{tag} day 61: a paused account opens « {x['paused']} »")
    p2.keyboard.press('Escape'); p2.wait_for_timeout(400)
  else: ok(False, f'{tag} day 61: the paused accounts are marked on the Accounts page')
  ok(p2.evaluate(WIDE) <= 1, f'{tag} day 61: nothing wider than the window')
  gw = p2.evaluate("() => { localStorage.removeItem('sb_nudge'); const n = SweepBilling.nudge('green_week'); const t = n ? n.textContent : ''; document.querySelectorAll('.sb-nudge').forEach((e) => e.remove()); return t }")
  ok(bool(gw), f'{tag} day 61, on Free: « Strong week, go Pro » can show again ({gw[:50]!r})')
  p2.close()
  return p2

def subscription(p, ctx, pg, errs, uid, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]; now = int(time.time())
  ev = {'id': 'evt_e2e_c_' + uid, 'object': 'event', 'type': 'customer.subscription.created', 'data': {'object': sub('sub_e2e_' + uid, uid, 'active', now + 30 * D)}}
  c, r = hook(ctx.request, ev, 'whsec_someone_else')
  ok(c == 400 and me(ctx)['plan'] == 'free', f'{tag} webhook: a wrong signature is refused (400), nothing changes')
  c, r = hook(ctx.request, ev)
  ok(c == 200 and r.get('result', '').startswith('synced active'), f'{tag} webhook: the subscription is created ({c} {r})')
  c, r = hook(ctx.request, ev)
  ok(c == 200 and r.get('result') == 'duplicate', f'{tag} webhook: the same event again is ignored')
  st = me(ctx)
  ok(st['plan'] == 'pro' and st['source'] == 'subscription' and st['accounts']['frozen'] == [] and st['free_window'] is None, f'{tag} Pro: paid, every account open, no window')
  time.sleep(1.1)
  ev2 = {'id': 'evt_e2e_d_' + uid, 'object': 'event', 'type': 'customer.subscription.deleted', 'data': {'object': sub('sub_e2e_' + uid, uid, 'canceled', now + 30 * D)}}
  c, r = hook(ctx.request, ev2)
  st = me(ctx)
  ok(c == 200 and st['plan'] == 'free' and (st['free_window'] or {}).get('kind') == 'subscription' and st['accounts']['active'] == ['ba2', 'ba4'], f'{tag} cancelled: Free again, the same accounts active')
  p3 = ctx.new_page(); p3.on('pageerror', lambda e: errs.append(str(e)[:160]))   # a new visit (the window opens once per visit)
  p3.goto(B1 + '/#dashboard'); p3.wait_for_selector('.sb-layer .sb-fw', timeout=15000); p3.wait_for_timeout(600)
  ok(p3.evaluate(TXT, '.sb-fw .sb-h') == [x['fwsub']], f"{tag} cancelled: the window opens again, « {x['fwsub']} »")
  shot(p3, f'b13-sub-{tag}')
  p3.close()

def spanish(p):
  tag = '390-es'; x = X['es']
  br, ctx, pg, errs, uid = trader(p, 'es', True, 'es')
  me(ctx); trial_ends(uid, time.time() - 3600)
  pg.goto(B1 + '/#dashboard'); pg.reload(); pg.wait_for_selector('.sb-layer .sb-fw', timeout=15000); pg.wait_for_timeout(700)
  ok(pg.evaluate(TXT, '.sb-fw .sb-h') == [x['fw']] and pg.evaluate(TXT, '.sb-fw .sb-bens li') == x['stays'], f"{tag}: « {x['fw']} », what stays")
  ok(x['zmoney'] in pg.evaluate(TXT, '.sb-fw .sb-fw-z li') and pg.evaluate(TXT, '.sb-fw .sb-fw-h')[2] == x['choose'] and pg.evaluate(TXT, '.sb-fw .sb-fw-go') == [x['go']], f'{tag}: paused, the choice, how to get it back')
  body = pg.evaluate("document.querySelector('.sb-fw').innerText")
  ok(not [w for w in EN_ONLY if w in body], f'{tag}: no English in the window')
  ok(pg.evaluate(WIDE) <= 1, f'{tag}: nothing wider than the window')
  shot(pg, 'b13-free-390-es')
  ok(not errs, f'{tag}: no page error ' + '; '.join(errs[:2]))
  br.close()

def admin(p, ctx_trader):
  br = p.chromium.launch(); adm = br.new_context(storage_state=STATE)
  # referral from the referrer's own connection (here everything comes from 127.0.0.1): to review, then approved in Admin
  sql("DELETE FROM referrals WHERE created_at > ?", (int(time.time()) - D,))   # earlier runs today (3 a day per connection)
  code = ctx_trader.request.get(B + '/api/referral', headers=H).json()['code']
  unthrottle()
  fr = br.new_context(); fr.request.get(B1 + '/r/' + code, max_redirects=0)
  email = 'billfriend%d@t.dev' % int(time.time() * 1000)
  r = fr.request.post(B1 + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000}), headers=H)
  fuid = uid_of(email); f0 = fr.request.get(B1 + '/api/billing/me', headers=H).json()
  row = sql('SELECT id, status FROM referrals WHERE referee_id = ?', (fuid,))
  ok(r.status == 201 and row and row[0][1] == 'review' and f0['plan'] == 'pro', 'referral: same connection as the referrer → to review, no Elite yet (' + json.dumps(row) + ')')
  a = adm.request.post(B1 + '/api/admin/referrals/%d' % row[0][0], data=json.dumps({'action': 'approve'}), headers=H)
  f1 = fr.request.get(B1 + '/api/billing/me', headers=H).json()
  g = sql("SELECT plan, ends_at - starts_at FROM billing_grants WHERE uid = ? AND reason = 'referral'", (fuid,))
  ok(a.status == 200 and f1['plan'] == 'elite' and g == [('elite', 14 * D)], 'referral: approved in Admin → the friend gets 14 days of Elite (' + json.dumps(g) + ')')
  # feedback: the trader sends, Admin reads and answers
  r = ctx_trader.request.post(B + '/api/feedback', data=json.dumps({'type': 'idea', 'message': 'Un filtre par setup sur le calendrier', 'page': '#calendar', 'lang': 'fr'}), headers=H)
  fid = r.json().get('id') if r.status == 201 else None
  items = adm.request.get(B + '/api/admin/feedback', headers=H).json().get('items', [])
  it = next((i for i in items if i['id'] == fid), {})
  ok(r.status == 201 and it.get('message') == 'Un filtre par setup sur le calendrier' and it.get('status') == 'new' and it.get('page') == '#calendar', 'feedback: the message reaches Admin, with its page')
  bad = adm.request.post(B + '/api/admin/feedback/%s' % fid, data=json.dumps({'status': 'bogus'}), headers=H)
  ok(bad.status == 400 and 'error' in bad.json() and 'ok' not in bad.json(), 'feedback: an unknown status is refused (400, an error, not « ok »)')
  gone = adm.request.post(B + '/api/admin/feedback/999999', data=json.dumps({'status': 'planned'}), headers=H)
  ok(gone.status == 404, 'feedback: a message that does not exist → 404')
  good = adm.request.post(B + '/api/admin/feedback/%s' % fid, data=json.dumps({'status': 'planned', 'reply': 'Prévu pour novembre.'}), headers=H)
  mine = next((i for i in ctx_trader.request.get(B + '/api/feedback', headers=H).json().get('items', []) if i['id'] == fid), {})
  ok(good.status == 200 and good.json().get('ok') is True and mine.get('status') == 'planned' and mine.get('reply') == 'Prévu pour novembre.', 'feedback: « planned » with a reply, the trader sees both')
  br.close()

srv = billing_server()
try:
  with sync_playwright() as p:
    br, ctx, pg, errs, uid = day50(p, 'fr', True)
    back_to_free(br, ctx, pg, errs, uid, 'fr', True)
    admin(p, ctx)
    ok(not errs, '390-fr: no page error ' + '; '.join(errs[:2]))
    br.close()
    br, ctx, pg, errs, uid = day50(p, 'en', False)
    back_to_free(br, ctx, pg, errs, uid, 'en', False)
    subscription(p, ctx, pg, errs, uid, 'en', False)
    ok(not errs, '1300-en: no page error ' + '; '.join(errs[:2]))
    br.close()
    spanish(p)
finally:
  stop(srv)
print(('FAIL ' if fails else 'ok   ') + f'{fails} failed')
sys.exit(1 if fails else 0)
