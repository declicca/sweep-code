import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.goto('http://127.0.0.1:8095/?x=1#trades'); await pg.wait_for_timeout(2500)
    print(await pg.evaluate("""(()=>{const top=document.querySelector('.main-wrap > .top'); const s=getComputedStyle(top); const t=document.querySelector('.main-wrap > .top #title').getBoundingClientRect(); const i=document.querySelector('.main-wrap > .top .nav-imp'); const ir=i.getBoundingClientRect(); return 'top display '+s.display+' wrap '+s.flexWrap+' w '+Math.round(top.getBoundingClientRect().width)+' | title mid '+Math.round(t.top+t.height/2)+' right '+Math.round(t.right)+' | csv mid '+Math.round(ir.top+ir.height/2)+' left '+Math.round(ir.left)+' right '+Math.round(ir.right)+' | children: '+[...top.children].filter(c=>c.offsetParent).map(c=>c.tagName+'.'+String(c.className).slice(0,20)).join(', ')})()"""))
    await pg.locator('.main-wrap > .top').screenshot(path='/tmp/csv.png')
    await br.close()
asyncio.run(main())
