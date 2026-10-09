import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); out=[]
    for state in ['/tmp/show_state.json','/home/claude/media/alex_state.json']:
      ctx=await br.new_context(**p.devices['iPhone 13'], storage_state=state, locale='fr-CA'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-07')")
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
      await pg.evaluate("editDoc('settings','settings',r=>{r.add_mode='manual'; delete r.add_mode_pref})"); await pg.wait_for_timeout(500)   # an old auto-saved « manual »
      await pg.locator('#bottomnav .plus, .bottomnav .plus').first.tap(); await pg.wait_for_timeout(1500)
      if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').tap(); await pg.wait_for_timeout(1200)
      out.append(state.split('/')[-1][:5]+': « + » opens '+('the screenshot screen' if await pg.locator('.nav-am-shot.open').count() else 'the manual form' if await pg.locator('#tkSlide.open').count() else 'nothing'))
      if await pg.locator('.nav-am-shot.open .nav-am-alt [data-am=to-manual]').count():
        await pg.locator('.nav-am-shot.open .nav-am-alt [data-am=to-manual]').tap(); await pg.wait_for_timeout(1200)
        out.append('   « Saisir à la main » → '+('manual form' if await pg.locator('#tkSlide.open').count() else '?'))
        await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(600)
        await pg.locator('#bottomnav .plus, .bottomnav .plus').first.tap(); await pg.wait_for_timeout(1500)
        if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').tap(); await pg.wait_for_timeout(1200)
        out.append('   next « + » opens '+('the screenshot screen again' if await pg.locator('.nav-am-shot.open').count() else 'the manual form'))
      await ctx.close()
    print('\n'.join(out)); await br.close()
asyncio.run(main())
