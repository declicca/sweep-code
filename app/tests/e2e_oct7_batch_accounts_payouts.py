import asyncio, datetime, random, json, sys
sys.path.insert(0,'/home/claude/media')
import media_lib as M
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA'); pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await ctx.route('**/api/ai/import', M.ai_route)
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); localStorage.setItem('sw.planSkip','2026-10-06')")
    await pg.clock.install(time=datetime.datetime(2026,10,6,15,40,0,tzinfo=datetime.timezone.utc))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    await pg.locator('.d-today').screenshot(path='/tmp/t7_today.png')
    n0=await pg.evaluate("S.trades.length")
    # several screenshots
    await pg.evaluate("document.body.classList.add('ai-on')")
    if False:
      pass
    # several accounts + cost
    await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
    na=await pg.evaluate("S.accounts.length"); ne=await pg.evaluate("S.expenses.length")
    await pg.locator('#main [data-act=acct-add]:not([data-v=\"0\"])').first.click(); await pg.wait_for_timeout(900)
    await pg.locator('form[data-form=account] [data-st-ph0=eval]').click(); await pg.wait_for_timeout(300)
    await pg.locator('form[data-form=account] [data-st-firm=apex]').click(); await pg.wait_for_timeout(300)
    if await pg.locator('form[data-form=account] [data-st-type]').count(): await pg.locator('form[data-form=account] [data-st-type]').first.click(); await pg.wait_for_timeout(300)
    await pg.locator('form[data-form=account] [data-st-size]').nth(1).click(); await pg.wait_for_timeout(300)
    await pg.fill('form[data-form=account] [name=name]','Apex 50K'); await pg.fill('form[data-form=account] [name=nav_cost]','35'); await pg.fill('form[data-form=account] [name=nav_qty]','3')
    await pg.locator('form[data-form=account] [type=submit]').click(); await pg.wait_for_timeout(2500)
    print('accounts added:', await pg.evaluate("S.accounts.length")-na, await pg.evaluate("S.accounts.filter(a=>/^Apex 50K/.test(a.name)).map(a=>a.name).join(', ')"), '| expenses added:', await pg.evaluate("S.expenses.length")-ne)
    await pg.evaluate("typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(400)
    # several payouts
    await pg.evaluate("location.hash='#payouts'"); await pg.wait_for_timeout(1800)
    np=await pg.evaluate("S.payouts.length")
    f=pg.locator('form[data-form=payout]').first
    await f.locator('[name=amount]').fill('1000')
    chips=f.locator('[data-also]:not([hidden])'); print('also-for chips:', await chips.count())
    await chips.nth(0).click(); await chips.nth(1).click()
    await f.locator('[type=submit]').click(); await pg.wait_for_timeout(2000)
    print('payouts added:', await pg.evaluate("S.payouts.length")-np)
    # plan: setups folded
    await pg.evaluate("SweepGame.openPlan && SweepGame.openPlan()"); await pg.wait_for_timeout(1500)
    print('plan setups hidden:', await pg.evaluate("[...document.querySelectorAll('#gSheet .g-setups')].every(g=>g.hidden)"), '| optional link:', await pg.evaluate("(document.querySelector('#gSheet .nav-setups-open')||{}).textContent||'none'"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
