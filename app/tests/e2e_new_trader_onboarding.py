import asyncio, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,locale='fr-CA')
    u='ob%d'%random.randint(1000,9999)
    await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2000)
    # new trader: the guided steps (Topstep → 50K)
    await pg.locator('[data-st-firm=topstep]').first.click(); await pg.wait_for_timeout(300)
    await pg.locator('[data-st-size="50000"]').first.click(); await pg.wait_for_timeout(300)
    print('onboarding form filled by the steps:', await pg.evaluate("(()=>{const f=document.querySelector('form[data-form=account]'); return [(f.querySelector('[name=firmName]')||{}).value,(f.querySelector('[name=name]')||{}).value,(f.querySelector('[name=start]')||{}).value].join(' | ')})()"))
    await pg.locator('form[data-form=account] button[type=submit]').first.click(); await pg.wait_for_timeout(3000)
    await pg.evaluate("typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(4500)
    print('onboarding before first trade:', await pg.locator('#gOb').count(), '| tour:', await pg.locator('.gd-tour').count())
    for _ in range(8):
      b=pg.locator('[data-gd=t-next], [data-gd=t-end]')
      if await b.count(): await b.first.click(); await pg.wait_for_timeout(400)
    print('checklist:', await pg.evaluate("[...document.querySelectorAll('.gd-steps .gd-st-t')].map(e=>e.textContent).join(' | ')"))
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1500)
    await pg.screenshot(path='/tmp/empty_trades.png')
    print('empty card:', await pg.locator('.ux-empty').count())
    await pg.evaluate("location.hash='#analytics'"); await pg.wait_for_timeout(1500); await pg.screenshot(path='/tmp/empty_an.png')
    await pg.evaluate("put('trades',{id:'t-ob',account_id:S.accounts[0].id,instrument:'NQ',date:'2026-10-02',entry_time:'10:00:00',direction:'long',contracts:1,entry:100,exit:101,stop:99,pnl_c:2000})"); await pg.wait_for_timeout(1000)
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(5000)
    print('onboarding after first trade:', await pg.locator('#gOb').count(), 'steps dots:', await pg.locator('#gOb .g-ob-dots i, #gOb [class*=dots] i').count())
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1200); print('empty card after trade:', await pg.locator('.ux-empty').count())
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
