"""
Sweep — the 90-day gameplan (brief « Parcours de 90 jours », 20 Oct.), phone 390 (FR, ES) and computer 1300 (EN), a new trader each time:
  python3 tests/e2e_gameplan.py http://127.0.0.1:8095 [storage_state, unused: it signs up its own traders]
 1  sign-up: « less than 6 months » offers the gameplan right under it, no second question: its track comes from the account
    (an evaluation → B; a simulation account, the new account type → A); « Create account » starts it today, Sweep ticks
    mission 1 (the account) at once; no field says « optional »; « Explore with sample data » shows it is preparing
 2  Today: the gameplan's card (before the Monday: when it starts); on day 9: today's mission, the late ones, the progress
 3  a mission: the notion of the day, « Test yourself » answered at once (right in blue, wrong in gold, why), « Done when »;
    ticked → its XP, the card moves; the map: 3 months, days done / today / late / to come, nothing wider than the screen
 4  day 31: nothing of Month 2 before the gate; the gate's criteria, « On to Month 2 » → Month 2 open, 150 XP
 5  Settings: the gameplan's day, « Stop » asks first, then « Start » again (the map opens)
The plan's dates are moved in the test database (SWEEP_TEST_DB), as if days had passed.
"""
import datetime as dt, json, os, random, sqlite3, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def until(pg, expr, ms=12000):
  for _ in range(ms // 150):
    if pg.evaluate(f'!!({expr})'): return True
    pg.wait_for_timeout(150)
  return False
TXT = {'fr': {'more': 'En savoir plus', 'a': 'Moins de 6 mois', 'gp': 'Ton parcours de 90 jours est inclus', 'opt': 'facultatif', 'prep': 'Préparation des données', 'kick': 'Ton parcours de 90 jours', 'day9': 'Jour 9 sur 90', 'late': 'à rattraper', 'quiz': 'Teste-toi', 'dw': 'C’est fait quand', 'gate': 'La porte du mois 1', 'pass': 'Passer au mois 2', 'set': 'Parcours de 90 jours', 'stop': 'Arrêter le parcours', 'go': 'Commencer le parcours'},
       'en': {'more': 'Learn more', 'a': 'Less than 6 months', 'gp': 'Your 90-day gameplan is included', 'opt': 'optional', 'prep': 'Preparing the sample data', 'kick': 'Your 90-day gameplan', 'day9': 'Day 9 of 90', 'late': 'to catch up', 'quiz': 'Test yourself', 'dw': 'Done when', 'gate': 'The Month 1 gate', 'pass': 'On to Month 2', 'set': '90-day gameplan', 'stop': 'Stop the gameplan', 'go': 'Start the gameplan'},
       'es': {'more': 'Saber más', 'a': 'Menos de 6 meses', 'gp': 'Tu recorrido de 90 días está incluido', 'opt': 'opcional', 'prep': 'Preparando los datos', 'kick': 'Tu recorrido de 90 días', 'day9': 'Día 9 de 90', 'late': 'por recuperar', 'quiz': 'Ponte a prueba', 'dw': 'Hecho cuando', 'gate': 'La puerta del mes 1', 'pass': 'Pasar al mes 2', 'set': 'Recorrido de 90 días', 'stop': 'Detener el recorrido', 'go': 'Empezar el recorrido'}}
WIDE = "Math.max(...[...document.querySelectorAll('#gSheet, #gSheet *, #main *')].map((e) => e.getBoundingClientRect().right)) - innerWidth"
STATE = "fetch('api/game/gameplan', {headers: {'X-Requested-With': 'fetch'}}).then((r) => r.json())"
def today_ny():   # the game's trading day: New York + 6 h
  return (dt.datetime.now(ZoneInfo('America/New_York')) + dt.timedelta(hours=6)).date()
def move(uid, day):   # the plan as if today were its day `day`
  start = (today_ny() - dt.timedelta(days=day - 1)).isoformat()
  d = sqlite3.connect(DB); d.execute('UPDATE game_gameplan SET start_day = ? WHERE user_id = ?', (start, uid)); d.commit(); d.close()

def run(p, lang, phone, full):
  global fails
  tag = f"{390 if phone else 1300} {lang}"
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
  br = p.chromium.launch(); errs = []
  c = br.new_context(viewport={'width': 390 if phone else 1300, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], color_scheme='dark')
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'gp%07d@t.dev' % random.randint(0, 9999999), 'consent': True, 'elapsed': 6000}), headers=H)
  pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  T = TXT[lang]
  # 1. sign-up
  pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=20000); pg.wait_for_timeout(700)
  ok(pg.locator('.nav-onb-me [data-exp="new"]').inner_text().strip() == T['a'] and pg.locator('.nav-onb-gp').count() == 0, f'{tag} 1 « {T["a"]} », nothing offered before it is tapped')
  ok(T['opt'] not in pg.locator('#main').text_content().lower(), f'{tag} 1 no field says « {T["opt"]} »')
  ok(pg.locator('[data-st-ph0]').evaluate_all("(b) => b.map((x) => x.dataset.stPh0)") == ['simulation', 'eval', 'funded', 'live'], f'{tag} 1 the account: simulation, evaluation, funded or live')
  sim = not full   # the Spanish run: a simulation account (track A); the others an evaluation (track B)
  if sim:
    pg.locator('form[data-form=account] [data-st-ph0=simulation]').click(); pg.wait_for_selector('form.nav-live [name=name]', timeout=5000); pg.wait_for_timeout(300)
    hd = pg.locator('.nav-live-h').text_content()
    ok('simulación' in hd.lower(), f'{tag} 1 simulation: its own short form')
    pg.fill('form.nav-live [name=firmName]', 'NinjaTrader'); pg.fill('form.nav-live [name=name]', 'Práctica'); pg.fill('form.nav-live [name=start]', '50000')
  else:
    for s in ('form[data-form=account] [data-st-ph0=eval]', '[data-st-firm=apex]'): pg.locator(s).first.click(); pg.wait_for_timeout(250)
    if pg.locator('[data-st-type=apex-eod]').count(): pg.locator('[data-st-type=apex-eod]').click(); pg.wait_for_timeout(250)
    pg.locator('[data-st-size="50000"]').click(); pg.wait_for_timeout(250)
    demo = pg.locator('[data-act="demo"]')
    ok(demo.count() == 1 and demo.is_visible(), f"{tag} 1 « explore with sample data » on the last step")
    if demo.count() and demo.is_visible():   # « Explore with sample data first »: preparing at once, then its window; « Cancel » there
      demo.click(); pg.wait_for_timeout(120)
      busy = [demo.get_attribute('aria-busy'), T['prep'] in (demo.text_content() or '')]
      until(pg, "document.querySelector('aside.nav-ask.open')", 30000)
      ok(busy == ['true', True] and pg.locator('aside.nav-ask.open').count() == 1, f'{tag} 1 « explore with sample data »: preparing at once ({busy}), then its window')
      pg.locator('aside.nav-ask.open [data-ask="0"]').click(); pg.wait_for_timeout(500)
  pg.locator('[data-onb-fn]').click(); pg.keyboard.type('Noa')
  pg.locator('.nav-onb-me [data-exp="new"]').click(); until(pg, "document.querySelector('.nav-onb-gp p')", 6000)
  box = pg.locator('.nav-onb-gp').inner_text() if pg.locator('.nav-onb-gp').count() else ''
  ok(T['gp'] in box and pg.locator('.nav-onb-gp button').count() == 0, f'{tag} 1 tapped: the gameplan offered right under it, no second question')
  if phone: ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} 1 the page no wider than the screen')
  pg.locator('.nav-onb-me [data-exp="new"]').click(); pg.wait_for_timeout(300)
  ok(pg.locator('.nav-onb-gp').count() == 0, f'{tag} 1 « {T["a"]} » tapped again: the offer goes')
  pg.locator('.nav-onb-me [data-exp="new"]').click(); until(pg, "document.querySelector('.nav-onb-gp p')", 6000)
  pg.locator('form[data-form=account][data-onb] [type=submit]').click()
  pg.wait_for_selector('#gSheet.g-plan, #gSheet .g-gate, #gSheet.g-pm', timeout=10000); pg.wait_for_timeout(600)
  st = pg.evaluate(STATE); want = 'A' if sim else 'B'
  ok(st.get('started') and st.get('track') == want and st.get('day') == 1 and ((st.get('done') or {}).get('1') or {}).get('by') == 'sweep', f"{tag} 1 « Create account »: the gameplan started today (day {st.get('day')}), track {want} from the account, mission 1 ticked by Sweep ({st.get('track')}, {list((st.get('done') or {}).keys())})")
  if sim: ok(pg.evaluate("S.accounts.map((a) => [a.money_type, a.phase])") == [['simulation', 'simulation']], f"{tag} 1 the account is a simulation one ({pg.evaluate('S.accounts.map((a) => [a.money_type, a.phase])')})")
  me = pg.evaluate("fetch('api/data',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>j.user&&j.user.experience)")
  ok(me == 'new', f'{tag} 1 the experience kept: « new » ({me})')
  uid = pg.evaluate("fetch('api/data',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>j.user&&j.user.id)")
  pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(500)
  # 2. Today
  pg.evaluate("location.hash = '#dashboard'"); until(pg, "document.getElementById('gpCard')", 10000)
  card = pg.locator('#gpCard').inner_text() if pg.locator('#gpCard').count() else ''
  ok(T['kick'] in card, f'{tag} 2 Today: the gameplan card ({card[:70]!r})')
  if not full: c.close(); br.close(); ok(not errs, f'{tag} no page error ({errs[:2]})'); return
  move(uid, 9); pg.reload(); until(pg, "document.getElementById('gpCard') && /9/.test(document.getElementById('gpCard').innerText)", 12000); pg.wait_for_timeout(600)
  card = pg.locator('#gpCard').inner_text()
  late = pg.locator('#gpCard .gp-late').inner_text() if pg.locator('#gpCard .gp-late').count() else ''
  ok(T['day9'] in card and pg.locator('#gpCard .gp-mis[data-n="9"]').count() == 1 and T['late'] in late, f'{tag} 2 day 9: today\'s mission (9), the late ones ({late!r})')
  bar0 = pg.evaluate("parseFloat(document.querySelector('#gpCard .gp-bar i').style.width)")
  if phone: pg.screenshot(path=f'/tmp/gp_{tag.replace(" ", "_")}_today.png')
  # 3. a mission that teaches: 8 (« Read the setup »)
  pg.evaluate("SweepGP.openMission(8)"); until(pg, "document.querySelector('#gSheet .gp-quiz')")
  sh = pg.locator('#gSheet').text_content()
  ok('Sweep Setup' in sh and T['quiz'] in sh and T['dw'] in sh and pg.locator('#gSheet .gp-q').count() == 3, f'{tag} 3 mission 8: the Sweep Setup, « {T["quiz"]} » (3 questions), « {T["dw"]} »')
  pg.locator('#gSheet .gp-q[data-qi="0"] [data-j="0"]').click(); pg.wait_for_timeout(250)   # right (a long)
  pg.locator('#gSheet .gp-q[data-qi="1"] [data-j="0"]').click(); pg.wait_for_timeout(250)   # wrong (the stop is beyond the sweep)
  q = pg.evaluate("[...document.querySelectorAll('#gSheet .gp-q')].slice(0, 2).map((x) => [x.className, !x.querySelector('.gp-why').hidden, !!x.querySelector('.right'), !!x.querySelector('.wrong')])")
  ok(q[0][0].endswith('is-ok') and q[0][1] and q[1][0].endswith('is-no') and q[1][2] and q[1][3], f'{tag} 3 answered at once: right, then wrong with the right one shown and why ({q})')
  pg.locator('#gSheet .gp-q[data-qi="2"] [data-j="2"]').click(); pg.wait_for_timeout(250)
  ok('2' in pg.locator('#gSheet .gp-score').inner_text(), f"{tag} 3 the score: {pg.locator('#gSheet .gp-score').inner_text()!r}")
  if phone: pg.screenshot(path=f'/tmp/gp_{tag.replace(" ", "_")}_mission.png'); ok(pg.evaluate(WIDE) <= 1, f'{tag} 3 the mission fits the screen ({pg.evaluate(WIDE)})')
  xp0 = pg.evaluate("fetch('api/game/profile',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>(j.profile||j).xp || 0)")
  pg.locator('#gSheet [data-gp="tick"][data-n="8"]').click()
  until(pg, "!document.getElementById('gSheet') && SweepGP.state().done && SweepGP.state().done['8']", 8000); pg.wait_for_timeout(700)
  xp1 = pg.evaluate("fetch('api/game/profile',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(j=>(j.profile||j).xp || 0)")
  bar1 = pg.evaluate("parseFloat(document.querySelector('#gpCard .gp-bar i').style.width)")
  ok(xp1 - xp0 == 20 and bar1 > bar0, f'{tag} 3 ticked: +20 XP ({xp0} → {xp1}), the bar moves ({bar0} → {bar1} %)')
  pg.click('#gpCard [data-gp=map]'); until(pg, "document.querySelector('#gSheet .gp-map')")
  states = pg.evaluate("Object.fromEntries([...document.querySelectorAll('#gSheet .gp-d')].map((d) => [d.dataset.n, d.className.split(' ').find((c) => c.startsWith('s-'))]))")
  ok(states.get('1') == 's-done' and states.get('8') == 's-done' and states.get('9') == 's-today' and states.get('5') == 's-late' and states.get('12') == 's-soon', f"{tag} 3 the map: 1 and 8 done, 9 today, 5 late, 12 to come ({[states.get(k) for k in ('1', '5', '8', '9', '12')]})")
  ok(pg.locator('#gSheet .gp-seg button').count() == 3, f'{tag} 3 the map: 3 months')
  if phone: pg.screenshot(path=f'/tmp/gp_{tag.replace(" ", "_")}_map.png'); ok(pg.evaluate(WIDE) <= 1, f'{tag} 3 the map fits the screen ({pg.evaluate(WIDE)})')
  pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(400)
  # 4. day 31: the gate
  move(uid, 31); pg.evaluate("SweepGP.load()"); pg.wait_for_timeout(800)
  st = pg.evaluate(STATE)
  ok(st['day'] == 31 and st['open_to'] == 30, f"{tag} 4 day 31: nothing of Month 2 before the gate (open to {st['open_to']})")
  pg.evaluate("SweepGP.openMission(30)"); until(pg, "document.querySelector('#gSheet.g-gp-gate')")
  g = pg.locator('#gSheet').text_content()
  if T['gate'] not in g or T['pass'] not in g: print('   gate text:', g[:300])
  ok(T['gate'] in g and pg.locator('#gSheet .gp-gl li').count() == 7 and T['pass'] in g, f'{tag} 4 the gate: its 7 criteria, « {T["pass"]} »')
  pg.locator('#gSheet [data-gp="gate"][data-c="pass"]').click(); until(pg, "!document.getElementById('gSheet')", 6000); pg.wait_for_timeout(500)
  st = pg.evaluate(STATE)
  ok((st.get('gates') or {}).get('1') == 'pass' and st['open_to'] == 31, f"{tag} 4 passed: Month 2 open (open to {st['open_to']})")
  # 5. Settings
  pg.evaluate("location.hash = '#settings'"); until(pg, "document.querySelector('#main .gp-set')", 10000); pg.wait_for_timeout(400)
  s = pg.locator('#main .gp-set').inner_text()
  ok(T['set'] in s and '31' in s and T['stop'] in s, f'{tag} 5 Settings: the gameplan, its day, « {T["stop"]} »')
  pg.locator('#main .gp-set [data-gp="stop"]').click(); until(pg, "document.querySelector('aside.nav-ask.open')", 4000)
  pg.locator('aside.nav-ask.open [data-ask="1"]').click(); until(pg, "document.querySelector('#main .gp-set [data-gp=go]')", 6000)
  ok(not pg.evaluate(STATE)['started'] and pg.locator('#main .gp-set [data-gp=go]').count() == 1 and pg.locator('#main .gp-set .gp-facts span').count() == 4, f'{tag} 5 « Stop » asked first, then the gameplan is gone; « {T["go"]} » and its 4 facts')
  pg.locator('#main .gp-set [data-gp=learn]').click(); until(pg, "document.querySelector('#gSheet .gp-learn-s')", 6000)
  ok(pg.locator('#gSheet .gp-lm').count() == 3 and pg.locator('#gSheet .gp-learn-go [data-gp=go]').count() == 1, f'{tag} 5 « {T["more"]} »: the 3 months and the button to start')
  pg.locator('#gSheet .gp-learn-go [data-gp=go]').click(); until(pg, "document.querySelector('#gSheet .gp-map')", 6000)
  ok(pg.evaluate(STATE)['started'] and pg.locator('#gSheet .gp-map').count() == 1, f'{tag} 5 started again from Settings: the map opens')
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  c.close(); br.close()

with sync_playwright() as p:
  for lang, phone, full in (('fr', True, True), ('en', False, True), ('es', True, False)):
    run(p, lang, phone, full)
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
