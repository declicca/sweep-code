"""
Sweep — opening a page does not keep the page busy (20 Oct., speed): phone 390 and computer 1300
  python3 tests/e2e_quiet_frames.py http://127.0.0.1:8095 /tmp/show_state.json
 1  Stats and Today, opened from the bar: while their figures count up, the page's nodes are not replaced at each frame
    (each replacement woke all the page's observers: a second of work on a phone); each count-up changes once, at its end
 2  the count-ups end on their value (whole numbers: exactly the number they count to)
 3  the key figure tiles are not cut once drawn (the amounts' fitting still runs)
 4  a shortened French figure (« −4,8 k $ ») is still fitted when its tile gets narrower (it was not taken for a figure: cut on the CI)
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
# childList changes in #main between 250 ms and 1400 ms after the page is asked for (the count-ups last 900 ms)
WATCH = """(r) => new Promise((done) => { let n = 0, on = false; const m = document.getElementById('main');
  const mo = new MutationObserver((rs) => { if (on) for (const x of rs) if (x.type === 'childList') n++; });
  mo.observe(m, { childList: true, subtree: true }); location.hash = '#' + r;
  setTimeout(() => { on = true; }, 250); setTimeout(() => { mo.disconnect(); done(n); }, 1400); })"""
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone in ((390, True), (1300, False)):
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'));")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160])); pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash'); pg.wait_for_timeout(3000)
    for r in ('analytics', 'dashboard'):
      pg.evaluate("location.hash = '#calendar'"); pg.wait_for_timeout(1200)
      n = pg.evaluate(WATCH, r); pg.wait_for_timeout(600)
      cus = pg.evaluate("[...document.querySelectorAll('#main [data-cu]')].length")
      ok(n <= 2 * cus + 12, f'1 {w} {r}: the page is not rebuilt at each frame of its count-ups ({n} changes, {cus} count-ups: its final value each, not one a frame)')
      bad = pg.evaluate("[...document.querySelectorAll('#main [data-cu][data-fmt=int]')].filter((e) => e.getClientRects().length && e.textContent.trim() !== String(Math.round(+e.dataset.cu))).map((e) => e.dataset.cu + '≠' + e.textContent)")
      ok(not bad, f'2 {w} {r}: the count-ups end on their value ({bad[:3]})')
      CUT = "[...document.querySelectorAll('#main .nav-kpi-g b, #main .d-perf b')].filter((e) => e.getClientRects().length && e.scrollWidth - (e.clientWidth || e.parentElement.clientWidth) > 1).map((e) => e.textContent)"
      for _ in range(16):   # once drawn: the count-ups and the fitting may end later on a loaded machine (the CI read them at 2 s, 21 Oct.)
        cut = pg.evaluate(CUT)
        if not cut: break
        pg.wait_for_timeout(250)
      ok(not cut, f'3 {w} {r}: no key figure cut ({cut[:3]})')
    # 4 (21 Oct., the CI): a shortened French figure (« −4,8 k $ ») is still a figure: its tile made narrower (75 % of it: within
    # what the fitting may shrink, 55 %), it is fitted again
    pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(2500)
    fig = pg.evaluate("""() => { const b = [...document.querySelectorAll('#main .nav-kpi-g b, #main .d-perf b')].find((e) => e.getClientRects().length && !e.children.length && /\\d/.test(e.textContent)); if (!b) return null;
      b.textContent = '\u22124,8\u202fk\u00a0$'; const px = Math.floor(b.scrollWidth * 0.75) + 'px'; b.parentElement.style.setProperty('width', px, 'important'); b.parentElement.style.setProperty('max-width', px, 'important'); dispatchEvent(new Event('resize')); return true }""")
    pg.wait_for_timeout(1200)
    cut4 = pg.evaluate(CUT) if fig else ['no figure']
    ok(fig and not cut4, f'4 {w}: a shortened figure « −4,8 k $ » in a narrower tile is fitted again ({cut4[:3]})')
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
