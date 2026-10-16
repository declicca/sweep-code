"""
Sweep — the manual trade form gives the exact P&L (brief 02, part 1, « Vérifier »), dev environment with Playwright:
  python3 tests/e2e_trade_form.py http://127.0.0.1:8095
A trader of its own. The expected amounts come from the exchanges' contract specs written below (tick size and tick value),
never from the app's own table:
 - every instrument of the form: long, 2 contracts, +7 ticks;
 - a short with several contracts, at a loss; a trade with an add and a partial exit (one trade from flat to flat);
 - fees: the account's round-trip commission is charged once per contract bought and sold (an add counts);
 - phone and computer: the form shows the result before saving, saves it, no page error;
 - 6E keeps its prices to the pip (before 16 Oct.: rounded to the cent, 1.0850 → 1.09); a symbol outside Sweep's list (ZC):
   a new trade asks for its P&L, an edited one keeps the P&L the trader gave (before: recomputed at $0);
 - the quick sheet (net P&L only, audit of 16 Oct.): « Long / Short » next to the P&L, asked before saving (before: « long »
   made up); a short with a bearish bias is not « against your bias »; the entry time is the New York time of the save.
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
      t6 = await trade({'account': 'tf-a', 'inst': '6E', 'dir': 'long', 'qty': 1, 'entry': 1.0855, 'exit': 1.08585})
      p6 = await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.instrument==='6E').pop(); return t?[t.entry,t.exit]:null})()")
      ok(p6 == [1.0855, 1.08585] and t6.get('pnl') == 4375, f'{tag} 6E 1.0855 → 1.08585: prices kept to the pip, +$43.75 ({p6}, {t6.get("pnl")})')
      tz = await trade({'account': 'tf-a', 'inst': 'ZC', 'dir': 'long', 'qty': 1, 'entry': 450.25, 'exit': 452.75})
      zc = await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.instrument==='ZC').pop(); return t?{pnl:t.pnl_c, check:!!t.pnl_check, id:t.id}:null})()")
      ok(zc and zc['pnl'] is None and zc['check'], f'{tag} ZC (not in the list), new: no P&L made up, the trader is asked for it ({zc})')
      await pg.evaluate("(id)=>editDoc('trades', id, d=>{d.pnl_c=12500; delete d.pnl_check})", zc['id']); await pg.wait_for_timeout(500)
      await pg.evaluate("(id)=>openTicket(id)", zc['id']); await pg.wait_for_timeout(700)
      await pg.evaluate("async()=>{tkSave(); await new Promise(r=>setTimeout(r,1500))}")
      ze = await pg.evaluate("(id)=>{const t=getDoc('trades',id); return [t.instrument, t.pnl_c, !!t.pnl_check]}", zc['id'])
      ok(ze == ['ZC', 12500, False], f'{tag} ZC edited and saved: the +$125 the trader gave is kept ({ze})')
      # the quick sheet: only the net P&L and the side
      await pg.evaluate("() => { editDoc('settings','settings', d => { d.add_mode_pref = 'shot'; }); const D = todayStr(); put('journals', Object.assign({}, getDoc('journals', D) || {}, { id: D, pre: { bias: 'bearish', max_loss: '1000', saved_at: Math.floor(Date.now() / 1000) } })); }")
      await pg.wait_for_timeout(600)
      await pg.evaluate("openTicket(null)"); await pg.wait_for_selector('.nav-am.open', timeout=8000); await pg.wait_for_timeout(500)
      side = await pg.evaluate("(()=>{const n=document.querySelector('.nav-am-net input'), d=document.querySelector('.nav-am .nav-am-dir .seg'); if(!n||!d) return null; const a=n.getBoundingClientRect(), b=d.getBoundingClientRect(); return {open: !d.closest('details') || d.closest('details').open, row: Math.abs(a.bottom-b.bottom)<8 && b.left>a.right, on: d.querySelectorAll('button.on').length}})()")
      ok(side and side['open'] and side['row'] and side['on'] == 0, f'{tag} quick sheet: « Long / Short » next to the net P&L, none picked ({side})')
      await pg.locator('.nav-am input[data-am-f="net"]').fill('-400'); c0 = await pg.evaluate("S.trades.length")
      await pg.locator('.nav-am [data-am="save"]').click(); await pg.wait_for_timeout(900)
      er = await pg.evaluate("(document.querySelector('.nav-am.open .nav-am-err')||{}).innerText||''")
      ok(await pg.evaluate("S.trades.length") == c0 and 'Long or Short' in er, f'{tag} no side: « Save » asks for it, nothing saved ({er})')
      await pg.locator('.nav-am [data-am-seg="dir"][data-v="short"]').click(); await pg.wait_for_timeout(300)
      ny = await pg.evaluate("new Intl.DateTimeFormat('en-GB',{timeZone:'America/New_York',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date())")
      await pg.locator('.nav-am [data-am="save"]').click(); await pg.wait_for_timeout(1500)
      q = await pg.evaluate("(()=>{const t=S.trades[S.trades.length-1]; const n=window.SweepCoach&&SweepCoach.trade(t); return {dir:t.direction, time:t.entry_time, date:t.date, today:todayStr(), pnl:t.real_pnl_c, coach: JSON.stringify(n||'')}})()")
      ok(q['dir'] == 'short' and q['pnl'] == -40000, f'{tag} quick short −$400: saved « short » ({q["dir"]}, {q["pnl"]})')
      ok(q['time'] and q['time'][:5] >= ny and q['date'] == q['today'], f'{tag} the entry time is the New York time of the save ({q["time"]}, {ny} ET, session {q["date"]})')
      ok('against' not in q['coach'].lower() and 'bias' not in q['coach'].lower(), f'{tag} bearish bias, short trade: not « against your bias » ({q["coach"][:90]})')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
