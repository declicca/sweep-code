"""
Sweep — « Delete my account » deletes everything (brief 00, phase 1.1; Loi 25), dev environment:
  python3 tests/e2e_delete_everything.py http://127.0.0.1:8095 [storage_state, unused: it signs up its own trader]
A new trader signs up, leaves traces everywhere Sweep keeps some (a trade, a share link, a feedback, a reset link, a
browser error, the weekly email's log and preferences, a crew event, the sign-up lead with the email), then deletes the
account with the password. Afterwards, in EVERY table of the database (not a fixed list): no row with the trader's id
(user_id, uid, referrer_id, referee_id, owner_id) and no row with the trader's email. Before 16 Oct.: reset_tokens,
signup_leads, client_errors, weekly_emails, email_prefs and crew_events kept them.
"""
import json, os, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
EMAIL = 'del%d@t.dev' % int(time.time() * 1000)
SEED = {   # tables a trader can fill without the browser, created as the app creates them
  'reset_tokens': ("CREATE TABLE IF NOT EXISTS reset_tokens (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)", "INSERT INTO reset_tokens VALUES (?, ?, ?, 0)", lambda u: ('t' * 64, u, int(time.time()) + 3600)),
  'client_errors': ("CREATE TABLE IF NOT EXISTS client_errors (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, msg TEXT, src TEXT, line INT, page TEXT, ua TEXT, ver TEXT, created_at INT NOT NULL)", "INSERT INTO client_errors (user_id, msg, created_at) VALUES (?, 'x', ?)", lambda u: (u, int(time.time()))),
  'weekly_emails': ("CREATE TABLE IF NOT EXISTS weekly_emails (user_id TEXT NOT NULL, week_start VARCHAR(10) NOT NULL, sent_at INT NOT NULL, ok INT NOT NULL DEFAULT 0, PRIMARY KEY (user_id, week_start))", "INSERT INTO weekly_emails VALUES (?, '2026-10-12', ?, 1)", lambda u: (u, int(time.time()))),
  'email_prefs': ("CREATE TABLE IF NOT EXISTS email_prefs (user_id TEXT NOT NULL PRIMARY KEY, token VARCHAR(40) NOT NULL, weekly_off INT NOT NULL DEFAULT 0, updated_at INT NOT NULL)", "INSERT INTO email_prefs VALUES (?, 'tok', 0, ?)", lambda u: (u, int(time.time()))),
  'crew_events': ("CREATE TABLE IF NOT EXISTS crew_events (id INTEGER PRIMARY KEY AUTOINCREMENT, crew_id BIGINT NOT NULL, user_id TEXT NOT NULL, type VARCHAR(30) NOT NULL, payload_json TEXT NULL, created_at INT NOT NULL)", "INSERT INTO crew_events (crew_id, user_id, type, created_at) VALUES (999, ?, 'joined', ?)", lambda u: (u, int(time.time()))),
  'signup_leads': ("CREATE TABLE IF NOT EXISTS signup_leads (email_lc VARCHAR(190) NOT NULL PRIMARY KEY, lang VARCHAR(5) NULL, ref VARCHAR(32) NULL, utm VARCHAR(190) NULL, created_at INT NOT NULL, updated_at INT NOT NULL, attempts INT NOT NULL DEFAULT 1, completed_at INT NULL, user_id VARCHAR(120) NULL)", "INSERT OR REPLACE INTO signup_leads (email_lc, created_at, updated_at, completed_at, user_id) VALUES (?, ?, ?, ?, ?)", None),
}
IDCOLS = ('user_id', 'uid', 'referrer_id', 'referee_id', 'owner_id')

def traces(uid, email):
  d = sqlite3.connect(DB); out = {}
  for (t,) in d.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
    cols = [r[1] for r in d.execute(f'PRAGMA table_info("{t}")')]
    n = 0
    for c in cols:
      if c in IDCOLS: n += d.execute(f'SELECT COUNT(*) FROM "{t}" WHERE "{c}" = ?', (uid,)).fetchone()[0]
      if c in ('email', 'email_lc'): n += d.execute(f'SELECT COUNT(*) FROM "{t}" WHERE lower("{c}") = ?', (email.lower(),)).fetchone()[0]
    if t == 'users': n += d.execute('SELECT COUNT(*) FROM users WHERE id = ?', (uid,)).fetchone()[0]
    if n: out[t] = n
  d.close(); return out

with sync_playwright() as p:
  br = p.chromium.launch(); ctx = br.new_context(); pg = ctx.new_page()
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': EMAIL, 'consent': True, 'elapsed': 6000}), headers=H)
  ok(r.ok, f'a new trader signs up ({r.status})')
  d0 = sqlite3.connect(DB); row = d0.execute('SELECT id FROM users WHERE lower(email) = ?', (EMAIL.lower(),)).fetchone(); d0.close(); uid = row and row[0]
  ok(bool(uid), f'signed in as {uid}')
  # traces through the app itself: a trade, a share link, a feedback
  r1 = ctx.request.post(B + '/api/docs/batch', data=json.dumps({'col': 'trades', 'put': [{'id': 'del-t1', 'date': '2026-10-15', 'instrument': 'NQ', 'direction': 'long', 'pnl_c': 1000}]}), headers=H)
  r2 = ctx.request.post(B + '/api/share/create', data=json.dumps({'kind': 'stats', 'card': {'title': 'x', 'stats': [['Win rate', '60%']]}}), headers=H)
  print('  trade', r1.status, '· share', r2.status)
  ctx.request.post(B + '/api/feedback', data=json.dumps({'type': 'idea', 'message': 'test deletion', 'rating': 4}), headers=H)
  # the tables a trader fills in other ways (forgot password, a browser error, the weekly email, a crew)
  d = sqlite3.connect(DB)
  for t, (ddl, ins, vals) in SEED.items():
    d.execute(ddl)
    d.execute(ins, vals(uid) if vals else (EMAIL.lower(), int(time.time()), int(time.time()), int(time.time()), uid))
  d.commit(); d.close()
  before = traces(uid, EMAIL)
  ok(all(t in before for t in SEED) and 'users' in before and 'documents' in before, f'traces before: {sorted(before)}')
  r = ctx.request.delete(B + '/api/account', data=json.dumps({'password': 'Testpass123!'}), headers=H)
  ok(r.ok, f'« Delete my account » with the password ({r.status})')
  left = traces(uid, EMAIL)
  ok(not left, f'nothing left in any table, nor the email ({left})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
