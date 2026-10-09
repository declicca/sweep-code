import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#accounts'); await pg.wait_for_timeout(2500)
      aid=await pg.evaluate("S.accounts.find(a=>a.status!=='archived').id"); old=await pg.evaluate(f"getDoc('accounts','{aid}').name")
      await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(1800)
      b=pg.locator('#main .nav-accname'); print(w, '| pencil in the title:', await b.count(), '| y:', await b.evaluate("e=>Math.round(e.getBoundingClientRect().top)"))
      await pg.locator('#main > .row').first.screenshot(path=f'/tmp/ren_{w}.png')
      await b.click(); await pg.wait_for_timeout(300)
      i=pg.locator('#main .nav-accname-in'); await i.fill('Topstep Combine #2'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(1200)
      print('   saved:', await pg.evaluate(f"getDoc('accounts','{aid}').name"), '| title now:', await pg.locator('#main .nav-accname').inner_text())
      await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1000)
      print('   accounts list shows it:', await pg.evaluate("document.querySelector('#main').innerText.includes('Topstep Combine #2')"))
      # Escape cancels
      await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(1200)
      await pg.locator('#main .nav-accname').click(); await pg.locator('#main .nav-accname-in').fill('Nope'); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(700)
      print('   Escape keeps:', await pg.evaluate(f"getDoc('accounts','{aid}').name"))
      await pg.evaluate(f"editDoc('accounts','{aid}',d=>{{d.name={old!r}}})"); await pg.wait_for_timeout(1200)
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
