import asyncio, datetime, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
      pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      if w==1440:
        await pg.evaluate("put('journals',{id:'2026-10-03',date:'2026-10-03',pre:{bias:'no_trade',day_off:true}})"); await pg.wait_for_timeout(1000)
      await pg.evaluate("location.hash='#journal'"); await pg.wait_for_timeout(1500)
      days=await pg.evaluate("[...document.querySelectorAll('#main .jlist a[href^=\"#journal/\"], #main .jstrip a[href^=\"#journal/\"]')].filter(a=>a.offsetParent).map(a=>a.getAttribute('href').slice(9))")
      wk=[d for d in days if datetime.date.fromisoformat(d).weekday()>=5]
      print(w, '| journal days shown:', len(days), '| weekend days shown:', wk)
      await pg.evaluate("location.hash='#calendar'"); await pg.wait_for_timeout(1500)
      print('   calendar columns:', await pg.evaluate("(()=>{const c=document.querySelector('#main .cal'); return c ? (c.className.match(/d(\\d)/)||[])[1] : 'none'})()"))
      await ctx.close()
    # daily review: written in the trade review → counted, and the sheet starts from it
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    acc=await pg.evaluate("S.accounts[0].id")
    await pg.evaluate(f"put('trades',{{id:'rv-1',account_id:'{acc}',instrument:'NQ',date:'2026-10-05',entry_time:'09:51:00',exit_time:'09:58:00',direction:'long',contracts:1,entry:30100,exit:30110,pnl_c:2000,emo:{{before:['Calm']}},rules_followed:'yes',setup:'Liquidity sweep',review:{{well:'Patience à l’entrée',wrong:'Sortie trop tôt'}}}})")
    await pg.evaluate("(()=>{ if (getDoc('trades','nt-emo')) { remove('trades','nt-emo'); } })()")
    await pg.wait_for_timeout(1500); await pg.evaluate("SweepGame.refresh()"); await pg.wait_for_timeout(2500)
    print('trades on the day:', await pg.evaluate("S.trades.filter(t=>t.date==='2026-10-05'||t.date==='2026-10-04').map(t=>t.id).join(',')"))
    print('review ring with the trade review written:', await pg.evaluate("(()=>{const r=document.querySelector('#gToday .g-lg.g-review b'); return r ? r.textContent : 'n/a'})()"))
    await pg.evaluate("SweepGame.open('review')"); await pg.wait_for_timeout(1000)
    print('daily review sheet starts with:', await pg.evaluate("JSON.stringify([document.querySelector('#gSheet [data-gr=well]').value, document.querySelector('#gSheet [data-gr=tomorrow]').value])"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
