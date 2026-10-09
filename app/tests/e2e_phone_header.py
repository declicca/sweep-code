import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for lang in ['en','fr']:
      ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=3,is_mobile=True,has_touch=True,color_scheme='dark',locale='en-US',storage_state='/tmp/show_state.json')
      await ctx.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
      pg=await ctx.new_page(); await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
      print(lang, await pg.evaluate("""(()=>{const r=e=>e.getBoundingClientRect(); const h=r(document.querySelector('.nav-hday')), d=r(document.querySelector('.nav-dash')), t=r(document.querySelector('#title')), g=r(document.querySelector('#main > .greet')), hp=getComputedStyle(document.querySelector('.nav-hplus')), bp=getComputedStyle(document.querySelector('#bottomnav .plus'));
        return 'right edge: header '+Math.round(h.right)+' vs cards '+Math.round(d.right)+' | title→greeting gap '+Math.round(g.top-t.bottom)+'px | « + » radius '+hp.borderRadius+' vs '+bp.borderRadius+', same gradient: '+(hp.backgroundImage.slice(0,40)===bp.backgroundImage.slice(0,40)) + ' | title fits: '+(document.querySelector('#title').scrollWidth<=document.querySelector('#title').clientWidth)})()"""))
      await pg.screenshot(path=f'/tmp/hdr_{lang}.png', clip={'x':0,'y':0,'width':390,'height':220}); await ctx.close()
    await br.close()
asyncio.run(main())
