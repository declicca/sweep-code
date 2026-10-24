"""
Sweep — Calendar, Journal and the economic calendar (brief 02 part 7), Playwright, phone (fr, es) and computer (en):
  python3 tests/e2e_calendar_news.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
 - « the trades taken around releases »: 6 trades entered 5 minutes after a high-impact release of the economic calendar
   (losing) against 6 others (winning), none saved from the ticket (as an import or a sync: no news data on the trade):
   Stats › trends says it, with what to do, sample « 6 vs 6 »; Stats › News counts them « within 15 min »;
 - the Journal: a day over its maximum of trades: « Trades max » « Dépassé (2/1) » (not « Max trades », « Exceeded »);
 - the Calendar: the releases' short names in the trader's language (« Chômage », not « Unemployment »), no CSV button;
 - the economic figures in the trader's language (20 Oct.): a release published « 0.7% », forecast « 0.4% », previous « -0.1% »
   reads « 0,7 % », « 0,4 % », « −0,1 % », surprise « +0,3 pp » in French and Spanish (list, event sheet, its « Result »
   sentence), unchanged in English;
 - the bundled schedule: the next two weeks as the official calendars say (BLS, Census, BEA, Fed: retail sales Oct. 15, GDP
   and PCE Oct. 29); a re-import of the file drops a future release that moved (no duplicate).
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import datetime as dt, hashlib, json, os, re, sqlite3, sys, time
from zoneinfo import ZoneInfo
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
  'fr': {'trend': r'^Tes trades à 15 minutes ou moins d’une annonce forte font en moyenne [−-]200 \$ \(0 ?% de réussite\), contre \+?150 \$ \(100 ?%\) pour les autres\.',
         'act': 'Cette semaine, attends 15 minutes après une annonce forte avant d’entrer.', 'sample': '6 vs 6 trades', 'max': 'Trades max', 'exc': 'Dépassé (2/1)', 'unemp': 'Chômage', 'within': '15 min'},
  'en': {'trend': r'^Your trades within 15 minutes of a high-impact release average [−-]\$200 \(0 ?% win rate\), against \+?\$150 \(100 ?%\) for the others\.',
         'act': 'This week, wait 15 minutes after a high-impact release before entering.', 'sample': '6 vs 6 trades', 'max': 'Max trades', 'exc': 'Exceeded (2/1)', 'unemp': 'Unemployment', 'within': '15 min'},
  'es': {'trend': r'^Tus operaciones a 15 minutos o menos de un anuncio de alto impacto promedian [−-]200 \$ \(0 ?% de acierto\), frente a \+?150 \$ \(100 ?%\) en las demás\.',
         'act': 'Esta semana, espera 15 minutos después de un anuncio de alto impacto antes de entrar.', 'sample': '6 vs 6', 'max': 'Operaciones máx.', 'exc': 'Superado (2/1)', 'unemp': 'Desempleo', 'within': '15 min'},
}
FILT = """() => { Object.assign(F, { period: 'all', from: '', to: '', account: 'all', firm: 'all', session: 'all', dir: 'all', inst: 'all' }); Object.assign(U, { setup: 'all', result: 'all', disc: 'all', tag: '', q: '' }); try { saveF(); } catch (e) {} }"""
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cal%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Lou', 'experience': 'gt1'}), headers=H)
  # (part 4) a release with its figures next Monday, 8:30 ET — « next week » as the app counts it: New York time + 6 h, from Monday
  eid = hashlib.sha1(('loc-test-' + lang).encode()).hexdigest()   # (an event's id: 40 hex characters, as the calendar's own)
  day = (dt.datetime.now(ZoneInfo('America/New_York')) + dt.timedelta(hours=6)).date(); mon = (day - dt.timedelta(days=day.weekday()) + dt.timedelta(days=7)).isoformat()
  ts = int(dt.datetime.fromisoformat(mon + 'T08:30').replace(tzinfo=ZoneInfo('America/New_York')).timestamp())
  d = sqlite3.connect(DB); d.execute("INSERT OR REPLACE INTO econ_events (id, ts, country, event, impact, actual, forecast, previous, source, updated_at) VALUES (?, ?, 'US', 'Retail Sales m/m', 'high', '0.7%', '0.4%', '-0.1%', 'manual', 0)", (eid, ts)); d.commit(); d.close()
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate("() => { put('accounts', { id: 'a', name: 'Main', status: 'active', starting_balance_c: 5000000, rules: {} }); render(); }")
  pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(600)
  # 6 days with a high-impact release at 8:30 ET in the economic calendar (July-September 2026)
  days = pg.evaluate("""fetch('api/econ?from=2026-07-01&to=2026-09-30', { credentials: 'same-origin' }).then((r) => r.json()).then((j) => [...new Set((j.events || [])
    .filter((e) => e.impact === 'high' && etStr(e.ts).slice(11, 16) === '08:30').map((e) => etStr(e.ts).slice(0, 10)))].sort().slice(0, 6))""")
  ok(len(days) == 6, f'{tag} 6 days with a high-impact release at 8:30 ET in the calendar ({days})')
  rows = []
  for k, d in enumerate(days):   # no « news » on the trades: as an import, a sync or a screenshot
    rows += [{'id': f'n{k}', 'date': d, 'entry_time': '08:35:00', 'pnl_c': -20000}, {'id': f'f{k}', 'date': d, 'entry_time': '12:30:00', 'pnl_c': 15000}]
  pg.evaluate("""(rows) => { for (const r of rows) put('trades', Object.assign({ account_id: 'a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 100, exit: 101, session_date: true, fees_c: 0 }, r, { session: sessionFor(r.entry_time) })); render(); }""", rows)
  pg.evaluate(FILT)
  # 1. Stats: the trend, with what to do (the calendar is loaded for these days, then the page drawn again)
  pg.evaluate("location.hash = '#analytics'; render()"); pg.wait_for_selector('#main .ikpis', timeout=10000)
  pg.wait_for_function("[...document.querySelectorAll('#main .ins li')].some((l) => /15/.test(l.textContent))", timeout=15000); pg.wait_for_timeout(500)
  li = [l for l in pg.evaluate(TXT, '#main .ins li') if re.search(x['trend'], l)]
  ok(len(li) == 1 and x['sample'] in li[0], f"{tag} Stats › trends: the trades around releases, sample « {x['sample']} » ({pg.evaluate(TXT, '#main .ins li')[:3]})")
  acts = pg.evaluate(TXT, '#main .ins li .ins-act')
  ok(not acts or x['act'] in acts, f"{tag} its action, where the list shows actions ({acts})")
  if SHOTS: pg.locator('#main .ins').first.screenshot(path=os.path.join(SHOTS, f'p7-trend-{tag}.png'))
  # Stats › News: « within 15 min » = the 6 trades, from the calendar
  pg.evaluate("location.hash = '#analytics/news'; render()"); pg.wait_for_timeout(1500)
  rows15 = pg.evaluate("[...document.querySelectorAll('#main table tr')].filter((r) => r.cells[0] && /15/.test(r.cells[0].textContent)).map((r) => [r.cells[0].textContent.trim(), r.cells[1].textContent.trim()])")
  ok(len(rows15) == 1 and rows15[0][1] == '6', f"{tag} Stats › News: within 15 minutes of a high-impact release: 6 trades ({rows15})")
  help_ = pg.evaluate(TXT, '#main .help')
  ok(not any(re.search(r'older trades|no news data|sans données|sin datos', h) for h in help_), f'{tag} Stats › News: every trade has its calendar data (no « without data » line)')
  # 2. the Journal: a day over its maximum of trades
  pg.evaluate("(d) => { put('journals', { id: d, pre: { max_trades: '1' } }); location.hash = '#journal/' + d; render(); }", days[0]); pg.wait_for_selector('#main .statline', timeout=10000); pg.wait_for_timeout(700)
  st = pg.evaluate("[...document.querySelectorAll('#main .statline > div')].map((d) => [...d.children].map((c) => c.textContent.trim()).join(' '))")
  ok((x['max'] + ' ' + x['exc']) in st, f"{tag} the Journal: « {x['max']} » « {x['exc']} » ({st})")
  # 3. the Calendar: the short names in the trader's language, no CSV button
  pg.evaluate("location.hash = '#calendar/2026-09'; render()"); pg.wait_for_timeout(1500)
  chips = pg.evaluate(TXT, '#main .cev span')
  ok(any(c.endswith(x['unemp']) for c in chips) and (lang == 'en' or not any(re.search(r'\b(Retail|Unemployment|Fed presser|FOMC minutes|ISM Mfg|ISM Svc)$', c) for c in chips)),
     f"{tag} the Calendar: « {x['unemp']} », no English short name ({chips[:6]})")
  ok(pg.evaluate("document.querySelectorAll('.main-wrap .top .nav-imp, #main [data-act=export-csv]').length") == 0, f'{tag} the Calendar: no CSV button')
  ok(pg.evaluate(WIDE) <= 1, f'{tag} nothing wider than the window')
  if SHOTS: pg.screenshot(path=os.path.join(SHOTS, f'p7-calendar-{tag}.png'))
  # 4. the economic figures in the trader's language: the release written before the app first opened (the browser keeps
  # the calendar's answers for a while: a release added later would only show after that)
  pg.evaluate("location.hash = '#news/next'"); pg.wait_for_selector(f'#main [data-act=ev-open][data-id="{eid}"]', timeout=15000); pg.wait_for_timeout(500)
  row = pg.evaluate(TXT, f'#main [data-act=ev-open][data-id="{eid}"]')[0]
  pg.click(f'#main [data-act=ev-open][data-id="{eid}"]'); pg.wait_for_selector('.evvals', timeout=10000); pg.wait_for_timeout(800)
  sheet = ' '.join(pg.evaluate(TXT, '.evvals') + pg.evaluate(TXT, '.facts-box'))
  want = ['0.7%', '0.4%', '-0.1%', '+0.3 pp'] if lang == 'en' else ['0,7 %', '0,4 %', '−0,1 %', '+0,3 pp']
  ok(all(w in row for w in want[:2]) and (lang == 'en' or '0.7' not in row), f'{tag} the economic calendar: the figures as the trader writes them ({row})')
  ok(all(w in sheet for w in want) and (lang == 'en' or not re.search(r'\d\.\d', sheet)), f'{tag} the release sheet and its « Result »: {want} ({sheet[:220]})')
  raw = pg.evaluate("document.querySelector('.evvals').textContent + ' ' + document.querySelector('.facts-box').textContent")
  ok(not re.search('[\\s\u00a0\u202f]{2,}%', raw), f'{tag} one space only before « % » ({raw[:120]!r})')
  d = sqlite3.connect(DB); d.execute('DELETE FROM econ_events WHERE id = ?', (eid,)); d.commit(); d.close()
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

def schedule(p):   # the bundled schedule checked against the official calendars; a re-import drops a future release that moved
  ctx = p.request.new_context(); unthrottle()
  r = ctx.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'sch%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  stale = int(time.mktime(time.strptime('2027-10-16 12:30', '%Y-%m-%d %H:%M')))   # a future « Retail Sales » the file no longer has
  d = sqlite3.connect(DB)
  d.execute("INSERT OR REPLACE INTO econ_events (id, ts, country, event, impact, source, updated_at, status) VALUES ('stale-test', ?, 'US', 'Retail Sales m/m', 'high', 'schedule', 0, 'estimated')", (stale,))
  d.execute("DELETE FROM app_settings WHERE k LIKE 'econ_seed:%'"); d.commit(); d.close()   # the file is imported again (as after an update)
  j = ctx.get(B + '/api/econ?from=2026-10-14&to=2026-10-31', headers=H).json()
  ev = [(e['event'], time.strftime('%Y-%m-%d', time.gmtime(e['ts'] - 4 * 3600)), e.get('status')) for e in j.get('events', [])]
  later = ctx.get(B + '/api/econ?from=2027-10-01&to=2027-10-31', headers=H).json().get('events', [])
  ok(('Retail Sales m/m', '2026-10-15', 'official') in ev and not any(e[0] == 'Retail Sales m/m' and e[1] == '2026-10-16' for e in ev), f'the schedule: retail sales on Oct. 15 (Census), not 16')
  ok(('Core PCE Price Index m/m', '2026-10-29', 'official') in ev and ('GDP q/q (Advance)', '2026-10-29', 'official') in ev, 'GDP and PCE on Oct. 29 (BEA)')
  ok(('FOMC Rate Decision', '2026-10-28', 'official') in ev and ('CPI m/m', '2026-10-14', 'official') in ev and ('PPI m/m', '2026-10-15', 'official') in ev, 'CPI Oct. 14, PPI Oct. 15, FOMC Oct. 28')
  ok(not any(e['id'] == 'stale-test' for e in later), 'a release that moved: its old row is gone after the import')
  ctx.dispose()

with sync_playwright() as p:
  schedule(p)
  run(p, 'fr', True)
  run(p, 'en', False)
  run(p, 'es', True)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
