import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for name,kw in [('desktop',{'viewport':{'width':1440,'height':900}}),('phone',p.devices['iPhone 13'])]:
      ctx=await br.new_context(**kw, storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
      await pg.screenshot(path=f'/tmp/l8_{name}.png')
      if name=='desktop':
        await pg.locator('.d-quick [data-q="#payouts"]').click(); await pg.wait_for_timeout(2000)
        print('quick access → payout form open:', await pg.evaluate("!!(document.querySelector('#main form[data-form=payout]')||{}).offsetParent"), '| cancel size:', await pg.evaluate("(()=>{const c=document.querySelector('form[data-form=payout] .nav-cancel'); return c? Math.round(c.getBoundingClientRect().width)+'px':'none'})()"))
      await ctx.close()
    await br.close()
asyncio.run(main())
