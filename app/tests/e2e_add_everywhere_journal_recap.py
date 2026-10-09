import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
      pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(2500)
      res=[]
      for r in ['#trades','#calendar','#journal/2026-10-02']:
        await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(1300)
        res.append(r+': '+await pg.evaluate("(()=>{const b=document.querySelector('.top .nav-addtop:not([hidden])'); return b ? (b.getAttribute('aria-label')+(b.dataset.date?' ['+b.dataset.date+']':'')) : 'missing'})()"))
      print(w, ' | '.join(res))
      # journal day: recap + folds
      print('   recap:', (await pg.locator('#main .nav-recap').inner_text()).replace('\n',' / ')[:160])
      print('   folded:', await pg.evaluate("[...document.querySelectorAll('#main .nav-fold')].map(s=>s.classList.contains('open')?'open':'closed').join(', ')"), '| page height', await pg.evaluate("document.body.scrollHeight"))
      await pg.locator('#main .nav-fold-h').first.click(); await pg.wait_for_timeout(400)
      print('   tap pre-market →', await pg.evaluate("document.querySelector('#main .nav-fold').classList.contains('open')"))
      if w==1440: await pg.locator('#main .nav-recap').screenshot(path='/tmp/recap.png')
      # add on that day
      await pg.locator('.top .nav-addtop').click(); await pg.wait_for_timeout(1000)
      print('   add from the day → form date:', await pg.evaluate("typeof TK!=='undefined'&&TK?TK.date:'no form'"))
      # form: order and $ amounts
      await pg.locator('#tkSlide [data-v=long]').first.click()
      el=pg.locator('#tkSlide [data-tk=entry]'); await el.fill('30100'); await el.dispatch_event('input'); await pg.wait_for_timeout(300)
      pos=await pg.evaluate("(()=>{const y=s=>{const e=document.querySelector(s); return e?Math.round(e.getBoundingClientRect().top):null}; return {entry:y('#tkSlide [data-tk=entry]'), multi:y('#tkSlide .nav-multi'), exit:y('#tkSlide [data-tk=exit]'), chart:y('#tkSlide .tkc, #tkSlide [class*=tkc]')}})()")
      print('   form order (y):', pos)
      await pg.locator('#tkSlide .nav-unit [data-unit=usd]').click(); await pg.wait_for_timeout(200)
      for k,v in [('stop','200'),('target','400'),('exit','-350')]:
        i=pg.locator(f'#tkSlide [data-usd={k}]'); await i.scroll_into_view_if_needed(); await i.fill(v); await i.dispatch_event('input'); await pg.wait_for_timeout(250)
      print('   $ → prices:', await pg.evaluate("[TK.stop, TK.target, TK.exit].join(' / ')"), '(expected 30090 / 30120 / 30082.50)')
      if w==390: await pg.locator('#tkSlide').screenshot(path='/tmp/form.png')
      await pg.evaluate("closeTicket()"); await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
