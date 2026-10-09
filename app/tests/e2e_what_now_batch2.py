import asyncio, random, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(**p.devices['iPhone 13'], locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.clock.install(time=datetime.datetime(2026,10,6,12,30,0,tzinfo=datetime.timezone.utc))
    await pg.goto('http://127.0.0.1:8095/auth.html?signup=1'); await pg.wait_for_timeout(1200)
    await pg.fill('#email','l2%d@gmail.com'%random.randint(1,999999)); await pg.fill('#password','Testpass123!x'); await pg.wait_for_timeout(2100); await pg.click('#go'); await pg.wait_for_timeout(3500)
    await pg.fill('.nav-prof [data-pf=first_name]','Lou'); await pg.fill('.nav-prof [data-pf=last_name]','Test'); await pg.click('.nav-prof [data-prof-go]'); await pg.wait_for_timeout(1500)
    print('after profile: account form visible right away:', await pg.evaluate("!!(document.querySelector('#main form[data-form=account]')||{}).offsetParent"), '| title:', await pg.evaluate("(document.querySelector('#main .onb h1, #main .onb h2')||{}).textContent"), '| hello screen:', await pg.locator('.nav-hello').count())
    await pg.screenshot(path='/tmp/l2_first.png')
    await pg.locator('.bottomnav .plus').first.tap(); await pg.wait_for_timeout(1200)
    print('« + » before any account → account form in a panel:', await pg.evaluate("!!document.querySelector('#drawer.on form[data-form=account], #drawer.on .ux-st')"))
    if await pg.locator('#scrim.on').count(): await pg.locator('#scrim.on').tap(position={'x':20,'y':20}); await pg.wait_for_timeout(700)
    print('   toast:', await pg.evaluate("(document.querySelector('.toast, #toast, .ux-toast')||{textContent:''}).textContent.trim().slice(0,70)"), '| plan opened:', await pg.locator('#gSheet').count(), '| trade form opened:', await pg.locator('#tkSlide.open, .nav-am.open').count())
    f='#main form[data-form=account]'
    await pg.click(f'{f} [data-st-ph0=eval]'); await pg.click(f'{f} [data-st-firm=topstep]'); await pg.wait_for_timeout(300)
    if await pg.locator(f'{f} [data-st-type]').count(): await pg.locator(f'{f} [data-st-type]').first.click()
    await pg.locator(f'{f} [data-st-size]').first.click(); await pg.wait_for_timeout(300); await pg.locator(f'{f} [type=submit]').click(); await pg.wait_for_timeout(2500)
    print('after the account: plan opened by itself:', await pg.locator('#gSheet').count(), '| welcome window:', await pg.locator('.g-ob').count(), '| add screen:', await pg.locator('.nav-am.open, #tkSlide.open').count())
    if await pg.locator('.nav-am-shot.open').count(): await pg.locator('.nav-am-shot .nav-am-alt [data-am=to-manual]').tap(); await pg.wait_for_timeout(1200)
    print('manual form: platform P&L hidden:', not await pg.evaluate("!!(document.querySelector('#tkSlide .nav-real')||{}).offsetParent"), '| link:', await pg.evaluate("(document.querySelector('#tkSlide .nav-real-l')||{}).textContent"), '| date visible:', await pg.evaluate("!!(document.querySelector('#tkSlide .nav-dt, #tkSlide [data-tk=date]')||{}).offsetParent"))
    await pg.screenshot(path='/tmp/l2_form.png')
    await pg.locator('#tkSlide .nav-real-l').tap(); await pg.wait_for_timeout(300); print('   after the link: field shown:', await pg.evaluate("!!(document.querySelector('#tkSlide .nav-real')||{}).offsetParent"))
    await pg.evaluate("closeTicket()"); await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1500)
    print('Trades, few trades: search visible', await pg.evaluate("[...document.querySelectorAll('#main input')].filter(i=>i.offsetParent&&/search|cherch|busc/i.test(i.placeholder||'')).length"), '| period chips:', await pg.evaluate("[...document.querySelectorAll('#main .seg')].filter(s=>s.offsetParent).map(s=>s.className+' «'+s.textContent.trim().slice(0,30)+'»').join(' ; ')"))
    await br.close()
asyncio.run(main())
