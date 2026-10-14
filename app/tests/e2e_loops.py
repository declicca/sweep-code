"""
Sweep — automatic emails through Loops (loops/loops.php), dev environment with Playwright:
  python3 tests/e2e_loops.py http://127.0.0.1:8095 [storage_state, unused: each case signs up its own trader]
A stand-in Loops (tests/loops_mock.php, port + 3) and a copy of the server that talks to it (port + 2, same database,
SWEEP_LOOPS_CONFIG); never the real Loops. The first run of loops/cron.php prepares it. Then a new trader, phone (fr,
390 × 844, touch) and computer (en, 1300 × 850), through the real screens: sign-up, first name + first account (Apex),
plan, first trade, the first trade deleted and added again, a payout. Loops gets signedUp, profileCompleted,
firstAccountAdded (Apex Trader Funding), firstTradeLogged and firstPayoutLogged exactly once each, with the contact
(language, first name, plan, lastLoginAt). The daily run (--now, --user): 7 days away → inactive7d, once.
A wrong key: the app saves as usual and the refusal is in the server log. No page error, nothing wider than the window.
"""
import json, os, signal, sqlite3, subprocess, sys, tempfile, time, urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B0 = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
APPDIR = '/tmp/g'   # the served copy (each shard has its own)
P = int(B0.rsplit(':', 1)[1]); B = f'http://127.0.0.1:{P + 2}'; MOCK = P + 3
DB = os.environ.get('SWEEP_TEST_DB', APPDIR + '/data/journal.db')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
NY = ZoneInfo('America/New_York')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
TMP = tempfile.mkdtemp(prefix='sweep-loops-e2e-')
CONF = os.path.join(TMP, 'loops-config.php'); SRVLOG = os.path.join(TMP, 'server.log')
def config(key): open(CONF, 'w').write("<?php return ['api_key' => '%s', 'api_url' => 'http://127.0.0.1:%d/api/v1', 'timeout' => 2];\n" % (key, MOCK))
def calls(): return [json.loads(l) for l in open(os.path.join(TMP, 'calls.jsonl'))] if os.path.exists(os.path.join(TMP, 'calls.jsonl')) else []
def events(uid, name=None): return [c['body'] for c in calls() if c['path'] == '/api/v1/events/send' and c['key'] == 'test-key' and c['body'].get('userId') == uid and (name is None or c['body'].get('eventName') == name)]
def wait(url):
  for _ in range(60):
    try: urllib.request.urlopen(url, timeout=2); return
    except urllib.error.HTTPError: return
    except Exception: time.sleep(0.2)
  raise RuntimeError('did not start: ' + url)
def start(args, env, log=subprocess.DEVNULL):
  return subprocess.Popen(args, cwd=APPDIR, env=env, stdout=log, stderr=log, start_new_session=True)
def stop(p):
  try: os.killpg(p.pid, signal.SIGTERM)
  except ProcessLookupError: pass
  p.wait()
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
def cron(*args):
  r = subprocess.run(['php', 'loops/cron.php', *args], cwd=APPDIR, env=dict(os.environ, SWEEP_LOOPS_CONFIG=CONF), capture_output=True, text=True, timeout=120)
  return r.returncode, r.stdout + r.stderr
def ny_now(dt=None): return (dt or datetime.now(timezone.utc)).astimezone(NY).strftime('%Y-%m-%d %H:%M')

config('test-key')
mock = start(['php', '-S', f'127.0.0.1:{MOCK}', 'tests/loops_mock.php'], dict(os.environ, LOOPS_MOCK_DIR=TMP, PHP_CLI_SERVER_WORKERS='4'))
srvlog = open(SRVLOG, 'w')
srv = start(['php', '-S', f'127.0.0.1:{P + 2}', 'router.php'], dict(os.environ, SWEEP_LOOPS_CONFIG=CONF, PHP_CLI_SERVER_WORKERS='4'), srvlog)
try:
  wait(f'http://127.0.0.1:{MOCK}/'); wait(B + '/api/auth/config')
  # a dev database already used by an earlier run: start from a Loops not prepared yet (this stand-in is new)
  d = sqlite3.connect(DB)
  d.execute("DELETE FROM app_settings WHERE k = 'loops_since' OR k LIKE 'loops_test_at:%'")
  try: d.execute('DELETE FROM email_events_log')
  except sqlite3.OperationalError: pass
  d.commit(); d.close()
  # the first run prepares Loops (on the dev database): contact properties, what existing traders already did
  rc, out = cron('--now=' + ny_now(), '--user=mateo')
  props = sorted(json.load(open(os.path.join(TMP, 'props.json'))).keys()) if os.path.exists(os.path.join(TMP, 'props.json')) else []
  ok(rc == 0 and 'Loops ready' in out and props == sorted(['language', 'plan', 'isPaying', 'isDiscordCrew', 'proTrialEndsAt', 'lastLoginAt']), f'first run of loops/cron.php: Loops ready, its contact properties created ({props})')

  def run(p, lang, phone):
    tag = f"{'390' if phone else '1300'}-{lang}"
    unthrottle()
    br = p.chromium.launch()
    ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone,
                         locale={'fr': 'fr-CA', 'en': 'en-US'}[lang], color_scheme='dark' if phone else 'light')
    ctx.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    n = 'lp%d' % int(time.time() * 1000)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000, 'lang': lang}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
    uid = ctx.request.get(B + '/api/data').json()['user']['id']
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.on('console', lambda m: m.type == 'error' and errs.append('console: ' + m.text[:160]))
    def tap(sel):
      last = None
      for _ in range(6):
        try: pg.locator(sel).first.click(timeout=3000); pg.wait_for_timeout(250); return
        except Exception as e: last = e; pg.wait_for_timeout(300)
      raise last
    # the real first screen: first name, guided picker Apex › EOD › 50K, « Create account »
    pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=20000); pg.wait_for_timeout(700)
    tap('form[data-form=account] [data-st-ph0=eval]'); tap('[data-st-firm=apex]')
    if pg.locator('[data-st-type=apex-eod]').count(): tap('[data-st-type=apex-eod]')
    tap('[data-st-size="50000"]')
    pg.locator('[data-onb-fn]').click(); pg.keyboard.type('Léa' if lang == 'fr' else 'Sam')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} first screen: nothing wider than the window')
    pg.screenshot(path=os.path.join(tempfile.gettempdir(), f'loops_{tag}_1.png'))
    tap('form[data-form=account][data-onb] [type=submit]')
    pg.wait_for_selector('#gSheet.g-plan, #gSheet .g-gate', timeout=8000); pg.wait_for_timeout(500)
    tap('#gSheet [data-g=bias][data-v=bullish]'); tap('#gSheet [data-g=save-plan]')
    pg.wait_for_selector('#tkSlide.open, .nav-am.open, .nav-am-shot.open', timeout=8000); pg.wait_for_timeout(600)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    if pg.locator('#tkSlide.open').count(): pg.evaluate("closeTicket()"); pg.wait_for_timeout(300)
    # first trade, deleted, added again; a payout
    pg.evaluate("put('trades', { id: 'lp-t1', account_id: S.accounts[0].id, instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 12000, pnl_manual: true, date: todayStr(), entry_time: '10:00', exit_time: '10:05' })")
    pg.wait_for_timeout(1500)
    pg.evaluate("remove('trades', 'lp-t1')"); pg.wait_for_timeout(1200)
    pg.evaluate("put('trades', { id: 'lp-t2', account_id: S.accounts[0].id, instrument: 'NQ', direction: 'short', contracts: 1, entry: 2, exit: 1, pnl_c: 9000, pnl_manual: true, date: todayStr(), entry_time: '11:00', exit_time: '11:05' })")
    pg.wait_for_timeout(1500)
    pg.evaluate("put('payouts', { id: 'lp-p1', account_id: S.accounts[0].id, date: todayStr(), gross_c: 100000, split_pct: 100, fees_c: 0, net_c: 100000, status: 'paid' })")
    pg.wait_for_timeout(1500)
    pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-dash .d-today', timeout=8000); pg.wait_for_timeout(900)
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} Today: nothing wider than the window')
    pg.screenshot(path=os.path.join(tempfile.gettempdir(), f'loops_{tag}_2.png'))
    time.sleep(1)
    got = {e: len(events(uid, e)) for e in ('signedUp', 'profileCompleted', 'firstAccountAdded', 'firstTradeLogged', 'firstPayoutLogged', 'tradesMilestone')}
    ok(got == {'signedUp': 1, 'profileCompleted': 1, 'firstAccountAdded': 1, 'firstTradeLogged': 1, 'firstPayoutLogged': 1, 'tradesMilestone': 0},
       f'{tag} each event exactly once, the first trade deleted and added again included ({got})')
    s = (events(uid, 'signedUp') or [{}])[0]
    ok(s.get('eventProperties') == {'language': lang, 'plan': s.get('plan')} and s.get('language') == lang and s.get('email') == n + '@t.dev' and isinstance(s.get('lastLoginAt'), int),
       f'{tag} signedUp: language {lang}, plan {s.get("plan")}, email, lastLoginAt ({s.get("eventProperties")})')
    a = (events(uid, 'firstAccountAdded') or [{}])[0]
    ok((a.get('eventProperties') or {}).get('propFirm') == 'Apex Trader Funding' and a.get('firstName') == ('Léa' if lang == 'fr' else 'Sam'),
       f'{tag} firstAccountAdded: propFirm Apex Trader Funding, the first name on the contact ({a.get("eventProperties")}, {a.get("firstName")})')
    ok(not errs, f'{tag} no page or console error ({errs[:2]})')
    br.close()
    return uid, ctx

  with sync_playwright() as p:
    uid_fr, _ = run(p, 'fr', True)
    uid_en, _ = run(p, 'en', False)

  # the daily run, on a test date: 7 days away → inactive7d, once
  d = sqlite3.connect(DB); away = (datetime.now(timezone.utc) - timedelta(days=7, hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
  d.execute('UPDATE users SET last_login = ? WHERE id = ?', (away, uid_fr)); d.commit(); d.close()
  rc, out = cron('--now=' + ny_now(), '--user=' + uid_fr)
  ok(rc == 0 and len(events(uid_fr, 'inactive7d')) == 1, f'daily run, 7 days away: inactive7d sent ({out.strip().splitlines()[-1] if out.strip() else rc})')
  rc, out = cron('--now=' + ny_now(), '--user=' + uid_fr)
  ok(rc == 0 and len(events(uid_fr, 'inactive7d')) == 1 and 'already sent' in out, 'the same run again: not twice')
  n0 = len(events(uid_en)); rc, out = cron('--all-events', '--user=' + uid_en)
  names = [e['eventName'] for e in events(uid_en)[n0:]]
  ok(rc == 0 and len(names) == 15 and len(set(names)) == 15, f'--all-events: the 15 events once each to a test trader ({len(names)})')
  d = sqlite3.connect(DB); n_log = d.execute('SELECT COUNT(*) FROM email_events_log WHERE user_id = ?', (uid_en,)).fetchone()[0]; d.close()
  ok(n_log == 5, f'--all-events records nothing (the trader keeps his 5 real events: {n_log})')
  rc, out = cron('--now=2026-01-01 07:30')
  ok(rc == 2 and '--user' in out, '--now without --user is refused: a test date never goes to every trader')

  # a wrong key: the app saves as usual, the refusal is logged
  config('wrong-key'); unthrottle()
  with sync_playwright() as p:
    br = p.chromium.launch(); ctx = br.new_context()
    n = 'lpk%d' % int(time.time() * 1000)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
    r2 = ctx.request.put(B + '/api/docs/accounts/k1', data=json.dumps({'name': 'Topstep 50K'}), headers=H)
    r3 = ctx.request.put(B + '/api/docs/trades/k-t1', data=json.dumps({'account_id': 'k1', 'instrument': 'NQ', 'direction': 'long', 'contracts': 1, 'pnl_c': 100, 'date': '2026-10-13'}), headers=H)
    data = ctx.request.get(B + '/api/data').json()
    br.close()
  time.sleep(0.5); srvlog.flush()
  log = open(SRVLOG).read()
  ok(r.status == 201 and r2.status == 200 and r3.status == 200 and len(data.get('trades', [])) == 1, f'wrong key: sign-up, account and trade saved as usual ({r.status}, {r2.status}, {r3.status})')
  ok('[Sweep loops] signedUp' in log and '401' in log, 'wrong key: the refusal is in the server log')
  uid_k = data['user']['id']
  d = sqlite3.connect(DB); left = d.execute('SELECT COUNT(*) FROM email_events_log WHERE user_id = ?', (uid_k,)).fetchone()[0]; d.close()
  ok(left == 0, f'wrong key: nothing marked as sent, it leaves at the next occasion ({left} line(s))')
finally:
  stop(srv); stop(mock); srvlog.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
