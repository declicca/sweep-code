import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w in [1280,1440,2060]:
      ctx=await br.new_context(viewport={'width':w,'height':1000},color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{analytics:1}}))")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(4000)
      r=await pg.evaluate("""(()=>{const a=document.querySelector('.d-col-a'), b=document.querySelector('.d-col-b'); const last=(c)=>[...c.children].filter(e=>e.offsetParent).sort((x,y)=>x.getBoundingClientRect().bottom-y.getBoundingClientRect().bottom).pop(); const la=last(a), lb=last(b); const order=[...b.children].filter(e=>e.offsetParent).sort((x,y)=>x.getBoundingClientRect().top-y.getBoundingClientRect().top).map(e=>[...e.classList].find(c=>c.startsWith('d-'))).join(' → ');
        return 'column bottoms '+Math.round(la.getBoundingClientRect().bottom)+' / '+Math.round(lb.getBoundingClientRect().bottom)+' | right column: '+order+' | « '+getComputedStyle(document.querySelector('#title'),'::before').content+' »'})()""")
      print(w, r)
      if w==1440: await pg.screenshot(path='/tmp/eq_1440.png', full_page=True)
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
