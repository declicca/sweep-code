import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/tmp/show_state.json', color_scheme='dark', locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
    await pg.goto('http://127.0.0.1:8095/?x=1#trades'); await pg.wait_for_timeout(2500)
    ar=pg.locator('#main .nav-addrow').first; await ar.hover(); await pg.wait_for_timeout(300)
    print('Trades add row on hover: background', await ar.evaluate("e=>getComputedStyle(e).backgroundColor"), '| transform', await ar.evaluate("e=>getComputedStyle(e).transform"))
    b=await ar.bounding_box(); await pg.screenshot(path='/tmp/ar_trades.png', clip={'x':b['x']-20,'y':b['y']-30,'width':700,'height':120})
    await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
    await pg.locator('.nav-acc-top .nav-addrow').click(); await pg.wait_for_timeout(1000)
    print('Accounts: add form above the list:', await pg.evaluate("(()=>{const f=document.querySelector('form[data-form=account]'); const tb=document.querySelector('#main table.acct-tbl'); if(!f) return 'no form'; return !!(f.compareDocumentPosition(tb) & 4)})()"))
    await pg.screenshot(path='/tmp/ar_acc.png')
    await pg.evaluate("location.hash='#payouts'"); await pg.wait_for_timeout(1800)
    print('Payouts: rows inside their list cards:', await pg.evaluate("[...document.querySelectorAll('.nav-pz-b')].map(b=>b.dataset.k+':'+(b.parentElement.classList.contains('nav-pz-list')?'in list':(b.classList.contains('nav-pz-solo')?'solo card':'?'))).join(' | ')"))
    await pg.locator('.nav-pz-b[data-k=payout]').hover(); await pg.wait_for_timeout(250)
    await pg.screenshot(path='/tmp/ar_pay.png', full_page=True)
    await br.close()
asyncio.run(main())
