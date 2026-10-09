import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05')")
    pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,5,15,0,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    pg.on('dialog', lambda d: asyncio.ensure_future(d.accept('Ai-je attendu mon niveau ?')))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
    # manual form order
    await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1000)
    if await pg.locator('#gSheet [data-g=plan-skip]').count(): await pg.locator('#gSheet [data-g=plan-skip]').click(); await pg.wait_for_timeout(1200)
    order=await pg.evaluate("""(()=>{const y=(s)=>{const e=document.querySelector(s); return e?e.getBoundingClientRect().top:null}; const items=[['Entry | Exit','#tkSlide [data-tk=entry]'],['Exit at target / stop','#tkSlide [data-act=tk-exitat]'],['+ position / partial','#tkSlide .nav-multi'],['SL | TP','#tkSlide [data-tk=stop]'],['Risk box','#tkSlide #tkRisk'],['Exit time','#tkSlide [data-tk=exitTime]'],['Real P&L','#tkSlide [data-real]']]; return items.map(([n,s])=>[n,y(s)]).filter(x=>x[1]!=null).sort((a,b)=>a[1]-b[1]).map(x=>x[0]).join(' → ')})()""")
    print('manual form:', order)
    await pg.locator('#tkSlide [data-tk=entry]').scroll_into_view_if_needed()
    bb=await pg.evaluate("(()=>{const a=document.querySelector('#tkSlide .nav-unit').getBoundingClientRect(), b=document.querySelector('#tkSlide .nav-real').getBoundingClientRect(); return {y:a.top-6,h:Math.min(b.bottom-a.top+12, 1400)}})()")
    await pg.evaluate("document.querySelector('#tkSlide .nav-unit').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(300)
    await pg.locator('#tkSlide').screenshot(path='/tmp/ord.png')
    await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(500)
    # screenshot form: 5 questions, more, add
    await pg.evaluate("SweepAddMode.open()"); await pg.wait_for_timeout(700)
    print('active questions:', await pg.evaluate("S.settings.questions.filter(q=>q.active).length"), '| shown:', await pg.locator('.nav-am-shot .nav-am-q').count())
    await pg.locator('.nav-am-shot [data-am=q-add]').click(); await pg.wait_for_timeout(1500)
    print('   question added:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot .nav-am-q > span')].pop().textContent"), '| in the checklist settings:', await pg.evaluate("S.settings.questions.some(q=>q.text==='Ai-je attendu mon niveau ?'&&q.active)"))
    await pg.evaluate("document.querySelector('.nav-am [data-am=close]').click()"); await pg.wait_for_timeout(600)
    await pg.evaluate("SweepAddMode.open()"); await pg.wait_for_timeout(700)
    print('   reopened with 6 questions → shown:', await pg.locator('.nav-am-shot .nav-am-q').count(), '|', await pg.evaluate("(document.querySelector('.nav-am-shot [data-am=q-more]')||{}).textContent||'no more button'"))
    await pg.locator('.nav-am-shot [data-am=q-more]').click(); await pg.wait_for_timeout(300)
    print('   after « more »:', await pg.locator('.nav-am-shot .nav-am-q').count())
    await pg.evaluate("editDoc('settings','settings',r=>{r.questions=r.questions.filter(q=>q.text!=='Ai-je attendu mon niveau ?')})"); await pg.wait_for_timeout(1500)
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
