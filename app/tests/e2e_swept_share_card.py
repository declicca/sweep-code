import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for lang in ['fr','en']:
      ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/home/claude/media/alex_state.json', color_scheme='dark', locale='fr-CA' if lang=='fr' else 'en-US'); pg=await ctx.new_page()
      await pg.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3500)
      # the « Day swept » moment, as the app shows it
      await pg.evaluate("""(()=>{const ov=document.createElement('div'); ov.className='g-sweep in done'; ov.innerHTML='<div class="g-sw-c"><div class="g-sw-acts"><button type="button" class="btn" data-g="share" data-k="sweep">Share</button><button type="button" class="btn primary" data-g="sw-close">Continue</button></div></div>'; ov.querySelector('[data-g=sw-close]').onclick=()=>ov.remove(); document.body.append(ov)})()""")
      await pg.locator('.g-sweep [data-g=share]').tap(); await pg.wait_for_timeout(3000)
      print(lang, '| share opens:', await pg.evaluate("SH.kind"), '|', await pg.evaluate("(()=>{const d=shData('swept','today'); return d.eyebrow+' · '+d.big+' · '+d.sub+' · '+JSON.stringify(d.stats)+' · who '+d.who})()"))
      print('   caption:', await pg.evaluate("shData('swept','today').cap"))
      await pg.evaluate("document.querySelectorAll('.nav-pass, .nav-dlg-scrim, .nav-dlg').forEach(e=>e.remove())"); await pg.wait_for_timeout(300); await pg.locator('#shPanel .sh-prev').screenshot(path=f'/tmp/swshare_{lang}.png')
      await ctx.close()
    await br.close()
asyncio.run(main())
