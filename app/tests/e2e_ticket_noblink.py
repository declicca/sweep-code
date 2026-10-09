import asyncio, datetime, json, sys
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
TODAY = len(sys.argv)>1   # today's date: the « ready Tuesday » message; otherwise a past date with a real chart
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); document.addEventListener('DOMContentLoaded',()=>{const st=document.createElement('style'); st.textContent='*{overflow-anchor:none!important}'; document.head.append(st)})")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(800)
    if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(800)   # plan first: skip
    if not TODAY:
      await pg.evaluate("(()=>{const d=document.querySelector('#tkSlide [data-tk=date]'); d.value='2026-09-29'; d.dispatchEvent(new Event('input',{bubbles:true})); d.dispatchEvent(new Event('change',{bubbles:true})); const t=document.querySelector('#tkSlide [data-tk=entryTime]'); t.value='10:00:00'; t.dispatchEvent(new Event('input',{bubbles:true})); t.dispatchEvent(new Event('change',{bubbles:true}))})()")
    await pg.wait_for_timeout(2500)
    state=await pg.evaluate("(()=>{const h=document.querySelector('#tkSlide .sc-tk'); return h? (h.hidden?'hidden':(h.querySelector('.sc-card')?'message':(h.querySelector('canvas')?'chart':'other'))):'none'})()")
    # watch every frame: does the chart block change (toolbar appears, blank box…) or the form jump when tapping Buy / Sell?
    await pg.evaluate("window.__f=[]; window.__stop=false; const tick=()=>{ setTimeout(()=>{const h=document.querySelector('#tkSlide .sc-tk'); const s=h? ((h.querySelector('.sc-tools')||{}).hidden?'T0':'T1')+(h.querySelector('.sc-skel')?'S':'')+(h.querySelector('.sc-card')?'M':'')+(h.querySelector('canvas')?'C':'')+':'+Math.round(h.getBoundingClientRect().top) : 'none'; window.__f.push(s)},0); if(!window.__stop) requestAnimationFrame(tick)}; requestAnimationFrame(tick)")
    for sel in ['[data-tk-dir=short], [data-v=short]','[data-tk-dir=long], [data-v=long]']:
      b=pg.locator('#tkSlide '+sel.split(', ')[0]+', #tkSlide '+sel.split(', ')[1]).first
      if await b.count(): await b.tap(); await pg.wait_for_timeout(500)
    frames=await pg.evaluate("window.__stop=true; window.__f")
    changes=[frames[i] for i in range(1,len(frames)) if frames[i]!=frames[i-1]]
    print(('today' if TODAY else 'past date'), '| chart block:', state, '| changes while tapping Buy/Sell:', changes[:8] or 'none', '| errors', errs[:2])
    await br.close()
asyncio.run(main())
