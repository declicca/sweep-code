import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    tid=await pg.evaluate("S.trades.filter(t=>t.demo)[0].id")
    await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(3000)
    await pg.evaluate("document.querySelector('.score').scrollIntoView({block:'start'}); scrollBy(0,-120)"); await pg.wait_for_timeout(500)
    # watch, frame by frame, where the score card sits on screen while answering 4 questions
    await pg.evaluate("window.__pos=[]; const tick=()=>{const s=document.querySelector('.score'); if(s) window.__pos.push(Math.round(s.getBoundingClientRect().top)); if(window.__pos.length<400) requestAnimationFrame(tick)}; requestAnimationFrame(tick)")
    btns=pg.locator('[data-act] >> text=/^(Oui|Non|N\\/A)$/')
    n=await btns.count(); idx=[1,5,7,10]
    for i in idx:
      if i<n: await btns.nth(i).tap(); await pg.wait_for_timeout(450)
    pos=await pg.evaluate("window.__pos")
    jumps=[(i,pos[i-1],pos[i]) for i in range(1,len(pos)) if abs(pos[i]-pos[i-1])>2]
    print('frames watched:', len(pos), '| position changes:', jumps[:10])
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
