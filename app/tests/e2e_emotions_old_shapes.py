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
    shapes={'ef-list':["Calm"], 'ef-text':"Calm", 'ef-beftext':{'before':'Calm','confidence':2}}
    for tid,emo in shapes.items():
      await pg.evaluate(f"put('trades',{{id:'{tid}',account_id:'{acc}',instrument:'NQ',date:'2026-10-02',entry_time:'10:00:00',exit_time:'10:05:00',direction:'long',contracts:1,entry:30100,exit:30120,pnl_c:4000,emo:{json.dumps(emo)}}})")
    await pg.wait_for_timeout(1500)
    for tid in shapes:
      await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(1800)
      for name in ['Patient','Focused']:
        c=pg.locator("[data-path='emo.before']", has_text=name).first; await c.scroll_into_view_if_needed(); await c.tap(); await pg.wait_for_timeout(600)
      sc=pg.locator("[data-path='emo.confidence'][data-v='4']").first
      if await sc.count(): await sc.tap(); await pg.wait_for_timeout(600)
      ex=pg.locator("[data-path='emo.execution'][data-v='3'], [data-path='emo.quality'][data-v='3']").first
      if await ex.count(): await ex.tap(); await pg.wait_for_timeout(600)
      await pg.wait_for_timeout(800)
      print(f'{tid:11}', await pg.evaluate(f"JSON.stringify(getDoc('trades','{tid}').emo)"), '| on screen:', await pg.evaluate("[...document.querySelectorAll('[data-path^=\"emo.\"].on')].map(b=>b.textContent.trim()).join(',')"))
    for tid in shapes: await pg.evaluate(f"(()=>{{ const i=S.trades.findIndex(t=>t.id==='{tid}'); }})()")
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
