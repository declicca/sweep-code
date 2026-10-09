import asyncio, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
    await pg.clock.install(time=datetime.datetime(2026,10,7,13,0,0,tzinfo=datetime.timezone.utc))
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    # a trade copied on 5 accounts, each copy with the same review
    await pg.evaluate("""['a-xfa','a-pa','a-flex','a-comb','a-live'].forEach((a,i)=>put('trades',{id:'rvt'+i,account_id:a,copy_group:'g-rv',instrument:'NQ',direction:'long',contracts:1,date:'2026-10-07',entry_time:'08:30:00',exit_time:'09:00:00',entry:31241,exit:31264,pnl_c:46000,fees_c:140,review:{well:'quick profits and respected my stop',lesson:'trust the BE'}}))"""); await pg.wait_for_timeout(1200)
    await pg.evaluate("SweepGame.openReview && SweepGame.openReview('2026-10-07')"); await pg.wait_for_timeout(1200)
    print('what went well:', repr(await pg.evaluate("(document.querySelector('[data-gr=well]')||{}).value")))
    print('to improve:', repr(await pg.evaluate("(document.querySelector('[data-gr=tomorrow]')||{}).value")))
    await pg.evaluate("['rvt0','rvt1','rvt2','rvt3','rvt4'].forEach(i=>remove('trades',i))")
    await br.close()
asyncio.run(main())
