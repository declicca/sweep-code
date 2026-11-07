"""
Sweep — on a computer, a row that runs past its width gets ‹ › over its ends (brief « expérience Apple », 7 Nov., step 3),
with Playwright:
  python3 tests/e2e_rail_paddles.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Stats' detailed analysis (9 tabs) runs past its width at 1300.
 - 1300 (EN: 980, its tabs are shorter): › only at first, the row's right edge fading; › moves the row; then ‹ too; at the end, › goes; ‹ brings it back;
   the buttons sit over the row's ends and nothing below moves; their names in FR (« Précédent », « Suivant »), EN, ES;
 - a row that fits (Today) has none; a phone (390, touch) has none: a finger slides the row;
 - light and dark; no horizontal scroll, no page error.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

ST = """(() => { const r = document.querySelector('#main .tabs.sw-rail'); if (!r) return null; const [l, n] = r.__pads; const rr = r.getBoundingClientRect(), lb = l.getBoundingClientRect(), nb = n.getBoundingClientRect();
  return { x: Math.round(r.scrollLeft), max: r.scrollWidth - r.clientWidth, l: !l.hidden, r: !n.hidden, fadeR: r.classList.contains('sw-more-r'), fadeL: r.classList.contains('sw-more-l'),
    over: (l.hidden || (lb.left >= rr.left - 1 && lb.top >= rr.top - 16)) && (n.hidden || (nb.right <= rr.right + 1 && Math.abs((nb.top + nb.height / 2) - (rr.top + rr.height / 2)) < 2)),
    names: [l.getAttribute('aria-label'), n.getAttribute('aria-label')] } })()"""

with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, scheme, names, w in (('fr', 'light', ['Précédent', 'Suivant'], 1300), ('en', 'dark', ['Previous', 'Next'], 980), ('es', 'light', ['Anterior', 'Siguiente'], 1300)):
    tag = f'{w}px {lang} {scheme}'
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, color_scheme=scheme, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#stats'); pg.wait_for_timeout(2600)
    pg.evaluate("document.querySelector('#main .tabs').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(500)
    s0 = pg.evaluate(ST)
    ok(s0 and s0['max'] > 0 and not s0['l'] and s0['r'] and s0['fadeR'] and not s0['fadeL'] and s0['over'], f'{tag} the analysis tabs: › only, over the row\'s end, the edge fading ({s0})')
    ok(s0 and s0['names'] == names, f'{tag} the buttons\' names: {s0 and s0["names"]}')
    if lang != 'fr': c.close(); continue
    below = pg.evaluate("(() => { const r = document.querySelector('#main .tabs'); const n = r.nextElementSibling; return n ? Math.round(n.getBoundingClientRect().top) : null })()")
    pg.click('.sw-pad-r:not([hidden])'); pg.wait_for_timeout(900)
    s1 = pg.evaluate(ST)
    ok(s1['x'] > 0 and s1['l'] and s1['fadeL'], f'{tag} › moves the row, ‹ appears ({s1})')
    for _ in range(4):
      if not pg.evaluate(ST)['r']: break
      pg.click('.sw-pad-r:not([hidden])'); pg.wait_for_timeout(900)
    s2 = pg.evaluate(ST)
    ok(s2['x'] >= s2['max'] - 2 and not s2['r'] and not s2['fadeR'], f'{tag} at the end, › goes ({s2})')
    pg.click('.sw-pad-l:not([hidden])'); pg.wait_for_timeout(900)
    ok(pg.evaluate(ST)['x'] < s2['x'], f'{tag} ‹ brings it back')
    ok(below == pg.evaluate("(() => { const n = document.querySelector('#main .tabs').nextElementSibling; return n ? Math.round(n.getBoundingClientRect().top) : null })()"), f'{tag} nothing below the row moved')
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2400)
    ok(pg.locator('.sw-pad').count() == 0, f'{tag} Today: every row fits, no button')
    ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    c.close()
  c = br.new_context(storage_state=STATE, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-CA')
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  pg = c.new_page(); pg.goto(B + '/#stats'); pg.wait_for_timeout(2600); pg.evaluate("scrollTo(0, 99999)"); pg.wait_for_timeout(600)
  ok(pg.locator('.sw-pad').count() == 0, '390px (touch) Stats: no button, a finger slides the rows')
  c.close()
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
