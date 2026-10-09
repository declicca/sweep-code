import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.goto('http://127.0.0.1:8095/?x=1#trades'); await pg.wait_for_timeout(3000)
    print('title row:', await pg.evaluate("(()=>{const g=document.querySelector('.nav-topacts'); if(!g) return 'no group'; return [...g.querySelectorAll('.nav-imp-b, .nav-addtop')].map(e=>e.textContent.trim()+' mid'+Math.round(e.getBoundingClientRect().top+e.getBoundingClientRect().height/2)+' h'+Math.round(e.getBoundingClientRect().height)).join(' | ')+' | bubble: '+document.querySelectorAll('.nav-imp-i').length})()"))
    await pg.locator('.main-wrap > .top').first.screenshot(path='/tmp/i_top.png')
    await pg.evaluate("location.hash='#payouts'"); await pg.wait_for_timeout(2000)
    print('payouts: share above numbers:', await pg.evaluate("(()=>{const r=document.querySelector('#main .sh-row'), k=document.querySelector('#main .kpis'); return r&&k? (r.getBoundingClientRect().bottom<=k.getBoundingClientRect().top+2) : 'missing'})()"))
    await pg.locator('#main').screenshot(path='/tmp/i_pay.png', clip=None) if False else await pg.screenshot(path='/tmp/i_pay.png', clip={'x':0,'y':0,'width':1440,'height':420})
    await pg.evaluate("location.hash='#analytics'"); await pg.wait_for_timeout(2500)
    print('stats rank hint:', await pg.evaluate("(document.querySelector('.nav-rank-more')||{}).textContent"))
    await pg.locator('#main #gIns .gm-ins-rank').click(); await pg.wait_for_timeout(1500)
    print('opens:', await pg.evaluate("(document.querySelector('#gSheet h2, #gSheet h3')||{}).textContent||'nothing'"), '|', await pg.evaluate("(document.querySelector('#gSheet')||{innerText:''}).innerText.replace(/\\n+/g,' · ').slice(0,200)"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
