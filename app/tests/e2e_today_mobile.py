import asyncio, datetime, json, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,13,10,0,tzinfo=datetime.timezone.utc)
G=json.dumps({"tips":{},"visited":{"analytics":1},"hideStart":True})
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script(f"localStorage.setItem('sw.guide', {json.dumps(G)}); sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    print('order:', await pg.evaluate("[...document.querySelectorAll('.nav-dash .d-col > *')].filter(e=>e.offsetHeight).sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top).map(e=>[...e.classList].find(c=>c.startsWith('d-'))).join(' → ')"))
    print('title row:', await pg.evaluate("(()=>{const w=document.querySelector('.top .nav-hday'); if(!w||w.hidden) return 'missing'; const r=w.getBoundingClientRect(), t=document.querySelector('#title').getBoundingClientRect(); return 'rings+plus at x='+Math.round(r.left)+', same row as the title: '+(Math.abs((r.top+r.bottom)/2-(t.top+t.bottom)/2)<16)+' | ring svg: '+!!w.querySelector('.nav-hring svg')+' | next step dot: '+w.querySelector('.nav-hring').classList.contains('due')+' ('+w.querySelector('.nav-hring').title+')'})()"))
    print('trends shown:', await pg.locator('.d-trends').count(), '(empty → hidden)')
    await pg.screenshot(path='/tmp/mob2.png')
    await pg.locator('.nav-hplus').click(); await pg.wait_for_timeout(900)
    print('« + » opens:', await pg.evaluate("document.querySelector('#gSheet .g-gate') ? 'plan first' : (document.querySelector('#tkSlide.open') ? 'trade form' : 'nothing')"))
    await pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach(b=>b.click()); typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(600)
    await pg.locator('.nav-hring').click(); await pg.wait_for_timeout(900)
    print('rings open:', await pg.evaluate("(document.querySelector('#gSheet .g-head h2')||{}).textContent || (document.querySelector('#gSheet .g-car')?'journal':'nothing')"))
    await pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach(b=>b.click())"); await pg.wait_for_timeout(500)
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1200)
    print('on Trades the small rings are hidden:', await pg.evaluate("(()=>{const w=document.querySelector('.top .nav-hday'); return !w || w.hidden})()"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
