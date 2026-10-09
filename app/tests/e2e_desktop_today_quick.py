import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900},color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{analytics:1}}))")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(4000)
    print('side « + » centred:', await pg.evaluate("(()=>{const b=document.querySelector('aside.side .new'), s=b.querySelector('svg'); const r=b.getBoundingClientRect(), q=s.getBoundingClientRect(); return Math.abs((r.left+r.right)/2-(q.left+q.right)/2).toFixed(1)+'px off'})()"))
    print('rank in the day card:', await pg.evaluate("!!document.querySelector('.d-today .nav-rank:not(.ph)')"), '| quick access:', await pg.evaluate("[...document.querySelectorAll('.d-quick .nav-q span')].map(s=>s.textContent).join(' · ')"))
    await pg.screenshot(path='/tmp/desk3.png', clip={'x':0,'y':0,'width':1440,'height':900})
    await pg.locator('.nav-q[data-q="#news"]').click(); await pg.wait_for_timeout(900)
    print('quick « Calendrier économique » →', await pg.evaluate("location.hash"))
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
    await pg.locator('.nav-q[data-q="plan"]').click(); await pg.wait_for_timeout(900)
    print('quick « Plan du jour » opens the plan:', await pg.evaluate("!!document.querySelector('#gSheet.g-plan, #gSheet [data-g=save-plan]')"))
    await pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach(b=>b.click())"); await pg.wait_for_timeout(500)
    await pg.locator('.d-today .nav-rank').click(); await pg.wait_for_timeout(900)
    print('rank opens Progression:', await pg.evaluate("!!document.querySelector('#gSheet .gc-hubwrap')"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
