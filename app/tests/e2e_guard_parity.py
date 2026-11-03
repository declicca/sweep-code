"""
Sweep — the account guardian and the account page show one drawdown room (brief « Gardien de compte », step 2; SWEEP.md 6,
rule 7), Playwright:
  python3 tests/e2e_guard_parity.py http://127.0.0.1:8095
A trader of his own with 60 accounts drawn at random (seeded): static, trailing at the end of the day, trailing trade by
trade, stopped at the start or not (with an offset), live without rules; trades over three weeks (Sunday evenings and
evening trades included), paid and requested payouts, dated adjustments. For each: the server's balance and drawdown floor
(api/guardian, guard/guard.php) equal the app's (acctState, src/app.js with its wrappers), and breached says the same.
"""
import json, random, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
R = random.Random(20261103)
def until(pg, js, ms=20000):   # (a predicate given as text is evaluated: the app's CSP refuses that)
  for _ in range(ms // 250):
    try:
      if pg.evaluate(js): return True
    except Exception: pass
    pg.wait_for_timeout(250)
  raise RuntimeError('timed out: ' + js)
def seed():
  accs, trades, pays = [], [], []
  days = ['2026-10-%02d' % d for d in range(12, 32)] + ['2026-11-%02d' % d for d in range(1, 4)]
  for i in range(60):
    typ = R.choice(['static', 'eod', 'trade', 'eod', 'trade', 'live'])
    start = R.choice([2500000, 5000000, 10000000, 15000000])
    a = {'id': 'pa%d' % i, 'name': 'P %d' % i, 'status': 'active', 'phase': R.choice(['eval', 'funded']), 'starting_balance_c': start}
    if typ == 'live': a.update(money_type='live', phase='live', rules={}); start = R.choice([0, 300000, 500000]); a['starting_balance_c'] = start
    else:
      r = {'dd_c': R.choice([100000, 200000, 250000, 300000]), 'dd_type': typ}
      if R.random() < .3: r['dd_lock'] = False
      elif R.random() < .3: r['dd_lock_offset_c'] = R.choice([10000, 20000])
      if R.random() < .5: r['dll_c'] = R.choice([50000, 100000])
      a['rules'] = r
    if R.random() < .25: a['adjustments'] = [{'id': 'ad%d' % i, 'at': R.choice(days), 'amount_c': R.choice([-15000, 8000, 30000])}]
    accs.append(a)
    for k in range(R.randint(0, 14)):
      d = R.choice(days); tm = R.choice(['09:31', '10:15', '11:02', '13:40', '15:55', '19:20', '20:05'])
      trades.append({'id': 'pt%d_%d' % (i, k), 'account_id': a['id'], 'date': d, 'entry_time': tm, 'exit_time': tm, 'instrument': 'MNQ', 'contracts': 1, 'direction': 'long',
                     'pnl_c': R.choice([-1, 1, 1]) * R.randint(1000, 90000), 'fees_c': R.choice([0, 250, 400])})
    if R.random() < .2: pays.append({'id': 'pp%d' % i, 'account_id': a['id'], 'status': R.choice(['paid', 'paid', 'requested']), 'amount_c': R.choice([50000, 100000]), 'payment_date': R.choice(days + [''])})
  return accs, trades, pays
with sync_playwright() as p:
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 1300, 'height': 850}, locale='en-US', timezone_id='America/New_York')
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('en')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}")
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'gp%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Pat', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); until(pg, "typeof put === 'function' && typeof acctState === 'function' && !!window.acctState.__adj")
  accs, trades, pays = seed()
  pg.evaluate("""async ([a, t, p]) => { a.forEach((x) => put('accounts', x)); t.forEach((x) => put('trades', x)); p.forEach((x) => put('payouts', x));
    await Promise.all(Object.values(chains)); await new Promise((r) => setTimeout(r, 800)); }""", [accs, trades, pays])
  pg.reload(); until(pg, "typeof acctState === 'function' && !!window.acctState.__adj && S.accounts.length >= 60")
  js = pg.evaluate("S.accounts.filter((a) => /^pa/.test(a.id)).map((a) => { const s = acctState(a); return [a.id, s.bal, s.thr, !!s.breached]; })")
  srv = pg.evaluate("apiJSON('api/guardian')")
  by = {a['id']: a for a in srv['accounts']}
  bad = []
  for aid, bal, thr, brk in js:
    g = by.get(aid)
    if not g: bad.append((aid, 'not watched')); continue
    fl = g['floors']['drawdown_c']
    if g['balance_c'] != bal or fl != thr or (g['level'] == 'breached') != (brk or (g['floors']['daily_c'] is not None and g['balance_c'] <= g['floors']['daily_c'])):
      bad.append((aid, [bal, thr, brk], [g['balance_c'], fl, g['level']]))
  ok(len(js) == 60 and not bad, f'60 accounts: the same balance, drawdown floor and breach on the account page and in the guardian ({len(js)} checked, {bad[:4]})')
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
