import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for name,kw in [('desktop',{'viewport':{'width':1440,'height':900}}),('phone',p.devices['iPhone 13'])]:
      ctx=await br.new_context(**kw, storage_state='/tmp/show_state.json', color_scheme='dark', locale='en-US'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); localStorage.setItem('sw.planSkip','2099-01-01')")
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1500)
      if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
      print(name, '| buttons under the title:', await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-tk-alt > *')].map(e=>e.textContent.trim()).join(' | ')"), '| header links left:', await pg.locator('#tkSlide .tk-head .nav-am-sw:visible, #tkSlide .tk-head .nav-imp:visible').count())
      await pg.screenshot(path=f'/tmp/man_{name}.png')
      await pg.locator('#tkSlide [data-tk-alt=shot]').click(); await pg.wait_for_timeout(1200)
      print('   « From a screenshot » →', 'screenshot screen' if await pg.locator('.nav-am-shot.open').count() else '?')
      await ctx.close()
    await br.close()
asyncio.run(main())
