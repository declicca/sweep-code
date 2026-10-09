import asyncio, datetime, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,9,20,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    u='po%d'%random.randint(1000,9999)
    await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
    # the profile is asked before the first account (since 2026-10-06): filled here so the « Complete your profile » window does not cover the page
    await ctx.request.post(B+'/api/me/profile', data={'first_name':'Test','last_name':'Trader','username':u}, headers={'X-Requested-With':'fetch'})
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
    await pg.evaluate("put('accounts',{id:'a-apex',name:'PA 50K',firm_id:'',starting_balance_c:5000000,status:'active'}); put('accounts',{id:'a-top',name:'XFA 50K',firm_id:'',starting_balance_c:5000000,status:'active'})"); await pg.wait_for_timeout(1200)
    async def apply(aid, firm, typ_idx, size_idx, phase='funded'):
      await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(2000)
      box=pg.locator('.ux-preset-apply')
      await box.locator('[data-st-open]').click(); await pg.wait_for_timeout(400)
      await box.locator(f'[data-st-firm="{firm}"]').click(); await pg.wait_for_timeout(300)
      if await box.locator('[data-st-type]').count(): await box.locator('[data-st-type]').nth(typ_idx).click(); await pg.wait_for_timeout(300)
      await box.locator('[data-st-size]').nth(size_idx).click(); await pg.wait_for_timeout(300)
      if await box.locator(f'[data-st-phase={phase}]').count(): await box.locator(f'[data-st-phase={phase}]').click(); await pg.wait_for_timeout(300)
      await box.locator('[data-pk-apply]').click(); await pg.wait_for_timeout(1500)
      return await pg.evaluate(f"JSON.stringify(Object.fromEntries(Object.entries(getDoc('accounts','{aid}').rules).filter(([k,v])=>k.startsWith('payout')||k==='consistency_pct')))")
    print('Apex EOD 50K funded preset →', await apply('a-apex','apex',0,1))
    print('Topstep 50K funded preset →', await apply('a-top','topstep',0,0))
    # Apex: 4 days ≥ $250 + one day at $200 → not ready
    days=[('2026-10-01',60000),('2026-10-02',50000),('2026-10-05',20000),('2026-10-06',40000),('2026-10-07',50000)]
    for i,(d,pnl) in enumerate(days):
      await pg.evaluate(f"put('trades',{{id:'pa-{i}',account_id:'a-apex',instrument:'NQ',date:'{d}',entry_time:'10:00:00',direction:'long',contracts:1,pnl_c:{pnl},pnl_manual:true,emo:{{}},review:{{}},discipline:{{}}}})")
    await pg.wait_for_timeout(1200)
    await pg.evaluate("location.hash='#account/a-apex'"); await pg.wait_for_timeout(1800)
    print('Apex with 4 qualifying days:', await pg.evaluate("document.querySelector('#main .nav-po').innerText.replace(/\\n+/g,' | ')"))
    await pg.evaluate("put('trades',{id:'pa-5',account_id:'a-apex',instrument:'NQ',date:'2026-10-08',entry_time:'10:00:00',direction:'long',contracts:1,pnl_c:40000,pnl_manual:true,emo:{},review:{},discipline:{}})"); await pg.wait_for_timeout(1200)
    await pg.evaluate("render()"); await pg.wait_for_timeout(800)
    print('Apex with the 5th day:', await pg.evaluate("document.querySelector('#main .nav-po').innerText.replace(/\\n+/g,' | ')"))
    await pg.locator('#main .nav-po').screenshot(path='/tmp/po_apex.png')
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
    print('Today badge on the Apex account:', await pg.evaluate("[...document.querySelectorAll('.nav-acc')].map(a=>a.querySelector('b').textContent+(a.querySelector('.nav-ready')?' ✓ ready':' —')).join(' | ')"))
    # Topstep: 5 winning days of $150+ … then a payout request resets the count
    for i,d in enumerate(['2026-10-01','2026-10-02','2026-10-05','2026-10-06','2026-10-07']):
      await pg.evaluate(f"put('trades',{{id:'pt-{i}',account_id:'a-top',instrument:'NQ',date:'{d}',entry_time:'10:00:00',direction:'long',contracts:1,pnl_c:{[30000,16000,14000,25000,20000][i]},pnl_manual:true,emo:{{}},review:{{}},discipline:{{}}}})")
    await pg.wait_for_timeout(1200)
    await pg.evaluate("location.hash='#account/a-top'"); await pg.wait_for_timeout(1800)
    print('Topstep (one day at $140):', await pg.evaluate("document.querySelector('#main .nav-po').innerText.replace(/\\n+/g,' | ')"))
    await pg.evaluate("put('payouts',{id:'po-1',account_id:'a-top',amount_c:50000,status:'paid',request_date:'2026-10-06',approval_date:'2026-10-07',payment_date:'2026-10-07'})"); await pg.wait_for_timeout(1200); await pg.evaluate("render()"); await pg.wait_for_timeout(800)
    print('Topstep after a payout requested on Oct 6:', await pg.evaluate("document.querySelector('#main .nav-po').innerText.replace(/\\n+/g,' | ')"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
