import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(2500)
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
    await pg.locator('#tkSlide [data-v=long]').first.click()
    q=pg.locator('#tkSlide [data-tk=qty]'); await q.fill('2'); await q.dispatch_event('input')
    e=pg.locator('#tkSlide [data-tk=entry]'); await e.fill('30100'); await e.dispatch_event('input'); await pg.wait_for_timeout(300)
    print('simple form shortcuts:', await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-px [data-px]')].map(b=>b.textContent).join(' | ')"))
    # scale in: +1 @ 30090
    await pg.locator('#tkSlide [data-px=add]').first.click(); await pg.wait_for_timeout(500)
    async def set_last(price, qty=None):
      rows=pg.locator('#tkSlide .tk-ex'); r=rows.nth(await rows.count()-1)
      if qty: qi=r.locator('[data-tkx=qty]'); await qi.fill(str(qty)); await qi.dispatch_event('input')
      pi=r.locator('[data-tkx=price]'); await pi.fill(str(price)); await pi.dispatch_event('input'); await pg.wait_for_timeout(300)
    await set_last(30090)
    summ=lambda: pg.evaluate("document.querySelector('#tkSlide .nav-pos-g').innerText.replace(/\\n/g,' ')")
    print('after adding 1 @ 30090:', await summ())
    # partial exit 1 @ 30120
    await pg.locator('#tkSlide .nav-pos [data-px=partial]').click(); await pg.wait_for_timeout(400); await set_last(30120)
    print('after partial 1 @ 30120:', await summ())
    # exit the rest @ 30110
    await pg.locator('#tkSlide .nav-pos [data-px=rest]').click(); await pg.wait_for_timeout(400); await set_last(30110)
    print('after exiting the rest @ 30110:', await summ())
    print('tags:', await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-extag')].map(e=>e.textContent).join(' → ')"))
    await pg.locator('#tkSlide .nav-pos').screenshot(path='/tmp/multi_pos.png')
    await pg.locator('#tkSlide [data-act=tk-save]').click(); await pg.wait_for_timeout(1500)
    t=await pg.evaluate("(()=>{const t=S.trades.slice().sort((a,b)=>(b.created_at||'').localeCompare(a.created_at||''))[0]; const x=S.trades.find(x=>x.entry===30096.67)||S.trades.filter(x=>Math.abs((x.entry||0)-30096.67)<0.01)[0]; return x?{entry:x.entry,exit:x.exit,contracts:x.contracts,pnl:x.pnl_c/100,id:x.id}:null})()")
    print('saved trade:', t, '(expected avg entry 30096.67, 3 contracts, P&L = (30120-30096.67)*20 + 2*(30110-30096.67)*20 ≈ $1000)')
    if t: await pg.evaluate(f"remove('trades','{t['id']}')")
    await pg.wait_for_timeout(800)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
