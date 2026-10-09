import asyncio, datetime, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900},locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    draft={'drafts':[{'trade':{'account_id':'demo-a1','instrument':'MGC','direction':'short','contracts':10,'date':'2026-10-05','entry_time':'09:10','exit_time':'09:34','entry':4171.86,'exit':4160.9,'pnl_c':109600,'fees_c':1600},'missing':[]}],'warnings':[]}
    await pg.route('**/api/ai/import', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(draft)))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.body.classList.add('ai-on'); SweepAddMode.open()"); await pg.wait_for_timeout(700)
    await pg.locator('.nav-am-shot [data-am-file]').set_input_files('/tmp/shot.png'); await pg.wait_for_timeout(2000)
    print('read from the screenshot:', await pg.evaluate("(document.querySelector('.nav-am-st')||{}).textContent"), '|', await pg.evaluate("['inst','qty','time','entry','exit'].map(k=>k+'='+(document.querySelector('.nav-am-shot [data-am-f='+k+']')||{}).value).join(' ')"), '| dir on:', await pg.evaluate("(document.querySelector('.nav-am-shot [data-am-seg=dir].on')||{}).dataset?.v"), '| P&L hint:', await pg.evaluate("document.querySelector('.nav-am-net input').placeholder"))
    await pg.locator('.nav-am-shot [data-am=save]').click(); await pg.wait_for_timeout(1200)
    t=await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.source==='screenshot'&&x.instrument==='MGC').pop(); return t?{pnl:t.pnl_c/100,fees:t.fees_c/100,net:tNet(t)/100,exit_time:t.exit_time,id:t.id}:null})()")
    print('saved:', t, '(Lucid net 1,080)')
    if t: await pg.evaluate(f"remove('trades','{t['id']}')"); await pg.wait_for_timeout(600)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
