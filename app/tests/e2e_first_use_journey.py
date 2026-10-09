"""Step 0 — real first-use journey: sign-up → profile → first account → first trade → first ring. Counts fields, taps, text."""
import asyncio, random, json, sys, time
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'; OUT='/home/claude/audit'
async def main(w, h, mob, tag):
  async with async_playwright() as p:
    br=await p.chromium.launch(); log=[]; taps=0; typed=0
    ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA')
    await ctx.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg=await ctx.new_page(); errs=[]
    import datetime as _dt; await pg.clock.install(time=_dt.datetime(2026,10,6,12,30,0,tzinfo=_dt.timezone.utc))   # same day as the server; pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
    async def screen(name):
      await pg.wait_for_timeout(500)
      info=await pg.evaluate("""(()=>{const vis=e=>e.offsetParent!==null&&getComputedStyle(e).visibility!=='hidden'; const f=[...document.querySelectorAll('input:not([type=hidden]),select,textarea')].filter(vis).length; const b=[...document.querySelectorAll('button,a.btn,[role=button]')].filter(vis).length; const top=document.querySelector('.nav-dlg.open, .nav-am.open, #tkSlide.open, #gSheet, .gd-help-ov')||document.querySelector('#main')||document.body; return {fields:f, buttons:b, text:(top.innerText||'').replace(/\\s+/g,' ').trim().slice(0,220)}})()""")
      n=len(log)+1; await pg.screenshot(path=f'{OUT}/{tag}-{n:02d}-{name}.png')
      log.append(dict(step=n, screen=name, **info, taps_so_far=taps, typed_fields_so_far=typed))
    async def tap(sel, **kw):
      nonlocal taps; el=pg.locator(sel).first; await el.click(**kw); taps+=1; await pg.wait_for_timeout(500)
    async def type_(sel, v):
      nonlocal taps, typed; el=pg.locator(sel).first; await el.fill(v); taps+=1; typed+=1; await pg.wait_for_timeout(150)
    t0=time.time()
    await pg.goto(B+'/auth.html?signup=1'); await pg.wait_for_timeout(1500); await screen('signup')
    await type_('#email','new%d@gmail.com'%random.randint(1000,999999)); await type_('#password','Testpass123!x'); await pg.wait_for_timeout(1800); await tap('#go'); await pg.wait_for_timeout(3500)
    await screen('profile')
    if await pg.locator('.nav-prof').count():
      await type_('.nav-prof [data-pf=first_name]','Alex'); await type_('.nav-prof [data-pf=last_name]','Martin')
      if await pg.locator('.nav-prof [data-src]').count(): await tap('.nav-prof [data-src=tiktok]')
      await tap('.nav-prof [data-prof-go]'); await pg.wait_for_timeout(1500)
    await screen('before-first-account')
    # first account: the simple welcome screen, then the app's form
    if await pg.locator('[data-hello-go]').count(): await tap('[data-hello-go]'); await pg.wait_for_timeout(600)
    if await pg.locator('form[data-form=account]:visible').count()==0:
      await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
      if await pg.locator('#main [data-act=acct-add]').count(): await tap('#main [data-act=acct-add]')
    await screen('add-account')
    f='form[data-form=account]'
    if await pg.locator(f'{f} [data-st-ph0]').count(): await tap(f'{f} [data-st-ph0=eval]')
    if await pg.locator(f'{f} [data-st-firm]').count(): await screen('firm-choice'); await tap(f'{f} [data-st-firm=topstep]')
    if await pg.locator(f'{f} [data-st-type]').count(): await tap(f'{f} [data-st-type]')
    if await pg.locator(f'{f} [data-st-size]').count(): await screen('size-choice'); await tap(f'{f} [data-st-size]')
    await screen('account-summary')
    await tap(f'{f} [type=submit]'); await pg.wait_for_timeout(2500)
    await screen('after-account')
    # first trade
    for _ in range(4):
      if await pg.locator('.nav-am-ask [data-am-pick=manual]').count(): await screen('add-way-question'); await tap('.nav-am-ask [data-am-pick=manual]'); await pg.wait_for_timeout(900); continue
      if await pg.locator('.nav-am-shot.open').count(): await screen('add-trade-entry'); await tap('.nav-am-shot .nav-am-alt [data-am=to-manual]'); await pg.wait_for_timeout(1200); continue
      if await pg.locator('#tkSlide.open, .nav-am-shot.open').count(): break
      if await pg.locator('#gSheet [data-g=plan-skip]').count():
        await screen('plan-first')
        await tap('#gSheet button:has-text("Long")')
        await type_('#gSheet input:visible','500')   # max loss of the day
        sv=pg.locator("#gSheet button:has-text(\"Enregistrer\")").last; await sv.click(); taps+=1; await pg.wait_for_timeout(1500); continue
      if await pg.locator('.nav-am-ask [data-am-pick=manual]').count(): await screen('add-way-question'); await tap('.nav-am-ask [data-am-pick=manual]'); continue
      await pg.evaluate("openTicket()"); taps+=1; await pg.wait_for_timeout(1200)
      if await pg.locator('#gSheet [data-g=plan-skip]').count():
        await screen('plan-first'); await tap('#gSheet button:has-text("Long")'); sv=pg.locator("#gSheet button:has-text(\"Enregistrer\")").last; await sv.click(); taps+=1; await pg.wait_for_timeout(1500)
      if await pg.locator('.nav-am-ask [data-am-pick=manual]').count(): await screen('add-way-question'); await tap('.nav-am-ask [data-am-pick=manual]')
    await pg.wait_for_timeout(800); await screen('trade-form')
    if await pg.locator('#tkSlide.open').count():
      await tap('#tkSlide [data-v=long]'); await type_('#tkSlide [data-tk=entry]','25100'); await type_('#tkSlide [data-tk=exit]','25120')
      await tap('#tkSlide [data-act=tk-save]'); await pg.wait_for_timeout(2500)
    await screen('after-first-trade')
    if await pg.locator('.nav-inst.open').count(): await tap('[data-inst-ok]')
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(2500)
    rings=await pg.evaluate("(()=>{const s=window.SweepGame&&SweepGame.state&&SweepGame.state(); return s&&s.today? JSON.stringify(s.today.rings):'—'})()")
    await screen('today-rings')
    secs=round(time.time()-t0)
    est=taps*1.2+typed*3.5
    print(json.dumps({'tag':tag,'screens':len(log),'taps':taps,'typed_fields':typed,'estimated_seconds_for_a_person':round(est),'rings_after':rings,'errors':errs[:3],'log':log}, ensure_ascii=False))
    await br.close()
w,h,mob,tag=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]=='1',sys.argv[4]
asyncio.run(main(w,h,mob,tag))
