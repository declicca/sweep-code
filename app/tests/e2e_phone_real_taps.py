import asyncio, random, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def run(p, state, label, fresh=False):
    br=await p.chromium.launch(); dev=p.devices['iPhone 13']; out=[]
    ctx=await br.new_context(**dev, **({'storage_state':state} if state else {}), locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:160]))
    async def T(desc, sel, check=None, wait=900):
        loc=pg.locator(sel).first
        try:
            if not await loc.count(): out.append(f'· {desc}: (absent)'); return False
            await loc.tap(timeout=3500); await pg.wait_for_timeout(wait)
            ok = True if check is None else await pg.evaluate(check)
            out.append(f"{'✅' if ok else '❌'} {desc}"); return ok
        except Exception as e:
            cov=await pg.evaluate(f"(()=>{{const e=document.querySelector({sel!r}); if(!e) return ''; const r=e.getBoundingClientRect(); const t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return t? t.tagName+'.'+String(t.className).slice(0,40):'none'}})()")
            out.append(f'❌ {desc}: tap blocked by {cov}'); return False
    if fresh:
        await pg.goto(B+'/auth.html?signup=1'); await pg.wait_for_timeout(1200)
        await pg.fill('#email','tap%d@gmail.com'%random.randint(1,999999)); await pg.fill('#password','Testpass123!x'); await pg.wait_for_timeout(2100)
        await T('sign-up button','#go',"!location.pathname.includes('auth')",3500)
        if await pg.locator('.nav-prof').count():
            await pg.fill('.nav-prof [data-pf=first_name]','Tap'); await pg.fill('.nav-prof [data-pf=last_name]','Test')
            await T('profile chip','.nav-prof [data-src=tiktok]',"!!document.querySelector('.nav-prof [data-src=tiktok].on')",300)
            await T('profile continue','.nav-prof [data-prof-go]',"!document.querySelector('.nav-prof')",1500)
    else:
        await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    # whatever window opened by itself: it must answer
    for i in range(4):
        if await pg.locator('.g-ob').count():
            if await pg.locator('.g-ob button:has-text("Plus tard")').count(): await T('onboarding « Plus tard »','.g-ob button:has-text("Plus tard")',"!document.querySelector('.g-ob')",1200)
            else: await T('onboarding first button','.g-ob button',None,1200)
        elif await pg.locator('.nav-dlg.open, .nav-inst.open').count(): await T('window button','.nav-dlg.open .btn.primary, .nav-inst [data-inst-ok]',None,800)
        elif await pg.locator('#gSheet').count(): await T('sheet close','#gSheet [data-g=close], #gSheet .g-x',None,800)
        else: break
    if await pg.locator('[data-hello-go]').count(): await T('« Ajouter mon compte »','[data-hello-go]',"!!document.querySelector('form[data-form=account]')",800)
    for name,h in [('Trades','#trades'),('Stats','#analytics'),('Comptes','#accounts'),('Aujourd’hui','#dashboard')]:
        await T(f'bottom bar → {name}', f'#bottomnav a[href="{h}"], .bottomnav a[href="{h}"], #bottomnav a[data-v="{h[1:]}"]', f"location.hash.startsWith('{h}')||(location.hash===''&&'{h}'==='#dashboard')", 1100)
    await T('« + » (add a trade)','#bottomnav .plus, .bottomnav .plus, #bottomnav [data-act=add-trade]',"!!document.querySelector('#tkSlide.open, .nav-am.open, #gSheet, #drawer.on')",1300)
    for _ in range(2):
        if await pg.locator('#gSheet').count(): await T('plan sheet: skip / close','#gSheet [data-g=plan-skip], #gSheet [data-g=close]',None,900)
    if await pg.locator('#tkSlide.open').count(): await T('trade form: cancel','#tkSlide [data-act=tk-cancel], #tkSlide .tk-x, #tkSlide button:has-text("Annuler")',"!document.querySelector('#tkSlide.open')",900)
    if await pg.locator('.nav-am.open').count(): await T('screenshot form: cancel','.nav-am.open [data-am=close]',"!document.querySelector('.nav-am.open')",900)
    await T('avatar menu','.nav-m-who, .mhdr .who, header .who, [data-act=menu], .nav-av',"!!document.querySelector('#navMenu.open, .nav-menu.open, #navMenu:not([hidden])')",800)
    await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    await T('search icon','.nav-search',None,800); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    await T('routine: help ?','.nav-rt [data-rt=help]',"!!document.querySelector('.nav-rt-help-t:not([hidden])')",400)
    if await pg.locator('.nav-rt.closed-rt').count(): await T('routine: open','.nav-rt-tg',"!document.querySelector('.nav-rt.closed-rt')",600)
    await T('routine: plan button','.nav-rt [data-rt=plan]',"!!document.querySelector('#gSheet')",1200)
    if await pg.locator('#gSheet').count(): await T('plan sheet close','#gSheet [data-g=close]',"!document.querySelector('#gSheet')",900)
    await T('trades: first row','#main a.trow',"location.hash.startsWith('#trade/')",1500) if await pg.evaluate("location.hash='#trades'") is None else None
    print(f'\n== {label}'); [print('  ',x) for x in out]; print('   errors', errs[:3])
    await br.close()
async def main():
  async with async_playwright() as p:
    await run(p, '/tmp/show_state.json', 'existing trader (sample data)')
    await run(p, '/home/claude/media/alex_state.json', 'existing trader (Alex, onboarding window shows)')
    await run(p, None, 'brand-new trader', fresh=True)
asyncio.run(main())
