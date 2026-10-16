"""
Sweep — sheets, menus and Back never leave or reload the app (Playwright, phone):
  python3 tests/e2e_history_back.py http://127.0.0.1:8095 /tmp/show_state.json
Game sheets switched and closed fast, the menu, Escape, the trade form: still in the app, never reloaded (a mark left in
the page survives); Back closes the open sheet and stays on the page. No page error. (16 Oct.: checks, it only printed;
its « reloads » counted the hash changes.)
"""
import asyncio, datetime, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='fr-CA',storage_state=STATE)
    await ctx.add_init_script("try{sessionStorage.setItem('sw.modal','1')}catch(e){}")
    pg=await ctx.new_page(); navs=[]; pg.on('framenavigated', lambda f: f==pg.main_frame and navs.append(f.url))
    pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500); n0=len(navs); await pg.evaluate("window.__alive='x'")
    steps=[("hub then season (switch)", "SweepGame.open('hub'); setTimeout(()=>SweepGame.open('season'),700)"),
           ("close", "document.querySelector('#gSheet [data-g=close]').click()"),
           ("plan then review", "SweepGame.open('plan'); setTimeout(()=>SweepGame.open('review'),700)"),
           ("close instantly + open the menu", "document.querySelector('#gSheet [data-g=close]').click(); document.querySelector('.who').click()"),
           ("Escape", "document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))"),
           ("trades, open the add form, close", "location.hash='#trades'; setTimeout(()=>{ openTicket(); setTimeout(()=>{ const s=document.querySelector('#gSheet [data-g=plan-skip]'); s&&s.click(); setTimeout(()=>closeTicket(),500) },600) },500)")]
    for name,js in steps:
      await pg.evaluate(js); await pg.wait_for_timeout(1800)
      alive = await pg.evaluate("window.__alive === 'x'")
      ok(pg.url.startswith(B) and alive, f"{name:34} → still in the app, not reloaded (page: {pg.url.split('#')[-1]})")
    # Back button: closes the sheet, stays on the page
    await pg.evaluate("SweepGame.open('hub')"); await pg.wait_for_timeout(900)
    await pg.go_back(); await pg.wait_for_timeout(900)
    ok(await pg.evaluate("!document.querySelector('#gSheet.open') && window.__alive === 'x'") and pg.url.split('#')[-1] == 'trades', f"Back closes the sheet and stays on the page ({pg.url.split('#')[-1]})")
    ok(not errs, f'no page error ({errs[:3]})'); await br.close()
asyncio.run(main())
print(f'{fails} failed' if fails else 'all passed'); sys.exit(1 if fails else 0)
