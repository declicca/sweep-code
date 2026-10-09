import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.removeItem('sw.planSkip')")
    pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,5,13,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    await pg.evaluate("editDoc('settings','settings',r=>{r.add_mode='shot'})"); await pg.wait_for_timeout(800)
    await pg.locator('.bottomnav .plus').first.click(); await pg.wait_for_timeout(900)
    print('« + » with the screenshot way, no plan yet → ', 'plan first' if await pg.locator('#gSheet [data-g=plan-skip]').count() else ('screenshot form' if await pg.locator('.nav-am-shot.open').count() else 'other'))
    if await pg.locator('#gSheet [data-g=plan-skip]').count():
      await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1200)
      print('   « Passer, ajouter mon trade » → screenshot form:', await pg.locator('.nav-am-shot.open').count()==1)
    await pg.evaluate("editDoc('settings','settings',r=>{r.add_mode='manual'}); localStorage.removeItem('sw.planSkip')"); await pg.wait_for_timeout(3000)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
