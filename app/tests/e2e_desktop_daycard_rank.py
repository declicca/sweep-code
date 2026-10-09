import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w in [1280,1440,1920]:
      ctx=await br.new_context(viewport={'width':w,'height':900},color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{analytics:1}}))")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(4000)
      r=await pg.evaluate("""(()=>{const d=document.querySelector('.d-today').getBoundingClientRect(), c=document.querySelector('.d-today .gc-cta'), cr=c&&c.getBoundingClientRect(), rk=document.querySelector('.d-today .d-rank').getBoundingClientRect(); return 'CTA fully visible: '+(cr && cr.right<=d.right+1 && c.scrollWidth<=c.clientWidth+1)+' | rank '+(rk.top>=d.top+40 ? 'under' : 'on the right')+' | card '+Math.round(d.width)+'x'+Math.round(d.height)})()""")
      print(w, r)
      el=pg.locator('.d-today'); await el.screenshot(path=f'/tmp/dt_{w}.png'); await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
