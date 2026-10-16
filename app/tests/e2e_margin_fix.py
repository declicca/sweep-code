"""
Sweep — two margins that were wrong (brief 00, phase 1.2-b and 1.2-c), Playwright, in memory (nothing saved):
  python3 tests/e2e_margin_fix.py http://127.0.0.1:8095 /tmp/show_state.json
 b. a payout that takes the account under its limit is caught even with no trade after it (it was subtracted only before
    the next trade): 50K, trailing $2,000, +$2,100 then a $2,050 payout → balance $50,050 under the $50,100 limit: breached;
    a payout without a date never holds back the ones after it;
 c. the trades of a session in their real order: an evening trade (19:00, counted on the next session) comes before that
    session's morning — real-time drawdown: +$1,000 at 19:00 then −$1,500 at 10:00 → room $500, not $1,500.
The expected numbers are worked out here by hand; the app's own state (acctState) is compared with them.
 f. one consistency everywhere (Q4, recommendation C): best day ÷ total net profit, unless the firm's catalogue says
    « consistency_base: win » (÷ the winning days) — +$400 / +$300 / +$300 / −$500 is 80 % on the account page, in « ready for a
    payout » and on the server (it was 40 % in the last two);
 d. Q3 (recommendation B): a trader whose account changes is told once — « We fixed how your room is calculated », one
    line per account changed (its room now, and before; or « drawdown exceeded »); not again after a reload (a mark in his
    settings); a trader whose numbers do not change never sees it. FR, EN, ES.
"""
import json, os, random, sqlite3, subprocess, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

ST = """([acc, trades, pays]) => { const keep = [S.trades, S.payouts]; S.trades = trades; S.payouts = pays;
  try { const s = acctState(acc); return { bal: s.bal, thr: s.thr, buffer: s.buffer, breached: !!s.breached }; } finally { [S.trades, S.payouts] = keep; } }"""
T = lambda i, d, t, v: {'id': f'm{i}', 'account_id': 'acc', 'date': d, 'session_date': True, 'entry_time': t, 'exit_time': t, 'instrument': 'NQ', 'direction': 'long', 'contracts': 1, 'pnl_c': v, 'fees_c': 0, 'created_at': f'2026-10-0{i}T00:00:00Z'}
P = lambda i, d, a: {'id': f'p{i}', 'account_id': 'acc', 'status': 'paid', 'amount_c': a, 'payment_date': d, 'request_date': d, 'approval_date': d}
with sync_playwright() as p:
  br = p.chromium.launch(); ctx = br.new_context(storage_state=STATE); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.add_init_script("sessionStorage.setItem('sw.modal','1')"); pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
  for kind in ('eod', 'trade'):
    acc = {'id': 'acc', 'name': 'Apex 50K', 'starting_balance_c': 5000000, 'phase': 'funded', 'rules': {'dd_c': 200000, 'dd_type': kind, 'dd_lock': False}}
    s = pg.evaluate(ST, [acc, [T(1, '2026-10-06', '10:00', 210000)], [P(1, '2026-10-07', 205000)]])
    ok(s['bal'] == 5005000 and s['thr'] == 5010000 and s['breached'], f'b {kind}: +$2,100, then a $2,050 payout, no trade after → $50,050 under $50,100: breached ({s})')
    s = pg.evaluate(ST, [acc, [T(1, '2026-10-06', '10:00', 210000)], [P(1, '2026-10-07', 100000)]])
    ok(not s['breached'] and s['bal'] == 5110000, f'b {kind}: a $1,000 payout stays above: not breached ({s})')
    s = pg.evaluate(ST, [acc, [T(1, '2026-10-06', '10:00', 210000)], [P(1, '', 1000), P(2, '2026-10-07', 205000)]])
    ok(s['breached'], f'b {kind}: a payout without a date does not hold back the next one ({s})')
    s = pg.evaluate(ST, [acc, [T(1, '2026-10-06', '10:00', 210000), T(3, '2026-10-09', '10:00', 50000)], [P(1, '2026-10-07', 205000)]])
    ok(s['breached'], f'b {kind}: under the limit right after the payout, then a winning trade: still breached ({s})')
  acc = {'id': 'acc', 'name': 'TPT 50K', 'starting_balance_c': 5000000, 'phase': 'funded', 'rules': {'dd_c': 200000, 'dd_type': 'trade', 'dd_lock': False}}
  s = pg.evaluate(ST, [acc, [T(2, '2026-10-08', '10:00', -150000), T(1, '2026-10-08', '19:00', 100000)], []])
  ok(s['buffer'] == 50000 and s['thr'] == 4900000, f'c real-time drawdown: +$1,000 at 19:00 (the evening before), then −$1,500 at 10:00 → room $500 ({s})')
  ok(pg.evaluate("sorted([{date:'2026-10-08',entry_time:'10:00',session_date:true,id:'a'},{date:'2026-10-08',entry_time:'19:00',session_date:true,id:'b'}]).map(t=>t.id).join('')") == 'ba', 'c the trades of a session in their real order: the evening one first')
  co = pg.evaluate("""() => { const keep = S.trades; const t = (id, tm, v) => ({ id, account_id: 'acc', date: '2026-10-08', session_date: true, entry_time: tm, exit_time: tm, instrument: 'NQ', direction: 'long', contracts: 1, pnl_c: v, fees_c: 0 });
    S.trades = [t('c2', '00:03', 20000), t('c1', '23:58', -50000)];
    try { const n = SweepCoach.trade(S.trades[0]); return (n && n.all) || []; } finally { S.trades = keep; } }""")
  ok('revenge' in co, f'c the coach in the real order: a trade at 00:03, 5 minutes after a loss at 23:58 the evening before, is « right after a loss » ({co})')
  ok(not errs, f'no page error ({errs[:2]})')
  # f. one consistency
  days = [('2026-09-01', 40000), ('2026-09-02', 30000), ('2026-09-03', 30000), ('2026-09-04', -50000)]
  tr = [T(i + 1, d, '10:00', v) for i, (d, v) in enumerate(days)]
  ev = {'id': 'acc', 'name': 'E', 'starting_balance_c': 5000000, 'phase': 'eval', 'rules': {'dd_c': 200000, 'dd_type': 'eod', 'target_c': 900000, 'consistency_pct': 50}}
  cs = pg.evaluate("""([acc, trades]) => { const keep = S.trades; S.trades = trades; try { return acctState(acc).cons } finally { S.trades = keep } }""", [ev, tr])
  ok(cs is not None and round(cs * 100) == 80, f'f account page: 80 % ({cs})')
  for base, want in ((None, (False, '80')), ('win', (True, '40'))):
    ru = {'consistency_pct': 50, 'payout_min_c': 100, **({'consistency_base': base} if base else {})}   # (a payout rule: a $1 minimum)
    st = pg.evaluate("""([ru, trades]) => { const keep = [S.trades, S.payouts]; S.trades = trades; S.payouts = [];
      try { const r = SweepPayout.status({ id: 'acc', starting_balance_c: 5000000, phase: 'funded', money_type: 'funded', rules: ru }); const c = r.conds.find((x) => x.k === 'cons'); return [c.ok, String(c.have).replace(/[^0-9]/g, '')]; }
      finally { [S.trades, S.payouts] = keep; } }""", [ru, tr])
    ok(st == list(want), f'f « ready for a payout », {base or "net (default)"}: {want[1]} %, within 50 %: {want[0]} ({st})')
    srv = json.loads(subprocess.run(['php', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'payout_parity.php')], input=json.dumps([{'start': 5000000, 'rules': ru, 'trades': tr, 'pays': []}]), capture_output=True, text=True, check=True).stdout)
    ok(srv and srv[0][0] is want[0], f'f the server, {base or "net (default)"}: ready {want[0]} like the app ({srv})')
  # d. told once
  W = {'fr': ('On a corrigé le calcul de ta marge', 'drawdown dépassé'), 'en': ('We fixed how your room is calculated', 'drawdown exceeded'), 'es': ('Corregimos el cálculo de tu margen', 'drawdown superado')}
  H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False), ('es', 390, True)):
    try: d = sqlite3.connect(os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    c = br.new_context(viewport={'width': w, 'height': 844}, is_mobile=phone, has_touch=phone)
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'mf%07d@t.dev' % random.randint(0, 9999999), 'consent': True, 'elapsed': 6000}), headers=H)
    pg = c.new_page(); e2 = []; pg.on('pageerror', lambda e: e2.append(str(e)[:160])); pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("""() => { put('accounts', { id: 'mf-a', name: 'Apex 50K', status: 'active', phase: 'funded', starting_balance_c: 5000000, rules: { dd_c: 200000, dd_type: 'eod', dd_lock: false } });
      put('accounts', { id: 'mf-b', name: 'TPT 50K', status: 'active', phase: 'funded', starting_balance_c: 5000000, rules: { dd_c: 200000, dd_type: 'trade', dd_lock: false } });
      put('accounts', { id: 'mf-c', name: 'Calme 50K', status: 'active', phase: 'funded', starting_balance_c: 5000000, rules: { dd_c: 200000, dd_type: 'eod', dd_lock: false } });
      const t = (id, a, d, tm, v) => put('trades', { id, account_id: a, date: d, session_date: true, entry_time: tm, exit_time: tm, instrument: 'NQ', direction: 'long', contracts: 1, pnl_c: v, pnl_manual: true });
      t('mf-1', 'mf-a', '2026-10-06', '10:00', 210000); put('payouts', { id: 'mf-p', account_id: 'mf-a', status: 'paid', amount_c: 205000, payment_date: '2026-10-07' });
      t('mf-2', 'mf-b', '2026-10-08', '10:00', -150000); t('mf-3', 'mf-b', '2026-10-08', '19:00', 100000); t('mf-4', 'mf-c', '2026-10-08', '10:00', 30000); }""")
    pg.wait_for_timeout(1500); pg.evaluate("location.hash='#accounts'"); pg.wait_for_timeout(2500)
    box = pg.evaluate("(document.querySelector('aside.nav-mfix.open')||{}).innerText||''")
    ok(W[lang][0] in box and 'Apex 50K' in box and W[lang][1] in box and 'TPT 50K' in box and 'Calme 50K' not in box, f'{lang} d the window, once: the 2 accounts that changed, not the other ({box[:160]!r})')
    if box: pg.locator('aside.nav-mfix [data-mfix]').click(); pg.wait_for_timeout(800)
    pg.reload(); pg.wait_for_timeout(3500)
    ok(pg.evaluate("!document.querySelector('aside.nav-mfix.open') && !!(S.settings && S.settings.margin_fix)"), f'{lang} d after a reload: not again (kept in his settings)')
    ok(not e2 and pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{lang} d no page error, nothing wider than the window ({e2[:1]})')
    if phone and lang == 'fr': pass
    c.close()
  # a trader whose numbers do not change: never the window
  c = br.new_context(storage_state=STATE); pg = c.new_page(); pg.add_init_script("sessionStorage.setItem('sw.modal','1')"); pg.goto(B + '/#accounts'); pg.wait_for_timeout(3500)
  ok(not pg.evaluate("!!document.querySelector('aside.nav-mfix.open')"), 'd the sample trader (nothing changes): no window'); c.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
