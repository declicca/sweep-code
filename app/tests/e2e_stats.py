"""
Sweep — Stats and Trends (brief 02, part 6), Playwright, phone (fr, es) and computer (en):
  python3 tests/e2e_stats.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own traders]
 - under 5 trades (those of the filters, 27 Oct.): « Your stats are coming: n of 5 », the net P&L, the win rate and the calendar,
   no empty tile, under 2 screens on a phone; no « ∞ » anywhere on Stats; 5 winning trades: « No loss yet » (no infinite profit factor);
 - the filters (period, account, session, direction, instrument) give the same net P&L and number of trades on Stats as on
   the trades list; a setup's line in the deep dive is the trades list filtered on that setup; a trade copied on 3
   accounts counts once on all accounts, once on its own account's view;
 - the 4 tiles' labels on one line on a phone (« Gain / perte moy. »);
 - a trade without a stop: « No stop: R unavailable », never a made-up R; with a stop, its R;
 - Stats › Patterns to watch (since SWEEP.md step 3; on Today before): the costliest first, with what to do: « Your trades after 11:00 cost you … »,
   « Try stopping at 11:00 this week. ».
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import json, os, re, sqlite3, sys, time
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
X = {
  'fr': {'soon': 'Tes stats arrivent : 3 trades sur 5', 'five': 'Dès 5 trades', 'noloss': 'Pas encore de perte', 'avgwl': 'Gain / perte moy.', 'rna': 'Sans stop : R indisponible', 'r': '+0,40R', 'title': 'La tendance de la semaine',
         'trend': r'^Tes trades après 11 h te coûtent 900 \$ depuis le début\.', 'act': 'Essaie de t’arrêter à 11 h cette semaine.'},
  'en': {'soon': 'Your stats are coming: 3 trades of 5', 'five': 'From 5 trades', 'noloss': 'No loss yet', 'avgwl': 'Avg win / loss', 'rna': 'No stop: R unavailable', 'r': '+0.40R', 'title': 'Trend of the week',
         'trend': r'^Your trades after 11:00 cost you \$900 all time\.', 'act': 'Try stopping at 11:00 this week.'},
  'es': {'soon': 'Tus estadísticas llegan: 3 operaciones de 5', 'five': 'Desde 5 operaciones', 'noloss': 'Aún sin pérdidas', 'avgwl': 'Ganancia / pérdida', 'rna': 'Sin stop: R no disponible', 'r': '+0,40R', 'title': 'La tendencia de la semana',
         'trend': r'^Tus operaciones después de las 11:00 te cuestan 900 \$ desde el inicio\.', 'act': 'Intenta parar a las 11:00 esta semana.'},
}
SET = """(rows) => { for (const r of rows) put('trades', Object.assign({ instrument: 'NQ', direction: 'long', contracts: 1, entry: 100, exit: 101, session_date: true, exit_time: '', fees_c: 0 }, r, { session: sessionFor(r.entry_time) })); render(); }"""
ACC = """() => { ['a', 'b', 'c'].forEach((id) => put('accounts', { id, name: 'Acc ' + id.toUpperCase(), status: 'active', starting_balance_c: 5000000, rules: {} })); render(); }"""
FIRST = [  # 3 winning trades
  {'id': 't1', 'account_id': 'a', 'date': '2026-09-08', 'entry_time': '09:45:00', 'pnl_c': 40000, 'setup': 'ORB'},
  {'id': 't3', 'account_id': 'b', 'date': '2026-09-09', 'entry_time': '09:50:00', 'pnl_c': 20000, 'setup': 'ORB', 'direction': 'short', 'instrument': 'ES', 'entry': 5000, 'stop': 5010, 'exit': 4996},
  {'id': 't5', 'account_id': 'a', 'date': '2026-09-10', 'entry_time': '03:30:00', 'pnl_c': 10000, 'setup': 'ORB'}]
FIVE_WINS = [
  {'id': 't7', 'account_id': 'a', 'date': '2026-10-01', 'entry_time': '09:40:00', 'pnl_c': 25000, 'setup': 'ORB'},
  {'id': 't11', 'account_id': 'b', 'date': '2026-10-05', 'entry_time': '09:35:00', 'pnl_c': 3000, 'setup': 'ORB', 'direction': 'short', 'instrument': 'MNQ'}]
REST = [
  {'id': 't2', 'account_id': 'a', 'date': '2026-09-08', 'entry_time': '11:15:00', 'pnl_c': -15000, 'setup': 'VWAP'},
  {'id': 't4', 'account_id': 'b', 'date': '2026-09-09', 'entry_time': '13:10:00', 'pnl_c': -30000, 'setup': 'VWAP', 'direction': 'short', 'instrument': 'ES'},
  {'id': 't6', 'account_id': 'a', 'date': '2026-09-15', 'entry_time': '11:20:00', 'pnl_c': -5000, 'setup': 'ORB', 'instrument': 'MNQ'},
  {'id': 't8', 'account_id': 'b', 'date': '2026-10-01', 'entry_time': '11:30:00', 'pnl_c': -12000, 'setup': 'VWAP', 'direction': 'short'},
  {'id': 't9', 'account_id': 'a', 'date': '2026-10-02', 'entry_time': '14:00:00', 'pnl_c': 8000, 'setup': 'VWAP', 'instrument': 'ES'},
  {'id': 't10', 'account_id': 'a', 'date': '2026-10-02', 'entry_time': '10:00:00', 'pnl_c': 0, 'setup': 'ORB'},
  {'id': 'g1a', 'account_id': 'a', 'date': '2026-10-06', 'entry_time': '09:45:00', 'pnl_c': 50000, 'setup': 'ORB', 'copy_group': 'cg1', 'created_at': '2026-10-06T14:00:00.000Z'},
  {'id': 'g1b', 'account_id': 'b', 'date': '2026-10-06', 'entry_time': '09:45:00', 'pnl_c': 50000, 'setup': 'ORB', 'copy_group': 'cg1', 'created_at': '2026-10-06T14:00:00.001Z'},
  {'id': 'g1c', 'account_id': 'c', 'date': '2026-10-06', 'entry_time': '09:45:00', 'pnl_c': 50000, 'setup': 'ORB', 'copy_group': 'cg1', 'created_at': '2026-10-06T14:00:00.002Z'}]
FILT = """(f) => { Object.assign(F, { period: 'all', from: '', to: '', account: 'all', firm: 'all', session: 'all', dir: 'all', inst: 'all' }, f); Object.assign(U, { setup: 'all', result: 'all', disc: 'all', tag: '', q: '' }); try { saveF(); } catch (e) {} }"""
NUM = "(t) => { const m = String(t || '').replace(/[\\u00a0\\u202f\\s,.]/g, '').match(/[−-]?\\$?(\\d+)/); return m ? (/^[−-]/.test(String(t).trim()) ? -1 : 1) * +m[1] : null; }"
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"

def trader(p, lang, phone, tag):
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'st%s%d@t.dev' % (tag, int(time.time() * 1000)), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Yan', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(ACC); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(800)
  return br, ctx, pg, errs

def stats_page(pg):
  pg.evaluate("location.hash = '#analytics'; render()"); pg.wait_for_selector('#main .ikpis', timeout=10000); pg.wait_for_timeout(600)

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  br, ctx, pg, errs = trader(p, lang, phone, tag.replace('-', ''))
  pg.evaluate(FILT, {})
  # 1. under 5 trades: no ratio that means nothing, no « ∞ »
  pg.evaluate(SET, FIRST); stats_page(pg)
  # (27 Oct., brief « nouveau trader » step 4) under 5 trades: « Your stats are coming », the net P&L, the win rate, the calendar — no empty tile
  soon = pg.evaluate("(document.querySelector('#main .st-soon h3') || {}).textContent || ''")
  tiles = pg.evaluate(TXT, '#main .ikpis .ik b')
  ok(soon == x['soon'] and len(tiles) == 2 and x['five'] not in pg.evaluate("document.querySelector('#main').innerText") and pg.locator('#main .cal, #main .calgrid, #main [class*=cal]').count() > 0,
     f"{tag} 3 trades: « {x['soon']} », 2 tiles (net P&L, win rate), the calendar, no « {x['five']} » ({soon!r}, {tiles})")
  ph = pg.evaluate("document.getElementById('main').scrollHeight / innerHeight")
  ok(ph < 2 or not phone, f'{tag} 3 trades: Stats under 2 screens on a phone ({ph:.2f})')
  ok('∞' not in pg.evaluate("document.querySelector('#main').innerText"), f'{tag} 3 trades: no « ∞ » on Stats')
  pg.evaluate(SET, FIVE_WINS); stats_page(pg)
  tiles = pg.evaluate(TXT, '#main .ikpis .ik b')
  ok(tiles[2:] == [x['noloss']] * 2 and re.match(r'^100\s?%$', tiles[1] or ''), f"{tag} 5 winning trades: 100 %, « {x['noloss']} » ({tiles})")
  ok('∞' not in pg.evaluate("document.querySelector('#main').innerText"), f'{tag} 5 winning trades: still no « ∞ »')
  lb = pg.evaluate("[...document.querySelectorAll('#main .ikpis .ik .lbl')].slice(1).map((l) => [l.textContent.replace(/\\s*i\\s*$/, '').trim(), l.getBoundingClientRect().height / (parseFloat(getComputedStyle(l).lineHeight) || 18)])")
  ok(all(h < 1.5 for _, h in lb) and lb[2][0] == x['avgwl'], f"{tag} the tiles' labels on one line, « {x['avgwl']} » too ({[(t, round(h, 1)) for t, h in lb]})")
  if SHOTS: pg.locator('#main .ikpis').screenshot(path=os.path.join(SHOTS, f'p6-kpis-{tag}.png'))
  # 2. the R: none without a stop, the real one with a stop
  pg.evaluate("location.hash = '#trade/t1'"); pg.wait_for_selector('#main .tr-top', timeout=10000); pg.wait_for_timeout(500)
  ok(pg.evaluate(TXT, '#main .nav-r-na') == [x['rna']], f"{tag} a trade without a stop: « {x['rna']} »")
  pg.evaluate("location.hash = '#trade/t3'"); pg.wait_for_timeout(700)
  ok(pg.locator('#main .nav-r-na').count() == 0 and x['r'] in pg.evaluate("document.querySelector('#main .tr-top') ? document.querySelector('#main').innerText.replace(/[\\u00a0\\u202f]/g, ' ') : ''"), f"{tag} with a stop (10 points of ES, $500): its R, {x['r']}")
  # 3. the filters: Stats = the trades list; a copied trade once
  pg.evaluate(SET, REST)
  combos = [({}, 12), ({'account': 'a'}, 8), ({'period': 'custom', 'from': '2026-10-01', 'to': '2026-10-31'}, 6), ({'session': 'nyam'}, 9), ({'dir': 'short'}, 4), ({'inst': 'ES'}, 3)]
  for f, n in combos:
    pg.evaluate(FILT, f); stats_page(pg)
    net_s = round(int(pg.evaluate("document.querySelector('#main .ikpis .ik b [data-cu]').dataset.cu")) / 100); cnt_s = pg.evaluate("stats(ft()).n")   # (the tile counts up to its value: data-cu)
    sub = pg.evaluate("document.querySelector('#main .ikpis .ik small').textContent")
    pg.evaluate("location.hash = '#trades'; render()"); pg.wait_for_selector('#main .tstats', state='attached', timeout=10000); pg.wait_for_timeout(500)
    tb = pg.evaluate("[...document.querySelectorAll('#main .tstats b')].map((b) => b.textContent)")
    net_t, cnt_t = pg.evaluate(NUM, tb[0]), int(re.sub(r'\D', '', tb[2]) or -1)
    ok(net_s == net_t and cnt_s == cnt_t == n and sub.startswith(str(n)), f'{tag} filters {f or "none"}: Stats {net_s} $ · {cnt_s} trades = trades list {net_t} $ · {cnt_t} trades (want {n})')
  # a setup: the deep dive's line = the trades list filtered on it
  pg.evaluate(FILT, {}); pg.evaluate("location.hash = '#analytics/setup'; render()"); pg.wait_for_selector('#main .ikpis', timeout=10000); pg.wait_for_timeout(700)
  row = pg.evaluate("(() => { const tr = [...document.querySelectorAll('#main table tr')].find((r) => r.cells[0] && r.cells[0].textContent.trim() === 'ORB'); return tr ? [tr.cells[1].textContent, tr.cells[2].textContent] : null; })()")
  pg.evaluate("location.hash = '#trades'; U.setup = 'ORB'; render()"); pg.wait_for_selector('#main .tstats', state='attached', timeout=10000); pg.wait_for_timeout(500)
  tb = pg.evaluate("[...document.querySelectorAll('#main .tstats b')].map((b) => b.textContent)")
  ok(row and int(row[0]) == int(re.sub(r'\D', '', tb[2])) == 8 and pg.evaluate(NUM, row[1]) == pg.evaluate(NUM, tb[0]), f'{tag} setup ORB: the deep dive {row} = the trades list {tb}')
  pg.evaluate("U.setup = 'all'")
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

def trend(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  br, ctx, pg, errs = trader(p, lang, phone, 'tr' + lang)
  pg.evaluate(FILT, {})
  rows = []
  for k, day in enumerate(['2026-09-01', '2026-09-02', '2026-09-03', '2026-09-04', '2026-09-08', '2026-09-09']):
    rows += [{'id': f'e{k}', 'account_id': 'a', 'date': day, 'entry_time': '09:45:00', 'pnl_c': 20000}, {'id': f'l{k}', 'account_id': 'a', 'date': day, 'entry_time': '11:15:00', 'pnl_c': -15000}]
  pg.evaluate(SET, rows)
  # (SWEEP.md step 3) the week's trend left Today: Stats › Patterns to watch, the costliest first, with what to do
  pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(800)
  ok(pg.locator('#main .nav-dash .d-trends').count() == 0, f'{tag} Today: no trend card any more')
  pg.evaluate("location.hash = '#analytics'; render()"); pg.wait_for_selector('#main .ins li', timeout=10000); pg.wait_for_timeout(800)
  li = pg.evaluate(TXT, '#main .ins li')
  ok(bool(li) and re.match(x['trend'], li[0]) and x['act'] in li[0], f'{tag} Stats: the costliest first, with what to do: {li[:1]}')
  ok(pg.evaluate(WIDE) <= 1, f'{tag} Stats: nothing wider than the window')
  if SHOTS: pg.locator('#main .ins').first.screenshot(path=os.path.join(SHOTS, f'p6-trend-{tag}.png'))
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

with sync_playwright() as p:
  run(p, 'fr', True); trend(p, 'fr', True)
  run(p, 'en', False); trend(p, 'en', False)
  run(p, 'es', True); trend(p, 'es', True)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
