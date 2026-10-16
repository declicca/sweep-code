"""
Sweep — design « iOS 27 », lot 1: the shared components look and behave the same everywhere, with Playwright:
  python3 tests/e2e_design_shared.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's sample data; changes nothing. Computer 1300 and phone 390 / 320, light and dark.
 1  one chooser: the selectors, the phone period bar and the view tabs (Journal, Deep Dive) are pill tracks of the same
    height (40 px on a computer, 44 px on a phone), the choice a raised pill (never the inverted black / white tab)
 2  phone filters (Trades, Calendar, Stats): « Filters » and the account type on one line (16 Oct.: one line of filters,
    tests/e2e_filters_line.py)
 3  a row of 4 figures or more (Journal day, Calendar month, Account) lines up in columns
 4  list separators start at the text (inset), not at the card's edge
 5  round icon buttons: the account « ⋯ » and the Calendar's month arrows are as wide as high
 6  phone: the controls fixed by the lot have a 44 px touch zone (text links, folds, pickers, short choices, trade header)
 7  white on blue / red: the chosen journal day and the swipe « Delete » reach 4.5:1
 8  the header's actions (« Add a trade », « Import a CSV », « Share my stats ») are pills of one height (40 / 44 px)
 9  one badge: Real / Simulated / Performance, Requested / Paid, « Drawdown exceeded », « est. » are 22 px pills
 10 a button's height includes its padding (Settings on a phone: 44 px, not 56)
 11 the filter sheet's values are plain text (no box inside the row)
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

def page(br, w, phone, scheme):
  c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
  pg.evaluate("U.mtype='all'; saveU()")
  return c, pg, errs

def go(pg, h, wait=1800):
  pg.evaluate(f"location.hash='#{h}'"); pg.wait_for_timeout(wait)

TRACKS = """(()=>[...document.querySelectorAll('#main .seg, #main .mseg, #main .tabs')].filter(e=>e.getClientRects().length && !e.closest('details:not([open])'))
  .map(e=>{const s=getComputedStyle(e), r=e.getBoundingClientRect(), on=e.querySelector('.on, [aria-selected=true]'), o=on&&getComputedStyle(on);
   return {c:e.className.split(' ').slice(0,2).join('.'), h:Math.round(r.height), pill:parseFloat(s.borderTopLeftRadius)>=r.height/2-1, inv:!!o&&o.backgroundColor===getComputedStyle(document.body).color}}))()"""
TOUCH = """(()=>{const sel='#main button.link, #main a.link, #main details.more > summary, #main .csel, #main .tr-nav > a, #main .tr-top > .btn.sm, #main .tr-top details.menu > summary, #main .acc-menu > summary, #main a.btn.sm[href^="#calendar/"], #main .seg > button, #main .tabs > a, #main .mseg > button';
  const z=e=>{const r=e.getBoundingClientRect(); let h=r.height, w=r.width; const a=getComputedStyle(e,'::after'); if(a.content!=='none'&&a.position==='absolute'){h=Math.max(h,parseFloat(a.height)||0); w=Math.max(w,parseFloat(a.width)||0)} return [w,h]};
  return [...document.querySelectorAll(sel)].filter(e=>e.getClientRects().length && getComputedStyle(e).display!=='inline' && !e.closest('details:not([open]) > :not(summary)'))
   .map(e=>[e.className||e.tagName, (e.innerText||'').trim().slice(0,18), ...z(e).map(Math.round)]).filter(([c,t,w,h])=>h<43.5 || (w<43.5 && t.length<=3))})()"""

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  # 1 · 3 · 5 — computer
  for scheme in ['light', 'dark']:
    c, pg, errs = page(br, 1300, False, scheme)
    tr = []
    for h in ['trades', 'journal', 'analytics', 'payouts']:
      go(pg, h); tr += [dict(t, page=h) for t in pg.evaluate(TRACKS)]
    bad = [t for t in tr if not t['pill'] or t['inv'] or t['h'] not in (40, 41)]
    ok(tr and not bad, f'1 computer {scheme}: {len(tr)} choosers, pill tracks 40 px, no inverted tab ({bad[:3]})')
    go(pg, 'calendar')
    cols = pg.evaluate("(()=>{const s=document.querySelector('#main .statline'); if(!s) return null; return [getComputedStyle(s).display, [...s.children].map(d=>Math.round(d.getBoundingClientRect().left))]})()")
    ok(cols and cols[0] == 'grid', f'3 computer {scheme}: the Calendar month figures are a grid ({cols})')
    arrows = pg.evaluate("[...document.querySelectorAll('#main a.btn.sm[href^=\"#calendar/\"]')].map(a=>{const r=a.getBoundingClientRect(); return [Math.round(r.width),Math.round(r.height)]})")
    ok(arrows and all(w == h == 40 for w, h in arrows), f'5 computer {scheme}: the month arrows are 40 px circles ({arrows})')
    hd = []
    for h in ['dashboard', 'trades', 'analytics']:
      go(pg, h); hd += pg.evaluate("[...document.querySelectorAll('.top .nav-addtop, .top .nav-imp-b, .top .sh-btn')].filter(e=>e.getClientRects().length).map(e=>{const r=e.getBoundingClientRect(); return [e.className.split(' ')[0], Math.round(r.height), getComputedStyle(e).borderTopLeftRadius]})")
    ok(len(hd) >= 3 and all(x[1] == 40 and x[2] == '999px' for x in hd), f'8 computer {scheme}: the header actions are 40 px pills ({hd})')
    bd = []
    for h in ['accounts', 'payouts', 'analytics']:
      go(pg, h); bd += pg.evaluate("[...document.querySelectorAll('#main .mny-tag, #main .pz-pill, #main .acc-flag, #main .est')].filter(e=>e.getClientRects().length).map(e=>{const r=e.getBoundingClientRect(); return [e.className.split(' ')[0], Math.round(r.height), getComputedStyle(e).borderTopLeftRadius, getComputedStyle(e).fontSize]})")
    kinds = sorted(set(x[0] for x in bd))
    ok(len(kinds) >= 2 and all(x[1] == 22 and x[2] == '999px' and x[3] == '11px' for x in bd), f'9 computer {scheme}: {len(bd)} badges ({kinds}), all 22 px pills of 11 px ({[x for x in bd if x[1] != 22][:3]})')
    allerr += errs; c.close()
  # phone 390 and 320
  for w, scheme in [(390, 'dark'), (390, 'light'), (320, 'light')]:
    c, pg, errs = page(br, w, True, scheme)
    tr = []
    for h in ['trades', 'journal', 'analytics']:
      go(pg, h); tr += [dict(t, page=h) for t in pg.evaluate(TRACKS)]
    bad = [t for t in tr if not t['pill'] or t['inv'] or t['h'] not in (44, 45)]
    ok(tr and not bad, f'1 phone {w} {scheme}: {len(tr)} choosers, pill tracks 44 px, no inverted tab ({bad[:3]})')
    for h in ['trades', 'calendar', 'analytics']:
      go(pg, h)
      r = pg.evaluate("(()=>{const row=document.querySelector('#main .fx .fx-row'), f=row&&row.querySelector('[data-act=fsheet]'), t=row&&row.querySelector('[data-fx=type]'); if(!f||!t) return null; const a=f.getBoundingClientRect(), b=t.getBoundingClientRect(); return {line:Math.abs(a.top-b.top)<2, named:!!t.getAttribute('aria-label'), rows:document.querySelectorAll('#main [data-fx=type]').length}})()")
      ok(r and r['line'] and r['named'] and r['rows'] == 1, f'2 phone {w} {scheme} {h}: « Filters » and the account type on one line (16 Oct.: the one line of filters) ({r})')
    for h in ['calendar', 'account/{A}', 'journal']:
      if '{A}' in h: h = h.replace('{A}', pg.evaluate("S.accounts.find(a=>a.status!=='archived').id"))
      go(pg, h)
      g = pg.evaluate("(()=>{const s=document.querySelector('#main .statline'); if(!s||s.children.length<4) return null; const L=[...s.children].map(d=>Math.round(d.getBoundingClientRect().left)); return [L[0]===L[2], L[1]===L[3], L]})()")
      ok(g and g[0] and g[1], f'3 phone {w} {scheme} {h.split("/")[0]}: the figures line up in two columns ({g})')
    go(pg, 'trades')
    sep = pg.evaluate("(()=>{const r=[...document.querySelectorAll('#main .tlist > .trow')][1]; if(!r) return null; const s=getComputedStyle(r); return [s.borderTopWidth, s.backgroundImage.startsWith('linear-gradient'), s.backgroundPositionX]})()")
    ok(sep and sep[0] == '0px' and sep[1] and sep[2] == '58px', f'4 phone {w} {scheme}: the trade list separators are inset ({sep})')
    small = pg.evaluate(TOUCH)
    acc = pg.evaluate("S.accounts.find(a=>a.status!=='archived').id")
    for h in [f'account/{acc}', 'calendar', 'news', 'settings', 'payouts', 'journal']:
      go(pg, h); small += [[h] + s for s in pg.evaluate(TOUCH)]
    go(pg, 'trade/' + pg.evaluate("S.trades[0].id"), 2400); small += [['trade'] + s for s in pg.evaluate(TOUCH)]
    ok(not small, f'6 phone {w} {scheme}: every fixed control has a 44 px touch zone ({small[:4]})')
    go(pg, f'account/{acc}')
    m = pg.evaluate("(()=>{const s=document.querySelector('#main .acc-menu > summary'); if(!s) return null; const r=s.getBoundingClientRect(); return [Math.round(r.width),Math.round(r.height)]})()")
    ok(m and m[0] == m[1] == 44, f'5 phone {w} {scheme}: the account « ⋯ » is a 44 px circle ({m})')
    if w == 390:
      wd = pg.evaluate("(() => { const d = new Date(todayStr() + 'T12:00:00'); while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() - 1); return d.toISOString().slice(0, 10) })()")
      go(pg, 'journal/' + wd)   # a weekday: the strip shows Monday to Friday (a weekend evening's session is Saturday)
      j = pg.evaluate("(()=>{const a=document.querySelector('#main .jstrip a.on b'); return a?getComputedStyle(a).color:null})()")
      ok(j == 'rgb(255, 255, 255)', f'7 phone {scheme}: the chosen journal day is white on blue ({j})')
      go(pg, 'trades')
      d = pg.evaluate("(()=>{const b=document.querySelector('#main a.trow.nav-ra-row .nav-ra button.del'); return b?getComputedStyle(b).backgroundColor:null})()")
      ok(d == 'rgb(212, 55, 61)', f'7 phone {scheme}: the swipe « Delete » is white on the deeper red ({d})')
    if w == 390:
      go(pg, 'settings')
      sb = pg.evaluate("[...document.querySelectorAll('#main .btn')].filter(e=>e.getClientRects().length).slice(0,4).map(e=>Math.round(e.getBoundingClientRect().height))")
      ok(sb and all(h == 44 for h in sb), f'10 phone {scheme}: the Settings buttons are 44 px ({sb})')
      go(pg, 'trades'); pg.locator('#main .fbtn').click(); pg.wait_for_timeout(900)
      fv = pg.evaluate("[...document.querySelectorAll('#fSheet .fs-val select')].map(e=>{const s=getComputedStyle(e); return [s.borderTopWidth, s.backgroundColor, s.boxShadow]})")
      ok(fv and all(x == ['0px', 'rgba(0, 0, 0, 0)', 'none'] for x in fv), f'11 phone {scheme}: the {len(fv)} filter values are plain text ({fv[:1]})')
      pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
      go(pg, 'analytics')
      sh = pg.evaluate("(()=>{const e=document.querySelector('.top .sh-btn'); if(!e) return null; const r=e.getBoundingClientRect(); return [Math.round(r.height), getComputedStyle(e).borderTopLeftRadius]})()")
      ok(sh == [44, '999px'], f'8 phone {scheme}: « Share my stats » is a 44 px pill ({sh})')
    allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
