import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,8,3,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    for i,t in enumerate(['20:27:00','20:48:00']):
      await pg.evaluate(f"put('trades',{{id:'jn-{i}',account_id:S.accounts[0].id,instrument:'NQ',date:'2026-10-04',entry_time:'{t}',exit_time:'{t}',direction:'long',contracts:1,entry:30100,exit:30120,pnl_c:4000}})")
    await pg.evaluate("editDoc('trades','jn-0',d=>{d.emo={before:'Frustrated'}})")
    await pg.wait_for_timeout(1500)
    await pg.evaluate("SweepGame.refresh()"); await pg.wait_for_timeout(2500); await pg.evaluate("SweepGame.openJournal()"); await pg.wait_for_timeout(1500)
    if not await pg.locator('#gSheet [data-g=j-emo]').count():
      print('journal sheet not opened via SweepGame.open; sheet html:', await pg.evaluate("(document.querySelector('#gSheet')||{}).className")); 
    print('sheet structure:', await pg.evaluate("(()=>{const s=document.getElementById('gSheet'); return [...s.querySelectorAll(':scope > *')].map(e=>e.className).join(' | ')+' || has .g-in: '+!!s.querySelector('.g-in')})()"))
    for name in ['Calme','Frustré']:
      await pg.locator('#gSheet [data-g=j-emo]', has_text=name).first.click(); await pg.wait_for_timeout(500)
    print('trade 1 doc emo:', await pg.evaluate("JSON.stringify((getDoc('trades','jn-0')||{}).emo)"), '| on screen:', await pg.evaluate("[...document.querySelectorAll('#gSheet [data-g=j-emo].on')].map(b=>b.textContent).join(',')"), '| title:', await pg.locator('#gSheet').inner_text() if False else '')
    await pg.locator('#gSheet [data-g=j-next]').click(); await pg.wait_for_timeout(800)
    for name in ['Patient','Avide']:
      await pg.locator('#gSheet [data-g=j-emo]', has_text=name).first.click(); await pg.wait_for_timeout(500)
    print('trade 2 doc emo:', await pg.evaluate("JSON.stringify((getDoc('trades','jn-1')||{}).emo)"), '| on screen:', await pg.evaluate("[...document.querySelectorAll('#gSheet [data-g=j-emo].on')].map(b=>b.textContent).join(',')"))
    print('trade 1 after:', await pg.evaluate("JSON.stringify((getDoc('trades','jn-0')||{}).emo)"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
