import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); document.addEventListener('DOMContentLoaded',()=>{const st=document.createElement('style'); st.textContent='*{overflow-anchor:none!important}'; document.head.append(st)})")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(1500)
    if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1200)   # plan first: skip
    for k,v in [('entry','30100'),('stop','30000'),('target','30200')]:
      await pg.locator(f'#tkSlide [data-tk={k}]').fill(v); await pg.wait_for_timeout(150)
    await pg.wait_for_timeout(800)
    res=[]
    for label in ["Sortie au stop","Sortie à l'objectif"]:
      b=pg.get_by_text(label, exact=True).first
      await b.scroll_into_view_if_needed(); await pg.wait_for_timeout(300)
      await pg.evaluate("""(lbl)=>{window.__f=[]; window.__stop=false; const tick=()=>{ setTimeout(()=>{const h=document.querySelector('#tkSlide .sc-tk'); const b=[...document.querySelectorAll('#tkSlide button')].find(x=>x.textContent.trim()===lbl); window.__f.push((h?((h.querySelector('.sc-tools')||{}).hidden?'T0':'T1')+(h.querySelector('.sc-skel')?'S':'')+(h.querySelector('.sc-card')?'M':''):'none')+'|'+(b?Math.round(b.getBoundingClientRect().top):'-'))},0); if(!window.__stop) requestAnimationFrame(tick)}; requestAnimationFrame(tick)}""", label)
      await b.tap(); await pg.wait_for_timeout(700)
      f=await pg.evaluate("window.__stop=true; window.__f")
      ch=[f[i] for i in range(1,len(f)) if f[i]!=f[i-1]]
      res.append(f"{label}: {'stable' if not ch else ch[:5]}")
    print(' | '.join(res), '| exit price now:', await pg.locator('#tkSlide [data-tk=exit]').input_value(), '| errors', errs[:2])
    await br.close()
asyncio.run(main())
