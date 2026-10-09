"""
Sweep — Today does not jump while scrolling (computer and phone): no card changes column, no layout shift.
  python3 tests/e2e_scroll_stable.py http://127.0.0.1:8095 /tmp/show_state.json
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for name, kw in [('computer', {'viewport': {'width': 1440, 'height': 900}}), ('phone', {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True})]:
      ctx = await br.new_context(**kw, storage_state=STATE)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); window.__cls=0; try{new PerformanceObserver(l=>{for(const e of l.getEntries()) if(!e.hadRecentInput) window.__cls+=e.value}).observe({type:'layout-shift',buffered:true})}catch(e){}")
      pg = await ctx.new_page(); await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(4500)
      snap = lambda: pg.evaluate("[...document.querySelectorAll('#main .d-col, #main .nav-dash')].map(c=>[...c.children].map(x=>String(x.className).split(' ').pop()).join(','))")
      first = await snap(); await pg.evaluate("window.__cls=0"); changes = 0; last = first
      for i in range(16):
        await pg.mouse.wheel(0, 350 if i < 8 else -350); await pg.wait_for_timeout(220)
        s = await snap()
        if s != last: changes += 1; last = s
      cls = await pg.evaluate("window.__cls")
      ok(changes == 0, f'[{name}] no card changes place while scrolling ({changes})')
      ok(cls < 0.01, f'[{name}] no layout shift while scrolling ({round(cls, 4)})')
      if name == 'computer':
        # the page is redrawn now and then (sync, edits): each redraw shows the cards where they already were, never the other column for a moment
        lay = await pg.evaluate("""(async()=>{ const where=()=>[...document.querySelectorAll('#main .d-col')].map(c=>[...c.children].map(x=>String(x.className).split(' ').pop()).join(',')).join('|'); const seen=new Set(); let stop=false; const tick=()=>{ seen.add(where()); if(!stop) requestAnimationFrame(tick)}; tick();
          for(let i=0;i<5;i++){ render(); await new Promise(r=>setTimeout(r,500)); } stop=true; return [...seen] })()""")
        ok(len(lay) == 1, f'[{name}] redrawing Today 5 times: the cards stay in place ({len(lay)} layouts seen)')
        # cards that grow and shrink after the page is drawn (late data, a sticky header): a card may move once, never back and forth
        moves = await pg.evaluate("""(async()=>{ const where=()=>[...document.querySelectorAll('#main .d-col')].map(c=>[...c.children].map(x=>String(x.className).split(' ').pop()).join(',')).join('|');
          let last=where(), n=0; const acc=document.querySelector('#main .d-acc');
          for(let i=0;i<10;i++){ if(acc) acc.style.minHeight=(i%2?200:900)+'px'; window.dispatchEvent(new Event('scroll')); await new Promise(r=>setTimeout(r,250)); const w=where(); if(w!==last){n++; last=w;} }
          if(acc) acc.style.minHeight=''; return n })()""")
        ok(moves <= 1, f'[{name}] cards that change size do not make the columns swap back and forth ({moves} moves)')
      await ctx.close()
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
