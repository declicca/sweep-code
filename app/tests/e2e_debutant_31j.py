"""
Sweep — Léa, a trader of less than 6 months, over 31 days (analyse « débutant » of 2 Nov., docs/parcours/ANALYSE-DEBUTANT-2026-11-02.md), Playwright:
  python3 tests/e2e_debutant_31j.py http://127.0.0.1:8095
A trader of her own each run (« Less than 6 months », the 90-day gameplan started with her account, following the discovery
missions: users.discovery_done = 2), phone 390 (fr, dark, touch), computer 1300 (en, light), phone 390 (es, light).
 1  day 1: a trade typed by its P&L alone, with its risk (« No screenshot? »), no target; Sweep AI not shown yet
 2  day 3: the gameplan moved — mission 2 ticked by that trade, « Mission 3 of 90 » on Today, the lesson of the mission Sweep ticked one
    tap away; one counter (no « Day N of 90 »), « Level N » without « · 0 complete days »
 3  missions 1 to 30: every trading word in a mission (PDH / PDL, R, window, micro, stop, target, process grade, setup) is explained
    where it appears (a touchable underlined word); mission 2 asks no target
 4  day 31: 25 trades over the month, by their P&L and risk (12 long, 10 short and a few more): the gameplan is past mission 3; Stats says
    nothing in the imperative about the side of the trade (« favor short trades ») under 20 trades a side; « Your edge » waits too
 5  the quick sheet: the Sweep Setup and « + Other » (before mission 8), a line under « Risk ($) » says what the risk and the R are,
    no « (optional) », the instrument in sight
No page error, nothing wider than the window.
"""
import datetime as dt, json, os, random, re, sqlite3, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def sql(q, a=()):
  d = sqlite3.connect(DB); r = d.execute(q, a).fetchall(); d.commit(); d.close(); return r
def today_ny():   # the game's session (tools/game-now.py pins the servers on 15:00 ET)
  pin = os.environ.get('SWEEP_GAME_NOW', '')
  now = dt.datetime.strptime(pin, '%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('America/New_York')) if pin else dt.datetime.now(ZoneInfo('America/New_York'))
  return (now + dt.timedelta(hours=6)).date()
def move(uid, day):   # the gameplan as if today were its day `day`
  sql('UPDATE game_gameplan SET start_day = ? WHERE user_id = ?', ((today_ny() - dt.timedelta(days=day - 1)).isoformat(), uid))
STATE = "fetch('api/game/gameplan', {headers: {'X-Requested-With': 'fetch'}}).then((r) => r.json())"
X = {'fr': {'mis': r'Mission (\d+) sur 90', 'day': r'\bJour \d+ sur 90', 'read': 'Lire la leçon', 'other': '+ Autre', 'opt': 'facultatif', 'riskh': 'Ce que tu perds si ton stop est touché',
            'imp': ['privilégie', 'concentre-toi sur', 'évite '], 'lv0': 'jour complet'},
     'en': {'mis': r'Mission (\d+) of 90', 'day': r'\bDay \d+ of 90', 'read': 'Read the lesson', 'other': '+ Other', 'opt': 'optional', 'riskh': 'What you lose if your stop is hit',
            'imp': ['favor long', 'favor short', 'This week, favor'], 'lv0': 'complete day'},
     'es': {'mis': r'Misión (\d+) de 90', 'day': r'\bDía \d+ de 90', 'read': 'Leer la lección', 'other': '+ Otro', 'opt': 'opcional', 'riskh': 'Lo que pierdes si tocan tu stop',
            'imp': ['prioriza las operaciones'], 'lv0': 'día completo'}}
# the trading words of the missions, as written in each language (src/gameplan.js JAR)
WORDS = {'fr': [r'\bPDH\b|\bPDL\b', r'(?<![\w’-])[−-]?\d*R(?![\w])', r'fenêtres?', r'\bmicros?\b', r'\bstops?\b', r'\bcibles?\b', r'notes? de processus', r'\bsetups?\b'],
         'en': [r'\bPDH\b|\bPDL\b', r'(?<![\w’-])[−-]?\d*R(?![\w])', r'\bwindows?\b', r'\bmicros?\b', r'\bstops?\b', r'\btargets?\b', r'process (?:grade|score)s?', r'\bsetups?\b'],
         'es': [r'\bPDH\b|\bPDL\b', r'(?<![\w’-])[−-]?\d*R(?![\w])', r'ventanas?', r'\bmicros?\b', r'\bstops?\b', r'stop y objetivos?', r'notas? de proceso', r'\bsetups?\b']}
WIDE = "document.documentElement.scrollWidth - innerWidth"
SHOTS = os.environ.get('SHOTS')   # a folder: screenshots of the moments checked

def run(p, lang, phone, scheme):
  tag = f"{390 if phone else 1300}-{lang}-{scheme}"; x = X[lang]
  try: sql('DELETE FROM attempts')
  except Exception: pass
  br = p.chromium.launch(); errs = []
  c = br.new_context(viewport={'width': 390 if phone else 1300, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme,
                     locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'lea%07d@t.dev' % random.randint(0, 9999999), 'consent': True, 'elapsed': 6000}), headers=H)
  pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  # sign-up: an evaluation of 50K, « Less than 6 months »: the gameplan starts with the account
  pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=20000); pg.wait_for_timeout(700)
  for s in ('form[data-form=account] [data-st-ph0=eval]', '[data-st-firm=topstep]'): pg.locator(s).first.click(); pg.wait_for_timeout(250)
  if pg.locator('[data-st-size="50000"]').count(): pg.locator('[data-st-size="50000"]').first.click(); pg.wait_for_timeout(250)
  pg.locator('[data-onb-fn]').click(); pg.keyboard.type('Léa')
  pg.locator('.nav-onb-me [data-exp="new"]').click(); pg.wait_for_timeout(600)
  pg.locator('form[data-form=account][data-onb] [type=submit]').click()
  pg.wait_for_selector('#gSheet', timeout=10000); pg.wait_for_timeout(600)
  uid = pg.evaluate("S.me && S.me.id")
  sql('UPDATE users SET discovery_done = 2 WHERE id = ?', (uid,))   # she follows the discovery missions (the tests' accounts see everything otherwise)
  st = pg.evaluate(STATE)
  ok(bool(st.get('started')) and st.get('day') == 1, f'{tag} day 1: the gameplan started with her account ({st.get("started")}, day {st.get("day")})')
  pg.keyboard.press('Escape'); pg.wait_for_timeout(500); pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach((b) => b.click())")
  pg.goto(B + '/#dashboard'); pg.reload(); pg.wait_for_selector('#main .nav-rt', timeout=15000); pg.wait_for_timeout(1500)
  ok(not pg.evaluate("(() => { const f = document.getElementById('askFab'); return !!f && f.getClientRects().length > 0 && getComputedStyle(f).display !== 'none' })()"), f'{tag} day 1: Sweep AI not shown yet')
  # 1. a trade by its P&L alone, with its risk, no target (« No screenshot? »)
  pg.evaluate("openTicket ? openTicket(null) : null"); pg.wait_for_timeout(900)
  if not pg.locator('.nav-am [data-am="no-shot"]').count(): pg.locator('#bottomnav .plus, .bn-plus').first.click(); pg.wait_for_timeout(900)
  pg.locator('.nav-am [data-am="no-shot"]').first.click(); pg.wait_for_timeout(700)
  sheet = pg.evaluate("(() => { const a = document.querySelector('.nav-am'); return a ? a.innerText : '' })()")
  if SHOTS: pg.screenshot(path=f'{SHOTS}/{tag}-quick.png')
  sp = pg.evaluate("[...document.querySelectorAll('.nav-am .nav-sp [data-sp], .nav-am .nav-sp [data-sp-other]')].map((b) => b.textContent.trim())")
  ok(sp[:1] == ['Sweep Setup'] and x['other'] in sp and len(sp) == 2, f'{tag} 5 the setups: the Sweep Setup and « {x["other"]} » ({sp})')
  ok(x['riskh'] in sheet and x['opt'] not in sheet.lower(), f'{tag} 5 a line says what the risk and the R are, no « {x["opt"]} »')
  inst = pg.evaluate("(() => { const s = document.querySelector('.nav-am [data-am-sel=inst]'); if (!s) return null; return [!s.closest('details'), s.textContent.trim()] })()")
  ok(bool(inst) and inst[0] and bool(inst[1]), f'{tag} 5 the instrument in sight, not folded ({inst})')
  pg.locator('.nav-am [data-am-f=net]').fill('-180'); pg.locator('.nav-am [data-am-seg=dir][data-v=long]').click()
  pg.locator('.nav-am [data-am-f=risk]').fill('200'); pg.wait_for_timeout(300)
  if pg.locator('.nav-am [data-am-sel=account].ph, .nav-am .nav-am-selb.ph').count(): pg.evaluate("(() => { const b = document.querySelector('.nav-am [data-am-pickf=account]'); if (b) b.click(); })()")
  pg.locator('.nav-am [data-am=save]').click(); pg.wait_for_timeout(1800)
  tr = pg.evaluate("S.trades.filter((t) => !t.demo).map((t) => [t.pnl_c, t.risk_c, t.target || null, t.date])")
  ok(len(tr) == 1 and tr[0][0] == -18000 and tr[0][1] == 20000 and tr[0][2] is None, f'{tag} 1 day 1: the trade by its P&L and its risk, no target ({tr})')
  day1 = tr[0][3] if tr else today_ny().isoformat()
  # 2. day 3: the gameplan moved
  move(uid, 3)
  pg.goto(B + '/#dashboard'); pg.reload(); pg.wait_for_selector('#main .nav-rt', timeout=15000); pg.wait_for_timeout(2500)
  st = pg.evaluate(STATE)
  ok('2' in (st.get('done') or {}), f'{tag} 2 day 3: mission 2 ticked by the trade without a target ({sorted((st.get("done") or {}).keys())})')
  line = pg.evaluate("(document.getElementById('gpLine') || {}).innerText || ''").replace(' ', ' ')
  m = re.search(x['mis'], line)
  ok(bool(m) and int(m.group(1)) >= 3 and not re.search(x['day'], line), f'{tag} 2 day 3: « Mission {m and m.group(1)} of 90 », one counter ({line[:120]!r})')
  ok(x['read'] in line, f'{tag} 2 the lesson of the mission Sweep ticked, one tap away ({line[:160]!r})')
  if SHOTS: pg.screenshot(path=f'{SHOTS}/{tag}-day3.png')
  sub = pg.evaluate("(document.querySelector('#main .nav-rt-sum') || {}).textContent || ''")
  ok(x['lv0'] not in sub, f'{tag} 2 « {sub.strip()} » without « 0 {x["lv0"]} »')
  ok(pg.evaluate(WIDE) <= 0, f'{tag} 2 Today: nothing wider than the window')
  # 3. missions 1 to 30: every trading word explained where it appears
  pg.wait_for_function("window.SweepGP || window.SweepGPLoad", timeout=10000)
  pg.evaluate("window.SweepGPLoad ? SweepGPLoad() : null"); pg.wait_for_timeout(800)
  bare = []
  for n in range(1, 31):
    pg.evaluate("(n) => SweepGP.openMission(n)", n); pg.wait_for_timeout(250)
    got = pg.evaluate("""(re) => { const m = document.querySelector('#gSheet .gp-m'); if (!m) return null;
      const parts = [...m.querySelectorAll('.gp-desc, .gp-dw p, .gp-learn')].filter((e) => e.dataset.b !== 'VOCAB');   // (the lexicon itself: its words are the definitions)
      const txt = parts.map((e) => e.textContent).join(' '), terms = [...m.querySelectorAll('.gp-term')].map((e) => e.textContent);
      const sub = (document.querySelector('#gSheet .g-sub, #gSheet .g-head small, #gSheet small') || {}).textContent || '';
      const f = (r) => (/d\\*R/.test(r) ? '' : 'i');   // (R: a capital letter, as in the app)
      return { miss: re.filter((r) => new RegExp(r, f(r)).test(txt) && !terms.some((t) => new RegExp(r, f(r)).test(t))), sub, txt: txt.slice(0, 400) } }""", [w.replace('(?<![\\w’-])', '(?<![\\w’-])') for w in WORDS[lang]])
    if got and got['miss']: bare.append((n, got['miss']))
    if n == 2:
      ok(bool(got) and not re.search(r'\b(cible|target|objetivo)\b', got['txt'], re.I) or lang == 'es' and 'stop y objetivo' not in got['txt'], f'{tag} 3 mission 2 asks no target ({got and got["txt"][:140]!r})')
      if SHOTS: pg.screenshot(path=f'{SHOTS}/{tag}-mission2.png')
      hd = pg.evaluate("document.querySelector('#gSheet') ? document.querySelector('#gSheet').innerText.slice(0, 200) : ''")
      ok(not re.search(r'\b(Jour|Day|Día) 2\b', hd), f'{tag} 2 the mission sheet: « Mission 2 », no calendar « Day 2 » ({hd[:90]!r})')
      if phone and pg.locator('#gSheet .gp-term').count():   # a touch on an underlined word: its line of the lexicon
        pg.locator('#gSheet .gp-term').first.tap(); pg.wait_for_timeout(300)
        ok(pg.evaluate("!!document.getElementById('swTip') && document.getElementById('swTip').textContent.length > 20"), f'{tag} 3 a touch on a word shows its explanation')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach((b) => b.click())"); pg.wait_for_timeout(150)
  ok(not bare, f'{tag} 3 missions 1 to 30: every trading word explained where it appears ({bare[:4]})')
  # 4. day 31: a month of trades by their P&L and risk
  move(uid, 31)
  start = today_ny() - dt.timedelta(days=30)
  rows = []
  for k in range(31):
    d = start + dt.timedelta(days=k)
    if d.weekday() >= 5 or k % 7 == 6: continue
    for j in range(1 if k % 3 else 2):
      i = len(rows); side = 'long' if i % 2 == 0 and i < 24 else 'short' if i < 22 else 'long'
      rows.append({'id': f'lea-{k}-{j}', 'date': d.isoformat(), 'direction': side, 'pnl_c': (24000 if side == 'short' else -9000) if i % 3 else -15000, 'risk_c': 20000})
  pg.evaluate("""(rows) => { const a = S.accounts.find((x) => x.status !== 'archived'); for (const r of rows) put('trades', Object.assign({ account_id: a.id, instrument: 'MNQ', contracts: 1, entry: 1, exit: 2, pnl_manual: true, entry_time: '10:05', exit_time: '10:20', stop: null, target: null }, r)); }""", rows)
  pg.evaluate("Promise.all(Object.values(chains || {})).then(() => true)"); pg.wait_for_timeout(1500)
  pg.goto(B + '/#dashboard'); pg.reload(); pg.wait_for_selector('#main .nav-rt', timeout=15000); pg.wait_for_timeout(2500)
  st = pg.evaluate(STATE)
  line = pg.evaluate("(document.getElementById('gpLine') || {}).innerText || ''").replace(' ', ' ')
  m = re.search(x['mis'], line)
  ok(bool(m) and int(m.group(1)) >= 3, f'{tag} 4 day 31: the gameplan past mission 3 (« {m and m.group(0)} », {len(st.get("done") or {})} done)')
  nl, ns = sum(r['direction'] == 'long' for r in rows), sum(r['direction'] == 'short' for r in rows)
  pg.evaluate("location.hash = '#analytics'"); pg.wait_for_timeout(2500)
  txt = pg.evaluate("document.getElementById('main').innerText")
  hit = [w for w in x['imp'] if w.lower() in txt.lower()]
  ok(not hit, f'{tag} 4 Stats ({nl} long, {ns} short): nothing in the imperative about the side of the trade ({hit})')
  ok(pg.evaluate("document.querySelectorAll('#main .ed-item, #main .edge-item, #main [data-edge-key]').length") == 0, f'{tag} 4 « Your edge » waits for 20 trades a group')
  ok(pg.evaluate(WIDE) <= 0, f'{tag} 4 Stats: nothing wider than the window')
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  br.close()

with sync_playwright() as p:
  run(p, 'fr', True, 'dark')
  run(p, 'en', False, 'light')
  run(p, 'es', True, 'light')
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
