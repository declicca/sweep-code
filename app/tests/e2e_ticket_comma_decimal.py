import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,13,56,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='en-US',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    for case,(entry,etime,exitp,xtime) in {'dot, exit after entry':('30150','09:50:00','30182.75','09:55:01'),'exit typed before entry time':('30150','09:56:30','30182.75','09:55:01'),'comma decimal':('30150','09:50:00','30182,75','09:55:01'),'comma entry and exit':('30150,25','09:50:00','30182,75','09:55:01'),'thousands with spaces':('30 150,25','09:50:00','30 182,75','09:55:01')}.items():
      await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
      await pg.locator('#tkSlide [data-tk-dir=long], #tkSlide [data-v=long]').first.click()
      for k,v in [('entry',entry),('exit',exitp)]:
        el=pg.locator(f'#tkSlide [data-tk={k}]').first
        await el.click(); await el.fill(''); await el.type(v, delay=10); await el.dispatch_event('change'); await pg.wait_for_timeout(150)
      vals=await pg.evaluate("[document.querySelector('#tkSlide [data-tk=entry]').value, document.querySelector('#tkSlide [data-tk=exit]').value]")
      await pg.locator('#tkSlide [data-act=tk-save]').click(); await pg.wait_for_timeout(1200)
      st=await pg.evaluate("(()=>{const s=tkState(); return JSON.stringify({ex:s.ex.map(e=>e.side+' '+e.qty+'@'+e.price+' '+e.t.slice(11)), open:s.pos.open, closed:s.pos.closed, qty:TK.qty, entryTime:TK.entryTime, exit:TK.exit})})()") if await pg.locator('#tkSlide.open').count() else 'saved'
      print(f'{case:30} fields {vals} → err: {await pg.evaluate("(document.querySelector(\'#tkErr\')||{}).textContent||\'\'")!r} | {st}')
      await pg.evaluate("typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(500)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
