import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,2,16,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.kpiTab','day')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    print('cards on the phone:', await pg.evaluate("[...document.querySelectorAll('.nav-dash .d-col > *')].filter(e=>e.offsetHeight).sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top).map(e=>[...e.classList].find(c=>c.startsWith('d-'))).join(' → ')"))
    print('strip:', await pg.evaluate("document.querySelectorAll('.nav-feed .nav-fd').length"), 'days | selected centred:', await pg.evaluate("(()=>{const s=document.querySelector('.nav-fstrip'), e=s.querySelector('.sel'); const r=e.getBoundingClientRect(), q=s.getBoundingClientRect(); return Math.abs((r.left+r.right)/2-(q.left+q.right)/2)<40})()"))
    print('day:', await pg.evaluate("document.querySelector('.nav-feed .nav-kpi-b').innerText.replace(/\\n/g,' ')"), '| releases:', await pg.evaluate("[...document.querySelectorAll('.nav-feed .nav-fev-n')].map(e=>e.textContent).join(', ')||document.querySelector('.nav-feed .nav-fn').innerText"))
    await pg.locator('.nav-feed').screenshot(path='/tmp/feed_day.png')
    await pg.locator('.nav-feed .nav-fd[data-fd="2026-10-01"]').click(); await pg.wait_for_timeout(700)
    print('tap Oct 1:', await pg.evaluate("document.querySelector('.nav-feed .nav-kpi-b').innerText.replace(/\\n/g,' ')"), '| trades:', await pg.locator('.nav-feed .nav-tr').count(), '| releases:', await pg.evaluate("[...document.querySelectorAll('.nav-feed .nav-fev-n')].map(e=>e.textContent).join(', ')"))
    await pg.locator('.nav-feed [data-kt=week]').click(); await pg.wait_for_timeout(500)
    print('week of Oct 1:', await pg.evaluate("document.querySelector('.nav-feed .nav-kpi-b').innerText.replace(/\\n/g,' ')"), '| trades:', await pg.locator('.nav-feed .nav-tr').count())
    await pg.locator('.nav-feed').screenshot(path='/tmp/feed_week.png')
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
