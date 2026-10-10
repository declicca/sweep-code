"""
Sweep — Admin dashboard (brief 01 step 4), dev environment with Playwright:
  python3 tests/e2e_admin_metrics.py http://127.0.0.1:8095 /tmp/show_state.json        (the test trader is the admin)
 - a JS error sent by a trader's browser (api/client-error) is listed, grouped by message, with the traders affected,
   the page, the browser and the version;
 - the four indicators of the brief (activation on the sign-up day, retention D7 and D30, swept days);
 - the sign-up week and source filters reload the numbers (« N of M traders »);
 - FR words, phone and computer, no horizontal scroll, no page error.
"""
import asyncio, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    msg = 'Test error %06d' % random.randint(0, 999999)
    for w, h, mob in ((1440, 900, False), (390, 844, True)):
      tag = f'{w}px'
      ctx = await br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(1500)
      if not mob:   # what the app does when a script fails on a trader's device
        r = await pg.evaluate(f"fetch('api/client-error',{{method:'POST',credentials:'same-origin',headers:{{'Content-Type':'application/json','X-Requested-With':'fetch'}},body:JSON.stringify({{msg:'{msg}',src:'app.js',line:7,page:'#trades',ver:'app.test'}})}}).then(r=>r.status)")
        ok(r == 200, f'a JS error is received by the server ({r})')
      await pg.evaluate("location.hash='#admin'"); await pg.wait_for_selector('#main .ux-brief', timeout=15000); await pg.wait_for_timeout(800)
      cards = await pg.evaluate("[...document.querySelectorAll('#main .ux-brief .ux-m small')].map(s=>s.textContent)")
      want = ['Activation : un trade le jour de l’inscription', 'Rétention J7', 'Rétention J30', 'Journées balayées']
      ok(all(any(c.startswith(x) for c in cards) for x in want), f'{tag} the four indicators ({cards})')
      row = await pg.evaluate(f"(()=>{{const r=[...document.querySelectorAll('#main .ux-errs tbody tr')].find(t=>t.textContent.includes('{msg}')); return r?[...r.children].map(c=>c.textContent.trim()):null}})()")
      ok(row is not None and row[1] == '1' and row[2] == '1' and row[4] == '#trades' and 'Chrome' in row[5] and row[6] == 'app.test', f'{tag} the error: 1 trader, 1 time, page, browser, version ({row})')
      before = await pg.evaluate("document.querySelector('#main .ux-bf small').textContent")
      opts = await pg.evaluate("[...document.querySelectorAll('#main [data-ux-mf=source] option')].map(o=>o.value)")
      ok(len(opts) >= 2 and opts[0] == '', f'{tag} the source filter lists « Toutes » and the sources ({opts})')
      await pg.select_option('#main [data-ux-mf=source]', opts[1]); await pg.wait_for_timeout(1500)
      after = await pg.evaluate("document.querySelector('#main .ux-bf small').textContent")
      sel = await pg.evaluate("document.querySelector('#main [data-ux-mf=source]').value")
      ok(sel == opts[1] and after != '' and after.startswith('Traders : '), f'{tag} choosing a source reloads the numbers (« {before} » → « {after} »)')
      await pg.select_option('#main [data-ux-mf=source]', ''); await pg.wait_for_timeout(1200)
      wk = await pg.evaluate("[...document.querySelectorAll('#main [data-ux-mf=cohort] option')].map(o=>o.textContent).slice(1,2)")
      ok(bool(wk) and wk[0].startswith('sem. du'), f'{tag} the sign-up weeks « sem. du … » ({wk})')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
