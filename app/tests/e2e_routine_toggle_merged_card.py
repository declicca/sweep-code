import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/tmp/show_state.json', color_scheme='dark', locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); if(!sessionStorage.getItem('x')){localStorage.removeItem('sw.rtClosed'); sessionStorage.setItem('x','1')}")
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_selector('.nav-rt-tg', timeout=15000); await pg.wait_for_timeout(800)
    print('merged card holds:', await pg.evaluate("[...document.querySelectorAll('.nav-merge > *')].map(e=>(e.className.match(/d-[a-z]+/)||[''])[0]).join(' → ')"), '| routine closed:', await pg.evaluate("!!document.querySelector('.nav-rt.closed-rt')"), '| steps visible:', await pg.evaluate("!!(document.querySelector('.nav-rt-steps')||{}).offsetParent"))
    await pg.screenshot(path='/tmp/mg_closed.png', full_page=True)
    await pg.locator('.nav-rt-tg').click(); await pg.wait_for_timeout(500)
    print('after click: open', await pg.evaluate("!document.querySelector('.nav-rt.closed-rt')"), '| steps visible:', await pg.evaluate("!!(document.querySelector('.nav-rt-steps')||{}).offsetParent"))
    await pg.screenshot(path='/tmp/mg_open.png')
    await pg.reload(); await pg.wait_for_timeout(3500); print('after reload, stays open:', await pg.evaluate("!document.querySelector('.nav-rt.closed-rt')"))
    await br.close()
asyncio.run(main())
