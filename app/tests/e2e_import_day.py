"""
Sweep — Today, « Import my session » under the Execution step (11 Nov., audit 3.1):
  python3 tests/e2e_import_day.py http://127.0.0.1:8095 /tmp/show_state.json
A trader whose trades come from a CSV file (an import key that is not the sync's) and with no trade today sees the link under
« Add a trade », on a computer (1300, FR light and EN dark); it opens the import page. Not on a phone (390, ES), not for a trader
who never imported. Also: the routine's small « ? » has 44 px under the finger on a phone; no page error.
"""
import sys, json
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
ST = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, w):
  global fails; fails += (not c); print(('ok   ' if c else 'FAIL ') + w)
with sync_playwright() as p:
  br = p.chromium.launch()
  for tag, vp, mob, lang, cs in (('1300-fr', {'width':1300,'height':850}, False, 'fr', 'light'), ('1300-en', {'width':1300,'height':850}, False, 'en', 'dark'), ('390-es', {'width':390,'height':844}, True, 'es', 'dark')):
    ctx = br.new_context(storage_state=ST, viewport=vp, is_mobile=mob, has_touch=mob, color_scheme=cs, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main section.nav-rt:not(.ph)', timeout=20000); pg.wait_for_timeout(1200)
    n0 = pg.locator('#main .nav-rt [data-rt=import]').count()
    today = pg.evaluate("S.trades.filter((t) => t.date === todayStr()).length")
    csv = pg.evaluate("S.trades.some((x) => !x.demo && x.import_key && !/^sync:/.test(x.import_key))")
    ok(n0 == (1 if (csv and not today) else 0), f'{tag} as is: link {n0} (csv trader {csv}, trades today {today})')
    # a CSV trader with no trade today
    pg.evaluate("() => { const t = S.trades.find((x) => x.date !== todayStr()); t.import_key = 'tv:1'; t.demo = false; S.trades = S.trades.filter((x) => x.date !== todayStr()); SweepNowRefresh(); }"); pg.wait_for_timeout(1500)
    b = pg.locator('#main .nav-rt [data-rt=import]')
    if pg.evaluate("S.trades.filter((t) => t.date === todayStr()).length") == 0 and b.count():
      txt = b.inner_text().strip(); vis = b.is_visible()
      ok(txt == {'fr': 'Importer ma séance', 'en': 'Import my session', 'es': 'Importar mi sesión'}[lang], f'{tag} the link reads « {txt} »')
      ok(vis == (not mob), f'{tag} visible on a computer only ({vis})')
      r = pg.evaluate("() => { const b = document.querySelector('#main .nav-rt [data-rt=import]').getBoundingClientRect(), c = document.querySelector('#main .nav-rt [data-rt=import]').closest('.nav-rt-step, .nav-rt-steps > *').getBoundingClientRect(); return { inside: b.left >= c.left - 1 && b.right <= c.right + 1 && b.bottom <= c.bottom + 1, wide: document.documentElement.scrollWidth - innerWidth } }")
      ok(mob or (r['inside'] and r['wide'] <= 0), f'{tag} inside its step, nothing wider than the window ({r})')
      if not mob:
        b.click(); pg.wait_for_timeout(900); ok(pg.evaluate('location.hash') == '#import', f'{tag} it opens the import page')
    else: ok(False, f'{tag} the link appears for a CSV trader without a trade today ({b.count()})')
    if mob:
      pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main section.nav-rt:not(.ph)', timeout=20000); pg.wait_for_timeout(800)
      z = pg.evaluate("() => { const h = document.querySelector('#main .nav-rt .nav-rt-help'); if (!h) return null; const a = getComputedStyle(h, '::after'); const r = h.getBoundingClientRect(); return [Math.round(r.width + 14), Math.round(r.height + 14), a.content] }")
      ok(z is None or (z[0] >= 42 and z[1] >= 44 and z[2] != 'none'), f'{tag} the « ? » has its zone under the finger ({z})')
    ok(not errs, f'{tag} no page error {errs[:1]}')
    ctx.close()
  br.close()
sys.exit(1 if fails else 0)
