"""
Sweep — a page's cards come in as they reach the screen (brief « expérience Apple », 7 Nov., step 1), with Playwright:
  python3 tests/e2e_reveal.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Robots normally see every card whole (html.no-reveal for
navigator.webdriver): here the browser says it is not a robot, so the effect is on.
 - a card below the screen waits, faded and lower; scrolled to, it rises in, then keeps no transform, no opacity, no class;
 - the first card of the page never moves; a card inside a card never waits; a folded card (« See more ») comes in when unfolded;
 - « Reduce motion »: no card waits; a robot (webdriver): no card waits;
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

HUMAN = "Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false, configurable: true })"
STATE_JS = """() => { const top = [...document.querySelectorAll('#main .surface')].filter((e) => !e.parentElement.closest('#main .surface') && e.getClientRects().length);
  return { n: top.length, wait: top.filter((e) => e.classList.contains('rv-wait')).length,
    first: top.length ? top[0].className : '', inner: document.querySelectorAll('#main .surface .surface.rv-wait').length,
    onScreen: top.filter((e) => e.classList.contains('rv-wait') && e.getBoundingClientRect().top < innerHeight).length } }"""

def ctx_for(br, w, phone, scheme, human=True, **kw):
  c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale='fr-CA', **kw)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  if human: c.add_init_script(HUMAN)
  return c

with sync_playwright() as p:
  br = p.chromium.launch()
  for w, phone, scheme in ((390, True, 'light'), (1300, False, 'dark')):
    tag = f'{w}px {scheme}'
    c = ctx_for(br, w, phone, scheme); pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#stats'); pg.wait_for_timeout(2600)
    st = pg.evaluate(STATE_JS)
    ok(st['n'] >= 4 and st['wait'] >= 1, f'{tag} Stats: the cards below the screen wait ({st["wait"]} of {st["n"]})')
    ok(st['onScreen'] == 0 and 'rv-wait' not in st['first'] and st['inner'] == 0, f'{tag} the cards on screen never wait, nor a card inside a card ({st})')
    look = pg.evaluate("(() => { const e = document.querySelector('#main .surface.rv-wait'); const s = getComputedStyle(e); return { o: +s.opacity, t: s.transform } })()")
    ok(look['o'] == 0 and look['t'] != 'none', f'{tag} a waiting card is faded and lower ({look})')
    pg.evaluate("document.querySelector('#main .surface.rv-wait').setAttribute('data-rv-t', '1')")
    pg.evaluate("document.querySelector('[data-rv-t]').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(120)
    mid = pg.evaluate("(() => { const e = document.querySelector('[data-rv-t]'); return { cls: e.className, o: +getComputedStyle(e).opacity } })()")
    ok('rv-in' in mid['cls'], f'{tag} scrolled to, it rises in ({mid})')
    pg.wait_for_timeout(1000)
    end = pg.evaluate("(() => { const e = document.querySelector('[data-rv-t]'); const s = getComputedStyle(e); return { cls: e.className, o: +s.opacity, t: s.transform, a: s.animationName } })()")
    ok(end['o'] == 1 and end['t'] == 'none' and 'rv-in' not in end['cls'] and 'rv-wait' not in end['cls'], f'{tag} once in: no transform, no opacity, no class left ({end})')
    pg.evaluate("scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(1300)
    left = pg.evaluate("[...document.querySelectorAll('#main .surface.rv-wait, #main .surface.rv-in')].filter((e) => e.getClientRects().length).length")
    ok(left == 0, f'{tag} at the foot of the page, every card shown is in ({left} left; a folded card comes in when unfolded)')
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
    d = pg.evaluate(STATE_JS)
    ok(d['onScreen'] == 0 and 'rv-wait' not in d['first'], f'{tag} Today: the first card does not move ({d})')
    ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    c.close()
  # « Reduce motion », and a robot
  for name, kw, human in (('reduce motion', {'reduced_motion': 'reduce'}, True), ('a robot (webdriver)', {}, False)):
    c = ctx_for(br, 390, True, 'light', human, **kw); pg = c.new_page()
    pg.goto(B + '/#stats'); pg.wait_for_timeout(2600)
    ok(pg.evaluate("document.querySelectorAll('#main .rv-wait').length") == 0, f'390px {name}: no card waits, all are whole')
    c.close()
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
