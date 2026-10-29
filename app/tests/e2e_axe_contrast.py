"""
Sweep — text contrast checked by axe-core (4.10.2, tests/vendor/axe.min.js, never deployed: deploy.sh excludes tests/), Playwright:
  python3 tests/e2e_axe_contrast.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Today, Stats and Trades, phone 390 and computer 1300, light and dark.
 1  axe « color-contrast »: no text under its ratio (4.5:1, 3:1 for large text) on the page
 2  the phone's tab bar, scrolled over the page's cards: its labels pass axe too (what axe cannot measure under the glass,
    « incomplete », is counted; the test's own computation over a blue and a gold card covers it: e2e_design_ios272 G)
"""
import os, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
AXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor', 'axe.min.js')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
RUN = """(sel) => axe.run(sel ? { include: [sel] } : document, { runOnly: { type: 'rule', values: ['color-contrast'] } }).then((r) => ({
  bad: r.violations.flatMap((v) => v.nodes.map((n) => [n.target.join(' '), (n.any[0] && n.any[0].data && n.any[0].data.contrastRatio) || null, (n.html || '').slice(0, 90)])),
  inc: r.incomplete.flatMap((v) => v.nodes).length }))"""
with sync_playwright() as p:
  br = p.chromium.launch()
  for w, phone in ((390, True), (1300, False)):
    for scheme in ('light', 'dark'):
      c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme)
      c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
      pg = c.new_page(); pg.goto(B + '/#dashboard'); pg.wait_for_timeout(3000)
      for h in ('#dashboard', '#analytics', '#trades'):
        tag = f'{w} {scheme} {h}'
        pg.evaluate("(h) => location.hash = h", h); pg.wait_for_timeout(2200)
        pg.evaluate("document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())"); pg.wait_for_timeout(300)
        if not pg.evaluate("typeof axe !== 'undefined'"): pg.add_script_tag(path=AXE)
        r = pg.evaluate(RUN, None)
        ok(not r['bad'], f'1 {tag}: no text under its contrast ratio ({len(r["bad"])}: {r["bad"][:4]}; {r["inc"]} not measurable)')
        if phone:
          pg.mouse.wheel(0, 700); pg.wait_for_timeout(600)
          r = pg.evaluate(RUN, '.bottomnav')
          ok(not r['bad'], f'2 {tag}: the tab bar over the cards ({r["bad"][:3]}; {r["inc"]} under the glass)')
          pg.mouse.wheel(0, -2000); pg.wait_for_timeout(300)
      c.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
