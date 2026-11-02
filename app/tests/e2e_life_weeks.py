"""
Sweep — the app over time (1 Nov., brief « L'app dans le temps »), Playwright:
  python3 tests/e2e_life_weeks.py http://127.0.0.1:8095
Two traders live 13 market days in the app, the clock advanced: for each moment of each day (8:45, 10:20, 16:40 New York time) a
copy of the server is started with its game clock pinned there (SWEEP_GAME_NOW, port + 7, same database), and the pages' clock
is set to the same time (Playwright clock). The days start the Monday after the real date: the sign-up (real time) comes first.
 - Sam (390 touch, French, dark): never plans nor reviews; a tilt day (two losses, −$1,050: room $950 of $2,000), two days away,
   two green days, then the $3,000 target.
 - Léo (1300, English, light): a plan and a review each day (« Use yesterday's plan » once, through the express plan), his
   rule for tomorrow written once, the gameplan's mission ticked each day.
Checks:
 A1 no « A full week inside your plan » for Sam (trades without a plan); A4 the « risk allowed » never above the last max loss
 chosen (the drawdown room only as a « limit »); B1 no missions-to-catch-up counter, « Day N » = missions done; C2 no window between
 the first trade and the review; C1 the coach never says the same sentence 3 days in a row; E1 one reward toast a day at most,
 never before the review; D1 the caution mode the morning after the tilt, gone after 2 green days; also A2 (the eval text and its
 room line), A3 (« Day complete »), D2 (one tap, then saved with the bias and max loss only), D4 (the rule of the day in « Now »),
 F (« right after a loss », « waiting for your firm »), B2 (no announcement before the sign-up, nothing counted on the bell),
 B3 (the strip starts at the sign-up). No page error, nothing wider than the window.
"""
import datetime as dt, json, os, random, re, signal, sqlite3, subprocess, sys, time, urllib.request
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APPDIR = os.path.dirname(os.path.dirname(DB)) if os.environ.get('SWEEP_TEST_DB') else '/tmp/g'   # the served copy
P1 = int(B.rsplit(':', 1)[1]) + 7; B1 = f'http://127.0.0.1:{P1}'
NY = ZoneInfo('America/New_York')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what, flush=True)

SRV = [None]
def server_at(moment):
  """the server, its game clock pinned to `moment` (New York, « YYYY-MM-DD HH:MM »)"""
  stop()
  try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=1); raise RuntimeError(f'port {P1} is already served: stop that server first')
  except RuntimeError: raise
  except Exception: pass
  env = dict(os.environ, SWEEP_GAME_NOW=moment, PHP_CLI_SERVER_WORKERS='4')
  SRV[0] = subprocess.Popen(['php', '-S', f'127.0.0.1:{P1}', 'router.php'], cwd=APPDIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
  for _ in range(60):
    if SRV[0].poll() is not None: raise RuntimeError(f'port {P1} already in use: the pinned server could not start')   # (never another copy answering)
    try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=2); return
    except Exception: time.sleep(0.15)
  raise RuntimeError('pinned server did not start')
def stop():
  p = SRV[0]
  if not p: return
  # the workers first (PHP_CLI_SERVER_WORKERS: with the parent gone first they keep the port, and answer with their old clock), then the server
  kids = subprocess.run(['pgrep', '-P', str(p.pid)], capture_output=True, text=True).stdout.split()
  for k in kids:
    try: os.kill(int(k), signal.SIGTERM)
    except (ProcessLookupError, PermissionError): pass
  try: p.terminate()
  except ProcessLookupError: pass
  p.wait(); SRV[0] = None
  for _ in range(80):   # the port free again: the next server must be the only one answering
    try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=1); time.sleep(0.1)
    except Exception: return
  # still answered: what is left of this test's own server on its port (P1 is this test's), then the check again
  subprocess.run(['pkill', '-f', f'php -S 127.0.0.1:{P1} '])
  time.sleep(0.5)
  try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=1); raise RuntimeError(f'port {P1} still answers after the server stopped')
  except RuntimeError: raise
  except Exception: return
def at(day, hm): return dt.datetime.strptime(f'{day} {hm}', '%Y-%m-%d %H:%M').replace(tzinfo=NY)   # (the clock takes a datetime: a number is read as seconds)
def epoch(day, hm): return int(at(day, hm).timestamp())

# the days: the Monday after the real date (New York), weekdays
real = (dt.datetime.now(NY) + dt.timedelta(hours=6)).date()   # the session of the sign-up (18:00 ET or later: the next day)
d0 = real + dt.timedelta(days=(7 - real.weekday()) % 7 or 7)   # next Monday
DAY0 = (d0 - dt.timedelta(days=1)).isoformat()                 # the Sunday before: the sign-up
WEEKDAYS = [(d0 + dt.timedelta(days=i)).isoformat() for i in range(28) if (d0 + dt.timedelta(days=i)).weekday() < 5]
N = int(os.environ.get('LW_DAYS') or 13)   # market days lived (LW_DAYS: fewer, to look at the first ones)
# Sam's day (index of market day) → net P&L of his trades in $ (None = away): the tilt on day 6 (two losses, the second right
# after the first), away 7 and 8, green 9 and 10, the target reached on 11 (+$3,050 in all)
SAM = {0: [150], 1: [120], 2: [-200], 3: [180], 4: [100], 5: [150, 100], 6: [-600, -450], 7: None, 8: None, 9: [900], 10: [1250], 11: [1350], 12: [100]}
TILT, TARGET = 6, 11
LEO = {i: ([200] if i % 3 else [150, -100]) for i in range(N)}
LEO[5] = [-200, -150]   # off his plan (shorts against a long bias): « Day complete » still, never « successful »

# what the pages log: a window that opens (and who opened it), the toasts
INIT = r"""(() => {
  window.__swLog = []; window.__swMoment = ''; window.__swUser = 0;
  const OPEN = '.nav-inst.nav-dlg, .nav-pass.nav-dlg, #gSheet, .g-sweep, #gOb, .nt-modal, .g-wnsheet, aside.nav-dlg';
  const log = (k, v) => window.__swLog.push({ k, v: String(v || '').replace(/\s+/g, ' ').trim().slice(0, 140), m: window.__swMoment, u: window.__swUser });
  const seen = new WeakSet();
  new MutationObserver((ms) => {
    for (const m of ms) {
      if (m.target && m.target.id === 'toast' || (m.target && m.target.parentElement && m.target.parentElement.id === 'toast')) { const t = document.getElementById('toast'); if (t && t.textContent.trim()) log('toast', t.textContent); }
      for (const n of m.addedNodes || []) {
        if (!(n instanceof Element)) continue;
        if (n.matches('.gm-sumtoast, .g-xpf')) log('toast', n.textContent);
        if (n.matches('.g-sweep')) log('toast', 'SWEEP ' + n.textContent);
        const o = n.matches(OPEN) ? n : null;
        if (o && !seen.has(o)) { seen.add(o); log('open', (o.className || o.id) + ' | ' + o.textContent.slice(0, 80)); }
      }
    }
  }).observe(document, { childList: true, subtree: true, characterData: true });   // (the document: its element does not exist yet)
})()"""
REWARD = re.compile(r'\bXP\b|[Bb]adge|[Ii]nsignia|Level \d|Niveau \d|Nivel \d|[Ss]treak|Racha|[Mm]ission|[Mm]isi[oó]n|Unlocked|Débloqué|Desbloqueado|[Bb]oss|[Jj]efe|Gameplan ·|Parcours ·|Recorrido ·|nouveaut|novedad|new · See|Day complete|Journée complète|Día completado|SWEEP|full week|semaine entière|semana entera|[Rr]ank|[Rr]ang\b|[Ss]eason|[Ss]aison|[Cc]hest|[Cc]offre')
NOW = "(() => { const n = document.querySelector('#main .nav-rt .nav-now'); return n ? n.innerText.replace(/\\s+/g, ' ').trim() : '' })()"
NOWV = "(() => { const b = document.querySelector('#main .nav-now[data-now=before]'); if (!b) return null; const v = b.querySelector('.nav-now-v'); return [b.querySelector('.nav-now-l b').textContent.trim(), v ? v.textContent : ''] })()"
COACH = "(() => { const c = document.querySelector('#main .co-today'); if (!c) return ''; const l = [...c.querySelectorAll('.co-ses')].pop(); return l ? l.textContent.replace(/\\s+/g, ' ').trim() : '' })()"
FIX = "(() => { const c = document.querySelector('#main .co-today .co-fix'); return c ? c.textContent.replace(/\\s+/g, ' ').trim() : '' })()"
WIDE = """(() => { let w = 0, who = ''; for (const e of document.querySelectorAll('#main *, #gSheet *, .nav-dlg *')) { if (!e.getClientRects().length) continue;
  const r = e.getBoundingClientRect().right - innerWidth; if (r <= w) continue;
  let clip = false; for (let p = e.parentElement; p && !p.matches('#main, #gSheet, .nav-dlg, body'); p = p.parentElement) if (getComputedStyle(p).overflowX !== 'visible') { clip = true; break; }   // (inside a scroller: the strip, the chips)
  if (!clip) { w = r; who = (e.className || e.tagName) + ' ' + (e.textContent || '').trim().slice(0, 30); } } return w > 1 ? who + ' +' + Math.round(w) : '' })()"""
amount = lambda s: int(re.sub(r'[^\d]', '', s or '') or 0)

class Trader:
  def __init__(s, br, name, lang, w, phone, theme):
    s.name, s.lang, s.phone = name, lang, phone
    loc = {'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang]
    s.ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale=loc, color_scheme=theme, timezone_id='America/New_York')
    s.ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')) } catch (e) {}" % lang)
    s.ctx.add_init_script(INIT)
    s.ctx.clock.install(time=at(DAY0, '12:00'))
    s.pg = None; s.errs = []; s.log = []
    s.morning, s.after, s.risk, s.toasts = [], [], [], {}
  def open(s, day, hm, moment, wait=True):
    s.ctx.clock.set_system_time(at(day, hm))
    if s.pg: s.collect(); s.pg.close()
    s.pg = s.ctx.new_page(); s.pg.on('pageerror', lambda e: s.errs.append(str(e)[:160]))
    s.pg.goto(B1 + '/#dashboard'); s.pg.evaluate("(m) => { window.__swMoment = m }", f'{day} {moment}')
    if not wait: s.pg.wait_for_timeout(1500); return
    try: s.pg.wait_for_selector('#main .nav-rt:not(.ph)', timeout=15000); s.pg.wait_for_selector('#main .co-today', timeout=4000)
    except Exception: pass
    s.pg.wait_for_timeout(1000)
  def collect(s):
    try: s.log += s.pg.evaluate("window.__swLog || []"); s.pg.evaluate("window.__swLog = []")
    except Exception: pass
  def ev(s, js, arg=None): return s.pg.evaluate(js, arg) if arg is not None else s.pg.evaluate(js)
  def put(s, col, doc): s.ev("([c, d]) => put(c, d)", [col, doc])
  def today(s, wait=900):
    s.pg.wait_for_timeout(wait); s.ev("location.hash = '#dashboard'; render()")
    try: s.pg.wait_for_selector('#main .nav-rt:not(.ph)', timeout=10000)
    except Exception: pass
    s.pg.wait_for_timeout(900)

def sign_up(t, first):
  r = t.ctx.request.post(B1 + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'lw%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status not in (200, 201): raise RuntimeError('sign-up refused: %s' % r.status)
  t.ctx.request.post(B1 + '/api/me/profile', data=json.dumps({'first_name': first, 'experience': 'new'}), headers=H)
  t.open(DAY0, '12:00', 'signup', wait=False)   # (no account yet: the welcome page)
  t.put('accounts', {'id': 'lw-a', 'name': 'Topstep 50K', 'status': 'active', 'phase': 'eval', 'money_type': 'eval', 'starting_balance_c': 5000000, 'created_on': DAY0,
                     'rules': {'dd_c': 200000, 'dd_type': 'eod', 'dd_lock': True, 'target_c': 300000}})
  # the plan of the sign-up (30 seconds: the bias and the max loss)
  t.put('journals', {'id': DAY0, 'pre': {'bias': 'bullish', 'max_loss': '500', 'saved_at': epoch(DAY0, '12:00')}})
  t.pg.wait_for_timeout(1500)
  t.ctx.request.post(B1 + '/api/game/gameplan/start', data=json.dumps({'track': 'B'}), headers=H)

def trade(t, day, k, pnl, hm, direction='long'):
  h, m = int(hm[:2]), int(hm[3:])
  t.put('trades', {'id': f'lw-{t.name}-{day}-{k}', 'account_id': 'lw-a', 'instrument': 'MNQ', 'direction': direction, 'contracts': 1, 'entry': 1, 'exit': 2,
                   'pnl_c': pnl * 100, 'pnl_manual': True, 'date': day, 'entry_time': hm, 'exit_time': hm, 'session_date': True})

def gpline(t):
  return t.ev("(() => { const g = document.getElementById('gpLine'); return g ? g.innerText.replace(/\\s+/g, ' ') : '' })()")

with sync_playwright() as p:
  br = p.chromium.launch()
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
  server_at(f'{DAY0} 12:00')
  sam = Trader(br, 'sam', 'fr', 390, True, 'dark'); leo = Trader(br, 'leo', 'en', 1300, False, 'light')
  sign_up(sam, 'Sam'); sign_up(leo, 'Léo')
  for t in (sam, leo):
    bell = t.ev("fetch('api/notifications', {headers: {'X-Requested-With': 'fetch'}}).then((r) => r.json())")
    ok(not [n for n in bell.get('items', []) if n.get('type') == 'news'] and not bell.get('unread'), f'{t.name} B2 the sign-up: no announcement in the bell, nothing on its badge ({bell.get("unread")})')
  days, i = [], 0
  for day in WEEKDAYS:
    if len(days) >= N: break
    server_at(f'{day} 08:45')
    st = sam.ctx.request.get(B1 + '/api/game/today', headers=H).json()
    if not (st.get('today') or {}).get('market'): continue   # a market holiday: the next weekday
    i = len(days); days.append(day)
    # ── 8:45 ──
    for t in (sam, leo):
      if t is sam and SAM[i] is None: continue   # away
      t.open(day, '08:45', 'morning')
      if t.phone and i in (0, 2):   # the morning is free for the app's suggestions (5 s after it opens): the trader answers « Later »
        t.pg.wait_for_timeout(4300)
        if t.pg.locator('[data-inst-later]').count(): t.ev("window.__swUser = 1"); t.pg.locator('[data-inst-later]').click(); t.pg.wait_for_timeout(500); t.ev("window.__swUser = 0")
      txt = t.ev(NOW); v = t.ev(NOWV)
      if v: t.risk.append((i, v[0], amount(v[1])))
      gl = ''
      dn = t.ev("fetch('api/game/gameplan', {headers: {'X-Requested-With': 'fetch'}}).then((r) => r.json()).then((s) => Object.keys(s.done || {}).length)")
      for _ in range(30):   # (the line kept in the browser is drawn first, the gameplan's state a moment later)
        gl = gpline(t); mN = re.search(r'(?:Mission|Misión) (\d+)', gl or '')   # (2 Nov., analyse débutant C2: « Mission N of 90 », the mission he is on)
        if mN and int(mN.group(1)) == max(1, dn): break
        t.pg.wait_for_timeout(200)
      ok('rattraper' not in t.ev("document.getElementById('main').innerText") and 'catch up' not in t.ev("document.getElementById('main').innerText") and t.ev("document.querySelectorAll('#main .gp-ln-late').length") == 0,
         f'{t.name} {day} B1 no counter of missions to catch up ({gl[:60]!r})')
      ok(bool(mN) and int(mN.group(1)) in (max(1, dn), dn + 1), f'{t.name} {day} B1 « Mission N of 90 » = the mission he is on (the next one, or the last done when the next is not open yet) ({mN and mN.group(1)} / {dn} done)')
      if t is leo:   # his plan: through the express plan with « Use yesterday's plan » on day 1, else saved as the app saves it
        if i == 1:
          t.ev("SweepGame.openPlan()"); t.pg.wait_for_selector('#gSheet.g-pm', timeout=8000); t.pg.wait_for_timeout(700)
          rs = t.pg.locator('#gSheet [data-pm="resume"]')
          ok(rs.count() == 1 and "yesterday" in rs.inner_text(), f'leo D2 « Use yesterday’s plan » offered ({rs.count() and rs.inner_text()!r})')
          t.ev("window.__swUser = 1"); rs.click(); t.pg.wait_for_timeout(400)
          if SHOTS: t.pg.screenshot(path=os.path.join(SHOTS, 'lw-leo-express-resumed.png'))
          f = t.ev("({ bias: (document.querySelector('#gSheet [data-q=X_bias].on') || {}).dataset?.v || '', ml: (document.querySelector('#gSheet [data-pmf=max_loss]') || {}).value || '', plan: (document.querySelector('#gSheet [data-pmf=X_plan]') || {}).value || '' })")
          t.pg.locator('#gSheet [data-pm="save"]').click(); t.pg.wait_for_timeout(1200); t.ev("window.__swUser = 0")
          j = t.ev("(d) => (getDoc('journals', d) || {}).pre || null", day)
          ok(f['bias'] == 'bullish' and f['ml'] == '500' and not f['plan'] and j and j.get('bias') == 'bullish' and j.get('max_loss') == '500', f'leo D2 one tap brings the plan back, saved with the bias and the max loss only, no scenario typed ({f}, {j and (j.get("bias"), j.get("max_loss"))})')
        else:
          t.put('journals', {'id': day, 'pre': {'bias': 'bullish', 'max_loss': '500', 'max_trades': '3', 'saved_at': epoch(day, '08:45')}})
        t.today()
        if i == 3: ok('Your rule today · wait for the confirmation' in t.ev(NOW), f'leo D4 the rule written last night in « Now » ({t.ev(NOW)[-80:]!r})')
        if i == 3 and SHOTS: t.pg.locator('#main .nav-rt').screenshot(path=os.path.join(SHOTS, 'lw-leo-rule.png'))
      t.morning.append((i, t.ev(COACH)))
      if t is sam:
        cz = t.ev("(document.querySelector('#main .nav-now-cz') || {}).textContent || ''").replace(' ', ' ')
        if i == TILT + 3: ok('Marge à 950 $' in cz and 'risque réduit de moitié aujourd’hui (250 $)' in cz and v and amount(v[1]) == 250, f'sam {day} D1 the first morning after the tilt: « {cz} », risk {v}')
        if i == TILT + 4: ok('au-delà de ta perte max' in cz and 'risque réduit de moitié aujourd’hui (250 $)' in cz and v and amount(v[1]) == 250, f'sam {day} D1 one green day since: still careful « {cz} », risk {v}')
        if i in (TILT + 3, TILT + 4): ok('Continue ce qui marche' not in t.ev("document.querySelector('#main .co-today') ? document.querySelector('#main .co-today').innerText : ''") and 'protège ton compte' in t.ev("document.querySelector('#main .co-today') ? document.querySelector('#main .co-today').innerText : ''"), f'sam {day} D1 the coach speaks of protecting the account')
        if i in (TILT + 5, TILT + 6) or i < TILT: ok(not cz, f'sam {day} D1 no caution line ({cz!r})')
        if i == 2:
          b = t.pg.locator('#main .co-today [data-co="resume"]')
          if SHOTS and b.count(): t.pg.locator('#main .co-today').screenshot(path=os.path.join(SHOTS, 'lw-sam-resume.png'))
          ok(b.count() == 1, f'sam C1/D2 3rd session without a plan: « Reprends ton dernier plan ? » in one tap ({t.ev(COACH)!r})')
          if b.count():
            t.ev("window.__swUser = 1"); b.click(); t.pg.wait_for_selector('#gSheet.g-pm', timeout=8000); t.pg.wait_for_timeout(700)
            f = t.ev("({ bias: (document.querySelector('#gSheet [data-q=X_bias].on') || {}).dataset?.v || '', ml: (document.querySelector('#gSheet [data-pmf=max_loss]') || {}).value || '' })")
            ok(f == {'bias': 'bullish', 'ml': '500'}, f'sam D2 the express plan opens with his last plan in it ({f})')
            t.pg.keyboard.press('Escape'); t.pg.wait_for_timeout(600); t.ev("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); t.pg.wait_for_timeout(500); t.ev("window.__swUser = 0")
            t.ev("localStorage.removeItem('pm.draft')")
        if i == TARGET + 1:   # the morning after the target: the window, its text, « Not yet »
          for _ in range(40):   # one window at a time: the payout's gold moment may come first (the trader closes it)
            if t.pg.locator('.nav-pass.nav-dlg').count(): break
            if t.pg.locator('.g-sweep [data-g="sw-close"]').count(): t.ev("window.__swUser = 1"); t.pg.locator('.g-sweep [data-g="sw-close"]').first.click(); t.pg.wait_for_timeout(500); t.ev("window.__swUser = 0")
            t.pg.wait_for_timeout(250)
          ok(t.ev("document.querySelectorAll('.nav-pass.nav-dlg.open, .g-sweep.in').length") <= 1, 'sam C2 never two windows at once')
          txt = t.ev("(document.querySelector('.nav-pass .nav-pass-s') || {}).textContent || ''").replace(' ', ' ').replace(' ', ' ')
          ok('sans dépasser ton drawdown' in txt and 'Ta marge est descendue à 950 $' in txt and 'toucher' not in txt, f'sam A2 the evaluation passed, the next morning: « {txt} »')
          if t.pg.locator('[data-pass-later]').count(): t.ev("window.__swUser = 1"); t.pg.locator('[data-pass-later]').click(); t.pg.wait_for_timeout(600); t.ev("window.__swUser = 0")
      if SHOTS and i in (0, TILT + 3): t.pg.screenshot(path=os.path.join(SHOTS, f'lw-{t.name}-{i}-morning.png'))
      ok(not t.ev(WIDE), f'{t.name} {day} morning: nothing wider than the window ({t.ev(WIDE)})')
      if t is leo:   # his mission of the day
        t.ev("""fetch('api/game/gameplan', {headers: {'X-Requested-With': 'fetch'}}).then((r) => r.json()).then((s) => { for (let n = 1; n <= s.open_to; n++) if (!(s.done || {})[n] && n % 30) return fetch('api/game/gameplan/done', { method: 'POST', headers: {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}, body: JSON.stringify({ n }) }); })""")
    # ── 10:20: the trades, then 7 s for anything that would open ──
    server_at(f'{day} 10:20')
    for t in (sam, leo):
      plan = SAM[i] if t is sam else LEO[i]
      if plan is None: continue
      t.open(day, '10:20', 'session')
      for k, pnl in enumerate(plan):
        trade(t, day, k, pnl, '10:%02d' % (16 + (i % 3) + k * 4 if t is leo else 20), 'short' if t is leo and i == 5 else 'long')
      t.pg.wait_for_timeout(6500 if t.phone else 3000); t.today(300)   # (the phone: the suggestions' 5 s and the evaluation's 0.9 s passed)
      t.after.append((i, t.ev(FIX)))
      if t is sam and i == 0:   # (the day's card comes with the first trade)
        fd = t.ev("[...document.querySelectorAll('#main .nav-fstrip .nav-fd')].map((b) => b.dataset.fd)")
        first = next((real + dt.timedelta(days=k)).isoformat() for k in range(7) if (real + dt.timedelta(days=k)).weekday() < 5)   # the sign-up's session (real time), its weekday
        ok(bool(fd) and fd[0] == first, f'sam B3 the strip of days starts at the sign-up, not 3 weeks before ({fd[:2]}, sign-up session {real})')
      if t is sam and i == TILT:
        if SHOTS: t.pg.screenshot(path=os.path.join(SHOTS, f'lw-sam-tilt.png'))
        ok('Pris tout de suite après une perte' in t.ev(FIX) and not re.search(r'\b0 min', t.ev(FIX)), f'sam F « right after a loss », not « 0 min » ({t.ev(FIX)!r})')
      if t is sam and i == TARGET + 1:
        acc = t.ev("(document.querySelector('#main .nav-acc .nav-ready') || {}).textContent || ''")
        ok('Objectifs atteints · en attente de ta firme' in acc and t.pg.locator('.nav-pass.nav-dlg').count() == 0, f'sam F after « Pas encore »: a line on the account card, no window ({acc!r})')
      if t is sam and i == 5:   # Monday of the second week: the week before had trades, never a plan
        nt = t.ev("fetch('api/notifications', {headers: {'X-Requested-With': 'fetch'}}).then((r) => r.json()).then((j) => (j.items || []).map((n) => n.type))")
        ok('wow_clean_week' not in nt, f'sam A1 no « A full week inside your plan » for a week without a plan ({nt[:6]})')
      ok(not t.ev(WIDE), f'{t.name} {day} session: nothing wider than the window ({t.ev(WIDE)})')
    # ── 16:40: Léo's review (Sam never does his) ──
    server_at(f'{day} 16:40')
    for t in ([sam, leo] if i in (TILT, TARGET) else [leo]):
      t.open(day, '16:40', 'close'); t.pg.wait_for_timeout(2000)   # (nothing opens before the review either)
      if t is sam: continue
      t.ev("window.__swUser = 1")
      t.pg.locator('#main [data-rt="fin"], #main .nav-rt-s [data-rt="review"]').first.click(); t.pg.wait_for_selector('#gSheet.g-rv', timeout=8000); t.pg.wait_for_timeout(600)
      for b in t.pg.locator('#gSheet [data-bal-same]:not(.on)').all(): b.click(); t.pg.wait_for_timeout(200)
      if i == 2: t.pg.locator('#gSheet [data-gr=tomorrow]').fill('Wait for the confirmation')
      t.ev("window.__swMoment += ' reviewed'"); t.pg.locator('#gSheet [data-g="save-review"]').click(); t.pg.wait_for_timeout(800)
      t.ev("window.__swUser = 0")
      t.pg.wait_for_timeout(3500)
      t.ev("document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())"); t.today(1200)
      pill = t.ev("(document.querySelector('#main .nav-rt-pill.ok') || {}).textContent || ''")
      ok(pill.strip() == 'Day complete', f'leo {day} A3 after the review: « Day complete » ({pill!r}){" — 0 trades in his plan" if i == 5 else ""}')
      if SHOTS and i in (2, 5): t.pg.screenshot(path=os.path.join(SHOTS, f'lw-leo-{i}-close.png'))
  stop()
  for t in (sam, leo): t.collect()
  print(f'   days lived: {days[0]} → {days[-1]} ({len(days)} market days)')
  ok(len(days) >= 10, f'at least 10 market days lived ({len(days)})')
  for t in (sam, leo):
    # A4: the risk allowed never above the last max loss chosen ($500); the room only as a limit
    bad = [r for r in t.risk if r[2] > 500 or (r[2] > 500 and 'limit' not in r[1].lower())]
    ok(t.risk and not bad, f'{t.name} A4 « risk allowed » never above the last max loss chosen ($500) over {len(t.risk)} mornings ({bad[:3] or [r[2] for r in t.risk]})')
    # C2: nothing opened by the app between the first trade and the review
    opened = [x for x in t.log if x['k'] == 'open' and not x['u'] and (x['m'].endswith('session') or x['m'].endswith('close'))]
    ok(not opened, f'{t.name} C2 no window between the first trade and the review ({opened[:3]})')
    # E1: one reward toast a day at most, after the review only
    rw = [x for x in t.log if x['k'] == 'toast' and REWARD.search(x['v'])]
    by = {}
    for x in rw: by.setdefault(x['m'].split(' ')[0], []).append(x)
    early = [x for x in rw if not x['m'].endswith('reviewed')]
    ok(not early and all(len(v) <= 1 for v in by.values()), f'{t.name} E1 at most one reward a day, only after the review ({len(rw)} in all; before the review: {early[:3]}; days with more: {[k for k, v in by.items() if len(v) > 1]})')
    # C1: the coach never says the same sentence 3 days in a row (the morning, after the trades)
    for kind, l in (('morning', t.morning), ('after the trades', t.after)):
      rep = [l[k][1] for k in range(2, len(l)) if l[k][1] and l[k][1] == l[k - 1][1] == l[k - 2][1]]
      ok(len(l) >= 8 and not rep, f'{t.name} C1 {kind}: never the same sentence 3 days in a row ({len(l)} days; repeated: {rep[:2]})')
    ok(not t.errs, f'{t.name} no page error ({t.errs[:2]})')
  print('   sam mornings:', [x[1][:50] for x in sam.morning])
  print('   leo after:', [x[1][:50] for x in leo.after])
  for t in (sam, leo): t.ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
