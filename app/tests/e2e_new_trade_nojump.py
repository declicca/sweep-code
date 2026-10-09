import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='en-US',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); document.addEventListener('DOMContentLoaded',()=>{const st=document.createElement('style'); st.textContent='*{overflow-anchor:none!important}'; document.head.append(st)})")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    async def slow(route):
      if route.request.method in ('POST','PUT','PATCH','DELETE'): await asyncio.sleep(0.2)
      await route.continue_()
    await pg.route('**/api/**', slow)
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    # a brand-new trade from today: its chart is « ready Tuesday » (message instead of candles)
    await pg.evaluate("put('trades',{id:'nt-today',account_id:S.accounts[0].id,instrument:'NQ',date:'2026-10-04',entry_time:'22:50:00',exit_time:'22:52:00',direction:'long',contracts:1,entry:30100,exit:30200,stop:30000,target:30200,pnl_c:200000})"); await pg.wait_for_timeout(800)
    await pg.evaluate("location.hash='#trade/nt-today'"); await pg.wait_for_timeout(3000)
    print('chart block:', await pg.evaluate("(document.querySelector('.sc-card')||{}).className||'chart'"))
    await pg.evaluate("document.querySelector('.score').scrollIntoView({block:'start'}); scrollBy(0,-120)"); await pg.wait_for_timeout(500)
    await pg.evaluate("window.__pos=[]; const tick=()=>{ setTimeout(()=>{const s=document.querySelector('.score'); if(s) window.__pos.push(Math.round(s.getBoundingClientRect().top));},0); if(window.__pos.length<200) requestAnimationFrame(tick)}; requestAnimationFrame(tick)")
    btns=pg.locator('[data-act] >> text=/^(Yes|No|N\\/A)$/'); n=await btns.count()
    for i in [1,4,7,10]:
      if i<n: await btns.nth(i).tap(); await pg.wait_for_timeout(450)
    pos=await pg.evaluate("window.__pos"); jumps=[(i,pos[i-1],pos[i]) for i in range(1,len(pos)) if abs(pos[i]-pos[i-1])>2]
    print('new trade, 4 answers: jumps', jumps[:6] or 'none', '| errors', errs[:2])
    await pg.evaluate("del('trades','nt-today')")
    await br.close()
asyncio.run(main())
