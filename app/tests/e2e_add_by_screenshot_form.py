import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    pg.on('dialog', lambda d: asyncio.ensure_future(d.accept('Serein')))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    await pg.evaluate("SweepAddMode.open()"); await pg.wait_for_timeout(700)
    await pg.locator('.nav-am-shot [data-am-sel=account]').tap(); await pg.wait_for_timeout(300)
    print('account list opens:', await pg.locator('.nav-am-shot [data-am-pickf=account]').count(), 'accounts | native selects left:', await pg.locator('.nav-am-shot select').count())
    await pg.locator('.nav-am-shot [data-am-pickf=account]').nth(2).tap(); await pg.wait_for_timeout(300)
    print('   picked:', await pg.evaluate("document.querySelector('.nav-am-shot [data-am-sel=account] span').textContent"), '| list closed:', await pg.locator('.nav-am-shot .nav-am-opts').count()==0)
    await pg.locator('.nav-am-more-d summary').tap(); await pg.wait_for_timeout(200)
    await pg.locator('.nav-am-shot [data-am-sel=inst]').tap(); await pg.wait_for_timeout(300)
    await pg.locator('.nav-am-shot [data-am-pickf=inst][data-v=MGC]').tap(); await pg.wait_for_timeout(300)
    print('   symbol:', await pg.evaluate("document.querySelector('.nav-am-shot [data-am-sel=inst] span').textContent"))
    print('emotions shown first:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot [data-am-emo]')].map(b=>b.textContent).join(', ')"))
    await pg.locator('.nav-am-shot [data-am=emo-more]').tap(); await pg.wait_for_timeout(300)
    print('   after « Voir plus »:', await pg.locator('.nav-am-shot [data-am-emo]').count(), 'emotions')
    await pg.locator('.nav-am-shot [data-am=emo-add]').tap(); await pg.wait_for_timeout(1200)
    print('   own emotion added and selected:', await pg.evaluate("!!document.querySelector('.nav-am-shot [data-am-emo=\"Serein\"].on')"), '| kept for next time:', await pg.evaluate("JSON.stringify(S.settings.custom_emotions||[])"))
    b=await pg.evaluate("(()=>{const b=document.querySelector('.nav-am-save'), r=b.getBoundingClientRect(), s=getComputedStyle(b); const range=document.createRange(); range.selectNodeContents(b); const t=range.getBoundingClientRect(); return 'text centred: '+(Math.abs((t.left+t.right)/2-(r.left+r.right)/2)<3)+' | radius '+s.borderRadius+' | height '+Math.round(r.height)})()")
    print('save button:', b)
    await pg.locator('.nav-am-save').scroll_into_view_if_needed(); await pg.locator('.nav-am-shot .nav-am-in').screenshot(path='/tmp/am2.png')
    await pg.evaluate("document.querySelector('.nav-am [data-am=close]').click()"); await pg.wait_for_timeout(500)
    await pg.evaluate("editDoc('settings','settings',r=>{delete r.custom_emotions})"); await pg.wait_for_timeout(800)
    # manual form: exit shortcuts right under the exit price
    await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(900)
    if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1200)
    print('manual form:', await pg.evaluate("(()=>{const y=s=>{const e=document.querySelector(s); return e?Math.round(e.getBoundingClientRect().top):null}; return 'exit price y='+y('#tkSlide [data-tk=exit]')+' · exit shortcuts y='+y('#tkSlide [data-act=tk-exitat]')+' · SL y='+y('#tkSlide [data-tk=stop]')})()"))
    await pg.locator('#tkSlide .nav-ee').screenshot(path='/tmp/man_ee.png')
    await pg.evaluate("closeTicket()")
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
