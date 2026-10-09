import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/home/claude/media/alex_state.json', locale='en-US', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    cdp=await ctx.new_cdp_session(pg); await cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(4000)
    for h in ['#trades','#analytics','#accounts','#dashboard']:
      # sample the opacity of the first content block every frame for 6 s: a re-appearance shows as a second drop
      r=await pg.evaluate("""(h)=>new Promise(res=>{const vals=[]; const t0=performance.now(); location.hash=h;
        function f(){const m=document.querySelector('#main'); const el=m && [...m.children].find(e=>e.offsetHeight>40); const cs=el&&getComputedStyle(el); const o=el? +cs.opacity : -1; const tt=Math.round(performance.now()-t0); vals.push([tt, Math.round(o*100)/100, (tt>900&&o<0.6)? (cs.animationName+' | '+el.tagName+'.'+String(el.className).slice(0,40)+' | parentAnim '+getComputedStyle(m).animationName+' | mainClass '+m.className) : '']); if(performance.now()-t0<6000) requestAnimationFrame(f); else res(vals)} requestAnimationFrame(f)})""", h)
      drops=[]; prev=1; started=False
      info=[x[2] for x in r if x[2]][:2]
      for t,o,_ in r:
        if o<0.5 and prev>=0.95: drops.append(t)
        prev=o
      first_visible=next((t for t,o,_ in r if o>=0.95), None)
      print(info); print(f"{h}: fades from 0 at {drops} ms, fully visible at {first_visible} ms, opacity drops after 1 s: {[d for d in drops if d>1000]}")
    await br.close()
asyncio.run(main())
