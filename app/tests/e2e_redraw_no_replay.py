import asyncio, json
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); window.__anim=[]; document.addEventListener('animationstart', e=>window.__anim.push(((e.target.className||e.target.tagName)+'').split(' ')[0]+':'+e.animationName), true);")
    pg=await ctx.new_page(); await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    for route in ['#dashboard','#trades','#calendar','#journal','#analytics','#accounts','#payouts','#settings']:
      await pg.evaluate(f"location.hash='{route}'"); await pg.wait_for_timeout(1500)
      await pg.evaluate("window.__anim=[]; render()"); await pg.wait_for_timeout(700)
      a=await pg.evaluate("[...new Set(window.__anim)]")
      print(f'{route:12} re-render (same page) replays:', a or 'nothing')
    await br.close()
asyncio.run(main())
