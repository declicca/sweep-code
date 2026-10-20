"""
Sweep — from an evaluation to its funded account (Playwright, phone, a trader of its own):
  python3 tests/e2e_eval_to_funded.py http://127.0.0.1:8095
The account form asks « Evaluation, funded or live account? » first, nothing left to choose at the end; an Apex funded
account and a Topstep Combine get their catalogue rules; the Combine at its target → « You passed » once (« Not yet »: not
again today); the account page offers « Move to funded »; moving creates the funded account (its own rules) and archives
the evaluation as passed, linked to it. No page error. (16 Oct.: checks, it only printed.)
"""
import asyncio, datetime, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,9,20,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    u='ps%d'%random.randint(1000,9999)
    await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
    # the profile is asked before the first account (since 2026-10-06): filled here so the « Complete your profile » window does not cover the page
    await ctx.request.post(B+'/api/me/profile', data={'first_name':'Test','last_name':'Trader','username':u}, headers={'X-Requested-With':'fetch'})
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
    await pg.evaluate("put('accounts',{id:'a-seed',name:'Perso',firm_id:'',starting_balance_c:1000000,status:'active'})"); await pg.wait_for_timeout(1000)
    async def add(phase, firm, size_idx, name):
      await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
      b=pg.locator('#main [data-act=acct-add]').first
      await b.click(); await pg.wait_for_timeout(900)
      st=pg.locator('form[data-form=account] .ux-st')
      q=await st.locator('.ux-st-q').first.inner_text()
      await st.locator(f'[data-st-ph0={phase}]').click(); await pg.wait_for_timeout(300)
      await st.locator(f'[data-st-firm="{firm}"]').click(); await pg.wait_for_timeout(300)
      if await st.locator('[data-st-type]').count(): await st.locator('[data-st-type]').first.click(); await pg.wait_for_timeout(300)
      if await st.locator('[data-st-size]').count(): await st.locator('[data-st-size]').nth(size_idx).click(); await pg.wait_for_timeout(300)
      phases=await st.locator('[data-st-phase]').count()
      nm=pg.locator('form[data-form=account] [name=name]'); await nm.fill(name)
      await pg.locator('form[data-form=account] [type=submit]').click(); await pg.wait_for_timeout(1500)
      a=await pg.evaluate(f"(()=>{{const a=S.accounts.find(x=>x.name==='{name}'); return a?{{id:a.id,phase:a.phase,preset:a.preset,target:a.rules&&a.rules.target_c,win:a.rules&&a.rules.payout_win_days,bal:a.starting_balance_c}}:null}})()")
      return q, phases, a
    q,ph,a=await add('funded','apex',1,'Apex PA 50K')
    ok('simulation' in q.lower() and 'live' in q and ph == 0, f'the first question: {q!r}, nothing left to choose at the end ({ph})')
    ok(a and a['phase'] == 'funded' and (a['preset'] or '').startswith('apex|') and a['preset'].endswith('|funded|') and a['win'], f'Apex funded: its catalogue rules ({a})')
    await pg.evaluate("closeTicket && closeTicket()"); await pg.wait_for_timeout(400)
    q,ph,ev=await add('eval','topstep',0,'Combine 50K')
    ok(ev and ev['phase'] == 'eval' and ev['preset'] == 'topstep|combine|50000|eval|' and ev['target'] == 300000, f'Topstep Combine 50K: target $3,000 ({ev})')
    await pg.evaluate("closeTicket && closeTicket()"); await pg.wait_for_timeout(400)
    # trade the evaluation to its target ($3,000 on a 50K Combine) over 3 days
    for i,(d,pnl) in enumerate([('2026-10-06',120000),('2026-10-07',100000),('2026-10-08',110000)]):
      await pg.evaluate(f"put('trades',{{id:'ev-{i}',account_id:'{ev['id']}',instrument:'NQ',date:'{d}',entry_time:'10:00:00',direction:'long',contracts:1,pnl_c:{pnl},pnl_manual:true,emo:{{}},review:{{}},discipline:{{}}}})")
    await pg.wait_for_timeout(1000)
    await pg.evaluate("location.hash='#dashboard'; render()"); await pg.wait_for_timeout(2500)
    win = await pg.evaluate("(document.querySelector('aside.nav-pass.open h2')||{}).textContent||''")
    ok('réussi' in win and 'Combine 50K' in win, f'target reached: « {win} » opens by itself')
    # « Pas encore » → not again today
    await pg.locator('[data-pass-later]').click(); await pg.wait_for_timeout(800)
    await pg.evaluate("render()"); await pg.wait_for_timeout(1500)
    ok(await pg.locator('.nav-pass.open').count() == 0, '« Pas encore »: not asked again today')
    # the account page button
    await pg.evaluate(f"location.hash='#account/{ev['id']}'"); await pg.wait_for_timeout(1500)
    row = await pg.evaluate("(document.querySelector('#main .nav-pass-row')||{innerText:''}).innerText.replace(/\\n/g,' ')")
    ok('Passer en financé' in row, f'the account page offers « Passer en financé » ({row})')
    await pg.locator('#main [data-pass-btn]').click(); await pg.wait_for_timeout(700)
    await pg.locator("[data-pass-go]").first.click(); await pg.wait_for_timeout(2000)   # Topstep asks Standard / Consistency: Standard (the default)
    r=await pg.evaluate(f"(()=>{{const o=getDoc('accounts','{ev['id']}'), n=S.accounts.find(x=>x.from_eval==='{ev['id']}'); return {{old:{{status:o.status,result:o.result,funded_id:o.funded_id}}, new:n?{{name:n.name,phase:n.phase,preset:n.preset,target:n.rules.target_c,win:n.rules.payout_win_days,win_min:n.rules.payout_win_min_c,bal:n.starting_balance_c}}:null, page:location.hash}}}})()")
    o, n = r['old'], r['new']
    ok(n and n['phase'] == 'funded' and n['preset'] == 'topstep|combine|50000|funded|' and n['target'] is None and n['win'], f'moved: the funded account with its own rules ({n})')
    ok(o['status'] == 'archived' and o['result'] == 'passed' and o['funded_id'] and r['page'] == '#account/' + o['funded_id'], f'the evaluation archived as passed, linked, its funded account opened ({o}, {r["page"]})')
    ok(not errs, f'no page error ({errs[:3]})'); await br.close()
asyncio.run(main())
print(f'{fails} failed' if fails else 'all passed'); sys.exit(1 if fails else 0)
