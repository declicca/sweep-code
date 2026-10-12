"""
Sweep — one scenario per firm and kind of drawdown (brief 02, part 2, « Vérifier »), dev environment with Playwright:
  python3 tests/e2e_account_firms.py http://127.0.0.1:8095 /tmp/show_state.json
For every program of the catalogue (presets/seed.json, first size), evaluation and funded:
 - the account's rules (SweepPresets.rulesOf) match the catalogue: drawdown, its kind (end of day / per trade), the stop at
   the start (+ Apex's $100), the daily loss limit (none when the trader did not take an optional one);
 - 4 sessions of trades: +0.6 × the drawdown; +0.5 then −0.3 in the same session; +0.5 (past the stop at the start); today a
   loss of the daily limit (or −0.1 × the drawdown without one). The limit, the room, « breached » and « Daily limit hit »
   are computed here by a model of the firms' rules written for this test, never by the app's code, and compared with
   acctState. In memory: nothing is saved.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
SEED = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'presets', 'seed.json')))
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
def model(start, dd, kind, off, days, dll):
    """the firms' rules: per trade the limit follows the best balance after each trade, end of day after each session;
    it never goes above the start (+ offset). Amounts in cents. days = [[pnl, …], …], the last one is today."""
    cap = lambda x: min(x, start + off)
    bal, peak, thr, breached = start, start, start - dd, False
    for day in days:
        for pnl in day:
            bal += pnl
            if bal <= thr: breached = True
            if kind == 'trade': peak = max(peak, bal); thr = cap(peak - dd)
        if kind != 'trade': peak = max(peak, bal); thr = cap(peak - dd)
    today = sum(days[-1])
    return {'thr': thr, 'buffer': bal - thr, 'breached': breached, 'dll_hit': bool(dll) and -today >= dll}
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(storage_state=STATE, locale='en-US', viewport={'width': 1300, 'height': 900}, bypass_csp=True)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    await pg.goto(B + '/#dashboard'); await pg.wait_for_function("!!window.SweepPresets", timeout=15000)
    await pg.evaluate("SweepPresets.load()"); await pg.wait_for_function("SweepPresets.ready()", timeout=15000)   # loaded on demand
    today = await pg.evaluate("todayStr()")
    days = ['2026-10-01', '2026-10-02', '2026-10-05', today]
    n = 0
    for f in SEED['firms']:
      for prog in f['programs']:
        s = prog['sizes'][0]
        for phase in ('eval', 'funded'):
          r = s.get(phase)
          if not r: continue
          n += 1; tag = f"{f['id']} {prog['id']} {s['size'] // 1000}K {phase}"
          got = await pg.evaluate("(v) => SweepPresets.rulesOf(v)", f"{f['id']}|{prog['id']}|{s['size']}|{phase}")
          if not got: ok(False, f'{tag}: no rules'); continue
          ru = got['rules']; dd = round(r['dd'] * 100); kind = r.get('dd_type') or 'eod'; off = round((r.get('dd_lock_offset') or 0) * 100)
          dll = None if (r.get('dll_optional') or not r.get('dll')) else round(r['dll'] * 100)
          want_rules = {'dd_c': dd, 'dd_type': kind, 'dd_lock': True, 'dd_lock_offset_c': off or None, 'dll_c': dll}
          bad = {k: (v, ru.get(k)) for k, v in want_rules.items() if ru.get(k) != v}
          ok(not bad, f'{tag}: rules from the catalogue (drawdown ${dd // 100}, {kind}, stop at the start +${off // 100}, daily limit {dll // 100 if dll else "none"})' + (f' — {bad}' if bad else ''))
          plan = [[round(.6 * dd)], [round(.5 * dd), -round(.3 * dd)], [round(.5 * dd)], [-dll if dll else -round(.1 * dd)]]
          start = round(s['size'] * 100)
          want = model(start, dd, kind, off, plan, dll); mis = {}
          for k in (2, 3, 4):   # after the 2nd session (per trade: stopped at the start already; end of day: not yet), the 3rd, today
            part = plan[:k]; w = model(start, dd, kind, off, part, dll if k == 4 else None)
            trades = [{'id': f'x{i}-{j}', 'account_id': 'acc', 'date': days[i], 'session_date': True, 'entry_time': f'{10 + j}:00:00', 'pnl_c': v, 'fees_c': 0} for i, d in enumerate(part) for j, v in enumerate(d)]
            st = await pg.evaluate("""([ru, start, trades]) => { const keep = [S.trades, S.payouts]; S.trades = trades; S.payouts = [];
              try { const r = acctState({ id: 'acc', starting_balance_c: start, phase: 'funded', money_type: 'funded', rules: ru }); return { thr: r.thr, buffer: r.buffer, breached: r.breached, label: r.label }; }
              finally { [S.trades, S.payouts] = keep; } }""", [ru, start, trades])
            for x in ('thr', 'buffer', 'breached'):
              if w[x] != st[x]: mis[f'{x} after session {k}'] = (w[x], st[x])
            if k == 4 and w['dll_hit'] != (st['label'] == 'Daily limit hit') and not w['breached']: mis['daily limit hit'] = (w['dll_hit'], st['label'])
          ok(not mis, f"{tag}: limit ${want['thr'] / 100:,.0f}, room ${want['buffer'] / 100:,.0f}" + (', breached' if want['breached'] else '') + (', daily limit hit' if want['dll_hit'] and not want['breached'] else '') + (f' — {mis}' if mis else ''))
    ok(n >= 20, f'{n} accounts checked (every program of the catalogue, evaluation and funded)')
    ok(not errs, 'no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
