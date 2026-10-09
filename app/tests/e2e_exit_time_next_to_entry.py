import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-06')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1200)
      if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
      pos=await pg.evaluate("""(()=>{const r=s=>{const e=document.querySelector(s); if(!e) return null; const b=e.getBoundingClientRect(); return [Math.round(b.left),Math.round(b.top)]}; return {date:r('#tkSlide [data-tk=date]'),entry:r('#tkSlide [data-tk=entryTime]'),exit:r('#tkSlide [data-tk=exitTime]'),risk:r('#tkSlide #tkRisk'),real:r('#tkSlide .nav-real')}})()""")
      print(w, pos)
      # typing an exit time still works after the move
      e=pg.locator('#tkSlide [data-tk=exitTime]'); await e.fill('10:15:00'); await e.dispatch_event('input'); await pg.locator('#tkSlide [data-v=long]').first.click(); await pg.wait_for_timeout(500)
      print('   exit time kept after a redraw:', await pg.evaluate("document.querySelector('#tkSlide [data-tk=exitTime]').value"), '| TK:', await pg.evaluate("TK.exitTime"))
      d=pg.locator('#tkSlide [data-tk=date]'); await d.scroll_into_view_if_needed()
      b=await pg.evaluate("(()=>{const a=document.querySelector('#tkSlide .nav-dt').getBoundingClientRect(); return {x:a.left-8,y:a.top-8,width:a.width+16,height:a.height+16}})()")
      await pg.screenshot(path=f'/tmp/dt_{w}.png', clip=b)
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
