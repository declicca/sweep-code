import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
PAGES=['#dashboard','#trades','#calendar','#journal','#analytics','#accounts','#payouts','#settings','#news']
SIZES=[(360,640,True,'small phone'),(430,932,True,'large phone'),(768,1024,True,'tablet portrait'),(1024,768,False,'tablet landscape'),(1280,800,False,'laptop'),(1920,1080,False,'large screen'),(2560,1440,False,'very large')]
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob,name in SIZES:
      ctx=await br.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      bad=[]
      for r in PAGES:
        await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(1100)
        res=await pg.evaluate("""(()=>{const o=[]; const W=document.documentElement.clientWidth;
          if(document.documentElement.scrollWidth>W+1) o.push('page scrolls sideways ('+document.documentElement.scrollWidth+'>'+W+')');
          // visible elements sticking out of the screen (not inside a scroll container)
          const out=[...document.querySelectorAll('#main *, .main-wrap .top *')].filter(e=>{const r=e.getBoundingClientRect(); if(!r.width||!r.height) return false; if(r.right<=W+1 && r.left>=-1) return false; let p=e.parentElement; while(p&&p!==document.body){const cs=getComputedStyle(p); if(/(auto|scroll|hidden)/.test(cs.overflowX)) return false; p=p.parentElement;} return true;});
          if(out.length) o.push(out.length+' element(s) off screen: '+out.slice(0,2).map(e=>e.tagName.toLowerCase()+'.'+String(e.className).split(' ')[0]).join(', '));
          // title row: buttons overlapping the title text
          const t=document.querySelector('.main-wrap .top #title'), btns=[...document.querySelectorAll('.main-wrap .top .nav-hday:not([hidden]), .main-wrap .top .nav-addtop:not([hidden])')];
          if(t){const tr=t.getBoundingClientRect(); const rng=document.createRange(); rng.selectNodeContents(t); const txt=[...rng.getClientRects()].filter(x=>x.width>0); for(const b of btns){const br=b.getBoundingClientRect(); if(!br.width) continue; for(const x of txt){ if(x.right>br.left+1 && x.left<br.right && x.bottom>br.top && x.top<br.bottom) { o.push('title text under '+b.className.split(' ')[0]); break; } }}}
          return o;})()""")
        if res: bad.append(r+': '+'; '.join(res))
      print(f"{name:16} {w}x{h}: " + ('all 9 pages clean' if not bad else ' | '.join(bad)))
      await pg.screenshot(path=f'/tmp/size_{w}.png')
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
