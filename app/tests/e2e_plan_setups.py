import asyncio, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{}}))")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    u='su%d'%random.randint(1000,9999)
    await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
    await pg.evaluate("put('accounts',{id:'a-su',name:'50K',firm_id:'',starting_balance_c:5000000,status:'active'})"); await pg.wait_for_timeout(1500)
    await pg.reload(); await pg.wait_for_timeout(3000)
    await pg.evaluate("SweepGame.open('plan')"); await pg.wait_for_timeout(1200)
    print('setups offered:', await pg.evaluate("[...document.querySelectorAll('#gSheet .g-setups .chip')].map(b=>b.textContent.trim()).join(' | ')"))
    await pg.locator('#gSheet [data-g=bias][data-v=bullish]').click()
    await pg.locator('#gSheet .g-setups .chip', has_text='Liquidity sweep').click()
    await pg.locator('#gSheet [data-g=setup-new]').click(); await pg.locator('#gSheet [data-g-newsetup]').fill('Silver Bullet'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(300)
    await pg.locator('#gSheet [data-gp=max_loss]').fill('500')
    await pg.locator('#gSheet .g-setups').screenshot(path='/tmp/plsu.png')
    print('selected:', await pg.evaluate("[...document.querySelectorAll('#gSheet .g-setups .chip.on')].map(b=>b.textContent.trim()).join(' | ')"))
    await pg.locator('#gSheet [data-g=save-plan]').click(); await pg.wait_for_timeout(1500)
    print('saved in settings:', await pg.evaluate("JSON.stringify(S.settings.setups)"), '| in the plan:', await pg.evaluate("JSON.stringify(Object.values(S.journals||{}).length ? null : (S.journals||[]).map?.(j=>j.pre&&j.pre.setups))"))
    await pg.evaluate("SweepGame.open('plan')"); await pg.wait_for_timeout(1000)
    print('next plan shows them as own setups:', await pg.evaluate("[...document.querySelectorAll('#gSheet .g-setups .chip:not(.g-sug)')].map(b=>b.textContent.trim()).join(' | ')"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
