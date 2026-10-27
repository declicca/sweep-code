"""
Sweep — a trader starting out: his mission's guardrails are the app's values (brief « nouveau trader », step 2, 27 Oct.), Playwright:
  python3 tests/e2e_rookie.py http://127.0.0.1:8095
« Less than 6 months », a Topstep 50K evaluation (daily limit $1,000), phone 390 (fr, touch) — and a trader of « More than a
year » on a computer 1300 (en) who sees what he saw before.
 1  the plan, typed nothing: 3 trades max, $500 (half the daily limit), « Commence petit : tu pourras la monter. »; the
    express plan too ($500)
 2  the trade forms offer MNQ (not NQ); a mini chosen: « Ta règle ce mois-ci : 1 micro-contrat. », no block
 3  the mission says the same: « fini après 2 pertes ou ta perte max du jour », 3 trades, 1 micro
 4  after 2 losses, « Maintenant »: « Fini pour aujourd’hui, c’était ta règle. » and « Fermer ma journée », the only blue button
No page error.
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
TX = {'fr': ('Commence petit : tu pourras la monter.', 'Ta règle ce mois-ci : 1 micro-contrat.', 'Fini pour la journée après 2 pertes ou ta perte max du jour', '3 trades maximum par séance', 'Fini pour aujourd’hui, c’était ta règle.', 'Fermer ma journée'),
      'es': ('Empieza pequeño: podrás subirla después.', 'Tu regla este mes: 1 micro-contrato.', 'Terminado por hoy tras 2 pérdidas o tu pérdida máx. del día', 'Máximo 3 operaciones por sesión', 'Terminado por hoy: era tu regla.', 'Cerrar mi día')}
LOSS = "([d, i]) => put('trades', { id: 'rk-l' + i, account_id: 'rk-a', instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -6000, pnl_manual: true, date: d, entry_time: '1' + i + ':00', exit_time: '1' + i + ':05' })"
BLUE = "[...document.querySelectorAll('#main .nav-rt .btn.primary')].filter((b) => b.getClientRects().length).length"
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, exp in (('fr', True, 'new'), ('en', False, 'gt1'), ('es', True, 'new')):
    w = 390 if phone else 1300; tag = f'{w}-{lang}-{exp}'; rk = exp == 'new'
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'rk%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': exp}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'rk-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000, target_c: 300000 } })")
    pg.wait_for_timeout(800)
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()")
    # 1. the plan (the short one of a first trade, then the express one)
    pg.evaluate("(d) => SweepGame.openPlan(d, { then: () => {} })", day); pg.wait_for_selector('#gSheet [data-gp=max_loss]', timeout=8000); pg.wait_for_timeout(400)
    v = pg.evaluate("[document.querySelector('#gSheet [data-gp=max_loss]').value, document.querySelector('#gSheet [data-gp=max_trades]').value, (document.querySelector('#gSheet .g-small') || {}).textContent || '']")
    tx = TX.get(lang)
    want = ['500', '3', tx[0]] if rk else ['1000', '', '']
    ok(v == want, f'1 {tag}: the plan without typing: {v} (want {want})')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(500)
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); pg.wait_for_selector('#gSheet [data-pmf=max_loss]', timeout=8000); pg.wait_for_timeout(400)
    ml = pg.evaluate("document.querySelector('#gSheet [data-pmf=max_loss]').value")
    ok(ml == ('500' if rk else '1000'), f'1 {tag}: the express plan: max loss {ml}')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(500)
    # 2. the trade form by hand
    pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open [data-tk=inst]', timeout=8000); pg.wait_for_timeout(400)
    inst = pg.evaluate("document.querySelector('#tkSlide [data-tk=inst]').value")
    ok(inst == ('MNQ' if rk else 'NQ'), f'2 {tag}: the trade form offers {inst}')
    pg.select_option('#tkSlide [data-tk=inst]', 'NQ'); pg.wait_for_timeout(500)
    rule = pg.evaluate("(document.querySelector('#tkSlide .tk-rookie') || {}).textContent || ''")
    ok(rule == (tx[1] if rk else ''), f'2 {tag}: a mini chosen: {rule!r}, no block')
    pg.evaluate("closeTicket()"); pg.wait_for_timeout(500)
    # 3. the mission says the same (the 90-day gameplan's first month)
    if rk:
      data = pg.evaluate("(window.SweepGPLoad ? SweepGPLoad() : Promise.resolve(window.SweepGP)).then((g) => JSON.stringify(g && g.data || {}))")
      ok(tx[2] in data and '−2R,' not in data and tx[3] in data, f'3 {tag}: the mission: « {tx[2]} », 3 trades')
    # 4. two losses
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '%s', max_trades: '%s', saved_at: Math.floor(Date.now() / 1000) - 3600 } })" % ('500' if rk else '1000', '3' if rk else '5'), day)
    for i in (1, 2): pg.evaluate(LOSS, [day, i])
    pg.wait_for_timeout(1500); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500); pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_timeout(1500)
    now = pg.evaluate("(document.querySelector('#main .nav-rt .nav-now') || {}).textContent || ''")
    btn = pg.evaluate("(() => { const b = document.querySelector('#main .nav-now [data-rt=fin].btn.primary'); return b ? b.textContent.trim() : '' })()")
    if rk:
      ok(tx[4] in now and btn == tx[5] and pg.evaluate(BLUE) == 1, f'4 {tag}: after 2 losses, « Maintenant » says his rule, « {btn} », one blue button ({now[:90]!r}, {pg.evaluate(BLUE)})')
      if os.environ.get('SWEEP_SHOTS'): pg.locator('#main .nav-rt').screenshot(path=os.path.join(os.environ['SWEEP_SHOTS'], f'rookie-now-{tag}.png'))
      b = pg.locator('#main .nav-now [data-rt=fin]'); b.tap(); pg.wait_for_selector('#gSheet [data-g=save-review]', timeout=8000)
      ok(True, f'4 {tag}: « {tx[5]} » opens the review')
    else:
      ok('Left today' in now and not btn, f'4 {tag}: more than a year: 2 losses do not end the day ({now[:80]!r})')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
