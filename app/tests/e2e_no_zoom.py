"""
Sweep — never a zoom (20 Oct., Mateo: a double tap by mistake zoomed), phone 390 (touch) and computer 1300, the app and the
sign-in page:
  python3 tests/e2e_no_zoom.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the viewport says it (maximum-scale=1, user-scalable=no) and the page has no pinch nor double-tap zoom (touch-action)
 2  phone: a double tap leaves the page at its own scale
 3  Safari's pinch (gesturestart / gesturechange) is stopped; two fingers moving do not zoom
 4  computer: ctrl / ⌘ + wheel (and a trackpad pinch) and ctrl / ⌘ + = − 0 are stopped; a plain wheel still scrolls
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
STOPPED = """(t) => { const e = t === 'wheel' ? new WheelEvent('wheel', { deltaY: -100, ctrlKey: true, cancelable: true, bubbles: true }) : t === 'wheel-plain' ? new WheelEvent('wheel', { deltaY: 100, cancelable: true, bubbles: true })
  : t.startsWith('key') ? new KeyboardEvent('keydown', { key: t.slice(3), ctrlKey: true, cancelable: true, bubbles: true }) : new Event(t, { cancelable: true, bubbles: true });
  document.body.dispatchEvent(e); return e.defaultPrevented }"""
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone in ((390, True), (1300, False)):
    for page, state in (('/#dashboard', STATE), ('/', None)):
      c = br.new_context(storage_state=state, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
      c.add_init_script("sessionStorage.setItem('sw.modal','1')")
      pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160])); pg.goto(B + page); pg.wait_for_timeout(2500)
      tag = f"{w} {'app' if state else 'sign-in'}"
      vp = pg.evaluate("document.querySelector('meta[name=viewport]').content")
      ta = pg.evaluate("getComputedStyle(document.documentElement).touchAction")
      ok('maximum-scale=1' in vp.replace(' ', '') and 'user-scalable=no' in vp.replace(' ', '') and ta == 'pan-x pan-y', f'1 {tag}: the viewport and touch-action say no zoom ({vp!r}, {ta})')
      ok(pg.evaluate(STOPPED, 'gesturestart') and pg.evaluate(STOPPED, 'gesturechange'), f"3 {tag}: Safari's pinch is stopped")
      if phone:
        pg.touchscreen.tap(195, 500); pg.wait_for_timeout(60); pg.touchscreen.tap(195, 500); pg.wait_for_timeout(600)
        ok(pg.evaluate("visualViewport.scale") == 1, f'2 {tag}: a double tap leaves the page at its scale ({pg.evaluate("visualViewport.scale")})')
        two = pg.evaluate("""(() => { const t = (id, x) => new Touch({ identifier: id, target: document.body, clientX: x, clientY: 400 }); const e = new TouchEvent('touchmove', { touches: [t(1, 150), t(2, 250)], cancelable: true, bubbles: true }); document.body.dispatchEvent(e); return e.defaultPrevented })()""")
        ok(two, f'3 {tag}: two fingers moving: stopped')
      else:
        ok(pg.evaluate(STOPPED, 'wheel') and all(pg.evaluate(STOPPED, 'key' + k) for k in ('=', '+', '-', '0')), f'4 {tag}: ctrl + wheel and ctrl + = + − 0 stopped')
        ok(not pg.evaluate(STOPPED, 'wheel-plain') and not pg.evaluate(STOPPED, 'keyc'), f'4 {tag}: a plain wheel and ctrl + C are left alone')
      c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
