import asyncio, sys
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(**p.devices['iPhone 13'], storage_state=STATE, locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    await pg.goto(B + '/?x=1#trades'); await pg.wait_for_timeout(4000)
    cnt="""()=>new Promise(res=>{let n=0; const m=document.getElementById('main'); const mo=new MutationObserver(r=>r.forEach(x=>{if(x.target===m) n+=x.addedNodes.length})); mo.observe(m,{childList:true}); setTimeout(()=>{mo.disconnect(); res(n)},2500)})"""
    p1=pg.evaluate(cnt); await pg.evaluate("syncNow()"); print('background sync, nothing changed → page redraws:', await p1)
    # a local save (the server adds its dates) then a sync
    await pg.evaluate("editDoc('trades', S.trades[0].id, d=>{d.notes=(d.notes||'')+' '})"); await pg.wait_for_timeout(2500)
    p2=pg.evaluate(cnt); await pg.evaluate("syncNow()"); print('after a save, sync → page redraws:', await p2)
    p3=pg.evaluate(cnt); await pg.evaluate("syncNow({manual:true})"); print('manual refresh (pull) → page redraws:', await p3)
    # real change from elsewhere: another device adds a trade on the server
    await pg.evaluate("fetch('api/data',{method:'GET'})"); 
    await br.close()
asyncio.run(main())
