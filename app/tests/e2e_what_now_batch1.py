import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); out=[]
    for name,kw in [('phone',p.devices['iPhone 13']),('desktop',{'viewport':{'width':1440,'height':900}})]:
      ctx=await br.new_context(**kw, storage_state='/tmp/show_state.json', color_scheme='dark', locale='fr-CA'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_selector('.nav-rt-steps', timeout=15000); await pg.wait_for_timeout(800)
      out.append(name+' | steps: '+await pg.evaluate("[...document.querySelectorAll('.nav-rt-s')].map(s=>(s.querySelector('h3,b,.nav-rt-st0')||s).textContent.trim().split('\\n')[0].slice(0,14)).join(' · ')")+' | steps open: '+str(await pg.evaluate("!!document.querySelector('.nav-rt-steps').offsetParent"))+' | primary buttons on page: '+str(await pg.evaluate("[...document.querySelectorAll('#main .btn.primary, .main-wrap > .top .btn.primary')].filter(b=>b.offsetParent&&getComputedStyle(b).backgroundColor.includes('76, 141')).length")))
      out.append('   header chips visible: '+str(await pg.evaluate("[...document.querySelectorAll('.main-wrap > .top .nav-hday, .main-wrap > .top .nav-addtop')].filter(e=>e.offsetParent).length"))+' | quick access: '+await pg.evaluate("[...document.querySelectorAll('.d-quick .nav-q span')].map(s=>s.textContent).join(' | ')"))
      await pg.screenshot(path=f'/tmp/l1_{name}.png')
      await pg.evaluate("location.hash='#analytics'"); await pg.wait_for_timeout(2000)
      out.append('   stats rank on top: '+str(await pg.evaluate("!!(document.querySelector('#gIns')||{}).offsetParent"))+' | ∞ left: '+str(await pg.evaluate("[...document.querySelectorAll('#main *')].filter(e=>e.children.length===0&&e.textContent.trim()==='∞').length")))
      await ctx.close()
    print('\n'.join(out)); await br.close()
asyncio.run(main())
