"""
Sweep — the app is never indexed by search engines (brief « app depuis le site », 12 Oct., step 2), dev server, HTTP only:
  python3 tests/e2e_noindex.py http://127.0.0.1:8095
 - every HTML page of the app says « noindex » (X-Robots-Tag), at all the addresses the website links to (/, /?signup=1,
   the plan links, utm_* tags); a public share page and its image too (a trader's stats);
 - robots.txt does not block the app (Google must read the « noindex »);
 - the public JSON the website reads is unchanged: api/presets (rules of the firms) and api/cohort-count.php (/100 counter);
 - api/public-totals (the website's counters, 1 Nov.): four totals and the time, nothing else, readable from makeitsweep.com
   only, cached 1 h; the sample data, a « Trades not detailed » line, an evaluation not passed and a payout only requested never count;
 - the project's .md files are never served.
"""
import base64, http.cookiejar, json, os, random, sqlite3, struct, sys, urllib.error, urllib.request, zlib
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
def get(path, headers=None, opener=None):
    try: r = (opener or urllib.request.build_opener()).open(urllib.request.Request(B + path, headers=headers or {})); return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e: return e.code, e.headers, e.read()
for u in ('/', '/?signup=1', '/?signup=1&plan=free', '/?signup=1&plan=pro&interval=year', '/?signup=1&plan=elite&interval=year', '/?signup=1&plan=pro&interval=year&utm_source=site&utm_campaign=prices', '/index.html'):
    st, h, _ = get(u)
    ok(st == 200 and (h.get('Content-Type') or '').startswith('text/html') and h.get('X-Robots-Tag') == 'noindex', f'{u}: HTML with « X-Robots-Tag: noindex » ({st}, {h.get("X-Robots-Tag")})')
st, h, body = get('/robots.txt')
ok(st == 404 or b'Disallow: /' not in body, f'robots.txt does not block the app ({st})')
st, h, body = get('/api/presets')
d = json.loads(body)
ok(st == 200 and d.get('origin') in ('seed', 'checked') and d.get('firms') and 'version' in d and 'checked_at' in d, f'api/presets: the JSON the website reads ({d.get("origin")}, {len(d.get("firms") or [])} firms)')
st, h, body = get('/api/cohort-count.php', {'Origin': 'https://makeitsweep.com'})
c = json.loads(body)
ok(st == 200 and set(c) == {'taken', 'total'} and h.get('Access-Control-Allow-Origin') == 'https://makeitsweep.com', f'api/cohort-count.php: the /100 counter, readable from makeitsweep.com ({c})')
for u in ('/INSTALLATION.md', '/README.md', '/CONTEXTE-APP.md', '/NOTES.md'):
    st, _, _ = get(u)
    ok(st in (403, 404), f'{u} is not served ({st})')
# a public share link and its image: a trader's stats
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
post = lambda p, b: json.load(op.open(urllib.request.Request(B + p, data=json.dumps(b).encode(), headers=H, method='POST')))
post('/api/auth/register', {'password': 'Testpass123!', 'email': 'ni%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000})
chunk = lambda t, x: struct.pack('>I', len(x)) + t + x + struct.pack('>I', zlib.crc32(t + x) & 0xffffffff)
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 40, 40, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(b'\x00' + b'\x4c\x8d\xff' * 40 for _ in range(40)))) + chunk(b'IEND', b'')
sid = post('/api/share/create', {'kind': 'week', 'card': {'label': 'Test', 'stats': [['Discipline', '67 %']]}, 'image': 'data:image/png;base64,' + base64.b64encode(png).decode(), 'lang': 'fr'}).get('id', '')
for u in ('/s/' + sid, '/s/' + sid + '.png'):
    st, h, _ = get(u)
    ok(st == 200 and h.get('X-Robots-Tag') == 'noindex', f'share {"image" if u.endswith(".png") else "page"}: « noindex » ({st}, {h.get("X-Robots-Tag")})')
# the website's counters: a new trader's real trade, passed evaluation and paid payout count; the rest never
DBF = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db'); CACHE = os.path.join(os.path.dirname(DBF), 'public-totals.json')
def totals(origin='https://makeitsweep.com'):
    try: os.remove(CACHE)
    except OSError: pass
    st, h, body = get('/api/public-totals', {'Origin': origin}); return st, h, json.loads(body)
def own(col):   # this trader's documents of a collection, as the server keeps them
    d = sqlite3.connect(DBF); r = [json.loads(x) for (x,) in d.execute("SELECT data FROM documents d JOIN users u ON u.id = d.user_id WHERE u.email = ? AND d.collection = ?", (EMAIL, col))]; d.close(); return r
put = lambda col, doc: op.open(urllib.request.Request(B + f'/api/docs/{col}/{doc["id"]}', data=json.dumps(doc).encode(), headers=H, method='PUT')).status
st, h, t0 = totals()
ok(st == 200 and set(t0) == {'traders', 'trades', 'evals_passed', 'payouts', 'at'} and all(isinstance(t0[k], int) for k in ('traders', 'trades', 'evals_passed', 'payouts'))
   and h.get('Access-Control-Allow-Origin') == 'https://makeitsweep.com' and 'max-age=3600' in (h.get('Cache-Control') or ''), f'api/public-totals: four totals and the time, readable from makeitsweep.com ({t0})')
st, h, _ = get('/api/public-totals', {'Origin': 'https://example.com'})
ok(st == 200 and not h.get('Access-Control-Allow-Origin'), f'api/public-totals: not readable from another site ({h.get("Access-Control-Allow-Origin")})')
st, h, again = get('/api/public-totals'); again = json.loads(again)
ok(again == t0, f'api/public-totals: kept 1 h, not counted again ({again.get("at")} = {t0.get("at")})')
EMAIL = 'pt%06d@t.dev' % random.randint(0, 999999)
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
post('/api/auth/register', {'password': 'Testpass123!', 'email': EMAIL, 'consent': True, 'elapsed': 6000})
t = dict(account_id='pt-a', instrument='NQ', direction='long', contracts=1, entry=1, exit=2, pnl_c=2000, date='2026-10-27')
for col, doc in (('accounts', {'id': 'pt-a', 'name': 'E1', 'status': 'archived', 'phase': 'eval', 'result': 'passed', 'starting_balance_c': 5000000}),
                 ('accounts', {'id': 'pt-b', 'name': 'E2', 'status': 'active', 'phase': 'eval', 'starting_balance_c': 5000000}),
                 ('accounts', {'id': 'pt-c', 'name': 'Demo', 'status': 'archived', 'phase': 'eval', 'result': 'passed', 'demo': True, 'starting_balance_c': 5000000}),
                 ('trades', dict(t, id='pt-t1')), ('trades', dict(t, id='pt-t2')), ('trades', dict(t, id='pt-t3', demo=True)), ('trades', dict(t, id='pt-t4', untracked=True, pnl_manual=True)),
                 ('payouts', {'id': 'pt-p1', 'account_id': 'pt-a', 'amount_c': 100000, 'status': 'paid', 'request_date': '2026-10-28'}),
                 ('payouts', {'id': 'pt-p2', 'account_id': 'pt-a', 'amount_c': 50000, 'status': 'requested', 'request_date': '2026-10-29'})): put(col, doc)
st, h, t1 = totals()
mine = {'trades': sum(1 for d in own('trades') if not d.get('demo') and not d.get('untracked')), 'evals_passed': sum(1 for d in own('accounts') if d.get('result') == 'passed' and not d.get('demo')),
        'payouts': sum(1 for d in own('payouts') if d.get('status') == 'paid' and not d.get('demo'))}
ok(mine == {'trades': 2, 'evals_passed': 1, 'payouts': 1} and all(t1[k] >= t0[k] + mine[k] for k in mine) and t1['traders'] >= t0['traders'] + 1,
   f'api/public-totals: a new trader, 2 trades, 1 evaluation passed, 1 payout paid count; the sample data, a summary line, an evaluation going on and a payout requested never ({t0} → {t1})')
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
