import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); out=[]
    for lang in ['fr','en','es']:
      ctx=await br.new_context(**p.devices['iPhone 13'], storage_state='/tmp/show_state.json', color_scheme='dark'); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
      await pg.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
      await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_timeout(3000)
      r=await pg.evaluate("(()=>{ if(!window.SweepGuide||!SweepGuide.open) return 'no guide api'; SweepGuide.open('whatsnew'); return 'ok'})()"); await pg.wait_for_timeout(900)
      t=await pg.evaluate("(document.querySelector('.gd-help-ov h2, .gd-art h2, [class*=gd] h2')||{}).textContent||''")
      n=await pg.evaluate("[...document.querySelectorAll('.gd-help-ov p, .gd-art p, [class*=gd-a] p, [class*=gd] li')].length")
      out.append(f"{lang}: {r} | title: {t[:50]} | lines {n} | errors {errs[:1]}")
      if lang=='fr': await pg.screenshot(path='/tmp/gd_fr.png')
      await ctx.close()
    print('\n'.join(out)); await br.close()
asyncio.run(main())
