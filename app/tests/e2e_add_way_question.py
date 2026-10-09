import asyncio, datetime, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
      pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      u='am%d'%random.randint(1000,9999)
      await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
      await pg.evaluate("put('accounts',{id:'a-am',name:'50K',firm_id:'',starting_balance_c:5000000,status:'active'})"); await pg.wait_for_timeout(1200)
      await pg.reload(); await pg.wait_for_timeout(2500)
      # 1) first « Add a trade »: the question
      await pg.evaluate("openTicket()"); await pg.wait_for_timeout(700)
      print(w, '| first Add a trade asks:', await pg.evaluate("(document.querySelector('.nav-am-ask h2')||{}).textContent||'no question'"))
      if mob: await pg.locator('.nav-am-ask .nav-am-in').screenshot(path='/tmp/am_q.png')
      await pg.locator('[data-am-pick=shot]').click(); await pg.wait_for_timeout(1200)
      if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)   # the plan comes first, as for any trade
      print('   picked « capture » → saved:', await pg.evaluate("S.settings.add_mode"), '| screenshot form open:', await pg.locator('.nav-am-shot.open').count())
      # 2) the screenshot form: picture, key fields, discipline, psychology on one screen
      await pg.locator('.nav-am-shot [data-am-file]').set_input_files('/tmp/shot.png'); await pg.wait_for_timeout(1500)
      print('   picture shown:', await pg.locator('.nav-am-drop.has img').count(), '| status:', await pg.evaluate("(document.querySelector('.nav-am-st')||{}).textContent||''"))
      await pg.locator('.nav-am-more-d summary').click(); await pg.wait_for_timeout(200)
      await pg.locator('.nav-am-shot [data-am-seg=dir][data-v=short]').click()
      for k,v in [('qty','2'),('time','09:42'),('entry','30100'),('exit','30080')]:
        i=pg.locator(f'.nav-am-shot [data-am-f={k}]'); await i.fill(v); await i.dispatch_event('input')
      qs=await pg.locator('.nav-am-shot .nav-am-q').count()
      for i in range(qs): await pg.locator('.nav-am-shot .nav-am-q').nth(i).locator('[data-v=y]').click()
      await pg.locator('.nav-am-shot [data-am-emo=Calm]').click(); await pg.locator('.nav-am-shot [data-am-emo=Confident]').click()
      await pg.locator('.nav-am-shot [data-am-seg=conf][data-v="4"]').click(); await pg.locator('.nav-am-shot [data-am-seg=exec][data-v="5"]').click()
      print('   placeholder P&L:', await pg.evaluate("document.querySelector('.nav-am-net input').placeholder"), '| discipline questions:', qs)
      if mob: await pg.locator('.nav-am-shot .nav-am-in').screenshot(path='/tmp/am_shot.png')
      await pg.locator('.nav-am-shot [data-am=save]').click(); await pg.wait_for_timeout(1500)
      t=await pg.evaluate("(()=>{const t=S.trades.find(x=>x.source==='screenshot'); return t?{dir:t.direction,qty:t.contracts,entry:t.entry,exit:t.exit,pnl:t.pnl_c/100,time:t.entry_time,disc:Object.keys(t.discipline).length,emo:t.emo,shots:t.shots.length}:null})()")
      print('   saved:', t)
      # 3) next « Add a trade » opens the screenshot form directly, with the link to the manual form
      await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
      if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
      print('   next Add a trade → screenshot form:', await pg.locator('.nav-am-shot.open').count(), '| no question:', await pg.locator('.nav-am-ask').count()==0)
      await pg.locator('.nav-am-shot [data-am=to-manual]').click(); await pg.wait_for_timeout(1200)
      print('   « Saisir manuellement » → manual form:', await pg.locator('#tkSlide.open').count(), '| link back to capture:', await pg.locator('#tkSlide .nav-am-sw').count())
      await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(500)
      # 4) Settings: switch the default to manual
      await pg.evaluate("location.hash='#settings'"); await pg.wait_for_timeout(1500)
      await pg.locator('.nav-am-set [data-am-set=manual]').click(); await pg.wait_for_timeout(700)
      await pg.evaluate("openTicket()"); await pg.wait_for_timeout(1000)
      print('   default set to manual in Settings → Add a trade opens:', 'manual form' if await pg.locator('#tkSlide.open').count() else 'other')
      await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(400)
      # 5) back button closes the screenshot form
      await pg.evaluate("SweepAddMode.open()"); await pg.wait_for_timeout(700)
      await pg.go_back(); await pg.wait_for_timeout(800)
      print('   back closes it:', await pg.locator('.nav-am-shot.open').count()==0, '| still in the app:', 'app' in await pg.evaluate("location.pathname+location.search+'app'"))
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
