"""
Sweep — every trading word of the first day says what it means where it is shown (brief « nouveau trader », step 3, 27 Oct.):
  python3 tests/e2e_terms.py http://127.0.0.1:8095
A new trader « Less than 6 months », phone 390 (fr and es, touch: a « i » opens with a tap) and computer 1300 (en).
 1  the account step: Drawdown, Payout, Coussin under the tiles, each with its « i »; for a trader starting out in an
    evaluation, the funded-account option and the daily-limit option are folded in « Plus d'options »
 2  the plan: Biais and the drawdown room with their « i »
 3  the trade forms: « Setup » with its « i », a setup held down says what it means (and does not pick it), « R » with its « i »
 4  the account page: Consistance, Pire recul, Facteur de profit, each with its explanation
No page error, nothing wider than the window.
"""
import json, os, random, sqlite3, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'dd': 'Drawdown : la perte maximale', 'bias': 'Biais : ce que tu penses', 'room': 'Marge de drawdown :', 'r': 'R : ton risque prévu', 'sweep': 'Le prix dépasse un haut', 'worst': 'Pire recul', 'more': 'Plus d’options', 'pf': 'Facteur de profit'},
     'en': {'dd': 'Drawdown: the most the account may lose', 'bias': 'Bias: what you think', 'room': 'Drawdown room:', 'r': 'R: your planned risk', 'sweep': 'Price runs past a recent high', 'worst': 'Worst drawdown', 'more': 'More options', 'pf': 'Profit factor'},
     'es': {'dd': 'Drawdown: la pérdida máxima', 'bias': 'Sesgo: lo que crees', 'room': 'Margen de drawdown:', 'r': 'R: tu riesgo previsto', 'sweep': 'El precio supera un máximo', 'worst': 'Peor retroceso', 'more': 'Más opciones', 'pf': 'Factor de beneficio'}}
TIP = "(document.getElementById('swTip') || {}).textContent || ''"
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone in (('fr', True), ('en', False), ('es', True)):
    w = 390 if phone else 1300; tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tm%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    tap = (lambda l: l.tap()) if phone else (lambda l: l.click())
    def tip_of(sel):   # a phone: a tap opens the bubble; a computer: the « i » carries the same sentence (shown on hover)
      el = pg.locator(sel).first
      if phone: tap(el); pg.wait_for_timeout(250); t = pg.evaluate(TIP); pg.evaluate("document.getElementById('swTip') && document.getElementById('swTip').remove()"); return t
      return el.get_attribute('data-tip') or ''
    # 1. the account step
    pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-onb-fn]', timeout=15000); pg.wait_for_timeout(600)
    n = pg.locator('#main .ux-st-gl .sw-term').count()
    t1 = tip_of('#main .ux-st-gl .sw-term')
    ok(n == 3 and t1.startswith(x['dd']), f'1 {tag}: Drawdown, Payout, Coussin under the tiles, each with its « i » ({n}, {t1[:50]!r})')
    tap(pg.locator('.nav-onb-me [data-exp="new"]')); pg.wait_for_timeout(200)
    f = '#main form[data-form=account]'
    for s in (f + ' [data-st-ph0=eval]', f + ' [data-st-firm=topstep]'):
      tap(pg.locator(s).first); pg.wait_for_timeout(300)
    if pg.locator(f + ' [data-st-type]').count(): tap(pg.locator(f + ' [data-st-type]').first); pg.wait_for_timeout(300)
    tap(pg.locator(f + ' [data-st-size="50000"]').first); pg.wait_for_timeout(500)
    more = pg.evaluate("(() => { const d = document.querySelector('#main .ux-st-more'); return d ? [d.open, d.querySelector('summary').textContent.trim(), !!d.querySelector('.ux-st-choice, .ux-st-opt')] : null })()")
    ok(more is None or (more[0] is False and more[1] == x['more'] and more[2]), f'1 {tag}: starting out, an evaluation: the funded-account choices in « {x["more"]} », folded ({more})')
    if more:
      tap(pg.locator('#main form[data-form=account] .nav-acc-opt > summary')); pg.wait_for_timeout(300)   # (31 Oct., C2) one « More options » for both
      if pg.locator('#main .ux-st-more .ux-st-cl .sw-term').count():
        ok(len(tip_of('#main .ux-st-more .ux-st-cl .sw-term')) > 40, f'1 {tag}: the funded-account option has its « i »')
    # (the account itself, put in: the rest of the first day)
    pg.evaluate("put('accounts', { id: 'tm-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000, target_c: 300000, consistency_pct: 50 } })")
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=15000); pg.wait_for_timeout(1500)
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()")
    # 2. the plan
    pg.evaluate("(d) => SweepGame.openPlan(d, { then: () => {} })", day); pg.wait_for_selector('#gSheet [data-gp=max_loss]', timeout=8000); pg.wait_for_timeout(400)
    tb = tip_of('#gSheet .g-f > span .sw-term')
    ok(tb.startswith(x['bias']), f'2 {tag}: « Biais » and its « i » ({tb[:40]!r})')
    rm = pg.locator('#gSheet .g-dll .sw-term')
    ok(rm.count() == 0 or tip_of('#gSheet .g-dll .sw-term').startswith(x['room']), f'2 {tag}: the drawdown room, its « i »')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(500)
    # 3. the trade forms
    pg.evaluate("openTicket(null)"); pg.wait_for_selector('.nav-am.open', timeout=8000); pg.wait_for_timeout(600)
    if pg.locator('.nav-am.open [data-am=no-shot]').count(): tap(pg.locator('.nav-am.open [data-am=no-shot]')); pg.wait_for_selector('.nav-am.open .nav-sp', timeout=8000); pg.wait_for_timeout(500)   # « No screenshot? »: the form with its setups
    pg.evaluate("(() => { const d = document.querySelector('.nav-am.open .nav-am-more-d'); if (d) d.open = true; })()"); pg.wait_for_timeout(300)
    if pg.locator('.nav-am.open .nav-sp .sw-term').count():
      ok(len(tip_of('.nav-am.open .nav-sp .sw-term')) > 30, f'3 {tag}: « Setup » with its « i »')
      chip = pg.locator('.nav-am.open [data-sp="Liquidity sweep"]')
      if chip.count():
        if phone:
          box = chip.bounding_box(); pg.mouse.move(box['x'] + 10, box['y'] + 10); pg.mouse.down(); pg.wait_for_timeout(700); held = pg.evaluate(TIP); pg.mouse.up(); pg.wait_for_timeout(300)
          ok(held.startswith(x['sweep']) and not pg.evaluate("document.querySelector('.nav-am.open [data-sp=\"Liquidity sweep\"]').classList.contains('on')"), f'3 {tag}: « Liquidity sweep » held down: what it means, not picked ({held[:40]!r})')
        else:
          ok((chip.get_attribute('title') or '').startswith(x['sweep']), f'3 {tag}: « Liquidity sweep »: what it means on hover')
    else: ok(False, f'3 {tag}: the setup row of the screenshot form')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400); pg.evaluate("document.querySelectorAll('.nav-am.open [data-am=close]').forEach((b) => b.click())"); pg.wait_for_timeout(400)
    pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open', timeout=8000); pg.wait_for_timeout(500)
    ok(pg.locator('#tkSlide #tkRisk .sw-term').count() == 1 and (pg.locator('#tkSlide #tkRisk .sw-term').get_attribute('data-tip') or '').startswith(x['r']), f'3 {tag}: « R » with its « i » in the form by hand')
    pg.evaluate("closeTicket()"); pg.wait_for_timeout(400)
    # 4. the account page
    pg.evaluate("location.hash = '#account/tm-a'"); pg.wait_for_timeout(1800)
    main = pg.evaluate("document.getElementById('main').innerText")
    terms = pg.evaluate("[...document.querySelectorAll('#main .statline .sw-term')].map((e) => e.getAttribute('data-tip'))")
    ok(x['worst'] in main and x['pf'] in main and len(terms) >= 2 and any(t.startswith(x['worst']) for t in terms), f'4 {tag}: « {x["worst"]} » and « {x["pf"]} », each with its explanation ({[t[:25] for t in terms]})')
    cons = pg.evaluate("(() => { const r = [...document.querySelectorAll('#main .rule')].find((e) => /Consist/.test(e.textContent)); const t = r && r.querySelector('[data-tip]'); return t ? t.getAttribute('data-tip') : '' })()")
    ok(len(cons) > 20, f'4 {tag}: the consistency with its explanation ({cons[:40]!r})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
