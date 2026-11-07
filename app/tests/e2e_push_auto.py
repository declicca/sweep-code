"""
Sweep — the phone first (brief « Notifications », 5 Nov. 2026), Playwright, phone 390 × 844 (touch) and computer 1300 × 850,
EN / FR / ES, light and dark:
  python3 tests/e2e_push_auto.py http://127.0.0.1:8095 /tmp/show_state.json
 - Settings › Notifications › On this device: four switches (My routine with the times of its 3 reminders under it, My
   accounts, My progress, News and subscription); « My routine » off hides its times; on a computer, the QR code;
 - Today on a computer, a trade journaled and no phone: « Sweep on your phone » with the QR code, never blue; « Later » hides it;
 - on a phone, the first account guardian alert seen: « Get this alert on your phone » once (« Later »: not again);
 - /?i=qr on a phone (the QR code): « Sweep on your home screen », the address cleaned;
 - the bell: an account's moment (pa_alert) in the trader's language;
 - Admin › Emails: « On the phone » (reach, the notifications without an email, the news of the month); an automation's page:
   its notification under its email, its text saved, switched on and off.
Checks: no page error, nothing wider than the window, no button or pill cut or out of its box, the texts in each language.
"""
import json, os, sqlite3, subprocess, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
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
STUB = """(() => {   // the browser's push service, replaced (tests/e2e_push.py): a subscription with the test's keys; the permission too
  const K = %s;
  try { Object.defineProperty(Notification, 'permission', { get: () => window.__perm || 'default', configurable: true }); Notification.requestPermission = async () => (window.__perm = 'granted'); } catch (e) {}
  const fake = { endpoint: K.endpoint, expirationTime: null, unsubscribe: async () => { localStorage.removeItem('t.sub'); return true; },
    toJSON() { return { endpoint: K.endpoint, expirationTime: null, keys: { p256dh: K.p256dh, auth: K.auth } }; } };
  if (window.PushManager) {
    PushManager.prototype.subscribe = async function () { localStorage.setItem('t.sub', '1'); return fake; };
    PushManager.prototype.getSubscription = async function () { return localStorage.getItem('t.sub') ? fake : null; };
  }
})();"""
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"
# a button, a pill, a switch or a title cut, or out of the window or of its box
CUT = """(sel) => [...document.querySelectorAll(sel)].filter((e) => e.offsetParent).map((e) => { const r = e.getBoundingClientRect(), p = e.parentElement.getBoundingClientRect();
  // an input holds a longer text by design; a switch (.sw) and a chip are checked against the window and their row only
  const text = !/^(INPUT|SELECT)$/.test(e.tagName) && !e.matches('.sw, .chip'), row = e.closest('.nt-prow, .ml-pu, .nav-remind, .nav-dlg-in') || e.parentElement, q = row.getBoundingClientRect();
  const out = r.right > innerWidth + 1 || r.left < -1 || (text && e.scrollWidth > e.clientWidth + 2) || r.right > Math.max(p.right, q.right) + 1.5 || r.left < Math.min(p.left, q.left) - 1.5;
  return out ? (e.className || e.tagName) + ':' + e.textContent.trim().slice(0, 30) + ' ' + Math.round(r.left) + '-' + Math.round(r.right) : ''; }).filter(Boolean)"""
X = {
  'fr': {'rows': ['Ma routine', 'Mes comptes', 'Mes progrès', 'Nouveautés et abonnement'], 'qr': 'Sweep sur ton téléphone', 'later': 'Plus tard', 'pushA': 'Reçois cette alerte sur ton téléphone',
         'inst': 'Ajoute Sweep à ton écran d’accueil', 'bell': 'Topstep 50K peut demander un payout'},
  'en': {'rows': ['My routine', 'My accounts', 'My progress', 'News and subscription'], 'qr': 'Sweep on your phone', 'later': 'Later', 'pushA': 'Get this alert on your phone',
         'inst': 'Add Sweep to your home screen', 'bell': 'Topstep 50K can ask for a payout'},
  'es': {'rows': ['Mi rutina', 'Mis cuentas', 'Mi progreso', 'Novedades y suscripción'], 'qr': 'Sweep en tu teléfono', 'later': 'Más tarde', 'pushA': 'Recibe esta alerta en tu teléfono',
         'inst': 'Añade Sweep a tu pantalla de inicio', 'bell': 'Topstep 50K puede pedir un payout'},
}
SEED = """() => { put('accounts', { id: 'a', name: 'Main 50K', status: 'active', starting_balance_c: 5000000, rules: {} }); render(); }"""

def trader(br, lang, phone, theme, quiet=True):
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], permissions=['notifications'], color_scheme=theme)
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); %s } catch (e) {}" % (lang, "sessionStorage.setItem('sw.modal', '1');" if quiet else ''))
  unthrottle()
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'pa%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Noa', 'experience': 'gt1'}), headers=H)
  return ctx

def start(ctx, errs):
  pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(600)
  return pg

def settings(pg):
  pg.goto(B + '/#settings'); pg.wait_for_selector('#main details.nav-sgd[data-i="2"]', timeout=20000)
  pg.evaluate("document.querySelector('#main details.nav-sgd[data-i=\"2\"]').open = true")
  pg.wait_for_selector('#ntPrefs .nt-push', timeout=20000); pg.wait_for_timeout(300)

def shot(pg, name, sel=None):
  if not SHOTS: return
  (pg.locator(sel) if sel else pg).screenshot(path=os.path.join(SHOTS, name + '.png'))

# 1. Settings: the four switches, the times under « My routine », the QR code on a computer
def run_settings(p, lang, phone, theme):
  tag = f"{'390' if phone else '1300'}-{lang}-{theme}"; x = X[lang]; errs = []
  keys = json.loads(php('keys').stdout)
  br = p.chromium.launch(); ctx = trader(br, lang, phone, theme)
  ctx.add_init_script(STUB % json.dumps({'endpoint': 'https://fcm.googleapis.com/fcm/send/pa-%s-%d' % (tag, int(time.time() * 1000)), 'p256dh': keys['p256dh'], 'auth': keys['auth']}))
  pg = start(ctx, errs); settings(pg)
  qr = pg.evaluate("(() => { const i = document.querySelector('#ntPrefs .nt-qr img'); return i ? i.complete && i.naturalWidth > 0 : null; })()")
  ok((qr is True and pg.evaluate(TXT, '#ntPrefs .nt-qr-h') == [x['qr']]) if not phone else qr is None, f"{tag} the QR code: {'shown and loaded' if not phone else 'not on a phone'}")
  pg.click('#ntPrefs [data-nt="push-on"]'); pg.wait_for_selector('#ntPrefs .nt-push-row', timeout=15000); pg.wait_for_timeout(400)
  names = pg.evaluate(TXT, '#ntPrefs .nt-push-row b'); subs = pg.evaluate("document.querySelectorAll('#ntPrefs .nt-push-sub select').length")
  ok(names == x['rows'] and subs == 3, f"{tag} four switches {names}, the 3 times under the routine ({subs})")
  cut = pg.evaluate(CUT, '#ntPrefs .nt-push-row .sw, #ntPrefs .nt-push-sub select, #ntPrefs .nt-push-row b, #ntPrefs .nt-push-row small, #ntPrefs .nt-qr img')
  ok(pg.evaluate(WIDE) <= 1 and not cut, f'{tag} nothing wider than the window, nothing cut {cut[:3]}')
  shot(pg, f'pa-settings-{tag}', '#ntPrefs')
  pg.click('#ntPrefs .nt-push-row:has([data-nt-push="routine"]) .sw'); pg.wait_for_timeout(1200)
  st = ctx.request.get(B + '/api/push', headers=H).json()
  ok(pg.evaluate("document.querySelectorAll('#ntPrefs .nt-push-sub').length") == 0 and st['groups']['routine'] is False and st['prefs']['streak']['on'] is False and st['groups']['accounts'] is True,
     f'{tag} « {x["rows"][0]} » off: its times hidden, its kinds off on the server, the others kept')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

# 2. Today on a computer: « Sweep on your phone », never blue, « Later » hides it
def run_routine_qr(p, lang, theme):
  tag = f'1300-{lang}-{theme}'; x = X[lang]; errs = []
  br = p.chromium.launch(); ctx = trader(br, lang, False, theme); pg = start(ctx, errs)
  pg.evaluate("() => { put('trades', { id: 't1', account_id: 'a', date: todayStr(), symbol: 'MNQ', side: 'long', contracts: 1, pnl_c: 12000, fees_c: 0, entry_time: '09:45' }); render(); }")
  pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-qr', timeout=15000); pg.wait_for_timeout(400)
  row = pg.evaluate("(() => { const r = document.querySelector('#main .nav-qr'), i = r.querySelector('img'); return { t: r.querySelector('b').textContent, img: i.complete && i.naturalWidth > 0, blue: !!r.querySelector('.primary') }; })()")
  cut = pg.evaluate(CUT, '#main .nav-qr .btn, #main .nav-qr .link, #main .nav-qr img')
  ok(row['t'] == x['qr'] and row['img'] and not row['blue'] and not cut and pg.evaluate(WIDE) <= 1, f"{tag} Today: « {x['qr']} » with its QR code, no blue button, nothing cut {cut[:2]}")
  shot(pg, f'pa-routine-qr-{tag}', '#main .nav-rt')
  pg.click('#main .nav-qr [data-rt="qr-later"]'); pg.wait_for_timeout(500)
  pg.reload(); pg.wait_for_selector('#main .nav-rt', timeout=15000); pg.wait_for_timeout(1200)
  ok(not pg.evaluate("!!document.querySelector('#main .nav-qr')") and pg.evaluate("+(localStorage.getItem('sw.qrLater') || 0) > Date.now() + 6 * 864e5"), f"{tag} « {x['later']} »: gone for 7 days")
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

# 3. on a phone: the first guardian alert seen → « Get this alert on your phone », once
def run_moment(p, lang, theme):
  tag = f'390-{lang}-{theme}'; x = X[lang]; errs = []
  keys = json.loads(php('keys').stdout)
  br = p.chromium.launch(); ctx = trader(br, lang, True, theme, quiet=False)
  ctx.add_init_script(STUB % json.dumps({'endpoint': 'https://fcm.googleapis.com/fcm/send/pm-%s-%d' % (tag, int(time.time() * 1000)), 'p256dh': keys['p256dh'], 'auth': keys['auth']}))
  pg = start(ctx, errs); pg.wait_for_timeout(5500)   # the 2nd-day offers wait 5 s after opening (none on the first day)
  pg.evaluate("() => { const s = document.createElement('section'); s.className = 'surface nav-guard lv-watch'; s.id = 'tGuard'; document.getElementById('main').prepend(s); }")
  pg.wait_for_selector('.nav-dlg.nav-inst[data-sg="pushA"]', timeout=8000); pg.wait_for_timeout(400)
  t = pg.evaluate(TXT, '.nav-dlg.nav-inst h2')
  cut = pg.evaluate(CUT, '.nav-dlg.nav-inst .btn, .nav-dlg.nav-inst .link, .nav-dlg.nav-inst h2')
  ok(t == [x['pushA']] and not cut and pg.evaluate(WIDE) <= 1, f"{tag} the first guardian alert seen: « {x['pushA']} », nothing cut {cut[:2]}")
  shot(pg, f'pa-moment-{tag}')
  pg.click('.nav-dlg.nav-inst [data-inst-later]'); pg.wait_for_timeout(400)
  pg.reload(); pg.wait_for_selector('#main .nav-dash', timeout=15000); pg.wait_for_timeout(1500)
  pg.evaluate("() => { const s = document.createElement('section'); s.className = 'surface nav-guard lv-danger'; document.getElementById('main').prepend(s); }"); pg.wait_for_timeout(2500)
  ok(not pg.evaluate("!!document.querySelector('.nav-dlg.nav-inst')"), f'{tag} offered once: not again')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

# 4. /?i=qr on a phone: how to install, the address cleaned
def run_qr_landing(p, lang, theme):
  tag = f'390-{lang}-{theme}'; x = X[lang]; errs = []
  br = p.chromium.launch(); ctx = trader(br, lang, True, theme); pg = start(ctx, errs)
  pg.goto(B + '/?i=qr'); pg.wait_for_selector('.nav-dlg.nav-inst', timeout=15000); pg.wait_for_timeout(400)
  ok(pg.evaluate(TXT, '.nav-dlg.nav-inst h2') == [x['inst']] and '?i=qr' not in pg.url, f"{tag} the QR code opened on the phone: « {x['inst']} », the address cleaned ({pg.url})")
  shot(pg, f'pa-qr-landing-{tag}')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

# 5. the bell: an account's moment in the trader's language
def run_bell(p, lang, phone, theme):
  tag = f"{'390' if phone else '1300'}-{lang}-{theme}"; x = X[lang]; errs = []
  br = p.chromium.launch(); ctx = trader(br, lang, phone, theme); pg = start(ctx, errs)
  uid = pg.evaluate("S.me.id")
  prm = {'t': 'Topstep 50K can ask for a payout', 'b': 'Every payout condition of your firm is met. Record your request in Sweep.', 't_en': 'Topstep 50K can ask for a payout', 't_fr': 'Topstep 50K peut demander un payout', 't_es': 'Topstep 50K puede pedir un payout',
         'b_en': 'Every payout condition of your firm is met. Record your request in Sweep.', 'b_fr': 'Toutes les conditions de payout de ta firme sont remplies. Note ta demande dans Sweep.', 'b_es': 'Se cumplen todas las condiciones de payout de tu firma. Registra tu solicitud en Sweep.'}
  d = sqlite3.connect(DB)
  d.execute("INSERT INTO notifications (user_id, type, category, title_key, body_key, params, icon, action_url, priority, dedupe_key, created_at, quiet) VALUES (?, 'pa_alert', 'prop_alerts', 'pa_alert.title', 'pa_alert.body', ?, 'star', '#account/a', 'normal', ?, ?, 0)",
            (uid, json.dumps(prm), 'pa:t%d' % time.time(), int(time.time()))); d.commit(); d.close()
  pg.reload(); pg.wait_for_selector('[data-nt="bell"]', timeout=15000); pg.wait_for_timeout(1500)
  pg.evaluate("window.SweepNotify && SweepNotify.refresh()"); pg.wait_for_timeout(800)
  pg.click('[data-nt="bell"]'); pg.wait_for_selector('.nt-item', timeout=10000); pg.wait_for_timeout(400)
  ok(any(s.startswith(x['bell']) for s in pg.evaluate(TXT, '.nt-item .nt-txt b')), f"{tag} the bell: « {x['bell']} »")
  ok(pg.evaluate(WIDE) <= 1, f'{tag} nothing wider than the window')
  shot(pg, f'pa-bell-{tag}')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

# 6. Admin › Emails: « On the phone »; an automation's notification saved, switched on and off
def run_admin(p, lang, phone, theme):
  tag = f"{'390' if phone else '1300'}-{lang}-{theme}"; errs = []
  br = p.chromium.launch()
  ctx = br.new_context(storage_state=STATE, viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], color_scheme=theme)
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#mail'); pg.wait_for_selector('#main .ml-pu-list .ml-pu', timeout=30000); pg.wait_for_timeout(500)
  n = pg.evaluate("document.querySelectorAll('#main .ml-pu-list .ml-pu').length"); news = pg.evaluate("!!document.querySelector('#main .ml-pu[data-pu=\"news\"]')")
  cut = pg.evaluate(CUT, '#main .ml-pu .btn, #main .ml-pu .chip, #main .ml-pu .ml-st, #main .ml-pu input')
  ok(n == 3 and news and not cut and pg.evaluate(WIDE) <= 1, f'{tag} Admin › Emails: the 3 notifications without an email (the account moments) and the news of the month, nothing cut {cut[:3]}')
  shot(pg, f'pa-admin-list-{tag}', '#main .ml')
  autos = ctx.request.get(B + '/api/admin/mail', headers=H).json()['autos']
  aid = next(a['id'] for a in autos if a['auto'] == 'inactive3d')
  pg.goto(B + '/#mail/%d' % aid); pg.wait_for_selector('#main .ml-auto .ml-pu', timeout=20000); pg.wait_for_timeout(400)
  inp = pg.locator('#main .ml-pu input[data-pu-f="0"]'); inp.fill('Your discipline is waiting.')
  pg.click('#main .ml-pu [data-ml="pu-save"]'); pg.wait_for_timeout(800)
  it = next(i for i in ctx.request.get(B + '/api/admin/push', headers=H).json()['items'] if i['key'] == 'inactive3d')
  ok(it['text'][pg.evaluate("document.querySelector('#main .ml-pu .ml-tabs .chip.on').dataset.v")][0] == 'Your discipline is waiting.' and it['on'] is False, f'{tag} the notification\'s title saved, still off')
  pg.click('#main .ml-pu [data-ml="pu-on"]'); pg.wait_for_timeout(800)
  on = next(i for i in ctx.request.get(B + '/api/admin/push', headers=H).json()['items'] if i['key'] == 'inactive3d')['on']
  ok(on is True and pg.evaluate("!!document.querySelector('#main .ml-pu .ml-st-active')"), f'{tag} switched on (« On »)')
  cut = pg.evaluate(CUT, '#main .ml-pu .btn, #main .ml-pu .chip, #main .ml-pu .ml-st, #main .ml-pu input')
  ok(not cut and pg.evaluate(WIDE) <= 1, f'{tag} the automation\'s page: nothing cut {cut[:3]}')
  shot(pg, f'pa-admin-auto-{tag}', '#main .ml-pu')
  pg.click('#main .ml-pu [data-ml="pu-on"]'); pg.wait_for_timeout(800)
  ctx.request.post(B + '/api/admin/push/inactive3d', data=json.dumps({'on': False, 'text': it['text'] | {'en': ['Your discipline is waiting', it['text']['en'][1]], 'fr': ['Ta discipline t’attend', it['text']['fr'][1]], 'es': ['Tu disciplina te espera', it['text']['es'][1]]}}), headers=H)
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

with sync_playwright() as p:
  run_settings(p, 'fr', True, 'dark'); run_settings(p, 'es', True, 'light'); run_settings(p, 'en', False, 'light'); run_settings(p, 'fr', False, 'dark')
  run_routine_qr(p, 'fr', 'light'); run_routine_qr(p, 'es', 'dark')
  run_moment(p, 'fr', 'dark'); run_moment(p, 'en', 'light')
  run_qr_landing(p, 'es', 'light')
  run_bell(p, 'fr', True, 'dark'); run_bell(p, 'en', False, 'light')
  run_admin(p, 'en', False, 'light'); run_admin(p, 'fr', True, 'dark')
print(f"\n{'all passed' if not fails else f'{fails} failed'}")
sys.exit(1 if fails else 0)
