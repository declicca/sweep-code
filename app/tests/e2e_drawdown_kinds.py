"""
Sweep — drawdown by kind of account (dev environment with Playwright):
  python3 tests/e2e_drawdown_kinds.py http://127.0.0.1:8095 /tmp/show_state.json
 Challenges and funded accounts (trailing drawdown): the limit follows the best balance, then stops at the starting
 balance (+ the firm's offset, Apex $100). With $2,000 of drawdown and +$6,000 of profit, the worst case is going back to
 the start: the room is $6,000, not $2,000.
 Live accounts without firm rules: the most you can lose is the live balance itself (some lives start at $0); the room is
 the current balance, never negative. A live account with its firm's own rules (Topstep Live: a fixed floor) keeps them.
 The room is the same on Today, in the Accounts list and on the account's page.
Part 1 injects accounts and trades in memory (nothing saved); part 2 saves two accounts in the test database, then removes them.
"""
import asyncio, re, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
def T(date, net, i): return {'id': f't{i}', 'account_id': 'acc', 'date': date, 'session_date': True, 'entry_time': f'{9 + i % 6:02d}:{(i * 7) % 60:02d}:00', 'pnl_c': net * 100, 'fees_c': 0}
EOD = {'dd_c': 200000, 'dd_type': 'eod', 'dd_lock': True}
CASES = [
  ('Funded EOD 50K, +3,000 +3,000: limit stopped at the start, room $6,000', {'starting_balance_c': 5000000, 'phase': 'funded', 'money_type': 'funded', 'rules': EOD},
   [T('2026-10-01', 3000, 1), T('2026-10-02', 3000, 2)], {'thr': 5000000, 'buffer': 600000, 'breached': False}),
  ('Funded intraday 50K, +3,000 +3,000: same', {'starting_balance_c': 5000000, 'phase': 'funded', 'money_type': 'funded', 'rules': dict(EOD, dd_type='trade')},
   [T('2026-10-01', 3000, 1), T('2026-10-02', 3000, 2)], {'thr': 5000000, 'buffer': 600000, 'breached': False}),
  ('Funded with the Apex offset (+$100): limit stopped at $50,100', {'starting_balance_c': 5000000, 'phase': 'funded', 'money_type': 'funded', 'rules': dict(EOD, dd_lock_offset_c=10000)},
   [T('2026-10-01', 3000, 1), T('2026-10-02', 3000, 2)], {'thr': 5010000, 'buffer': 590000, 'breached': False}),
  ('Challenge Topstep 50K, +2,500: limit stopped at the start, room $2,500', {'starting_balance_c': 5000000, 'phase': 'eval', 'money_type': 'eval', 'rules': dict(EOD, target_c=300000)},
   [T('2026-10-01', 2500, 1)], {'thr': 5000000, 'buffer': 250000, 'breached': False}),
  ('Before the stop: +1,000 → limit $49,000, room $2,000', {'starting_balance_c': 5000000, 'phase': 'funded', 'money_type': 'funded', 'rules': EOD},
   [T('2026-10-01', 1000, 1)], {'thr': 4900000, 'buffer': 200000, 'breached': False}),
  ('Funded starting at $0 (displayed balance from zero), +6,000: limit stopped at $0, room $6,000', {'starting_balance_c': 0, 'phase': 'funded', 'money_type': 'funded', 'rules': EOD},
   [T('2026-10-01', 3000, 1), T('2026-10-02', 3000, 2)], {'thr': 0, 'buffer': 600000, 'breached': False}),
  ('Stopped, then back under the start: exceeded', {'starting_balance_c': 5000000, 'phase': 'funded', 'money_type': 'funded', 'rules': EOD},
   [T('2026-10-01', 3000, 1), T('2026-10-02', -3100, 2)], {'thr': 5000000, 'breached': True}),
  ('Live without rules, starting at $0, +1,500 −400: room = balance $1,100', {'starting_balance_c': 0, 'phase': 'live', 'money_type': 'live', 'rules': {}},
   [T('2026-10-01', 1500, 1), T('2026-10-02', -400, 2)], {'thr': 0, 'buffer': 110000, 'dd': 110000, 'breached': False}),
  ('Live without rules, $25,000 deposited, −800: room = balance $24,200', {'starting_balance_c': 2500000, 'phase': 'live', 'money_type': 'live', 'rules': {}},
   [T('2026-10-01', -800, 1)], {'thr': 0, 'buffer': 2420000, 'breached': False}),
  ('Live without rules, starting at $0, first trade −300: room $0, never negative', {'starting_balance_c': 0, 'phase': 'live', 'money_type': 'live', 'rules': {}},
   [T('2026-10-01', -300, 1)], {'buffer': 0, 'breached': False}),
  ('Topstep Live with its fixed floor: the firm rules are kept', {'starting_balance_c': 1000000, 'phase': 'live', 'money_type': 'live', 'rules': {'dd_c': 900000, 'dd_type': 'static', 'dd_lock': True, 'dd_floor_c': 100000}},
   [T('2026-10-01', 2000, 1)], {'thr': 100000, 'buffer': 1100000, 'breached': False}),
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
    print('— 1. the maths (acctState)')
    for name, acc, trades, want in CASES:
      got = await pg.evaluate("""([acc, trades]) => { const keep = [S.trades, S.payouts];
        S.trades = trades; S.payouts = [];
        try { const r = acctState(Object.assign({ id: 'acc' }, acc)); return { thr: r.thr, buffer: r.buffer == null ? null : Math.max(0, r.buffer), dd: r.dd, breached: r.breached }; }
        finally { [S.trades, S.payouts] = keep; } }""", [acc, trades])
      bad = {k: (v, got.get(k)) for k, v in want.items() if got.get(k) != v}
      ok(not bad, name + (f'  {bad}' if bad else ''))
    print('— 2. the same room on every screen')
    await pg.evaluate("""(()=>{const fid=(S.accounts[0]||{}).firm_id||'';
      put('accounts',{id:'dk-fun',firm_id:fid,name:'DK Funded 50K',starting_balance_c:5000000,status:'active',phase:'funded',money_type:'funded',rules:{dd_c:200000,dd_type:'eod',dd_lock:true}});
      put('accounts',{id:'dk-live',firm_id:fid,name:'DK Live',starting_balance_c:0,status:'active',phase:'live',money_type:'live',rules:{}});
      [['2026-10-01',300000],['2026-10-02',300000]].forEach(([d,c],i)=>put('trades',{id:'dk-f'+i,account_id:'dk-fun',date:d,session_date:true,entry_time:'10:00:00',exit_time:'10:10:00',instrument:'NQ',direction:'long',contracts:1,pnl_c:c,pnl_manual:true}));
      [['2026-10-01',150000],['2026-10-02',-40000]].forEach(([d,c],i)=>put('trades',{id:'dk-l'+i,account_id:'dk-live',date:d,session_date:true,entry_time:'10:00:00',exit_time:'10:10:00',instrument:'NQ',direction:'long',contracts:1,pnl_c:c,pnl_manual:true}));
    })()"""); await pg.wait_for_timeout(1500)
    sp = lambda s: re.sub(r'[\s  ]+', ' ', s or '')
    for aid, room in (('dk-fun', '6 000 $'), ('dk-live', '1 100 $')):
      await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
      today = sp(await pg.evaluate(f"(document.querySelector('#main .nav-acc[href=\"#account/{aid}\"] .nav-acc-dd')||{{}}).innerText||''"))
      ok(today.endswith(room), f'{aid} Today: « {today} » (expects {room})')
      await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
      row = sp(await pg.evaluate(f"(document.querySelector('#main [data-href=\"#account/{aid}\"]')||{{}}).innerText||''"))
      ok(('Marge DD ' + room) in row, f'{aid} Accounts list: « Marge DD {room} » ({row[:90]})')
      await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(1600)
      page = await pg.evaluate("(()=>{const r=[...document.querySelectorAll('#main .rule')].find(x=>/Marge de drawdown/.test(x.textContent)); return r?r.querySelector('b').textContent:''})()")
      ok(sp(page).strip() == room, f'{aid} account page: « Marge de drawdown {sp(page).strip()} » (expects {room})')
    await pg.evaluate("""(()=>{['dk-f0','dk-f1','dk-l0','dk-l1'].forEach(id=>remove('trades',id)); ['dk-fun','dk-live'].forEach(id=>remove('accounts',id));})()"""); await pg.wait_for_timeout(1200)
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
