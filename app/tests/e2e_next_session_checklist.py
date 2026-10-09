import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.clock.install(time=datetime.datetime(2026,10,7,22,30,0,tzinfo=datetime.timezone.utc))   # 18:30 ET
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_selector('.nav-rt-steps', timeout=15000); await pg.wait_for_timeout(1200)
    print('18:30 ET: plan step tag:', await pg.evaluate("(document.querySelector('.nav-next-ses')||{}).textContent"), '| next session:', await pg.evaluate("SweepNextSession()"))
    await pg.locator('.nav-rt [data-rt=plan]').first.tap(); await pg.wait_for_timeout(1500)
    print('plan opens for:', await pg.evaluate("(document.querySelector('#gSheet .g-sub, #gSheet .muted, #gSheet small')||{}).textContent"))
    await pg.screenshot(path='/tmp/l5_plan.png')
    await pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach(b=>b.click())"); await pg.wait_for_timeout(600)
    await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1500)
    print('manual form checklist questions shown:', await pg.evaluate("[...document.querySelectorAll('.nav-ck-q')].filter(q=>q.offsetParent).length"), 'of', await pg.evaluate("document.querySelectorAll('.nav-ck-q').length"))
    await pg.evaluate("document.querySelectorAll('.nav-ck-q')[0].querySelector('[data-v=y]').click(); document.querySelectorAll('.nav-ck-q')[1].querySelector('[data-v=n]').click()")
    await pg.evaluate("TK.direction='long'; tkRefresh({panel:true})"); await pg.wait_for_timeout(400); await pg.fill('#tkSlide [data-tk=entry]','25100'); await pg.fill('#tkSlide [data-tk=exit]','25110')
    await pg.locator('.nav-ck').scroll_into_view_if_needed(); await pg.locator('.nav-ck').screenshot(path='/tmp/l5_ck.png')
    n0=await pg.evaluate("S.trades.length"); await pg.evaluate("document.querySelector('#tkSlide [data-act=tk-save]').click()"); await pg.wait_for_timeout(2500)
    print('saved trade discipline:', await pg.evaluate(f"JSON.stringify((S.trades.slice(-1)[0]||{{}}).discipline)"), '| new trades:', await pg.evaluate("S.trades.length")-n0)
    await br.close()
asyncio.run(main())
