import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1276,800,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      res=[]
      for route,act in [('#payouts',"(()=>{const s=document.querySelector('#main select'); if(s){s.selectedIndex=Math.min(1,s.options.length-1); s.dispatchEvent(new Event('change',{bubbles:true}))}})()"),('#journal',"(()=>{const b=[...document.querySelectorAll('#main button')].find(x=>/^(Oui|Non)$/.test(x.textContent.trim())); b&&b.click()})()")]:
        await pg.goto(B+'/?x=1'+route); await pg.wait_for_timeout(2000)
        await pg.evaluate(act); await pg.wait_for_timeout(900)
        r=await pg.evaluate("[...document.querySelectorAll('#main .nav-seg')].map(seg=>{const th=seg.querySelector('.nav-thumb'), on=seg.querySelector('.on'); if(!th||!on) return 'no thumb'; const a=th.getBoundingClientRect(), b=on.getBoundingClientRect(), s=seg.getBoundingClientRect(); return (Math.abs(a.left-b.left)<2 && a.right<=s.right+1 ? 'thumb on the selected tab' : 'THUMB OUT OF PLACE '+Math.round(a.left)+' vs '+Math.round(b.left))}).join(', ')")
        res.append(f"{route}: {r}")
      print(w, ' | '.join(res)); await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
