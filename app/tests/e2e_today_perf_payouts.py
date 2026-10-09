import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,17,20,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=1 if not mob else 2,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='en-US',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{analytics:1}}))")
      pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
      await pg.evaluate("AI.on = true; document.body.classList.add('ai-on'); askShow(true); render()"); await pg.wait_for_timeout(800)
      r=await pg.evaluate("""(()=>{const cta=document.querySelector('#gToday .gc-cta'); const k=cta&&cta.dataset.g; const ctaVis=cta? getComputedStyle(cta).display!=='none' : false;
        const pf=document.querySelector('.d-perf').getBoundingClientRect(), py=document.querySelector('.d-pay').getBoundingClientRect();
        const qa=[...document.querySelectorAll('.d-quick .nav-q span')].map(s=>s.textContent);
        return 'day card button: '+k+' '+(ctaVis?'shown':'hidden')+' | payouts right under Day/Week: gap '+Math.round(py.top-pf.bottom)+'px | quick access: '+(qa.join(', ')||'(phone: none)')})()""")
      print(w, r)
      print('   when the next step is « Add a trade »:', await pg.evaluate("(()=>{const c=document.querySelector('#gToday .gc-cta'); if(!c) return 'no button'; c.dataset.g='add'; return getComputedStyle(c).display==='none' ? 'hidden (title-row button instead)' : 'shown'})()"))
      await pg.locator('.d-perf').scroll_into_view_if_needed()
      bb=await pg.evaluate("(()=>{const a=document.querySelector('.d-perf').getBoundingClientRect(), b=document.querySelector('.d-pay').getBoundingClientRect(); return {x:Math.min(a.left,b.left),y:a.top,w:Math.max(a.right,b.right)-Math.min(a.left,b.left),h:b.bottom-a.top}})()")
      await pg.screenshot(path=f'/tmp/r4_{w}.png', clip={'x':bb['x']-4,'y':bb['y']-4,'width':bb['w']+8,'height':bb['h']+8})
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
