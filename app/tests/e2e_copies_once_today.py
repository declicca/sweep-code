import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.kpiTab','day')")
      pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,5,16,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      if w==1440:
        accs=await pg.evaluate("S.accounts.slice(0,5).map(a=>a.id)")
        for i,a in enumerate(accs):
          await pg.evaluate(f"put('trades',{{id:'cg-{i}',copy_group:'g-test',account_id:'{a}',instrument:'NQ',date:'2026-10-05',entry_time:'09:57:00',direction:'short',contracts:1,entry:30100,exit:30040,pnl_c:120150,pnl_manual:true,setup:'Reversal',emo:{{}},review:{{}},discipline:{{}}}})")
        await pg.evaluate("put('trades',{id:'cg-solo',account_id:'"+accs[0]+"',instrument:'NQ',date:'2026-10-05',entry_time:'10:30:00',direction:'long',contracts:1,pnl_c:-30000,pnl_manual:true,emo:{},review:{},discipline:{}})")
        await pg.wait_for_timeout(1200); await pg.evaluate("render()"); await pg.wait_for_timeout(800)
      r=await pg.evaluate("(()=>{const c=document.querySelector('.d-perf'); return c.querySelector('.nav-kpi-b').innerText.replace(/\\n/g,' ')+' || '+[...c.querySelectorAll('.nav-tr')].map(a=>a.innerText.replace(/\\n/g,' ')).join(' | ')})()")
      print(w, r)
      await pg.locator('.d-perf .nav-trs').screenshot(path=f'/tmp/cpg_{w}.png')
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
