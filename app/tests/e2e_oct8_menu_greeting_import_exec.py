import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA'); pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.clock.install(time=datetime.datetime(2026,10,6,15,40,0,tzinfo=datetime.timezone.utc))
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    print('greeting:', await pg.evaluate("document.querySelector('.main-wrap .top #title').dataset.hi"))
    print('icons centred (closed):', await pg.evaluate("[...document.querySelectorAll('aside.side a[data-v], aside.side .nav-prog, aside.side .nav-search, aside.side .nt-bell')].filter(e=>e.offsetParent).map(e=>{const i=e.querySelector('svg').getBoundingClientRect(); return Math.round(i.left+i.width/2)}).join(',')"))
    await pg.locator('aside.side').screenshot(path='/tmp/s8_closed.png')
    await pg.evaluate("document.querySelector('aside.side').classList.add('open')"); await pg.wait_for_timeout(500)
    await pg.locator('aside.side').screenshot(path='/tmp/s8_open.png')
    print('open labels:', await pg.evaluate("[...document.querySelectorAll('aside.side .nav-side-l')].map(e=>e.textContent+':'+(getComputedStyle(e).opacity)).join(' | ')"))
    await pg.evaluate("document.querySelector('aside.side').classList.remove('open'); location.hash='#trades'"); await pg.wait_for_timeout(1500)
    print('trades title row:', await pg.evaluate("(()=>{const g=document.querySelector('.main-wrap .top .nav-topacts'); if(!g) return 'no group'; const a=g.querySelector('.nav-imp').getBoundingClientRect(), b=g.querySelector('.nav-addtop').getBoundingClientRect(); return 'gap between import and add: '+Math.round(b.left-a.right)+'px'})()"))
    await pg.locator('.main-wrap > .top').first.screenshot(path='/tmp/s8_top.png')
    r=await pg.evaluate("fetch('api/game/today',{credentials:'same-origin',headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>JSON.stringify(j.today.rings)+' compliant '+j.today.compliant+'/'+j.today.trades)")
    print('rings today:', r)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
