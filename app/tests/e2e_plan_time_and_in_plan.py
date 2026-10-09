import asyncio, random, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    await pg.clock.install(time=datetime.datetime(2026,10,6,12,20,0,tzinfo=datetime.timezone.utc))   # 08:20 ET: the plan is made here
    await pg.goto(B+'/auth.html?signup=1'); await pg.wait_for_timeout(1200)
    await pg.fill('#email','pf%d@gmail.com'%random.randint(1,999999)); await pg.fill('#password','Testpass123!x'); await pg.wait_for_timeout(2100); await pg.click('#go'); await pg.wait_for_timeout(3500)
    await pg.fill('.nav-prof [data-pf=first_name]','P'); await pg.fill('.nav-prof [data-pf=last_name]','F'); await pg.click('.nav-prof [data-prof-go]'); await pg.wait_for_timeout(1200)
    await pg.evaluate("put('firms',{id:'f1',name:'Apex'}); put('accounts',{id:'acc1',name:'PA 50K',firm_id:'f1',starting_balance_c:5000000,status:'active'})"); await pg.wait_for_timeout(800)
    # the plan, saved at 08:20 (the server does not look at it yet)
    await pg.evaluate("put('journals',{id:'2026-10-06', pre:{saved_at: Math.floor(Date.now()/1000), bias:'bullish', max_loss:'2000', max_trades:'5', setups:[], levels:'31200-31240'}})"); await pg.wait_for_timeout(1500)
    # a long trade at 08:30 without a stop, logged later
    await pg.evaluate("put('trades',{id:'t1',account_id:'acc1',instrument:'NQ',direction:'long',contracts:2,date:'2026-10-06',entry_time:'08:30:00',exit_time:'09:01:00',entry:31241.63,exit:31264.5,pnl_c:91480,fees_c:700})"); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("fetch('api/game/today',{credentials:'same-origin',headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>JSON.stringify({rings:j.today.rings, compliant:j.today.compliant, trades:j.today.trades, detail:(j.today.detail||[]).map(d=>d.v)}))")
    print('long trade, plan saved before it, server checking at 09:05:', r)
    await pg.evaluate("put('trades',{id:'t2',account_id:'acc1',instrument:'NQ',direction:'short',contracts:1,date:'2026-10-06',entry_time:'09:20:00',exit_time:'09:30:00',entry:31270,exit:31260,pnl_c:20000,fees_c:350})"); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("fetch('api/game/today',{credentials:'same-origin',headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>JSON.stringify({rings:j.today.rings, compliant:j.today.compliant, trades:j.today.trades, detail:(j.today.detail||[]).map(d=>d.v)}))")
    print('plus a short trade on a long bias:', r)
    await br.close()
asyncio.run(main())
