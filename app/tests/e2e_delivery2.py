import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.clock.install(time=datetime.datetime(2026,10,6,15,40,0,tzinfo=datetime.timezone.utc))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    print('16 disc chip:', await pg.evaluate("(document.querySelector('.nav-rt-disc')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"))
    await pg.locator('.nav-rt-disc').click(); await pg.wait_for_timeout(500); print('   explained:', await pg.evaluate("(document.querySelector('.nav-dwhy h2')||{}).textContent")); await pg.locator('[data-dwhy-ok]').click()
    await pg.locator('.nav-rt').screenshot(path='/tmp/d2_rt.png')
    # 9
    r=pg.locator('.nav-acc .nav-ready', has_text='payout').first
    if await r.count(): await r.click(); await pg.wait_for_timeout(1800); print('9 payout form account:', await pg.evaluate("(()=>{const f=document.querySelector('form[data-form=payout]'); return location.hash+' · '+(f&&acctLabel(f.querySelector('[name=account]').value))})()"))
    # 14
    await pg.evaluate("F.account='a-pa'; location.hash='#dashboard'; render()"); await pg.wait_for_timeout(1200)
    print('14 pill:', await pg.evaluate("(document.querySelector('.nav-fpill')||{innerText:'none'}).innerText.replace(/\\n/g,' ')")); await pg.locator('.nav-fpill').click(); await pg.wait_for_timeout(600); print('   after ✕:', await pg.evaluate("F.account"))
    # 10 + 11 desktop
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1800)
    n0=await pg.evaluate("S.trades.length")
    row=pg.locator('#main tr[data-href^=\"#trade/\"]').first; await row.hover(); await row.locator('.nav-dots-b').click(); await pg.wait_for_timeout(300)
    print('10 ⋯ menu:', await pg.evaluate("[...document.querySelectorAll('.nav-dots.open [data-ra]')].map(b=>b.textContent).join(' / ')"))
    await pg.locator('.nav-dots.open [data-ra=del]').click(); await pg.wait_for_timeout(600)
    print('11 deleted:', n0-await pg.evaluate("S.trades.length"), '| toast:', await pg.evaluate("(document.querySelector('.nav-undo')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"))
    await pg.locator('.nav-undo button').click(); await pg.wait_for_timeout(800); print('   after Undo:', await pg.evaluate("S.trades.length")==n0)
    # 17
    await pg.evaluate("location.hash='#analytics'"); await pg.wait_for_timeout(2000)
    await pg.locator('.nav-shstats').click(); await pg.wait_for_timeout(2500)
    print('17 share opens:', await pg.evaluate("SH.kind"), '|', await pg.evaluate("(()=>{const d=shData('discipline','view'); return d.label+' · '+d.big+' · '+JSON.stringify(d.stats)})()"))
    await pg.locator('#shPanel .sh-prev').screenshot(path='/tmp/d2_disc.png'); await pg.evaluate("closeShare()")
    # 13
    await pg.evaluate("put('accounts',{id:'a-test-fail',name:'Test 25K',firm_id:'f-apex',starting_balance_c:2500000,status:'active'})"); await pg.wait_for_timeout(800)
    await pg.evaluate("location.hash='#account/a-test-fail'"); await pg.wait_for_timeout(1500)
    print('13 button:', await pg.locator('[data-fail]').count()); await pg.locator('[data-fail]').click(); await pg.wait_for_timeout(1500)
    print('   archived list:', await pg.evaluate("(document.querySelector('.nav-arch')||{innerText:'none'}).innerText.replace(/\\n/g,' ').slice(0,160)"))
    await pg.evaluate("remove('accounts','a-test-fail')")
    # 19
    await pg.evaluate("BILL.st = Object.assign({}, BILL.st||{}, {trial:{kind:'trial',plan:'pro',ends_at:'2026-10-16T00:00:00Z',days_left:10}}); localStorage.removeItem('sw.trialCard.2026-10-16'); location.hash='#dashboard'; render()"); await pg.wait_for_timeout(1500)
    print('19 trial card:', await pg.evaluate("(document.querySelector('.nav-trial')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"))
    print('errors', errs[:3]); await ctx.close()
    # phone: swipe + pull to refresh
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True, storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page(); cdp=await ctx.new_cdp_session(pg)
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(3000)
    rr=pg.locator('#main .nav-ra-row').first; b=await rr.bounding_box()
    async def drag(x0,y0,x1,y1):
      await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x0,'y':y0}]})
      for i in range(1,11): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x0+(x1-x0)*i/10,'y':y0+(y1-y0)*i/10}]}); await pg.wait_for_timeout(16)
      await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(500)
    if b:
      await drag(b['x']+300,b['y']+b['height']/2,b['x']+120,b['y']+b['height']/2+4)
      print('10 phone swipe shows actions:', await pg.evaluate("!!document.querySelector('.nav-ra-row.sw')"))
      await pg.screenshot(path='/tmp/d2_swipe.png', clip={'x':0,'y':max(0,b['y']-60),'width':390,'height':200})
    else: print('10 phone: no row', await pg.evaluate("document.querySelectorAll('#main a.trow, #main a.nav-tr').length"))
    await pg.evaluate("document.querySelectorAll('.nav-ra-row.sw').forEach(x=>x.classList.remove('sw')); location.hash='#dashboard'"); await pg.wait_for_timeout(1500); await pg.evaluate("scrollTo(0,0)")
    await drag(195,200,195,330); await pg.wait_for_timeout(1500)
    print('12 pull to refresh ran, page still fine:', await pg.evaluate("!!document.querySelector('#main .nav-rt')"))
    await br.close()
asyncio.run(main())
