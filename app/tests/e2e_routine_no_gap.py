import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); localStorage.setItem('sw.rtClosed','0'); localStorage.setItem('sw.rtShown','2099-01-01')")
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_selector('.nav-rt-steps', state='attached', timeout=15000); await pg.wait_for_timeout(1000)
    await pg.evaluate("document.querySelector('.nav-rt').classList.add('closed-rt')"); await pg.wait_for_timeout(600)
    print(await pg.evaluate("""(()=>{const c=document.querySelector('.nav-rt'); const cb=c.getBoundingClientRect(); const cs=getComputedStyle(c); const out=['card bottom '+Math.round(cb.bottom)+' pad-bottom '+cs.paddingBottom+' gap '+cs.rowGap];
      [...c.children].forEach(e=>{const r=e.getBoundingClientRect(); const s=getComputedStyle(e); out.push('  '+e.tagName+'.'+String(e.className).slice(0,30)+' top '+Math.round(r.top)+' h '+Math.round(r.height)+' disp '+s.display+' mt '+s.marginTop+' mb '+s.marginBottom+(e.hidden?' [hidden]':''))}); return out.join('\\n')})()"""))
    b=await pg.locator('.nav-rt').bounding_box(); await pg.screenshot(path='/tmp/gap.png', clip={'x':0,'y':b['y'],'width':390,'height':b['height']})
    await br.close()
asyncio.run(main())
