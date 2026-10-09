import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='en-US',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    acc=await pg.evaluate("S.accounts[0].id")
    # a brand-new trade, saved like the form does (empty emotions and checklist), then the app is reloaded
    await pg.evaluate(f"put('trades',{{id:'rt-1',account_id:'{acc}',instrument:'NQ',date:'2026-10-02',entry_time:'10:00:00',exit_time:'10:05:00',direction:'long',contracts:1,entry:30100,exit:30120,pnl_c:4000,emo:{{}},discipline:{{}},review:{{}}}})")
    await pg.wait_for_timeout(1500); await pg.reload(); await pg.wait_for_timeout(3000)
    print('after reload, emo is:', await pg.evaluate("JSON.stringify(getDoc('trades','rt-1').emo)"), '| discipline:', await pg.evaluate("JSON.stringify(getDoc('trades','rt-1').discipline)"))
    await pg.evaluate("location.hash='#trade/rt-1'"); await pg.wait_for_timeout(2000)
    for name in ['Calm','Patient']:
      c=pg.locator("[data-path='emo.before']", has_text=name).first; await c.scroll_into_view_if_needed(); await c.tap(); await pg.wait_for_timeout(500)
    sc=pg.locator("[data-path='emo.confidence'][data-v='4']").first; await sc.tap(); await pg.wait_for_timeout(1500)
    await pg.reload(); await pg.wait_for_timeout(3000)
    print('saved and reloaded:', await pg.evaluate("JSON.stringify(getDoc('trades','rt-1').emo)"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
