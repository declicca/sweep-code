import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("try{sessionStorage.setItem('sw.modal','1')}catch(e){}")
    pg=await ctx.new_page(); navs=[]; pg.on('framenavigated', lambda f: f==pg.main_frame and navs.append(f.url))
    pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500); n0=len(navs)
    steps=[("hub then season (switch)", "SweepGame.open('hub'); setTimeout(()=>SweepGame.open('season'),700)"),
           ("close", "document.querySelector('#gSheet [data-g=close]').click()"),
           ("plan then review", "SweepGame.open('plan'); setTimeout(()=>SweepGame.open('review'),700)"),
           ("close instantly + open the menu", "document.querySelector('#gSheet [data-g=close]').click(); document.querySelector('.who').click()"),
           ("Escape", "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))"),
           ("trades, open the add form, close", "location.hash='#trades'; setTimeout(()=>{ openTicket(); setTimeout(()=>{ const s=document.querySelector('#gSheet [data-g=plan-skip]'); s&&s.click(); setTimeout(()=>closeTicket(),500) },600) },500)")]
    for name,js in steps:
      await pg.evaluate(js); await pg.wait_for_timeout(1800)
      print(f"{name:34} → still in the app: {pg.url.startswith(B)} | page: {pg.url.split('#')[-1]} | reloads: {len(navs)-n0}")
    # Back button: closes the sheet, stays on the page
    await pg.evaluate("SweepGame.open('hub')"); await pg.wait_for_timeout(900)
    await pg.go_back(); await pg.wait_for_timeout(900)
    print('back closes the sheet:', await pg.evaluate("!document.querySelector('#gSheet.open')"), '| still on', pg.url.split('#')[-1])
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
