import asyncio, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:200])); pg.on('console', lambda m: m.type=='error' and errs.append(m.text[:150]))
    u='gq%d'%random.randint(1000,9999)
    await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
    await pg.evaluate("put('accounts',{id:'a-gq',name:'50K',firm_id:'',starting_balance_c:5000000,status:'active'})"); await pg.wait_for_timeout(1200); await pg.reload(); await pg.wait_for_timeout(3000)
    await pg.evaluate("SweepGame.open('hub')"); await pg.wait_for_timeout(2500)
    await pg.locator('#gSheet .gc-step.next').click(); await pg.wait_for_timeout(500)
    await pg.locator('#gSheet [data-g=node-go]').click(); await pg.wait_for_timeout(1200)

    print('goal questions open:', await pg.locator('#gOb').count(), '| text:', (await pg.locator('#gOb').inner_text())[:120].replace('\n',' / ') if await pg.locator('#gOb').count() else '', '| errors', errs[:4])
    await br.close()
asyncio.run(main())
