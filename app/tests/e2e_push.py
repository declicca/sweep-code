"""
Sweep — notifications on the phone (brief 02 part 10), Playwright, phone (fr, es) and computer (en):
  python3 tests/e2e_push.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
The server has test keys (SWEEP_PUSH_CONFIG = tools/push-config.local.php) and writes each message to a file
(SWEEP_PUSH_MOCK): nothing goes to a push service. The browser's push service is replaced by a stand-in subscription whose
keys the test made (tests/push_ua.php), so the test opens the very message the phone would get.
 - Settings › Notifications › « Sur cet appareil »: « Activer les notifications » registers /sw.js and this device;
   then the plan, the review and the week, each with its time (« 8 h 45 », New York) and its switch, saved on the server;
 - the scheduled task at the trader's time (9:00 here, chosen in the app; nothing at 8:45): the phone gets « Ton plan du
   jour t'attend. », in the trader's language, opening Today; « Désactiver sur cet appareil » forgets the device;
 - Safari on an iPhone, not added to the Home Screen: how to do it, no button.
 - (27 Oct.) right after a first plan, on a phone, once: « Je te rappelle demain à 8 h 45 pour ton plan ? », on in one tap; on an
   iPhone outside the Home Screen the three gestures; never on a computer; it replaces the « reminders » suggestion of the 2nd day.
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import json, os, sqlite3, subprocess, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
MOCK = os.environ.get('SWEEP_PUSH_MOCK', '')
SHOTS = os.environ.get('SWEEP_SHOTS', '')
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
def php(*a):
  return subprocess.run(['php', os.path.join(APP, 'tests', 'push_ua.php')] + list(a), capture_output=True, text=True, env=os.environ, timeout=60)
X = {
  'fr': {'denied': 'Les notifications sont bloquées pour Sweep.', 'h': 'Sur cet appareil', 'on': 'Activer les notifications', 'off': 'Désactiver sur cet appareil', 'rows': ['Rappel du plan', 'Rappel de la revue', 'Bilan de la semaine'],
         'times': ['8 h 45', '16 h 30', '17 h 00'], 'nine': '9 h 00', 'title': 'Ton plan du jour t’attend.', 'ios': 'Sur iPhone : ajoute Sweep à ton écran d’accueil',
         'help': 'Heure de New York, pour la cloche aussi.'},
  'en': {'denied': 'Notifications are blocked for Sweep.', 'h': 'On this device', 'on': 'Turn on notifications', 'off': 'Turn off on this device', 'rows': ['Plan reminder', 'Review reminder', 'Your week'],
         'times': ['8:45 AM', '4:30 PM', '5:00 PM'], 'nine': '9:00 AM', 'title': 'Your plan of the day is waiting.', 'ios': 'On iPhone: add Sweep to your Home Screen',
         'help': 'New York time, for the bell too.'},
  'es': {'denied': 'Las notificaciones están bloqueadas para Sweep.', 'h': 'En este dispositivo', 'on': 'Activar las notificaciones', 'off': 'Desactivar en este dispositivo', 'rows': ['Recordatorio del plan', 'Recordatorio de la revisión', 'Balance de la semana'],
         'times': ['8:45', '16:30', '17:00'], 'nine': '9:00', 'title': 'Tu plan del día te espera.', 'ios': 'En iPhone: añade Sweep a tu pantalla de inicio',
         'help': 'Hora de Nueva York, también para la campana.'},
}
SEED = """() => { put('accounts', { id: 'a', name: 'Main 50K', status: 'active', starting_balance_c: 5000000, rules: {} }); render(); }"""
STUB = """(() => {   // the browser's push service, replaced: a subscription with the test's keys; the permission too
  // (headless Chromium always says « denied » for Notification.permission, whatever the context grants)
  const K = %s;
  try { Object.defineProperty(Notification, 'permission', { get: () => window.__perm || 'default', configurable: true }); Notification.requestPermission = async () => (window.__perm = 'granted'); } catch (e) {}
  const fake = { endpoint: K.endpoint, expirationTime: null, unsubscribe: async () => { localStorage.removeItem('t.sub'); window.__unsub = (window.__unsub || 0) + 1; return true; },
    toJSON() { return { endpoint: K.endpoint, expirationTime: null, keys: { p256dh: K.p256dh, auth: K.auth } }; } };
  if (window.PushManager) {
    PushManager.prototype.subscribe = async function (o) { window.__key = o && o.applicationServerKey ? o.applicationServerKey.byteLength : 0; localStorage.setItem('t.sub', '1'); return fake; };
    PushManager.prototype.getSubscription = async function () { return localStorage.getItem('t.sub') ? fake : null; };
  }
})();"""
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"
IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'

def trader(br, lang, phone, ua=None, perm=True):
  o = dict(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True,
           locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], permissions=['notifications'] if perm else [])
  if ua: o['user_agent'] = ua
  ctx = br.new_context(**o)
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  unthrottle()
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'push%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Noa', 'experience': 'gt1'}), headers=H)
  return ctx

def settings(pg):
  pg.goto(B + '/#settings'); pg.wait_for_selector('#main details.nav-sgd[data-i="2"]', timeout=20000)
  pg.evaluate("document.querySelector('#main details.nav-sgd[data-i=\"2\"]').open = true")
  pg.wait_for_selector('#ntPrefs .nt-push', timeout=20000); pg.wait_for_timeout(300)

def state(ctx): return ctx.request.get(B + '/api/push', headers=H).json()

def until(f, s=10):
  t = time.time()
  while time.time() - t < s:
    v = f()
    if v: return v
    time.sleep(0.25)
  return f()

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  keys = json.loads(php('keys').stdout)
  ep = 'https://fcm.googleapis.com/fcm/send/e2e-%s-%d' % (tag, int(time.time() * 1000))
  br = p.chromium.launch()
  ctx = trader(br, lang, phone)
  ctx.add_init_script(STUB % json.dumps({'endpoint': ep, 'p256dh': keys['p256dh'], 'auth': keys['auth']}))
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(800)
  uid = pg.evaluate("S.me && S.me.id")
  # 1. « On this device »: one button
  settings(pg)
  ok(pg.evaluate(TXT, '#ntPrefs .nt-push-h') == [x['h']] and pg.evaluate(TXT, '#ntPrefs [data-nt="push-on"]') == [x['on']] and state(ctx)['available'] is True,
     f"{tag} Settings › Notifications: « {x['h']} », « {x['on']} »")
  if SHOTS: pg.locator('#ntPrefs').screenshot(path=os.path.join(SHOTS, f'p10-off-{tag}.png'))
  pg.evaluate("window.__perm = 'denied'; render()"); pg.wait_for_timeout(300)
  ok(pg.evaluate(TXT, '#ntPrefs .nt-push-note')[:1] and pg.evaluate(TXT, '#ntPrefs .nt-push-note')[0].startswith(x['denied']) and not pg.evaluate("!!document.querySelector('#ntPrefs [data-nt=\"push-on\"]')"),
     f"{tag} blocked in the phone's settings: « {x['denied']}… », no button")
  pg.evaluate("window.__perm = 'default'; render()"); pg.wait_for_selector('#ntPrefs [data-nt="push-on"]', timeout=5000)
  # 2. turn on: /sw.js and this device on the server; the three reminders with their time
  pg.click('#ntPrefs [data-nt="push-on"]'); pg.wait_for_selector('#ntPrefs .nt-push-row', timeout=15000); pg.wait_for_timeout(300)
  st = state(ctx)
  sw = pg.evaluate("navigator.serviceWorker.getRegistration('/').then((r) => { const w = r && (r.active || r.waiting || r.installing); return w ? w.scriptURL : ''; })")
  ok(st['devices'] == 1 and sw.endswith('/sw.js') and pg.evaluate("window.__key") == 65, f"{tag} turned on: /sw.js registered, this device on the server, the server's key given to the browser ({st['devices']}, {sw})")
  names = pg.evaluate(TXT, '#ntPrefs .nt-push-row b')
  times = pg.evaluate("[...document.querySelectorAll('#ntPrefs .nt-push-row select')].map((s) => s.options[s.selectedIndex].textContent)")
  ok(names == x['rows'] and times == x['times'] and pg.evaluate("[...document.querySelectorAll('#ntPrefs [data-nt-push]')].every((i) => i.checked)"),
     f"{tag} the plan, the review and the week, on, at {times} ({names})")
  ok(pg.evaluate(TXT, '#ntPrefs .nt-push-help')[0].startswith(x['help']), f"{tag} « {x['help']} »")
  # 3. the plan at 9:00, the review off: saved on the server
  pg.select_option('#ntPrefs select[data-nt-push-at="plan"]', '09:00')
  pg.click('#ntPrefs .nt-push-row:nth-child(2) .sw')
  st = until(lambda: (lambda s: s if s['prefs']['plan']['at'] == '09:00' and s['prefs']['review']['on'] is False else None)(state(ctx)), 25)   # (24 Oct.: 10 s were not enough on a busy CI machine)
  ok(bool(st) and st['prefs']['weekly'] == {'on': True, 'at': '17:00'}, f"{tag} plan at 9:00, review off: saved ({st and st['prefs']})")
  ok(pg.evaluate("(() => { const s = document.querySelector('#ntPrefs select[data-nt-push-at=\"plan\"]'); return s.options[s.selectedIndex].textContent; })()") == x['nine'], f"{tag} it reads « {x['nine']} »")
  ok(pg.evaluate(WIDE) <= 1, f'{tag} nothing wider than the window')
  if SHOTS: pg.locator('#ntPrefs').screenshot(path=os.path.join(SHOTS, f'p10-on-{tag}.png'))
  # 4. the scheduled task: nothing at 8:45, the plan at 9:00 (the trader's time), in the trader's language
  open(MOCK, 'a').close()
  a = php('run', uid, '08:45'); early = [l for l in php('open', MOCK, keys['pem'], keys['auth'], ep).stdout.splitlines() if l]
  b = php('run', uid, '09:00'); got = [json.loads(l) for l in php('open', MOCK, keys['pem'], keys['auth'], ep).stdout.splitlines() if l]
  msg = got[0]['msg'] if got else {}
  ok(a.returncode == 0 and b.returncode == 0 and early == [] and len(got) == 1 and msg.get('title') == x['title'] and msg.get('url') == '#dashboard',
     f"{tag} the reminder: nothing at 8:45, « {x['title']} » at 9:00, opening Today ({a.stderr.strip()[:120]}{b.stderr.strip()[:120]} {msg})")
  # 5. turn off on this device
  pg.click('#ntPrefs [data-nt="push-off"]'); pg.wait_for_selector('#ntPrefs [data-nt="push-on"]', timeout=10000)
  ok(state(ctx)['devices'] == 0 and pg.evaluate("window.__unsub") == 1, f"{tag} « {x['off']} »: the device forgotten, the browser's subscription ended")
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

def run_iphone(p, lang):   # Safari on an iPhone, not added to the Home Screen
  x = X[lang]; br = p.chromium.launch()
  ctx = trader(br, lang, True, ua=IPHONE, perm=False)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(800)
  settings(pg)
  note = pg.evaluate(TXT, '#ntPrefs .nt-push-note')
  ok(len(note) == 1 and note[0].startswith(x['ios']) and not pg.evaluate("!!document.querySelector('#ntPrefs [data-nt=\"push-on\"]')") and pg.evaluate(WIDE) <= 1 and not errs,
     f"390-{lang} iPhone in Safari: « {x['ios']}… », no button ({note})")
  if SHOTS: pg.locator('#ntPrefs').screenshot(path=os.path.join(SHOTS, f'p10-iphone-{lang}.png'))
  br.close()

PLAN = "() => { put('journals', { id: todayStr(), pre: { bias: 'bullish', max_loss: '500', max_trades: '2', saved_at: Math.floor(Date.now() / 1000) } }); render(); }"
RM = {'fr': ('Je te rappelle demain à 8 h 45 pour ton plan ?', 'Rappel activé : demain à 8 h 45.', 'Tes rappels sur iPhone : ajoute Sweep à ton écran d’accueil.'),
      'en': ('Shall I remind you tomorrow at 8:45 AM for your plan?', 'Reminder on: tomorrow at 8:45 AM.', '')}
def run_remind(p, lang, phone, ua=None):   # (27 Oct., brief activation step E) right after a first plan, once: tomorrow's reminder in one tap
  tag = f"{'390' if phone else '1300'}-{lang}{' iPhone' if ua else ''}"; q, done, ios = RM[lang]
  keys = json.loads(php('keys').stdout); ep = 'https://fcm.googleapis.com/fcm/send/e2e-rm-%s-%d' % (lang, int(time.time() * 1000))
  br = p.chromium.launch(); ctx = trader(br, lang, phone, ua=ua, perm=not ua)
  if not ua: ctx.add_init_script(STUB % json.dumps({'endpoint': ep, 'p256dh': keys['p256dh'], 'auth': keys['auth']}))
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(800)
  ok(pg.locator('#main .nav-remind').count() == 0, f'{tag} before a plan: no reminder offer')
  pg.evaluate(PLAN); pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(600)
  sp = lambda v: (v or '').replace('\xa0', ' ').replace('\u202f', ' ')
  row = sp(until(lambda: pg.locator('#main .nav-rt .nav-remind').count() and pg.locator('#main .nav-rt .nav-remind').inner_text(), 8) or '')
  if not phone:
    ok(not row, f'{tag}: a computer: no offer ({row!r})'); br.close(); return
  if ua:
    if SHOTS: pg.locator('#main .nav-remind').screenshot(path=os.path.join(SHOTS, f'p10-remind-iphone-{lang}.png'))
    ok(bool(row) and ios in row and pg.locator('#main .nav-remind ol li').count() == 3 and pg.locator('#main [data-rt=remind-yes]').count() == 0, f'{tag}: the three gestures, not a refusal ({(row or "")[:80]!r})')
    pg.locator('#main [data-rt=remind-no]').tap(); pg.wait_for_timeout(500)
  else:
    ok(bool(row) and q in row, f'{tag}: after the first plan, « {q} » ({(row or "")[:80]!r})')
    if SHOTS: pg.locator('#main .nav-rt').screenshot(path=os.path.join(SHOTS, f'p10-remind-{tag}.png'))
    blue = pg.evaluate("[...document.querySelectorAll('#main .nav-rt .btn.primary')].filter((b) => b.getClientRects().length).length")
    ok(blue <= 1, f'{tag}: the offer adds no blue button ({blue})')
    pg.locator('#main [data-rt=remind-yes]').tap()
    msg = sp(until(lambda: (pg.evaluate("(document.getElementById('toast') || {}).textContent || ''") or '').startswith(done[:12]) and pg.evaluate("document.getElementById('toast').textContent"), 10) or '')
    ok(bool(msg) and done in msg and until(lambda: state(ctx).get('devices'), 8), f'{tag}: one tap: « {done} », this phone subscribed ({msg!r})')
  pg.reload(); pg.wait_for_selector('#main .nav-rt', timeout=15000); pg.wait_for_timeout(2500)
  ok(pg.locator('#main .nav-remind').count() == 0 and pg.evaluate("JSON.parse(localStorage.getItem('sw.sugg') || '{}').push.done") is True, f'{tag}: once: not offered again, and it replaces the « reminders » suggestion of the 2nd day')
  ok(pg.evaluate(WIDE) <= 1 and not errs, f'{tag}: nothing wider than the window, no page error ({errs[:1]})')
  br.close()

if not MOCK: print('FAIL SWEEP_PUSH_MOCK is not set (tools/run.sh, tools/par.py)'); sys.exit(1)
with sync_playwright() as p:
  run(p, 'fr', True)
  run(p, 'en', False)
  run(p, 'es', True)
  run_iphone(p, 'fr')
  run_remind(p, 'fr', True)
  run_remind(p, 'en', False)
  run_remind(p, 'fr', True, ua=IPHONE)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
