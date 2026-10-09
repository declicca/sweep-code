import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,13,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{}}))")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    state=lambda: pg.evaluate("document.querySelector('#gSheet .g-gate') ? 'plan first' : (document.querySelector('#tkSlide.open') ? 'trade form' : 'nothing')")
    await pg.locator('#bottomnav .plus, #bottomnav [data-act=add-trade]').first.click(); await pg.wait_for_timeout(1000)
    print('1) « + » with no plan today →', await state())
    await pg.screenshot(path='/tmp/gate_plan.png')
    await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
    print('2) « Passer » →', await state())
    await pg.evaluate("typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(600)
    await pg.locator('#bottomnav .plus, #bottomnav [data-act=add-trade]').first.click(); await pg.wait_for_timeout(1000)
    print('3) « + » again the same day (skipped) →', await state())
    await pg.evaluate("typeof closeTicket==='function'&&closeTicket(); localStorage.removeItem('sw.planSkip')"); await pg.wait_for_timeout(600)
    await pg.keyboard.press('n'); await pg.wait_for_timeout(1000)
    print('4) « N » key, skip forgotten →', await state())
    await pg.locator('#gSheet [data-g=bias][data-v=bullish]').click()
    await pg.locator('#gSheet .g-setups .chip').first.click()
    await pg.locator('#gSheet [data-gp=max_loss]').fill('600')
    await pg.locator('#gSheet [data-g=save-plan]').click(); await pg.wait_for_timeout(1400)
    print('5) « Enregistrer et ajouter mon trade » →', await state(), '| plan saved:', await pg.evaluate("!!(getDoc('journals','2026-10-05')||{}).pre"))
    await pg.evaluate("typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(600)
    await pg.locator('#bottomnav .plus, #bottomnav [data-act=add-trade]').first.click(); await pg.wait_for_timeout(1000)
    print('6) « + » once the plan exists →', await state())
    tid=await pg.evaluate("S.trades.filter(t=>t.demo)[0].id"); await pg.evaluate("closeTicket()")
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
