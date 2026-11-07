"""
Sweep — one figure in the spotlight per page (brief « expérience Apple », 7 Nov., step 2), with Playwright:
  python3 tests/e2e_hero_figures.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing on the server.
 - « Now »'s figure on Today: 30 px on a phone, 36 px on a computer; My money's real net: 34 px / 40 px;
 - Stats' net P&L: 40 px on a computer, unchanged on a phone (24 px: the tile is half the width);
 - 7 digits (« −1 234 567,89 $ ») in each spot: shrunk inside its box, never past it, never « … »;
 - phone 390 and computer 1300, light and dark; no horizontal scroll, no page error.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

BIG = '−1 234 567,89 $'
FS = "(s) => { const e = document.querySelector(s); return e ? parseFloat(getComputedStyle(e).fontSize) : 0 }"
INSIDE = """([s, box]) => { const e = document.querySelector(s); if (!e) return null; const b = e.closest(box).getBoundingClientRect(), r = e.getBoundingClientRect();
  return { fs: parseFloat(getComputedStyle(e).fontSize), fits: e.scrollWidth <= e.clientWidth + 1 && r.right <= b.right + 1 && r.left >= b.left - 1, cut: getComputedStyle(e).textOverflow === 'ellipsis' } }"""

with sync_playwright() as p:
  br = p.chromium.launch()
  for w, phone, scheme in ((390, True, 'light'), (1300, False, 'dark')):
    tag = f'{w}px {scheme}'
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
    now, mny = pg.evaluate(FS, '#main .nav-now-l:not(.nav-now-cnt) .nav-now-v'), pg.evaluate(FS, '#main .d-money .nav-mny-big')
    ok(now == (30 if phone else 36), f'{tag} Today: « Now »\'s figure at {now} px')
    ok(mny == (34 if phone else 40), f'{tag} My money\'s real net at {mny} px')
    for sel, box in (('#main .nav-now-l:not(.nav-now-cnt) .nav-now-v', '.nav-now'), ('#main .d-money .nav-mny-big', '.d-money')):
      pg.evaluate("([s, t]) => { document.querySelector(s).textContent = t }", [sel, BIG]); pg.wait_for_timeout(900)
      r = pg.evaluate(INSIDE, [sel, box])
      ok(r and r['fits'] and not r['cut'], f'{tag} 7 digits in {sel.split(" ")[-1]}: shrunk inside its card ({r})')
    ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} Today: no horizontal scroll')
    pg.goto(B + '/#stats'); pg.wait_for_timeout(2600)
    net = pg.evaluate(FS, '#main .ikpis>.ik:first-child b')
    ok(net == (24 if phone else 40), f'{tag} Stats: the net P&L at {net} px' + (' (a phone: the half-width tile keeps its size)' if phone else ''))
    pg.evaluate("t => { document.querySelector('#main .ikpis>.ik:first-child b span').textContent = t }", BIG); pg.wait_for_timeout(900)
    r = pg.evaluate(INSIDE, ['#main .ikpis>.ik:first-child b span', '.ik'])
    ok(r and r['fits'] and not r['cut'], f'{tag} Stats: 7 digits shrunk inside the tile ({r})')
    ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} Stats: no horizontal scroll')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    c.close()
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
