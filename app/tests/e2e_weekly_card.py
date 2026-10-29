"""
Sweep — the week's recap in « Your routine » (brief 01 step 5), dev environment with Playwright:
  python3 tests/e2e_weekly_card.py http://127.0.0.1:8095 /tmp/show_state.json
The moment the recap is ready is tested on the server (tests/weekly_test.php); here the server's answer is set to « ready,
not seen » so the card can be checked whatever the day:
 - « Your week is ready » with « Open the weekly recap », the routine's only primary button, and no step highlighted (in place of the next step);
 - the button opens the week's recap; once opened (seen), the card no longer offers it;
 - FR / EN words, phone and computer, no horizontal scroll, no page error.
"""
import asyncio, json, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
WORDS = {'fr': ('Ta semaine est prête', 'Ouvrir le bilan de la semaine'), 'en': ('Your week is ready', 'Open the weekly recap')}   # (SWEEP.md step 6: one name)
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for lang, w, h, mob in (('fr', 390, 844, True), ('en', 1440, 900, False)):
      tag = f'{lang} {w}px'; W = WORDS[lang]; seen = {'v': False}
      ctx = await br.new_context(storage_state=STATE, locale=lang, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
      async def today(route):   # the server says: this week's recap is ready (seen once opened)
        r = await route.fetch(); d = await r.json()
        d['weekly'] = dict(d.get('weekly') or {}, open=True, week='2026-10-05', seen=seen['v'], done=False)
        await route.fulfill(response=r, body=json.dumps(d), headers=dict(r.headers, **{'content-type': 'application/json'}))
      async def weekly(route):
        seen['v'] = True; await route.continue_()
      await ctx.route('**/api/game/today*', today); await ctx.route('**/api/game/weekly*', weekly)
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#dashboard'); await pg.wait_for_selector('#main .nav-rt .nav-rt-wk', timeout=15000); await pg.wait_for_timeout(600)
      row = await pg.evaluate("(()=>{const r=document.querySelector('#main .nav-rt .nav-rt-wk'); return {t:r.querySelector('b').textContent, b:r.querySelector('button').textContent, prim:r.querySelector('button').classList.contains('primary')}})()")
      ok(row['t'] == W[0] and row['b'] == W[1] and row['prim'], f'{tag} « {W[0]} » + « {W[1]} » ({row})')
      # every primary button of the card (the « Getting started » rows inside it are quiet since brief 02 part 5)
      prim = await pg.evaluate("[...document.querySelectorAll('#main .nav-rt .btn.primary')].length")
      nxt = await pg.evaluate("(document.querySelector('#main .nav-rt .nav-rt-steps')||{dataset:{next:'0'}}).dataset.next")
      ok(prim == 1 and nxt == '0', f'{tag} in place of the next step: one primary button in the card ({prim}), no step highlighted (data-next={nxt})')
      vis = await pg.evaluate("(()=>{const b=document.querySelector('#main .nav-rt-wk button').getBoundingClientRect(); return b.width>0 && b.right<=innerWidth})()")
      ok(vis, f'{tag} the button fits the screen')
      try: await pg.click('#main .nav-rt-wk button', timeout=12000)
      except Exception:   # (a slow CI machine: say what was in the way, close it, try again)
        print('  note: click retried:', await pg.evaluate("(()=>{const b=document.querySelector('#main .nav-rt-wk button'); if(!b) return 'no button'; const r=b.getBoundingClientRect(); const hide=[]; for(let p=b;p;p=p.parentElement){const s=getComputedStyle(p); if(s.visibility!=='visible'||s.display==='none'||+s.opacity===0) hide.push((p.className||p.tagName)+':'+s.visibility+'/'+s.display+'/'+s.opacity)} return {rect:[r.x,r.y,r.width,r.height].map(Math.round), hide, open:[...document.querySelectorAll('.nav-dlg.open, .evp.open, #gSheet, .nav-pass')].map(x=>x.id||x.className)}})()"))
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(800)
        await pg.click('#main .nav-rt-wk button', timeout=20000)
      await pg.wait_for_selector('#gSheet', timeout=8000); await pg.wait_for_timeout(1200)
      ok(await pg.locator('#gSheet').count() == 1, f'{tag} « {W[1]} » opens the week\'s recap')
      await pg.keyboard.press('Escape'); await pg.wait_for_timeout(900)
      ok(await pg.locator('#main .nav-rt .nav-rt-wk').count() == 0, f'{tag} once opened, the card no longer offers it')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
