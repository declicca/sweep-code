"""
Sweep — design « iOS 27.2 », lot 1: the visual defects of the 28 Oct. analysis, with Playwright:
  python3 tests/e2e_design_ios272.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Computer 1300 and phone 390, light and dark, EN / FR / ES.
 V1 every card of Today has its 26 px corners (« My money » moved to the other column by the balance too), no flat line on top
 V2 the percent follows the language: « 75% » in English, « 75 % » in French and Spanish
 V3 the routine's three figures read the same: the label on top, the value under it, no coloured fill
 V4 the trade page: Geist Mono for the numbers only, never for a value in words (setup, session, date)
 V5 the trade page, computer: no empty column (« Setup & costs » above the full review)
 V6 Stats: the performance score in flat bars (no 3D)
 V8 Stats' calendar: a loss day as light as a win day (the brand gold, the same opacity scale)
No page error, nothing wider than the window.
"""
import re, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
PCT_SPACED = "(() => { const w = document.createTreeWalker(document.getElementById('main'), NodeFilter.SHOW_TEXT); const out = []; let n; while ((n = w.nextNode())) { if (/\\d[ \\u00a0\\u202f]%/.test(n.nodeValue)) out.push(n.nodeValue.trim().slice(0, 30)); } return out })()"
PCT_TIGHT = "(() => { const w = document.createTreeWalker(document.getElementById('main'), NodeFilter.SHOW_TEXT); const out = []; let n; while ((n = w.nextNode())) { if (/\\d%/.test(n.nodeValue) && !(n.parentElement && n.parentElement.closest('[style*=width], svg, .chartbox'))) out.push(n.nodeValue.trim().slice(0, 30)); } return out })()"
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, w, phone, scheme in (('en', 1300, False, 'light'), ('fr', 390, True, 'dark'), ('es', 1300, False, 'dark'), ('en', 390, True, 'light')):
    tag = f'{w}-{lang}-{scheme}'
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale={'en': 'en-US', 'fr': 'fr-CA', 'es': 'es-ES'}[lang])
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=15000); pg.wait_for_timeout(2500)
    # V1
    cards = pg.evaluate("[...document.querySelectorAll('#main .nav-dash .d-col > .surface')].filter((e) => e.getClientRects().length).map((e) => { const s = getComputedStyle(e), merged = e.classList.contains('d-pay') && e.parentElement.querySelector(':scope > .d-perf'); return [e.className.split(' ').filter((k) => /^d-/.test(k)).join('.'), s.borderTopLeftRadius, s.borderTopRightRadius, !!merged] })")
    bad = [x for x in cards if not x[3] and (x[1] != '26px' or x[2] != '26px')]
    ok(cards and not bad, f'V1 {tag}: every card of Today has its 26 px corners ({bad or len(cards)})')
    # V2
    if lang == 'en': sp = pg.evaluate(PCT_SPACED); ok(not sp, f'V2 {tag}: « 75% » in English ({sp[:3]})')
    else: tt = pg.evaluate(PCT_TIGHT); ok(not tt, f'V2 {tag}: « 75 % » in {lang} ({tt[:3]})')
    # V3
    fig = pg.evaluate("[...document.querySelectorAll('#main .nav-rt-me .nav-rt-disc, #main .nav-rt-me .nav-rt-streak, #main .nav-rt-me .nav-rt-lv')].filter((b) => b.getClientRects().length).map((b) => { const s = b.querySelector('small'), v = b.querySelector('b'); return [!!s && !!v && s.getBoundingClientRect().bottom <= v.getBoundingClientRect().top + 2, getComputedStyle(b).backgroundColor] })")
    ok(fig and all(f[0] for f in fig) and len(set(f[1] for f in fig)) == 1, f'V3 {tag}: the routine\'s figures, label on top, one same fill ({fig})')
    # V4, V5
    tid = pg.evaluate("(S.trades.filter((t) => !t.demo || true).filter((t) => !t.untracked && t.setup).slice(-1)[0] || {}).id")
    pg.evaluate("(id) => location.hash = '#trade/' + id", tid); pg.wait_for_selector('#main .facts', timeout=10000); pg.wait_for_timeout(1500)
    mono = pg.evaluate("[...document.querySelectorAll('#main .facts > div > span:last-child')].filter((v) => /[A-Za-zÀ-ÿ]{3,}/.test(v.textContent) && /Mono/.test(getComputedStyle(v).fontFamily)).map((v) => v.textContent.trim())")
    ok(not mono, f'V4 {tag}: no value in words in Geist Mono on the trade page ({mono[:3]})')
    if not phone:
      gap = pg.evaluate("(() => { const m = document.querySelector('#main .tr-main'), s = document.querySelector('#main .tr-side'); if (!m || !s) return null; const a = m.getBoundingClientRect(), b = s.getBoundingClientRect(); return [Math.round(a.left), Math.round(b.left), Math.round(a.width), Math.round(b.width)] })()")
      ok(gap and gap[0] == gap[1], f'V5 {tag}: « Setup & costs » above the full review, no empty column ({gap})')
    # V6, V8
    pg.evaluate("location.hash = '#analytics'"); pg.wait_for_timeout(2200)
    ok(pg.locator('#main svg.iso').count() == 0, f'V6 {tag}: no 3D chart on Stats')
    if not phone:
      ok(pg.locator('#main .psc .dr').count() == 6, f'V6 {tag}: the performance score in 6 flat bars')
    heat = pg.evaluate("[...document.querySelectorAll('#main .cal .d[style*=background]')].map((d) => d.getAttribute('style'))")
    gold = [h for h in heat if 'neg-rgb' in h]
    ok(heat and not gold, f'V8 {tag}: a loss day in the light brand gold, never the dark gold ({gold[:2]})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
