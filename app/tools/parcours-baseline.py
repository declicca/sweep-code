"""
Sweep — the journey's baseline, moment M1 (SWEEP.md, step 0): a new trader goes through the app as it is, with real taps,
from the sign-up screen to (a) the plan saved (the risk allowed today is on screen) and (b) the first trade saved
(« Trade saved » with the coach), without a screenshot (« Enter manually ») and with one (the test screenshot); and the
manual form with the entry price forgotten first (27 Oct.): the cursor lands in the field, the trade is still saved.
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
  if path in ('manual', 'forgot'):
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


rows = []
with sync_playwright() as p:
  for lang, phone, exp in (('fr', True, 'new'), ('en', False, 'gt1')):
    for path in ('manual', 'shot', 'forgot'):
      r = run(p, lang, phone, exp, path); rows.append(r)
      pl, tr = r['plan'], r['trade']
      print(f"{r['case']:<18} plan: {pl['taps']} taps, {pl['fields']} fields, {pl['screens']} screens, ~{pl['human_s']} s human ({pl['robot_s']} s robot), risk {r['risk_allowed_shown'] or '—'} | "
            f"trade: {tr['taps']} taps, {tr['fields']} fields, {tr['screens']} screens, ~{tr['human_s']} s human ({tr['robot_s']} s robot) | saved {r['trade_saved']} {'' if not r['errors'] else r['errors']}")
if OUT:
  with open(OUT, 'w') as f: json.dump({'base': B, 'at': time.strftime('%Y-%m-%d %H:%M'), 'rows': rows}, f, ensure_ascii=False, indent=1)
sys.exit(0 if all(r['trade_saved'] and not r['errors'] for r in rows) else 1)
