import asyncio, datetime, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    draft={'drafts':[{'trade':{'account_id':'demo-a1','instrument':'MGC','direction':'short','contracts':10,'date':'2026-10-05','entry_time':'09:10','exit_time':'09:34','entry':4171.86,'exit':4160.9,'pnl_c':109600,'fees_c':1600},'missing':[]}],'warnings':[]}
    await pg.route('**/api/ai/import', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(draft)))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    # A) with Sweep AI: the net is filled like the platform shows it; details folded
    await pg.evaluate("document.body.classList.add('ai-on'); SweepAddMode.open()"); await pg.wait_for_timeout(700)
    print('before the screenshot — visible fields:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot .tk-f > span')].filter(s=>s.offsetParent).map(s=>s.textContent).join(' | ')"))
    await pg.locator('.nav-am-shot [data-am-file]').set_input_files('/tmp/shot.png'); await pg.wait_for_timeout(2000)
    print('A) net prefilled:', await pg.evaluate("document.querySelector('.nav-am-net input').value"), '| details folded:', await pg.evaluate("!document.querySelector('.nav-am-more-d').open"), '| summary:', await pg.evaluate("document.querySelector('.nav-am-more-d summary small').textContent"))
    r=pg.locator('.nav-am-shot [data-am-f=risk]'); await r.fill('400'); await r.dispatch_event('input'); await pg.wait_for_timeout(200)
    print('   with $400 risk:', await pg.evaluate("document.querySelector('.nav-am-r').innerText.replace(/\\n/g,' ')"))
    await pg.locator('.nav-am-shot .nav-am-in').screenshot(path='/tmp/net_form.png')
    await pg.locator('.nav-am-more-d summary').click(); await pg.wait_for_timeout(300)
    print('   « Vérifier le trade » opens the details:', await pg.evaluate("document.querySelector('.nav-am-more-d').open"), '| entry shown:', await pg.evaluate("document.querySelector('.nav-am-more-d [data-am-f=entry]').value"))
    await pg.locator('.nav-am-shot [data-am=save]').click(); await pg.wait_for_timeout(1500)
    t=await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.source==='screenshot'&&x.instrument==='MGC').pop(); return t?{net:tNet(t)/100,real:t.real_pnl_c/100,fees:t.fees_c/100,risk:t.risk_c/100,R:(tNet(t)/tRisk(t)).toFixed(2),id:t.id}:null})()")
    print('   saved:', t, '(Lucid: net 1,080)')
    if t: await pg.evaluate(f"remove('trades','{t['id']}')")
    # B) without AI: only the net P&L, nothing else
    await pg.evaluate("document.body.classList.remove('ai-on'); SweepAddMode.open()"); await pg.wait_for_timeout(700)
    n=pg.locator('.nav-am-shot [data-am-f=net]'); await n.fill('-350'); await n.dispatch_event('input')
    await pg.locator('.nav-am-shot [data-am=save]').click(); await pg.wait_for_timeout(1500)
    t=await pg.evaluate("(()=>{const t=S.trades.filter(x=>x.source==='screenshot'&&x.real_pnl_c===-35000).pop(); return t?{net:tNet(t)/100,dir:t.direction,id:t.id}:null})()")
    print('B) net only (-350):', t, '| error shown:', await pg.evaluate("(document.querySelector('.nav-am-err')||{}).textContent||''"))
    if t: await pg.evaluate(f"remove('trades','{t['id']}')"); await pg.wait_for_timeout(800)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
