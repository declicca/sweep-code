"""
Sweep — UI regression sweep: every page on 4 setups (phone dark FR, small phone light EN, desktop light FR, large desktop dark EN).
Flags JS errors, server 5xx, horizontal overflow, broken pages and English text left in French.
Run in a dev environment: python3 tests/e2e_ui.py   (needs a signed-in storage state at /tmp/gb_state.json)
"""
import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
ROUTES=['dashboard','trades','calendar','journal','analytics','accounts','payouts','news','referral','feedback','settings','import','admin']
JS_CHECK="""(()=>{
 const out={overflow: document.documentElement.scrollWidth - innerWidth};
 const wide=[]; document.querySelectorAll('#main *').forEach(e=>{const r=e.getBoundingClientRect(); if(r.width>0 && r.right>innerWidth+2 && !e.closest('.gc-c2,.seg,.jstrip,.ss-cols,.tchart,.sc-chart,.tbl,.tblwrap,.scrollx,.wr-arch,.cr-rx,.g-chips-row,.mchips,.fbar,.fbars,[style*=overflow]')) wide.push(e.tagName+'.'+(e.className||'').toString().slice(0,40))});
 out.wide=[...new Set(wide)].slice(0,6);
 const fr = window.I18N_FR||{}; const eng=[];
 if (LANG==='fr'){ const w=document.createTreeWalker(document.getElementById('main'),NodeFilter.SHOW_TEXT); let n; while((n=w.nextNode())){ const t=n.textContent.trim(); if(t.length>3 && fr[t] && fr[t]!==t && !n.parentElement.closest('[data-noi18n]')) eng.push(t);} }
 out.untranslated=[...new Set(eng)].slice(0,8);
 return out;})()"""
async def run(br, name, vp, mob, scheme, loc):
  ctx=await br.new_context(viewport=vp,device_scale_factor=1,has_touch=mob,is_mobile=mob,color_scheme=scheme,locale=loc,storage_state='/tmp/gb_state.json')
  pg=await ctx.new_page(); errs=[]
  pg.on('pageerror',lambda e: errs.append('PAGEERR '+str(e)[:150]))
  pg.on('console',lambda m: errs.append('CONSOLE '+m.text[:150]) if m.type=='error' and 'fonts.googleapis' not in m.text and '403' not in m.text else None)
  pg.on('response',lambda r: errs.append(f'HTTP {r.status} {r.url[-60:]}') if r.status>=500 else None)
  await ctx.add_init_script("localStorage.setItem('sw.guide', JSON.stringify({tour:true,tips:{trades:1,calendar:1,journal:1,analytics:1,accounts:1,payouts:1,news:1,settings:1,trade:1},hideStart:true,visited:{}}))")
  if loc.startswith('en'): await ctx.add_init_script("localStorage.setItem('tj.lang','en')")
  res={}
  await pg.goto(B+'/?x=0#dashboard'); await pg.wait_for_timeout(2500)
  for r in ROUTES:
    await pg.evaluate(f"location.hash='#{r}'"); await pg.wait_for_timeout(1300)
    for _ in range(3):
      c=pg.locator('#gSheet [data-g=close]')
      if await c.count(): await c.first.click(); await pg.wait_for_timeout(250)
    res[r]=await pg.evaluate(JS_CHECK)
    if 'could not be displayed' in (await pg.locator('#main').inner_text())[:300]: res[r]['broken']=True
  tid=await pg.evaluate("(S.trades[0]||{}).id"); aid=await pg.evaluate("(S.accounts[0]||{}).id")
  for r in [f'trade/{tid}', f'account/{aid}', 'journal/2026-10-01']:
    await pg.evaluate(f"location.hash='#{r}'"); await pg.wait_for_timeout(1800); res[r.split('/')[0]+'_detail']=await pg.evaluate(JS_CHECK)
  # sheets
  await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1200)
  for js in ["openTicket()", "SweepGame.openPlan()", "SweepGame.openReview()"]:
    try:
      await pg.evaluate(js); await pg.wait_for_timeout(900)
      res['sheet:'+js]=await pg.evaluate("({overflowX: [...document.querySelectorAll('.evp.open, #tkSlide.open')].map(e=>e.scrollWidth-e.clientWidth)})")
      await pg.keyboard.press('Escape'); await pg.evaluate("typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(500)
    except Exception as e: errs.append('SHEET '+js+' '+str(e)[:80])
  await ctx.close()
  bad={k:v for k,v in res.items() if (isinstance(v,dict) and (v.get('overflow',0)>2 or v.get('wide') or v.get('untranslated') or v.get('broken') or any(x>2 for x in v.get('overflowX',[]))))}
  print(f'== {name}: {len(res)} checks, errors={len(errs)}'); 
  for e in sorted(set(errs))[:10]: print('  ',e)
  for k,v in bad.items(): print('  ',k,json.dumps(v,ensure_ascii=False)[:300])
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    await run(br,'phone-dark-fr',{'width':390,'height':844},True,'dark','fr-CA')
    await run(br,'phone-light-en',{'width':375,'height':720},True,'light','en-US')
    await run(br,'desktop-light-fr',{'width':1366,'height':860},False,'light','fr-CA')
    await run(br,'desktop-dark-en',{'width':1920,'height':1080},False,'dark','en-US')
    await br.close()
asyncio.run(main())
