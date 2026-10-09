import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for name,kw in [('d',{'viewport':{'width':1440,'height':900}}),('m',p.devices['iPhone 13'])]:
      ctx=await br.new_context(**kw, storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      await pg.clock.install(time=datetime.datetime(2026,10,7,22,30,0,tzinfo=datetime.timezone.utc))
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
      if name=='m':
        await pg.locator('.nav-feed [data-kt=week]').tap(); await pg.wait_for_timeout(1500)
      print(name, await pg.evaluate("[...document.querySelectorAll('.nav-ev, .nav-fev')].filter(e=>e.offsetParent).map(b=>(b.querySelector('[class$=-n]')||b).textContent.replace(/\\s+/g,' ').trim().slice(0,24)+' → '+(b.querySelector('.nav-nonum-r')?'[Sans chiffre]':(b.querySelector('.nav-ev-v3')||{textContent:'?'}).textContent.replace(/\\s+/g,' ').trim())+' | pills: '+b.querySelectorAll('.nav-nonum').length).slice(0,4).join(' || ')"))
      await ctx.close()
    await br.close()
asyncio.run(main())
