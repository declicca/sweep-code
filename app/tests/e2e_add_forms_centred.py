import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(1280,800,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=1 if not mob else 2,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='en-US',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); localStorage.setItem('sw.planSkip','2026-10-06')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1200)
      if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
      geo="(s)=>{const e=document.querySelector(s); const r=e.getBoundingClientRect(); return [Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height), Math.round(r.left+r.width/2)]}"
      a=await pg.evaluate(f"({geo})('#tkSlide')")
      if w==1440: await pg.screenshot(path='/tmp/center_man.png')
      await pg.locator('#tkSlide .nav-am-sw').click(); await pg.wait_for_timeout(1200)
      b=await pg.evaluate(f"({geo})('.nav-am-shot')")
      over=await pg.evaluate("(()=>{const c=document.querySelector('.nav-am-shot .nav-am-in'); const r=c.getBoundingClientRect(); return [...c.querySelectorAll('*')].filter(e=>{const q=e.getBoundingClientRect(); return q.width && q.right>r.right+1}).length})()")
      print(w, '| manual [left,top,w,h,centre]:', a, '| screenshot:', b, '| elements sticking out:', over)
      if w==1440:
        await pg.locator('.nav-am-shot .nav-am-sec').last.scroll_into_view_if_needed(); await pg.wait_for_timeout(300)
        await pg.screenshot(path='/tmp/center_shot.png')
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
