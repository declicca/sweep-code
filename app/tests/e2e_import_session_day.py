"""
Sweep — CSV imports use the trading day (session) of each trade, like the firms (dev environment with Playwright):
  python3 tests/e2e_import_session_day.py http://127.0.0.1:8095 /tmp/show_state.json
 - TopstepX: the TradeDay column is taken as is;
 - TopstepX without TradeDay, Rithmic: a trade opened at 18:00 New York time or later belongs to the next day;
 - a daytime trade keeps its day; the import key (duplicates) does not change.
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
TX = ('Id,ContractName,EnteredAt,ExitedAt,EntryPrice,ExitPrice,Fees,PnL,Size,Type,TradeDay,TradeDuration,Commissions\n'
      '900001,NQZ6,10/01/2026 23:30:00 +00:00,10/01/2026 23:40:00 +00:00,24900,24910,2.1,400,1,Long,10/02/2026 00:00:00 -05:00,0:10:00,0\n'
      '900002,NQZ6,10/01/2026 14:00:00 +00:00,10/01/2026 14:05:00 +00:00,24900,24905,2.1,200,1,Long,10/01/2026 00:00:00 -05:00,0:05:00,0\n')
TX_NODAY = ('Id,ContractName,EnteredAt,ExitedAt,EntryPrice,ExitPrice,Fees,PnL,Size,Type,TradeDuration,Commissions\n'
            '900003,NQZ6,10/01/2026 23:30:00 +00:00,10/01/2026 23:40:00 +00:00,24900,24910,2.1,400,1,Long,0:10:00,0\n')
RT = ('Completed Orders\nAccount,Status,Remarks,Buy/Sell,Qty To Fill,Symbol,Qty Filled,Avg Fill Price,Limit Price,Order Number,Create Time,Update Time,Commission\n'
      'APEX-1,Filled,,B,0,NQZ6,1,24900,24900,1,2026-10-01 19:30:00,2026-10-01 19:30:00,2.1\n'
      'APEX-1,Filled,,S,0,NQZ6,1,24910,24910,2,2026-10-01 19:40:00,2026-10-01 19:40:00,2.1\n'
      'APEX-1,Filled,,B,0,NQZ6,1,24900,24900,3,2026-10-02 10:00:00,2026-10-02 10:00:00,2.1\n'
      'APEX-1,Filled,,S,0,NQZ6,1,24905,24905,4,2026-10-02 10:05:00,2026-10-02 10:05:00,2.1\n')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); ctx = await br.new_context(storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg = await ctx.new_page(); await pg.goto(B + '/?x=1#trades'); await pg.wait_for_timeout(2500)
    run = lambda csv: pg.evaluate("(t)=>parseTradovate(t).map(r=>({date:r.date,time:r.entry_time,key:r.key}))", csv)
    tx = await run(TX)
    by = {r['key']: r for r in tx}
    ok(by['tx:900001']['date'] == '2026-10-02' and by['tx:900002']['date'] == '2026-10-01', f'TopstepX: TradeDay used (19:30 ET on Oct 1 → Oct 2; 10:00 → Oct 1): {tx}')
    nd = await run(TX_NODAY)
    ok(nd[0]['date'] == '2026-10-02', f'TopstepX without TradeDay: 19:30 ET → next day {nd}')
    rt = await run(RT)
    ok([r['date'] for r in rt] == ['2026-10-02', '2026-10-02'] and rt[0]['time'] == '19:30', f'Rithmic: 19:30 → Oct 2, 10:00 on Oct 2 stays: {rt}')
    ok(all(r['key'] for r in tx + rt), 'each row keeps its import key (no duplicates on a second import)')
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
