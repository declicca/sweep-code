import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA'); pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.clock.install(time=datetime.datetime(2026,10,6,15,40,0,tzinfo=datetime.timezone.utc))
    await pg.goto('http://127.0.0.1:8095/?x=1#journal/w2026-09-28'); await pg.wait_for_timeout(3500)
    await pg.screenshot(path='/tmp/wk.png', full_page=True)
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1500)
    print('import on Trades:', await pg.locator('.main-wrap .top .nav-imp').count())
    await pg.locator('.main-wrap .top [data-imp-help]').click(); await pg.wait_for_timeout(1200)
    print('help article:', await pg.evaluate("(document.querySelector('.gd-help-ov h2, .gd-help-ov h3')||{}).textContent||'none'"))
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
    await pg.evaluate("location.hash='#analytics'"); await pg.wait_for_timeout(2000)
    print('slippage visible on Stats:', await pg.evaluate("[...document.querySelectorAll('.nav-slip')].some(e=>e.offsetParent)"))
    # payout share card
    await pg.evaluate("location.hash='#payouts'"); await pg.wait_for_timeout(1500)
    await pg.evaluate("openShare('payout','po-3')"); await pg.wait_for_timeout(2500)
    print('payout card:', await pg.evaluate("(()=>{const d=shData('payout','po-3'); return d.eyebrow+' | line: '+d.whoLine+' | '+JSON.stringify(d.stats)})()"))
    await pg.locator('#shPanel .sh-prev').screenshot(path='/tmp/pcard.png')
    await pg.locator('#shPanel [data-focus=dol]').click(); await pg.wait_for_timeout(1500)
    print('dollars:', await pg.evaluate("JSON.stringify(shData('payout','po-3').stats)"))
    await pg.locator('#shPanel [data-focus=disc]').click(); await pg.wait_for_timeout(800)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
