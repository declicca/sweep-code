"""
Sweep — accuracy (points A2 to A6), dev environment with Playwright:
  python3 tests/e2e_accuracy.py http://127.0.0.1:8095 /tmp/show_state.json
 A2 an evening trade shows « séance du 8 oct. · entré le 7 à 23:36 », never « 8 oct. 23:36 » alone;
 A3 Topstep 50K +$2,000 then +$1,000 → not passed (consistency); TPT 50K +$3,000 in one day → not passed; the status says
    what is missing (« Objectif atteint · il manque : consistance 67 % (max 55 %) / 1 jour sur 3 ») and « Move to funded » is not offered;
 A4 Apex EOD 50K funded, +$2,500, payout $1,500, −$1,050 → drawdown exceeded (balance after withdrawals vs threshold);
 A5 an exceeded account: gold « Drawdown dépassé » on Today and in Accounts, room « $0 », at the bottom of the list;
 A6 Rithmic file with two accounts → two Sweep accounts, one copy group, never merged; no fees → « fees not included »;
    a file without fees on an account with a commission per contract → that commission is applied, no warning.
"""
import asyncio, sys, re
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

SETUP = """async () => {
  const fid = 'fx' + Date.now(); put('firms', { id: fid, name: 'Test Firm' });
  const mk = (id, name, pv, start, phase) => { const r = SweepPresets.rulesOf(pv); put('accounts', { id, firm_id: fid, name, starting_balance_c: start * 100, status: 'active', created_on: '2026-09-01', phase, preset: pv, rules: r.rules }); };
  const tr = (acc, date, pnl, time) => put('trades', { id: 'acc-' + acc + date + pnl, account_id: acc, instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: pnl * 100, pnl_manual: true, date, entry_time: time || '10:00', exit_time: '10:05', session_date: true });
  await SweepPresets.load(); await new Promise(r => setTimeout(r, 900));
  mk('t-ts', 'TS Combine 50K', 'topstep|combine|50000|eval|', 50000, 'eval'); tr('t-ts', '2026-10-01', 2000); tr('t-ts', '2026-10-02', 1000);
  mk('t-tpt', 'TPT Test 50K', 'tpt|tpt-test|50000|eval|', 50000, 'eval'); tr('t-tpt', '2026-10-01', 3000);
  mk('t-apx', 'APX PA 50K', 'apex|apex-eod|50000|funded|', 50000, 'funded'); tr('t-apx', '2026-10-01', 2500);
  put('payouts', { id: 'p-apx', account_id: 't-apx', amount_c: 150000, status: 'paid', request_date: '2026-10-02', approval_date: '2026-10-02', payment_date: '2026-10-02' });
  tr('t-apx', '2026-10-05', -1050);
  put('trades', { id: 'acc-eve', account_id: 't-apx', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 100, pnl_manual: true, date: '2026-10-08', entry_time: '23:36', exit_time: '23:40', session_date: true, executions: [{ id: 'e1', side: 'buy', qty: 1, price: 1, t: '2026-10-07 23:36:00' }, { id: 'e2', side: 'sell', qty: 1, price: 2, t: '2026-10-07 23:40:00' }] });
  await new Promise(r => setTimeout(r, 1500));
}"""
CLEAN = """async () => { for (const id of ['t-ts', 't-tpt', 't-apx', 't-r1', 't-r2', 't-r3']) { S.trades.filter(t => t.account_id === id).forEach(t => remove('trades', t.id)); if (getDoc('accounts', id)) remove('accounts', id); } if (getDoc('payouts', 'p-apx')) remove('payouts', 'p-apx'); await new Promise(r => setTimeout(r, 1200)); }"""
RITHMIC = ('Completed Orders\\nAccount,Status,Remarks,Buy/Sell,Qty To Fill,Symbol,Qty Filled,Avg Fill Price,Limit Price,Order Number,Create Time,Update Time,Commission\\n'
           'APEX-111,Filled,,B,0,NQZ6,1,24900,24900,1,2026-10-02 10:00:00,2026-10-02 10:00:00,\\nAPEX-111,Filled,,S,0,NQZ6,1,24910,24910,2,2026-10-02 10:05:00,2026-10-02 10:05:00,\\n'
           'APEX-222,Filled,,B,0,NQZ6,1,24900,24900,3,2026-10-02 10:00:01,2026-10-02 10:00:01,\\nAPEX-222,Filled,,S,0,NQZ6,1,24910,24910,4,2026-10-02 10:05:01,2026-10-02 10:05:01,\\n')

async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(viewport={'width': 1280, 'height': 900}, locale='fr-CA', storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    await pg.goto(B + '/?x=1#trades'); await pg.wait_for_timeout(2500)
    await pg.evaluate(CLEAN); await pg.evaluate(SETUP)
    # A2
    await pg.evaluate("location.hash='#trade/acc-eve'"); await pg.wait_for_timeout(1500)
    txt = await pg.evaluate("document.getElementById('main').innerText")
    ok('séance du' in txt and 'entré le 7 à 23:36' in txt, 'A2 trade page: « séance du 8 oct. · entré le 7 à 23:36 »')
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1500)
    row = await pg.evaluate("(()=>{const r=document.querySelector('#main [data-href=\"#trade/acc-eve\"]'); return r?r.innerText.replace(/\\s+/g,' '):''})()")
    ok('23:36' in row and ('le 7' in row or 'entré' in row), f'A2 trades list: the clock time says it was the 7th ({row[:90]})')
    # A3
    for aid, name, miss in [('t-ts', 'Topstep 50K +2,000 then +1,000', ['consistance 67\u202f% (max 55\u202f%)']), ('t-tpt', 'TPT 50K +3,000 in one day', ['consistance 100\u202f% (max 50\u202f%)', '1 jour sur 3'])]:
      st = await pg.evaluate(f"(()=>{{const s=acctState(getDoc('accounts','{aid}')); return {{passed:s.passed, reached:s.reached, label:s.label, status:s.status}}}})()")
      ok(st['reached'] and not st['passed'] and 'Objectif atteint · il manque : ' in st['label'] and all(m in st['label'] for m in miss), f"A3 {name}: not passed, « {st['label']} » (expects {miss})")
      await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(1400)
      ok(await pg.locator('#main [data-pass-btn]').count() == 0, f'A3 {name}: no « Move to funded » button')
    # A4
    st = await pg.evaluate("(()=>{const s=acctState(getDoc('accounts','t-apx')); return {breached:s.breached, bal:s.bal, thr:s.thr, label:s.label}})()")
    ok(st['breached'] and st['bal'] == 4995100 and st['thr'] == 5010000,   # 4,995,100 = +2,500 −1,500 −1,050 and the +$1 evening trade (A2)
        f"A4 Apex: balance after payout $49,950 ≤ threshold $50,100 → exceeded ({st})")
    # A5
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1800)
    card = await pg.evaluate("(()=>{const a=document.querySelector('#main .nav-acc[href=\"#account/t-apx\"]'); return a?a.innerText.replace(/\\s+/g,' '):''})()")
    ok('Drawdown dépassé' in card and not re.search(r'−\$|-\$|−\d', card), f'A5 Today: gold « Drawdown dépassé », room never negative ({card[:120]})')
    order = await pg.evaluate("[...document.querySelectorAll('#main .nav-acc')].map(a=>a.getAttribute('href'))")
    ok(order and order[-1] == '#account/t-apx', 'A5 Today: the exceeded account is at the bottom')
    await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1800)
    rows = await pg.evaluate("[...document.querySelectorAll('#main tr[data-href^=\"#account/\"]')].map(r=>[r.dataset.href, r.innerText.replace(/\\s+/g,' ')])")
    apx = [r for r in rows if r[0] == '#account/t-apx']
    ok(apx and 'Drawdown dépassé' in apx[0][1] and ('Marge DD $0' in apx[0][1] or 'Marge DD 0\u00a0$' in apx[0][1] or 'Marge DD 0 $' in apx[0][1]), f"A5 Accounts list: label + « Marge DD $0 » ({apx[0][1][:110] if apx else ''})")
    flagged = [i for i, r in enumerate(rows) if 'Drawdown dépassé' in r[1]]
    tables = await pg.evaluate("[...document.querySelectorAll('#main table')].map(t=>[...t.querySelectorAll('tr[data-href^=\"#account/\"]')].map(r=>r.innerText.includes('Drawdown dépassé')?1:0))")
    good = all(fl == sorted(fl) for fl in tables if fl)   # in each table: every exceeded account after the others
    ok(flagged and good, f'A5 Accounts list: exceeded accounts at the bottom ({tables})')
    ok(not await pg.evaluate("[...document.querySelectorAll('#main tr.total')].length"), 'A13 no « All accounts » total row')
    # A5b: exceeded, then back above the threshold → still exceeded, the room stays « 0 $ » with an empty bar (account page)
    await pg.evaluate("put('trades',{id:'t-apx-up',account_id:'t-apx',date:'2026-10-06',session_date:true,entry_time:'10:00:00',exit_time:'10:10:00',instrument:'NQ',direction:'long',contracts:1,pnl_c:300000,pnl_manual:true})")
    await pg.evaluate("location.hash='#account/t-apx'"); await pg.wait_for_timeout(1600)
    room = await pg.evaluate("""(()=>{const s=acctState(getDoc('accounts','t-apx')); const l=[...document.querySelectorAll('#main .rule')].find(r=>/Marge de drawdown/.test(r.textContent)); if(!l) return null; const i=l.querySelector('.pbar i'); return [s.breached, s.buffer>0, l.querySelector('b').textContent.replace(/\\s+/g,' ').trim(), i?parseFloat(i.style.width):null]})()""")
    ok(room and room[0] and room[1] and room[2] in ('0 $', '0\u00a0$', '$0') and room[3] == 0, f'A5b exceeded then back above the threshold: account page room « 0 $ », bar empty ({room})')
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1600)
    tbar = await pg.evaluate("""(()=>{const a=document.querySelector('#main .nav-acc[href="#account/t-apx"]'); const i=a&&a.querySelector('.nav-acc-dd s'); return a?[a.querySelector('.nav-acc-dd small').textContent.replace(/\\s+/g,' '), i?parseFloat(i.style.width):null]:null})()""")
    ok(tbar and tbar[0].endswith('0 $') and tbar[1] == 0, f'A5b Today: room « 0 $ » and an empty bar ({tbar})')
    await pg.evaluate("remove('trades','t-apx-up')"); await pg.wait_for_timeout(600)
    # A6
    await pg.evaluate("""(()=>{const fid=getDoc('accounts','t-apx').firm_id; put('accounts',{id:'t-r1',firm_id:fid,name:'Copy APEX-111',starting_balance_c:5000000,status:'active',rules:{}}); put('accounts',{id:'t-r2',firm_id:fid,name:'Copy APEX-222',starting_balance_c:5000000,status:'active',rules:{}});})()""")
    await pg.wait_for_timeout(800)
    await pg.evaluate("location.hash='#import'"); await pg.wait_for_timeout(1200)
    await pg.evaluate(f"(()=>{{IMP.rows=parseTradovate('{RITHMIC}'); IMP.file='r.csv'; IMP.account='t-r1'; render();}})()"); await pg.wait_for_timeout(800)
    sel = await pg.evaluate("[...document.querySelectorAll('#main [data-imap]')].map(s=>s.dataset.imap+'→'+s.value)")
    ok(sorted(sel) == ['APEX-111→t-r1', 'APEX-222→t-r2'], f'A6 Rithmic: each account of the file → its Sweep account ({sel})')
    nofee = await pg.evaluate("!!document.querySelector('#main .ux-inofee')")
    ok(nofee, 'A6 no fees in the file nor on the account → « fees not included »')
    await pg.evaluate("void impGo()"); await pg.wait_for_timeout(3000)
    imp = await pg.evaluate("S.trades.filter(t=>t.account_id==='t-r1'||t.account_id==='t-r2').map(t=>[t.account_id,t.copy_group,t.session_date])")
    ok(len(imp) == 2 and imp[0][0] != imp[1][0] and imp[0][1] and imp[0][1] == imp[1][1] and all(x[2] for x in imp), f'A6 two trades on two accounts, one copy group, never merged ({imp})')
    # A6b: no fees in the file, a commission per contract on the account → applied (round trip × contracts), no warning
    await pg.evaluate("""(()=>{const fid=getDoc('accounts','t-apx').firm_id; put('accounts',{id:'t-r3',firm_id:fid,name:'Fees APEX-333',starting_balance_c:5000000,status:'active',fee_rt_c:250,rules:{}});})()""")
    await pg.wait_for_timeout(800)
    FEE = 'Completed Orders\\nAccount,Status,Remarks,Buy/Sell,Qty To Fill,Symbol,Qty Filled,Avg Fill Price,Limit Price,Order Number,Create Time,Update Time,Commission\\nAPEX-333,Filled,,B,0,NQZ6,2,21000,21000,31,2026-10-02 10:00:00,2026-10-02 10:00:00,0\\nAPEX-333,Filled,,S,0,NQZ6,2,21010,21010,32,2026-10-02 10:05:00,2026-10-02 10:05:00,0\\n'
    await pg.evaluate(f"(()=>{{IMP.rows=parseTradovate('{FEE}'); IMP.file='f.csv'; IMP.account='t-r3'; render();}})()"); await pg.wait_for_timeout(800)
    warn = await pg.evaluate("!!document.querySelector('#main .ux-inofee')")
    await pg.evaluate("void impGo()"); await pg.wait_for_timeout(3000)
    fee = await pg.evaluate("S.trades.filter(t=>t.account_id==='t-r3').map(t=>[t.contracts,t.fees_c,!!t.fees_auto])")
    ok(not warn and fee == [[2, 500, True]], f'A6b commission of the account ($2.50 × 2 contracts) applied, no « fees not included » (warning: {warn}, trades: {fee})')
    # A7 instruments
    r7 = await pg.evaluate("[PV('6E')*0.001, PV('ZN')*0.5, PV('MBT')*100, instOf('XYZ').tickC, !!instOf('XYZ').unknown, PV('SIL')*0.1, PV('NG')*0.01, PV('HG')*0.01, PV('M6E')*0.001, PV('MET')*10, PV('ZB')*1, PV('SI')*0.1]")
    ok(r7[:3] == [12500, 50000, 1000] and r7[3] == 0 and r7[4], f'A7 6E 1.0800→1.0810 = $125, ZN ½ pt = $500, MBT 100 pts = $10; unknown symbol: no point value ({r7[:5]})')
    ok(all(x > 0 for x in r7[5:]), 'A7 SIL, NG, HG, M6E, MET, ZB, SI are priced')
    unk = await pg.evaluate("parseTradovate('Completed Orders\\nAccount,Status,Remarks,Buy/Sell,Qty To Fill,Symbol,Qty Filled,Avg Fill Price,Limit Price,Order Number,Create Time,Update Time,Commission\\nA,Filled,,B,0,XYZZ6,1,10,10,1,2026-10-02 10:00:00,2026-10-02 10:00:00,1\\nA,Filled,,S,0,XYZZ6,1,11,11,2,2026-10-02 10:05:00,2026-10-02 10:05:00,1\\n').map(r=>[r.inst,r.unknown,r.pnl_c])")
    ok(unk == [['XYZ', True, 0]], f'A7 unknown symbol in an import: never priced as NQ, P&L to type ({unk})')
    # A8 presets
    cat = await pg.evaluate("fetch('api/presets').then(r=>r.json())")
    names = [f['name'] for f in cat['firms']]
    ok('Tradeify' not in names and 'Alpha Futures' not in names, f'A8 empty firms are not offered ({names})')
    rap = await pg.evaluate("SweepPresets.rulesOf('mffu|mffu-rapid-eod|50000|funded|').rules")
    ok(rap['payout_min_c'] == 50000 and rap['payout_min_bal_c'] == 5210000, 'A8 MFFU Rapid EOD 50K funded: payout rules ($500 minimum, balance to keep)')
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await pg.evaluate(CLEAN)
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
