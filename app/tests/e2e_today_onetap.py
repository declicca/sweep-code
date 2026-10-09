import asyncio, datetime, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,1,20,20,0,tzinfo=datetime.timezone.utc)
G=json.dumps({"tips":{},"visited":{"analytics":1},"hideStart":True})
TARGETS=[('Trades','.d-perf:not(.nav-feed) .nav-all, #bottomnav a[data-v=trades]:visible','#trades'),('Calendar','.d-cal .nav-ch:visible, .nav-feed .nav-all','#calendar'),('a day','.d-cal [data-day]:visible, .nav-feed .nav-fdate a','#journal/'),('Stats','.d-trends .nav-ch h2:visible, #bottomnav a[data-v=analytics]:visible, #nav a[data-v=analytics]:visible','#analytics'),
         ('Accounts','.d-acc .nav-ch','#accounts'),('an account','.d-acc .nav-acc','#account/'),('Payouts','.d-pay .nav-ch','#payouts'),('News','.d-news .nav-ch:visible, .nav-feed .nav-fh a','#news'),('Progression','.nav-rt-lv:visible, .nav-rank:not(.ph):visible, .d-today .gc-meta:visible, .nav-hday .nav-hring:visible','any')]
async def run(br,w,h,mob,lang):
  ctx=await br.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,locale={'fr':'fr-CA','en':'en-US','es':'es-ES'}[lang],storage_state='/tmp/show_state.json')
  await ctx.add_init_script(f"localStorage.setItem('sw.guide', {json.dumps(G)}); sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
  pg=await ctx.new_page(); await pg.clock.install(time=NOW); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
  res=[]
  for name,sel,want in TARGETS:
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2300)
    el=pg.locator(sel).first; await el.scroll_into_view_if_needed(); await el.click(); await pg.wait_for_timeout(900)
    ok = (await pg.evaluate("!!document.querySelector('#gSheet .gc-hubwrap')")) if want=='hub' else (await pg.evaluate("!!document.querySelector('#gSheet.open')")) if want=='any' else (await pg.evaluate("location.hash")).startswith(want)
    res.append(f"{name} {'✅' if ok else '❌'}")
  print(f'{w}-{lang}:', ' · '.join(res), '| errors', errs[:2]); await ctx.close()
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for w,h,mob in [(390,844,True),(1440,900,False)]:
      for lang in ['en','fr','es']: await run(br,w,h,mob,lang)
    await br.close()
asyncio.run(main())
