"""
Sweep — the fixes of the 27 Oct. app tour (group A), dev environment with Playwright, phone 390 (touch) and computer 1300, French:
  python3 tests/e2e_tour_fixes.py http://127.0.0.1:8095 /tmp/show_state.json
 A1  the manual form: the entry price has no number as a hint (it looked filled in); « Save » without it: the field is
     scrolled to, outlined in gold, the cursor in it; typing a price takes the outline away
 A2  the checklist of the trade form and of the trade page in the trader's language (the default questions are saved in English)
 A3  « 1 nouveauté » in the singular
 A4  the welcome page: no bar at the bottom over its account tiles
 A5  the welcome page: no « add Sweep to your home screen » on the sign-up day
 A6  « Less than 6 months » counts at once: the coach's tone for a trader starting out, never « No setup chosen »
"""
import json, os, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
EN_QS = ['Was this trade part of my trading plan?', 'Did I wait for confirmation?', 'Was my entry valid?', 'Did I respect my maximum position size?', 'Did I define my risk before entering?']
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

with sync_playwright() as p:
  br = p.chromium.launch()
  for w, phone in ((390, True), (1300, False)):
    tag = str(w)
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=15000); pg.wait_for_timeout(1500)
    # A1
    pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open [data-tk="entry"]', timeout=8000); pg.wait_for_timeout(600)
    ph = pg.evaluate("document.querySelector('#tkSlide [data-tk=\"entry\"]').getAttribute('placeholder')")
    ok(ph == '', f'A1 {tag} the entry price has no number as a hint ({ph!r})')
    pg.locator('#tkSlide .tk-dir button').first.click(); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#tkSlide').scrollTop = 0; const s = document.querySelector('#tkSlide .tk-body, #tkSlide'); s.scrollTop = 0")
    pg.locator('#tkSlide [data-act="tk-save"]').first.click(); pg.wait_for_timeout(900)
    st = pg.evaluate("""(() => { const f = document.querySelector('#tkSlide [data-tk="entry"]'), r = f.getBoundingClientRect(), box = f.closest('.tk-in') || f;
      return { miss: box.hasAttribute('data-tk-miss'), inv: f.getAttribute('aria-invalid'), focus: document.activeElement === f, seen: r.top >= 0 && r.bottom <= innerHeight,
        ring: getComputedStyle(box).boxShadow, err: (document.getElementById('tkErr') || {}).textContent || '' }; })()""")
    ok(st['miss'] and st['inv'] == 'true' and st['focus'] and st['seen'], f'A1 {tag} « Save » without the entry price: the field is on screen, outlined, the cursor in it ({st})')
    ok('0px 0px 0px 3px' in st['ring'], f'A1 {tag} the gold outline is drawn ({st["ring"][:60]})')
    pg.locator('#tkSlide [data-tk="entry"]').type('21850'); pg.wait_for_timeout(300)
    ok(not pg.evaluate("!!document.querySelector('#tkSlide [data-tk-miss], #tkSlide [aria-invalid]')"), f'A1 {tag} typing a price takes the outline away')
    # A2
    pg.evaluate("showStep2 && showStep2('f1')") if pg.evaluate("typeof showStep2 === 'function' && !document.querySelector('#tkSlide .nav-ck-q')") else None
    pg.wait_for_timeout(800)
    qs = pg.evaluate("[...document.querySelectorAll('.nav-ck-q > span, .nav-am .nav-q-l, #tkSlide .nav-ck-q span')].map((e) => e.textContent.trim()).filter(Boolean)")
    ok(qs and not any(q.startswith(e) for q in qs for e in EN_QS), f'A2 {tag} the checklist questions in French ({qs[:3]})')
    # A2 on the trade page too
    pg.evaluate("closeTicket && closeTicket()"); pg.wait_for_timeout(500)
    pg.evaluate("location.hash = '#trade/' + encodeURIComponent(S.trades[0].id)"); pg.wait_for_timeout(1800)
    tq = pg.evaluate("[...document.querySelectorAll('#main .qlist .q > span')].map((e) => e.textContent.trim()).filter(Boolean)")
    ok(tq and not any(q.startswith(e) for q in tq for e in EN_QS), f'A2 {tag} the trade page questions in French ({tq[:2]})')
    # (27 Oct., brief « daily loop » step 2) the coach in the singular: a plan of 1 trade, 1 trade done
    if phone:
      j0 = pg.evaluate("JSON.stringify(getDoc('journals', todayStr()) || null)")
      pg.evaluate("() => { const d = todayStr(); put('accounts', { id: 'tf-acc', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } }); put('journals', { id: d, pre: { bias: 'bullish', max_loss: '500', max_trades: '1', saved_at: Math.floor(Date.now() / 1000) } }); put('trades', { id: 'tf-one', account_id: 'tf-acc', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 5000, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:05' }) }")
      pg.wait_for_timeout(800)
      bf = pg.evaluate("SweepCoach.before({ form: 'manual', account: 'tf-acc', date: todayStr(), qty: 1 })") or ''
      ok('1 trades' not in bf and 'Ton trade prévu est fait' in bf, f'{tag} the coach in the singular: « Ton trade prévu est fait » ({bf[-110:]!r})')
      pg.evaluate("(j) => { remove('trades', 'tf-one'); remove('accounts', 'tf-acc'); const o = JSON.parse(j); if (o) put('journals', o); else remove('journals', todayStr()) }", j0); pg.wait_for_timeout(500)
      pg.evaluate("Promise.all(Object.values(chains)).then(() => true)")   # (27 Oct.: the shared trader must be left as found — a later test of the same group saw this account on the CI)
    # A3
    st3 = pg.evaluate("[SweepGame.sumText(1), SweepGame.sumText(3)]")
    ok(st3 == ['1 nouveauté · Voir Ma progression', '3 nouveautés · Voir Ma progression'], f'A3 {tag} « 1 nouveauté », « 3 nouveautés » ({st3})')
    c.close()

    # a new trader, French: the welcome page
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    c = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    n = 'tour%d' % int(time.time() * 1000)
    r = c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
    ok(r.status == 201, f'{tag} new trader signed up ({r.status})')
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-onb-fn]', timeout=15000); pg.wait_for_timeout(800)
    # A4, A5
    ok(not pg.locator('#bottomnav').is_visible(), f'A4 {tag} the welcome page: no bar at the bottom')
    txt = pg.locator('#main').inner_text()
    ok('Safari' not in txt and 'écran d’accueil' not in txt and "écran d'accueil" not in txt, f'A5 {tag} the welcome page: no « add to the home screen »')
    # A6
    pg.fill('[data-onb-fn]', 'Léa'); pg.locator('.nav-onb-me [data-exp="new"]').click(); pg.wait_for_timeout(300)
    f = '#main form[data-form=account]'
    for s in (f + ' [data-st-ph0=eval]', f + ' [data-st-firm=topstep]', f + ' [data-st-size="50000"]'):
      pg.locator(s).first.click(); pg.wait_for_timeout(250)
    pg.evaluate("(f) => document.querySelector(f).requestSubmit()", f)
    pg.wait_for_function("S.accounts.length > 0", timeout=8000); pg.wait_for_timeout(1500)
    ok(pg.evaluate("S.me && S.me.experience") == 'new', f'A6 {tag} « Less than 6 months » counts at once ({pg.evaluate("S.me && S.me.experience")!r})')
    ok(pg.locator('#bottomnav').is_visible() or not phone, f'A4 {tag} the bar at the bottom is back once the account exists')
    seen = []
    for _ in range(3):
      seen.append(pg.evaluate("document.body.innerText"))
      sk = pg.locator('#gSheet [data-g=plan-skip]')
      if sk.count() and sk.first.is_visible(): sk.first.click(); pg.wait_for_timeout(1200)
      else: pg.wait_for_timeout(800)
    ok(not any('Pas de setup choisi' in t for t in seen), 'A6 ' + tag + ' the coach never asks a setup of a trader starting out')
    c.close()
  # EN and ES (phone, dark): the singular, and the Spanish checklist not in English
  for lang, one in (('en', '1 new · See My progress'), ('es', '1 novedad · Ver Mi progreso')):
    c = br.new_context(storage_state=STATE, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale={'en': 'en-US', 'es': 'es-ES'}[lang], color_scheme='dark')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=15000); pg.wait_for_timeout(1200)
    ok(pg.evaluate("SweepGame.sumText(1)") == one, f'A3 390 {lang} « {one} »')
    if lang == 'es':
      pg.evaluate("location.hash = '#trade/' + encodeURIComponent(S.trades[0].id)"); pg.wait_for_timeout(1800)
      tq = pg.evaluate("[...document.querySelectorAll('#main .qlist .q > span')].map((e) => e.textContent.trim()).filter(Boolean)")
      ok(tq and not any(q.startswith(e) for q in tq for e in EN_QS), f'A2 390 es the trade page questions in Spanish ({tq[:2]})')
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
