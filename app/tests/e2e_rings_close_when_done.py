import asyncio, random, datetime
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1')")
    await pg.clock.install(time=datetime.datetime(2026,10,6,13,20,0,tzinfo=datetime.timezone.utc))
    await pg.goto('http://127.0.0.1:8095/auth.html?signup=1'); await pg.wait_for_timeout(1200)
    await pg.fill('#email','rg%d@gmail.com'%random.randint(1,999999)); await pg.fill('#password','Testpass123!x'); await pg.wait_for_timeout(2100); await pg.click('#go'); await pg.wait_for_timeout(3500)
    await pg.fill('.nav-prof [data-pf=first_name]','R'); await pg.fill('.nav-prof [data-pf=last_name]','G'); await pg.click('.nav-prof [data-prof-go]'); await pg.wait_for_timeout(1200)
    await pg.evaluate("put('firms',{id:'f1',name:'Apex'}); put('accounts',{id:'acc1',name:'PA 50K',firm_id:'f1',starting_balance_c:5000000,status:'active'})"); await pg.wait_for_timeout(600)
    # a trade first (08:30), the plan AFTER it (late), a short against a long bias, no checklist; then the review
    await pg.evaluate("put('trades',{id:'t1',account_id:'acc1',instrument:'NQ',direction:'short',contracts:1,date:'2026-10-06',entry_time:'08:30:00',exit_time:'09:00:00',entry:31241,exit:31230,pnl_c:22000,fees_c:350})"); await pg.wait_for_timeout(800)
    await pg.evaluate("put('journals',{id:'2026-10-06', pre:{saved_at:Math.floor(Date.now()/1000), bias:'bullish', max_loss:'2000', setups:[]}, post:{well:'ok', tomorrow:'wait', discipline:3, reviewed_at:new Date().toISOString()}})"); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("fetch('api/game/today',{credentials:'same-origin',headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>JSON.stringify({rings:j.today.rings, swept:j.today.swept, compliant:j.today.compliant, trades:j.today.trades, plan_late:j.today.plan_late, exec_score:j.today.exec_score}))")
    print('plan made after the trade, trade against the bias, review done:', r)
    await br.close()
asyncio.run(main())
