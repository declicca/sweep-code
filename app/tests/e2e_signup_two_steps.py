import asyncio, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA')
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/auth.html?signup=1'); await pg.wait_for_timeout(1500)
      vis=lambda: pg.evaluate("['nameF','userF','emailF','passF','askF','consentF'].filter(i=>!document.getElementById(i).hidden).join(',')")
      print(w,'| step 1:', await pg.evaluate("document.getElementById('h').textContent+' / '+document.getElementById('sub').textContent"), '| fields:', await vis(), '| button:', await pg.evaluate("document.getElementById('go').textContent"))
      if mob: await pg.screenshot(path='/tmp/sg1.png')
      em='lead%d@t.dev'%random.randint(1000,99999)
      await pg.fill('#email', em); await pg.fill('#password', 'Testpass123!x'); await pg.click('#go'); await pg.wait_for_timeout(1200)
      print('   step 2:', await pg.evaluate("document.getElementById('h').textContent+' / '+document.getElementById('sub').textContent"), '| fields:', await vis(), '| button:', await pg.evaluate("document.getElementById('go').textContent"))
      if mob: await pg.screenshot(path='/tmp/sg2.png')
      lead=await pg.evaluate(f"fetch('api/auth/config').then(()=>1)")
      # one word only → asks for first and last name
      await pg.fill('#fullname','Alex'); await pg.fill('#username','u%d'%random.randint(1000,99999)); await pg.check('#consent'); await pg.click('#go'); await pg.wait_for_timeout(800)
      print('   one word:', await pg.evaluate("document.getElementById('err').textContent"))
      await pg.fill('#fullname','Alex Martin'); await pg.click('#go'); await pg.wait_for_timeout(3000)
      print('   created, in the app:', pg.url.endswith('/') or '#' in pg.url, '| full name:', await pg.evaluate("(window.S&&S.me&&S.me.full_name)||'?'"))
      print('   lead kept:', em)
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
