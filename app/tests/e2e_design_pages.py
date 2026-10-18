"""
Sweep — design « iOS 27 », lot 2: the pages (Stats, Deep Dive, My money, Today), with Playwright:
  python3 tests/e2e_design_pages.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Computer 1300 and phone 390 / 320, light and dark.
 1  Stats: « P&L breakdown » and « Patterns to watch » end at the same height; the figure tiles centre their content
 2  Deep Dive · Behavior: every table is whole in its card (none cut behind a scroll); Long vs short uses the full width
 3  My money (computer): its period and the account type in the one line of filters (16 Oct.); « Export (CSV) » in the title
    row; 2 rows of controls (« My entries / Analysis » first in the filters' line, 18 Oct.)
 4  My money (phone): the same line; « Export » in the title row
 5  Today · My money: the three amounts on one line, whatever their label
 6  a payout's amount is in Geist Mono, semibold
 7  the selector that stays at the top while scrolling is opaque (nothing shows through it)
 8  Settings: a group is a rounded header then its cards, no frame around the cards (no box in a box)
 9  Accounts (computer): the account's name starts at its column, in line with its second line (the grip in the margin)
 10 sign-in page: the main button is white on the deeper blue (44 px computer, 48 px phone); the previews are the current app;
    its fonts come from the app (no Google Fonts, 16 Oct.)
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
    m = pg.evaluate("(()=>{const t=document.querySelector('#main .fx [data-fx=type]'), p=document.querySelector('#main .fx [data-fx=mper]'), pane=document.querySelector('#main .mny-pane'); if(!t||!p||!pane) return null; const tops=new Set([...document.querySelectorAll('#main > .nav-seg, #main > .fx, #main .mny-view')].filter(e=>e.getClientRects().length).map(e=>Math.round(e.getBoundingClientRect().top))); return {row:Math.abs(t.getBoundingClientRect().top-p.getBoundingClientRect().top)<2, rows:tops.size, top:!!document.querySelector('.top .mny-exp[data-mny=csv]'), inMain:document.querySelectorAll('#main [data-mny=csv]').length}})()")
    ok(m and m['row'] and m['rows'] == 2 and m['top'] and m['inMain'] == 0, f'3 computer {scheme}: My money — period and type in the one line of filters, 2 rows of controls (« My entries / Analysis » in it since 18 Oct.), « Export (CSV) » in the title row ({m})')
    fam = pg.evaluate("(()=>{const a=document.querySelector('#main .pz-amt-v'); if(!a) return null; const s=getComputedStyle(a); return [s.fontFamily, s.fontWeight]})()")
    ok(fam and 'Geist Mono' in fam[0] and fam[1] == '600', f'6 computer {scheme}: a payout amount is Geist Mono semibold ({fam})')
    go(pg, 'dashboard', 2400); scroll_all(pg)
    mt = pg.evaluate("(()=>{const b=[...document.querySelectorAll('#main .nav-mny-g > div > b')]; return b.map(e=>Math.round(e.getBoundingClientRect().bottom))})()")
    ok(mt and len(mt) == 3 and max(mt) - min(mt) <= 3, f'5 computer {scheme}: Today · the three money amounts end on one line ({mt})')
    go(pg, 'settings')
    sg = pg.evaluate("[...document.querySelectorAll('#main details.nav-sgd')].map(d=>[getComputedStyle(d).boxShadow, getComputedStyle(d.querySelector('summary')).borderTopLeftRadius])")
    ok(sg and all(x[0] == 'none' and x[1] == '20px' for x in sg), f'8 computer {scheme}: {len(sg)} Settings groups, rounded headers, no frame ({sg[:1]})')
    go(pg, 'accounts')
    al = pg.evaluate("(()=>{const td=document.querySelector('#main table.acct-tbl tbody tr td'); if(!td) return null; const tn=[...td.childNodes].find(n=>n.nodeType===3&&n.textContent.trim()); const r=document.createRange(); r.selectNodeContents(tn); const th=document.querySelector('#main table.acct-tbl thead th'); const ln=td.querySelector('.acc-line'); return [Math.round(r.getBoundingClientRect().left), ln?Math.round(ln.getBoundingClientRect().left):null, Math.round(th.getBoundingClientRect().left+parseFloat(getComputedStyle(th).paddingLeft))]})()")
    ok(al and al[0] == al[2] and (al[1] is None or al[1] == al[0]), f'9 computer {scheme}: the account name lines up with its column ({al})')
    allerr += errs; c.close()
  for w, phone in [(1300, False), (390, True)]:
    c = br.new_context(locale='fr-CA', viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme='dark')
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160])); ext = []
    pg.on('request', lambda r: ext.append(r.url) if 'google' in r.url else None); csp = []
    pg.on('console', lambda m: csp.append(m.text[:120]) if 'Content Security Policy' in m.text or 'Content-Security-Policy' in m.text else None)
    pg.goto(B + '/'); pg.wait_for_timeout(1800)
    fo = pg.evaluate("document.fonts.check('16px Geist') && [...document.fonts].some(f=>f.family.replace(/[\"']/g,'')==='Geist' && f.status==='loaded')")
    ok(fo and not ext and not csp, f'10 sign-in {w}: Geist from the app, no request to Google, no CSP error (brief 00, 1.1) ({fo}, {ext[:1]}, {csp[:1]})')
    b = pg.evaluate("(()=>{const b=document.querySelector('#go'); if(!b) return null; const s=getComputedStyle(b); return [s.color, s.backgroundImage.includes('47, 111, 228'), Math.round(b.getBoundingClientRect().height)]})()")
    ok(b and b[0] == 'rgb(255, 255, 255)' and b[1] and b[2] == (48 if phone else 44), f'10 sign-in {w}: white on the deeper blue, {48 if phone else 44} px ({b})')
    if not phone:
      im = pg.evaluate("[...document.querySelectorAll('#shotD, #shotP')].map(i=>[i.getAttribute('src'), i.naturalWidth])")
      ok(im and all('v=20261015' in (x[0] or '') and x[1] > 0 for x in im), f'10 sign-in: the previews are the 15 Oct. ones ({im})')
    allerr += errs; c.close()
  for w, scheme, lang in [(390, 'dark', 'fr'), (390, 'light', 'en'), (320, 'light', 'es')]:
    c, pg, errs = page(br, w, True, scheme, lang)
    go(pg, 'analytics')
    jc = pg.evaluate("[...document.querySelectorAll('#main .ikpis > .ik')].map(e=>getComputedStyle(e).justifyContent)")
    ok(jc and all(j == 'center' for j in jc), f'1 phone {w} {scheme}: the KPI tiles centre their content ({len(jc)})')
    go(pg, 'payouts')
    m = pg.evaluate("(()=>{const row=document.querySelector('#main .fx .fx-row'), e=document.querySelector('.top .mny-exp'); const vis=x=>x&&x.getClientRects().length&&getComputedStyle(x).display!=='none'; return {typeInRow:!!(row&&row.querySelector('[data-fx=type]')&&row.querySelector('[data-fx=mper]')), exp:!!e&&vis(e.querySelector('.s'))&&!vis(e.querySelector('.l')), h:e?Math.round(e.getBoundingClientRect().height):0, ov:document.documentElement.scrollWidth-innerWidth}})()")
    ok(m['typeInRow'] and m['exp'] and m['h'] == 44 and m['ov'] <= 0, f'4 phone {w} {scheme} {lang}: My money — period and type in the one line, short « Export » in the title row ({m})')
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
