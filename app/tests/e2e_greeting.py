import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(390,844,True),(1440,900,False)]:
      for lang in ['fr','en','es']:
        ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=3 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='en-US',storage_state='/tmp/show_state.json')
        await ctx.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
        pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
        await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
        r=await pg.evaluate("""(()=>{const t=document.querySelector('#title'), g=document.querySelector('#main > .greet'), cs=getComputedStyle(t,'::before'); const tr=t.getBoundingClientRect(), gr=g.getBoundingClientRect(); return '« '+cs.content.replace(/"/g,'')+' » / « '+t.textContent+' » / « '+g.textContent+' » | gap title→date '+Math.round(gr.top-tr.bottom)+'px'})()""")
        print(f'{w} {lang}: {r}')
        if lang=='fr': await pg.screenshot(path=f'/tmp/g3_{w}.png', clip={'x':0,'y':0,'width':w,'height':260 if mob else 220})
        if lang=='fr':
          await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1200)
          print('   on Trades the greeting line is gone:', await pg.evaluate("getComputedStyle(document.querySelector('#title'),'::before').content in {'none':1,'normal':1} || !document.querySelector('.top.nav-3l')"))
        await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
