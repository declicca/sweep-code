"""
Sweep — design « iOS 27 », lot 2: the pages (Stats, Deep Dive, My money, Today), with Playwright:
  python3 tests/e2e_design_pages.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Computer 1300 and phone 390 / 320, light and dark.
 1  Stats: « P&L breakdown » and « Patterns to watch » end at the same height; the figure tiles centre their content
 2  Deep Dive · Behavior: every table is whole in its card (none cut behind a scroll); Long vs short uses the full width
 3  My money (computer): account type and period on one row; « Export (CSV) » in the title row; 4 rows of controls
 4  My money (phone): the type on the line of « Filters »; « Export » in the title row; the period's label kept for readers
 5  Today · My money: the three amounts on one line, whatever their label
 6  a payout's amount is in Geist Mono, semibold
 7  the selector that stays at the top while scrolling is opaque (nothing shows through it)
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

def page(br, w, phone, scheme, lang='fr'):
  c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
  pg.evaluate("U.mtype='all'; U.deep='discipline'; saveU()")
  return c, pg, errs

def go(pg, h, wait=1800):
  pg.evaluate(f"location.hash='#{h}'"); pg.wait_for_timeout(wait)

def scroll_all(pg):
  pg.evaluate("(async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=500){scrollTo(0,y);await new Promise(r=>setTimeout(r,80))} scrollTo(0,0)})()"); pg.wait_for_timeout(1400)

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for scheme in ['light', 'dark']:
    c, pg, errs = page(br, 1300, False, scheme)
    go(pg, 'analytics')
    two = pg.evaluate("(()=>{const g=document.querySelector('#main .igrid.g-two'); if(!g) return null; return [...g.children].map(e=>Math.round(e.getBoundingClientRect().height))})()")
    ok(two and len(two) == 2 and abs(two[0] - two[1]) <= 1, f'1 computer {scheme}: « P&L breakdown » and « Patterns to watch » are as high ({two})')
    jc = pg.evaluate("[...document.querySelectorAll('#main .g-ins .tiles > .it, #main .ikpis > .ik')].map(e=>getComputedStyle(e).justifyContent)")
    ok(jc and all(j == 'center' for j in jc), f'1 computer {scheme}: the {len(jc)} figure tiles centre their content')
    for i, name in [(1, 'Behavior'), (7, 'Long vs short')]:
      pg.locator('section.deep .tabs > button').nth(i).click(); pg.wait_for_timeout(1200)
      cut = pg.evaluate("[...document.querySelectorAll('section.deep table')].map(t=>t.parentElement).filter(w=>w.scrollWidth>w.clientWidth+1).map(w=>[w.scrollWidth,w.clientWidth])")
      ok(not cut, f'2 computer {scheme} {name}: every table is whole ({cut})')
    lw = pg.evaluate("(()=>{const s=document.querySelector('section.deep table.tbl'); const d=document.querySelector('section.deep'); return s&&d?[Math.round(s.closest('.surface').getBoundingClientRect().width), Math.round(d.getBoundingClientRect().width)]:null})()")
    ok(lw and abs(lw[0] - lw[1]) <= 2, f'2 computer {scheme}: Long vs short uses the full width ({lw})')
    pg.evaluate("U.deep='discipline'; saveU()")
    go(pg, 'payouts')
    m = pg.evaluate("""(()=>{const t=document.querySelector('#main .mny-top .mny-tseg'), p=document.querySelector('#main .mny-top .mny-per'), pane=document.querySelector('#main .mny-pane');
      if(!t||!p||!pane) return null; const tops=new Set([...document.querySelectorAll('#main > .nav-seg, #main > .fbars, #main .mny-top, #main .mny-view')].filter(e=>e.getClientRects().length).map(e=>Math.round(e.getBoundingClientRect().top)));
      return {row:Math.abs(t.getBoundingClientRect().top-p.getBoundingClientRect().top)<6, rows:tops.size, top:!!document.querySelector('.top .mny-exp[data-mny=csv]'), inMain:document.querySelectorAll('#main [data-mny=csv]').length}})()""")
    ok(m and m['row'] and m['rows'] == 4 and m['top'] and m['inMain'] == 0, f'3 computer {scheme}: My money — type and period on one row, 4 rows of controls, « Export (CSV) » in the title row ({m})')
    fam = pg.evaluate("(()=>{const a=document.querySelector('#main .pz-amt-v'); if(!a) return null; const s=getComputedStyle(a); return [s.fontFamily, s.fontWeight]})()")
    ok(fam and 'Geist Mono' in fam[0] and fam[1] == '600', f'6 computer {scheme}: a payout amount is Geist Mono semibold ({fam})')
    go(pg, 'dashboard', 2400); scroll_all(pg)
    mt = pg.evaluate("(()=>{const b=[...document.querySelectorAll('#main .nav-mny-g > div > b')]; return b.map(e=>Math.round(e.getBoundingClientRect().bottom))})()")
    ok(mt and len(mt) == 3 and max(mt) - min(mt) <= 3, f'5 computer {scheme}: Today · the three money amounts end on one line ({mt})')
    allerr += errs; c.close()
  for w, scheme, lang in [(390, 'dark', 'fr'), (390, 'light', 'en'), (320, 'light', 'es')]:
    c, pg, errs = page(br, w, True, scheme, lang)
    go(pg, 'analytics')
    jc = pg.evaluate("[...document.querySelectorAll('#main .ikpis > .ik')].map(e=>getComputedStyle(e).justifyContent)")
    ok(jc and all(j == 'center' for j in jc), f'1 phone {w} {scheme}: the KPI tiles centre their content ({len(jc)})')
    go(pg, 'payouts')
    m = pg.evaluate("""(()=>{const row=document.querySelector('#main .mfb > .mfb-row'), t=row&&row.querySelector('.mny-tseg'), l=document.querySelector('#main .mny-top .mny-tsl'), e=document.querySelector('.top .mny-exp');
      const vis=x=>x&&x.getClientRects().length&&getComputedStyle(x).display!=='none';
      return {typeInRow:!!t, label:!!l&&l.textContent.trim().length>0&&l.getBoundingClientRect().width<=1, exp:!!e&&vis(e.querySelector('.s'))&&!vis(e.querySelector('.l')), h:e?Math.round(e.getBoundingClientRect().height):0, ov:document.documentElement.scrollWidth-innerWidth}})()""")
    ok(m['typeInRow'] and m['label'] and m['exp'] and m['h'] == 44 and m['ov'] <= 0, f'4 phone {w} {scheme} {lang}: My money — type beside « Filters », short « Export » in the title row ({m})')
    go(pg, 'dashboard', 2400); scroll_all(pg)
    mt = pg.evaluate("[...document.querySelectorAll('#main .nav-mny-g > div > b')].map(e=>Math.round(e.getBoundingClientRect().bottom))")
    ok(mt and len(mt) == 3 and max(mt) - min(mt) <= 4, f'5 phone {w} {scheme}: Today · the three money amounts end on one line ({mt})')
    go(pg, 'payouts')
    pg.evaluate("scrollTo(0, 600)"); pg.wait_for_timeout(700)
    st = pg.evaluate("(()=>{const s=document.querySelector('#main .nav-seg'); if(!s) return null; const c=getComputedStyle(s); return [s.classList.contains('is-stuck'), c.backgroundImage.startsWith('linear-gradient'), /14px/.test(c.boxShadow)]})()")
    ok(st is None or not st[0] or (st[1] and st[2]), f'7 phone {w} {scheme}: the stuck selector is opaque, its band covers the gap ({st})')
    allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
