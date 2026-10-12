"""
Sweep — the manual trade form gives the exact P&L (brief 02, part 1, « Vérifier »), dev environment with Playwright:
  python3 tests/e2e_trade_form.py http://127.0.0.1:8095
A trader of its own. The expected amounts come from the exchanges' contract specs written below (tick size and tick value),
never from the app's own table:
 - every instrument of the form: long, 2 contracts, +7 ticks;
 - a short with several contracts, at a loss; a trade with an add and a partial exit (one trade from flat to flat);
 - fees: the account's round-trip commission is charged once per contract bought and sold (an add counts);
 - phone and computer: the form shows the result before saving, saves it, no page error.
"""
import asyncio, json, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
# CME / COMEX / NYMEX / CBOT specs: tick size, $ per tick per contract
SPEC = {'NQ': (.25, 5.00), 'MNQ': (.25, .50), 'ES': (.25, 12.50), 'MES': (.25, 1.25), 'YM': (1, 5.00), 'MYM': (1, .50), 'RTY': (.1, 5.00), 'M2K': (.1, .50),
        'CL': (.01, 10.00), 'MCL': (.01, 1.00), 'GC': (.1, 10.00), 'MGC': (.1, 1.00), '6E': (.00005, 6.25), 'M6E': (.0001, 1.25), 'ZN': (1 / 64, 15.625), 'ZB': (1 / 32, 31.25),
        'SI': (.005, 25.00), 'SIL': (.005, 5.00), 'NG': (.001, 10.00), 'HG': (.0005, 12.50), 'MBT': (5, .50), 'MET': (.5, .05)}
PRICE = {'NQ': 21000, 'MNQ': 21000, 'ES': 5800, 'MES': 5800, 'YM': 42000, 'MYM': 42000, 'RTY': 2200, 'M2K': 2200, 'CL': 72.5, 'MCL': 72.5, 'GC': 2650, 'MGC': 2650, '6E': 1.085, 'M6E': 1.085,
         'ZN': 110.5, 'ZB': 118, 'SI': 31.5, 'SIL': 31.5, 'NG': 2.75, 'HG': 4.3, 'MBT': 62000, 'MET': 2500}
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
SAVE = """async (o) => { Object.assign(TK, o.tk); if (o.execs) { TK.multi = true; TK.execs = o.execs; } const ids = new Set(S.trades.map(t => t.id));
  tkRefresh(); const shown = (document.querySelector('#tkResult') || {}).innerText || '';
  tkSave(); await new Promise(r => setTimeout(r, 1500)); const t = S.trades.find(x => !ids.has(x.id));
  return t ? { pnl: t.pnl_c, fees: t.fees_c == null ? null : t.fees_c, auto: !!t.fees_auto, net: tNet(t), qty: t.contracts, dir: t.direction, shown } : { shown, err: (document.querySelector('#tkErr') || {}).innerText }; }"""
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for w, h, mob in ((1300, 850, False), (390, 844, True)):
      tag = f'{w}px'
      ctx = await br.new_context(base_url=B, locale='en-US', viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
      H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
      r = await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tf%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
      ok(r.ok, f'{tag} a trader of its own ({r.status})')
      await ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Tia', 'last_name': 'Test'}), headers=H)
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#trades'); await pg.wait_for_timeout(2500)
      await pg.evaluate("""() => { put('accounts', {id:'tf-a', name:'Live NoFee', status:'active', phase:'live', money_type:'live', starting_balance_c:5000000, rules:{}});
        put('accounts', {id:'tf-b', name:'Live Fee', status:'active', phase:'live', money_type:'live', starting_balance_c:5000000, rules:{}, fee_rt_c:412}); }""")
      await pg.wait_for_timeout(800)
      async def trade(tk, execs=None):
        await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(700)
        return await pg.evaluate(SAVE, {'tk': tk, 'execs': execs})
      insts = list(SPEC) if not mob else ['NQ', 'CL', 'ZN']
      bad = []
      for inst in insts:
        tick, val = SPEC[inst]; e = PRICE[inst]; x = round(e + 7 * tick, 8)
        t = await trade({'account': 'tf-a', 'inst': inst, 'dir': 'long', 'qty': 2, 'entry': e, 'exit': x})
        want = round(7 * val * 2 * 100)
        if t.get('pnl') != want: bad.append((inst, t.get('pnl'), want, t.get('err')))
      ok(not bad, f'{tag} {len(insts)} instruments, long 2 contracts +7 ticks: exact P&L for each' + (f' — wrong: {bad}' if bad else ''))
      t = await trade({'account': 'tf-a', 'inst': 'ES', 'dir': 'short', 'qty': 3, 'entry': 5800, 'exit': 5802.5})
      ok(t.get('pnl') == -37500 and t.get('dir') == 'short' and t.get('qty') == 3, f'{tag} short 3 ES 5800 → 5802.50: −2.5 pts × 3 × $50 = −$375 ({t.get("pnl")})')
      ok('375' in t.get('shown', '') and ('−' in t['shown'] or '-' in t['shown']), f'{tag} the form shows the result before saving ({t.get("shown", "")[:60]!r})')
      d = '2026-10-08'
      ex = [{'id': 'a', 'side': 'buy', 'qty': 1, 'price': 21000, 't': d + ' 10:00:00'}, {'id': 'b', 'side': 'buy', 'qty': 1, 'price': 21002, 't': d + ' 10:05:00'},
            {'id': 'c', 'side': 'sell', 'qty': 1, 'price': 21005, 't': d + ' 10:10:00'}, {'id': 'd', 'side': 'sell', 'qty': 1, 'price': 21004, 't': d + ' 10:15:00'}]
      t = await trade({'account': 'tf-a', 'inst': 'NQ', 'date': d}, ex)
      ok(t.get('pnl') == 14000 and t.get('qty') == 2, f'{tag} NQ with an add and a partial exit: (21005 + 21004) − (21000 + 21002) = 7 pts × $20 = $140, 2 contracts max ({t.get("pnl")}, {t.get("qty")})')
      t = await trade({'account': 'tf-b', 'inst': 'MNQ', 'dir': 'long', 'qty': 3, 'entry': 21000, 'exit': 21010})
      ok(t.get('fees') == 1236 and t.get('auto') and t.get('net') == 6000 - 1236, f'{tag} fees: 3 contracts × $4.12 round trip = $12.36, net $60 − $12.36 ({t.get("fees")}, {t.get("net")})')
      ex2 = [{'id': 'a', 'side': 'buy', 'qty': 2, 'price': 21000, 't': d + ' 11:00:00'}, {'id': 'b', 'side': 'sell', 'qty': 1, 'price': 21004, 't': d + ' 11:05:00'},
             {'id': 'c', 'side': 'buy', 'qty': 1, 'price': 21002, 't': d + ' 11:10:00'}, {'id': 'd', 'side': 'sell', 'qty': 2, 'price': 21006, 't': d + ' 11:15:00'}]
      t = await trade({'account': 'tf-b', 'inst': 'MNQ', 'date': d}, ex2)
      ok(t.get('qty') == 2 and t.get('fees') == 3 * 412, f'{tag} fees with an add: 3 contracts bought and sold (2, then 1 more) = 3 round trips, $12.36 — not 2 ({t.get("fees")})')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
