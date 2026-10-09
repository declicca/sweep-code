import asyncio, json
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=1 if not mob else 2,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-06')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1200)
      if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
      geo="(sel)=>{const e=document.querySelector(sel), r=e.getBoundingClientRect(), h=e.querySelector('h2'); return [Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height), getComputedStyle(h).fontSize, (e.querySelector('.tk-head > .link, .nav-am-head > .link')||{}).textContent]}"
      a=await pg.evaluate(f"({geo})('#tkSlide')")
      await pg.screenshot(path=f'/tmp/same_man_{w}.png')
      await pg.locator('#tkSlide .nav-am-sw').click(); await pg.wait_for_timeout(1200)
      b=await pg.evaluate(f"({geo})('.nav-am-shot')")
      print(w, '| manual:', a, '| screenshot:', b, '| same place:', a[:4]==b[:4])
      await pg.screenshot(path=f'/tmp/same_shot_{w}.png')
      await pg.locator('.nav-am-shot [data-am=close]').click(); await pg.wait_for_timeout(500)
      print('   « Annuler » closes it:', await pg.locator('.nav-am-shot.open').count()==0)
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
