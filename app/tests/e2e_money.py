"""
Sweep — money: performance, progress and real money never mixed (dev environment with Playwright).
  python3 tests/e2e_money.py http://127.0.0.1:8095
A new trader is created with the mandatory scenario:
  Apex Éval A (eval, passed) +3,200 · Apex Éval B (eval, failed) −2,100 · Topstep Combine (eval, running) +900
  Apex Funded from A (funded) +4,000 · Topstep Live (live) +1,000
  Payouts: Apex Funded $2,000 gross, split 100 %, fees 0, paid · $1,500 requested
  Expenses: 2 Apex evaluations $100, activation $85, Combine $49/month for 2 months → $383
Expected: performance +7,000 (never labelled money) · Eval +2,000 simulated · Funded +4,000 simulated · Live +1,000 real ·
net real +2,617 · prop ROI 422 % · evaluations passed 50 % · cost to get a funded account $383 · no « 7 000 » next to a money label.
Also: the monthly Combine stops when the account is passed · a negative refund lowers expenses · a denied payout counts 0 ·
a trade copied on 3 accounts counts once in performance and 3 times in Accounts · migration + « Classify your accounts » once.
"""
import asyncio, sys, random, re, datetime
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def ago(n): return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()
SCEN = """async (d) => {
  const F1 = 'f-apex', F2 = 'f-ts';
  put('firms', { id: F1, name: 'Apex' }); put('firms', { id: F2, name: 'Topstep' });
  const A = (id, firm, name, mt, extra) => put('accounts', Object.assign({ id, firm_id: firm, name, starting_balance_c: 5000000, status: 'active', created_on: d.a40, money_type: mt, phase: mt }, extra || {}));
  A('evA', F1, 'Apex Éval A', 'eval', { rules: { target_c: 300000, dd_c: 250000 }, status: 'archived', result: 'passed' });
  A('evB', F1, 'Apex Éval B', 'eval', { rules: { target_c: 300000, dd_c: 250000 }, status: 'archived', result: 'failed' });
  A('comb', F2, 'Topstep Combine', 'eval', { rules: { target_c: 300000, dd_c: 200000 } });
  A('fun', F1, 'Apex PA', 'funded', { rules: { dd_c: 250000, payout_min_c: 50000 }, from_eval: 'evA', created_on: d.a30 });
  A('live', F2, 'Topstep Live', 'live', { rules: {} });
  const T = (id, acc, pnl, date) => put('trades', { id, account_id: acc, instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: pnl, pnl_manual: true, date, entry_time: '10:00', exit_time: '10:05', session_date: true });
  T('t1', 'evA', 320000, d.a35); T('t2', 'evB', -210000, d.a34); T('t3', 'comb', 90000, d.t); T('t4', 'fun', 400000, d.a10); T('t5', 'live', 100000, d.t);
  put('payouts', { id: 'p1', account_id: 'fun', firm_id: F1, gross_c: 200000, split_pct: 100, fees_c: 0, net_c: 200000, amount_c: 200000, status: 'paid', paid_on: d.a5, payment_date: d.a5, request_date: d.a7 });
  put('payouts', { id: 'p2', account_id: 'fun', firm_id: F1, gross_c: 150000, split_pct: 100, fees_c: 0, net_c: 150000, amount_c: 150000, status: 'requested', request_date: d.a2 });
  const E = (id, acc, firm, cat, c, date, extra) => put('expenses', Object.assign({ id, account_id: acc, firm_id: firm, category: cat, amount_c: c, date }, extra || {}));
  E('e1', 'evA', F1, 'evaluation', 10000, d.a40); E('e2', 'evB', F1, 'evaluation', 10000, d.a39); E('e3', 'fun', F1, 'activation', 8500, d.a30);
  E('e4', 'comb', F2, 'subscription', 4900, d.m1, { recurring: 'monthly' });
  await new Promise((r) => setTimeout(r, 2500));
}"""
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    u = 'mny%d' % random.randint(10000, 99999)
    rq = await p.request.new_context(base_url=B)
    r = await rq.post('/api/auth/register', data={'username': u, 'password': 'Testpass123!', 'email': u + '@t.dev', 'consent': True, 'elapsed': 6000}, headers=H)
    assert r.status == 201, await r.text()
    await rq.post('/api/me/profile', data={'first_name': 'Test', 'last_name': 'Money', 'username': u}, headers=H)
    st = await rq.storage_state()
    ctx = await br.new_context(viewport={'width': 1440, 'height': 900}, locale='fr-CA', storage_state=st)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    today = await pg.evaluate('todayStr()')
    t0 = datetime.date.fromisoformat(today)
    def a(n): return (t0 - datetime.timedelta(days=n)).isoformat()
    m1 = (t0.replace(day=1) - datetime.timedelta(days=1)).replace(day=min(t0.day, 28)).isoformat()   # one month ago: the server adds this month's charge
    await pg.evaluate(SCEN, {'t': today, 'a40': a(40), 'a39': a(39), 'a35': a(35), 'a34': a(34), 'a30': a(30), 'a10': a(10), 'a7': a(7), 'a5': a(5), 'a2': a(2), 'm1': m1})
    await pg.goto(B + '/?x=2#dashboard'); await pg.wait_for_timeout(3000)   # reload: the server adds the second month of the Combine
    m = await pg.evaluate("(()=>{const m=SweepMoney.moneyOf({}); return {perf:m.perf.total, by:m.perf.byType, real:m.real, roi:m.roiProp, ind:m.ind, nexp:(S.expenses||[]).length}})()")
    ok(m['perf'] == 700000, f"performance +7,000 ({m['perf']})")
    ok(m['by']['eval'] == 200000 and m['by']['funded'] == 400000 and m['by']['live'] == 100000, f"Eval +2,000 · Funded +4,000 · Live +1,000 ({m['by']})")
    ok(m['real']['payouts'] == 200000 and m['real']['pending'] == 150000 and m['real']['expenses'] == 38300 and m['real']['net'] == 261700, f"paid 2,000 · pending 1,500 · expenses 383 · net real +2,617 ({m['real']}, {m['nexp']} expenses)")
    ok(m['roi'] is not None and round(m['roi'] * 100) == 422, f"prop ROI 422 % ({m['roi']})")
    ok(m['ind']['passRate'] == 0.5 and m['ind']['costPerFunded'] == 38300, f"evaluations passed 50 % · cost to get a funded account $383 ({m['ind']})")
    # screens
    shots = {}
    async def go(h, name):
      await pg.evaluate(f"location.hash='{h}'"); await pg.wait_for_timeout(1800); shots[name] = await pg.evaluate("document.getElementById('main').innerText")
    await pg.evaluate("U.mper='all'; saveU()")
    await pg.evaluate("U.mview = 'analysis'")   # « My money » → Analysis: net real, ROI, indicators (« My entries » holds the lists)
    await go('#payouts', 'money'); await pg.evaluate("U.mview = 'entries'"); await go('#accounts', 'accounts'); await go('#analytics', 'stats'); await go('#dashboard', 'today')
    ok('2\u202f617' in shots['money'] and '422 %' in shots['money'] and '50 %' in shots['money'], 'My money shows net real +2,617, ROI 422 %, passed 50 %')
    ok(all(g in shots['accounts'] for g in ['LIVE', 'FINANCÉS', 'ÉVALUATIONS']) or all(g.lower() in shots['accounts'].lower() for g in ['Live', 'Financés', 'Évaluations']), 'Accounts grouped Live / Funded / Evaluations')
    ok('Réel' in shots['today'] and 'Mon argent' in shots['today'], 'Today: « My money » card with « Real »')
    # no « 7 000 » next to a money label, on the main pages
    bad = []
    for h in ['#dashboard', '#trades', '#analytics', '#accounts', '#payouts', '#calendar', '#journal', '#news', '#settings', '#progress', '#import', '#account/fun', '#account/live', '#trade/t4', '#plan']:
      await pg.evaluate(f"location.hash='{h}'"); await pg.wait_for_timeout(1300)
      bad += await pg.evaluate("""(h)=>[...document.querySelectorAll('#main *')].filter(e=>e.children.length===0&&/7[\\u202f\\u00a0 ,.]?000/.test(e.textContent)&&e.getClientRects().length).filter(e=>{const c=e.closest('.surface, .nav-card, section'); return c&&/(Gagné|Revenu|Net réel|Mon argent)/.test(c.innerText)}).map(e=>h+': '+e.textContent.trim().slice(0,30))""", h)
    ok(not bad, f'no « 7 000 » next to a money label on 15 pages ({bad[:3]})')
    # the monthly Combine stops when the account is passed
    await pg.evaluate("editDoc('accounts','comb',d=>{d.result='passed'})"); await pg.wait_for_timeout(1200)
    await pg.goto(B + '/?x=3#payouts'); await pg.wait_for_timeout(2500)
    end = await pg.evaluate("(getDoc('expenses','e4')||{}).recurring_end||''")
    ok(bool(end), f'the monthly Combine stops when the account is passed (recurring_end {end})')
    # refund, denied payout
    await pg.evaluate("put('expenses',{id:'e5',account_id:'evB',firm_id:'f-apex',category:'evaluation',amount_c:-5000,date:todayStr()}); put('payouts',{id:'p3',account_id:'fun',firm_id:'f-apex',gross_c:99900,net_c:99900,amount_c:99900,status:'rejected',request_date:todayStr()})"); await pg.wait_for_timeout(800)
    m2 = await pg.evaluate("(()=>{const m=SweepMoney.moneyOf({}); return m.real})()")
    ok(m2['expenses'] == 33300 and m2['payouts'] == 200000 and m2['pending'] == 150000, f'a refund lowers expenses (−50), a denied payout counts 0 ({m2})')
    # copy on 3 accounts
    await pg.evaluate("""(()=>{['c1','c2','c3'].forEach((id,i)=>put('accounts',{id,firm_id:'f-ts',name:'Copy '+i,starting_balance_c:5000000,status:'active',money_type:'eval',rules:{target_c:300000}})); ['c1','c2','c3'].forEach((a,i)=>put('trades',{id:'cp'+i,account_id:a,copy_group:'g1',instrument:'NQ',direction:'long',contracts:1,entry:1,exit:2,pnl_c:50000,pnl_manual:true,date:todayStr(),entry_time:'11:00',exit_time:'11:05',session_date:true,created_at:'2026-01-0'+(i+1)}))})()"""); await pg.wait_for_timeout(1000)
    c = await pg.evaluate("(()=>{const m=SweepMoney.moneyOf({}); const per=m.accounts.filter(a=>['c1','c2','c3'].includes(a.id)).map(a=>a.net); return {perf:m.perf.total, per}})()")
    ok(c['perf'] == 750000 and c['per'] == [50000, 50000, 50000], f'a copied trade: once in performance (+500), three times in Accounts ({c})')
    # migration: an account without type, then « Classify your accounts » once
    await pg.evaluate("put('accounts',{id:'old1',firm_id:'f-ts',name:'Old one',starting_balance_c:5000000,status:'active',rules:{target_c:300000}}); put('accounts',{id:'old2',firm_id:'f-ts',name:'Unknown one',starting_balance_c:5000000,status:'active',rules:{},preset:'x',created_at:'2026-01-02T00:00:00Z'})"); await pg.wait_for_timeout(800)
    await pg.goto(B + '/?x=4#dashboard'); await pg.wait_for_timeout(3500)
    mt = await pg.evaluate("[getDoc('accounts','old1').money_type, getDoc('accounts','old2').money_type||null, !!document.querySelector('aside.mny-cls')]")
    ok(mt[0] == 'eval' and mt[1] is None and mt[2], f'migration: target → eval, unknown → « Classify your accounts » window ({mt})')
    if mt[2]:
      await pg.evaluate("document.querySelectorAll('#gSheet.open [data-g=close], .evp.open [data-act=close]').forEach(b=>b.click())"); await pg.wait_for_timeout(400)
      await pg.evaluate("(()=>{const a=document.querySelector('aside.mny-cls'); a.querySelector('[data-cls=personal]').click(); a.querySelector('[data-cls-done]').click();})()"); await pg.wait_for_timeout(1500)
    await pg.goto(B + '/?x=5#dashboard'); await pg.wait_for_timeout(3500)
    ok(await pg.locator('aside.mny-cls').count() == 0 and await pg.evaluate("getDoc('accounts','old2').money_type") == 'personal', 'the window appears only once, the choice is kept')
    # the Stats type filter never hides trades elsewhere: with « Live » chosen in Stats, Trades still lists every trade
    await pg.evaluate("U.mtype='live'; saveU(); F.period='all'; saveF(); location.hash='#trades'"); await pg.wait_for_timeout(1800)
    rows = await pg.evaluate("document.querySelectorAll('#main tr[data-href^=\"#trade/\"], #main .trow, #main [data-href^=\"#trade/\"]').length")
    empty = await pg.evaluate("/No trades match|Aucun trade ne correspond|Ningún trade coincide/.test(document.getElementById('main').innerText)")
    active = await pg.evaluate("!!document.querySelector('#main .mny-tseg [data-mtype=live].on')")
    ok(rows >= 1 and not empty and active, f'with « Live » chosen, Trades shows the live trades and says so (selector on « Live », {rows} rows)')
    await pg.evaluate("location.hash='#calendar'"); await pg.wait_for_timeout(1200)
    # 14 (lot A, 9 Oct): the Calendar shows the same selector and follows it — never a hidden filter
    sel = await pg.evaluate("!!document.querySelector('#main .mny-tseg [data-mtype=live].on')")
    shown = await pg.evaluate("(()=>{const mo=todayStr().slice(0,7); return S.trades.filter(t=>t.date&&t.date.startsWith(mo)&&acctOK(t)).length})()")
    live = await pg.evaluate("(()=>{const mo=todayStr().slice(0,7); return S.trades.filter(t=>t.date&&t.date.startsWith(mo)&&moneyTypeOf(S.accounts.find(a=>a.id===t.account_id))==='live').length})()")
    ok(sel and shown == live, f'Calendar shows the « Live » selector and only the live trades of the month ({shown} = {live})')
    await pg.evaluate("U.mtype='all'; saveU()")
    # change an account's type in place (it was funded, not an evaluation): trades, rules and stats unchanged
    before = await pg.evaluate("[S.trades.filter(t=>t.account_id==='comb').length, JSON.stringify(getDoc('accounts','comb').rules), SweepMoney.moneyOf({}).perf.total]")
    await pg.evaluate("location.hash='#account/comb'"); await pg.wait_for_timeout(1500)
    await pg.locator('#main [data-acc-type=funded]').click(); await pg.wait_for_timeout(1200)
    after = await pg.evaluate("[S.trades.filter(t=>t.account_id==='comb').length, JSON.stringify(getDoc('accounts','comb').rules), SweepMoney.moneyOf({}).perf.total, getDoc('accounts','comb').money_type, getDoc('accounts','comb').phase, !!document.querySelector('#main [data-acc-type=funded].on')]")
    ok(after[:3] == before and after[3] == 'funded' and after[4] == 'funded' and after[5], f'account type changed in place (Evaluation → Funded): same trades, rules and performance ({after})')
    await pg.evaluate("editDoc('accounts','comb',d=>{d.money_type='eval'; d.phase='eval'})"); await pg.wait_for_timeout(600)
    # one account-type selector, shown wherever it applies: Today, Trades, Stats, My money
    shown = {}
    for h in ['#dashboard', '#trades', '#analytics', '#payouts']:
      await pg.evaluate(f"location.hash='{h}'"); await pg.wait_for_timeout(1500)
      shown[h] = await pg.evaluate("document.querySelectorAll('#main .mny-tseg [data-mtype]').length")
    ok(all(v == 5 for v in shown.values()), f'the account-type selector is on Today, Trades, Stats and My money ({shown})')
    await pg.evaluate("location.hash='#payouts'"); await pg.wait_for_timeout(1200)
    await pg.locator('#main .mny-tseg [data-mtype=live]').first.click(); await pg.wait_for_timeout(1200)
    live = await pg.evaluate("[U.mtype, SweepMoney.moneyOf({mtype:'live'}).real]")
    ok(live[0] == 'live' and live[1]['payouts'] == 0 and live[1]['live'] == 100000 and live[1]['expenses'] == 0, f'My money, « Live » only: the live account’s real P&L, no evaluation payouts or expenses ({live})')
    await pg.evaluate("U.mtype='all'; saveU()")
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
