"""
Sweep — Stats, lean (10 Nov., brief « produit final » step 5), dev environment with Playwright:
  python3 tests/e2e_stats_lean.py http://127.0.0.1:8095 /tmp/show_state.json
Computer 1300 x 850 (light and dark) and phone 390 x 844 (touch):
 - before the « Deep dive »: at most 12 cards, none of the six small tiles (most active, most / least profitable, direction,
   winning streak, green days), no game rank strip; the drawdown, the P&L breakdown and « Patterns to watch » are there;
 - every figure stays findable: « Day of week » shows the most active and the most / least profitable days, « Long vs short »
   the direction, « Behavior » the winning streak and the green days, and a « Duration » tab holds the duration analysis;
 - phone: #analytics/duration opens the duration analysis; no horizontal overflow, no page error.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
TOP = """(() => { const m = document.getElementById('main'), deep = m.querySelector('section.deep'); const vis = (e) => e.checkVisibility();
  const cards = [...m.querySelectorAll('.ikpis > *, .igrid > *, section.ic')].filter((e) => vis(e) && (!deep || (deep.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_PRECEDING)));
  const txt = cards.map((c) => c.textContent).join(' ');
  return { n: cards.length, tiles: !!m.querySelector('.g-ins .tiles, .g-ins .it'), rank: !!m.querySelector('#gIns, .nav-rank'),
    dd: /Drawdown|drawdown/.test(txt), split: /Répartition du P&L|P&L breakdown/.test(txt), pat: /Tendances à surveiller|Patterns to watch/.test(txt),
    over: document.documentElement.scrollWidth > innerWidth } })()"""
def tab(pg, k):
  pg.locator(f'#main section.deep [data-k="deep"][data-v="{k}"]').click(); pg.wait_for_timeout(600)
  return pg.evaluate("document.querySelector('#main section.deep').textContent")
with sync_playwright() as p:
  br = p.chromium.launch()
  for cs in ('light', 'dark'):
    ctx = br.new_context(storage_state=STATE, viewport={'width': 1300, 'height': 850}, color_scheme=cs, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + '/#analytics'); pg.wait_for_selector('#main section.deep', timeout=20000); pg.wait_for_timeout(1500)
    r = pg.evaluate(TOP); tag = f'1300-{cs}'
    ok(r['n'] <= 12, f'{tag} at most 12 cards before the « Deep dive » ({r["n"]})')
    ok(not r['tiles'] and not r['rank'], f'{tag} no small tiles, no rank strip')
    ok(r['dd'] and r['split'] and r['pat'], f'{tag} drawdown, P&L breakdown, patterns to watch kept ({r})')
    ok(not r['over'], f'{tag} no horizontal overflow')
    t = tab(pg, 'weekday'); ok('Plus actif' in t and 'Plus rentable' in t and 'Moins rentable' in t, f'{tag} « Day of week »: most active, most / least profitable')
    t = tab(pg, 'direction'); ok('Direction des trades' in t, f'{tag} « Long vs short »: the direction')
    t = tab(pg, 'behavior'); ok('Plus longue série gagnante' in t and 'Jours verts de suite' in t, f'{tag} « Behavior »: winning streak, green days')
    t = tab(pg, 'duration'); ok('Analyse de durée' in t or 'durée' in t.lower(), f'{tag} a « Duration » tab with the duration analysis')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    ctx.close()
  ctx = br.new_context(storage_state=STATE, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-CA')
  ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
  pg.goto(B + '/#analytics'); pg.wait_for_selector('#main .g-top', timeout=20000); pg.wait_for_timeout(1500)
  r = pg.evaluate(TOP)
  ok(r['n'] <= 12 and not r['tiles'] and not r['over'], f'390 at most 12 cards, no small tiles, no overflow ({r["n"]})')
  pg.evaluate("location.hash = '#analytics/duration'"); pg.wait_for_timeout(1500)
  ok(pg.evaluate("/durée/i.test(document.querySelector('#main section.deep').textContent) && document.querySelector('#main section.deep').checkVisibility()"), '390 #analytics/duration opens the duration analysis')
  ok(not errs, '390 no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
