import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for name,kw in [('desktop',{'viewport':{'width':1440,'height':900}}),('phone',p.devices['iPhone 13'])]:
      ctx=await br.new_context(**kw, storage_state='/tmp/show_state.json', color_scheme='dark', locale='en-US'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_selector('.nav-rt-tg', timeout=15000); await pg.wait_for_timeout(800)
      st=lambda: pg.evaluate("[!document.querySelector('.nav-rt.closed-rt'), !!(document.querySelector('.nav-rt-steps')||{}).offsetParent]")
      print(name, 'closed by default (open, steps visible):', await st())
      await pg.screenshot(path=f'/tmp/rt3_{name}_closed.png')
      await (pg.locator('.nav-rt-tg').tap() if name=='phone' else pg.locator('.nav-rt-tg').click()); await pg.wait_for_timeout(500)
      print(name, 'after tap/click:', await st())
      await pg.screenshot(path=f'/tmp/rt3_{name}_open.png')
      await pg.evaluate("document.body.classList.add('ai-on'); SweepAddMode.open()"); await pg.wait_for_timeout(1000)
      print(name, 'screenshot form alternatives:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot .nav-am-alt > *')].map(e=>e.textContent.trim()).join(' | ')"))
      await ctx.close()
    await br.close()
asyncio.run(main())
