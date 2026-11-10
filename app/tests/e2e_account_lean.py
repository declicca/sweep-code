"""
Sweep — an account's page, lean (10 Nov., brief « produit final » step 4), dev environment with Playwright:
  python3 tests/e2e_account_lean.py http://127.0.0.1:8095 /tmp/show_state.json
A funded sample account, phone 390 x 844 (touch, light and dark) and computer 1300 x 850:
 - « Move to live » is in the page's « ⋯ » menu, no card on the page; an evaluation that passed has « Move to funded » there too;
 - the payout rules are folded, their summary on the line, and open with a tap;
 - the status repeats neither the name nor the balance of the page's top, and has no second equity curve;
 - phone: the page is at most 1,710 px high (2,437 px before), no horizontal overflow, no page error.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
with sync_playwright() as p:
  br = p.chromium.launch()
  for w, h, mob, cs in ((390, 844, True, 'light'), (390, 844, True, 'dark'), (1300, 850, False, 'dark')):
    tag = f'{w}-{cs}'
    ctx = br.new_context(storage_state=STATE, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, color_scheme=cs, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + '/#accounts'); pg.wait_for_function("() => typeof S !== 'undefined' && (S.accounts || []).length > 0", timeout=20000); pg.wait_for_timeout(800)
    aid = pg.evaluate("(S.accounts.find((a) => a.phase === 'funded' && a.status !== 'archived') || {}).id")
    ok(bool(aid), f'{tag} a funded sample account ({aid})')
    pg.evaluate(f"location.hash = '#account/{aid}'"); pg.wait_for_selector('#main details.menu', timeout=15000); pg.wait_for_timeout(1500)
    r = pg.evaluate("""(() => { const m = document.getElementById('main'), po = m.querySelector('details.nav-po-rules'), st = m.querySelector('.acards .acard');
      return { live: !!m.querySelector('details.menu .menu-pop [data-live-go]'), row: !!m.querySelector('.nav-live-row, .nav-pass-row.ok'),
        folded: po ? !po.open : null, sum: po ? (po.querySelector('summary small') || {}).textContent || '' : '',
        repeat: st ? ['.ac-top', '.ac-bal > span:first-child', '.spark'].filter((s) => { const e = st.querySelector(s); return e && e.checkVisibility(); }) : null,
        height: m.scrollHeight, over: document.documentElement.scrollWidth > innerWidth } })()""")
    ok(r['live'] and not r['row'], f'{tag} « Move to live » in the « ⋯ » menu, no card on the page ({r["live"]}, {r["row"]})')
    ok(r['folded'] is True and len(r['sum'].strip()) > 0, f'{tag} the payout rules folded, their summary on the line (« {r["sum"]} »)')
    ok(r['repeat'] == [], f'{tag} the status repeats nothing of the top ({r["repeat"]})')
    if mob: ok(r['height'] <= 1710, f'{tag} the page at most 1,710 px high ({r["height"]})')
    ok(not r['over'], f'{tag} no horizontal overflow')
    pg.locator('#main details.nav-po-rules > summary').click(); pg.wait_for_timeout(300)
    ok(pg.evaluate("document.querySelector('#main details.nav-po-rules').open && !!document.querySelector('#main details.nav-po-rules input[data-po]').checkVisibility()"), f'{tag} a tap opens the payout rules')
    # an evaluation that passed: « Move to funded » in its menu
    ev = pg.evaluate("(S.accounts.find((a) => window.SweepPass && SweepPass.passed(a)) || {}).id")
    if ev:
      pg.evaluate(f"location.hash = '#account/{ev}'"); pg.wait_for_timeout(1500)
      ok(pg.evaluate("!!document.querySelector('#main details.menu .menu-pop [data-pass-btn]') && !document.querySelector('#main .nav-pass-row.ok')"), f'{tag} a passed evaluation: « Move to funded » in the « ⋯ » menu')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    ctx.close()
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
