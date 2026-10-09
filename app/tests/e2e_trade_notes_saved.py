import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    for tid,how in [('nb-db','stored as [] on the server'),('nb-mem','[] in the open app (old copy)')]:
      if tid=='nb-mem':
        await pg.evaluate("(()=>{const t=S.trades.find(x=>x.id==='nb-mem'); if(t){t.review=[]; t.discipline=[];}})()")
      await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(1800)
      print(tid, '| review on load:', await pg.evaluate(f"JSON.stringify(getDoc('trades','{tid}').review)"))
      boxes=pg.locator("#main textarea[data-bind*='review.']")
      cnt=await boxes.count()
      for i,txt in enumerate(['Rejet du high','Patience','Sortie trop tôt','Attendre la clôture'][:cnt]):
        b=boxes.nth(i); await b.scroll_into_view_if_needed(); await b.tap(); await b.type(txt, delay=5); await pg.wait_for_timeout(200)
      await pg.wait_for_timeout(2500)
      await pg.reload(); await pg.wait_for_timeout(3000)
      print(f'   {how}: after typing and reload →', await pg.evaluate(f"JSON.stringify(getDoc('trades','{tid}').review)"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
