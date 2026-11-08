"""
Sweep — the trade chart in full screen (8 Nov., a « Trade page jump » report of a 402 x 714 phone), dev environment with Playwright:
  python3 tests/e2e_chart_full.py http://127.0.0.1:8095 /tmp/show_state.json
On a trade's page, the chart scrolled into view, a tap on its full-screen button:
 - the chart covers the screen, above the top bar and the tab bar (the card's « bubbles on top » z-index 30 kept it under
   them, « exit full screen » out of reach), and its button is the one under the finger;
 - the page under it does not move, and a tap on the same button brings the page back where it was (the tapped control
   followed into the full screen scrolled it 323 px);
 - no « Trade page jump » report.
Phone 402 x 714 (touch, light) and computer 1300 x 850 (dark), no page error.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
ON_TOP = "(() => { const w = document.querySelector('.sc-wrap.sc-full'); if (!w) return null; const pts = [[innerWidth / 2, 30], [innerWidth / 2, innerHeight - 30], [innerWidth - 30, innerHeight / 2]]; return pts.every(([x, y]) => w.contains(document.elementFromPoint(x, y))) })()"
with sync_playwright() as p:
  br = p.chromium.launch()
  for w, h, mob, cs in ((402, 714, True, 'light'), (1300, 850, False, 'dark')):
    tag = f'{w}-{cs}'
    ctx = br.new_context(storage_state=STATE, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, color_scheme=cs, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = ctx.new_page(); errs = []; reps = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.on('request', lambda r: reps.append(r.post_data or '') if r.url.endswith('/api/client-error') else None)
    pg.goto(B + '/#trades'); pg.wait_for_function("() => typeof S !== 'undefined' && (S.trades || []).length > 0", timeout=20000); pg.wait_for_timeout(800)
    tid = pg.evaluate("S.trades[0].id"); pg.evaluate(f"location.hash = '#trade/{tid}'"); pg.wait_for_selector('#main .sc-ic[data-sc=full]', timeout=15000); pg.wait_for_timeout(1200)
    pg.evaluate("document.querySelector('#main .sc-ic[data-sc=full]').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(600)
    y0 = pg.evaluate("scrollY")
    btn = pg.locator('#main .sc-ic[data-sc=full]')
    btn.tap() if mob else btn.click()
    pg.wait_for_timeout(900)
    top = pg.evaluate(ON_TOP); y1 = pg.evaluate("scrollY")
    ok(top is True, f'{tag} the chart in full screen covers the screen, above the top bar and the tab bar ({top})')
    ok(abs(y1 - y0) <= 1, f'{tag} the page under it does not move ({y0} → {y1})')
    pg.screenshot(path=f'/tmp/chart_full_{tag}.png')
    out = pg.locator('.sc-wrap.sc-full .sc-ic[data-sc=full]')
    try:
      out.tap(timeout=3000) if mob else out.click(timeout=3000); tapped = True
    except Exception as e: tapped = False
    pg.wait_for_timeout(900)
    y2 = pg.evaluate("scrollY"); closed = pg.evaluate("!document.querySelector('.sc-full') && !document.body.classList.contains('sc-lock')")
    ok(tapped and closed, f'{tag} the same button, under the finger, leaves the full screen (tapped {tapped}, closed {closed})')
    ok(abs(y2 - y0) <= 1, f'{tag} the page is back where it was ({y0} → {y2})')
    jumps = [r for r in reps if 'Trade page jump' in r]
    ok(not jumps, f'{tag} no « Trade page jump » report ({jumps[:1]})')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    ctx.close()
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
