import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for w,mob in [(1440,False),(390,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':900 if not mob else 844},device_scale_factor=2,is_mobile=mob,has_touch=mob, storage_state='/home/claude/media/alex_state.json', color_scheme='dark', locale='fr-CA'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      await pg.goto('http://127.0.0.1:8095/?x=1#payouts'); await pg.wait_for_timeout(3000)
      r=await pg.evaluate("""(()=>{const fb=document.querySelector('#main > .fbars')||document.querySelector('#main > .mfb'); if(!fb) return 'phone: '+[...document.querySelector('#main').children].slice(0,4).map(e=>e.tagName+'.'+String(e.className).slice(0,30)+' y'+Math.round(e.getBoundingClientRect().top)+' h'+Math.round(e.getBoundingClientRect().height)).join(' | ')+' || share in: '+(document.querySelector('#main .sh-btn')||{parentElement:{className:'none'}}).parentElement.className; const ctl=[...fb.children].filter(e=>!e.classList.contains('nav-sh-fb')&&e.offsetParent); const sel=ctl[0]&&ctl[0].getBoundingClientRect(); const b=fb.querySelector('.sh-btn'); if(!b) return 'no button'; const B=b.getBoundingClientRect(); const main=document.querySelector('#main').getBoundingClientRect();
        const kp=document.querySelector('#main .kpis'); const K=kp&&kp.getBoundingClientRect();
        return 'dropdown mid '+Math.round(sel.top+sel.height/2)+' h'+Math.round(sel.height)+' | button mid '+Math.round(B.top+B.height/2)+' h'+Math.round(B.height)+' | button right '+Math.round(B.right)+' vs numbers right '+(K?Math.round(K.right):'-')})()""")
      print(w, r)
      await pg.screenshot(path=f'/tmp/pfb_{w}.png', clip={'x':0,'y':0,'width':w,'height':360 if not mob else 420})
      await ctx.close()
    await br.close()
asyncio.run(main())
