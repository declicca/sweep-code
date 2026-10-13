"""Sweep — automatic sync over HTTP (step 2): personal key, push from the NinjaTrader 8 add-on, accounts found,
preview, link, trades in api/data, wrong / revoked keys. Its own trader, no browser.
  python3 tests/e2e_sync_push.py [BASE] [STATE]"""
import json, sys, time, uuid, urllib.request, urllib.error, http.cookiejar
from datetime import datetime
from zoneinfo import ZoneInfo

B = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095').rstrip('/')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
jar = http.cookiejar.CookieJar(); web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
bare = urllib.request.build_opener()   # the add-on: no cookie, no session
fails = 0

def ok(c, what):
    global fails
    if not c: fails += 1
    print(('ok   ' if c else 'FAIL ') + what)

def call(op, method, path, body=None, headers=None):
    req = urllib.request.Request(B + '/' + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=headers or {})
    try:
        with op.open(req, timeout=30) as r: return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b'{}')
        except Exception: return e.code, {}

def ms(ny):   # New York wall clock → UTC milliseconds (what the add-on sends)
    return int(datetime.strptime(ny, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)

# a trader of its own, with one account
n = 'sync' + uuid.uuid4().hex[:8]
s, _ = call(web, 'POST', 'api/auth/register', {'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}, H)
ok(s in (200, 201), 'sign-up of a test trader')
s, _ = call(web, 'PUT', 'api/docs/accounts/acc-sync-1', {'name': 'Apex 1', 'firm_id': '', 'starting_balance_c': 5000000, 'status': 'active', 'fee_rt_c': 400, 'money_type': 'eval', 'phase': 'eval'}, H)
ok(s == 200, 'a Sweep account to link')

# the key: shown once, needed for every push
s, k = call(web, 'POST', 'api/sync/key', {'platform': 'ninjatrader'}, H)
key = k.get('key', '')
ok(s == 200 and key.startswith('swk_') and len(key) == 44, 'a personal key for NinjaTrader 8')
ok(call(web, 'POST', 'api/sync/key', {'platform': 'tradovate'}, H)[0] == 400, 'unknown platform refused')
ok(call(bare, 'POST', 'api/sync/key', {'platform': 'ninjatrader'}, {'Content-Type': 'application/json'})[0] in (401, 403), 'creating a key needs the trader\'s session')

fills = [
    {'id': 'x1', 'account': 'APEX-777-01', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 2, 'price': 21000.25, 'ts': ms('2026-10-07 09:31:05'), 'fee': 0.62, 'point_value': 2},
    {'id': 'x2', 'account': 'APEX-777-01', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 1, 'price': 21010.25, 'ts': ms('2026-10-07 09:35:00'), 'fee': 0.31, 'point_value': 2},
    {'id': 'x3', 'account': 'APEX-777-01', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 1, 'price': 21015.25, 'ts': ms('2026-10-07 09:40:00'), 'fee': 0.31, 'point_value': 2},
]
push = {'client': 'Sweep NT8 test', 'accounts': [{'name': 'APEX-777-01', 'connection': 'Apex', 'provider': 'Rithmic', 'currency': 'USD', 'cash': 50020}], 'fills': fills}
AK = {'Content-Type': 'application/json', 'X-Sweep-Key': key}

# the add-on's push: key only (no session, no X-Requested-With)
s, r = call(bare, 'POST', 'api/sync/push', push, AK)
ok(s == 200 and r.get('new') == 3 and r.get('accounts') == [{'name': 'APEX-777-01', 'state': 'new'}], 'push with the key alone: 3 executions kept, account found « new »')
ok(call(bare, 'POST', 'api/sync/push', push, {'Content-Type': 'application/json', 'X-Sweep-Key': 'swk_' + '0' * 40})[0] == 401, 'a wrong key → 401')
ok(call(bare, 'POST', 'api/sync/push', push, {'Content-Type': 'application/json'})[0] == 401, 'no key → 401 (a session is not enough)')
ok(call(bare, 'GET', 'api/sync/push', None, AK)[0] == 405, 'GET on the push address → 405')

# the Connections screen's data, the preview, then the link
s, st = call(web, 'GET', 'api/sync', None, H)
acc = (st.get('accounts') or [{}])[0]
ok(s == 200 and acc.get('name') == 'APEX-777-01' and acc.get('guess') == {'firm': 'apex', 'phase': 'eval'} and st['connections'][0]['client'] == 'Sweep NT8 test', 'status: the account found (Apex evaluation guessed), the add-on seen')
s, pv = call(web, 'GET', 'api/sync/accounts/%s/preview?account_id=acc-sync-1' % acc.get('id'), None, H)
ok(s == 200 and pv == {'add': 1, 'complete': 0, 'manual': 0, 'open': 0}, 'preview before linking: 1 trade to add')
s, ln = call(web, 'POST', 'api/sync/accounts/%s' % acc.get('id'), {'action': 'link', 'account_id': 'acc-sync-1'}, H)
ok(s == 200 and ln.get('ok') and ln.get('created') == 1, 'linked: 1 trade written')
s, data = call(web, 'GET', 'api/data', None, H)
t = [x for x in data.get('trades', []) if x.get('source') == 'ninjatrader']
t = t[0] if t else {}
ok(len([x for x in data.get('trades', []) if x.get('source') == 'ninjatrader']) == 1 and t.get('account_id') == 'acc-sync-1' and t.get('instrument') == 'MNQ' and t.get('contracts') == 2 and t.get('pnl_c') == 5000 and t.get('fees_c') == 124, 'the trade in the app: MNQ long 2, +$50 ((10 + 15 points) × $2), fees $1.24 from NinjaTrader')
ok(t.get('date') == '2026-10-07' and t.get('entry_time') == '09:31' and t.get('exit_time') == '09:40' and t.get('session') == 'nyam' and isinstance(t.get('review'), dict) and isinstance(t.get('emo'), dict), 'New York times, session NY AM, empty journal fields as objects')

# the same push again (the add-on resends the session at startup): nothing doubled
s, r = call(bare, 'POST', 'api/sync/push', push, AK)
s2, data2 = call(web, 'GET', 'api/data', None, H)
ok(s == 200 and r.get('new') == 0 and len([x for x in data2.get('trades', []) if x.get('source') == 'ninjatrader']) == 1, 'the same push again: nothing new, still 1 trade')

# a second platform: Quantower has its own key; a key pasted in the other platform's add-on is refused (« platform »)
s, kq = call(web, 'POST', 'api/sync/key', {'platform': 'quantower'}, H)
QK = {'Content-Type': 'application/json', 'X-Sweep-Key': kq.get('key', '')}
ok(s == 200 and kq.get('key', '').startswith('swk_') and kq.get('key') != key, 'a personal key for Quantower, separate from the NinjaTrader 8 one')
s1, r1 = call(bare, 'POST', 'api/sync/push', dict(push, client='Sweep Quantower test'), AK)
s2, r2 = call(bare, 'POST', 'api/sync/push', push, QK)
ok(s1 == 401 and r1.get('code') == 'platform' and 'NinjaTrader 8' in r1.get('error', '') and s2 == 401 and r2.get('code') == 'platform', 'a key used by the other platform\'s add-on → 401 « This key is for NinjaTrader 8 »')
s, r = call(bare, 'POST', 'api/sync/push', dict(push, client='Sweep Quantower test'), QK)
s, st = call(web, 'GET', 'api/sync', None, H)
pl = sorted((a.get('platform'), a.get('name'), a.get('state')) for a in st.get('accounts', []))
ok(r.get('new') == 3 and pl == [('ninjatrader', 'APEX-777-01', 'linked'), ('quantower', 'APEX-777-01', 'new')] and sorted(c['platform'] for c in st['connections']) == ['ninjatrader', 'quantower'], 'the Quantower push: its account listed under Quantower, the NinjaTrader 8 one unchanged')
def raw(path):
    try:
        with web.open(urllib.request.Request(B + '/' + path, headers=H), timeout=30) as r: return r.status, r.headers.get('Content-Type'), r.read()[:2]
    except urllib.error.HTTPError as e: return e.code, None, b''
d1, dq, dx = raw('api/sync/addon'), raw('api/sync/addon?platform=quantower'), raw('api/sync/addon?platform=tradovate')
ok(d1[0] == 200 and d1[1] == 'application/zip' and d1[2] == b'PK' and st['addons']['ninjatrader'] and dq[0] == (200 if st['addons']['quantower'] else 404) and dx[0] == 400, 'add-ons: NinjaTrader 8 by default (zip), Quantower once it exists, unknown platform → 400')

# heartbeat (no executions) and a revoked key
ok(call(bare, 'POST', 'api/sync/push', {'client': 'Sweep NT8 test', 'fills': []}, AK)[0] == 200, 'heartbeat without executions → 200')
ok(call(web, 'DELETE', 'api/sync/key?platform=ninjatrader', None, H)[1].get('revoked') == 1, 'stop the sync (key revoked)')
ok(call(bare, 'POST', 'api/sync/push', push, AK)[0] == 401, 'the revoked key no longer works')
s, data3 = call(web, 'GET', 'api/data', None, H)
ok(len([x for x in data3.get('trades', []) if x.get('source') == 'ninjatrader']) == 1, 'the synced trade stays after stopping (it is the trader\'s)')
ok(call(web, 'GET', 'sync/sync-store.php', None, H)[0] in (403, 404), 'the sync code is never served directly')

print('\n%s' % ('%d failed' % fails if fails else 'all passed'))
sys.exit(1 if fails else 0)
