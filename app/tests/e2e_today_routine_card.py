import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for name,state,clock,w,h,mob in [('morning','/tmp/show_state.json',datetime.datetime(2026,10,6,12,30,0,tzinfo=datetime.timezone.utc),1440,900,False),
                                      ('swept','/home/claude/media/alex_state.json',datetime.datetime(2026,10,6,15,40,0,tzinfo=datetime.timezone.utc),1440,900,False),
                                      ('phone-morning','/tmp/show_state.json',datetime.datetime(2026,10,6,12,30,0,tzinfo=datetime.timezone.utc),390,844,True),
                                      ('phone-swept','/home/claude/media/alex_state.json',datetime.datetime(2026,10,6,15,40,0,tzinfo=datetime.timezone.utc),390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state=state)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); localStorage.setItem('sw.guide', JSON.stringify({hideStart:true,startCelebrated:true,tips:{},visited:{}}))")
      pg=await ctx.new_page(); await pg.clock.install(time=clock); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3800)
      print(name, '|', await pg.evaluate("(document.querySelector('.nav-rt')||{innerText:'none'}).innerText.replace(/\\n+/g,' | ').slice(0,300)"))
      el=pg.locator('.nav-rt')
      if await el.count(): await el.screenshot(path=f'/tmp/rt_{name}.png')
      if name=='morning':
        await pg.locator('.nav-rt [data-rt=help]').click(); await pg.wait_for_timeout(300); print('   help shown:', await pg.evaluate("!document.querySelector('.nav-rt-help-t').hidden"))
        await pg.locator('.nav-rt [data-rt=plan]').click(); await pg.wait_for_timeout(1200); print('   « Faire mon plan » opens:', await pg.evaluate("(document.querySelector('#gSheet h2, #gSheet h3')||{}).textContent||'nothing'"))
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
