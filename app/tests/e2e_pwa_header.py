"""
Sweep — the app added to the Home Screen (19 Oct., Mateo's recording), phone 390, navigator.standalone and no navigator.vibrate, like on the iPhone:
  python3 tests/e2e_pwa_header.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the app marks itself (html.pwa) even without « display-mode: standalone », and its own rules apply: the header right
    under the status bar (here, without a safe area: 6 px), transparent at the top of a page (no band, no line)
 2  scrolled: a clean line under the header, no blurred shadow fading the text under it
 3  pull to refresh: the activity indicator's 8 spokes appear with the pull (half way: 4), a haptic tap once far enough
    (the switch of Safari 18, toggled once), then it spins and goes away
 4  in the browser (not installed): no mark, the header as it was
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
TOUCH = """([type, y]) => { const t = new Touch({ identifier: 1, target: document.body, clientX: 200, clientY: y }); document.body.dispatchEvent(new TouchEvent(type, { touches: type === 'touchend' ? [] : [t], changedTouches: [t], bubbles: true })) }"""
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for installed in (True, False):
    c = br.new_context(storage_state=STATE, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-CA', color_scheme='dark')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'));" + ("Object.defineProperty(navigator, 'standalone', { get: () => true }); Object.defineProperty(navigator, 'vibrate', { value: undefined });" if installed else ''))
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(3000)
    side = "(() => { const s = getComputedStyle(document.querySelector('aside.side')); return [s.paddingTop, s.backgroundColor, s.borderBottomColor, s.boxShadow] })()"
    if not installed:
      ok(not pg.evaluate("document.documentElement.classList.contains('pwa')") and pg.evaluate(side)[0] == '10px', f'4 browser: no mark, the header as it was ({pg.evaluate(side)[0]})')
      c.close(); continue
    top = pg.evaluate(side)
    ok(pg.evaluate("document.documentElement.classList.contains('pwa')"), '1 installed: html.pwa')
    ok(top[0] == '6px' and top[1] == 'rgba(0, 0, 0, 0)' and top[2] == 'rgba(0, 0, 0, 0)' and top[3] == 'none', f'1 installed, top of the page: the header right under the status bar and transparent ({top})')
    pg.evaluate("scrollTo(0, 500)"); pg.wait_for_timeout(700)
    sc = pg.evaluate(side)
    ok(sc[3] == 'none' and sc[2] != 'rgba(0, 0, 0, 0)', f'2 scrolled: a line, no blurred shadow ({sc[2]}, {sc[3]})')
    pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(500)
    pg.evaluate(TOUCH, ['touchstart', 100]); pg.evaluate(TOUCH, ['touchmove', 145]); pg.wait_for_timeout(100)
    half = pg.evaluate("[...document.querySelectorAll('.nav-ptr b')].map((b) => +getComputedStyle(b).opacity)")
    ok(len(half) == 8 and sum(1 for x in half if x >= .99) == 4 and all(x == 0 for x in half[4:]), f'3 half way: 4 of the 8 spokes ({half})')
    ok(pg.locator('#navPtrTick').count() == 0, '3 no haptic yet')
    pg.evaluate(TOUCH, ['touchmove', 200]); pg.wait_for_timeout(100)
    on = pg.evaluate("[document.querySelector('.nav-ptr').classList.contains('armed'), !!document.querySelector('#navPtrTick input[switch]'), (document.querySelector('#navPtrTick input') || {}).checked]")
    ok(on == [True, True, True], f'3 far enough: armed, the haptic switch toggled once ({on})')
    pg.evaluate(TOUCH, ['touchmove', 205]); pg.wait_for_timeout(50)
    ok(pg.evaluate("document.querySelector('#navPtrTick input').checked") is True, '3 one tap only while it stays armed')
    pg.evaluate(TOUCH, ['touchend', 205]); pg.wait_for_timeout(150)
    busy = pg.evaluate("(() => { const e = document.querySelector('.nav-ptr'); return e ? [e.classList.contains('busy'), getComputedStyle(e.querySelector('i')).animationName] : null })()")
    ok(busy == [True, 'nav-ptr-spin'], f'3 released: it spins ({busy})')
    pg.wait_for_timeout(4000)
    ok(pg.locator('.nav-ptr').count() == 0, '3 then it goes away')
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
