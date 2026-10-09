import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for name,kw in [('d',{'viewport':{'width':1440,'height':900}}),('m',p.devices['iPhone 13'])]:
      ctx=await br.new_context(**kw, storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      await pg.clock.install(time=datetime.datetime(2026,10,8,11,0,0,tzinfo=datetime.timezone.utc))
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
      print(name, await pg.evaluate("[...document.querySelectorAll('.nav-ev-v3')].filter(e=>e.offsetParent).map(e=>e.closest('button').querySelector('[class$=-n]').textContent.trim().slice(0,22)+' → '+e.textContent.replace(/\\s+/g,' ').trim()).slice(0,3).join(' | ')"))
      el=pg.locator('.nav-ev-v3:visible').first
      if await el.count(): await el.locator('xpath=ancestor::button').screenshot(path=f'/tmp/nv_{name}.png')
      await ctx.close()
    await br.close()
asyncio.run(main())
