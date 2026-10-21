"""
Sweep — the site's captures: the sample trader « Alex » on the capture server (never a real one), one per language.
  python3 tools/site-shots/seed.py <base_url> <state_prefix> [en fr es]
 - Alex signs up (alex.morgan.<lang>@example.com), his profile is filled;
 - his data (data.py) go through the app's own bulkPut, the browser's clock on the server's (SHOTS_NOW, New York time);
   the accounts get the firms' real plans (presets/seed.json through SweepPresets.rulesOf), the P&L is the app's calcPnl;
 - the session is saved to <state_prefix>-<lang>.json.
Then history.php replays his days in the game (plan at 8:45, review after the close), as if he had used the app every day.
"""
import datetime as dt, json, os, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data
B, PREFIX = sys.argv[1], sys.argv[2]; LANGS = sys.argv[3:] or ['en', 'fr', 'es']
NY = ZoneInfo('America/New_York')
NOW = dt.datetime.strptime(os.environ.get('SHOTS_NOW', '2026-10-15 11:05'), '%Y-%m-%d %H:%M').replace(tzinfo=NY)
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
PASS = 'Sweep-Alex-2026!'
LOC = {'en': 'en-US', 'fr': 'fr-CA', 'es': 'es-ES'}
USER = {'en': 'alexmorgan', 'fr': 'alex.morgan', 'es': 'alex_morgan'}   # one Alex per language: three usernames
PUT = """async (d) => {
  for (const a of d.accounts) { const got = SweepPresets.rulesOf(a.preset); if (!got) throw new Error('no plan ' + a.preset);
    a.rules = got.rules; a.starting_balance_c = Math.round(got.start * 100); a.phase = a.money_type = a.preset.split('|')[3]; }
  for (const t of d.trades) t.pnl_c = calcPnl(t.direction, t.entry, t.exit, t.contracts, t.instrument);
  S.settings = S.settings || defaultSettings();
  S.settings.setups = d.setups; await bulkPut('settings', [S.settings]);
  for (const c of ['firms', 'accounts', 'payouts', 'expenses', 'journals', 'trades']) await bulkPut(c, d[c]);
  render(); return [S.accounts.length, S.trades.length, S.journals.length];
}"""

def one(br, lang):
  ctx = br.new_context(viewport={'width': 1300, 'height': 850}, locale=LOC[lang], bypass_csp=True, timezone_id='America/New_York')
  ctx.clock.set_fixed_time(NOW)
  ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'));" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': PASS, 'email': 'alex.morgan.%s@example.com' % lang, 'username': USER[lang], 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise SystemExit('sign-up refused: %s %s' % (r.status, r.text()[:200]))
  r = ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Alex', 'last_name': 'Morgan', 'experience': 'gt1'}), headers=H)
  assert r.ok, r.text()
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
  pg.goto(B + '/'); pg.wait_for_function("typeof bulkPut === 'function' && typeof S !== 'undefined' && S.mode === 'server' && !!window.SweepPresets", timeout=60000)
  pg.evaluate("SweepPresets.load()"); pg.wait_for_function("SweepPresets.ready()", timeout=15000)
  d = data.build(lang); d['setups'] = data.SETUPS[lang]
  n = pg.evaluate(PUT, d); pg.wait_for_timeout(1500)
  uid = pg.evaluate("S.uid")
  ctx.storage_state(path='%s-%s.json' % (PREFIX, lang)); ctx.close()
  print(f'seed {lang}: {uid} accounts/trades/journals {n}', 'errors:', errs[:2])
  return uid

with sync_playwright() as p:
  br = p.chromium.launch()
  uids = {lang: one(br, lang) for lang in LANGS}
  br.close()
json.dump(uids, open(PREFIX + '-uids.json', 'w'))
