"""
Sweep — an account found by a platform is linked from Today in one tap (13 Nov., brief « relier les comptes trouvés »):
  python3 tests/e2e_sync_today.py http://127.0.0.1:8095 [storage_state, unused: each case signs up its own trader]
Phone 390×844 (touch, fr, dark) and computer 1300×850 (fr, light), then EN and ES texts. A trader with a Sweep account
« Lucid 50K » (firm Lucid Trading) and a trade typed by hand; the add-on (its key) sends two accounts and executions:
  - Today shows one line: « NinjaTrader a trouvé le compte LUCID50K-778. Relier à … Lucid 50K ? », « Relier » and « Ce n'est
    pas un compte de trading »; inside the window, buttons not clipped and not over each other, no page wider than the window;
  - « Relier »: the trades arrive (1 added, the typed one completed, not doubled), the line moves to the next account found
    (no account stands out: « Choisir le compte », which opens the account's sheet);
  - « Ce n'est pas un compte de trading »: ignored, the line is gone and stays gone after a reload.
A trader with no Sweep account that fits: « Créer ce compte » creates it (firm, size) and links it.
No JS error, no broken file.
"""
import json, os, sqlite3, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095').rstrip('/')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOTS = os.environ.get('TMPDIR', '/tmp').rstrip('/')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
ms = lambda ny: int(datetime.strptime(ny, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)
DAY = '2026-11-10'
FILLS = [
  {'id': 'u1', 'account': 'LUCID50K-778', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 1, 'price': 21000.25, 'ts': ms(DAY + ' 09:31:05'), 'point_value': 2},
  {'id': 'u2', 'account': 'LUCID50K-778', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 1, 'price': 21012.75, 'ts': ms(DAY + ' 09:36:00'), 'point_value': 2},
  {'id': 'u3', 'account': 'LUCID50K-778', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 2, 'price': 21030.5, 'ts': ms(DAY + ' 10:15:00'), 'point_value': 2},
  {'id': 'u4', 'account': 'LUCID50K-778', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 2, 'price': 21020.5, 'ts': ms(DAY + ' 10:22:00'), 'point_value': 2},
]
TXT = {'fr': ('NinjaTrader a trouvé le compte LUCID50K-778. Relier à', 'Relier', 'Ce n’est pas un compte de trading', 'Choisir le compte', 'Créer ce compte'),
       'en': ('NinjaTrader found the account LUCID50K-778. Link it to', 'Link', 'Not a trading account', 'Choose the account', 'Create this account'),
       'es': ('NinjaTrader encontró la cuenta LUCID50K-778. ¿Vincularla a', 'Vincular', 'No es una cuenta de trading', 'Elegir la cuenta', 'Crear esta cuenta')}
LINE = """(() => { const el = document.querySelector('#main .sy-today'); if (!el || !el.checkVisibility()) return null;
  const r = el.getBoundingClientRect(), bs = [...el.querySelectorAll('button')].map((b) => { const q = b.getBoundingClientRect(); return { t: b.textContent.trim(), l: q.left, r: q.right, t0: q.top, b: q.bottom, w: b.scrollWidth - b.clientWidth, dis: b.disabled }; });
  const over = bs.length === 2 && !(bs[0].r <= bs[1].l + 0.5 || bs[1].r <= bs[0].l + 0.5 || bs[0].b <= bs[1].t0 + 0.5 || bs[1].b <= bs[0].t0 + 0.5);
  return { text: el.querySelector('.sy-txt').textContent.trim(), bs, over, inside: r.left >= 0 && r.right <= innerWidth + 0.5 && bs.every((b) => b.l >= r.left - 0.5 && b.r <= r.right + 0.5 && b.w <= 4),
    first: el.previousElementSibling ? el.previousElementSibling.className : '', wide: document.documentElement.scrollWidth - innerWidth }; })()"""

def trader(p, lang, phone, solo=False):
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, device_scale_factor=2 if phone else 1,
                       color_scheme='dark' if phone else 'light', locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  n = 'st%d' % int(time.time() * 1000)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Lea', 'last_name': 'Test', 'experience': 'gt1'}), headers=H)
  if True:
    ctx.request.put(B + '/api/docs/firms/f-lu', data=json.dumps({'name': 'Lucid Trading'}), headers=H)
    ctx.request.put(B + '/api/docs/accounts/acc-lu', data=json.dumps({'name': 'Lucid 50K', 'firm_id': 'f-lu', 'starting_balance_c': 5000000, 'status': 'active', 'money_type': 'eval', 'phase': 'eval', 'created_on': DAY}), headers=H)
    if not solo: ctx.request.put(B + '/api/docs/accounts/acc-b', data=json.dumps({'name': 'Perso', 'firm_id': '', 'starting_balance_c': 1000000, 'status': 'active', 'created_on': DAY}), headers=H)
    ctx.request.put(B + '/api/docs/trades/man-st', data=json.dumps({'account_id': 'acc-lu', 'instrument': 'MNQ', 'date': DAY, 'session_date': True, 'entry_time': '09:32', 'exit_time': '09:36', 'direction': 'long',
      'contracts': 1, 'entry': 21000, 'exit': 21013, 'pnl_c': 2600, 'notes': 'Patient entry', 'discipline': {}, 'emo': {}, 'review': {}, 'tags': [], 'shots': []}), headers=H)
  key = ctx.request.post(B + '/api/sync/key', data=json.dumps({'platform': 'ninjatrader'}), headers=H).json()['key']
  accts = [{'name': 'LUCID50K-778', 'cash': 50420}, {'name': 'LUCID-100K-5', 'cash': 100300} if solo else {'name': 'ZZ-OTHER-9', 'cash': 3300}]
  r = ctx.request.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep NT8 1.3.0', 'accounts': accts, 'fills': FILLS}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  if r.status != 200: raise RuntimeError('push refused: %s %s' % (r.status, r.text()[:80]))
  pg = ctx.new_page(); errs = []; bad = []
  pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.on('console', lambda m: errs.append('console: ' + m.text[:160]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
  pg.on('response', lambda r: bad.append('%d %s' % (r.status, r.url[len(B):][:80])) if r.status >= 400 and '/api/' not in r.url else None)
  pg.goto(B + '/#dashboard'); pg.wait_for_function("() => typeof S !== 'undefined' && S.me", timeout=20000)
  return br, ctx, pg, errs, bad

with sync_playwright() as p:
  for phone in (True, False):
    tag = 'phone' if phone else 'computer'; t = TXT['fr']
    br, ctx, pg, errs, bad = trader(p, 'fr', phone)
    try: pg.wait_for_selector('#main .sy-today', timeout=9000)
    except Exception: print('DEBUG', pg.evaluate("JSON.stringify({ hash: location.hash, onb: !!document.querySelector('#main .onb'), kids: [...document.getElementById('main').children].map((c) => c.className).slice(0, 6), st: window.SweepSync && SweepSync.state(), mode: S.mode })")[:900]); raise
    pg.wait_for_timeout(900)
    ln = pg.evaluate(LINE)
    ok(ln and ln['text'].startswith(t[0]) and 'Lucid 50K' in ln['text'] and [b['t'] for b in ln['bs']] == [t[1], t[2]], f'{tag} Today: the account found and the Sweep account proposed, « Relier » and « Ce n’est pas un compte de trading » ({ln and ln["text"][:90]})')
    ok(ln and ln['inside'] and not ln['over'] and ln['wide'] <= 0, f'{tag} the line inside the window, its buttons whole and apart ({ln and (ln["inside"], ln["over"], ln["wide"], ln["bs"])})')
    ok(ln and 'nav-dash' not in ln['first'], f'{tag} the line above the day\'s cards')
    pg.screenshot(path=f'{SHOTS}/sync-today-{tag}-1.png')
    (pg.locator('#main .sy-today [data-sy="t-link"]').tap if phone else pg.locator('#main .sy-today [data-sy="t-link"]').click)()
    pg.wait_for_function("() => (S.trades || []).filter((x) => x.source === 'ninjatrader').length === 2", timeout=15000); pg.wait_for_timeout(1200)
    tr = pg.evaluate("S.trades.filter((x) => !x.demo).map((x) => [x.id, x.account_id, x.source || '', x.notes || ''])")
    ok(len(tr) == 2 and all(x[1] == 'acc-lu' and x[2] == 'ninjatrader' for x in tr) and any(x[0] == 'man-st' and x[3] == 'Patient entry' for x in tr), f'{tag} « Relier »: the trades already received are written, the one typed by hand completed and not doubled ({tr})')
    ln = pg.evaluate(LINE)
    ok(ln and 'ZZ-OTHER-9' in ln['text'] and 'LUCID50K' not in ln['text'] and ln['bs'][0]['t'] == t[3] and ln['inside'] and not ln['over'], f'{tag} the linked account left the line; the next one found, none stands out: « Choisir le compte » ({ln and (ln["text"][:80], ln["inside"], ln["over"], ln["bs"])})')
    (pg.locator('#main .sy-today [data-sy="t-choose"]').tap if phone else pg.locator('#main .sy-today [data-sy="t-choose"]').click)()
    pg.wait_for_selector('#sySheet.open .sy-opts', timeout=8000)
    ok(pg.evaluate("[...document.querySelectorAll('#sySheet .sy-opt')].some((b) => /Perso/.test(b.textContent)) && !/Lucid 50K/.test(document.querySelector('#sySheet .sy-opts').textContent)"), f'{tag} « Choisir le compte » opens the account\'s sheet: the free Sweep accounts, not the one just linked')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    (pg.locator('#main .sy-today [data-sy="t-ignore"]').tap if phone else pg.locator('#main .sy-today [data-sy="t-ignore"]').click)()
    pg.wait_for_function("() => !document.querySelector('#main .sy-today')", timeout=10000)
    pg.reload(); pg.wait_for_function("() => typeof S !== 'undefined' && S.me && window.SweepSync && SweepSync.state()", timeout=25000); pg.wait_for_timeout(800)
    st = pg.evaluate("SweepSync.state().accounts.map((a) => [a.name, a.state])")
    ok(pg.evaluate("!document.querySelector('#main .sy-today')") and sorted(st) == [['LUCID50K-778', 'linked'], ['ZZ-OTHER-9', 'ignored']], f'{tag} « Ce n’est pas un compte de trading »: ignored, the line is gone and stays gone ({st})')
    pg.screenshot(path=f'{SHOTS}/sync-today-{tag}-2.png')
    ok(not errs and not bad, f'{tag} no JS error, no broken file' + ('' if not errs and not bad else ': ' + ' | '.join((errs + bad)[:3])))
    br.close()
  # no free Sweep account left for the next account found: « Créer ce compte », the firm and the size already filled in
  br, ctx, pg, errs, bad = trader(p, 'fr', True, solo=True)
  pg.wait_for_selector('#main .sy-today [data-sy="t-link"]', timeout=15000); pg.wait_for_timeout(600)
  pg.locator('#main .sy-today [data-sy="t-link"]').tap()
  pg.wait_for_selector('#main .sy-today [data-sy="t-create"]', timeout=15000); pg.wait_for_timeout(600)
  ln = pg.evaluate(LINE)
  ok(ln and 'LUCID-100K-5' in ln['text'] and ln['bs'][0]['t'] == TXT['fr'][4] and 'Lucid Trading' in ln['text'] and '100' in ln['text'] and ln['inside'] and not ln['over'], f'no free Sweep account: « Créer ce compte », with what the name and the balance say ({ln and ln["text"][-80:]})')
  pg.screenshot(path=f'{SHOTS}/sync-today-create.png')
  pg.locator('#main .sy-today [data-sy="t-create"]').tap()
  pg.wait_for_function("() => !document.querySelector('#main .sy-today') && S.accounts.some((x) => x.name === 'LUCID-100K-5')", timeout=15000); pg.wait_for_timeout(600)
  ac = pg.evaluate("(() => { const a = S.accounts.find((x) => !x.demo && x.name === 'LUCID-100K-5'), st = SweepSync.state().accounts.find((x) => x.name === 'LUCID-100K-5'); return a ? [a.starting_balance_c, a.firm_id, S.firms.filter((f) => !f.demo && /lucid/i.test(f.name)).length, st && st.state, st && st.account_id === a.id] : null; })()")
  ok(ac == [10000000, 'f-lu', 1, 'linked', True], f'« Créer ce compte »: created with its name, the trader\'s Lucid Trading firm (not a second one) and $100,000, then linked ({ac})')
  ok(not errs and not bad, 'no JS error, no broken file' + ('' if not errs and not bad else ': ' + ' | '.join((errs + bad)[:3])))
  br.close()
  for lang in ('en', 'es'):
    br, ctx, pg, errs, bad = trader(p, lang, True)
    pg.wait_for_selector('#main .sy-today', timeout=15000); pg.wait_for_timeout(900)
    ln = pg.evaluate(LINE); t = TXT[lang]
    ok(ln and ln['text'].startswith(t[0]) and [b['t'] for b in ln['bs']] == [t[1], t[2]] and ln['inside'] and not ln['over'], f'{lang}: the line and its two actions in that language ({ln and ln["text"][:70]})')
    br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
