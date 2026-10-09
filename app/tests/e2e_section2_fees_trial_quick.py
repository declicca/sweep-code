import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.goto(B+'/?x=1#accounts'); await pg.wait_for_timeout(2500)
    ne=await pg.evaluate("S.expenses.length")
    await pg.locator('#main [data-act=acct-add]:not([data-v=\"0\"])').first.click(); await pg.wait_for_timeout(900)
    f='form[data-form=account]'
    await pg.locator(f'{f} [data-st-ph0=eval]').click(); await pg.locator(f'{f} [data-st-firm=topstep]').click(); await pg.wait_for_timeout(300)
    if await pg.locator(f'{f} [data-st-type]').count(): await pg.locator(f'{f} [data-st-type]').first.click()
    await pg.locator(f'{f} [data-st-size]').nth(2).click(); await pg.wait_for_timeout(700)
    print('fee option:', await pg.evaluate("(document.querySelector('.nav-fee')||{innerText:'none'}).innerText.replace(/\\n/g,' ')"), '| amount', await pg.evaluate("(document.querySelector('[name=nav_fee]')||{}).value"), '| free cost field hidden:', await pg.evaluate("(document.querySelector('[name=nav_cost]')||{closest:()=>({hidden:'?'})}).closest('.nav-acc-x').hidden"))
    await pg.locator('.nav-fee').screenshot(path='/tmp/s2_fee.png')
    await pg.locator(f'{f} [type=submit]').click(); await pg.wait_for_timeout(2500)
    print('expense added:', await pg.evaluate(f"S.expenses.length")-ne, await pg.evaluate("JSON.stringify(S.expenses.slice(-1).map(e=>[e.category,e.amount_c/100]))"))
    await pg.evaluate("const a=S.accounts.slice(-1)[0]; if(a) remove('accounts',a.id); const e=S.expenses.slice(-1)[0]; if(e) remove('expenses',e.id)"); await pg.wait_for_timeout(500)
    # trial rules
    for kind,left in [('trial',3),('trial',10),('early_access',10)]:
      await pg.evaluate(f"document.querySelectorAll('.nav-trial').forEach(x=>x.remove()); Object.keys(localStorage).filter(k=>k.startsWith('sw.trialCard')).forEach(k=>localStorage.removeItem(k)); BILL.st=Object.assign({{}},BILL.st||{{}},{{trial:{{kind:'{kind}',plan:'pro',ends_at:'2026-10-20T00:00:00Z',days_left:{left}}}}}); location.hash='#dashboard'; render()"); await pg.wait_for_timeout(1200)
      print(f'trial {kind}, {left} days left → card:', await pg.locator('.nav-trial').count())
    print('errors', errs[:3]); await ctx.close()
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True, storage_state='/home/claude/media/alex_state.json', locale='fr-CA'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    print('phone quick access visible:', await pg.evaluate("(()=>{const q=document.querySelector('.d-quick'); return !!(q&&q.offsetParent)})()"), '| order:', await pg.evaluate("[...document.querySelectorAll('.nav-dash [class*=\"d-\"]')].filter(e=>e.offsetParent&&/\\bd-(today|perf|pay|acc|quick)\\b/.test(e.className)).sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top).map(e=>(e.className.match(/\\bd-(today|perf|pay|acc|quick)\\b/)||[''])[0]).join(' → ')"))
    await br.close()
asyncio.run(main())
