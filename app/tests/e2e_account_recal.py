"""
Sweep — an account added « already running » gives the right drawdown room (brief 02, part 2, « Vérifier »), Playwright:
  python3 tests/e2e_account_recal.py http://127.0.0.1:8095 /tmp/show_state.json
The accounts are written the way the add-account form writes them (« Already running »: current balance, highest balance):
an adjustment « Highest balance » the day before, an adjustment « Balance when added » that day, and hwm_c. Hand-computed:
 - trailing drawdown stopped at the start (Topstep 50K, $2,000): peak $54,000, now $53,000 → limit $50,000, room $3,000;
 - Apex (+$100): peak $53,000, now $52,500 → limit $50,100, room $2,400;
 - no stop at the start: peak $53,000, now $52,500 → limit $51,000, room $1,500; then +$1,500 of trades → new peak $54,000,
   limit $52,000, room $2,000 (the highest balance keeps following the account);
 - per trade, no stop: peak $52,000, now $51,800, a −$1,000 trade → limit $50,000, room $800;
 - added at $50,500 (peak $51,000, no stop), then +$800 the same day (end of day, per trade): the adjustments come before that
   day's trades → peak $51,300, limit $49,300, room $2,000 (not a peak of $51,800);
 - static: now $51,000 → limit $48,000, room $3,000; below the limit typed → breached.
In memory (nothing saved), then the same room on the account's page.
"""
import asyncio, json, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
YD, D, D2 = '2026-10-07', '2026-10-08', '2026-10-09'
def running(start, cur, peak=None):   # what the add-account form writes for « Already running » (nav.js)
    adj = []
    if peak is not None and peak > start and peak >= cur: adj.append({'id': 'h', 'at': YD, 'amount_c': (peak - start) * 100, 'note': 'Highest balance'})
    base = peak if adj else start
    if cur != base: adj.append({'id': 'c', 'at': D, 'amount_c': (cur - base) * 100, 'note': 'Balance when added to Sweep'})
    return {'adjustments': adj, 'hwm_c': max(start, peak if peak is not None else cur) * 100}
def T(date, net, i): return {'id': f't{i}', 'account_id': 'acc', 'date': date, 'session_date': True, 'entry_time': f'{10 + i}:00:00', 'pnl_c': net * 100, 'fees_c': 0}
EOD = {'dd_c': 200000, 'dd_type': 'eod', 'dd_lock': True}
CASES = [
  ('Topstep 50K, stopped at the start: peak $54,000, now $53,000 → limit $50,000, room $3,000', dict(EOD), running(50000, 53000, 54000), [], {'thr': 5000000, 'buffer': 300000, 'breached': False}),
  ('Apex (+$100): peak $53,000, now $52,500 → limit $50,100, room $2,400', dict(EOD, dd_lock_offset_c=10000), running(50000, 52500, 53000), [], {'thr': 5010000, 'buffer': 240000, 'breached': False}),
  ('No stop at the start: peak $53,000, now $52,500 → limit $51,000, room $1,500', dict(EOD, dd_lock=False), running(50000, 52500, 53000), [], {'thr': 5100000, 'buffer': 150000, 'breached': False}),
  ('… then +$1,500 of trades: new peak $54,000 → limit $52,000, room $2,000', dict(EOD, dd_lock=False), running(50000, 52500, 53000), [T(D2, 1500, 1)], {'thr': 5200000, 'buffer': 200000, 'breached': False}),
  ('Per trade, no stop: peak $52,000, now $51,800, a −$1,000 trade → limit $50,000, room $800', dict(EOD, dd_type='trade', dd_lock=False), running(50000, 51800, 52000), [T(D2, -1000, 1)], {'thr': 5000000, 'buffer': 80000, 'breached': False}),
  ('Added at $50,500 (peak $51,000, no stop), then +$800 the same day → peak $51,300, limit $49,300, room $2,000', dict(EOD, dd_lock=False), running(50000, 50500, 51000), [T(D, 800, 1)], {'thr': 4930000, 'buffer': 200000, 'breached': False}),
  ('… per trade, the same → limit $49,300, room $2,000', dict(EOD, dd_type='trade', dd_lock=False), running(50000, 50500, 51000), [T(D, 800, 1)], {'thr': 4930000, 'buffer': 200000, 'breached': False}),
  ('Static: now $51,000 → limit $48,000, room $3,000', dict(EOD, dd_type='static'), running(50000, 51000), [], {'thr': 4800000, 'buffer': 300000, 'breached': False}),
  ('No stop, peak $54,000, now $51,900 → limit $52,000: breached', dict(EOD, dd_lock=False), running(50000, 51900, 54000), [], {'thr': 5200000, 'breached': True}),
  ('Only the current balance typed ($52,000, no peak), stopped at the start → limit $50,000, room $2,000', dict(EOD), running(50000, 52000), [], {'thr': 5000000, 'buffer': 200000, 'breached': False}),
]
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': 1300, 'height': 900})
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
    for name, rules, extra, trades, want in CASES:
      got = await pg.evaluate("""([rules, extra, trades]) => { const keep = [S.trades, S.payouts]; S.trades = trades; S.payouts = [];
        try { const r = acctState(Object.assign({ id: 'acc', starting_balance_c: 5000000, phase: 'funded', money_type: 'funded', rules }, extra)); return { thr: r.thr, buffer: r.buffer, breached: r.breached, bal: r.bal }; }
        finally { [S.trades, S.payouts] = keep; } }""", [rules, extra, trades])
      bad = {k: (v, got.get(k)) for k, v in want.items() if got.get(k) != v}
      ok(not bad, name + (f'  {bad} (balance {got.get("bal")})' if bad else ''))
    # the same room on the account's page
    await pg.evaluate("""(x) => { put('firms', {id:'f-rc', name:'Topstep'}); put('accounts', Object.assign({id:'rc-acc', firm_id:'f-rc', name:'Recal 50K', starting_balance_c:5000000, status:'active', phase:'funded', money_type:'funded',
      rules:{dd_c:200000, dd_type:'eod', dd_lock:true}}, x)); }""", running(50000, 53000, 54000))
    await pg.evaluate("location.hash='#account/rc-acc'"); await pg.wait_for_timeout(2000)
    room = await pg.evaluate("(()=>{const r=[...document.querySelectorAll('#main .rule')].find(x=>/Marge de drawdown/.test(x.textContent)); return r?r.querySelector('b').textContent.replace(/\\s+/g,' ').trim():''})()")
    ok(room.replace(' ', ' ').replace(' ', ' ') == '3 000 $', f'account page: « Marge de drawdown {room} » (expects 3 000 $)')
    await pg.evaluate("editDoc('accounts','rc-acc', d => { d.status = 'archived'; })")
    ok(not errs, 'no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
