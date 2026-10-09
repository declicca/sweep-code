import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto('http://127.0.0.1:8095/?x=1#payouts'); await pg.wait_for_timeout(2500)
    print('payouts:', await pg.evaluate("JSON.stringify(S.payouts.map(p=>[p.status,p.amount_c/100,p.request_date,p.payment_date]))"))
    b=pg.locator('#main .sh-row [data-act=share][data-k=net]')
    print('button:', (await b.inner_text()).strip())
    await b.click(); await pg.wait_for_timeout(1500)
    print('choices:', await pg.evaluate("[...document.querySelectorAll('#shPanel [data-shpo]')].map(b=>b.textContent+(b.classList.contains('on')?'*':'')).join(' | ')"))
    await pg.locator('#shPanel [data-shpo=all]').click(); await pg.wait_for_timeout(1500)
    d=lambda: pg.evaluate("(()=>{const d=shData(SH.kind,SH.id); return d? d.label+' · '+d.eyebrow+' · '+d.big+' · '+JSON.stringify(d.stats)+' · cap: '+d.cap : 'none'})()")
    print('lifetime, received:', await d())
    await pg.locator('#shPanel [data-shpo-m=requested]').click(); await pg.wait_for_timeout(1200)
    print('lifetime, requested:', await d())
    await pg.locator('#shPanel').screenshot(path='/tmp/shpo.png')
    await pg.locator('#shPanel [data-shpo=week]').click(); await pg.wait_for_timeout(1000)
    print('this week, requested:', await d())
    await pg.locator('#shPanel [data-shpo=net]').click(); await pg.wait_for_timeout(1000)
    print('back to net:', await pg.evaluate("SH.kind"), '| card ok:', await pg.evaluate("!!shData(SH.kind,SH.id)"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
