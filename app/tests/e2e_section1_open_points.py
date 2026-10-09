import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    # e. highest balance
    r=await pg.evaluate("""(()=>{ put('accounts',{id:'a-hwm',name:'HWM 50K',firm_id:'f-apex',starting_balance_c:5000000,status:'active',rules:{dd_c:200000,dd_type:'eod'},adjustments:[{id:'x1',at:'2026-10-05',amount_c:300000},{id:'x2',at:'2026-10-06',amount_c:-100000}],hwm_c:5300000});
      const s=acctState(getDoc('accounts','a-hwm')); return 'balance '+s.bal/100+' | floor '+s.thr/100+' | drawdown room '+s.buffer/100 })()""")
    print('e. running account (start 50K, highest 53K, now 52K, trailing $2,000):', r)
    # d. grouped accounts → manual form « Also on »
    await pg.evaluate("put('accounts',{id:'g1',name:'Apex 50K #1',firm_id:'f-apex',starting_balance_c:5000000,status:'active',group_id:'grp-t'}); put('accounts',{id:'g2',name:'Apex 50K #2',firm_id:'f-apex',starting_balance_c:5000000,status:'active',group_id:'grp-t'}); put('accounts',{id:'g3',name:'Apex 50K #3',firm_id:'f-apex',starting_balance_c:5000000,status:'active',group_id:'grp-t'})"); await pg.wait_for_timeout(600)
    await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1200)
    if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(900)
    await pg.evaluate("TK.account='g1'; tkRefresh({panel:true})"); await pg.wait_for_timeout(900)
    print('d. manual form « Also on » pre-selected:', await pg.evaluate("[...TK.copyTo].map(i=>acct(i).name).join(', ')"))
    await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(400)
    # b + c
    await pg.evaluate("put('trades',{id:'tr-plat',account_id:'a-xfa',instrument:'NQ',direction:'long',contracts:1,date:'2026-10-06',entry_time:'10:01:00',exit_time:'10:20:00',entry:25100,exit:25120,pnl_c:40000,real_pnl_c:38520,fees_c:148,setup:'VWAP reclaim',discipline:{plan:'y',stop:'y',size:'y',risk:'n'}})"); await pg.wait_for_timeout(600)
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1800)
    print('b. row mark:', await pg.evaluate("(()=>{const r=[...document.querySelectorAll('#main [data-href=\"#trade/tr-plat\"], #main a[href=\"#trade/tr-plat\"]')][0]; return r? ((r.querySelector('.nav-plat-r')||{}).textContent||'none') : 'row not found'})()"))
    await pg.evaluate("location.hash='#trade/tr-plat'"); await pg.wait_for_timeout(2200)
    print('c. trade page discipline featured:', await pg.locator('.nav-tdisc').count(), await pg.evaluate("(document.querySelector('.nav-tdisc')||{innerText:''}).innerText.replace(/\\n/g,' ')"))
    if await pg.locator('.nav-tdisc').count():
      await pg.locator('.nav-tdisc').click(); await pg.wait_for_timeout(500); print('   explained:', await pg.evaluate("(document.querySelector('.nav-dwhy-v')||{innerText:'none'}).innerText.replace(/\\n/g,' ')")); await pg.locator('[data-dwhy-ok]').click()
    await pg.evaluate("['a-hwm','g1','g2','g3'].forEach(i=>remove('accounts',i)); remove('trades','tr-plat')"); await pg.wait_for_timeout(500)
    print('errors', errs[:3]); await ctx.close()
    # phone: swipe + pull to refresh
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True, storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page(); cdp=await ctx.new_cdp_session(pg)
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    calls=[]; pg.on('request', lambda rq: calls.append(rq.url) if '/api/data' in rq.url else None)
    await pg.goto(B+'/?x=1#trades'); await pg.wait_for_timeout(3000)
    async def drag(x0,y0,x1,y1):
      await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x0,'y':y0}]})
      for i in range(1,11): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x0+(x1-x0)*i/10,'y':y0+(y1-y0)*i/10}]}); await pg.wait_for_timeout(16)
      await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(500)
    rr=pg.locator('#main .nav-ra-row').nth(1); await rr.scroll_into_view_if_needed(); b=await rr.bounding_box()
    await drag(b['x']+300,b['y']+b['height']/2,b['x']+100,b['y']+b['height']/2+3)
    print('a. swipe: actions shown', await pg.evaluate("!!document.querySelector('.nav-ra-row.nav-sw')"))
    b=await rr.bounding_box(); await pg.screenshot(path='/tmp/s1_swipe.png', clip={'x':0,'y':b['y']-70,'width':390,'height':b['height']+140})
    n0=await pg.evaluate("S.trades.length"); await rr.locator('[data-ra=del]').tap(); await pg.wait_for_timeout(600)
    print('   delete from the swipe:', n0-await pg.evaluate("S.trades.length"), '| undo toast:', await pg.locator('.nav-undo').count()); await pg.locator('.nav-undo button').tap(); await pg.wait_for_timeout(600); print('   undone:', await pg.evaluate("S.trades.length")==n0)
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500); await pg.evaluate("scrollTo(0,0)"); calls.clear()
    await drag(195,200,195,340); await pg.wait_for_timeout(1500)
    print('f. pull to refresh: data reloaded from the server', len(calls), 'time(s), no page reload:', await pg.evaluate("!!document.querySelector('#main .nav-rt')"))
    await br.close()
asyncio.run(main())
