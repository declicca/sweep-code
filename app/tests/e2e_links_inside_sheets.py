import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
      pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      acc=await pg.evaluate("S.accounts[0].id")
      await pg.evaluate(f"put('trades',{{id:'ns-1',account_id:'{acc}',instrument:'NQ',date:'2026-10-05',entry_time:'09:51:00',exit_time:'09:58:00',direction:'short',contracts:1,entry:30100,exit:30090,pnl_c:2000,rules_followed:'no',emo:{{}},review:{{}},discipline:{{}}}})")
      await pg.wait_for_timeout(1200); await pg.evaluate("SweepGame.refresh()"); await pg.wait_for_timeout(2500)
      res=[]
      # 1. ring → « Trades in your plan » → « Open the trade »
      await pg.evaluate("document.querySelector('#gToday .g-ringbtn').click()"); await pg.wait_for_timeout(900)
      await pg.locator('#gSheet [data-g=exec-why]').click(); await pg.wait_for_timeout(600)
      await pg.locator('#gSheet a[href="#trade/ns-1"]').first.click(); await pg.wait_for_timeout(1300)
      res.append('« Ouvrir le trade » → '+await pg.evaluate("location.hash")+(' (sheet closed)' if not await pg.locator('#gSheet.open').count() else ' (sheet still open!)'))
      # 2. back button returns to Today
      await pg.go_back(); await pg.wait_for_timeout(900)
      res.append('back → '+await pg.evaluate("location.hash"))
      # 3. a link in the day detail (off-plan list)
      await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(900)
      await pg.evaluate("document.querySelector('#gToday .g-ringbtn').click()"); await pg.wait_for_timeout(900)
      off=pg.locator('#gSheet .g-offrow').first
      if await off.count(): await off.click(); await pg.wait_for_timeout(1300); res.append('day detail trade row → '+await pg.evaluate("location.hash"))
      # 4. the avatar menu still navigates
      await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(900)
      await pg.evaluate("document.querySelector('aside.side .who').click()"); await pg.wait_for_timeout(600)
      lk=pg.locator('#navMenu a[href="#settings"], #navMenu [data-href="#settings"]').first
      if await lk.count(): await lk.click(); await pg.wait_for_timeout(1000); res.append('menu → '+await pg.evaluate("location.hash"))
      print(w, ' | '.join(res))
      await pg.evaluate("remove('trades','ns-1')"); await pg.wait_for_timeout(800)
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
