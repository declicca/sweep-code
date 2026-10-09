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
      print(w,'| sign-up shows:', await pg.evaluate("['nameF','userF','emailF','passF','askF','consentF'].filter(i=>!document.getElementById(i).hidden).join(',')"), '| title/steps visible:', await pg.evaluate("!document.getElementById('h').hidden || !document.getElementById('sub').hidden"), '| note:', await pg.evaluate("document.getElementById('consentNote').innerText.slice(0,60)"))
      if mob: await pg.screenshot(path='/tmp/sg3_1.png')
      em='new%d@gmail.com'%random.randint(1000,99999)
      await pg.fill('#email', em); await pg.fill('#password','Testpass123!x'); await pg.wait_for_timeout(2100); await pg.click('#go'); await pg.wait_for_timeout(3500)
      print('   straight in:', '/auth' not in pg.url, '| profile window:', await pg.evaluate("(document.querySelector('.nav-prof h2')||{}).textContent||'none'"), '| username suggested:', await pg.evaluate("(document.querySelector('.nav-prof [data-pf=username]')||{}).value"))
      if mob: await pg.screenshot(path='/tmp/sg3_2.png')
      await pg.fill('.nav-prof [data-pf=first_name]','Alex'); await pg.fill('.nav-prof [data-pf=last_name]','Martin'); await pg.select_option('.nav-prof [data-pf=found_via]','tiktok'); await pg.fill('.nav-prof [data-pf=accounts_info]','3 × Apex 50K')
      await pg.click('.nav-prof [data-prof-go]'); await pg.wait_for_timeout(1500)
      print('   after Continue: window closed:', await pg.locator('.nav-prof').count()==0, '| greeting:', await pg.evaluate("(document.querySelector('.nav-greet, .nav-hi, [class*=greet]')||{}).textContent||''"), '| me:', await pg.evaluate("S.me.first_name+' '+S.me.last_name+' / '+S.me.full_name"))
      await pg.evaluate("location.hash='#settings'"); await pg.wait_for_timeout(1500)
      print('   settings: profile fields:', await pg.evaluate("[...document.querySelectorAll('.nav-set-prof [data-pf]')].map(i=>i.dataset.pf+'='+i.value).join(' | ')"), '| support:', await pg.evaluate("(document.querySelector('.nav-set-help a')||{}).textContent"))
      if not mob: await pg.screenshot(path='/tmp/sg3_set.png')
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
