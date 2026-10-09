import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); localStorage.removeItem('sw.rtShown')")
    await pg.goto('http://127.0.0.1:8095/?x=1#accounts'); await pg.wait_for_timeout(2500)
    await pg.locator('#main [data-act=acct-add][data-v="1"]').first.click(); await pg.wait_for_timeout(900)
    print('add account: cancel shown', await pg.locator('#main form[data-form=account] .nav-cancel').count())
    await pg.locator('#main form[data-form=account] .nav-cancel').click(); await pg.wait_for_timeout(900)
    print('   after cancel: form gone', await pg.locator('#main form[data-form=account]').count()==0)
    await pg.evaluate("location.hash='#payouts'"); await pg.wait_for_timeout(1500)
    await pg.locator('.nav-pz-b[data-k=payout]').click(); await pg.wait_for_timeout(500)
    await pg.locator('form[data-form=payout] .nav-cancel').click(); await pg.wait_for_timeout(500)
    print('payout cancel: form hidden', not await pg.evaluate("!!(document.querySelector('form[data-form=payout]')||{}).offsetParent"))
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_selector('.nav-rt-steps', state='attached', timeout=15000); await pg.wait_for_timeout(600)
    print('first visit of the day: open', await pg.evaluate("!document.querySelector('.nav-rt').classList.contains('closed-rt')")); await pg.wait_for_timeout(5200)
    print('   5 s later: folded', await pg.evaluate("document.querySelector('.nav-rt').classList.contains('closed-rt')"))
    b=await pg.locator('.d-perf').bounding_box(); await pg.screenshot(path='/tmp/l6_perf.png', clip={'x':b['x'],'y':b['y'],'width':b['width'],'height':min(300,b['height'])})
    await br.close()
asyncio.run(main())
