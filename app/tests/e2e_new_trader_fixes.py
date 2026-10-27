"""
Sweep — a new trader's first day, the small fixes (brief « nouveau trader », step 1, 27 Oct.), Playwright:
  python3 tests/e2e_new_trader_fixes.py http://127.0.0.1:8095
A trader of its own (« Less than 6 months », the 90-day gameplan), one Topstep 50K evaluation (target $3,000, consistency 50 %),
a plan, one winning trade today. Phone 390 (fr, touch, dark), computer 1300 (en), phone 390 (es).
 N1  the account page: the day's P&L « aujourd'hui » / « hoy », never « today » in French or Spanish
 N2  the routine: « 1 sur 1 trade dans ton plan » (the singular)
 N3  the account page, one winning day: the consistency says « Se calcule à partir de 2 jours gagnants », no gold bar
 N4  the account page of an evaluation: « Règles de payout » folded (still opens)
 N5  the coach after the very first trade: « Premier trade noté… », not « Rien à corriger… Refais exactement pareil »
 N6  mission 1 of the gameplan: what is done is checked (track, account, guardrails)
 N7  Stats: « Facteur de profit » / « Factor de beneficio » with its « i », « Séance »
 N8  the help opens (SweepGuide.open)
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
X = {
  'fr': {'today': ' aujourd’hui', 'inplan': 'sur 1 trade dans ton plan', 'cons': 'Se calcule à partir de 2 jours gagnants', 'first': 'Premier trade noté', 'pf': 'Facteur de profit', 'sess': 'Séance', 'en': ['Profit factor', ' today']},
  'en': {'today': ' today', 'inplan': 'of 1 trade in your plan', 'cons': 'Counts from 2 winning days', 'first': 'First trade logged', 'pf': 'Profit factor', 'sess': 'Session', 'en': []},
  'es': {'today': ' hoy', 'inplan': 'de 1 operación en tu plan', 'cons': 'Se calcula a partir de 2 días ganadores', 'first': 'Primera operación anotada', 'pf': 'Factor de beneficio', 'sess': None, 'en': ['Profit factor', ' today']},
}
SP = lambda v: (v or '').replace('\xa0', ' ').replace(' ', ' ')
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, scheme in (('fr', True, 'dark'), ('en', False, 'light'), ('es', True, 'light')):
    w = 390 if phone else 1300; tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme,
                         locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'nt%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'new'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'nt-a', name: 'Topstep 50K', status: 'active', phase: 'eval', money_type: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000, target_c: 300000, consistency_pct: 50 } })")
    gp = ctx.request.post(B + '/api/game/gameplan/start', data=json.dumps({'track': 'B'}), headers=H).json()
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()")
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '500', max_trades: '3', saved_at: Math.floor(Date.now() / 1000) - 3600 } })", day)
    pg.evaluate("(d) => put('trades', { id: 'nt-t1', account_id: 'nt-a', instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 15000, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:05', discipline: { plan: 'y', confirm: 'y', entry: 'y', size: 'y', risk: 'y' } })", day)
    pg.wait_for_timeout(1500); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
    pg.reload(); pg.wait_for_selector('#main .nav-rt', timeout=15000); pg.wait_for_timeout(2500)
    # N2
    ex = SP(pg.evaluate("(document.querySelector('#main .nav-rt-s:nth-child(2) .nav-rt-st') || {}).textContent || ''"))
    ok(x['inplan'] in ex, f'N2 {tag}: « …{x["inplan"]} » ({ex!r})')
    # N5
    co = SP(pg.evaluate("document.querySelector('#main .co-today') ? document.querySelector('#main .co-today').innerText : ''"))
    ok(x['first'] in co and 'Refais exactement pareil' not in co and 'Do exactly the same again' not in co, f'N5 {tag}: the coach after the first trade, « {x["first"]}… » ({co[-120:]!r})')
    # N1 (the account page, its status card)
    pg.evaluate("location.hash = '#account/nt-a'"); pg.wait_for_timeout(1800)
    card = SP(pg.evaluate("(document.querySelector('#main .acard .ac-sub') || {}).textContent || ''"))
    ok(x['today'].strip() in card and (lang == 'en' or 'today' not in pg.evaluate("document.getElementById('main').innerText")), f'N1 {tag}: the account page, « {x["today"].strip()} » ({card!r})')
    # N3, N4
    cons = pg.evaluate("(() => { const r = [...document.querySelectorAll('#main .rule')].find((e) => /Consist/.test(e.textContent)); return r ? [r.textContent.replace(/\\s+/g, ' ').trim(), !!r.querySelector('.bar, .neg, [class*=bar]')] : null })()")
    ok(cons is not None and x['cons'] in SP(cons[0]) and '100' not in cons[0] and not cons[1], f'N3 {tag}: one winning day, the consistency « {x["cons"]} », no bar ({cons})')
    det = pg.evaluate("(() => { const d = document.querySelector('#main details.nav-po-rules'); return d ? d.open : null })()")
    ok(det is False, f'N4 {tag}: an evaluation: « payout rules » folded ({det})')
    if det is False:
      pg.locator('#main details.nav-po-rules > summary').click(); pg.wait_for_timeout(300)
      ok(pg.evaluate("document.querySelector('#main details.nav-po-rules').open") is True, f'N4 {tag}: one tap opens them')
    # N6
    if gp and gp.get('started') and gp.get('access'):
      pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(1200)
      pg.evaluate("window.SweepGPLoad ? SweepGPLoad().then((g) => g.openMission(1)) : SweepGP.openMission(1)"); pg.wait_for_selector('#gSheet .gp-m1', timeout=10000); pg.wait_for_timeout(400)
      li = pg.evaluate("[...document.querySelectorAll('#gSheet .gp-m1 li')].map((l) => l.classList.contains('ok'))")
      ok(li == [True, True, True], f'N6 {tag}: mission 1, what is done is checked: track, account, guardrails ({li})')
      pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(400)
    else: print(f'skip N6 {tag}: no gameplan for this trader ({gp})')
    # N7
    pg.evaluate("location.hash = '#analytics'"); pg.wait_for_timeout(2000)
    txt = pg.evaluate("document.getElementById('main').innerText")
    ok(x['pf'] in txt and not any(e in txt for e in x['en']), f'N7 {tag}: Stats « {x["pf"]} », no English ({[e for e in x["en"] if e in txt]})')
    tip = pg.evaluate("(() => { const l = [...document.querySelectorAll('#main .ik .lbl')].find((e) => e.textContent.includes(%s)); const i = l && l.querySelector('.info'); return i ? i.getAttribute('data-tip') : null })()" % json.dumps(x['pf']))
    ok(bool(tip) and (lang == 'en' or 'gross' not in tip.lower()), f'N7 {tag}: its « i » in the trader\'s language ({tip!r})')
    if x['sess']:
      pg.evaluate("location.hash = '#trade/nt-t1'"); pg.wait_for_timeout(1500)
      ok(x['sess'] in pg.evaluate("document.getElementById('main').innerText"), f'N7 {tag}: « {x["sess"]} » on the trade page')
    # N8
    pg.evaluate("SweepGuide.open()"); pg.wait_for_timeout(800)
    ok(pg.evaluate("!!document.querySelector('.gd-help-ov.open .gd-body h2')"), f'N8 {tag}: the help opens')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
