"""
Sweep — browser tests of the prop-rule maths (acctState in the app bundle), on known scenarios.
Run in a dev environment with Playwright (not on the server): python3 tests/e2e_prop_rules.py http://127.0.0.1:8095 state.json
The account and trades below are injected in memory only; nothing is saved.
"""
import asyncio, json, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else None
def T(date, net, i): return {'id': f't{i}', 'account_id': 'acc', 'date': date, 'entry_time': f'{9+i%6:02d}:{(i*7)%60:02d}:00', 'pnl_c': net * 100, 'fees_c': 0}
CASES = [
  ('EOD trailing: dip inside the day stays above the limit', {'dd_c': 200000, 'dd_type': 'eod'}, [T('2026-09-01', 1500, 1), T('2026-09-02', -1000, 2), T('2026-09-02', 900, 3)], {'breached': False, 'thr': 4950000}),
  ('EOD trailing: intraday breach counts even if the day ends above', {'dd_c': 200000, 'dd_type': 'eod'}, [T('2026-09-01', 1500, 1), T('2026-09-02', -2100, 2), T('2026-09-02', 800, 3)], {'breached': True}),
  ('EOD trailing stops at the starting balance (lock)', {'dd_c': 200000, 'dd_type': 'eod'}, [T('2026-09-01', 3000, 1)], {'breached': False, 'thr': 5000000}),
  ('Static drawdown never moves', {'dd_c': 200000, 'dd_type': 'static'}, [T('2026-09-01', 3000, 1), T('2026-09-02', -4000, 2)], {'breached': False, 'thr': 4800000}),
  ('Static drawdown breach', {'dd_c': 200000, 'dd_type': 'static'}, [T('2026-09-01', -2000, 1)], {'breached': True}),
  ('Per-trade trailing (intraday type)', {'dd_c': 200000, 'dd_type': 'trade'}, [T('2026-09-01', 1000, 1), T('2026-09-01', -2000, 2)], {'breached': True}),
  ('Consistency = best day / total profit', {'dd_c': 200000, 'dd_type': 'eod', 'consistency_pct': 50}, [T('2026-09-01', 1000, 1), T('2026-09-02', 500, 2), T('2026-09-03', 500, 3)], {'cons': 0.5, 'days': 3}),
]
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(storage_state=STATE) if STATE else await br.new_context()
    pg = await ctx.new_page(); await pg.goto(B + '/?t=1#dashboard'); await pg.wait_for_timeout(2500)
    fails = 0
    for name, rules, trades, want in CASES:
      got = await pg.evaluate("""([rules, trades]) => { const keep = [S.trades, S.payouts];
        S.trades = trades; S.payouts = [];
        try { const r = acctState({ id: 'acc', starting_balance_c: 5000000, rules }); return { breached: r.breached, thr: r.thr, cons: r.cons, days: r.days }; }
        finally { [S.trades, S.payouts] = keep; } }""", [rules, trades])
      bad = {k: (v, got.get(k)) for k, v in want.items() if (round(got.get(k), 4) if isinstance(v, float) else got.get(k)) != v}
      print(('FAIL ' if bad else 'ok   ') + name + (f'  {bad}' if bad else ''))
      fails += bool(bad)
    await br.close()
    print(f'{len(CASES) - fails}/{len(CASES)} passed'); sys.exit(1 if fails else 0)
asyncio.run(main())
