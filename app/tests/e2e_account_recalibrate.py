import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#accounts'); await pg.wait_for_timeout(2500)
    aid=await pg.evaluate("S.accounts.find(a=>a.status!=='archived').id")
    bal0=await pg.evaluate(f"acctState(getDoc('accounts','{aid}')).bal")
    await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(1800)
    box=pg.locator('#main .nav-recal'); await box.scroll_into_view_if_needed()
    print('card:', (await box.inner_text()).replace('\n',' | ')[:200])
    real=(bal0-42088)/100   # the platform shows $420.88 less
    i=box.locator('[data-recal=bal]'); await i.fill(f'{real:.2f}'); await box.locator('[data-recal-go=bal]').click(); await pg.wait_for_timeout(1000)
    bal1=await pg.evaluate(f"acctState(getDoc('accounts','{aid}')).bal")
    print('Sweep balance', bal0/100, '→', bal1/100, '(platform', real, ') | adjustments:', await pg.evaluate(f"JSON.stringify(getDoc('accounts','{aid}').adjustments.map(x=>x.amount_c))"))
    a2=box.locator('[data-recal=amt]'); await a2.fill('-25'); await box.locator('[data-recal-go=amt]').click(); await pg.wait_for_timeout(800)
    print('after a manual -25:', (await pg.evaluate(f"acctState(getDoc('accounts','{aid}')).bal"))/100)
    await box.screenshot(path='/tmp/recal.png')
    # the accounts list and Today use the same balance
    await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
    exp=f"{(bal0-42088-2500)/100:,.2f}"
    shown=await pg.evaluate(f"document.querySelector('#main').innerText.includes('{exp}')")
    print(f'accounts list shows the recalibrated balance ({exp}):', shown)
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
    print('Today shows it too:', await pg.evaluate(f"document.querySelector('#main').innerText.includes('{exp}')"))
    # undo both
    await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(1500)
    for _ in range(2):
      rm=pg.locator('#main .nav-recal [data-recal-rm]').first; await rm.scroll_into_view_if_needed(); await rm.click(); await pg.wait_for_timeout(800)
    print('after removing both:', (await pg.evaluate(f"acctState(getDoc('accounts','{aid}')).bal"))/100, '(back to', bal0/100, ')')
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
