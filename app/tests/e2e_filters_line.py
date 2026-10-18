"""
Sweep — one line of filters on every page (16 Oct.), with Playwright:
  python3 tests/e2e_filters_line.py http://127.0.0.1:8095 /tmp/show_state.json [screenshots folder]
Uses the signed-in trader's sample data; puts every filter back as it was. Computer 1300 and phone 390 / 320, FR / EN / ES.
 1  Trades, Stats, Calendar, My money, Today: one line — Period ▾ (not on Calendar / Today), Account type ▾, Filters — nothing
    else above the content (no row of selects, no second row of filters)
 2  Period ▾: a menu under the pill (computer) / a sheet (phone); a choice applies and closes it; « Custom » keeps it open
    with two dates, the pill shows the dates
 3  Account type ▾: the choice applies everywhere (the pill shows it); Escape closes, the focus goes back to the pill
 4  Filters: the same sheet on a computer and a phone; an active filter shows as a removable pill (×), and its count
 5  My money: its own period (month… custom) in the same line; Stats: « Copies » in the Filters sheet when there are copies
 6  phone: the line scrolls on its own, nothing wider than the window, 44 px touch zones
"""
import sys, os
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
SHOTS = sys.argv[3] if len(sys.argv) > 3 else ''
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

def page(br, w, phone, lang='fr', scheme='dark'):
  c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
  pg.evaluate("Object.assign(F,{period:'all',firm:'all',account:'all',session:'all',dir:'all',inst:'all'}); saveF(); Object.assign(U,{mtype:'all',mper:'month',result:'all',setup:'all',disc:'all',tag:''}); saveU()")
  return c, pg, errs

def go(pg, h, wait=1700):
  pg.evaluate(f"location.hash='#{h}'"); pg.wait_for_timeout(wait)

def shot(pg, name):
  if SHOTS: os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, name + '.png'))

LINE = """(()=>{const fx=document.querySelector('#main .fx'); if(!fx) return null; const row=fx.querySelector('.fx-row');
  return {kinds:[...row.children].map(c=>c.dataset.fx||(c.dataset.act==='fsheet'?'filters':c.dataset.act==='fclear'?'on':'?')),
   others:document.querySelectorAll('#main .fbars, #main .mfb, #main .mseg, #main .mny-top, #main .mny-cseg, #main select[data-filter], #main select[data-ui]').length,
   oneLine:new Set([...row.children].map(c=>{const b=c.getBoundingClientRect(); return Math.round(b.top+b.height/2)})).size===1}})()"""

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for w, phone, lang, scheme in [(1300, False, 'fr', 'dark'), (390, True, 'fr', 'light'), (320, True, 'es', 'dark'), (1300, False, 'en', 'light')]:
    tag = f'{w} {lang}'
    c, pg, errs = page(br, w, phone, lang, scheme)
    want = {'trades': ['per', 'type', 'filters'], 'analytics': ['per', 'type', 'filters'], 'calendar': ['type', 'filters'], 'payouts': ['view', 'mper', 'type', 'filters']}   # (« My entries / Analysis » first in the line since 18 Oct.)
    for h, k in want.items():
      go(pg, h); r = pg.evaluate(LINE)
      ok(r and r['kinds'] == k and r['others'] == 0 and r['oneLine'], f'1 {tag} {h}: one line {k}, nothing else ({r})')
      if h == 'payouts': shot(pg, f'{w}-{lang}-payouts')
    go(pg, 'dashboard', 2200)
    t = pg.evaluate("(()=>{const h=document.querySelector('#main .nav-kpi-h'); return h?[!!h.querySelector('.nav-kseg'), !!h.querySelector('[data-fx=type]'), document.querySelectorAll('#main .nav-ktype').length]:null})()")
    ok(t == [True, True, 0], f'1 {tag} Today: Day / Week and the type pill on one header ({t})')
    # 2. Period
    go(pg, 'analytics')
    pg.locator('#main [data-fx="per"]').click(); pg.wait_for_timeout(400)
    m = pg.evaluate("(()=>{const m=document.getElementById('fxMenu'); if(!m) return null; return {sheet:m.classList.contains('fxm-sheet'), n:m.querySelectorAll('.fxm-o').length, on:(m.querySelector('.fxm-o.on')||{}).dataset.fxv, focus:document.activeElement&&document.activeElement.classList.contains('fxm-o')}})()")
    ok(m and m['sheet'] == phone and m['n'] == 5 and m['on'] == 'all' and m['focus'], f'2 {tag} Period ▾ opens its {5} choices ({"sheet" if phone else "menu"}), the current one marked, focused ({m})')
    shot(pg, f'{w}-{lang}-period-menu')
    pg.locator('#fxMenu [data-fxv="month"]').click(); pg.wait_for_timeout(700)
    r = pg.evaluate("[F.period, !!document.getElementById('fxMenu'), document.querySelector('#main [data-fx=per]').textContent.trim()]")
    ok(r[0] == 'month' and not r[1] and r[2], f'2 {tag} « month » applies and closes ({r})')
    pg.locator('#main [data-fx="per"]').click(); pg.wait_for_timeout(400)
    pg.locator('#fxMenu [data-fxv="custom"]').click(); pg.wait_for_timeout(700)
    d = pg.evaluate("[F.period, document.querySelectorAll('#fxMenu .fxm-d input[type=date]').length]")
    ok(d == ['custom', 2], f'2 {tag} « Custom » keeps the window open with two dates ({d})')
    pg.locator('#fxMenu input[data-filter="from"]').fill('2026-10-01'); pg.locator('#fxMenu input[data-filter="from"]').dispatch_event('change'); pg.wait_for_timeout(700)
    lab = pg.evaluate("[F.from, document.querySelector('#main [data-fx=per]').textContent.trim()]")
    ok(lab[0] == '2026-10-01' and '–' in lab[1], f'2 {tag} the pill shows the dates ({lab})')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    pg.evaluate("F.period='all'; saveF(); render()"); pg.wait_for_timeout(500)
    # 3. Account type
    pg.locator('#main [data-fx="type"]').click(); pg.wait_for_timeout(400)
    pg.locator('#fxMenu [data-mtype="funded"]').click(); pg.wait_for_timeout(700)
    r = pg.evaluate("[U.mtype, document.querySelector('#main [data-fx=type]').classList.contains('fx-set')]")
    ok(r == ['funded', True], f'3 {tag} type « funded » applies, the pill shows it ({r})')
    go(pg, 'trades')
    ok(pg.evaluate("U.mtype") == 'funded' and 'fx-set' in (pg.get_attribute('#main [data-fx="type"]', 'class') or ''), f'3 {tag} it follows on Trades')
    pg.locator('#main [data-fx="type"]').click(); pg.wait_for_timeout(300); pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    ok(not pg.evaluate("!!document.getElementById('fxMenu')") and pg.evaluate("document.activeElement && document.activeElement.dataset.fx") == 'type', f'3 {tag} Escape closes, the focus goes back to the pill')
    pg.evaluate("U.mtype='all'; saveU(); render()"); pg.wait_for_timeout(500)
    # 4. Filters
    pg.locator('#main [data-act="fsheet"]').click(); pg.wait_for_timeout(700)
    ok(pg.evaluate("!!document.querySelector('#fSheet.open') && document.querySelectorAll('#fSheet .fs-row').length >= 4"), f'4 {tag} Filters: the sheet opens (computer too)')
    shot(pg, f'{w}-{lang}-filters-sheet')
    sel = pg.locator('#fSheet select[data-filter="dir"]')
    if sel.count(): sel.select_option('long'); pg.wait_for_timeout(600)
    pg.locator('#fSheet [data-act="fsheet-close"]').last.click(); pg.wait_for_timeout(600)
    r = pg.evaluate("[F.dir, (document.querySelector('#main .fx-more b')||{}).textContent, [...document.querySelectorAll('#main .fx-on')].map(x=>x.dataset.k)]")
    ok(r[0] == 'long' and r[1] == '1' and r[2] == ['F:dir'], f'4 {tag} an active filter: counted on « Filters », a removable pill ({r})')
    pg.locator('#main .fx-on').first.click(); pg.wait_for_timeout(600)
    ok(pg.evaluate("F.dir") == 'all' and pg.locator('#main .fx-on').count() == 0, f'4 {tag} × removes it')
    # 5. My money
    go(pg, 'payouts')
    pg.locator('#main [data-fx="mper"]').click(); pg.wait_for_timeout(400)
    pg.locator('#fxMenu [data-mny-per="year"]').click(); pg.wait_for_timeout(700)
    ok(pg.evaluate("U.mper") == 'year', f'5 {tag} My money: its period « year » from the line')
    pg.evaluate("U.mper='month'; saveU()")
    if phone:
      r = pg.evaluate("(()=>{const row=document.querySelector('#main .fx-row'); const s=getComputedStyle(row); return [s.overflowX, s.flexWrap, document.documentElement.scrollWidth-innerWidth, [...row.children].map(c=>{const b=c.getBoundingClientRect(); const a=getComputedStyle(c,'::after'); return Math.round(Math.max(b.height, parseFloat(a.height)||0))})]})()")
      ok(r[0] == 'auto' and r[1] == 'nowrap' and r[2] <= 0 and all(h >= 44 for h in r[3]), f'6 {tag} the line scrolls on its own, no overflow, 44 px zones ({r})')
    allerr += errs; c.close()
  # Stats: « Copies » in the sheet when there are copies
  c, pg, errs = page(br, 1300, False)
  pg.evaluate("(()=>{const t=S.trades.find(x=>x.demo); if(t) editDoc('trades',t.id,d=>{d.copy_group='ftest'}); })()"); pg.wait_for_timeout(500)
  go(pg, 'analytics'); pg.locator('#main [data-act="fsheet"]').click(); pg.wait_for_timeout(700)
  ok(pg.evaluate("!!document.querySelector('#fSheet select[data-ui=\"copyMode\"]')") and pg.evaluate("document.querySelectorAll('#main .mny-cseg').length") == 0, '5 Stats: « Copies » is in the Filters sheet, no longer under the line')
  pg.evaluate("(()=>{const t=S.trades.find(x=>x.copy_group==='ftest'); if(t) editDoc('trades',t.id,d=>{delete d.copy_group}); })()"); pg.wait_for_timeout(400)
  allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
