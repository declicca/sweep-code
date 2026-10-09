import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,20,10,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900},locale='en-US',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#journal/2026-10-05'); await pg.wait_for_timeout(2500)
    print('MGC instrument:', await pg.evaluate("JSON.stringify(instOf('MGC'))"))
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
    await pg.locator('#tkSlide [data-tk=inst]').select_option('MGC'); await pg.wait_for_timeout(200)
    await pg.locator('#tkSlide [data-v=short]').first.click()
    async def typ(k,v):
      el=pg.locator(f'#tkSlide [data-tk={k}]'); await el.fill(v); await el.dispatch_event('input'); await pg.wait_for_timeout(150)
    await typ('qty','10'); await typ('entry','4171.86'); await typ('exit','4160.9'); await typ('stop','4176'); await typ('target','4157')
    await typ('entryTime','09:10:33'); await typ('exitTime','09:34:54')
    print('risk box:', await pg.evaluate("document.querySelector('#tkRisk').innerText.replace(/\\n/g,' ')"))
    print('result line:', await pg.evaluate("document.querySelector('#tkResult').innerText.replace(/\\n/g,' ')"))
    await pg.locator('#tkSlide [data-act=tk-save]').click(); await pg.wait_for_timeout(1500)
    t=await pg.evaluate("(()=>{const t=S.trades.find(x=>x.instrument==='MGC'&&x.entry===4171.86); return t?{pnl:t.pnl_c/100,fees:(t.fees_c||0)/100,net:tNet(t)/100,id:t.id}:null})()")
    print('saved:', t, '(Lucid: gross 1,096 · fees 16 · net 1,080)')
    # with the platform's fees on the trade page, the net matches Lucid
    await pg.evaluate(f"editDoc('trades','{t['id']}',d=>{{d.fees_c=1600}})"); await pg.wait_for_timeout(500)
    print('with $16 fees, net:', await pg.evaluate(f"tNet(getDoc('trades','{t['id']}'))/100"))
    # an old trade saved with the rounded formula is corrected once on load
    await pg.evaluate(f"editDoc('trades','{t['id']}',d=>{{d.fees_c=null; d.pnl_c=110000}})"); await pg.wait_for_timeout(1200)
    await pg.reload(); await pg.wait_for_timeout(4500)
    print('old rounded P&L 1,100 → after reload:', await pg.evaluate(f"getDoc('trades','{t['id']}').pnl_c/100"))
    await pg.evaluate(f"remove('trades','{t['id']}')"); await pg.wait_for_timeout(800)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
