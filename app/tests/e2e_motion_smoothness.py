import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for label,kw,cpu in [('phone (4× slower CPU)',p.devices['iPhone 13'],4),('computer',{'viewport':{'width':1440,'height':900}},1)]:
      ctx=await br.new_context(**kw, storage_state='/home/claude/media/alex_state.json'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
      cdp=await ctx.new_cdp_session(pg); await cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu})
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
      res=[]
      for h in ['#trades','#analytics','#accounts','#dashboard','#payouts','#journal']:
        r=await pg.evaluate("""(h)=>new Promise(res=>{let frames=[], lt=0; const po=new PerformanceObserver(l=>l.getEntries().forEach(e=>lt+=e.duration)); try{po.observe({type:'longtask'})}catch(e){}
          const t0=performance.now(); let last=t0; function f(t){frames.push(t-last); last=t; if(t-t0<900) requestAnimationFrame(f); else {po.disconnect(); const slow=frames.filter(x=>x>34).length; res({ms:Math.round(t-t0), frames:frames.length, slow, worst:Math.round(Math.max(...frames)), longtask:Math.round(lt)})}}
          location.hash=h; requestAnimationFrame(f)})""", h)
        res.append(f"{h}: {r['frames']} frames, {r['slow']} slow, worst {r['worst']} ms, blocked {r['longtask']} ms")
      print('==',label); [print('  ',x) for x in res]
      await ctx.close()
    await br.close()
asyncio.run(main())
