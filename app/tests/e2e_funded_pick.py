"""
Sweep — a funded account through the guided steps (audit of 16 Oct., R13 + R14), Playwright:
  python3 tests/e2e_funded_pick.py http://127.0.0.1:8095
A trader of its own adds his accounts. Phone 390 (fr) and computer 1300 (en):
 R13  « Funded › Topstep »: the crumb says « XFA (Trading Combine) », the name proposed is « Topstep XFA 50K » (before:
      « Trading Combine 50K »); « Funded › Apex »: each program shown as the funded account (« Apex Trader Funding PA »,
      after the EOD Trail…), the name « Apex Trader Funding PA 50K » (before: « EOD Trail 50K », no firm); an evaluation keeps
      its program's name;
 R14  for a funded account, « New or already running? » is above « More options », not inside it; « Already running »
      unticks the activation fee (paid long ago) and asks the current balance; saved: the balance as typed, no fee expense.
No page error, nothing wider than the window.
"""
import json, random, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'after': 'après le', 'run': 'Déjà en cours'}, 'en': {'after': 'after the', 'run': 'Already running'}}
with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'fp%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Sam', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account] [data-st-ph0]', timeout=20000); pg.wait_for_timeout(600)
    def tap(sel):   # the first-run form can be redrawn by a late sync while it is tapped: find the button again
      for n in range(3):
        try: el = pg.locator(sel).first; el.scroll_into_view_if_needed(timeout=5000); el.click(timeout=5000); break
        except Exception:
          if n == 2: raise
          pg.wait_for_timeout(600)
      pg.wait_for_timeout(250)
    F = 'form[data-form=account]'
    # R13: Topstep, funded
    tap(f'{F} [data-st-ph0=funded]'); tap(f'{F} [data-st-firm=topstep]')
    if pg.locator(f'{F} [data-st-type=combine]').count(): tap(f'{F} [data-st-type=combine]')   # (one program: no step)
    tap(f'{F} [data-st-size="50000"]')
    crumb = pg.evaluate("(document.querySelector('form[data-form=account] [data-st-go=type]') || {}).textContent || ''")
    name = pg.evaluate("(document.querySelector('form[data-form=account] [name=name]') || {}).value || ''")
    ok(crumb == 'XFA (Trading Combine)' and name == 'Topstep XFA 50K', f'{tag} R13 the crumb « {crumb} », the name « {name} »')
    # R14: « New or already running? » above « More options »
    pos = pg.evaluate("(() => { const st = document.querySelector('form[data-form=account] .nav-acst'), o = document.querySelector('form[data-form=account] details.nav-acc-opt'); return st && o ? [!o.contains(st), !!(st.compareDocumentPosition(o) & Node.DOCUMENT_POSITION_FOLLOWING), st.getClientRects().length > 0] : null })()")
    ok(pos == [True, True, True], f'{tag} R14 « New or already running? » shown above « More options », not inside it ({pos})')
    fee0 = pg.evaluate("(document.querySelector('form[data-form=account] [name=nav_fee_on]') || {}).checked")
    pg.locator(f'{F} [data-acst=run]').click(); pg.wait_for_timeout(300)
    fee1 = pg.evaluate("(document.querySelector('form[data-form=account] [name=nav_fee_on]') || {}).checked")
    vis = pg.evaluate("!document.querySelector('form[data-form=account] .nav-acst-run').hidden")
    ok(fee0 is not False and fee1 is False and vis, f'{tag} R14 « {x["run"]} »: the activation fee unticked ({fee0} → {fee1}), the current balance asked')
    if phone: pg.screenshot(path='/tmp/funded_pick_390.png', full_page=True)
    pg.locator(f'{F} [name=nav_cur]').fill('52340')
    if pg.locator(f'{F} [data-onb-fn]').count(): pg.locator(f'{F} [data-onb-fn]').fill('Sam')
    ex0 = pg.evaluate("(S.expenses || []).length")
    pg.evaluate("document.querySelector('form[data-form=account]').requestSubmit()"); pg.wait_for_timeout(1500)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    a = pg.evaluate("(() => { const a = S.accounts.find((x) => x.name === 'Topstep XFA 50K'); if (!a) return null; const st = acctState(a); return { phase: a.phase, bal: st.bal } })()")
    ex1 = pg.evaluate("(S.expenses || []).length")
    ok(a and a['phase'] == 'funded' and a['bal'] == 5234000 and ex1 == ex0, f'{tag} saved: funded, balance $52,340 as typed, no activation expense ({a}, {ex0} → {ex1})')
    # Apex funded, and an evaluation keeps its name
    pg.evaluate("location.hash = '#accounts'"); pg.wait_for_timeout(1200)
    if pg.locator('#main [data-act=acct-add]').count(): pg.locator('#main [data-act=acct-add]').last.click(); pg.wait_for_timeout(800)
    if pg.locator(f'{F} [data-st-ph0]').count():
      tap(f'{F} [data-st-ph0=funded]'); tap(f'{F} [data-st-firm=apex]')
      row = pg.evaluate("(document.querySelector('form[data-form=account] [data-st-type=apex-eod]') || {}).textContent || ''")
      ok('Apex Trader Funding PA' in row and x['after'].split(' ')[0] in row, f'{tag} R13 « Funded › Apex »: each program shown as the funded account ({" ".join(row.split())[:80]!r})')
      if pg.locator(f'{F} [data-st-type=apex-eod]').count(): tap(f'{F} [data-st-type=apex-eod]')
      tap(f'{F} [data-st-size="50000"]')
      nm = pg.evaluate("(document.querySelector('form[data-form=account] [name=name]') || {}).value || ''")
      ok(nm == 'Apex Trader Funding PA 50K', f'{tag} R13 Apex funded: « {nm} »')
      pg.locator(f'{F} [data-st-go=phase]').first.click(); pg.wait_for_timeout(300)
      tap(f'{F} [data-st-ph0=eval]'); tap(f'{F} [data-st-firm=topstep]')
      if pg.locator(f'{F} [data-st-type=combine]').count(): tap(f'{F} [data-st-type=combine]')
      tap(f'{F} [data-st-size="50000"]')
      nm2 = pg.evaluate("(document.querySelector('form[data-form=account] [name=name]') || {}).value || ''")
      inside = pg.evaluate("(() => { const st = document.querySelector('form[data-form=account] .nav-acst'), o = document.querySelector('form[data-form=account] details.nav-acc-opt'); return !!(st && o && o.contains(st)) })()")
      ok(nm2 == 'Trading Combine 50K' and inside, f'{tag} an evaluation keeps « {nm2} », the question stays under « More options » ({inside})')
    else: ok(False, f'{tag} the add-account form opens again')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    allerr += errs; ctx.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
