"""
Sweep — copy groups with a master account (brief « avance concurrentielle », step 2), Playwright:
  python3 tests/e2e_copy_group.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
A new trader with 4 Apex accounts: Apex 1 (the master), Apex 2 (×1), Apex 3 (×2, $4 commission, drawdown and payout rules),
Apex 4 (synced itself with NinjaTrader through the real sync routes). At 390 × 844 (touch) and 1300 × 850, light and dark,
EN / FR / ES:
 - Accounts › « Copy trading » › « Create a copy group »: the sheet (master, followers, × multiplier, « Synced » note), saved;
 - a trade typed on the master: the form chooses Apex 2 and 3, never Apex 4 (synced: its own trade, no double); Apex 3 at
   2 contracts, P&L × 2, its commission; its balance, drawdown margin and payout counter move;
 - the Journal: one row « ×3 accounts » that unfolds (each account, its contracts, its P&L);
 - editing the master's trade asks « Apply to the group? » → the copies follow (a loss now: Apex 3's margin drops);
 - a trade synced on the master (the add-on's push): the server copies it on Apex 2 and 3, Apex 4's own synced trade joins
   the group (« ×4 accounts »), no double;
 - deleting the master's trade asks: « Delete on all 3 accounts » → gone, « Undo » brings them back;
 - Free (billing on, a second server at port + 1): the card says Pro, « Create a copy group » opens the plans sheet.
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import json, os, signal, sqlite3, subprocess, sys, time, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APPDIR = os.path.dirname(os.path.dirname(DB))   # the served copy (each shard has its own)
P1 = int(B.rsplit(':', 1)[1]) + 1; B1 = f'http://127.0.0.1:{P1}'
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def sql(q, args=()):
  d = sqlite3.connect(DB, timeout=10); c = d.execute(q, args); r = c.fetchall(); d.commit(); d.close(); return r
def unthrottle():
  try: sql('DELETE FROM attempts')
  except Exception: pass
def ms(ny): return int(datetime.strptime(ny, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)
X = {
  'en': {'title': 'Copy trading', 'create': 'Create a copy group', 'sheet': 'Copy group', 'synced': 'Synced: its own trades count, never a copy', 'saved': 'Copy group saved',
         'x3': '×3 accounts', 'x4': '×4 accounts', 'editT': 'Apply to the group?', 'editAll': 'Apply to all 3 accounts', 'delT': 'Delete this trade?', 'delAll': 'Delete on all 3 accounts',
         'pw': 'Log once, on every account'},
  'fr': {'title': 'Copy trading', 'create': 'Créer un groupe de copie', 'sheet': 'Groupe de copie', 'synced': 'Synchronisé : ses propres trades comptent, jamais une copie', 'saved': 'Groupe de copie enregistré',
         'x3': '×3 comptes', 'x4': '×4 comptes', 'editT': 'Appliquer au groupe ?', 'editAll': 'Appliquer aux 3 comptes', 'delT': 'Supprimer ce trade ?', 'delAll': 'Supprimer sur les 3 comptes',
         'pw': 'Une saisie, sur tous tes comptes'},
  'es': {'title': 'Copy trading', 'create': 'Crear un grupo de copia', 'sheet': 'Grupo de copia', 'synced': 'Sincronizada: cuentan sus propias operaciones, nunca una copia', 'saved': 'Grupo de copia guardado',
         'x3': '×3 cuentas', 'x4': '×4 cuentas', 'editT': '¿Aplicar al grupo?', 'editAll': 'Aplicar a las 3 cuentas', 'delT': '¿Eliminar esta operación?', 'delAll': 'Eliminar en las 3 cuentas',
         'pw': 'Un registro, en todas tus cuentas'},
}
SEED = """() => {
  put('firms', { id: 'apx', name: 'Apex' });
  const A = (id, name, extra) => put('accounts', Object.assign({ id, name, firm_id: 'apx', starting_balance_c: 5000000, status: 'active', phase: 'funded', money_type: 'funded', created_on: todayStr(), rules: {} }, extra || {}));
  A('M', 'Apex 1'); A('F1', 'Apex 2'); A('F2', 'Apex 3', { fee_rt_c: 400, rules: { dd_c: 250000, dd_type: 'eod', payout_win_days: 5, payout_win_min_c: 20000 } }); A('S', 'Apex 4');
  render(); return todayStr(); }"""
TXT = "(sel) => [...document.querySelectorAll(sel)].filter((e) => e.getClientRects().length).map((e) => e.textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim())"
# (from e2e_weekly_share) elements and text that run past the window, scrolling rows apart (the invisible touch areas of
# small links, pseudo-elements clipped by the page, are not content)
WIDE = """(()=>{ const W = document.documentElement.clientWidth, out = [];
  const name = (e) => e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\\s+/).slice(0, 2).join('.');
  const inside = (e) => { for (let x = e; x; x = x.parentElement) { const c = getComputedStyle(x); if (x === document.body) break; if (c.position === 'fixed' || (x !== e && c.overflowX !== 'visible' && x.getBoundingClientRect().right <= W + .5)) return true; } return false; };   // body / html clip the page itself: not a scrolling row
  document.querySelectorAll('body *').forEach((e) => {
    const r = e.getBoundingClientRect(); if (!r.width || inside(e)) return;
    if (r.right > W + .5) out.push(name(e) + ' ' + Math.round(r.right) + 'px');
  });
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);   // text running out of its box
  for (let n = tw.nextNode(); n; n = tw.nextNode()) { if (!n.textContent.trim() || inside(n.parentElement)) continue; const g = document.createRange(); g.selectNodeContents(n); const r = g.getBoundingClientRect();
    if (r.right > W + .5) out.push('text « ' + n.textContent.trim().slice(0, 30) + ' » in ' + name(n.parentElement) + ' ' + Math.round(r.right) + 'px'); }
  return { sw: document.documentElement.scrollWidth, w: innerWidth, cw: W, out: out.slice(-8) }; })()"""
wide = lambda pg: pg.evaluate(WIDE)['out']
ON = "(acc) => S.trades.filter((t) => t.account_id === acc && !t.demo).map((t) => ({ id: t.id, at: String(t.entry_time || '').slice(0, 5), n: t.contracts, pnl: t.pnl_c, fees: t.fees_c || 0, g: t.copy_group || null, src: t.copy_src || null, source: t.source || null })).sort((a, b) => a.at < b.at ? -1 : 1)"
ST = "(acc) => { const a = getDoc('accounts', acc), s = acctState(a), q = window.SweepPayout && SweepPayout.status(a); return { bal: s.bal, buffer: s.buffer, pct: q ? q.pct : null }; }"

def tap(pg, sel, phone):
  if phone: pg.locator(sel).first.tap()
  else: pg.locator(sel).first.click()

def run(p, lang, phone, dark):
  tag = f"{'390' if phone else '1300'}-{lang}-{'dark' if dark else 'light'}"; x = X[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True,
                       locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], color_scheme='dark' if dark else 'light')
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cg%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Zoé', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  day = pg.evaluate(SEED); pg.wait_for_timeout(1500)
  # the add-on (no session, its key only): Apex 4 synced with its 10:00 trade
  key = ctx.request.post(B + '/api/sync/key', data=json.dumps({'platform': 'ninjatrader'}), headers=H).json()['key']
  AK = {'Content-Type': 'application/json', 'X-Sweep-Key': key}
  F = lambda i, acct, side, q, px, hm: {'id': i, 'account': acct, 'contract': 'NQ 12-26', 'side': side, 'qty': q, 'price': px, 'ts': ms(f'{day} {hm}'), 'point_value': 20}
  push = lambda fills, accts: ctx.request.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep NT8 test', 'accounts': [{'name': a} for a in accts], 'fills': fills}), headers=AK)
  push([F('s1', 'APEX-4', 'buy', 1, 21000, '10:00:20'), F('s2', 'APEX-4', 'sell', 1, 21010, '10:05:00')], ['APEX-4', 'APEX-1'])
  sid = lambda name: [a['id'] for a in ctx.request.get(B + '/api/sync', headers=H).json()['accounts'] if a['name'] == name][0]
  ok(ctx.request.post(B + f'/api/sync/accounts/{sid("APEX-4")}', data=json.dumps({'action': 'link', 'account_id': 'S'}), headers=H).status == 200, f'{tag} Apex 4 linked to NinjaTrader (its 10:00 trade)')
  pg.reload(); pg.wait_for_selector('#main', timeout=20000); pg.wait_for_timeout(1200)
  pg.evaluate("async () => { if (window.SweepSync) await SweepSync.load(); }"); pg.wait_for_timeout(300)

  # 1. Accounts › « Copy trading » › the sheet
  pg.evaluate("location.hash = '#accounts'"); pg.wait_for_selector('#main .cg-card', timeout=10000); pg.wait_for_timeout(500)
  ok(pg.evaluate(TXT, '#main .cg-card h2') == [x['title']] and pg.evaluate(TXT, '#main .cg-card [data-cg-new]') == [x['create']], f"{tag} Accounts: « {x['title']} » · « {x['create']} »")
  tap(pg, '#main [data-cg-new]', phone); pg.wait_for_selector('#cgSheet.open', timeout=5000); pg.wait_for_timeout(500)
  tap(pg, '#cgSheet [data-cg-lead="M"]', phone); pg.wait_for_timeout(200)
  on = pg.evaluate("[...document.querySelectorAll('#cgSheet .cg-pick.on')].map((b) => b.dataset.cgPick).sort()")
  ok(pg.evaluate(TXT, '#cgSheet h2') == [x['sheet']] and on == ['F1', 'F2', 'S'], f"{tag} the sheet « {x['sheet']} »: master Apex 1, the 3 others followers ({on})")
  ok(pg.evaluate(TXT, '#cgSheet .cg-pick[data-cg-pick="S"] small') == [x['synced']], f"{tag} Apex 4: « {x['synced']} »")
  tap(pg, '#cgSheet [data-cg-m="1"][data-id="F2"]', phone); pg.wait_for_timeout(200)
  ok(pg.evaluate(TXT, '#cgSheet .cg-pick[data-cg-pick="F2"] + .cg-step b') == ['×2'], f'{tag} Apex 3 at ×2 (one tap on +)')
  ok(not wide(pg), f'{tag} the sheet: nothing wider than the window ({wide(pg)})')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'cg-sheet-{tag}.png'))
  tap(pg, '#cgSheet [data-cg="save"]', phone); pg.wait_for_timeout(900)
  acc = pg.evaluate("['M', 'F1', 'F2', 'S'].map((id) => { const a = getDoc('accounts', id); return [a.group_id || null, !!a.copy_lead, a.copy_pct || 100]; })")
  ok(acc[0][0] and all(a[0] == acc[0][0] for a in acc) and [a[1] for a in acc] == [True, False, False, False] and [a[2] for a in acc] == [100, 100, 200, 100], f'{tag} saved: one group, Apex 1 the master, Apex 3 at 200 % ({acc})')
  ok(pg.locator('#cgSheet.open').count() == 0 and pg.evaluate(TXT, '#main .cg-grp-t b') == ['Apex — Apex 1'] and not wide(pg), f"{tag} the card shows the group; nothing wider than the window ({pg.evaluate(TXT, '#main .cg-grp-t b')}, {wide(pg)})")
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'cg-accounts-{tag}.png'), full_page=True)

  # 2. a trade typed on the master: copied on Apex 2 and 3, never on the synced Apex 4
  before = pg.evaluate(ST, 'F2')
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(600)
  pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open', timeout=8000); pg.wait_for_timeout(400)
  pg.evaluate("() => { TK.account = 'M'; tkRefresh(); }"); pg.wait_for_timeout(900)
  ok(pg.evaluate("[...TK.copyTo].sort()") == ['F1', 'F2'], f"{tag} the form on the master: copies on Apex 2 and 3 chosen, in sight, not on the synced Apex 4 ({pg.evaluate('[...TK.copyTo].sort()')})")
  pg.evaluate("() => { TK.inst = 'NQ'; TK.dir = 'long'; TK.qty = 1; TK.entry = 21000; TK.exit = 21010; TK.entryTime = '10:00'; TK.exitTime = '10:05'; tkRefresh(); }"); pg.wait_for_timeout(300)
  tap(pg, '#tkSlide [data-act="tk-save"]', phone); pg.wait_for_function("S.trades.filter((t) => t.account_id === 'F2').length >= 1", timeout=10000); pg.wait_for_timeout(900)
  m, f1, f2, s4 = (pg.evaluate(ON, a) for a in ['M', 'F1', 'F2', 'S'])
  g = m[0]['g'] if m else None
  ok(len(m) == 1 and len(f1) == 1 and len(f2) == 1 and g and f1[0]['g'] == g and f2[0]['g'] == g, f'{tag} saved on the master: one copy on Apex 2 and on Apex 3, one group')
  ok(f1[0]['n'] == 1 and f1[0]['pnl'] == 20000 and f2[0]['n'] == 2 and f2[0]['pnl'] == 40000 and f2[0]['fees'] == 800, f"{tag} Apex 2: 1 contract +$200; Apex 3 ×2: 2 contracts +$400, its $4 × 2 commission ({f1[0]}, {f2[0]})")
  ok(len(s4) == 1 and s4[0]['source'] == 'ninjatrader' and not s4[0]['src'], f'{tag} Apex 4 synced: its own trade only, no copy (no double) ({s4})')
  after = pg.evaluate(ST, 'F2')
  ok(after['bal'] - before['bal'] == 40000 - 800 and (after['pct'] or 0) > (before['pct'] or 0), f"{tag} Apex 3: balance +$392, the payout counter moves ({before} → {after})")

  # 3. the Journal: one row « ×3 accounts » that unfolds
  pg.evaluate(f"location.hash = '#journal/{day}'"); pg.wait_for_selector('#main [data-cg-tog]', timeout=10000); pg.wait_for_timeout(500)
  ok(pg.evaluate(CGL) == [x['x3']], f"{tag} the Journal: one row « {x['x3']} » ({pg.evaluate(CGL)})")
  hid = "() => [...document.querySelectorAll('#main .cg-list .cg-r, #main tr.cg-sub')].filter((e) => e.getClientRects().length).length"
  n0 = pg.evaluate(hid)
  tap(pg, '#main [data-cg-tog]', phone); pg.wait_for_timeout(400)
  ok(n0 == 0 and pg.evaluate(hid) == 3 and pg.evaluate("location.hash").startswith('#journal'), f'{tag} folded, then one tap: the 3 accounts, the page stays ({n0} → {pg.evaluate(hid)})')
  ok(not wide(pg), f'{tag} the Journal: nothing wider than the window ({wide(pg)})')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'cg-journal-{tag}.png'), full_page=True)

  # 4. editing the master's trade asks to apply it to the group
  mid = m[0]['id']
  pg.evaluate(f"() => {{ openTicket('{mid}'); }}"); pg.wait_for_selector('#tkSlide.open', timeout=5000); pg.wait_for_timeout(500)
  pg.evaluate("() => { TK.exit = 20990; tkRefresh(); }"); pg.wait_for_timeout(300)
  tap(pg, '#tkSlide [data-act="tk-save"]', phone); pg.wait_for_selector('.cg-ask.open', timeout=5000); pg.wait_for_timeout(300)
  ok(pg.evaluate(TXT, '.cg-ask h2') == [x['editT']] and pg.evaluate(TXT, '.cg-ask [data-cg-ask="a"]') == [x['editAll']], f"{tag} the edit asks « {x['editT']} » · « {x['editAll']} »")
  ok(pg.evaluate(ON, 'F2')[0]['pnl'] == 40000, f'{tag} nothing changed on the copies before the answer')
  ok(not wide(pg), f'{tag} the question: nothing wider than the window ({wide(pg)})')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'cg-ask-{tag}.png'))
  tap(pg, '.cg-ask [data-cg-ask="a"]', phone); pg.wait_for_timeout(900)
  f1, f2 = pg.evaluate(ON, 'F1'), pg.evaluate(ON, 'F2'); lost = pg.evaluate(ST, 'F2')
  ok(f1[0]['pnl'] == -20000 and f2[0]['pnl'] == -40000 and f2[0]['n'] == 2, f'{tag} applied: Apex 2 −$200, Apex 3 −$400 (2 contracts)')
  ok(lost['buffer'] < after['buffer'] and lost['bal'] == before['bal'] - 40000 - 800, f"{tag} Apex 3: balance and drawdown margin follow the loss ({after} → {lost})")

  # 5. a trade synced on the master: copied by the server on Apex 2 and 3; Apex 4's own synced trade joins the group
  push([F('m1', 'APEX-1', 'sell', 1, 21100, '11:00:00'), F('m2', 'APEX-1', 'buy', 1, 21090, '11:10:00'), F('s3', 'APEX-4', 'sell', 1, 21100, '11:00:30'), F('s4', 'APEX-4', 'buy', 1, 21090, '11:10:00')], ['APEX-1', 'APEX-4'])
  ok(ctx.request.post(B + f'/api/sync/accounts/{sid("APEX-1")}', data=json.dumps({'action': 'link', 'account_id': 'M'}), headers=H).status == 200, f'{tag} Apex 1 linked to NinjaTrader (its 11:00 trade)')
  pg.reload(); pg.wait_for_selector('#main', timeout=20000); pg.wait_for_timeout(1500)
  at11 = lambda a: [t for t in pg.evaluate(ON, a) if t['at'] == '11:00']
  m11, f111, f211, s11 = at11('M'), at11('F1'), at11('F2'), at11('S')
  g11 = m11[0]['g'] if m11 else None
  ok(len(m11) == 1 and len(f111) == 1 and len(f211) == 1 and len(s11) == 1, f'{tag} the synced master trade: one copy on Apex 2 and 3, Apex 4 keeps its own (no double)')
  ok(g11 and f111[0]['g'] == g11 and f211[0]['g'] == g11 and s11[0]['g'] == g11 and f211[0]['n'] == 2 and f211[0]['pnl'] == 40000 and f111[0]['src'] == m11[0]['id'], f'{tag} one group of 4: Apex 3 at 2 contracts +$400 ({m11}, {f211}, {s11})')
  pg.evaluate(f"location.hash = '#journal/{day}'"); pg.wait_for_selector('#main [data-cg-tog]', timeout=10000); pg.wait_for_timeout(500)
  ok(sorted(pg.evaluate(CGL)) == sorted([x['x3'], x['x4']]), f"{tag} the Journal: « {x['x4']} » for the synced trade ({pg.evaluate(CGL)})")

  # 6. deleting the master's trade asks: all 3 accounts, or this one only
  pg.evaluate(f"location.hash = '#trade/{mid}'"); pg.wait_for_selector('#main details.menu summary', timeout=10000); pg.wait_for_timeout(600)
  tap(pg, '#main details.menu summary', phone); pg.wait_for_timeout(300)
  tap(pg, '#main [data-act="del-trade"]', phone); pg.wait_for_selector('.cg-ask.open', timeout=5000); pg.wait_for_timeout(300)
  ok(pg.evaluate(TXT, '.cg-ask h2') == [x['delT']] and pg.evaluate(TXT, '.cg-ask [data-cg-ask="a"]') == [x['delAll']], f"{tag} the delete asks « {x['delT']} » · « {x['delAll']} »")
  tap(pg, '.cg-ask [data-cg-ask="a"]', phone); pg.wait_for_timeout(700)
  left = pg.evaluate(f"S.trades.filter((t) => t.copy_group === '{g}').length")
  ok(left == 0 and pg.locator('.nav-undo button').count() == 1, f'{tag} deleted on the 3 accounts, « Undo » offered')
  pg.locator('.nav-undo button').first.click(); pg.wait_for_timeout(700)
  ok(pg.evaluate(f"S.trades.filter((t) => t.copy_group === '{g}').length") == 3, f'{tag} « Undo »: the 3 trades are back')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

def billing_server():
  env = dict(os.environ, SWEEP_BILLING_CONFIG=APPDIR + '/tools/billing-config.local.php', PHP_CLI_SERVER_WORKERS='4')
  pr = subprocess.Popen(['php', '-S', f'127.0.0.1:{P1}', 'router.php'], cwd=APPDIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
  for _ in range(50):
    try: urllib.request.urlopen(B1 + '/api/auth/config', timeout=2); return pr
    except Exception: time.sleep(0.2)
  raise RuntimeError('billing server did not start')

def free(p, lang, phone):
  """7. Free: what a copy group is, « Pro », and the plans sheet"""
  tag = f"free-{'390' if phone else '1300'}-{lang}"; x = X[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  email = 'cgf%d@t.dev' % int(time.time() * 1000)
  r = ctx.request.post(B1 + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B1 + '/api/me/profile', data=json.dumps({'first_name': 'Zoé', 'experience': 'gt1'}), headers=H)
  uid = sql('SELECT id FROM users WHERE email_lc = ?', (email.lower(),))[0][0]
  ctx.request.get(B1 + '/api/billing/me', headers=H)   # the trial is created on the first visit
  sql("UPDATE billing_grants SET ends_at = ? WHERE uid = ? AND reason IN ('trial', 'early_access')", (int(time.time()) - 86400, uid))   # the trial ended: Free
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B1 + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate("""() => { put('firms', { id: 'apx', name: 'Apex' }); const A = (id, name) => put('accounts', { id, name, firm_id: 'apx', starting_balance_c: 5000000, status: 'active', phase: 'funded', money_type: 'funded', created_on: todayStr(), rules: {} });
    A('M', 'Apex 1'); A('F1', 'Apex 2'); render(); }""")
  pg.wait_for_function("typeof BILL !== 'undefined' && BILL.on && BILL.st && BILL.st.plan === 'free'", timeout=15000)
  pg.wait_for_timeout(1500)
  for _ in range(3):   # the « trial ended » window opens by itself once: closed as the trader would
    if not pg.locator('.sb-layer').count(): break
    pg.keyboard.press('Escape'); pg.wait_for_timeout(600)
  pg.evaluate("location.hash = '#accounts'"); pg.wait_for_selector('#main .cg-card [data-cg-new]', timeout=10000); pg.wait_for_timeout(500)
  ok(pg.evaluate(TXT, '#main .cg-card .cg-pro') == ['Pro'] and pg.evaluate(TXT, '#main .cg-card .cg-pitch') != [], f'{tag} Free: what a copy group does, « Pro » on the button')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'cg-free-card-{tag}.png'))
  tap(pg, '#main [data-cg-new]', phone); pg.wait_for_timeout(900)
  ok(pg.locator('#cgSheet.open').count() == 0 and x['pw'] in ' '.join(pg.evaluate(TXT, '.sb-pw h2')), f"{tag} the plans sheet « {x['pw']} », no group sheet ({pg.evaluate(TXT, '.sb-pw h2')})")
  ok(not wide(pg), f'{tag} nothing wider than the window')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'cg-free-{tag}.png'))
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

# the copies' pill: its words (« ×3 accounts »), written out on a phone, in its label on a computer's table where it reads « ×3 » (2 Nov.)
CGL = "[...document.querySelectorAll('#main [data-cg-tog]')].filter((e) => e.getClientRects().length).map((e) => (e.getAttribute('aria-label') || e.textContent).replace(/\\s+/g, ' ').trim())"

with sync_playwright() as p:
  run(p, 'fr', True, False)
  run(p, 'en', False, True)
  run(p, 'es', True, True)
  run(p, 'fr', False, False)
  srv = billing_server()
  try:
    free(p, 'fr', True)
    free(p, 'en', False)
  finally:
    try: os.killpg(srv.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    srv.wait()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
