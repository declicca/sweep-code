"""
Sweep — « My money » in two views (Mateo, 9 Oct): « My entries » (add a payout or an expense, the lists) and « Analysis »
(net real money, by month, indicators, by firm). Dev environment with Playwright:
  python3 tests/e2e_money_views.py http://127.0.0.1:8095 /tmp/show_state.json
 - the page opens on « My entries »; the two add buttons are in sight without scrolling, on a phone (390 px) and a computer;
 - « Add a payout » is the screen's only primary (blue) button; each button opens its form;
 - « Analysis » holds the net real money, by month, the indicators and by firm, and no add button;
 - the choice is remembered (back on the page: the same view); EN / FR / ES words; no horizontal scroll, no page error.
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
WORDS = {'fr': ('Mes entrées', 'Analyse', 'Ajouter un payout', 'Ajouter une dépense'), 'en': ('My entries', 'Analysis', 'Add a payout', 'Add an expense'),
         'es': ('Mis entradas', 'Análisis', 'Añadir un payout', 'Añadir un gasto')}
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for lang, w, h, mob in (('fr', 390, 844, True), ('es', 1440, 900, False), ('en', 1300, 850, False)):
      tag = f'{lang} {w}px'
      ctx = await br.new_context(storage_state=STATE, locale=lang, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(1500)
      await pg.evaluate("U.mview = 'entries'; U.addP = U.addE = false; saveU()")
      await pg.evaluate("location.hash = '#payouts'"); await pg.wait_for_selector('#main .mny-actions', timeout=10000); await pg.wait_for_timeout(700)
      W = WORDS[lang]
      tabs = await pg.evaluate("[...document.querySelectorAll('#main .mny-view [data-mny-view]')].map(b => [b.dataset.mnyView, b.textContent.trim(), b.classList.contains('on')])")
      ok(tabs == [['entries', W[0], True], ['analysis', W[1], False]], f'{tag} « {W[0]} » / « {W[1]} », opens on « {W[0]} » ({tabs})')
      btn = await pg.evaluate("""[...document.querySelectorAll('#main .mny-actions .btn')].map(b => { const r = b.getBoundingClientRect();
        return { label: b.getAttribute('aria-label'), primary: b.classList.contains('primary'), bottom: r.bottom, visible: r.width > 0 && r.bottom <= innerHeight, fits: b.scrollWidth <= b.clientWidth + 1 }; })""")
      ok([b['label'] for b in btn] == [W[2], W[3]], f'{tag} the two buttons: « {W[2]} », « {W[3]} »')
      ok(all(b['visible'] for b in btn), f'{tag} both in sight without scrolling (bottom at {[round(b["bottom"]) for b in btn]} px, screen {h} px)')
      ok(all(b['fits'] for b in btn), f'{tag} their words fit in the buttons')
      prim = await pg.evaluate("document.querySelectorAll('#main .btn.primary').length")
      ok(btn[0]['primary'] and not btn[1]['primary'] and prim == 1, f'{tag} « {W[2]} » is the only primary button ({prim})')
      for k, form in (('addP', 'payout'), ('addE', 'expense')):
        await pg.click(f'#main [data-mny={k}]'); await pg.wait_for_timeout(600)
        ok(await pg.locator(f'#main form[data-form={form}]').count() == 1, f'{tag} « {k} » opens the {form} form')
        await pg.evaluate("U.addP = U.addE = false; render()"); await pg.wait_for_timeout(400)
      ok(await pg.locator('#main .mny-net').count() == 0, f'{tag} « {W[0]} »: no analysis block')
      await pg.click('#main [data-mny-view=analysis]'); await pg.wait_for_timeout(800)
      blocks = await pg.evaluate("[!!document.querySelector('#main .mny-net'), document.querySelectorAll('#main .mny-pane .mny-h').length, document.querySelectorAll('#main .mny-actions').length]")
      ok(blocks[0] and blocks[1] >= 4 and blocks[2] == 0, f'{tag} « {W[1]} »: net real + by month + indicators + by firm, no add button ({blocks})')
      await pg.evaluate("location.hash = '#dashboard'"); await pg.wait_for_timeout(800); await pg.evaluate("location.hash = '#payouts'"); await pg.wait_for_timeout(1000)
      ok(await pg.evaluate("(document.querySelector('#main [data-mny-view=analysis]')||{classList:{contains(){return false}}}).classList.contains('on')"), f'{tag} back on the page: still « {W[1]} » (remembered)')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await pg.evaluate("U.mview = 'entries'; saveU()"); await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
