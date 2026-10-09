import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/tmp/show_state.json', color_scheme='dark', locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); localStorage.setItem('sw.planSkip','2099-01-01')")
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    print('left column order:', await pg.evaluate("[...document.querySelectorAll('.nav-dash .d-col-a > *')].map(e=>(e.className.match(/d-[a-z]+/)||[''])[0]).join(' → ')"), '| right column:', await pg.evaluate("[...document.querySelectorAll('.nav-dash .d-col-b > *')].map(e=>(e.className.match(/d-[a-z]+/)||[''])[0]).join(' → ')"))
    await pg.screenshot(path='/tmp/ln_desk.png')
    await pg.evaluate("document.body.classList.add('ai-on'); SweepAddMode.open()"); await pg.wait_for_timeout(1200)
    print('computer screenshot form: header buttons', await pg.locator('.nav-am-shot .nav-am-head .nav-am-sw:visible, .nav-am-shot .nav-am-head .nav-imp:visible').count(), '| under the drop zone:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot .nav-am-alt > *')].map(e=>e.textContent.trim()).join(' | ')"))
    await pg.locator('.nav-am-shot').screenshot(path='/tmp/ln_form.png')
    await ctx.close()
    ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/tmp/show_state.json', color_scheme='dark', locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en')); localStorage.setItem('sw.planSkip','2099-01-01')")
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    await pg.evaluate("document.body.classList.add('ai-on'); SweepAddMode.open()"); await pg.wait_for_timeout(1200)
    print('phone screenshot form: header buttons', await pg.locator('.nav-am-shot .nav-am-head .nav-am-sw:visible, .nav-am-shot .nav-am-head .nav-imp:visible').count(), '| under the drop zone:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot .nav-am-alt > *')].map(e=>e.textContent.trim()).join(' | ')"))
    await pg.screenshot(path='/tmp/ln_phone.png')
    await br.close()
asyncio.run(main())
