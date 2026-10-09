import asyncio, datetime, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    u='lv%d'%random.randint(1000,9999)
    await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
    # the profile is asked before the first account (since 2026-10-06): filled here so the « Complete your profile » window does not cover the page
    await ctx.request.post(B+'/api/me/profile', data={'first_name':'Test','last_name':'Trader','username':u}, headers={'X-Requested-With':'fetch'})
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
    await pg.evaluate("put('accounts',{id:'a-seed',name:'Perso',firm_id:'',starting_balance_c:1000000,status:'active'})"); await pg.wait_for_timeout(1000)
    async def add(phase, firm, size_idx, name, shot=None):
      await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
      await pg.locator('#main [data-act=acct-add]:not([data-v="0"])').first.click(); await pg.wait_for_timeout(900)
      st=pg.locator('form[data-form=account] .ux-st')
      if shot:
        print('choices:', await pg.evaluate("[...document.querySelectorAll('form[data-form=account] [data-st-ph0]')].map(b=>b.innerText.replace(/\\n/g,' — ')).join(' | ')"))
        await st.screenshot(path=shot)
      await st.locator(f'[data-st-ph0={phase}]').click(); await pg.wait_for_timeout(500)
      if phase == 'live':   # since the « live account » form (no presets: live rules differ by platform): broker, name, balance
        f = pg.locator('form[data-form=account]')
        sel = f.locator('select[name=firm]')
        if await sel.count():
          try: await sel.select_option('__new')
          except Exception: pass
        if await f.locator('[name=firmName]').count(): await f.locator('[name=firmName]').fill('Topstep')
        await f.locator('[name=start]').fill('10000'); await f.locator('[name=name]').fill(name)
        await f.locator('[type=submit]').click(); await pg.wait_for_timeout(1500)
        a = await pg.evaluate(f"(()=>{{const a=S.accounts.find(x=>x.name==='{name}'); return a?{{id:a.id,phase:a.phase,start:a.starting_balance_c/100}}:null}})()")
        return 'live form (no preset)', a
      await st.locator(f'[data-st-firm="{firm}"]').click(); await pg.wait_for_timeout(300)
      if await st.locator('[data-st-type]').count(): await st.locator('[data-st-type]').first.click(); await pg.wait_for_timeout(300)
      if await st.locator('[data-st-size]').count(): await st.locator('[data-st-size]').nth(size_idx).click(); await pg.wait_for_timeout(300)
      summ=await st.locator('.ux-st-sum').inner_text() if await st.locator('.ux-st-sum').count() else ''
      start=await pg.locator('form[data-form=account] [name=start]').input_value()
      await pg.locator('form[data-form=account] [name=name]').fill(name)
      await pg.locator('form[data-form=account] [type=submit]').click(); await pg.wait_for_timeout(1500)
      a=await pg.evaluate(f"(()=>{{const a=S.accounts.find(x=>x.name==='{name}'); return a?{{id:a.id,phase:a.phase,start:a.starting_balance_c/100,dd:a.rules.dd_c/100,dd_type:a.rules.dd_type,dll:a.rules.dll_c&&a.rules.dll_c/100,win:a.rules.payout_win_days,pct:a.rules.payout_max_pct,max:a.rules.payout_max_c}}:null}})()")
      await pg.evaluate("closeTicket && closeTicket()"); await pg.wait_for_timeout(400)
      return summ.replace('\n',' ')+' | start field: '+start, a
    s,a=await add('live','topstep',0,'Topstep Live 50K','/tmp/live_q.png')
    print('Topstep live:', a, '|', s[:120])
    s,b=await add('funded','lucid',1,'LucidFlex 50K')
    print('Lucid funded:', b)
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
    print('Today badges:', await pg.evaluate("[...document.querySelectorAll('.nav-acc')].map(e=>e.querySelector('.nav-acc-t b').innerText).join(' | ')"))
    await pg.evaluate(f"location.hash='#account/{b['id']}'"); await pg.wait_for_timeout(1500)
    print('funded account page line:', await pg.evaluate("(document.querySelector('#main .nav-live-row')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"))
    await pg.locator('#main [data-live-go]').click(); await pg.wait_for_timeout(1800)
    r=await pg.evaluate(f"(()=>{{const o=getDoc('accounts','{b['id']}'), n=S.accounts.find(x=>x.from_funded==='{b['id']}'); return {{old:[o.status,o.result], new:n?[n.phase,n.preset,n.rules.payout_max_c,n.rules.payout_max_pct,n.rules.payout_win_days]:null, page:location.hash, badge:!!document.querySelector('#main .nav-live')}}}})()")
    print('moved to live:', r)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
