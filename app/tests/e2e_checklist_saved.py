import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/tmp/show_state.json', locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(1500)
    await pg.locator('#tkSlide .tk-dir button').first.click(); await pg.wait_for_timeout(300)
    await pg.fill('#tkSlide [data-tk=entry]','25100'); await pg.fill('#tkSlide [data-tk=exit]','25110'); await pg.wait_for_timeout(300)
    await pg.locator('.nav-ck-q').nth(1).locator('[data-v=n]').click()
    ids=await pg.evaluate("S.trades.map(t=>t.id)")
    await pg.locator('#tkSlide [data-act=tk-save]').click(); await pg.wait_for_timeout(3000)
    r=await pg.evaluate(f"(()=>{{const old=new Set({ids}); const n=S.trades.filter(t=>!old.has(t.id)); return n.length+' new | discipline: '+JSON.stringify(n.map(t=>t.discipline))}})()")
    print('saved:', r)
    await br.close()
asyncio.run(main())
