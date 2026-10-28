"""
Sweep — the long pages (brief « activation », step F: C2, C3, C4 of the 27 Oct. tour), with Playwright:
  python3 tests/e2e_long_pages.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Phone 390 (fr, es) and computer 1300 (en).
 C2 phone: the Trades list in one row per day (date, trades, P&L), the last 2 weeks, « Voir plus » shows the rest; a day opens
    on a tap; the whole list well under its old height (7,887 px for 130 trades)
 C3 the trade page: the setup chosen in one place (not again in the facts); the fees, the platform's P&L and the tags under
    « Plus de détails »; « Contexte économique » only with an announcement; phone: under 1,610 px (2,414 before; at most 1,609, a third less)
 C4 the manual form opens on its fields only: no « From a screenshot », no CSV import, no « Log with AI » in it
No page error, nothing wider than the window.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
MORE = {'fr': 'Plus de détails', 'en': 'More details', 'es': 'Más detalles'}
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone in (('fr', True), ('en', False), ('es', True)):
    w = 390 if phone else 1300; tag = f'{w}-{lang}'
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'en': 'en-US', 'fr': 'fr-CA', 'es': 'es-ES'}[lang])
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#trades'); pg.wait_for_timeout(3000)
    # C2
    if phone:
      days = pg.evaluate("[...document.querySelectorAll('#main .tday')].map((d) => [d.querySelector('summary b').textContent, d.querySelector('summary .muted').textContent, d.querySelector('.tday-v').textContent])")
      n = pg.evaluate("S.trades.filter((t) => !t.demo || true).length"); h = pg.evaluate("document.documentElement.scrollHeight")
      ok(days and all(len(x) == 3 and x[0] and x[2] for x in days), f'C2 {tag}: one row per day, date, trades and P&L ({len(days)} days)')
      ok(h < 2500, f'C2 {tag}: the list {h} px for {n} trades (7,887 before)')
      closed = pg.evaluate("(() => { const d = [...document.querySelectorAll('#main .tday')].find((x) => !x.open); return d ? [...d.querySelectorAll('.trow')].filter((r) => r.checkVisibility()).length : null })()")   # (a closed details keeps its box: checkVisibility says what shows)
      pg.evaluate("(() => { const d = [...document.querySelectorAll('#main .tday')].find((x) => !x.open); if (d) d.querySelector('summary').click(); })()"); pg.wait_for_timeout(300)
      opened = pg.evaluate("(() => { const l = [...document.querySelectorAll('#main .tday[open] .tlist .trow')]; return l.length })()")
      ok(closed == 0 and opened >= 1, f'C2 {tag}: a day opens on a tap ({closed}, {opened} rows)')
      if pg.locator('#main [data-act=more-days]').count():
        n0 = len(days); pg.locator('#main [data-act=more-days]').click(); pg.wait_for_timeout(800)
        ok(pg.locator('#main .tday').count() > n0, f'C2 {tag}: « See more » shows the older days')
    # C3
    tid = pg.evaluate("(S.trades.filter((t) => !t.untracked && t.setup && Array.isArray(t.news) && !t.news.length).slice(-1)[0] || S.trades.filter((t) => !t.untracked && t.setup).slice(-1)[0] || {}).id")
    pg.evaluate("(id) => location.hash = '#trade/' + id", tid); pg.wait_for_selector('#main .facts', timeout=10000); pg.wait_for_timeout(1500)
    setup_rows = pg.evaluate("[...document.querySelectorAll('#main .facts > div')].filter((r) => r.getClientRects().length && /^Setup$/i.test((r.firstElementChild || {}).textContent || '')).length")
    ok(setup_rows == 0 and pg.locator('#main .tr-side [data-bind$="|setup"]').count() == 1, f'C3 {tag}: the setup in one place ({setup_rows} in the facts)')
    more = pg.evaluate("(() => { const d = document.querySelector('#main .tr-more'); return d ? [d.querySelector('summary').textContent.trim(), !!d.querySelector('[data-bind$=\"|fees_c\"]'), d.open] : null })()")
    ok(more and more[0] == MORE[lang] and more[1] and not more[2], f'C3 {tag}: the fees under « {MORE[lang]} », folded ({more})')
    news = pg.evaluate("(() => { const t = getDoc('trades', location.hash.split('/')[1]), b = document.getElementById('newsCtx'); return [Array.isArray(t.news) ? t.news.length : null, b ? !!b.getClientRects().length : null] })()")
    ok(news[0] != 0 or news[1] is False, f'C3 {tag}: « Economic context » only with an announcement ({news})')
    if phone:
      h = pg.evaluate("document.documentElement.scrollHeight")
      ok(h <= 1609, f'C3 {tag}: the trade page {h} px (2,414 before; at most 1,609, a third less)')
    # C4
    pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open', timeout=8000); pg.wait_for_timeout(1000)
    extra = pg.evaluate("[...document.querySelectorAll('#tkSlide.open .nav-tk-alt, #tkSlide.open [data-act=ai-log], #tkSlide.open [data-tk-alt]')].length")
    ok(extra == 0, f'C4 {tag}: the manual form on its fields only ({extra} other ways in it)')
    pg.evaluate("closeTicket()"); pg.wait_for_timeout(400)
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
