import asyncio, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for who in ['new','mateo']:
      ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA', **({'storage_state':'/tmp/show_state.json'} if who=='mateo' else {}))
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{}}))")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      if who=='new':
        u='hs%d'%random.randint(1000,9999)
        await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
        await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
        await pg.evaluate("put('accounts',{id:'a-hs',name:'50K',firm_id:'',starting_balance_c:5000000,status:'active'})"); await pg.wait_for_timeout(1200); await pg.reload()
      else: await pg.goto(B+'/?x=1#dashboard')
      await pg.wait_for_timeout(3000)
      await pg.evaluate("SweepGame.open('hub')"); await pg.wait_for_timeout(2500)
      print(who, '| steps:', await pg.evaluate("[...document.querySelectorAll('#gSheet .gc-step')].map(b=>(b.classList.contains('done')?'✓ ':b.classList.contains('next')?'→ ':'· ')+b.querySelector('b').textContent).join(' | ')"))
      await pg.screenshot(path=f'/tmp/hub_{who}.png')
      nx=pg.locator('#gSheet .gc-step.next').first
      if await nx.count():
        await nx.click(); await pg.wait_for_timeout(600)
        print('   tap the next step →', (await pg.locator('#gSheet .g-cel').inner_text()).replace('\n',' / ')[:160])
        go=pg.locator('#gSheet [data-g=node-go]')
        if await go.count():
          await go.click(); await pg.wait_for_timeout(900)
          print('   « Y aller » opens:', 'goal questions' if await pg.locator('#gOb').count() else ('journal sheet' if await pg.locator('#gSheet .g-car').count() else await pg.evaluate("location.hash")))
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
