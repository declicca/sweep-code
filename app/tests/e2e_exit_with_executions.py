import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,19,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(2500)
    summ=lambda: pg.evaluate("(document.querySelector('#tkSlide .nav-pos-g')||{innerText:''}).innerText.replace(/\\n/g,' ')")
    async def typ(sel, v):
      el=pg.locator(sel); await el.scroll_into_view_if_needed(); await el.fill(v); await el.dispatch_event('input'); await pg.wait_for_timeout(300)
    async def last_row_price(v, qty=None):
      rows=pg.locator('#tkSlide .tk-ex:not(.nav-auto)'); r=rows.nth(await rows.count()-1)
      if qty: q=r.locator('[data-tkx=qty]'); await q.fill(str(qty)); await q.dispatch_event('input'); await pg.wait_for_timeout(200)
      pr=r.locator('[data-tkx=price]'); await pr.fill(str(v)); await pr.dispatch_event('input'); await pg.wait_for_timeout(400)
    # A) exit typed first, then « add to the position »
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
    await pg.locator('#tkSlide [data-v=long]').first.click()
    await typ('#tkSlide [data-tk=qty]','2'); await typ('#tkSlide [data-tk=entry]','30000'); await typ('#tkSlide [data-tk=exit]','30020')
    await pg.locator('#tkSlide .nav-px [data-px=add]').first.click(); await pg.wait_for_timeout(700)
    print('A) after « Ajouter à la position »: exit field kept:', await pg.evaluate("(document.querySelector('#tkSlide [data-ax=price]')||{}).value"), '| rows shown:', await pg.locator('#tkSlide .tk-ex:not(.nav-auto)').count())
    await last_row_price(29990)
    print('   position:', await summ())
    await pg.locator('#tkSlide [data-act=tk-save]').click(); await pg.wait_for_timeout(1500)
    print('   saved:', await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.date==='2026-10-05').sort((a,b)=>(b.created_at||'').localeCompare(a.created_at||''))[0]; return t?{entry:t.entry,exit:t.exit,qty:t.contracts,pnl:t.pnl_c/100,id:t.id}:null})()"), '(expected avg 29996.67, exit 30020, 3, +$1400)')
    # B) partial first, exit typed after
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
    await pg.locator('#tkSlide [data-v=long]').first.click()
    await typ('#tkSlide [data-tk=qty]','2'); await typ('#tkSlide [data-tk=entry]','30000')
    await pg.locator('#tkSlide .nav-px [data-px=partial]').first.click(); await pg.wait_for_timeout(700)
    await last_row_price(30010)
    print('B) after a partial 1 @ 30010:', await summ())
    await typ('#tkSlide [data-ax=price]','30030')
    print('   exit price 30030 typed:', await summ())
    await pg.locator('#tkSlide').screenshot(path='/tmp/ax.png')
    await pg.locator('#tkSlide [data-act=tk-save]').click(); await pg.wait_for_timeout(1500)
    print('   saved:', await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.date==='2026-10-05').sort((a,b)=>(b.created_at||'').localeCompare(a.created_at||''))[0]; return t?{entry:t.entry,exit:t.exit,qty:t.contracts,pnl:t.pnl_c/100}:null})()"), '(expected exit avg 30020, 2, +$800)')
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
