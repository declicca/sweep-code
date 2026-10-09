import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); dev=p.devices['iPhone 13']
    for state in ['/tmp/show_state.json','/home/claude/media/alex_state.json']:
      for h in ['#dashboard','#trades','#analytics','#accounts','#payouts','#journal','#calendar','#settings','#journal/weekly','#trade/'+('sc-035-xfa' if 'alex' in state else 'demo-t1')]:
        ctx=await br.new_context(**dev, storage_state=state, locale='fr-CA'); pg=await ctx.new_page()
        await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
        cdp=await ctx.new_cdp_session(pg); await cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        await pg.goto('http://127.0.0.1:8095/?x=1'+h); await pg.wait_for_timeout(4000)
        r=await pg.evaluate("""new Promise(res=>{let n=0; const seen={}; const mo=new MutationObserver(recs=>{n+=recs.length; recs.forEach(r=>{const t=r.target; const k=(t.className&&String(t.className).slice(0,30))||t.tagName; seen[k]=(seen[k]||0)+1})}); mo.observe(document.body,{childList:true,subtree:true,attributes:true,characterData:true}); let lt=0; const po=new PerformanceObserver(l=>l.getEntries().forEach(e=>lt+=e.duration)); try{po.observe({type:'longtask',buffered:false})}catch(e){} setTimeout(()=>{mo.disconnect(); po.disconnect(); res({mutations:n, longtask_ms:Math.round(lt), top:Object.entries(seen).sort((a,b)=>b[1]-a[1]).slice(0,4)})},3000)})""")
        print(state.split('/')[-1][:5], h, r)
        await ctx.close()
    await br.close()
asyncio.run(main())
