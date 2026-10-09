import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.clock.install(time=datetime.datetime(2026,10,7,22,30,0,tzinfo=datetime.timezone.utc))
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    await pg.locator('.nav-feed [data-kt=week]').tap(); await pg.wait_for_timeout(1800)
    print('week news:', await pg.evaluate("[...document.querySelectorAll('.nav-fnews-w .nav-fev')].map(e=>(e.classList.contains('nav-fev-past')?'(past) ':'')+e.textContent.trim().replace(/\\s+/g,' ').slice(0,40)).join(' | ')"))
    el=pg.locator('.nav-fnews-w'); 
    if await el.count(): await el.scroll_into_view_if_needed(); await el.screenshot(path='/tmp/wk.png')
    await br.close()
asyncio.run(main())
