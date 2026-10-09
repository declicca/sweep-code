import asyncio, datetime, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,1,20,20,0,tzinfo=datetime.timezone.utc)
G=json.dumps({"tips":{},"visited":{"analytics":1},"hideStart":True})
WEEK={'en':'Week','fr':'Semaine','es':'Semana'}; SUB={'en':'Subscription','fr':'Abonnement','es':'Suscripción'}; SET={'en':'Settings','fr':'Réglages','es':'Ajustes'}
EXP={'en':'Export','fr':'Export','es':'Export'}
OLD=['#dashboard','#calendar','#journal','#journal/weekly','#payouts','#news','#analytics','#plan','#settings','#referral','#feedback','#import','#accounts','#trades','#today','#stats','#subscription','#progress']
async def run(br,w,h,mob,lang):
  ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale={'fr':'fr-CA','en':'en-US','es':'es-ES'}[lang],storage_state='/tmp/show_state.json')
  await ctx.add_init_script(f"localStorage.setItem('sw.guide', {json.dumps(G)}); localStorage.setItem('tj.lang', JSON.stringify('{lang}')); sessionStorage.setItem('sw.modal','1')")
  pg=await ctx.new_page(); await pg.clock.install(time=NOW); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
  async def home():
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2600)
    for _ in range(4):
      c=pg.locator('#gSheet [data-g=close], .nt-modal .btn')
      if await c.count(): await c.first.evaluate('e=>e.click()'); await pg.wait_for_timeout(250)
  tab=lambda v: f'#bottomnav a[data-v={v}]' if mob else f'#nav a[data-v={v}]'
  res={}
  # 1 add a trade
  await home(); await pg.locator('.bottomnav .plus' if mob else 'aside.side .new').first.click(); await pg.wait_for_timeout(700)
  # no plan yet today: « + » shows the plan first, « Skip, add my trade » goes straight to the form (2 taps)
  taps='1'
  if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(700); taps='2 (plan first)'
  # first time: « how do you like to add a trade? » (asked once) → « by hand » opens the form
  if await pg.locator('.nav-am-ask [data-am-pick=manual]').count(): await pg.locator('.nav-am-ask [data-am-pick=manual]').click(); await pg.wait_for_timeout(900); taps=taps+' + way chosen once'
  res['add trade']=(taps, await pg.evaluate("!!document.querySelector('#tkSlide.open, .nav-am-shot.open')"))
  if await pg.locator('.nav-am.open [data-am=close]').count(): await pg.locator('.nav-am.open [data-am=close]').first.click(); await pg.wait_for_timeout(500)
  try: await pg.wait_for_selector('.nav-am.open, #tkSlide.open', timeout=4000)   # the sheet can open a moment after the tap
  except Exception: pass
  await pg.wait_for_timeout(400)
  for _ in range(4):   # the sheet may still be opening: close it until it is gone
    if not await pg.locator('.nav-am.open').count(): break
    print('SHEET:', await pg.evaluate("[...document.querySelectorAll('.nav-am.open button, .nav-am.open a')].slice(0,6).map(b=>(b.dataset.am||'')+':'+b.textContent.trim().slice(0,20)).join(' | ')"))
    btn = pg.locator('.nav-am.open [data-am=close]')
    if await btn.count(): await btn.first.click()
    else: await pg.keyboard.press('Escape')
    await pg.wait_for_timeout(600)
  await pg.evaluate("localStorage.removeItem('sw.planSkip')")
  # 2 week stats
  await home()
  try:
    await pg.locator(tab('analytics')).first.click(timeout=15000)
  except Exception:   # say what covers the tab bar, then fail
    print('COVERED BY:', await pg.evaluate("(()=>{const b=document.querySelector('#bottomnav a[data-v=analytics]'); if(!b) return 'no tab'; const r=b.getBoundingClientRect(); const e=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2); return (e?e.outerHTML.slice(0,160):'nothing')+' | open: '+[...document.querySelectorAll('.open, [aria-modal=true], .nt-modal, .nav-dlg, .nav-undo')].filter(x=>x.getClientRects().length).map(x=>x.className).join(' / ')+' | '+location.hash})()"))
    raise
  await pg.wait_for_timeout(1200)
  import re as _re
  WK={'en':r'^(Week|This week)$','fr':r'^(Semaine|Cette semaine)$','es':r'^(Semana|Esta semana)$'}[lang]
  wk=pg.locator('#main button, #main a').filter(has_text=_re.compile(WK)).first
  ok2=False
  if await wk.count(): await wk.click(); await pg.wait_for_timeout(800); ok2=await wk.evaluate("e=>e.classList.contains('on')||e.getAttribute('aria-pressed')==='true'||e.getAttribute('aria-selected')==='true'")
  res['week stats']=('2 (or 0: « This week » card on Today)', ok2)
  # 3 prop account + drawdown distance
  await home(); await pg.locator(tab('accounts')).first.click(); await pg.wait_for_timeout(1200)
  acc=pg.locator('#main [data-href^="#account/"], #main a[href^="#account/"]').first; await acc.click(); await pg.wait_for_timeout(1300)
  res['account + drawdown']=('2', await pg.evaluate("/drawdown/i.test(document.querySelector('#main').innerText)"))
  # 4 streak
  await home(); res['streak']=('0', await pg.evaluate("[...document.querySelectorAll('.nav-rank, .nav-hstreak, .g-today .gc-mid, .nav-lvring, .nav-rt-streak')].some(e=>e.offsetParent!==null && /\\d/.test(e.innerText))"))
  # 5 subscription
  await home(); await pg.locator('aside.side .who').first.click(); await pg.wait_for_timeout(400)
  await pg.locator('#navMenu [role=menuitem][data-navm=plan]').click(); await pg.wait_for_timeout(1300)
  res['subscription']=('2', await pg.evaluate("location.hash==='#plan' && document.querySelector('#main').innerText.length>60"))
  # 6 export data
  await home(); await pg.locator('aside.side .who').first.click(); await pg.wait_for_timeout(400)
  await pg.locator('#navMenu [data-navm=settings]').click(); await pg.wait_for_timeout(1500)
  btn=pg.locator('#main [data-ux-export], #main button:has-text("ZIP"), #main a:has-text("ZIP")').first
  res['export data']=('3', await btn.count()>0)
  # old routes never land on an empty page
  empty=[]
  for r in OLD:
    await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(700)
    n=await pg.evaluate("document.querySelector('#main').innerText.trim().length")
    if n<40: empty.append(r)
    await pg.evaluate("document.querySelector('#gSheet [data-g=close]')&&document.querySelector('#gSheet [data-g=close]').click()")
  # floating elements over content
  await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(900)
  floats=await pg.evaluate("[...document.querySelectorAll('body *')].filter(e=>{const s=getComputedStyle(e);return s.position==='fixed'&&e.offsetWidth>40&&e.offsetHeight>30&&s.display!=='none'&&s.visibility!=='hidden'&&!e.closest('#bottomnav,aside.side,#toast,.toast,#scrim')&&!/scrim|toast|bottomnav|side|sheet|drawer|modal|cmd|nav-menu|evp|ask/.test(e.className+e.id)}).map(e=>e.className||e.id).slice(0,5)")
  print(f"{w}-{lang}", ' | '.join(f"{k}: {'✅' if v[1] else '❌'} ({v[0]})" for k,v in res.items()), '| empty routes:', empty or 'none', '| floating:', floats or 'none', '| errors:', errs[:2])
  await ctx.close()
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for w,h,mob in [(390,844,True),(1440,900,False)]:
      for lang in ['en','fr','es']: await run(br,w,h,mob,lang)
    await br.close()
asyncio.run(main())
