import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,12,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
      pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.route('https://s.tradingview.com/**', lambda r: r.fulfill(status=200, content_type='text/html', body='<html><body style="background:#111;color:#888;font:14px sans-serif">TradingView</body></html>'))
      resp=await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      if w==1440: print('CSP allows the chart frame:', 'frame-src https://s.tradingview.com' in (resp.headers.get('content-security-policy') or ''))
      # 1) the form: entry | exit, then TP / SL
      await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
      pos=await pg.evaluate("""(()=>{const y=s=>{const e=document.querySelector(s); return e?Math.round(e.getBoundingClientRect().top):null}; return {entry:y('#tkSlide [data-tk=entry]'), exit:y('#tkSlide [data-tk=exit]'), sw:y('#tkSlide .nav-unit'), tp:y('#tkSlide [data-tk=target]'), sl:y('#tkSlide [data-tk=stop]'), time:y('#tkSlide [data-tk=exitTime]'), chart:y('#tkSlide .tkc, #tkSlide [class*=tkc]')}})()""")
      print(w, 'form:', pos, '| labels:', await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-ee > .tk-f > span')].map(s=>s.textContent).join(' | ')"))
      if mob: await pg.locator('#tkSlide').screenshot(path='/tmp/pre_form.png')
      await pg.locator('#tkSlide .nav-unit [data-unit=usd]').click(); await pg.wait_for_timeout(300)
      print('   $ mode: exit row shows', await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-ee > *')].filter(e=>e.offsetParent).map(e=>(e.querySelector('span')||e).textContent.trim()).join(' | ')"))
      await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(500)
      # 2) the plan sheet
      await pg.evaluate("SweepGame.open('plan')"); await pg.wait_for_timeout(900)
      print('   plan sheet: block', await pg.locator('#gSheet .nav-pre').count())
      await pg.locator('#gSheet [data-pre-chart]').click(); await pg.wait_for_timeout(600)
      print('   chart frame:', await pg.evaluate("(document.querySelector('#gSheet .nav-tv')||{}).src||'none'").__await__() if False else (await pg.evaluate("(document.querySelector('#gSheet .nav-tv')||{}).src||'none'"))[:95])
      await pg.locator('#gSheet [data-pre-inst=ES]').click(); await pg.wait_for_timeout(400)
      print('   ES chosen →', 'ES1' in await pg.evaluate("document.querySelector('#gSheet .nav-tv').src"))
      await pg.locator('#gSheet [data-pre-up]').set_input_files('/tmp/shot.png'); await pg.wait_for_timeout(1800)
      print('   screenshot in the plan:', await pg.locator('#gSheet .nav-pre-shots img').count(), '| saved on the day:', await pg.evaluate("JSON.stringify((getDoc('journals','2026-10-05')||{}).pre?.shots?.length||0)"))
      if mob: await pg.locator('#gSheet .nav-pre').screenshot(path='/tmp/pre_plan.png')
      await pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach(b=>b.click())"); await pg.wait_for_timeout(600)
      # 3) the Journal day shows the same screenshot
      await pg.evaluate("location.hash='#journal/2026-10-05'"); await pg.wait_for_timeout(1500)
      await pg.locator('#main .nav-fold-h').first.click(); await pg.wait_for_timeout(500)
      print('   journal pre-market: screenshots', await pg.locator('#main .nav-pre-shots img').count())
      await pg.locator('#main [data-pre-rm]').first.click(); await pg.wait_for_timeout(800)
      print('   removed →', await pg.locator('#main .nav-pre-shots img').count())
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
