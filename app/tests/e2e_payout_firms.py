"""
Sweep — « ready for a payout », one test per firm and kind of funded account (brief 02, part 3, « Vérifier »), Playwright:
  python3 tests/e2e_payout_firms.py http://127.0.0.1:8095 /tmp/show_state.json
For every funded program and size of the catalogue (presets/seed.json), Topstep's « Consistency » option and its daily-loss-
limit option included, Apex's accounts bought before March 2026 (apex-legacy) included:
 - the account's payout rules (SweepPresets.rulesOf) match the catalogue (winning days, traded days, minimum, cap, ladder,
   safety net, number of payouts, split);
 - 8 scenarios: everything met; one day short; one big day; after a paid payout (a new cycle, the next step of the ladder);
   after a request still waiting (same: the request restarts the count and takes its step); a planned payout (not asked
   yet: nothing restarts); every payout of the firm already made; a breached account.
« Ready », the amount that can be asked for and each condition are computed here by a model of the firms' rules written
for this test (from the catalogue's own numbers), never by the app's code, and compared with SweepPayout.status. In
memory: nothing is saved.
The server counts the same way (GameV2::payoutStatus: the game's map and its « ready for a payout » badge): every scenario
but the breached one (the server does not follow the drawdown) goes through tests/payout_parity.php, same « ready », same %.
"""
import datetime as dt, json, math, os, subprocess, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
SEED = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'presets', 'seed.json')))
fails = 0
def ok(c, what):
  global fails
  print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
c_ = lambda x: None if x is None else round(x * 100)

def firm_rules(s, opts):
  """the funded rules of one size with the options chosen at purchase: a variant replaces the fields it names"""
  r = dict(s['funded'])
  for o in opts:
    v = ((s.get('variants') or {}).get(o) or {}).get('funded')
    for k, x in (v or {}).items():
      if x is None: r.pop(k, None)
      else: r[k] = x
  po = dict(r.get('payout') or {})
  if 'dll' in opts and po.get('max_dll'): po['max'] = po['max_dll']
  return po, r.get('consistency')

def model(po, cons, start, days, prev, bal):
  """the firm's conditions for the next payout. days: the cycle's daily results (cents) since the last counted payout;
  prev: payouts already made (requested, approved or paid); bal: the balance (paid payouts taken out)"""
  out = {}
  W, wm, T = po.get('win_days') or 0, c_(po.get('win_min') or 0), po.get('trade_days') or 0
  cyc = sum(days)
  if W: out['win'] = sum(1 for v in days if (v >= wm if wm else v > 0)) >= W
  if T: out['tdays'] = len(days) >= T
  if po.get('cycle_pos') and prev: out['pos'] = cyc > 0
  if po.get('first_min') and not prev: out['fmin'] = cyc >= c_(po['first_min'])
  if po.get('cycle_min') and prev: out['cmin'] = cyc >= c_(po['cycle_min'])
  if cons:
    pos = [v for v in days if v > 0]; tot = sum(pos)
    out['cons'] = tot > 0 and max(pos) / tot * 100 <= cons
  mn = c_(po.get('min') or 0); mb = c_(po.get('min_bal'))
  if mb: out['bal'] = bal >= mb + mn
  avail = bal - mb if mb else bal - start
  if po.get('max_pct'): avail = min(avail, (bal - start) * po['max_pct'] // 100)
  lad = po.get('ladder')
  cap = c_(lad[min(prev, len(lad) - 1)]) if lad else c_(po.get('max'))
  if cap: avail = min(avail, cap)
  avail = max(0, avail)
  out['amt'] = avail >= max(1, mn)
  if po.get('max_payouts'): out['maxn'] = prev < po['max_payouts']
  return out, avail

def plan(po, cons, start):
  """the smallest clean cycle that meets every rule: n equal days of d cents"""
  n = max(po.get('win_days') or 0, po.get('trade_days') or 0, 1)
  if cons: n = max(n, math.ceil(100 / cons))
  mn = c_(po.get('min') or 0); mb = c_(po.get('min_bal'))
  need = [mn, c_(po.get('first_min') or 0), c_(po.get('cycle_min') or 0)]
  if mb: need.append(mb - start + mn)
  if po.get('max_pct'): need.append(math.ceil(mn * 100 / po['max_pct']))
  P = max(need) + 5000   # a little more than just enough
  d = max(math.ceil(P / n / 100) * 100, c_(po.get('win_min') or 0) or 0)
  return n, d

def accounts():
  for f in SEED['firms']:
    for p in f['programs']:
      paths = [[]]
      for o in p.get('options') or []:
        if o.get('phase') in ('funded', 'all'): paths = [[c['id']] if c['id'] != o.get('default') else [] for c in o['choices']]
      for s in p['sizes']:
        if not (s.get('funded') or {}).get('payout'): continue
        for path in paths:
          for dll in ([[], ['dll']] if s['funded'].get('dll_optional') else [[]]):
            yield f, p, s, path + dll

def main():
  with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(storage_state=STATE, locale='en-US', viewport={'width': 1300, 'height': 900}, bypass_csp=True)   # (wait_for_function needs it)
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_function("!!window.SweepPresets && !!window.SweepPayout", timeout=15000)
    pg.wait_for_function("SweepPresets.ready() || (SweepPresets.load(), false)", timeout=20000, polling=500)   # loaded on demand (asked again until the app has started)
    base = dt.date.fromisoformat(pg.evaluate("todayStr()")) - dt.timedelta(days=300)
    day = lambda i: (base + dt.timedelta(days=i)).isoformat()
    n_acc = 0; seen = set(); parity = []
    for f, p, s, opts in accounts():
      n_acc += 1; seen.add((f['id'], p['id'], tuple(opts)))
      tag = f"{f['id']} {p['id']} {s['size'] // 1000}K" + (' ' + '+'.join(opts) if opts else '')
      pv = f"{f['id']}|{p['id']}|{s['size']}|funded|{'+'.join(opts)}"
      got = pg.evaluate("(v) => SweepPresets.rulesOf(v)", pv)
      if not got: ok(False, f'{tag}: no rules'); continue
      ru = got['rules']; po, cons = firm_rules(s, opts); start = round(s['size'] * 100)
      want = {'payout_win_days': po.get('win_days'), 'payout_trade_days': po.get('trade_days'), 'payout_min_c': c_(po.get('min')), 'payout_max_c': c_(po.get('max')),
              'payout_max_pct': po.get('max_pct'), 'payout_min_bal_c': c_(po.get('min_bal')), 'payout_max_n': po.get('max_payouts'), 'payout_split_pct': po.get('split_pct'),
              'payout_ladder_c': [c_(x) for x in po['ladder']] if po.get('ladder') else None, 'consistency_pct': cons}
      bad = {k: (v, ru.get(k)) for k, v in want.items() if ru.get(k) != v}
      ok(not bad, f'{tag}: payout rules from the catalogue' + (f' — {bad}' if bad else ''))
      n, d = plan(po, cons, start)
      T = lambda i, v, k='': {'id': f't{k}{i}', 'account_id': 'acc', 'date': day(i), 'session_date': True, 'entry_time': '10:00:00', 'pnl_c': v, 'fees_c': 0}
      P = lambda i, st, a, k='': {'id': f'p{k}{i}', 'account_id': 'acc', 'status': st, 'amount_c': a, 'request_date': day(i), 'approval_date': day(i), 'payment_date': day(i)}
      cyc = [T(i, d) for i in range(n)]
      _, a0 = model(po, cons, start, [d] * n, 0, start + n * d)
      later = [T(n + 1 + i, d, 'b') for i in range(n)]
      mx = po.get('max_payouts') or 0
      cases = [
        ('everything met', cyc, [], [d] * n, 0, start + n * d),
        ('one day short', cyc[:-1], [], [d] * (n - 1), 0, start + (n - 1) * d),
        ('one big day', [T(0, d * 4)] + cyc[1:], [], [d * 4] + [d] * (n - 1), 0, start + (n + 3) * d),
        ('after a paid payout', cyc + later, [P(n, 'paid', a0)], [d] * n, 1, start + 2 * n * d - a0),
        ('after a request still waiting', cyc + later, [P(n, 'requested', a0)], [d] * n, 1, start + 2 * n * d),
        ('a planned payout', cyc, [P(n - 1, 'planned', a0)], [d] * n, 0, start + n * d),
      ]
      if mx: cases.append(('every payout made', [T(mx + 1 + i, d, 'c') for i in range(n)], [P(i, 'paid', 100, 'm') for i in range(mx)], [d] * n, mx, start + n * d - 100 * mx))
      mis = {}; summary = ''
      for name, trades, pays, days, prev, bal in cases:
        w, wa = model(po, cons, start, days, prev, bal)
        if name == 'everything met' and not all(w.values()): mis['test plan'] = ('ready', w); continue
        st = pg.evaluate("""([ru, start, trades, pays]) => { const keep = [S.trades, S.payouts]; S.trades = trades; S.payouts = pays;
          try { const r = SweepPayout.status({ id: 'acc', starting_balance_c: start, phase: 'funded', money_type: 'funded', rules: ru }); return r && { ready: r.ready, avail: r.avail, pct: r.pct, conds: Object.fromEntries(r.conds.map((c) => [c.k, c.ok])) }; }
          finally { [S.trades, S.payouts] = keep; } }""", [ru, start, trades, pays])
        if not st: mis[name] = 'no status'; continue
        parity.append({'tag': f'{tag} · {name}', 'start': start, 'rules': ru, 'trades': trades, 'pays': pays, 'app': [st['ready'], st['pct']]})
        want_ready = all(w.values())
        if st['ready'] != want_ready or st['avail'] != wa or st['conds'] != w: mis[name] = {'model': (want_ready, wa, w), 'app': (st['ready'], st['avail'], st['conds'])}
        if name == 'everything met': summary = f'{n} days of ${d // 100:,}, up to ${wa / 100:,.0f}'
        if name == 'after a paid payout' and po.get('ladder'): summary += f', then up to ${wa / 100:,.0f} (payout 2)'
      # a breached account is never ready, whatever its cycle
      br_tr = cyc + [T(n, -start)]
      st = pg.evaluate("""([ru, start, trades]) => { const keep = [S.trades, S.payouts]; S.trades = trades; S.payouts = [];
        try { const r = SweepPayout.status({ id: 'acc', starting_balance_c: start, phase: 'funded', money_type: 'funded', rules: ru }); return r && r.ready; }
        finally { [S.trades, S.payouts] = keep; } }""", [ru, start, br_tr])
      if st is not False: mis['breached'] = st
      ok(not mis, f'{tag}: {len(cases) + 1} scenarios ({summary})' + (f' — {json.dumps(mis)}' if mis else ''))
    srv = json.loads(subprocess.run(['php', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'payout_parity.php')], input=json.dumps(parity), capture_output=True, text=True, check=True).stdout)
    off = [(c['tag'], c['app'], s2) for c, s2 in zip(parity, srv) if c['app'] != s2]
    ok(len(srv) == len(parity) and not off, f'the server counts the same way: {len(parity)} scenarios, same « ready » and %' + (f' — {off[:3]}' if off else ''))
    ok(('topstep', 'combine', ('consistency',)) in seen and ('apex', 'apex-legacy', ()) in seen, 'Topstep « Consistency » and Apex accounts from before March 2026 are covered')
    ok(n_acc >= 60, f'{n_acc} funded accounts checked (every funded program and size of the catalogue)')
    ok(not errs, 'no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    br.close()
  print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
main()
