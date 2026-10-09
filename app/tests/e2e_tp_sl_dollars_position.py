import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,18,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900},locale='en-US',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(2500)
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
    await pg.locator('#tkSlide [data-tk=inst]').select_option('MGC'); await pg.wait_for_timeout(300)
    await pg.locator('#tkSlide [data-v=short]').first.click()
    e=pg.locator('#tkSlide [data-tk=entry]'); await e.fill('4220.4'); await e.dispatch_event('input'); await pg.wait_for_timeout(200)
    print('labels:', await pg.evaluate("[...document.querySelectorAll('#tkSlide .tk-f:has([data-tk=stop]) > span, #tkSlide .tk-f:has([data-tk=target]) > span')].map(s=>s.textContent).join(' / ')"))
    await pg.locator('#tkSlide .nav-px [data-px=add]').first.click(); await pg.wait_for_timeout(500)
    rows=pg.locator('#tkSlide .tk-ex'); r=rows.nth(1)
    q=r.locator('[data-tkx=qty]'); await q.fill('2'); await q.dispatch_event('input')
    pr=r.locator('[data-tkx=price]'); await pr.fill('4215.30'); await pr.dispatch_event('input'); await pg.wait_for_timeout(400)
    print('position:', await pg.evaluate("document.querySelector('#tkSlide .nav-pos-g').innerText.replace(/\\n/g,' ')"))
    await pg.locator('#tkSlide .nav-unit [data-unit=usd]').click(); await pg.wait_for_timeout(200)
    for k,v in [('target','1000'),('stop','300')]:
      i=pg.locator(f'#tkSlide [data-usd={k}]'); await i.fill(v); await i.dispatch_event('input'); await pg.wait_for_timeout(300)
    print('TP $1000 / SL $300 →', await pg.evaluate("'TP '+TK.target+' · SL '+TK.stop"), '(expected TP 4183.70, SL 4227.00)')
    print('risk box:', await pg.evaluate("document.querySelector('#tkRisk').innerText.replace(/\\n/g,' ')"))
    # one more execution: the $ amounts stay, the prices follow
    await pg.locator('#tkSlide .nav-pos [data-px=add]').click(); await pg.wait_for_timeout(400)
    r=pg.locator('#tkSlide .tk-ex').nth(2); pr=r.locator('[data-tkx=price]'); await pr.fill('4210'); await pr.dispatch_event('input'); await pg.wait_for_timeout(500)
    await pg.evaluate("document.querySelector('#tkSlide [data-usd=target]').dispatchEvent(new Event('input',{bubbles:true}))"); await pg.wait_for_timeout(300)
    print('after adding 1 @ 4210:', await pg.evaluate("'avg '+positionOf(tkExecs(),'MGC').avgEntry.toFixed(2)+' · TP '+TK.target+' · SL '+TK.stop"), '| risk box:', await pg.evaluate("document.querySelector('#tkRisk').innerText.replace(/\\n/g,' ')"))
    await pg.locator('#tkSlide').screenshot(path='/tmp/mgc.png')
    await pg.evaluate("closeTicket()")
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
