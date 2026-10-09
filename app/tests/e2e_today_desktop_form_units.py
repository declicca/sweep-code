import asyncio, datetime
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
NOW=datetime.datetime(2026,10,5,17,0,0,tzinfo=datetime.timezone.utc)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900},color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.planSkip','2026-10-05'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{analytics:1}}))")
    pg=await ctx.new_page(); await pg.clock.install(time=NOW); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    await pg.evaluate("AI.on = true; document.body.classList.add('ai-on'); askShow(true); render()"); await pg.wait_for_timeout(800)
    print('Today:', await pg.evaluate("""(()=>{const t=document.querySelector('#title').getBoundingClientRect(), b=document.querySelector('.top .nav-addtop:not([hidden])'); const br=b&&b.getBoundingClientRect(); const colB=[...document.querySelectorAll('.d-col-b > *')].filter(e=>e.offsetHeight).sort((x,y)=>x.getBoundingClientRect().top-y.getBoundingClientRect().top).map(e=>[...e.classList].find(c=>c.startsWith('d-'))).join(' → '); const colA=[...document.querySelectorAll('.d-col-a > *')].filter(e=>e.offsetHeight).sort((x,y)=>x.getBoundingClientRect().top-y.getBoundingClientRect().top).map(e=>[...e.classList].find(c=>c.startsWith('d-'))).join(' → '); const last=(s)=>Math.max(...[...document.querySelectorAll(s+' > *')].filter(e=>e.offsetHeight).map(e=>e.getBoundingClientRect().bottom)); return 'add button: '+(br?'right edge '+Math.round(br.right)+', on the title block rows':'missing')+' | left: '+colA+' | right: '+colB+' | bottoms '+Math.round(last('.d-col-a'))+'/'+Math.round(last('.d-col-b'))})()"""))
    await pg.screenshot(path='/tmp/r3_today.png', full_page=True)
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(1500)
    print('Trades list add row:', await pg.evaluate("(()=>{const r=document.querySelector('#main .nav-addrow'); if(!r) return 'missing'; const n=r.nextElementSibling; return r.textContent.trim()+' | above: '+(n?n.tagName+'.'+n.className.split(' ')[0]:'')})()"))
    # form
    await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
    await pg.locator('#tkSlide [data-v=long]').first.click()
    e=pg.locator('#tkSlide [data-tk=entry]'); await e.fill('30100'); await e.dispatch_event('input'); await pg.wait_for_timeout(300)
    print('switch default:', await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-unit .on')].map(b=>b.textContent).join(',')"), '| $ fields visible:', await pg.locator('#tkSlide .nav-usd.st').is_visible())
    await pg.locator('#tkSlide .nav-unit [data-unit=usd]').click(); await pg.wait_for_timeout(300)
    print('after « Montant $ »: price boxes visible:', await pg.locator('#tkSlide [data-tk=stop]').is_visible(), '| $ boxes visible:', await pg.locator('#tkSlide .nav-usd.st').is_visible())
    for k,v in [('stop','200'),('target','400')]:
      i=pg.locator(f'#tkSlide [data-usd={k}]'); await i.fill(v); await i.dispatch_event('input'); await pg.wait_for_timeout(200)
    print('   prices:', await pg.evaluate("TK.stop+' / '+TK.target"), '| shown:', await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-usd.st .nav-usd-eq')].map(x=>x.textContent).join(' ; ')"))
    await pg.locator('#tkSlide .nav-unit').screenshot(path='/tmp/r3_unit.png')
    await pg.locator('#tkSlide .nav-unit [data-unit=px]').click(); await pg.wait_for_timeout(300)
    print('   back to « Prix »:', await pg.locator('#tkSlide [data-tk=stop]').input_value(), '/', await pg.locator('#tkSlide [data-tk=target]').input_value())
    # several executions
    await pg.locator('#tkSlide .nav-px [data-px=add]').first.click(); await pg.wait_for_timeout(900)
    print('executions placed:', await pg.evaluate("""(()=>{const avg=document.querySelector('#tkAvg').closest('.tk-f'), ex=document.querySelector('#tkSlide .tk-exs').closest('.tk-f'), stop=document.querySelector('#tkSlide [data-tk=stop]'); const r=document.querySelectorAll('#tkSlide .tk-ex'); const last=r[r.length-1].getBoundingClientRect(); return 'right after the average entry: '+(avg.nextElementSibling===ex)+' | before stop/target: '+!!(ex.compareDocumentPosition(stop)&4)+' | new line lit: '+r[r.length-1].classList.contains('nav-new')+' | in view: '+(last.top>0&&last.bottom<innerHeight)})()"""))
    await pg.locator('#tkSlide').screenshot(path='/tmp/r3_multi.png')
    await pg.evaluate("closeTicket()")
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
