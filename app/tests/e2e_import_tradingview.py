"""
Sweep — TradingView « Order History » CSV import (dev environment with Playwright):
  python3 tests/e2e_import_tradingview.py http://127.0.0.1:8095 /tmp/show_state.json
Sample: tests/samples/tradingview-order-history-sample.csv (2 NQ, partial exits on MNQ, a cancelled order, an evening 6E trade).
"""
import asyncio, sys, os, json
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
CSV = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples', 'tradingview-order-history-sample.csv')).read()
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); ctx = await br.new_context(viewport={'width': 1280, 'height': 900}, locale='fr-CA', storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    await pg.goto(B + '/?x=1#import'); await pg.wait_for_timeout(2500)
    rows = await pg.evaluate("(t)=>parseTradovate(t).map(r=>({inst:r.inst,dir:r.dir,qty:r.qty,date:r.date,t:r.entry_time,x:r.exit_time,e:r.entry,ex:r.exit,pnl:r.pnl_c,fees:r.fees_c,key:r.key}))", CSV)
    print(json.dumps(rows))
    ok(len(rows) == 3, f'3 round trips (the cancelled order is skipped): {len(rows)}')
    nq = [r for r in rows if r['inst'] == 'NQ']; mnq = [r for r in rows if r['inst'] == 'MNQ']; e6 = [r for r in rows if r['inst'] == '6E']
    ok(nq and nq[0]['dir'] == 'long' and nq[0]['qty'] == 2 and nq[0]['pnl'] == 158000 and nq[0]['fees'] == 840 and nq[0]['t'] == '09:52', f'NQ long 2 @ 24,912.25 → 24,951.75 = +$1,580, fees $8.40 ({nq[:1]})')
    ok(mnq and mnq[0]['dir'] == 'short' and mnq[0]['qty'] == 3 and mnq[0]['pnl'] == round(((24960 - 24950) * 1 + (24960 - 24965.25) * 2) * 2 * 100), f'MNQ short 3, exits 1 + 2 → one trade, P&L from both exits ({mnq[:1]})')
    ok(e6 and e6[0]['date'] == '2026-09-30' and e6[0]['t'] == '19:30' and e6[0]['pnl'] == 12500, f'6E at 19:30 ET → session of the next day, +$125 ({e6[:1]})')
    # the file in the page: preview, time zone, import
    await pg.evaluate("(t)=>{IMP.rows=parseTradovate(t); IMP.file='tv.csv'; IMP.err=''; IMP.account=(S.accounts.find(a=>a.status!=='archived')||{}).id; render();}", CSV); await pg.wait_for_timeout(800)
    ok(await pg.locator('#main [data-itz]').count() == 1, 'the preview asks for the time zone of the file (New York by default)')
    await pg.select_option('#main [data-itz]', 'UTC'); await pg.wait_for_timeout(800)
    t_utc = await pg.evaluate("IMP.rows.find(r=>r.inst==='NQ').entry_time")
    ok(t_utc == '05:52', f'times written in UTC → New York (09:52 UTC = 05:52 ET): {t_utc}')
    await pg.select_option('#main [data-itz]', 'America/New_York'); await pg.wait_for_timeout(800)
    n0 = await pg.evaluate("S.trades.length")
    await pg.evaluate("void impGo()"); await pg.wait_for_timeout(3000)   # not awaited: the import moves to #trades
    new = await pg.evaluate("S.trades.filter(t=>String(t.import_key||'').startsWith('tv:')).map(t=>[t.instrument,t.date,t.session_date,t.pnl_c])")
    ok(len(new) == 3 and all(x[2] for x in new), f'3 trades imported, with their session date ({new})')
    await pg.evaluate("location.hash='#import'"); await pg.wait_for_timeout(800)
    await pg.evaluate("(t)=>{IMP.rows=parseTradovate(t); IMP.file='tv.csv'; render();}", CSV); await pg.wait_for_timeout(600)
    btn = await pg.evaluate("(document.querySelector('#main [data-act=imp-go]')||{}).disabled")
    ok(btn is True, 'importing the same file again adds nothing (already imported)')
    await pg.evaluate("S.trades.filter(t=>String(t.import_key||'').startsWith('tv:')).forEach(t=>remove('trades',t.id))"); await pg.wait_for_timeout(800)
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
