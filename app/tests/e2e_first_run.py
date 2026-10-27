"""
Sweep — the first run in 3 steps (brief 03 step 1), dev environment with Playwright:
  python3 tests/e2e_first_run.py http://127.0.0.1:8095 [storage_state, unused: every case signs up its own trader]
A brand-new trader, phone (fr, es) and computer (en), from the first screen after sign-up to the trade form:
  1. « Three steps and you're trading »: first name on top (asked again if empty, nothing created), « How long have you
     been trading? » optional, the guided picker (Apex › EOD › 50K), the account options folded under « More options »;
  2. « Create account » → the plan of the day, its max loss taken from the account's daily limit ($1,000), « Save and add
     my trade » → 3. the trade form. At most 8 taps, the first name (and the experience when tapped) kept on the server.
Then Today grows with the trader: with 0 trades only the routine; the 1st trade brings performance, accounts, calendar and
news; My money and the rank wait for the 5th trade (or a payout). « Your real net » is not on the first day:
it opens the first time My money is opened after a first payout (27 Oct.; before: nothing opens by itself). Checks: no page error, nothing wider than the window, no English in fr/es.
16 Oct. (brief 00, 1.2-i): no « + » outside the page while there is no account (it opened « Add an account first », in
English); that window in the trader's language; « Trade saved · <the coach> » in the trader's language too.
"""
import json, os, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
MAX_TAPS = 8
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():   # every case signs up a trader: the sign-up limiter is cleared on the dev database
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
TXT = {
  'fr': {'title': 'Trois étapes et tu trades.', 'need': 'Entre ton prénom.', 'gate': 'Avant ton premier trade', 'more': 'Plus d’options', 'wel': 'Bienvenue'},
  'en': {'title': 'Three steps and you’re trading.', 'need': 'Enter your first name.', 'gate': 'Before your first trade', 'more': 'More options', 'wel': 'Welcome'},
  'es': {'title': 'Tres pasos y operas.', 'need': 'Escribe tu nombre.', 'gate': 'Antes de tu primera operación', 'more': 'Más opciones', 'wel': 'Bienvenido'},
}
EN_ONLY = ['Three steps', 'Your first name', 'How long have you been trading', 'More options', 'Your account', 'Your plan', 'Your first trade', 'Welcome', 'optional']
CARDS = "(() => { const d = document.querySelector('#main .nav-dash'); return d ? ['.d-today', '.d-perf', '.d-acc', '.d-cal', '.d-news', '.d-pay', '.d-rank', '.d-quick'].filter((q) => d.querySelector(q)).map((q) => q.slice(3)) : null })()"
WIDE = "document.documentElement.scrollWidth - innerWidth"
PLUS = "[...document.querySelectorAll('[data-act=add-trade]')].filter((e) => !e.closest('#main') && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden').length"
SAVED = {'fr': 'Trade enregistré', 'en': 'Trade saved', 'es': 'Operación guardada'}

def run(p, lang, phone, exp):
  tag = f"{'390' if phone else '1300'}-{lang}"
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], color_scheme='dark' if phone else 'light')
  ctx.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  n = 'fr%d' % int(time.time() * 1000)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  taps = [0]
  def tap(sel, count=True):
    last = None
    for _ in range(6):
      try:
        pg.locator(sel).first.click(timeout=3000); pg.wait_for_timeout(250)
        if count: taps[0] += 1
        return
      except Exception as e: last = e; pg.wait_for_timeout(300)
    raise last
  # 1. the first screen
  pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=20000); pg.wait_for_timeout(700)
  t0 = time.time()
  main = pg.locator('#main .onb').inner_text()
  ok(TXT[lang]['title'] in main and pg.locator('#title').inner_text().strip() == TXT[lang]['wel'], f'{tag} « {TXT[lang]["title"]} », page « {TXT[lang]["wel"]} »')
  ok(pg.locator('#main .onb-steps li').count() == 3, f'{tag} 3 steps: account, plan, first trade')
  first = pg.evaluate("(() => { const f = document.querySelector('form[data-form=account][data-onb]'); return f.firstElementChild && f.firstElementChild.className })()")
  ok(first == 'nav-onb-me', f'{tag} the first name is on top of the form ({first})')
  ok(pg.locator('.nav-dlg.open, .nav-prof.open, aside.nav-prof').count() == 0, f'{tag} no « Complete your profile » window')
  ok(pg.evaluate("!document.querySelector('#askFab') || getComputedStyle(document.querySelector('#askFab')).display === 'none'"), f'{tag} one action: no « Ask Sweep » button on this page')
  ok(pg.locator('.nav-acc-opt').count() == 1 and not pg.locator('.nav-acc-opt').is_visible(), f'{tag} « More options » hidden while the picker asks')
  plus = pg.evaluate(PLUS)
  ok(plus == 0, f'{tag} one action: no « + » in the bars while there is no account ({plus})')
  pg.evaluate("openTicket(null)"); pg.wait_for_timeout(600)   # the « N » key still opens it
  dr = pg.evaluate("(document.querySelector('#drawer.on') || {}).innerText || ''")
  ok(dr and (lang == 'en' or ('Add an account first' not in dr and 'Trades belong' not in dr)), f'{tag} « Add an account first » in the trader\'s language ({dr[:60]!r})')
  pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
  if pg.locator('[data-act=close-drawer]').first.is_visible(): pg.locator('[data-act=close-drawer]').first.click(); pg.wait_for_timeout(400)
  # the guided picker; « Create account » without a first name: asked, nothing created
  tap('form[data-form=account] [data-st-ph0=eval]'); tap('[data-st-firm=apex]')
  if pg.locator('[data-st-type=apex-eod]').count(): tap('[data-st-type=apex-eod]')
  tap('[data-st-size="50000"]')
  more = pg.locator('.nav-acc-opt summary')
  ok(more.is_visible() and TXT[lang]['more'] in more.inner_text(), f'{tag} last step: « {TXT[lang]["more"]} » folded')
  ok(not pg.locator('.nav-acc-opt [name=nav_qty]').is_visible() and not pg.locator('.nav-acc-opt [data-src]').first.is_visible(), f'{tag} count, cost and source under it, not shown')
  if phone: pg.screenshot(path=f'/tmp/fr_{tag}_1_account.png', full_page=False)
  pg.evaluate("document.querySelector('form[data-form=account][data-onb]').requestSubmit()"); pg.wait_for_timeout(600)
  err = pg.locator('.nav-onb-me .nav-prof-err').inner_text()
  ok(err == TXT[lang]['need'] and pg.evaluate("S.accounts.length") == 0, f'{tag} no first name: « {err} », no account created')
  # the first name (1 tap + typing), the experience when he answers it
  pg.locator('[data-onb-fn]').click(); taps[0] += 1; pg.keyboard.type('Léa')
  if exp: tap(f'.nav-onb-me [data-exp="{exp}"]')
  texts = [pg.locator('#main .onb').inner_text()]
  ok(pg.evaluate(WIDE) <= 0, f'{tag} nothing wider than the window ({pg.evaluate(WIDE)})')
  # 2. « Create account » → the plan of the day
  tap('form[data-form=account][data-onb] [type=submit]')
  pg.wait_for_selector('#gSheet.g-plan, #gSheet .g-gate', timeout=8000); pg.wait_for_timeout(500)
  sh = pg.locator('#gSheet').inner_text(); texts.append(sh)
  ml = pg.evaluate("(document.querySelector('#gSheet [data-gp=max_loss]') || {}).value")
  ok(TXT[lang]['gate'] in sh and ml == '1000', f'{tag} the plan opens, its max loss from the account daily limit ({ml})')
  ok(pg.locator('.rn.open').count() == 0 and pg.locator('#tkSlide.open, .nav-am.open, .nav-am-shot.open').count() == 0, f'{tag} no « Your real net », no trade form before the plan')
  if phone: pg.screenshot(path=f'/tmp/fr_{tag}_2_plan.png')
  tap('#gSheet [data-g=bias][data-v=bullish]'); tap('#gSheet [data-g=save-plan]')
  # 3. the trade form
  pg.wait_for_selector('#tkSlide.open, .nav-am.open, .nav-am-shot.open', timeout=8000); secs = time.time() - t0
  ok(taps[0] <= MAX_TAPS + (1 if exp else 0), f'{tag} {taps[0]} taps to the trade form (at most {MAX_TAPS}{" + the optional answer" if exp else ""}), {secs:.0f} s automated')
  if phone: pg.screenshot(path=f'/tmp/fr_{tag}_3_trade.png')
  pg.wait_for_timeout(900)
  j = pg.evaluate("(() => { const d = (window.SweepNextSession && SweepNextSession()) || todayStr(); const j = getDoc('journals', d); return j && j.pre ? [j.pre.bias, j.pre.max_loss] : null })()")
  ok(j == ['bullish', '1000'], f'{tag} the plan is saved ({j})')
  me = pg.evaluate("fetch('api/data',{headers:{'X-Requested-With':'fetch'},credentials:'same-origin'}).then(r=>r.json()).then(j=>j.user&&[j.user.first_name,j.user.experience||null])")
  ok(me == ['Léa', exp or None], f'{tag} first name (and experience) kept on the server ({me})')
  acc = pg.evaluate("S.accounts.map(a=>[a.preset||'', a.rules && a.rules.dll_c])")
  ok(len(acc) == 1 and acc[0][0].startswith('apex') and acc[0][1] == 100000, f'{tag} one Apex EOD 50K account, daily limit $1,000 ({acc})')
  # Today with 0 trades: the routine only
  pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
  if pg.locator('#tkSlide.open').count(): pg.evaluate("closeTicket()"); pg.wait_for_timeout(400)
  ok(pg.locator('.nav-am.open, #tkSlide.open').count() == 0, f'{tag} the trade form closes')
  pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-dash .d-today', timeout=8000); pg.wait_for_timeout(900)
  c0 = pg.evaluate(CARDS)
  ok(c0 == ['today', 'acc'], f'{tag} Today with no trade: the routine and the accounts (SWEEP.md step 3: the accounts from the first account) ({c0})')
  ok(pg.locator('.rn.open').count() == 0, f'{tag} « Your real net » not on the first day')
  if phone: pg.screenshot(path=f'/tmp/fr_{tag}_4_today0.png')   # (27 Oct.) never full_page on a phone context: Chromium drops the touch emulation (maxTouchPoints 0) and the install window never came
  # the first trade → performance, accounts (SWEEP.md step 3: no month card nor news card on Today any more)
  pg.evaluate("put('trades', { id: 'fr-t1', account_id: S.accounts[0].id, instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 12000, pnl_manual: true, date: todayStr(), entry_time: '10:00', exit_time: '10:05' }); render()")
  pg.wait_for_timeout(1200); c1 = pg.evaluate(CARDS)
  ok(c1 == ['today', 'perf', 'acc'], f'{tag} after the 1st trade: performance, accounts; no month, news, money or rank card ({c1})')
  # (audit of 16 Oct.) nothing opens over the coach after the 1st trade: no « Add Sweep to your home screen » on the day of
  # sign-up (nor ever on a computer), no « Go Pro » banner during the trial
  ov = pg.evaluate("[document.querySelectorAll('aside.nav-inst').length, document.querySelectorAll('.sb-nudge').length]")
  ok(ov == [0, 0], f'{tag} after the 1st trade, the day of sign-up: no install window, no Pro banner ({ov})')
  pg.evaluate("for (let i = 2; i <= 5; i++) put('trades', { id: 'fr-t' + i, account_id: S.accounts[0].id, instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 5000, pnl_manual: true, date: todayStr(), entry_time: '1' + i + ':00', exit_time: '1' + i + ':05' }); render()")
  pg.wait_for_timeout(1500); c5 = pg.evaluate(CARDS)
  ok(c5 is not None and 'pay' in c5 and 'rank' not in c5 and 'quick' not in c5, f'{tag} from the 5th trade: My money too; no rank (SWEEP.md step 3), no « Quick access » ({c5})')
  ok(pg.evaluate(WIDE) <= 0, f'{tag} Today: nothing wider than the window')
  # My money opened for the first time, no payout yet: nothing opens (27 Oct., brief A7); after a first payout → « Your real net »
  if pg.locator('.nav-inst.open [data-inst-ok]').count(): pg.locator('.nav-inst.open [data-inst-ok]').click(); pg.wait_for_timeout(400)   # « Add Sweep to your home screen », after the 1st trade
  pg.evaluate("location.hash = '#payouts'"); pg.wait_for_timeout(1500)
  ok(pg.locator('.rn.open').count() == 0, f'{tag} My money without a payout: « Your real net » does not open by itself')
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(500)
  pg.evaluate("put('payouts', { id: 'fr-p1', account_id: S.accounts[0].id, amount_c: 50000, status: 'paid', request_date: todayStr(), payment_date: todayStr() })"); pg.wait_for_timeout(600)
  pg.evaluate("location.hash = '#payouts'"); pg.wait_for_selector('.rn.open [data-rn-per]', timeout=6000)
  ok(pg.evaluate("(S.settings.realnet || {}).auto") == pg.evaluate("todayStr()"), f'{tag} My money opened: « Your real net » offered, once')
  pg.locator('.rn.open [data-rn=later]').click(); pg.wait_for_timeout(700)
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(600); pg.evaluate("location.hash = '#payouts'"); pg.wait_for_timeout(1200)
  ok(pg.locator('.rn.open').count() == 0, f'{tag} not offered again on the next visit')
  # a trade saved with the form: the message and the coach's line in the trader's language; the « + » is back
  ok(pg.evaluate(PLUS) >= 1, f'{tag} with an account, the « + » is back ({pg.evaluate(PLUS)})')
  pg.evaluate("openTicket(null,{manual:true})"); pg.wait_for_timeout(800)
  pg.evaluate("Object.assign(TK,{account:S.accounts[0].id,inst:'NQ',dir:'long',qty:1,entry:21000,exit:21010}); tkRefresh(); window.__toasts=[]; new MutationObserver(()=>{const t=document.getElementById('toast'); if(t&&t.textContent&&!window.__toasts.includes(t.textContent)) window.__toasts.push(t.textContent)}).observe(document.getElementById('toast'),{childList:true,characterData:true,subtree:true}); tkSave()")
  pg.wait_for_timeout(2500); msg = next((m for m in pg.evaluate("window.__toasts") if m.startswith(SAVED[lang])), (pg.evaluate("window.__toasts") or [""])[0])   # (every message: « Level 2 reached » may come right after, 27 Oct.)
  ok(msg.startswith(SAVED[lang]) and (lang == 'en' or 'Trade saved' not in msg), f'{tag} « {SAVED[lang]} » and the coach, in one language ({msg!r})')
  if lang != 'en':
    import re
    bad = [w for w in EN_ONLY if any(re.search(r'(?<![\w’])' + re.escape(w) + r'(?![\w’])', t) for t in texts)]
    ok(not bad, f'{tag} no English on the first screens ({bad})')
  ov = pg.evaluate("[document.querySelectorAll('aside.nav-inst').length, document.querySelectorAll('.sb-nudge').length]")
  ok(ov == [0, 0], f'{tag} « {SAVED[lang]} » with the coach, nothing over it ({ov})')
  # the 2nd day of use: the install window comes after a trade, on a phone only (« What's new » marked as seen: it would take the session's window)
  pg.evaluate("editDoc('settings', 'settings', (r) => { r.news_seen = SweepNews.list.map((n) => n.id) })"); pg.wait_for_timeout(400)
  pg.evaluate("() => { localStorage.setItem('sw.day0', ymdAdd(todayStr(), -1)); S.me.created_at = Math.floor(Date.now() / 1000) - 2 * 86400; sessionStorage.removeItem('sw.modal'); put('trades', { id: 'fr-d2', account_id: S.accounts[0].id, instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 3000, pnl_manual: true, date: todayStr(), entry_time: '15:30', exit_time: '15:35' }); render() }")
  pg.wait_for_timeout(1500); n2 = pg.locator('aside.nav-inst.open').count()
  why = '' if n2 == (1 if phone else 0) else pg.evaluate("""JSON.stringify({ coarse: matchMedia('(pointer: coarse)').matches, touch: navigator.maxTouchPoints, w: innerWidth, day0: localStorage.getItem('sw.day0'), today: todayStr(),
    created: S.me && S.me.created_at, modal: sessionStorage.getItem('sw.modal'), sugg: localStorage.getItem('sw.sugg'), shown: localStorage.getItem('sw.installShown'),
    open: [...document.querySelectorAll('.open, [role=dialog]')].map((e) => e.id || e.className).slice(0, 6), real: S.trades.filter((x) => !x.demo).length })""")   # (27 Oct.) what kept it closed
  ok(n2 == (1 if phone else 0), f'{tag} the 2nd day of use, after a trade: the install window {"opens" if phone else "never opens on a computer"} ({n2} {why})')
  if n2: pg.locator('.nav-inst.open [data-inst-ok]').click(); pg.wait_for_timeout(300)
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  br.close()

def topstep(p, lang, phone):
  """(audit of 16 Oct.) a Topstep Combine 50K without the daily limit option ($2,000 drawdown): the first plan's max loss is
  prefilled with half the drawdown, $1,000 (before: empty, and the plan refused)"""
  tag = f"{'390' if phone else '1300'}-{lang} Topstep"
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'ts%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  pg.evaluate("""() => { put('firms', { id: 'tf', name: 'Topstep' }); put('accounts', { id: 'ta', firm_id: 'tf', name: 'Trading Combine 50K', starting_balance_c: 5000000, status: 'active', phase: 'eval', created_on: todayStr(), rules: { dd_c: 200000, dd_type: 'eod', target_c: 300000 } }); }""")
  pg.wait_for_timeout(800)
  pg.evaluate("SweepGame.openPlan(null, { then: () => { window.__then = 1 } })"); pg.wait_for_selector('#gSheet [data-g=save-plan]', timeout=8000); pg.wait_for_timeout(500)
  ml = pg.evaluate("(document.querySelector('#gSheet [data-gp=max_loss]') || {}).value")
  ok(ml == '1000', f'{tag} no daily limit: the max loss starts at half the drawdown, $1,000 ({ml!r})')
  pg.locator('#gSheet [data-g=bias][data-v=bullish]').click(); pg.wait_for_timeout(200); pg.locator('#gSheet [data-g=save-plan]').click(); pg.wait_for_timeout(1200)
  j = pg.evaluate("(() => { const d = (SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr(); const j = getDoc('journals', d); return [j && j.pre && j.pre.max_loss, !!window.__then] })()")
  ok(j == ['1000', True], f'{tag} the plan is saved and the trade form comes next ({j})')
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  br.close()

with sync_playwright() as p:
  for lang, phone, exp in (('fr', True, ''), ('en', False, ''), ('es', True, 'lt1')):
    print(f"— {'phone' if phone else 'computer'} {lang}")
    run(p, lang, phone, exp)
  for lang, phone in (('es', False), ('fr', True)):
    topstep(p, lang, phone)
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
