import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/home/claude/media/alex_state.json'); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:200])); pg.on('console', lambda m: errs.append('console: '+m.text[:160]) if 'Sweep:' in m.text else None)
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    await pg.evaluate("put('accounts',{id:'g1',name:'Apex 50K #1',firm_id:'f-apex',starting_balance_c:5000000,status:'active',group_id:'grp-t'}); put('accounts',{id:'g2',name:'Apex 50K #2',firm_id:'f-apex',starting_balance_c:5000000,status:'active',group_id:'grp-t'})"); await pg.wait_for_timeout(500)
    await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1500)
    print('sheet:', await pg.locator('#gSheet').count(), '| tk open:', await pg.locator('#tkSlide.open').count(), '| am open:', await pg.locator('.nav-am.open').count())
    if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1000)
    print('tk open after skip:', await pg.locator('#tkSlide.open').count(), '| TK:', await pg.evaluate("typeof TK!=='undefined'&&TK? TK.account+' copy '+[...TK.copyTo].join(','):'none'"))
    await pg.evaluate("TK.account='g1'; tkRefresh({panel:true})"); await pg.wait_for_timeout(1000)
    print('after account g1:', await pg.evaluate("[...TK.copyTo].join(',')"), '| errors', errs[:2]); msgs=[]
    await pg.evaluate("['g1','g2'].forEach(i=>remove('accounts',i))"); await br.close()
asyncio.run(main())
