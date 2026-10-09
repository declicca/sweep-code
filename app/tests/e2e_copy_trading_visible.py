import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(390,844,True),(1440,900,False)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
      pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      # 1) screenshot form: also on 2 other accounts
      await pg.evaluate("SweepAddMode.open()"); await pg.wait_for_timeout(700)
      print(w, '| « Aussi sur » in the screenshot form:', await pg.locator('.nav-am-shot [data-am-copy]').count(), 'accounts')
      await pg.locator('.nav-am-shot [data-am-copy]').nth(0).click(); await pg.locator('.nav-am-shot [data-am-copy]').nth(1).click()
      await pg.locator('.nav-am-more-d summary').click(); await pg.wait_for_timeout(200)
      await pg.locator('.nav-am-shot [data-am-seg=dir][data-v=long]').click()
      for k,v in [('entry','30100'),('exit','30120'),('time','10:00')]:
        i=pg.locator(f'.nav-am-shot [data-am-f={k}]'); await i.fill(v); await i.dispatch_event('input')
      if mob: await pg.locator('.nav-am-shot .nav-am-copy').screenshot(path='/tmp/copy_form.png')
      await pg.locator('.nav-am-shot [data-am=save]').click(); await pg.wait_for_timeout(1500)
      g=await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.source==='screenshot'&&x.entry===30100&&x.exit===30120); return {n:t.length, groups:[...new Set(t.map(x=>x.copy_group))].length, accounts:t.map(x=>acctLabel(x.account_id)), id:t[0]&&t[0].id}})()")
      print('   saved on', g['n'], 'accounts, one copy group:', g['groups']==1, '|', ', '.join(g['accounts']))
      # 2) the trade page says where it is and offers to copy to the rest
      await pg.evaluate(f"location.hash='#trade/{g['id']}'"); await pg.wait_for_timeout(1500)
      print('   trade page line:', await pg.evaluate("(document.querySelector('#main .nav-copy')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"))
      if mob: await pg.locator('#main .nav-copy').screenshot(path='/tmp/copy_line.png')
      await pg.locator('#main .nav-copy [data-act=copy-open]').click(); await pg.wait_for_timeout(700)
      chips=pg.locator('#main [data-act=copy-pick]'); n=await chips.count()
      print('   « Copier sur d’autres comptes » opens the picker with', n, 'accounts')
      if n:
        await chips.first.click(); await pg.wait_for_timeout(300); await pg.locator('#main [data-act=copy-do]').click(); await pg.wait_for_timeout(1200)
        print('   after copying: line now says:', await pg.evaluate("(document.querySelector('#main .nav-copy')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"))
      # clean
      await pg.evaluate("S.trades.filter(x=>x.source==='screenshot'&&x.entry===30100&&x.exit===30120).forEach(x=>remove('trades',x.id))"); await pg.wait_for_timeout(1000)
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
