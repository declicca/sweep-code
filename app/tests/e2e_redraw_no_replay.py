"""
Sweep — redrawing the same page replays no entrance animation (Playwright, phone, 8 pages):
  python3 tests/e2e_redraw_no_replay.py http://127.0.0.1:8095 /tmp/show_state.json
(16 Oct.: checks, it only printed.)
"""
import asyncio, json, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); window.__anim=[]; document.addEventListener('animationstart', e=>window.__anim.push(((e.target.className||e.target.tagName)+'').split(' ')[0]+':'+e.animationName), true);")
    pg=await ctx.new_page(); await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3500)
    for route in ['#dashboard','#trades','#calendar','#journal','#analytics','#accounts','#payouts','#settings']:
      await pg.evaluate(f"location.hash='{route}'"); await pg.wait_for_timeout(1500)
      await pg.evaluate("window.__anim=[]; render()"); await pg.wait_for_timeout(700)
      a=await pg.evaluate("[...new Set(window.__anim)]")
      ok(not a, f'{route:12} redrawn on the same page: nothing replayed ({a})')
    await br.close()
asyncio.run(main())
print(f'{fails} failed' if fails else 'all passed'); sys.exit(1 if fails else 0)
