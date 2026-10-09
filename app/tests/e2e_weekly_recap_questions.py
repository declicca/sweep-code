import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,2,22,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("SweepGame.open('weekly')"); await pg.wait_for_timeout(1800)
    print('step 1 (recap):', (await pg.locator('#gSheet .wk-step').inner_text()).replace('\n',' | ')[:420])
    await pg.locator('#gSheet .wk-step').screenshot(path='/tmp/wk0.png')
    await pg.locator('#gSheet [data-g=wk-next]').click(); await pg.wait_for_timeout(700)
    print('step 2 (questions):', await pg.evaluate("[...document.querySelectorAll('#gSheet .wk-step .g-f > span, #gSheet .wk-hint')].map(e=>e.textContent).join(' | ')"))
    for k,v in [('best','Attendre la clôture 5 min'),('fix','Entrer avant la confirmation'),('rule','Stop après 2 pertes'),('intention','Patience')]:
      a=pg.locator(f'#gSheet [data-wq={k}]')
      if await a.count(): await a.fill(v)
    await pg.locator('#gSheet [data-g=wk-grade][data-v="4"]').click()
    await pg.locator('#gSheet .wk-step').screenshot(path='/tmp/wk1.png')
    await pg.locator('#gSheet [data-g=wk-save]').click(); await pg.wait_for_timeout(1500)
    print('after saving → step:', await pg.evaluate("document.querySelector('#gSheet .wk-step h3') ? document.querySelector('#gSheet .wk-step h3').textContent : document.querySelector('#gSheet .wk-step').innerText.slice(0,60)"))
    await pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); await pg.wait_for_timeout(600)
    await pg.evaluate("SweepGame.open('weekly')"); await pg.wait_for_timeout(1500)
    if await pg.locator('#gSheet [data-g=wk-next]').count(): await pg.locator('#gSheet [data-g=wk-next]').first.click(); await pg.wait_for_timeout(500)
    print('reopened, answers kept:', await pg.evaluate("[...document.querySelectorAll('#gSheet [data-wq]')].map(x=>x.value).filter(Boolean).join(' / ')"), '| grade:', await pg.evaluate("(document.querySelector('#gSheet .wk-grade .on')||{}).textContent"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
