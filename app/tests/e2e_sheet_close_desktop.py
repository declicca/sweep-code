import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900},locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    for k in ['plan','review','hub']:
      await pg.evaluate(f"SweepGame.open('{k}')"); await pg.wait_for_timeout(700)
      # watch the closing sheet's position frame by frame
      await pg.evaluate("""window.__fr=[]; const el=document.getElementById('gSheet'); (function f(){ const r=el.getBoundingClientRect(); window.__fr.push(Math.round(r.left+r.width/2)); if(el.isConnected && window.__fr.length<40) requestAnimationFrame(f) })(); el.querySelector('[data-g=close]').click()""")
      await pg.wait_for_timeout(700)
      fr=await pg.evaluate("window.__fr")
      fr=[x for x in fr if x]; print(f"{k:7} centre during closing: {sorted(set(fr))} (screen centre 720)")
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
