import asyncio
from playwright.async_api import async_playwright
async def drag(pg, cdp, x, y0, y1, steps=8):
    await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':x,'y':y0}]})
    for i in range(1,steps+1):
        await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':x,'y':y0+(y1-y0)*i/steps}]}); await pg.wait_for_timeout(16)
    await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-06')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150])); cdp=await ctx.new_cdp_session(pg)
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    for name, opener, sel in [('manual', "openTicket(null,{manual:true})", '#tkSlide'), ('screenshot', "SweepAddMode.open()", '.nav-am-shot')]:
      for where in ['handle', 'middle (scrolled to top)']:
        await pg.evaluate(opener); await pg.wait_for_timeout(1200)
        if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
        r=await pg.evaluate(f"(()=>{{const e=document.querySelector('{sel}'); const b=e.getBoundingClientRect(); return [b.top, getComputedStyle(e).transform]}})()")
        y0 = r[0]+20 if where=='handle' else r[0]+300
        await drag(pg, cdp, 195, y0, y0+260)
        await pg.wait_for_timeout(900)
        open_=await pg.evaluate(f"!!document.querySelector('{sel}.open')")
        print(f'{name:10} swipe from the {where}: closed = {not open_}')
        if open_:
          await pg.evaluate("document.querySelectorAll('.nav-am [data-am=close]').forEach(b=>b.click()); typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(700)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
