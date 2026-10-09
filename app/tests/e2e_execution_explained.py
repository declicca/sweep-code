import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    acc=await pg.evaluate("S.accounts[0].id")
    await pg.evaluate("put('journals',{id:'2026-10-05',date:'2026-10-05',pre:{bias:'bullish',setups:['Liquidity sweep'],max_loss:'800',max_trades:'3',created_at:'2026-10-05T12:00:00Z'}})")
    await pg.evaluate(f"put('trades',{{id:'xw-1',account_id:'{acc}',instrument:'NQ',date:'2026-10-05',entry_time:'09:51:00',exit_time:'09:58:00',direction:'short',contracts:1,entry:30100,exit:30090,pnl_c:2000,setup:'Reversal',rules_followed:'partial',emo:{{}},review:{{}},discipline:{{}}}})")
    await pg.evaluate(f"put('trades',{{id:'xw-2',account_id:'{acc}',instrument:'NQ',date:'2026-10-05',entry_time:'10:20:00',exit_time:'10:30:00',direction:'long',contracts:1,entry:30100,stop:30090,exit:30120,pnl_c:4000,setup:'Liquidity sweep',rules_followed:'yes',emo:{{}},review:{{}},discipline:{{}}}})")
    await pg.wait_for_timeout(1500); await pg.evaluate("SweepGame.refresh()"); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelector('#gToday .g-ringbtn').click()"); await pg.wait_for_timeout(900)
    await pg.locator('#gSheet [data-g=exec-why]').click(); await pg.wait_for_timeout(700)
    print((await pg.locator('#gSheet .g-in').inner_text()).replace('\n',' | ')[:900])
    await pg.locator('#gSheet .g-in').screenshot(path='/tmp/xw.png')
    await pg.locator('#gSheet [data-g=detail-back]').click(); await pg.wait_for_timeout(600)
    print('back to the day detail:', await pg.locator('#gSheet [data-g=exec-why]').count() == 1)
    await pg.evaluate("remove('trades','xw-1'); remove('trades','xw-2'); remove('journals','2026-10-05')"); await pg.wait_for_timeout(1200)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
