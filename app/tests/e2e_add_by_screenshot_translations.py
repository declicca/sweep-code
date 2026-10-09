import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for lang in ['fr','es']:
      ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='en-US',storage_state='/tmp/show_state.json')
      await ctx.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      await pg.evaluate("SweepAddMode.open()"); await pg.wait_for_timeout(1200)
      print(lang, '| questions:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot .nav-am-q > span')].slice(0,2).map(s=>s.textContent).join(' / ')"))
      print('   emotions:', await pg.evaluate("[...document.querySelectorAll('.nav-am-shot [data-am-emo]')].map(b=>b.textContent).join(', ')"))
      print('   own texts kept:', await pg.evaluate("document.querySelector('.nav-am-shot h2').textContent+' | '+document.querySelector('.nav-am-save').textContent"))
      await pg.locator('.nav-am-shot [data-am-emo=Angry]').click(); await pg.wait_for_timeout(300)
      print('   tap still works after translation:', await pg.evaluate("document.querySelector('.nav-am-shot [data-am-emo=Angry]').classList.contains('on')"))
      if lang=='fr': await pg.locator('.nav-am-shot .nav-am-in').screenshot(path='/tmp/am_tr.png')
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
