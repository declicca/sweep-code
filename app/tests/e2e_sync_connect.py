"""
Sweep — connecting NinjaTrader 8 in one go (3 Nov., brief docs/parcours/CONNEXION-NINJATRADER-2026-11-03.md):
  python3 tests/e2e_sync_connect.py http://127.0.0.1:8095 [storage_state, unused: each case signs up its own trader]
 1  a trader like Mario (computer 1300, fr-CA): « Connecter » makes no key; « Télécharger » gives the add-on with a key in it;
    still nothing 2 minutes later → where to look (Control Center › New › Sweep Sync); the add-on says hello with that key and
    its 19 accounts (2 NinjaTrader simulations, 8 Apex evaluations, 5 Apex funded, 4 others) → « Relier mes 17 comptes »:
    every line filled in (« Nouveau compte »), one tap links the 17 without leaving the sheet → 17 Sweep accounts named as in
    NinjaTrader, the Apex ones with Apex Trader Funding and their phase, their size from the balance, the 4 others « À compléter »
    on Accounts, Sim101 and Playback101 still ignored, the executions sent next become trades in the right account;
 2  a trader with Apex accounts already: each line filled in with a free Sweep account of the same firm and phase, never twice;
 3  the « Relier mes comptes » sheet at 390 (touch) and 1300, light and dark, EN, FR and ES: inside the screen, nothing wider
    than the window, no English word left in FR or ES, no page error; screenshots.
"""
import io, json, os, re, sqlite3, sys, time, zipfile
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
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what, flush=True)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
ms = lambda ny: int(datetime.strptime(ny, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)
DAY = '2026-10-07'
# what NinjaTrader 8 sends for a trader like Mario: 19 accounts, balances included (add-on 1.1.0 and later)
EVALS = ['APEX-41275-%02d' % i for i in range(1, 9)]
FUNDED = ['PA-APEX-41275-%02d' % i for i in range(1, 6)]
OTHERS = ['LFE0507712', 'TPT-88812', 'MFFU-50K-3', 'BX-200417']
ACCTS = [{'name': 'Sim101', 'connection': 'Simulation', 'cash': 100000}, {'name': 'Playback101', 'connection': 'Playback', 'cash': 100000}] \
  + [{'name': n, 'connection': 'Apex', 'provider': 'Rithmic', 'currency': 'USD', 'cash': 50000 + i * 137.5} for i, n in enumerate(EVALS)] \
  + [{'name': n, 'connection': 'Apex', 'provider': 'Rithmic', 'currency': 'USD', 'cash': 100000 + i * 812} for i, n in enumerate(FUNDED)] \
  + [{'name': n, 'connection': 'Rithmic', 'provider': 'Rithmic', 'currency': 'USD', 'cash': 25000 + i * 1000} for i, n in enumerate(OTHERS)]
LANGS = {'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}
T = {'fr': {'go': 'Relier mes 17 comptes', 'do': 'Relier 17 comptes', 'new': '+ Nouveau compte', 'note': 'Chaque compte trouvé est déjà rempli', 'todo': 'À compléter'},
     'en': {'go': 'Link my 17 accounts', 'do': 'Link 17 accounts', 'new': '+ New account', 'note': 'Each account found is filled in already', 'todo': 'To complete'},
     'es': {'go': 'Vincular mis 17 cuentas', 'do': 'Vincular 17 cuentas', 'new': '+ Nueva cuenta', 'note': 'Cada cuenta encontrada ya está rellenada', 'todo': 'Por completar'}}
EN_WORDS = ['Link my', 'New account', 'Each account found', 'To complete', 'Evaluation', 'Funded', 'Choose…', 'Ignore this']

def new_trader(p, lang, phone, dark=False):
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, device_scale_factor=2 if phone else 1,
                       locale=LANGS[lang], color_scheme='dark' if dark else 'light', accept_downloads=True)
  ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  n = 'nt%d' % int(time.time() * 1000)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Mario', 'last_name': 'Test', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []
  pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.on('console', lambda m: errs.append('console: ' + m.text[:160]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
  return br, ctx, pg, errs

def tap(pg, sel):
  last = None
  for _ in range(6):
    try: pg.locator(sel).first.click(timeout=3000); pg.wait_for_timeout(250); return
    except Exception as e: last = e; pg.wait_for_timeout(300)
  raise last

def until(pg, js, timeout=20):   # asks the page (wait_for_function would eval: the app's CSP refuses it)
  end = time.time() + timeout
  while time.time() < end:
    if pg.evaluate(js): return True
    pg.wait_for_timeout(400)
  raise TimeoutError('still false after %d s: %s' % (timeout, js[:120]))

def in_screen(pg):
  return pg.evaluate("""()=>{const e=document.querySelector('#sySheet.open'); if(!e) return 'closed'; const r=e.getBoundingClientRect();
    if(r.left<-1||r.right>innerWidth+1||r.bottom>innerHeight+1) return 'outside '+JSON.stringify([r.left,r.right,r.bottom]);
    for(const b of e.querySelectorAll('button,a,input,select,code')){ if(!b.offsetParent) continue; const q=b.getBoundingClientRect(); if(q.right>r.right+1||q.left<r.left-1) return 'sticks out: '+(b.textContent||'').slice(0,30); }
    return ''}""")
wide = lambda pg: pg.evaluate("document.documentElement.scrollWidth - innerWidth")
api = lambda pg: pg.evaluate("fetch('api/sync',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json())")

def settings(pg):
  pg.goto(B + '/#settings'); pg.wait_for_selector('#main details.nav-sgd[data-i="3"]', timeout=15000)
  pg.evaluate("document.querySelector('#main details.nav-sgd[data-i=\"3\"]').open = true")
  pg.wait_for_selector('#main .sy-sec .sy-row', timeout=20000); pg.wait_for_timeout(300)

def zip_key(raw):
  z = zipfile.ZipFile(io.BytesIO(raw)); ents = {n: z.read(n).decode('utf-8') for n in z.namelist()}
  m = re.search(r'public const string EmbeddedKey = "(swk_[0-9a-f]{40})";', ents.get('AddOns/SweepSync.cs', ''))
  return (m.group(1) if m else None), ents

def push(ctx, key, accounts, fills=()):
  return ctx.request.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep NT8 1.3.0', 'accounts': accounts, 'fills': list(fills)}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})

def case_mario(p):
  br, ctx, pg, errs = new_trader(p, 'fr', False)
  settings(pg)
  tap(pg, '#main .sy-sec [data-sy="connect"][data-p="ninjatrader"]'); pg.wait_for_selector('#sySheet.open a.sy-dl', timeout=8000); pg.wait_for_timeout(400)
  ok(api(pg)['connections'] == [] and not pg.locator('#sySheet .sy-key').count(), '1 « Connecter »: no key made, none to copy')
  with pg.expect_download() as d: pg.locator('#sySheet a.sy-dl').click()
  raw = open(d.value.path(), 'rb').read(); key, ents = zip_key(raw)
  st = api(pg)
  ok(d.value.suggested_filename == 'SweepSync.zip' and sorted(ents) == ['AddOns/SweepSync.cs', 'Info.xml'] and key and 'Version = "1.3.0"' in ents['AddOns/SweepSync.cs'], f'1 « Télécharger »: SweepSync.zip, Info.xml and AddOns/SweepSync.cs (1.3.0), the key in EmbeddedKey ({sorted(ents)})')
  ok(len(st['connections']) == 1 and st['connections'][0]['downloaded_at'] > 0 and not st['connections'][0]['last_seen_at'], '1 the key was made by the download (downloaded, not seen yet)')
  # 2 minutes later and still nothing: where to look in NinjaTrader
  pg.evaluate("(() => { const n = Date.now.bind(Date); Date.now = () => n() + 130000; })()")
  until(pg, "!!document.querySelector('#sySheet .sy-late')", 15)
  ok('Toujours rien ? Dans NinjaTrader : Control Center › New › Sweep Sync. Sa fenêtre dit pourquoi.' in pg.inner_text('#sySheet .sy-late'), '1 after 2 minutes without the add-on: Control Center › New › Sweep Sync')
  pg.screenshot(path=f'{SHOTS}/nt-connect-late-1300.png')
  r = push(ctx, key, ACCTS)
  ok(r.status == 200 and len(r.json()['accounts']) == 19, f'1 the add-on says hello with the key of its download: 19 accounts received ({r.status})')
  until(pg, "(document.querySelector('#sySheet .sy-main')||{}).textContent === 'Relier mes 17 comptes'")
  ok(not pg.locator('#sySheet .sy-late').count(), '1 the add-on seen: no more « Toujours rien »')
  tap(pg, '#sySheet [data-sy="linkall"]'); pg.wait_for_selector('#sySheet.open .sy-all select', timeout=8000); pg.wait_for_timeout(400)
  rows = pg.eval_on_selector_all('#sySheet .sy-all-row', 'l => l.map(x => [x.querySelector("b").textContent, x.querySelector("select").value, (x.querySelector(".sy-all-pv")||{}).textContent || ""])')
  names = [x[0] for x in rows]
  ok(len(rows) == 17 and 'Sim101' not in names and 'Playback101' not in names and all(x[1] == 'new' for x in rows), f'1 « Relier mes comptes »: 17 lines, each « Nouveau compte » already, no simulation ({len(rows)})')
  pv = dict((x[0], x[2]) for x in rows)
  ok('Apex · Évaluation' in pv['APEX-41275-01'] and '50' in pv['APEX-41275-01'] and 'Apex · Financé' in pv['PA-APEX-41275-01'] and 'À compléter' in pv['LFE0507712'], f'1 each new account says what it will be (Apex · Évaluation · 50 000 $; À compléter) ({pv["APEX-41275-01"]} | {pv["PA-APEX-41275-01"]} | {pv["LFE0507712"]})')
  ok(pg.inner_text('#sySheet [data-sy="doall"]') == 'Relier 17 comptes' and in_screen(pg) == '' and not pg.locator('#sySheet .sy-err').count(), f'1 one button « Relier 17 comptes », no error under a line, the sheet inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/nt-mario-all-1300.png')
  n0 = pg.evaluate("location.hash")
  tap(pg, '#sySheet [data-sy="doall"]')
  until(pg, "!document.querySelector('#sySheet.open')", 40)
  ok(pg.evaluate("location.hash") == n0, '1 one tap: linked without leaving the page')
  st = api(pg); acc = pg.evaluate("S.accounts.filter(a => !a.demo).map(a => ({id: a.id, name: a.name, firm: (S.firms.find(f => f.id === a.firm_id) || {}).name || null, phase: a.phase || null, start: a.starting_balance_c}))")
  by = {a['name']: a for a in acc}
  linked = {x['name']: x['account_id'] for x in st['accounts'] if x['state'] == 'linked'}
  ok(len(acc) == 17 and sorted(by) == sorted(EVALS + FUNDED + OTHERS) and len(linked) == 17 and all(linked[n] == by[n]['id'] for n in linked), f'1 17 Sweep accounts named as in NinjaTrader, each linked to its own ({len(acc)}, {len(linked)})')
  ok(all(by[n]['firm'] == 'Apex Trader Funding' and by[n]['phase'] == 'eval' and by[n]['start'] == 5000000 for n in EVALS) and all(by[n]['firm'] == 'Apex Trader Funding' and by[n]['phase'] == 'funded' and by[n]['start'] == 10000000 for n in FUNDED), '1 the Apex accounts: Apex Trader Funding, evaluation or funded, 50K / 100K from their balance')
  ok(all(by[n]['phase'] is None for n in OTHERS) and [by[n]['firm'] for n in OTHERS] == [None, 'Take Profit Trader', 'MyFundedFutures', None] and len([f for f in pg.evaluate("S.firms.map(f => f.name)") if 'Apex' in f]) == 1, f'1 the others: a firm only when the name starts with it (13 Nov.: TPT-…, MFFU-…), none invented for LFE… or BX-…; one Apex firm for all ({[by[n]["firm"] for n in OTHERS]})')
  ok(sorted(x['name'] for x in st['accounts'] if x['state'] == 'ignored') == ['Playback101', 'Sim101'], '1 Sim101 and Playback101 still ignored')
  pg.goto(B + '/#accounts'); pg.wait_for_selector('#main table.acct-tbl', timeout=15000); pg.wait_for_timeout(800)
  todo = pg.evaluate("[...document.querySelectorAll('#main table.acct-tbl tr[data-href]')].filter(tr => tr.querySelector('.sy-todo')).map(tr => tr.children[0].textContent.trim())")
  ok(len(todo) == 2 and all(any(t.startswith(o) for o in ('LFE0507712', 'BX-200417')) for t in todo) and pg.inner_text('#main .sy-todo') == 'À compléter', f'1 Accounts: the 2 accounts without a firm say « À compléter » ({todo})')
  pg.screenshot(path=f'{SHOTS}/nt-mario-accounts-1300.png')
  # the executions sent next become trades in the right account
  fills = [{'id': 'm1', 'account': 'PA-APEX-41275-03', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 1, 'price': 21000.25, 'ts': ms(DAY + ' 09:31:05'), 'point_value': 2},
           {'id': 'm2', 'account': 'PA-APEX-41275-03', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 1, 'price': 21010.25, 'ts': ms(DAY + ' 09:40:00'), 'point_value': 2}]
  r = push(ctx, key, ACCTS, fills)
  pg.evaluate("syncNow({manual: true})"); until(pg, "S.trades.some(t => t.source === 'ninjatrader')", 20)
  tr = pg.evaluate("S.trades.filter(t => t.source === 'ninjatrader').map(t => [t.account_id, t.pnl_c])")
  ok(r.status == 200 and tr == [[by['PA-APEX-41275-03']['id'], 2000]], f'1 an execution pair sent next: one trade in PA-APEX-41275-03 (+$20) ({tr})')
  ok(wide(pg) <= 0 and not errs, f'1 nothing wider than the window, no page error {errs[:2]}')
  br.close()

def case_owned(p):   # Apex accounts in Sweep already: each line takes a free one of the same firm and phase, never twice
  br, ctx, pg, errs = new_trader(p, 'en', False)
  ctx.request.put(B + '/api/docs/firms/f-apex', data=json.dumps({'name': 'Apex Trader Funding'}), headers=H)
  for i, (nm, ph) in enumerate([('My Apex eval', 'eval'), ('My Apex PA', 'funded')]):
    ctx.request.put(B + '/api/docs/accounts/acc-o%d' % i, data=json.dumps({'name': nm, 'firm_id': 'f-apex', 'starting_balance_c': 5000000, 'status': 'active', 'money_type': ph, 'phase': ph, 'created_on': DAY}), headers=H)
  key = zip_key(ctx.request.get(B + '/api/sync/addon?platform=ninjatrader', headers=H).body())[0]
  push(ctx, key, [{'name': 'APEX-7-01', 'cash': 50100}, {'name': 'APEX-7-02', 'cash': 50000}, {'name': 'PA-APEX-7-01', 'cash': 50500}])
  settings(pg); tap(pg, '#main .sy-sec .sy-found [data-sy="linkall"]'); pg.wait_for_selector('#sySheet.open .sy-all select', timeout=8000); pg.wait_for_timeout(400)
  rows = dict(pg.eval_on_selector_all('#sySheet .sy-all-row', 'l => l.map(x => [x.querySelector("b").textContent, x.querySelector("select").value])'))
  ok(rows == {'APEX-7-01': 'acc-o0', 'APEX-7-02': 'new', 'PA-APEX-7-01': 'acc-o1'}, f'2 filled in with the free Apex accounts of the same phase, the second evaluation as a new account (no double) ({rows})')
  tap(pg, '#sySheet [data-sy="doall"]'); until(pg, "!document.querySelector('#sySheet.open')", 30)
  st = api(pg)
  ln = {x['name']: x['account_id'] for x in st['accounts'] if x['state'] == 'linked'}
  ok(ln.get('APEX-7-01') == 'acc-o0' and ln.get('PA-APEX-7-01') == 'acc-o1' and ln.get('APEX-7-02') not in (None, 'acc-o0', 'acc-o1') and pg.evaluate("S.accounts.filter(a => !a.demo).length") == 3, f'2 linked: the two existing accounts, one created; nothing doubled ({ln})')
  ok(not errs, f'2 no page error {errs[:2]}')
  br.close()

def case_layout(p, lang, phone, dark):
  tag = '%s-%s-%s' % (lang, '390' if phone else '1300', 'dark' if dark else 'light')
  br, ctx, pg, errs = new_trader(p, lang, phone, dark)
  key = zip_key(ctx.request.get(B + '/api/sync/addon?platform=ninjatrader', headers=H).body())[0]
  push(ctx, key, ACCTS)
  settings(pg); tap(pg, '#main .sy-sec .sy-found [data-sy="linkall"]'); pg.wait_for_selector('#sySheet.open .sy-all select', timeout=8000); pg.wait_for_timeout(700)
  txt = pg.inner_text('#sySheet'); x = T[lang]
  left = [w for w in EN_WORDS if lang != 'en' and w in txt.replace('MyFundedFutures', '')]   # (a firm's own name is not a text to translate)
  ok(x['note'] in txt and pg.inner_text('#sySheet [data-sy="doall"]') == x['do'] and x['new'] in txt and not left, f'{tag}: the sheet in {lang} ({left})')
  er = pg.eval_on_selector_all('#sySheet .sy-err', 'l => l.map(x => x.textContent)')
  ok(not er, f'{tag}: no error under a line before linking ({er[:2]})')
  ok(in_screen(pg) == '' and wide(pg) <= 0, f'{tag}: inside the screen, nothing wider than the window ({in_screen(pg)}, {wide(pg)})')
  pg.screenshot(path=f'{SHOTS}/nt-all-{tag}.png')
  ok(not errs, f'{tag}: no page error {errs[:2]}')
  br.close()

with sync_playwright() as p:
  case_mario(p)
  case_owned(p)
  for lang in ('fr', 'en', 'es'):
    for phone in (True, False):
      for dark in (False, True): case_layout(p, lang, phone, dark)
print('\n%s' % ('%d failed' % fails if fails else 'all passed'))
sys.exit(1 if fails else 0)
