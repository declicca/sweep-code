import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); out=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(2500)
    r=pg.locator('#main tr[data-href^="#trade/"]').nth(1); await r.hover(); await pg.wait_for_timeout(300)
    out.append('computer hover buttons: '+str(await r.locator('button[data-ra]').count())+' ('+(await r.locator('button[data-ra]').first.get_attribute('aria-label'))+')')
    b=await r.bounding_box(); await pg.screenshot(path='/tmp/sw2_hover.png', clip={'x':b['x']+b['width']-420,'y':b['y']-40,'width':420,'height':b['height']+80})
    n0=await pg.evaluate("S.trades.length"); await r.locator('button[data-ra=del]').click(); await pg.wait_for_timeout(600)
    out.append(f"trash: deleted {n0-await pg.evaluate('S.trades.length')}, undo shown {await pg.locator('.nav-undo').count()}"); await pg.locator('.nav-undo button').click(); await pg.wait_for_timeout(600)
    await pg.locator('#main tr[data-href^="#trade/"]').nth(0).click(); await pg.wait_for_timeout(1200); out.append('row click → '+await pg.evaluate("location.hash"))
    await ctx.close()
    ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page(); cdp=await ctx.new_cdp_session(pg)
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(2800)
    async def drag(x0,y0,x1,y1):
      await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x0,'y':y0}]})
      for i in range(1,13): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x0+(x1-x0)*i/12,'y':y0+(y1-y0)*i/12}]}); await pg.wait_for_timeout(16)
      await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(600)
    rr=pg.locator('#main .nav-ra-row').nth(1); await rr.scroll_into_view_if_needed(); b=await rr.bounding_box(); y=b['y']+b['height']/2
    await drag(b['x']+300,y,b['x']+200,y+2); out.append('short swipe → Delete shown: '+str(await pg.evaluate("!!document.querySelector('.nav-ra-row.nav-sw')")))
    await pg.screenshot(path='/tmp/sw2_short.png', clip={'x':0,'y':b['y']-50,'width':390,'height':b['height']+100})
    await pg.touchscreen.tap(60,y); await pg.wait_for_timeout(400)
    n0=await pg.evaluate("S.trades.length"); await drag(b['x']+330,y,b['x']+30,y+2)
    out.append(f"long swipe → deleted {n0-await pg.evaluate('S.trades.length')}, undo {await pg.locator('.nav-undo').count()}")
    await pg.locator('.nav-undo button').tap(); await pg.wait_for_timeout(600); out.append('undo → back: '+str(await pg.evaluate("S.trades.length")==n0))
    r0=pg.locator('#main .nav-ra-row').first; b0=await r0.bounding_box(); await pg.touchscreen.tap(b0['x']+100,b0['y']+b0['height']/2); await pg.wait_for_timeout(1200); out.append('tap row → '+await pg.evaluate("location.hash"))
    print('\n'.join(out)); await br.close()
asyncio.run(main())
