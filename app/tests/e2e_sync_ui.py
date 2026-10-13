"""
Sweep — automatic sync, the screens (step 3), phone 390×844 (touch) and computer 1300×850, fr-CA; then EN and ES:
  python3 tests/e2e_sync_ui.py http://127.0.0.1:8095 [storage_state, unused: each case signs up its own trader]
Settings › Data › Connections → Connect (a key shown once, the 3 steps) → executions pushed with that key (as the add-on) →
« 1 account found » → its sheet: the Sweep accounts, + New account, Ignore → the preview (1 to add, 1 typed by hand completed)
→ Link → the synced trades in the journal (the hand-typed one kept its notes), the NinjaTrader chip, « Edit » only changes the
stop and target (the platform's prices stay exact), the account page says « Synced with NinjaTrader », a CSV row already synced
is « already imported », « Stop the sync » with Undo then for good. Each size: no JS error, no broken file, nothing wider than
the window, the sheet inside the screen, screenshots.
After the key (trader feedback, 13 Oct.): the connect sheet follows the add-on live (waiting → connected · 3 accounts found →
« Link my 3 accounts »), every account found is linked at once (a Sweep account with the same name chosen already, one
picked, one ignored), and a new account found later rings the bell, whose link opens its sheet.
Quantower (2nd platform, open to every trader since 13 Oct.): shown once its add-on exists (sync/addon/SweepSync-Quantower.zip),
its own block, connect sheet and key, its account found under it, linked, the Quantower chip and « Synced with Quantower ».
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
DAY = '2026-10-07'
FILLS = [   # MNQ: long 1 at 09:31 (also typed by hand), short 2 at 10:15
  {'id': 'u1', 'account': 'APEX-555-01', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 1, 'price': 21000.25, 'ts': ms(DAY + ' 09:31:05'), 'point_value': 2},
  {'id': 'u2', 'account': 'APEX-555-01', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 1, 'price': 21012.75, 'ts': ms(DAY + ' 09:36:00'), 'point_value': 2},
  {'id': 'u3', 'account': 'APEX-555-01', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 2, 'price': 21030.5, 'ts': ms(DAY + ' 10:15:00'), 'point_value': 2},
  {'id': 'u4', 'account': 'APEX-555-01', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 2, 'price': 21020.5, 'ts': ms(DAY + ' 10:22:00'), 'point_value': 2},
]

def new_trader(p, lang, phone):
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, device_scale_factor=2 if phone else 1,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  n = 'sy%d' % int(time.time() * 1000)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Lea', 'last_name': 'Test', 'experience': 'gt1'}), headers=H)
  ctx.request.put(B + '/api/docs/accounts/acc-sy', data=json.dumps({'name': 'Apex 1', 'firm_id': '', 'starting_balance_c': 5000000, 'status': 'active', 'money_type': 'eval', 'phase': 'eval', 'created_on': DAY}), headers=H)
  ctx.request.put(B + '/api/docs/trades/man-sy', data=json.dumps({'account_id': 'acc-sy', 'instrument': 'MNQ', 'date': DAY, 'session_date': True, 'entry_time': '09:32', 'exit_time': '09:36', 'direction': 'long',
    'contracts': 1, 'entry': 21000, 'exit': 21013, 'pnl_c': 2600, 'notes': 'Patient entry', 'discipline': {}, 'emo': {}, 'review': {}, 'tags': [], 'shots': []}), headers=H)
  pg = ctx.new_page(); errs = []; bad = []
  pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.on('console', lambda m: errs.append('console: ' + m.text[:160]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
  pg.on('response', lambda r: bad.append('%d %s' % (r.status, r.url[len(B):][:80])) if r.status >= 400 and '/api/' not in r.url else None)
  return br, ctx, pg, errs, bad

def tap(pg, sel):
  last = None
  for _ in range(6):
    try: pg.locator(sel).first.click(timeout=3000); pg.wait_for_timeout(250); return
    except Exception as e: last = e; pg.wait_for_timeout(300)
  raise last

def until(pg, js, timeout=15):   # waits for a condition by asking the page (wait_for_function would eval: the app's CSP refuses it)
  end = time.time() + timeout
  while time.time() < end:
    if pg.evaluate(js): return True
    pg.wait_for_timeout(400)
  raise TimeoutError('still false after %d s: %s' % (timeout, js[:120]))

def wide(pg):   # nothing wider than the window
  return pg.evaluate("document.documentElement.scrollWidth - innerWidth")

def in_screen(pg):   # the open sheet is inside the window and nothing in it sticks out
  return pg.evaluate("""()=>{const e=document.querySelector('#sySheet.open'); if(!e) return 'closed'; const r=e.getBoundingClientRect();
    if(r.left<-1||r.right>innerWidth+1||r.bottom>innerHeight+1) return 'outside '+JSON.stringify([r.left,r.right,r.bottom]);
    for(const b of e.querySelectorAll('button,a,input,code')){ if(!b.offsetParent) continue; const q=b.getBoundingClientRect(); if(q.right>r.right+1||q.left<r.left-1) return 'sticks out: '+(b.textContent||'').slice(0,30); }
    return ''}""")

def settings(pg):   # (waits of 20 s: the GitHub runner with 3 groups at once can take more than 10 s, 12 Oct.)
  pg.goto(B + '/#settings'); pg.wait_for_selector('#main details.nav-sgd[data-i="3"]', timeout=15000)
  pg.evaluate("document.querySelector('#main details.nav-sgd[data-i=\"3\"]').open = true")
  pg.wait_for_selector('#main .sy-sec .sy-row', timeout=20000); pg.wait_for_timeout(300)

def case_fr(p, phone):
  tag = '390' if phone else '1300'
  br, ctx, pg, errs, bad = new_trader(p, 'fr', phone)
  pg.goto(B + '/#import'); pg.wait_for_selector('#main .sy-tip[data-sytip="tipImport"]', timeout=20000); pg.wait_for_timeout(300)
  ok('Sur NinjaTrader 8 ? Connecte-le une fois' in pg.inner_text('#main .sy-tip') and pg.locator('#main .sy-tip [data-sy="connect"]').count() == 1 and wide(pg) <= 0, f'{tag}: import page: « Sur NinjaTrader 8 ? Connecte-le une fois » with Connecter, nothing too wide')
  pg.screenshot(path=f'{SHOTS}/sync-tip-import-{tag}.png')
  pg.goto(B + '/#accounts'); pg.wait_for_timeout(800)
  pg.evaluate("(()=>{const all=document.querySelectorAll('#main [data-act=\"acct-add\"][data-v=\"1\"]'); const b=all[all.length-1]; if(b && !document.querySelector('#main form[data-form=\"account\"]')) b.click();})()")
  pg.wait_for_selector('#main .acct-add .sy-tip[data-sytip="tipAcct"]', timeout=20000); pg.wait_for_timeout(300)
  ok('Tu trades sur NinjaTrader 8 ? Connecte-le' in pg.inner_text('#main .acct-add .sy-tip') and wide(pg) <= 0, f'{tag}: under « Add account »: « Tu trades sur NinjaTrader 8 ? Connecte-le »')
  pg.screenshot(path=f'{SHOTS}/sync-tip-account-{tag}.png')
  settings(pg)
  sec = pg.locator('#main .sy-sec')
  ok(pg.evaluate("!!document.querySelector('#main details.nav-sgd[data-i=\"3\"] .sy-sec')") and 'Connexions' in sec.inner_text() and 'NinjaTrader 8' in sec.inner_text() and 'Tes trades arrivent seuls' in sec.inner_text(), f'{tag}: Réglages › Données › Connexions, NinjaTrader 8 not connected yet')
  tap(pg, '#main .sy-sec [data-sy="connect"]'); pg.wait_for_selector('#sySheet.open .sy-key code', timeout=8000); pg.wait_for_timeout(500)
  key = pg.inner_text('#sySheet .sy-key code').strip(); txt = pg.inner_text('#sySheet')
  ok(key.startswith('swk_') and len(key) == 44 and 'Connecter NinjaTrader 8' in txt and 'Tools › Import › NinjaScript Add-On' in txt and 'ne peut jamais passer un ordre' in txt, f'{tag}: connect sheet: the key, the 3 steps, the key cannot trade')
  dl = pg.evaluate("(async()=>{const a=document.querySelector('#sySheet a[download]'); if(!a) return null; const r=await fetch(a.href,{headers:{'X-Requested-With':'fetch'}}); const b=new Uint8Array(await r.arrayBuffer()); return [a.textContent.trim(), r.status, r.headers.get('content-type'), b.length, String.fromCharCode(b[0],b[1])]})()")
  ok(dl and dl[0] == 'Télécharger' and dl[1] == 200 and dl[2] == 'application/zip' and dl[3] > 1000 and dl[4] == 'PK', f'{tag}: « Télécharger » gives the add-on (zip) ({dl})')
  ok(in_screen(pg) == '', f'{tag}: connect sheet inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/sync-connect-{tag}.png')
  tap(pg, '#sySheet [data-sy="copy"]'); pg.wait_for_timeout(300)
  tap(pg, '#sySheet [data-sy="close"].sy-main'); pg.wait_for_timeout(500)
  ok(not pg.locator('#sySheet.open').count(), f'{tag}: « Terminé » closes the sheet')
  # the add-on pushes (key only)
  r = ctx.request.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep NT8 test', 'accounts': [{'name': 'APEX-555-01', 'connection': 'Apex', 'provider': 'Rithmic'}], 'fills': FILLS}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  ok(r.status == 200, f'{tag}: executions received with the key')
  pg.evaluate("SweepSync.load()"); pg.wait_for_timeout(600)
  sec_t = pg.inner_text('#main .sy-sec')
  ok('1 compte trouvé' in sec_t and 'APEX-555-01' in sec_t and 'Apex · Évaluation' in sec_t and 'À relier' in sec_t and 'Add-on vu' in sec_t, f'{tag}: « 1 compte trouvé », the account (Apex · Évaluation, à relier), add-on seen')
  pg.screenshot(path=f'{SHOTS}/sync-settings-{tag}.png', full_page=False)
  tap(pg, '#main .sy-sec .sy-found [data-sy="linkall"]'); pg.wait_for_selector('#sySheet.open .sy-opts', timeout=8000)
  opts = pg.inner_text('#sySheet .sy-opts')
  chips = pg.eval_on_selector_all('#sySheet .sy-sub .sy-chip', 'l => l.map(x => x.textContent)')
  ok(chips == ['Apex · Évaluation', 'Rithmic'], f'{tag}: the account\'s chips, « Apex » once ({chips})')
  ok('Apex 1' in opts and '+ Nouveau compte' in opts and 'Ignorer ce compte' in opts and 'C’est quel compte Sweep ?' in pg.inner_text('#sySheet'), f'{tag}: link sheet: the Sweep account, + Nouveau compte, Ignorer ce compte')
  tap(pg, '#sySheet [data-sy="pick"][data-v="acc-sy"]'); pg.wait_for_selector('#sySheet .sy-pv li:not(.muted)', timeout=8000); pg.wait_for_timeout(300)
  pv = pg.inner_text('#sySheet .sy-pv')
  ok('1 trade à ajouter' in pv and '1 trade saisi à la main, complété (tes notes restent)' in pv, f'{tag}: preview: 1 trade to add, 1 typed by hand completed')
  ok(in_screen(pg) == '', f'{tag}: link sheet inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/sync-link-{tag}.png')
  tap(pg, '#sySheet [data-sy="link"]'); pg.wait_for_timeout(1500)
  ok(not pg.locator('#sySheet.open').count() and 'Relié à Apex 1 · 2 trades' in pg.inner_text('#main .sy-sec'), f'{tag}: linked: sheet closed, « Relié à Apex 1 · 2 trades »')
  pg.wait_for_function("S.trades.filter(t => t.source === 'ninjatrader').length === 2", timeout=15000)
  man = pg.evaluate("S.trades.find(t => t.id === 'man-sy')")
  ok(man and man.get('notes') == 'Patient entry' and man.get('source') == 'ninjatrader' and man.get('entry') == 21000.25 and len(S_trades(pg)) == 2, f'{tag}: the hand-typed trade completed (notes kept, exact entry 21,000.25), no double')
  sid = pg.evaluate("S.trades.find(t => t.source === 'ninjatrader' && t.id !== 'man-sy').id")
  pg.goto(B + '/#trade/' + sid); pg.wait_for_selector('#main .th-head .lbl .sy-chip', timeout=20000)
  ok(pg.inner_text('#main .th-head .lbl .sy-chip') == 'NinjaTrader', f'{tag}: trade page: the NinjaTrader chip')
  tap(pg, '#main [data-act="edit-trade"]'); pg.wait_for_selector('#sySheet.open [data-syf="stop"]', timeout=8000)
  ok(not pg.locator('#tkSlide.open').count() and 'viennent de NinjaTrader' in pg.inner_text('#sySheet'), f'{tag}: « Modifier » opens the stop / target editor, not the trade form')
  pg.screenshot(path=f'{SHOTS}/sync-edit-{tag}.png')
  pg.fill('#sySheet [data-syf="stop"]', '21035,5'); pg.fill('#sySheet [data-syf="target"]', '21010'); tap(pg, '#sySheet [data-sy="save-edit"]'); pg.wait_for_timeout(800)
  t = pg.evaluate("S.trades.find(t => t.id === '%s')" % sid)
  ok(t['stop'] == 21035.5 and t['target'] == 21010 and t['entry'] == 21030.5 and t['exit'] == 21020.5 and t['pnl_c'] == 4000 and t.get('risk_c') == 2000, f'{tag}: stop 21,035.5 and target saved (risk $20), prices and P&L unchanged')
  pg.goto(B + '/#account/acc-sy'); pg.wait_for_selector('#main .sy-acct', timeout=20000)
  ok('Synchronisé avec NinjaTrader · APEX-555-01' in pg.inner_text('#main .sy-acct'), f'{tag}: account page: « Synchronisé avec NinjaTrader · APEX-555-01 »')
  pg.wait_for_timeout(700); pg.screenshot(path=f'{SHOTS}/sync-account-{tag}.png')
  # CSV import of the same trade (Tradovate Performance): already imported
  csv = 'symbol,_priceFormat,_priceFormatType,_tickSize,buyFillId,sellFillId,qty,buyPrice,sellPrice,pnl,boughtTimestamp,soldTimestamp,duration\nMNQZ6,-2,0,0.25,111,112,2,21020.50,21030.50,$40.00,10/07/2026 10:22:00,10/07/2026 10:15:00,7min\n'
  pg.goto(B + '/#import'); pg.wait_for_selector('#main input[type=file]', state='attached', timeout=10000)
  pg.set_input_files('#main input[type=file]', files=[{'name': 'perf.csv', 'mimeType': 'text/csv', 'buffer': csv.encode()}]); pg.wait_for_timeout(1200)
  k = pg.evaluate("(IMP.rows||[]).map(r => r.key)")
  ok(len(k) == 1 and k[0].startswith('sync:') and pg.locator('#main [data-act="imp-go"][disabled]').count() == 1, f'{tag}: CSV row already synced → « déjà importé », nothing to import ({k})')
  # stop: Undo, then for good
  settings(pg); tap(pg, '#main .sy-sec [data-sy="manage"]'); pg.wait_for_selector('#sySheet.open [data-sy="stop"]', timeout=8000); pg.wait_for_timeout(600)   # the sheet slides in
  mt = pg.inner_text('#sySheet')
  ok('Sweep NT8 test' in mt and 'Arrêter la synchro' in mt and 'Nouvelle clé' in mt, f'{tag}: manage sheet: add-on version, new key, stop')
  ok(in_screen(pg) == '', f'{tag}: manage sheet inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/sync-manage-{tag}.png')
  tap(pg, '#sySheet [data-sy="stop"]'); pg.wait_for_selector('.nav-undo.on button', timeout=5000)
  ok('Synchro arrêtée' in pg.inner_text('.nav-undo') and pg.locator('#main .sy-sec [data-sy="connect"][data-p="ninjatrader"]').count() == 1, f'{tag}: « Synchro arrêtée · Annuler »')
  tap(pg, '.nav-undo button'); pg.wait_for_timeout(5600)
  st = pg.evaluate("fetch('api/sync',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json())")
  ok(len(st['connections']) == 1, f'{tag}: Undo → the key still works')
  settings(pg); tap(pg, '#main .sy-sec [data-sy="manage"]'); tap(pg, '#sySheet [data-sy="stop"]'); pg.wait_for_timeout(5000)
  # the key is revoked when « Undo » is over (5 s), then the request: waited for, not a fixed delay (a busy machine is slower)
  pg.wait_for_function("fetch('api/sync',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json()).then(d=>!d.connections.length)", timeout=20000, polling=500)
  st = pg.evaluate("fetch('api/sync',{headers:{'X-Requested-With':'fetch'}}).then(r=>r.json())")
  r = ctx.request.post(B + '/api/sync/push', data=json.dumps({'fills': []}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  ok(len(st['connections']) == 0 and r.status == 401 and pg.evaluate("S.trades.filter(t => t.source === 'ninjatrader').length") == 2, f'{tag}: stopped for good: key revoked (401), the synced trades stay ({[c["platform"] for c in st["connections"]]}, {r.status})')
  ok(wide(pg) <= 0, f'{tag}: nothing wider than the window ({wide(pg)} px)')
  ok(not errs, f'{tag}: no JS error {errs[:3]}')
  ok(not bad, f'{tag}: no broken file {bad[:3]}')
  br.close()

def S_trades(pg): return pg.evaluate("S.trades.filter(t => !t.demo)")

def case_multi(p, phone):   # after the key: the sheet follows the add-on; several accounts linked at once; the bell
  tag = 'M' + ('390' if phone else '1300')
  br, ctx, pg, errs, bad = new_trader(p, 'fr', phone)
  ctx.request.put(B + '/api/docs/accounts/acc-sy2', data=json.dumps({'name': 'APEX-777-02', 'firm_id': '', 'starting_balance_c': 5000000, 'status': 'active', 'money_type': 'eval', 'phase': 'eval', 'created_on': DAY}), headers=H)
  settings(pg)
  tap(pg, '#main .sy-sec [data-sy="connect"][data-p="quantower"]'); pg.wait_for_selector('#sySheet.open .sy-key code', timeout=8000); pg.wait_for_timeout(500)
  key = pg.inner_text('#sySheet .sy-key code').strip(); txt = pg.inner_text('#sySheet')
  ok('Reviens ici : les comptes que l’add-on trouve' in txt and 'En attente de l’add-on…' in txt and pg.inner_text('#sySheet .sy-main') == 'Terminé', f'{tag}: connect sheet: « Reviens ici », waiting for the add-on')
  accs = [{'name': 'APEX-555-01', 'connection': 'Rithmic'}, {'name': 'APEX-777-02', 'connection': 'Rithmic'}, {'name': 'PA-APEX-3-01', 'connection': 'Rithmic'}]
  r = ctx.request.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep Quantower test', 'accounts': accs, 'fills': FILLS}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  until(pg, "(document.querySelector('#sySheet .sy-main')||{}).textContent === 'Relier mes 3 comptes'")
  ok(r.status == 200 and 'Add-on connecté · 3 comptes trouvés' in pg.inner_text('#sySheet .sy-live'), f'{tag}: the open sheet follows the add-on: « Add-on connecté · 3 comptes trouvés », « Relier mes 3 comptes »')
  ok(in_screen(pg) == '', f'{tag}: connect sheet inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/sync-live-{tag}.png')
  tap(pg, '#sySheet [data-sy="linkall"]'); pg.wait_for_selector('#sySheet.open .sy-all select', timeout=8000); pg.wait_for_timeout(400)
  rows = pg.eval_on_selector_all('#sySheet .sy-all-row', 'l => l.map(x => [x.querySelector("b").textContent, x.querySelector("select").value])')
  ok(pg.inner_text('#sySheet .sy-head h2') == 'Relier mes comptes' and [r0 for r0, _ in rows] == ['APEX-555-01', 'APEX-777-02', 'PA-APEX-3-01'] and dict(rows)['APEX-777-02'] == 'acc-sy2' and dict(rows)['APEX-555-01'] == '', f'{tag}: all the accounts found at once; the Sweep account with the same name chosen already ({rows})')
  sel = pg.locator('#sySheet .sy-all-row').nth(0).locator('select'); sel.select_option('acc-sy'); pg.wait_for_timeout(300)
  pg.locator('#sySheet .sy-all-row').nth(2).locator('select').select_option('ignore'); pg.wait_for_timeout(300)
  until(pg, "[...document.querySelectorAll('#sySheet .sy-all-pv')].length === 2 && ![...document.querySelectorAll('#sySheet .sy-all-pv')].some(x => x.textContent.includes('Chargement'))", 10)
  pv = pg.eval_on_selector_all('#sySheet .sy-all-pv', 'l => l.map(x => x.textContent)')
  dis = pg.evaluate("[...document.querySelectorAll('#sySheet .sy-all-row')[2].querySelectorAll('option')].filter(o => o.disabled).map(o => o.value).sort()")
  ok('1 trade à ajouter · 1 trade saisi à la main, complété (tes notes restent)' in pv[0] and 'Aucun trade pour l’instant' in pv[1] and dis == ['acc-sy', 'acc-sy2'], f'{tag}: a preview under each chosen account; a Sweep account chosen once is not offered again ({pv}, {dis})')
  ok(pg.inner_text('#sySheet [data-sy="doall"]') == 'Relier 2 comptes' and in_screen(pg) == '', f'{tag}: « Relier 2 comptes », inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/sync-all-{tag}.png')
  tap(pg, '#sySheet [data-sy="doall"]'); pg.wait_for_selector('#toast.on', timeout=10000)
  toast = pg.inner_text('#toast'); pg.wait_for_timeout(1500)
  qb = pg.inner_text('#main .sy-plat[data-p="quantower"]')
  ok(toast == '2 comptes reliés · 2 trades ajoutés', f'{tag}: « 2 comptes reliés · 2 trades ajoutés » ({toast})')
  ok(not pg.locator('#sySheet.open').count() and 'Relié à Apex 1 · 2 trades' in qb and 'Relié à APEX-777-02' in qb and 'Ignoré' in qb, f'{tag}: linked at once: sheet closed, Apex 1 (2 trades), APEX-777-02, the third ignored')
  # a 4th account found later: the bell's notification opens its sheet
  ctx.request.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep Quantower test', 'accounts': [{'name': 'APEX-999-09'}], 'fills': []}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  nt = ctx.request.get(B + '/api/notifications', headers=H).json()
  found = [n for n in nt.get('items', []) if n.get('type') == 'sync_found']
  ok(len(found) == 1 and found[0]['params'] == {'n': 3, 'platform': 'Quantower'} and found[0]['action_url'] == '#settings/sync', f'{tag}: one bell notification for the accounts found that day ({[(n["params"], n["action_url"]) for n in found]})')
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(1500)
  tap(pg, '[data-nt="bell"]:visible'); pg.wait_for_selector('.nt-item', timeout=8000); pg.wait_for_timeout(400)
  item = pg.locator('.nt-item', has_text='Quantower a trouvé tes comptes').first
  ok(item.count() == 1 and '3 à relier à tes comptes Sweep' in item.inner_text(), f'{tag}: the bell: « Quantower a trouvé tes comptes · 3 à relier… »')
  item.click(); pg.wait_for_selector('#sySheet.open', timeout=20000); pg.wait_for_timeout(600)
  ok(pg.inner_text('#sySheet .sy-head h2') == 'APEX-999-09' and pg.evaluate("location.hash") == '#settings' and pg.evaluate("document.querySelector('#main details.nav-sgd[data-i=\"3\"]').open"), f'{tag}: its link opens Settings › Data and the sheet of the account still to link ({pg.evaluate("location.hash")})')
  ok(wide(pg) <= 0, f'{tag}: nothing wider than the window ({wide(pg)} px)')
  ok(not errs, f'{tag}: no JS error {errs[:3]}')
  ok(not bad, f'{tag}: no broken file {bad[:3]}')
  br.close()

def case_quantower(p, phone):   # the 2nd platform: its block, connect sheet, account found, link, chip
  tag = 'Q' + ('390' if phone else '1300')
  br, ctx, pg, errs, bad = new_trader(p, 'fr', phone)
  settings(pg)
  blocks = pg.eval_on_selector_all('#main .sy-sec .sy-plat', 'l => l.map(x => x.dataset.p)')
  ok(blocks == ['ninjatrader', 'quantower'] and 'Tes trades arrivent seuls depuis Quantower' in pg.inner_text('#main .sy-plat[data-p="quantower"]'), f'{tag}: Connections: NinjaTrader 8 then Quantower, each with « Connecter » ({blocks})')
  tap(pg, '#main .sy-sec [data-sy="connect"][data-p="quantower"]'); pg.wait_for_selector('#sySheet.open .sy-key code', timeout=8000); pg.wait_for_timeout(500)
  key = pg.inner_text('#sySheet .sy-key code').strip(); txt = pg.inner_text('#sySheet')
  ok(key.startswith('swk_') and 'Connecter Quantower' in txt and 'Télécharge l’add-on Sweep pour Quantower' in txt and 'Settings › Scripts › plug-ins' in txt and 'ouvre le panneau Sweep Sync' in txt and 'NinjaScript' not in txt, f'{tag}: Quantower connect sheet: its key and its own 3 steps')
  dl = pg.evaluate("(async()=>{const a=document.querySelector('#sySheet a[download]'); if(!a) return null; const r=await fetch(a.href,{headers:{'X-Requested-With':'fetch'}}); const b=new Uint8Array(await r.arrayBuffer()); return [a.getAttribute('href'), r.status, String.fromCharCode(b[0],b[1])]})()")
  ok(dl and dl[0] == 'api/sync/addon?platform=quantower' and dl[1] == 200 and dl[2] == 'PK', f'{tag}: « Télécharger » gives the Quantower add-on ({dl})')
  ok(in_screen(pg) == '', f'{tag}: connect sheet inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/sync-q-connect-{tag}.png')
  tap(pg, '#sySheet [data-sy="close"].sy-main'); pg.wait_for_timeout(500)
  r = ctx.request.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep Quantower test', 'accounts': [{'name': 'APEX-555-01', 'connection': 'Rithmic'}], 'fills': FILLS}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  ok(r.status == 200, f'{tag}: executions received with the Quantower key')
  pg.evaluate("SweepSync.load()"); pg.wait_for_timeout(600)
  qb, nb = pg.inner_text('#main .sy-plat[data-p="quantower"]'), pg.inner_text('#main .sy-plat[data-p="ninjatrader"]')
  ok('1 compte trouvé' in qb and 'APEX-555-01' in qb and 'Add-on vu' in qb and 'APEX-555-01' not in nb and 'Connecter' in nb, f'{tag}: the account found under Quantower only')
  ok(wide(pg) <= 0, f'{tag}: two platforms, nothing wider than the window ({wide(pg)} px)')
  pg.screenshot(path=f'{SHOTS}/sync-q-settings-{tag}.png')
  tap(pg, '#main .sy-plat[data-p="quantower"] .sy-found [data-sy="linkall"]'); tap(pg, '#sySheet [data-sy="pick"][data-v="acc-sy"]'); pg.wait_for_selector('#sySheet .sy-pv li:not(.muted)', timeout=8000)
  tap(pg, '#sySheet [data-sy="link"]'); pg.wait_for_timeout(1500)
  ok('Relié à Apex 1 · 2 trades' in pg.inner_text('#main .sy-plat[data-p="quantower"]'), f'{tag}: linked under Quantower')
  pg.wait_for_function("S.trades.filter(t => t.source === 'quantower').length === 2", timeout=15000)
  sid = pg.evaluate("S.trades.find(t => t.source === 'quantower' && t.id !== 'man-sy').id")
  pg.goto(B + '/#trade/' + sid); pg.wait_for_selector('#main .th-head .lbl .sy-chip', timeout=20000)
  ok(pg.inner_text('#main .th-head .lbl .sy-chip') == 'Quantower', f'{tag}: trade page: the Quantower chip')
  tap(pg, '#main [data-act="edit-trade"]'); pg.wait_for_selector('#sySheet.open [data-syf="stop"]', timeout=8000)
  ok('viennent de Quantower' in pg.inner_text('#sySheet') and not pg.locator('#tkSlide.open').count(), f'{tag}: « Modifier »: stop / target only, « viennent de Quantower »')
  tap(pg, '#sySheet [data-sy="close"]'); pg.wait_for_timeout(400)
  pg.goto(B + '/#account/acc-sy'); pg.wait_for_selector('#main .sy-acct', timeout=20000)
  ok('Synchronisé avec Quantower · APEX-555-01' in pg.inner_text('#main .sy-acct'), f'{tag}: account page: « Synchronisé avec Quantower · APEX-555-01 »')
  settings(pg); tap(pg, '#main .sy-plat[data-p="quantower"] [data-sy="manage"]'); pg.wait_for_selector('#sySheet.open [data-sy="stop"]', timeout=8000); pg.wait_for_timeout(600)
  ok(pg.inner_text('#sySheet .sy-head h2') == 'Quantower' and 'Sweep Quantower test' in pg.inner_text('#sySheet'), f'{tag}: manage sheet: Quantower, its add-on version')
  ok(in_screen(pg) == '', f'{tag}: manage sheet inside the screen ({in_screen(pg)})')
  pg.screenshot(path=f'{SHOTS}/sync-q-manage-{tag}.png')
  ok(not errs, f'{tag}: no JS error {errs[:3]}')
  ok(not bad, f'{tag}: no broken file {bad[:3]}')
  br.close()

def case_lang(p, lang):   # the section, the sheets and the preview in English and Spanish (never a French or English word left)
  br, ctx, pg, errs, bad = new_trader(p, lang, True)
  pg.goto(B + '/#import'); pg.wait_for_selector('#main .sy-tip', timeout=20000)
  tip = pg.inner_text('#main .sy-tip')
  ok(({'en': 'On NinjaTrader 8? Connect it once', 'es': '¿En NinjaTrader 8? Conéctalo una vez'}[lang]) in tip and (lang == 'en' or 'Connect it' not in tip), f'{lang}: import page invitation translated')
  settings(pg)
  W = {'en': ['Connections', 'Your trades arrive on their own', 'Connect'], 'es': ['Conexiones', 'Tus operaciones llegan solas', 'Conectar']}[lang]
  s = pg.inner_text('#main .sy-sec')
  ok(all(w in s for w in W), f'{lang}: Connections section translated')
  tap(pg, '#main .sy-sec [data-sy="connect"]'); pg.wait_for_selector('#sySheet.open .sy-key code', timeout=8000)
  key = pg.inner_text('#sySheet .sy-key code').strip(); txt = pg.inner_text('#sySheet')
  ok(({'en': 'Paste your key', 'es': 'Pega tu clave'}[lang]) in txt and 'Colle' not in txt and (lang == 'en' or 'Paste' not in txt), f'{lang}: connect sheet translated')
  tap(pg, '#sySheet [data-sy="close"].sy-main')
  ctx.request.post(B + '/api/sync/push', data=json.dumps({'fills': FILLS}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  pg.evaluate("SweepSync.load()"); pg.wait_for_timeout(600)
  tap(pg, '#main .sy-sec .sy-found [data-sy="linkall"]'); tap(pg, '#sySheet [data-sy="pick"][data-v="acc-sy"]'); pg.wait_for_selector('#sySheet .sy-pv li:not(.muted)', timeout=8000)
  pv = pg.inner_text('#sySheet')
  ok(({'en': '1 trade to add', 'es': '1 operación por añadir'}[lang]) in pv and 'trade à ajouter' not in pv, f'{lang}: preview translated')
  tap(pg, '#sySheet [data-sy="close"]'); pg.wait_for_timeout(400)
  pg.wait_for_selector('#main .sy-sec [data-sy="connect"][data-p="quantower"]', timeout=20000)
  tap(pg, '#main .sy-sec [data-sy="connect"][data-p="quantower"]'); pg.wait_for_selector('#sySheet.open .sy-key code', timeout=8000)
  q = pg.inner_text('#sySheet')
  ok(({'en': 'In Quantower, open the Sweep Sync panel', 'es': 'En Quantower, abre el panel Sweep Sync'}[lang]) in q and ({'en': 'Connect Quantower', 'es': 'Conectar Quantower'}[lang]) in q and 'Dans Quantower' not in q, f'{lang}: Quantower connect sheet translated')
  ok(not errs, f'{lang}: no JS error {errs[:3]}')
  br.close()

def case_trader(p):   # every trader sees Connections (the beta for administrators ended on 12 Oct.)
  br, ctx, pg, errs, bad = new_trader(p, 'fr', True)
  pg.goto(B + '/#settings'); pg.wait_for_selector('#main details.nav-sgd[data-i="3"]', timeout=15000)
  pg.evaluate("document.querySelector('#main details.nav-sgd[data-i=\"3\"]').open = true"); pg.wait_for_timeout(1200)
  ok(pg.evaluate("S.me && !S.me.is_admin") and pg.locator('#main .sy-sec').count() == 1 and not errs, 'a trader who is not an administrator sees Connections')
  # the platforms come with the section's own load (api/sync): waited for, not 1.2 s (the GitHub machine was slower, 13 Oct.)
  try: pg.wait_for_selector('#main .sy-sec .sy-plat[data-p="quantower"]', timeout=15000)
  except Exception: pass
  blocks = pg.eval_on_selector_all('#main .sy-sec .sy-plat', 'l => l.map(x => x.dataset.p)')
  ok(blocks == ['ninjatrader', 'quantower'], f'a trader sees NinjaTrader 8 and Quantower in Connections ({blocks})')
  pg.goto(B + '/#import'); pg.wait_for_selector('#main .sy-tip [data-sy="connect"]', timeout=20000)
  tap(pg, '#main .sy-tip [data-sy="connect"]'); pg.wait_for_selector('#sySheet.open .sy-key code', timeout=8000)
  ok(pg.inner_text('#sySheet .sy-key code').startswith('swk_'), 'the invitation\'s « Connecter » opens the connect sheet with the key')
  tap(pg, '#sySheet [data-sy="close"].sy-main'); pg.goto(B + '/#accounts'); pg.goto(B + '/#import'); pg.wait_for_timeout(1500)
  ok(pg.locator('#main .sy-tip').count() == 0 and pg.locator('#main #drop').count() == 1 and not errs, 'connected: no more invitation on the import page')
  br.close()

with sync_playwright() as p:
  case_trader(p)
  case_fr(p, True)
  case_fr(p, False)
  case_lang(p, 'en')
  case_lang(p, 'es')
  case_quantower(p, True)
  case_quantower(p, False)
  case_multi(p, True)
  case_multi(p, False)
print('\n%s' % ('%d failed' % fails if fails else 'all passed'))
sys.exit(1 if fails else 0)
