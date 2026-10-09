import asyncio, subprocess
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#settings'); await pg.wait_for_timeout(2500)
    print('Settings shows:', await pg.evaluate("(document.querySelector('.nav-ver')||{}).textContent"))
    b0=await pg.evaluate("document.querySelector('meta[name=sweep-build]').content")
    subprocess.run(['bash','-c','echo "<!-- deploy test -->" >> /tmp/g/app.html'])          # a new version is deployed
    # 1. typing in a field: nothing reloads, a banner offers the update
    await pg.evaluate("location.hash='#journal'"); await pg.wait_for_timeout(1500)
    b1=await pg.evaluate("document.querySelector('meta[name=sweep-build]').content")
    print('changing page reloaded to the new version:', b1!=b0)
    await pg.evaluate("document.querySelector('#main textarea, #main input:not([type=hidden])').focus()")
    await pg.evaluate("window.dispatchEvent(new Event('x'))")
    subprocess.run(['bash','-c','echo "<!-- deploy test 2 -->" >> /tmp/g/app.html'])
    await pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false}); document.dispatchEvent(new Event('visibilitychange'))"); await pg.wait_for_timeout(1500)
    print('while typing: banner shown =', await pg.locator('#navUpdate.on').count()==1, '| still same page (no reload):', await pg.evaluate("document.querySelector('meta[name=sweep-build]').content")==b1)
    await pg.locator('#navUpdate button').click(); await pg.wait_for_timeout(2000)
    print('« Update » loads the new version:', await pg.evaluate("document.querySelector('meta[name=sweep-build]').content")!=b1, '| errors', errs[:2])
    await br.close()
asyncio.run(main())
