import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,14,30,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    aid=await pg.evaluate("S.accounts.find(a=>a.status!=='archived').id")
    # 1. commission on the account
    await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(1800)
    f=pg.locator('.nav-fee input'); await f.scroll_into_view_if_needed(); await f.fill('4.12'); await f.dispatch_event('change'); await pg.wait_for_timeout(600)
    print('1) account commission:', await pg.evaluate(f"getDoc('accounts','{aid}').fee_rt_c"))
    bal0=await pg.evaluate(f"(()=>{{const a=getDoc('accounts','{aid}'); return S.trades.filter(t=>t.account_id==='{aid}').reduce((s,t)=>s+tNet(t),0)}})()")
    # 2. a trade stopped out with slippage: stop at -10 pts (-$200), platform shows -$350
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
    await pg.evaluate(f"(()=>{{ TK.account='{aid}'; }})()")
    await pg.locator('#tkSlide [data-v=long]').first.click()
    for k,v in [('entry','30100'),('stop','30090'),('exit','30090')]:
      el=pg.locator(f'#tkSlide [data-tk={k}]').first; await el.scroll_into_view_if_needed(); await el.fill(v); await el.dispatch_event('change'); await pg.wait_for_timeout(200)
    r=pg.locator('#tkSlide [data-real]'); await r.scroll_into_view_if_needed(); await r.fill('-350'); await r.dispatch_event('input'); await pg.wait_for_timeout(300)
    print('2) form line:', (await pg.locator('#tkSlide .nav-real-gap').inner_text()))
    await pg.locator('#tkSlide .nav-real').screenshot(path='/tmp/real_form.png')
    await pg.locator('#tkSlide [data-act=tk-save]').click(); await pg.wait_for_timeout(1500)
    t=await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.real_pnl_c!=null).slice(-1)[0]; return t?{id:t.id,real:t.real_pnl_c,calc:t.pnl_calc_c,fees:t.fees_c,pnl:t.pnl_c,net:tNet(t)}:null})()")
    print('   saved:', t)
    bal1=await pg.evaluate(f"S.trades.filter(t=>t.account_id==='{aid}').reduce((s,t)=>s+tNet(t),0)")
    print('   account P&L moved by', (bal1-bal0)/100, '$ (expected -350)')
    # 3. trade review page
    await pg.evaluate(f"location.hash='#trade/{t['id']}'"); await pg.wait_for_timeout(2000)
    box=pg.locator('#main .nav-real-tr'); await box.scroll_into_view_if_needed()
    print('3) trade page:', await box.locator('.nav-real-gap').inner_text())
    inp=box.locator('input'); await inp.fill('-300'); await inp.dispatch_event('change'); await pg.wait_for_timeout(800)
    print('   changed to -300 → net', await pg.evaluate(f"tNet(getDoc('trades','{t['id']}'))/100"))
    # 4. Stats
    await pg.evaluate("location.hash='#analytics'"); await pg.wait_for_timeout(2000)
    c=pg.locator('#main .nav-slip'); await c.scroll_into_view_if_needed()
    print('4) stats card:', (await c.inner_text()).replace('\n',' | ')[:200])
    await c.screenshot(path='/tmp/real_stats.png')
    # cleanup
    await pg.evaluate(f"remove('trades','{t['id']}'); editDoc('accounts','{aid}', d=>{{ delete d.fee_rt_c; }})"); await pg.wait_for_timeout(1200)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
