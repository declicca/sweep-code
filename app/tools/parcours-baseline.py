"""
Sweep — the journey's baseline, moment M1 (SWEEP.md, step 0): a new trader goes through the app as it is, with real taps,
from the sign-up screen to (a) the plan saved (the risk allowed today is on screen) and (b) the first trade saved
(« Trade saved » with the coach), without a screenshot (« Enter manually »), with one (the test screenshot), and with
« No screenshot? Enter your P&L » (SWEEP.md step 2; BASELINE_PATHS="manual shot" for the app before it); and the manual
form with the entry price forgotten first (27 Oct.): the cursor lands in the field, the trade is still saved. And a current
trader's day (27 Oct., brief « daily loop »): an account and 10 trades, then the plan, 2 trades by screenshot, closing the day.
Counts the taps, the fields typed and the screens, and the robot's time (its own pauses taken out). A rough human time is
given too: 2.5 s a tap, 5 s a field (the same scale as the journey audit of 16 Oct.).
  sh tools/sync.sh /tmp/gpar && DEST=/tmp/gpar PORT=8495 sh tools/run.sh python3 tools/parcours-baseline.py http://127.0.0.1:8495 [--json out.json]
Out of the deploy (tools/). Each run signs up its own traders on the served copy (the sign-up limiter is cleared there).
"""
import json, os, sqlite3, sys, time
from playwright.sync_api import sync_playwright

B = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'http://127.0.0.1:8095'
OUT = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else ''
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests', 'fixture-shot.png')
# a current trader's day: two real one-trade screenshots (read by the test answers of Sweep AI, tests/samples/shot-ai-mock.json)
DAY_SHOTS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests', 'samples', f) for f in ('shot-topstepx-one-trade.png', 'shot-tradesea-one-trade.png')]
SAVED = {'fr': 'Trade enregistré', 'en': 'Trade saved', 'es': 'Operación guardada'}
TAP_S, FIELD_S = 2.5, 5.0


def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass


def run(p, lang, phone, exp, path):
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  c = {'taps': 0, 'fields': 0, 'screens': [], 'pause': 0.0}

  def wait(ms):
    t = time.time(); pg.wait_for_timeout(ms); c['pause'] += time.time() - t

  def tap(sel):
    el = pg.locator(sel).first; el.wait_for(state='visible', timeout=10000)
    el.tap() if phone else el.click()
    c['taps'] += 1; wait(250)

  def field(sel, text):   # a tap into the field, then the typing
    tap(sel); pg.keyboard.press('ControlOrMeta+a'); pg.keyboard.type(text); c['fields'] += 1

  def screen(name, sel):
    pg.wait_for_selector(sel, timeout=15000); c['screens'].append(name)

  mark = {}
  def at(k): mark[k] = {'taps': c['taps'], 'fields': c['fields'], 'screens': len(c['screens']), 'robot_s': round(time.time() - t0 - c['pause'], 1)}

  pg.goto(B + '/?signup=1'); t0 = time.time()
  screen('signup', '#email')
  field('#email', 'base%d@t.dev' % int(time.time() * 1000)); field('#password', 'Testpass123!')
  wait(4500)   # the sign-up refuses a form filled faster than a human
  tap('#go')
  screen('welcome', '[data-onb-fn]'); wait(700)
  field('[data-onb-fn]', 'Léa' if lang != 'en' else 'Alex')
  tap(f'[data-exp={exp}]')
  tap('form[data-form=account] [data-st-ph0=eval]'); tap('[data-st-firm=topstep]')
  if pg.locator('[data-st-type^=topstep]').count(): tap('[data-st-type^=topstep]')
  tap('[data-st-size="50000"]')
  tap('form[data-form=account][data-onb] [type=submit]')
  screen('plan', '#gSheet [data-g=save-plan]'); wait(500)
  risk = pg.evaluate("(document.querySelector('#gSheet [data-gp=max_loss]') || {}).value || ''")
  tap('#gSheet [data-g=bias][data-v=bullish]'); tap('#gSheet [data-g=save-plan]')
  at('plan')
  screen('trade-sheet', '.nav-am.open, #tkSlide.open'); wait(600)
  pg.evaluate("window.__toasts = []; new MutationObserver(() => { const t = document.getElementById('toast'); if (t && t.textContent && !window.__toasts.includes(t.textContent)) window.__toasts.push(t.textContent) }).observe(document.getElementById('toast'), { childList: true, characterData: true, subtree: true })")   # every message (a celebration can follow « Trade saved »)
  forgot = None
  if path == 'noshot':   # (SWEEP.md step 2) « No screenshot? Enter your P&L »: the same sheet, the net P&L focused at once
    tap('.nav-am.open [data-am=no-shot]'); pg.wait_for_selector('.nav-am.open [data-am-f=net]', timeout=8000)
    focused = pg.evaluate("document.activeElement && document.activeElement.dataset && document.activeElement.dataset.amF === 'net'")
    if not focused: tap('.nav-am.open [data-am-f=net]')
    pg.keyboard.type('250'); c['fields'] += 1
    tap('.nav-am.open [data-am-seg=dir][data-v=long]'); tap('.nav-am.open [data-am=save]')
  elif path in ('manual', 'forgot'):
    tap('[data-am=to-manual]'); screen('manual-form', '#tkSlide.open [data-act=tk-save]'); wait(600)
    tap('#tkSlide [data-act=tk-dir][data-v=long]')
    if path == 'forgot':   # (27 Oct., brief A1) « Save » without the entry price: the cursor lands in the field, then the trade is saved
      tap('#tkSlide [data-act=tk-save]'); wait(700)
      forgot = pg.evaluate("document.activeElement === document.querySelector('#tkSlide [data-tk=entry]') && !!document.querySelector('#tkSlide [data-tk-miss]')")
      pg.keyboard.type('21000.00'); c['fields'] += 1
      field('#tkSlide [data-tk=exit]', '21010.00'); tap('#tkSlide [data-act=tk-save]')
    entry = float(pg.evaluate("(document.querySelector('#tkSlide [data-tk=entry]') || {}).value || '0'") or 0) or 21000
    if path == 'manual':
      field('#tkSlide [data-tk=entry]', '%.2f' % entry); field('#tkSlide [data-tk=exit]', '%.2f' % (entry + 10))
      tap('#tkSlide [data-act=tk-save]')
  else:
    if phone:
      with pg.expect_file_chooser() as fc: tap('label.nav-am-drop')
      fc.value.set_files(SHOT); c['taps'] += 1   # the photo picked in the phone's picker
    else:
      pg.locator('label.nav-am-drop input[type=file]').set_input_files(SHOT); c['taps'] += 2   # « choose a file », then the file
    screen('shot-read', '.nav-am.open [data-am=save]'); wait(1500)
    if not pg.evaluate("(document.querySelector('.nav-am.open [data-am-f=net]') || {}).value"): field('.nav-am.open [data-am-f=net]', '250')
    tap('.nav-am.open [data-am-seg=dir][data-v=long]'); tap('.nav-am.open [data-am=save]')
  for _ in range(40):
    saved = next((m for m in pg.evaluate("window.__toasts") if m.startswith(SAVED[lang])), '')
    if saved: break
    wait(250)
  at('trade')
  n = pg.evaluate("S.trades.filter(t => !t.demo).length")
  br.close()
  human = lambda m: round(m['taps'] * TAP_S + m['fields'] * FIELD_S)
  for k in mark: mark[k]['human_s'] = human(mark[k])
  return {'case': f"{'390' if phone else '1300'}-{lang}-{path}", 'experience': exp, 'risk_allowed_shown': risk, 'plan': mark.get('plan'), 'trade': mark.get('trade'),
          'trade_saved': saved.startswith(SAVED[lang]) and n == 1 and forgot is not False, 'forgot_focused': forgot, 'toast': saved[:120], 'screens': c['screens'], 'errors': errs[:3]}



def run_day(p, lang, phone):
  """(27 Oct., brief « daily loop ») a current trader — an account and 10 trades already — through one day: the plan, 2 trades
  by screenshot, closing the day (the review). Taps, fields and screens of each part, and of the whole day."""
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'day%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Sam', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  c = {'taps': 0, 'fields': 0, 'screens': [], 'pause': 0.0}
  def wait(ms):
    t = time.time(); pg.wait_for_timeout(ms); c['pause'] += time.time() - t
  def tap(sel):
    el = pg.locator(sel).first; el.wait_for(state='visible', timeout=10000)
    el.tap() if phone else el.click()
    c['taps'] += 1; wait(250)
  def field(sel, text):
    tap(sel); pg.keyboard.press('ControlOrMeta+a'); pg.keyboard.type(text); c['fields'] += 1
  def screen(name, sel):
    pg.wait_for_selector(sel, timeout=15000); c['screens'].append(name)
  def seen(sel): return pg.locator(sel).count() > 0 and pg.locator(sel).first.is_visible()
  pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main', timeout=15000); wait(2000)
  pg.evaluate("""() => { put('accounts', { id: 'day-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } });
    let d = todayStr(), n = 0; while (n < 10) { d = ymdAdd(d, -1); const w = new Date(d + 'T12:00:00').getDay(); if (w === 0 || w === 6) continue;
      put('trades', { id: 'day-h' + n, account_id: 'day-a', instrument: 'MNQ', direction: n % 2 ? 'short' : 'long', contracts: 1, entry: 1, exit: 2, pnl_c: n % 3 ? 12000 : -8000, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:20' }); n++; } }""")
  wait(1500); pg.reload(); pg.wait_for_selector('#main .nav-rt', timeout=15000); wait(1500)
  market = pg.evaluate("!!(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.market)")
  if not market: br.close(); return {'case': f"{'390' if phone else '1300'}-{lang}-day", 'skipped': 'market closed (the game clock)'}
  t0 = time.time(); mark = {}
  def at(k): mark[k] = {'taps': c['taps'], 'fields': c['fields'], 'screens': len(c['screens']), 'robot_s': round(time.time() - t0 - c['pause'], 1)}
  # 1. the plan
  tap('#main .nav-rt [data-rt=plan]'); screen('plan', '#gSheet.g-pm [data-pm-screen], #gSheet [data-g=save-plan]'); wait(500)
  mode = pg.evaluate("(document.querySelector('#gSheet.g-pm [data-pm-screen]') || { dataset: {} }).dataset.pmScreen || 'short'")
  if mode == 'express':
    tap('#gSheet [data-q="X_bias"][data-v="bullish"]')
    if not pg.evaluate("!!document.querySelector('#gSheet [data-pm=inst-pick].on')") and seen('#gSheet [data-pm=inst-pick]'): tap('#gSheet [data-pm=inst-pick]')
    field('#gSheet [data-pmf="X_levels"]', 'PDH 21000'); field('#gSheet [data-pmf="X_plan"]', 'Cassure du PDH')
    if not pg.input_value('#gSheet [data-pmf="max_loss"]'): field('#gSheet [data-pmf="max_loss"]', '500')
    tap('#gSheet [data-pm="next"]'); screen('plan-sheet', '#gSheet [data-pm="save"]'); tap('#gSheet [data-pm="save"]')
  elif mode == 'short':
    tap('#gSheet [data-g=bias][data-v=bullish]'); tap('#gSheet [data-g=save-plan]')
  wait(1200); at('plan'); p0 = dict(mark['plan'])
  # 2. two trades by screenshot
  pg.evaluate("window.__toasts = []; new MutationObserver(() => { const t = document.getElementById('toast'); if (t && t.textContent && !window.__toasts.includes(t.textContent)) window.__toasts.push(t.textContent) }).observe(document.getElementById('toast'), { childList: true, characterData: true, subtree: true })")
  saved = 0; n0 = pg.evaluate("S.trades.filter((t) => !t.demo).length")
  for i in range(2):
    if pg.locator('#gSheet').count(): pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); wait(400)
    if pg.evaluate("location.hash") != '#dashboard': pg.evaluate("location.hash = '#dashboard'"); wait(800)
    tap('#bottomnav .plus' if phone else '.nav-addtop'); screen('trade-sheet', '.nav-am.open'); wait(500)
    if phone:
      with pg.expect_file_chooser() as fc: tap('label.nav-am-drop')
      fc.value.set_files(DAY_SHOTS[i]); c['taps'] += 1
    else:
      pg.locator('label.nav-am-drop input[type=file]').set_input_files(DAY_SHOTS[i]); c['taps'] += 2
    screen('shot-read', '.nav-am.open [data-am=save]'); wait(2500)
    if not pg.evaluate("(document.querySelector('.nav-am.open [data-am-f=net]') || {}).value"): field('.nav-am.open [data-am-f=net]', '150')   # not read: typed
    if not pg.evaluate("!!document.querySelector('.nav-am.open [data-am-seg=dir].on')"): tap('.nav-am.open [data-am-seg=dir][data-v=long]')
    tap('.nav-am.open [data-am=save]'); wait(1500)
    pg.evaluate("(n) => { const t = S.trades.filter((x) => !x.demo).slice(n).find((x) => x.date !== todayStr()); if (t) editDoc('trades', t.id, (d) => { d.date = todayStr(); }) }", n0)   # (the test screenshots carry their own date: put on today, as a real one would be)
    if seen('#gSheet [data-pm=link]'): c['screens'].append('scenario'); tap('#gSheet [data-pm=link]')   # « Which scenario of your sheet? »
    wait(600)
    if pg.evaluate("location.hash").startswith('#trade/'): c['screens'].append('trade-page')
  saved = pg.evaluate("S.trades.filter((t) => !t.demo).length") - n0   # (the screenshots carry their own date)
  at('trades')
  # 3. closing the day
  if pg.evaluate("location.hash") != '#dashboard': tap('a[href="#dashboard"]'); wait(800)
  tap('#main .nav-rt [data-rt=review]'); screen('review', '#gSheet [data-g=save-review]'); wait(500)
  for sel in ('[data-g=r-followed][data-v=yes]', '[data-g=r-score][data-v="4"]', '[data-g=r-grade][data-v=B]'):   # only a question with no answer yet (filled in from the day since 27 Oct.)
    grp = sel.split(']')[0] + ']'
    if seen('#gSheet ' + sel) and not pg.evaluate("(g) => !!document.querySelector(g + '.on')", '#gSheet ' + grp): tap('#gSheet ' + sel)
  for k in range(pg.locator('#gSheet [data-bal-same]').count()): tap(f'#gSheet [data-bal-same] >> nth={k}')   # « Your balance on Topstep? » « It matches » (brief « pertes oubliées », step 2)
  tap('#gSheet [data-g=save-review]'); wait(1200)
  closed = pg.evaluate("(() => { const j = getDoc('journals', todayStr()); return !!(j && j.post && (j.post.reviewed_at || j.post.followed)) })()")
  at('day')
  br.close()
  part = lambda a, b: {k: mark[b][k] - (mark[a][k] if a else 0) for k in ('taps', 'fields', 'screens')}
  return {'case': f"{'390' if phone else '1300'}-{lang}-day", 'plan_mode': mode, 'plan': part(None, 'plan'), 'trades': part('plan', 'trades'), 'close': part('trades', 'day'),
          'day': mark['day'], 'screens': c['screens'], 'trades_saved': saved, 'day_closed': closed, 'trade_saved': saved == 2 and closed, 'errors': errs[:3]}

rows = []
with sync_playwright() as p:
  for lang, phone, exp in (('fr', True, 'new'), ('en', False, 'gt1')):
    for path in ([p for p in ('manual', 'shot', 'noshot', 'forgot') if p in os.environ.get('BASELINE_PATHS', 'manual shot noshot forgot').split()]):
      r = run(p, lang, phone, exp, path); rows.append(r)
      pl, tr = r['plan'], r['trade']
      print(f"{r['case']:<18} plan: {pl['taps']} taps, {pl['fields']} fields, {pl['screens']} screens, ~{pl['human_s']} s human ({pl['robot_s']} s robot), risk {r['risk_allowed_shown'] or '—'} | "
            f"trade: {tr['taps']} taps, {tr['fields']} fields, {tr['screens']} screens, ~{tr['human_s']} s human ({tr['robot_s']} s robot) | saved {r['trade_saved']} {'' if not r['errors'] else r['errors']}")
  if 'day' in os.environ.get('BASELINE_PATHS', 'manual shot noshot forgot day').split():
    for lang, phone in (('fr', True), ('en', False)):
      r = run_day(p, lang, phone); rows.append(r)
      if r.get('skipped'): print(f"{r['case']:<18} skipped: {r['skipped']}"); r['trade_saved'] = True; r['errors'] = []; continue
      print(f"{r['case']:<18} day: {r['day']['taps']} taps, {r['day']['fields']} fields, {r['day']['screens']} screens (plan {r['plan']['taps']} [{r['plan_mode']}], 2 trades {r['trades']['taps']}, closing {r['close']['taps']}) | saved {r['trades_saved']}, closed {r['day_closed']} {'' if not r['errors'] else r['errors']}")
if OUT:
  with open(OUT, 'w') as f: json.dump({'base': B, 'at': time.strftime('%Y-%m-%d %H:%M'), 'rows': rows}, f, ensure_ascii=False, indent=1)
sys.exit(0 if all(r['trade_saved'] and not r['errors'] for r in rows) else 1)
