"""
Sweep — the payout counter in the app (brief 02, part 3, « Améliorer »), Playwright, phone (fr, es) and computer (en):
  python3 tests/e2e_payout_conditions.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
A new trader, three funded accounts from the catalogue: Apex EOD 50K, Topstep 50K « Consistency », LucidPro 50K.
 - not ready, what is missing exactly: Apex with 4 winning days of $250+ and $2,200 of profit → « 1 more winning day of
   $250+ », « $400 more above the balance to keep »; Topstep with a $900 day out of $1,100 → « bring your best day under
   40%: about $1,150 more profit, spread over at least 2 days »;
 - ready: « You can request up to $900 » (the smaller of the $1,500 step and what is above the $52,100 safety net) and
   « Record my request » → My money's form, open, for this account, « requested », $900; saved → the account's history
   says « Payout 1 of 6 », the counter starts again (« 5 more winning days », payouts made 1 / 6);
 - Today: « Ready for payout » on the LucidPro account → the same pre-filled request;
 - the server's « ready for a payout » (the game's map) is the app's (100 % for LucidPro).
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import json, os, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
X = {   # {m}: amounts in the app's own money format, {p}: a percent with the app's rule
  'fr': {'notyet': 'Pas encore', 'win1': 'Encore 1 jour gagnant de {250} et +', 'bal': 'Encore {400} au-dessus du solde à garder', 'avail': 'Tu peux demander jusqu’à {900}', 'req': 'Enregistrer ma demande',
         'win5': 'Encore 5 jours gagnants de {250} et +', 'no': 'Payout 1 sur 6', 'cons': 'Baisse ton meilleur jour sous {40%} : environ {1150} de profit en plus, réparti sur au moins 2 jours', 'ready': 'Prêt pour le payout'},
  'en': {'notyet': 'Not yet', 'win1': '1 more winning day of {250}+', 'bal': '{400} more above the balance to keep', 'avail': 'You can request up to {900}', 'req': 'Record my request',
         'win5': '5 more winning days of {250}+', 'no': 'Payout 1 of 6', 'cons': 'Bring your best day under {40%}: about {1150} more profit, spread over at least 2 days', 'ready': 'Ready for payout'},
  'es': {'notyet': 'Aún no', 'win1': 'Falta 1 día ganador de {250} o más', 'bal': 'Faltan {400} por encima del saldo a mantener', 'avail': 'Puedes pedir hasta {900}', 'req': 'Registrar mi solicitud',
         'win5': 'Faltan 5 días ganadores de {250} o más', 'no': 'Payout 1 de 6', 'cons': 'Baja tu mejor día bajo el {40%}: unos {1150} más de beneficio, repartidos en al menos 2 días', 'ready': 'Listo para el payout'},
}
SEED = """() => {
  const ago = (k) => { const d = new Date(todayStr() + 'T12:00:00'); d.setDate(d.getDate() - k); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  const mk = (id, pv) => { const r = SweepPresets.rulesOf(pv); put('firms', { id: 'f-' + id, name: r.firm }); put('accounts', { id, firm_id: 'f-' + id, name: r.name, starting_balance_c: r.start * 100, status: 'active', phase: 'funded', money_type: 'funded', preset: pv, rules: r.rules, created_on: ago(30) }); };
  mk('pa', 'apex|apex-eod|50000|funded'); mk('pt', 'topstep|combine|50000|funded|consistency'); mk('pl', 'lucid|lucidpro|50000|funded');
  const T = (id, acc, k, usd) => put('trades', { id, account_id: acc, instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: usd * 100, pnl_manual: true, fees_c: 0, session_date: true, date: ago(k), entry_time: '10:00', exit_time: '10:30' });
  [600, 500, 200, 400, 500].forEach((v, i) => T('pa' + i, 'pa', 9 - i, v));
  [100, 100, 900].forEach((v, i) => T('pt' + i, 'pt', 4 - i, v));
  [300, 300, 300].forEach((v, i) => T('pl' + i, 'pl', 4 - i, v));
  render(); }"""
NORM = "(s) => s.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim()"
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  ctx.add_init_script("window.__swNow = '2026-10-27T10:30:00-04:00'")   # (activation D) a market open: the first trade after the plan, whatever the hour of the run
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'po%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Inès', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000)
  pg.wait_for_function("window.SweepPresets && (SweepPresets.ready() || (SweepPresets.load(), false))", timeout=20000, polling=500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(1800)
  m = lambda usd: pg.evaluate(NORM, pg.evaluate("(c) => moneyU(c)", usd * 100))
  pc = '40%' if lang == 'en' else '40 %'
  x = {k: v.replace('{250}', m(250)).replace('{400}', m(400)).replace('{900}', m(900)).replace('{1150}', m(1150)).replace('{40%}', pc) for k, v in X[lang].items()}
  def acct(aid):
    pg.evaluate(f"location.hash = '#account/{aid}'"); pg.wait_for_selector('#main .nav-po', timeout=10000); pg.wait_for_timeout(700)
  # Apex: 4 winning days of $250+ (and one at $200), $2,200 of profit: not ready, what is missing
  acct('pa')
  ok(pg.evaluate(TXT, '#main .nav-po-h > b') == [x['notyet']], f"{tag} Apex: « {x['notyet']} »")
  todo = pg.evaluate(TXT, '#main .nav-po-todo li')
  ok(todo == [x['win1'], x['bal']], f'{tag} Apex: what is missing ' + json.dumps(todo, ensure_ascii=False))
  ok(pg.evaluate(WIDE) <= 1, f'{tag} Apex: nothing wider than the window')
  if SHOTS: pg.locator('#main .nav-po').screenshot(path=os.path.join(SHOTS, f'p3-notyet-{tag}.png'))
  # the 5th winning day ($800): ready, up to $900, « Record my request »
  pg.evaluate("put('trades', { id: 'pa9', account_id: 'pa', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 80000, pnl_manual: true, fees_c: 0, session_date: true, date: (() => { const d = new Date(todayStr() + 'T12:00:00'); d.setDate(d.getDate() - 1); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; })(), entry_time: '10:00', exit_time: '10:30' }); render()")
  pg.wait_for_timeout(900)
  ok(pg.locator('#main .nav-po-h.ok').count() == 1 and pg.evaluate(TXT, '#main .nav-po-h.ok > span') == [x['avail']], f"{tag} Apex: ready, « {x['avail']} »")
  ok(pg.evaluate(TXT, '#main .nav-po-req') == [x['req']], f"{tag} Apex: « {x['req']} »")
  if SHOTS: pg.locator('#main .nav-po').screenshot(path=os.path.join(SHOTS, f'p3-ready-{tag}.png'))
  pg.click('#main .nav-po-req'); pg.wait_for_selector('#main form[data-form="payout"]', timeout=10000); pg.wait_for_timeout(600)
  f = pg.evaluate("() => { const f = document.querySelector('#main form[data-form=\"payout\"]'); return { acc: f.elements.account.value, st: (f.querySelector('input[name=status]:checked') || {}).value, gross: f.elements.gross.value, net: f.elements.net.value, hash: location.hash } }")
  ok(f['hash'].startswith('#payouts') and f['acc'] == 'pa' and f['st'] == 'requested' and f['gross'] == '900' and f['net'] == '900', f'{tag} the request form: this account, « requested », $900 ({f})')
  ok(pg.evaluate(WIDE) <= 1, f'{tag} My money: nothing wider than the window')
  if SHOTS: pg.locator('#main form[data-form="payout"]').screenshot(path=os.path.join(SHOTS, f'p3-form-{tag}.png'))
  pg.click('#main form[data-form="payout"] button[type=submit]'); pg.wait_for_timeout(1200)
  po = pg.evaluate("S.payouts.filter((p) => p.account_id === 'pa').map((p) => [p.status, p.gross_c, p.request_date === todayStr()])")
  ok(po == [['requested', 90000, True]], f'{tag} saved: one request of $900 today ({po})')
  # the account's history: « Payout 1 of 6 »; the counter starts again from the request
  acct('pa')
  ok(pg.evaluate(TXT, '#main .pz-list .pz-no') == [x['no']], f"{tag} the account's payouts: « {x['no']} »")
  ok(pg.evaluate(TXT, '#main .nav-po-h > b') == [x['notyet']] and pg.evaluate(TXT, '#main .nav-po-todo li')[:1] == [x['win5']], f"{tag} after the request: « {x['win5']} »")
  ok('1 / 6' in pg.evaluate("[...document.querySelectorAll('#main .nav-po-c li')].map((l) => l.textContent).join(' | ')"), f'{tag} after the request: payouts made 1 / 6')
  # Topstep « Consistency »: the split stays 90 %, and the best day
  acct('pt')
  ok(pg.evaluate("getDoc('accounts', 'pt').rules.payout_split_pct") == 90, f'{tag} Topstep « Consistency »: the 90 % split is kept')
  todo = pg.evaluate(TXT, '#main .nav-po-todo li')
  ok(todo == [x['cons']], f'{tag} Topstep: ' + json.dumps(todo, ensure_ascii=False))
  # Today: « Ready for payout » on LucidPro → the same pre-filled request
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(1200)
  pill = pg.locator('#main .nav-acc[href="#account/pl"] .nav-ready')
  ok(pill.count() == 1 and pg.evaluate(TXT, '#main .nav-acc[href="#account/pl"] .nav-ready') == [x['ready']], f"{tag} Today: « {x['ready']} » on LucidPro")
  if pill.count():
    pill.click(); pg.wait_for_selector('#main form[data-form="payout"]', timeout=10000); pg.wait_for_timeout(600)
    f = pg.evaluate("() => { const f = document.querySelector('#main form[data-form=\"payout\"]'); return { acc: f.elements.account.value, st: (f.querySelector('input[name=status]:checked') || {}).value, gross: f.elements.gross.value } }")
    ok(f == {'acc': 'pl', 'st': 'requested', 'gross': '900'}, f'{tag} Today → the request for LucidPro, $900 ({f})')
  # the server counts the same way (the game's map)
  srv = ctx.request.get(B + '/api/game/today', headers=H).json().get('map', {}).get('payout', {})
  app = pg.evaluate("Math.max(...['pa', 'pt', 'pl'].map((id) => SweepPayout.status(getDoc('accounts', id)).pct))")
  ok(srv.get('configured') is True and srv.get('ready') == app == 100, f'{tag} the server says the same: {srv} (app {app})')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

with sync_playwright() as p:
  run(p, 'fr', True)
  run(p, 'en', False)
  run(p, 'es', True)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
