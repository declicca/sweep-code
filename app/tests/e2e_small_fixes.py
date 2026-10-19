"""
Sweep — the small consistencies of the audit of 16 Oct. (R15-R18, R21, R22), Playwright:
  python3 tests/e2e_small_fixes.py http://127.0.0.1:8095
A trader of its own. Phone 390 (fr) and computer 1300 (en):
 R15  the full manual form: no « Daily risk left » box (the coach's line says what is left), a warning only past the limit;
 R16  the screenshot sheet: « Touche pour choisir une capture » on a phone, « Paste or drop your screenshot (Ctrl+V) » on a computer;
 R17  « Your real net » done since January, nothing yet this month: My money on Today shows the real net since January, not $0;
 R18  an account added « already running » (an adjustment), no trade yet: the Accounts card is on Today;
 R21  « Not trading today » chosen in the plan: a day off (the routine says so, nothing else to do);
 R22  the rule of the last review comes back in the next plan, a day off between them skipped;
 R23  « Check the trade »: the Symbol list and the date inside the card; Sweep AI steps aside reading down an account (phone).
No page error, nothing wider than the window.
"""
import json, random, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def shot(pg):   # « New trade » shows its fields once a screenshot is there (18 Oct.): the test one, read as no table
    pg.route('**/api/ai/import', lambda r: r.fulfill(status=200, content_type='application/json', body='{"trades": []}'))
    pg.locator('.nav-am.open input[data-am-file]').first.set_input_files('tests/fixture-shot.png')
    pg.wait_for_selector('.nav-am.open .nav-am-grid', timeout=8000); pg.wait_for_timeout(300)
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'drop': 'Touche pour choisir une capture', 'since': 'Net réel depuis janvier'}, 'en': {'drop': 'Paste or drop your screenshot (Ctrl+V)', 'since': 'Net real money · since January'}}
GAMEDAY = "(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()"
with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'sf%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Ari', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
    # R18: an account already running, no trade
    pg.evaluate("put('accounts', { id: 'sf-a', name: 'Apex PA 50K', status: 'active', phase: 'funded', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 250000, dll_c: 100000 }, adjustments: [{ id: 'adj1', at: '2026-10-01', amount_c: 234000, note: '' }] })"); pg.wait_for_timeout(900)
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-dash', timeout=8000); pg.wait_for_timeout(1000)
    ok(pg.locator('#main .nav-dash .d-acc').count() == 1 and pg.evaluate("S.trades.filter((t) => !t.demo).length") == 0, f'{tag} R18 an account already running, no trade: the Accounts card is on Today')
    # R17: the real net since January, nothing this month
    pg.evaluate("""() => { put('expenses', { id: 'est-sf-evaluation', date: '2026-01-01', firm_id: '', account_id: '', category: 'evaluation', amount_c: 60000, estimated: true });
      put('payouts', { id: 'est-payouts', firm_id: '', account_id: '', gross_c: 360000, split_pct: 100, fees_c: 0, net_c: 360000, amount_c: 360000, status: 'paid', paid_on: '2026-01-01', payment_date: '2026-01-01', request_date: '2026-01-01' });
      const s = JSON.parse(JSON.stringify(S.settings)); s.realnet = { state: 'done', at: '2026-10-10', from: '2026-01-01', per: 'year' }; put('settings', s); }""")
    pg.wait_for_timeout(1000); pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_timeout(1500)
    mny = pg.evaluate("(() => { const c = document.querySelector('#main .d-money'); return c ? [c.querySelector('.nav-mny-l').textContent.trim(), c.querySelector('.nav-mny-big').textContent.trim()] : null })()")
    want = pg.evaluate("money(300000, { dec: 0 })")
    ok(mny and mny[0].startswith(x['since']) and mny[1] == want, f'{tag} R17 My money: « {mny} » (want « {x["since"]} », {want})')
    # R21: « Not trading today » in the plan
    day = pg.evaluate(GAMEDAY)
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); pg.wait_for_selector('#gSheet [data-pm=dayoff]', timeout=8000); pg.wait_for_timeout(400)
    pg.locator('#gSheet [data-pm=dayoff]').click(); pg.wait_for_timeout(2500)   # (the pre-market questionnaire, since 19 Oct.: its « Not trading today »)
    off = pg.evaluate("(d) => { const j = getDoc('journals', d); return !!(j && j.pre && j.pre.day_off) }", day)
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_timeout(2500)
    ok(off and pg.locator('#main .nav-rt.off').count() == 1, f'{tag} R21 « Not trading today » in the plan: a day off, the routine says so ({off})')
    # R22: the last review's rule, a day off between
    pg.evaluate("""(d) => { put('journals', { id: ymdAdd(d, -3), pre: { bias: 'bullish', max_loss: '1000', saved_at: 1 }, post: { reviewed_at: '2026-10-10T20:00:00Z', tomorrow: 'Stop after 2 trades.' } });
      put('journals', { id: ymdAdd(d, -2), pre: { bias: 'no_trade', day_off: true }, post: { reviewed_at: '2026-10-11T20:00:00Z' } }); }""", day)
    pg.wait_for_timeout(800)
    rule = pg.evaluate("(d) => SweepCoach.ruleFor(d)", pg.evaluate("(d) => ymdAdd(d, 1)", day))
    ok(rule == 'Stop after 2 trades.', f'{tag} R22 the next plan starts with the last review rule, the day off skipped (« {rule} »)')
    # R15 + R16: the two add forms
    pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open', timeout=8000); pg.wait_for_timeout(600)
    pg.evaluate("() => { TK.account = 'sf-a'; TK.inst = 'NQ'; TK.dir = 'long'; TK.qty = 1; TK.entry = 21000; TK.stop = 20990; tkRefresh(); }"); pg.wait_for_timeout(500)
    ok(pg.locator('#tkSlide .tk-budget').count() == 0, f'{tag} R15 the manual form: no « Daily risk left » box')
    pg.evaluate("() => { TK.qty = 10; TK.stop = 20900; tkRefresh(); }"); pg.wait_for_timeout(500)
    ok(pg.locator('#tkSlide .tk-warn', has_text='Risk limit exceeded' if lang == 'en' else 'Limite de risque').count() >= 1 or pg.locator('#tkSlide .tk-warn').count() >= 1, f'{tag} R15 past the limit: the warning stays')
    pg.evaluate("closeTicket()"); pg.wait_for_timeout(500)
    pg.evaluate("editDoc('settings', 'settings', (d) => { d.add_mode_pref = 'shot'; })"); pg.wait_for_timeout(300)
    pg.evaluate("openTicket(null)"); pg.wait_for_selector('.nav-am.open', timeout=8000); pg.wait_for_timeout(500)
    drop = pg.evaluate("(document.querySelector('.nav-am .nav-am-drop b') || {}).textContent || ''")
    ok(drop == x['drop'], f'{tag} R16 the screenshot sheet: « {drop} »')
    shot(pg)
    # R23: « Check the trade » open, the Symbol list and the date stay inside the card
    pg.evaluate("document.querySelectorAll('.nav-am.open details.nav-am-more-d').forEach((d) => d.open = true)"); pg.wait_for_timeout(400)
    fit = pg.evaluate("(() => { const d = document.querySelector('.nav-am.open .nav-am-more-d').getBoundingClientRect(), b = document.querySelector('.nav-am.open .nav-am-more-d .nav-am-selb').getBoundingClientRect(), i = document.querySelector('.nav-am.open .nav-am-more-d input[type=date]').getBoundingClientRect(); return [Math.round(d.right - b.right), Math.round(d.right - i.right)] })()")
    ok(fit[0] >= 8 and fit[1] >= 8, f'{tag} R23 « Check the trade »: the Symbol list and the date inside the card ({fit})')
    pg.evaluate("document.querySelectorAll('.nav-am.open [data-am=close]').forEach((b) => b.click())"); pg.wait_for_timeout(400)
    # R23: Sweep AI's button steps aside while reading down an account (phone), back on the way up
    pg.evaluate("location.hash = '#account/sf-a'"); pg.wait_for_timeout(1800)
    pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(300); pg.evaluate("scrollBy(0, 400)"); pg.wait_for_timeout(700)
    away = pg.evaluate("getComputedStyle(document.querySelector('.ask-fab')).opacity")
    pg.evaluate("scrollBy(0, -150)"); pg.wait_for_timeout(700)
    back = pg.evaluate("[getComputedStyle(document.querySelector('.ask-fab')).opacity, document.body.classList.contains('ux-fab-cover')]")
    side = pg.evaluate("(() => { const b = document.querySelector('aside.side .nav-ask-side'); return !!b && getComputedStyle(b).display !== 'none' })()")
    if phone: ok(away == '0' and (back[0] == '1' or back[1]), f'{tag} R23 Sweep AI steps aside reading down an account (phone), back scrolling up unless it would sit on a control ({away}, {back})')
    else: ok(pg.evaluate("getComputedStyle(document.querySelector('.ask-fab')).display") == 'none' and side, f'{tag} audit 18 Oct.: on a computer, Sweep AI is in the left menu, nothing floats over the cards ({side})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
    allerr += errs; ctx.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
