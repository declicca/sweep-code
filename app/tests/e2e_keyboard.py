import asyncio, datetime, json, re
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,1,20,20,0,tzinfo=datetime.timezone.utc)
G=json.dumps({"tips":{},"visited":{"analytics":1},"hideStart":True})
WK={'en':r'^(Week|This week)$','fr':r'^(Semaine|Cette semaine)$','es':r'^(Semana|Esta semana)$'}
async def tab_to(pg, test_js, maxn=80):
  for i in range(maxn):
    if await pg.evaluate(f"(()=>{{const e=document.activeElement; return !!e && ({test_js})}})()"): return i
    await pg.keyboard.press('Tab')
  return None
async def run(br, lang):
  ctx=await br.new_context(viewport={'width':1440,'height':900},color_scheme='dark',locale={'fr':'fr-CA','en':'en-US','es':'es-ES'}[lang],storage_state='/tmp/show_state.json')
  await ctx.add_init_script(f"localStorage.setItem('sw.guide', {json.dumps(G)}); sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
  pg=await ctx.new_page(); await pg.clock.install(time=NOW); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
  async def home():
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2600); await pg.evaluate("document.activeElement&&document.activeElement.blur()")
  res={}
  await home(); await pg.keyboard.press('n'); await pg.wait_for_timeout(700); res['add trade (N)']=await pg.evaluate("!!document.querySelector('#tkSlide.open, .nav-am-shot.open')")
  await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500); res['Esc closes the form']=await pg.evaluate("!document.querySelector('#tkSlide.open')")
  await home(); n=await tab_to(pg,"e.matches('#nav a[data-v=analytics]')"); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(1200)
  rx=WK[lang].replace('\\\\','\\')
  n2=await tab_to(pg,f"e.matches('#main button, #main a') && /{rx}/.test(e.innerText.trim())"); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(700)
  res['week stats']=n is not None and n2 is not None and await pg.evaluate("location.hash==='#analytics'")
  await home(); await tab_to(pg,"e.matches('#nav a[data-v=accounts]')"); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(1200)
  await tab_to(pg,"e.matches('tr[data-href]')"); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(1200)
  res['account + drawdown']=await pg.evaluate("location.hash.startsWith('#account/') && /drawdown/i.test(document.querySelector('#main').innerText)")
  await home(); res['streak (visible)']=await pg.evaluate("!!document.querySelector('.nav-rank')")
  await home(); await tab_to(pg,"e.matches('aside.side .who')"); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
  inside=await pg.evaluate("!!document.activeElement.closest('#navMenu')")
  await tab_to(pg,"e.matches('#navMenu [role=menuitem][data-navm=plan]')",20); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(1000)
  res['subscription']=inside and await pg.evaluate("location.hash==='#plan'")
  await home(); await tab_to(pg,"e.matches('aside.side .who')"); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(400)
  # focus trap: 15 Tabs stay inside the menu; Escape returns focus to the avatar
  for i in range(15): await pg.keyboard.press('Tab')
  trap=await pg.evaluate("!!document.activeElement.closest('#navMenu')")
  await pg.keyboard.press('Escape'); await pg.wait_for_timeout(400)
  back=await pg.evaluate("document.activeElement && document.activeElement.matches('aside.side .who')")
  res['menu: focus stays inside']=trap; res['menu: Esc returns focus to avatar']=back
  await pg.keyboard.press('Enter'); await pg.wait_for_timeout(400); await tab_to(pg,"e.matches('#navMenu [data-navm=settings]')",20); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(1500)
  ex=await tab_to(pg,"/ZIP/.test(e.innerText||'')",260)
  res['export data (3 steps)']=ex is not None
  # a sheet: opened from the keyboard, focus trapped, returned on close
  await home(); await tab_to(pg,"e.matches('.nav-rank, .nav-lvring, .nav-rt-lv')"); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(1200)
  for i in range(30): await pg.keyboard.press('Tab')
  trap=await pg.evaluate("!!document.activeElement.closest('#gSheet')"); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(700)
  res['sheet: focus trapped, returns to trigger']=trap and await pg.evaluate("document.activeElement && document.activeElement.matches('.nav-rank, .nav-lvring, .nav-rt-lv')")
  ring=await pg.evaluate("getComputedStyle(document.activeElement).outlineStyle+' '+getComputedStyle(document.activeElement).outlineWidth")
  print(lang, ' | '.join(f"{k}: {'✅' if v else '❌'}" for k,v in res.items()), '| focus ring:', ring, '| errors', errs[:2])
  await ctx.close()
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for lang in ['fr','en','es']: await run(br, lang)
    await br.close()
asyncio.run(main())
