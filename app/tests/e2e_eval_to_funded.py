import asyncio, datetime, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
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
    print('first question:', q, '| phase choice left at the end:', ph, '| saved:', a)
    await pg.evaluate("closeTicket && closeTicket()"); await pg.wait_for_timeout(400)
    q,ph,ev=await add('eval','topstep',0,'Combine 50K')
    print('evaluation account:', ev)
    await pg.evaluate("closeTicket && closeTicket()"); await pg.wait_for_timeout(400)
    # trade the evaluation to its target ($3,000 on a 50K Combine) over 3 days
    for i,(d,pnl) in enumerate([('2026-10-06',120000),('2026-10-07',100000),('2026-10-08',110000)]):
      await pg.evaluate(f"put('trades',{{id:'ev-{i}',account_id:'{ev['id']}',instrument:'NQ',date:'{d}',entry_time:'10:00:00',direction:'long',contracts:1,pnl_c:{pnl},pnl_manual:true,emo:{{}},review:{{}},discipline:{{}}}})")
    await pg.wait_for_timeout(1000)
    await pg.evaluate("location.hash='#dashboard'; render()"); await pg.wait_for_timeout(2500)
    print('window shown:', await pg.evaluate("(document.querySelector('.nav-pass h2')||{}).textContent||'none'"))
    print('debug:', await pg.evaluate("[...document.querySelectorAll('.nav-pass')].map(e=>e.tagName+'.'+e.className+' '+JSON.stringify(e.getBoundingClientRect())+' '+getComputedStyle(e).visibility+'/'+getComputedStyle(e).opacity+'/'+getComputedStyle(e).transform).join(' || ')"))
    await pg.locator('aside.nav-pass .nav-dlg-in').screenshot(path='/tmp/pass.png', timeout=5000)
    # « Pas encore » → not again today
    await pg.locator('[data-pass-later]').click(); await pg.wait_for_timeout(800)
    await pg.evaluate("render()"); await pg.wait_for_timeout(1500)
    print('after « Pas encore », asked again today:', await pg.locator('.nav-pass.open').count()>0)
    # the account page button
    await pg.evaluate(f"location.hash='#account/{ev['id']}'"); await pg.wait_for_timeout(1500)
    print('account page:', await pg.evaluate("(document.querySelector('#main .nav-pass-row')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"))
    await pg.locator('#main [data-pass-btn]').click(); await pg.wait_for_timeout(700)
    await pg.locator("[data-pass-go]").first.click(); await pg.wait_for_timeout(2000)   # Topstep asks Standard / Consistency: Standard (the default)
    r=await pg.evaluate(f"(()=>{{const o=getDoc('accounts','{ev['id']}'), n=S.accounts.find(x=>x.from_eval==='{ev['id']}'); return {{old:{{status:o.status,result:o.result,funded_id:o.funded_id}}, new:n?{{name:n.name,phase:n.phase,preset:n.preset,target:n.rules.target_c,win:n.rules.payout_win_days,win_min:n.rules.payout_win_min_c,bal:n.starting_balance_c}}:null, page:location.hash}}}})()")
    print('moved to funded:', r)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
